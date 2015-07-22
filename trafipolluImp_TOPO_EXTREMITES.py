__author__ = 'latty'

from trafipolluImp_TOPO_tools import *

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)


class ModuleTopoExtremites(object):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:

        """
        #
        self.__dict_symu_extremites = {}
        #
        self.__module_topo_for_interconnexions = None
        # Update members with arguments
        self.__update_members(False, **kwargs)

    @property
    def dict_symu_extremites(self):
        return self.__dict_symu_extremites

    def get_set_edges_ids(self):
        return self.__dict_symu_extremites['set_edges_ids']

    def clear(self):
        """

        :return:

        """
        self.__dict_symu_extremites = {}

    def __update_members(self, test_validity=True, **kwargs):
        """

        :param kwargs:
        :return:

        """
        # Update members with arguments
        self.__module_topo_for_interconnexions = kwargs.setdefault(
            'module_topo_for_interconnexions',
            self.__module_topo_for_interconnexions
        )
        if self.__module_topo_for_interconnexions:
            self.__module_topo_for_troncons = self.__module_topo_for_interconnexions.module_topo_for_troncons

        # logger.fatal('Pas de module TOPO pour les interconnexions transmis !\n')
        assert test_validity or (self.__module_topo_for_interconnexions and self.__module_topo_for_troncons), \
            "Pas de module TOPO pour les interconnexions transmis !"

    def build(self, **kwargs):
        """

        :param kwargs:
        :return:

        """
        self.__update_members(**kwargs)

        dict_symu_troncons = self.__module_topo_for_troncons.dict_symu_troncons

        dict_symu_extremites = self.build_dict_extremites(dict_symu_troncons)

        if not kwargs.setdefault('staticmethod', False):
            self.__dict_symu_extremites.update(dict_symu_extremites)

        if not kwargs.setdefault('log_debug', False):
            self.log_debug(dict_symu_extremites)

        return dict_symu_extremites

    @staticmethod
    def build_dict_extremites(dict_symu_troncons):
        """

        :param dict_symu_troncons:
        :return:

        """
        nt_lists_extremites = ModuleTopoExtremites.build_list_extremites(dict_symu_troncons)
        dict_symu_extremites = {
            'ENTREES': nt_lists_extremites.list_entrees,
            'SORTIES': nt_lists_extremites.list_sorties,
            'set_edges_ids': nt_lists_extremites.set_edges_ids
        }

        return dict_symu_extremites

    @staticmethod
    def build_list_extremites(dict_symu_troncons):
        set_edges_ids = set()
        list_extremites_entrees = []
        list_extremites_sorties = []

        # on recupere la liste des symu troncons generes par module topo troncons
        for symu_troncon in dict_symu_troncons.values():
            type_extremite = ModuleTopoExtremites.find_type_extremite(symu_troncon)
            if type_extremite.is_entree:
                symu_extremite_id = 'E_' + symu_troncon.id
                # maj du lien symu troncon extremite
                symu_troncon.id_eltamont = symu_extremite_id
                #
                list_extremites_entrees.append(symu_extremite_id)
                # on met a jour la liste des id edges d'extremites
                set_edges_ids.add(symu_extremite_id)
            if type_extremite.is_sortie:
                symu_extremite_id = 'S_' + symu_troncon.id
                # maj du lien symu troncon extremite
                symu_troncon.id_eltaval = symu_extremite_id
                #
                list_extremites_sorties.append(symu_extremite_id)
                # on met a jour la liste des id edges d'extremites
                set_edges_ids.add(symu_extremite_id)

        return NT_LISTS_EXTREMITE(list_extremites_entrees, list_extremites_sorties, set_edges_ids)

    @staticmethod
    def log_debug(dict_symu_extremites):
        """

        :param dict_symu_extremites:
        :return:

        """
        # logger.info("dict_symu_extremites: {0:s}".format(dict_symu_extremites))
        logger.info(
            '%d (symu) extremites added\n\tnb ENTREES: %d\n\tnb SORTIES: %d' % (
                len(dict_symu_extremites['ENTREES']) + len(dict_symu_extremites['SORTIES']),
                len(dict_symu_extremites['ENTREES']),
                len(dict_symu_extremites['SORTIES'])
            )
        )

    @staticmethod
    def find_type_extremite(symu_troncon):
        """

        :param symu_troncon:
        :return:

        """
        is_entree = symu_troncon.id_eltamont == '-1'
        is_sortie = symu_troncon.id_eltaval == '-1'
        return NT_TYPE_EXTREMITE(is_entree, is_sortie)
