# Licensed under the Apache License, Version 2.0 (the "License")
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

import MySQLdb
import h5py
import numpy as np
import math
from contextlib import closing
import os
import sys
from contextlib import closing
from django.core.exceptions import ObjectDoesNotExist

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'

from ocpuser.models import Project
from ocpuser.models import Dataset
from ocpuser.models import Token
from ocpuser.models import Channel
import annotation

# need imports to be conditional
try:
  from cassandra.cluster import Cluster
except:
   pass
try:
  import riak
except:
   pass

import ocpcaprivate
from ocpcaerror import OCPCAError

import logging
logger=logging.getLogger("ocp")

# OCP Version
# RB changes to VERSION from VERSION_NUMBER  -- it's not a number.  We'll want A.B.C.D type releases
OCP_VERSION = '0.6'
SCHEMA_VERSION = '0.6'

OCP_channeltypes = {0:'image',1:'annotation',2:'probmap',3:'timeseries'}

# channeltype groups
IMAGE_CHANNELS = [ 'image', 'probmap' ]
TIMESERIES_CHANNELS = [ 'timeseries' ]
ANNOTATION_CHANNELS = [ 'annotation' ]

# datatype groups
DTYPE_uint8 = [ 'uint8' ]
DTYPE_uint16 = [ 'uint16' ]
DTYPE_uint32 = [ 'rgb32','uint32' ]
DTYPE_uint64 = [ 'rgb64' ]
DTYPE_float32 = [ 'probability' ]
OCP_dtypetonp = {'uint8':np.uint8,'uint16':np.uint16,'uint32':np.uint32,'rgb32':np.uint32,'rgb64':np.uint64,'probability':np.float32}

# Propagated Values
PROPAGATED = 2
UNDER_PROPAGATION = 1
NOT_PROPAGATED = 0

# ReadOnly Values
READONLY_TRUE = 1
READONLY_FALSE = 0

# SCALING OPTIONS
ZSLICES = 0
ISOTROPIC = 1

# Exception Values
EXCEPTION_TRUE = 1
EXCEPTION_FALSE = 0

# Public Values
PUBLIC_TRUE = 1
PUBLIC_FALSE = 0

"""While this is not a true inheritance hierarchy from OCPCADataset->OPCPCAProject->OCPCAChannel
    modeling it as such makes it easier to call things on the channel.  It has dataset properties, etc."""

