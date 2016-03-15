import sys, os 
import json 
import argparse 

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
import django
from django.conf import settings
django.setup()

from ndtype import S3_FALSE, MYSQL

from nduser.models import Dataset, Project, Token, Channel
from django.contrib.auth.models import User

class ImportProject:
  """ Given a JSON string, deserializes, creating Projects, Datasets, Tokens, and Channels """

  def __init__(self, jsonstr, dataset=None, user=None, skipProject=False, skipToken=False, skipChannel=False):
    
    data = json.loads(jsonstr)
  
    if user is not None:
      try:
        self.user = User.objects.get(username = user)
      except User.DoesNotExist:
        raise
    else:
      try:
        userid = data['project']['user'] 
        self.user = User.objects.get(id = int(userid))
      except User.DoesNotExist:
        raise 

    # do Dataset, Project, Token, Channel to avoid foreign key problems 
    if dataset is None:
      self.datasetobj = self.importDataset(data['dataset'])
    else:
      try:
        self.datasetobj = Dataset.objects.get(dataset_name = dataset) 
      except Dataset.DoesNotExist:
        raise

    if not skipProject:
      self.projectobj = self.importProject(data['project']) 
    else:
      try:
        self.projectobj = Project.objects.get( project_name = data['project']['project_name'] )
      except Project.DoesNotExist:
        raise

    self.tokenobjs = []
    if not skipToken:
      for token in data['tokens']:
        self.tokenobjs.append( self.importToken( token ) )
    
    self.channelobjs = []
    if not skipChannel:
      for channel in data['channels']:
        self.channelobjs.append( self.importChannel( channel ) )

    # we wait until the end to save, in case we have errors 
    self._save()

  def importDataset(self, data):
    
    d = Dataset()
    d.dataset_name = data['dataset_name'] 
    d.dataset_description = data['dataset_description']
    d.user = self.user
    d.public = data['public']
    d.ximagesize = data['ximagesize']
    d.yimagesize = data['yimagesize']
    d.zimagesize = data['zimagesize']
    d.xoffset = data['xoffset']
    d.yoffset = data['yoffset']
    d.zoffset = data['zoffset']
    d.xvoxelres = data['xvoxelres']
    d.yvoxelres = data['yvoxelres']
    d.zvoxelres = data['zvoxelres']
    d.scalingoption = data['scalingoption']
    d.scalinglevels = data['scalinglevels']
    d.starttime = data['starttime']
    d.endtime = data['endtime']

    return d

  def importProject(self, data):
    
    p = Project()
    p.project_name = data['project_name']
    p.project_description = data['project_description']
    p.user = self.user
    # skip dataset for now 
    p.public = data['public']
    p.host = data['host']
    p.kvengine = data['kvengine']
    # backwards compatibility with OCP 
    if 'mdengine' in data.keys():
      p.mdengine = data['mdengine']
    else:
      p.mdengine = MYSQL
    if 's3backend' in data.keys():
      p.s3backend = data['s3backend']
    else:
      p.s3backend = S3_FALSE

    if 'nd_version' in data.keys():
      p.nd_version = data['nd_version']
    else:
      p.nd_version = data['ocp_version']

    p.schema_version = data['schema_version']
    return p 

  def importToken(self, data):
    
    t = Token()
    t.token_name = data['token_name']
    t.token_description = data['token_description']
    t.user = self.user
    # skip project for now
    t.public = data['public']

    return t

  def importChannel(self, data):
    
    c = Channel()
    # skip project for now
    c.channel_name = data['channel_name']
    c.channel_description = data['channel_description']
    c.channel_type = data['channel_type']
    c.resolution = data['resolution']
    c.propagate = data['propagate']
    c.channel_datatype = data['channel_datatype']
    c.readonly = data['readonly']
    c.exceptions = data['exceptions']
    c.startwindow = data['startwindow']
    c.endwindow = data['endwindow']
    c.default = data['default']
    c.header = data['header']

    return c 

  def _save(self):
    
    # save in the correct order, setting foreign keys as we go
    # dataset first 
    self.datasetobj.save()
    self.projectobj.dataset = self.datasetobj 

    # project next 
    self.projectobj.save() 

    # tokens and channels last 
    for tokenobj in self.tokenobjs:
      tokenobj.project = self.projectobj
      tokenobj.save()

    for channelobj in self.channelobjs:
      channelobj.project = self.projectobj
      channelobj.save() 

def main():

  parser = argparse.ArgumentParser(description='Import Dataset, Project, Tokens, and Channels from a JSON serialized object. Assume the projects already exist.')
  parser.add_argument('filename', action='store', help='File to read from.')
  parser.add_argument('--dataset', action='store', help='If the dataset already exists, specify the name here.')
  parser.add_argument('--user', action='store', help='Override the given user ID with this user (enter username)')
  parser.add_argument('--skipProject', action='store_true', help='Skip creating project.')
  parser.add_argument('--skipToken', action='store_true', help='Skip creating tokens.')
  parser.add_argument('--skipChannel', action='store_true', help='Skip creating channels.')


  result = parser.parse_args() 

  with open(result.filename, 'r') as f:
    jsonstr = f.read()

  i = ImportProject(jsonstr, dataset=result.dataset, user=result.user, skipProject=result.skipProject, skipToken=result.skipToken, skipChannel=result.skipChannel)

if __name__ == '__main__':
  main() 
    

