__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
from trafipolluImp_MixInF import MixInF

b_add_points_internes_for_interconnexions = True

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import build_logger

logger = build_logger(__name__)


# voir dans 'trafipolluImp_MixInF' pour des explications/liens
class trafipolluImp_EXPORT_CONNEXIONS(MixInF):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.dict_edges = kwargs['dict_edges']
        self.dict_lanes = kwargs['dict_lanes']
        self.dict_nodes = kwargs['dict_nodes']
        self.dict_roundabouts = kwargs['dict_roundabouts']
        self.list_symu_connexions = kwargs['list_symu_connexions']
        #
        self.pyxb_parser = pyxb_parser
        #
        self.cursor_symuvia = {
            #
            'sg3_node': None,
            'node_id': 0,
            'sym_CONNEXION': None,
            'id_amont_troncon_lane': "",
            #
            'ra_id': 0,
            'sg3_ra': None
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
            'REPARTITEUR': [],
            'GIRATOIRE': []
        }
        for node_id in self.dict_nodes:
            try:
                type_connexion = self.dict_nodes[node_id]['sg3_to_symuvia']['type_connexion']
            except Exception as e:
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

        if len(list_id_nodes_for_CONNEXIONS['GIRATOIRE']):
            sym_CONNEXIONS.GIRATOIRES = self.export_GIRATOIRES(
                list_id_nodes_for_CONNEXIONS['GIRATOIRE'],
                str_path_to_child
            )

        return sym_CONNEXIONS

    @pyxbDecorator(pyxb_parser)
    def export_GIRATOIRES(self, list_id_nodes, *args):
        """

        :param list_id_nodes:
        :param args:
        :return:
        """
        str_path_to_child, sym_GIRATOIRES = pyxbDecorator.get_path_instance(*args)

        logger.info('list_id_nodes: %s' % list_id_nodes)
        set_ra_ids = set(self.dict_nodes[node_id]['sg3_to_symuvia']['sg3_ra_id'] for node_id in list_id_nodes)
        logger.info('set_ra_ids: %s' % set_ra_ids)

        for ra_id in set_ra_ids:
            self.select_ra(ra_id)
            sym_GIRATOIRE = self.export_GIRATOIRE(str_path_to_child)
            sym_GIRATOIRES.append(sym_GIRATOIRE)
            self.list_symu_connexions.append(sym_GIRATOIRE)

        return sym_GIRATOIRES

    @pyxbDecorator(pyxb_parser)
    def export_GIRATOIRE(self, *args):
        """

        :return:
        """
        sym_GIRATOIRE = None

        try:
            id_GIRATOIRE = self.build_id_for_GIRATOIRE(self.cursor_symuvia['ra_id'])
        except Exception as e:
            logger.warning('Exception: %s' % e)
        else:
            sg3_ra = self.cursor_symuvia['sg3_ra']
            set_troncons_inoutgoing_for_ra = sg3_ra['set_troncons_inoutgoing']
            list_id_troncons_for_ra = [troncon_id for troncon_id in set_troncons_inoutgoing_for_ra]
            str_list_troncons_for_ra = " ".join(list_id_troncons_for_ra)
            try:
                str_path_to_child, sym_GIRATOIRE = pyxbDecorator.get_path_instance(
                    *args,
                    id=id_GIRATOIRE,
                    troncons=str_list_troncons_for_ra,
                    nb_voie=sg3_ra['nb_voie'],
                    LargeurVoie=sg3_ra['largeur_voie'],
                    vit_max="8"
                )
            except Exception as e:
                logger.warning('Exception: %s' % e)

                # sym_GIRATOIRE.TRONCONS_INTERNES = self.export_TRONCONS_INTERNES(str_path_to_child)

        return sym_GIRATOIRE

    @pyxbDecorator(pyxb_parser)
    def export_TRONCONS_INTERNES(self, *args):
        """

        :param args:
        :return:
        """
        str_path_to_child, sym_TRONCONS_INTERNES = pyxbDecorator.get_path_instance(*args)
        for troncon_interne in self.export_TRONCON_INTERNE(str_path_to_child):
            sym_TRONCONS_INTERNES.append(troncon_interne)
        return sym_TRONCONS_INTERNES

    @pyxbDecorator(pyxb_parser)
    def export_TRONCON_INTERNE(self, *args):
        """

        :param args:
        :return:
        """
        list_TRONCON_INTERNE = []
        sg3_ra = self.cursor_symuvia['sg3_ra']
        list_edges_ids_on_ra = sg3_ra['list_edges']

        for edge_id_on_ra in list_edges_ids_on_ra:
            try:
                sg3_edge_on_ra = self.dict_edges[edge_id_on_ra]

                np_edge_center_axis = sg3_edge_on_ra['np_edge_center_axis']

                sg3_start_node = self.dict_nodes[sg3_edge_on_ra['ui_start_node']]
                # #
                edges_inoutgoing_ra = list(sg3_start_node['sg3_to_symuvia']['set_edges_inoutgoing_ra'])
                # edge_inoutgoing_ra = edges_inoutgoing_ra[0]
                #
                str_path_to_child, sym_TRONCON_INTERNE = pyxbDecorator.get_path_instance(
                    *args,
                    id="toto",
                    troncon_amont="-1",
                    troncon_aval="-1",
                    extremite_amont="0.0 0.0",
                    extremite_aval="0.0 0.0"
                    # extremite_amont=np_edge_center_axis[0][0:2],
                    # extremite_aval=np_edge_center_axis[-1][0:2]
                )

                # POINTS INTERNES du TRONCON INTERNE

                # on ajoute le TRONCON INTERNE a la liste
                list_TRONCON_INTERNE.append(sym_TRONCON_INTERNE)
            except Exception as e:
                logger.warning('Exception: %s' % e)

        return list_TRONCON_INTERNE

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
        except Exception as e:
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
        except Exception as e:
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
            sg3_node_interconnexions = self.cursor_symuvia['sg3_node']['sg3_to_symuvia']['list_interconnexions']
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
                    sym_MOUVEMENT.POINTS_INTERNES = self.module_topo.build_pyxb_POINTS_INTERNES(interconnexion.geometry)

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

    def select_ra(self, ra_id):
        """

        :param ra_id:
        :return:
        """
        self.cursor_symuvia['ra_id'] = ra_id
        self.cursor_symuvia['sg3_ra'] = self.dict_roundabouts[ra_id]

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

    @staticmethod
    def build_id_for_GIRATOIRE(
            ra_id,
            prefix="G_"
    ):
        """

        :param ra_id:
        :return:
        """
        return prefix + str(ra_id)



