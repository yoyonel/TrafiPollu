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

b_export_connexion = True

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


class trafipolluImp_EXPORT(object):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        #
        self.module_topo = kwargs['module_topo']
        #
        self.pyxb_parser = pyxb_parser
        #
        self.list_symu_connexions = []
        #
        infilename = kwargs.setdefault('infilename_for_symuvia', infilename_for_symuvia)
        logger.info("trafipolluImp_EXPORT - Open file: %s ..." % infilename)
        xml = open(infilename).read()
        self.symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        logger.info("trafipolluImp_EXPORT - Open file: %s [DONE]" % infilename)
        #
        self.symu_ROOT_RESEAU_TRONCONS = None
        self.symu_ROOT_RESEAU_CONNEXIONS = None
        self.symu_ROOT_TRAFICS = None

        self.module_export_trafics = trafipolluImp_EXPORT_TRAFICS(module_topo=self.module_topo)
        self.module_export_connexions = trafipolluImp_EXPORT_CONNEXIONS(module_topo=self.module_topo)

    def clear(self):
        """

        :return:
        """
        self.list_symu_connexions = []

    @timerDecorator()
    def update_SYMUVIA(self):
        """

        :return:

        """
        self.update_TRONCONS()

        if b_export_connexion:
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
        self.symu_ROOT_RESEAU_CONNEXIONS = self.module_export_connexions.export_CONNEXIONS('RESEAU')

    def update_TRAFICS(self):
        """

        :return:
        """
        self.symu_ROOT_TRAFICS = self.module_export_trafics.export_TRAFICS('ROOT_SYMUBRUIT')

    @timerDecorator()
    def export(self, update_symu=False, outfilename=outfilename_for_symuvia):
        """

        :param filename:
        :return:
        """

        if update_symu:
            self.update_SYMUVIA()

            if self.symu_ROOT_RESEAU_TRONCONS:
                self.symu_ROOT.RESEAUX.RESEAU[0].TRONCONS = self.symu_ROOT_RESEAU_TRONCONS

                # Si des symu-troncons exportes alors on a forcement un entete TRAFICS a remplir
                self.symu_ROOT.TRAFICS = self.symu_ROOT_TRAFICS

                if b_export_connexion:
                    self.symu_ROOT.RESEAUX.RESEAU[0].CONNEXIONS = self.symu_ROOT_RESEAU_CONNEXIONS
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
        logger.info("Write in file: %s ..." % outfilename)
        f = open(outfilename, "w")
        str_xml = ""
        if prettyxml:
            try:
                dom = sym_node.toDOM(None, element_name=element_name)
            except pyxb.IncompleteElementContentError as e:
                logger.fatal('*** ERROR : IncompleteElementContentError')
                logger.fatal('- Details error: ', e.details())
            except pyxb.MissingAttributeError as e:
                logger.fatal('*** ERROR : MissingAttributeError')
                logger.fatal('- Details error: ', e.details())
            else:
                str_xml = dom.toprettyxml(indent="\t", newl="\n", encoding='utf-8')
        else:
            str_xml = sym_node.toxml('utf-8', element_name=element_name)
        #
        f.write(str_xml)
        f.close()
        logger.info("Write in file: %s [DONE]" % outfilename)

    @pyxbDecorator(pyxb_parser)
    def export_TRONCONS(self, *args):
        """

        :return:

        """
        sym_TRONCONS = pyxbDecorator.get_instance(*args)
        try:
            # logger.info(u'self.module_topo.dict_symu_troncons: {0:s}'.format(self.module_topo.dict_symu_troncons))
            for symu_troncon in self.module_topo.dict_symu_troncons.values():
                sym_TRONCONS.append(symu_troncon)
        except pyxb.ValidationError as e:
            logger.fatal("Exception in 'export_TRONCONS' - details: ", e.details())
        #
        return sym_TRONCONS