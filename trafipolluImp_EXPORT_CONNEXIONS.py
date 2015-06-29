__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
from trafipolluImp_MixInF import MixInF

# url: https://github.com/brentpayne/learning-python/blob/master/MixInMultipleInheritance/mixin_multiple_inheritance.py
class trafipolluImp_EXPORT_CONNEXIONS(MixInF):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.dict_edges = kwargs['dict_edges']
        self.dict_lanes = kwargs['dict_lanes']
        self.dict_nodes = kwargs['dict_nodes']
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
        self.list_symu_connexions = kwargs['list_symu_connexions']
        #
        self.module_topo = kwargs['module_topo']

        #
        super(trafipolluImp_EXPORT_CONNEXIONS, self).__init__(**kwargs)

    @pyxbDecorator(pyxb_parser)
    def export_CONNEXIONS(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_CONNEXIONS = pyxbDecorator.get_path_instance(*args)
        sym_CONNEXIONS.CARREFOURSAFEUX = self.export_CARREFOURSAFEUX(str_path_to_child)
        return sym_CONNEXIONS

    @pyxbDecorator(pyxb_parser)
    def export_CARREFOURSAFEUX(self, *args):
        """

        :param node_id:
        :return:
        # """

        # TODO: construction TOPO ici !
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
        sym_CARREFOURAFEUX = None

        try:
            sg3_node = self.cursor_symuvia['sg3_node']
            id_CAF = self.build_id_for_CAF(self.cursor_symuvia['node_id'])
        except Exception, e:
            pass
        else:
            str_path_to_child, sym_CARREFOURAFEUX = pyxbDecorator.get_path_instance(
                *args,
                id=id_CAF,
                vit_max="1"
            )
            #
            self.select_CAF(sym_CARREFOURAFEUX)
            #
            sym_CARREFOURAFEUX.MOUVEMENTS_AUTORISES = self.export_MOUVEMENTS_AUTORISES(str_path_to_child)
            sym_CARREFOURAFEUX.ENTREES_CAF = self.export_ENTREES_CAF(str_path_to_child)
            #
            # print 'node_id: ', self.current['node_id']
            # print 'sg3_node: ', self.current['sg3_node']
            # print "sg3_node['edge_ids']:", self.current['sg3_node']['edge_ids']
            # print 'nb_edges_connected: ', nb_edges_connected

        return sym_CARREFOURAFEUX

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

    #########################################################################################################
    ## Version avec les interconnexions SG3
    #########################################################################################################
    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT_AUTORISE(self, *args):
        """

        :return:
        """
        list_MOUVEMENT_AUTORISE = []

        # CAF - IN
        try:
            sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions']
        except Exception, e:
            pass
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():
                #
                # print '+-++-> key_for_troncon_lane_1: ', key_for_troncon_lane_1
                # for interconnexion in list_interconnexions:
                # print '\ amont + id_lane: ', interconnexion[0]
                # print '\ aval  + id_lane: ', interconnexion[1]

                # dans la liste (courante) d'interconnexions l'amont est constant
                # car le dictionnaire self.cursor_symuvia['sg3_node']['CAF_interconnexions'] a sa clee sur l'amont
                #
                # on recupere la 1ere interconnexion (par exemple)
                interconnexion = list_interconnexions[0]

                # on recupere les informations sur l'amont
                caf_amont = interconnexion.amont
                caf_amont_symu_troncon = caf_amont.symu_troncon
                caf_amont_id_lane = caf_amont.id_lane

                # convert id lane from Python -> SYMUVIA
                symu_lane_id = caf_amont_id_lane + 1

                sym_MOUVEMENT_AUTORISE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=caf_amont_symu_troncon.id,
                    num_voie_amont=symu_lane_id
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

        try:
            key_amont_troncon_lane = self.cursor_symuvia['id_amont_troncon_lane']
            list_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions'][key_amont_troncon_lane]
        except Exception, e:
            pass
        else:
            for interconnexion in list_interconnexions:
                caf_aval = interconnexion.aval
                caf_aval_symu_troncon = caf_aval.symu_troncon
                caf_aval_id_lane = caf_aval.id_lane

                # convert id lane from Python -> SYMUVIA
                symu_lane_id = caf_aval_id_lane + 1

                sym_MOUVEMENT_SORTIE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=caf_aval_symu_troncon.id,
                    num_voie_aval=symu_lane_id
                )

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
        list_ENTREE_CAF = []

        try:
            # CAF - IN
            sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions']
        except Exception, e:
            pass
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():
                interconnexion = list_interconnexions[0]

                sg3_caf_amont = interconnexion.amont

                caf_amont_symu_troncon = sg3_caf_amont.symu_troncon
                python_amont_lane_id = sg3_caf_amont.id_lane

                # convert id lane from Python -> SYMUVIA
                symu_lane_id = python_amont_lane_id + 1

                sym_ENTREE_CAF = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=caf_amont_symu_troncon.id,
                    num_voie_amont=symu_lane_id
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

        try:
            key_amont_troncon_lane = self.cursor_symuvia['id_amont_troncon_lane']
            list_interconnexions = self.cursor_symuvia['sg3_node']['CAF_interconnexions'][key_amont_troncon_lane]
        except Exception, e:
            pass
        else:
            for interconnexion in list_interconnexions:
                caf_aval = interconnexion.aval
                caf_aval_symu_troncon = caf_aval.symu_troncon
                caf_aval_id_lane = caf_aval.id_lane

                sym_MOUVEMENT = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=caf_aval_symu_troncon.id,
                    num_voie_aval=caf_aval_id_lane + 1  # convert id lane from Python -> SYMUVIA
                )

                # print 'interconnexion.geometry: ', interconnexion.geometry
                # sym_MOUVEMENT.POINTS_INTERNES = self.module_topo.build_pyxb_POINTS_INTERNES(interconnexion.geometry[1:-1])
                sym_MOUVEMENT.POINTS_INTERNES = self.module_topo.build_pyxb_POINTS_INTERNES(interconnexion.geometry)

                # [TOPO] - Link between TRONCON & CAF
                caf_aval_symu_troncon.id_eltamont = self.get_CAF().id

                #
                list_MOUVEMENT.append(sym_MOUVEMENT)

        return list_MOUVEMENT

    def select_node(self, node_id):
        """

        :param node_id:
        """
        self.cursor_symuvia['node_id'] = node_id
        self.cursor_symuvia['sg3_node'] = self.dict_nodes[node_id]

    def select_CAF(self, sym_CAF):
        """

        :param sym_CAF:
        :return:
        """
        self.cursor_symuvia['sym_CAF'] = sym_CAF

    def get_CAF(self):
        """

        :return:
        """
        return self.cursor_symuvia['sym_CAF']

    @staticmethod
    def build_id_for_CAF(node_id):
        """

        :param node_id:
        :return:
        """
        return 'CAF_' + str(node_id)