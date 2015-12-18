# -*- coding: utf-8 -*-
"""

    imt_tools: Outils utilises par les modules du plugin

"""

"""
/***************************************************************************
 interactive map tracking
                                 A QGIS plugin
 Tools for Interactive Map Tools
                              -------------------
        begin                : 2015-02-10
        git sha              : $Format:%H$
        copyright            : (C) 2015 by IGN
        email                : lionel.atty@ign.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'latty'

from qgis.core import *
import os
import collections
# from socket import gethostbyname, gethostname
import socket

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QAbstractButton, QCheckBox

try:
    import cPickle as pickle
except:
    import pickle
import qgis_log_tools
from collections import namedtuple

import logging
from qgis_log_tools import QGISLogHandler

import networkx as nx
import matplotlib.pyplot as plt

import time
from functools import wraps
# from time import time

from PyQt4.QtCore import QDateTime
from math import modf

import shlex
from subprocess import call, PIPE, STDOUT

from PyQt4.QtNetwork import QTcpSocket
import getpass


defaultQtDateFormatString = "yyyy-MM-ddThh:mm:ss.zzz"

#
if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])


def get_lan_ip():
    """

    Finding the ip lan address (OS independant)
     url: http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib#

    :return: String of the IP
    :rtype: str
    """
    # print 'gethostname(): ', socket.gethostname()
    # print 'gethostbyname: ', socket.gethostbyname
    global ip
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        print 'get_lan_ip - WARNING: probleme avec "gethostbyname"'
        ip = '127.0.0.1'
    finally:
        if ip.startswith("127.") and os.name != "nt":
            interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "wifi0", "ath0", "ath1", "ppp0"]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip


def find_index_field_by_name(field_names, field_name):
    """

    Search a field (by name) in a list of fields.

    :param field_names: list of field name
    :type field_names: list[str]

    :param field_name: field name
    :type field_name: str

    :return: If found return the index of the field in the list Else return -1
    :rtype: int
    """
    # find index for field 'user-id'
    try:
        id_for_user_id = field_names.index(field_name)
    except ValueError:
        # field non trouve !
        return -1
    return id_for_user_id


# url: http://stackoverflow.com/questions/117014/how-to-retrieve-name-of-current-windows-user-ad-or-local-using-python
def get_os_username():
    """

    :return:
    :rtype:
    """
    return getpass.getuser()


def get_timestamp():
    """

    :return:
    :rtype: .

    """
    # Python time
    return time.time()


def convert_timestamp_to_qdatetime(timestamp):
    """

    :param timestamp:
    :type timestamp: .
    :return:
    """
    timestamp_frac, timestamp_whole = modf(timestamp)
    # Qt time
    qdatetime = QDateTime()
    qdatetime.setTime_t(int(timestamp_whole))
    qdatetime = qdatetime.addMSecs(int(timestamp_frac * 1000))
    #
    return qdatetime


# def convert_timestamp_to_qt_string_format(timestamp, QtDateFormat):
# # String Qt time
# return convert_timestamp_to_qdatetime(timestamp).toString(QtDateFormat)


def convert_timestamp_to_qt_string_format(timestamp, QtDateFormatString=defaultQtDateFormatString):
    """

    :param timestamp:
    :type timestamp: .
    :param QtDateFormatString:
    :type QtDateFormatString: `str`.
    :return:
    :rtype: .
    """
    # String Qt time
    return convert_timestamp_to_qdatetime(timestamp).toString(QtDateFormatString)


# def get_timestamp_from_qt_string_format(QtDateFormat):
# """ Retrieve timestamp from the system and convert into a ISO QString/QDateTime format.
#
# urls:
# - https://docs.python.org/2/library/datetime.html
# - http://stackoverflow.com/questions/2935041/how-to-convert-from-timestamp-to-date-in-qt
#     - http://stackoverflow.com/questions/3387655/safest-way-to-convert-float-to-integer-in-python
#     - http://pyqt.sourceforge.net/Docs/PyQt4/qt.html -> Qt.DateFormat
#       Qt.ISODate 	= 1 : ISO 8601 extended format: either YYYY-MM-DD for dates or YYYY-MM-DDTHH:mm:ss, YYYY-MM-DDTHH:mm:ssTZD
#       (e.g., 1997-07-16T19:20:30+01:00) for combined dates and times.
#
#     :param QtDateFormat: enum (value) for ISO conversion (from Qt C++ API) [default=1(=Qt.ISODate)]
#     :type QtDateFormat: int
#
#     :return: TimeStamp in ISO QString from QDateTime format.
#     :rtype: QString
#     """
#     return convert_timestamp_to_qt_string_format(get_timestamp(), QtDateFormat)


