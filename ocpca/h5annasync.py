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

import os
import sys
import argparse

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import h5py
import MySQLdb
import numpy as np
from celery import Celery
from contextlib import closing
import glob
import anydbm

import h5ann
import annotation
import ocpcarest
import ocpcaproj
import ocpcadb
import ocpcaprivate

from ocpcaerror import OCPCAError

import logging
logger=logging.getLogger("ocp")

def h5Async( fileName ):
  """ Write h5py files back to database """

  any_db = anydbm.open( ocpcaprivate.ssd_log_location+ocpcaprivate.bsd_name, 'c' )
  import time
  import pdb; pdb.set_trace()

  fileName = "/ssdata/kunal_hdf5_testTm7DmL.hdf5"

  #value = any_db.pop( fileName )

  #from ast import literal_eval as make_tuple
  #( token, timestamp, options ) = make_tuple ( value )

  token = "kunal_hdf5_test"
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadToken ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    retvals = []

    start = time.time()
    h5f = h5py.File ( fileName, driver='core', backing_store=False)

    for k in h5f.keys():

      idgrp = h5f.get(k)

      # Convert HDF5 to Annotation
      anno = h5ann.H5toAnnotation (k, idgrp, db)

      # set the indentifier
      if not ('update' in options or 'dataonly' in options or 'reduce' in options ):
        anno.setID ( db )

      print "Setting ID:", anno.annid

      try:
        if anno.__class__ in [ annotation.AnnNeuron, annotation.AnnSeed ] and ( idgrp.get('VOXELS') or idgrp.get('CUTOUT') ):
          logger.warning ( "Cannot write to annotation type {}".format( annot.__class__ ) )
          raise OCPCAError ( "Cannot write to annotation type {}".format( annot.__class__ ) ) 

        if 'update' in options and 'dataonly' in options:
          logger.warning ( "Illegal combination of options. Cannot use update and dataonly together" )
          raise OCPCAError ( "Illegal combination of options. Cannot use update and dataonly together" )

        elif not 'dataonly' in options and not 'reduce' in options:

          # Put into the database
          db.putAnnotation ( anno, options )
          print "Putting Annotation", anno.annid

        # Get the resolution if it's specified
        if 'RESOLUTION' in idgrp:
          resolution = int( idgrp.get('RESOLUTION')[0] )

        # Load the data associated with this annotation
        # Is it voxel data?
        if 'VOXELS' in idgrp:
          voxels = np.asarray( idgrp.get('VOXELS'), dtype=np.uint32 )
        else:
          voxels = None

        if voxels!=None and 'reduce' not in options:

          if 'preserve' in options:
            confilctopt = 'P'
          elif 'exception' in options:
            conflictopt = 'E'
          else:
            conflictopt = 'O'

          # Check that the voxels have a conforming size:
          if voxels.shape[1] != 3:
            logger.warning ( "Voxels data not the right shape. Must be (:,3). Shape is {}".format( str(voxels.shape) ) )
            raise OCPCAError ( "Voxels data not the right shape. Must be (:,3). Shape is {}".format( str(voxels.shape) ) )

          exceptions = db.annotate ( anno.annid, resolution, voxels, conflictopt )

        # Otherwise this is a shave operation
        elif voxels != None and 'reduce' in options:

          # Check that the voxels have a conforming size:
          if voxels.shape[1] != 3:
            logger.warning ( "Voxels data not the right shape. Must be (:,3). Shape is {}".format( str(voxels.shape) ) )
            raise OCPCAError ( "Voxels data not the right shape. Must be (:,3). Shape is {}".format( str(voxels.shape) ) )

          db.shave ( ann0.annid, resolution, voxels )

        # Is it dense data?
        if 'CUTOUT' in idgrp:
          cutout = np.array( idgrp.get('CUTOUT'), dtype=np.uint32 )
        else:
          cutout = None
        if 'XYZOFFSET' in idgrp:
          h5xyzoffset = idgrp.get('XYZOFFSET')
        else:
          h5xyzoffset = None

        if cutout !=None and h5xyzoffset !=None and 'reduce' not in options:

          if 'preserve' in options:
            conflictopt = 'P'
          elif 'exceptions' in options:
            conflictopt = 'E'
          else:
            conflictopt = 'O'

          # the zstart in datasetcfg is sometimes offset to make it aligned.
          # Probably remove the offset is the best idea and align the data to zero regardless of where it starts.
          # for now.

          corner = h5xyzoffset[:]
          # RBISO?? apply offsets?

          db.annotateEntityDense ( anno.annid, corner, resolution, np.array(cutout), conflictopt )

        elif cutout != None and h5xyzoffset != None and 'reduce' in options:

          corner = h5xyzoffset[:]
          # RBISO?? apply offsets?

        elif cutout != None or h5xyzoffset !=None:
          #TODO this is a loggable error
          pass

        # only add the identifier if you commit
        if not 'dataonly' in options and not 'reduce' in options:
          retvals.append ( anno.annid )

        os.remove( fileName )

        # Here with no error is successful
        print " Done successfully :", anno.annid
        print time.time()-start

      except MySQLdb.OperationalError, e:
        logger.warning ( "Put Annotation: Transaction did not complete. {}".format(e) )
        continue
      except MySQLdb.Error, e:
        logger.warning ( "Put Annotation: Put transaction rollback. {}".format(e) )
        rsybaise
      except OSError , e:
        logger.warning ( "Cannot unlink file from system. {}".format(e) )
      except Exception, e:
        logger.warning ( "Put Annotation: Put transaction rollback. {}".format(e) )
        raise

if __name__ == "__main__":
  h5Async( "anno981.h5" )
