__author__ = 'latty'

import numpy as np

from shapely.geometry import Point, LineString
import pyxb

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import CreateNamedTupleOnGlobals
from imt_tools import CreateNamedTuple
from imt_tools import timerDecorator


NT_LANE_SG3_SYMU = CreateNamedTupleOnGlobals(
    'NT_LANE_SG3_SYMU',
    [
        'symu_troncon',
        'start_id_lane',
        'nb_lanes'
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

NT_LANE_SYMU = CreateNamedTupleOnGlobals(
    'NT_LANE_SYMU',
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


class trafipolluImp_TOPO(object):
    """

    """

    def __init__(self, dict_edges, dict_lanes, dict_nodes):
        """

        """
        self.dict_edges = dict_edges
        self.dict_lanes = dict_lanes
        self.dict_nodes = dict_nodes
        #
        self.dict_pyxb_symutroncons = {}
        #
        self.dict_extremites = {
            'ENTREES': [],
            'SORTIES': [],
        }
        #

    def clear(self):
        """

        :return:
        """
        self.dict_pyxb_symutroncons = {}

    @timerDecorator()
    def build_topo(self):
        """

        :return:
        """
        self.convert_sg3_edges_to_pyxb_symutroncons()
        self.build_topo_for_interconnexions()
        #
        self.build_topo_extrimites()

    @timerDecorator()
    def convert_sg3_edges_to_pyxb_symutroncons(self):
        """

        :return:

        """
        # self.dict_edges: clee sur les id des edges
        # on parcourt l'ensemble des id des edges disponibles
        for sg3_edge_id in self.dict_edges:
            self.dict_pyxb_symutroncons.update(self.build_pyxb_symutroncon_from_sg3_edge(sg3_edge_id))

        print 'convert_sg3_edges_to_pyxb_symutroncons - %d troncons added' % len(self.dict_pyxb_symutroncons.keys())
        #

    @staticmethod
    def update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTroncon, sg3_edge):
        """
        Update de liste_troncon:
            liste_troncon est le resultat de la fonction donc elle insere ou non des troncons dans le systeme
            L'update regarde si le troncon n'a pas deja ete calculee (prealablement)
            si oui: on met a jour les donnees sans rajouter un nouvel object (nouvelle adresse memoire)
            si non: on rajoute l'object (sym_TRONCON) dans la liste (instance de l'object)
            L'update permet de garder une coherence avec les liens topologiques calcules pour les nodes/CAF
            ps: a revoir, une forte impression que c'est tres foireux (meme si impression de deja vu dans les
            codes transmis par LICIT)
        """
        try:
            list_pyxb_symuTRONCONS = filter(lambda x: x.id == pyxb_symuTroncon.id, sg3_edge['sg3_to_symuvia'])
        except:
            # la cle 'sg3_to_symuvia' n'existe pas donc on est dans l'init (premiere passe)
            dict_pyxb_symuTroncons[pyxb_symuTroncon.id] = pyxb_symuTroncon
        else:
            if list_pyxb_symuTRONCONS:
                # le troncon est deja present
                # TODO: il faudrait (plutot) updater le TRONCON (au lieu de le remplacer)
                pyxb_symuTroncon = list_pyxb_symuTRONCONS[0]
            #
            dict_pyxb_symuTroncons[pyxb_symuTroncon.id] = pyxb_symuTroncon

    def _build_pyxb_symutroncon_from_sg3_edge_lane(self, *args):
        """

        :return:

        """
        try:
            sg3_edge, sg3_edge_id, sg3_lane_id, nb_lanes, func_build_pyxb_symutroncon = args
            # update list TRONCONS
            result_build = func_build_pyxb_symutroncon(
                sg3_edge=sg3_edge,
                sg3_edge_id=sg3_edge_id,
                sg3_lane_id=sg3_lane_id,
                nb_lanes=nb_lanes
            )
            #
            pyxb_symuTRONCON = symuvia_parser.typeTroncon(
                id=self.build_id_for_TRONCON(sg3_edge['str_ign_id'], sg3_lane_id),
                largeur_voie=sg3_edge['f_road_width'] / sg3_edge['ui_lane_number'],
                id_eltamont="-1",
                id_eltaval="-1",
                extremite_amont=result_build.amont,
                extremite_aval=result_build.aval,
                nb_voie=nb_lanes
            )

            # if result_build.points_internes:
            # transfert des POINTS_INTERNES
            pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(result_build.points_internes)

            # LINK STREETGEN3 to SYMUVIA (TOPO)
            self.build_link_from_sg3_to_symuvia_for_lane(pyxb_symuTRONCON, sg3_edge_id, sg3_lane_id, nb_lanes)
        except Exception, e:
            print '_build_pyxb_symutroncon_from_sg3_edge_lane - Exception: ', e
        else:
            return pyxb_symuTRONCON

    def build_pyxb_symutroncon_from_sg3_edge(self, sg3_edge_id):
        """

        :param sg3_edge_id:
        :return:
        """

        dict_pyxb_symuTroncons = {}

        sg3_edge = self.dict_edges[sg3_edge_id]

        try:
            grouped_lanes = sg3_edge['grouped_lanes']
        except:
            # Il y a des edge_sg3 sans voie(s) dans le reseau SG3 ... faudrait demander a Remi !
            # Peut etre des edges_sg3 aidant uniquement aux connexions/creation (de zones) d'intersections
            print ""
            print "!!! 'BUG' with edge id: ", sg3_edge_id, " - no 'group_lanes' found !!!"
            print ""
        else:
            #
            list_functions_for_building_pyxb_symuTroncon = (
                self.build_pyxb_symuTroncon_with_lanes_in_one_group,
                self.build_pyxb_symuTroncon_with_lane_in_groups,
                self.build_pyxb_symuTroncon_with_lanes_in_groups,
            )
            b_several_groups = len(grouped_lanes) > 1
            sg3_lane_id = 0
            try:
                for nb_lanes in grouped_lanes:
                    #
                    id_function = b_several_groups + (b_several_groups & (nb_lanes > 1))
                    #
                    pyxb_symuTRONCON = self._build_pyxb_symutroncon_from_sg3_edge_lane(
                        sg3_edge, sg3_edge_id, sg3_lane_id, nb_lanes,
                        list_functions_for_building_pyxb_symuTroncon[id_function]
                    )
                    # Update list_troncon
                    self.update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTRONCON, sg3_edge)
                    # next lanes group
                    sg3_lane_id += nb_lanes
            except Exception, e:
                print 'Exception, e: ', e
        finally:
            return dict_pyxb_symuTroncons

    def build_link_from_sg3_to_symuvia_for_lane(self, pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes):
        """

        :param sg3_edge_id:
        :param cur_id_lane:
        :param nb_lanes:
        :return:
        """
        # LINK STREETGEN3 to SYMUVIA (TOPO)
        symu_lanes = self.dict_lanes[sg3_edge_id]['sg3_to_symuvia']
        for id_lane in range(cur_id_lane, cur_id_lane + nb_lanes):
            symu_lanes[id_lane] = NT_LANE_SG3_SYMU(pyxb_symuTRONCON, cur_id_lane, nb_lanes)

    def build_pyxb_symuTroncon_with_lanes_in_groups(self, **kwargs):
        """
        1 Groupe de plusieurs voies (dans la meme direction) dans une serie de groupes (de voies) pour l'edge_sg3
        On recupere les coefficients 1D de projection de chaque point sur sa voie.
        On rassemble tout ces coefficients et re-echantillone les voies (nombres de points d'echantillon homogene entre
         chaque voie). On moyenne tous les points de chaque voie pour former un axe edge mediant.

        :return:

        """
        # print '### build_pyxb_symuTroncon_with_lanes_in_groups ...'
        #
        sg3_edge_id = kwargs['sg3_edge_id']
        cur_id_lane = kwargs['sg3_lane_id']
        nb_lanes = kwargs['nb_lanes']
        #
        shp_lanes = []
        # transfert lane_center_axis for each lane in 2D
        list_1D_coefficients = []
        # on parcourt le groupe de 'voies' dans le meme sens
        try:
            for id_lane in range(cur_id_lane, cur_id_lane + nb_lanes):
                # get the linestring of the current lane
                sg3_lane_geometry = self.dict_lanes[sg3_edge_id]['informations'][id_lane].lane_center_axis
                shp_lane = LineString(sg3_lane_geometry)
                # project this linestring into 1D coefficients
                linestring_proj_1D_coefficients = [
                    shp_lane.project(Point(point), normalized=True)
                    for point in list(shp_lane.coords)
                ]
                # save the geometry lane
                shp_lanes.append(shp_lane)
                # save the 1D coefficients from the lane
                list_1D_coefficients += linestring_proj_1D_coefficients

                # print ''
                # print('id_lane: {}\n'
                # '- sg3_lane: {}\n'
                # '- shp_lane: {}\n'
                #       '- linestring_proj_1D_coefficients: {}\n').format(id_lane, sg3_lane, shp_lane.wkt,
                #                                                         linestring_proj_1D_coefficients)
        except Exception, e:
            print 'Exception: ', e

        # ##########################
        # clean the list of 1D coefficients
        # remove duplicate values
        # url: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
        list_1D_coefficients = list(set(list_1D_coefficients))
        # sort the list of 1D coefficients
        list_1D_coefficients.sort()
        # print '-> after set & sort - list_1D_coefficients: {}'.format(list_1D_coefficients)
        # ##########################

        # Compute the troncon center axis
        # Methode: on utilise les coefficients 1D de chaque voie qui va composer ce troncon.
        # On retroprojete chaque coeffient (1D) sur l'ensemble des voies (2D) et on effectue la moyenne des positions
        # On recupere 'une sorte d'axe median' des voies (du meme groupe)
        #
        lane_geometry = []
        try:
            # coefficient de normalisation depend du nombre de voies qu'on utilise pour la moyenne
            norm_lanes_center_axis = 1.0 / len(shp_lanes)
            # pour chaque coefficient 1D
            for coef_point in list_1D_coefficients:
                # on calcule la moyenne des points sur les lanes pour ce coefficient
                np_point_for_troncon = np.array(Point(0, 0).coords[0])
                # pour chaque shapely lane
                for shp_lane in shp_lanes:
                    projected_point_on_lane = np.array((shp_lane.interpolate(coef_point, normalized=True)).coords[0])
                    # on projete le coefficient et on somme le point
                    np_point_for_troncon += projected_point_on_lane
                # on calcule la moyenne
                np_point_for_troncon *= norm_lanes_center_axis
                lane_geometry.append(list(np_point_for_troncon))
                #
                # print "point_for_troncon: ", np_point_for_troncon
                # print "list_lane_center_axis:", lanes_center_axis
                # print "list_1D_coefficients:", list_1D_coefficients
        except Exception, e:
            print 'Exception: ', e
        else:
            # print 'troncon_center_axis: ', troncon_center_axis
            # sg3_edge = self.dict_edges[sg3_edge_id]
            # print 'sg3_edge - amont, aval - ({}, {}): '.format(sg3_edge['np_amont'], sg3_edge['np_aval'])

            lane_direction = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction

            id_amont, id_aval = 0, -1

            if lane_direction:
                lane_geometry.reverse()

            # Comme la liste des coefficients 1D est triee,
            # on peut declarer le 1er et dernier point comme Amont/Aval
            return NT_RESULT_BUILD_PYXB(
                lane_geometry[id_amont],
                lane_geometry[id_aval],
                lane_geometry
            )

    def build_pyxb_symuTroncon_with_lanes_in_one_group(self, **kwargs):
        """
        Plusieurs voies (meme direction) dans 1 unique groupe pour une edge_sg3
        L'idee dans ce cas est d'utiliser les informations geometriques d'edge_sg3 (centre de l'axe de l'edge)
        Faut faire attention au clipping pour ne recuperer qu'a partir d'amont/aval du troncon correspondant

        :return:

        """
        # print '### build_pyxb_symuTroncon_with_lanes_in_one_group ...'
        #
        sg3_edge = kwargs['sg3_edge']
        sg3_edge_id = kwargs['sg3_edge_id']
        #
        shp_edge_geometry = LineString(sg3_edge['np_edge_center_axis'])

        # note : on pourrait recuperer le sens avec les attributs 'left' 'right' des lanes_sg3
        # ca eviterait le sorted (sur 2 valeurs c'est pas ouf mais bon)
        list_amont_aval_proj = (
            shp_edge_geometry.project(Point(sg3_edge['np_amont'])),
            shp_edge_geometry.project(Point(sg3_edge['np_aval']))
        )
        list_sorted_coefs_amont_aval = sorted(list_amont_aval_proj)

        # print "++ list_amont_aval_proj: ", list_amont_aval_proj
        # on recupere les coefficients 1D des amont/aval
        coef_amont, coef_aval = list_sorted_coefs_amont_aval

        # liste des points formant l'axe de l'edge_sg3
        sg3_edge_center_axis = filter(
            lambda x: coef_amont <= shp_edge_geometry.project(Point(x)) <= coef_aval,
            list(shp_edge_geometry.coords)
        )

        cur_id_lane = 0
        lane_direction = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction
        NT_LANE_INFORMATIONS = CreateNamedTuple('NT_LANE_INFORMATIONS', ['amont', 'aval'])

        # b_need_to_inverse_lane = lane_direction != (coef_amont == list_amont_aval_proj[0])
        # print ('b_need_to_inverse_lane: {}\n'
        # 'lane_direction: {}\n'
        #        'coef_amont == list_amont_aval_proj[0]: {}').format(
        #     b_need_to_inverse_lane,
        #     lane_direction,
        #     coef_amont == list_amont_aval_proj[0])

        b_same_direction_for_amont_aval_and_edge = coef_amont == list_amont_aval_proj[0]
        if lane_direction:
            #
            lane_geometry = sg3_edge_center_axis[::-1]
            #
            if b_same_direction_for_amont_aval_and_edge:
                lane_oriented = NT_LANE_INFORMATIONS(sg3_edge['np_aval'], sg3_edge['np_amont'])
            else:
                lane_oriented = NT_LANE_INFORMATIONS(sg3_edge['np_amont'], sg3_edge['np_aval'])
        else:
            #
            lane_geometry = sg3_edge_center_axis
            #
            if b_same_direction_for_amont_aval_and_edge:
                lane_oriented = NT_LANE_INFORMATIONS(sg3_edge['np_amont'], sg3_edge['np_aval'])
            else:
                lane_oriented = NT_LANE_INFORMATIONS(sg3_edge['np_aval'], sg3_edge['np_amont'])

        #
        # print ('lane_direction: {} - list_amont_aval_proj: {} - list_amont_aval_proj_sort: {}').format(
        # lane_direction,
        #     list_amont_aval_proj,
        #     list_sorted_coefs_amont_aval)
        #

        return NT_RESULT_BUILD_PYXB(
            lane_oriented.amont,
            lane_oriented.aval,
            lane_geometry
        )

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)

    def build_pyxb_symuTroncon_with_lane_in_groups(self, **kwargs):
        """
        1 voie dans une serie de groupe.
        Cas le plus simple, on recupere les informations directement de la voie_sg3 (correspondance directe)
        Note: Faudrait voir pour un generateur d'id pour les nouveaux troncons_symu

        :param pyxb_symuTRONCON:
        :param cur_id_lane:
        :param nb_lanes:
        :return:
        """
        # print '### build_pyxb_symuTroncon_with_lane_in_groups ...'
        #
        sg3_edge_id = kwargs['sg3_edge_id']
        cur_id_lane = kwargs['sg3_lane_id']
        #
        try:
            sg3_lane = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane]

            try:
                lane_direction = sg3_lane.lane_direction
                #
                id_amont, id_aval = (
                    (0, -1),  # lane_direction == false => same direction than edge
                    (-1, 0)  # lane_direction == true
                )[lane_direction]
                #
                lane_geometry = sg3_lane.lane_center_axis
                if lane_direction:
                    lane_points_internes = lane_geometry[1:-1][::-1]
                else:
                    lane_points_internes = lane_geometry[1:-1]

                # print ''
                # print 'udpate_TRONCON_with_lane_in_groups'
                # print '\tpyxb_symuTRONCON.id: ', pyxb_symuTRONCON.id
                # print '\tcur_id_lane: ', cur_id_lane
                # print '\tlane_geometry: ', lane_geometry
                # print '\tsg3_edge - amont, aval: ', self.dict_edges[sg3_edge_id]['np_amont'], \
                # self.dict_edges[sg3_edge_id]['np_aval'],

                return NT_RESULT_BUILD_PYXB(
                    lane_geometry[id_amont],
                    lane_geometry[id_aval],
                    lane_points_internes
                )
            except Exception, e:
                print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e
        except Exception, e:
            print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e

    @staticmethod
    def build_id_for_TRONCON(str_pyxb_symutroncon_id, lane_id):
        """

        :param pyxb_symuTRONCON:
        :param lane_id:
        :return:
        """
        return str_pyxb_symutroncon_id + '_lane_' + str(lane_id)

    @staticmethod
    def build_pyxb_POINTS_INTERNES(list_points):
        """

        :param :
        :return:

        """
        pyxb_symuPOINTS_INTERNES = symuvia_parser.typePointsInternes()

        [pyxb_symuPOINTS_INTERNES.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
        return pyxb_symuPOINTS_INTERNES

    @timerDecorator()
    def build_topo_for_interconnexions(self):
        """

        """
        list_remove_nodes = []

        # pour chaque node SG3
        for node_id, dict_values in self.dict_nodes.iteritems():
            try:
                list_interconnexions = dict_values['interconnexions']
                set_id_edges = dict_values['set_id_edges']
            except Exception, e:
                print ''
                print 'node_id: ', node_id
                print 'build_topo_for_interconnexions - Exception: ', e
                # print 'dict_values: ', dict_values
            else:
                str_type_connexion = ''
                nb_edges_connected_on_this_node = len(set_id_edges)
                if nb_edges_connected_on_this_node == 2:
                    str_type_connexion = 'REPARTITEUR'
                elif nb_edges_connected_on_this_node > 2:
                    # potentiellement un CAF
                    str_type_connexion = 'CAF'

                # pour chaque interconnexion
                for interconnexion in list_interconnexions:
                    symu_troncons = []
                    symu_troncons_lane_id = []
                    # parcours sur les elements interconnectes (connexion entre 2 elements)
                    for python_id in range(2):
                        str_sg3_id = str(python_id + 1)
                        #
                        sg3_edge_id = interconnexion['edge_id' + str_sg3_id]
                        sg3_lane_ordinality = interconnexion['lane_ordinality' + str_sg3_id]
                        try:
                            sg3_lanes = self.dict_lanes[sg3_edge_id]
                            python_lane_id = sg3_lanes['sg3_to_python'][sg3_lane_ordinality]
                            symu_lane = sg3_lanes['sg3_to_symuvia'][python_lane_id]
                            sg3_group_lanes_start_id = symu_lane.start_id_lane
                        except Exception, e:
                            print '# build_topo_for_nodes - Find Symu_Troncon - EXCEPTION: ', e
                        else:
                            #
                            symu_troncons.append(symu_lane.symu_troncon)
                            symu_troncons_lane_id.append(python_lane_id - sg3_group_lanes_start_id)

                    if len(symu_troncons) == 2:
                        self.dict_nodes[node_id].setdefault(
                            'sg3_to_symuvia',
                            {
                                'type_connexion': str_type_connexion,
                                'list_interconnexions': {}
                            }
                        )
                        list_interconnexions = self.dict_nodes[node_id]['sg3_to_symuvia']['list_interconnexions']

                        #
                        # INVERSION du sens amont/aval
                        #
                        id_amont, id_aval = 1, 0
                        #

                        # #################################################
                        # SIMPLIFICATION DES VOIES D'INTERCONNEXIONS
                        ##################################################
                        sg3_interconnexion_geometry = interconnexion['np_interconnexion'][::-1]  # inverse list
                        shp_interconnexion = LineString(sg3_interconnexion_geometry)
                        # print 'shp_interconnexion - nb points: ', len(shp_interconnexion.coords)
                        shp_interconnexion = shp_interconnexion.simplify(0.10, preserve_topology=False)
                        # print 'after simplify -> shp_interconnexion - nb points: ', len(shp_interconnexion.coords)
                        sg3_interconnexion_geometry = np.array(shp_interconnexion)
                        ##################################################

                        # build key with id symu_troncon and the id lane
                        key_for_interconnexion = symu_troncons[id_amont].id + '_' + str(symu_troncons_lane_id[id_amont])
                        list_interconnexions.setdefault(key_for_interconnexion, []).append(
                            NT_INTERCONNEXION(
                                lane_amont=NT_LANE_SYMU(symu_troncons[id_amont], symu_troncons_lane_id[id_amont]),
                                lane_aval=NT_LANE_SYMU(symu_troncons[id_aval], symu_troncons_lane_id[id_aval]),
                                geometry=sg3_interconnexion_geometry
                            )
                        )

                        # TODO -> [TOPO] : FAKE TOPO pour CONNEXIONS/EXTREMITES
                        symu_troncons[id_amont].id_eltaval = symu_troncons[id_aval]
                        symu_troncons[id_aval].id_eltamont = symu_troncons[id_amont]


                # si il n'y a aucune interconnexion associee au node
                if not self.dict_nodes[node_id]['sg3_to_symuvia']['list_interconnexions']:
                    # alors on retire le node de la liste des nodes (utiles pour l'export SYMUVIA)
                    self.dict_nodes.pop(node_id)
                    #
                    list_remove_nodes.append(node_id)

        if list_remove_nodes:
            print '# build_topo_for_nodes - nb nodes_removed: ', len(list_remove_nodes)

    @timerDecorator()
    def build_topo_extrimites(self):
        """

        :return:
        """
        try:
            for symu_troncon in self.dict_pyxb_symutroncons.values():
                # AVAL -> SORTIE
                b_aval_not_connected = symu_troncon.id_eltaval == "-1"
                if b_aval_not_connected:
                    id_for_extrimite = self.build_id_for_extremite(symu_troncon, 'S_')
                    self.dict_extremites['SORTIES'].append(id_for_extrimite)
                    # update troncon id for aval
                    # TOPO : Link between TRONCON and EXTREMITE
                    symu_troncon.id_eltaval = id_for_extrimite
                # AMONtT -> ENTREE
                b_amont_not_connected = symu_troncon.id_eltamont == "-1"
                if b_amont_not_connected:
                    id_for_extrimite = self.build_id_for_extremite(symu_troncon, 'E_')
                    self.dict_extremites['ENTREES'].append(id_for_extrimite)
                    # update troncon id for aval
                    # TOPO : Link between TRONCON and EXTREMITE
                    symu_troncon.id_eltamont = id_for_extrimite
        except Exception, e:
            print 'build_topo_extrimites - Exception: ', e

    def build_id_for_extremite(self, symu_troncon, prefix=""):
        """

        :param symu_troncon:
        :return:
        """
        id_extremite = prefix + symu_troncon.id
        return id_extremite
