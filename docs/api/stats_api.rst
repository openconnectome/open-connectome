Statistics API
***************

.. _stats-overview:

Stats Service
===================

The stats service allows a user to compute basic statistics (mean, standard deviation, etc) for an image dataset. Since image datasets can range from a few gigabytes to a few terabytes, NeuroData doesn't compute statistics directly from the image database. Rather, the stats service provides infrastructure for the end user to generate an image histogram, which is then stored in our database. Computation of statistics is done on the fly, based on the stored image histogram. We expose RESTful Web interfaces to both generate and access the histogram, as well as generate statistics based on a stored histogram.

**Note:** Only **integer** datatypes are supported. We currently do not support generating a histogram for a float32 dataset. Furthermore, only **uint8** and **uint16** datatypes are currently supported due to memory constraints.

Additionally, the image channel must **not** be set read only for the histogram service to generate a histogram.

Histograms
==========

.. _stats-hist:

getHistogram
------------

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/hist/

   :synopsis: Retrieve the histogram for an image dataset from the database.

   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string

   :statuscode 200: Histogram retrieved.
   :statuscode 404: No histogram for this token / channel.
   :statuscode 400: Web argument syntax error.

.. _stats-genhist:

genHistogram
------------

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/genHist/

   :synopsis: Generate a histogram for an image dataset and store it in the database.


   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string

   :statuscode 200: Histogram generation started or queued.
   :statuscode 400: Web argument syntax error or unsupported token / channel type.

Stats
=====

.. _stats-all:

allStatistics
-------------

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/all/

   :synopsis: Retrieve the histogram, mean, standard deviation, min, max, and 1st, 50th, and 99th percentile.


   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string

   :statuscode 200: Histogram and various statistics retrieved.
   :statuscode 400: Web argument syntax error.
   :statuscode 404: No histogram in database for specified token / channel.

.. _stats-mean:

Mean
----

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/mean/

   :synopsis: Calculate the mean of an image dataset from the stored histogram.


   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string

   :statuscode 200: Mean calculated and returned.
   :statuscode 400: Web argument syntax error.
   :statuscode 404: No histogram in database for specified token / channel.

.. _stats-std:

Standard Deviation
------------------

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/std/

   :synopsis: Calculate the standard deviation of an image dataset from the stored histogram.


   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string

   :statuscode 200: Standard deviation calculated and returned.
   :statuscode 400: Web argument syntax error.
   :statuscode 404: No histogram in database for specified token / channel.

.. _stats-percentile:

Percentile
----------

.. http:get:: (string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/percentile/(decimal:percentile_value)

   :synopsis: Calculate the standard deviation of an image dataset from the stored histogram.


   :param server_name: ND Server Name (typically openconnecto.me)
   :type server_name: string
   :param token_name: ND Token 
   :type token_name: string
   :param channel_name: ND Channel
   :type channel_name: string
   :param percentile_value: Arbitrary percentile expressed as a percent (e.g. 1 for 1%, 95.99 for 95.99%)
   :type percentile_value: decimal

   :statuscode 200: Percentile calculated and returned.
   :statuscode 400: Web argument syntax error.
   :statuscode 404: No histogram in database for specified token / channel.
