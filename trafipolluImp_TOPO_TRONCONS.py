__author__ = 'latty'

from itertools import groupby
import numpy as np

import pyxb
from shapely.geometry import Point, LineString

from trafipolluImp_TOPO_tools import *
import trafipolluImp_DUMP as module_DUMP
import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import print_exception




# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)

b_use_simplification_for_points_internes_troncon = True
b_add_points_internes_troncons = True


class ModuleTopoTroncons(object):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        # from DUMP
        self.__object_DUMP = kwargs.setdefault('object_DUMP', None)
        #
        self.__dict_symu_troncons = {}
        self.__dict_grouped_lanes = {}
        self.__dict_sg3_to_symuvia = {}

    ###############
    # PROPORTIES
    ###############
    @property
    def dict_sg3_to_symuvia(self):
        return self.__dict_sg3_to_symuvia

    @property
    def object_DUMP(self):
        return self.__object_DUMP

    @property
    def dict_symu_troncons(self):
        return self.__dict_symu_troncons

    def clear(self):
        """

        :return:

        """
        self.__dict_symu_troncons = {}
        self.__dict_grouped_lanes = {}
        self.__dict_sg3_to_symuvia = {}

    def update_parameters(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # on redefinie un lien vers le module DUMP si une instance est transmise en parametre (dict params)
        # sinon on utilise le module dump fournit a l'init
        self.__object_DUMP = kwargs.setdefault('object_DUMP', self.__object_DUMP)

    def build(self, **kwargs):
        """
        Construit un dictionnaire contenant les troncons SYMUVIA.
        Cette methode effectue aussi la construction des liens entre les edges SG3 et les troncons SYMUVIA

        :param dict_edges: dict( str : dict(...) )
            Dictionnaire contenant les edges SG3
             - key: edge id
             - values: PYXB Symuvia TRONCON
        :param kwargs: dict( str: values )
            - 'object_DUMP': par defaut conserve l'instance du module DUMP transmis prealablement
                Instance du module DUMP, si present remplace le module actuel
            - 'staticmethod': False par defaut
                si False -> on met a jour la classe avec les valeurs construites
                si True -> on renvoie le resultat (sans affecter la classe, comportement d'un @staticmethod)
        :return: dict( str : pyxb object )

        """
        dict_symutroncons = {}

        self.update_parameters(**kwargs)

        if self.__object_DUMP:
            # construction des groupes lanes
            # logger.info('object_DUMP.dict_lanes: %s' % object_DUMP.dict_lanes)
            dict_grouped_lanes = self.__build_dict_grouped_lanes(self.__object_DUMP.dict_lanes)
            # logger.info('dict_grouped_lanwglGetProcAddressglCreateShaderObject
            # es: %s' % dict_grouped_lanes)

            # on parcourt l'ensemble des id des edges disponibles
            for edge_id, sg3_edge in self.__object_DUMP.dict_edges.iteritems():
                group_lanes_for_edge = dict_grouped_lanes[edge_id]['grouped_lanes']
                # logger.info('group_lanes_for_edge: %s' % group_lanes_for_edge)
                dict_symutroncons.update(self.__build_symutroncons_from_sg3_edge(sg3_edge, group_lanes_for_edge))
            #
            if not kwargs.setdefault('staticmethod', False):
                self.__dict_symu_troncons.update(dict_symutroncons)
            # debug infos
            # logger.info('__dict_sg3_to_symuvia: %s' % str(self.__dict_sg3_to_symuvia))
            logger.info('%d (symu) troncons added' % len(dict_symutroncons.keys()))
        else:
            logger.fatal('Pas de DUMP disponible pour la construction de SYMUVIA troncons !')

        return dict_symutroncons

    @staticmethod
    def static_build_dict_grouped_lanes(dict_lanes, str_id_for_grouped_lanes='grouped_lanes'):
        """

        :param dict_lanes: informations des voies des edges
            - key: edge id SG3
            - values: liste de voies pour l'edge
        :return:
        Retourne un dictionnaire dont les
        - key: indice edge SG3
        - value: liste de groupes de lanes dans le meme sens.
            Chaque element de la liste decrit le nombre de voies consecutives dans le meme sens.
        """
        dict_grouped_lanes = {}

        list_edges_counting_grouped_lanes = [
            [
                # url: http://stackoverflow.com/questions/13870962/python-how-to-get-the-length-of-itertools-grouper
                sum(1 for i in value_groupby)
                for key_groupby, value_groupby in
                groupby(
                    # reorganisation de la liste pour suivre un ordre 'pythonien' d'indices (0...n-1)
                    # url: http://stackoverflow.com/questions/2177590/how-can-i-reorder-a-list-in-python
                    [
                        dict_lanes[sg3_edge_id][lane_ordinality]
                        for lane_ordinality in ListLanesPythonOrderingIter(dict_lanes[sg3_edge_id])
                    ],
                    lambda x: x['lane_direction']
                )
            ]
            for sg3_edge_id in dict_lanes
        ]

        map(
            lambda x, y: dict_grouped_lanes.__setitem__(x, {str_id_for_grouped_lanes: y}),
            dict_lanes,
            list_edges_counting_grouped_lanes
        )

        # DEBUG
        # list_lane_ordinality = [
        # [
        #         lane_ordinality
        #         for lane_ordinality in ListLanesPythonOrderingIter(dict_lanes[sg3_edge_id])
        #     ]
        #     for sg3_edge_id in dict_lanes
        # ]
        # logger.info('list_lane_ordinality: %s' % list_lane_ordinality)

        return dict_grouped_lanes

    def __build_dict_grouped_lanes(self, dict_lanes, str_id_for_grouped_lanes='grouped_lanes'):
        """

        :param dict_lanes: informations des voies des edges
            - key: edge id SG3
            - values: liste de voies pour l'edge
        :return:
        Retourne un dictionnaire dont les
        - key: indice edge SG3
        - value: liste de groupes de lanes dans le meme sens.
            Chaque element de la liste decrit le nombre de voies consecutives dans le meme sens.

        TEST:
        dict_lanes = {
            'edge_0': [
                {},
                {'lane_direction': False},
                {'lane_direction': True},
                {'lane_direction': True},
                {'lane_direction': False},
                {'lane_direction': True}
            ]
        }
        >> trafipolluImp_TOPO_for_TRONCONS.build_dict_grouped_lanes(dict_lanes)
        {'edge_0': {'grouped_lanes': [2, 1, 1, 1]}}

        """
        dict_grouped_lanes = self.static_build_dict_grouped_lanes(dict_lanes, str_id_for_grouped_lanes)
        self.__dict_grouped_lanes.update(dict_grouped_lanes)
        return dict_grouped_lanes

    def __build_symutroncons_from_sg3_edge(self, sg3_edge, grouped_lanes_for_edge):
        """

        :param sg3_edge: edge SG3
        :param grouped_lanes_for_edge: tableau des groupes de voies mono-directionnelles pour cet edge SG3
        :return:
            Dictionnaire des troncons symuvia
            - key : id du troncon symuvia
            - value: object pyxb symuvia troncon

        """
        dict_symutroncons = {}

        sg3_edge_id = module_DUMP.get_edge_id(sg3_edge)
        python_lane_id = 0

        # logger.info("sg3_edge_id: %d" % sg3_edge_id)

        try:
            # on parcourt les groupes de voies (mono-directionnelles) pour la sg3_edge
            # on recupere le nombre de voies (SG3) consecutives mono-directionnelles
            for nb_lanes_in_group in grouped_lanes_for_edge:
                # logger.info('nb_lanes_in_group: %s', nb_lanes_in_group)

                # on construit un symu_troncon avec un groupe de voies mono-directionnelles
                symutroncon = self.__build_symutroncon_from_sg3_lanes(
                    sg3_edge,
                    sg3_edge_id,
                    python_lane_id,
                    nb_lanes_in_group
                )

                # construction du lien topologique entre SG3 et SYMUVIA
                self.__build_links_sg3_symuvia(
                    sg3_edge_id,
                    python_lane_id,
                    nb_lanes_in_group,
                    symutroncon,
                    len(grouped_lanes_for_edge) > 1
                )

                # on rajoute l'element dans le dictionnaire resultat
                dict_symutroncons.update({symutroncon.id: symutroncon})

                # prochain groupe de voies
                python_lane_id += nb_lanes_in_group

        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        finally:
            return dict_symutroncons

    def __build_symutroncon_from_sg3_lanes(self, *args):
        """
        Construction d'un symutroncon a partir d'un groupe de voies SG3
        :return:

        """
        try:
            # on recupere les amont/aval et points internes du troncon construit a partir du groupes de voies
            results_compute_aapt = self.__compute_amont_aval_points_internes_from_sg3_lanes(*args)
            # logger.info('results_compute_aapt: %s' % results_compute_aapt)
            # construction de l'objet PYXB pour export Symuvia TRONCON
            pyxb_symutroncon = self.__build_pyxb_troncon(results_compute_aapt, *args)
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            return pyxb_symutroncon

    def __build_pyxb_troncon(self, results_compute_aapt, *args):
        """

        :param results_compute_aapt:
        :param args:
        :return:

        """
        try:
            sg3_edge, sg3_edge_id, python_lane_id, nb_lanes_in_group = args

            # construction du nom LICIT pour le troncon (aide debug)
            nom_rue = self.build_LICIT_name_for_edge(sg3_edge)
            # logger.info('nom_rue: %s' % nom_rue)

            # construction de l'object pyxb symtroncon
            pyxb_symutroncon = symuvia_parser.typeTroncon(
                id=self.build_id_for_symutroncon(sg3_edge['ign_id'], python_lane_id),
                nom_axe=nom_rue,
                largeur_voie=sg3_edge['road_width'] / sg3_edge['lane_number'],
                id_eltamont="-1",
                id_eltaval="-1",
                extremite_amont=results_compute_aapt.amont,
                extremite_aval=results_compute_aapt.aval,
                nb_voie=nb_lanes_in_group
            )
            # logger.info('pyxb_symutroncon: %s' % pyxb_symutroncon)

            # transfert des POINTS_INTERNES
            if b_add_points_internes_troncons:
                pyxb_symutroncon.POINTS_INTERNES = self.__build_pyxb_troncon_points_internes(results_compute_aapt)
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            return pyxb_symutroncon

    def __compute_amont_aval_points_internes_from_sg3_lanes(self, *args):
        """
        1 Groupe de plusieurs voies (dans la meme direction) dans une serie de groupes (de voies) pour l'edge_sg3
        On recupere les coefficients 1D de projection de chaque point sur sa voie.
        On rassemble tout ces coefficients et re-echantillone les voies (nombres de points d'echantillon homogene entre
         chaque voie). On moyenne tous les points de chaque voie pour former un axe (edge) mediant.

        :return:

        """
        # on recupere les arguments
        sg3_edge, sg3_edge_id, python_lane_id, nb_lanes_in_group = args

        # intervalles (sur les indices) des voies du groupe
        range_python_lanes_id = range(python_lane_id, python_lane_id + nb_lanes_in_group)

        # on recupere les listes des geometries des voies du groupe
        # et on calcul leurs projections sur leurs axes respectifs
        shp_lanes, list_1d_coefficients = self.__build_lists_shp_lanes_and_projected_coefficients(
            sg3_edge_id,
            range_python_lanes_id
        )
        # logger.info('list_1d_coefficients: %s' % list_1d_coefficients)

        # via les geometries des voies et leurs coefficients de projection
        # on calcul un axe 'mediant' pour le troncon representant cet agglomerat de voies
        lane_geometry = self.__build_lane_geometry(shp_lanes, list_1d_coefficients)
        # logger.info('lane_geometry: %s' % lane_geometry)

        # # TEST: DEBUG
        # lane_geometry = self.__get_lane_geometry(sg3_edge_id, nb_lanes_in_group-1)
        # logger.info('lane_geometry: %s' % lane_geometry)

        # Faudrait verifier la validite du resultat (plus de 2 points au moins)

        # Comme la liste des coefficients 1D est triee,
        # on peut declarer le 1er et dernier point comme Amont/Aval
        id_vertice_for_amont, id_vertice_for_aval = 0, -1
        # on retourne les resultats de construction

        return NT_RESULT_BUILD_PYXB(
            lane_geometry[id_vertice_for_amont],
            lane_geometry[id_vertice_for_aval],
            lane_geometry
        )

    @staticmethod
    def __build_lane_geometry(shp_lanes, list_1d_coefficients):
        # Calcul de l'axe central du TRONCON (Symuvia)
        # Methode: on utilise les coefficients 1D de chaque voie qui va composer ce troncon.
        # On retroprojete chaque coeffient (1D) sur l'ensemble des voies (2D) et on effectue la moyenne des positions
        # On recupere 'une sorte d'axe median' des voies (du meme groupe)
        #
        lane_geometry = []
        # coefficient de normalisation depend du nombre de voies qu'on utilise pour la moyenne
        norm_lanes_center_axis = 1.0 / len(shp_lanes)

        # pour chaque coefficient 1D
        for coef_point in list_1d_coefficients:
            # on calcule la moyenne des points sur les lanes pour ce coefficient
            np_point_for_troncon = np.array((0.0, 0.0))
            # pour chaque shapely lane
            for shp_lane in shp_lanes:
                projected_point_on_lane = np.array((shp_lane.interpolate(coef_point, normalized=True)).coords[0])
                # on projete le coefficient et on somme le point
                np_point_for_troncon += projected_point_on_lane
            # on calcule la moyenne
            np_point_for_troncon *= norm_lanes_center_axis
            lane_geometry.append(list(np_point_for_troncon))
        return lane_geometry

    def __build_lists_shp_lanes_and_projected_coefficients(self, sg3_edge_id, range_python_lanes_ids):
        """

        :param sg3_edge:
        :param sg3_edge_id:
        :param start_python_lane_id:
        :param nb_lanes_in_group:
        :return:
            tuple de resultats
            - liste des shapely geoms des voies pour l'intervalle considere
            - liste des coefficients (projectes sur leurs axes) des points des geoms des voies. Cette liste finale
              (fusionnee) est triee et 'cleanee': on s'assure l'unicite des coefficients (en particulier 0.0 et 1.0, qui
              sont les amonts/avals (projetes) de chaque voie
        """
        # transfert lane_center_axis for each lane in 2D
        list_projected_coefficients = []
        shp_lanes = []
        # on parcourt le groupe de 'voies' dans le meme sens
        # parcours des voies de sg3_edge dans l'ordre python (0 ... n-1)
        # pour chaque voie dans le groupe de voie
        for python_lane_id in range_python_lanes_ids:
            # on recupere la geometrie de la voie
            sg3_lane_geom = self.__get_lane_geometry(sg3_edge_id, python_lane_id)

            # on la transforme en shapely geom
            shp_lane = LineString(sg3_lane_geom)

            # on projete les points formant la voie sur son axe pour recuperer des coefficients 1D. Les coefficients
            # sont normes par la longueur de l'axe, donc les coefficients sont entre [0.0, 1.0])
            linestring_proj_1D_coefficients = [
                shp_lane.project(Point(point), normalized=True)
                for point in list(shp_lane.coords)
            ]

            # on ajoute la geometrie de la voie
            shp_lanes.append(shp_lane)
            # logger.info(u'{1:d} - shp_lane: {0:s}'.format(shp_lane, python_lane_id))

            # on ajpute les coefficients geometriques de la voie
            list_projected_coefficients += linestring_proj_1D_coefficients

        # ##########################
        # clean the list of 1D coefficients
        # remove duplicate values
        # url: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
        list_projected_coefficients = list(set(list_projected_coefficients))
        # sort the list of 1D coefficients
        list_projected_coefficients.sort()
        # ##########################

        # logger.info(u'shp_lanes: {0:s}'.format(shp_lanes))

        # on retourne un tuple de resultats
        return shp_lanes, list_projected_coefficients

    def __get_lane_geometry(self, sg3_edge_id, python_id_lane):
        """

        :param sg3_edge:
        :param python_id_lane:
        :param nb_lanes:
        :return:

        """
        nb_lanes = self.__object_DUMP.get_lane_number(sg3_edge_id)
        # on convertie le python id lane par rapport a l'edge SG3 en lane ordinality
        lane_ordinality = convert_python_id_to_lane_ordinality(python_id_lane, nb_lanes)
        # on recupere depuis le DUMP l'information de geometrie associee a la voie SG3
        return self.__object_DUMP.get_lane_geometry(sg3_edge_id, lane_ordinality)

    @staticmethod
    def build_id_for_symutroncon(str_pyxb_symutroncon_id, lane_id):
        """

        :param pyxb_symuTRONCON:
        :param lane_id:
        :return:
        """
        return str_pyxb_symutroncon_id + '_lane_' + str(lane_id)

    @staticmethod
    def build_LICIT_name_for_edge(sg3_edge):
        # mise a jour des champs (debug LICIT)
        nom_rue_g = sg3_edge['nom_rue_g']
        nom_rue_d = sg3_edge['nom_rue_d']
        nom_rue = nom_rue_g
        if nom_rue_g != nom_rue_d:
            nom_rue += '-_-' + nom_rue_d
        return nom_rue

    @staticmethod
    def optimize_list_points(
            list_points,
            min_distance=0.60,
            tolerance_distance=0.10,
            epsilon=0.05
    ):
        """

        :param list_points:
        :param min_distance:
        :param tolerance_distance:
        :param epsilon:
        :return:

        """
        shp_list_points_optimized = []
        try:
            min_distance += epsilon
            shp_list_points = LineString(list_points)
            # resampling
            list_shp_points_resampled = [
                shp_list_points.interpolate(distance)
                for distance in np.arange(min_distance,
                                          shp_list_points.length - min_distance,
                                          min_distance)
            ]
            list_shp_points = list_shp_points_resampled
        except:
            # exception si LineString(list_points) ne fonctionne pas.
            # On optimise que des lignes strings (plus de 3 points dans liste_points)
            pass
        else:
            try:
                resample_shp_geometry = LineString(list_shp_points)
                shp_list_points_optimized = resample_shp_geometry.simplify(
                    tolerance_distance,
                    preserve_topology=False
                )
            except:
                # exception si LineString(list_shp_points) ne fonctionne pas.
                # On optimise que des lignes strings (plus de 3 points dans list_shp_points)
                pass
        finally:
            return np.array(shp_list_points_optimized)

    @staticmethod
    def __build_pyxb_troncon_points_internes(results_compute_aapt):
        """

        :param results_compute_aapt:
        :return:

        """
        try:
            pyxb_symutroncon_points_internes = None

            list_points = results_compute_aapt.points_internes
            # transfert des POINTS_INTERNES
            if len(list_points):
                if b_use_simplification_for_points_internes_troncon:
                    list_points = ModuleTopoTroncons.optimize_list_points(list_points, 2.0, 0.10)
                pyxb_symutroncon_points_internes = symuvia_parser.typePointsInternes()
                [pyxb_symutroncon_points_internes.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            return pyxb_symutroncon_points_internes

    def __build_links_sg3_symuvia(
            self,
            sg3_edge_id,
            start_python_lane_id,
            nb_lanes_in_group,
            pyxb_symutroncon,
            multi_groups
    ):
        """

        :param sg3_edge_id:
        :param start_python_lane_id:
        :param nb_lanes:
        :param pyxb_symutroncon:
        :return:

        """
        logger.info('sg3_edge_id: %d' % sg3_edge_id)

        nb_lanes = self.__object_DUMP.get_lane_number(sg3_edge_id)
        # SG3 order (lane_ordinality)
        self.__dict_sg3_to_symuvia.setdefault(sg3_edge_id, [None] * (nb_lanes + 1))

        range_python_lanes_id = range(start_python_lane_id, start_python_lane_id + nb_lanes_in_group)
        # on recupere les indices des voies du groupe (Python order)
        for python_lane_id in range_python_lanes_id:
            # on convertie le python id de la voie en SG3 lane ordinality (SG3 order)
            sg3_lane_ordinality = convert_python_id_to_lane_ordinality(python_lane_id, nb_lanes)

            # if multi_groups:
            # lane_direction = False
            # else:
            #     lane_direction = self.__object_DUMP.get_lane_direction(sg3_edge_id, sg3_lane_ordinality)
            # #
            # b_inverse_order = not lane_direction
            lane_direction = self.__object_DUMP.get_lane_direction(sg3_edge_id, sg3_lane_ordinality)
            b_inverse_order = lane_direction

            # on convertie le python id (de la voie) en numero de voie (SYMUVIA order)
            symu_lane_id = convert_lane_python_id_to_lane_symuvia_id(
                python_lane_id,
                start_python_lane_id,
                nb_lanes_in_group,
                b_inverse_order
            )

            # on construit le tuple representant la voie SYMUVIA : (symutroncon, id de la voie (SYMUVIA order))
            nt_lane_symuvia = NT_LANE_SYMUVIA(pyxb_symutroncon, symu_lane_id)
            # on enregistre le lien topologique entre la voie SG3 -> SYMUVIA
            self.__dict_sg3_to_symuvia[sg3_edge_id][sg3_lane_ordinality] = nt_lane_symuvia

            logger.info('-> python_lane_id=%d -> sg3_lane_ordinality=%d -> symu_lane_id=%d' %
                        (python_lane_id, sg3_lane_ordinality, symu_lane_id))

    def __convert_sg3_lane_to_symuvia_lane(self, nt_lane_sg3):
        """

        :param nt_lane_sg3: trafipolluImp_DUMP.NT_LANE_SG3
        :return:
        """
        return self.__dict_sg3_to_symuvia[nt_lane_sg3.edge_id][nt_lane_sg3.lane_ordinality]

    def get_symu_troncon(self, symu_troncon_id):
        """

        :param symu_troncon_id:
        :return:
        """
        return self.__dict_symu_troncons[symu_troncon_id]


def test_build_dict_grouped_lanes(dict_lanes=None):
    """

    :param dict_lanes:
    :return:

    >> test_build_dict_grouped_lanes()
    {'edge_0': {'grouped_lanes': [2, 1, 1, 1]}}

    """
    if dict_lanes is None:
        print dict_lanes
        dict_lanes = {
            'edge_0': [
                {},
                {'lane_direction': False},
                {'lane_direction': True},
                {'lane_direction': True},
                {'lane_direction': False},
                {'lane_direction': True}
            ]
        }
        # python order for lane_ordinality
        # so dict_lanes['edge_0'] is equivalent to (lane ordinality order)
        # 5 3 1 2 4
        # t t f t f
    return ModuleTopoTroncons.static_build_dict_grouped_lanes(dict_lanes)