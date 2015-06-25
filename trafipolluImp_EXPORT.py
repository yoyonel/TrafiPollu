__author__ = 'latty'

import os

import pyxb

# import parser_symuvia_xsd_2_04_pyxb as symuvia_parser
# import trafipolluImp_PYXB as module_pyxb_parser

# pyxb_parser = module_pyxb_parser.trafipolluImp_PYXB(symuvia_parser)

from trafipolluImp_PYXB import pyxb_parser
from trafipolluImp_PYXB import symuvia_parser
from trafipolluImp_PYXB import pyxbDecorator

from trafipolluImp_EXPORT_CONNEXIONS import trafipolluImp_EXPORT_CONNEXIONS

qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))
#
infilename_for_symuvia = qgis_plugins_directory + '/' + "project_empty_from_symunet" + "_xsd_" + "2_04" + ".xml"
outfilename_for_symuvia = qgis_plugins_directory + '/' + "export_from_sg3_to_symuvia" + "_xsd_" + "2_04" + ".xml"


class trafipolluImp_EXPORT(trafipolluImp_EXPORT_CONNEXIONS):
    """

    """
    def __init__(self, dict_edges, dict_lanes, dict_nodes, module_topo, infilename=infilename_for_symuvia):
        """

        """
        self.dict_edges = dict_edges
        self.dict_lanes = dict_lanes
        self.dict_nodes = dict_nodes
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
        self.list_symu_connexions = []
        #
        print "trafipolluImp_EXPORT - Open file: ", infilename, "..."
        xml = open(infilename).read()
        self.symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        print "trafipolluImp_EXPORT - Open file: ", infilename, "[DONE]"
        #
        self.symu_ROOT_RESEAU_TRONCONS = None
        self.symu_ROOT_RESEAU_CONNEXIONS = None
        self.symu_ROOT_TRAFICS = None

        self.module_topo = module_topo

        super(trafipolluImp_EXPORT, self).__init__(
            dict_edges,
            dict_lanes,
            dict_nodes,
            module_topo,
            self.list_symu_connexions
        )

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

    def update_TRONCONS(self):
        """

        :return:
        """
        self.symu_ROOT_RESEAU_TRONCONS = self.export_TRONCONS('RESEAU')

    def update_CONNEXIONS(self):
        """

        :return:
        """
        self.symu_ROOT_RESEAU_CONNEXIONS = self.export_CONNEXIONS('RESEAU')

    def update_TRAFICS(self):
        """

        :return:
        """
        self.symu_ROOT_TRAFICS = self.export_TRAFICS('ROOT_SYMUBRUIT')

    def update_SYMUVIA(self):
        """

        :return:
        """
        print "Update SYMUVIA ..."
        self.update_TRONCONS()
        # self.update_CONNEXIONS()
        self.update_TRAFICS()
        #
        print "Update SYMUVIA [DONE]"

    def export(self, update_symu=False, outfilename=outfilename_for_symuvia):
        """

        :param filename:
        :return:
        """

        if update_symu:
            self.update_SYMUVIA()
            #
            b_add_trafics = False
            if self.module_topo.dict_pyxb_symutroncons:
                self.symu_ROOT.RESEAUX.RESEAU[0].TRONCONS = self.symu_ROOT_RESEAU_TRONCONS
                b_add_trafics = True
            if self.list_symu_connexions != []:
                self.symu_ROOT.RESEAUX.RESEAU[0].CONNEXIONS = self.symu_ROOT_RESEAU_CONNEXIONS
                b_add_trafics = True
            if b_add_trafics:
                self.symu_ROOT.TRAFICS = self.symu_ROOT_TRAFICS

        #
        self.save_ROOT(self.symu_ROOT, outfilename)

    def save_ROOT(self, sym_ROOT, outfilename):
        """

        :return:
        """
        return self.save_SYMUVIA_Node('ROOT_SYMUBRUIT', sym_ROOT, outfilename)

    @staticmethod
    def save_SYMUVIA_Node(element_name, sym_node, outfilename, prettyxml=True):
        """

        :param sym_node:
        :param outfilename:
        :return:
        """
        print "Write in file: ", outfilename, "..."
        f = open(outfilename, "w")
        str_xml = ""
        if prettyxml:
            try:
                dom = sym_node.toDOM(None, element_name=element_name)
            except pyxb.IncompleteElementContentError as e:
                print '*** ERROR : IncompleteElementContentError'
                print '- Details error: ', e.details()
            except pyxb.MissingAttributeError as e:
                print '*** ERROR : MissingAttributeError'
                print '- Details error: ', e.details()
            else:
                str_xml = dom.toprettyxml(indent="\t", newl="\n", encoding='utf-8')
        else:
            str_xml = sym_node.toxml('utf-8', element_name=element_name)
        #
        f.write(str_xml)
        f.close()
        print "Write in file: ", outfilename, "[DONE]"

    @pyxbDecorator(pyxb_parser)
    def export_TRAFICS(self, *args):
        """

        :param args:
        :return:

        """
        @pyxbDecorator(pyxb_parser)
        def export_TRAFIC(list_troncons, list_connexions, *args):
            #
            @pyxbDecorator(pyxb_parser)
            def export_TRONCONS(list_troncons, *args):
                @pyxbDecorator(pyxb_parser)
                def export_TRONCON(arg_sym_TRONCON, *args):
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
                @pyxbDecorator(pyxb_parser)
                def export_CONNEXION_INTERNE(sym_CAF, *args):
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

    @pyxbDecorator(pyxb_parser)
    def export_TRONCONS(self, *args):
        """

        :return:

        """
        # TODO: construction TOPO ici !
        print '****** self.module_topo.convert_sg3_edges_to_pyxb_symutroncons() *****'
        self.module_topo.convert_sg3_edges_to_pyxb_symutroncons()

        sym_TRONCONS = pyxbDecorator.get_instance(*args)
        # for pyxb_symuTRONCON in self.module_topo.dict_pyxb_symutroncons:
        for pyxb_symuTRONCON in self.module_topo.dict_pyxb_symutroncons.values():
            sym_TRONCONS.append(pyxb_symuTRONCON)
        #
        return sym_TRONCONS

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)

    @staticmethod
    def build_id_for_CAF(node_id):
        """

        :param node_id:
        :return:
        """
        return 'CAF_' + str(node_id)
