# Copyright 2014 NeuroData (http://neurodata.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.db import models
from django.db.models.signals import post_save
from django.template import Context
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from ndlib.ndtype import *

# Create your models here.
class Dataset ( models.Model):
   dataset_name = models.CharField(max_length=255, primary_key=True,verbose_name="Name of the Image dataset")
   dataset_description = models.CharField(max_length=4096,blank=True)
   user = models.ForeignKey(settings.AUTH_USER_MODEL)
   ISPUBLIC_CHOICES = (
       (PUBLIC_FALSE, 'Private'),
       (PUBLIC_TRUE, 'Public'),
   )
   public =  models.IntegerField(default=PUBLIC_FALSE, choices=ISPUBLIC_CHOICES)
   ximagesize =  models.IntegerField()
   yimagesize =  models.IntegerField()
   zimagesize =  models.IntegerField()
   xoffset =  models.IntegerField(default=0)
   yoffset =  models.IntegerField(default=0)
   zoffset =  models.IntegerField(default=0)
   xvoxelres = models.FloatField(default=1.0)
   yvoxelres = models.FloatField(default=1.0)
   zvoxelres = models.FloatField(default=1.0)
   SCALING_CHOICES = (
     (ZSLICES, 'Z Slices'),
     (ISOTROPIC, 'Isotropic'),
   )
   scalingoption = models.IntegerField(default=ZSLICES, choices=SCALING_CHOICES)
   scalinglevels = models.IntegerField(default=0)

   class Meta:
     """ Meta """
     db_table = u"datasets"
     managed = True

   def __unicode__(self):
     return self.dataset_name


class Project ( models.Model):
  project_name  =  models.CharField(max_length=255, primary_key=True)
  project_description  =  models.CharField(max_length=4096, blank=True)
  user = models.ForeignKey(settings.AUTH_USER_MODEL)
  ISPUBLIC_CHOICES = (
    (PUBLIC_FALSE, 'Private'),
    (PUBLIC_TRUE, 'Public'),
  )
  public =  models.IntegerField(default=0, choices=ISPUBLIC_CHOICES)
  dataset = models.ForeignKey(Dataset)
  HOST_CHOICES = (
    ('localhost', 'default'),
  )
  host =  models.CharField(max_length=255, choices=HOST_CHOICES, default='localhost')
  KVENGINE_CHOICES = (
    (MYSQL, 'MySQL'),
    (REDIS, 'Redis'),
  )
  kvengine =  models.CharField(max_length=255, choices=KVENGINE_CHOICES, default=MYSQL)
  KVSERVER_CHOICES = (
    ('localhost', 'default'),
  )
  kvserver =  models.CharField(max_length=255, choices=KVSERVER_CHOICES, default='localhost')
  MDENGINE_CHOICES = (
    (MYSQL, 'MySQL'),
  )
  mdengine = models.CharField(max_length=255, choices=MDENGINE_CHOICES, default=MYSQL)
  S3BACKEND_CHOICES = (
    (S3_TRUE, 'Yes'),
    (S3_FALSE, 'No'),
  )
  s3backend = models.IntegerField(choices=S3BACKEND_CHOICES, default=S3_TRUE)

  # Version information -- set automatically
  nd_version =  models.CharField(max_length=255, default=ND_VERSION)
  schema_version =  models.CharField(max_length=255, default=SCHEMA_VERSION)

  class Meta:
    """ Meta """
    db_table = u"projects"
    managed = True

  def __unicode__(self):
    return self.project_name


class Token ( models.Model):
  token_name = models.CharField(max_length=255, primary_key=True)
  token_description  =  models.CharField(max_length=4096,blank=True)
  user = models.ForeignKey(settings.AUTH_USER_MODEL)
  project  = models.ForeignKey(Project)
  ISPUBLIC_CHOICES = (
    (PUBLIC_FALSE, 'Private'),
    (PUBLIC_TRUE, 'Public'),
  )
  public =  models.IntegerField(default=PUBLIC_FALSE, choices=ISPUBLIC_CHOICES)


  class Meta:
    """ Meta """
    # Required to override the default table name
    db_table = u"tokens"
    managed = True

  def __unicode__(self):
    return self.token_name