class OCPCADataset:
  """Configuration for a dataset"""

  def __init__ ( self, dataset_name ):
    """Construct a db configuration from the dataset parameters""" 
    
    try:
      self.ds = Dataset.objects.get(dataset_name = dataset_name)
    except ObjectDoesNotExist, e:
      logger.warning ( "Dataset {} does not exist. {}".format(dataset_name, e) )
      raise OCPCAError ( "Dataset {} does not exist".format(dataset_name) )

    self.resolutions = []
    self.cubedim = {}
    self.imagesz = {}
    self.offset = {}
    self.voxelres = {}
    self.scale = {}
    self.scalingoption = self.ds.scalingoption
    self.scalinglevels = self.ds.scalinglevels
    self.timerange = (self.ds.starttime, self.ds.endtime)
    # nearisotropic service for Stephan
    self.nearisoscaledown = {}

    for i in range (self.ds.scalinglevels+1):
      """Populate the dictionaries"""

      # add this level to the resolutions
      self.resolutions.append( i )

      # set the image size
      #  the scaled down image rounded up to the nearest cube
      xpixels=((self.ds.ximagesize-1)/2**i)+1
      ypixels=((self.ds.yimagesize-1)/2**i)+1
      if self.ds.scalingoption == ZSLICES:
        zpixels=self.ds.zimagesize
      else:
        zpixels=((self.ds.zimagesize-1)/2**i)+1
      self.imagesz[i] = [ xpixels, ypixels, zpixels ]

      # set the offset
      xoffseti = 0 if self.ds.xoffset==0 else ((self.ds.xoffset)/2**i)
      yoffseti = 0 if self.ds.yoffset==0 else ((self.ds.yoffset)/2**i)
      if self.ds.zoffset==0:
        zoffseti = 0
      else:
        if self.ds.scalingoption == ZSLICES:
          zoffseti = self.ds.zoffset
        else:
         zoffseti = ((self.ds.zoffset)/2**i)

      self.offset[i] = [ xoffseti, yoffseti, zoffseti ]

      # set the voxelresolution
      xvoxelresi = self.ds.xvoxelres*float(2**i)
      yvoxelresi = self.ds.yvoxelres*float(2**i)
      zvoxelresi = self.ds.zvoxelres if self.ds.scalingoption == ZSLICES else self.ds.zvoxelres*float(2**i)

      self.voxelres[i] = [ xvoxelresi, yvoxelresi, zvoxelresi ]
      self.scale[i] = { 'xy':xvoxelresi/yvoxelresi , 'yz':zvoxelresi/xvoxelresi, 'xz':zvoxelresi/yvoxelresi }

      # choose the cubedim as a function of the zscale
      #self.cubedim[i] = [128, 128, 16]
      # this may need to be changed.  
      if self.ds.scalingoption == ZSLICES:
        self.cubedim[i] = [128, 128, 16]
        if float(self.ds.zvoxelres/self.ds.xvoxelres)/(2**i) >  0.5:
          self.cubedim[i] = [128, 128, 16]
        else: 
          self.cubedim[i] = [64, 64, 64]

        # Make an exception for bock11 data -- just an inconsistency in original ingest
        if self.ds.ximagesize == 135424 and i == 5:
          self.cubedim[i] = [128, 128, 16]
      else:
        # RB what should we use as a cubedim?
        self.cubedim[i] = [128, 128, 16]

  # Accessors
  def getDatasetName(self):
    return self.ds.dataset_name
  def getResolutions(self):
    return self.resolutions
  def getPublic(self):
    return self.ds.public
  def getImageSize(self):
    return self.imagesz
  def getOffset(self):
    return self.offset
  def getScale(self):
    return self.scale
  def getVoxelRes(self):
    return self.voxelres
  def getCubeDims(self):
    return self.cubedim
  def getTimeRange(self):
    return self.timerange
  def getDatasetDescription ( self ):
    return self.ds.dataset_description

  def checkCube (self, resolution, corner, dim, timeargs):
    """Return true if the specified range of values is inside the cube"""

    [xstart, ystart, zstart ] = corner
    [tstart, tend] = timeargs

    from operator import add
    [xend, yend, zend] = map(add, corner, dim) 

    if ( ( xstart >= 0 ) and ( xstart < xend) and ( xend <= self.imagesz[resolution][0]) and\
        ( ystart >= 0 ) and ( ystart < yend) and ( yend <= self.imagesz[resolution][1]) and\
        ( zstart >= 0 ) and ( zstart < zend) and ( zend <= self.imagesz[resolution][2]) and\
        ( tstart >= self.timerange[0]) and ((tstart < tend) or tstart==0 and tend==0) and (tend <= (self.timerange[1]+1))):
      return True
    else:
      return False

  def imageSize ( self, resolution ):
    """Return the image size"""
    return  [ self.imagesz [resolution], self.timerange ]


class OCPCAProject:

  def __init__(self, token_name):

    if isinstance(token_name, str) or isinstance(token_name, unicode):
      try:
        self.tk = Token.objects.get(token_name = token_name)
        self.pr = Project.objects.get(project_name = self.tk.project_id)
        self.datasetcfg = OCPCADataset(self.pr.dataset_id)
      except ObjectDoesNotExist, e:
        logger.warning ( "Token {} does not exist. {}".format(token_name, e) )
        raise OCPCAError ( "Token {} does not exist".format(token_name) )
    elif isinstance(token_name, Project):
      # Constructor for OCPCAProject from Project Name
      try:
        self.tk = None
        self.pr = token_name
        self.datasetcfg = OCPCADataset(self.pr.dataset_id)
      except ObjectDoesNotExist, e:
        logger.warning ( "Token {} does not exist. {}".format(token_name, e) )
        raise OCPCAError ( "Token {} does not exist".format(token_name) )

  # Accessors
  def getToken ( self ):
    return self.tk.token_name
  def getDBHost ( self ):
      return self.pr.host
  def getKVEngine ( self ):
    return self.pr.kvengine
  def getKVServer ( self ):
    return self.pr.kvserver
  def getDBName ( self ):
    return self.pr.project_name
  def getProjectName ( self ):
    return self.pr.project_name
  def getProjectDescription ( self ):
    return self.pr.project_description
  def getOCPVersion ( self ):
    return self.pr.ocp_version
  def getSchemaVersion ( self ):
    return self.pr.schema_version

  def projectChannels ( self, channel_list=None ):
    """Return a generator of Channel Objects"""
    if channel_list is None:
      chs = Channel.objects.filter(project_id=self.pr)
    else:
      chs = channel_list
    for ch in chs:
      yield OCPCAChannel(self, ch.channel_name)

  def getChannelObj ( self, channel_name='default' ):
    """Returns a object for that channel"""
    if channel_name == 'default':
      channel_name = Channel.objects.get(project_id=self.pr, default=True)
    return OCPCAChannel(self, channel_name)

  # accessors for RB to fix
  def getDBUser( self ):
    return ocpcaprivate.dbuser
  def getDBPasswd( self ):
    return ocpcaprivate.dbpasswd


