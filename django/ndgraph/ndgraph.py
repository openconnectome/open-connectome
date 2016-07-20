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

import numpy as np
import networkx as nx
from contextlib import closing
from operator import add, sub
import tempfile

import ndproject
import ndproj
import ramondb
import annotation
import ndchannel
import spatialdb

from ndwserror import NDWSError
import logging
logger = logging.getLogger("neurodata")

def getAnnoIds(proj, ch, resolution, xmin, xmax, ymin, ymax, zmin, zmax):
  """Return a list of anno ids restricted by equality predicates. Equalities are alternating in field/value in the url."""

  mins = (xmin, ymin, zmin)
  maxs = (xmax, ymax, zmax)
  offset = proj.datasetcfg.offset[resolution]
  # Add a comment
  corner = map(max, zip(*[mins, map(sub, mins, offset)]))
  dim = map(sub, maxs, mins)

  if not proj.datasetcfg.checkCube(resolution, corner, dim):
    logger.error("Illegal cutout corner={}, dim={}".format(corner, dim))
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

def genGraphRAMON(token_name, channel, graphType="graphml", xmin=0, xmax=0, ymin=0, ymax=0, zmin=0, zmax=0):
  """Generate the graph based on different inputs"""

  [xmin, xmax, ymin, ymax, zmin, zmax] = [int(i) for i in [xmin, xmax, ymin, ymax, zmin, zmax]]

  with closing (ndproj.NDProjectsDB()) as fproj:
    proj = fproj.loadToken(token_name)

  with closing (ramondb.RamonDB(proj)) as db:
    ch = proj.getChannelObj(channel)
    resolution = ch.getResolution()

    cubeRestrictions = xmin + xmax + ymin + ymax + zmin + zmax
    matrix = []
    # assumption that the channel is a neuron channel
    if cubeRestrictions != 0:
      idslist = getAnnoIds(proj, ch, resolution, xmin, xmax, ymin, ymax, zmin, zmax)
    else:
      # entire cube
      [xmax, ymax, zmax] = proj.datasetcfg.imagesz[resolution]
      idslist = getAnnoIds(proj, ch, resolution, xmin, xmax, ymin, ymax, zmin, zmax)

    if idslist.size == 0:
      logger.error("Area specified x:{},{} y:{},{} z:{},{} is empty".format(xmin, xmax, ymin, ymax, zmin, zmax))
      raise NDWSError("Area specified x:{},{} y:{},{} z:{},{} is empty".format(xmin, xmax, ymin, ymax, zmin, zmax))

    annos = {}
    for i in idslist:
      tmp = db.getAnnotation(ch, i)
      if int(db.annodb.getAnnotationKV(ch, i)['ann_type']) == annotation.ANNO_SYNAPSE:
        annos[i]=[int(s) for s in tmp.getField('segments').split(',')]

    # create and export graph
    outputGraph = nx.Graph()
    for key in annos:
      outputGraph.add_edges_from([tuple(annos[key])])

  try:
    f = tempfile.NamedTemporaryFile()
    if graphType.upper() == "GRAPHML":
      nx.write_graphml(outputGraph, f)
    elif graphType.upper() == "ADJLIST":
      nx.write_adjlist(outputGraph, f)
    elif graphType.upper() == "EDGELIST":
      nx.write_edgelist(outputGraph, f)
    elif graphType.upper() == "GEXF":
      nx.write_gexf(outputGraph, f)
    elif graphType.upper() == "GML":
      nx.write_gml(outputGraph, f)
    elif graphType.upper() == "GPICKLE":
      nx.write_gpickle(outputGraph, f)
    elif graphType.upper() == "YAML":
      nx.write_yaml(outputGraph, f)
    elif graphType.upper() == "PAJEK":
      nx.write_net(outputGraph, f)
    else:
      nx.write_graphml(outputGraph, f)
    f.flush()
    f.seek(0)
  except:
    logger.error("Internal file error in creating/editing a NamedTemporaryFile")
    f.close()
    raise NDWSError("Internal file error in creating/editing a NamedTemporaryFile")

  return (f, graphType.lower())
