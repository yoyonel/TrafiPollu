__author__ = 'latty'

import pyxb

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
from imt_tools import print_exception


b_add_points_internes_for_interconnexions = True

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


# voir dans 'trafipolluImp_MixInF' pour des explications/liens
class trafipolluImp_EXPORT_CONNEXIONS(object):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.pyxb_parser = pyxb_parser
        #
        self.cursor_symuvia = {
            'sg3_node': None,
            'node_id': 0,
            'sym_CONNEXION': None,
            'id_amont_troncon_lane': "",
            'list_mouvements_entrees_for_troncon': []
        }
        #
        self.module_topo = kwargs['module_topo']

    @pyxbDecorator(pyxb_parser)
    def export_CONNEXIONS(self, *args):
        """

        :return:

        """
        str_path_to_child, sym_CONNEXIONS = pyxbDecorator.get_path_instance(*args)

        # dict_symu_connexions = self.module_topo.dict_symu_connexions
        # logger.info(u'dict_symu_connexions: {0:s}'.format(dict_symu_connexions))

        list_connexions_for_CAF = self.module_topo.dict_symu_connexions_caf
        if len(list_connexions_for_CAF):
            sym_CONNEXIONS.CARREFOURSAFEUX = self.export_CARREFOURSAFEUX(list_connexions_for_CAF, str_path_to_child)

        list_connexions_for_REPARTITEUR = self.module_topo.dict_symu_connexions_repartiteur
        if len(list_connexions_for_REPARTITEUR):
            sym_CONNEXIONS.REPARTITEURS = self.export_REPARTITEURS(list_connexions_for_REPARTITEUR, str_path_to_child)


        # list_id_nodes_for_CONNEXIONS = {
        # 'CAF': [],
        #     'REPARTITEUR': []
        # }
        # for node_id in self.dict_nodes:
        #     try:
        #         type_connexion = self.dict_nodes[node_id]['sg3_to_symuvia']['type_connexion']
        #     except Exception, e:
        #         logger.fatal('Exception: %s' % print_exception())
        #     else:
        #         list_id_nodes_for_CONNEXIONS[type_connexion].append(node_id)
        #
        # if len(list_id_nodes_for_CONNEXIONS['CAF']):
        #     sym_CONNEXIONS.CARREFOURSAFEUX = self.export_CARREFOURSAFEUX(
        #         list_id_nodes_for_CONNEXIONS['CAF'],
        #         str_path_to_child
        #     )
        #
        # if len(list_id_nodes_for_CONNEXIONS['REPARTITEUR']):
        #     sym_CONNEXIONS.REPARTITEURS = self.export_REPARTITEURS(
        #         list_id_nodes_for_CONNEXIONS['REPARTITEUR'],
        #         str_path_to_child
        #     )

        list_symu_extremites = self.module_topo.get_extremites_set_edges_ids()
        if list_symu_extremites:
            sym_CONNEXIONS.EXTREMITES = self.export_EXTREMITES(list_symu_extremites, str_path_to_child)

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

            # self.list_symu_connexions.append(sym_CAF)

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
            logger.fatal('Exception: %s' % print_exception())
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

            # self.list_symu_connexions.append(sym_REPARTITEUR)

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
            logger.fatal('Exception: %s' % print_exception())
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
            sg3_node_id = self.get_node_id()
            dict_mouvements_entrees_for_node = self.module_topo.get_dict_symu_mouvements_entrees_for_node(sg3_node_id)
            # logger.info(u'dict_symu_mouvements_entrees_for_node: {0:s}'.format(dict_symu_mouvements_entrees_for_node))
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for mouvement_entrees_id, list_mouvements_entrees_for_troncon in dict_mouvements_entrees_for_node.iteritems():
                logger.info('len(list_mouvements_entrees_for_troncon): %d' % len(list_mouvements_entrees_for_troncon))
                logger.info('mouvement_entrees_id: %s' % mouvement_entrees_id)
                #
                mouvement_entree = list_mouvements_entrees_for_troncon[0]
                # on recupere les informations sur l'amont
                nt_symu_lane_amont = mouvement_entree.nt_symuvia_lane_amont
                #
                amont_symu_troncon = nt_symu_lane_amont.symu_troncon
                amont_id_lane = nt_symu_lane_amont.id_lane

                # [TOPO] - Link between TRONCON & CAF
                amont_symu_troncon.id_eltaval = self.get_CONNEXION().id

                sym_MOUVEMENT_AUTORISE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=amont_symu_troncon.id,
                    num_voie_amont=amont_id_lane
                )
                # MOUVEMENT_SORTIES
                self.cursor_symuvia['list_mouvements_entrees_for_troncon'] = list_mouvements_entrees_for_troncon

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
            list_mouvements_entrees_for_troncons = self.cursor_symuvia['list_mouvements_entrees_for_troncon']
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            for mouvement_entree in list_mouvements_entrees_for_troncons:
                # on recupere les informations sur l'amont
                nt_lane_aval = mouvement_entree.nt_symuvia_lane_aval
                #
                aval_symu_troncon = nt_lane_aval.symu_troncon
                aval_id_lane = nt_lane_aval.id_lane

                # [TOPO] - Link between TRONCON & CAF
                aval_symu_troncon.id_eltamont = self.get_CONNEXION().id

                sym_MOUVEMENT_SORTIE = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=aval_symu_troncon.id,
                    num_voie_aval=aval_id_lane
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

        # CAF - IN
        try:
            sg3_node_id = self.get_node_id()
            # list_interconnexions = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
            dict_mouvements_entrees_for_node = self.module_topo.get_dict_symu_mouvements_entrees_for_node(sg3_node_id)
            # logger.info(u'dict_symu_mouvements_entrees_for_node: {0:s}'.format(dict_symu_mouvements_entrees_for_node))
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            str_path_to_child = pyxbDecorator.get_path(*args)
            for mouvement_entrees_id, list_mouvements_entrees_for_troncon in dict_mouvements_entrees_for_node.iteritems():
                #
                mouvement_entree = list_mouvements_entrees_for_troncon[0]
                # on recupere les informations sur l'amont
                nt_lane_amont = mouvement_entree.nt_symuvia_lane_amont
                #
                amont_symu_troncon = nt_lane_amont.symu_troncon
                amont_id_lane = nt_lane_amont.id_lane
                # [TOPO] - Link between TRONCON & CAF
                amont_symu_troncon.id_eltaval = self.get_CONNEXION().id
                sym_ENTREE_CAF = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_amont=amont_symu_troncon.id,
                    num_voie_amont=amont_id_lane
                )

                # MOUVEMENT_SORTIES
                self.cursor_symuvia['list_mouvements_entrees_for_troncon'] = list_mouvements_entrees_for_troncon

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
            list_mouvements_entrees_for_troncons = self.cursor_symuvia['list_mouvements_entrees_for_troncon']
        except Exception, e:
            logger.fatal('Exception: %s' % print_exception())
        else:
            for mouvement_entree in list_mouvements_entrees_for_troncons:
                # on recupere les informations sur l'amont
                nt_lane_aval = mouvement_entree.nt_symuvia_lane_aval
                #
                aval_symu_troncon = nt_lane_aval.symu_troncon
                aval_id_lane = nt_lane_aval.id_lane

                # [TOPO] - Link between TRONCON & CAF
                aval_symu_troncon.id_eltamont = self.get_CONNEXION().id

                #
                sym_MOUVEMENT = pyxbDecorator.get_instance(
                    *args,
                    id_troncon_aval=aval_symu_troncon.id,
                    num_voie_aval=aval_id_lane
                )

                #
                if b_add_points_internes_for_interconnexions:
                    sym_MOUVEMENT.POINTS_INTERNES = self.build_pyxb_POINTS_INTERNES(
                        mouvement_entree.interconnexion_geom
                    )

                # [TOPO] - Link between TRONCON & CAF
                aval_symu_troncon.id_eltamont = self.get_CONNEXION().id

                list_MOUVEMENT.append(sym_MOUVEMENT)

            return list_MOUVEMENT

    @staticmethod
    def build_pyxb_POINTS_INTERNES(list_points):
        """

        :param :
        :return:

        """
        pyxb_symuPOINTS_INTERNES = symuvia_parser.typePointsInternes()

        [pyxb_symuPOINTS_INTERNES.append(pyxb.BIND(coordonnees=[x[0], x[1]])) for x in list_points]
        return pyxb_symuPOINTS_INTERNES

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
        self.cursor_symuvia['sg3_node'] = self.module_topo.get_node(node_id)

    def get_node(self):
        return self.cursor_symuvia['sg3_node']

    def get_node_id(self):
        return self.cursor_symuvia['node_id']

    def select_CONNEXION(self, symu_connexion):
        """

        :param symu_connexion:
        :return:
        """
        self.cursor_symuvia['sym_CONNEXION'] = symu_connexion

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

        # @staticmethod
        # def build_id_python_to_symuvia(python_id):
        # """
        #
        #     :param python_id:
        #     :return:
        #
        #     """
        #     return python_id + 1