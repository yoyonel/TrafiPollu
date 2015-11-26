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

import ConfigParser
from collections import defaultdict


qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))
#
infilename_for_symuvia = qgis_plugins_directory + '/' + "project_empty_from_symunet" + "_xsd_" + "2_04" + ".xml"
outfilename_for_symuvia = qgis_plugins_directory + '/' + "export_from_sg3_to_symuvia" + "_xsd_" + "2_04" + ".xml"

b_export_connexion = True

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


class CConfig:
    def __init__(self, filename):
        self.Config = ConfigParser.ConfigParser()
        self.current_section = None
        self.config_filename = filename
        self.dict = defaultdict(defaultdict)

    def load(self):
        try:
            self.Config.read(self.config_filename)
        except ConfigParser.ParsingError:
            logger.warning("can't read the file: ${0}".format(self.config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

    def load_section(self, section_name, set_current=True):
        try:
            options = self.Config.options(section_name)
            for option in options:
                try:
                    self.dict[section_name][option] = self.Config.get(section_name, option)
                    if self.dict[section_name][option] == -1:
                        print("skip: [option]->%s" % option)
                # except ConfigParser.NoOptionError:
                except:
                    print("exception on [option]->%s!" % option)
                    self.dict[section_name][option] = None
            if set_current:
                self.set_current_section(section_name)
        # except ConfigParser.NoSectionError:
        except:
            print("exception on: [Section]->%s!" % section_name)

    def get_option(self, option_name, default_value=None, section_name=None):
        if not section_name:
            section_name = self.current_section

        try:
            return dict[section_name][option_name]
        except:
            return default_value

    def set_current_section(self, section):
        self.current_section = section


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
            logger.warning("can't read the file: ${0}".format(self.config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

        # load la section et place cette section en section courante
        Config.load_section('EXPORT')

        # recuperation des options liees a la section courante 'EXPORT'
        # XSD informations
        self.xsd_version = Config.get_option('xsd_version', "2_04")
        self.xsd_prefix = Config.get_option('xsd_prefix', "_xsd_")
        # IMPORT informations
        self.symuvia_import_filename = Config.get_option('symuvia_import_filename', "project_empty_from_symunet")
        self.symuvia_import_ext = Config.get_option('symuvia_import_ext', "xml")
        self.symuvia_import_path = Config.get_option('symuvia_import_path', qgis_plugins_directory + '/')
        # EXPORT informations
        self.symuvia_export_filename = Config.get_option('symuvia_export_filename', "export_from_sg3_to_symuvia")
        self.symuvia_export_ext = Config.get_option('symuvia_export_ext', "xml")
        self.symuvia_export_path = Config.get_option('symuvia_export_path', qgis_plugins_directory + '/')

        # construction du nom du fichier
        # IMPORT
        self.symuvia_infilename = self.symuvia_import_path + \
            self.symuvia_import_filename + \
            self.xsd_prefix + self.xsd_version + \
            '.' + self.symuvia_import_ext
        # EXPORT
        self.symuvia_outfilename = self.symuvia_export_path + \
            self.symuvia_export_filename + \
            self.xsd_prefix + self.xsd_version + \
            '.' + self.symuvia_export_ext

        logger.info("trafipolluImp_EXPORT - Open file: %s ..." % self.symuvia_infilename)
        xml = open(self.symuvia_infilename).read()
        self.symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        logger.info("trafipolluImp_EXPORT - Open file: %s [DONE]" % self.symuvia_infilename)

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

    @timerDecorator()
    def update_SYMUVIA(self):
        """

        :return:

        """
        # TODO: construction TOPO ici !
        # Ya une feinte presente dans la construction topologique liee a une contrainte d'ordonnancement.
        # Actuellement pour determiner les extremites, on doit examiner les TRONCONS qui n'ont pas un lieu amont ou
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

    @timerDecorator()
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