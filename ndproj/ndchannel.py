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


from contextlib import closing
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from ndlib.ndtype import *
from nduser.models import Channel
from ndproj.ndprojdb import NDProjectsDB
from ndproj.ndobject import NDObject
from ndramon import annotation
from webservices.ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")


#RBTODO 
# interface to check time -- a la dataset checkCube?
#        ( tstart >= self._timerange[0]) and ((tstart < tend) or tstart==0 and tend==0) and (tend <= (self._timerange[1]+1))):


class NDChannel(NDObject):

  def __init__(self, ch):
    """Constructor for a channel. It is a project and then some."""
    from ndproject import NDProject
    self.ch = ch
    self.pr = NDProject.fromName(self.project_name)
    with closing (NDProjectsDB.getProjDB(self.pr)) as db:
      self.db = db

  @classmethod
  def fromName(cls, pr, channel_name):
    try:
      pr = pr
      ch = Channel.objects.get(channel_name = channel_name, project=pr.project_name)
      return cls(ch)
    except Channel.DoesNotExist as e:
      logger.error("Channel {} does not exist. {}".format(channel_name, e))
      raise Channel.DoesNotExist

  @classmethod
  def fromJson(cls, project_name, channel):
    ch = Channel(**cls.deserialize(channel))
    ch.project_id = project_name
    return cls(ch)
  
  def save(self):
    try:
      self.ch.save()
    except Exception as e:
      raise

  def create(self):
    try:
      self.save()
      self.db.newNDChannel(self.channel_name)
    except NDWSError as e:
      self.ch.delete()
      raise
    except Exception as e:
      raise

  def delete(self):
    try:
      self.db.deleteNDChannel(self.channel_name)
      self.ch.delete()
    except Exception as e:
      raise
  
  def update(self):
    try:
      self.ch.save()
    except Exception as e:
      raise
    
  def serialize(self):
    return NDObject.serialize(self.ch)
  
  @property
  def channel_id(self):
    return self.ch.id
  
  @property
  def channel_name(self):
    return self.ch.channel_name

  @channel_name.setter
  def channel_name(self, value):
    # TODO KL check for unwanted chars here
    self.ch.channel_name = value

  @property
  def channel_description(self):
    return self.ch.channel_description

  @channel_description.setter
  def channel_description(self, value):
    self.ch.channel_description = value

  @property
  def project_name(self):
    return self.ch.project_id

  @project_name.setter
  def project_name(self, value):
    self.ch.project_id = value

  @property
  def channel_type(self):
    return self.ch.channel_type

  @channel_type.setter
  def channel_type(self, value):
    self.ch.channel_type = value

  @property
  def resolution(self):
    return self.ch.resolution

  @resolution.setter
  def resolution(self, value):
    self.ch.resolution = value

  @property
  def propagate(self):
    # TODO KL port logic
    return self.ch.propagate

  @propagate.setter
  def propagate(self, value):
    # TODO KL port logic
    self.ch.propagate = value
    self.update()

  @property
  def channel_datatype(self):
    return self.ch.channel_datatype
  
  @property
  def readonly(self):
    return self.ch.readonly

  @readonly.setter
  def readonly(self, value):
    self.ch.readonly = value

  @property
  def default(self):
    return self.ch.default

  @default.setter
  def default(self, value):
    self.ch.default = value

  @property
  def time_range(self):
    return [int(self.ch.starttime),int(self.ch.endtime)]

  @property
  def default_time_range(self):
    return [int(self.ch.starttime),int(self.ch.starttime+1)]
  
  @property
  def window_range(self):
    return [int(self.ch.startwindow),int(self.ch.endwindow)]
  
  @property
  def exceptions(self):
    return self.ch.exceptions

  @property
  def channel_model ( self ):
    return Channel.objects.get(channel_name=self.ch.channel_name, project=self.pr.project_name)

  def getExceptions ( self ):
    return self.ch.exceptions

  def isDefault (self):
    return self.ch.default

  def getS3IndexTable (self, resolution):
    """Return the S3 index table"""
    if self.pr.kvengine == MYSQL:
      return '{}_res{}_s3index'.format(self.ch.channel_name, resolution)

  def getIdsTable (self):
    if self.pr.nd_version == '0.0':
      return "ids"
    else:
      return "{}_ids".format(self.ch.channel_name)

  def getTable (self, resolution):
    """Return the appropriate table for the specified resolution"""
    if self.pr.nd_version == '0.0':
      return "res{}".format(resolution)
    else:
      if self.pr.kvengine == MYSQL:
        return "{}_res{}".format(self.ch.channel_name, resolution)
      elif self.pr.kvengine == CASSANDRA:
        return "{}_cuboids".format(self.ch.channel_name, 'cuboids')
      elif self.pr.kvengine == DYNAMODB:
        return "{}_{}_cuboids".format(self.pr.getProjectName(), self.ch.channel_name)

  def getNearIsoTable (self, resolution):
    """Return the appropriate table for the specified resolution"""
    if self.pr.nd_version == '0.0':
      return "res{}neariso".format(resolution)
    else:
      return "{}_res{}neariso".format(self.ch.channel_name, resolution)

  def getKVTable (self, resolution):
    """Return the appropriate KvPairs for the specified resolution"""
    if self.pr.nd_version == '0.0':
      return "kvpairs{}".format(resolution)
    else:
      return "{}_kvpairs{}".format(self.ch.channel_name, resolution)

  def getRamonTable(self):
    """Return the name of the ramon table"""
    if self.pr.kvengine == MYSQL:
      return "{}_ramon".format(self.ch.channel_name)
    else:
      logger.error("RAMON not support for KV Engine {}".format(self.pr.kvengine))
      raise NDWSError("RAMON not support for KV Engine {}".format(self.pr.kvengine))

  def getIdxTable (self, resolution):
    """Return the appropriate Index table for the specified resolution"""
    if self.pr.nd_version == '0.0':
      return "idx{}".format(resolution)
    else:
      if self.pr.kvengine == MYSQL:
        return "{}_idx{}".format(self.ch.channel_name, resolution)
      elif self.pr.kvengine == CASSANDRA:
        return "{}_indexes".format(self.ch.channel_name)
      elif self.pr.kvengine == DYNAMODB:
        return "{}_{}_indexes".format(self.pr.getProjectName(), self.ch.channel_name)

  def getAnnoTable (self, anno_type):
    """Return the appropriate table for the specified type"""
    if self.pr.nd_version == '0.0':
      return "{}".format(annotation.anno_dbtables[anno_type])
    else:
      return "{}_{}".format(self.ch.channel_name, annotation.anno_dbtables[anno_type])

  def getExceptionsTable (self, resolution):
    """Return the appropiate exceptions table for the specified resolution"""
    if self.pr.nd_version == '0.0':
      return "exc{}".format(resolution)
    else:
      return "{}_exc{}".format(self.ch.channel_name, resolution)

  def setPropagate (self, value):
    if value in [NOT_PROPAGATED, PROPAGATED]:
      self.ch.propagate = value
      self.setReadOnly ( READONLY_FALSE )
      self.ch.save()
    elif value in [UNDER_PROPAGATION]:
      self.ch.propagate = value
      self.setReadOnly ( READONLY_TRUE )
      self.ch.save()
    else:
      logger.error ( "Wrong Propagate Value {} for Channel {}".format( value, self.ch.channel_name ) )
      raise NDWSError ( "Wrong Propagate Value {} for Channel {}".format( value, self.ch.channel_name ) )

  def setReadOnly (self, value):
    if value in [READONLY_TRUE, READONLY_FALSE]:
      self.ch.readonly = value
      self.ch.save()
    else:
      logger.error ( "Wrong Readonly Value {} for Channel {}".format( value, self.channel_name ) )
      raise NDWSError ( "Wrong Readonly Value {} for Channel {}".format( value, self.ch.channel_name ) )

  def isPropagated (self):
    if self.ch.propagate in [PROPAGATED]:
      return True
    else:
      return False

  def deleteChannel(self):
    """Delete the channel project"""
    self.ch.delete()