class OCPCAChannel:

  def __init__(self, proj, channel_name = None):
    """Constructor for a channel. It is a project and then some."""
    try:
      self.pr = proj
      self.ch = Channel.objects.get(channel_name = channel_name, project=self.pr.getProjectName())
    except ObjectDoesNotExist, e:
      logger.warning ( "Channel {} does not exist. {}".format(channel_name, e) )
      raise OCPCAError ( "Channel {} does not exist".format(channel_name) )

  def getDataType ( self ):
    return self.ch.channel_datatype
  def getChannelName ( self ):
    return self.ch.channel_name
  def getChannelType ( self ):
    return self.ch.channel_type
  def getChannelDescription ( self ):
    return self.ch.channel_description
  def getExceptions ( self ):
    return self.ch.exceptions
  def getReadOnly (self):
    return self.ch.readonly
  def getResolution (self):
    return self.ch.resolution
  def getWindowRange (self):
    return [self.ch.startwindow,self.ch.endwindow]
  def getPropagate (self):
    return self.ch.propagate
  def isDefault (self):
    return self.ch.default 

  def getIdsTable (self):
    if self.pr.getOCPVersion() == '0.0':
      return "ids"
    else:
      return "{}_ids".format(self.ch.channel_name)

  def getTable (self, resolution):
    """Return the appropriate table for the specified resolution"""
    if self.pr.getOCPVersion() == '0.0':
      return "res{}".format(resolution)
    else:
      return "{}_res{}".format(self.ch.channel_name, resolution)

  def getNearIsoTable (self, resolution):
    """Return the appropriate table for the specified resolution"""
    if self.pr.getOCPVersion() == '0.0':
      return "res{}neariso".format(resolution)
    else:
      return "{}_res{}neariso".format(self.ch.channel_name, resolution)
  
  def getIdxTable (self, resolution):
    """Return the appropriate Index table for the specified resolution"""
    if self.pr.getOCPVersion() == '0.0':
      return "idx{}".format(resolution)
    else:
      return "{}_idx{}".format(self.ch.channel_name, resolution)

  def getAnnoTable (self, anno_type):
    """Return the appropriate table for the specified type"""
    if self.pr.getOCPVersion() == '0.0':
      return "{}".format(annotation.anno_dbtables[anno_type])
    else:
      return "{}_{}".format(self.ch.channel_name, annotation.anno_dbtables[anno_type])

  def getExceptionsTable (self, resolution):
    """Return the appropiate exceptions table for the specified resolution"""
    if self.pr.getOCPVersion() == '0.0':
      return "exc{}".format(resolution)
    else:
      return "{}_exc{}".format(self.ch.channel_name, resolution)

  def setPropagate (self, value):
    if value in [NOT_PROPAGATED]:
      self.ch.propagate = value
      self.setReadOnly ( READONLY_FALSE )
      self.ch.save()
    elif value in [UNDER_PROPAGATION,PROPAGATED]:
      self.ch.propagate = value
      self.setReadOnly ( READONLY_TRUE )
      self.ch.save()
    else:
      logger.error ( "Wrong Propagate Value {} for Channel {}".format( value, self.ch.channel_name ) )
      raise OCPCAError ( "Wrong Propagate Value {} for Channel {}".format( value, self.ch.channel_name ) )
  
  def setReadOnly (self, value):
    if value in [READONLY_TRUE,READONLY_FALSE]:
      self.ch.readonly = value
    else:
      logger.error ( "Wrong Readonly Value {} for Channel {}".format( value, self.channel_name ) )
      raise OCPCAError ( "Wrong Readonly Value {} for Channel {}".format( value, self.ch.channel_name ) )

  def isPropagated (self):
    if self.ch.propagate in [PROPAGATED]:
      return True
    else:
      return False

