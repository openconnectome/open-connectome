Scalable database cluster for the spatial analysis and annotation of high-throughput brain imaging data called Neurodata Web Services(formerly called the Open Connectome Project).

[![Neurodata.io](https://img.shields.io/badge/Visit-neurodata.io-ff69b4.svg)](http://neurodata.io/)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.19972.svg)](http://dx.doi.org/10.5281/zenodo.19972)
[![Hex.pm](https://img.shields.io/hexpm/l/plug.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)
[![Docs](https://img.shields.io/badge/Docs-latest-brightgreen.svg)](http://docs.neurodata.io/ndstore/)
[![Build Status](https://travis-ci.org/neurodata/ndstore.svg?branch=microns)](https://travis-ci.org/neurodata/ndstore)

Root directory of the cutout and annotation services.
Major directories include:

  * spdb -- [Spatial Database submodule](https://github.com/neurodata/spdb)
  * webservices -- Webservices module
  * ndproj -- Project Module
  * ramon -- RAMON and Annotation metadata module
  * django -- Django module
  * setup -- Setup instructions
  * test -- Test module
  * examples -- How to use the service
  * util -- Useful common files across the modules
  * ingest -- Scripts to insert datasets into the databases
  * admin -- Scripts to manage the databases
  * ndlib -- [Common library and Ctype accelerations submodule](https://github.com/neurodata/ndlib)
  * docs -- Sphinx documentation for the project
  * cython -- Cython acclerations for the service (Deprecated)
  * scripts -- Useful general purpose scripts
  * onetime -- Misc scripts for the service
  * NOTE: git submodule init and git submodule update for all submodules

#### Architecture

![](./docs/images/neurodata_cluster.png)

#### Benchmarks

The benchmarks were performed on AWS EC2 instance type i2.8xlarge with a MySQL backend.

##### Read Throughput

![](./docs/images/neurodata_read_throughput.png)

##### Write Throughput

![](./docs/images/neurodata_write_throughput.png)
