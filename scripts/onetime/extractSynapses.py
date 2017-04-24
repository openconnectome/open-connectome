# Copyright 2014 NeuroData (http://neurodata.io)
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


import subprocess
import re

#for annid in [ 1, 18, 19, 2, 20, 22, 23, 24, 25, 3, 5, 42, 43, 46, 53, 54, 61, 77, 79, 80, 100, 115, 117, 118, 119, 99 ]:

for annid in [ 288899,\
  289462,\
  289467,\
  289932,\
  291363,\
  291375,\
  291466,\
  291474,\
  291543,\
  292132,\
  295808,\
  296728,\
  296913,\
  297129,\
  297716,\
  299360,\
  311963,\
  313051,\
  313559,\
  317121,\
  317748,\
  318800,\
  318828,\
  318836,\
  319020,\
  320116,\
  321830,\
  322024,\
  322749,\
  322982,\
  325175,\
  325184,\
  325271,\
  325576,\
  328128,\
  330715,\
  331212,\
  331321,\
  332549,\
  332691,\
  332780,\
  332785,\
  334173,\
  334182,\
  337723,\
  338501,\
  339563,\
  341048,\
  341340,\
  342169,\
  342863,\
  343587,\
  343611,\
  344231,\
  349359,\
  349469,\
  349606,\
  349616,\
  350160,\
  352375,\
  353208,\
  355221,\
  356303,\
  356612,\
  357666,\
  358025,\
  358128,\
  358854,\
  359513,\
  360412,\
  360454,\
  360650,\
  361489,\
  361975,\
  362728,\
  362775,\
  363898,\
  363935,\
  364086 ]:

  cmdstr = "python /Users/randal/EM-connectome/web/examples/annoread.py neurodata.io bockSynapse1 %s --voxels" % ( annid )
  p = subprocess.Popen ( cmdstr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
  print "Looking at %s" % ( annid )
  for line in p.stdout.readlines():
      if re.match ('^Voxel.*$',line):
        result = re.match('^Voxel[\D]+(\d+)$',line)
        print "Annotation ID %s: found %s voxels with --voxels" % ( annid, result.group(1) )
      retval = p.wait()
  cmdstr = "python /Users/randal/EM-connectome/web/examples/annoread.py neurodata.io bockSynapse1 %s --tightcutout" % ( annid )
  p = subprocess.Popen ( cmdstr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
  for line in p.stdout.readlines():
      if re.match ('^\d+ voxels',line):
        result = re.match ('(^\d+) voxels',line)
        print "Annotation ID %s: found %s voxels with --tightcutout" % ( annid, result.group(1) )
      retval = p.wait()


  
