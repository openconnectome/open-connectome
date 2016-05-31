.. meta::
   :description: Official documentation for NeuroData Web Services: Scalable database cluster for the spatial analysis and annotation of high-throughput brain imaging data
   :keywords: annotation, tracing, neuroscience, object detection
.. title::
   NeuroData

.. raw:: html

	<h1>NeuroData Web Services: Scalable database cluster for the spatial analysis and annotation of high-throughput brain imaging data</h1>
	<br>

NeuroData provides a scalable database cluster for the spatial analysis and annotation of high-throughput brain imaging data for 3D image stacks, time-series and multi-channel data (e.g., electron microscopy, array tomography, CLARITY, histology, and multimodal MRI data). The system is designed primarily for workloads that build connectomes---neural connectivity maps of the brain---using the parallel execution of computer vision algorithms on high-performance compute clusters. These services and open science data sets are publicly available at neurodata.io.

The system design inherits much from NoSQL scale-out and data-intensive computing architectures. We distribute data to cluster nodes by partitioning a spatial index. We direct I/O to different systems---reads to parallel disk arrays and writes to solid-state storage---to avoid I/O interference and maximize throughput. All programming interfaces are RESTful Web services, which are simple and stateless, improving scalability and usability. We include a performance evaluation of the production system, highlighting the effectiveness of spatial data organization.

.. figure:: images/neurodata_example.png
    :height: 500px  
    :width: 1000px
    :align: center
    :alt: Spatially Registered Databases in NeuroData. 
    
    Spatially Registered Databases in NeuroData   

    Electron microscopy images of a mouse somatosensory cortex (left), a probability map output by a computer vision algorithm that detects membranes (center), and an annotation database that describes axons and dendrites (right).

.. raw:: html

  <div>
    <img style="width:30px;height:30px;vertical-align:middle">
    <span style=""></span>
    <IMG SRC="_static/GitHub.png" height="50" width="50"> <a href="https://github.com/neurodata/ndstore/zipball/master"> [ZIP]   </a>  
    <a image="_static/GitHub.png" href="https://github.com/neurodata/ndstore/tarball/master">[TAR.GZ] </a></p>
  </div>

.. sidebar:: NeuroData Contact Us

   If you have questions about NeuroData, or have data to store, please let us know: support@neurodata.io

.. toctree::
   :maxdepth: 1
   :caption: NeuroData Documentation

   sphinx/introduction
   sphinx/datamodel
   sphinx/console
   sphinx/ingesting
   sphinx/config
   sphinx/faq

.. toctree::
   :maxdepth: 1
   :caption: API Documentation
   

   api/nd_types
   api/info_api
   api/public_api
   api/data_api
   api/slice_api
   api/ramon_api
   api/propagate_api
   api/stats_api
   api/json_api
   api/overlay_api
   api/tile_api
   api/graphgen_api
   api/nifti_api
   api/swc_api

.. toctree::
   :maxdepth: 1
   :caption: Further Reading

   api/functions
   Mailing List <https://groups.google.com/forum/#!forum/ocp-support/> 
   Github repo <https://github.com/neurodata/ndstore>
   Release Notes <https://github.com/neurodata/ndstore/releases/>

All of the APIs enumerated here are RESTful calls that are used via the browser or calls to the web service. For additional usage information see online RESTful documentation.

If you use NeuroData or its data derivatives, please cite:
  R Burns, K Lillaney, E Perlman, P Manavalan, JT Vogelstein (2015). ocp v0.7. Zenodo. 10.5281/zenodo.15974 `zenodo <https://zenodo.org/record/15974?ln=en#.VYyl-XUVhBc>`_ `bibtex <https://zenodo.org/record/15974?ln=en#.VYyjE3UVhBc>`_

  R Burns, K Lillaney, D R Berger, L Grosenick, K Deisseroth, R C Reid, W Gray Roncal, P Manavalan, D D Bock, N Kasthuri, M Kazhdan, S J Smith, D Kleissas, E Perlman, K Chung, N C Weiler, J Lichtman, A S Szalay, J T Vogelstein, and R J Vogelstein. The open connectome project data cluster: scalable analysis and vision for high-throughput neuroscience. SSDBM, 2013 `acm <http://dl.acm.org/citation.cfm?id=2484870>`_ `bibtex <http://dl.acm.org/citation.cfm?id=2484870>`_