def get_timestamp_from_qt_string_format(QtDateFormatString=defaultQtDateFormatString):
    """

    :param QtDateFormatString:
    :type QtDateFormatString: `str`.
    :return:
    :rtype: .
    """
    return convert_timestamp_to_qt_string_format(get_timestamp(), QtDateFormatString)


def construct_listpoints_from_extent(_extent):
    """ Construct a list of QGIS points from QGIS extent.

    :param _extent: QGIS extent
    :type _extent: QgsRectangle

    :return: List of QGIS points
    :rtype: list[QgsPoint]
    """
    x1 = _extent.xMinimum()
    y1 = _extent.yMinimum()
    x3 = _extent.xMaximum()
    y3 = _extent.yMaximum()
    x2 = x1
    y2 = y3
    x4 = x3
    y4 = y1
    return [QgsPoint(x1, y1),
            QgsPoint(x2, y2),
            QgsPoint(x3, y3),
            QgsPoint(x4, y4),
            QgsPoint(x1, y1)]


def find_layer_in_qgis_legend_interface(_iface, _layername):
    """

    :param _iface:
    :type _iface: .
    :param _layername:
    :type _layername: .
    :return:
    :rtype:
    """
    try:
        layer_searched = [layer_searched
                          for layer_searched in _iface.legendInterface().layers()
                          if layer_searched.name() == _layername]
        return layer_searched[0]
    except:
        return None


class TpTimer:
    """

    """

    def __init__(self):
        """

        """
        self.currentTime = self.default_timers()
        self.dict_process_timeupdate = {}
        self.dict_process_delay = {}

    @staticmethod
    def default_timers():
        """

        :return:
        :rtype: list[float, float].
        """
        return [time.time(), time.time()]

    @staticmethod
    def default_delay():
        """

        :return:
        :rtype: `float`.
        """
        return 0.0

    def get_current_time(self):
        """

        :return:
        :rtype: `float`.
        """
        self.update_current_time()
        return self.currentTime[0]

    def __getitem__(self, key):
        """

        :param key:
        :return:
        """
        return self.dict_process_timeupdate.setdefault(key, self.default_timers())

    def update_current_time(self):
        """

        """
        self.currentTime = [time.time(), self.currentTime[0]]

    def delta_without_key(self):
        """

        :return:
        :rtype: `float`.
        """
        return self.currentTime[0] - self.currentTime[1]

    def delta(self, key):
        """

        :param key:
        :type key: `str`.
        :return:
        :rtype: `float`.
        """
        list_times = self.__getitem__(key)
        return list_times[0] - list_times[1]

    def delta_with_current_time(self, key):
        """

        :param key:
        :type key: `str`.
        :return:
        :rtype: `float`.
        """
        self.update_current_time()
        list_times = self.__getitem__(key)
        return self.currentTime[0] - list_times[0]

    def update(self, key):
        """

        :param key:
        :type key: `str`.
        :return:
        :rtype: `float`.
        """
        self.update_current_time()
        list_times = self.__getitem__(key)
        self.dict_process_timeupdate[key] = [self.currentTime[0], list_times[0]]
        return self.dict_process_timeupdate[key]

    def get_delay(self, process_name):
        """

        :param process_name:
        :type process_name: `str`.
        :return:
        :rtype: .
        """
        return self.dict_process_delay.setdefault(process_name, self.default_delay())

    def set_delay(self, delay_name, time_delay):
        """

        :param delay_name:
        :type delay_name: `str`.
        :param time_delay:
        :type time_delay: `float`.

        """
        self.dict_process_delay[delay_name] = time_delay

    def is_time_to_update(self, process_name, delay_name):
        """

        :param process_name:
        :type process_name: `str`.
        :param delay_name:
        :type delay_name: `str`.
        :return:
        :rtype: `float`.
        """
        return self.delta_with_current_time(process_name) >= self.get_delay(delay_name)


