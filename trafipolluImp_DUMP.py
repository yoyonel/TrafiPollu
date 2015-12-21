"""

Module de gestion pour le DUMP des donnees DB-StreetGen vers Python

.. warning::
    Il y a une partie construction TOPOlogique aussi dans ce module
    -> Probleme de design a revoir !

"""

__author__ = 'latty'

import numpy as np
from itertools import groupby

from shapely.wkb import loads as sp_wkb_loads

import imt_tools
from imt_tools import timer_decorator

# need to be in Globals for Pickled 'dict_edges'
"""
"""
NT_LANE_INFORMATIONS = imt_tools.create_namedtuple_on_globals(
    'NT_LANE_INFORMATIONS',
    [
        'lane_side',
        'lane_direction',
        'lane_center_axis',
        'nb_lanes'
    ]
)

"""
"""
str_ids_for_lanes = {
    'SG3 Informations': "LANES - SG3 Informations",
    'SG3 to SYMUVIA': "LANES - SG3 to SYMUVIA",
    'SG3 to PYTHON': "LANES - SG3 to PYTHON"
}

# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = imt_tools.build_logger(__name__)


@timer_decorator
def dump_for_roundabouts(objects_from_sql_request):
    """

    :param objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2

        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]
    :type objects_from_sql_request: psycopg2.extras.DictCursor.

    :return: Dictionnaire d'informations (converties) sur les ronds-points
    :rtype: `dict`.
    """
    dict_roundabouts = {}

    for object_from_sql_request in objects_from_sql_request:
        # on transfert le contenu du DictCursor
        dict_sql_request = dict(object_from_sql_request)
        # on transfert les donnees geometriques (en memoire)
        dict_sql_request.update(load_geom_buffers_with_shapely(dict_sql_request))
        dict_sql_request.update(
            load_arrays_with_numpely(
                dict_sql_request,
                [
                    ('wkb_centroid', 'np_centroid')
                ]
            )
        )
        ra_id = object_from_sql_request['id']
        dict_roundabouts.update(
            {
                ra_id: dict_sql_request
            }
        )

    return dict_roundabouts


@timer_decorator
def dump_for_edges(objects_from_sql_request):
    """

    :param objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2
        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]
    :type objects_from_sql_request: psycopg2.extras.DictCursor.

    :return:
        Renvoie un DICTionnaire avec les donnees  des 'edges'/'troncons"
        DUMPees depuis la BD-SG vers Python en format "compatibles" (exploitables) par
        Python, utilisation des formats:

            * shapely.wkb
            * numpy.array
    :rtype: `dict`.

    """
    dict_edges = {}
    # url: http://stackoverflow.com/questions/10252247/how-do-i-get-a-list-of-column-names-from-a-psycopg2-cursor
    # column_names = [desc[0] for desc in cursor.description]
    for object_from_sql_request in objects_from_sql_request:
        # dict_sql_request = object_from_sql_request.copy()
        dict_sql_request = dict(object_from_sql_request)

        dict_sql_request.update(load_geom_buffers_with_shapely(dict_sql_request))

        dict_sql_request.update(
            load_arrays_with_numpely(
                dict_sql_request,
                [
                    ('wkb_amont', 'np_amont'),
                    ('wkb_aval', 'np_aval'),
                    ('wkb_edge_center_axis', 'np_edge_center_axis')
                ]
            )
        )
        edge_id = object_from_sql_request['str_edge_id']
        dict_edges.update({edge_id: dict_sql_request})
    #
    logger.info("nb edges added: %d" % len(dict_edges.keys()))
    #
    return dict_edges


