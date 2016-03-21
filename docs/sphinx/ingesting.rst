How to Ingest Data
******************

Prepping The Data
=================

There are two important components to how data should be organized before uploading to the service. First is file hierarchy (how the folders holding data should be organized) which is as follows; all channel specific data is saved in a folder with the name of the channel. For example if you have image data of two mouse cortices, one cortex would be stored in an image channel Cortex1. So, all the data from that imaging would be stored in a folder named Cortex1. In the case of time series data each channel folder should contain sub-folders time0, time1, time2, ..., timeN, each of which contains the image data for that specific time slot. All the channel folders should be stored inside a folder named the same as the token name. Note that the token name you choose must be unique across all projects in NeuroData.

Second is how the files themselves are organized. Currently the auto-ingest service only supports tiff, tif, and png files. The files should be organized such that there is a tiff/png/tif for each Z-slice, with each named the slice number up to 4 digits. For example if there was a imaging set with 405 image slices in tif form, the image channel folder(s) should have files labeled 0000.tif through 0404.tif. Files must not have a prefix or suffix to the number of the slice. If the slice number starts at a value other than 0000, please specify that starting value as the Z offset.

.. figure:: ../images/ingesting_directory.png
    :width: 450px
    :height: 550px
    :align: center

    This figure illustrated visually how the data should be organized for ingest.

Some common mistakes you can make
=================================

#TODO AE - Expand these
Spaces in channel/project/dataset/token names are not allowed
Special characters in channel/project/dataset/token names not allowed (minus underscore)
Numbering the channel slices incorrectly
If your slice number starts at 1 then mention z-offset as 1. we deal with missing slice numbers
channel types are image/annotation not Image/Annotation
if dataset exists use a different name or you have changes parameters
you can send multiple channels at once but channels need to be in the same dataset, check this
check if you have the lastest version of ndio, pip install -U ndio
check your dir strucute proj/channel/slice
HTTP accessible urls(have to go over the firewall) do a wget on your slice to check if this works

Help Section
============

#TODO AE
How do I check the image size, I am unssure. Use indentify on unix command line
How do I check the datatype. Again use identify on command line
How do I name my projects/datasets/token - Repeat it here <lab-name>year
How do I check if my data is publicly accessible - do a curl/wget


S3 Bucket Upload
================

If you are uploading data through an amazon s3 bucket, this additional step is necessary for us to be able to access the data. In order to make the data in your S3 bucket public and available over HTTP you need to add this bucket policy (in the permissions tab of properties) and save it. Make sure to replace the "examplebucket" in the sample json with your bucket name. When including the data url be sure to set the data_url as http://<example-bucket>.s3.amazonaws.com/ (with example-bucket being replaced with your bucket name).

.. code-block:: json

    {
      "Version":"2012-10-17",
        "Statement":[
          {
            "Sid":"AddPerm",
            "Effect":"Allow",
            "Principal": "*",
            "Action":["s3:GetObject"],
            "Resource":["arn:aws:s3:::examplebucket/*"]
          }
        ]
    }

Uploading
=========

Overview
++++++++

This section will initially address how to upload one channels worth of material. Located in the auto-ingest folder in the ingest folder of ndstore is a file named generatejson.py (https://github.com/neurodata/ndstore/blob/master/ingest/autoingest/generatejson.py). To upload your data edit the hard-coded values in the code to reflect your data, being sure to specify that you are trying to put data to http://openconnecto.me and your DataURL is http accessible (if it is not the script will fail). The editable portion of the script is below the "Edit the below values" and above the "Edit above here" comment. Once the script has run you do not need to maintain a connection to the script. The script can be run simply by calling "python2 generatejson.py" on the script (using python 2.7). In the event that more than one channels worth of data needs to be ingested at once, the service supports this operation as well. To add channels, add additional create channel calls to the AutoIngest object before posting the data. The AutoIngest object is part of NeuroData's python library, Ndio, which must be installed prior to using the script.

Explanation of Additional Terms
+++++++++++++++++++++++++++++++
The :ref:`data model <datamodel>` holds an explanation of the majority of the terms encountered when editing the generatejson.py script, however some extra terms that are not enumerated in that explanation are included here.

.. function:: Scaling

   Scaling is the orientation of the data being stored, 0 corresponds to a Z-slice orientation (as in a collection of tiff images in which each tiff is a slice on the z plane) and 1 corresponds to an isotropic orientation (in which each tiff is a slice on the y plane).

   :Type: INT
   :Default: 1

.. function:: Exceptions

   Exceptions is an option to enable the possibility for annotations to contradict each other (assign different values to the same point). 1 corresponds to True, 0 corresponds to False.

   :Type: INT
   :Default: 0

.. function:: Read Only

   This option allows the user to control if, after the initial data commit, the channel is read-only. Generally this is suggested with data that will be publicly viewable. 1 corresponds to True, 0 corresponds to False.

   :Type: INT
   :Default: 0

.. function:: Data URL

   This url points to the root directory of the files, meaning the folder identified by the token name should be in the directory being pointed to. Dropbox (or any data requiring authentication to download such as non-HTTP s3) is not an acceptable HTTP Server. To make data in s3 available for ingest through out service, please see the instructions above.

   :Type: AlphaNumeric
   :Default: None
   :Example: http://ExampleServer.University.edu/MyData/UploadData/

.. function:: File Format

   File format refers to the overarching kind of data, as in slices (normal image data) or catmaid (tile-based).

   :Type: {SLICE, CATMAID}
   :Default: None
   :Example: SLICE

.. function:: File Type

   File type refers to the specific type of file that the data is stored in, as in, tiff, png, or tif.

   :Type: AlphaNumeric
   :Default: None
   :Example: tiff

Unsupported Image Types
=======================

We currently do not support 3-D tiffs.
