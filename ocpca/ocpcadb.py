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

# RBTODO batch i/o with getcubes when possible

import numpy as np
import cStringIO
import zlib
import MySQLdb
import re
import tempfile
import h5py
from collections import defaultdict
import itertools
from contextlib import closing

import ocpcaproj
import annotation
import annindex
from cube import Cube
import imagecube
import anncube
import probmapcube
import ocpcachannel
import ocplib

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")


import mysqlkvio
try:
  import casskvio
except:
  pass
try:
  import riakkvio
except:
  pass


################################################################################
#
#  class: OCPCADB
#
#  Manipulate/create/read from the Morton-order cube store
#
################################################################################

class OCPCADB: 

  def __init__ (self, proj):
    """Connect with the brain databases"""

    self.datasetcfg = proj.datasetcfg 
    self.proj = proj

    # Are there exceptions?
    #self.EXCEPT_FLAG = self.proj.getExceptions()
    self.KVENGINE = self.proj.getKVEngine()

    # Choose the I/O engine for key/value data
    if self.proj.getKVEngine() == 'MySQL':
      import mysqlkvio
      self.kvio = mysqlkvio.MySQLKVIO(self)
      self.NPZ = True
    elif self.proj.getKVEngine() == 'Riak':
      import riakkvio
      self.kvio = riakkvio.RiakKVIO(self)
      self.NPZ = False
    elif self.proj.getKVEngine() == 'Cassandra':
      import casskvio
      self.kvio = casskvio.CassandraKVIO(self)
      self.NPZ = False
    else:
      raise OCPCAError ("Unknown key/value store.  Engine = {}".format(self.proj.getKVEngine()))

    # Connection info for the metadata
    try:
      self.conn = MySQLdb.connect (host = self.proj.getDBHost(),
                            user = self.proj.getDBUser(),
                            passwd = self.proj.getDBPasswd(),
                            db = self.proj.getDBName())

      # start with no cursor
      self.cursor = None

    except MySQLdb.Error, e:
      self.conn = None
      logger.error("Failed to connect to database: %s, %s" % (self.proj.getDBHost(), self.proj.getDBName()))
      raise

    #if (self.proj.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS):
    self.annoIdx = annindex.AnnotateIndex ( self.kvio, self.proj )

  def setChannel ( self, channel_name ):
    """Switch the channel pointer"""
    ch = self.proj.getChannelObj(channel_name)

  def close ( self ):
    """Close the connection"""
    if self.conn:
      self.conn.close()
    self.kvio.close()