def get_return_code_of_simple_cmd(cmd, stderr=STDOUT):
    """
        Execute a simple external command and return its exit status.

    :param cmd:
    :type cmd: `str`.
    :param stderr:
    :type stderr: .
    :return:
    :rtype: .
    """
    args = shlex.split(cmd)
    return call(args, stdout=PIPE, stderr=stderr)


def is_network_alive(url="www.google.com"):
    """

    :param url:
    :type url: `str`.
    :return:
    :rtype: bool.
    """
    #cmd = "ping -c 1 " + url
    cmd = "curl --output /dev/null --silent --head --fail" + url
    return get_return_code_of_simple_cmd(cmd) == 0


def isConnected(url):
    """

    :param url:
    :type url: `str`.
    :return:
    :rtype: bool.
    """
    socket = QTcpSocket()
    socket.connectToHost(url, 80)
    return socket.waitForConnected(1000)


DEFAULT_SEGMENT_EPSILON = 1e-08


def extent_equal(r1, r2, epsilon=DEFAULT_SEGMENT_EPSILON):
    """

    :param r1:
    :type r1: QgsRectangle.
    :param r2:
    :type r2: QgsRectangle.
    :param epsilon:
    :type epsilon: `float`.
    :return:
    :rtype: bool.
    """
    return abs(r1.xMaximum() - r2.xMaximum()) <= epsilon and \
           abs(r1.yMaximum() - r2.yMaximum()) <= epsilon and \
           abs(r1.xMinimum() - r2.xMinimum()) <= epsilon and \
           abs(r1.yMinimum() - r2.yMinimum()) <= epsilon


qsettings_id_pickle = "pickle"
#
pickle_id_gui = "GUI"
pickle_id_list_checkbox = "list_checkbox"
pickle_id_list_tabs_size = "list_tabs_size"


def save_gui_states_in_qsettings(dict_qobject_slot):
    """

    :param dict_qobject_slot:
    :type dict_qobject_slot: `dict`.
    """
    s = QSettings()
    #
    for qobject in dict_qobject_slot.keys():
        slot = dict_qobject_slot[qobject]
        id_string = slot.__name__
        s.setValue(id_string, str(qobject.isChecked()))


def serialize_checkbox(checkbox):
    """

    :param checkbox:
    :type checkbox: .
    :return:
    :rtype: `dict`.
    """
    return {
        'isEnabled': checkbox.isEnabled(),
        'isChecked': checkbox.isChecked()
    }


def serialize_list_checkbox(dlg, list_id_checkbox):
    """

    :param dlg:
    :type dlg:

    :param list_id_checkbox:
    :type list_id_checkbox:

    :return:
    :rtype: `dict`.

    """
    return_dict = {}
    for string_id_checkbox in list_id_checkbox:
        qt_checkbox = dlg.__getattribute__(string_id_checkbox)
        dict_checkbox_id = {
            string_id_checkbox: serialize_checkbox(qt_checkbox)
        }
        return_dict.update(dict_checkbox_id)
    return return_dict


def serialize_tabs_size(imt):
    """

    :param imt:
    :type imt:
    :return:
    :rtype: `dict`.
    """
    return imt.dict_tabs_size