class Channel ( models.Model):

  project  = models.ForeignKey(Project)
  channel_name = models.CharField(max_length=255)
  channel_description  =  models.CharField(max_length=4096,blank=True)
  CHANNELTYPE_CHOICES = (
    (IMAGE, 'IMAGES'),
    (ANNOTATION, 'ANNOTATIONS'),
    (TIMESERIES,'TIMESERIES'),
  )
  channel_type = models.CharField(max_length=255, choices=CHANNELTYPE_CHOICES)

  resolution = models.IntegerField(default=0)

  PROPAGATE_CHOICES = (
    (NOT_PROPAGATED, 'NOT PROPAGATED'),
    (PROPAGATED, 'PROPAGATED'),
  )
  propagate =  models.IntegerField(choices=PROPAGATE_CHOICES, default=NOT_PROPAGATED)

  DATATYPE_CHOICES = (
    (UINT8, 'uint8'),
    (UINT16, 'uint16'),
    (UINT32, 'uint32'),
    (UINT64, 'uint64'),
    (INT8, 'int8'),
    (INT16, 'int16'),
    (INT32, 'int32'),
    (INT64, 'int64'),
    (FLOAT32, 'float32'),
  )
  channel_datatype = models.CharField(max_length=255, choices=DATATYPE_CHOICES)

  READONLY_CHOICES = (
    (READONLY_TRUE, 'Yes'),
    (READONLY_FALSE, 'No'),
  )
  readonly =  models.IntegerField(choices=READONLY_CHOICES, default=READONLY_FALSE)

  EXCEPTION_CHOICES = (
    (EXCEPTION_TRUE, 'Yes'),
    (EXCEPTION_FALSE, 'No'),
  )
  exceptions =  models.IntegerField(choices=EXCEPTION_CHOICES, default=EXCEPTION_FALSE)
  starttime = models.IntegerField(default=0)
  endtime = models.IntegerField(default=1)
  startwindow = models.IntegerField(default=0)
  endwindow = models.IntegerField(default=0)
  default = models.BooleanField(default=False)
  header = models.CharField(max_length=8192, default='', blank=True)

  class Meta:
    """ Meta """
    # Required to override the default table name
    db_table = u"channels"
    managed = True
    unique_together = ('project', 'channel_name',)

  def __unicode__(self):
    return self.channel_name

class Backup ( models.Model):

  backup_id = models.AutoField(primary_key=True)

  project  = models.ForeignKey(Project)

  # can specific a channel or can be all channels
  channel = models.ForeignKey(Channel, blank=True, null=True)

  PROTOCOL_CHOICES = (
    (FILE_SYSTEM, 'file system'),
    (AMAZON_S3, 'Amazon S3'),
  )
  protocol = models.CharField(max_length=255,choices=PROTOCOL_CHOICES)

  filename   =  models.CharField(max_length=4096)
  jsonfile   =  models.CharField(max_length=4096)

  description  =  models.CharField(max_length=4096, default="")

  datetimestamp = models.DateTimeField ( auto_now_add = True )

  STATUS_CHOICES = (
    (0, 'Done'),
    (1, 'Processing'),
    (2, 'Failed'),
  )
  status = models.IntegerField(choices=STATUS_CHOICES,default=0)

  class Meta:
    """ Meta """
    # Required to override the default table name
    db_table = u"backups"
    managed = True
    unique_together = ('project', 'datetimestamp',)

  def __unicode__(self):
    return self.description


class NIFTIHeader ( models.Model):

  channel = models.OneToOneField(Channel, primary_key=True)
  # all headers are 384 bytes for now.
  header = models.BinaryField(max_length=1024)
  affine = models.BinaryField(max_length=1024)

  class Meta:
    """ Meta """
    # Required to override the default table name
    db_table = u"nifti_header"
    managed = True

  def __unicode__(self):
    return self.header
