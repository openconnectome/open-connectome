Data Model
**********

.. _datamodel:

Assumptions
===========

The assumption is that the person reading has no experience with our service before this point, but has a sufficient knowledge of basic imaging terms, as in they understand what a pixel is. Second, this document is written primarily for neuroscientists to become acquainted with what our service can do or does. Finally, it is assumed that the person reading this has sufficient knowledge of how imaging works to know that the image sizes for a given research effort must be consistent.

Overview
========

Our data model for image datasets is composed of the following components:
* Dataset: containing metadata required to efficiently store, visualize, and analyze data for a set of projects; it effectively defines the dataspace
* Project: is a database storing a collection of channels
* Token: a name for a project, a project can have multiple tokens, each with different permissions (eg, read vs. write)
* Channel: is a collection of tables, including the actual images, as well as metadata

To understand the relationship between the above 4 different components of the data model, consider the following example.
* We collect a large multi-modal MRI dataset, and registered each image into MNI152 space. The dataset would contain the details of MNI152 (number of voxels, resolution, etc.). Each subject gets her own project. For the first subject, let’s create a token pointing to that project called “Subject1”, and let’s give that token write access.
* Each channel for this project corresponds to a different modality. For example, the T1 image might be the first channel, called “T1”. So, to access that channel, we pair the token with the channel name: ‘\Subject1\T1\’. The T1 channel happens to be a 3D image stack. Let’s say we also got an fMRI scan from that subject, also co-registered to MNI152 space. We can then make another channel called ‘fMRI’ containing all the fMRI data and metadata. Note that this is actually 3D+time data, which is no problem to store within a given channel. Finally, assume we also have Diffusion MRI data associated with that subject. So, we can generate another channel called “DTI” to store that data and metadata. Although DTI data is not typically thought of as time-series data, it is 4D, so we could store it as a time-series channel.
* Now, imagine from the DTI data, we created a fractional anisotropy map. We could make a new channel, called “FA”, and put it there. Similarly, imagine from the fMRI we created a general linear model, we could again create a new channel, “GLM”, and put the coefficients in there.
* The advantage of having a data model is that all of the data and metadata can be captured and stored together, which makes visualization, analysis, and reproducibility much simpler.

.. figure:: ../images/datamodel_simple.png
    :width: 500px
    :height: 200px
    :align: center

    This is a simple example of the data model, consisting of one example of each component.


.. figure:: ../images/datamodel_complex.png
    :width: 800px
    :height: 400px
    :align: center

    This is a complex example of the data model, consisting of multiple projects, tokens, and databases.


Dataset Attributes
==================

.. function:: Dataset Name

   Dataset Name is the overarching name of the research effort. Standard naming convention is to do LabNamePublicationYear or LeadResearcherCurrentYear.

   :Type: AlphaNumeric
   :Default: None
   :Example: kasthuri11

.. function:: Image Size

   Image size is the pixel count dimensions of the data. For example is the data is stored as a series of 100 slices each 2100x2000 pixel TIFF images, the X,Y,Z dimensions are (2100, 2000, 100).

   :Type: [INT,INT,INT]
   :Default: None
   :Example: [2100,2000,100]

.. function:: Voxel Resolution

    Voxel Resolution is the voxel scale per unit pixel. We store X,Y,Z voxel resolution separately.

   :Type: [FLOAT,FLOAT,FLOAT]
   :Default: [0.0,0.0,0.0]

.. function:: Offset Value

   If your data is not well aligned and there is "excess" image data you do not wish to examine, but are present in your images, offset is how you specify where your actual image starts. Offset is provided a pixel coordinate offset from origin which specifies the "actual" origin of the image. The offset is for X,Y,Z dimensions. This offset should also be reflective of your file names, if you start you file numbers at 0002.tif your offset should be (0,0,2).

   :Type: [INT,INT,INT]
   :Default: [0,0,0]

.. function:: Time Range

   Time Range is a parameter to support storage of Time Series data, so the value of the tuple is a 0 to X range of how many images over time were taken. It takes 2 inputs timeStepStart and timeStepStop.

   :Type: [INT,INT]
   :Default: [0,0]
   :Example: [0,600]

