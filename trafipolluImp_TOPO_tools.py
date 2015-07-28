__author__ = 'latty'

from imt_tools import CreateNamedTupleOnGlobals
from imt_tools import CreateNamedTuple

NT_LANE_SG3_SYMU = CreateNamedTupleOnGlobals(
    'NT_LANE_SG3_SYMU',
    [
        'symu_troncon',
        'start_id_lane',
        'nb_lanes',
        'lane_direction'
    ]
)

NT_INTERCONNEXION = CreateNamedTupleOnGlobals(
    'NT_INTERCONNEXION',
    [
        'lane_amont',
        'lane_aval',
        'geometry'
    ]
)

NT_CONNEXIONS_SYMUVIA = CreateNamedTupleOnGlobals(
    'NT_CONNEXIONS_SYMUVIA',
    [
        'list_connexions',
        'type_connexion'
    ]
)

NT_CONNEXION_SYMUVIA = CreateNamedTupleOnGlobals(
    'NT_CONNEXION_SYMUVIA',
    [
        'nt_symuvia_lane_amont',
        'nt_symuvia_lane_aval',
        'interconnexion_geom'
    ]
)

NT_LANE_SYMUVIA = CreateNamedTupleOnGlobals(
    'NT_LANE_SYMUVIA',
    [
        'symu_troncon',
        'id_lane',
    ]
)
#
NT_LANES_SYMUVIA = CreateNamedTupleOnGlobals(
    'NT_LANES_SYMUVIA',
    [
        'symu_troncon',
        'ids_lane'
    ]
)

NT_RESULT_BUILD_PYXB = CreateNamedTuple(
    'NT_RESULT_BUILD_PYXB',
    [
        'amont',
        'aval',
        'points_internes'
    ]
)

NT_TYPE_EXTREMITE = CreateNamedTuple(
    'NT_TYPE_EXTREMITE',
    [
        'is_entree',
        'is_sortie'
    ]
)

NT_LISTS_EXTREMITE = CreateNamedTuple(
    'NT_LISTS_EXTREMITE',
    [
        'list_entrees',
        'list_sorties',
        'set_edges_ids'
    ]
)


def number_is_even(number):
    """

    :param number:
    :return:

    """
    return number % 2 == 0


def count_number_odds(number):
    """

    :param number:
    :return:

    """
    return int(float((number / 2.0) + 0.5))


def count_number_even(number):
    return number - count_number_odds(number)


def test_count_number_odds(max_number=16):
    """

    :param max_number:
    :return:

    TESTS:
        >> test_count_number_odds()
        [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8]

    """
    range_numbers = range(0, max_number)
    return [
        count_number_odds(number)
        for number in range_numbers
    ]


def convert_lane_ordinality_to_python_id(lane_ordinality, nb_lanes):
    return convert_lane_ordinality_to_python_id_left(lane_ordinality, nb_lanes)
    # return convert_lane_ordinality_to_python_id_right(lane_ordinality, nb_lanes)


def convert_python_id_to_lane_ordinality(python_id, nb_lanes):
    # ordre de SG3 [3, 1, 2, 4] sur edge de 4 voies
    return convert_python_id_to_lane_ordinality_left(python_id, nb_lanes)
    # return convert_python_id_to_lane_ordinality_right(python_id, nb_lanes)


def convert_python_id_to_lane_ordinality_left(python_id, nb_lanes):
    """

    :param python_id:
    :param nb_lanes:
    :return:

    TESTS:
        >> test_convert_python_id_to_lane_ordinality()
        [[1], [1, 2], [3, 1, 2], [3, 1, 2, 4], [5, 3, 1, 2, 4]]

    """
    nb_odds = count_number_odds(nb_lanes)
    if python_id < nb_odds:
        lane_ordinality = (nb_odds - python_id) * 2 - 1
    else:
        lane_ordinality = (python_id - nb_odds + 1) * 2
    return lane_ordinality


def convert_python_id_to_lane_ordinality_right(python_id, nb_lanes):
    """

    :param python_id:
    :param nb_lanes:
    :return:

    TEST:
        >> test_convert_python_id_to_lane_ordinality()
         [[1], [2, 1], [2, 1, 3], [4, 2, 1, 3], [4, 2, 1, 3, 5]]

    """
    return convert_python_id_to_lane_ordinality_left((nb_lanes - 1) - python_id, nb_lanes)


def test_convert_python_id_to_lane_ordinality(max_nb_lanes=6):
    """

    :param max_nb_lanes:
    :return:

    """
    range_nb_lanes = range(1, max_nb_lanes)
    ranges_python_id = [range(0, nb_lanes) for nb_lanes in range_nb_lanes]
    return [
        [
            convert_python_id_to_lane_ordinality(python_id, len(range_python_id))
            for python_id in range_python_id
        ]
        for range_python_id in ranges_python_id
    ]


def convert_lane_ordinality_to_python_id_left(lane_ordinality, nb_lanes):
    """

    :param nb_lanes:
    :param lane_ordinality:
    :return:

    TESTS:
     #>> test_convert_lane_ordinality_to_python_id()
     [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]]

    """
    nb_odds = count_number_odds(nb_lanes)
    if number_is_even(lane_ordinality):
        python_id = nb_odds + (lane_ordinality / 2) - 1
    else:
        python_id = nb_odds - (lane_ordinality + 1) / 2
    return python_id


def convert_lane_ordinality_to_python_id_right(lane_ordinality, nb_lanes):
    """

    :param nb_lanes:
    :param lane_ordinality:
    :return:

    TESTS:
     #>> test_convert_lane_ordinality_to_python_id()
     [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]]

    """
    nb_evens = count_number_even(nb_lanes)
    if number_is_even(lane_ordinality):
        python_id = nb_evens - lane_ordinality / 2
    else:
        python_id = nb_evens + (lane_ordinality - 1) / 2
    return python_id


def test_convert_lane_ordinality_to_python_id(max_nb_lanes=6):
    """

    :param max_nb_lanes:
    :return:

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


def convert_lane_python_id_to_lane_symuvia_id(
        python_lane_id,
        start_python_lane_id,
        nb_lanes_in_group,
        b_inverse=False
):
    """

    :param python_lane_id:
    :param nb_lanes:
    :return:

    """
    symu_lane_id = python_lane_id - start_python_lane_id
    if b_inverse:
        symu_lane_id = (nb_lanes_in_group - 1) - symu_lane_id
    symu_lane_id += 1

    return symu_lane_id


# url: http://anandology.com/python-practice-book/iterators.html
class ListLanesPythonOrderingIter(object):
    """
    Construit un iterator pour parcourir dans un ordre pythonien les indices (ordinality) de voies SG3

    """

    def __init__(self, list_lane_informations):
        """

        :param list_lane_informations:
        :return:
        """
        self.list_lanes = list_lane_informations
        self.nb_lanes = len(list_lane_informations) - 1  # -1 car indice pour cette liste [1 ... n]
        self.python_id = 0

    def __iter__(self):
        # Iterators are iterables too.
        # Adding this functions to make them so.
        return self

    def next(self):
        if self.python_id < self.nb_lanes:
            lane_ordinality = convert_python_id_to_lane_ordinality(self.python_id, self.nb_lanes)
            self.python_id += 1
            return lane_ordinality
        else:
            raise StopIteration