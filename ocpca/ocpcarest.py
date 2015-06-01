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

import StringIO
import tempfile
import numpy as np
import zlib
import h5py
import os
import cStringIO
import csv
import re
import json
from PIL import Image
import MySQLdb
import itertools
from contextlib import closing

import restargs
import anncube
import ocpcadb
import ocpcaproj
import ocpcachannel
import h5ann
import h5projinfo
import jsonprojinfo
import annotation
import mcfc
import ocplib
import ocpcaprivate
from windowcutout import windowCutout

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")


def cutout (imageargs, ch, proj, db):
  """Build and Return a cube of data for the specified dimensions. This method is called by all of the more basic services to build the data. They then format and refine the output.
  
  :param imageargs: String of arguments passed
  :param ch: OCPCAChannel object
  :param proj: OCPCAProject object
  :param db: OCPCADB object
  """

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs(imageargs, proj.datasetcfg)
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments {} failed: {}".format(imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  filterlist = args.getFilter()
  zscaling = args.getZScaling()
  timerange = args.getTimeRange()
 
  # Perform the cutout
  if ch.getChannelType() in ocpcaproj.TIMESERIES_CHANNELS:
    cube = db.timecutout(ch, corner, dim, resolution, timerange)
  else:
    cube = db.cutout(ch, corner, dim, resolution, zscaling)

  filterCube(ch, cube, filterlist)
  return cube

def filterCube(ch, cube, filterlist=None):
  """Call Filter on a cube"""

  if ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS and filterlist is not None:
    cube.data = ocplib.filter_ctype_OMP ( cube.data, filterlist )
  elif filterlist is not None and ch.getChannelType not in ANNOTATION_CHANNELS:
    logger.warning("Filter only possible for Annotation Channels")
    raise OCPCAError("Filter only possible for Annotation Channels")

def numpyZip ( chanargs, proj, db ):
  """Return a web readable Numpy Pickle zipped"""

  try:
    # argument of format channel/service/imageargs
    m = re.match("([\w+,]+)/(\w+)/([\w+,/-]+)$", chanargs)
    [channels, service, imageargs] = [i for i in m.groups()]
  except Exception, e:
    logger.warning("Arguments not in the correct format {}. {}".format(chanargs, e))
    raise OCPCAError("Arguments not in the correct format {}. {}".format(chanargs, e))

  try: 
    channel_list = channels.split(',')
    ch = proj.getChannelObj(channel_list[0])

    channel_data = cutout( imageargs, ch, proj, db ).data
    cubedata = np.zeros ( (len(channel_list),)+channel_data.shape, dtype=channel_data.dtype )
    cubedata[0,:] = channel_data
    
    for idx,channel_name in enumerate(channel_list[1:]):
      if channel_name == '0':
        continue
      else:
        ch = proj.getChannelObj(channel_name)
        if ocpcaproj.OCP_dtypetonp[ch.getDataType()] == cubedata.dtype:
          cubedata[idx+1,:] = cutout(imageargs, ch, proj, db).data
        else:
          raise OCPCAError("The npz cutout can only contain cutouts of one single Channel Type.")

    
    # Create the compressed cube
    fileobj = cStringIO.StringIO ()
    np.save ( fileobj, cubedata )
    cdz = zlib.compress (fileobj.getvalue()) 

    # Package the object as a Web readable file handle
    fileobj = cStringIO.StringIO(cdz)
    fileobj.seek(0)
    return fileobj.read()

  except Exception,e:
    raise OCPCAError("{}".format(e))