@timer_decorator
def dump_for_nodes(objects_from_sql_request):
    """

    :param objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2

        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]

    :type objects_from_sql_request: psycopg2.extras.DictCursor.:
    :return:
        Renvoie un DICTionnaire avec les donnees  des 'nodes'/'intersections"
        DUMPees depuis la BD-SG vers Python en format "compatibles" (exploitables) par
        Python, utilisation des formats:

            * shapely.wkb
            * numpy.array
    :rtype: `dict`.
    """
    dict_nodes = {}
    # get values from SQL request
    for object_from_sql_request in objects_from_sql_request:
        #
        str_node_id = object_from_sql_request['str_node_id']
        dict_sql_request = {
            'array_str_edge_ids': object_from_sql_request['str_edge_ids'],
            'wkb_geom': object_from_sql_request['wkb_geom']
        }
        dict_sql_request.update(load_geom_buffers_with_shapely(dict_sql_request))
        #
        dict_sql_request.update(
            load_arrays_with_numpely(
                dict_sql_request,
                [
                    ('wkb_geom', 'np_geom')
                ]
            )
        )
        #
        # print '%s - dict_sql_request: %s' % (str_node_id, dict_sql_request['np_geom'])
        #
        dict_nodes[str_node_id] = dict_sql_request
    #
    logger.info("nb nodes added: %d" % len(dict_nodes.keys()))

    # for k, v in dict_nodes.iteritems():
    #     print 'dict_nodes[%s].np_geom: %s' % (k, v['np_geom'])
    #
    return dict_nodes


@timer_decorator
def dump_for_interconnexions(objects_from_sql_request):
    """

    :param objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2

        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]

    :type objects_from_sql_request: psycopg2.extras.DictCursor.

    :return:
        #.  Renvoie un DICTionnaire avec les donnees  des 'edges'/'troncons"
            DUMPees depuis la BD-SG vers Python en format "compatibles" (exploitables) par
            Python, utilisation des formats:

            * shapely.wkb
            * numpy.array
        #.  DICTionnaire de set ids des inrerconnexions:

            * key: `str`.
            * vallues: set().
    :rtype: (dict, dict).

    """
    dict_interconnexions = {}
    dict_set_id_edges = {}
    nb_total_interconnexion = 0

    for object_from_sql_request in objects_from_sql_request:
        #
        node_id = object_from_sql_request['str_node_id']
        #
        dict_sql_request = {
            'edge_id1': object_from_sql_request['str_edge_id1'],
            'edge_id2': object_from_sql_request['str_edge_id2'],
            'lane_ordinality1': object_from_sql_request['str_lane_ordinality1'],
            'lane_ordinality2': object_from_sql_request['str_lane_ordinality2'],
            'wkb_interconnexion': object_from_sql_request['wkb_interconnexion']
        }
        #
        dict_sql_request.update(load_geom_buffers_with_shapely(dict_sql_request))
        #
        dict_sql_request.update(
            load_arrays_with_numpely(
                dict_sql_request,
                [
                    ('wkb_interconnexion', 'np_interconnexion')
                ]
            )
        )
        #
        dict_interconnexions.setdefault(node_id, []).append(dict_sql_request)
        #
        dict_set_id_edges.setdefault(node_id, set()).add(dict_sql_request['edge_id1'])
        dict_set_id_edges[node_id].add(dict_sql_request['edge_id2'])
        #
        nb_total_interconnexion += 1

    #
    logger.info("nb interconnexions added: %d" % len(dict_interconnexions.keys()))
    logger.info("total interconnexions added: %d" % nb_total_interconnexion)
    #
    return dict_interconnexions, dict_set_id_edges


def load_arrays_with_numpely(dict_sql_request, list_params_to_convert):
    """

    :param dict_sql_request:
        * key: .
        * values: .
    :type dict_sql_request: `dict`.

    :param list_params_to_convert:
    :type list_params_to_convert: list(tuples).

    :return:
        * key: .
        * values: .
    :rtype: `dict`.

    """
    dict_arrays_loaded = {}
    for param_name, column_name in list_params_to_convert:
        dict_arrays_loaded[column_name] = np.asarray(dict_sql_request[param_name])
    return dict_arrays_loaded


