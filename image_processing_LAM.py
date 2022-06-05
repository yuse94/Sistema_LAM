# LIBRARIES
from numpy import max, min, arctan, pi, arange, meshgrid, hstack, array, sqrt
from skimage import filters, morphology, transform, img_as_ubyte
from skimage.color import rgb2gray
from skimage.measure import label, regionprops
from warnings import simplefilter

simplefilter(action='ignore', category=FutureWarning)


# FUNCTIONS TO IMAGE PROCESSING

def scale_image(img):
    """
    :param img:
    :return img_as_ubyte(img):
    """

    if len(img[1]) > 1000 or len(img[0]) > 2000:  # Maximum image size: X, Y
        img = transform.rescale(img, 0.8, multichannel=True)
        img = scale_image(img)
    return img_as_ubyte(img)


def straighten_img(img, my_threshold):
    """
    :param img:
    :param my_threshold:
    :return straightened_img:
    """

    filtered_image = green_filter(img, my_threshold)

    img_markers = markers(filtered_image)
    reference_1, reference_2 = img_markers[0], img_markers[1]

    pos_reference = reference_2 - reference_1
    img_rotation_angle = arctan(pos_reference[0] / pos_reference[1])
    rotated_image = transform.rotate(img, img_rotation_angle * 180 / pi)

    reference_markers = [reference_1[1], reference_2[1]]
    reference_markers.sort()

    clipping_space_image = abs(reference_1[1] - reference_2[1]) / 10

    x_1 = int(round(reference_markers[0] - clipping_space_image))
    x_2 = int(round(reference_markers[1] + clipping_space_image))

    straightened_img = rotated_image[:, x_1:x_2]

    straightened_img = img_as_ubyte(straightened_img)

    return straightened_img


def img_grid(center_x, center_y, size_x, size_y, divisions_size):
    """
    :param center_x:
    :param center_y:
    :param size_x:
    :param size_y:
    :param divisions_size:
    :return mesh_x, mesh_y, x_horizontal, y_horizontal, x_vertical, y_vertical:
    """

    # The grid is built in the four quadrants of the image

    x_1 = arange(center_x, size_x, divisions_size)
    y_1 = arange(center_y, size_y, divisions_size)
    [mesh_x_1, mesh_y_1] = meshgrid(x_1, y_1)

    x_2 = arange(center_x, 0, -divisions_size)
    y_2 = arange(center_y, 0, -divisions_size)
    [mesh_x_2, mesh_y_2] = meshgrid(x_2, y_2)

    x_3 = arange(center_x, size_x, divisions_size)
    y_3 = arange(center_y, 0, -divisions_size)
    [mesh_x_3, mesh_y_3] = meshgrid(x_3, y_3)

    x_4 = arange(center_x, 0, -divisions_size)
    y_4 = arange(center_y, size_y, divisions_size)
    [mesh_x_4, mesh_y_4] = meshgrid(x_4, y_4)

    [mesh_x, mesh_y] = meshgrid(hstack((x_1, x_2, x_3, x_4)),
                                hstack((y_1, y_2, y_3, y_4)))

    x_horizontal = hstack([mesh_x_1[0, :], mesh_x_2[0, :], mesh_x_3[0, :], mesh_x_4[0, :]])
    y_horizontal = hstack([mesh_y_1[0, :], mesh_y_2[0, :], mesh_y_3[0, :], mesh_y_4[0, :]])

    x_vertical = hstack((mesh_x_1[:, 0], mesh_x_2[:, 0], mesh_x_3[:, 0], mesh_x_4[:, 0]))
    y_vertical = hstack((mesh_y_1[:, 0], mesh_y_2[:, 0], mesh_y_3[:, 0], mesh_y_4[:, 0]))

    return mesh_x, mesh_y, x_horizontal, y_horizontal, x_vertical, y_vertical


def green_filter(img, my_threshold):
    """
    :param img:
    :param my_threshold:
    :return filtered_image:
    """

    channel_green = rgb2gray(img[:, :, 1])
    gray_img = rgb2gray(img) * 255

    green_img = channel_green - gray_img

    green_img[green_img < 0] = 0

    green_img = filters.median(green_img)

    filter_threshold = round(max(green_img) * my_threshold)
    green_binary_img = green_img > filter_threshold
    filtered_image = morphology.remove_small_holes(green_binary_img)

    return filtered_image


# SEGMENTATION

def markers(binary_image):
    """
    :param binary_image:
    :return [reference_1, reference_2, centers_y, centers_x, scale_ratio]:
    """

    binary_image = label(binary_image)
    marker_regions = regionprops(binary_image)
    centers_y = []
    centers_x = []

    for i in range(0, len(marker_regions)):
        y, x = marker_regions[i].centroid
        centers_y.append(y)
        centers_x.append(x)

    marker_centers = [i for i, x in enumerate(centers_x) if x == min(centers_x)]
    reference_1 = [centers_y[marker_centers[0]], centers_x[marker_centers[0]]]
    centers_y.pop(marker_centers[0])
    centers_x.pop(marker_centers[0])

    marker_centers = [i for i, x in enumerate(centers_x) if x == max(centers_x)]
    reference_2 = [centers_y[marker_centers[0]], centers_x[marker_centers[0]]]
    centers_y.pop(marker_centers[0])
    centers_x.pop(marker_centers[0])

    reference_1 = array(reference_1)
    reference_2 = array(reference_2)
    marker_centers_y = array(centers_y)
    marker_centers_x = array(centers_x)
    scale_ratio = 100.0 / sqrt((reference_1[1] ** 2 + reference_2[1] ** 2))

    return reference_1, reference_2, marker_centers_y, marker_centers_x, scale_ratio
