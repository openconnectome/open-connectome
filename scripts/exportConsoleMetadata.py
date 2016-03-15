import sys, os 
import json 
import argparse 

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
import django
from django.conf import settings
django.setup()

from nduser.models import Dataset, Project, Token, Channel
from django.forms.models import model_to_dict

class ExportProject:
  """ serializes a project, including all its tokens and channels, to JSON. Optionally serializes the dataset, too """
  
  def __init__(self, project):
    try:
      self.projectobj = Project.objects.get( project_name = project )
    except Project.DoesNotExist:
      raise

    self.datasetobj = self.projectobj.dataset 
    self.tokenobjs = Token.objects.filter( project = self.projectobj )
    self.channelobjs = Channel.objects.filter( project = self.projectobj )

  def toJSON(self):
    ret = {}
    ret['dataset'] = model_to_dict( self.datasetobj )
    ret['project'] = model_to_dict( self.projectobj )
    ret['tokens'] = []
    for token in self.tokenobjs:
      ret['tokens'].append(model_to_dict( token ))
    ret['channels'] = []
    for channel in self.channelobjs:
      ret['channels'].append(model_to_dict( channel ))
  
    return json.dumps(ret)

def main():

  parser = argparse.ArgumentParser(description='Serialize the metadata from the ndstore console to a JSON object and write it to disk.')
  parser.add_argument('project', action='store', help='Name of the project from ndstore.')
  parser.add_argument('filename', action='store', help='File to write the resulting JSON object to.')

  result = parser.parse_args() 

  e = ExportProject(result.project)
  jsonstr = e.toJSON()
  
  with open(result.filename, 'w') as f:
    f.write(jsonstr) 

if __name__ == '__main__':
  main() 
    

