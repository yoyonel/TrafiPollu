__author__ = 'atty'

import operator
from numpy import asarray
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from lxml import etree

from shapely.geometry import MultiPoint
import matplotlib.pyplot as plt

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser



# creation de l'objet logger qui va nous servir a ecrire dans les logs
from imt_tools import init_logger

logger = init_logger(__name__)


# xml_filen ame="/home/atty/Prog/reseau_symuvia/reseau_paris6_v11_new.xml"
# >>> t1 = time.time();
# >>> result = extract_convexhull_from_symuvia_network(symuvia_xml_filename='/home/atty/Prog/reseau_symuvia/reseau_paris6_v11_new.xml');
# >>> print 'time: ', time.time() - t1
# time:  2.25858998299
def extract_convexhull_from_symuvia_network(**kwargs):
    """

    :param xml_filename:
    :return:

    """
    list_extremites = []
    list_convex_hull = []

    symu_ROOT = None

    if 'symuvia_xml_filename' in kwargs:
        xml_filename = kwargs['symuvia_xml_filename']
        try:
            xml = open(xml_filename).read()
            symu_ROOT = symuvia_parser.CreateFromDocument(xml)
        except Exception, e:
            logger.fatal('extract_convexhull_from_symuvia_network - Exception: ', e)
    elif 'symuvia_root_node' in kwargs:
        symu_ROOT = kwargs['symuvia_root_node']

    if symu_ROOT:
        # On utilise les extremites amont/aval des TRONCONS
        # pour calculer le convex hull du reseau
        # On pourrait (peut etre) n'utiliser que les EXTREMITES definit dans le XML
        # pour recuperer une enveloppe (convex hull) exploitable ...  A VOIR !
        symu_ROOT_RESEAU_TRONCONS = symu_ROOT.RESEAUX.RESEAU[0].TRONCONS
        list_TRONCONS = symu_ROOT_RESEAU_TRONCONS.TRONCON
        # url: http://stackoverflow.com/a/952943 (Making a flat list out of list of lists in Python)
        list_extremites = reduce(
            operator.add,
            [(TRONCON.extremite_amont, TRONCON.extremite_aval) for TRONCON in list_TRONCONS]
        )
        logger.info('# list_extremites: ', len(list_extremites))
        # url: http://toblerity.org/shapely/manual.html
        convex_hull = MultiPoint(list_extremites).convex_hull
        list_convex_hull = list(convex_hull.exterior.coords)

    return list_convex_hull, list_extremites


# >>> t1 = time.time();
# >>> result = extract_convexhull_from_symuvia_network_2(symuvia_xml_filename='/home/atty/Prog/reseau_symuvia/reseau_paris6_v11_new.xml');
# >>> print 'time: ', time.time() - t1
# time:  0.0156140327454
def extract_convexhull_from_symuvia_network_2(
        **kwargs
):
    """

    :param xml_filename:
    :return:

    """
    xml_filename = kwargs['symuvia_xml_filename']

    # url: http://www.ibm.com/developerworks/library/x-hiperfparse/
    class TronconsExtremitesTarget(object):
        def __init__(self):
            self.TRONCONS = {}
            self.EXTREMITES = []
            self.dict_amonts_avals = {}
            self.in_RESEAUX = False

        def start(self, tag, attrib):
            if tag == 'RESEAUX':
                self.in_RESEAUX = True

            if self.in_RESEAUX:
                if tag == 'TRONCON':
                    id_TRONCON = attrib['id']
                    # url: http://stackoverflow.com/questions/5352546/best-way-to-extract-subset-of-key-value-pairs-from-python-dictionary-object
                    list_of_keys = ('extremite_amont', 'extremite_aval', 'id_eltamont')
                    self.TRONCONS[id_TRONCON] = {k: v for k, v in attrib.iteritems() if k in list_of_keys}
                    #
                    self.dict_amonts_avals[attrib['id_eltaval']] = id_TRONCON
                    self.dict_amonts_avals[attrib['id_eltamont']] = id_TRONCON
                if tag == 'EXTREMITE':
                    id_EXTREMITE = attrib['id']
                    self.EXTREMITES.append(id_EXTREMITE)

        def end(self, tag):
            if tag == 'RESEAUX':
                self.close()

        def data(self, data):
            pass

        def close(self):
            return self.TRONCONS, self.EXTREMITES, self.dict_amonts_avals

    parser = etree.XMLParser(target=TronconsExtremitesTarget())
    # list_extremites = find_extremites_without_tests(etree.parse(xml_filename, parser))
    list_extremites = find_extremites_with_tests(etree.parse(xml_filename, parser))

    # # url: http://toblerity.org/shapely/manual.html
    convex_hull = MultiPoint(list_extremites).convex_hull
    list_convex_hull = list(convex_hull.exterior.coords)

    return list_convex_hull, list_extremites


