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

from django.conf.urls import *
from ocpuser.views import *
import django.contrib.auth

# Uncomment the next two lines to enable the admin:                        
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('ocpuser.views',
                       url(r'^profile/$', 'profile'),
                       url(r'^datasets/$', 'get_datasets'),
                       url(r'^channels/$', 'get_channels'),
                       url(r'^token/$', 'get_tokens'),
                       url(r'^alltokens/$', 'get_alltokens'),
                       url(r'^createproject/$', 'createproject'),
                       url(r'^createdataset/$', 'createdataset'),
                       url(r'^createtoken/$', 'createtoken'),
                       url(r'^updateproject/$', 'updateproject'),
                       url(r'^updatetoken/$', 'updatetoken'),
                       url(r'^updatechannel/$', 'updatechannel'),
                       url(r'^updatedataset/$', 'updatedataset'),
                       url(r'^restoreproject/$', 'restoreproject'),
                       url(r'^download/$', 'downloaddata'),
)
