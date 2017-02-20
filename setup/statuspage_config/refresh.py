# Copyright 2016 Kunal Lillaney (http://kunallillaney.github.io)
# Alex Eusman 2017
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

import pytest
import sys
sys.path.append('..')
from core.component import Component
import os

os.chdir('../../test/')
component = Component.fromName('Blosc API')
if (pytest.main(["test_blosc.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Image API')
if (pytest.main(["test_image.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Jpeg API')
if (pytest.main(["test_jpeg.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Raw API')
if (pytest.main(["test_raw.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Propagate API')
if (pytest.main(["test_propagate.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Time API')
if (pytest.main(["test_time.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Autoingest API')
if (pytest.main(["test_autoingest.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Anno IO')
if (pytest.main(["test_io.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Anno Query')
if (pytest.main(["test_query.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Annoid API')
if (pytest.main(["test_annoid.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Json Ramon')
if (pytest.main(["test_jsonann.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('HDF5 Ramon')
if (pytest.main(["test_ramon.py"])+pytest.main(["test_neuron.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Graphgen API')
if (pytest.main(["test_graphgen.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Probability API')
if (pytest.main(["test_probability.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Stats API')
if (pytest.main(["test_stats.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Info API')
if (pytest.main(["test_info.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')

component = Component.fromName('Resource Manager')
if (pytest.main(["test_resource.py"]) >= 1):
  #Partial Outage
  component.update('partial_outage')
else:
  #Operational
  component.update('operational')