def find_extremites_without_tests(*results_parse):
    """

    :param results_parse:
    :return:
    on genere la liste des coordonnees des amonts/avals des troncons qui possede au moins une extremite

    Version sans TEST du coup on double le nombre de points dans le nuage (amont&aval des troncons avec extremites)

    """
    # url: http://stackoverflow.com/questions/4004550/converting-string-series-to-float-list-in-python
    dict_TRONCONS, list_EXTREMITES, dict_amonts_avals = results_parse

    list_extremites = reduce(
        operator.add,
        [
            # conversion des coordonnees amont/aval en list float
            (
                [float(x) for x in TRONCON['extremite_amont'].split()],
                [float(x) for x in TRONCON['extremite_aval'].split()]
            )
            # on recupere les TRONCONS dont l'amont ou l'aval est une extremite
            for TRONCON in
            [
                dict_TRONCONS[dict_amonts_avals[id_EXTREMITE]]
                for id_EXTREMITE in list_EXTREMITES
            ]
        ]
    )
    return list_extremites


def find_extremites_with_tests(*results_parse):
    """

    :param result_parse:
    :return:

    Version avec TEST (on cherche un id dans un dictionnaire (... in list_EXTREMITES ...))
    On recupere les coordonnees des extremites uniquement (amont ou aval)

    """
    dict_TRONCONS, list_EXTREMITES, dict_amonts_avals = results_parse
    list_str_amont_aval = ('aval', 'amont')
    list_extremites = [
        #
        [
            # on convertit les coordonnees contenues dans la str en liste de floattants
            float(x) for x in
            # on recupere la str representant les coordonnees de l'amont ou l'aval selon si l'amont ou l'aval
            # est une extremite (un des deux).
            TRONCON['extremite_' + list_str_amont_aval[TRONCON['id_eltamont'] in list_EXTREMITES]].split()
        ]
        # on recupere les TRONCONS dont l'amont ou l'aval est une extremite
        for TRONCON in
        [
            dict_TRONCONS[dict_amonts_avals[id_EXTREMITE]]
            for id_EXTREMITE in list_EXTREMITES
        ]
    ]
    return list_extremites


def build_QgsTransfrom_from_Symuvia_to_SG3(
        symuviaSrid=2154,  # LAMBERT93
        postgisSrid=932011  # Custom (translated) Lambert93
):
    """

    :return:

    """
    src_crs = QgsCoordinateReferenceSystem().createFromProj4(symuviaSrid)
    dst_crs = QgsCoordinateReferenceSystem(postgisSrid, QgsCoordinateReferenceSystem.PostgisCrsId)
    return QgsCoordinateTransform(src_crs, dst_crs)


# appel: debug_draw(extract_convexhull_from_symuvia_network())
def debug_draw(results_from_ecfsn):
    """

    :param results_from_ecfsn:
    :return:
    """
    convex_hull, points_cloud = results_from_ecfsn

    # url: http://docs.scipy.org/doc/scipy-dev/reference/generated/scipy.spatial.ConvexHull.html
    # url: http://matplotlib.org/users/pyplot_tutorial.html
    np_convex_hull = asarray(convex_hull)
    np_points_cloud = asarray(points_cloud)

    plt.plot(np_convex_hull[:, 0], np_convex_hull[:, 1], '--b', lw=2)
    plt.plot(np_points_cloud[:, 0], np_points_cloud[:, 1], 'ro')

    plt.show()
