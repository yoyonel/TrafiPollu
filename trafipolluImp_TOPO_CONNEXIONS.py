__author__ = 'latty'

import numpy as np

from shapely.geometry import LineString

from imt_tools import print_exception
from trafipolluImp_TOPO_tools import *


# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)

b_use_simplification_for_points_internes_interconnexion = True


class ModuleTopoConnexions(object):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:

        """
        #
        self.__dict_symu_connexions = {}
        self.__dict_symu_connexions_CAF = {}
        self.__dict_symu_connexions_REPARTITEUR = {}
        self.__dict_symu_mouvements_entrees = {}
        #
        self.__object_DUMP = None
        #
        self.__dict_sg3_to_symuvia_from_topo_for_troncons = {}
        self.__module_topo_for_troncons = None
        #
        # Update members with arguments
        self.__update_members(**kwargs)

    def clear(self):
        """

        :return:

        """
        self.__dict_symu_connexions = {}
        self.__dict_symu_connexions_CAF = {}
        self.__dict_symu_connexions_REPARTITEUR = {}
        self.__dict_symu_mouvements_entrees = {}
        #
        self.__dict_sg3_to_symuvia_from_topo_for_troncons = {}

    @property
    def object_DUMP(self):
        return self.__object_DUMP

    @property
    def module_topo_for_troncons(self):
        return self.__module_topo_for_troncons

    @property
    def dict_symu_connexions(self):
        return self.__dict_symu_connexions

    @property
    def dict_symu_connexions_caf(self):
        return self.__dict_symu_connexions_CAF

    @property
    def dict_symu_connexions_repartiteur(self):
        return self.__dict_symu_connexions_REPARTITEUR

    @property
    def dict_symu_mouvements_entrees(self):
        return self.__dict_symu_mouvements_entrees

    def __update_members(self, **kwargs):
        """

        :param kwargs:
        :return:

        """
        # Update members with arguments
        self.__module_topo_for_troncons = kwargs.setdefault('module_topo_for_troncons', self.__module_topo_for_troncons)
        if self.__module_topo_for_troncons:
            self.__object_DUMP = self.__module_topo_for_troncons.object_DUMP
            self.__dict_sg3_to_symuvia_from_topo_for_troncons = self.__module_topo_for_troncons.dict_sg3_to_symuvia
        else:
            self.__object_DUMP = kwargs.setdefault('object_DUMP', self.__object_DUMP)
            self.__dict_sg3_to_symuvia_from_topo_for_troncons = kwargs.setdefault(
                'dict_sg3_to_symuvia',
                self.__dict_sg3_to_symuvia_from_topo_for_troncons
            )
            if self.__object_DUMP:
                logger.warning('Pas de module TOPO pour troncons transmis\n'
                               "Fort risque de manque d'informations TOPOlogiques (sur les troncons)!")

    def build(self, **kwargs):
        """

        :param kwargs:
        :return:

        """
        dict_symu_connexions = {}
        dict_symu_connexions_caf = {}
        dict_symu_connexions_repartiteur = {}
        dict_symu_mouvements_entrees = {}

        # on redefinie un lien vers le module DUMP si une instance est transmise en parametre (dict params)
        # sinon on utilise le module dump fournit a l'init
        self.__update_members(**kwargs)

        if self.__object_DUMP:
            # Pour chaque node
            # logger.info('self.object_DUMP.dict_nodes: %s' % self.object_DUMP.dict_nodes)
            for sg3_node_id, sg3_node in self.__object_DUMP.dict_nodes.iteritems():
                # resultat
                list_symu_connexions = []

                # On recupere la liste des interconnexions pour le node
                list_sg3_interconnexions = self.__object_DUMP.get_interconnexions(sg3_node_id)

                # on determine le type de la connexion
                type_connexion = self.__find_type_connexion(sg3_node_id)
                # si connexion REPARTITEUR
                if type_connexion == 'REPARTITEUR':
                    # construction de la liste des SYMUVIA connexions a partir de la liste des SG3 interconnexions
                    list_symu_connexions = self.__build_list_symu_connexions(list_sg3_interconnexions)
                    # on stocke le resultat
                    dict_symu_connexions_repartiteur[sg3_node_id] = list_symu_connexions
                elif type_connexion == 'CAF':  # si connexion CAF
                    # construction de la liste des SYMUVIA connexions a partir de la liste des SG3 interconnexions
                    list_symu_connexions = self.__build_list_symu_connexions(list_sg3_interconnexions)
                    # on stocke le resultat
                    dict_symu_connexions_caf[sg3_node_id] = list_symu_connexions

                if len(list_symu_connexions):
                    # on stocke le resultat
                    dict_symu_connexions[sg3_node_id] = list_symu_connexions

                    try:
                        # TOPO pour les mouvements
                        dict_symu_mouvements_entrees_for_node = {}
                        for nt_symu_connexion in list_symu_connexions:
                            nt_symuvia_lane_amont = nt_symu_connexion.nt_symuvia_lane_amont
                            mouvement_entrees_id = nt_symuvia_lane_amont.symu_troncon.id + '_lane' + str(
                                nt_symuvia_lane_amont.id_lane)
                            dict_symu_mouvements_entrees_for_node.setdefault(mouvement_entrees_id, [])
                            dict_symu_mouvements_entrees_for_node[mouvement_entrees_id].append(nt_symu_connexion)
                            #
                            # logger.info('mouvement_entrees_id: %s' % mouvement_entrees_id)
                            # logger.info('nt_symuvia_lane_amont.id_lane: %s' % nt_symuvia_lane_amont.id_lane)
                        # on stocke le resultat
                        dict_symu_mouvements_entrees[sg3_node_id] = dict_symu_mouvements_entrees_for_node
                    except Exception, e:
                        logger.fatal('Exception: %s' % print_exception())
            #
            if not kwargs.setdefault('staticmethod', False):
                self.__dict_symu_connexions.update(dict_symu_connexions)
                self.__dict_symu_connexions_CAF.update(dict_symu_connexions_caf)
                self.__dict_symu_connexions_REPARTITEUR.update(dict_symu_connexions_repartiteur)
                self.__dict_symu_mouvements_entrees.update(dict_symu_mouvements_entrees)
                # logger.info('dict_symu_mouvements_entrees: {0:s}'.format(dict_symu_mouvements_entrees))

            # debug infos
            # logger.info('__dict_sg3_to_symuvia: %s' % str(self.__dict_sg3_to_symuvia))
            logger.info('%d (symu) connexions added' % len(dict_symu_connexions.keys()))
        else:
            logger.fatal('Pas de DUMP disponible pour la construction de SYMUVIA Connexions !')

        # logger.info("dict_symu_connexions: %s" % str(dict_symu_connexions))
        return dict_symu_connexions

    def __build_list_symu_connexions(self, list_sg3_interconnexions):
        """

        :param list_sg3_interconnexions:
        :return:

        """
        list_nt_symu_connexions = []

        # pour chaque interconnexion (sg3)
        for sg3_interconnexion in list_sg3_interconnexions:
            nt_symu_connexion = self.__build_symu_connexion(sg3_interconnexion)
            # on stocke le resultat
            list_nt_symu_connexions.append(nt_symu_connexion)

        # retourne le resultat
        return list_nt_symu_connexions

    def __build_symu_connexion(self, sg3_interconnexion):
        """

        :param sg3_interconnexion:
        :return:

        """
        try:
            # on recupere les informations d'interconnexion SG3
            # amont/aval: (edge id, lane_ordinality)
            nt_sg3_amont = self.__object_DUMP.get_interconnexion_amont(sg3_interconnexion)
            nt_sg3_aval = self.__object_DUMP.get_interconnexion_aval(sg3_interconnexion)

            logger.info(u'nt_sg3_amont: {0:s}'.format(nt_sg3_amont))
            logger.info(u'nt_sg3_aval: {0:s}'.format(nt_sg3_aval))

            # on convertit ces informations vers SYMUVIA
            # on utilise les constructions de liens realise dans TOPO_TRONCONS
            # par l'init on est normalement relie aux resultats de TOPO_TRONCONS
            # en particulier les liens entre SG3 et SYMUVIA (pour les troncons)
            symuvia_lane_amont = self.__convert_sg3_lane_to_symuvia_lane(nt_sg3_amont)
            symuvia_lane_aval = self.__convert_sg3_lane_to_symuvia_lane(nt_sg3_aval)

            logger.info(u'symuvia_lane_amont: {0:d}'.format(symuvia_lane_amont.id_lane))
            logger.info(u'symuvia_lane_aval: {0:d}'.format(symuvia_lane_aval.id_lane))

            if symuvia_lane_amont is None:
                nt_lane_sg3 = nt_sg3_amont
                # self.__dict_sg3_to_symuvia_from_topo_for_troncons[nt_lane_sg3.edge_id][nt_lane_sg3.lane_ordinality]
                logger.info('dict_sg3_to_symuvia_from_topo_for_troncons[%d] = %s' % (
                    nt_lane_sg3.edge_id,
                    self.__dict_sg3_to_symuvia_from_topo_for_troncons[nt_lane_sg3.edge_id])
                )
                assert False, "Gros probleme!"

            # logger.info('symuvia_lane_amont id: %s' % symuvia_lane_amont.symu_troncon.id)
            # logger.info('symuvia_lane_amont id_lane: %s' % symuvia_lane_amont.id_lane)

            # Etablissement des liens de connexions (TOPO) pour les symu troncons amont/aval
            self.__connect_amont_aval_symu_troncons(symuvia_lane_amont, symuvia_lane_aval)

            # GEOMETRIE
            interconnexion_geom = self.__build_interconnexion_geometry(sg3_interconnexion)

            # On construit le TupleNamed resultat pour l'interconnexion
            return NT_CONNEXION_SYMUVIA(
                symuvia_lane_amont,
                symuvia_lane_aval,
                interconnexion_geom
            )
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())

    def __build_interconnexion_geometry(self, sg3_interconnexion):
        """

        :param sg3_interconnexion:
        :return:
        """
        interconnexion_geom = self.__object_DUMP.get_interconnexion_geometry(sg3_interconnexion)
        # simplification de la geometrie
        if b_use_simplification_for_points_internes_interconnexion:
            # permet de simplifier les lignes droites et eviter d'exporter un noeud 'POINTS_INTERNES'
            # inutile dans ce cas pour SYMUVIA
            interconnexion_geom = self.__simplify_list_points(interconnexion_geom, 0.10)
            # On retire les 1er et dernier points qui sont les amont/aval de l'interconnexion
            interconnexion_geom = interconnexion_geom[1:-1]
        return interconnexion_geom

    def __find_type_connexion(self, sg3_node_id):
        """

        :param set_edges_ids:
        :return:

        """
        type_connexion = ''

        # On recupere la liste des edges connectees par ce node
        set_edges_ids = self.__object_DUMP.get_set_edges_ids(sg3_node_id)

        # Strategie tres basique pour l'instant
        # on compte le nombre de voies connectees a l'interconnexion/node
        # et selon on decide si on a a faire a un 'REPARTITEUR' ou 'CAF'
        # TODO: prendre en compte le cas 'ROND-POINT'
        nb_edges_connected = len(set_edges_ids)
        if nb_edges_connected == 2:
            type_connexion = 'REPARTITEUR'
        elif nb_edges_connected > 2:
            type_connexion = 'CAF'

        return type_connexion

    @staticmethod
    def __simplify_list_points(
            list_points,
            tolerance_distance=0.10
    ):
        """

        :param list_points: list des points a simplfier.
                -> A priori cette liste provient d'une interconnexion SG3
                donc elle possede (normalement) au moins 4 points (amont 2 points internes aval)
        :param tolerance_distance:
        :return:

        """
        shp_list_points = LineString(list_points)
        shp_simplify_list_points = shp_list_points.simplify(tolerance_distance, preserve_topology=False)
        return np.asarray(shp_simplify_list_points)

    def __convert_sg3_lane_to_symuvia_lane(self, nt_lane_sg3):
        """

        :param nt_lane_sg3: trafipolluImp_DUMP.NT_LANE_SG3
            NamedTuple contenant un indice edge (SG3) et un indice voie lane_ordinality (SG3)
        :return: NamedTuple resultat contenant un id de troncon (SYMUVIA) et un indice de voie (SYMUVIA)
        """
        return self.__dict_sg3_to_symuvia_from_topo_for_troncons[nt_lane_sg3.edge_id][nt_lane_sg3.lane_ordinality]

    @staticmethod
    def __connect_amont_aval_symu_troncons(symuvia_lane_amont, symuvia_lane_aval):
        """

        :param symuvia_lane_amont:
        :param symuvia_lane_aval:
        :return:
        """
        # on recupere les symu troncons des amont/aval de la connexion
        symu_troncon_amont = symuvia_lane_amont.symu_troncon
        symu_troncon_aval = symuvia_lane_aval.symu_troncon
        # on lie ces symu troncons amont/aval:
        # - amont: son extrimite aval est connecte au symu troncon aval de la connexion
        # - aval: son extrimite amont est connecte au symu troncon amont de la connexion
        symu_troncon_amont.id_eltaval = symu_troncon_aval.id
        symu_troncon_aval.id_eltamont = symu_troncon_amont.id