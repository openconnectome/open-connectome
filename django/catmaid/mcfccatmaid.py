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

import django
import re
import numpy as np
import cStringIO
import pylibmc
import math
from contextlib import closing

import restargs
import ocpcadb
import ocpcaproj
import ocpcarest
import mcfc

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")

class MCFCCatmaid:
  """Prefetch CATMAID tiles into MocpcacheDB"""

  def __init__(self):
    """Bind the mocpcache"""

    self.proj = None
    self.db = None
    self.token = None
    self.tilesz = 512
    self.colors = ('C','M','Y','R','G','B')
    self.channel_list = None
    # make the mocpcache connection
    self.mc = pylibmc.Client(["127.0.0.1"], binary=True,behaviors={"tcp_nodelay":True,"ketama": True})

  def __del__(self):
    pass


  def buildKey (self, res, xtile, ytile, zslice):
    return 'mcfc/{}/{}/{}/{}/{}/{}/{}'.format(self.token, ','.join(self.channel_list), ','.join(self.colors), res, xtile, ytile, zslice)

  def cacheMissXY ( self, res, xtile, ytile, zslice ):
    """On a miss. Cutout, return the image and load the cache in a background thread"""

    # figure out the cutout (limit to max image size)
    xstart = xtile*self.tilesz
    ystart = ytile*self.tilesz
    xend = min ((xtile+1)*self.tilesz,self.proj.datasetcfg.imageSize(res)[0][0])
    yend = min ((ytile+1)*self.tilesz,self.proj.datasetcfg.imageSize(res)[0][1])

    # call the mcfc interface
    imageargs = '{}/{},{}/{},{}/{},{}/'.format(res, xstart, xend, ystart, yend, zslice, zslice+1) 

    tiledata = None
    for index, channel_name in enumerate(self.channel_list):
      ch = self.proj.getChannelObj(channel_name)
      cutout = ocpcarest.cutout(imageargs, ch, self.proj, self.db)
      # initialize the tiledata by type
      if tiledata == None:
        tiledata = np.zeros((len(self.channel_list), cutout.data.shape[0], self.tilesz, self.tilesz), dtype=cutout.data.dtype)

      tiledata[index, 0, 0:((yend-1)%self.tilesz+1), 0:((xend-1)%self.tilesz+1)] = cutout.data[0, :, :]
      tiledata[index,:] = ocpcarest.window(tiledata[index,:], ch)
    
    # We have an compound array.  Now color it.
    return mcfc.mcfcPNG (tiledata.reshape((tiledata.shape[0],tiledata.shape[2],tiledata.shape[3])), self.colors)


  def cacheMissXZ ( self, res, xtile, yslice, ztile ):
    """On a miss. Cutout, return the image and load the cache in a background thread"""
  
    # figure out the cutout (limit to max image size)
    xstart = xtile * self.tilesz
    xend = min ((xtile+1) * self.tilesz, self.proj.datasetcfg.imageSize(res)[0][0])

    # z cutouts need to get rescaled
    #  we'll map to the closest pixel range and tolerate one pixel error at the boundary
    scalefactor = self.proj.datasetcfg.getScale()[res]['xz']
    zoffset = self.proj.datasetcfg.getOffset()[res][2]
    ztilestart = int((ztile*self.tilesz)/scalefactor) + zoffset
    zstart = max ( ztilestart, zoffset ) 
    ztileend = int(math.ceil(((ztile+1)*self.tilesz)/scalefactor)) + zoffset
    zend = min ( ztileend, self.proj.datasetcfg.imageSize(res)[0][2] )

    # call the mcfc interface
    imageargs = '{}/{},{}/{},{}/{},{}/'.format(res, xstart, xend, yslice, yslice+1, zstart, zend) 

    tiledata = None
    for index,channel_name in enumerate(self.channel_list):
      ch = self.proj.getChannelObj(channel_name)
      cutout = ocpcarest.cutout(imageargs, ch, self.proj, self.db)
      # initialize the tiledata by type
      if tiledata == None:
        tiledata = np.zeros((len(self.channel_list), zend-zstart, cutout.data.shape[1], self.tilesz), dtype=cutout.data.dtype)
      tiledata[index, 0:zend-zstart, 0, 0:((xend-1)%self.tilesz+1)] = cutout.data[:, 0, :]
      
    tiledata = ocpcarest.window(tiledata, ch)

    # We have an compound array.  Now color it.
    img = mcfc.mcfcPNG (tiledata.reshape((tiledata.shape[0],tiledata.shape[1],tiledata.shape[3])), self.colors)
    return img.resize ((self.tilesz,self.tilesz))

  def cacheMissYZ (self, res, xtile, ytile, ztile):
    """On a miss. Cutout, return the image and load the cache in a background thread"""

    # figure out the cutout (limit to max image size)
    ystart = ytile * self.tilesz
    yend = min((ytile+1)*self.tilesz, self.proj.datasetcfg.imageSize(res)[0][1])

    # z cutouts need to get rescaled
    #  we'll map to the closest pixel range and tolerate one pixel error at the boundary
    scalefactor = self.proj.datasetcfg.getScale()[res]['yz']
    zoffset = self.proj.datasetcfg.getOffset()[res][2]
    ztilestart = int((ztile*self.tilesz)/scalefactor) + zoffset
    zstart = max(ztilestart, zoffset) 
    ztileend = int(math.ceil(((ztile+1)*self.tilesz)/scalefactor)) + zoffset
    zend = min(ztileend, self.proj.datasetcfg.imageSize(res)[0][2])

    # call the mcfc interface
    imageargs = '{}/{},{}/{},{}/{},{}/'.format(res, xtile, xtile+1, ystart, yend, zstart, zend) 

    tiledata = None
    for index,channel_name in enumerate(self.channel_list):
      ch = self.proj.getChannelObj(channel_name)
      cutout = ocpcarest.cutout(imageargs, ch, self.proj, self.db)
      # initialize the tiledata by type
      if tiledata == None:
        tiledata = np.zeros((len(self.channel_list), ztileend-ztilestart, self.tilesz, cutout.data.shape[2]), dtype=cutout.data.dtype)

      tiledata[index, 0:zend-zstart, 0:((yend-1)%self.tilesz+1), 0] = cutout.data[:, :, 0]

    tiledata = ocpcarest.window(tiledata, ch)

    # We have an compound array. Now color it.
    img = mcfc.mcfcPNG(tiledata.reshape((tiledata.shape[0],tiledata.shape[1],tiledata.shape[2])), self.colors)
    return img.resize((self.tilesz,self.tilesz))


  def getTile ( self, webargs ):
    """Either fetch the file from mocpcache or get a mcfc image"""

    try:
      # arguments of format /token/channel/slice_type/z/x_y_res.png
      m = re.match("(\w+)/([\w+,[:\w]*]*)/(xy|yz|xz)/(\d+)/(\d+)_(\d+)_(\d+).png", webargs)
      [self.token, channels, slice_type] = [i for i in m.groups()[:3]]
      [ztile, ytile, xtile, res] = [int(i) for i in m.groups()[3:]]

      #self.channel_list, self.colors = zip(*[i.groups() for i in map(re.compile("(\w+):(\w+)").match, re.split(',', channels))])

      # check for channel_name:color and put them in the designated list
      try:
        self.channel_list, colors = zip(*re.findall("(\w+)[:]?(\w)?", channels))
        # checking for a non-empty list
        if not not filter(None, colors):
          # if it is a mixed then replace the missing ones with the existing schema
          self.colors = [ b if a is u'' else a for a,b in zip(colors, self.colors)]
      except Exception, e:
        logger.warning("Incorrect channel formst for getTile {}. {}".format(channels, e))
        raise OCPCAError("Incorrect channel format for getTile {}. {}".format(channels, e))
      
      #self.colors = [] 
    except Exception, e:
      logger.warning("Incorrect arguments for getTile {}. {}".format(webargs, e))
      raise OCPCAError("Incorrect arguments for getTile {}. {}".format(webargs, e))

    with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
      self.proj = projdb.loadToken ( self.token )

    with closing ( ocpcadb.OCPCADB(self.proj) ) as self.db:
      
      # mocpcache key
      mckey = self.buildKey(res, xtile, ytile, ztile)

      # if tile is in mocpcache, return it
      tile = self.mc.get(mckey)
      
      if tile == None:

        if slice_type == 'xy':
          img = self.cacheMissXY(res, xtile, ytile, ztile)
        elif slice_type == 'xz':
          img = self.cacheMissXZ(res, xtile, ytile, ztile)
        elif slice_type == 'yz':
          img = self.cacheMissYZ(res, xtile, ytile, ztile)
        else:
          logger.warning ("Requested illegal image plance {}. Should be xy, xz, yz.".format(slice_type))
          raise OCPCAError ("Requested illegal image plance {}. Should be xy, xz, yz.".format(slice_type))
        
        fobj = cStringIO.StringIO ( )
        img.save ( fobj, "PNG" )
        self.mc.set(mckey, fobj.getvalue())
      
      else:
        fobj = cStringIO.StringIO(tile)

      fobj.seek(0)
      return fobj
