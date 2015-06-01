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

""" Sample JSON format for HBP. Generates 2 samples: Basic and Complete.\
    Run with python samplejson -h for help 
"""

import json
import argparse

def ocpJson(dataset, project, channel_list):
  """Genarate OCP json object"""
  ocp_dict = {}
  ocp_dict['dataset'] = datasetDict(*dataset)
  ocp_dict['project'] = projectDict(*project)
  ocp_dict['channels'] = {}
  for channel_name, value in channel_list.iteritems():
    ocp_dict['channels'][channel_name] = channelDict(*value)

  return json.dumps(ocp_dict, sort_keys=True, indent=4)

def datasetDict(imagesize, voxelres, offset=[0,0,0], timerange=[0,0], scalinglevels=0, scaling=0):
  """Generate the dataset dictionary"""
  dataset_dict = {}
  dataset_dict['imagesize'] = imagesize
  dataset_dict['voxelres'] = voxelres
  if offset is not None:
    dataset_dict['offset'] = offset
  if timerange is not None:
    dataset_dict['timerange'] = timerange
  if scalinglevels is not None:
    dataset_dict['scalinglevels'] = scalinglevels
  if scaling is not None:
    dataset_dict['scaling'] = scaling
  return dataset_dict

def channelDict(channel_name, datatype, channel_type, data_url, file_name, exceptions=0, resolution=0, windowrange=[0,0], readonly=0):
  """Genearte the project dictionary"""
  channel_dict = {}
  channel_dict['channel_name'] = channel_name
  channel_dict['datatype'] = datatype
  channel_dict['channel_type'] = data_url
  if exceptions is not None:
    channel_dict['exceptions'] = exceptions
  if resolution is not None:
    channel_dict['resolution'] = resolution
  if windowrange is not None:
    channel_dict['windowrange'] = windowrange
  if readonly is not None:
    channel_dict['readonly'] = readonly
  channel_dict['data_url'] = data_url
  channel_dict['file_name'] = file_name
  return channel_dict

def projectDict(project_name, token_name='', public=0):
  """Genarate the project dictionary"""
  project_dict = {}
  project_dict['project_name'] = project_name
  if token_name is not None:
    project_dict['token_name'] = project_name if token_name == '' else token_name
  if public is not None:
    project_dict['public'] = public
  return project_dict

def main():

  parser = argparse.ArgumentParser(description="Test generation script for OCP JSON file. By default this will print the basic file in ocp.JSON")
  parser.add_argument('--output_file', action='store', type=str, default='ocp.JSON', help='Name of output file')
  parser.add_argument('--complete', dest='complete', action='store_true', help='Argument for detailed JSON which is not basic')
  result = parser.parse_args()

  try:
    f = open(result.output_file, 'w')

    if not result.complete:
      basic_example = (([100,100,100],[1.0,1.0,5.0],None,None,None,None), ('sample_project_1',None,None), {'sample_channel_1':('sample_channel_1', 'uint8', 'image', 'sample_data_url', 'sample_filename',None,None,None,None)})
      f.write(ocpJson(*basic_example))

    else:
      dataset = ([100,100,100],[1.0,1.0,5.0],[0,0,1],[0,100],5)
      project = ('sample_project_1',)
      channels = {'sample_channel_1':('sample_channel_1','uint8', 'image','sample_data_url', 'sample_filename',None,None,None,None), 'sample_channel_2':('sample_channel_2', 'uint16', 'time', 'sample_data_url2', 'sample_filename2',None,None,[100,500])}
      complete_example = (dataset, project, channels)
      f.write(ocpJson(*complete_example))
  except Exception, e:
    print "Error. {}".format(e)
    raise
  finally:
    f.close()

if __name__ == "__main__":
  main()