def update_checkbox_from_serialization(qobject, id_qobject, state):
    """

    :param qobject:
    :type qobject:
    :param id_qobject:
    :type id_qobject:
    :param state:
    :type state:

    """
    try:
        qobject.setEnabled(state[pickle_id_gui][pickle_id_list_checkbox][id_qobject].setdefault('isEnabled', True))
        qobject.setChecked(state[pickle_id_gui][pickle_id_list_checkbox][id_qobject].setdefault('isChecked', False))
    except KeyError:
        logging.warning(
            "Desynchronisation entre l'interface Qt (ui) du plugin et la derniere version serialisee dans les QSettings (via Pickle)")
        logging.warning("-> Ce probleme devrait disparaitre a la prochaine restauration du plug.")
    finally:
        #
        # print state[pickle_id_gui][pickle_id_list_checkbox][id_qobject], ' * ', \
        # id_qobject, ' * ', \
        #     state[pickle_id_gui][pickle_id_list_checkbox][id_qobject].setdefault('isChecked', False)
        pass


def update_list_checkbox_from_serialization(dlg, list_string_id_checkbox, pickle_state):
    """

    :param dlg:
    :type dlg:
    :param list_string_id_checkbox:
    :type list_string_id_checkbox:
    :param pickle_state:
    :type pickle_state:

    """
    for string_id_dlg in list_string_id_checkbox:
        qt_checkbox = dlg.__getattribute__(string_id_dlg)
        update_checkbox_from_serialization(qt_checkbox, string_id_dlg, pickle_state)


def update_tabs_size_from_serialization(imt, pickle_state):
    """

    :param imt:
    :type imt:
    :param pickle_state:
    :type pickle_state:

    """
    imt.dict_tabs_size = pickle_state[pickle_id_gui][pickle_id_list_tabs_size]


def saves_states_in_qsettings_pickle(imt, pickle_name_in_qsettings=qsettings_id_pickle):
    """

    :param imt:
    :type imt:
    :param pickle_name_in_qsettings:
    :type pickle_name_in_qsettings: `str`.

    """
    pickle_string_dump = ""
    try:
        pickle_string_dump = pickle.dumps(imt)
    finally:
        imt.qsettings.beginGroup(imt.qsettings_group_name)
        imt.qsettings.setValue(pickle_name_in_qsettings, pickle_string_dump)
        imt.qsettings.endGroup()


def restore_states_from_pickle(imt, pickle_name_in_qsettings=qsettings_id_pickle):
    """

    Methode de restauration de l'etat du GUI (fenetre QT du plugin).
    On utilise les QSettings (variables d'environnement Qt) pour stocker une serialisation (via Pickle) du
    GUI Qt.

    :param imt:
    :type imt: .
    :param pickle_name_in_qsettings:
    :type pickle_name_in_qsettings: `str`.
    """

    qsettings = imt.qsettings
    qsettings.beginGroup(imt.qsettings_group_name)
    qsettings_pickle = qsettings.value(pickle_name_in_qsettings)
    qsettings.endGroup()

    # print "in QSettings - pickle: ", qsettings_pickle
    if qsettings_pickle:
        imt_for_states = None
        try:
            imt_for_states = pickle.loads(str(qsettings_pickle))
        finally:
            state = imt_for_states.getState()
            imt.restoreState(state)
    # else:
    # update_list_checkbox_from_qsettings(imt)

    # TODO: test on QT dump
    test_qt_dump(imt)


# url: http://stackoverflow.com/questions/121396/accessing-object-memory-address
# url: https://docs.python.org/2/reference/datamodel.html#object.__repr__
# url: http://stackoverflow.com/questions/1810526/python-calling-a-method-of-an-instances-member-by-name-using-getattribute
# url: https://docs.python.org/2/library/functions.html#id

def build_list_id_filter_by_qt_type(dlg, qt_type):
    """

    :param dlg:
    :type dlg:
    :param qt_type:
    :type qt_type:
    :return:
    :rtype: list.
    """
    list_id = []
    list_children = dlg.findChildren(qt_type)
    for qt_object in list_children:
        qt_object_id = id(qt_object)
        list_id.append(qt_object_id)
    return list_id


