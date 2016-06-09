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

from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.core.files.base import ContentFile
from wsgiref.util import FileWrapper

import os
import numpy as np
import json
import re
from contextlib import closing
import tarfile
import pdb

from django.conf import settings

from ndwserror import NDWSError
import ndproj
import spatialdb
import ndgraph

import logging
logger=logging.getLogger("neurodata")


def getResponse( filename ):

    output = tarfile.open('/tmp/GeneratedGraph.tar.gz', mode='w')
    try:
        output.add(filename)
    except Exception, e:
      logger.warning("Unable to write to tar")
      raise OCPCAError("Unable to write to tar")
    finally:
        output.close()

    wrapper = FileWrapper(file("/tmp/GeneratedGraph.tar.gz"))
    response = HttpResponse(wrapper,'application/x-gzip')
    response['Content-Length'] = 5
    response['Content-Disposition'] = 'attachment; filename="GeneratedGraph.tar.gz"'
    return response



def buildGraph (request, webargs):
  #Indicated which type of arguements to return/send
  arguementType=0
  pdb.set_trace()
  try:
    # argument of format /token/channel/Arguments
    #Tries each of the possible 3 entries
    #ndgraph/test_graph_syn/test_graph_syn/pajek/5472/6496/8712/9736/1000/1100/
    #http://127.0.0.1:8000/ocp/ndgraph/GraphAnno/synanno/


    if re.match("(\w+)/(\w+)/$", webargs) is not None:
        m = re.match("(\w+)/(\w+)/$", webargs)
        [syntoken, synchan_name] = [i for i in m.groups()]
        arguementType=1
    elif re.match("(\w+)/(\w+)/(\w+)/$", webargs) is not None:
        m = re.match("(\w+)/(\w+)/(\w+)/$", webargs)
        [syntoken, synchan_name, graphType] = [i for i in m.groups()]
        arguementType=2
    elif re.match("(\w+)/(\w+)/(\w+)/(\d+),(\d+)/(\d+),(\d+)/(\d+),(\d+)/$", webargs) is not None:
        m = re.match("(\w+)/(\w+)/(\w+)/(\d+),(\d+)/(\d+),(\d+)/(\d+),(\d+)/$", webargs)
        [syntoken, synchan_name, graphType, Xmin,Xmax,Ymin,Ymax,Zmin,Zmax] = [i for i in m.groups()]
        arguementType=3
    else:
        logger.warning("Arguments not in the correct format: /token/channel/Arguments")
        raise OCPCAError("Arguments not in the correct format: /token/channel/Arguments")


  except Exception, e:
    logger.warning("Arguments not in the correct format: /token/channel/Arguments")
    raise OCPCAError("Arguments not in the correct format: /token/channel/Arguments")

  if arguementType==1:
      return getResponse(ndgraph.genGraphRAMON (syntoken, synchan_name))
  elif arguementType==2:
      return getResponse(ndgraph.genGraphRAMON (syntoken, synchan_name, graphType))
  elif arguementType==3:
      return getResponse(ndgraph.genGraphRAMON (syntoken, synchan_name, graphType, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax))
  else:
      logger.warning("Unable to return file")
      raise NDWSError("Unable to return file")
