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
sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from ndlib.ndtype import *

DEV_MODE = False

# kvengine settings
KV_ENGINE = MYSQL
# KV_ENGINE = REDIS

# mdengine settings
MD_ENGINE = MYSQL

# kvserver settings
KV_SERVER = 'localhost'

# server to check against
SITE_HOST = 'localhost/nd'
# SITE_HOST = 'localhost:8080'
