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

import os
import sys
import argparse
import requests

def main():

  parser = argparse.ArgumentParser(description='Post a file as a tiff')
  parser.add_argument('baseurl', action="store" )
  parser.add_argument('token', action="store" )
  parser.add_argument('channel', action="store" )
  parser.add_argument('filename', action="store" )
  parser.add_argument('--create', action="store_true")
  parser.add_argument('--annotations', action="store_true")
  result = parser.parse_args()

  url = 'https://{}/sd/{}/{}/nii/'.format(result.baseurl, result.token, result.channel)

  if result.create:
    url = '{}create/'.format(url)
  if result.annotations:
    url = '{}annotations/'.format(url)

  print url

  try:

    requests.packages.urllib3.disable_warnings()
    response = requests.post(url, open(result.filename).read(), verify=False)
    if response.status_code == 200:
      print "Success for url {}".format(url)
    else:
      print "Error for url {}. Status {}. Message {}".format(url,response.status_code,response.text)
      response.raise_for_status()

  except Exception, e:

    raise

if __name__ == "__main__":
  main()
