__author__ = 'latty'

from shapely.geometry import Point, LineString
import pyxb

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import CreateNamedTupleOnGlobals


NT_LANE_SG3_SYMU = CreateNamedTupleOnGlobals(
    'NT_LANE_SG3_SYMU',
    [
        'symu_troncon',
        'start_id_lane',
        'nb_lanes'
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
            self.dict_pyxb_symutroncons.update(self.convert_sg3_edge_to_pyxb_symutroncon(sg3_edge_id))
        #
        print 'convert_sg3_edges_to_pyxb_symutroncons - %d troncons added' % len(self.dict_pyxb_symutroncons.keys())
        #

    @staticmethod
    def update_list_troncons(dict_pyxb_simuTroncons, pyxb_simuTroncon, sg3_edge):
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
            list_pyxb_simuTRONCON = filter(lambda x: x.id == pyxb_simuTroncon.id, sg3_edge['sg3_to_symuvia'])
        except:
            # la cle 'sg3_to_symuvia' n'existe pas donc on est dans l'init (premiere passe)
            dict_pyxb_simuTroncons[pyxb_simuTroncon.id] = pyxb_simuTroncon
        else:
            if len(list_pyxb_simuTRONCON) == 0:
                # nouveau troncon
                dict_pyxb_simuTroncons[pyxb_simuTroncon.id] = pyxb_simuTroncon
            else:
                # le troncon est deja present
                # TODO: il faudrait updater le TRONCON
                dict_pyxb_simuTroncons[list_pyxb_simuTRONCON[0].id] = list_pyxb_simuTRONCON[0]

    def convert_sg3_edge_to_pyxb_symutroncon(self, sg3_edge_id):
        """

        :param sg3_edge_id:
        :return:
        """
        dict_pyxb_simuTroncons = {}

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
            print '- len(grouped_lanes) : ', len(grouped_lanes)
            if len(grouped_lanes) > 1:
                # print '++ grouped_lanes: ', grouped_lanes
                # on a plusieurs groupes de voies (dans des directions differentes) pour ce troncon
                cur_id_lane = 0
                for nb_lanes in grouped_lanes:

                    pyxb_symuTRONCON = symuvia_parser.typeTroncon(
                        id=sg3_edge['str_ign_id'],
                        largeur_voie=sg3_edge['f_road_width'] / sg3_edge['ui_lane_number'],
                        id_eltamont="-1",
                        id_eltaval="-1"
                    )

                    if nb_lanes > 1:
                        # groupe de plusieurs voies dans la meme direction
                        self.update_TRONCON_with_lanes_in_groups(pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes)
                        # Update list_troncon (local function)
                        self.update_list_troncons(dict_pyxb_simuTroncons, pyxb_symuTRONCON, sg3_edge)
                    else:
                        # groupe d'une seule voie (pour une direction)
                        self.udpate_TRONCON_with_lane_in_groups(pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes)
                        # Update list_troncon (local function)
                        self.update_list_troncons(dict_pyxb_simuTroncons, pyxb_symuTRONCON, sg3_edge)

                    # next lanes group
                    cur_id_lane += nb_lanes
            else:
                # le troncon possede 1 groupe de voies mono-directionnelles
                nb_lanes = grouped_lanes[0]
                #
                # sym_TRONCON = self.build_TRONCON(sg3_edge, *args)
                pyxb_symuTRONCON = symuvia_parser.typeTroncon(
                    id=sg3_edge['str_ign_id'],
                    largeur_voie=sg3_edge['f_road_width'] / sg3_edge['ui_lane_number'],
                    id_eltamont="-1",
                    id_eltaval="-1"
                )

                self.update_TRONCON_with_lanes_in_one_group(pyxb_symuTRONCON, sg3_edge, sg3_edge_id, nb_lanes)

                # Update list_troncon (local function)
                self.update_list_troncons(dict_pyxb_simuTroncons, pyxb_symuTRONCON, sg3_edge)
        finally:
            # LINK STREETGEN3 to SYMUVIA (TOPO)
            sg3_edge['sg3_to_symuvia'] = dict_pyxb_simuTroncons.values()
            #
            # print self.dict_lanes[sg3_edge_id]['sg3_to_symuvia']

            return dict_pyxb_simuTroncons

    def update_TRONCON_with_lanes_in_groups(self, pyxb_symuTRONCON, sg3_edge_id, cur_id_lane, nb_lanes):
        """
        1 Groupe de plusieurs voies (dans la meme direction) dans une serie de groupes (de voies) pour l'edge_sg3
        :return:
        """
        # TODO : a finir !
        # TODO : il faudrait 'au moins' decaler les amont/aval pour etre centre avec les lanes de ce groupe

        sg3_edge = self.dict_edges[sg3_edge_id]
        lane_direction = not self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction
        sg3_edges_amont_aval = [
            {'amont': sg3_edge['np_aval'], 'aval': sg3_edge['np_amont']},
            {'aval': sg3_edge['np_aval'], 'amont': sg3_edge['np_amont']},
        ]

        self.update_pyxb_node(
            pyxb_symuTRONCON,
            id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
            nb_voie=nb_lanes,
            extremite_amont=sg3_edges_amont_aval[lane_direction]['amont'],
            extremite_aval=sg3_edges_amont_aval[lane_direction]['aval']
        )

        # LINK STREETGEN3 to SYMUVIA (TOPO)
        symu_lanes = self.dict_lanes[sg3_edge_id]['sg3_to_symuvia']
        for id_lane in range(cur_id_lane, cur_id_lane + nb_lanes):
            symu_lanes[id_lane] = NT_LANE_SG3_SYMU(pyxb_symuTRONCON, cur_id_lane, nb_lanes)

    def update_TRONCON_with_lanes_in_one_group(self, pyxb_symuTRONCON, sg3_edge, sg3_edge_id, nb_lanes):
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
        list_amont_aval_proj = sorted(
            [
                edge_center_axis.project(Point(sg3_edge['np_amont'])),
                edge_center_axis.project(Point(sg3_edge['np_aval']))
            ]
        )

        # print "++ list_amont_aval_proj: ", list_amont_aval_proj
        # on recupere les coefficients 1D des amont/aval
        coef_amont, coef_aval = list_amont_aval_proj
        troncon_center_axis = []
        # liste des points formant l'axe de l'edge_sg3
        troncon_center_axis = filter(
            lambda x: coef_amont <= edge_center_axis.project(Point(x)) <= coef_aval,
            list(edge_center_axis.coords)
        )

        pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(troncon_center_axis)

        cur_id_lane = 0
        lane_direction = not self.dict_lanes[sg3_edge_id]['informations'][cur_id_lane].lane_direction
        sg3_edges_amont_aval = [
            {'amont': sg3_edge['np_aval'], 'aval': sg3_edge['np_amont']},
            {'aval': sg3_edge['np_aval'], 'amont': sg3_edge['np_amont']},
        ]
        self.update_pyxb_node(
            pyxb_symuTRONCON,
            id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
            nb_voie=nb_lanes,
            extremite_amont=sg3_edges_amont_aval[lane_direction]['amont'],
            extremite_aval=sg3_edges_amont_aval[lane_direction]['aval']
        )

        # LINK STREETGEN3 to SYMUVIA (TOPO)
        symu_lanes = self.dict_lanes[sg3_edge_id]['sg3_to_symuvia']
        for id_lane in range(nb_lanes):
            symu_lanes[id_lane] = NT_LANE_SG3_SYMU(pyxb_symuTRONCON, 0, nb_lanes)

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)

    def udpate_TRONCON_with_lane_in_groups(self, pyxb_symuTRONCON, edge_id, cur_id_lane, nb_lanes):
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
            edge_center_axis = self.dict_lanes[edge_id]['lane_center_axis'][cur_id_lane]
            lane_direction = self.dict_lanes[edge_id]['informations'][cur_id_lane].lane_direction

            id_amont, id_aval = 0, -1
            if lane_direction:
                id_amont, id_aval = -1, 0

            try:
                self.update_pyxb_node(
                    pyxb_symuTRONCON,
                    nb_voie=nb_lanes,
                    id=self.build_id_for_TRONCON(pyxb_symuTRONCON, cur_id_lane),
                    extremite_amont=edge_center_axis[id_amont],
                    extremite_aval=edge_center_axis[id_aval]
                )

                # transfert des points internes (eventuellement)
                pyxb_symuTRONCON.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(edge_center_axis[1:-1])

                # LINK STREETGEN3 to SYMUVIA (TOPO)
                symu_lanes = self.dict_lanes[edge_id]['sg3_to_symuvia']
                for id_lane in range(cur_id_lane, cur_id_lane + nb_lanes):
                    symu_lanes[id_lane] = NT_LANE_SG3_SYMU(pyxb_symuTRONCON, cur_id_lane, nb_lanes)

            except Exception, e:
                print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e
        except Exception, e:
            print 'udpate_TRONCON_with_lane_in_groups - EXCEPTION: ', e

    @staticmethod
    def build_id_for_TRONCON(pyxb_symuTRONCON, lane_id):
        """

        :param node_id:
        :return:
        """
        return pyxb_symuTRONCON.id + '_lane_' + str(lane_id)

    def build_pyxb_POINTS_INTERNES(self, list_points, *args):
        """

        :param :
        :return:

        """
        pyxb_symuPOINTS_INTERNES = symuvia_parser.typePointsInternes()

        [pyxb_symuPOINTS_INTERNES.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
        return pyxb_symuPOINTS_INTERNES

    @staticmethod
    def get_id_lane_from_id_name(symu_troncon):
        """
        """
        str_key_for_lane = '_lane_'
        l_str_key_for_lane = len(str_key_for_lane)
        id_in_list = 0
        symu_troncon_id = symu_troncon.id
        try:
            id_in_list = int(symu_troncon_id[symu_troncon_id.find(str_key_for_lane) + l_str_key_for_lane:])
        except:
            print "# build_topo_for_nodes - PROBLEME! symuvia_troncon_id: %s - probleme de conversion en 'int'" % symu_troncon_id
        finally:
            return id_in_list

    def build_topo_for_nodes(self):
        """

        """
        # !!!!! FAUDRAIT CLEAN LE RESEAU des troncons sans voies, ou node/caf avec de tel troncons !!!!

        list_remove_nodes = []

        for node_id, dict_values in self.dict_nodes.iteritems():
            caf_entrees = []
            caf_sorties = []
            caf_entrees_sorties = [caf_entrees, caf_sorties]

            #
            # print 'build_topo_for_nodes - dict_values: ', dict_values

            # Pour chaque edge SG3
            for edge_id in dict_values['array_str_edge_ids']:
                sg3_edge = self.dict_edges[edge_id]

                try:
                    # on recupere la liste des edges SYMUVIA correspondantes (potentiellement plusieurs)
                    list_symu_edges = sg3_edge['sg3_to_symuvia']
                except Exception, e:
                    print '# build_topo_for_nodes - EXCEPTION: ', e
                    # remove this node
                    list_remove_nodes.append(node_id)
                else:
                    # pour chaque troncon SYMUVIA
                    for symu_troncon in list_symu_edges:
                        # on recupere le numero de voie par rapport au tag id attribue (TODO: a revoir!)
                        id_in_list = self.get_id_lane_from_id_name(symu_troncon)

                        lane = self.dict_lanes[edge_id]['informations'][id_in_list]
                        lane_direction = lane.lane_direction

                        print "node_id: %s, edge_id: %s, sg3_edge['ui_start_node']: %s, lane_direction: %s" % \
                              (node_id, edge_id, sg3_edge['ui_start_node'], lane_direction)

                        # '!=' est l'operateur XOR en Python
                        id_caf_in_out = int((sg3_edge['ui_start_node'] == node_id) != lane_direction)

                        caf_entrees_sorties[id_caf_in_out].append(symu_troncon)

                        # print 'id_caf_inout: ', id_caf_inout
                        # print "sge_edge['start_node']: ", sge_edge['start_node']
                        # print 'id_in_list: ', id_in_list
                        # print 'oncoming: ', oncoming
                    # print "id edge in SG3: ", edge_id
                    # print "-> id edges in SYMUVIA: ", list_symuvia_edges

                    #
                    self.dict_nodes[node_id].setdefault(
                        'CAF',
                        {
                            'in': caf_entrees,
                            'out': caf_sorties
                        }
                    )

                    #
                    # print "node_id: ", node_id
                    # print "-> caf_entrees (SYMUVIA): ", caf_entrees
                    # print "-> caf_sorties (SYMUVIA): ", caf_sorties
                    # print "-> dict_nodes[node_id]: ", dict_nodes[node_id]
        # remove nodes
        nodes_removed = [self.dict_nodes.pop(k, None) for k in list_remove_nodes]
        #
        print '# build_topo_for_nodes - nb nodes_removed: ', len(nodes_removed)
        print '# build_topo_for_nodes - nb nodes : ', len(self.dict_nodes.keys())

    def build_topo_for_interconnexions(self):
        """

        """
        list_remove_nodes = []

        # pour chaque node SG3
        for node_id, dict_values in self.dict_nodes.iteritems():

            # pour chaque interconnexion
            for interconnexion in dict_values['interconnexions']:

                sg3_id_edge1 = interconnexion['edge_id1']
                sg3_id_edge2 = interconnexion['edge_id2']
                #
                sg3_edge1 = self.dict_edges[sg3_id_edge1]
                sg3_edge2 = self.dict_edges[sg3_id_edge2]
                #
                sg3_lane_ordinality1 = interconnexion['lane_ordinality1']
                sg3_lane_ordinality2 = interconnexion['lane_ordinality2']

                try:
                    # on recupere la liste des edges SYMUVIA correspondantes (potentiellement plusieurs)
                    list_symu_edges_1 = sg3_edge1['sg3_to_symuvia']
                    list_symu_edges_2 = sg3_edge1['sg3_to_symuvia']
                except Exception, e:
                    print '# build_topo_for_nodes - Find SG3_edges - EXCEPTION: ', e
                    # remove this node
                    list_remove_nodes.append(node_id)
                else:
                    # print "self.dict_lanes: ", self.dict_lanes
                    try:
                        lane1 = self.dict_lanes[sg3_id_edge1]
                        lane2 = self.dict_lanes[sg3_id_edge2]

                        python_id_lane1 = lane1['sg3_to_python'][sg3_lane_ordinality1]
                        python_id_lane2 = lane2['sg3_to_python'][sg3_lane_ordinality2]

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
                        #     '\n\t' + '- python_id_lane1: ', python_id_lane1, \
                        #     '\n\t' + '- start id for group lane: ', sg3_start_id_group_lanes_for_troncon1, '\n'
                        # print '*-*- symu_troncon2: ', symu_troncon2, \
                        #     '\n\t' + '- python_id_lane2: ', python_id_lane2, \
                        #     '\n\t' + '- sg3_start_id_troncon2: ', sg3_start_id_group_lanes_for_troncon2, '\n'
                        # print ''

                        symu_troncon1_id_lane = python_id_lane1 - sg3_start_id_group_lanes_for_troncon1
                        symu_troncon2_id_lane = python_id_lane2 - sg3_start_id_group_lanes_for_troncon2

                        if not lane1['informations'][python_id_lane1].lane_direction:
                            print "lane1['informations'][python_id_lane1].lane_direction: ", lane1['informations'][
                                python_id_lane1].lane_direction
                            print "symu_troncon1_id_lane: ", symu_troncon1_id_lane
                            symu_troncon1_id_lane = (lane1['informations'][
                                                         python_id_lane1].nb_lanes - 1) - symu_troncon1_id_lane
                            print "symu_troncon1_id_lane: ", symu_troncon1_id_lane
                            print ''
                        if not lane2['informations'][python_id_lane2].lane_direction:
                            print "lane2['informations'][python_id_lane].lane_direction: ", lane2['informations'][
                                python_id_lane2].lane_direction
                            print "symu_troncon2_id_lane: ", symu_troncon2_id_lane
                            symu_troncon2_id_lane = (lane2['informations'][
                                                         python_id_lane2].nb_lanes - 1) - symu_troncon2_id_lane
                            print "symu_troncon2_id_lane: ", symu_troncon2_id_lane
                            print ''

                        self.dict_nodes[node_id].setdefault('CAF_interconnexions', {})
                        CAF_interconnexions = self.dict_nodes[node_id]['CAF_interconnexions']

                        #
                        # INVERSION du sens amont/aval
                        #
                        # build key with id symu_troncon and the id lane
                        key_for_troncon_lane = symu_troncon2.id + '_' + str(symu_troncon2_id_lane)
                        CAF_interconnexions.setdefault(key_for_troncon_lane, []).append(
                            (
                                #
                                # (symu_troncon1, python_id_lane1 - sg3_start_id_group_lanes_for_troncon1),
                                # (symu_troncon2, python_id_lane2 - sg3_start_id_group_lanes_for_troncon2)
                                (symu_troncon2, symu_troncon2_id_lane),
                                (symu_troncon1, symu_troncon1_id_lane)
                            )
                        )
                        #
                        print '++ key_for_troncon_lane: ', key_for_troncon_lane

                        # nodes_removed = [self.dict_nodes.pop(k, None) for k in list_remove_nodes]
                        #
                        # print '# build_topo_for_nodes - nb nodes_removed: ', len(nodes_removed)
                        # print '# build_topo_for_nodes - nb nodes : ', len(self.dict_nodes.keys())
