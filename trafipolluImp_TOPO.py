__author__ = 'latty'

from trafipolluImp_TOPO_TRONCONS import ModuleTopoTroncons
from trafipolluImp_TOPO_CONNEXIONS import ModuleTopoConnexions
from trafipolluImp_TOPO_EXTREMITES import ModuleTopoExtremites

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)


class ModuleTopo(object):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        """
        #
        self.__dict_sg3_to_symuvia = {}
        # from DUMP
        self.__object_DUMP = kwargs.setdefault('object_DUMP', None)

        # 'chaine' entre les modules: DUMP -> TOPO_TRONCONS -> TOPO_INTERCONNEXIONS -> TOPO_EXTRIMITES
        self.module_topo_for_troncons = ModuleTopoTroncons(object_DUMP=self.object_DUMP)
        self.module_topo_for_connexions = ModuleTopoConnexions(
            module_topo_for_troncons=self.module_topo_for_troncons
        )
        self.module_topo_for_extremites = ModuleTopoExtremites(
            module_topo_for_interconnexions=self.module_topo_for_connexions
        )

    def clear(self):
        """

        :return:

        """
        self.__dict_sg3_to_symuvia = {}
        self.module_topo_for_troncons.clear()
        self.module_topo_for_connexions.clear()
        self.module_topo_for_extremites.clear()

    def build(self, *args, **kwargs):
        """

        :return:
        """
        self.module_topo_for_troncons.build(**kwargs)
        self.module_topo_for_connexions.build(**kwargs)
        self.module_topo_for_extremites.build(**kwargs)

    @property
    def dict_symu_troncons(self):
        return self.module_topo_for_troncons.dict_symu_troncons

    @property
    def dict_symu_extremites(self):
        return self.module_topo_for_extremites.dict_symu_extremites

    @property
    def object_DUMP(self):
        return self.__object_DUMP

    @property
    def dict_symu_connexions(self):
        return self.module_topo_for_connexions.dict_symu_connexions

    @property
    def dict_symu_connexions_caf(self):
        return self.module_topo_for_connexions.dict_symu_connexions_caf

    @property
    def dict_symu_connexions_repartiteur(self):
        return self.module_topo_for_connexions.dict_symu_connexions_repartiteur

    @property
    def dict_symu_mouvements_entrees(self):
        return self.module_topo_for_connexions.dict_symu_mouvements_entrees

    def get_extremites_set_edges_ids(self):
        return self.module_topo_for_extremites.get_set_edges_ids()

    def get_node(self, sg3_node_id):
        """

        :param sg3_node_id:
        :return:

        """
        return self.object_DUMP.get_node(sg3_node_id)

    def get_list_interconnexions(self, sg3_node_id):
        return self.object_DUMP.get_interconnexions(sg3_node_id)

    def get_dict_symu_mouvements_entrees_for_node(self, sg3_node_id):
        return self.dict_symu_mouvements_entrees[sg3_node_id]
