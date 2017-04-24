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

#RBTODO -- do under a txn

import blosc
import numpy as np
from contextlib import closing
import MySQLdb
from PIL import Image
from spdb.ndcube.cube import Cube
from spdb import spatialdb
from spdb.ndkvio.s3io import S3IO
from ndproj.ndproject import NDProject
from ndctypelib import *
from ndlib.ndtype import *
from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

"""Construct a hierarchy off of a completed database."""

def buildStack(token, channel_name, resolution=None):
  """Wrapper for the different datatypes """

  pr = NDProject.fromTokenName(token)
  ch = pr.getChannelObj(channel_name)

  try:

    # if ch.channel_type in ANNOTATION_CHANNELS and pr.kvengine == MYSQL:
      # clearStack(pr, ch, resolution)
    
    # build zslice and isotropic stack
    buildImageStack(pr, ch, resolution)
    # if zsclice stack then build neariso as well
    if pr.datasetcfg.scalingoption == ZSLICES:
      buildImageStack(pr, ch, resolution, neariso=True)
  
    # mark channel as propagated after it is done 
    ch.propagate = PROPAGATED
  
  except Exception as e:
    # import pdb; pdb.set_trace()
    # clearStack(pr, ch, resolution)
    # RB This is a a thorny issue.  anno propagate doesn't work when not PROPAGATED
    # mark it as not propagated if there is an error
    ch.propagate = NOT_PROPAGATED
  except MySQLdb.Error as e:
    # import pdb; pdb.set_trace()
    # clearStack(pr, ch, resolution)
    ch.propagate = NOT_PROPAGATED
    logger.error("Error in building image stack {}".format(token))
    raise NDWSError("Error in the building image stack {}".format(token))


def clearStack (proj, ch, res=None):
  """ Clear a ND stack for a given project """
   
  assert(0)

  with closing(spatialdb.SpatialDB(proj)) as db:
    
    # pick a resolution
    if res is None:
      res = 1
    
    high_res = proj.datasetcfg.scalinglevels
    list_of_tables = []
    sql = ""
   
    # Creating a list of all tables to clear
    if ch.channel_datatype in ANNOTATION_CHANNELS:
      list_of_tables.append(ch.getRamonTable())
    for cur_res in range(res, high_res):
      list_of_tables.append(ch.getTable(cur_res))
      # list_of_tables.append(ch.getNearIsoTable(cur_res))
      if ch.channel_datatype in ANNOTATION_CHANNELS:
        list_of_tables.append(ch.getIdxTable(cur_res))
        list_of_tables.append(ch.getExceptionsTable(cur_res))

    # Creating the sql query to execute
    for table_name in list_of_tables:
      sql += "TRUNCATE table {};".format(table_name)
    
    # Executing the query to clear the tables
    try:
      db.kvio.conn.cursor().execute(sql)
      db.kvio.conn.commit()
    except MySQLdb.Error, e:
      logger.error ("Error truncating the table. {}".format(e))
      raise
    finally:
      db.kvio.conn.cursor().close()


