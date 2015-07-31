__author__ = 'latty'

#url: http://pymotw.com/2/ConfigParser/

from ConfigParser import SafeConfigParser

# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


class TPConfig:
    """

    """

    def __init__(self, filenames="defaults.cfg"):
        """

        :param filenames:
        :return:
        """

        self.__parser = SafeConfigParser()
        found = self.__parser.read(filenames)
        logger.info("self.__parser.read(%s): %s" % (filenames, found))

    @property
    def parser(self):
        return self.__parser


def get_dict_with_configs(configparser, section, dict):
    """

    :param dict:
    :param configparser:
    :param section:
    :return:

    """
    result_dict = {}
    for keys in dict.keys():
        if configparser.has_option(section, keys):
            result_dict[keys] = get_option(configparser, section, keys, dict[keys])
        else:
            result_dict[keys] = dict[keys]
    return result_dict


def get_option(configparser, section, option, default_value):
    """

    :param configparser:
    :param section:
    :param option:
    :param default_value:
    :return:

    """
    return type(default_value)(configparser.get(section, option))