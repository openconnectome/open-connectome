NeuroData Types
***************

.. _nd-channeltype:

Channel Types
=============

Channels in NeuroData are individual entites inside projects. You can have multiple same and different channel types inside the same project. Each channel has its unique properties. For example, annotation  channels allow your to store annotation paint data and metadata using RAMON. Image channels allow you to store image data which is 3-dimenisonal in xyz dimensions. Timeseries channels allow you to store time data which is 4-dimenisonal in xyz+time dimensions.

=================   ===============
Channel Type        NeuroData Value
=================   ===============
Image               image
Timeseries          timseries
Annotation          annnotation
=================   ===============

.. _nd-datatype:

Data Types
==========

Each channel has an associated datatype. The datatype of the channel represent the type of data stored in that channel. For example, an image channel which has 8-bit data will be of the datatype uint8. A probablity map which has floating point data will be of the type float32. A 32-bit image will be a color image with the 8-bit quantities for each R, G, B, and A. 

===============     ===============
Data Type           NeuroData Value
===============     ===============
8-bit Integer       uint8
16-bit Integer      uint16
32-bit RGBA         uint32
64-bit RGBA         uint64
32-bit Float        float32
===============     ===============

.. _nd-combo:

Possible Combination of Channel Types and Data Types
=====================================================

NeuroData allows certain set combinations of the above mentioned channel type and data types. We support the following combinations.

=============       =======================================
Channel Type        Possible Data Types
=============       =======================================
Image               uint8, uint16, uint32, uint64, float32
Timeseries          uint8, uint16, float32
Annotation          uint32, uint64
=============       =======================================

