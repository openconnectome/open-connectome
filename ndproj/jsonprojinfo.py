#/p Copyright 2014 NeuroData (http://neurodata.io)
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

import json
import urllib2
from lxml import etree
from django.conf import settings
from ndlib.ndtype import ZSLICES
from webservices.ndwserror import NDWSError
from ndproj.nddataset import NDDataset
from ndproj.ndtoken import NDToken
import logging
logger = logging.getLogger("neurodata")


def projdict ( proj ):

  projdict = {}
  projdict['name'] = proj.project_name
  projdict['description'] = proj.project_description
  projdict['schema_version'] = proj.schema_version
  projdict['ndstore_version'] = proj.nd_version
  projdict['s3backend'] = proj.s3backend

  # These fields are internal
  #projdict['dbname'] = proj._dbname
  #projdict['host'] = proj._dbhost
  #projdict['schemaversion'] = proj.getSchemaVersion()
  #projdict['kvengine'] = proj._kvengine
  #projdict['kvserver'] = proj._kvserver

  return projdict

def datasetdict ( dataset ):

  dsdict = {}
  dsdict['name'] = dataset.dataset_name
  dsdict['scalinglevels'] = dataset.scalinglevels
  if dataset.scalingoption == ZSLICES:
    dsdict['scaling'] = 'zslices'
  else:
    dsdict['scaling'] = 'xyz'
  dsdict['resolutions'] = dataset.resolutions
  dsdict['imagesize'] = dataset.image_size
  dsdict['offset'] = dataset.offset
  dsdict['voxelres'] = dataset.voxelres
  dsdict['cube_dimension'] = dataset.cubedim
  dsdict['supercube_dimension'] = dataset.supercubedim
  # Stephan projinfo
  if dataset.scalingoption == ZSLICES:
    dsdict['neariso_scaledown'] = dataset.nearisoscaledown
    dsdict['neariso_offset'] = dataset.neariso_offset
    dsdict['neariso_voxelres'] = dataset.neariso_voxelres
    dsdict['neariso_imagesize'] = dataset.neariso_imagesz
  # Figure out neariso in new design
  dsdict['description'] = dataset.dataset_description

  return dsdict

def chandict ( channel ):
  chandict = {}
  chandict['channel_type'] = channel.channel_type
  chandict['datatype'] = channel.channel_datatype
  chandict['exceptions'] = channel.exceptions
  chandict['readonly'] = channel.readonly
  chandict['resolution'] = channel.resolution
  chandict['propagate'] = channel.propagate
  chandict['windowrange'] = channel.window_range
  chandict['description'] = channel.channel_description
  chandict['timerange'] = channel.time_range

  return chandict

def jsonInfo (proj):
  """All Project Info"""

  jsonprojinfo = {}
  jsonprojinfo['dataset'] = datasetdict ( proj.datasetcfg )
  jsonprojinfo['project'] = projdict ( proj )
  jsonprojinfo['channels'] = {}
  for ch in proj.projectChannels():
    jsonprojinfo['channels'][ch.channel_name] = chandict ( ch ) 
  
  jsonprojinfo['metadata'] = metadatadict( proj )
  return json.dumps ( jsonprojinfo, sort_keys=True, indent=4 )

def xmlInfo (token, proj):
  """All Project Info"""
  
  jsonprojinfo = {}
  jsonprojinfo['dataset'] = datasetdict ( proj.datasetcfg )
  jsonprojinfo['project'] = projdict ( proj )
  jsonprojinfo['channels'] = {}
  for ch in proj.projectChannels():
    jsonprojinfo['channels'][ch.channel_name] = chandict ( ch ) 
  jsonprojinfo['metadata'] = metadatadict( proj )
  
  root = etree.Element('Volume', InputChecksum="", host="http://neurodata.io/ocptilecache/tilecache/viking/", name=token, num_sections=str(jsonprojinfo['dataset']['imagesize'][0][2]), num_stos="0", path="http://neurodata.io/ocptilecache/tilecache/viking/")
  etree.SubElement(root, 'Scale', UnitsOfMeasure="nm", UnitsPerPixel=str(jsonprojinfo['dataset']['voxelres'][0][0]/jsonprojinfo['dataset']['voxelres'][0][1]))
  tileserver_element = etree.SubElement(root, 'OCPTileServer', CoordSpaceName="volume", host="http://neurodata.io/ocptilecache/tilecache/viking/", FilePrefix="", FilePostfix=".png", TileXDim="512", TileYDim="512", GridXdim=str(jsonprojinfo['dataset']['imagesize'][0][0]/512), GridYDim=str(jsonprojinfo['dataset']['imagesize'][0][1]/512), MaxLevel=str(jsonprojinfo['dataset']["resolutions"][-1]))
  for channel_name in jsonprojinfo['channels'].keys():
    etree.SubElement(tileserver_element, "Channel", Name=channel_name, Path=channel_name, Datatype=jsonprojinfo['channels'][channel_name]['datatype'])
  for slice_number in range(jsonprojinfo['dataset']['offset'][0][2], jsonprojinfo['dataset']['offset'][0][2]+jsonprojinfo['dataset']['imagesize'][0][2]):
    etree.SubElement(root, "Section", Number="{}".format(slice_number))
  
  return etree.tostring(root)


def metadatadict( proj ):
  """Metadata Info"""
  if settings.LIMS_SERVER_ENABLED:
    try:
      url = 'http://{}/metadata/ocp/get/{}/'.format(settings.LIMS_SERVER, proj.project_name)
      req = urllib2.Request(url)
      response = urllib2.urlopen(req, timeout=0.5)
      return json.loads(response.read())
    except urllib2.URLError, e:
      logger.error("Failed URL {}".format(url))
      return {}
  else:
    return {}


def publicTokens ( projdb ):
  """List of Public Tokens"""
    
  tokens = NDToken.public_list()
  # tokens = projdb.getPublicTokens ()
  return json.dumps (tokens, sort_keys=True, indent=4)

def publicDatasets ( projdb ):
  """List of Public Datasets"""

  datasets = NDDataset.public_list()
  # datasets = projdb.getPublicDatasets()
  return json.dumps(datasets, sort_keys=True, indent=4)
