__author__ = 'latty'

import numpy as np

from shapely.geometry import Point, LineString
import pyxb

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import CreateNamedTupleOnGlobals
from imt_tools import CreateNamedTuple


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
        'amont',
        'aval',
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
        self.dict_pyxb_symuconnexions = {}
        #

    def clear(self):
        """

        :return:
        """
        self.dict_pyxb_symutroncons = {}
        self.dict_pyxb_symuconnexions = {}

    def convert_sg3_edges_to_pyxb_symutroncons(self):
        """

        :return:

        """
        for sg3_edge_id in self.dict_lanes:
            self.dict_pyxb_symutroncons.update(self.build_pyxb_symutroncon_from_sg3_edge(sg3_edge_id))
        #
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

    def build_pyxb_symutroncon_from_sg3_edge(self, sg3_edge_id):
        """

        :param sg3_edge_id:
        :return:
        """
        dict_pyxb_symuTroncons = {}

        sg3_edge = self.dict_edges[sg3_edge_id]

        # print "sg3_edge: ", sg3_edge
        try:
            grouped_lanes = sg3_edge['grouped_lanes']
        except:
            # Il y a des edge_sg3 sans voie(s) dans le reseau SG3 ... faudrait demander a Remi !
            # Peut etre des edges_sg3 aidant uniquement aux connexions/creation (de zones) d'intersections
            print ""
            print "!!! 'BUG' with edge id: ", sg3_edge_id, " - no 'group_lanes' found !!!"
            print ""
        else:
            # print '- len(grouped_lanes) : ', len(grouped_lanes)
            cur_id_lane = 0
            if len(grouped_lanes) > 1:
                # print '++ grouped_lanes: ', grouped_lanes
                # on a plusieurs groupes de voies (dans des directions differentes) pour ce troncon
                # Groupe de plusieurs voies dans la meme direction ?
                list_update_functions_for_pyxb_symuTroncon = (
                    self.update_pyxb_symuTroncon_with_lane_in_groups,  # false
                    self.update_pyxb_symuTroncon_with_lanes_in_groups,  # true
                )
                for nb_lanes in grouped_lanes:
                    pyxb_symuTRONCON = symuvia_parser.typeTroncon(
                        id=sg3_edge['str_ign_id'],
                        largeur_voie=sg3_edge['f_road_width'] / sg3_edge['ui_lane_number'],
                        id_eltamont="-1",
                        id_eltaval="-1"
                    )
                    # update list TRONCONS
                    list_update_functions_for_pyxb_symuTroncon[nb_lanes > 1](
                        pyxb_symuTRONCON,
                        sg3_edge_id,
                        cur_id_lane,
                        nb_lanes
                    )

                    # Update list_troncon
                    self.update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTRONCON, sg3_edge)

                    # LINK STREETGEN3 to SYMUVIA (TOPO)
                    self.build_link_from_sg3_to_symuvia_for_lane(pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes)

                    # next lanes group
                    cur_id_lane += nb_lanes
            else:
                # le troncon possede 1 groupe de voies mono-directionnelles
                nb_lanes = grouped_lanes[0]
                #
                pyxb_symuTRONCON = symuvia_parser.typeTroncon(
                    id=sg3_edge['str_ign_id'],
                    largeur_voie=sg3_edge['f_road_width'] / sg3_edge['ui_lane_number'],
                    id_eltamont="-1",
                    id_eltaval="-1"
                )

                self.update_pyxb_symuTroncon_with_lanes_in_one_group(pyxb_symuTRONCON, sg3_edge, sg3_edge_id, nb_lanes)

                # LINK STREETGEN3 to SYMUVIA (TOPO)
                self.build_link_from_sg3_to_symuvia_for_lane(pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes)

                # Update list_troncon
                self.update_dict_pyxb_symuTroncons(dict_pyxb_symuTroncons, pyxb_symuTRONCON, sg3_edge)
        finally:
            # LINK STREETGEN3 to SYMUVIA (TOPO)
            sg3_edge['sg3_to_symuvia'] = dict_pyxb_symuTroncons.values()
            #
            # print self.dict_lanes[sg3_edge_id]['sg3_to_symuvia']

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

    def update_pyxb_symuTroncon_with_lanes_in_groups(self, pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes):
        """
        1 Groupe de plusieurs voies (dans la meme direction) dans une serie de groupes (de voies) pour l'edge_sg3
        Pas encore finie, experimental car le cas n'est pas present dans le reseau (pas possible de tester directement
        cet algo).
        :return:
        """
        lanes_informations = []
        # transfert lane_center_axis for each lane in 2D
        list_1D_coefficients = []
        # on parcourt le groupe de 'voies' dans le meme sens
        for id_lane in range(cur_id_lane, cur_id_lane + nb_lanes):
            try:
                # sg3_id_lane = self.dict_lanes[sg3_edge_id]['python_to_sg3']
                # print 'id_lane : ', id_lane

                # get the linestring of the current lane
                # sg3_lane = self.dict_lanes[sg3_edge_id]['lane_center_axis'][id_lane]
                sg3_lane = self.dict_lanes[sg3_edge_id]['informations'][id_lane].lane_center_axis
                shp_lane = LineString(sg3_lane)
                # project this linestring into 1D coefficients
                linestring_proj_1D_coefficients = [
                    shp_lane.project(Point(point), normalized=True)
                    for point in list(shp_lane.coords)
                ]
                # save the lane informations
                lane_informations = {
                    'LineString': shp_lane,
                    'LineString_Proj': linestring_proj_1D_coefficients
                }
                # append the lane (informations)
                lanes_informations.append(lane_informations)
                # expand the list
                list_1D_coefficients += linestring_proj_1D_coefficients

                print ''
                print('id_lane: {}\n'
                      '- sg3_lane: {}\n'
                      '- shp_lane: {}\n'
                      '- linestring_proj_1D_coefficients: {}\n').format(id_lane, sg3_lane, shp_lane.wkt,
                                                                        linestring_proj_1D_coefficients)
            except Exception, e:
                print 'Exception: ', e

        try:
            # ##########################
            # clean the list of 1D coefficients
            # remove duplicate values
            # url: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
            list_1D_coefficients = list(set(list_1D_coefficients))
            # sort the list of 1D coefficients
            list_1D_coefficients.sort()
            print '-> after set & sort - list_1D_coefficients: {}'.format(list_1D_coefficients)
            # ##########################
        except Exception, e:
            print 'Exception: ', e

        # Compute the troncon center axis
        # Methode: on utilise les coefficients 1D de chaque voie qui va composer ce troncon.
        # On retroprojete chaque coeffient (1D) sur l'ensemble des voies (2D) et on effectue la moyenne des positions
        # On recupere 'une sorte d'axe median' des voies (du meme groupe)
        #
        troncon_center_axis = []
        try:
            # coefficient de normalisation depend du nombre de voies qu'on utilise pour la moyenne
            norm_lanes_center_axis = 1.0 / len(lanes_informations)
            # pour chaque coefficient 1D
            for coef_point in list_1D_coefficients:
                # on calcule la moyenne des points sur les lanes pour ce coefficient
                np_point_for_troncon = np.array(Point(0, 0).coords[0])
                # pour chaque lane
                for lane_informations in lanes_informations:
                    # on recupere la geometrie
                    shp_lane = lane_informations['LineString']
                    projected_point_on_lane = np.array((shp_lane.interpolate(coef_point, normalized=True)).coords[0])
                    # on projete le coefficient et on somme le point
                    np_point_for_troncon += projected_point_on_lane
                # on calcule la moyenne
                np_point_for_troncon *= norm_lanes_center_axis
                troncon_center_axis.append(list(np_point_for_troncon))
                #
                print "point_for_troncon: ", np_point_for_troncon
                # print "list_lane_center_axis:", lanes_center_axis
                # print "list_1D_coefficients:", list_1D_coefficients
        except Exception, e:
            print 'Exception: ', e
        finally:
            print 'troncon_center_axis: ', troncon_center_axis
            sg3_edge = self.dict_edges[sg3_edge_id]
            print 'sg3_edge - amont, aval - ({}, {}): '.format(sg3_edge['np_amont'], sg3_edge['np_aval'])

            lane_direction = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction
            id_amont, id_aval = 0, -1
            if lane_direction:
                id_amont, id_aval = -1, 0
            # Comme la liste des coefficients 1D est triee,
            # on peut declarer le 1er et dernier point comme Amont/Aval
            # cur_id_lane = 0
            self.update_pyxb_node(
                pyxb_symuTRONCON,
                id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
                nb_voie=nb_lanes,
                extremite_amont=troncon_center_axis[id_amont],
                extremite_aval=troncon_center_axis[id_aval]
            )

            # id_amont, id_aval = 1, -1
            # if lane_direction:
            # id_amont, id_aval = -1, 1
            # pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(troncon_center_axis[id_amont:id_aval])
            if lane_direction:
                troncon_center_axis.reverse()
            pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(troncon_center_axis)


    def update_pyxb_symuTroncon_with_lanes_in_one_group(self, pyxb_symuTRONCON, sg3_edge, sg3_edge_id, nb_lanes):
        """
        Plusieurs voies (meme direction) dans 1 unique groupe pour une edge_sg3
        L'idee dans ce cas est d'utiliser les informations geometriques d'edge_sg3 (centre de l'axe de l'edge)
        Faut faire attention au clipping pour ne recuperer qu'a partir d'amont/aval du troncon correspondant
        :return:
        """
        #
        edge_center_axis = LineString(sg3_edge['np_edge_center_axis'])

        # note : on pourrait recuperer le sens avec les attributs 'left' 'right' des lanes_sg3
        # ca eviterait le sorted (sur 2 valeurs c'est pas ouf mais bon)
        list_amont_aval_proj = (
            edge_center_axis.project(Point(sg3_edge['np_amont'])),
            edge_center_axis.project(Point(sg3_edge['np_aval']))
        )
        list_sorted_coefs_amont_aval = sorted(list_amont_aval_proj)

        # print "++ list_amont_aval_proj: ", list_amont_aval_proj
        # on recupere les coefficients 1D des amont/aval
        coef_amont, coef_aval = list_sorted_coefs_amont_aval

        # liste des points formant l'axe de l'edge_sg3
        troncon_center_axis = filter(
            lambda x: coef_amont <= edge_center_axis.project(Point(x)) <= coef_aval,
            list(edge_center_axis.coords)
        )

        cur_id_lane = 0
        lane_direction = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction
        NT_LANE_INFORMATIONS = CreateNamedTuple('NT_LANE_INFORMATIONS', ['amont', 'aval', 'geometry'])
        lane_oriented = (
            NT_LANE_INFORMATIONS(sg3_edge['np_aval'], sg3_edge['np_amont'], troncon_center_axis[::-1]),
            NT_LANE_INFORMATIONS(sg3_edge['np_amont'], sg3_edge['np_aval'], troncon_center_axis),
        )[lane_direction != (coef_amont == list_amont_aval_proj[0])]
        #
        print ('lane_direction: {} - list_amont_aval_proj: {} - list_amont_aval_proj_sort: {}').format(
            lane_direction,
            list_amont_aval_proj,
            list_sorted_coefs_amont_aval)
        #
        self.update_pyxb_node(
            pyxb_symuTRONCON,
            id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
            nb_voie=nb_lanes,
            extremite_amont=lane_oriented.amont,
            extremite_aval=lane_oriented.aval,
        )
        #
        pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(lane_oriented.geometry)

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)

    def update_pyxb_symuTroncon_with_lane_in_groups(self, pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes):
        """
        1 voie dans une serie de groupe.
        Cas le plus simple, on recupere les informations directement de la voie_sg3 (correspondance directe)
        Note: Faudrait voir pour un generateur d'id pour les nouveaux troncons_symu

        :param pyxb_symuTRONCON:
        :param cur_id_lane:
        :param nb_lanes:
        :return:
        """

        try:
            sg3_lane = self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane]
            edge_center_axis = sg3_lane.lane_center_axis
            lane_direction = sg3_lane.lane_direction

            id_amont, id_aval = (
                (0, -1),  # lane_direction == false => same direction than edge
                (-1, 0)  # lane_direction == true
            )[lane_direction]

            try:
                self.update_pyxb_node(
                    pyxb_symuTRONCON,
                    nb_voie=nb_lanes,
                    id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
                    extremite_amont=edge_center_axis[id_amont],
                    extremite_aval=edge_center_axis[id_aval]
                )

                # transfert des points internes (eventuellement)
                # pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(edge_center_axis[1:-1])
                pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(edge_center_axis)

                print ''
                print 'udpate_TRONCON_with_lane_in_groups'
                print '\tpyxb_symuTRONCON.id: ', pyxb_symuTRONCON.id
                print '\tcur_id_lane: ', cur_id_lane
                print '\tedge_center_axis: ', edge_center_axis
                print '\tsg3_edge - amont, aval: ', self.dict_edges[sg3_edge_id]['np_amont'], \
                    self.dict_edges[sg3_edge_id]['np_aval'],

            except Exception, e:
                print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e
        except Exception, e:
            print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e

    @staticmethod
    def build_id_for_TRONCON(pyxb_symuTRONCON, lane_id):
        """

        :param pyxb_symuTRONCON:
        :param lane_id:
        :return:
        """
        return pyxb_symuTRONCON.id + '_lane_' + str(lane_id)

    @staticmethod
    def build_pyxb_POINTS_INTERNES(list_points):
        """

        :param :
        :return:

        """
        pyxb_symuPOINTS_INTERNES = symuvia_parser.typePointsInternes()

        [pyxb_symuPOINTS_INTERNES.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
        return pyxb_symuPOINTS_INTERNES

    def build_topo_for_interconnexions(self):
        """

        """
        list_remove_nodes = []

        # pour chaque node SG3
        for node_id, dict_values in self.dict_nodes.iteritems():

            # pour chaque interconnexion
            try:
                list_interconnexions = dict_values['interconnexions']
            except Exception, e:
                pass
            else:
                for interconnexion in list_interconnexions:

                    sg3_id_edge1 = interconnexion['edge_id1']
                    sg3_id_edge2 = interconnexion['edge_id2']
                    #
                    sg3_lane_ordinality1 = interconnexion['lane_ordinality1']
                    sg3_lane_ordinality2 = interconnexion['lane_ordinality2']
                    #
                    sg3_lane_geometry = interconnexion['np_interconnexion']

                    # print "self.dict_lanes: ", self.dict_lanes
                    try:
                        lane1 = self.dict_lanes[sg3_id_edge1]
                        lane2 = self.dict_lanes[sg3_id_edge2]

                        python_id_lane1 = lane1['sg3_to_python'][sg3_lane_ordinality1]
                        python_id_lane2 = lane2['sg3_to_python'][sg3_lane_ordinality2]

                        print "lane1['sg3_to_symuvia']: ", lane1['sg3_to_symuvia']
                        print "lane2['sg3_to_symuvia']: ", lane2['sg3_to_symuvia']
                        print "python_id_lane1: ", python_id_lane1
                        print "python_id_lane2: ", python_id_lane2

                        symu_troncon1 = lane1['sg3_to_symuvia'][python_id_lane1].symu_troncon
                        symu_troncon2 = lane2['sg3_to_symuvia'][python_id_lane2].symu_troncon

                        sg3_start_id_group_lanes_for_troncon1 = lane1['sg3_to_symuvia'][python_id_lane1].start_id_lane
                        sg3_start_id_group_lanes_for_troncon2 = lane2['sg3_to_symuvia'][python_id_lane2].start_id_lane

                    except Exception, e:
                        print '# build_topo_for_nodes - Find Symu_Troncon - EXCEPTION: ', e
                        # remove this node
                        list_remove_nodes.append(node_id)
                    else:
                        # print '*-*- symu_troncon1: ', symu_troncon1, \
                        # '\n\t' + '- python_id_lane1: ', python_id_lane1, \
                        # '\n\t' + '- start id for group lane: ', sg3_start_id_group_lanes_for_troncon1, '\n'
                        # print '*-*- symu_troncon2: ', symu_troncon2, \
                        # '\n\t' + '- python_id_lane2: ', python_id_lane2, \
                        #     '\n\t' + '- sg3_start_id_troncon2: ', sg3_start_id_group_lanes_for_troncon2, '\n'
                        # print ''

                        symu_troncon1_id_lane = python_id_lane1 - sg3_start_id_group_lanes_for_troncon1
                        symu_troncon2_id_lane = python_id_lane2 - sg3_start_id_group_lanes_for_troncon2

                        if not lane1['informations'][python_id_lane1].lane_direction:
                            print "lane1['informations'][python_id_lane1].lane_direction: ", lane1['informations'][
                                python_id_lane1].lane_direction
                            print "symu_troncon1_id_lane: ", symu_troncon1_id_lane
                            #
                            symu_troncon1_id_lane = lane1['informations'][python_id_lane1].nb_lanes
                            symu_troncon1_id_lane -= 1
                            symu_troncon1_id_lane -= symu_troncon1_id_lane
                            #
                            print "symu_troncon1_id_lane: ", symu_troncon1_id_lane
                            print ''
                        if not lane2['informations'][python_id_lane2].lane_direction:
                            print "lane2['informations'][python_id_lane].lane_direction: ", lane2['informations'][
                                python_id_lane2].lane_direction
                            print "symu_troncon2_id_lane: ", symu_troncon2_id_lane
                            #
                            symu_troncon2_id_lane = lane2['informations'][python_id_lane2].nb_lanes
                            symu_troncon2_id_lane -= 1
                            symu_troncon2_id_lane -= symu_troncon2_id_lane
                            #
                            print "symu_troncon2_id_lane: ", symu_troncon2_id_lane
                            print ''

                        self.dict_nodes[node_id].setdefault('CAF_interconnexions', {})
                        CAF_interconnexions = self.dict_nodes[node_id]['CAF_interconnexions']

                        #
                        # INVERSION du sens amont/aval
                        #
                        # url: http://docs.scipy.org/doc/numpy/reference/generated/numpy.flipud.html
                        sg3_lane_geometry = np.flipud(sg3_lane_geometry)
                        # build key with id symu_troncon and the id lane
                        key_for_troncon_lane = symu_troncon2.id + '_' + str(symu_troncon2_id_lane)
                        CAF_interconnexions.setdefault(key_for_troncon_lane, []).append(
                            NT_INTERCONNEXION(
                                amont=NT_LANE_SYMU(symu_troncon2, symu_troncon2_id_lane),
                                aval=NT_LANE_SYMU(symu_troncon1, symu_troncon1_id_lane),
                                geometry=sg3_lane_geometry
                            )
                        )

                        print '++ key_for_troncon_lane: ', key_for_troncon_lane

                nodes_removed = [self.dict_nodes.pop(k, None) for k in list_remove_nodes]
                if nodes_removed:
                    print '# build_topo_for_nodes - nb nodes_removed: ', len(nodes_removed)
                    print '# build_topo_for_nodes - nb nodes : ', len(self.dict_nodes.keys())