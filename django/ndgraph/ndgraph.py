# Copyright 2014 NeuroData (http://neurodata.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO UA remove unwanted imports from all your files. I removed MySQLdb here. Check if you have any other ones like h5py
import numpy as np
import networkx as nx
import h5py
import re
from contextlib import closing
from django.conf import settings
from operator import add, sub

import annotation
import restargs
import ramondb
import ndproject
import ndproj
import h5ann
import ndlib
import ndchannel
import spatialdb

from ndwserror import NDWSError
import logging
logger = logging.getLogger("neurodata")


def getAnnoIds(proj, ch, resolution, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax):
  """Return a list of anno ids restricted by equality predicates. Equalities are alternating in field/value in the url."""
  mins = (int(Xmin), int(Ymin), int(Zmin))
  maxs = (int(Xmax), int(Ymax), int(Zmax))
  offset = proj.datasetcfg.offset[resolution]
  corner = map(max, zip(*[mins, map(sub, mins, offset)]))
  dim = map(sub, maxs, mins)

  if not proj.datasetcfg.checkCube(resolution, corner, dim):
    # TODO UA this logger.error when you are raising an error. we use warning when we are expecting an exception and doing something more vs breaking out of the code by calling NDWSError
    logger.warning("Illegal cutout corner={}, dim={}".format(corner, dim))
    raise NDWSError("Illegal cutout corner={}, dim={}".format(corner, dim))
  with closing (spatialdb.SpatialDB(proj)) as sdb:
    cutout = sdb.cutout(ch, corner, dim, resolution)

  if cutout.isNotZeros():
    annoids = np.unique(cutout.data)
  else:
    annoids = np.asarray([0], dtype=np.uint32)

  if annoids[0] == 0:
    return annoids[1:]
  else:
    return annoids

def genGraphRAMON(token_name, channel, graphType="graphml", Xmin=0, Xmax=0, Ymin=0, Ymax=0, Zmin=0, Zmax=0,):
  """Generate the graph based on different inputs"""
  
  # TODO UA we use xmin and not Xmin, upper camel case is not usually a python thing and we do not use in OCP anywhere, please fix this in both files. Should be a simple find and replace
  with closing (ndproj.NDProjectsDB()) as fproj:
    proj = fproj.loadToken(token_name)
  
  with closing (ramondb.RamonDB(proj)) as db:
    ch = proj.getChannelObj(channel)
    resolution = ch.getResolution()
      
    # TODO UA all these arguments should be converted to in when it comes in from webargs in view not here and everywhere else
    cubeRestrictions = int(Xmin) + int(Xmax) + int(Ymin) + int(Ymax) + int(Zmin) + int(Zmax)
    matrix = []
    # assumption that the channel is a neuron channel
    if cubeRestrictions != 0:
      idslist = getAnnoIds(proj, ch, resolution, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax)
    else:
      # entire cube
      [Xmax, Ymax, Zmax] = proj.datasetcfg.imagesz[resolution]
      idslist = getAnnoIds(proj, ch, resolution, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax)

    if idslist.size == 0:
      logger.error("Area specified is empty")
      raise NDWSError("Area specified is empty")
    
    annos = {}
    for i in idslist:
      tmp = db.getAnnotation(ch, i)
      if int(db.annodb.getAnnotationKV(ch, i)['ann_type']) == annotation.ANNO_SYNAPSE:
        annos[i]=[int(s) for s in tmp.getField('segments').split(',')]

    # create and export graph
    outputGraph = nx.Graph()
    for key in annos:
      outputGraph.add_edges_from([tuple(annos[key])])

  if graphType.upper() == "GRAPHML":
    nx.write_graphml(outputGraph, ("/tmp/{}_{}.graphml").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.graphml").format(proj.getProjectName(), channel)
  elif graphType.upper() == "ADJLIST":
    nx.write_adjlist(outputGraph, ("/tmp/{}_{}.adjlist").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.adjlist").format(proj.getProjectName(), channel)
  elif graphType.upper() == "EDGELIST":
    nx.write_edgelist(outputGraph, ("/tmp/{}_{}.edgelist").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.edgelist").format(proj.getProjectName(), channel)
  elif graphType.upper() == "GEXF":
    nx.write_gexf(outputGraph, ("/tmp/{}_{}.gexf").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.gexf").format(proj.getProjectName(), channel)
  elif graphType.upper() == "GML":
    nx.write_gml(outputGraph, ("/tmp/{}_{}.gml").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.gml").format(proj.getProjectName(), channel)
  elif graphType.upper() == "GPICKLE":
    nx.write_gpickle(outputGraph, ("/tmp/{}_{}.gpickle").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.gpickle").format(proj.getProjectName(), channel)
  elif graphType.upper() == "YAML":
    nx.write_yaml(outputGraph, ("/tmp/{}_{}.yaml").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.yaml").format(proj.getProjectName(), channel)
  elif graphType.upper() == "PAJEK":
    nx.write_net(outputGraph, ("/tmp/{}_{}.net").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.net").format(proj.getProjectName(), channel)
  else:
    nx.write_graphml(outputGraph, ("/tmp/{}_{}.graphml").format(
        proj.getProjectName(), channel))
    return ("/tmp/{}_{}.graphml").format(proj.getProjectName(), channel)
