__author__ = 'latty'

import numpy as np
from itertools import groupby

from shapely.wkb import loads as sp_wkb_loads

import imt_tools







# need to be in Globals for Pickled 'dict_edges'
NT_LANE_INFORMATIONS = imt_tools.CreateNamedTupleOnGlobals(
    'NT_LANE_INFORMATIONS',
    [
        'lane_side',
        'lane_direction',
        'nb_lanes'
    ]
)


def dump_for_edges(objects_from_sql_request):
    """

    :return:
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

        dict_sql_request['np_amont_to_aval'] = dict_sql_request['np_aval'] - dict_sql_request['np_amont']

        edge_id = object_from_sql_request['str_edge_id']
        dict_edges.update({edge_id: dict_sql_request})
    #
    print '# dump_for_edge - nb edges added: ', len(dict_edges.keys())
    #
    return dict_edges


def dump_for_nodes(objects_from_sql_request):
    """

    :return:
    """
    dict_nodes = {}
    # get values from SQL request
    for object_from_sql_request in objects_from_sql_request:
        #
        str_node_id = object_from_sql_request['str_node_id']
        array_str_edge_ids = object_from_sql_request['str_edge_ids']
        #
        dict_nodes[str_node_id] = {'array_str_edge_ids': array_str_edge_ids}
    #
    print '# dump_for_nodes - nb nodes added: ', len(dict_nodes.keys())
    #
    return dict_nodes


def dump_for_interconnexions(objects_from_sql_request):
    """

    :param objects_from_sql_request:
    :return:

    """
    dict_interconnexions = {}
    nb_total_interconnexion = 0
    for object_from_sql_request in objects_from_sql_request:
        #
        node_id = object_from_sql_request['str_node_id']
        #
        dict_interconnexions.setdefault(node_id, []).append(
            {
                'edge_id1': object_from_sql_request['str_edge_id1'],
                'edge_id2': object_from_sql_request['str_edge_id2'],
                'lane_ordinality1': object_from_sql_request['str_lane_ordinality1'],
                'lane_ordinality2': object_from_sql_request['str_lane_ordinality2'],
                'np_interconnexion': np.asarray(object_from_sql_request['wkb_interconnexion'])
            }
        )
        nb_total_interconnexion += 1
    #
    print '# dump_for_interconnexions - nb CAF added: ', len(dict_interconnexions.keys())
    print '# dump_for_interconnexions - total interconnexions added: ', nb_total_interconnexion
    #
    return dict_interconnexions


def load_arrays_with_numpely(dict_sql_request, list_params_to_convert):
    """

    :param dict_objects_from_sql_request:
    :param list_params_to_convert:
    :return:
    """
    dict_arrays_loaded = {}
    for param_name, column_name in list_params_to_convert:
        dict_arrays_loaded[column_name] = np.asarray(dict_sql_request[param_name])
    return dict_arrays_loaded


def load_geom_buffers_with_shapely(dict_objects_from_sql_request):
    """

    :param dict_objects_from_sql_request:
    :return:
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

    :return:
    """
    # url: https://wiki.python.org/moin/BitManipulation
    lambdas_generate_id = {
        'left': lambda nb_lanes_by_2, position, even: nb_lanes_by_2 - (position >> 1),
        'right': lambda nb_lanes_by_2, position, even: nb_lanes_by_2 + (position >> 1) - even,
        'center': lambda nb_lanes_by_2, position, even: nb_lanes_by_2
    }

    lane_position = object_sql_lane['lane_position']
    lane_side = object_sql_lane['lane_side']

    # update list sides for (grouping)
    lambda_generate_id = lambdas_generate_id[lane_side]
    nb_lanes_by_2 = nb_lanes >> 1
    # test si l'entier est pair ?
    # revient a tester le bit de point faible
    even = not (nb_lanes & 1)

    return lambda_generate_id(nb_lanes_by_2, lane_position, even)


def dump_lanes(objects_from_sql_request, dict_edges, dict_lanes):
    # get sides informations for each 'edge'/'troncon'
    for object_from_sql_request in objects_from_sql_request:
        #
        edge_id = object_from_sql_request['edge_id']
        lane_side = object_from_sql_request['lane_side']
        #
        nb_lanes = dict_edges[edge_id]['ui_lane_number']
        dict_lanes.setdefault(edge_id,
                              {
                                  'informations': [None] * nb_lanes,  # pre-allocate size for list,
                                  'sg3_to_symuvia': [None] * nb_lanes,  # pre-allocate size for list,
                                  'sg3_to_python': {}
                              })
        #
        lane_center_axis = object_from_sql_request['lane_center_axis']
        lane_center_axis = np.asarray(sp_wkb_loads(bytes(lane_center_axis)))
        dict_lanes[edge_id].setdefault('lane_center_axis', []).append(lane_center_axis)

        lane_direction = object_from_sql_request['lane_direction']

        # id_in_list = object_from_sql_request['lane_ordinality'] - 1
        id_in_list = generate_id_for_lane(object_from_sql_request, nb_lanes)
        # print 'edge_id: %s id_in_list: %s' % (edge_id, id_in_list)

        dict_lanes[edge_id]['informations'][id_in_list] = NT_LANE_INFORMATIONS(
            lane_side,
            lane_direction,
            nb_lanes
        )

        dict_lanes[edge_id]['sg3_to_python'].update({object_from_sql_request['lane_ordinality']: id_in_list})
        # for future: http://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        # find a key with value

    # print "** dict_lanes: ", dict_lanes
    # print "** _dict_sides:", self.__dict_sides

    # create the dict: dict_grouped_lanes
    # contain : for each edge_id list of lanes in same direction
    dict_grouped_lanes = {}
    map(lambda x, y: dict_grouped_lanes.__setitem__(x, {'grouped_lanes': y}),
        dict_lanes,
        [
            [
                sum(1 for i in g) for edge_id, g in
                groupby(dict_lanes[edge_id]['informations'], lambda x: x.lane_direction)
            ]
            for edge_id in dict_lanes
        ])
    print "** self._dict_grouped_lanes:", dict_grouped_lanes

    # update dict_edges with lanes grouped informations
    for edge_id, grouped_lanes in dict_grouped_lanes.items():
        dict_edges[edge_id].update(grouped_lanes)
        # print "** self._dict_edges: ", dict_edges


def edges_is_same_orientation(edge0, edge1):
    """

    :param edge0:
    :param edge1:
    :return:

    """
    return edge0.dot(edge1) > 0


def compute_direction_linestring(np_linestring):
    """

    :param linestring:
    :return:

    """
    amont = np_linestring[0]
    aval = np_linestring[-1]
    return amont - aval