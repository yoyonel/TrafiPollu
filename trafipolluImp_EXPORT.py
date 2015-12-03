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
from imt_tools import timer_decorator

import ConfigParser
from collections import defaultdict
from Config_Tools import CConfig

from imt_tools import build_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = build_logger(__name__)

qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))
#
infilename_for_symuvia = qgis_plugins_directory + '/' + "project_empty_from_symunet" + "_xsd_" + "2_04" + ".xml"
outfilename_for_symuvia = qgis_plugins_directory + '/' + "export_from_sg3_to_symuvia" + "_xsd_" + "2_04" + ".xml"

b_export_connexion = True


class trafipolluImp_EXPORT(
    trafipolluImp_EXPORT_CONNEXIONS,
    trafipolluImp_EXPORT_TRAFICS
):
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

        self.configs = defaultdict()
        #
        self.config_filename = qgis_plugins_directory + '/' + \
                               kwargs.setdefault('config_filename', 'config_' + __name__ + '.ini')
        logger.info("Config INI filename: {0}".format(self.config_filename))
        self.Config = CConfig(self.config_filename)
        Config = self.Config    # alias sur la Config
        try:
            Config.load()
        except ConfigParser.ParsingError:
            logger.warning("can't read the file: {0}".format(self.config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

        # load la section et place cette section en section courante
        Config.load_section('EXPORT')

        # recuperation des options liees a la section courante 'EXPORT'
        Config.update(
            self.__dict__,
            {
                # XSD
                'xsd_version': ('xsd_version', '2_04'),
                'xsd_prefix': ('xsd_prefix', '_xsd_'),
                # IMPORT
                'symuvia_import_filename': ('symuvia_import_filename', 'project_empty_from_symunet'),
                'symuvia_import_ext': ('symuvia_import_ext', 'xml'),
                'symuvia_import_path': ('symuvia_import_path', qgis_plugins_directory + '/'),
                # EXPORT
                'symuvia_export_filename': ('symuvia_export_filename', 'export_from_sg3_to_symuvia'),
                'symuvia_export_ext': ('symuvia_export_ext', 'xml'),
                'symuvia_export_path': ('symuvia_export_path', qgis_plugins_directory + '/')
            }
        )
        self.symuvia_infilename = self.generate_filename('import')      # generate filename for: 'symuvia_import_'
        self.symuvia_outfilename = self.generate_filename('export')     # generate filename for: 'symuvia_export_'
        #
        #logger.info("__dict__: {0}".format(self.__dict__))
        logger.info("Symuvia - infilename: {0}".format(self.symuvia_infilename))
        logger.info("Symuvia - outfilename: {0}".format(self.symuvia_outfilename))

        logger.info("Open file: %s ..." % self.symuvia_infilename)
        xml = open(self.symuvia_infilename).read()
        self.symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        logger.info("Open file: %s [DONE]" % self.symuvia_infilename)

        self.symu_ROOT_RESEAU_TRONCONS = None
        self.symu_ROOT_RESEAU_CONNEXIONS = None
        self.symu_ROOT_TRAFICS = None

        kwargs.update({'list_symu_connexions': self.list_symu_connexions})
        super(trafipolluImp_EXPORT, self).__init__(**kwargs)

    def clear(self):
        """

        :return:
        """
        self.list_symu_connexions = []

    def generate_filename(self, target):
        """

        :param target:
            - 'import'
            - 'export'
        :return:
        """
        return self.__dict__[str('symuvia_' + target + '_path')] + \
            self.__dict__[str('symuvia_' + target + '_filename')] + \
            self.__dict__['xsd_prefix'] + self.__dict__['xsd_version'] + \
            '.' + self.__dict__[str('symuvia_' + target + '_ext')]

    @timer_decorator
    def update_SYMUVIA(self):
        """

        :return:

        """
        # TODO: construction TOPO ici !
        # Ya une feinte presente dans la construction topologique liee a une contrainte d'ordonnancement.
        # aval. Le probleme vient que les attributions des amonts/avals (liens par IDs) se font dans les exports (
        # CONNEXIONS).
        # Du coup pour esquiver le probleme, quand on calcule la topo pour les interconnexions, on affecte des fakes
        # ids aux amonts/avals des interconnexions pour que le module extremites ne les prennent pas en compte.
        # Dans l'export des CONNEXIONS par la suite, ces ids amonts/avals d'interconnexions sont reattribuees pour
        # coincider au vrai lien topologiques (avec un CAF/REPARTITEUR ou un TRONCON)
        self.module_topo.build_topo()
        #
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
        self.symu_ROOT_RESEAU_CONNEXIONS = self.export_CONNEXIONS('RESEAU')

    def update_TRAFICS(self):
        """

        :return:
        """
        self.symu_ROOT_TRAFICS = self.export_TRAFICS('ROOT_SYMUBRUIT')

    @timer_decorator
    def export(self, update_symu=False, outfilename=""):
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

            if b_export_connexion:
                if self.list_symu_connexions != []:
                    self.symu_ROOT.RESEAUX.RESEAU[0].CONNEXIONS = self.symu_ROOT_RESEAU_CONNEXIONS
                    b_add_trafics = True
                if b_add_trafics:
                    self.symu_ROOT.TRAFICS = self.symu_ROOT_TRAFICS
        #
        self.save_ROOT(
            self.symu_ROOT,
            outfilename if outfilename else self.symuvia_outfilename
        )

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
            for pyxb_symuTRONCON in self.module_topo.dict_pyxb_symutroncons.values():
                sym_TRONCONS.append(pyxb_symuTRONCON)
        except pyxb.ValidationError as e:
            logger.fatal("Exception in 'export_TRONCONS' - details: ", e.details())
        #
        return sym_TRONCONS