class OCPCAProjectsDB:
  """Database for the projects"""

  def __init__(self):
    """Create the database connection"""

    self.conn = MySQLdb.connect (host = ocpcaprivate.dbhost, user = ocpcaprivate.dbuser, passwd = ocpcaprivate.dbpasswd, db = ocpcaprivate.db ) 

  # for context lib closing
  def close (self):
    pass

  def newOCPCAProject ( self, project_name ):
    """Make the database for a project."""

    with closing(self.conn.cursor()) as cursor:

      try:
        # Make the database 
        sql = "CREATE DATABASE {}".format( project_name )
     
        cursor.execute ( sql )
        self.conn.commit()
      except MySQLdb.Error, e:
        logger.error ("Failed to create database for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))
        raise OCPCAError ("Failed to create database for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))


  def newOCPCAChannel ( self, project_name, channel_name ):
    """Make the tables for a channel."""
    
    pr = Project.objects.get(project_name=project_name)
    ch = Channel.objects.get(channel_name=channel_name, project_id=project_name)
    ds = Dataset.objects.get(dataset_name=pr.dataset_id)

    # Connect to the database
    with closing (MySQLdb.connect (host = pr.host, user = ocpcaprivate.dbuser, passwd = ocpcaprivate.dbpasswd, db = pr.project_name )) as conn:
      with closing(conn.cursor()) as cursor:

        try:

          if pr.kvengine == 'MySQL':

            if ch.channel_type not in ['timeseries']:

              for i in range(ds.scalinglevels+1): 
                cursor.execute ( "CREATE TABLE {}_res{} ( zindex BIGINT PRIMARY KEY, cube LONGBLOB )".format(ch.channel_name,i) )
              conn.commit()

            elif ch.channel_type == 'timeseries':

              for i in range(ds.scalinglevels+1): 
                cursor.execute ( "CREATE TABLE {}_res{} ( zindex BIGINT, timestamp INT, cube LONGBLOB, PRIMARY KEY(zindex,timestamp))".format(ch.channel_name,i) )
              conn.commit()

            else:
              assert(0) #RBTODO throw a big error

          elif pr.kvengine == 'Riak':

            #RBTODO figure out new schema for Riak
            rcli = riak.RiakClient(host=proj.getKVServer(), pb_port=8087, protocol='pbc')
            bucket = rcli.bucket_type("ocp{}".format(proj.getProjectType())).bucket(proj.getDBName())
            bucket.set_property('allow_mult',False)

          elif pr.kvengine == 'Cassandra':

            #RBTODO figure out new schema for Cassandra
            cluster = Cluster( [proj.getKVServer()] )
            try:
              session = cluster.connect()

              session.execute ("CREATE KEYSPACE {} WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }}".format(proj.getDBName()), timeout=30)
              session.execute ( "USE {}".format(proj.getDBName()) )
              session.execute ( "CREATE table cuboids ( resolution int, zidx bigint, cuboid text, PRIMARY KEY ( resolution, zidx ) )", timeout=30)
            except Exception, e:
              raise
            finally:
              cluster.shutdown()
            
          else:
            logging.error ("Unknown KV Engine requested: %s" % "RBTODO get name")
            raise OCPCAError ("Unknown KV Engine requested: %s" % "RBTODO get name")


          # tables specific to annotation projects
          if ch.channel_type == 'annotation': 

            cursor.execute("CREATE TABLE {}_ids ( id BIGINT PRIMARY KEY)".format(ch.channel_name))

            # And the RAMON objects
            cursor.execute ( "CREATE TABLE {}_annotations (annoid BIGINT PRIMARY KEY, type INT, confidence FLOAT, status INT)".format(ch.channel_name))
            cursor.execute ( "CREATE TABLE {}_seeds (annoid BIGINT PRIMARY KEY, parentid BIGINT, sourceid BIGINT, cube_location INT, positionx INT, positiony INT, positionz INT)".format(ch.channel_name))
            cursor.execute ( "CREATE TABLE {}_synapses (annoid BIGINT PRIMARY KEY, synapse_type INT, weight FLOAT)".format(ch.channel_name))
            cursor.execute ( "CREATE TABLE {}_segments (annoid BIGINT PRIMARY KEY, segmentclass INT, parentseed INT, neuron INT)".format(ch.channel_name))
            cursor.execute ( "CREATE TABLE {}_organelles (annoid BIGINT PRIMARY KEY, organelleclass INT, parentseed INT, centroidx INT, centroidy INT, centroidz INT)".format(ch.channel_name))
            cursor.execute ( "CREATE TABLE {}_kvpairs ( annoid BIGINT, kv_key VARCHAR(255), kv_value VARCHAR(20000), PRIMARY KEY ( annoid, kv_key ))".format(ch.channel_name))

            conn.commit()

            if pr.kvengine == 'MySQL':
              for i in range(ds.scalinglevels+1):
                # RB always create the exception tables.....just don't use them if they are not defined
#                if ch.exceptions:
                cursor.execute ( "CREATE TABLE {}_exc{} ( zindex BIGINT, id BIGINT, exlist LONGBLOB, PRIMARY KEY ( zindex, id))".format(ch.channel_name,i))
                cursor.execute ( "CREATE TABLE {}_idx{} ( annid BIGINT PRIMARY KEY, cube LONGBLOB )".format(ch.channel_name,i))

              conn.commit()

            elif pr.kvengine == 'Riak':
              pass

            elif pr.kvengine == 'Cassandra':

              cluster = Cluster( [pr.kvserver] )
              try:
                session = cluster.connect()
                session.execute ( "USE {}".format(pr.project_name))
                session.execute( "CREATE table exceptions ( resolution int, zidx bigint, annoid bigint, exceptions text, PRIMARY KEY ( resolution, zidx, annoid ) )", timeout=30)
                session.execute("CREATE table indexes ( resolution int, annoid bigint, cuboids text, PRIMARY KEY ( resolution, annoid ) )", timeout=30)
              except Exception, e:
                raise
              finally:
                cluster.shutdown()

        except MySQLdb.Error, e:
          logging.error ("Failed to create tables for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise OCPCAError ("Failed to create tables for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))
        except Exception, e:
          raise 


  def deleteOCPCADB (self, project_name):

    pr = Project.objects.get(project_name = project_name)

    if pr.kvengine == 'MySQL':
      # delete the database
      sql = "DROP DATABASE {}".format(pr.project_name)

      with closing(self.conn.cursor()) as cursor:
        try:
          cursor.execute(sql)
          self.conn.commit()
        except MySQLdb.Error, e:
          # Skipping the error if the database does not exist
          if e.args[0] == 1008:
            logger.warning("Database {} does not exist".format(pr.project_name))
            pass
          else:
            self.conn.rollback()
            logger.error ("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))
            raise OCPCAError ("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))


    #  try to delete the database anyway
    #  Sometimes weird crashes can get stuff out of sync

    elif pr.kvengine == 'Cassandra':

      cluster = Cluster( [pr.kvserver] )
      try:
        session = cluster.connect()
        session.execute ( "DROP KEYSPACE {}".format(pr.project_name), timeout=30 )
      finally:
        cluster.shutdown()

    elif pr.kvengine == 'Riak':

      # connect to Riak
      rcli = riak.RiakClient(host=proj.kvserver, pb_port=8087, protocol='pbc')
      bucket = rcli.bucket_type("ocp{}".format(proj.getProjectType())).bucket(proj.getDBName())

      key_list = rcli.get_keys(bucket)

      for k in key_list:
        bucket.delete(k)


  def deleteOCPCAChannel (self, proj, channel_name):
    """Delete the tables for this channel"""

    pr = OCPCAProject(proj)
    ch = OCPCAChannel(pr, channel_name)
    table_list = []

    if ch.getChannelType() in ANNOTATION_CHANNELS:
      table_list.append(ch.getIdsTable())
      for key in annotation.anno_dbtables.keys():
        table_list.append(ch.getAnnoTable(key))

    for i in pr.datasetcfg.getResolutions():
      table_list.append(ch.getTable(i))
      if ch.getChannelType() in ANNOTATION_CHANNELS:
        table_list = table_list + [ch.getIdxTable(i), ch.getExceptionsTable(i)]

    print table_list
    if pr.getKVEngine() == 'MySQL':
    
      try:
        conn = MySQLdb.connect (host = ocpcaprivate.dbhost, user = ocpcaprivate.dbuser, passwd = ocpcaprivate.dbpasswd, db = pr.getProjectName() ) 
        # delete the tables for this channel
        sql = "DROP TABLES IF EXISTS {}".format(','.join(table_list))
      
        with closing(conn.cursor()) as cursor:
          cursor.execute (sql)
          conn.commit()
      except MySQLdb.Error, e:
        # Skipping the error if the table does not exist
        if e.args[0] == 1051:
          pass
        else:
          conn.rollback()
          logger.error ("Failed to drop channel tables {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise OCPCAError ("Failed to drop channel tables {}: {}. sql={}".format(e.args[0], e.args[1], sql))
      
    elif pr.getKVEngine() == 'Cassandra':
      # KL TODO
      pass
    
    elif pr.getKVEngine() == 'Riak':
      # KL TODO
      pass

  def loadDatasetConfig ( self, dataset ):
    """Query the database for the dataset information and build a db configuration"""
    return OCPCADataset (dataset)

  def loadToken ( self, token ):
    """Query django configuration for a token to bind to a project"""
    return OCPCAProject (token)

  def getPublic ( self ):
    """ Return a list of public tokens """

    tkns = Token.objects.filter(public = PUBLIC_TRUE)
    return [t.token_name for t in tkns]