def buildImageStack(proj, ch, res=None, neariso=False, direct=False):
  """Build the hierarchy of images"""

  with closing(spatialdb.SpatialDB(proj)) as db:
    
    s3_io = S3IO(db)
    # pick a resolution
    if res is None:
      # resolution is absent then pick channel base resolution + 1
      res = ch.resolution + 1

    high_res = proj.datasetcfg.scalinglevels
    scaling = proj.datasetcfg.scalingoption

    for cur_res in range (res, high_res+1):
      
      # only run neariso for the tables beyond isotropic
      if neariso and proj.datasetcfg.nearisoscaledown[cur_res] == 1:
        continue

      # Get the source database sizes
      [ximagesz, yimagesz, zimagesz] = proj.datasetcfg.dataset_dim(cur_res)
      timerange = ch.time_range
      if proj.s3backend == S3_TRUE:
        [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = proj.datasetcfg.get_supercubedim(cur_res)
      else:
        [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = proj.datasetcfg.get_cubedim(cur_res)

      if scaling == ZSLICES and neariso==False:
        (xscale, yscale, zscale) = (2, 2, 1)
      elif scaling == ISOTROPIC or neariso==True:
        (xscale, yscale, zscale) = (2, 2, 2)
      else:
        logger.error("Invalid scaling option in project = {}".format(scaling))
        raise NDWSError("Invalid scaling option in project = {}".format(scaling)) 

      biggercubedim = [xsupercubedim*xscale, ysupercubedim*yscale, zsupercubedim*zscale]

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xsupercubedim + 1
      ylimit = (yimagesz-1) / ysupercubedim + 1
      if not neariso:
        zlimit = (zimagesz-1) / zsupercubedim + 1
      else:
        zlimit = (zimagesz/(2**(cur_res))-1) / zsupercubedim + 1

      # Iterating over time
      for ts in range(timerange[0], timerange[1], 1):
        # Iterating over zslice
        for z in range(zlimit):
          # Iterating over y
          for y in range(ylimit):
            # Iterating over x
            for x in range(xlimit):

              # olddata target array for the new data (z,y,x) order
              olddata = db.cutout(ch, [x*xscale*xsupercubedim, y*yscale*ysupercubedim, z*zscale*zsupercubedim ], biggercubedim, cur_res-1, [ts,ts+1], direct=direct).data
              olddata = olddata[0,:,:,:]
 
              newdata = np.zeros([zsupercubedim, ysupercubedim, xsupercubedim], dtype=ND_dtypetonp.get(ch.channel_datatype))
              
              if ch.channel_type not in ANNOTATION_CHANNELS:
              
                for sl in range(zsupercubedim):

                  if scaling == ZSLICES and neariso is False:
                    data = olddata[sl,:,:]
                  elif scaling == ISOTROPIC or neariso is True:
                    data = isotropicBuild_ctype(olddata[sl*2,:,:], olddata[sl*2+1,:,:])

                  # Convert each slice to an image
                  # 8-bit int option
                  if olddata.dtype in [np.uint8, np.int8]:
                    slimage = Image.frombuffer('L', (xsupercubedim*2, ysupercubedim*2), data.flatten(), 'raw', 'L', 0, 1)
                  # 16-bit int option
                  elif olddata.dtype in [np.uint16, np.int16]:
                    slimage = Image.frombuffer('I;16', (xsupercubedim*2,ysupercubedim*2), data.flatten(), 'raw', 'I;16', 0, 1)
                  # 32-bit float option
                  elif olddata.dtype == np.float32:
                    slimage = Image.frombuffer('F', (xsupercubedim * 2, ysupercubedim * 2), data.flatten(), 'raw', 'F', 0, 1)
                  # 32 bit RGBA data
                  elif olddata.dtype == np.uint32:
                    slimage = Image.fromarray( data, "RGBA" )

                  # Resize the image and put in the new cube array
                  if olddata.dtype != np.uint32:
                    newdata[sl, :, :] = np.asarray(slimage.resize([xsupercubedim, ysupercubedim]))
                  else:
                    tempdata = np.asarray(slimage.resize([xsupercubedim, ysupercubedim]))
                    newdata[sl,:,:] = np.left_shift(tempdata[:,:,3], 24, dtype=np.uint32) | np.left_shift(tempdata[:,:,2], 16, dtype=np.uint32) | np.left_shift(tempdata[:,:,1], 8, dtype=np.uint32) | np.uint32(tempdata[:,:,0])

                zidx = XYZMorton ([x,y,z])
                cube = Cube.CubeFactory(supercubedim, ch.channel_type, ch.channel_datatype, time_range=[ts, ts+1])
                cube.zeros()
                # copying array into cube.data
                # we have to ensure that we always insert 4D data into the database
                # we convert 4D data to 3D data since we cannot process 4D data in ctypes
                # removing this breaks caching since caching expects there to be 4D cuboids
                cube.data[0,:] = newdata
                
                # checking if the cube is empty or not
                if cube.isNotZeros():
                  if proj.s3backend == S3_TRUE:
                    s3_io.putCube(ch, ts, zidx, cur_res, blosc.pack_array(cube.data), neariso=neariso)
                  else:
                    db.putCube(ch, ts, zidx, cur_res, cube, update=True, neariso=neariso)
              
              # annotation channel
              else:
    
                try:
                  if scaling == ZSLICES and neariso==False:
                    ZSliceStackCube_ctype(olddata, newdata)
                  else:
                    IsotropicStackCube_ctype(olddata, newdata)

                  corner = [x*xsupercubedim, y*ysupercubedim, z*zsupercubedim] 
                  # add resized data to cube
                  if np.any(newdata):
                    db.annotateDense(ch, ts, corner, cur_res, newdata, 'O', neariso=neariso)

                except Exception as e:
                  print("Exception {}".format(e))
