#!/usr/bin/python

import MySQLdb
import sys
 
con = None
con = MySQLdb.connect (host = 'localhost', user = 'brain', passwd = '88brain88', db = 'ocpconfig' )
cur = con.cursor()
cur.execute("select dataset,ximagesize,yimagesize,startslice,endslice,zoomlevels,zscale,startwindow,endwindow,starttime,endtime from datasets;")
rows = cur.fetchall()
con2 =  MySQLdb.connect('', 'brain','88brain88', 'ocpdjango');
cur2 = con2.cursor()
for row in rows:
    sql="INSERT INTO {0} (dataset_name, ximagesize, yimagesize, startslice, endslice, zoomlevels, zscale, startwindow, endwindow, starttime, endtime,dataset_description) VALUES (\'{1}\',{2},{3},{4},{5},{6},{7}, {8},{9},{10},{11},\'{12}\')".format ('datasets', row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10],row[0] )
    print sql
    try:
        cur2.execute(sql)
    except MySQLdb.Error, e:
        print "Failed to insert dataset " + row[0]
con2.commit() 
con2.close()
con.close()
