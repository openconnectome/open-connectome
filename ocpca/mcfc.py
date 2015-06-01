# Copyright 2014 Open Connectome Project (http://openconnecto.me)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
from PIL import Image

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")

def mcfcPNG (cutout, colors, enhancement=4.0):
  """False color a multichannel cutout.  Takes a 3-d array and returns a 2-d array 
     that combined all channels based on colors.  
    The inbound channels should be 8-bit, i.e. window them if need be.

    xdim, ydim: these should be the dimensions of the output image and should correspond 
      to the amount of data in the channel cutout
  """

  combined_cutout = np.zeros(cutout.shape[1:], dtype=np.uint32)

  for i in range(cutout.shape[0]):
    
    data32 = np.array (cutout[i,:], dtype=np.uint32)

    # First is Cyan
    if colors[i] == 'C':
      combined_cutout += np.left_shift(data32,8) + np.left_shift(data32,16)
    # Second is Magenta
    elif colors[i] == 'M':
      combined_cutout +=  np.left_shift(data32,16) + data32 
    # Third is Yellow
    elif colors[i] == 'Y':  
      combined_cutout +=  np.left_shift(data32,8) + data32 
    # Fourth is Red
    elif colors[i] == 'R':
      combined_cutout +=  data32 
    # Fifth is Green
    elif colors[i] == 'G':
      combined_cutout += np.left_shift(data32,8)
    # Sixth is Blue
    elif colors[i] == 'B':
      combined_cutout +=  np.left_shift(data32,16) 
    else:
      logger.warning ("Unsupported color requested: {}".format(color[i]))
      raise OCPCAError ("Unsupported color requested: {}".format(color[i]))

  # Set the alpha channel only for nonzero pixels
  combined_cutout = np.where (combined_cutout > 0, combined_cutout + 0xFF000000, 0)
  outimage = Image.frombuffer ( 'RGBA', cutout.shape[1:], combined_cutout.flatten(), 'raw', 'RGBA', 0, 1 ) 
  
  # Enhance the image
  from PIL import ImageEnhance
  enhancer = ImageEnhance.Brightness(outimage)
  outimage = enhancer.enhance(enhancement)
  
  return outimage