def load_geom_buffers_with_shapely(dict_objects_from_sql_request):
    """

    :param dict_objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2

        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]

    :type dict_objects_from_sql_request: psycopg2.extras.DictCursor.

    :return:
        * key: .
        * values: .
    :rtype: `dict`.
    """
    dict_buffers_loaded = {}
    # urls:
    # - http://toblerity.org/shapely/manual.html
    # - http://gis.stackexchange.com/questions/89323/postgis-parse-geometry-wkb-with-ogr
    # - https://docs.python.org/2/c-api/buffer.html
    for column_name, object_from_sql_request in dict_objects_from_sql_request.iteritems():
        if isinstance(object_from_sql_request, buffer):
            dict_buffers_loaded[column_name] = sp_wkb_loads(bytes(object_from_sql_request))
    return dict_buffers_loaded


def generate_id_for_lane(object_sql_lane, nb_lanes):
    """

    :param object_sql_lane:
    :type object_sql_lane: .

    :param nb_lanes:
    :type nb_lanes: `int`.

    :return:
    :rtype: .

    """
    # lane_position = object_sql_lane['lane_position']
    # lane_side = object_sql_lane['lane_side']
    # # url: https://wiki.python.org/moin/BitManipulation
    # lambdas_generate_id = {
    # 'left': lambda nb_lanes_by_2, position, even: nb_lanes_by_2 - (position >> 1),
    #     'right': lambda nb_lanes_by_2, position, even: nb_lanes_by_2 + (position >> 1) - even,
    #     'center': lambda nb_lanes_by_2, position, even: nb_lanes_by_2
    # }
    # # update list sides for (grouping)
    # lambda_generate_id = lambdas_generate_id[lane_side]
    # nb_lanes_by_2 = nb_lanes >> 1
    # # test si l'entier est pair ?
    # # revient a tester le bit de point faible
    # even = not (nb_lanes & 1)
    #
    # return lambda_generate_id(nb_lanes_by_2, lane_position, even)
    return convert_lane_ordinality_to_python_id(object_sql_lane['lane_ordinality'], nb_lanes)


def number_is_even(number):
    """

    :param number:
    :type number: `int`.

    :return:
    :rtype: `int`.

    """
    return number % 2 == 0


def count_number_odds(number):
    """

    :param number:
    :type number: `int`.

    :return:
    :rtype: `int`.

    """
    return int(float((number / 2.0) + 0.5))


def convert_lane_ordinality_to_python_id(lane_ordinality, nb_lanes):
    """

    :param lane_ordinality:
    :type lane_ordinality: `int`.

    :param nb_lanes:
    :type nb_lanes: `int`.

    :return: IDentfiant (numerique) Python Index ([0 ... n-1])
    :rtype: `int`.

    [TEST]  Voir: :py:func:`test_convert_lane_ordinality_to_python_id`

    >>> test_convert_lane_ordinality_to_python_id()
    [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]]

    """
    nb_odds = count_number_odds(nb_lanes)
    if number_is_even(lane_ordinality):
        python_id = nb_odds + (lane_ordinality / 2) - 1
    else:
        python_id = nb_odds - (lane_ordinality + 1) / 2
    return python_id


def convert_python_id_to_lane_ordinality(python_id, nb_lanes):
    """

    :param python_id:
    :type python_id: `int`.

    :param nb_lanes:
    :type nb_lanes: `int`.

    :return:
    :rtype: `int`.

    .. todo::

        [TEST]  Voir: :py:func:`test_convert_python_id_to_lane_ordinality`

    """
    nb_odds = count_number_odds(nb_lanes)
    return ((nb_odds - python_id) * 2 - 1) if python_id < nb_odds else (python_id - nb_odds + 1) * 2


