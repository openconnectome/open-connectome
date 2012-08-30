import numpy as np
import array
import cStringIO
import MySQLdb

import empaths
import dbconfig
import zindex
import emcaproj

#
#  AnnotateIndex: Maintain the index in the database
# AUTHOR: Priya Manavalan

class AnnotateIndex:

  # Constructor 
  #
   def __init__(self,dbconf,emcaproj):
      self.dbcfg = dbconf
      self.proj = emcaproj
      
      dbinfo = self.proj.getDBHost(), self.proj.getDBUser(), self.proj.getDBPasswd(), self.proj.getDBName()

    # Connection info                                                                                                
      try:
         self.conn = MySQLdb.connect (host = self.proj.getDBHost(),
                                      user = self.proj.getDBUser(),
                                      passwd = self.proj.getDBPasswd(),
                                      db = self.proj.getDBName())
      except:
         raise AnnError ( dbinfo )
    
    # How many slices?                                                                                               
      [ self.startslice, endslice ] = self.dbcfg.slicerange
      self.slices = endslice - self.startslice + 1
      pass
   
   def __del__(self):
      """Destructor"""
      pass
   
   #
   # getIndex -- Retrieve the index for the annotation with id
   #
   def getIndex ( self, entityid, resolution ):
    #Establish a connection
      cursor = self.conn.cursor ()

  # PYTODO rename cube to cubes
     
    #get the block from the database                                            
      sql = "SELECT cube FROM " + self.proj.getIdxTable(resolution) + " WHERE annid\
 = " + str(entityid)
      #print sql
      try:
         cursor.execute ( sql )
      except MySQLdb.Error, e:
         print "Failed to retrieve cube %d: %s. sql=%s" % (e.args[0], e.args[1], sql)
         assert 0
      except BaseException, e:
         print "DBG: SOMETHING REALLY WRONG HERE", e
         
      row = cursor.fetchone ()
      cursor.close()
     
    # If we can't find a index, they don't exist                                
      if ( row == None ):
         return []
      else:
         fobj = cStringIO.StringIO ( row[0] )
         return np.load ( fobj )      

#
# Update Index Dense - Updated the annotation database with the given hash index table
#
   def updateIndexDense(self,index,resolution):
      """Updated the database index table with the input index hash table"""

      cursor = self.conn.cursor ()

      for key, value in index.iteritems():
         cubelist = list(value)
         cubeindex=np.array(cubelist)
         #print cubeindex
         
         curindex = self.getIndex(key,resolution)
         
    #Used for testing
         #print ("Current Index", curindex )
         if curindex==[]:
            sql = "INSERT INTO " +  self.proj.getIdxTable(resolution)  +  "( annid, cube) VALUES ( %s, %s)"
            
            try:
               fileobj = cStringIO.StringIO ()
               np.save ( fileobj, cubeindex )
          #     print sql, key
               cursor.execute ( sql, (key, fileobj.getvalue()))
            except MySQLdb.Error, e:
               print "Error inserting exceptions %d: %s. sql=%s" % (e.args[0], e.args[1], sql)
               assert 0
            except BaseException, e:
               print "DBG: SOMETHING REALLY WRONG HERE", e
         else:
             #Update index to the union of the currentIndex and the updated index                                                               
            newIndex=np.union1d(curindex,cubeindex)
#            print "Updating Index for annotation ",key, " to" , newIndex
            
         #update index in the database                                                                                                      
            sql = "UPDATE " + self.proj.getIdxTable(resolution) + " SET cube=(%s) WHERE annid=" + str(key)
            try:
               fileobj = cStringIO.StringIO ()
               np.save ( fileobj, newIndex )
               cursor.execute ( sql, (fileobj.getvalue()))
            except MySQLdb.Error, e:
               print "Error updating exceptions %d: %s. sql=%s" % (e.args[0], e.args[1], sql)
               assert 0
               
      cursor.close()
<<<<<<< HEAD
      self.conn.commit()
              #self.updateIndex(key,cubeIdx,resolution)

   #
   #deleteIndex:
   #   Delete the index for a given annotation id
   #
   def deleteIndex(self,annid,resolutions):
      """delete the index for a given annid""" 
      cursor = self.conn.cursor ()
=======
>>>>>>> 2cd2ce566b4f69b79009068aa81bea408470a666

      #delete Index table for each resolution
      for res in resolutions:
         sql = "DELETE FROM " +  self.proj.getIdxTable(res)  +  " WHERE annid=" + str(annid)
         print sql
         
         try:
            cursor.execute ( sql )
         except MySQLdb.Error, e:
            print "Error deleting the index %d: %s. sql=%s" % (e.args[0], e.args[1], sql)
            assert 0
         except BaseException, e:
            print "DBG: SOMETHING REALLY WRONG HERE", e
      cursor.close()
      self.conn.commit()
# end AnnotateIndex
