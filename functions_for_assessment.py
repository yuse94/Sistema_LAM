# LIBRARIES
from numpy import angle


def anterior_angle_from_horizontal(right_point, left_point, tolerance):
    """
    :param right_point:
    :param left_point:
    :param tolerance:
    :return side_lowered, angle_points:
    """

    distance_points = left_point - right_point
    angle_points = -angle(complex(distance_points[1], distance_points[0]), deg=True)
    angle_points = round(angle_points, 2)

    if angle_points > tolerance:
        side_lowered = 'Der.'
    elif angle_points < -tolerance:
        side_lowered = 'Izq.'
    else:
        side_lowered = 'Alin.'

    return side_lowered, angle_points


def posterior_angle_from_horizontal(left_point, right_point, tolerance):
    """
    :param left_point:
    :param right_point:
    :param tolerance:
    :return side_lowered, angle_points:
    """

    distance_points = right_point - left_point
    angle_points = -angle(complex(distance_points[1], distance_points[0]), deg=True)
    angle_points = round(angle_points, 2)

    if angle_points < tolerance:
        side_lowered = 'Der.'
    elif angle_points > -tolerance:
        side_lowered = 'Izq.'
    else:
        side_lowered = 'Alin.'

    return side_lowered, angle_points


def angle_from_vertical(first_point, second_point, tolerance):
    """
    Anterior view: first point the top, second point the bottom

    Posterior view: first point the bottom, second point the top

    :param first_point:
    :param second_point:
    :param tolerance:
    :return direction, angle_points:
    """

    distance_points = first_point - second_point
    angle_points = 90 - abs(angle(complex(distance_points[1], distance_points[0]), deg=True))
    angle_points = round(angle_points, 2)

    if angle_points < -tolerance:
        direction = 'Izq.'
    elif angle_points > tolerance:
        direction = 'Der.'
    else:
        direction = 'Alin.'

    return direction, angle_points


def lateral_angle_from_vertical(top_point, bottom_point, tolerance):
    """
    :param top_point:
    :param bottom_point:
    :param tolerance:
    :return direction, angle_points:
    """

    distance_points = top_point - bottom_point
    angle_points = 90 - abs(angle(complex(distance_points[1], distance_points[0]), deg=True))
    angle_points = round(angle_points, 2)

    if angle_points < -tolerance:
        direction = 'Pos.'
    elif angle_points > tolerance:
        direction = 'Ant.'
    else:
        direction = 'Alin.'

    return direction, angle_points


def lateral_angle_from_horizontal(posterior_point, anterior_point):
    """
    :param posterior_point:
    :param anterior_point:
    :return direction, angle_points:
    """

    distance_points = posterior_point - anterior_point
    angle_points = 180 - abs(angle(complex(distance_points[1], distance_points[0]), deg=True))
    angle_points = round(angle_points, 2)

    if angle_points > 15:
        direction = 'Ant.'
    elif angle_points < 5:
        direction = 'Pos.'
    else:
        direction = 'Normal'

    return direction, angle_points


def anterior_distance_from_vertical(center_point_x, reference_point, scale, tolerance):
    """
    :param center_point_x:
    :param reference_point:
    :param scale:
    :param tolerance:
    :return direction, distance:
    """

    distance = (center_point_x[1] - reference_point[1]) * scale
    distance = round(distance, 2)

    if distance > tolerance:
        direction = 'Der.'
    elif distance < -tolerance:
        direction = 'Izq.'
    else:
        direction = 'Alin.'

    return direction, distance


def posterior_distance_from_vertical(center_point_x, reference_point, scale, tolerance):
    """
    :param center_point_x:
    :param reference_point:
    :param scale:
    :param tolerance:
    :return direction, distance:
    """

    distance = (reference_point[1] - center_point_x[1]) * scale
    distance = round(distance, 2)

    if distance > tolerance:
        direction = 'Der.'
    elif distance < -tolerance:
        direction = 'Izq.'
    else:
        direction = 'Alin.'

    return direction, distance


def lateral_distance_from_vertical(center_point_x, reference_point, scale, tolerance):
    """
    :param center_point_x:
    :param reference_point:
    :param scale:
    :param tolerance:
    :return direction, distance:
    """

    distance = (reference_point[1] - center_point_x[1]) * scale
    distance = round(distance, 2)

    if distance > tolerance:
        direction = 'Ant.'
    elif distance < -tolerance:
        direction = 'Pos.'
    else:
        direction = 'Alin.'

    return direction, distance


def anterior_rotation(first_point, second_point, tolerance):
    """
    Left side: first point the top, second point the bottom\n
    Right side: first point the bottom, second point the top

    :param first_point:
    :param second_point:
    :param tolerance:
    :return direction, angle_points:
    """

    distance_points = first_point - second_point
    angle_points = abs(angle(complex(distance_points[1], distance_points[0]), deg=True)) - 90
    angle_points = round(angle_points, 2)

    if angle_points > tolerance:
        direction = 'Rot.Ext.'
    elif angle_points < -tolerance:
        direction = 'Rot.Int.'
    else:
        direction = 'Alin.'

    return direction, angle_points


def valgu_or_varus(first_point, second_point, tolerance):
    """
    Anterior:\n
    Left side: first point the bottom, second point the top\n
    Right side: first point the top, second point the bottom

    Posterior:\n
    Left side: first point the top, second point the bottom\n
    Right side: first point the bottom, second point the top

    :param first_point:
    :param second_point:
    :param tolerance:
    :return direction, angle_points:
    """

    distance_points = first_point - second_point
    angle_points = 90 - abs(angle(complex(distance_points[1], distance_points[0]), deg=True))
    angle_points = round(angle_points, 2)

    if angle_points > tolerance:
        direction = 'Valgo'
    elif angle_points < -tolerance:
        direction = 'Varo'
    else:
        direction = 'Alin.'

    return direction, angle_points