def HDF5(chanargs, proj, db):
  """Return a web readable HDF5 file"""

  # Create an in-memory HDF5 file
  tmpfile = tempfile.NamedTemporaryFile()
  fh5out = h5py.File(tmpfile.name, driver='core', backing_store=True)

  try:
    # argument of format channel/service/imageargs
    m = re.match("([\w+,]+)/(\w+)/([\w+,/-]+)$", chanargs)
    [channels, service, imageargs] = [i for i in m.groups()]
  except Exception, e:
    logger.warning("Arguments not in the correct format {}. {}".format(chanargs, e))
    raise OCPCAError("Arguments not in the correct format {}. {}".format(chanargs, e))

  try: 
    for channel_name in channels.split(','):
      ch = proj.getChannelObj(channel_name)
      cube = cutout(imageargs, ch, proj, db)
      cube.RGBAChannel()
      changrp = fh5out.create_group( "{}".format(channel_name) )
      changrp.create_dataset("CUTOUT", tuple(cube.data.shape), cube.data.dtype, compression='gzip', data=cube.data)
      changrp.create_dataset("CHANNELTYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=ch.getChannelType())
      changrp.create_dataset("DATATYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=ch.getDataType())

  except:
    fh5out.close()
    tmpfile.close()
    raise

  fh5out.close()
  tmpfile.seek(0)
  return tmpfile.read()

def window(data, ch, window_range=None ):
  """Performs a window transformation on the cutout area"""

  if window_range is None:
    window_range = ch.getWindowRange()

  [startwindow, endwindow] = window_range

  if ch.getChannelType() in ocpcaproj.IMAGE_CHANNELS and ch.getDataType() in ocpcaproj.DTYPE_uint16:
    if (startwindow == endwindow == 0):
      return np.uint8(data * 1.0/256)
    elif endwindow!=0:
      windowCutout (data, window_range)
      return np.uint8(data)

  return data

def imgSlice(webargs, proj, db):
  """Return the cube object for any plane xy, yz, xz"""

  try:
    # argument of format channel/service/resolution/cutoutargs
    m = re.match("(\w+)/(xy|yz|xz)/(\d+)/([\d+,/]+)?(window/\d+,\d+/)?$", webargs)
    [channel, service, resolution, imageargs] = [i for i in m.groups()[:-1]]
    window_args = m.groups()[-1]
    imageargs = resolution + '/' + imageargs
  except Exception, e:
    logger.warning("Incorrect arguments for imgSlice {}. {}".format(webargs, e))
    raise OCPCAError("Incorrect arguments for imgSlice {}. {}".format(webargs, e))

  try:
    # Rewrite the imageargs to be a cutout
    if service == 'xy':
      m = re.match("(\d+/\d+,\d+/\d+,\d+/)(\d+)/(\d+)?[/]?$", imageargs)
      if m.group(3) is None:
        cutoutargs = '{}{},{}/'.format(m.group(1), m.group(2), int(m.group(2))+1) 
      else:
        cutoutargs = '{}{},{}/{},{}/'.format(m.group(1), m.group(2), int(m.group(2))+1, m.group(3), int(m.group(3))+1)

    elif service == 'xz':
      m = re.match("(\d+/\d+,\d+/)(\d+)(/\d+,\d+)/(\d+)?[/]?", imageargs)
      if m.group(4) is None:
        cutoutargs = '{}{},{}{}/'.format(m.group(1), m.group(2), int(m.group(2))+1, m.group(3)) 
      else:
        cutoutargs = '{}{},{}{}/{},{}/'.format(m.group(1), m.group(2), int(m.group(2))+1, m.group(3), m.group(4), int(m.group(4))+1) 

    elif service == 'yz':
      m = re.match("(\d+/)(\d+)(/\d+,\d+/\d+,\d+)/(\d+)?[/]?", imageargs)
      if m.group(4) is None:
        cutoutargs = '{}{},{}{}/'.format(m.group(1), m.group(2), int(m.group(2))+1, m.group(3)) 
      else:
        cutoutargs = '{}{},{}{}/{},{}/'.format(m.group(1), m.group(2), int(m.group(2))+1, m.group(3), m.group(4), int(m.group(4))+1) 
    else:
      raise "No such image plane {}".format(service)
  except Exception, e:
    logger.warning ("Illegal image arguments={}.  Error={}".format(imageargs,e))
    raise OCPCAError ("Illegal image arguments={}.  Error={}".format(imageargs,e))

  # Perform the cutout
  ch = proj.getChannelObj(channel)
  cb = cutout(cutoutargs, ch, proj, db)

  if window_args is not None:
    try:
      window_range = [int(i) for i in re.match("window/(\d+),(\d+)/", window_args).groups()]
    except:
      logger.warning ("Illegal window arguments={}.  Error={}".format(imageargs,e))
      raise OCPCAError ("Illegal window arguments={}.  Error={}".format(imageargs,e))
  else:
    window_range = None
  
  cb.data = window(cb.data, ch, window_range=window_range)
  return cb

def imgPNG(proj, webargs, cb):
  """Return a png object for any plane"""
  
  try:
    # argument of format channel/service/resolution/cutoutargs
    m = re.match("(\w+)/(xy|yz|xz)/(\d+)/([\d+,/]+)(window/\d+,\d+/)?$", webargs)
    [channel, service, resolution, imageargs] = [i for i in m.groups()[:-1]]
  except Exception, e:
    logger.warning("Incorrect arguments for imgSlice {}. {}".format(webargs, e))
    raise OCPCAError("Incorrect arguments for imgSlice {}. {}".format(webargs, e))

  if service == 'xy':
    img = cb.xyImage()
  elif service == 'yz':
    img = cb.yzImage(proj.datasetcfg.scale[int(resolution)][service])
  elif service == 'xz':
    img = cb.xzImage(proj.datasetcfg.scale[int(resolution)][service])

  fileobj = cStringIO.StringIO ( )
  img.save ( fileobj, "PNG" )
  fileobj.seek(0)
  return fileobj.read()

def imgAnno ( service, chanargs, proj, db ):
  """Return a plane fileobj.read() for a single objects"""

  [channel, service, annoidstr, imageargs] = chanargs.split('/', 3)
  ch = ocpcaproj.OCPCAChannel(proj,channel)
  annoids = [int(x) for x in annoidstr.split(',')]

  # retrieve the annotation 
  if len(annoids) == 1:
    anno = db.getAnnotation ( ch, annoids[0] )
    if anno == None:
      logger.warning("No annotation found at identifier = {}".format(annoids[0]))
      raise OCPCAError ("No annotation found at identifier = {}".format(annoids[0]))
    else:
      iscompound = True if anno.__class__ in [ annotation.AnnNeuron ] else False; 
  else:
    iscompound = False

  try:
    # Rewrite the imageargs to be a cutout
    if service == 'xy':
      m = re.match("(\d+/\d+,\d+/\d+,\d+/)(\d+)/", imageargs)
      cutoutargs = '{}{},{}/'.format(m.group(1),m.group(2),int(m.group(2))+1) 

    elif service == 'xz':
      m = re.match("(\d+/\d+,\d+/)(\d+)(/\d+,\d+)/", imageargs)
      cutoutargs = '{}{},{}{}/'.format(m.group(1),m.group(2),int(m.group(2))+1,m.group(3)) 

    elif service == 'yz':
      m = re.compile("(\d+/)(\d+)(/\d+,\d+/\d+,\d+)/", imageargs)
      cutoutargs = '{}{},{}{}/'.format(m.group(1),m.group(2),int(m.group(2))+1,m.group(3)) 
    else:
      raise "No such image plane {}".format(service)
  except Exception, e:
    logger.warning ("Illegal image arguments={}.  Error={}".format(imageargs,e))
    raise OCPCAError ("Illegal image arguments={}.  Error={}".format(imageargs,e))


  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs ( cutoutargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (cutoutrags,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if iscompound:
    # remap the ids for a neuron
    dataids = db.getChildren ( annoids[0] ) 
    cb = db.annoCutout ( ch, dataids, resolution, corner, dim, annoids[0] )
  else:
    # no remap when not a neuron
    dataids = annoids
    cb = db.annoCutout ( ch, dataids, resolution, corner, dim, None )

  # reshape to 2-d
  if service=='xy':
    img = cb.xyImage ( )
  elif service=='xz':
    img = cb.xzImage ( proj.datasetcfg.zscale[resolution] )
  elif service=='yz':
    img = cb.yzImage (  proj.datasetcfg.zscale[resolution] )

  fileobj = cStringIO.StringIO ( )
  img.save ( fileobj, "PNG" )
  fileobj.seek(0)
  return fileobj.read()

def annId ( chanargs, proj, db ):
  """Return the annotation identifier of a voxel"""

  [channel, service, imageargs] = chanargs.split('/',2)
  ch = ocpcaproj.OCPCAChannel(proj,channel)
  # Perform argument processing
  (resolution, voxel) = restargs.voxel ( imageargs, proj.datasetcfg )

  # Get the identifier
  return db.getVoxel ( ch, resolution, voxel )

def listIds ( chanargs, proj, db ):
  """Return the list of annotation identifiers in a region"""
  
  [channel, service, imageargs] = chanargs.split('/', 2)
  ch = ocpcaproj.OCPCAChannel(proj,channel)

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  
  cb = db.cutout ( ch, corner, dim, resolution )
  ids =  np.unique(cb.data)

  idstr=''.join([`id`+', ' for id in ids])
  
  idstr1 = idstr.lstrip('0,')
  return idstr1.rstrip(', ')

def selectService ( service, webargs, proj, db ):
  """Select the service and pass on the arguments to the appropiate function."""
  
  if service in ['xy','yz','xz']:
    return imgPNG(proj, webargs, imgSlice (webargs, proj, db))
  elif service == 'hdf5':
    return HDF5(webargs, proj, db)
  elif service in ['npz','zip']:
    return  numpyZip ( webargs, proj, db ) 
  elif service == 'id':
    return annId ( webargs, proj, db )
  elif service == 'ids':
    return listIds ( webargs, proj, db )
  elif service in ['xzanno', 'yzanno', 'xyanno']:
    return imgAnno ( service.strip('anno'), webargs, proj, db )
  else:
    logger.warning("An illegal Web GET service was requested {}. Args {}".format( service, args ))
    raise OCPCAError ("No such Web service: {}".format(service) )


def selectPost ( webargs, proj, db, postdata ):
  """Identify the service and pass on the arguments to the appropiate service."""

  [channel, service, postargs] = webargs.split('/', 2)

  # Create a list of channels from the comma separated argument
  channel_list = channel.split(',')

  # Process the arguments
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs ( postargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning( "REST Arguments {} failed: {}".format(postargs,e) )
    raise OCPCAError(e)

  corner = args.getCorner()
  resolution = args.getResolution()
  timerange = args.getTimeRange()
  conflictopt = restargs.conflictOption ( "" )

  # Bind the annotation database
  db.startTxn()

  tries = 0
  done = False

  while not done and tries < 5:

    try:

      if service == 'npz':

        # get the data out of the compressed blob
        rawdata = zlib.decompress ( postdata )
        fileobj = cStringIO.StringIO ( rawdata )
        voxarray = np.load ( fileobj )
        
        if voxarray.shape[0] != len(channel_list):
          logger.warning("The npz data has some missing channels")
          raise OCPCAError("The npz data has some missing channels")
      
        for idx,channel_name in enumerate(channel_list):
          ch = proj.getChannelObj(channel_name)
          #ch = ocpcaproj.OCPCAChannel(proj, channel)
  
          # Don't write to readonly channels
          if ch.getReadOnly() == ocpcaproj.READONLY_TRUE:
            logger.warning("Attempt to write to read only project {}".format(proj.getDBName()))
            raise OCPCAError("Attempt to write to read only project {}".format(proj.getDBName()))
       
          if voxarray.dtype == ocpcaproj.OCP_dtypetonp[ch.getDataType()]:
            pass
          else:
            logger.warning("Wrong datatype in POST")
            raise OCPCAError("Wrong datatype in POST")
            
          if ch.getChannelType() in ocpcaproj.IMAGE_CHANNELS:
            db.writeCuboid ( ch, corner, resolution, voxarray[idx,:] )
            entityid = 0

          elif ch.getChannelType() in ocpcaproj.TIMESERIES_CHANNELS:
            db.writeTimeCuboid(ch, corner, resolution, timerange, voxarray[idx,:])
            entityid = 0
          
          elif ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS:
            entityid = db.annotateDense(ch, corner, resolution, voxarray[idx,:], conflictopt)

      elif service == 'hdf5':
  
        # Get the HDF5 file.
        with closing (tempfile.NamedTemporaryFile ( )) as tmpfile:

          tmpfile.write ( postdata )
          tmpfile.seek(0)
          h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )
  
          for channel_name in channel_list:
            ch = proj.getChannelObj(channel_name)
            voxarray = h5f.get(ch.getChannelName())['CUTOUT'].value
            h5_datatype = h5f.get(ch.getChannelName())['DATATYPE'].value[0]
            h5_channeltype = h5f.get(ch.getChannelName())['CHANNELTYPE'].value[0]

            # Checking the datatype of the voxarray
            if ch.getDataType() != h5_datatype or voxarray.dtype != ocpcaproj.OCP_dtypetonp[ch.getDataType()]:
              logger.warning("Channel datatype {} in the HDF5 file does not match with the {} in the database.".format(h5_datatype, ch.getDataType()))
              raise OCPCAError("Channel datatype {} in the HDF5 file does not match with the {} in the database.".format(h5_datatype, ch.getDataType()))

            if ch.getChannelType() != h5_channeltype:
              logger.warning("Channel type {} in HDF5 file does not match with the {} in the database.".format(h5_channeltype, ch.getChannelType()))
              raise OCPCAError("Channel type {} in HDF5 file does not match with the {} in the database.".format(h5_channeltype, ch.getChannelType()))
          
            # Don't write to readonly channels
            if ch.getReadOnly() == ocpcaproj.READONLY_TRUE:
              logger.warning("Attempt to write to read only project {}".format(proj.getDBName()))
              raise OCPCAError("Attempt to write to read only project {}".format(proj.getDBName()))
            
            if ch.getChannelType() in ocpcaproj.IMAGE_CHANNELS: 
              db.writeCuboid (ch, corner, resolution, voxarray)
              entityid = 0

            elif ch.getChannelType() in ocpcaproj.TIMESERIES_CHANNELS:
              db.writeTimeCuboid (ch, corner, resolution, timerange, voxarray)
              entityid = 0
            
            elif ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS:
              entityid = db.annotateDense ( ch, corner, resolution, voxarray, conflictopt )
  
          h5f.flush()
          h5f.close()
      
      else:
        logger.warning("An illegal Web POST service was requested: {}. Args {}".format(service, webargs))
        raise OCPCAError("An illegal Web POST service was requested: {}. Args {}".format(service, webargs))
        
      db.commit()
      done = True

    # rollback if you catch an error
    except MySQLdb.OperationalError, e:
      logger.warning("Transaction did not complete. {}".format(e))
      tries += 1
      db.rollback()
      continue
    except MySQLdb.Error, e:
      logger.warning("POST transaction rollback. {}".format(e))
      db.rollback()
      raise
    except Exception, e:
      logger.exception("POST transaction rollback. {}".format(e))
      db.rollback()
      raise
    
  return str(entityid)


def getCutout ( webargs ):
  """Interface to the cutout service for annotations.Load the annotation project and invoke the appropriate dataset."""

  #[ token, sym, rangeargs ] = webargs.partition ('/')
  [token, webargs] = webargs.split('/', 1)
  [channel, service, chanargs] = webargs.split('/', 2)

  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    return selectService ( service, webargs, proj, db )


def putCutout ( webargs, postdata ):
  """Interface to the write cutout data. Load the annotation project and invoke the appropriate dataset"""

  [ token, rangeargs ] = webargs.split('/',1)
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    return selectPost ( rangeargs, proj, db, postdata )


################# RAMON interfaces #######################


"""An enumeration for options processing in getAnnotation"""
AR_NODATA = 0
AR_VOXELS = 1
AR_CUTOUT = 2
AR_TIGHTCUTOUT = 3
AR_BOUNDINGBOX = 4
AR_CUBOIDS = 5


def getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution=None, corner=None, dim=None ): 
  """Retrieve the annotation and put it in the HDF5 file."""

  # retrieve the annotation 
  anno = db.getAnnotation ( ch, annoid )
  if anno == None:
    logger.warning("No annotation found at identifier = %s" % (annoid))
    raise OCPCAError ("No annotation found at identifier = %s" % (annoid))

  # create the HDF5 object
  h5anno = h5ann.AnnotationtoH5 ( anno, h5f )

  # only return data for annotation types that have data
  if anno.__class__ in [ annotation.AnnSeed ] and dataoption != AR_NODATA: 
    logger.warning("No data associated with annotation type %s" % ( anno.__class__))
    raise OCPCAError ("No data associated with annotation type %s" % ( anno.__class__))

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
    dataids = db.getChildren ( ch, annoid ) 
  else:
    dataids = [anno.annid]

  # get the voxel data if requested
  if dataoption == AR_VOXELS:

  # RBTODO Need to make voxels zoom

    allvoxels = []

    # add voxels for all of the ids
    for dataid in dataids:
  
      voxlist = db.getLocations(ch, dataid, resolution) 
      if len(voxlist) != 0:
        allvoxels =  allvoxels + voxlist 

    allvoxels = [ el for el in set ( [ tuple(t) for t in allvoxels ] ) ]
    h5anno.addVoxels ( resolution,  allvoxels )

  # support list of IDs to filter cutout
  elif dataoption==AR_CUTOUT:

    # cutout the data with the and remap for neurons.
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      cb = db.annoCutout(ch, dataids,resolution,corner,dim,annoid)
    else:
      # don't need to remap single annotations
      cb = db.annoCutout(ch, dataids,resolution,corner,dim,None)

    # again an abstraction problem with corner.
    #  return the corner to cutout arguments space
    offset = proj.datasetcfg.offset[resolution]
    retcorner = [corner[0]+offset[0], corner[1]+offset[1], corner[2]+offset[2]]
    h5anno.addCutout ( resolution, retcorner, cb.data )

  elif dataoption == AR_TIGHTCUTOUT:

    # determine if it is a compound type (NEURON) and get the list of relevant segments
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      dataids = db.getChildren(ch, annoid) 
    else:
      dataids = [anno.annid]

    # get the bounding box from the index
    bbcorner, bbdim = db.getBoundingBox(ch, dataids, resolution)

    # figure out which ids are in object
    if bbcorner != None:
      if bbdim[0]*bbdim[1]*bbdim[2] >= 1024*1024*256:
        logger.warning ("Cutout region is inappropriately large.  Dimension: %s,%s,%s" % (bbdim[0],bbdim[1],bbdim[2]))
        raise OCPCAError ("Cutout region is inappropriately large.  Dimension: %s,%s,%s" % (bbdim[0],bbdim[1],bbdim[2]))

    # Call the cuboids interface to get the minimum amount of data
    if anno.__class__ == annotation.AnnNeuron:
      offsets = db.annoCubeOffsets(ch, dataids, resolution, annoid)
    else:
      offsets = db.annoCubeOffsets(ch, [annoid], resolution)

    datacuboid = None

    # get a list of indexes in XYZ space
    # for each cube in the index, add it to the data cube
    for (offset,cbdata) in offsets:
      if datacuboid == None:
        datacuboid = np.zeros ( (bbdim[2],bbdim[1],bbdim[0]), dtype=cbdata.dtype )

      datacuboid [ offset[2]-bbcorner[2]:offset[2]-bbcorner[2]+cbdata.shape[0], offset[1]-bbcorner[1]:offset[1]-bbcorner[1]+cbdata.shape[1], offset[0]-bbcorner[0]:offset[0]-bbcorner[0]+cbdata.shape[2] ]  = cbdata

    h5anno.addCutout ( resolution, bbcorner, datacuboid )

  elif dataoption==AR_BOUNDINGBOX:

    # determine if it is a compound type (NEURON) and get the list of relevant segments
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      dataids = db.getChildren(ch, annoid) 
    else:
      dataids = [anno.annid]

    bbcorner, bbdim = db.getBoundingBox(ch, dataids, resolution)
    h5anno.addBoundingBox(resolution, bbcorner, bbdim)

  # populate with a minimal list of cuboids
  elif dataoption == AR_CUBOIDS:

  #CUBOIDS don't work at zoom resolution
  
    h5anno.mkCuboidGroup(resolution)

    if anno.__class__ == annotation.AnnNeuron:
      offsets = db.annoCubeOffsets(ch, dataids, resolution, annoid)
    else:
      offsets = db.annoCubeOffsets(ch, [annoid], resolution)

    # get a list of indexes in XYZ space
    # for each cube in the index, add it to the hdf5 file
    for (offset,cbdata) in offsets:
      h5anno.addCuboid ( offset, cbdata )

def getAnnotation ( webargs ):
  """Fetch a RAMON object as HDF5 by object identifier"""

  [token, channel, otherargs] = webargs.split('/', 2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Split the URL and get the args
    ch = ocpcaproj.OCPCAChannel(proj, channel)
    option_args = otherargs.split('/', 2)

    # Make the HDF5 file
    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    h5f = h5py.File ( tmpfile.name,"w" )
 
    try: 
 
      db.startTxn ()
     
      # if the first argument is numeric.  it is an annoid
      if re.match ( '^[\d,]+$', option_args[0] ): 

        annoids = map(int, option_args[0].split(','))

        for annoid in annoids: 

          # if it's a compoun data type (NEURON) get the list of data ids
          # default is no data
          if option_args[1] == '' or option_args[1] == 'nodata':
            dataoption = AR_NODATA
            getAnnoById ( ch, annoid, h5f, proj, db, dataoption )
    
          # if you want voxels you either requested the resolution id/voxels/resolution
          #  or you get data from the default resolution
          elif option_args[1] == 'voxels':
            dataoption = AR_VOXELS

            try:
              [resstr, sym, rest] = option_args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning ( "Improperly formatted voxel arguments {}".format(option_args[2]))
              raise OCPCAError("Improperly formatted voxel arguments {}".format(option_args[2]))

            getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution )

          #  or you get data from the default resolution
          elif option_args[1] == 'cuboids':
            dataoption = AR_CUBOIDS
            try:
              [resstr, sym, rest] = option_args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning ( "Improperly formatted cuboids arguments {}".format(option_args[2]))
              raise OCPCAError("Improperly formatted cuboids arguments {}".format(option_args[2]))
    
            getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution )
    
          elif option_args[1] =='cutout':
    
            # if there are no args or only resolution, it's a tight cutout request
            if option_args[2] == '' or re.match('^\d+[\w\/]*$', option_args[2]):
              dataoption = AR_TIGHTCUTOUT
              try:
                [resstr, sym, rest] = option_args[2].partition('/')
                resolution = int(resstr) 
              except:
                logger.warning ( "Improperly formatted cutout arguments {}".format(option_args[2]))
                raise OCPCAError("Improperly formatted cutout arguments {}".format(option_args[2]))

              getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution )
    
            else:

              dataoption = AR_CUTOUT
   
              # Perform argument processing
              brargs = restargs.BrainRestArgs ();
              brargs.cutoutArgs ( option_args[2], proj.datasetcfg )
    
              # Extract the relevant values
              corner = brargs.getCorner()
              dim = brargs.getDim()
              resolution = brargs.getResolution()
    
              getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution, corner, dim )
    
          elif option_args[1] == 'boundingbox':
    
            dataoption = AR_BOUNDINGBOX
            try:
              [resstr, sym, rest] = option_args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning("Improperly formatted bounding box arguments {}".format(option_args[2]))
              raise OCPCAError("Improperly formatted bounding box arguments {}".format(option_args[2]))
        
            getAnnoById ( ch, annoid, h5f, proj, db, dataoption, resolution )
    
          else:
            logger.warning ("Fetch identifier {}. Error: no such data option {}".format( annoid, option_args[1] ))
            raise OCPCAError ("Fetch identifier {}. Error: no such data option {}".format( annoid, option_args[1] ))
    
      # the first argument is not numeric.  it is a service other than getAnnotation
      else:
        logger.warning("Get interface {} requested. Illegal or not implemented. Args: {}".format( option_args[0], webargs ))
        raise OCPCAError ("Get interface {} requested. Illegal or not implemented".format( option_args[0] ))
    
    # Close the file on a error: it won't get closed by the Web server
    except: 
      db.rollback()
      h5f.close()
      raise

    # Close the HDF5 file always
    h5f.flush()
    h5f.close()
    db.commit()
 
    # Return the HDF5 file
    tmpfile.seek(0)
    return tmpfile.read()

