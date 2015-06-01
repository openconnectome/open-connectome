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
import json

import ocpcadb
import ocpcaproj

import logging
logger=logging.getLogger("ocp")


def projdict ( proj ):

  projdict = {}
  projdict['name'] = proj.getProjectName()
  projdict['description'] = proj.getProjectDescription()
  projdict['version'] = proj.getOCPVersion()

  # These fields are internal
  #projdict['dbname'] = proj._dbname
  #projdict['host'] = proj._dbhost
  #projdict['schemaversion'] = proj.getSchemaVersion()
  #projdict['kvengine'] = proj._kvengine
  #projdict['kvserver'] = proj._kvserver

  return projdict

def datasetdict ( dataset ):

  dsdict = {}
  dsdict['scalinglevels'] = dataset.scalinglevels
  if dataset.scalingoption == ocpcaproj.ZSLICES:
    dsdict['scaling'] = 'zslices'
  else:
    dsdict['scaling'] = 'xyz'
  dsdict['resolutions'] = dataset.resolutions
  dsdict['imagesize'] = dataset.imagesz
  dsdict['offset'] = dataset.offset
  dsdict['voxelres'] = dataset.voxelres
  dsdict['cube_dimension'] = dataset.cubedim
  # dsdict['neariso_scaledown'] = dataset.nearisoscaledown
  # Figure out neariso in new design
  dsdict['timerange'] = dataset.timerange
  dsdict['description'] = dataset.getDatasetDescription()

  return dsdict

def chandict ( channel ):
  chandict = {}
  chandict['channel_type'] = channel.getChannelType()
  chandict['datatype'] = channel.getDataType()
  chandict['exceptions'] = channel.getExceptions()
  chandict['readonly'] = channel.getReadOnly()
  chandict['resolution'] = channel.getResolution()
  chandict['propagate'] = channel.getPropagate()
  chandict['windowrange'] = channel.getWindowRange()

  return chandict

def jsonInfo ( proj ):
  """All Project Info"""

  jsonprojinfo = {}
  jsonprojinfo['dataset'] = datasetdict ( proj.datasetcfg )
  jsonprojinfo['project'] = projdict ( proj )
  jsonprojinfo['channels'] = {}
  for ch in proj.projectChannels():
    jsonprojinfo['channels'][ch.getChannelName()] = chandict ( ch ) 

  return json.dumps ( jsonprojinfo, sort_keys=True, indent=4 )


def jsonChanInfo ( proj, db ):
  """List of Channels"""

  if proj.getProjectType() in ocpcaproj.CHANNEL_PROJECTS:
    return json.dumps ( db.getChannels(), sort_keys=True, indent=4 )
  else:
    return json.dumps ({})


def publicTokens ( projdb ):
  """List of Public Tokens"""
  
  tokens = projdb.getPublic ()
  return json.dumps (tokens, sort_keys=True, indent=4)
