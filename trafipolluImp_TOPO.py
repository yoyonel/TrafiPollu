__author__ = 'latty'

import numpy as np
from itertools import groupby

from shapely.geometry import Point, LineString
import pyxb

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import CreateNamedTupleOnGlobals
from imt_tools import CreateNamedTuple
from imt_tools import print_exception
import trafipolluImp_DUMP as module_DUMP


NT_LANE_SG3_SYMU = CreateNamedTupleOnGlobals(
    'NT_LANE_SG3_SYMU',
    [
        'symu_troncon',
        'start_id_lane',
        'nb_lanes',
        'lane_direction'
    ]
)

NT_INTERCONNEXION = CreateNamedTupleOnGlobals(
    'NT_INTERCONNEXION',
    [
        'lane_amont',
        'lane_aval',
        'geometry'
    ]
)

NT_LANE_SYMUVIA = CreateNamedTupleOnGlobals(
    'NT_LANE_SYMUVIA',
    [
        'symu_troncon',
        'id_lane',
    ]
)

NT_RESULT_BUILD_PYXB = CreateNamedTuple(
    'NT_RESULT_BUILD_PYXB',
    [
        'amont',
        'aval',
        'points_internes'
    ]
)

# ######## OPTIONS D'EXPORT ############
b_add_points_internes_troncons = True
b_use_simplification_for_points_internes_troncon = True
b_use_simplification_for_points_internes_interconnexion = True
# ######## ######### ######### #########

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)


def number_is_even(number):
    """

    :param number:
    :return:
    """
    return number % 2 == 0


def count_number_odds(max_number):
    """

    :param max_number:
    :return:
    """
    return int(float((max_number / 2.0) + 0.5))


def convert_lane_ordinality_to_python_id(lane_ordinality, nb_lanes):
    """

    :param nb_lanes:
    :param lane_ordinality:
    :return:
    """
    nb_odds = count_number_odds(nb_lanes)
    return (nb_odds + (lane_ordinality / 2) - 1) if number_is_even(lane_ordinality) \
        else (nb_odds - (lane_ordinality + 1) / 2)


def convert_python_id_to_lane_ordinality(python_id, nb_lanes):
    """

    :param python_id:
    :param nb_lanes:
    :return:
    """
    nb_odds = count_number_odds(nb_lanes)
    return ((nb_odds - python_id) * 2 - 1) if python_id < nb_odds else (python_id - nb_odds + 1) * 2


def convert_lane_python_id_to_lane_symuvia_id(python_id, start_python_id, nb_lanes_in_group, lane_direction):
    """

    :param python_id:
    :param nb_lanes:
    :return:

    TESTS:
    >> convert_lane_python_to_symuvia_id(0, 0, 1, True)
    1
    >> convert_lane_python_to_symuvia_id(0, 0, 1, False)
    1
    >> convert_lane_python_to_symuvia_id(0, 0, 2, False)
    1
    >> convert_lane_python_to_symuvia_id(0, 0, 2, True)
    2
    >> convert_lane_python_to_symuvia_id(1, 1, 1, True)
    1
    >> convert_lane_python_to_symuvia_id(1, 1, 1, False)
    1
    """
    # repere relatif au sous groupe de voies
    symu_lane_id = python_id - start_python_id
    # inversion du numero de voie selon le sens de la voie (TODO: a verifier pour le sens et l'inversion)
    if not lane_direction:
        symu_lane_id = (nb_lanes_in_group - 1) - symu_lane_id
    # 0 ... n-1 -> 1 ... n
    symu_lane_id += 1
    # on renvoie l'indice symuvia calcule
    return symu_lane_id


# url: http://anandology.com/python-practice-book/iterators.html
class ListLanesPythonOrderingIter(object):
    """
    Construit un iterator pour parcourir dans un ordre pythonien les indices (ordinality) de voies SG3

    """

    def __init__(self, list_lane_informations):
        """

        :param list_lane_informations:
        :return:
        """
        self.list_lanes = list_lane_informations
        self.nb_lanes = len(list_lane_informations) - 1  # -1 car indice pour cette liste [1 ... n]
        self.id = 0

    def __iter__(self):
        # Iterators are iterables too.
        # Adding this functions to make them so.
        return self

    def next(self):
        if self.id < self.nb_lanes:
            lane_ordinality = convert_python_id_to_lane_ordinality(self.id, self.nb_lanes)
            self.id += 1
            return lane_ordinality
        else:
            raise StopIteration


