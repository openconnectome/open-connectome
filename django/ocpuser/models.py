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

from django.db import models
from django.db.models.signals import post_save
from django.template import Context
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
class Dataset ( models.Model):
    dataset_name = models.CharField(max_length=255, primary_key=True,verbose_name="Name of the Image dataset")    
    dataset_description = models.CharField(max_length=4096,blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True)
    ISPUBLIC_CHOICES = (
        (0, 'Private'),
        (1, 'Public'),
    )
    public =  models.IntegerField(default=0, choices=ISPUBLIC_CHOICES)
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
        (0, 'Z Slices'),
        (1, 'Isotropic'),
    )
    scalingoption = models.IntegerField(default=0, choices=SCALING_CHOICES)
    scalinglevels = models.IntegerField(default=0)
    starttime = models.IntegerField(default=0)
    endtime = models.IntegerField(default=0)
    
    class Meta:
        """ Meta """
        db_table = u"datasets"
        managed = True
       
    def __unicode__(self):
        return self.dataset_name


class Project ( models.Model):
    project_name  =  models.CharField(max_length=255, primary_key=True)
    project_description  =  models.CharField(max_length=4096, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True)
    ISPUBLIC_CHOICES = (
        (0, 'Private'),
        (1, 'Public'),
    )
    public =  models.IntegerField(default=0, choices=ISPUBLIC_CHOICES)
    dataset = models.ForeignKey(Dataset)
    HOST_CHOICES = (
      ('localhost', 'localhost'),
      ('openconnecto.me', 'openconnecto.me'),
      ('braingraph1.cs.jhu.edu', 'braingraph1'),
      ('braingraph1dev.cs.jhu.edu', 'braingraph1dev'),
      ('braingraph2.cs.jhu.edu', 'braingraph2'),
      ('dsp061.pha.jhu.edu', 'dsp061'),
      ('dsp062.pha.jhu.edu', 'dsp062'),
      ('dsp063.pha.jhu.edu', 'dsp063'),
    )
    host =  models.CharField(max_length=255, choices=HOST_CHOICES, default='localhost')
    KVENGINE_CHOICES = (
        ('MySQL','MySQL'),
        ('Cassandra','Cassandra'),
        ('Riak','Riak'),

        )
    kvengine =  models.CharField(max_length=255, choices=KVENGINE_CHOICES, default='MySQL')
    KVSERVER_CHOICES = (
        ('localhost', 'localhost'),
        ('openconnecto.me', 'openconnecto.me'),
        ('braingraph1.cs.jhu.edu', 'braingraph1'),
        ('braingraph1dev.cs.jhu.edu', 'braingraph1dev'),
        ('braingraph2.cs.jhu.edu', 'braingraph2'),
        ('dsp061.pha.jhu.edu', 'dsp061'),
        ('dsp062.pha.jhu.edu', 'dsp062'),
        ('dsp063.pha.jhu.edu', 'dsp063'),
        )
    kvserver =  models.CharField(max_length=255, choices=KVSERVER_CHOICES, default='localhost')

    # Version information -- set automatically
    ocp_version =  models.CharField(max_length=255, default='0.6')
    schema_version =  models.CharField(max_length=255, default='0.6')

    class Meta:
        """ Meta """
        db_table = u"projects"
        managed = True
        
    def __unicode__(self):
        return self.project_name


class Token ( models.Model):
    token_name = models.CharField(max_length=255, primary_key=True)
    token_description  =  models.CharField(max_length=4096,blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True)
    project  = models.ForeignKey(Project)
    ISPUBLIC_CHOICES = (
        (0, 'Private'),
        (1, 'Public'),
    )
    public =  models.IntegerField(default=0, choices=ISPUBLIC_CHOICES)
    
    
    class Meta:
        """ Meta """
         # Required to override the default table name
        db_table = u"tokens"
        managed = True
    def __unicode__(self):
        return self.token_name


class Channel ( models.Model):

   project  = models.ForeignKey(Project,blank=True)
   channel_name = models.CharField(max_length=255)
   channel_description  =  models.CharField(max_length=4096,blank=True)
   CHANNELTYPE_CHOICES = (
        ('image', 'IMAGES'),
        ('annotation', 'ANNOTATIONS'),
        ('probmap', 'PROBABILITY_MAP'),
        ('rgb', 'RGB'),
        ('timeseries','TIMESERIES'),
        )
   channel_type = models.CharField(max_length=255,choices=CHANNELTYPE_CHOICES)

   resolution = models.IntegerField(default=0)

   PROPAGATE_CHOICES = (
        (0, 'NOT PROPAGATED'),
        (2, 'PROPAGATED'),
        )
   propagate =  models.IntegerField(choices=PROPAGATE_CHOICES, default=0)

   DATATYPE_CHOICES = (
        ('uint8', 'uint8'),
        ('uint16', 'uint16'),
        ('uint32', 'uint32'),
        ('uint64', 'uint64'),
        ('float32', 'float32'),
        )
   channel_datatype = models.CharField(max_length=255,choices=DATATYPE_CHOICES)

   READONLY_CHOICES = (
        (1, 'Yes'),
        (0, 'No'),
        )
   readonly =  models.IntegerField(choices=READONLY_CHOICES, default=0)

   EXCEPTION_CHOICES = (
       (1, 'Yes'),
       (0, 'No'),
     )
   exceptions =  models.IntegerField(choices=EXCEPTION_CHOICES, default=0)
   startwindow = models.IntegerField(default=0)
   endwindow = models.IntegerField(default=0)
   default = models.BooleanField(default=False)
   
   class Meta:
       """ Meta """
        # Required to override the default table name
       db_table = u"channels"
       managed = True
       unique_together = ('project', 'channel_name',)


   def __unicode__(self):
       return self.channel_name

