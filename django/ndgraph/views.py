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

    # TODO UA We can make this better by actually keeping the tempfile in memory and not using writing it to disk. For this now this is fine but we have to remove this soon after we have fixed other problems in graphgen.
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
  """Build a graph based on different arguments"""

try:
    return getResponse(ndgraph.genGraphRAMON (*((webargs.replace(',','/').split('/'))[0:-1])))
except Exception as e:
    logger.warning(e)
    raise NDWSError(e)
