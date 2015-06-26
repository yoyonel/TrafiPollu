__author__ = 'latty'

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import pyxbDecorator
from trafipolluImp_MixInF import MixInF


class trafipolluImp_EXPORT_TRAFICS(MixInF):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.list_symu_connexions = kwargs['list_symu_connexions']
        #
        self.module_topo = kwargs['module_topo']
        #
        super(trafipolluImp_EXPORT_TRAFICS, self).__init__(**kwargs)

    @pyxbDecorator(pyxb_parser)
    def export_TRAFICS(self, *args):
        """

        :param args:
        :return:

        """

        @pyxbDecorator(pyxb_parser)
        def export_TRAFIC(list_troncons, list_connexions, *args):
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
                    # print 'TRAFIC/TRONCONS/TRONCON - sym_TRONCON: ', sym_TRONCON
                    self.update_pyxb_node(
                        sym_TRONCON,
                        id=arg_sym_TRONCON.id,
                        agressivite='true'
                    )
                    return sym_TRONCON

                #
                # print 'TRAFIC/TRONCONS - args: ', args1
                str_path_to_child, sym_TRONCONS = pyxbDecorator.get_path_instance(*args)
                # print 'TRAFIC/TRONCONS - sym_TRONCONS: ', sym_TRONCONS
                # print 'TRAFIC/TRONCONS - str_path_to_child: ', str_path_to_child
                # print 'TRAFIC/TRONCONS - list_troncons: ', list_troncons
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
                    # print 'TRAFIC/TRONCONS/TRONCON - sym_TRONCON: ', sym_TRONCON
                    self.update_pyxb_node(
                        sym_CONNEXION_INTERNE,
                        id=sym_CAF.id
                    )
                    return sym_CONNEXION_INTERNE

                str_path_to_child, sym_CONNEXIONS_INTERNES = pyxbDecorator.get_path_instance(*args)
                for sym_CAF in list_connexions:
                    sym_CONNEXIONS_INTERNES.append(export_CONNEXION_INTERNE(sym_CAF, str_path_to_child))
                return sym_CONNEXIONS_INTERNES

            #
            # print 'TRAFIC - args: ', args
            str_path_to_child, sym_TRAFIC = pyxbDecorator.get_path_instance(*args)
            # print 'TRAFIC - str_path_to_child: ', str_path_to_child
            # print 'TRAFIC - sym_TRAFIC: ', sym_TRAFIC
            self.update_pyxb_node(
                sym_TRAFIC,
                id="trafID",
                accbornee="true",
                coeffrelax="0.55"
            )
            if list_troncons != []:
                sym_TRAFIC.TRONCONS = export_TRONCONS(list_troncons, str_path_to_child)
            if list_connexions != []:
                # print 'list_connexions: ', list_connexions
                sym_TRAFIC.CONNEXIONS_INTERNES = export_CONNEXIONS_INTERNES(list_connexions, str_path_to_child)
            return sym_TRAFIC

        str_path_to_child, sym_TRAFICS = pyxbDecorator.get_path_instance(*args)
        # print 'TRAFICS - str_path_to_child: ', str_path_to_child
        # print 'TRAFICS - sym_TRAFICS: ', sym_TRAFICS
        # print 'TRAFICS - self.list_troncons: ', self.list_troncons
        # sym_TRAFICS.append(export_TRAFIC(self.list_symu_troncons, self.list_symu_connexions, str_path_to_child))
        sym_TRAFICS.append(
            # export_TRAFIC(self.module_topo.dict_pyxb_symutroncons, self.list_symu_connexions, str_path_to_child)
            export_TRAFIC(
                self.module_topo.dict_pyxb_symutroncons.values(),
                self.list_symu_connexions,
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