@timer_decorator
def dump_lanes(objects_from_sql_request, dict_edges):
    """

    :param objects_from_sql_request: Le type de l'object depend du cursor utilise via psycopg2

        Voir dans: :py:class:`trafipolluImp_SQL` [function: connect_sql_server]

    :type objects_from_sql_request: psycopg2.extras.DictCursor.

    :param dict_edges:
    :type dict_edges: `dict`.

    :return:
    :rtype: (dict, dict).

    """
    dict_lanes = {}
    # get sides informations for each 'edge'/'troncon'
    for object_from_sql_request in objects_from_sql_request:
        # retieve informations/values from the SQL request
        sg3_edge_id = object_from_sql_request['edge_id']
        lane_side = object_from_sql_request['lane_side']
        lane_direction = object_from_sql_request['lane_direction']
        lane_center_axis = object_from_sql_request['lane_center_axis']
        lane_ordinality = object_from_sql_request['lane_ordinality']
        #
        nb_lanes = dict_edges[sg3_edge_id]['ui_lane_number']
        #
        dict_lanes.setdefault(sg3_edge_id,
                              {
                                  str_ids_for_lanes['SG3 Informations']: [None] * nb_lanes,
                                  # pre-allocate size for list,
                                  str_ids_for_lanes['SG3 to SYMUVIA']: [None] * nb_lanes,  # pre-allocate size for list,
                                  str_ids_for_lanes['SG3 to PYTHON']: [None] * (nb_lanes + 1),
                                  # pre-allocate size for list,
                              })

        # decompression des donnees a la main
        lane_center_axis = np.asarray(sp_wkb_loads(bytes(lane_center_axis)))

        python_lane_id = generate_id_for_lane(object_from_sql_request, nb_lanes)

        set_python_lane_id(dict_lanes, sg3_edge_id, lane_ordinality, python_lane_id)

        # Attention ici !
        # on places les lanes dans des listes pythons (avec ordre python) et non dans l'ordre fournit par la requete
        # SQL (ce qui etait avant) et/ou l'ordre fournit par SG3 (ordonality id)
        set_lane_informations(
            dict_lanes, sg3_edge_id, python_lane_id,
            NT_LANE_INFORMATIONS(lane_side, lane_direction, lane_center_axis, nb_lanes)
        )

        # for future: http://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        # find a key with value

    # create the dict: dict_grouped_lanes
    # contain : for each edge_id list of lanes in same direction
    dict_grouped_lanes = build_dict_grouped_lanes(dict_lanes)

    return dict_lanes, dict_grouped_lanes


def build_dict_grouped_lanes(dict_lanes, str_id_for_grouped_lanes='grouped_lanes'):
    """

    |   A partir d'un dump des informations de 'voies' (informations contenues dans les 'edges' SG),
        construction des groupes de voies homogenes au sens SYMUVIA (du terme).
    |   Concretement si l'edge SG contient plusieurs voies ou groupes de voies dans des sens contraires (amont -> aval
        ou aval -> amont), la fonction identifie et decompose les groupes de voies (consecutives) dans le meme et cree
        une liste de groupes de voies uni-directionnelles.

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param str_id_for_grouped_lanes:
    :type str_id_for_grouped_lanes: `str`.

    :return:
        Retourne un dictionnaire dont les::
            - key: indice d'une edge SG3
            - value: liste de groupes de lanes dans le meme sens.
                     Chaque element de la liste decrit le nombre de voies consecutives dans le meme sens.
    :rtype: `dict`.

    """
    dict_grouped_lanes = {}
    map(lambda x, y: dict_grouped_lanes.__setitem__(x, {str_id_for_grouped_lanes: y}),
        dict_lanes,
        [
            [
                sum(1 for _ in value_groupby)
                for key_groupby, value_groupby in
                groupby(get_list_lanes_informations_from_edge_id(dict_lanes, sg3_edge_id), lambda x: x.lane_direction)
            ]
            for sg3_edge_id in dict_lanes
        ])
    return dict_grouped_lanes


def set_lane_informations(dict_lanes, sg3_edge_id, python_lane_id, informations):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    :param informations:
    :type informations: .

    """
    get_list_lanes_informations_from_edge_id(dict_lanes, sg3_edge_id)[python_lane_id] = informations


def get_list_lanes_informations_from_lane(lane):
    """

    :param lane:
    :type lane: list.
    :return:
    :rtype: list.

    """
    return lane[str_ids_for_lanes['SG3 Informations']]


def get_list_lanes_informations_from_edge_id(dict_lanes, sg3_edge_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :return:
    :rtype: list.

    """
    return dict_lanes[sg3_edge_id][str_ids_for_lanes['SG3 Informations']]


