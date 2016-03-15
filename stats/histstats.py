# Copyright 2015 NeuroData (http://neurodata.io)
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

import os
import sys 
import numpy as np 

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.conf import settings

import django
django.setup()

import logging
logger = logging.getLogger("neurodata")

class HistStats():

  def mean(self, histogram, bins):
    """ Given a histogram and the bin widths, calculate the mean for the histogram
        and return it """
    mean_upper = 0
    mean_lower = 0
    for i, binval in enumerate(histogram):
      mean_upper += binval*( (bins[i+1] + bins[i]) / 2 )
      mean_lower += binval 

    mean = mean_upper / mean_lower
    return mean

  def stddev(self, histogram, bins):
    """ Compute the standard deviation of the histogram """
    mean = self.mean(histogram, bins) 
    std_upper = 0
    std_lower = 0
    for i, binval in enumerate(histogram):
      std_upper += binval * ( ( ( (bins[i+1] + bins[i])/2 ) - mean )**2 )
      std_lower += binval

    stddev = np.sqrt(std_upper / std_lower)
    return stddev 

  def percentile(self, histogram, bins, percent):
    """ Calculate the <<percent>> percentile of the histogram """
    # handle > 100 or < 0
    if float(percent) <= 0:
      return 0
    elif float(percent) >= 100:
      return bins[-1]

    # if histogram is all 0s, return 0
    if len(np.nonzero(histogram)[0]) == 0:
      return 0

    # normalize the histogram
    hist_norm = np.zeros(histogram.shape)
    
    hist_sum = 0.0 # dividing by a float ensures we get a float for normalized histograms
    for binval in histogram:
      hist_sum += binval
    
    for i, binval in enumerate(histogram):
      hist_norm[i] = histogram[i] / hist_sum

    # compute the percentile using the normalized histogram
    bin_sum = 0.0 # the normalized histogram is floating point 
    i = 0
    pfloat = float(percent) * 0.01 
    while bin_sum < pfloat and i < hist_norm.shape[0]:
      bin_sum += hist_norm[i]
      i += 1

    if i+1 >= len(bins):
      return bins[-1]

    return bins[i+1] 

  def min(self, histogram, bins):
    for i, binval in enumerate(histogram):
      if binval > 0:
        return bins[i]
    return 0 

  def max(self, histogram, bins):
    max = 0
    for i, binval in enumerate(histogram):
      if binval > 0:
        max = bins[i] 

    return max 
