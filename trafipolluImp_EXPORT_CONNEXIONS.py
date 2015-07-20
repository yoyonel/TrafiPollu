__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
from trafipolluImp_MixInF import MixInF

b_add_points_internes_for_interconnexions = True

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


# voir dans 'trafipolluImp_MixInF' pour des explications/liens
class trafipolluImp_EXPORT_CONNEXIONS(MixInF):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.transfer_arguments(
            [
                'dict_edges',
                'dict_lanes',
                'dict_nodes',
                'list_symu_connexions'
            ],
            **kwargs
        )
        #
        self.pyxb_parser = pyxb_parser
        #
        self.cursor_symuvia = {
            'sg3_node': None,
            'node_id': 0,
            'sym_CONNEXION': None,
            'id_amont_troncon_lane': ""
        }
        #
        super(trafipolluImp_EXPORT_CONNEXIONS, self).__init__(**kwargs)

    @pyxbDecorator(pyxb_parser)
    def export_CONNEXIONS(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_CONNEXIONS = pyxbDecorator.get_path_instance(*args)

        list_id_nodes_for_CONNEXIONS = {
            'CAF': [],
            'REPARTITEUR': []
        }
        for node_id in self.dict_nodes:
            try:
                type_connexion = self.dict_nodes[node_id]['sg3_to_symuvia']['type_connexion']
            except Exception, e:
                logger.fatal('Exception: %s' % e)
            else:
                list_id_nodes_for_CONNEXIONS[type_connexion].append(node_id)

        if len(list_id_nodes_for_CONNEXIONS['CAF']):
            sym_CONNEXIONS.CARREFOURSAFEUX = self.export_CARREFOURSAFEUX(
                list_id_nodes_for_CONNEXIONS['CAF'],
                str_path_to_child
            )

        if len(list_id_nodes_for_CONNEXIONS['REPARTITEUR']):
            sym_CONNEXIONS.REPARTITEURS = self.export_REPARTITEURS(
                list_id_nodes_for_CONNEXIONS['REPARTITEUR'],
                str_path_to_child
            )

        list_extrimites = self.module_topo.dict_extremites['ENTREES']
        list_extrimites.extend(self.module_topo.dict_extremites['SORTIES'])
        if len(list_extrimites):
            sym_CONNEXIONS.EXTREMITES = self.export_EXTREMITES(
                list_extrimites,
                str_path_to_child
            )

        return sym_CONNEXIONS

    @pyxbDecorator(pyxb_parser)
    def export_CARREFOURSAFEUX(self, list_id_nodes, *args):
        """

        :param node_id:
        :return:
        # """
        str_path_to_child, sym_CAFS = pyxbDecorator.get_path_instance(*args)

        for node_id in list_id_nodes:
            self.select_node(node_id)

            sym_CAF = self.export_CARREFOURAFEUX(str_path_to_child)

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
            self.select_CONNEXION(sym_CARREFOURAFEUX)
            #
            sym_CARREFOURAFEUX.MOUVEMENTS_AUTORISES = self.export_MOUVEMENTS_AUTORISES(str_path_to_child)
            sym_CARREFOURAFEUX.ENTREES_CAF = self.export_ENTREES_CAF(str_path_to_child)

        return sym_CARREFOURAFEUX

    @pyxbDecorator(pyxb_parser)
    def export_REPARTITEURS(self, list_id_nodes, *args):
        """

        :param node_id:
        :return:
        # """
        str_path_to_child, sym_REPARTITEURS = pyxbDecorator.get_path_instance(*args)

        for node_id in list_id_nodes:
            self.select_node(node_id)

            sym_REPARTITEUR = self.export_REPARTITEUR(str_path_to_child)

            sym_REPARTITEURS.append(sym_REPARTITEUR)

            self.list_symu_connexions.append(sym_REPARTITEUR)

        return sym_REPARTITEURS

    @pyxbDecorator(pyxb_parser)
    def export_REPARTITEUR(self, *args):
        """

        :return:
        """
        sym_REPARTITEUR = None

        try:
            id_REPARTITEUR = self.build_id_for_REPARTITEUR(self.cursor_symuvia['node_id'])
        except Exception, e:
            pass
        else:
            str_path_to_child, sym_REPARTITEUR = pyxbDecorator.get_path_instance(
                *args,
                id=id_REPARTITEUR
            )
            #
            self.select_CONNEXION(sym_REPARTITEUR)
            #
            sym_REPARTITEUR.MOUVEMENTS_AUTORISES = self.export_MOUVEMENTS_AUTORISES(str_path_to_child)

        return sym_REPARTITEUR

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
    # # Version avec les interconnexions SG3
    #########################################################################################################
    @pyxbDecorator(pyxb_parser)
    def export_MOUVEMENT_AUTORISE(self, *args):
        """

        :return:
        """
        list_MOUVEMENT_AUTORISE = []

        # CAF - IN
        try:
            sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
        except Exception, e:
            pass
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():
                #
                # dans la liste (courante) d'interconnexions l'amont est constant
                # car le dictionnaire self.cursor_symuvia['sg3_node']['sg3_to_symuvia'] a sa clee sur l'amont
                #
                # on recupere la 1ere interconnexion (par exemple)
                interconnexion = list_interconnexions[0]

                # on recupere les informations sur l'amont
                lane_amont = interconnexion.lane_amont
                #
                lane_amont_symu_troncon = lane_amont.symu_troncon
                lane_amont_id_lane = lane_amont.id_lane

                # [TOPO] - Link between TRONCON & CAF
                lane_amont_symu_troncon.id_eltaval = self.get_CONNEXION().id

                # convert id lane from Python -> SYMUVIA
                symu_lane_id = self.build_id_python_to_symuvia(lane_amont_id_lane)
                sym_MOUVEMENT_AUTORISE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=lane_amont_symu_troncon.id,
                    num_voie_amont=symu_lane_id
                )

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
            list_interconnexions_for_node = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
            list_interconnexions = list_interconnexions_for_node[key_amont_troncon_lane]
        except Exception, e:
            pass
        else:
            for interconnexion in list_interconnexions:
                aval = interconnexion.lane_aval
                # aval = interconnexion.lane_amont

                aval_symu_troncon = aval.symu_troncon
                aval_id_lane = aval.id_lane

                # [TOPO] - Link between TRONCON & CAF
                aval_symu_troncon.id_eltamont = self.get_CONNEXION().id

                # convert id lane from Python -> SYMUVIA
                symu_lane_id = self.build_id_python_to_symuvia(aval_id_lane)
                #
                sym_MOUVEMENT_SORTIE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=aval_symu_troncon.id,
                    num_voie_aval=symu_lane_id
                )

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
            sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
        except Exception, e:
            pass
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for key_for_troncon_lane_1, list_interconnexions in sg3_node_interconnexions.iteritems():
                interconnexion = list_interconnexions[0]

                sg3_caf_amont = interconnexion.lane_amont
                # sg3_caf_amont = interconnexion.lane_aval

                caf_amont_symu_troncon = sg3_caf_amont.symu_troncon

                # [TOPO] - Link between TRONCON & CAF
                caf_amont_symu_troncon.id_eltaval = self.get_CONNEXION().id

                python_amont_lane_id = sg3_caf_amont.id_lane
                # convert id lane from Python -> SYMUVIA
                symu_lane_id = self.build_id_python_to_symuvia(python_amont_lane_id)

                sym_ENTREE_CAF = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=caf_amont_symu_troncon.id,
                    num_voie_amont=symu_lane_id
                )

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
            list_interconnexions_for_node = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
            list_interconnexions = list_interconnexions_for_node[key_amont_troncon_lane]
        except Exception, e:
            pass
        else:
            for interconnexion in list_interconnexions:
                aval = interconnexion.lane_aval
                # aval = interconnexion.lane_amont

                aval_symu_troncon = aval.symu_troncon

                # [TOPO] - Link between TRONCON & CAF
                aval_symu_troncon.id_eltamont = self.get_CONNEXION().id

                #
                aval_id_lane = aval.id_lane
                sym_id_lane = self.build_id_python_to_symuvia(aval_id_lane)
                sym_MOUVEMENT = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=aval_symu_troncon.id,
                    num_voie_aval=sym_id_lane  # convert id lane : Python -> SYMUVIA
                )

                if b_add_points_internes_for_interconnexions:
                    sym_MOUVEMENT.POINTS_INTERNES = self.module_topo.__build_pyxb_troncon_points_internes(
                        interconnexion.geometry)

                #
                list_MOUVEMENT.append(sym_MOUVEMENT)

        return list_MOUVEMENT

    @pyxbDecorator(pyxb_parser)
    def export_EXTREMITES(self, list_extremites, *args):
        """

        :param list_extremites:
        :param args:
        :return:

        """
        str_path_to_child, sym_EXTREMITES = pyxbDecorator.get_path_instance(*args)
        for id_extremite in list_extremites:
            sym_EXTREMITES.append(self.export_EXTREMITE(id_extremite, str_path_to_child))
        return sym_EXTREMITES

    @pyxbDecorator(pyxb_parser)
    def export_EXTREMITE(self, id_extremite, *args):
        """

        :param args:
        :return:

        """
        return pyxbDecorator.get_instance(
            *args,
            id=id_extremite
        )

    def select_node(self, node_id):
        """

        :param node_id:
        """
        self.cursor_symuvia['node_id'] = node_id
        self.cursor_symuvia['sg3_node'] = self.dict_nodes[node_id]

    def select_CONNEXION(self, sym_CONNEXION):
        """

        :param sym_CONNEXION:
        :return:
        """
        self.cursor_symuvia['sym_CONNEXION'] = sym_CONNEXION

    def get_CONNEXION(self):
        """

        :return:
        """
        return self.cursor_symuvia['sym_CONNEXION']

    @staticmethod
    def build_id_for_CONNEXION(str_id_connexion, node_id):
        """

        :param str_id_connexion:
        :param node_id:
        :return:
        """
        return str_id_connexion + str(node_id)

    @staticmethod
    def build_id_for_CAF(node_id):
        """

        :param node_id:
        :return:
        """
        return trafipolluImp_EXPORT_CONNEXIONS.build_id_for_CONNEXION('CAF_', node_id)

    @staticmethod
    def build_id_for_REPARTITEUR(node_id):
        """

        :param node_id:
        :return:
        """
        return trafipolluImp_EXPORT_CONNEXIONS.build_id_for_CONNEXION('REP_', node_id)

    @staticmethod
    def build_id_python_to_symuvia(python_id):
        """

        :param python_id:
        :return:

        """
        return python_id + 1