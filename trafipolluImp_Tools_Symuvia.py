__author__ = 'atty'

import operator
from numpy import asarray
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform

from shapely.geometry import MultiPoint
import matplotlib.pyplot as plt

import parser_symuvia_xsd_2_04_pyxb as symuvia_parser



# xml_filename="/home/atty/Prog/reseau_symuvia/reseau_paris6_v11_new.xml"
def extract_convexhull_from_symuvia_network(
        **kwargs
):
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
            print 'extract_convexhull_from_symuvia_network - Exception: ', e
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
        # url: http://toblerity.org/shapely/manual.html
        convex_hull = MultiPoint(list_extremites).convex_hull
        list_convex_hull = list(convex_hull.exterior.coords)

    return list_convex_hull, list_extremites


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
def debug_draw(
        results_from_ecfsn
):
    """

    :param results_from_ecfsn:
    :return:
    """
    convex_hull, points_cloud = results_from_ecfsn

    # url: http://docs.scipy.org/doc/scipy-dev/reference/generated/scipy.spatial.ConvexHull.html
    #url: http://matplotlib.org/users/pyplot_tutorial.html
    np_convex_hull = asarray(convex_hull)
    np_points_cloud = asarray(points_cloud)

    plt.plot(np_convex_hull[:, 0], np_convex_hull[:, 1], '--b', lw=2)
    plt.plot(np_points_cloud[:, 0], np_points_cloud[:, 1], 'ro')

    plt.show()
