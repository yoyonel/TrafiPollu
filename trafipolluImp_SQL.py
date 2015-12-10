__author__ = 'latty'

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry

import psycopg2
import psycopg2.extras

import trafipolluImp_DUMP as tpi_DUMP
import imt_tools
import trafipolluImp_Tools_Symuvia as tpi_TS

from imt_tools import build_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = build_logger(__name__)

#import ConfigParser
from collections import defaultdict
from Config_Tools import CConfig

import os


qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))


class trafipolluImp_SQL(object):
    """

    Implementation du module SQL

    Utilise pour gerer la communication entre la BDD StreetGen et Python/QGIS.

    Module principalement utilise pour le DUMP des donnees, et partiellement pour la TOPO (pb de design ... :/ a revoir)

    """

    def __init__(self, **kwargs):
        """

        Initialisation du module SQL:
            - Recuperation des donnees du parent (dicts: edges, node, lanes, ...)
            - Declaration de la liste des scripts SQL pris en charges
            - Recuperation des donnees de connexions a la BDD (utilisation du module 'Config')
            - Tentative d'etablissement de la connection

        .. note::
            Il faudra (peut etre) revoir ce mecanisme de connection.

            Ce n'est surement pas judicieux de le placer dans l'init de ce module
            (qui est dans l'init du parent, donc du plugin, donc au chargement de QGIS)

        :param kwargs: dictionnaire (unpack) des parametres/donnees du plugin (mecanisme de transmission)
        :type kwargs: dict

        """
        self.dict_edges = kwargs['dict_edges']
        self.dict_nodes = kwargs['dict_nodes']
        self.dict_lanes = kwargs['dict_lanes']
        self.dict_roundabouts = kwargs['dict_roundabouts']

        iface = kwargs['iface']
        self._map_canvas = iface.mapCanvas()

        #
        self._dict_sql_methods = {
            'update_def_zone_test': self._update_tables_from_qgis,
            'update_table_edges_from_qgis': self._update_tables_from_qgis,
            'update_tables_from_def_zone_test': self._update_tables_from_qgis,
            #
            'update_table_detecting_roundabouts_from_qgis': self._update_tables_from_qgis,
            #
            'dump_informations_from_edges': self._request_for_edges,
            'dump_sides_from_edges': self._request_for_lanes,
            'dump_informations_from_nodes': self._request_for_nodes,
            'dump_informations_from_lane_interconnexion': self._request_for_interconnexions,
            # TODO: travail sur les rond points [desactiver]
            # 'dump_roundabouts': self._request_for_roundabouts
        }

        ##########
        # CONFIG #
        ##########
        configs = CConfig.load_from_module(__name__, **kwargs)

        self._dict_params_server = defaultdict(dict)

        # load une section du fichier config
        configs.load_section('SQL_LOCAL_SERVER')
        configs.update(
            self._dict_params_server['LOCAL'],
            {
                'host': ('host', 'localhost'),
                'port': ('port', '5433'),
                'user': ('user', 'postgres'),
                'password': ('password', 'postgres'),
                'connect_timeout': ('connect_timeout', '2'),
                #
                'dbname': ('dbname', 'street_gen_3'),
                'database': ('database', 'bdtopo_topological')
            }
        )
        # recuperation des options liees a la section courante 'SQL_LOCAL_SERVER'
        # load une section du fichier config
        configs.load_section('SQL_IGN_SERVER')
        # recuperation des options liees a la section courante 'SQL_IGN_SERVER'
        configs.update(
            self._dict_params_server['IGN'],
            {
                'host': ('host', '172.16.3.50'),
                'port': ('port', '5432'),
                'user': ('user', 'streetgen'),
                'password': ('password', 'streetgen'),
                'connect_timeout': ('connect_timeout', '2'),
                #
                'dbname': ('dbname', 'street_gen_4'),
                'database': ('database', 'bdtopo_topological')
            }
        )
        ##########

        self.connection = None
        self.cursor = None
        self.b_connection_to_postgres_server = False

        self.connect_sql_server()

    def __del__(self):
        """

        Appel: disconnect_sql_server

        """
        self.disconnect_sql_server()

    def disconnect_sql_server(self):
        """

        Deconnection au serveur DB-StreetGen

        """
        if self.b_connection_to_postgres_server:
            self.cursor.close()
            self.connection.close()

    # TODO: a tester avant de valider la suppression de ce code
    # def get_value(self, name_server, option):
    #     """
    #
    #     :param name_server:
    #     :type name_server: str
    #     :param option:
    #     :type option: str
    #     :return:
    #     """
    #     return self.__dict__['sql_' + name_server + '_' + option]

    def connect_sql_server(self):
        """

        Tente de se connecter au serveur DB-StreetGen, suivant les parametres de connexions recuperes.

        :return: Renvoie:

           True  -- Si on a trouve une connection valide vers BD-StreetGen
           False -- Sinon

        :rtype: bool
        """
        # boucle sur la listes des parametres serveurs (possibles)
        for name_server in self._dict_params_server:
            try:
                # on tente d'etablir une connection au serveur
                self.connection = psycopg2.connect(**self._dict_params_server[name_server])
            except psycopg2.Error as e:
                logger.warning("[SQL] PsyCopg2 Error : %s - Detail: %s" % (e.pgerror, e.diag.message_detail))
            else:
                try:
                    # cursor utilise: DictCursor
                    self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                except Exception as e:
                    logger.fatal('PostGres : problem pour recuperer un cursor -> %s' % e)
                else:
                    #
                    self.b_connection_to_postgres_server = True
                    # Logs: informations sur le serveur 'valide'
                    self.connect_sql_server_log(name_server)
                    # on sort des qu'on a etablie une connection valide
                    break

        if not self.b_connection_to_postgres_server:
            logger.fatal('Impossible de se connecter a un serveur !')

        return self.b_connection_to_postgres_server

    def connect_sql_server_log(self, name_server):
        """

        LOG: on log les informations du serveur avec lequel on a etablit une connection 'valide'

        :param name_server: id d'un jeu de parametres valides pour se connecteur a un serveur DB-StreetGen
        :type name_server: str
        :return:
        """
        logger.info('connected with %s server' % name_server)
        logger.info('informations de connections:')
        map(
            lambda s: logger.info(s),
            map(
                lambda x: '- ' + str(x[0]) + ': ' + str(x[1]),
                self._dict_params_server[name_server].iteritems()
            )
        )

    @staticmethod
    def _update_tables_from_qgis(**kwargs):
        """
        Methode utlisee par les id scripts SQL:

            - :download:`update_def_zone_test.sql <../../update_def_zone_test.sql>`.
            - :download:`update_table_edges_from_qgis.sql <../../update_table_edges_from_qgis.sql>`.
            - :download:`update_tables_from_def_zone_test.sql <../../update_tables_from_def_zone_test.sql>`.
            - :download:`update_table_detecting_roundabouts_from_qgis.sql <../../update_table_detecting_roundabouts_from_qgis.sql>`.

        pour mettre a jour les vues SQL utilisees pour definir la zone de DUMP StreetGen -> Python/Symuvia

        :param kwargs: Dictionnaire des parametres (transmis)
        :type kwargs: (unpack) dict.
        :return:
        """
        try:
            # on recupere la 'connection' prealablement etablie
            connection = kwargs['connection']
        except KeyError as e:
            logger.warning('No connection ! -> {0}'.format(e))
            pass
        else:
            try:
                logger.info("try to commit ...")
                connection.commit()
            except Exception as e:
                logger.warning('Probleme au moment du commit ! -> {0}'.format(e))
                pass

    def build_sql_parameters_with_map_extent(self):
        """

        Fonctions convertissant l'extent de visualisation courante dans QGIS en polygone PostGIS
        (dans le bon systeme de coordonne Srid).

        Le resultat est transmis via un dictionnaire de parametres qui sera utilise par insertion dans les scripts SQL

        :return: Dictionnaire de parametres contenant un polygone PostGIS de l'extent QGIS
        :rtype: `dict`.
        """
        mapCanvas = self._map_canvas
        mapCanvas_extent = mapCanvas.extent()
        # get the list points from the current extent (from QGIS MapCanvas)
        list_points_from_mapcanvas = imt_tools.construct_listpoints_from_extent(mapCanvas_extent)

        # url: http://qgis.org/api/classQgsMapCanvas.html#af0ffae7b5e5ec8b29764773fa6a74d58
        extent_src_crs = mapCanvas.mapSettings().destinationCrs()
        # url: http://qgis.org/api/classQgsCoordinateReferenceSystem.html#a3cb64f24049d50fbacffd1eece5125ee
        # srid of translated lambert 93 to match laser referential
        extent_postgisSrid = 932011
        extent_dst_crs = QgsCoordinateReferenceSystem(extent_postgisSrid, QgsCoordinateReferenceSystem.PostgisCrsId)
        # url: http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/crs.html
        xform = QgsCoordinateTransform(extent_src_crs, extent_dst_crs)
        #
        list_points = [xform.transform(point) for point in list_points_from_mapcanvas]
        # list of lists of points
        gPolyline = QgsGeometry.fromPolyline(list_points)
        gPolylineWkt = gPolyline.exportToWkt()

        dict_parameters = {
            'gPolylineWkt': gPolylineWkt,
            'extent_postgisSrid': extent_postgisSrid
        }

        #######
        # LOG #
        #######
        logger.info("* list_points_from_mapcanvas: %s", list_points_from_mapcanvas)
        logger.info("* gPolygonWkt: %s", gPolylineWkt)
        logger.info("* extent_postgisSrid: %s", extent_postgisSrid)
        logger.info("extent_src_crs.postgisSrid: %s", extent_src_crs.postgisSrid())
        #######

        return dict_parameters

    def build_sql_parameters_with_map_extent_for_roundabouts(self):
        """
        idem que 'build_sql_parameters_with_map_extent'
        .. note::
        Faudrait penser a fusionner/refactorer cette partie

        :return:
        """
        mapCanvas = self._map_canvas
        mapCanvas_extent = mapCanvas.extent()
        # get the list points from the current extent (from QGIS MapCanvas)
        list_points_from_mapcanvas = imt_tools.construct_listpoints_from_extent(mapCanvas_extent)

        # url: http://qgis.org/api/classQgsMapCanvas.html#af0ffae7b5e5ec8b29764773fa6a74d58
        extent_src_crs = mapCanvas.mapSettings().destinationCrs()
        # url: http://qgis.org/api/classQgsCoordinateReferenceSystem.html#a3cb64f24049d50fbacffd1eece5125ee
        # srid of translated lambert 93 to match laser referential
        extent_postgisSrid = 932011
        extent_dst_crs = QgsCoordinateReferenceSystem(extent_postgisSrid, QgsCoordinateReferenceSystem.PostgisCrsId)
        # url: http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/crs.html
        xform = QgsCoordinateTransform(extent_src_crs, extent_dst_crs)
        #
        list_points = [xform.transform(point) for point in list_points_from_mapcanvas]

        # list of lists of points
        gPolygon = QgsGeometry.fromPolygon([list_points])
        gPolygoneWkt = gPolygon.exportToWkt()

        dict_parameters = {
            'gPolygonWkt': gPolygoneWkt,
            'extent_postgisSrid': extent_postgisSrid
        }

        logger.info("* list_points_from_mapcanvas: %s", list_points_from_mapcanvas)
        logger.info("* gPolygonWkt: %s", gPolygoneWkt)
        logger.info("* extent_postgisSrid: %s", extent_postgisSrid)
        logger.info("extent_src_crs.postgisSrid: %s", extent_src_crs.postgisSrid())

        return dict_parameters

    @staticmethod
    def build_sql_parameters_with_update_def_zone_test(
            b_update_def_zone_test_with_convex_hull_on_symuvia_network=False,
            **kwargs
    ):
        """

        Fonctions construisant un polygone PostGIS pour definir une zone de travail pour les scripts de DUMP.

        Cette zone (polygone) est constuire a partir de l'extraction d'une empreinte geographique liee a un reseau
        Symuvia.

        Voir dans :py:mod:`trafipolluImp_Tools_Symuvia` pour des details sur l'empreinte d'un reseau Symuvia.

        Le resultat est transmis via un dictionnaire de parametres qui sera utilise par insertion dans les scripts SQL

        .. warning::
            Non stable, a revoir.
            Fonctionne avec SG3 mais pas SG4 ...

        :param b_update_def_zone_test_with_convex_hull_on_symuvia_network:
        :type b_update_def_zone_test_with_convex_hull_on_symuvia_network: bool
        :param kwargs: Dictionnaire de parametres (transmis)
        :type kwargs: `dict`.
        :return:
        """
        gPolygonWkt = ''

        if b_update_def_zone_test_with_convex_hull_on_symuvia_network:
            shp_convex_hull, shp_list_extremites = tpi_TS.extract_convexhull_from_symuvia_network(**kwargs)
            gPolygonWkt = shp_convex_hull.wkt

        if gPolygonWkt == '':
            # Convex hull du reseau symuvia '/home/latty/__DEV__/__Ifsttar__/Envoi_IGN_2015_07/reseau_paris6_v31.xml'
            gPolygonWkt = 'POLYGON ((650701.858831 6860988.892569, 650685.579302 6860989.63957, 650637.589042 6861000.671025, 650625.9989689999 6861022.21112, 650475.062469 6861507.425974, 650919.609638 6862039.011138, 650988.736866 6862060.741522, 651337.303769 6861890.548595, 651383.122202 6861735.047361, 651396.56811 6861476.753853, 651404.1191219999 6861230.871522, 651403.524419 6861226.192165, 651019.06407 6861047.190387, 650836.022246 6861012.096856, 650701.858831 6860988.892569))'

        gPolygonSRID = 2154  # SRID du Lambert93

        logger.info('################ gPolygonWkt: {0}'.format(gPolygonWkt))

        dict_parameters = {
            'gPolygonWkt': gPolygonWkt,
            'gPolygonSRID': gPolygonSRID
        }

        return dict_parameters

    def execute_sql_commands(self, sql_file, id_sql_method):
        """

        Execute les commandes SQL contenues dans le script 'sql_file' identifie par 'id_sql_method'.

        Si l'id du script est soit:

            - update_table_edges_from_qgis
            - update_table_detecting_roundabouts_from_qgis
            - update_def_zone_test

        -> alors le calcul des parametres de zone d'extraction (a partir de l'extent QGIS ou d'une empreinte de reseau
        Symuvia, ou autre) pour les transmettre par la suite au script SQL (aux commandes du script).

        Dans tous les cas, on parse le script SQL pour executer toutes les commandes inclues dans le fichier script.

        :param sql_file: nom du fichier script SQL a executer
        :type sql_file: str

        :param id_sql_method: identifiant du script SQL a executer
        :type id_sql_method: str

        :return:
        """
        if not self.b_connection_to_postgres_server:
            self.connect_sql_server()

        if self.b_connection_to_postgres_server:

            dict_parameters = {}
            if id_sql_method == 'update_table_edges_from_qgis':
                dict_parameters = self.build_sql_parameters_with_map_extent()
            elif id_sql_method == 'update_table_detecting_roundabouts_from_qgis':
                dict_parameters = self.build_sql_parameters_with_map_extent_for_roundabouts()
            elif id_sql_method == 'update_def_zone_test':
                dict_parameters = self.build_sql_parameters_with_update_def_zone_test()

            try:
                sql_method = self._dict_sql_methods[id_sql_method]
            except KeyError as e:
                sql_method = None
                logger.warning('Pas de methode (python) associee au script sql: {0}'.format(e))

            # all SQL commands (split on ';')
            sqlCommands = sql_file.split(';')

            # Execute every command from the input file
            for command in sqlCommands:
                # This will skip and report errors
                # For example, if the tables do not yet exist, this will skip over
                # the DROP TABLE commands
                try:
                    # command = command.format(gPolylineWkt, extent_postgisSrid)
                    # https://docs.python.org/2/library/string.html#string.Formatter
                    # todo : look here for more advanced features on string formatter
                    # command = command.format(**dict_parameters)

                    if not command.isspace():
                        # url: http://initd.org/psycopg/docs/usage.html#query-parameters
                        # url: http://initd.org/psycopg/docs/advanced.html#adapting-new-types
                        try:
                            self.cursor.execute(command, dict_parameters)
                        except psycopg2.ProgrammingError as e:
                            logger.warning("psycopg2.ProgrammingError: {0}".format(e))
                            if id_sql_method == 'update_def_zone_test':
                                logger.warning("-> probleme connu avec 'update_def_zone_test'. Lie a la lib psycopg2")
                            else:
                                b_programming_error = True

                        sql_method(connection=self.connection, cursor=self.cursor)
                except psycopg2.OperationalError, msg:
                    logger.warning("Command skipped: %s", msg)
                    #

    def _request_for_entity(self, **kwargs):
        """

        Implementation generique pour le dump (fetch SQL) des donnees.

        kwargs doit contenir (au moins) 2 keys:

            - func_for_dumping: function de dump pour recuperer les informations sur la base DB-StreetGen
            - meth_post_request: methode de post traitement apres la recuperation des informations

        :param kwargs: Dictionnaire de parametres (transmis)
        :type kwargs: `dict`.
        :return:

        Code de retour::

             1 -- aucun probleme
            -1 -- pas de cursor disponible
            -2 -- probleme pendant le fetchall SQL

        :rtype: `int`.
        """
        try:
            cursor = kwargs["cursor"]
        except KeyError:
            logger.warning('Pas de cursor disponible!')
            return -1
        else:
            try:
                logger.info("try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except Exception as e:
                logger.warning("Probleme lors d'un 'fetchall' -> Exception: %s".format(e))
                return -2
            else:
                try:
                    post_resquest_for_entity = kwargs['meth_post_request']
                    dump_for_entity = kwargs['func_for_dumping']
                    post_resquest_for_entity(dump_for_entity(objects_from_sql_request))
                except KeyError as e:
                    logger.warning('Pb! -> {0}'.format(e))
                return 1

    def _request_for_roundabouts(self, **kwargs):
        """

        Implementation specialisee pour le DUMP d'informations sur les rond-points.

        Voir: :py:func:`_request_for_entity`

        :param kwargs:
        :type kwargs: str
        :return:
        :rtype: int
        """
        kwargs.update(
            {
                'meth_post_request': self._post_request_for_roundabouts,
                'func_for_dumping': tpi_DUMP.dump_for_roundabouts
            }
        )
        return self._request_for_entity(**kwargs)

    def _post_request_for_roundabouts(self, results_dump):
        """

        Implementation de la post-request pour les rond-points.

        Transfert des donnees recuperees pour les rond-points dans les structures de donnees Python

        :param results_dump: Dictionnaire contenant le DUMP des informations SQL-StreetGen sur les rond-points
        :type results_dump: `dict`.
        :return:
        """
        dict_roundabouts = results_dump

        for ra_id, ra_dump in dict_roundabouts.iteritems():
            # ajouter les informations aux 'nodes'
            for node_id in ra_dump['list_nodes']:
                if node_id in self.dict_nodes:
                    self.dict_nodes[node_id].update({'roundabouts': ra_id})
            # ajouter les informations aux 'edges'
            for edge_id in ra_dump['list_edges']:
                if edge_id in self.dict_edges:
                    self.dict_edges[edge_id].update({'roundabouts': ra_id})

        self.dict_roundabouts.update(dict_roundabouts)

    def _request_for_edges(self, **kwargs):
        """

        Implementation specialisee pour le DUMP d'informations sur les edges/aretes/troncons.

        Voir: :py:func:`_request_for_entity`

        :param kwargs:
        :type kwargs: str
        :return:
        :rtype: int

        """
        kwargs.update(
            {
                'meth_post_request': self._post_request_for_edges,
                'func_for_dumping': tpi_DUMP.dump_for_edges
            }
        )
        return self._request_for_entity(**kwargs)

    def _post_request_for_edges(self, results_dump):
        """

        Implementation de la post-request pour les edges.

        Transfert des donnees recuperees pour les edges dans les structures de donnees Python

        :param results_dump: Dictionnaire contenant le DUMP des informations SQL-StreetGen sur les edges
        :type results_dump: `dict`.
        :return:
        """
        dict_edges = results_dump
        self.dict_edges.update(dict_edges)

    def _request_for_nodes(self, **kwargs):
        """

        Implementation specialisee pour le DUMP d'informations sur les nodes/noeuds/centre d'intersections

        Voir: :py:func:`_request_for_entity`

        :param kwargs:
        :type kwargs: str
        :return:
        :rtype: int

        """
        kwargs.update(
            {
                'meth_post_request': self._post_request_for_nodes,
                'func_for_dumping': tpi_DUMP.dump_for_nodes
            }
        )
        return self._request_for_entity(**kwargs)

    def _post_request_for_nodes(self, results_dump):
        """

        Implementation de la post-request pour les nodes.

        Transfert des donnees recuperees pour les nodes dans les structures de donnees Python

        :param results_dump: Dictionnaire contenant le DUMP des informations SQL-StreetGen sur les nodes
        :type results_dump: `dict`.
        :return:
        """
        dict_nodes = results_dump
        self.dict_nodes.update(dict_nodes)

    def _request_for_interconnexions(self, **kwargs):
        """

        Implementation specialisee pour le DUMP d'informations sur les interconnexions

        Voir: :py:func:`_request_for_entity`

        :param kwargs:
        :type kwargs: str
        :return:
        :rtype: int
        """
        kwargs.update(
            {
                'meth_post_request': self._post_request_for_interconnexions,
                'func_for_dumping': tpi_DUMP.dump_for_interconnexions
            }
        )
        return self._request_for_entity(**kwargs)

    def _post_request_for_interconnexions(self, results_dump):
        """

        Implementation de la post-request pour les interconnexions.

        Transfert des donnees recuperees pour les interconnexions dans les structures de donnees Python

        :param results_dump: Dictionnaire contenant le DUMP des informations SQL-StreetGen sur les interconnexions
        :type results_dump: `dict`.
        :return:
        """
        dict_interconnexions, dict_set_id_edges = results_dump

        # ajouter les informations d'interconnexions au noeud
        for node_id, interconnexions in dict_interconnexions.iteritems():
            self.dict_nodes[node_id].update(
                {
                    'interconnexions': interconnexions,
                    'set_id_edges': dict_set_id_edges[node_id]
                }
            )

    def _request_for_lanes(self, **kwargs):
        """

        Implementation specialisee pour le DUMP d'informations sur les lanes/voies

        Voir: :py:func:`_request_for_entity`

        :param kwargs:
        :type kwargs: `dict`.
        :return:
        :rtype: int
        """
        kwargs.update(
            {
                'meth_post_request': self._post_request_for_lanes,
                'func_for_dumping': lambda x: tpi_DUMP.dump_lanes(x, self.dict_edges)
            }
        )
        return self._request_for_entity(**kwargs)

    def _post_request_for_lanes(self, results_dump):
        """

        Implementation de la post-request pour les lanes/voies.

        Transfert des donnees recuperees pour les lanes/voies dans les structures de donnees Python

        :param results_dump: Dictionnaire contenant le DUMP des informations SQL-StreetGen sur les lanes/voies
        :type results_dump: `dict`.
        :return:
        """
        dict_lanes, dict_grouped_lanes = results_dump

        self.dict_lanes.update(dict_lanes)
        # update dict_edges with lanes grouped informations
        for sg3_edge_id, grouped_lanes in dict_grouped_lanes.items():
            self.dict_edges[sg3_edge_id].update(grouped_lanes)