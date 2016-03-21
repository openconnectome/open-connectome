Propagate APIs
***************

.. _nd-propagation:

Propagation Service
===================

NeuroData allows only downsampling of data via a service called Propagation. This service does not upsample your data. You can post to a specific resolution and call on the :ref:`set propagation service <propagate-set>` to downsample your data in the background. When your data is under propagation, the project is locked and you cannot post data to it. This is done to maintain the consistency of data across different resolutions. You can check the status of your project via the :ref:`get propagation service <propagate-get>`. Both these services return values which have signfies something. You can use the value reference table below to idenitfy the propgation state of your project.
*WARNING: It make take quite a while for propagation of some projects which are big. Please be patient.*

===================     ===============
Propagation Value       NeuroData Value
===================     ===============
Not Propagated          0
Under Propagation       1
Propagated              2
===================     ===============

.. _propagate-get:

getPropagate
------------

.. http:get:: (string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/getPropagate/

   :synopsis: Get the :ref:`propagation<nd-propagation>` state of the channel.

   :param server_name: Server Name in NeuroData. In the general case this is openconnecto.me.
   :type server_name: string
   :param token_name: Token Name in NeuroData.
   :type token_name: string
   :param channel_name: Channel Name in NeuroData. *Optional*. If missing will use default channel for the token.
   :type channel_name: string

   :statuscode 200: No error
   :statuscode 404: Error in the syntax or file format

.. _propagate-set:

setPropagate
------------

.. http:get:: (string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/setPropagate/(int:propagate_value)/

   :synopsis: Set the :ref:`propagation<nd-propagation>` state of the channel.

   :param server_name: Server Name in NeuroData. In the general case this is openconnecto.me.
   :type server_name: string
   :param token_name: Token Name in NeuroData.
   :type token_name: string
   :param channel_name: Channel Name in NeuroData. *Optional*. If missing will use default channel for the token.
   :type channel_name: string
   :param propagate_value: 0,1,2
   :param propagate_value: int

   :statuscode 200: No error
   :statuscode 404: Error in the syntax or file format
