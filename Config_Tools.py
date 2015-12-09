__author__ = 'latty'

import ConfigParser
from collections import defaultdict
from imt_tools import build_logger

import os
qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))

# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = build_logger(__name__)
#logger = build_logger(__name__, list_handlers=['stream'])

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


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

    def load(self):
        """

        :return: Charge ou recharge le fichier INI associe a l'init. de la classe
        """
        try:
            self.Config.read(self.config_filename)
        except ConfigParser.ParsingError:
            logger.warning("can't read the file: {0}".format(self.config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

    def set_current_section(self, section):
        """

        :param section:
        :return:
        """
        self.current_section = section
        logger.info("Set current section to {0}".format(section))

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
                        logger.warning("skip: [option]->{0}".format(option))
                except ConfigParser.NoOptionError:
                    logger.warning("exception on [option]->{0}!".format(option))
                    self.dict_configs[section_name][option] = None
            if set_current:
                self.set_current_section(section_name)
        except ConfigParser.NoSectionError:
            logger.warning("exception on: [Section]->{0}!".format(section_name))

        logger.info("dict_configs: {0}".format(list(self.dict_configs.iteritems())))

    def get_option(self, option_name, **kwargs):
        """

        :param option_name:
        :param default_value:
        :param section_name:
        :return:
        """
        section_name = kwargs.get('section_name', self.current_section)
        default_value = kwargs.get('default_value', None)

        try:
            # version 'simple' sans cast
            # return self.dict_configs[section_name][option_name]

            # version avec cast lie a la valeur par defaut
            value = self.dict_configs[section_name][option_name]
            type_default_value = type(default_value)
            if type_default_value == bool:
                if value.lower() not in _boolean_states:
                    raise ValueError('Not a boolean: {0}'.format(value))
                return _boolean_states[value.lower()]
            else:
                return type(default_value)(value)
        except KeyError as e:
            # debug du debug :p
            logger.info("option_name: {0}".format(option_name))
            logger.info("section_name: {0}".format(section_name))
            logger.info("default_value: {0}".format(default_value))
            logger.info("dict_configs: {0}".format(list(self.dict_configs.iteritems())))
            #
            logger.warning("-> Use default for {0}".format(e))
            return default_value

    def update(self, _dict2update, _dictparams):
        """

        Update d'un dictionnaire (arg0) pour recuperer les valeurs d'une liste/dict de parametres transmis (arg1).
        Le dict. de parametres contient:
         - le nom du membre ou le nom de la cle dans le dictionnaire resultat (la cle du dict.)
         - le nom de l'option dans le fichier de config et une valeur par defaut (value: tuple)

        A noter que les valeurs par defaut des options typent (castent) les valeurs des options
        recuperees dans le fichier CONFIG.

        :param _dict2update:
        :type _dict2update: `dict`

        :param _dictparams:
            Dictionnaire definit par::
                - key: `str` - nombre du parametre
                - value: tuple(nom de l'option [str.], valeur par defaut [str.])
        :type _dictparams: `dict`

        :return:
        """
        for name_member, (option_name, default_value) in _dictparams.iteritems():
            _dict2update[name_member] = self.get_option(option_name, default_value=default_value)

    ##################
    # STATIC METHODS #
    ##################
    @staticmethod
    def load_from_module(module_name, **kwargs):
        """

        :param module_name:
        :type module_name: `str`

        :param kwargs
        :type kwargs: (unpack) dict.

        :return:
        :rtype: CConfig.

        """
        config_filename = qgis_plugins_directory + '/' + \
                          kwargs.setdefault('config_filename', 'config_' + module_name + '.ini')
        logger.info("Config INI filename: {0}".format(config_filename))
        config = CConfig(config_filename)
        try:
            config.load()
        except ConfigParser.ParsingError:
            logger.warning("can't read the file: {0}".format(config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

        return config
