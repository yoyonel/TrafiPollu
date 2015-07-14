__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
from trafipolluImp_MixInF import MixInF

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


class trafipolluImp_EXPORT_TRAFICS(MixInF):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.transfer_arguments(['module_topo', 'list_symu_connexions'], **kwargs)
        #
        super(trafipolluImp_EXPORT_TRAFICS, self).__init__(**kwargs)

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
                list_troncons,
                list_connexions,
                list_extrimites,
                *args
        ):
            """

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

                #
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
            if list_troncons != []:
                sym_TRAFIC.TRONCONS = export_TRONCONS(list_troncons, str_path_to_child)
            if list_connexions != []:
                sym_TRAFIC.CONNEXIONS_INTERNES = export_CONNEXIONS_INTERNES(list_connexions, str_path_to_child)
            if list_extrimites != ():
                sym_TRAFIC.EXTREMITES = export_EXTREMITES(list_extrimites, str_path_to_child)

            return sym_TRAFIC

        str_path_to_child, sym_TRAFICS = pyxbDecorator.get_path_instance(*args)
        list_extremites = self.module_topo.dict_extremites['ENTREES']
        list_extremites.extend(self.module_topo.dict_extremites['SORTIES'])
        sym_TRAFICS.append(
            export_TRAFIC(
                self.module_topo.dict_pyxb_symutroncons.values(),
                self.list_symu_connexions,
                list_extremites,
                str_path_to_child
            )
        )
        return sym_TRAFICS