class trafipolluImp_TOPO_for_TRONCONS(object):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        """
        #
        self.__dict_symu_troncons = {}
        self.__dict_grouped_lanes = {}
        #
        self.__dict_sg3_to_symuvia = {}

        # from DUMP
        self.object_DUMP = kwargs.setdefault('object_DUMP', None)

    def clear(self):
        """

        :return:

        """
        self.__dict_symu_troncons = {}
        self.__dict_grouped_lanes = {}
        #
        self.__dict_sg3_to_symuvia = {}
        #
        self.object_DUMP = None

    def build_symutroncons(self, **kwargs):
        """

        :param dict_edges: dictionnaire contenant les edges SG3
         - key: edge id
         - values:
        :return:

        """
        dict_symutroncons = {}

        # on redefinie un lien vers le module DUMP si une instance est transmise en parametre (dict params)
        # sinon on utilise le module dump fournit a l'init
        self.object_DUMP = kwargs.setdefault('object_DUMP', self.object_DUMP)

        if self.object_DUMP:
            # construction des groupes lanes
            # logger.info('object_DUMP.dict_lanes: %s' % object_DUMP.dict_lanes)
            dict_grouped_lanes = self.__build_dict_grouped_lanes(self.object_DUMP.dict_lanes)
            # logger.info('dict_grouped_lanes: %s' % dict_grouped_lanes)

            # on parcourt l'ensemble des id des edges disponibles
            for edge_id, sg3_edge in self.object_DUMP.dict_edges.iteritems():
                group_lanes_for_edge = dict_grouped_lanes[edge_id]['grouped_lanes']
                # logger.info('group_lanes_for_edge: %s' % group_lanes_for_edge)
                dict_symutroncons.update(self.__build_symutroncons_from_sg3_edge(sg3_edge, group_lanes_for_edge))
            #
            if not kwargs.setdefault('is_static', False):
                self.__dict_symu_troncons.update(dict_symutroncons)
            # debug infos
            # logger.info('__dict_sg3_to_symuvia: %s' % str(self.__dict_sg3_to_symuvia))
            logger.info('%d (symu) troncons added' % len(dict_symutroncons.keys()))
        else:
            logger.fatal('Pas de DUMP disponible pour la construction de SYMUVIA troncons !')

        return dict_symutroncons

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
        dict_grouped_lanes = {}

        list_edges_counting_grouped_lanes = [
            [
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
                    symutroncon
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
        # on recupere les amont/aval et points internes du troncon construit a partir du groupes de voies
        results_compute_aapt = self.__compute_amont_aval_points_internes_from_sg3_lanes(*args)
        # logger.info('results_compute_aapt: %s' % results_compute_aapt)
        # construction de l'objet PYXB pour export Symuvia TRONCON
        pyxb_symutroncon = self.__build_pyxb_troncon(results_compute_aapt, *args)
        return pyxb_symutroncon

    def __build_pyxb_troncon(self, results_compute_aapt, *args):
        """

        :param results_compute_aapt:
        :param args:
        :return:

        """
        sg3_edge, sg3_edge_id, python_lane_id, nb_lanes_in_group = args

        # construction du nom LICIT pour le troncon (aide debug)
        nom_rue = self.__build_LICIT_name_for_edge(sg3_edge)
        # logger.info('nom_rue: %s' % nom_rue)

        # construction de l'object pyxb symtroncon
        pyxb_symutroncon = symuvia_parser.typeTroncon(
            id=self.__build_id_for_symutroncon(sg3_edge['ign_id'], python_lane_id),
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
        pyxb_symutroncon.POINTS_INTERNES = self.__build_pyxb_troncon_points_internes(results_compute_aapt)

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
            np_point_for_troncon = np.array((0, 0))
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
            sg3_lane_geometry = self.get_lane_geometry(sg3_edge_id, python_lane_id)
            # on la transforme en shapely geom
            shp_lane = LineString(sg3_lane_geometry)
            # on projete les points formant la voie sur son axe pour recuperer des coefficients 1D. Les coefficients
            # sont normes par la longueur de l'axe, donc les coefficients sont entre [0.0, 1.0])
            linestring_proj_1D_coefficients = [
                shp_lane.project(Point(point), normalized=True)
                for point in list(shp_lane.coords)
            ]
            # on sauvegarde la geometrie de la voie
            shp_lanes.append(shp_lane)
            # on sauvegarde les coefficients geometriques de la voie
            list_projected_coefficients += linestring_proj_1D_coefficients

        # ##########################
        # clean the list of 1D coefficients
        # remove duplicate values
        # url: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
        list_projected_coefficients = list(set(list_projected_coefficients))
        # sort the list of 1D coefficients
        list_projected_coefficients.sort()
        # ##########################

        # on retourne un tuple de resultats
        return shp_lanes, list_projected_coefficients

    def get_lane_geometry(self, sg3_edge_id, python_id_lane):
        """

        :param sg3_edge:
        :param python_id_lane:
        :param nb_lanes:
        :return:

        """
        nb_lanes = self.object_DUMP.get_lane_number(sg3_edge_id)
        # on convertie le python id lane par rapport a l'edge SG3 en lane ordinality
        lane_ordinality = convert_python_id_to_lane_ordinality(python_id_lane, nb_lanes)
        # on recupere depuis le DUMP l'information de geometrie associee a la voie SG3
        return self.object_DUMP.get_lane_geometry(sg3_edge_id, lane_ordinality)

    @staticmethod
    def __build_id_for_symutroncon(str_pyxb_symutroncon_id, lane_id):
        """

        :param pyxb_symuTRONCON:
        :param lane_id:
        :return:
        """
        return str_pyxb_symutroncon_id + '_lane_' + str(lane_id)

    @staticmethod
    def __build_LICIT_name_for_edge(sg3_edge):
        # mise a jour des champs (debug LICIT)
        nom_rue_g = sg3_edge['nom_rue_g']
        nom_rue_d = sg3_edge['nom_rue_d']
        nom_rue = nom_rue_g
        if nom_rue_g != nom_rue_d:
            nom_rue += '-_-' + nom_rue_d
        return nom_rue

    @staticmethod
    def __optimize_list_points(
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
        pyxb_symutroncon_points_internes = None

        list_points = results_compute_aapt.points_internes
        # transfert des POINTS_INTERNES
        if list_points:
            if b_use_simplification_for_points_internes_troncon:
                list_points = trafipolluImp_TOPO_for_TRONCONS.__optimize_list_points(list_points, 2.0, 0.10)
            pyxb_symutroncon_points_internes = symuvia_parser.typePointsInternes()
            [pyxb_symutroncon_points_internes.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]

        return pyxb_symutroncon_points_internes

    def __build_links_sg3_symuvia(
            self,
            sg3_edge_id,
            start_python_lane_id,
            nb_lanes_in_group,
            pyxb_symutroncon
    ):
        """

        :param sg3_edge_id:
        :param start_python_lane_id:
        :param nb_lanes:
        :param pyxb_symutroncon:
        :return:

        """
        nb_lanes = self.object_DUMP.get_lane_number(sg3_edge_id)
        lane_ordinality = convert_python_id_to_lane_ordinality(start_python_lane_id, nb_lanes)
        lane_direction = self.object_DUMP.get_lane_direction(sg3_edge_id, lane_ordinality)
        range_python_lanes_id = range(start_python_lane_id, start_python_lane_id + nb_lanes_in_group)

        # SG3 order (lane_ordinality)
        self.__dict_sg3_to_symuvia[sg3_edge_id] = [None] * (nb_lanes + 1)

        # on recupere les indices des voies du groupe (Python order)
        for python_lane_id in range_python_lanes_id:
            # on convertie le python id de la voie en SG3 lane ordinality (SG3 order)
            sg3_lane_ordinality = convert_python_id_to_lane_ordinality(python_lane_id, nb_lanes)
            # on convertie le python id de la voie en numero de voie (SYMUVIA order)
            symuvia_lane_id = convert_lane_python_id_to_lane_symuvia_id(
                python_lane_id,
                start_python_lane_id,
                nb_lanes_in_group,
                lane_direction
            )
            # on construit le tuple representant la voie SYMUVIA : (symutroncon, id de la voie (SYMUVIA order))
            lane_symuvia = NT_LANE_SYMUVIA(pyxb_symutroncon, symuvia_lane_id)
            # on enregistre le lien topologique entre la voie SG3 -> SYMUVIA
            self.__dict_sg3_to_symuvia[sg3_edge_id][sg3_lane_ordinality] = lane_symuvia


class trafipolluImp_TOPO_for_INTERCONNEXIONS(object):
    """

    """
    pass


class trafipolluImp_TOPO_for_EXTREMITES(object):
    """

    """
    pass


    # class trafipolluImp_TOPO(object):
    # """
    #
    #     """
    #
    #     def __init__(self, **kwargs):
    #         """
    #
    #         """
    #         self.dict_edges = kwargs['dict_edges']
    #         self.dict_nodes = kwargs['dict_nodes']
    #         self.dict_lanes = kwargs['dict_lanes']
    #         #
    #         self.dict_pyxb_symutroncons = {}
    #         #
    #         self.dict_extremites = {
    #             'ENTREES': [],
    #             'SORTIES': [],
    #         }
    #
    #     def clear(self):
    #         """
    #
    #         :return:
    #
    #         """
    #         self.dict_pyxb_symutroncons = {}
    #         #
    #         self.dict_extremites = {
    #             'ENTREES': [],
    #             'SORTIES': [],
    #         }
    #
    #     @timerDecorator()
    #     def build_topo(self):
    #         """
    #
    #         :return:
    #
    #         """
    #         self.convert_sg3_edges_to_pyxb_symutroncons()
    #         self.build_topo_for_interconnexions()
    #         self.build_topo_extrimites()
    #
    #     @timerDecorator()
    #     def convert_sg3_edges_to_pyxb_symutroncons(self):
    #         """
    #
    #         :return:
    #
    #         """
    #         # self.dict_edges: clee sur les id des edges
    #         # on parcourt l'ensemble des id des edges disponibles
    #         for sg3_edge_id in self.dict_edges:
    #             self.dict_pyxb_symutroncons.update(self.build_pyxb_symutroncon_from_sg3_edge(sg3_edge_id))
    #
    #         logger.info(
    #             'convert_sg3_edges_to_pyxb_symutroncons - %d troncons added' %
    #             len(self.dict_pyxb_symutroncons.keys())
    #         )
    #         #
    #
    #     @staticmethod
    #     def update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTroncon, sg3_edge):
    #         """
    #         Update de liste_troncon:
    #             liste_troncon est le resultat de la fonction donc elle insere ou non des troncons dans le systeme
    #             L'update regarde si le troncon n'a pas deja ete calculee (prealablement)
    #             si oui: on met a jour les donnees sans rajouter un nouvel object (nouvelle adresse memoire)
    #             si non: on rajoute l'object (sym_TRONCON) dans la liste (instance de l'object)
    #             L'update permet de garder une coherence avec les liens topologiques calcules pour les nodes/CAF
    #             ps: a revoir, une forte impression que c'est tres foireux (meme si impression de deja vu dans les
    #             codes transmis par LICIT)
    #         """
    #         try:
    #             list_pyxb_symuTRONCONS = filter(lambda x: x.id == pyxb_symuTroncon.id, sg3_edge['sg3_to_symuvia'])
    #         except:
    #             # la cle 'sg3_to_symuvia' n'existe pas donc on est dans l'init (premiere passe)
    #             dict_pyxb_symuTroncons[pyxb_symuTroncon.id] = pyxb_symuTroncon
    #         else:
    #             if list_pyxb_symuTRONCONS:
    #                 # le troncon est deja present
    #                 # TODO: il faudrait (plutot) updater le TRONCON (au lieu de le remplacer)
    #                 pyxb_symuTroncon = list_pyxb_symuTRONCONS[0]
    #             #
    #             dict_pyxb_symuTroncons[pyxb_symuTroncon.id] = pyxb_symuTroncon
    #
    #     def _build_pyxb_symutroncon_from_sg3_edge_lane(self, *args):
    #         """
    #
    #         :return:
    #
    #         """
    #         try:
    #             sg3_edge, sg3_edge_id, python_lane_id, nb_lanes, func_build_pyxb_symutroncon = args
    #             # Construction TOPO d'un symu TRONCON
    #             result_build = func_build_pyxb_symutroncon(
    #                 sg3_edge=sg3_edge,
    #                 sg3_edge_id=sg3_edge_id,
    #                 python_lane_id=python_lane_id,
    #                 nb_lanes=nb_lanes
    #             )
    #             # mise a jour des champs (debug LICIT)
    #             nom_rue_g = sg3_edge['nom_rue_g']
    #             nom_rue_d = sg3_edge['nom_rue_d']
    #             nom_rue = nom_rue_g
    #             if nom_rue_g != nom_rue_d:
    #                 nom_rue += '-_-' + nom_rue_d
    #             # construction de l'objet PYXB pour export Symuvia TRONCON
    #             pyxb_symuTRONCON = symuvia_parser.typeTroncon(
    #                 id=self.build_id_for_TRONCON(sg3_edge['ign_id'], python_lane_id),
    #                 nom_axe=nom_rue,
    #                 largeur_voie=sg3_edge['road_width'] / sg3_edge['lane_number'],
    #                 id_eltamont="-1",
    #                 id_eltaval="-1",
    #                 extremite_amont=result_build.amont,
    #                 extremite_aval=result_build.aval,
    #                 nb_voie=nb_lanes
    #             )
    #
    #             # if result_build.points_internes:
    #             # transfert des POINTS_INTERNES
    #             if b_add_points_internes_troncons:
    #                 points_internes = result_build.points_internes
    #                 if points_internes:
    #                     if b_use_simplification_for_points_internes_troncon:
    #                         points_internes = self.optimize_list_points(result_build.points_internes, 2.0, 0.10)
    #                     pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(points_internes)
    #
    #             # MOG : probleme autour des sens edge, lanes, symuvia
    #             # lane_direction = self.dict_lanes[sg3_edge_id]['informations'][python_lane_id].lane_direction
    #             lane_direction = module_DUMP.get_lane_direction_from_python_lane_id(self.dict_lanes, sg3_edge_id,
    #                                                                              python_lane_id)
    #
    #             # LINK STREETGEN3 to SYMUVIA (TOPO)
    #             self.build_link_from_sg3_to_symuvia_for_lane(
    #                 pyxb_symuTRONCON,
    #                 sg3_edge_id,
    #                 python_lane_id,
    #                 nb_lanes,
    #                 lane_direction
    #             )
    #
    #         except Exception, e:
    #             logger.fatal('_build_pyxb_symutroncon_from_sg3_edge_lane - Exception: ' % e)
    #         else:
    #             return pyxb_symuTRONCON
    #
    #     def build_pyxb_symutroncon_from_sg3_edge(self, sg3_edge_id):
    #         """
    #
    #         :param sg3_edge_id:
    #         :return:
    #         """
    #
    #         dict_pyxb_symuTroncons = {}
    #
    #         sg3_edge = self.dict_edges[sg3_edge_id]
    #
    #         try:
    #             grouped_lanes = sg3_edge['grouped_lanes']
    #         except:
    #             # Il y a des edge_sg3 sans voie(s) dans le reseau SG3 ... faudrait demander a Remi !
    #             # Peut etre des edges_sg3 aidant uniquement aux connexions/creation (de zones) d'intersections
    #             logger.fatal("!!! 'BUG' with edge id: ", sg3_edge_id, " - no 'group_lanes' found !!!")
    #         else:
    #             python_lane_id = 0
    #             try:
    #                 for nb_lanes_in_group in grouped_lanes:
    #                     pyxb_symuTRONCON = self._build_pyxb_symutroncon_from_sg3_edge_lane(
    #                         sg3_edge, sg3_edge_id, python_lane_id, nb_lanes_in_group,
    #                         self.build_pyxb_symuTroncon_with_lanes_in_groups
    #                     )
    #                     # Update list_troncon
    #                     self.update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTRONCON, sg3_edge)
    #                     # next lanes group
    #                     python_lane_id += nb_lanes_in_group
    #             except Exception, e:
    #                 logger.fatal('Exception: %s' % e)
    #         finally:
    #             return dict_pyxb_symuTroncons
    #
    #     def build_link_from_sg3_to_symuvia_for_lane(
    #             self,
    #             pyxb_symuTRONCON,
    #             sg3_edge_id,
    #             python_lane_id,
    #             nb_lanes,
    #             lane_direction
    #     ):
    #         """
    #
    #         :param pyxb_symuTRONCON:
    #         :param lane_direction:
    #         :param sg3_edge_id:
    #         :param python_lane_id:
    #         :param nb_lanes:
    #         :return:
    #
    #         """
    #         symu_lanes = module_DUMP.get_Symuvia_list_lanes_from_edge_id(self.dict_lanes, sg3_edge_id)
    #
    #         for python_id in range(python_lane_id, python_lane_id + nb_lanes):
    #             symu_lanes[python_id] = NT_LANE_SG3_SYMU(
    #                 pyxb_symuTRONCON,
    #                 python_lane_id,
    #                 nb_lanes,
    #                 lane_direction
    #             )
    #
    #     def build_pyxb_symuTroncon_with_lanes_in_groups(self, **kwargs):
    #         """
    #         1 Groupe de plusieurs voies (dans la meme direction) dans une serie de groupes (de voies) pour l'edge_sg3
    #         On recupere les coefficients 1D de projection de chaque point sur sa voie.
    #         On rassemble tout ces coefficients et re-echantillone les voies (nombres de points d'echantillon homogene entre
    #          chaque voie). On moyenne tous les points de chaque voie pour former un axe (edge) mediant.
    #
    #         :return:
    #
    #         """
    #         sg3_edge_id = kwargs['sg3_edge_id']
    #         python_lane_id = kwargs['python_lane_id']
    #         nb_lanes = kwargs['nb_lanes']
    #         #
    #         shp_lanes = []
    #         # transfert lane_center_axis for each lane in 2D
    #         list_1D_coefficients = []
    #         # on parcourt le groupe de 'voies' dans le meme sens
    #         try:
    #             for id_lane in range(python_lane_id, python_lane_id + nb_lanes):
    #                 # get the linestring of the current lane
    #                 sg3_lane_geometry = module_DUMP.get_lane_geometry_from_python_lane_id(
    #                     self.dict_lanes,
    #                     sg3_edge_id,
    #                     id_lane
    #                 )
    #                 shp_lane = LineString(sg3_lane_geometry)
    #                 # project this linestring into 1D coefficients
    #                 linestring_proj_1D_coefficients = [
    #                     shp_lane.project(Point(point), normalized=True)
    #                     for point in list(shp_lane.coords)
    #                 ]
    #                 # save the geometry lane
    #                 shp_lanes.append(shp_lane)
    #                 # save the 1D coefficients from the lane
    #                 list_1D_coefficients += linestring_proj_1D_coefficients
    #         except Exception, e:
    #             logger.fatal('Exception: %s' % e)
    #
    #         # ##########################
    #         # clean the list of 1D coefficients
    #         # remove duplicate values
    #         # url: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
    #         list_1D_coefficients = list(set(list_1D_coefficients))
    #         # sort the list of 1D coefficients
    #         list_1D_coefficients.sort()
    #         # ##########################
    #
    #         # Compute the troncon center axis
    #         # Methode: on utilise les coefficients 1D de chaque voie qui va composer ce troncon.
    #         # On retroprojete chaque coeffient (1D) sur l'ensemble des voies (2D) et on effectue la moyenne des positions
    #         # On recupere 'une sorte d'axe median' des voies (du meme groupe)
    #         #
    #         lane_geometry = []
    #         try:
    #             # coefficient de normalisation depend du nombre de voies qu'on utilise pour la moyenne
    #             norm_lanes_center_axis = 1.0 / len(shp_lanes)
    #             # pour chaque coefficient 1D
    #             for coef_point in list_1D_coefficients:
    #                 # on calcule la moyenne des points sur les lanes pour ce coefficient
    #                 np_point_for_troncon = np.array(Point(0, 0).coords[0])
    #                 # pour chaque shapely lane
    #                 for shp_lane in shp_lanes:
    #                     projected_point_on_lane = np.array((shp_lane.interpolate(coef_point, normalized=True)).coords[0])
    #                     # on projete le coefficient et on somme le point
    #                     np_point_for_troncon += projected_point_on_lane
    #                 # on calcule la moyenne
    #                 np_point_for_troncon *= norm_lanes_center_axis
    #                 lane_geometry.append(list(np_point_for_troncon))
    #         except Exception, e:
    #             logger.fatal('Exception: %s' % e)
    #         else:
    #             id_vertice_for_amont, id_vertice_for_aval = 0, -1
    #
    #             # Comme la liste des coefficients 1D est triee,
    #             # on peut declarer le 1er et dernier point comme Amont/Aval
    #             return NT_RESULT_BUILD_PYXB(
    #                 lane_geometry[id_vertice_for_amont],
    #                 lane_geometry[id_vertice_for_aval],
    #                 lane_geometry
    #             )
    #
    #     @staticmethod
    #     def update_pyxb_node(node, **kwargs):
    #         """
    #
    #         :param kwargs:
    #         :return:
    #         """
    #         for k, v in kwargs.iteritems():
    #             node._setAttribute(k, v)
    #
    #     def build_pyxb_symuTroncon_with_lane_in_groups(self, **kwargs):
    #         """
    #         1 voie dans une serie de groupe.
    #         Cas le plus simple, on recupere les informations directement de la voie_sg3 (correspondance directe)
    #         Note: Faudrait voir pour un generateur d'id pour les nouveaux troncons_symu
    #
    #         :return:
    #
    #         """
    #         sg3_edge_id = kwargs['sg3_edge_id']
    #         python_lane_id = kwargs['python_lane_id']
    #         #
    #         try:
    #             sg3_lane = module_DUMP.get_lane_from_python_lane_id(self.dict_lanes, sg3_edge_id, python_lane_id)
    #
    #             try:
    #                 lane_geometry = sg3_lane.lane_center_axis
    #                 lane_points_internes = lane_geometry[1:-1]  # du 2nd a l'avant dernier point
    #
    #                 id_vertice_for_amont, id_vertice_for_aval = 0, -1
    #
    #                 return NT_RESULT_BUILD_PYXB(
    #                     lane_geometry[id_vertice_for_amont],
    #                     lane_geometry[id_vertice_for_aval],
    #                     lane_points_internes
    #                 )
    #             except Exception, e:
    #                 logger.fatal('Exception: %s' % e)
    #         except Exception, e:
    #             logger.fatal('Exception: %s' % e)
    #
    #     @staticmethod
    #     def build_id_for_TRONCON(str_pyxb_symutroncon_id, lane_id):
    #         """
    #
    #         :param pyxb_symuTRONCON:
    #         :param lane_id:
    #         :return:
    #         """
    #         return str_pyxb_symutroncon_id + '_lane_' + str(lane_id)
    #
    #     @staticmethod
    #     def build_pyxb_POINTS_INTERNES(list_points):
    #         """
    #
    #         :param :
    #         :return:
    #
    #         """
    #         pyxb_symuPOINTS_INTERNES = symuvia_parser.typePointsInternes()
    #
    #         [pyxb_symuPOINTS_INTERNES.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
    #         return pyxb_symuPOINTS_INTERNES
    #
    #     @staticmethod
    #     def simplify_list_points(
    #             list_points,
    #             tolerance_distance=0.10
    #     ):
    #         """
    #
    #         :param list_points: list des points a simplfier.
    #                 -> A priori cette liste provient d'une interconnexion SG3
    #                 donc elle possede (normalement) au moins 4 points (amont 2 points internes aval)
    #         :param tolerance_distance:
    #         :return:
    #
    #         """
    #         shp_list_points = LineString(list_points)
    #         shp_simplify_list_points = shp_list_points.simplify(tolerance_distance, preserve_topology=False)
    #         return np.asarray(shp_simplify_list_points)
    #
    #     @staticmethod
    #     def optimize_list_points(
    #             list_points,
    #             min_distance=0.60,
    #             tolerance_distance=0.10,
    #             epsilon=0.05
    #     ):
    #         """
    #
    #         :return:
    #
    #         """
    #         min_distance += epsilon
    #         shp_list_points_optimized = []
    #
    #         try:
    #             shp_list_points = LineString(list_points)
    #             # resampling
    #             list_shp_points_resampled = [
    #                 shp_list_points.interpolate(distance)
    #                 for distance in np.arange(min_distance,
    #                                           shp_list_points.length - min_distance,
    #                                           min_distance)
    #             ]
    #             list_shp_points = list_shp_points_resampled
    #         # except Exception, e:
    #         # logger.fatal('Exception: %s' % e)
    #         except:
    #             pass
    #         else:
    #             try:
    #                 resample_shp_geometry = LineString(list_shp_points)
    #                 shp_list_points_optimized = resample_shp_geometry.simplify(
    #                     tolerance_distance,
    #                     preserve_topology=False
    #                 )
    #             # except Exception, e:
    #             # logger.fatal('Exception: %s' % e)
    #             except:
    #                 pass
    #         finally:
    #             return np.array(shp_list_points_optimized)
    #
    #     @timerDecorator()
    #     def build_topo_for_interconnexions(self):
    #         """
    #
    #         """
    #         list_remove_nodes = []
    #         dict_interconnexions = {}
    #
    #         id_amont, id_aval = interval_ids_amont_aval = range(2)
    #
    #         # pour chaque node SG3
    #         for node_id, dict_values in self.dict_nodes.iteritems():
    #             try:
    #                 node_list_interconnexions = dict_values['interconnexions']
    #                 set_id_edges = dict_values['set_id_edges']
    #             except Exception, e:
    #                 logger.fatal('build_topo_for_interconnexions - Exception: %s' % e)
    #                 logger.fatal('\tnode_id: %s' % node_id)
    #                 logger.fatal("\tdict_node[%s]: %s" % (node_id, dict_values))
    #                 #
    #                 list_remove_nodes.append(node_id)
    #             else:
    #                 #
    #                 str_type_connexion = ''
    #                 nb_edges_connected_on_this_node = len(set_id_edges)
    #                 if nb_edges_connected_on_this_node == 2:
    #                     str_type_connexion = 'REPARTITEUR'
    #                 elif nb_edges_connected_on_this_node > 2:
    #                     # potentiellement un CAF
    #                     str_type_connexion = 'CAF'
    #
    #                 # pour chaque interconnexion
    #                 for interconnexion in node_list_interconnexions:
    #                     symu_troncons = []
    #                     symu_troncons_lane_id = []
    #
    #                     # parcours sur les elements interconnectes (connexion amont -> aval)
    #                     for python_id in interval_ids_amont_aval:
    #                         str_sg3_id = str(python_id + 1)
    #                         #
    #                         sg3_edge_id = interconnexion['edge_id' + str_sg3_id]
    #                         sg3_lane_ordinality = interconnexion['lane_ordinality' + str_sg3_id]
    #                         try:
    #                             symu_lane, symu_lane_id = self.find_symu_troncon_lane(
    #                                 sg3_edge_id,
    #                                 sg3_lane_ordinality
    #                             )
    #                         except Exception, e:
    #                             logger.fatal('# Find Symu_Troncon - EXCEPTION: %s' % e)
    #                         else:
    #                             #
    #                             symu_troncons.append(symu_lane.symu_troncon)
    #                             symu_troncons_lane_id.append(symu_lane_id)
    #
    #                     if len(symu_troncons) == 2:
    #                         dict_interconnexions.setdefault(node_id, {
    #                             'sg3_to_symuvia': {
    #                                 'type_connexion': str_type_connexion,
    #                                 'list_interconnexions': {}
    #                             }
    #                         }
    #                         )
    #
    #                         # #################################################
    #                         # SIMPLIFICATION DES VOIES D'INTERCONNEXIONS
    #                         # #################################################
    #                         if b_use_simplification_for_points_internes_interconnexion:
    #                             # permet de simplifier les lignes droites et eviter d'exporter un noeud 'POINTS_INTERNES'
    #                             # inutile dans ce cas pour SYMUVIA
    #                             sg3_interconnexion_geometry = self.simplify_list_points(
    #                                 interconnexion['np_interconnexion'],
    #                                 0.10
    #                             )[1:-1]  # les 1er et dernier points sont les amont/aval de l'interconnexion/troncons
    #                         else:
    #                             sg3_interconnexion_geometry = interconnexion['np_interconnexion']
    #                         ##################################################
    #
    #                         #
    #                         list_interconnexions = dict_interconnexions[node_id]['sg3_to_symuvia']['list_interconnexions']
    #
    #                         # build key with id symu_troncon and the id lane
    #                         key_for_interconnexion = self.build_id_for_interconnexion(
    #                             symu_troncons,
    #                             symu_troncons_lane_id,
    #                             id_amont
    #                         )
    #
    #                         list_interconnexions.setdefault(key_for_interconnexion, []).append(
    #                             NT_INTERCONNEXION(
    #                                 lane_amont=NT_LANE_SYMU(symu_troncons[id_amont], symu_troncons_lane_id[id_amont]),
    #                                 lane_aval=NT_LANE_SYMU(symu_troncons[id_aval], symu_troncons_lane_id[id_aval]),
    #                                 geometry=sg3_interconnexion_geometry
    #                             )
    #                         )
    #
    #                         # TODO -> [TOPO] : FAKE TOPO pour CONNEXIONS/EXTREMITES
    #                         symu_troncons[id_amont].id_eltaval = symu_troncons[id_aval].id
    #                         symu_troncons[id_aval].id_eltamont = symu_troncons[id_amont].id
    #
    #                 # si il n'y a aucune interconnexion associee au node
    #                 if not dict_interconnexions[node_id]['sg3_to_symuvia']['list_interconnexions']:
    #                     # alors on retire le node de la liste des nodes (utiles pour l'export SYMUVIA)
    #                     list_remove_nodes.append(node_id)
    #
    #         for id_node_to_remove in list_remove_nodes:
    #             self.dict_nodes.pop(id_node_to_remove)
    #
    #         self.dict_nodes.update(dict_interconnexions)
    #
    #         if list_remove_nodes:
    #             logger.info('# build_topo_for_nodes - nb nodes_removed: %d' % len(list_remove_nodes))
    #
    #
    #     def find_symu_troncon_lane(
    #             self,
    #             sg3_edge_id,
    #             sg3_lane_ordinality
    #     ):
    #         """
    #
    #
    #         :param sg3_lane_ordinality:
    #         :param dict_lanes:
    #         :param sg3_edge_id:
    #         :return:
    #
    #         """
    #         python_lane_id = module_DUMP.get_python_id_from_lane_ordinality(
    #             self.dict_lanes,
    #             sg3_edge_id,
    #             sg3_lane_ordinality
    #         )
    #
    #         symu_lane = module_DUMP.get_symu_troncon_from_python_id(
    #             self.dict_lanes,
    #             sg3_edge_id,
    #             python_lane_id
    #         )
    #
    #         symu_lane_id = python_lane_id - symu_lane.start_id_lane
    #
    #         # #######################################################################
    #         # Conversion SG3/Python -> SYMUVIA
    #         # On doit prendre en compte l'orientation de la lane par rapport a l'edge
    #         # #######################################################################
    #         if symu_lane.lane_direction:
    #             symu_lane_id = (symu_lane.nb_lanes - 1) - symu_lane_id
    #         # #######################################################################
    #
    #         return symu_lane, symu_lane_id
    #
    #     @timerDecorator()
    #     def build_topo_extrimites(self):
    #         """
    #
    #         :return:
    #         """
    #         try:
    #             for symu_troncon in self.dict_pyxb_symutroncons.values():
    #                 # AVAL -> SORTIE
    #                 b_aval_not_connected = symu_troncon.id_eltaval == "-1"
    #                 if b_aval_not_connected:
    #                     id_for_extrimite = self.build_id_for_extremite(symu_troncon, 'S_')
    #                     self.dict_extremites['SORTIES'].append(id_for_extrimite)
    #                     # update troncon id for aval
    #                     # TOPO : Link between TRONCON and EXTREMITE
    #                     symu_troncon.id_eltaval = id_for_extrimite
    #                 # AMONtT -> ENTREE
    #                 b_amont_not_connected = symu_troncon.id_eltamont == "-1"
    #                 if b_amont_not_connected:
    #                     id_for_extrimite = self.build_id_for_extremite(symu_troncon, 'E_')
    #                     self.dict_extremites['ENTREES'].append(id_for_extrimite)
    #                     # update troncon id for aval
    #                     # TOPO : Link between TRONCON and EXTREMITE
    #                     symu_troncon.id_eltamont = id_for_extrimite
    #         except Exception, e:
    #             logger.fatal('Exception: %s' % e)
    #
    #     @staticmethod
    #     def build_id_for_extremite(symu_troncon, prefix=""):
    #         """
    #
    #         :param symu_troncon:
    #         :param prefix:
    #         :return:
    #
    #         """
    #         return prefix + symu_troncon.id
    #
    #     @staticmethod
    #     def build_id_for_interconnexion(
    #             symu_troncons,
    #             symu_troncons_lane_id,
    #             id_amont
    #     ):
    #         """
    #
    #         :param symu_troncons:
    #         :param symu_troncons_lane_id:
    #         :param id_amont:
    #         :return:
    #         """
    #         return symu_troncons[id_amont].id + '_' + str(symu_troncons_lane_id[id_amont])