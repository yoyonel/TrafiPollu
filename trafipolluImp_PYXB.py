__author__ = 'atty'

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import build_logger

logger = build_logger(__name__)


class trafipolluImp_PYXB(object):
    """

    """

    def __init__(self, parser):
        """

        :param parser:
        :return:
        """
        self.pyxb_tree_ctd = {}
        #
        ctd_root_node = parser.ROOT_SYMUBRUIT
        self.dump_pyxb_tree(('ROOT_SYMUBRUIT', ctd_root_node))

    def dump_pyxb_tree(self, tuple_Name_CTD, prefix=""):
        """

        :param root:
        :param prefix:
        :return:
        """
        #
        node_parent = tuple_Name_CTD[1]
        tp_node_parent = node_parent.typeDefinition()
        prefix_node = prefix + tuple_Name_CTD[0]
        #
        self.pyxb_tree_ctd[prefix_node] = node_parent.typeDefinition()
        #
        for child_pyxb in tp_node_parent._ElementMap:
            uri_child = child_pyxb.uriTuple()[1]
            node_child = node_parent.memberElement(uri_child)
            self.dump_pyxb_tree((uri_child, node_child), prefix_node + '/')

    def get_CTD(self, path_to_CTD, update_dict=True):
        """

        :param path_to_CTD:
        :return:
        """
        try:
            return self.pyxb_tree_ctd[path_to_CTD]
        except KeyError:
            # cherche les clees avec le suffixe path_to_CTD
            # potentiellement il peut avoir plusieurs cles repondant au critere de suffixe
            l_key = filter(
                lambda x: x.endswith(path_to_CTD),
                self.pyxb_tree_ctd.keys()
            )
            l_ctd = map(lambda x: self.pyxb_tree_ctd[x], l_key)
            # si on ne trouve qu'une clee
            # -> on met a jour le dictionnaire pour retrouver directement le resultat a la prochaine requete
            if update_dict and len(l_key) == 1:
                self.pyxb_tree_ctd[path_to_CTD] = l_ctd[0]
                # print "-_- Found one occurence ! : %s -_-" % str(l_ctd[0])
            if len(l_key) > 1:
                print "!!! WARNING: multiple occurences found !!!"
            # debug: tuple listes des classes et cles (paths)
            try:
                return l_ctd[0]
            except:
                return None

    def get_instance(self, path_to_CTD, update_dict=True, **kwargs):
        """

        :param path_to_CTD:
        :param update_dict:
        :return:
        """
        try:
            CTD = self.get_CTD(path_to_CTD, update_dict)
            return CTD(**kwargs)
        except:
            return None


pyxb_parser = trafipolluImp_PYXB(symuvia_parser)


class pyxbDecorator(object):
    """

    """

    def __init__(self, parser_pyxb):
        self.parser_pyxb = parser_pyxb
        self.pyxb_result = ()

    def __call__(self, f):
        """
        """

        def wrapped_f(*args):
            """
            """
            if self.pyxb_result == ():
                str_child_name = f.__name__[7:]  # 7 = len('export_')
                str_parent = args[-1]
                if type(str_parent) is tuple:
                    str_parent = str_parent[0]
                str_path_to_child = str_parent + '/' + str_child_name
                sym_NODE = self.parser_pyxb.get_instance(str_path_to_child)
                self.pyxb_result = (str_child_name, sym_NODE)
            # update de la liste des arguments
            # on rajoute en fin de liste le tuple : (nom du child, instance de l'element)
            args = list(args)
            args.append(self.pyxb_result)
            args = iter(args)
            return f(*args)

        return wrapped_f

    @staticmethod
    def get_path(*args):
        """
        """
        return args[-2] + '/' + args[-1][0]

    @staticmethod
    def get_instance(*args, **kwargs):
        """
        """
        return pyxb_parser.get_instance(pyxbDecorator.get_path(*args), **kwargs)

    @staticmethod
    def get_path_instance(*args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        str_parent = args[-2]
        str_child = args[-1][0]
        str_path_to_child = str_parent + '/' + str_child
        sym_NODE = pyxb_parser.get_instance(str_path_to_child, **kwargs)
        return str_path_to_child, sym_NODE

    @staticmethod
    def get_path_from_args(*args):
        """
        """
        return args[-1]