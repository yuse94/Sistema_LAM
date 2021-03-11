"""
==============================
Rescale, resize, and downscale
==============================

`Rescale` operation resizes an image by a given scaling factor. The scaling
factor can either be a single floating point value, or multiple values - one
along each axis.

`Resize` serves the same purpose, but allows to specify an output image shape
instead of a scaling factor.

Note that when down-sampling an image, `resize` and `rescale` should perform
Gaussian smoothing to avoid aliasing artifacts. See the `anti_aliasing` and
`anti_aliasing_sigma` arguments to these functions.

`Downscale` serves the purpose of down-sampling an n-dimensional image by
integer factors using the local mean on the elements of each block of the size
factors given as a parameter to the function.

"""

import matplotlib.pyplot as plt
import numpy as np
from skimage import (data, io, filters, data_dir, 
                     morphology, transform, img_as_ubyte)
from skimage.transform import rescale, resize, downscale_local_mean
import os

def escalar(img):

	if (len(img[1])>1200 or len(img)>2000):
		img = transform.rescale(img, 4.0/5.0,multichannel=True)
		img = escalar(img)
	return img_as_ubyte(img)


image = io.imread("anterior.png")
image = escalar(image)

plt.imshow(image)
plt.title("Image")
plt.show()
