Introduction
************

NeuroData provides a scalable database cluster for the spatial analysis and annotation of high-throughput brain imaging data for 3-d electron microscopy image stacks, time-series and multi-channel data. The system is designed primarily for workloads that build connectomes—neural connectivity maps of the brain—using the parallel execution of computer vision algorithms on high-performance compute clusters. These services and open science data sets are publicly available at neurodata.io.

The system design inherits much from NoSQL scale-out and data-intensive computing architectures. We distribute data to cluster nodes by partitioning a spatial index. We direct I/O to different systems—reads to parallel disk arrays and writes to solid-state storage—to avoid I/O interference and maximize throughput. All programming interfaces are RESTful Web services, which are simple and stateless, improving scalability and usability. We include a performance evaluation of the production system, highlighting the effectiveness of spatial data organization.

.. figure:: ../images/nd_cluster.png
    :align: center
    :width: 1000px
    :height: 500px
    :alt: NeuroData Data Cluster

    NeuroData Data Cluster

    NeuroData Data Cluster and clients as configured to run and visualize the parallel vision workflow for synapse detection
