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


import h5py
import numpy as np

import ocpcadb
import ocpcaproj

import logging
logger=logging.getLogger("ocp")


def h5ProjInfo ( proj, h5f ):
  """Populate the HDF5 file with project attributes"""
  
  projgrp = h5f.create_group ( 'PROJECT' )
  projgrp.create_dataset("NAME", (1,), dtype=h5py.special_dtype(vlen=str), data=proj.getProjectName())
  projgrp.create_dataset("HOST", (1,), dtype=h5py.special_dtype(vlen=str), data=proj.getDBHost())
  projgrp.create_dataset("OCP_VERSION", (1,), dtype=h5py.special_dtype(vlen=str), data=proj.getOCPVersion())
  projgrp.create_dataset("SCHEMA_VERSION", (1,), dtype=h5py.special_dtype(vlen=str), data=proj.getSchemaVersion())
  #projgrp.create_dataset ( "DATAURL", (1,), dtype=h5py.special_dtype(vlen=str), data=proj._overlayserver )
  #projgrp.create_dataset ( "KNENGINE", (1,), dtype=h5py.special_dtype(vlen=str), data=proj._kvserver )
  #projgrp.create_dataset ( "KVSERVER", (1,), dtype=h5py.special_dtype(vlen=str), data=proj._kvengine )


def h5DatasetInfo ( dataset, h5f ):
  """Populate the HDF5 with db configuration information"""

  dsgrp = h5f.create_group('DATASET')
  dsgrp.create_dataset('NAME', (1,), dtype=h5py.special_dtype(vlen=str), data=dataset.getDatasetName())
  dsgrp.create_dataset('RESOLUTIONS', data=dataset.getResolutions())
  imggrp = dsgrp.create_group('IMAGE_SIZE')
  for k,v in dataset.getImageSize().iteritems():
    imggrp.create_dataset ( str(k), data=v )
  imggrp = dsgrp.create_group('OFFSET')
  for k,v in dataset.getOffset().iteritems():
    imggrp.create_dataset ( str(k), data=v )
  imggrp = dsgrp.create_group('VOXELRES')
  for k,v in dataset.getVoxelRes().iteritems():
    imggrp.create_dataset ( str(k), data=v )
  cdgrp = dsgrp.create_group('CUBE_DIMENSION')
  for k,v in dataset.getCubeDims().iteritems():
    cdgrp.create_dataset ( str(k), data=v )
  dsgrp.create_dataset("TIMERANGE", data=dataset.getTimeRange())


def h5ChannelInfo (proj, h5f):
  """Populate the HDF5 file with chanel information"""

  chgrp = h5f.create_group('CHANNELS')

  for ch in proj.projectChannels():

    changrp = chgrp.create_group(ch.getChannelName())
    changrp.create_dataset('NAME', (1,), dtype=h5py.special_dtype(vlen=str), data=ch.getChannelName())
    changrp.create_dataset("TYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=ch.getChannelType())
    changrp.create_dataset("DATATYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=ch.getDataType())
    changrp.create_dataset("RESOLUTION", (1,), dtype=np.uint8, data=ch.getResolution())
    changrp.create_dataset("READONLY", (1,), dtype=bool, data=(False if ch.getReadOnly() == ocpcaproj.READONLY_FALSE else True))
    changrp.create_dataset("EXCEPTIONS", (1,), dtype=bool, data=(False if ch.getExceptions() == ocpcaproj.EXCEPTION_FALSE else True))
    changrp.create_dataset("PROPAGATE", (1,), dtype=np.uint8, data=ch.getPropagate())
    changrp.create_dataset("DEFAULT", (1,), dtype=bool, data=ch.isDefault())
    changrp.create_dataset("WINDOWRANGE", data=ch.getWindowRange())


def h5Info ( proj, db, h5f ):
  """Wrapper for the parts"""

  h5ProjInfo ( proj, h5f )
  h5DatasetInfo ( proj.datasetcfg, h5f )
  h5ChannelInfo (proj, h5f)