def build_dict_id_qt_type(dlg, qt_type):
    """

    :param dlg:
    :type dlg: .
    :param qt_type:
    :type qt_type: .
    :return:
    :rtype: `dict`.
    """
    dict_id_qt_type = {}
    list_id_for_qt_type = build_list_id_filter_by_qt_type(dlg, qt_type)
    for qt_object_id in list_id_for_qt_type:
        dict_id_qt_type[qt_object_id] = qt_type
    return dict_id_qt_type


def build_list_member_name_filter_by_qtype(dlg, *qt_types):
    """

    :param dlg:
    :type dlg: .
    :param qt_types:
    :type qt_types: .
    :return:
    :rtype: list.
    """
    list_member_name = []
    for qt_type in qt_types:
        dict_id_qt_type = build_dict_id_qt_type(dlg, qt_type)
        dlg_dict = dlg.__getattribute__('__dict__')
        for dlg_id_string_member in dlg_dict:
            # get the Qt object member associated
            qt_object = dlg_dict[dlg_id_string_member]
            # get the 'unique' python id
            unique_id_qt_object = id(qt_object)
            if unique_id_qt_object in dict_id_qt_type:
                list_member_name.append(dlg_id_string_member)
    return list_member_name


def build_list_member_name_filter_by_qtypes(dlg, *qt_types):
    """

    :param dlg:
    :type dlg: .
    :param qt_types:
    :type qt_types: .
    :return:
    :rtype: list.

    """
    return_list = []
    for qt_type in qt_types:
        return_list.extend(build_list_member_name_filter_by_qtype(dlg, qt_type))
    return return_list


def build_list_member_name_filter_qcheckbox(dlg):
    """

    Renvoie la liste des ids des elements presents dans dlg qui sont de type `QCheckBox`

    :param dlg:
    :type dlg: `QtGui.QDialog`

    :return:
    :rtype: `list`

    """
    return build_list_member_name_filter_by_qtypes(dlg, QCheckBox)


def test_qt_dump(imt):
    """

    Show a connection between Python class and Qt Gui (wrapper)

    :param imt:
    """
    list_qt_types = [
        QAbstractButton
    ]
    dict_id_qt_type = {}
    for qt_type in list_qt_types:
        dict_id_qt_type.update(build_dict_id_qt_type(imt.dlg, qt_type))

    # list_id_for_qabstractbutton = []
    # list_children = imt.dlg.findChildren(QAbstractButton)
    # for qt_button in list_children:
    # qgis_log_tools.logMessageINFO("* From Qt, filter 'QAbstractButton'" + "\n" +
    #                                   "\t- text: " + qt_button.text() + "\n" +
    #                                   "\t- isChecked: " + str(qt_button.isChecked()) + "\n" +

    #                                   "\t- python mem: " + str(qt_button.__repr__) + "\n")
    #     # url: https://docs.python.org/2/library/functions.html#id
    #     list_id_for_qabstractbutton.append(id(qt_button))

    # url: http://stackoverflow.com/questions/1810526/python-calling-a-method-of-an-instances-member-by-name-using-getattribute
    # get member from interactive_map_tracking dlg (Qt Gui)
    imt_dlg_dict = imt.dlg.__getattribute__('__dict__')
    for imt_dlg_id_string_member in imt_dlg_dict.keys():
        # url: http://stackoverflow.com/questions/16408472/print-memory-address-of-python-variable
        # get the Qt object member associated
        qt_object = imt_dlg_dict[imt_dlg_id_string_member]
        # get the 'unique' python id
        unique_id_qt_object = id(qt_object)
        if unique_id_qt_object in dict_id_qt_type:
            qgis_log_tools.logMessageINFO("* From IMT Python class, find Qt element (in dlg)" + "\n" +
                                          "\t- Member name: " + imt_dlg_id_string_member + "\n" +
                                          "\t- Qt type: " + str(dict_id_qt_type[unique_id_qt_object]) + "\n" +
                                          "\t-- isChecked: " + str(qt_object.isChecked()))


