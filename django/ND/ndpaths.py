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

#
# Code to load project paths
#

import os, sys

ND_BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.." ))
ND_UTIL_PATH = os.path.join(ND_BASE_PATH, "util" )
ND_WS_PATH = os.path.join(ND_BASE_PATH, "webservices" )
ND_SPDB_PATH = os.path.join(ND_BASE_PATH, "spdb" )
# KLTODO going to rename this to nd lib? in the future
ND_STATS_PATH = os.path.join(ND_BASE_PATH, "stats" )
ND_RAMON_PATH = os.path.join(ND_BASE_PATH, "ramon" )
ND_LIB_PATH = os.path.join(ND_BASE_PATH, "ndlib" )
ND_PROJ_PATH = os.path.join(ND_BASE_PATH, "ndproj" )
ND_DJANGO_PATH = os.path.join(ND_BASE_PATH, "django" )

sys.path += [ ND_UTIL_PATH, ND_WS_PATH, ND_SPDB_PATH, ND_STATS_PATH, ND_PROJ_PATH, ND_RAMON_PATH, ND_LIB_PATH, ND_DJANGO_PATH ]
