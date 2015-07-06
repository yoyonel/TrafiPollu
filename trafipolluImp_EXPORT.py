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
from trafipolluImp_EXPORT_TRAFICS import trafipolluImp_EXPORT_TRAFICS
from imt_tools import timerDecorator

qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))
#
infilename_for_symuvia = qgis_plugins_directory + '/' + "project_empty_from_symunet" + "_xsd_" + "2_04" + ".xml"
outfilename_for_symuvia = qgis_plugins_directory + '/' + "export_from_sg3_to_symuvia" + "_xsd_" + "2_04" + ".xml"


class trafipolluImp_EXPORT(
    trafipolluImp_EXPORT_CONNEXIONS,
    trafipolluImp_EXPORT_TRAFICS
):
    """

    """
    # def __init__(self, dict_edges, dict_lanes, dict_nodes, module_topo, infilename=infilename_for_symuvia):
    def __init__(self, **kwargs):
        """

        """
        self.pyxb_parser = pyxb_parser
        #
        self.list_symu_connexions = []
        #
        infilename = kwargs.setdefault('infilename_for_symuvia', infilename_for_symuvia)
        print "trafipolluImp_EXPORT - Open file: ", infilename, "..."
        xml = open(infilename).read()
        self.symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        print "trafipolluImp_EXPORT - Open file: ", infilename, "[DONE]"
        #
        self.symu_ROOT_RESEAU_TRONCONS = None
        self.symu_ROOT_RESEAU_CONNEXIONS = None
        self.symu_ROOT_TRAFICS = None

        self.module_topo = kwargs['module_topo']

        kwargs.update({'list_symu_connexions': self.list_symu_connexions})
        super(trafipolluImp_EXPORT, self).__init__(**kwargs)

    @timerDecorator()
    def update_SYMUVIA(self):
        """

        :return:
        """
        # TODO: construction TOPO ici ! un peu merdique car il faut faire attention a l'ordre entre la construction
        # topologique et l'export (qui a aussi des parties de constructions topologiques, c'est la ou c'est (encore)
        # foireux). Faudra penser a decomposer tout ca, pour lever la dependance et la contrainte d'ordonnancement !
        # Ce type de dependance pourra 'bloquer' par exemple le parallellisme (multi-threads computation) !

        self.module_topo.convert_sg3_edges_to_pyxb_symutroncons()
        self.module_topo.build_topo_for_interconnexions()
        #
        self.update_TRONCONS()
        #
        self.module_topo.build_topo_extrimites()
        #
        self.update_CONNEXIONS()
        self.update_TRAFICS()

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

    @timerDecorator()
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
    def export_TRONCONS(self, *args):
        """

        :return:

        """
        sym_TRONCONS = pyxbDecorator.get_instance(*args)
        try:
            for pyxb_symuTRONCON in self.module_topo.dict_pyxb_symutroncons.values():
                sym_TRONCONS.append(pyxb_symuTRONCON)
        except pyxb.ValidationError as e:
            print("Exception in 'export_TRONCONS' - details: ", e.details())
        #
        return sym_TRONCONS