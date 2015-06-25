__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator


class trafipolluImp_EXPORT_CONNEXIONS(object):
    def __init__(self, dict_edges, dict_lanes, dict_nodes, module_topo, list_symu_connexions):
        """

        """
        self.dict_edges = dict_edges
        self.dict_lanes = dict_lanes
        self.dict_nodes = dict_nodes
        #
        self.pyxb_parser = pyxb_parser
        #
        self.cursor_symuvia = {
            'sg3_node': None,
            'node_id': 0,
            'sym_CAF': None,
            'id_amont_troncon_lane': ""
        }
        #
        self.list_symu_connexions = list_symu_connexions
        #
        self.module_topo = module_topo  # tpi_TOPO.trafipolluImp_TOPO(self.dict_edges, self.dict_lanes, self.dict_nodes)

    @pyxbDecorator(pyxb_parser)
    def export_CONNEXIONS(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_CONNEXIONS = pyxbDecorator.get_path_instance(*args)
        # print 'sym_CONNEXIONS: ', sym_CONNEXIONS
        sym_CONNEXIONS.CARREFOURSAFEUX = self.export_CARREFOURSAFEUX(str_path_to_child)

        return sym_CONNEXIONS

    @pyxbDecorator(pyxb_parser)
    def export_CARREFOURSAFEUX(self, *args):
        """

        :param node_id:
        :return:
        # """

        # TODO: construction TOPO ici !
        self.module_topo.build_topo_for_nodes()
        #
        self.module_topo.build_topo_for_interconnexions()

        str_path_to_child, sym_CAFS = pyxbDecorator.get_path_instance(*args)
        for node_id in self.dict_nodes:
            self.select_node(node_id)
            sym_CAF = self.export_CARREFOURAFEUX(str_path_to_child)
            if sym_CAF:
                sym_CAFS.append(sym_CAF)
                self.list_symu_connexions.append(sym_CAF)
        return sym_CAFS

    @pyxbDecorator(pyxb_parser)
    def export_CARREFOURAFEUX(self, *args):
        """

        :return:
        """
        sym_CAF = None
        #
        sg3_node = self.cursor_symuvia['sg3_node']
        nb_edges_connected = len(sg3_node['array_str_edge_ids'])
        b_node_is_CAF = nb_edges_connected > 2  # dummy test
        if b_node_is_CAF:
            id_CAF = self.build_id_for_CAF(self.cursor_symuvia['node_id'])
            str_path_to_child, sym_CAF = pyxbDecorator.get_path_instance(
                *args,
                id=id_CAF,
                vit_max="1"
            )
            #
            self.select_CAF(sym_CAF)
            #
            sym_CAF.MOUVEMENTS_AUTORISES = self.export_MOUVEMENTS_AUTORISES(str_path_to_child)
            sym_CAF.ENTREES_CAF = self.export_ENTREES_CAF(str_path_to_child)
        #
        # print 'node_id: ', self.current['node_id']
        # print 'sg3_node: ', self.current['sg3_node']
        # print "sg3_node['edge_ids']:", self.current['sg3_node']['edge_ids']
        # print 'nb_edges_connected: ', nb_edges_connected
        #
        return sym_CAF

    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENTS_AUTORISES(self, *args):
        """

        :param node_id:
        :return:
        """
        str_path_to_child, sym_MOUVEMENTS_AUTORISES = pyxbDecorator.get_path_instance(*args)
        for mouvement_autorise in self.export_MOUVEMENT_AUTORISE(str_path_to_child):
            sym_MOUVEMENTS_AUTORISES.append(mouvement_autorise)
        return sym_MOUVEMENTS_AUTORISES


    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT_SORTIES(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_MOUVEMENT_SORTIES = pyxbDecorator.get_path_instance(*args)
        for mvt_sortie in self.export_MOUVEMENT_SORTIE(str_path_to_child):
            sym_MOUVEMENT_SORTIES.append(mvt_sortie)
        return sym_MOUVEMENT_SORTIES

    @pyxbDecorator(pyxb_parser)
    def export_ENTREES_CAF(self, *args):
        """

        :param node_id:
        :return:

        """
        str_path_to_child, sym_ENTREES_CAF = pyxbDecorator.get_path_instance(*args)
        for entree_caf in self.export_ENTREE_CAF(str_path_to_child):
            sym_ENTREES_CAF.append(entree_caf)
        return sym_ENTREES_CAF

    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENTS(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_MOUVEMENTS = pyxbDecorator.get_path_instance(*args)
        for mouvement in self.export_MOUVEMENT(str_path_to_child):
            sym_MOUVEMENTS.append(mouvement)
        return sym_MOUVEMENTS


    # ########################################################################################################
    ## Version autogenere en connectant tout ce qui est possible d'etre connecte
    #########################################################################################################
    # @pyxbDecorator(pyxb_parser)
    # def export_MOUVEMENT_AUTORISE(self, *args):
    #     """
    #
    #     :return:
    #     """
    #     str_path_to_child = pyxbDecorator.get_path(*args)
    #
    #     list_MOUVEMENT_AUTORISE = []
    #
    #     # CAF - IN
    #     sg3_node_caf_in = self.cursor_symuvia['sg3_node']['CAF']['in']
    #     for sym_troncon in sg3_node_caf_in:
    #
    #         ids_lanes = range(sym_troncon.nb_voie+1)[1:]
    #         for id_lane in ids_lanes:
    #
    #             sym_MOUVEMENT_AUTORISE = pyxbDecorator.get_instance(
    #                 *args,
    #                 id_troncon_amont=sym_troncon.id,
    #                 num_voie_amont=id_lane
    #             )
    #
    #             # MOUVEMENT_SORTIES
    #             sym_MOUVEMENT_AUTORISE.MOUVEMENT_SORTIES = self.export_MOUVEMENT_SORTIES(str_path_to_child)
    #
    #             #
    #             list_MOUVEMENT_AUTORISE.append(sym_MOUVEMENT_AUTORISE)
    #
    #             # [TOPO] - Link between TRONCON & CAF
    #             sym_troncon.id_eltaval = self.get_CAF().id
    #
    #     return list_MOUVEMENT_AUTORISE
    #
    # @pyxbDecorator(pyxb_parser)
    # def export_MOUVEMENT_SORTIE(self, *args):
    #     """
    #
    #     :return:
    #
    #     """
    #     list_mvt_sortie = []
    #     # CAF - OUT
    #     for sym_troncon in self.cursor_symuvia['sg3_node']['CAF']['out']:
    #         ids_lanes = range(sym_troncon.nb_voie+1)[1:]
    #         for id_lane in ids_lanes:
    #             sym_MOUVEMENT_SORTIE = pyxbDecorator.get_instance(*args)
    #             sym_MOUVEMENT_SORTIE.id_troncon_aval = sym_troncon.id
    #             sym_MOUVEMENT_SORTIE.num_voie_aval = id_lane
    #             # [TOPO] - Link between TRONCON & CAF
    #             sym_troncon.id_eltamont = self.get_CAF().id
    #             #
    #             list_mvt_sortie.append(sym_MOUVEMENT_SORTIE)
    #     return list_mvt_sortie
    #
    # @pyxbDecorator(pyxb_parser)
    # def export_ENTREE_CAF(self, *args):
    #     """
    #
    #     :return:
    #
    #     """
    #     str_path_to_child = pyxbDecorator.get_path(*args)
    #     list_entree_caf = []
    #     # CAF - IN
    #     for sym_troncon in self.cursor_symuvia['sg3_node']['CAF']['in']:
    #         ids_lanes = range(sym_troncon.nb_voie+1)[1:]
    #         for id_lane in ids_lanes:
    #             sym_ENTREE_CAF = pyxbDecorator.get_instance(*args)
    #             #
    #             sym_ENTREE_CAF.id_troncon_amont = sym_troncon.id
    #             sym_ENTREE_CAF.num_voie_amont = id_lane
    #             # [TOPO] - Link between TRONCON & CAF
    #             sym_troncon.id_eltaval = self.get_CAF().id
    #             #
    #             sym_ENTREE_CAF.MOUVEMENTS = self.export_MOUVEMENTS(str_path_to_child)
    #             #
    #             list_entree_caf.append(sym_ENTREE_CAF)
    #     return list_entree_caf
    #
    # @pyxbDecorator(pyxb_parser)
    # def export_MOUVEMENT(self, *args):
    #     """
    #
    #     :return:
    #
    #     """
    #     list_mouvement = []
    #     # CAF - OUT
    #     for sym_troncon in self.cursor_symuvia['sg3_node']['CAF']['out']:
    #         ids_lanes = range(sym_troncon.nb_voie+1)[1:]
    #         for id_lane in ids_lanes:
    #             sym_MOUVEMENT = pyxbDecorator.get_instance(*args)
    #             #
    #             sym_MOUVEMENT.id_troncon_aval = sym_troncon.id
    #             sym_MOUVEMENT.num_voie_aval = id_lane
    #             # [TOPO] - Link between TRONCON & CAF
    #             sym_troncon.id_eltamont = self.get_CAF().id
    #             #
    #             list_mouvement.append(sym_MOUVEMENT)
    #     return list_mouvement


    #########################################################################################################
    ## Version avec les interconnexions SG3
    #########################################################################################################
    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT_AUTORISE(self, *args):
        """

        :return:
        """
        str_path_to_child = pyxbDecorator.get_path(*args)

        list_MOUVEMENT_AUTORISE = []

        # CAF - IN
        sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions']
        for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():

            print '+-++-> key_for_troncon_lane_1: ', key_for_troncon_lane_1
            for interconnexion in list_interconnexions:
                print '\ amont + id_lane: ', interconnexion[0]
                print '\ aval  + id_lane: ', interconnexion[1]

            interconnexion = list_interconnexions[0]

            caf_amont_symu_troncon = interconnexion[0][0]
            caf_amont_id_lane = interconnexion[0][1]

            sym_MOUVEMENT_AUTORISE = pyxbDecorator.get_instance(
                *args,
                id_troncon_amont=caf_amont_symu_troncon.id,
                num_voie_amont=caf_amont_id_lane + 1  # convert id lane from Python -> SYMUVIA
            )

            # [TOPO] - Link between TRONCON & CAF
            caf_amont_symu_troncon.id_eltaval = self.get_CAF().id

            # MOUVEMENT_SORTIES
            self.cursor_symuvia['id_amont_troncon_lane'] = key_for_troncon_lane_1
            sym_MOUVEMENT_AUTORISE.MOUVEMENT_SORTIES = self.export_MOUVEMENT_SORTIES(str_path_to_child)

            #
            list_MOUVEMENT_AUTORISE.append(sym_MOUVEMENT_AUTORISE)

        return list_MOUVEMENT_AUTORISE

    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT_SORTIE(self, *args):
        """

        :return:

        """
        list_MOUVEMENT_SORTIE = []

        key_amont_troncon_lane = self.cursor_symuvia['id_amont_troncon_lane']
        list_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions'][key_amont_troncon_lane]

        for interconnexion in list_interconnexions:
            caf_aval_symu_troncon = interconnexion[1][0]
            caf_aval_id_lane = interconnexion[1][1]

            sym_MOUVEMENT_SORTIE = pyxbDecorator.get_instance(*args)
            sym_MOUVEMENT_SORTIE.id_troncon_aval = caf_aval_symu_troncon.id
            sym_MOUVEMENT_SORTIE.num_voie_aval = caf_aval_id_lane + 1  # convert id lane from Python -> SYMUVIA

            # [TOPO] - Link between TRONCON & CAF
            caf_aval_symu_troncon.id_eltamont = self.get_CAF().id

            #
            list_MOUVEMENT_SORTIE.append(sym_MOUVEMENT_SORTIE)

        return list_MOUVEMENT_SORTIE

    @pyxbDecorator(pyxb_parser)
    def export_ENTREE_CAF(self, *args):
        """

        :return:

        """
        str_path_to_child = pyxbDecorator.get_path(*args)

        list_ENTREE_CAF = []

        # CAF - IN
        sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions']
        for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():
            interconnexion = list_interconnexions[0]

            caf_amont_symu_troncon = interconnexion[0][0]
            caf_amont_id_lane = interconnexion[0][1]

            sym_ENTREE_CAF = pyxbDecorator.get_instance(
                *args,
                id_troncon_amont=caf_amont_symu_troncon.id,
                num_voie_amont=caf_amont_id_lane + 1  # convert id lane from Python -> SYMUVIA
            )

            # [TOPO] - Link between TRONCON & CAF
            caf_amont_symu_troncon.id_eltaval = self.get_CAF().id

            # MOUVEMENT_SORTIES
            self.cursor_symuvia['id_amont_troncon_lane'] = key_for_troncon_lane_1
            sym_ENTREE_CAF.MOUVEMENTS = self.export_MOUVEMENTS(str_path_to_child)

            #
            list_ENTREE_CAF.append(sym_ENTREE_CAF)

        return list_ENTREE_CAF

    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT(self, *args):
        """

        :return:

        """
        list_MOUVEMENT = []

        key_amont_troncon_lane = self.cursor_symuvia['id_amont_troncon_lane']
        list_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions'][key_amont_troncon_lane]

        for interconnexion in list_interconnexions:
            caf_aval_symu_troncon = interconnexion[1][0]
            caf_aval_id_lane = interconnexion[1][1]

            sym_MOUVEMENT = pyxbDecorator.get_instance(
                *args,
                id_troncon_aval=caf_aval_symu_troncon.id,
                num_voie_aval=caf_aval_id_lane + 1  # convert id lane from Python -> SYMUVIA
            )

            # [TOPO] - Link between TRONCON & CAF
            caf_aval_symu_troncon.id_eltamont = self.get_CAF().id

            #
            list_MOUVEMENT.append(sym_MOUVEMENT)

        return list_MOUVEMENT