def update_list_checkbox_from_qsettings(imt):
    """

    CONDITION: init_signals need to be call before init_plugin
    otherwise signals_manager have no information about signals
    and we can't rely slot signature with qobject

    :param imt:
    :type imt: .
    """
    s = imt.qsettings
    s.beginGroup(imt.qsettings_group_name)
    restore_gui_states_from_qsettings(imt)
    s.endGroup()


def restore_gui_states_from_qsettings(imt, b_launch_slot=True):
    """

    :param imt:
    :type imt: .
    :param b_launch_slot:
    :type b_launch_slot: bool.

    """
    s = imt.qsettings
    for tuple_dlg_id_slot in imt.list_tuples_dlg_id_slot:
        # print qobject, type(qobject )
        qobject = tuple_dlg_id_slot[0]
        id_slot = tuple_dlg_id_slot[2]
        id_in_qsetting = id_slot
        qobject_is_checked = eval(s.value(id_in_qsetting, "False"))
        qobject.setChecked(qobject_is_checked)
        #
        if b_launch_slot:
            slot = imt.signals_manager.get_slot(qobject, id_slot)
            if slot:
                slot()
                #
                # print "id_in_qsetting: ", id_in_qsetting, " - value: ", s.value(id_in_qsetting, "False")


def print_group_name_values_in_qsettings(group_name=""):
    """

    :param group_name:
    :type group_name: `str`.

    """
    qsettings = QSettings()
    keys = [x for x in qsettings.allKeys() if group_name in x]
    for key in keys:
        print key, str(qsettings.value(key))
        # import qgis_log_tools
        # qgis_log_tools.logMessageINFO(str(key)+": "+str(qsettings.value(key)))


def get_itemData(combobox):
    """

    :param combobox:
    :type combobox: .
    :return:
    :rtype: .
    """
    return combobox.itemData(combobox.currentIndex())


def get_itemText(combobox):
    """

    :param combobox:
    :type combobox: .
    :return:
    :rtype: .
    """
    return combobox.itemText(combobox.currentIndex())


def create_named_tuple_from_names(name, list_names):
    """

    :param list_names:
    :type list_names: list.
    :return:
    :rtype: namedtuple.
    """
    return namedtuple(name, list_names)


# url: http://stackoverflow.com/questions/16377215/how-to-pickle-a-namedtuple-instance-correctly
# url: https://docs.python.org/2/library/functions.html#globals
def create_namedtuple_on_globals(*args):
    """

    :param args:
    :type args: .
    :return:
    :rtype: nametuple.
    """
    namedtupleClass = collections.namedtuple(*args)
    globals()[namedtupleClass.__name__] = namedtupleClass
    return namedtupleClass


def create_namedtuple(*args):
    """

    :param args:
    :type args: .
    :return:
    :rtype: nametuple.
    """
    return collections.namedtuple(*args)


class Timer:
    """
    """

    def __enter__(self):
        """

        :return:
        :rtype: .
        """
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        """

        :param args:

        """
        self.end = time.clock()
        self.interval = self.end - self.start


# class timer_decorator(object):
#     """
#
#     """
#
#     def __init__(self, prefix="-> TIMER\n\t", postfix=""):
#         """
#
#         :param prefix:
#         :param postfix:
#         :return:
#         """
#         self.__prefix = prefix
#         self.__postfix = postfix
#
#     def __call__(self, f):
#         """
#
#         :param f:
#         :return:
#         """
#         def wrapped_f(*args):
#             """
#
#             :param args:
#             :return:
#             """
#
#             try:
#                 with Timer() as t:
#                     return f(*args)
#             finally:
#                 print '%s%s took %.03f sec.%s' % (
#                     self.__prefix,
#                     f.__name__,
#                     t.interval,
#                     self.__postfix
#                 )
#
#         return wrapped_f