.. function:: Scaling Levels

   Scaling levels is the number of levels the data is scalable to (how many zoom levels are present in the data). The highest resolution of the data is at scaling level 0, and for each level up the data is down sampled by 2x2 (per slice). To learn more about the sampling service used, visit the :ref:`the propagation <nd-propagation>` service page.

   :Type: INT
   :Default: 0

.. function:: Scaling Choices

   Scaling Choices represent the orientation of the data being stored, Z Slices corresponds to a Z-slice orientation (as in a collection of tiff images in which each tiff is a slice on the z plane) and Isotropic corresponds to an isotropic orientation (in which each tiff is a slice on the y plane).

   :Type: {Z Slices, Isotropic}
   :Default: Z Slices

Project Attributes
==================

.. function:: Project Name

   Project name is the specific project within a dataset's name. If there is only one project associated with a dataset then standard convention is to name the project the same as its associated dataset.

   :Type: AlphaNumeric
   :Default: None
   :Example: kashturi11

.. function:: Public Project

   This option allows users to specify if they want the project/channels to be publicly viewable/search-able.

   :Type: {TRUE, FALSE}
   :Default: FALSE

.. function:: Host Server

   This option allows users to specify which server their data is being stored on, this is relevent only to users that are trying to link to existing databases on a particular server.

   :Type: AlphaNumeric
   :Default: default

.. function:: KV Engine

   This option allows users to specify what engine their KV data should be store in, this is not relevant for most users.

   :Type: AlphaNumeric
   :Default: default

.. function:: KV Server

   This option allows users to specify what server their KV data should be store on, this is not relevant for most users.

   :Type: AlphaNumeric
   :Default: default

Token
=====

.. function:: Token Name

   The token name is the default token. If you do not wish to specify one, a default one will be created for you with the same name as the project name. However, if the project is private you must specify a token. Note that token names must be unique across all projects stored in NeuroData, both private and public.

   :Type: AlphaNumeric
   :Default: None
   :Example: kashturi11

.. function:: Public Token

   Public tokens are search-able by anyone using the service through the console page, private (not public) tokens are not.

   :Type: {TRUE, FALSE}
   :Default: FALSE

Channel Attributes
==================

.. function:: Channel Name

   Channel Name is the specific name of a specific series of data. Standard naming convention is to do ImageTypeIterationNumber or NameSubProjectName.

   :Type: AlphaNumeric
   :Default: None
   :Example: image1

.. function:: Data Type

   The data type is the storage method of data in the channel. It can be uint8, uint16, uint32, uint64, or float32. If you wish to learn more about our supported data types visit :ref:`the NeuroData datatypes page. <nd-datatype>`

   :Type: {uint8, uint16, uint32, uint64, float32}
   :Default: None

.. function:: Channel Type

   The channel type is the kind of data being stored in the channel. It can be image, annotation, or timeseries. If you wish to learn more about our supported channel types visit :ref:`the NeuroData datatypes page. <nd-channeltype>`

   :Type: {image, annotation, timeseries}
   :Default: None

.. function:: Exception Enabled

   Exceptions is an option to enable the possibility for annotations to contradict each other (assign different values to the same point).

   :Type: {TRUE,FALSE}
   :Default: TRUE

.. function:: Base Resolution

   Resolution is the starting resolution of the data being uploaded to the channel.

   :Type: INT
   :Default: 0

.. function:: Window Range

   Window range is the maximum and minimum pixel values for a particular image. This is used so that the image can be displayed in a readable way for viewing through RESTful calls.

   :Type: [INT,INT]
   :Default: [0,0]
   :Example: [0,1100]

.. function:: Read Only

   This option allows the user to control if, after the initial data commit, the channel is read-only. Generally this is suggested with data that will be publicly viewable.

   :Type: {TRUE,FALSE}
   :Default: TRUE

.. function:: Propagated Status

   The propagation status enumerates to the user what the current state of the propagation service is for the current project. To learn more about the propagation service vist :ref:`the documentation. <nd-propagation>`

   :Type: {PROPAGATED, NOT PROPAGATED}
   :Default: NOT PROPAGATED
