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

from core.component import Component

#Spatial Database
component = Component()
component.name = 'Test_Blosc'
component.create()

component = Component()
component.name = 'Test_Image'
component.create()

component = Component()
component.name = 'Test_Jpeg'
component.create()

component = Component()
component.name = 'Test_Raw'
component.create()

component = Component()
component.name = 'Test_Propagate'
component.create()

component = Component()
component.name = 'Test_Time'
component.create()

component = Component()
component.name = 'Test_Autoingest'
component.create()

component = Component()
component.name = 'Test_Io' #Change to Anno IO
component.create()

component = Component()
component.name = 'Test_Query' #Change to Anno Query
component.create()

component = Component()
component.name = 'Test_Annoid'
component.create()

component = Component()
component.name = 'Test_Jsonann' #Json Ramon
component.create()

component = Component()
component.name = 'Test_Ramon' #HDF5 Ramon
component.create()

component = Component()
component.name = 'Test_Neuron' #HDF5 Ramon
component.create()

component = Component()
component.name = 'Test_Graphgen'
component.create()

component = Component()
component.name = 'Test_Probability'
component.create()

component = Component()
component.name = 'Test_Stats'
component.create()

component = Component()
component.name = 'Test_Info'
component.create()

component = Component()
component.name = 'Test_Resource' #Resource Management
component.create()