#
#  Cursor handling routines.  We operate in two modes.  TxN at a time
#  
#

  def getCursor ( self ):
    """If we are in a transaction, return the cursor, otherwise make one"""

    if self.cursor == None:
      return self.conn.cursor()
    else:
      return self.cursor

  def closeCursor ( self, cursor ):
    """Close the cursor if we are not in a transaction"""

    if self.cursor == None:
      cursor.close()

  def closeCursorCommit ( self, cursor ):
    """Close the cursor if we are not in a transaction"""

    if self.cursor == None:
      self.conn.commit()
      cursor.close()

  def commit ( self ):
    """Commit the transaction. Moved out of __del__ to make explicit.""" 

    self.cursor.close()
    self.conn.commit()

  def startTxn ( self ):
    """Start a transaction.  Ensure database is in multi-statement mode."""

    self.cursor = self.conn.cursor()
    sql = "START TRANSACTION"
    self.cursor.execute ( sql )

  def rollback ( self ):
    """Rollback the transaction.  To be called on exceptions."""

    self.cursor.close()
    self.conn.rollback()


  def peekID ( self ):
    """Look at the next ID but don't claim it.  This is an internal interface.
        It is not thread safe.  Need a way to lock the ids table for the 
        transaction to make it safe."""
    
    with closing(self.conn.cursor()) as cursor:

      # Query the current max identifier
      sql = "SELECT max(id) FROM " + str ( self.proj.getIdsTable() )
      try:
        cursor.execute ( sql )
      except MySQLdb.Error, e:
        logger.warning ("Problem retrieving identifier %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
        raise

      # Here we've queried the highest id successfully    
      row = cursor.fetchone()
      # if the table is empty start at 1, 0 is no annotation
      if ( row[0] == None ):
        identifier = 1
      else:
        identifier = int ( row[0] ) + 1

      return identifier


  def nextID ( self, ch ):
    """Get an new identifier. This is it's own txn and should not be called inside another transaction."""

    with closing(self.conn.cursor()) as cursor:
    
      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format(ch.getIdsTable())
      try:

        cursor.execute ( sql )

        # Query the current max identifier
        sql = "SELECT max(id) FROM {}".format(ch.getIdsTable()) 
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to create annotation identifier {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

        # Here we've queried the highest id successfully    
        row = cursor.fetchone ()
        # if the table is empty start at 1, 0 is no 
        if ( row[0] == None ):
          identifier = 1
        else:
          identifier = int ( row[0] ) + 1

        # increment and update query
        sql = "INSERT INTO {} VALUES ({})".format(ch.getIdsTable(), identifier)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to insert into identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

      return identifier


  def setID ( self, ch, annoid ):
    """Set a user specified identifier in the ids table"""

    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format( ch.getIdsTable() )
      try:
        # try the insert, get ane exception if it doesn't work
        sql = "INSERT INTO {} VALUES({})".format(ch.getIdsTable(), annoid)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.warning ( "Failed to set identifier table: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

    return annoid


  #
  #  setBatchID
  # 
  #  Place the user selected id into the ids table
  #
  def setBatchID ( self, annoidList ):
    """ Set a user specified identifier """

    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format(self.proj.getIdsTable())
      try:
        # try the insert, get and if it doesn't work
        sql = "INSERT INTO {} VALUES ( %s ) ".format( str(self.proj.getIdsTable()) )
        try:
          cursor.executemany ( sql, [str(i) for i in annoidList] )  
        except MySQLdb.Error, e:
          logger.warning ( "Failed to set identifier table: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

    return annoidList


  def reserve ( self, ch, count ):
    """Reserve contiguous identifiers. This is it's own txn and should not be called inside another transaction."""
    
    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format( ch.getIdsTable() )
      try:
        cursor.execute ( sql )

        # Query the current max identifier
        sql = "SELECT max(id) FROM {}".format( ch.getIdsTable() ) 
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to create annotation identifier %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
          raise

        # Here we've queried the highest id successfully    
        row = cursor.fetchone ()
        # if the table is empty start at 1, 0 is no 
        if ( row[0] == None ):
          identifier = 0
        else:
          identifier = int ( row[0] ) 

        # increment and update query
        sql = "INSERT INTO {} VALUES ({}) ".format(ch.getIdsTable(), identifier+count)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to insert into identifier table: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
          raise

      except Exception, e:
        logger.error ( "Failed to insert into identifier table: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

      return identifier+1


  # GET and PUT Methods for Image/Annotaion/Probmap Tables

  def getCube(self, ch, zidx, resolution, update=False):
    """Load a cube from the database"""

    # get the size of the image and cube
    [xcubedim, ycubedim, zcubedim] = cubedim = self.datasetcfg.cubedim[resolution] 
    cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())
  
    # get the block from the database
    cubestr = self.kvio.getCube(ch, zidx, resolution, update)

    if not cubestr:
      cube.zeros()
    else:
      # Handle the cube format here.  
      if self.NPZ:
          # decompress the cube
          cube.fromNPZ ( cubestr )

      else:
          # cubes are HDF5 files
          with closing(tempfile.NamedTemporaryFile()) as tmpfile:
            tmpfile.write(cubestr)
            tmpfile.seek(0)
            h5 = h5py.File(tmpfile.name) 
  
            # load the numpy array
            cube.data = np.array(h5['cuboid'])
            h5.close()

    return cube


  def getCubes(self, ch, listofidxs, resolution, neariso=False):
    """Return a list of cubes"""
    
    return self.kvio.getCubes(ch, listofidxs, resolution, neariso)


  def putCube(self, ch, zidx, resolution, cube, update=False):
    """ Store a cube in the annotation database """
  
    if cube.isNotZeros():
      # Handle the cube format here.  
      if self.NPZ:
        self.kvio.putCube(ch, zidx, resolution, cube.toNPZ(), not cube.fromZeros())
      else:
        with closing(tempfile.NamedTemporaryFile()) as tmpfile:
          h5 = h5py.File ( tmpfile.name, driver="core" )
          h5.create_dataset ( "cuboid", tuple(cube.data.shape), cube.data.dtype, compression='gzip',  data=cube.data )
          h5.close()
          tmpfile.seek(0)

          self.kvio.putCube(ch, zidx, resolution, tmpfile.read(), not cube.fromZeros())
    
  
  # GET AND PUT methods for Timeseries Database
  
  def getTimeCube(self, ch, zidx, timestamp, resolution, update=False):
    """Load a time cube from the database"""

    # get the size of the image and cube
    [xcubedim, ycubedim, zcubedim] = cubedim = self.datasetcfg.cubedim[resolution] 
    cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())

    # get the block from the database
    cubestr = self.kvio.getTimeCube(ch, zidx, timestamp, resolution, update)

    if not cubestr:
      cube.zeros()
    else:
      # Handle the cube format here.  
      if self.NPZ:
          # decompress the cube
          cube.fromNPZ(cubestr)

      else:
        # cubes are HDF5 files
        with closing(tempfile.NamedTemporaryFile()) as tmpfile:
          tmpfile.write(cubestr)
          tmpfile.seek(0)
          h5 = h5py.File(tmpfile.name) 

          # load the numpy array
          cube.data = np.array(h5['cuboid'])
          h5.close()

    return cube
  
  
  def getTimeCubes(self, ch, idx, listoftimestamps, resolution):
    """ Return a column of timeseries cubes. Better at I/O """

    return self.kvio.getTimeCubes(ch, idx, listoftimestamps, resolution)

  
  def putTimeCube(self, ch, zidx, timestamp, resolution, cube, update=False):
    """Store a cube in the annotation database"""

    if cube.isNotZeros():
      # Handle the cube format here.  
      if self.NPZ:
        self.kvio.putTimeCube(ch, zidx, timestamp, resolution, cube.toNPZ(), update)
      else:
        with closing(tempfile.NamedTemporaryFile()) as tmpfile:
          h5 = h5py.File ( tmpfile.name, driver='core', backing_store=True )
          h5.create_dataset ( "cuboid", tuple(cube.data.shape), cube.data.dtype, compression='gzip',  data=cube.data )
          h5.close()
          tmpfile.seek(0)
          self.kvio.putTimeSeriesCube ( zidx, timestamp, resolution, tmpfile.read(), update )
  
  def getExceptions ( self, ch, zidx, resolution, annoid ):
    """Load a cube from the annotation database"""

    excstr = self.kvio.getExceptions ( ch, zidx, resolution, annoid )
    if excstr:
      if self.NPZ:
        return np.load(cStringIO.StringIO ( zlib.decompress(excstr)))
      else:
        # cubes are HDF5 files
        with closing(tempfile.NamedTemporaryFile()) as tmpfile:
          tmpfile.write ( excstr )
          tmpfile.seek(0)
          h5 = h5py.File ( tmpfile.name ) 
  
          # load the numpy array
          excs = np.array ( h5['exceptions'] )
          h5.close()
          return excs

    else:
      return []


  def updateExceptions ( self, ch, key, resolution, exid, exceptions, update=False ):
    """Merge new exceptions with existing exceptions"""

    curexlist = self.getExceptions( ch, key, resolution, exid ) 

    update = False

    if curexlist!=[]:
      oldexlist = [ ocplib.XYZMorton ( trpl ) for trpl in curexlist ]
      newexlist = [ ocplib.XYZMorton ( trpl ) for trpl in exceptions ]
      exlist = set(newexlist + oldexlist)
      exlist = [ ocplib.MortonXYZ ( zidx ) for zidx in exlist ]
      update = True
    else:
      exlist = exceptions

    self.putExceptions ( ch, key, resolution, exid, exlist, update )


  def putExceptions ( self, ch, key, resolution, exid, exceptions, update ):
    """Package the object and transact with kvio"""

    exceptions = np.array ( exceptions, dtype=np.uint32 )

    #RBMAYBE make exceptions zipped in a future incompatible version??
    if self.NPZ:
      fileobj = cStringIO.StringIO ()
      np.save ( fileobj, exceptions )
      excstr = fileobj.getvalue()
      self.kvio.putExceptions(ch, key, resolution, exid, excstr, update)
    else:
      with closing (tempfile.NamedTemporaryFile()) as tmpfile:
        h5 = h5py.File ( tmpfile.name )
        h5.create_dataset ( "exceptions", tuple(exceptions.shape), exceptions.dtype, compression='gzip',  data=exceptions )
        h5.close()
        tmpfile.seek(0)
        self.kvio.putExceptions(ch, key, resolution, exid, tmpfile.read(), update)


  def removeExceptions ( self, ch, key, resolution, entityid, exceptions ):
    """Remove a list of exceptions. Should be done in a transaction"""

    curexlist = self.getExceptions(ch, key, resolution, entityid) 

    if curexlist != []:

      oldexlist = set([ ocplib.XYZMorton ( trpl ) for trpl in curexlist ])
      newexlist = set([ ocplib.XYZMorton ( trpl ) for trpl in exceptions ])
      exlist = oldexlist-newexlist
      exlist = [ ocplib.MortonXYZ ( zidx ) for zidx in exlist ]

      self.putExceptions ( ch, key, resolution, exid, exlist, True )


  #
  # queryRange
  #
  def queryRange ( self, lowkey, highkey, resolution, channel=None ):
    """Create a stateful query to a range of values not including the high value.
         To be used with getNextCube().
         Not thread safe (context per object)
         Also, one cursor only.  Not at multiple resolutions"""

    self._qr_cursor = self.conn.cursor ()
    self._qr_resolution = resolution

    if channel == None:
      # get the block from the database
      sql = "SELECT zindex, cube FROM " + self.proj.getTable(resolution) + " WHERE zindex >= " + str(lowkey) + " AND zindex < " + str(highkey)
    else:
      # or from a channel database
      channel = ocpcachannel.toID ( channel, self )
      sql = "SELECT zindex, cube FROM " + self.proj.getTable(resolution) + " WHERE channel = " + str(channel) + " AND zindex >= " + str(lowkey) + " AND zindex < " + str(highkey)
  
    try:
      self._qr_cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.error ( "Failed to retrieve data cube : %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise

  
  def getNextCube ( self ):
    """ Retrieve the next cube in a queryRange. Not thread safe (context per object) """

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ self._qr_resolution ] 

    # Create a cube object
    cube = anncube.AnnotateCube ( cubedim )

    row = self._qr_cursor.fetchone()

    # If we can't find a cube, assume it hasn't been written yet
    if ( row == None ):
      cube.zeros ()
      self._qr_cursor.close()
      return [None,None]
    else: 
      # decompress the cube
      cube.fromNPZ ( row[1] )
      return [row[0],cube]


  def getAllExceptions ( self, key, resolution ):
    """Load all exceptions for this cube"""

    # get the block from the database
    cursor = self.getCursor()
    sql = "SELECT id, exlist FROM %s where zindex=%s" % ( 'exc'+str(resolution), key )
    try:
      cursor.execute ( sql )
      excrows = cursor.fetchall()
    except MySQLdb.Error, e:
      logger.error ( "Error reading exceptions %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise
    finally:
      self.closeCursor ( cursor )

    # Parse and unzip all of the exceptions    
    excs = []
    if excrows == None:
      return []
    else:
      for excstr in excrows:
        excs.append ((np.uint32(excstr[0]), np.load(cStringIO.StringIO(zlib.decompress(excstr[1])))))
      return excs


  def annotate ( self, ch, entityid, resolution, locations, conflictopt='O' ):
    """Label the voxel locations or add as exceptions is the are already labeled."""

    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    #  An item may exist across several cubes
    #  Convert the locations into Morton order

    # dictionary with the index
    cubeidx = defaultdict(set)

    cubelocs = ocplib.locate_ctype ( np.array(locations, dtype=np.uint32), cubedim )

    # sort the arrary, by cubeloc
    cubelocs = ocplib.quicksort ( cubelocs )
    #cubelocs2.view('u4,u4,u4,u4').sort(order=['f0'], axis=0)

    # get the nonzero element offsets 
    nzdiff = np.r_[np.nonzero(np.diff(cubelocs[:,0]))]
    # then turn into a set of ranges of the same element
    listoffsets = np.r_[0, nzdiff + 1, len(cubelocs)]

    # start a transaction if supported
    self.kvio.startTxn()
    for i in range(len(listoffsets)-1):

      # grab the list of voxels for the first cube
      voxlist = cubelocs[listoffsets[i]:listoffsets[i+1],:][:,1:4]
      #  and the morton key
      key = cubelocs[listoffsets[i],0]

      cube = self.getCube ( ch, key, resolution, True )

      # get a voxel offset for the cube
      cubeoff = ocplib.MortonXYZ( key )
      #cubeoff = zindex.MortonXYZ(key)
      offset = np.asarray([cubeoff[0]*cubedim[0],cubeoff[1]*cubedim[1],cubeoff[2]*cubedim[2]], dtype = np.uint32)

      # add the items
      exceptions = np.array(cube.annotate(entityid, offset, voxlist, conflictopt), dtype=np.uint8)
      #exceptions = np.array(cube.annotate(entityid, offset, voxlist, conflictopt), dtype=np.uint8)

      # update the sparse list of exceptions
      if ch.getExceptions() == ocpcaproj.EXCEPTION_TRUE:
        if len(exceptions) != 0:
          self.updateExceptions(ch, key, resolution, entityid, exceptions)

      self.putCube(ch, key, resolution, cube)

      # add this cube to the index
      cubeidx[entityid].add(key)

    # write it to the database
    self.annoIdx.updateIndexDense(ch, cubeidx, resolution)
    # commit cubes.  not commit controlled with metadata
    self.kvio.commit()


  #
  # putCubeSSD
  # 
  def putCubeSSD ( key, reolution, cube ):
    """ Write the cube to SSD's """
    print "HELLO"



  #
  # shave
  #
  #  reduce the voxels 
  #
  def shave ( self, ch, entityid, resolution, locations ):
    """Label the voxel locations or add as exceptions is the are already labeled."""

    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # dictionary with the index
    cubeidx = defaultdict(set)

    # convert voxels z coordinate
    cubelocs = ocplib.locate_ctype ( np.array(locations, dtype=np.uint32), cubedim )

    # sort the arrary, by cubeloc
    cubelocs = ocplib.quicksort ( cubelocs )
    #cubelocs.view('u4,u4,u4,u4').sort(order=['f0'], axis=0)

    # get the nonzero element offsets 
    nzdiff = np.r_[np.nonzero(np.diff(cubelocs[:,0]))]
    # then turn into a set of ranges of the same element
    listoffsets = np.r_[0, nzdiff + 1, len(cubelocs)]

    self.kvio.startTxn()

    try:

      for i in range(len(listoffsets)-1):

        # grab the list of voxels for the first cube
        voxlist = cubelocs[listoffsets[i]:listoffsets[i+1],:][:,1:4]
        #  and the morton key
        key = cubelocs[listoffsets[i],0]

        cube = self.getCube (ch, key, resolution, True)

        # get a voxel offset for the cube
        cubeoff = ocplib.MortonXYZ(key)
        #cubeoff2 = zindex.MortonXYZ(key)
        offset = np.asarray( [cubeoff[0]*cubedim[0],cubeoff[1]*cubedim[1],cubeoff[2]*cubedim[2]], dtype=np.uint32 )

        # remove the items
        exlist, zeroed = cube.shave (entityid, offset, voxlist)
        # make sure that exceptions are stored as 8 bits
        exceptions = np.array(exlist, dtype=np.uint8)

        # update the sparse list of exceptions
        if ch.getExceptions == ocpcaproj.EXCEPTION_TRUE:
          if len(exceptions) != 0:
            self.removeExceptions ( ch, key, resolution, entityid, exceptions )

        self.putCube (ch, key, resolution, cube)

        # For now do no index processing when shaving.  Assume there are still some
        #  voxels in the cube???

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()


  #
  # annotateDense
  #
  #  Process a cube of data that has been labelled with annotations.
  #
  def annotateDense ( self, ch, corner, resolution, annodata, conflictopt ):
    """Process all the annotations in the dense volume"""

    index_dict = defaultdict(set)

    # dim is in xyz, data is in zyxj
    dim = [ annodata.shape[2], annodata.shape[1], annodata.shape[0] ]

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    zoffset = corner[2]%zcubedim
    yoffset = corner[1]%ycubedim
    xoffset = corner[0]%xcubedim

    databuffer = np.zeros ([znumcubes*zcubedim, ynumcubes*ycubedim, xnumcubes*xcubedim], dtype=np.uint32 )
    databuffer [ zoffset:zoffset+dim[2], yoffset:yoffset+dim[1], xoffset:xoffset+dim[0] ] = annodata 

    # start a transaction if supported
    self.kvio.startTxn()

    try:

      for z in range(znumcubes):
        for y in range(ynumcubes):
          for x in range(xnumcubes):

            key = ocplib.XYZMorton ([x+xstart,y+ystart,z+zstart])
            cube = self.getCube (ch, key, resolution, True)
            
            if conflictopt == 'O':
              cube.overwrite ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            elif conflictopt == 'P':
              cube.preserve ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            elif conflictopt == 'E': 
              if ch.getExceptions() == ocpcaproj.EXCEPTION_TRUE:
                exdata = cube.exception ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
                for exid in np.unique ( exdata ):
                  if exid != 0:
                    # get the offsets
                    exoffsets = np.nonzero ( exdata==exid )
                    # assemble into 3-tuples zyx->xyz
                    exceptions = np.array ( zip(exoffsets[2], exoffsets[1], exoffsets[0]), dtype=np.uint32 )
                    # update the exceptions
                    self.updateExceptions ( ch, key, resolution, exid, exceptions )
                    # add to the index
                    index_dict[exid].add(key)
              else:
                logger.error("No exceptions for this project.")
                raise OCPCAError ( "No exceptions for this project.")
            else:
              logger.error ( "Unsupported conflict option %s" % conflictopt )
              raise OCPCAError ( "Unsupported conflict option %s" % conflictopt )
            
            self.putCube (ch, key, resolution, cube)

            #update the index for the cube
            # get the unique elements that are being added to the data
            uniqueels = np.unique ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            for el in uniqueels:
              index_dict[el].add(key) 

            # remove 0 no reason to index that
            if 0 in index_dict:
              del(index_dict[0])

      # Update all indexes
      self.annoIdx.updateIndexDense(ch, index_dict, resolution)
      # commit cubes.  not commit controlled with metadata

    except:
      self.kvio.rollback()
      raise
    
    self.kvio.commit()


  #
  #  Called when labeling an entity
  #
  def annotateEntityDense ( self, ch, entityid, corner, resolution, annodata, conflictopt ):
    """Relabel all nonzero pixels to annotation id and call annotateDense"""

    #vec_func = np.vectorize ( lambda x: 0 if x == 0 else entityid ) 
    #annodata = vec_func ( annodata )
    annodata = ocplib.annotateEntityDense_ctype ( annodata, entityid )

    return self.annotateDense ( ch, corner, resolution, annodata, conflictopt )

  #
  # shaveDense
  #
  #  Reduce the specified annotations 
  #
  def shaveDense ( self, ch, entityid, corner, resolution, annodata ):
    """Process all the annotations in the dense volume"""


    index_dict = defaultdict(set)

    # dim is in xyz, data is in zyxj
    dim = [ annodata.shape[2], annodata.shape[1], annodata.shape[0] ]

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    zoffset = corner[2]%zcubedim
    yoffset = corner[1]%ycubedim
    xoffset = corner[0]%xcubedim

    databuffer = np.zeros ([znumcubes*zcubedim, ynumcubes*ycubedim, xnumcubes*xcubedim], dtype=np.uint32 )
    databuffer [ zoffset:zoffset+dim[2], yoffset:yoffset+dim[1], xoffset:xoffset+dim[0] ] = annodata 

    # start a transaction if supported
    self.kvio.startTxn()

    try:

      for z in range(znumcubes):
        for y in range(ynumcubes):
          for x in range(xnumcubes):

            key = ocplib.XYZMorton ([x+xstart,y+ystart,z+zstart])
            cube = self.getCube(ch, key, resolution, True)

            exdata = cube.shaveDense ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            for exid in np.unique ( exdata ):
              if exid != 0:
                # get the offsets
                exoffsets = np.nonzero ( exdata==exid )
                # assemble into 3-tuples zyx->xyz
                exceptions = np.array ( zip(exoffsets[2], exoffsets[1], exoffsets[0]), dtype=np.uint32 )
                # update the exceptions
                self.removeExceptions ( key, resolution, exid, exceptions )
                # add to the index
                index_dict[exid].add(key)

            self.putCube(ch, key, resolution, cube)

            #update the index for the cube
            # get the unique elements that are being added to the data
            uniqueels = np.unique ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            for el in uniqueels:
              index_dict[el].add(key) 

            # remove 0 no reason to index that
            del(index_dict[0])

      # Update all indexes
      self.annoIdx.updateIndexDense(ch, index_dict, resolution)

    except:
      self.kvio.rollback()
      raise

    # commit cubes.  not commit controlled with metadata
    self.kvio.commit()


  #
  # shaveEntityDense
  #
  #  Takes a bitmap for an entity and calls denseShave
  #  renumber the annotations to match the entity id.
  #
  def shaveEntityDense ( self, ch, entityid, corner, resolution, annodata ):
    """Process all the annotations in the dense volume"""

    # Make shaving a per entity operation
    vec_func = np.vectorize ( lambda x: 0 if x == 0 else entityid ) 
    annodata = vec_func ( annodata )

    self.shaveDense ( ch, entityid, corner, resolution, annodata )


  def _zoominCutout ( self, ch, corner, dim, resolution ):
    """Scale to a smaller cutout that will be zoomed"""

    # scale the corner to lower resolution
    effcorner = corner[0]/(2**(ch.getResolution()-resolution)), corner[1]/(2**(ch.getResolution()-resolution)), corner[2]

    # pixels offset within big range
    xpixeloffset = corner[0]%(2**(ch.getResolution()-resolution))
    ypixeloffset = corner[1]%(2**(ch.getResolution()-resolution))

    # get the new dimension, snap up to power of 2
    outcorner = (corner[0]+dim[0],corner[1]+dim[1],corner[2]+dim[2])

    newoutcorner = (outcorner[0]-1)/(2**(ch.getResolution()-resolution))+1, (outcorner[1]-1)/(2**(ch.getResolution()-resolution))+1, outcorner[2]
    effdim = (newoutcorner[0]-effcorner[0],newoutcorner[1]-effcorner[1],newoutcorner[2]-effcorner[2])

    return effcorner, effdim, (xpixeloffset,ypixeloffset)


  def _zoomoutCutout ( self, ch, corner, dim, resolution ):
    """Scale to a larger cutout that will be shrunk"""

    # scale the corner to higher resolution
    effcorner = corner[0]*(2**(resolution-ch.getResolution())), corner[1]*(2**(resolution-ch.getResolution())), corner[2]

    effdim = dim[0]*(2**(resolution-ch.getResolution())),dim[1]*(2**(resolution-ch.getResolution())),dim[2]

    return effcorner, effdim 


  def cutout ( self, ch, corner, dim, resolution, zscaling=None, annoids=None ):
    """Extract a cube of arbitrary size.  Need not be aligned."""

    # alter query if  (ocpcaproj)._resolution is > resolution. if cutout is below resolution, get a smaller cube and scaleup
    if ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS and ch.getResolution() > resolution:

      # find the effective dimensions of the cutout (where the data is)
      effcorner, effdim, (xpixeloffset,ypixeloffset) = self._zoominCutout ( ch, corner, dim, resolution )
      [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ ch.getResolution() ] 
      effresolution = ch.getResolution()

    # alter query if  (ocpcaproj)._resolution is < resolution. if cutout is above resolution, get a large cube and scaledown
    elif ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS and ch.getResolution() < resolution and ch.getPropagate() not in [ocpcaproj.PROPAGATED]:  

      [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ ch.getResolution() ] 
      effcorner, effdim = self._zoomoutCutout ( ch, corner, dim, resolution )
      effresolution = ch.getResolution()

    # this is the default path when not scaling up the resolution
    else:

      # get the size of the image and cube
      [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 
      effcorner = corner
      effdim = dim
      effresolution = resolution 

    # Round to the nearest larger cube in all dimensions
    zstart = effcorner[2]/zcubedim
    ystart = effcorner[1]/ycubedim
    xstart = effcorner[0]/xcubedim

    znumcubes = (effcorner[2]+effdim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (effcorner[1]+effdim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (effcorner[0]+effdim[0]+xcubedim-1)/xcubedim - xstart
  
    # use the requested resolution
    if zscaling == 'nearisotropic' and self.datasetcfg.nearisoscaledown[resolution] > 1:
      dbname = ch.getNearIsoTable(resolution)
    else:
      dbname = ch.getTable(effresolution)

    import cube
    incube = Cube.getCube ( cubedim, ch.getChannelType(), ch.getDataType() )
    outcube = Cube.getCube([xnumcubes*xcubedim,ynumcubes*ycubedim,znumcubes*zcubedim], ch.getChannelType(), ch.getDataType())
                                        
    # Build a list of indexes to access
    listofidxs = []
    for z in range ( znumcubes ):
      for y in range ( ynumcubes ):
        for x in range ( xnumcubes ):
          mortonidx = ocplib.XYZMorton ( [x+xstart, y+ystart, z+zstart] )
          listofidxs.append ( mortonidx )

    # Sort the indexes in Morton order
    listofidxs.sort()
    
    # xyz offset stored for later use
    lowxyz = ocplib.MortonXYZ ( listofidxs[0] )
    
    self.kvio.startTxn()

    try:

      if zscaling == 'nearisotropic' and self.datasetcfg.nearisoscaledown[resolution] > 1:
        cuboids = self.getCubes(ch, listofidxs, effresolution, True)
      else:
        cuboids = self.getCubes(ch, listofidxs, effresolution)

      # use the batch generator interface
      for idx, datastring in cuboids:
 
        #add the query result cube to the bigger cube
        curxyz = ocplib.MortonXYZ(int(idx))
        offset = [ curxyz[0]-lowxyz[0], curxyz[1]-lowxyz[1], curxyz[2]-lowxyz[2] ]

        if self.NPZ:
          incube.fromNPZ ( datastring[:] )

        else:
          # cubes are HDF5 files
          with closing(tempfile.NamedTemporaryFile()) as tmpfile:
            tmpfile.write ( datastring )
            tmpfile.seek(0)
            h5 = h5py.File ( tmpfile.name, driver='core', backing_store=False ) 
            # load the numpy array
            incube.data = np.array ( h5['cuboid'] )

            h5.close()

        # apply exceptions if it's an annotation project
        if annoids!= None and ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS:
          incube.data = ocplib.filter_ctype_OMP ( incube.data, annoids )
          if ch.getExceptions() == ocpcaproj.EXCEPTION_TRUE:
            self.applyCubeExceptions ( ch, annoids, effresolution, idx, incube )

        # add it to the output cube
        outcube.addData ( incube, offset ) 

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()

    # if we fetched a smaller cube to zoom, correct the result
    if ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS and ch.getResolution() > resolution:

      outcube.zoomData ( ch.getResolution()-resolution )

      # need to trim based on the cube cutout at resolution()
      outcube.trim ( corner[0]%(xcubedim*(2**(ch.getResolution()-resolution)))+xpixeloffset,dim[0], corner[1]%(ycubedim*(2**(ch.getResolution()-resolution)))+ypixeloffset,dim[1], corner[2]%zcubedim,dim[2] )

    # if we fetch a larger cube, downscale it and correct
    elif ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS and ch.getResolution() < resolution and ch.getPropagate() not in [ocpcaproj.PROPAGATED]:

      outcube.downScale (resolution - ch.getResolution())

      # need to trime based on the cube cutout at resolution
      outcube.trim ( corner[0]%(xcubedim*(2**(ch.getResolution()-resolution))),dim[0], corner[1]%(ycubedim*(2**(ch.getResolution()-resolution))),dim[1], corner[2]%zcubedim,dim[2] )
      
    # need to trim down the array to size only if the dimensions are not the same
    elif dim[0] % xcubedim  == 0 and dim[1] % ycubedim  == 0 and dim[2] % zcubedim  == 0 and corner[0] % xcubedim  == 0 and corner[1] % ycubedim  == 0 and corner[2] % zcubedim  == 0:
      pass
    else:
      outcube.trim ( corner[0]%xcubedim,dim[0],corner[1]%ycubedim,dim[1],corner[2]%zcubedim,dim[2] )

    return outcube


  def timecutout(self, ch, corner, dim, resolution, timerange):
    """Extract a cube of arbitrary size.  Need not be aligned."""

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    # use the requested resolution
    import cube
    incube = Cube.getCube ( cubedim, ch.getChannelType(), ch.getDataType() )
    outcube = Cube.getCube([xnumcubes*xcubedim,ynumcubes*ycubedim,znumcubes*zcubedim], ch.getChannelType(), ch.getDataType(), timerange=timerange)

    # Build a list of indexes to access
    listofidxs = []
    for z in range (znumcubes):
      for y in range (ynumcubes):
        for x in range (xnumcubes):
          mortonidx = ocplib.XYZMorton([x+xstart, y+ystart, z+zstart])
          listofidxs.append(mortonidx)

    # Sort the indexes in Morton order
    listofidxs.sort()

    # xyz offset stored for later use
    lowxyz = ocplib.MortonXYZ(listofidxs[0])

    self.kvio.startTxn()

    try:
      for idx in listofidxs:
        cuboids = self.getTimeCubes(ch, idx, range(timerange[0],timerange[1]), resolution)
        
        # use the batch generator interface
        for idx, timestamp, datastring in cuboids:

          # add the query result cube to the bigger cube
          curxyz = ocplib.MortonXYZ(int(idx))
          offset = [ curxyz[0]-lowxyz[0], curxyz[1]-lowxyz[1], curxyz[2]-lowxyz[2] ]

          if self.NPZ:
            incube.fromNPZ(datastring[:])

          else:
            # cubes are HDF5 files
            with closing(tempfile.NamedTemporaryFile()) as tmpfile:
              tmpfile = tempfile.NamedTemporaryFile ()
              tmpfile.write ( datastring )
              tmpfile.seek(0)
              h5 = h5py.File ( tmpfile.name, driver='core', backing_store=False ) 
              # load the numpy array
              incube.data = np.array ( h5['cuboid'] )
              h5.close()
          
          # add it to the output cube
          outcube.addData(incube, offset, timestamp)

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()

    # need to trim down the array to size only if the dimensions are not the same
    if dim[0] % xcubedim  == 0 and dim[1] % ycubedim  == 0 and dim[2] % zcubedim  == 0 and corner[0] % xcubedim  == 0 and corner[1] % ycubedim  == 0 and corner[2] % zcubedim  == 0:
      pass
    else:
      outcube.trim ( corner[0]%xcubedim,dim[0],corner[1]%ycubedim,dim[1],corner[2]%zcubedim,dim[2] )

    return outcube


  def getVoxel ( self, ch, resolution, voxel ):
    """Return the identifier at a voxel"""

    # get the size of the image and cube
    [xcubedim, ycubedim, zcubedim] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # convert the voxel into zindex and offsets. Round to the nearest larger cube in all dimensions
    xyzcube = [ voxel[0]/xcubedim, voxel[1]/ycubedim, voxel[2]/zcubedim ]
    xyzoffset =[ voxel[0]%xcubedim, voxel[1]%ycubedim, voxel[2]%zcubedim ]
    key = ocplib.XYZMorton ( xyzcube )

    cube = self.getCube(ch, key, resolution)

    if cube is None:
      return 0
    else:
      return cube.getVoxel(xyzoffset)


  # Alternate to getVolume that returns a annocube
  def annoCutout ( self, ch, annoids, resolution, corner, dim, remapid=None ):
    """Fetch a volume cutout with only the specified annotation"""

    # cutout is zoom aware
    cube = self.cutout(ch, corner,dim,resolution, annoids=annoids )
  
    # KL TODO
    if remapid:
      vec_func = np.vectorize ( lambda x: np.uint32(remapid) if x != 0 else np.uint32(0) ) 
      cube.data = vec_func ( cube.data )

    return cube

  # helper function to apply exceptions
  def applyCubeExceptions ( self, ch, annoids, resolution, idx, cube ):
    """Apply the expcetions to a specified cube and resolution"""

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 
  
    (x,y,z) = ocplib.MortonXYZ ( idx )

    # for the target ids
    for annoid in annoids:
      # apply exceptions
      exceptions = self.getExceptions( ch, idx, resolution, annoid ) 
      for e in exceptions:
        cube.data[e[2],e[1],e[0]]=annoid

  #
  #  zoomVoxels
  #
  def zoomVoxels ( self, voxels, resgap ):
    """Convert voxels from one resolution to another based 
       on a positive number of hierarcy levels.
       This is used by both exception and the voxels data argument."""

    # correct for zoomed resolution
    newvoxels = []
    scaling = 2**(resgap)
    for vox in voxels:
      for numy in range(scaling):
        for numx in range(scaling):
          newvoxels.append ( (vox[0]*scaling + numx, vox[1]*scaling + numy, vox[2]) )
    return newvoxels


  #
  # getLocations -- return the list of locations associated with an identifier
  #
  def getLocations ( self, ch, entityid, res ):

    # get the size of the image and cube
    resolution = int(res)
    
    #scale to project resolution
    if ch.getResolution() > resolution:
      effectiveres = ch.getResolution() 
    else:
      effectiveres = resolution


    voxlist = []
    
    zidxs = self.annoIdx.getIndex(ch, entityid,resolution)

    for zidx in zidxs:

      print zidx

      cb = self.getCube(ch, zidx,effectiveres) 

      # mask out the entries that do not match the annotation id
      # KL TODO
      vec_func = np.vectorize ( lambda x: entityid if x == entityid else 0 )
      annodata = vec_func ( cb.data )
    
      # where are the entries
      offsets = np.nonzero ( annodata ) 
      voxels = np.array(zip(offsets[2], offsets[1], offsets[0]), dtype=np.uint32)

      # Get cube offset information
      [x,y,z] = ocplib.MortonXYZ(zidx)
      xoffset = x * self.datasetcfg.cubedim[resolution][0] 
      yoffset = y * self.datasetcfg.cubedim[resolution][1] 
      zoffset = z * self.datasetcfg.cubedim[resolution][2] 

      # Now add the exception voxels
      if ch.getExceptions() ==  ocpcaproj.EXCEPTION_TRUE:
        exceptions = self.getExceptions( ch, zidx, resolution, entityid ) 
        if exceptions != []:
          voxels = np.append ( voxels.flatten(), exceptions.flatten())
          voxels = voxels.reshape(len(voxels)/3,3)

      # Change the voxels back to image address space
      [ voxlist.append([a+xoffset, b+yoffset, c+zoffset]) for (a,b,c) in voxels ] 

    # zoom out the voxels if necessary 
    if effectiveres > resolution:
      voxlist = self.zoomVoxels ( voxlist, effectiveres-resolution )

    return voxlist


  def getBoundingBox ( self, ch, annids, res ):
    """Return a corner and dimension of the bounding box for an annotation using the index"""
  
    # get the size of the image and cube
    resolution = int(res)

    # determine the resolution for project information
    if ch.getResolution() > resolution:
      effectiveres = ch.getResolution() 
      scaling = 2**(effectiveres-resolution)
    else:
      effectiveres = resolution
      scaling=1

    # all boxes in the indexes
    zidxs=[]
    for annid in annids:
      zidxs = itertools.chain(zidxs,self.annoIdx.getIndex(ch, annid, effectiveres))
    
    # convert to xyz coordinates
    try:
      xyzvals = np.array ( [ ocplib.MortonXYZ(zidx) for zidx in zidxs ], dtype=np.uint32 )
    # if there's nothing in the chain, the array creation will fail
    except:
      return None, None

    cubedim = self.datasetcfg.cubedim [ resolution ] 

    # find the corners
    xmin = min(xyzvals[:,0]) * cubedim[0] * scaling
    xmax = (max(xyzvals[:,0])+1) * cubedim[0] * scaling
    ymin = min(xyzvals[:,1]) * cubedim[1] * scaling
    ymax = (max(xyzvals[:,1])+1) * cubedim[1] * scaling
    zmin = min(xyzvals[:,2]) * cubedim[2]
    zmax = (max(xyzvals[:,2])+1) * cubedim[2]

    corner = [ xmin, ymin, zmin ]
    dim = [ xmax-xmin, ymax-ymin, zmax-zmin ]

    return (corner,dim)


  def annoCubeOffsets ( self, ch, dataids, resolution, remapid=False ):
    """an iterable on the offsets and cubes for an annotation"""
   
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # alter query if  (ocpcaproj)._resolution is > resolution
    # if cutout is below resolution, get a smaller cube and scaleup
    if ch.getResolution() > resolution:
      effectiveres = ch.getResolution() 
    else:
      effectiveres = resolution

    zidxs = set()
    for did in dataids:
      zidxs |= set ( self.annoIdx.getIndex(ch, did,effectiveres))

    for zidx in zidxs:

      # get the cube and mask out the non annoid values
      cb = self.getCube(ch, zidx, effectiveres) 
      if not remapid:
        cb.data = ocplib.filter_ctype_OMP ( cb.data, dataids )
      else: 
        cb.data = ocplib.filter_ctype_OMP ( cb.data, dataids )
        # KL TODO
        vec_func = np.vectorize ( lambda x: np.uint32(remapid) if x != 0 else np.uint32(0) ) 
        cb.data = vec_func ( cb.data )

      # zoom the data if not at the right resolution
      # and translate the zindex to the upper resolution
      (xoff,yoff,zoff) = ocplib.MortonXYZ ( zidx )
      offset = (xoff*xcubedim, yoff*ycubedim, zoff*zcubedim)

      # if we're zooming, so be it
      if resolution < effectiveres:
        cb.zoomData ( effectiveres-resolution )
        offset = (offset[0]*(2**(effectiveres-resolution)),offset[1]*(2**(effectiveres-resolution)),offset[2])

      # add any exceptions
      # Get exceptions if this DB supports it
      if ch.getExceptions() == ocpcaproj.EXCEPTION_TRUE:
        for exid in dataids:
          exceptions = self.getExceptions(ch, zidx, effectiveres, exid) 
          if exceptions != []:
            if resolution < effectiveres:
                exceptions = self.zoomVoxels ( exceptions, effectiveres-resolution )
            # write as a loop first, then figure out how to optimize 
            # exceptions are stored relative to cube offset
            for e in exceptions:
              if not remapid:
                cb.data[e[2],e[1],e[0]]=exid
              else:
                cb.data[e[2],e[1],e[0]]=remapid

      yield (offset,cb.data)

  #
  # getAnnotation:  
  #    Look up an annotation, switch on what kind it is, build an HDF5 file and
  #     return it.
  def getAnnotation ( self, ch, annid ):
    """Return a RAMON object by identifier"""

    cursor = self.getCursor()
    try:
      return annotation.getAnnotation(ch, annid, self, cursor)
    except:
      self.closeCursor(cursor) 
      raise

    self.closeCursorCommit(cursor)


  def updateAnnotation (self, ch, annid, field, value):
    """Update a RAMON object by identifier"""

    cursor = self.getCursor()
    try:
      anno = self.getAnnotation(ch, annid)
      if anno is None:
        logger.warning("No annotation found at identifier = {}".format(annid))
        raise OCPCAError ("No annotation found at identifier = {}".format(annid))
      anno.setField(ch, field, value)
      anno.update(ch, cursor)
    except:
      self.closeCursor(cursor) 
      raise
    self.closeCursorCommit(cursor)


  def putAnnotation ( self, ch, anno, options='' ):
    """store an HDF5 annotation to the database"""
    
    cursor = self.getCursor()
    try:
      retval = annotation.putAnnotation(ch, anno, self, cursor, options)
    except:
      self.closeCursor(cursor) 
      raise

    self.closeCursorCommit(cursor)

    return retval

  def deleteAnnotation ( self, ch, annoid, options='' ):
    """delete an HDF5 annotation from the database"""

    cursor = self.getCursor()
    try:
      self.deleteAnnoData ( ch, annoid )
      retval = annotation.deleteAnnotation ( ch, annoid, self, cursor, options )
    except:
      self.closeCursor( cursor ) 
      raise

    self.closeCursorCommit(cursor)
    
    return retval
  
  #
  #deleteAnnoData:
  #    Delete the voxel data from the database for annoid 
  #
  def deleteAnnoData ( self, ch, annoid):

    resolutions = self.datasetcfg.resolutions

    self.kvio.startTxn()

    try:

      for res in resolutions:
      
        #get the cubes that contain the annotation
        zidxs = self.annoIdx.getIndex(ch, annoid,res,True)
        
        #Delete annotation data
        for key in zidxs:
          cube = self.getCube(ch, key, res, True)
          # KL TODO
          vec_func = np.vectorize ( lambda x: 0 if x == annoid else x )
          cube.data = vec_func ( cube.data )
          # remove the expcetions
          if ch.getExceptions == ocpcaproj.EXCEPTION_TRUE:
            self.kvio.deleteExceptions(ch, key, res, annoid)
          self.putCube(ch, key, res, cube)
        
      # delete Index
      self.annoIdx.deleteIndex(ch, annoid,resolutions)

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()


  def getChildren ( self, ch, annoid ):
    """get all the children of the annotation"""
 
    cursor = self.getCursor()
    try:
      retval = annotation.getChildren (ch, annoid, self, cursor)
    finally:
      self.closeCursor ( cursor )

    return retval

  
  # getAnnoObjects:  
  #    Return a list of annotation object IDs
  #  for now by type and status
  def getAnnoObjects ( self, ch, args ):
    """Return a list of annotation object ids that match equality predicates.  
      Legal predicates are currently:
        type
        status
      Predicates are given in a dictionary.
    """

    # legal equality fields
    eqfields = ( 'type', 'status' )
    # legal comparative fields
    compfields = ( 'confidence' )

    # start of the SQL clause
    sql = "SELECT annoid FROM {}".format(ch.getAnnoTable('annotation'))
    clause = ''
    limitclause = ""

    # iterate over the predicates
    it = iter(args)
    try: 

      field = it.next()

      # build a query for all the predicates
      while ( field ):

        # provide a limit clause for iterating through the database
        if field == "limit":
          val = it.next()
          if not re.match('^\d+$',val): 
            logger.warning ( "Limit needs an integer. Illegal value:%s" % (field,val) )
            raise OCPCAError ( "Limit needs an integer. Illegal value:%s" % (field,val) )

          limitclause = " LIMIT %s " % (val)

        # all other clauses
        else:
          if clause == '':
            clause += " WHERE "
          else:  
            clause += ' AND '

          if field in eqfields:
            val = it.next()
            if not re.match('^\w+$',val): 
              logger.warning ( "For field %s. Illegal value:%s" % (field,val) )
              raise OCPCAError ( "For field %s. Illegal value:%s" % (field,val) )

            clause += '%s = %s' % ( field, val )

          elif field in compfields:

            opstr = it.next()
            if opstr == 'lt':
              op = ' < '
            elif opstr == 'gt':
              op = ' > '
            else:
              logger.warning ( "Not a comparison operator: %s" % (opstr) )
              raise OCPCAError ( "Not a comparison operator: %s" % (opstr) )

            val = it.next()
            if not re.match('^[\d\.]+$',val): 
              logger.warning ( "For field %s. Illegal value:%s" % (field,val) )
              raise OCPCAError ( "For field %s. Illegal value:%s" % (field,val) )
            clause += '%s %s %s' % ( field, op, val )


          #RBTODO key/value fields?

          else:
            raise OCPCAError ( "Illegal field in URL: %s" % (field) )

        field = it.next()

    except StopIteration:
      pass
 

    sql += clause + limitclause + ';'

    cursor = self.getCursor()

    try:
      cursor.execute ( sql )
      annoids = np.array ( cursor.fetchall(), dtype=np.uint32 ).flatten()
    except MySQLdb.Error, e:
      logger.error ( "Error retrieving ids: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise
    finally:
      self.closeCursor( cursor )

    return np.array(annoids)


  def writeCuboid(self, ch, corner, resolution, cuboiddata):
    """Write an image through the Web service"""

    # dim is in xyz, data is in zyx order
    dim = cuboiddata.shape[::-1]

    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    zoffset = corner[2]%zcubedim
    yoffset = corner[1]%ycubedim
    xoffset = corner[0]%xcubedim

    databuffer = np.zeros ([znumcubes*zcubedim, ynumcubes*ycubedim, xnumcubes*xcubedim], dtype=cuboiddata.dtype )
    databuffer [ zoffset:zoffset+dim[2], yoffset:yoffset+dim[1], xoffset:xoffset+dim[0] ] = cuboiddata 

    self.kvio.startTxn()
 
    try:
      for z in range(znumcubes):
        for y in range(ynumcubes):
          for x in range(xnumcubes):

            key = ocplib.XYZMorton ([x+xstart,y+ystart,z+zstart])
            cube = self.getCube (ch, key, resolution, update=True)
            # overwrite the cube
            cube.overwrite ( databuffer [ z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim ] )
            # update in the database
            self.putCube (ch, key, resolution, cube)

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()

  def writeTimeCuboid(self, ch, corner, resolution, timerange, cuboiddata):
    """Write an image through the Web service"""

    # dim is in xyz, data is in zyx order
    dim = cuboiddata.shape[::-1][:-1]

    # get the size of the image and cube
    [xcubedim, ycubedim, zcubedim] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    zoffset = corner[2]%zcubedim
    yoffset = corner[1]%ycubedim
    xoffset = corner[0]%xcubedim

    databuffer = np.zeros([timerange[1]-timerange[0]]+[znumcubes*zcubedim, ynumcubes*ycubedim, xnumcubes*xcubedim], dtype=cuboiddata.dtype )
    databuffer[:, zoffset:zoffset+dim[2], yoffset:yoffset+dim[1], xoffset:xoffset+dim[0]] = cuboiddata 

    self.kvio.startTxn()
 
    try:
      for z in range(znumcubes):
        for y in range(ynumcubes):
          for x in range(xnumcubes):
            for timestamp in range(timerange[0], timerange[1], 1):

              zidx = ocplib.XYZMorton([x+xstart,y+ystart,z+zstart])
              cube = self.getTimeCube(ch, zidx, timestamp, resolution, update=True)
              # overwrite the cube
              cube.overwrite(databuffer[timestamp-timerange[0], z*zcubedim:(z+1)*zcubedim, y*ycubedim:(y+1)*ycubedim, x*xcubedim:(x+1)*xcubedim])
              # update in the database
              self.putTimeCube(ch, zidx, timestamp, resolution, cube)

    except:
      self.kvio.rollback()
      raise

    self.kvio.commit()


  def mergeGlobal(self, ids, mergetype, res):
    """Global merge routine.  Converts a list of ids into the merge id at a given resolution.
       This will collapse all exceptions for the voxels for the merged ids."""

    # get the size of the image and cube
    resolution = int(res)
    # ID to merge annotations into 
    mergeid = ids[0]
    
    # Turned off for now( Will's request)
    #if len(self.annoIdx.getIndex(int(mergeid),resolution)) == 0:
    #  raise OCPCAError(ids[0] + " not a valid annotation id. This id does not have paint data")
  
    # Get the list of cubeindexes for the Ramon objects
    listofidxs = set()
    addindex = []
    # RB!!!! do this for all ids, promoting the exceptions of the merge id
    for annid in ids:
      if annid== mergeid:
        continue
      # Get the Annotation index for that id
      curindex = self.annoIdx.getIndex(ch, annid,resolution)
      # Final list of index which has to be updated in idx table
      addindex = np.union1d(addindex,curindex)
      # Merge the annotations in the cubes for the current id
      listofidxs = set(curindex)
      for key in listofidxs:
        cube = self.getCube (ch, key,resolution)
        if ch.getExceptions() == ocpcaproj.EXCEPTION_TRUE:
          oldexlist = self.getExceptions( ch, key, resolution, annid ) 
          self.kvio.deleteExceptions ( ch, key, resolution, annid )
        #
        # RB!!!!! this next line is wrong!  the problem is that
        #  we are merging all annotations.  So at the end, there
        #  need to be no exceptions left.  This line will leave
        #  exceptions with the same value as the annotation.
        #  Just delete the exceptions
        #
        # Ctype optimized version for mergeCube
        ocplib.mergeCube_ctype ( cube.data, mergeid, annid )
        self.putCube ( ch, key, resolution, cube )
        
      # Delete annotation and all it's meta data from the database
      #
      # RB!!!!! except for the merge annotation
      if annid != mergeid:
        try:
          # reordered because paint data no longer exists
          #KL TODO Merge for all resolutions and then delete for all of them.
          self.annoIdx.deleteIndexResolution(ch, annid,resolution)
          #self.annoIdx.deleteIndex(annid,resolution)
          self.deleteAnnotation (ch, annid, '' )
        except:
          logger.warning("Failed to delete annotation {} during merge.".format(annid))
    self.annoIdx.updateIndex(ch, mergeid,addindex,resolution)     
    self.kvio.commit()
    
    return "Merged Id's {} into {}".format(ids,mergeid)

  def merge2D(self, ids, mergetype, res, slicenum):
    # get the size of the image and cube
    resolution = int(res)
    print ids
    # PYTODO Check if this is a valid annotation that we are relabeling to
    if len(self.annoIdx.getIndex(ids[0],1)) == 0:
      raise OCPCAError(ids[0] + " not a valid annotation id")
    print mergetype
    listofidxs = set()
    for annid in ids[1:]:
      listofidxs |= set(self.annoIdx.getIndex(annid,resolution))

    return "Merge 2D"

  def merge3D(self, ids, corner, dim, res):
     # get the size of the image and cube
    resolution = int(res)
    dbname = self.proj.getTable(resolution)
    
    # PYTODO Check if this is a valid annotation that we are relabelubg to
    if len(self.annoIdx.getIndex(ids[0],1)) == 0:
      raise OCPCAError(ids[0] + " not a valid annotation id")

    listofidxs = set()
    for annid in ids[1:]:
      listofidxs |= set(self.annoIdx.getIndex(annid,resolution))

      # Perform the cutout
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ]

    # Get the Cutout
    cube = self.cutout(corner,dim,resolution)    
    vec_func = np.vectorize ( lambda x: ids[0] if x in ids[1:] else x )
    cube.data = vec_func ( cube.data )

    self.annotateDense ( corner, resolution, cube )    

    # PYTODO - Relabel exceptions?????

    # Update Index and delete object?
    for annid in ids[1:]:
      #Wself.annoIdx.deleteIndex(annid,resolution)
      print "updateIndex"

    return "Merge 3D"


  def exceptionsCutout ( self, corner, dim, resolution ):
    """Return a list of exceptions in the specified region.
        Will return a np.array of shape x,y,z,id1,...,idn where n is the longest exception list"""
  
    # get the size of the image and cube
    [ xcubedim, ycubedim, zcubedim ] = cubedim = self.datasetcfg.cubedim [ resolution ] 

    # Round to the nearest larger cube in all dimensions
    zstart = corner[2]/zcubedim
    ystart = corner[1]/ycubedim
    xstart = corner[0]/xcubedim

    znumcubes = (corner[2]+dim[2]+zcubedim-1)/zcubedim - zstart
    ynumcubes = (corner[1]+dim[1]+ycubedim-1)/ycubedim - ystart
    xnumcubes = (corner[0]+dim[0]+xcubedim-1)/xcubedim - xstart

    # Build a list of indexes to access                                                                                     
    listofidxs = []
    for z in range ( znumcubes ):
      for y in range ( ynumcubes ):
        for x in range ( xnumcubes ):
          mortonidx = ocplib.XYZMorton ( [x+xstart, y+ystart, z+zstart] )
          listofidxs.append ( mortonidx )

    # Sort the indexes in Morton order
    listofidxs.sort()

    # generate list of ids for query
    sqllist = ', '.join(map(lambda x: str(x), listofidxs))
    sql = "SELECT zindex,id,exlist FROM exc{} WHERE zindex in ({})".format(resolution,sqllist)


    with closing(self.conn.cursor()) as func_cursor:

      # this query needs its own cursor
      try:
        func_cursor.execute(sql)
      except MySQLdb.Error, e:
        logger.warning ("Failed to query exceptions in cutout %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
        raise

      # data structure to hold list of exceptions
      excdict = defaultdict(set)

      prevzindex = None

      while ( True ):

        try: 
          cuboidzindex, annid, zexlist = func_cursor.fetchone()
        except:
          func_cursor.close()
          break

        # first row in a cuboid
        if np.uint32(cuboidzindex) != prevzindex:
          prevzindex = cuboidzindex
          # data for the current cube
          cube = self.getCube ( cuboidzindex, resolution )
          [ xcube, ycube, zcube ] = ocplib.MortonXYZ ( cuboidzindex )
          xcubeoff =xcube*xcubedim
          ycubeoff =ycube*ycubedim
          zcubeoff =zcube*zcubedim

        # accumulate entries and decompress the list of exceptions
        fobj = cStringIO.StringIO ( zlib.decompress(zexlist) )
        exlist = np.load (fobj)

        for exc in exlist:
          excdict[(exc[0]+xcubeoff,exc[1]+ycubeoff,exc[2]+zcubeoff)].add(np.uint32(annid))
          # add voxel data 
          excdict[(exc[0]+xcubeoff,exc[1]+ycubeoff,exc[2]+zcubeoff)].add(cube.data[exc[2]%zcubedim,exc[1]%ycubedim,exc[0]%xcubedim])


    # Watch out for no exceptions
    if len(excdict) != 0:

      maxlist = max([ len(v) for (k,v) in excdict.iteritems() ])
      exoutput = np.zeros([len(excdict),maxlist+3], dtype=np.uint32)

      i=0
      for k,v in excdict.iteritems():
        l = len(v)
        exoutput[i,0:(l+3)] = [x for x in itertools.chain(k,v)]
        i+=1

    # Return None if there are no exceptions.
    else:
      exoutput = None

    return exoutput
