"""Module d'implementation principale du plugin: Interactive Map Tracking pour le project TrafiPollu

.. moduleauthor:: Lionel ATTY <lionel.atty@ign.fr>
"""
__author__ = 'atty'

import os
import cPickle as pickle

from signalsmanager import SignalsManager
import imt_tools
from trafipolluImp_SQL import trafipolluImp_SQL
import trafipolluImp_EXPORT as tpi_EXPORT
import trafipolluImp_TOPO as tpi_TOPO

from imt_tools import build_logger
# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = build_logger(__name__)
#
# logger = build_logger(__name__, list_handlers=['toto'])
# Affichage dans la console:
#   WARNING - Pas de module de gestion pour l'handler: ''toto''
#   (module a ajouter dans /home/latty/.qgis2/python/plugins/interactive_map_tracking/imt_tools.py)


class TrafiPolluImp(object):
    """
    Classe principale d'implementation du plugin
    """

    def __init__(self, iface, dlg):
        """

        Methode d'entree du plugin.
        Lancee au chargement des plugins par QGIS

        :param iface: interface vers QGIS windows
        :param dlg: boite de dialogue QT => interface vers notre GUI Qt
        :return:

        """
        ##############
        # GUI
        ##############
        self.dlg = dlg
        # utilitaire pour la gestion des signaux Qt
        # utilise pour la gestion des interactions avec le GUI (Qt) du plugin
        # SignalsManager utilise un pattern singleton, ce module peut etre considere 'global' (au plugin)
        self.signals_manager = SignalsManager.instance()
        ##############

        ##############
        # MODULES
        ##############
        # Structures de donnees principales
        # pour les modules: SQL, DUMP, TOPO et EXPORT
        self.__dict_edges = {}  # key: id_edge  -   value: (topo) informations from SG3
        self.__dict_lanes = {}
        self.__dict_nodes = {}
        self.__dict_roundabouts = {}

        # Construction d'un dictionnaire de transmissions de parametres (membres)
        # C'est le mecanisme utilise pour simuler un pattern de modularite
        # (pas forcement la meilleur solution, a reflechir)
        kwargs = {
            'iface': iface,
            'dict_edges': self.__dict_edges,
            'dict_lanes': self.__dict_lanes,
            'dict_nodes': self.__dict_nodes,
            'dict_roundabouts': self.__dict_roundabouts,
        }
        # Initialisation des modules
        # Transmissions des parametres/membres 'communs'
        self.module_SQL = trafipolluImp_SQL(**kwargs)
        self.module_topo = tpi_TOPO.trafipolluImp_TOPO(**kwargs)
        kwargs.update({'module_topo': self.module_topo})
        self.module_export = tpi_EXPORT.trafipolluImp_EXPORT(**kwargs)
        ##############

        ##############
        # LOGS
        ##############
        logger.info("Init")
        ##############

    ##############
    # GUI
    ##############
    def _init_signals_(self):
        """

        Initialisation des signaux pour la gestion des interactions avec la fenetre GUI du plugin
        :return:
        """
        #
        self.signals_manager.add_clicked(self.dlg.execute_sql_commands, self.slot_execute_SQL_commands, "GUI")
        self.signals_manager.add_clicked(self.dlg.refreshSqlScriptList, self.slot_refreshSqlScriptList, "GUI")
        self.signals_manager.add_clicked(self.dlg.pickle_trafipollu, self.slot_Pickled_TrafiPollu, "GUI")
        self.signals_manager.add_clicked(self.dlg.export_to_symuvia, self.slot_export_to_symuvia, "GUI")
        self.signals_manager.add_clicked(self.dlg.tf_dump_topo_export, self.slot_dump_topo_export, "GUI")
        self.signals_manager.add_clicked(self.dlg.tf_clear, self.slot_clear, "GUI")
        #
        self.signals_manager.add(self.dlg.combobox_sql_scripts,
                                 "currentIndexChanged (int)",
                                 self.slot_currentIndexChanged_SQL,
                                 "GUI")

    ##################
    ### GUI: SLOTS ###
    ##################
    # Interface entre Qt-GUI et le plugin
    # a terme: Faudrait automatiser cette generation de code (l'Interface)
    def slot_clear(self):
        """

        Interface GUI-Plugin: 'clear'

        :return:
        """
        self._clear_()

    def slot_dump_topo_export(self):
        """

        Interface GUI-Plugin: 'Dump Topo Export'

        :return:
        """
        self._dump_topo_export_()

    def slot_Pickled_TrafiPollu(self):
        """

        Interface GUI-Plugin: Serialisation

        :return:
        """
        self._pickled_trafipollu_()

    def slot_execute_SQL_commands(self):
        """

        Interface GUI-Plugin: lancement d'execution d'un script SQL

        :return:
        """
        self._execute_sql_commands(
            self.dlg.plainTextEdit_sql_script.toPlainText(),
            imt_tools.get_itemText(self.dlg.combobox_sql_scripts)
        )

    def slot_refreshSqlScriptList(self):
        """

        Interface GUI: Mise a jour de la liste des scripts SQL dans l'interface GUI

        :return:
        """
        self._refresh_sql_script_list()

    def slot_currentIndexChanged_SQL(self, id_index):
        """

        Interface GUI: Mise a jour de l'affichage du source du script SQL courant dans l'interface GUI

        :param id_index:
        """
        sql_filename = imt_tools.get_itemData(self.dlg.combobox_sql_scripts)
        self.dlg.plainTextEdit_sql_script.setPlainText(self.get_sql_file(sql_filename))

    def slot_export_to_symuvia(self):
        """

        Interface GUI-Plugin: lancement l'execution du module 'EXPORT'

        :return:
        """
        self.module_export.export(True)
    ##################

    ################################################################################
    ### PLUG/GUI: Implementations des methodes/fonctions utilisees par les SLOTS ###
    ################################################################################
    @staticmethod
    def _enable_trafipollu_():
        """

        Connection with QGIS interface

        """
        pass

    def _disable_trafipollu_(self):
        """

        Disconnection with QGIS interface

        """
        self.module_SQL.disconnect_sql_server()

    def _execute_sql_commands(self, sql_file, sql_choice_combobox):
        """

        Lance l'execution d'un script SQL decrit par son source sql_file.
        On utilise le parametre sql_choice_combobox pour identifier (plus rapidement) le script qu'on souhaite execute.

        :param sql_file:
        :type sql_file: str
        :param sql_choice_combobox:
        :type sql_choice_combobox: str
        :return:
        """
        self.module_SQL.execute_sql_commands(sql_file, sql_choice_combobox)

    @staticmethod
    def get_sql_filename(sql_name):
        """

        Construction d'un nom de fichier SQL par rapport a un nom de script SQL du plugin

        :param sql_name:
        :type sql_name: str
        :return:
        :rtype: str
        """
        path = os.path.normcase(os.path.dirname(__file__))
        return path + '/' + sql_name + '.sql'

    @staticmethod
    def get_sql_file(sql_filename):
        """

        Charge un fichier/script SQL et renvoie son contenu

        :param sql_filename: Nom du fichier/script SQL
        :type sql_filename: str
        :return: Renvoie le contenu du script SQL
        :rtype: str

        """
        sql_file = ""
        try:
            fd = open(sql_filename)
            if fd:
                sql_file = fd.read()
                fd.close()
        except Exception as e:
            logger.warning("Probleme de lecture du fichier sql: {0}".format(sql_filename))
            logger.warning("-> Exception: {0}", e)
        finally:
            return sql_file

    def _refresh_sql_script_list(self):
        """

        Rafraichi la liste des scripts SQL disponible dans l'interface/GUI du plugin
        :return:
        """
        self.dlg.combobox_sql_scripts.clear()

        path = os.path.normcase(os.path.dirname(__file__))
        files = os.listdir(path)

        [
            self.dlg.combobox_sql_scripts.addItem(os.path.basename(i)[:-4], path + '/' + i)
            for i in files if i.endswith('.sql')
        ]

    def _dump_topo_export_(self):
        """

        Lance une serie d'operations pour effectuer un export 'complet' de QGIS -> SYMUVIA
        Les operations sont:
        - DUMP: StreetGen[DB] -> StreetGen[PYTHON]

            - edges: troncons/axe des routes
            - lanes: voies pour chaque troncon
            - nodes: noeuds d'intersections entre les troncons (carrefours, rond-point, etc ...)
            - interconnexions: interconnections des voies (rattachees a des troncons) dans une intersection (node)
            - rond-points: informations sur les rond-points 'detectes' [desactiver]

        - TOPO: StreetGen[PYTHON] -> Format compatible StreetGen-TrafiPollu[PYTHON]
        - EXPORT: Format compatible StreetGen-TrafiPollu[PYTHON] -> XML pour SYMUVIA[XML]

        :return:

        """
        #
        list_sql_commands = [
            # probleme avec la lib psycopg2 : https://github.com/philipsoutham/py-mysql2pgsql/issues/80
            # -> utilise un polygone statique pour definir def_zone_test
            # 'update_def_zone_test',
            # -> utilise le mapcanvas de qgis (viewport) pour definir la zone d'export
            'update_table_edges_from_qgis',
            # -> utliise la couche layer 'def_zone_test' pour extraire un polygon et definir la zone d'export
            # ne fonctionne pas/plus ... je ne sais pas pourquoi ...
            # 'update_tables_from_def_zone_test',

            #
            'dump_informations_from_edges',
            'dump_sides_from_edges',
            'dump_informations_from_nodes',
            'dump_informations_from_lane_interconnexion',
            # TODO: travail sur les rond-points [desactiver]
            # 'dump_roundabouts',
        ]
        # boucle sur les operations SQL a traiter (pour le DUMP)
        for sql_command in list_sql_commands:
            # Selon l'operation SQL, on recupere le fichier script .sql (correspondant)
            sql_filename = self.get_sql_filename(sql_command)
            sql_file = self.get_sql_file(sql_filename)
            # traitement de la requete SQL [DUMP/TOPO]
            self._execute_sql_commands(
                sql_file,
                sql_command
            )

        # TEST: construction d'un graph topologique
        # imt_tools.build_networkx_graph(self.__dict_nodes, self.__dict_edges)

        # traitement de la requete d'export [EXPORT]
        self.module_export.export(True)

    def _clear_(self):
        """

        Lance un 'clear' sur les structures de donnees utilisees par le plugin
        ~ re-initialise les donnees du cote du plug (clean)

        :return:

        """
        logger.info('clean ressources ...')
        # clear des structures de donnees utilisees pour les DUMP/TOPO
        self.__dict_edges.clear()
        self.__dict_lanes.clear()
        self.__dict_nodes.clear()
        # On clear les donnees rattachees aux modules: TOPO, EXPORT
        self.module_topo.clear()
        self.module_export.clear()

    #############################
    ### SERIALISATION: PICLKE ###
    #############################
    def _pickled_trafipollu_(self):
        """

        Module de serialisation du plugin.
        Cette partie n'est pas finalisee.
        La serialisation (dans le cadre du plugin/projet) peut etre interessante pour effectuer des debugs/tests/...
        offline par rapport a la base de donnees.

        .. warning::
            Non stabilise, non teste, a utiliser en toute connaissance de cause

        :return:
        """
        # test Pickle
        qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))
        infilename_for_pickle = qgis_plugins_directory + '/' + "dump_pickle.p"
        logger.info("Pickle TrafiPollu in: %s ..." % infilename_for_pickle)
        pickle.dump(self, open(infilename_for_pickle, "wb"))
        logger.info("Pickle TrafiPollu in: %s [DONE]" % infilename_for_pickle)

    def __getstate__(self):
        """

        SERIALISATION: recupere l'etat de l'interface principale

        note: normalement les objects numpy (array) et shapely (natif, wkb/t) sont 'dumpables'
        et donc serialisables via Pickle !

        NUMPY test:
        ----------
        >>> import cPickle as pickle
        >>> import numpy as np
        >>> np_object = np.asarray([1, 2])
        >>> pickle.dumps(np_object)
        "cnumpy.core.multiarray\n_reconstruct\np1\n(cnumpy\nndarray\np2\n(I0\ntS'b'\ntRp3\n(I1\n(I2\ntcnumpy\ndtype\np4\n(S'i8'\nI0\nI1\ntRp5\n(I3\nS'<'\nNNNI-1\nI-1\nI0\ntbI00\nS'\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntb."
        >>> str_dump_pickle = pickle.dumps(np_object)
        >>> pickle.loads(str_dump_pickle)
        array([1, 2])

        SHAPELY tests:
        -------------
        >>> import shapely.geometry as sp_geom
        >>> import shapely.wkb as sp_wkb
        >>> point = sp_geom.Point(0, 0)
        >>> pickle.dumps(point)
        "cshapely.geometry.point\nPoint\np1\n(tRp2\nS'\\x01\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nb."
        >>> pickle.dumps(point.wkb)
        "S'\\x01\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\n."
        >>> str_point_wkb = pickle.dumps(point.wkb)
        >>> pickle.loads(str_point_wkb)
        '\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        >>> sp_wkb.loads(pickle.loads(str_point_wkb))
        <shapely.geometry.point.Point object at 0x7fc00e1ace50>
        >>> sp_wkb.loads(pickle.loads(str_point_wkb)).wkt
        'POINT (0 0)'

        :return: Dictionnaire contenant une representation d'une serialisation de la classe
        :rtype: dict
        """

        #
        # NAMEDTUPLE:
        # ----------
        # Ya un truc/trick pour le support des namedtuple, le type ou le namedtuple doit etre present
        # dans le contexte de la classe pickler, du coup le namedtuple est initialise a l'exterieur (autre module)
        # on doit s'assurer que le type est accessible. Pour ce faire, j'utilise le contexte globals() de python.
        # Ya une fonction dans imt_tools qui permet de creer un type namedtuple et rajouter en meme temps le type
        # dans le contexte global de python (ya peut etre moyen de faire quelque chose de plus propre avec un contexte
        # a l'echelle du pluging ... a voir)

        dict_states_for_pickle = {
            'dict_edges': self.__dict_edges,
            'dict_lanes': self.__dict_lanes,
            'dict_nodes': self.__dict_nodes,
        }
        return dict_states_for_pickle

    def __setstate__(self, states):
        """

        Recupere et place des states pickle dans la classe.

        :param states:
        :type states: pickle
        :return:
        """
        self.pickle_states = states
    #############################
