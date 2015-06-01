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

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

base_urlpatterns = patterns('',
    url(r'^ocpca/', include('ocpca.urls')),
    url(r'^ca/', include('ocpca.urls')),
    url(r'^overlay/', include('overlay.urls')),
    url(r'^catmaid/', include('catmaid.urls')),
    url(r'^synaptogram/', include('synaptogram.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^ocpuser/', include('ocpuser.urls')),
)

urlpatterns = patterns('', 
    url('^', include(base_urlpatterns)), # maintains unprefixed URLs
    url('^ocp/', include(base_urlpatterns)),
)

