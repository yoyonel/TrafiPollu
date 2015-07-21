__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


class trafipolluImp_EXPORT_TRAFICS(object):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.module_topo = kwargs['module_topo']

    # Le decorator pyxbDecorator utilise les noms des methodes export_<Type_PYXB> pour retrouver les paths des types
    # (complexes, ...) XML a construire/instancien.
    # Le probleme c'est que certains types comme: TRONCONS, TRONCON sont des homonimies pour d'autres structures:
    # RESEAUX/RESEAU par exemple.
    # Le probleme (homonimie) vient aussi de notre strategie d'heritage utilisee pour transmettre les methodes d'export
    # a la classe mere trafipolluImp_EXPORT.
    # Du coup dans le meme namespace de la classe mere (trafipolluImp_EXPORT) on a des conflits sur les methodes:
    # export_TRONCONS, export_TRONCON, ...
    # La methode de resolution utilisee a ete de recreer un nouveau namespace 'local' lie au noeud racine 'TRAFICS'
    # d'ou l'utilisation des methodes imbriquees (qui revient au meme en terme de namespace que l'utilisation d'un
    # system de classes imbriquees.
    @pyxbDecorator(pyxb_parser)
    def export_TRAFICS(self, *args):
        """

        :param args:
        :return:

        """

        @pyxbDecorator(pyxb_parser)
        def export_TRAFIC(
                dict_symuvia_objects,
                *args
        ):
            """

            :param dict_symuvia_objects:
            :param args:
            :return:
            """

            @pyxbDecorator(pyxb_parser)
            def export_TRONCONS(list_troncons, *args):
                """

                """

                @pyxbDecorator(pyxb_parser)
                def export_TRONCON(arg_sym_TRONCON, *args):
                    """

                    """
                    sym_TRONCON = pyxbDecorator.get_instance(*args)
                    self.update_pyxb_node(
                        sym_TRONCON,
                        id=arg_sym_TRONCON.id,
                        agressivite='true'
                    )
                    return sym_TRONCON

                str_path_to_child, sym_TRONCONS = pyxbDecorator.get_path_instance(*args)
                for sym_TRONCON in list_troncons:
                    sym_TRONCONS.append(export_TRONCON(sym_TRONCON, str_path_to_child))
                return sym_TRONCONS

            #
            @pyxbDecorator(pyxb_parser)
            def export_CONNEXIONS_INTERNES(list_connexions, *args):
                """

                """

                @pyxbDecorator(pyxb_parser)
                def export_CONNEXION_INTERNE(sym_CAF, *args):
                    """

                    """
                    sym_CONNEXION_INTERNE = pyxbDecorator.get_instance(*args)
                    self.update_pyxb_node(
                        sym_CONNEXION_INTERNE,
                        id=sym_CAF.id
                    )
                    return sym_CONNEXION_INTERNE

                #
                str_path_to_child, sym_CONNEXIONS_INTERNES = pyxbDecorator.get_path_instance(*args)
                for sym_CAF in list_connexions:
                    sym_CONNEXIONS_INTERNES.append(export_CONNEXION_INTERNE(sym_CAF, str_path_to_child))
                return sym_CONNEXIONS_INTERNES

            #
            @pyxbDecorator(pyxb_parser)
            def export_EXTREMITES(list_extrimites, *args):
                """

                """

                @pyxbDecorator(pyxb_parser)
                def export_EXTREMITE(id_extremite, *args):
                    """

                    """
                    sym_EXTREMITE = pyxbDecorator.get_instance(*args)
                    self.update_pyxb_node(
                        sym_EXTREMITE,
                        id=id_extremite
                    )
                    return sym_EXTREMITE

                #
                str_path_to_child, sym_EXTREMITES = pyxbDecorator.get_path_instance(*args)
                for id_extremite in list_extrimites:
                    sym_EXTREMITES.append(export_EXTREMITE(id_extremite, str_path_to_child))
                return sym_EXTREMITES

            #
            str_path_to_child, sym_TRAFIC = pyxbDecorator.get_path_instance(*args)
            self.update_pyxb_node(
                sym_TRAFIC,
                id="trafID",
                accbornee="true",
                coeffrelax="0.55"
            )

            list_symu_troncons = dict_symuvia_objects.setdefault('list_symu_troncons', [])
            # logger.info('list_symu_troncons: %s' % list_symu_troncons)
            if list_symu_troncons:
                sym_TRAFIC.TRONCONS = export_TRONCONS(list_symu_troncons, str_path_to_child)

            list_symu_extremites = dict_symuvia_objects.setdefault('list_symu_extremites', [])
            if list_symu_extremites:
                sym_TRAFIC.EXTREMITES = export_EXTREMITES(list_symu_extremites, str_path_to_child)

            # if list_connexions != []:
            # sym_TRAFIC.CONNEXIONS_INTERNES = export_CONNEXIONS_INTERNES(list_connexions, str_path_to_child)

            return sym_TRAFIC

        str_path_to_child, sym_TRAFICS = pyxbDecorator.get_path_instance(*args)

        # list_extremites = self.module_topo.dict_extremites['ENTREES']
        # list_extremites.extend(self.module_topo.dict_extremites['SORTIES'])

        sym_TRAFICS.append(
            export_TRAFIC(
                {
                    'list_symu_troncons': self.module_topo.dict_symu_troncons.values(),
                    'list_symu_extremites': self.module_topo.get_extremites_set_edges_ids()
                },
                str_path_to_child
            )
        )
        return sym_TRAFICS

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)