def timer_decorator(f, prefix="-> TIMER\n\t", postfix=""):
    """

    :param f:
    :type f: `func`

    :param prefix:
    :type prefix: `str`.

    :param postfix:
    :type postfix: `str`.

    """

    @wraps(f)
    def wrap(*args, **kw):
        """

        :param args:
        :type args: .

        :param kw:
        :type kw: .

        :return:
        :rtype: .

        """
        with Timer() as t:
            result = f(*args, **kw)
        print '{0:s}{1:s} took {2:.03f} sec.{3:s}'.format(prefix,
                                                          f.__name__,
                                                          t.interval,
                                                          postfix)
        return result

    return wrap


default_header_for_log = '################## NEW SESSION ##################'


def build_logger(logger_name, **kwargs):
    """

    :param logger_name:
    :type logger_name: `str`.
    :param kwargs:
        - list_handlers: ['stream', 'file', ...]
        - level: logging level of this logger
        - log_threadName[bool]:
        - for qgis handler log:
            - qgis_tag[string]:
            - qgis_separate_tab[bool]:
    :type kwargs: .
    :return: logger.
    :rtype: .
    """
    # filter logger name
    logger_name = filter_logger_name(logger_name)

    # url: http://stackoverflow.com/a/1098639
    #      "Proper way to use **kwargs in Python"
    options = {'list_handlers': ['stream', 'file', 'qgis']}
    options.update(kwargs)

    logger = logging.getLogger(logger_name)

    formatter = construct_formatter_for_logger(**kwargs)

    #
    level = kwargs.get('level', logging.DEBUG)
    logger.setLevel(level)

    dict_functions_to_generate_handlers = {
        'stream': (config_stream_handler, {'formatter': formatter}),
        'file': (config_file_handler, {'formatter': formatter, 'logger_name': logger_name}),
        'qgis': (QGISLogHandler,
                 {
                     'level': level,
                     'tag': kwargs.get('qgis_tag', construct_qgis_tag(logger_name, **kwargs)),
                     'module': logger_name
                 })
    }
    list_handlers = options.get('list_handlers', [])
    for name_handler in list_handlers:
        try:
            func_generate_handler, params = dict_functions_to_generate_handlers[name_handler]
            handler = func_generate_handler(**params)
            logger.addHandler(handler)
        except KeyError as e:
            print "WARNING - Pas de module de gestion pour l'handler: {0}".format(e)
            print "(module a ajouter dans {0})".format(__file__)

    header = options.get('header', default_header_for_log)
    logger.info(header)

    return logger


def filter_logger_name(logger_name):
    """

    :param logger_name:
    :type logger_name: `str`.
    :return:
    :rtype: `str`.
    """
    try:
        logger_name = logger_name.split('.')[1]
    except:
        pass
    logger_name = logger_name.replace('trafipolluImp_', 'tpi_')
    return logger_name


def config_file_handler(**kwargs):
    """

    :param kwargs:
        Needed:
            - logger_name: name of the logger
    :type kwargs: .
    :return:
        if logger_name is not provided => return a NullHandler
        else return a FileHandler
    :rtype: FileHandller.
    """
    try:
        logger_name = kwargs['logger_name']
        #
        filename = kwargs.get('filepath', construct_filename_for_logger(logger_name))
        mode = kwargs.get('mode', 'a')
        file_handler = logging.FileHandler(filename, mode)
        # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
        # cree precedement et on ajoute ce handler au logger
        level = kwargs.get('level', logging.DEBUG)
        file_handler.setLevel(level)
        if 'formatter' in kwargs:
            file_handler.setFormatter(kwargs['formatter'])
    except KeyError:
        file_handler = logging.NullHandler()

    return file_handler


