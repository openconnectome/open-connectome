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

from django.conf.urls import url
from . import views
from swcview import SwcView

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()
urlpatterns = [
  # catmaid
  url(r'^catmaid/(?P<webargs>\w+/.*)$', views.catmaid),
  # nifti -- volumetric 3-d and 4-d
  url(r'(?P<webargs>^\w+/[\w+,/]*nii/[\w,/]*)$', views.nifti),
  # swc -- annotations file get and put
  url(r'(?P<token_name>^\w+)/(?P<channel_name>[\w+,]*)/swc/?P<ids>([\w,/]*)$', SwcView.as_view()),
  # fetch ids (with predicates)
  url(r'(?P<webargs>^\w+/\w+/query/[\w\.,/]*)$', views.queryObjects),
  # get project information
  url(r'(?P<webargs>^\w+/projinfo/[\w,/]*)$', views.projinfo),
  url(r'(?P<webargs>^\w+/info/[\w,/]*)$', views.jsoninfo),
  url(r'(?P<webargs>^\w+/volume.vikingxml)$', views.xmlinfo),
  # get public tokens 
  url(r'(?P<webargs>^public_tokens/)$', views.publictokens),
  # get public datasets 
  url(r'(?P<webargs>^public_datasets/)$', views.publicdatasets),
  # Create/Delete channel interfaces
  # url(r'(?P<webargs>^\w+/createChannel/)$', views.createChannel),
  # url(r'(?P<webargs>^\w+/deleteChannel/)$', views.deleteChannel),
  # get channel information
  #url(r'(?P<webargs>^\w+/chaninfo/[\w,/]*)$', 'chaninfo'),
  # reserve identifiers for annotation projects
  url(r'(?P<webargs>^\w+/\w+/reserve/[\w+,/]*)$', views.reserve),
  # get list of multiply labelled voxels in a cutout region
  url(r'(?P<webargs>^\w+/exceptions/[\w,/]*)$', views.exceptions),
  # multi-channel false color image
  url(r'(?P<webargs>^\w+/[\w,]+/mcfc/[\w,/-]+)$', views.mcFalseColor),
  # projection services
  url(r'(?P<webargs>^\w+/[\w,]+/(minproj|maxproj)/[\w,/-]+)$', views.minmaxProject),
  # get and put services
  url(r'(?P<webargs>^\w+/([\w+,]*/)*(xy|xz|yz|tiff|hdf5|blosc|blaze|jpeg|npz|raw|zip|diff|id|ids|xyanno|xzanno|yzanno)/[\w\.,/-]*)$', views.cutout),
  # single field interfaces
  url(r'(?P<webargs>^\w+/\w+/getField/\d+/[\w+,/]*)$', views.getField),
  url(r'(?P<webargs>^\w+/\w+/setField/\d+/[\w+,./]*)$', views.setField),
  # propagate interfaces
  url(r'(?P<webargs>^\w+/[\w+,]+/getPropagate/)$', views.getPropagate),
  url(r'(?P<webargs>^\w+/[\w+,]+/setPropagate/[\d+,]+/)$', views.setPropagate),
  # merge annotations
  url(r'(?P<webargs>^\w+/\w+/merge/[\w,/]+)$', views.merge),
  # csv metadata read
  url(r'(?P<webargs>^\w+/(csv)[\d+/]?[\w,/]*)$', views.csv),
  # RAMON JSON interfaces
  url(r'(?P<webargs>^\w+/\w+/ramon/[\w,/]*)$', views.jsonramon),
  # HDF5 interfaces
  url(r'(?P<webargs>^\w+/\w+/[\d+/]?[\w,/]*)$', views.annotation),
  # JSON interfaces
  url(r'(?P<webargs>^autoIngest/)$', views.autoIngest),
]
