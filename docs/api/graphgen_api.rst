GrahpGen API
**************

.. _graphgen-get:

getGraph
--------

.. http:get:: (string:server_name)/nd/ca/(string:token_name)/(string:channel_name)/(string:graph_type)/(int:Xmin)/,int:Xmax)/(int:Ymin),(int:Ymax)/(int:Zmin),(int:Zmax)/

   :synopsis: Get the graph of neuron RAMON objects, each neuron is a node and synapses between these neurons are represented by vertices. The graph generated is unweighted and has no direction. Graphs are created by doing a spatial cutout of the annotation data, finding the unique ids of the annotations present, traversing the RAMON database for appropriate values, and generating a graph. 

   :param server_name: Server Name in NeuroData. In the general case this is openconnecto.me.
   :type server_name: string
   :param token_name: Token Name in NeuroData.
   :type token_name: string
   :param channel_name: Channel Name in NeuroData.
   :type channel_name: string
   :param graph_type: *Optional* The type of graph to be returned, most major types supported.
   :type graph_type: string
   :param Xmin, Ymin, Zmin: The starting dimension(s) of the cutout.
   :type Xmin, Ymin, Zmin: int
   :param Xmax, Ymax, Zmax: The ending dimension(s) of the cutout.
   :type Xmax, Ymax, Zmax: int

   :statuscode 200: No error
   :statuscode 404: Error in the syntax or file format
