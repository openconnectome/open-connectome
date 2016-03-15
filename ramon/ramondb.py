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

import numpy as np
import cStringIO
import zlib
import re
from collections import defaultdict
import itertools
import blosc
from contextlib import closing
from operator import add, sub, div, mod
import MySQLdb

import ndlib
from ndtype import ANNOTATION_CHANNELS, TIMESERIES_CHANNELS, EXCEPTION_TRUE, PROPAGATED

import annotation
import mysqlramondb

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

"""
.. module:: ramonddb
    :synopsis: Manipulate/create/read annotations in the ramon format

.. moduleauthor:: Kunal Lillaney <lillaney@jhu.edu>
"""

class RamonDB:

  def __init__ (self, proj):
    """Connect with the brain databases"""

    self.datasetcfg = proj.datasetcfg
    self.proj = proj

#    if self.proj.getMDEngine():
    # import pdb; pdb.set_trace()
    self.annodb = mysqlramondb.MySQLRamonDB(proj)


  def close(self):
    """Call close on whatever type this is"""
    self.annodb.close()


  def assignID ( self, ch, annid ):
    """if annid == 0, create a new identifier"""
    if annid == 0: 
      return self.annodb.nextID(ch)
    else:
      return self.annodb.setID(ch, annid)

  #
  # getAnnotation:
  #    Look up an annotation, switch on what kind it is, build an HDF5 file and
  #     return it.
  def getAnnotation ( self, ch, annid ):
    """Return a RAMON object by identifier"""

    kvdict = self.annodb.getAnnotationKV ( ch, annid )
 
    annotype = int(kvdict['ann_type'])

    # switch on the type of annotation
    if annotype is None:
      return None
    elif annotype == annotation.ANNO_SYNAPSE:
      anno = annotation.AnnSynapse(self.annodb,ch)
    elif annotype == annotation.ANNO_SEED:
      anno = annotation.AnnSeed(self.annodb,ch)
    elif annotype == annotation.ANNO_SEGMENT:
      anno = annotation.AnnSegment(self.annodb,ch)
    elif annotype == annotation.ANNO_NEURON:
      anno = annotation.AnnNeuron(self.annodb,ch)
    elif annotype == annotation.ANNO_ORGANELLE:
      anno = annotation.AnnOrganelle(self.annodb,ch)
    elif annotype == annotation.ANNO_NODE:
      anno = annotation.AnnNode(self.annodb,ch)
    elif annotype == annotation.ANNO_SKELETON:
      anno = annotation.AnnSkeleton(self.annodb,ch)
    elif annotype == annotation.ANNO_ROI:
      anno = annotation.AnnROI(self.annodb,ch)
    elif annotype == annotation.ANNO_ANNOTATION:
      anno = annotation.Annotation(self.annodb,ch)
    else:
      raise NDWSError ( "Unrecognized annotation type {}".format(type) )

    # load the annotation
    anno.fromDict ( kvdict )

    return anno


  def updateAnnotation (self, ch, annid, field, value):
    """Update a RAMON object by identifier"""

    self.annodb.startTxn()
    try:
      anno = self.getAnnotation(ch, annid)
      if anno is None:
        logger.warning("No annotation found at identifier = {}".format(annid))
        raise OCPCAError ("No annotation found at identifier = {}".format(annid))
      anno.setField(field, value)
      self.annodb.putAnnotationKV(ch, annid, anno.toDict(), update=True)
      self.annodb.commit()
    except:
      self.annodb.rollback()
      raise


  def putAnnotation ( self, ch, anno, options='' ):
    """store an HDF5 annotation to the database"""

    self.annodb.startTxn()

    try:
      # for updates, make sure the annotation exists and is of the right type

      if 'update' in options:
 
        kvdict = self.annodb.getAnnotationKV ( ch, anno.annid )

        # can't update annotations that don't exist
        if  kvdict == None:
          raise NDWSError ( "During update no annotation found at id {}".format(anno.annid)  )

        else:
          self.annodb.putAnnotationKV ( ch, anno.annid, anno.toDict(), update=True)
        
      # Write the user chosen annotation id
      else:
        kvdict = anno.toDict()
        self.annodb.putAnnotationKV ( ch, anno.annid, kvdict)

      self.annodb.commit()

    except Exception, e:
      self.annodb.rollback()
      raise


  def deleteAnnotation ( self, ch, annoid, options='' ):
    """delete an HDF5 annotation from the database"""

    self.annodb.startTxn()
    try:
      self.annodb.deleteAnnotation(ch, annoid)
      self.annodb.commit()

    except Exception, e:
      self.annodb.rollback()
      raise

  def getSegments ( self, ch, annoid ):
    """get all the children of the annotation"""

    # ensure that the annotation is a neuron
    anno = self.getAnnotation ( ch, annoid )
    if anno.__class__ in [ annotation.AnnNeuron ]:
      return np.array(self.annodb.querySegments ( ch, annoid ), dtype=np.uint32)
    else:
      return None

  def getAnnoObjects ( self, ch, args ):
    """equality and predicate queries on metadata"""

    return self.annodb.getAnnoObjects ( ch, args )  
