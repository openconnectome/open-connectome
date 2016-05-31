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

import MySQLdb
import numpy as np
import networkx as nx
import h5py
import re
from contextlib import closing
from django.conf import settings
from operator import add, sub

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
    logger.warning("Illegal cutout corner={}, dim={}".format(corner, dim))
    raise NDWSError("Illegal cutout corner={}, dim={}".format(corner, dim))
  sdb = (spatialdb.SpatialDB(proj))
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
  fproj = ndproj.NDProjectsDB()
  proj = fproj.loadToken(token_name)
  db = ramondb.RamonDB(proj)
  ch = proj.getChannelObj(channel)
  resolution = ch.getResolution()

  cubeRestrictions = int(Xmin) + int(Xmax) + int(Ymin) + int(Ymax) + int(Zmin) + int(Zmax)
  matrix = []
  #assumption that the channel is a neuron channel
  if cubeRestrictions != 0:
    idslist = getAnnoIds(proj, ch, resolution, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax)
  else:
    #Entire cube
    [Xmax, Ymax, Zmax] = proj.datasetcfg.imagesz[resolution]
    idslist = getAnnoIds(proj, ch, resolution, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax)

  if (idslist.size) == 0:
    logger.warning("Area specified is empty")
    raise NDWSError("Area specified is empty")
  pdb.set_trace()
  
  annos={}
  for i in idslist:
    tmp=db.annodb.getSegments(ch, i)
    annos[i]=tmp

  # Create and export graph
  outputGraph = nx.Graph()
  outputGraph.add_edges_from(annos)

  if graphType.upper() == "GRAPHML":
    nx.write_graphml(outputGraph, ("/tmp/{}_{}.graphml").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.graphml").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "ADJLIST":
    nx.write_adjlist(outputGraph, ("/tmp/{}_{}.adjlist").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.adjlist").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "EDGELIST":
    nx.write_edgelist(outputGraph, ("/tmp/{}_{}.edgelist").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.edgelist").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "GEXF":
    nx.write_gexf(outputGraph, ("/tmp/{}_{}.gexf").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.gexf").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "GML":
    nx.write_gml(outputGraph, ("/tmp/{}_{}.gml").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.gml").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "GPICKLE":
    nx.write_gpickle(outputGraph, ("/tmp/{}_{}.gpickle").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.gpickle").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "YAML":
    nx.write_yaml(outputGraph, ("/tmp/{}_{}.yaml").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.yaml").format(project.getProjectName(), channel.getChannelName())
  elif graphType.upper() == "PAJEK":
    nx.write_net(outputGraph, ("/tmp/{}_{}.net").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.net").format(project.getProjectName(), channel.getChannelName())
  else:
    nx.write_graphml(outputGraph, ("/tmp/{}_{}.graphml").format(
        project.getProjectName(), channel.getChannelName()))
    return ("/tmp/{}_{}.graphml").format(project.getProjectName(), channel.getChannelName())