def get_lane_from_python_lane_id(dict_lanes, sg3_edge_id, python_lane_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    :return:
    :rtype: .

    """
    return dict_lanes[sg3_edge_id][str_ids_for_lanes['SG3 Informations']][python_lane_id]


def get_lane_direction_from_python_lane_id(dict_lanes, sg3_edge_id, python_lane_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    :return:
    :rtype: .

    """
    return get_lane_from_python_lane_id(dict_lanes, sg3_edge_id, python_lane_id).lane_direction


def get_lane_geometry_from_python_lane_id(dict_lanes, sg3_edge_id, python_lane_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    :return:
    :rtype: .

    """
    return get_lane_from_python_lane_id(dict_lanes, sg3_edge_id, python_lane_id).lane_center_axis


def get_Symuvia_list_lanes_from_edge_id(dict_lanes, sg3_edge_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :return:
    :rtype: .

    """
    return dict_lanes[sg3_edge_id][str_ids_for_lanes['SG3 to SYMUVIA']]


def get_symu_troncon_from_python_id(dict_lanes, sg3_edge_id, python_lane_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    :return:
    :rtype: .

    """
    return dict_lanes[sg3_edge_id][str_ids_for_lanes['SG3 to SYMUVIA']][python_lane_id]


def get_PYTHON_list_lanes(dict_lanes, sg3_edge_id):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :return:
    :rtype: .

    """
    return dict_lanes[sg3_edge_id][str_ids_for_lanes['SG3 to PYTHON']]


def get_python_id_from_lane_ordinality(dict_lanes, sg3_edge_id, lane_ordinality):
    """

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param lane_ordinality:
    :type lane_ordinality: `int`.

    :return:
    :rtype: .
    """
    return get_PYTHON_list_lanes(dict_lanes, sg3_edge_id)[lane_ordinality]


def set_python_lane_id(dict_lanes, sg3_edge_id, lane_ordinality, python_lane_id):
    """

    Methode:

    :param dict_lanes:
    :type dict_lanes: `dict`.

    :param sg3_edge_id:
    :type sg3_edge_id: `int`.

    :param lane_ordinality:
    :type lane_ordinality: `int`.

    :param python_lane_id:
    :type python_lane_id: `int`.

    """
    get_PYTHON_list_lanes(dict_lanes, sg3_edge_id)[lane_ordinality] = python_lane_id


#############################################
# TESTS
#############################################
def test_convert_lane_ordinality_to_python_id(max_nb_lanes=6):
    """

    Fonction test pour :py:func:`convert_lane_ordinality_to_python_id`
    Utilise la fonction: :py:func:`convert_python_id_to_lane_ordinality`

    -> l'integrite de ce test depend des deux fonctions (mentionnees)

    On test la reversibilite du calcul d'indices: SG3<->PYTHON

    :param max_nb_lanes: Nombre de groupes de voies. La taille des groupes de voies est egale a leur indice.
    :type max_nb_lanes: `uint`

    :return: List de listes d'indices generes pour chaque groupes de voies. list[list[`int`]]
    :rtype: `list`

    """
    range_nb_lanes = range(1, max_nb_lanes)
    ranges_python_id = [range(0, nb_lanes) for nb_lanes in range_nb_lanes]
    # on test la reversibilite du calcul d'indices: SG3<->PYTHON
    ranges_lane_ordinality = [
        [
            convert_python_id_to_lane_ordinality(python_id, len(ranges_python_id[nb_lanes - 1]))
            for python_id in ranges_python_id[nb_lanes - 1]
        ]
        for nb_lanes in range_nb_lanes
    ]
    return [
        [
            convert_lane_ordinality_to_python_id(lane_ordinality, len(range_lane_ordinality))
            for lane_ordinality in range_lane_ordinality
        ]
        for range_lane_ordinality in ranges_lane_ordinality
    ]
