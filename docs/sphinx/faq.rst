Frequently Asked Questions (FAQ)
********************************

This page will be updated to reflect commonly asked questions to provide a common reference point for questions and answers.  Users may also wish to search for answers on the general `NeuroData Support mailing list <https://groups.google.com/forum/#!forum/ocp-support>`_ archives.

New questions should be asked on  `our support pages <support@neurodata.io>`_.

**What is this project?**

This project is part of `NeuroData <http://neurodata.io>`_.  The following information applies across our projects.

**How do I get started?**

To learn how to navigate the web console please visit our `Adminstrator Console <console>`_ page.

**How do I install NeuroData?**

Please begin with the `configuration <config>`_ page, which should get you up and running in no time.

**How do I contribute my data to NeuroData?**

Please visit our `How to Ingest Data <ingesting>`_ page, which will help you with mulitple options.

**Can I keep my data private?**

We are an open science data portal so we do encourage you to make their data public as it will enable open science and allow other people to work on your data. But the project does NOT enforce you to make your data public. You can keep your data private for as long as you like.

**How much data can I upload?**

You can upload upto 1TB using the auto-ingest function provided. If you have more data please send us a note on our support forums and one of us will contact you.

**How do I contribute code to NeuroData?**

This project is under active development.  To contribute new functionality or extend the project, either get in touch with us directly, or clone our git repo and issue a pull request. Prior to contributing, checkout our dev branches to see if some of your suggestions are already being implemented. To issue a pull request, head over to our repository and select the pull requests option on the righthand side, then issue a new pull request. NDIO is our internal master branch which is not yet deployed to the servers and might not be tested with all the tool-boxes but is an excellent place to look for new features.

**How do I put in a new feature request or propose an idea?**

You can open an issue on our github `repository <https://github.com/neurodata/ndstore/issues>`_ and tag it as a feature. Prior to opening a new feature request, please checout our other feature issues to see if some of your suggestions or features have not been discussed before.

**How do I report code bugs?**

You can open an issue on our github `repository <https://github.com/neurodata/ndstore/issues>`_ and tag it as a bug. Prior to reporting a bug, please checout our other bugs to see if your bug has been reported or not. Do also have a look at our support forums to identify if this is a bug or not.

**How do I view my data?**

Please visit our NeuroDataViz page.

**How do I download data?**

You can download sub volumes of data using our RESTful API's. `Here <../api/data_api>`_ is the documentation for this. You catch fetch the data in HDF5, Numpy or Blosc format. It is also highly recommended to fetch this data in regions of 1024,1024,16. Alternatively there is a python library NDIO, which wraps around these RESTful API's.

**How do I use the RESTful interface?**
The RESTful interface can be accessed with any browser by inputting the correct link or any package that supports web requests. 

**Is there a support forum?**

Information on making a support request and archived questions and answers may be found `here <https://groups.google.com/a/neurodata.io/forum/#!forum/support>`_.

**What do I do if a service is down?**

If a service appears to be down, it is highly recommended that you wait some time and try to access it again later. If later the service is still down the fastest way to get a response will be to open an issue `here. <https://github.com/neurodata/ndstore/issues>`_