def construct_formatter_for_logger(**kwargs):
    """

    :param kwargs:
    :type kwargs: .
    :return:
    :rtype: Formatter.
    """
    # creation d'un formateur qui va ajouter:
    # - le temps
    # - le niveau
    # - la fonction appelante
    # de chaque message quand on ecrira un message dans le log
    # see def basicConfig(**kwargs) in __init__.py for logging python module
    # fs =  format    Use the specified format string for the handler.
    # dfs=  datefmt   Use the specified date/time format.
    #
    fs = "[%(asctime)s "
    fs += "%(threadName)s " if kwargs.get("log_threadName", False) else ""
    fs += "%(funcName)s, %(levelname)s] %(message)s"
    dfs = None
    # formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(funcName)s :: %(message)s')
    return logging.Formatter(fs, dfs)


def construct_filename_for_logger(logger_name):
    """

    :param logger_name:
    :type logger_name: `str`.
    :return:
    :rtype: `str`.
    """
    pathname = os.path.normcase(os.path.dirname(__file__))
    filename = pathname + '/' + '%s.log' % logger_name
    return filename


def construct_qgis_tag(logger_name, **kwargs):
    """

    :param logger_name:
    :type logger_name: `str`.
    :param kwargs:
    :type kwargs: `dict`.
    :return:
    :rtype: `str`.
    """
    tag = 'Plugins/TrafiPollu'
    tag += '/{0}'.format(logger_name) if kwargs.get('qgis_separate_tab', False) else ''
    return tag


def config_stream_handler(**kwargs):
    """

    :param kwargs:
    :type kwargs: `dict`.
    :return:
    :rtype: StreamHandler.
    """
    stream_handler = logging.StreamHandler()
    level = kwargs.get('level', logging.DEBUG)
    stream_handler.setLevel(level)
    if 'formatter' in kwargs:
        stream_handler.setFormatter(kwargs['formatter'])
    return stream_handler


# url: http://stackoverflow.com/questions/19022868/how-to-make-dictionary-read-only-in-python
class ReadOnlyDict(dict):
    """

    """

    @staticmethod
    def __readonly__(*args, **kwargs):
        """

        :param args:
        :type args: list.
        :param kwargs:
        :type kwargs: `dict`.

        """
        raise RuntimeError("Cannot modify ReadOnlyDict")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    del __readonly__


def build_networkx_graph(dict_nodes, dict_edges):
    """

    :param dict_nodes:
    :type dict_nodes: `dict`.
    :param dict_edges:
    :type dict_edges: `dict`.
    :return:
    :rtype: nx.DiGraph.
    """
    print '############### build_networkx_graph ...'

    graph = nx.DiGraph()

    dict_position_node = {}

    for edge_id, values in dict_edges.iteritems():
        try:
            ui_start_node = values['ui_start_node']
            ui_end_node = values['ui_end_node']
        except:
            pass
        else:
            try:
                dict_position_node[ui_start_node] = list(dict_nodes[ui_start_node]['np_geom'])[0:2]
                dict_position_node[ui_end_node] = list(dict_nodes[ui_end_node]['np_geom'])[0:2]
            except:
                pass
            else:
                graph.add_edge(ui_start_node, ui_end_node)

    for k, v in dict_nodes.iteritems():
        print 'dict_nodes[%s].np_geom: %s' % (k, v['np_geom'])
    print 'dict_position_node: ', dict_position_node

    list_simple_cycles = list(nx.simple_cycles(graph))

    print 'graph.number_of_nodes: ', graph.number_of_nodes()
    print 'graph.number_of_edges: ', graph.number_of_edges()
    print 'graph.nodes: ', graph.nodes()
    print 'graph.edges: ', graph.edges()

    print 'number of cycles detected: ', len(list_simple_cycles)
    print 'cycles detected: ', list_simple_cycles

    nx.draw_networkx_edges(graph, pos=dict_position_node, edge_color='b')

    set_nodes_from_cycles = list(set([item for sublist in list_simple_cycles for item in sublist]))
    nx.draw_networkx_nodes(graph, pos=dict_position_node, node_list=set_nodes_from_cycles, edge_color='r')

    plt.show()

    return graph
