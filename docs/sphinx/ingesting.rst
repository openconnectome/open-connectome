How to Ingest Data
******************

Prepping The Data
=================

There are two important components to how data should be organized before uploading to the service. First is file hierarchy (how the folders holding data should be organized) which is as follows; all channel specific data is saved in a folder with the name of the channel. For example if you have image data of two mouse cortices, one cortex would be stored in an image channel Cortex1. So, all the data from that imaging would be stored in a folder named Cortex1. In the case of time series data each channel folder should contain sub-folders time0000, time0001, time0002, ..., time####, each of which contains the image data for that specific time slot. All the channel folders should be stored inside a folder named the same as the token name. Note that the token name you choose must be unique across all projects in NeuroData.

Second is how the files themselves are organized. Currently the auto-ingest service only supports tiff, tif, and png files. The files should be organized such that there is a tiff/png/tif for each Z-slice, with each named the slice number up to 4 digits. For example if there was a imaging set with 405 image slices in tif form, the image channel folder(s) should have files labeled 0000.tif through 0404.tif. Files must not have a prefix or suffix to the number of the slice. If the slice number starts at a value other than 0000, please specify that starting value as the Z offset.

.. figure:: ../images/ingesting_directory.png
    :width: 450px
    :height: 550px
    :align: center

    This figure illustrated visually how the data should be organized for ingest.

Some common mistakes you can make
=================================

* Special characters and spaces in channel/project/dataset/token names not allowed with the exception of an underscore.
* Numbering the channel slices incorrectly compared to the offset and number of slices defined in the dataset when ingesting.
* Offset (Z value) should match the lowest image file number.
* Channel types are not capitalized, so they should be image/annotation not Image/Annotation.
* Check if the dataset name is already taken, if it is you must use another.
* If you upload multiple channels at once they must all be part of the same dataset.
* Check if you have the lastest version of ndio using "pip install -U ndio".
* Make sure your directory structure is accurate and correctly ordered.
* Make sure your data is HTTP accessible, see below how to check this if you are unsure.
* Make sure the naming of your folders and files has the required leading zeros.

Unsupported Image Types
=======================

We currently do not support 3-D tiffs.

Help Section
============

How do I check the image size of my data?
-----------------------------------------

Use the 'tiffinfo' command in terminal to check datatype on tiff (or tif) images, or pnginfo for png images, to get a variety of data about a particular image file including image size.

How do I check the datatype?
----------------------------

Unfortunately there is no universally acceptable answer to this question, as everyone's data types vary based on how the image was saved. The most common answer to this is to use the 'tiffinfo' command in terminal to check datatype on tiff (or tif) images, or pnginfo for png images.

How do I name my projects/datasets/token?
-----------------------------------------

Please see naming convections in the :ref:`data model <datamodel>`.

How do I check if my data is publicly accessible?
-------------------------------------------------

The most common way of doing this is by doing a curl or wget on the data. For example, if you have your data stored on a server with a name space of MyServer on your network, with your publicly accessible folder named MyPublic containing the data, you would attempt to access http://MyServer/MyPublic/TokenName/ChannelName/###.tif where TokenName and ChannelName are replaced by the token and channel names used in your data and the pound signs are replaced with whichever slice number is desired. The command in terminal would be "curl http://MyServer/MyPublic/TokenName/ChannelName/###.tif" and if there is a response other than webpage not found the data is accessible.


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

Should you wish to instead host the data temporarily in the NeuroData s3 bucket to ingest it, please contact neurodata for the bucket name and follow the below instructions. First, install the Amazon WebServices command line client. Then navigate to one level above the folder labeled with your token name (in this example called tokenname). Input the following command into your comand line: aws cp tokenname/ --recursive bucketname/yourfolder --acl "bucket-owner-full-control". Finally, when the data has all been uploaded follow the instructions to complete the ingest process with the bucket name in the dataurl being the neurodata bucket name followed by a slash and the folder name provided to you by NeuroData. 

Uploading
=========

Overview
--------

This section will initially address how to upload one channels worth of material. Located in the auto-ingest folder in the ingest folder of ndstore is a file named autoingest.py (https://github.com/neurodata/ndstore/blob/master/ingest/autoingest/autoingest.py). To upload your data edit the hard-coded values in the code to reflect your data, being sure to specify that you are trying to put data to http://openconnecto.me and your DataURL is http accessible (if it is not the script will fail). The editable portion of the script is below the "Edit the below values" and above the "Edit above here" comment. Once the script has run you do not need to maintain a connection to the script. The script can be run simply by calling "python2 autoingest.py" on the script (using python 2.7). In the event that more than one channels worth of data needs to be ingested at once, the service supports this operation as well. To add channels, add additional create channel calls to the AutoIngest object before posting the data. The AutoIngest object is part of NeuroData's python library, Ndio, which must be installed prior to using the script.

Explanation of Additional Terms
-------------------------------

The :ref:`data model <datamodel>` holds an explanation of the majority of the terms encountered when editing the autoingest.py script, however some extra terms that are not enumerated in that explanation are included here.

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