def getCSV ( webargs ):
  """Fetch a RAMON object as CSV.  Always includes bounding box.  No data option."""

  [ token, csvliteral, annoid, reststr ] = webargs.split ('/',3)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Make the HDF5 file
    # Create an in-memory HDF5 file
    with closing (tempfile.NamedTemporaryFile()) as tmpfile:
      h5f = h5py.File ( tmpfile.name )

      try:

        dataoption = AR_BOUNDINGBOX
        try:
          [resstr, sym, rest] = reststr.partition('/')
          resolution = int(resstr) 
        except:
          logger.warning ( "Improperly formatted cutout arguments {}".format(reststr))
          raise OCPCAError("Improperly formatted cutout arguments {}".format(reststr))
  
        getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )

        # convert the HDF5 file to csv
        csvstr = h5ann.h5toCSV ( h5f )
  
      finally:
        h5f.close()

  return csvstr 

def getAnnotations ( webargs, postdata ):
  """Get multiple annotations.  Takes an HDF5 that lists ids in the post."""

  [ token, objectsliteral, otherargs ] = webargs.split ('/',2)

  # Get the annotation database
  [ db, proj, projdb ] = loadDBProj ( token )

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )
  
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    # Read the post data HDF5 and get a list of identifiers
    tmpinfile = tempfile.NamedTemporaryFile ( )
    tmpinfile.write ( postdata )
    tmpinfile.seek(0)
    h5in = h5py.File ( tmpinfile.name )

    try:

      # IDENTIFIERS
      if not h5in.get('ANNOIDS'):
        logger.warning ("Requesting multiple annotations.  But no HDF5 \'ANNOIDS\' field specified.") 
        raise OCPCAError ("Requesting multiple annotations.  But no HDF5 \'ANNOIDS\' field specified.") 

      # GET the data out of the HDF5 file.  Never operate on the data in place.
      annoids = h5in['ANNOIDS'][:]

      # set variables to None: need them in call to getAnnoByID, but not all paths set all
      corner = None
      dim = None
      resolution = None
      dataarg = ''

      # process options
      # Split the URL and get the args
      if otherargs != '':
        ( dataarg, cutout ) = otherargs.split('/', 1)

      if dataarg =='' or dataarg == 'nodata':
        dataoption = AR_NODATA

      elif dataarg == 'voxels':
        dataoption = AR_VOXELS
        # only arg to voxels is resolution
        try:
          [resstr, sym, rest] = cutout.partition('/')
          resolution = int(resstr) 
        except:
          logger.warning ( "Improperly formatted voxel arguments {}".format(cutout))
          raise OCPCAError("Improperly formatted voxel arguments {}".format(cutout))


      elif dataarg == 'cutout':
        # if blank of just resolution then a tightcutout
        if cutout == '' or re.match('^\d+[\/]*$', cutout):
          dataoption = AR_TIGHTCUTOUT
          try:
            [resstr, sym, rest] = cutout.partition('/')
            resolution = int(resstr) 
          except:
            logger.warning ( "Improperly formatted cutout arguments {}".format(cutout))
            raise OCPCAError("Improperly formatted cutout arguments {}".format(cutout))
        else:
          dataoption = AR_CUTOUT

          # Perform argument processing
          brargs = restargs.BrainRestArgs ();
          brargs.cutoutArgs ( cutout, proj.datsetcfg )

          # Extract the relevant values
          corner = brargs.getCorner()
          dim = brargs.getDim()
          resolution = brargs.getResolution()

      # RBTODO test this interface
      elif dataarg == 'boundingbox':
        # if blank of just resolution then a tightcutout
        if cutout == '' or re.match('^\d+[\/]*$', cutout):
          dataoption = AR_BOUNDINGBOX
          try:
            [resstr, sym, rest] = cutout.partition('/')
            resolution = int(resstr) 
          except:
            logger.warning ( "Improperly formatted bounding box arguments {}".format(cutout))
            raise OCPCAError("Improperly formatted bounding box arguments {}".format(cutout))

      else:
          logger.warning ("In getAnnotations: Error: no such data option %s " % ( dataarg ))
          raise OCPCAError ("In getAnnotations: Error: no such data option %s " % ( dataarg ))

      try:

        # Make the HDF5 output file
        # Create an in-memory HDF5 file
        tmpoutfile = tempfile.NamedTemporaryFile()
        h5fout = h5py.File ( tmpoutfile.name )

        # get annotations for each identifier
        for annoid in annoids:
          # the int here is to prevent using a numpy value in an inner loop.  This is a 10x performance gain.
          getAnnoById ( int(annoid), h5fout, proj, db, dataoption, resolution, corner, dim )

      except:
        h5fout.close()
        tmpoutfile.close()

    finally:
      # close temporary file
      h5in.close()
      tmpinfile.close()

    # Transmit back the populated HDF5 file
    h5fout.flush()
    h5fout.close()
    tmpoutfile.seek(0)
    return tmpoutfile.read()

