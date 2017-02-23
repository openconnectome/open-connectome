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

from statuspage.core.component import Component

#Spatial Database
component = Component()
component.name = 'Blosc API'
component.create()

component = Component()
component.name = 'Image API'
component.create()

component = Component()
component.name = 'Jpeg API'
component.create()

component = Component()
component.name = 'Raw API'
component.create()

component = Component()
component.name = 'Propagate API'
component.create()

component = Component()
component.name = 'Time API'
component.create()

component = Component()
component.name = 'Autoingest API'
component.create()

component = Component()
component.name = 'Anno IO' #Change to Anno IO
component.create()

component = Component()
component.name = 'Anno Query' #Change to Anno Query
component.create()

component = Component()
component.name = 'Annoid API'
component.create()

component = Component()
component.name = 'Json Ramon' #Json Ramon
component.create()

component = Component()
component.name = 'HDF5 Ramon' #HDF5 Ramon
component.create()

component = Component()
component.name = 'Graphgen API'
component.create()

component = Component()
component.name = 'Probability API'
component.create()

component = Component()
component.name = 'Stats API'
component.create()

component = Component()
component.name = 'Info API'
component.create()

component = Component()
component.name = 'Resource Manager' #Resource Management
component.create()
