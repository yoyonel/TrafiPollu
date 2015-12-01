__author__ = 'latty'


import ConfigParser
from collections import defaultdict
from imt_tools import build_logger


class CConfig(object):
    """

    """

    def __init__(self, filename, **kwargs):
        """

        :param filename: nom du fichier config a charger (.ini)
        :param kwargs:
            - logger: pour passer un logger possede par le module caller
        :return: N'effectue pas le chargement a ce niveau.
                Initialisation de la classe et du logger associe/cree.
        """
        self.Config = ConfigParser.ConfigParser()
        self.current_section = None
        self.config_filename = filename
        self.dict_configs = defaultdict(defaultdict)
        #
        # on recupere le logger associe au module utilisant le CConfig
        # par defaut on utilise un logger lie au module courant: 'CConfig'
        self.logger = kwargs.get('logger', build_logger(__name__))

    def load(self):
        """

        :return: Charge ou recharge le fichier INI associe a l'init. de la classe
        """
        try:
            self.Config.read(self.config_filename)
        except ConfigParser.ParsingError:
            self.logger.warning("can't read the file: {0}".format(self.config_filename))
            self.logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

    def set_current_section(self, section):
        """

        :param section:
        :return:
        """
        self.current_section = section

    def load_section(self, section_name, set_current=True):
        """

        :param section_name:
        :param set_current:
        :return:
        """
        try:
            options = self.Config.options(section_name)
            for option in options:
                try:
                    self.dict_configs[section_name][option] = self.Config.get(section_name, option)
                    if self.dict_configs[section_name][option] == -1:
                        self.logger.warning("skip: [option]->{0}".format(option))
                except ConfigParser.NoOptionError:
                    self.logger.warning("exception on [option]->{0}!".format(option))
                    self.dict_configs[section_name][option] = None
            if set_current:
                self.set_current_section(section_name)
        except ConfigParser.NoSectionError:
            self.logger.warning("exception on: [Section]->{0}!".format(section_name))

    def get_option(self, option_name, **kwargs):
        """

        :param option_name:
        :param default_value:
        :param section_name:
        :return:
        """
        section_name = kwargs.get('section_name', None)
        default_value = kwargs.get('default_value', None)

        try:
            return self.dict_configs[section_name][option_name]
        except KeyError:
            return default_value

    def update(self, _dict2update, _dictparams):
        """

        :param _dict2update:
        :param _dictparams:
        :return:
        """
        for name_member, (option_name, default_value) in _dictparams.iteritems():
            _dict2update[name_member] = self.get_option(option_name, default_value=default_value)