def putAnnotationAsync ( webargs, postdata ):
  """Put a RAMON object asynchrously as HDF5 by object identifier"""
  
  print "TESTING"
  import ocpdatastream

  
  #[ token, sym, optionsargs ] = webargs.partition ('/')
  #options = optionsargs.split('/')

  #import anydbm
  #import time
  #any_db = anydbm.open( ocpcaprivate.ssd_log_location+ocpcaprivate.bsd_name, 'c', 0777)

  #print "Wrting Data to SSD"

  # pattern for using contexts to close databases
  # get the project 
  #with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
  #  proj = projdb.loadToken ( token )

  # Don't write to readonly projects
  #if proj.getReadOnly()==1:
  #  logger.warning("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
  #  raise OCPCAError("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
  #(fd,filename) = tempfile.mkstemp(suffix=".hdf5", prefix=token, dir=ocpcaprivate.ssd_log_location)
  #os.close(fd)
  #try:
  #  fd = os.open(filename ,os.O_CREAT | os.O_WRONLY | os.O_NOATIME | os.O_SYNC )
  #  os.write ( fd, postdata )
  #  os.close( fd )
  #  metadata = ( token, time.time(), optionsargs )
  #  any_db[ str(filename) ] = "{}".format( metadata )
  #except Exception, e:
  #  print e
  
  #from ocpca.tasks import async

  #async.delay( filename )
  #async.apply_async(countdown=5)

  # TODO KL - celery to rewrite data
  #import h5annasync
  #h5annasync.h5Async( token, optionsargs )


