#!/usr/bin/python

import MySQLdb
import sys
 
#Get the data from ocpconfig.project
con = None
con = MySQLdb.connect (host = 'localhost', user = 'brain', passwd = '88brain88', db = 'ocpconfig' )
cur = con.cursor()
sql = "SELECT token, openid, host, project, datatype, dataset, dataurl, readonly, exceptions, resolution , public, kvserver, kvengine, propagate from {}".format('projects')
cur.execute(sql)
rows = cur.fetchall()
con.close()


con2 =  MySQLdb.connect('localhost', 'brain','88brain88', 'ocpdjango');
cur2 = con2.cursor()
for row in rows:

    token_name= row[0]
    token_description= row[0]
    openid = row[1]
    host= row[2]
    project_name=row[3].strip()
    project_description = row[3]
    datatype = row[4]
    dataset_name =row[5]
    dataurl=row[6]
    readonly=row[7]
    exceptions=row[8]
    resolution = row[9]
    public = row[10]
    kvserver=row[11]
    kvengine=row[12]
    propagate=row[13]
    userid = 1
    if datatype==1:
        overlayproject=None
    else:
        overlayproject=dataset_name
        
    overlayserver='http://openconnecto.me/ocp'
    #get the dataset id
    sql2 = "SELECT id,dataset_name from datasets where dataset_name= \'{}\'".format(dataset_name)
    try:
        cur2.execute(sql2)
        row3 = cur2.fetchone()
        if ( row3 != None):
            [dataset_id,name]= row3
            sql = "INSERT INTO {0} ( project_name, project_description,user_id,dataset_id,datatype,overlayproject,overlayserver, resolution, exceptions,host, kvengine,kvserver,propagate ) VALUES (\'{1}\ ',\'{2}\',{3},{4},{5},\'{6}\',\'{7}\',{8}, {9},\'{10}\',\'{11}\',\'{12}\',{13})".format ('projects',  project_name.rstrip(), project_description,userid,int(dataset_id),datatype,overlayproject,overlayserver, resolution, exceptions,host, kvengine,kvserver,propagate  )
            cur2.execute(sql)

            sql3= "INSERT INTO {0} (token_name, token_description, project_id, readonly, public) VALUES (\'{1}\',\'{2}\',\'{3}\',{4},{5})".format ('tokens', token_name, token_description,project_name,readonly,public )
            cur2.execute(sql3)
    except:
        print "failed to fetch " + dataset_name
        print "Failed to insert project " + project_name
    
    
con2.commit() 
con2.close()
#con.close()