def putAnnotation ( webargs, postdata ):
  """Put a RAMON object as HDF5 by object identifier"""
    
  [token, channel, optionsargs] = webargs.split('/',2)

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )
  
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    ch = ocpcaproj.OCPCAChannel(proj, channel)
    # Don't write to readonly projects
    if ch.getReadOnly() == ocpcaproj.READONLY_TRUE:
      logger.warning("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
      raise OCPCAError("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))

    # return string of id values
    retvals = [] 

    # Make a named temporary file for the HDF5
    with closing (tempfile.NamedTemporaryFile()) as tmpfile:
      tmpfile.write ( postdata )
      tmpfile.seek(0)
      h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

      # get the conflict option if it exists
      options = optionsargs.split('/')
      if 'preserve' in options:
        conflictopt = 'P'
      elif 'exception' in options:
        conflictopt = 'E'
      else:
        conflictopt = 'O'
  
      try:
  
        for k in h5f.keys():
          
          idgrp = h5f.get(k)
  
          # Convert HDF5 to annotation
          anno = h5ann.H5toAnnotation ( k, idgrp, db )
  
          # set the identifier (separate transaction)
          if not ('update' in options or 'dataonly' in options or 'reduce' in options):
            anno.setID ( ch, db )
  
          # start a transaction: get mysql out of line at a time mode
          db.startTxn ()
  
          tries = 0 
          done = False
          while not done and tries < 5:
  
            try:
  
              if anno.__class__ in [ annotation.AnnNeuron, annotation.AnnSeed ] and ( idgrp.get('VOXELS') or idgrp.get('CUTOUT')):
                logger.warning ("Cannot write to annotation type %s" % (anno.__class__))
                raise OCPCAError ("Cannot write to annotation type %s" % (anno.__class__))
  
              if 'update' in options and 'dataonly' in options:
                logger.warning ("Illegal combination of options. Cannot use udpate and dataonly together")
                raise OCPCAError ("Illegal combination of options. Cannot use udpate and dataonly together")
  
              elif not 'dataonly' in options and not 'reduce' in options:
  
                # Put into the database
                db.putAnnotation ( ch, anno, options )
  
              #  Get the resolution if it's specified
              if 'RESOLUTION' in idgrp:
                resolution = int(idgrp.get('RESOLUTION')[0])
  
              # Load the data associated with this annotation
              #  Is it voxel data?
              if 'VOXELS' in idgrp:
                voxels = np.array(idgrp.get('VOXELS'),dtype=np.uint32)
                voxels = voxels - proj.datasetcfg.offset[resolution]
              else: 
                voxels = None
  
              if voxels!=None and 'reduce' not in options:
  
                if 'preserve' in options:
                  conflictopt = 'P'
                elif 'exception' in options:
                  conflictopt = 'E'
                else:
                  conflictopt = 'O'
  
                # Check that the voxels have a conforming size:
                if voxels.shape[1] != 3:
                  logger.warning ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
                  raise OCPCAError ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
  
                exceptions = db.annotate ( ch, anno.annid, resolution, voxels, conflictopt )
  
              # Otherwise this is a shave operation
              elif voxels != None and 'reduce' in options:

  
                # Check that the voxels have a conforming size:
                if voxels.shape[1] != 3:
                  logger.warning ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
                  raise OCPCAError ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
                db.shave ( ch, anno.annid, resolution, voxels )
  
              # Is it dense data?
              if 'CUTOUT' in idgrp:
                cutout = np.array(idgrp.get('CUTOUT'),dtype=np.uint32)
              else:
                cutout = None
              if 'XYZOFFSET' in idgrp:
                h5xyzoffset = idgrp.get('XYZOFFSET')
              else:
                h5xyzoffset = None
  
              if cutout != None and h5xyzoffset != None and 'reduce' not in options:
  
                #  the zstart in datasetcfg is sometimes offset to make it aligned.
                #   Probably remove the offset is the best idea.  and align data
                #    to zero regardless of where it starts.  For now.
                offset = proj.datasetcfg.offset[resolution]
                corner = (h5xyzoffset[0]-offset[0],h5xyzoffset[1]-offset[1],h5xyzoffset[2]-offset[2])
  
                db.annotateEntityDense ( ch, anno.annid, corner, resolution, np.array(cutout), conflictopt )
  
              elif cutout != None and h5xyzoffset != None and 'reduce' in options:

                offset = proj.datasetcfg.offset[resolution]
                corner = (h5xyzoffset[0]-offset[0],h5xyzoffset[1]-offset[1],h5xyzoffset[2]-offset[2])
  
                db.shaveEntityDense ( ch, anno.annid, corner, resolution, np.array(cutout))
  
              elif cutout != None or h5xyzoffset != None:
                #TODO this is a loggable error
                pass
  
              # Is it dense data?
              if 'CUBOIDS' in idgrp:
                cuboids = h5ann.H5getCuboids(idgrp)
                for (corner, cuboiddata) in cuboids:
                  db.annotateEntityDense ( anno.annid, corner, resolution, cuboiddata, conflictopt ) 
  
              # only add the identifier if you commit
              if not 'dataonly' in options and not 'reduce' in options:
                retvals.append(anno.annid)
  
              # Here with no error is successful
              done = True
  
            # rollback if you catch an error
            except MySQLdb.OperationalError, e:
              logger.warning (" Put Anntotation: Transaction did not complete. %s" % (e))
              tries += 1
              db.rollback()
              continue
            except MySQLdb.Error, e:
              logger.warning ("Put Annotation: Put transaction rollback. %s" % (e))
              db.rollback()
              raise
            except Exception, e:
              logger.exception ("Put Annotation:Put transaction rollback. %s" % (e))
              db.rollback()
              raise
  
            # Commit if there is no error
            db.commit()
  
      finally:
        h5f.close()
  
      retstr = ','.join(map(str, retvals))
  
      # return the identifier
      return retstr
  
def queryAnnoObjects ( webargs, postdata=None ):
  """ Return a list of anno ids restricted by equality predicates.
      Equalities are alternating in field/value in the url.
  """

  [ token, channel, query ,restargs ] = webargs.split ('/', 3)

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    ch = ocpcaproj.OCPCAChannel(proj,channel)
    annoids = db.getAnnoObjects(ch, restargs.split('/'))

    # We have a cutout as well
    if postdata:

    # RB this is a brute force implementation.  This probably needs to be
    #  optimized to use several different execution strategies based on the
    #  cutout size and the number of objects.

      # Make a named temporary file for the HDF5
      with closing (tempfile.NamedTemporaryFile()) as tmpfile:

        tmpfile.write ( postdata )
        tmpfile.seek(0)
        h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

        try:
  
          offset = proj.datasetcfg.offset[resolution]
          corner = (h5f['XYZOFFSET'][0]-offset[0],h5f['XYZOFFSET'][1]-offset[1],h5f['XYZOFFSET'][2]-offset[2])
          dim = h5f['CUTOUTSIZE'][:]
          resolution = h5f['RESOLUTION'][0]
  
          if not proj.datasetcfg.checkCube( resolution, corner[0], corner[0]+dim[0], corner[1], corner[1]+dim[1], corner[2], corner[2]+dim[2] ):
            logger.warning ( "Illegal cutout corner=%s, dim=%s" % ( corner, dim))
            raise OCPCAError ( "Illegal cutout corner=%s, dim=%s" % ( corner, dim))
  
          cutout = db.cutout ( ch, corner, dim, resolution )
          annoids = np.intersect1d ( annoids, np.unique( cutout.data ))
  
        finally:
  
          h5f.close()
  
    return h5ann.PackageIDs ( annoids ) 


def deleteAnnotation ( webargs ):
  """Delete a RAMON object"""

  [ token, channel, otherargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    ch = ocpcaproj.OCPCAChannel(proj, channel)
    # Don't write to readonly projects              
    if ch.getReadOnly() == ocpcaproj.READONLY_TRUE:
      logger.warning("Attempt to delete from a read only project. {}: {}".format(ch.getChannelName(),webargs))
      raise OCPCAError("Attempt to delete from a  read only project. {}: {}".format(ch.getChannelName(),webargs))

    # Split the URL and get the args
    args = otherargs.split('/', 2)

    # if the first argument is numeric.  it is an annoid
    if re.match ( '^[\d,]+$', args[0] ): 
      annoids = map(int, args[0].split(','))
    # if not..this is not a well-formed delete request
    else:
      logger.warning ("Delete did not specify a legal object identifier = %s" % args[0] )
      raise OCPCAError ("Delete did not specify a legal object identifier = %s" % args[0] )

    for annoid in annoids: 

      db.startTxn()
      tries = 0
      done = False
      while not done and tries < 5:

        try:
          db.deleteAnnotation ( ch, annoid )
          done = True
        # rollback if you catch an error
        except MySQLdb.OperationalError, e:
          logger.warning ("Transaction did not complete. %s" % (e))
          tries += 1
          db.rollback()
          continue
        except MySQLdb.Error, e:
          logger.warning ("Put transaction rollback. %s" % (e))
          db.rollback()
          raise
        except Exception, e:
          logger.exception ("Put transaction rollback. %s" % (e))
          db.rollback()
          raise

        db.commit()


def jsonInfo ( webargs ):
  """Return project information in json format"""

  [ token, projinfoliteral, rest] = webargs.split ('/',2)

  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

    return jsonprojinfo.jsonInfo( proj )


def projInfo ( webargs ):

  [ token, projinfoliteral, rest ] = webargs.split ('/',2)

  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile ()
    h5f = h5py.File ( tmpfile.name )

    try:
      # Populate the file with project information
      h5projinfo.h5Info ( proj, db, h5f ) 
    finally:
      h5f.close()
      tmpfile.seek(0)

    return tmpfile.read()

def chanInfo ( webargs ):
  """Return information about the project's channels"""

  [ token, projinfoliteral, otherargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    import jsonprojinfo
    return jsonprojinfo.jsonChanInfo( proj, db )


def reserve ( webargs ):
  """Reserve annotation ids"""

  [token, channel, reservestr, cnt, other] = webargs.split ('/', 4)

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    ch = ocpcaproj.OCPCAChannel(proj,channel)
    if ch.getChannelType() not in ocpcaproj.ANNOTATION_CHANNELS:
      raise OCPCAError ("Illegal project type for reserve.")

    try:
      count = int(cnt)
      # perform the reservation
      firstid = db.reserve (ch, count)
      return json.dumps ( (firstid, int(cnt)) )
    except:
      raise OCPCAError ("Illegal arguments to reserve: {}".format(webargs))

def getField ( webargs ):
  """Return a single HDF5 field"""

  try:
    [token, channel, annid, verb, field, rest] = webargs.split ('/',5)
  except:
    logger.warning("Illegal getField request.  Wrong number of arguments.")
    raise OCPCAError("Illegal getField request.  Wrong number of arguments.")

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    ch = ocpcaproj.OCPCAChannel(proj, channel)
    anno = db.getAnnotation(ch, annid)

    if anno is None:
      logger.warning("No annotation found at identifier = {}".format(annoid))
      raise OCPCAError ("No annotation found at identifier = {}".format(annoid))

    return anno.getField(ch, field)

def setField ( webargs ):
  """Assign a single HDF5 field"""

  try:
    [token, channel, annid, verb, field, value, rest] = webargs.split ('/',6)
  except:
    logger.warning("Illegal getField request.  Wrong number of arguments.")
    raise OCPCAError("Illegal getField request.  Wrong number of arguments.")
    
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    ch = ocpcaproj.OCPCAChannel(proj, channel)
    db.updateAnnotation(ch, annid, field, value)

def getPropagate (webargs):
  """ Return the value of the Propagate field """
  
  # input in the format token/channel_list/getPropagate/
  try:
    (token, channel_list) = re.match("(\w+)/([\w+,]+)/getPropagate/$", webargs).groups()
  except Exception, e:
    logger.warning("Illegal getPropagate request. Wrong format {}. {}".format(webargs,e))
    raise OCPCAError("Illegal getPropagate request. Wrong format {}. {}".format(webargs, e))

  # pattern for using contexts to close databases
  with closing(ocpcaproj.OCPCAProjectsDB()) as projdb:
    proj = projdb.loadToken(token)
    value_list = []
    
    for channel_name in channel_list.split(','):
      ch = proj.getChannelObj(channel_name)
      value_list.append(ch.getPropagate())

  return ','.join(str(i) for i in value_list)

def setPropagate(webargs):
  """Set the value of the propagate field"""

  # input in the format token/channel_list/setPropagate/value/
  try:
    (token, channel_list, value_list) = re.match("(\w+)/([\w+,]+)/setPropagate/([\d+,]+)/$", webargs).groups()
  except:
    logger.warning("Illegal setPropagate request. Wrong format {}. {}".format(webargs, e))
    raise OCPCAError("Illegal setPropagate request. Wrong format {}. {}".format(webargs, e))
    
  # pattern for using contexts to close databases. get the project
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken(token)
    
    for channel_name in channel_list.split(','):
      ch = proj.getChannelObj(channel_name)

      value = value_list[0]
      # If the value is to set under propagation
      if int(value) == ocpcaproj.UNDER_PROPAGATION and ch.getPropagate() != ocpcaproj.UNDER_PROPAGATION:
        ch.setPropagate(ocpcaproj.UNDER_PROPAGATION)
        #from ocpca.tasks import propagate
        import ocpcastack
        ocpcastack.buildStack(token, channel_name)
        #propagate.delay ( token )
      elif int(value) == ocpcaproj.NOT_PROPAGATED:
        if ch.getPropagate() == ocpcaproj.UNDER_PROPAGATION:
          logger.warning("Cannot set this value. Project is under propagation.")
          raise OCPCAError("Cannot set this value. Project is under propagation.")
        else:
          ch.setPropagate(ocpcaproj.NOT_PROPAGATED)
      else:
        logger.warning("Invalid Value {} for setPropagate".format(value))
        raise OCPCAError("Invalid Value {} for setPropagate".format(value))

def merge (webargs):
  """Return a single HDF5 field"""
  
  try:
    [token, service, relabelids, rest] = webargs.split ('/',3)
  except:
    logger.warning("Illegal globalMerge request.  Wrong number of arguments.")
    raise OCPCAError("Illegal globalMerber request.  Wrong number of arguments.")
  
  # get the ids from the list of ids and store it in a list vairable
  ids = relabelids.split(',')
  last_id = len(ids)-1
  ids[last_id] = ids[last_id].replace("/","")
  
  # Make ids a numpy array to speed vectorize
  ids = np.array(ids,dtype=np.uint32)
  # Validate ids . If ids do not exist raise errors

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    #Check that all ids in the id strings are valid annotation objects
    for curid in ids:
      obj = db.getAnnotation(curid)
      if obj == None:
        logger.warning("Invalid object id {} used in merge".format(curid))
        raise OCPCAError("Invalid object id used in merge")

    [mergetype,resolution] = rest.split('/',1)
    if mergetype == "global":
      if resolution != "":
        [resolution,extra] = resolution.split('/')
      else:
        resolution=proj.getResolution()
      return db.mergeGlobal(ids, mergetype, int(resolution))
    else:
      # PYTODO illegal merge (no support if not global)
      assert 0
  
def publicTokens ( self ):
  """Return a json formatted list of public tokens"""
  
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:

    import jsonprojinfo
    return jsonprojinfo.publicTokens ( projdb )

def exceptions ( webargs, ):
  """list of multiply defined voxels in a cutout"""

  [token, exceptliteral, cutoutargs] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Perform argument processing
    try:
      args = restargs.BrainRestArgs ();
      args.cutoutArgs ( cutoutargs, proj.datasetcfg )
    except restargs.RESTArgsError, e:
      logger.warning("REST Arguments %s failed: %s" % (webargs,e))
      raise OCPCAError(e)

    # Extract the relevant values
    corner = args.getCorner()
    dim = args.getDim()
    resolution = args.getResolution()

    # check to make sure it's an annotation project
    if proj.getChannelType() not in ocpcaproj.ANNOTATION_PROJECTS : 
      logger.warning("Asked for exceptions on project that is not of type ANNOTATIONS")
      raise OCPCAError("Asked for exceptions on project that is not of type ANNOTATIONS")
    elif not proj.getExceptions():
      logger.warning("Asked for exceptions on project without exceptions")
      raise OCPCAError("Asked for exceptions on project without exceptions")
      
    # Get the exceptions -- expect a rect np.array of shape x,y,z,id1,id2,...,idn where n is the longest exception list
    exceptions = db.exceptionsCutout ( corner, dim, resolution )

    # package as an HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    fh5out = h5py.File ( tmpfile.name )
  
    try:
  
      # empty HDF5 file if exceptions = None
      if exceptions == None:
        ds = fh5out.create_dataset ( "exceptions", (3,), np.uint8 )
      else:
        ds = fh5out.create_dataset ( "exceptions", tuple(exceptions.shape), exceptions.dtype, compression='gzip', data=exceptions )
  
    except:
      fh5out.close()
      raise

    fh5out.close()
    tmpfile.seek(0)
    return tmpfile.read()

def minmaxProject ( webargs ):
  """Return a minimum or maximum projection across a volume by a specified plane"""

  [ token, minormax, plane, chanstr, cutoutargs ] = webargs.split ('/', 4)

  # split the channel string
  channels = chanstr.split(",")

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    mcdata = None

    for i in range(len(channels)):

      channel_name = channels[i]

      ch = ocpcaproj.OCPCAChannel(proj,channel_name)
      cb = cutout ( cutoutargs, ch, proj, db )
      FilterCube ( cutoutargs, cb )

      # project onto the image plane
      if plane == 'xy':

        # take the min project or maxproject
        if minormax == 'maxproj':
          cbplane = np.amax (cb.data, axis=0)
        elif minormax == 'minproj':
          cbplane = np.amin (cb.data, axis=0)
        else:
          logger.error("Illegal projection requested.  Projection = {}", minormax)
          raise OCPCAError("Illegal image plane requested. Projections  = {}", minormax)

        #initiliaze the multi-color array
        if mcdata == None:
          mcdata = np.zeros((len(channels),cb.data.shape[1],cb.data.shape[2]), dtype=cb.data.dtype)

      elif plane == 'xz':

        # take the min project or maxproject
        if minormax == 'maxproj':
          cbplane = np.amax (cb.data, axis=1)
        elif minormax == 'minproj':
          cbplane = np.amin (cb.data, axis=1)
        else:
          logger.error("Illegal projection requested.  Projection = {}", minormax)
          raise OCPCAError("Illegal image plane requested. Projections  = {}", minormax)

        #initiliaze the multi-color array
        if mcdata == None:
          mcdata = np.zeros((len(channels),cb.data.shape[0],cb.data.shape[2]), dtype=cb.data.dtype)

      elif plane == 'yz':

        # take the min project or maxproject
        if minormax == 'maxproj':
          cbplane = np.amax (cb.data, axis=2)
        elif minormax == 'minproj':
          cbplane = np.amin (cb.data, axis=2)
        else:
          logger.error("Illegal projection requested.  Projection = {}", minormax)
          raise OCPCAError("Illegal image plane requested. Projections  = {}", minormax)

        #initiliaze the multi-color array
        if mcdata == None:
          mcdata = np.zeros((len(channels),cb.data.shape[0],cb.data.shape[1]), dtype=cb.data.dtype)

      else:
        logger.error("Illegal image plane requested.  Plane = {}", plane)
        raise OCPCAError("Illegal image plane requested.  Plane = {}", plane)

      # put the plane into the multi-channel array
      mcdata[i,:,:] = cbplane

  # manage the color space
  # reduction factor.  How to scale data.  16 bit->8bit, or windowed
  (startwindow,endwindow) = ch.getWindowRange()
  if ch.getDataType() == ocpcaproj.DTYPE_uint16 and ( startwindow == endwindow == 0):
    #pass
    mcdata = np.uint8(mcdata * 1.0/256)
  elif ch.getDataType() == ocpcaproj.DTYPE_uint16 and ( endwindow!=0 ):
    from windowcutout import windowCutout
    windowCutout ( mcdata, (startwindow, endwindow) )

  # We have an compound array.  Now color it.
  colors = ('C','M','Y','R','G','B')
  colors = ('R','M','Y','R','G','B')
  img =  mcfc.mcfcPNG ( mcdata, colors, 2.0 )

  fileobj = cStringIO.StringIO ( )
  img.save ( fileobj, "PNG" )

  fileobj.seek(0)
  return fileobj.read()
