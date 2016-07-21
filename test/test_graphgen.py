# Copyright 2014 Open Connectome Project (http://openconnecto.me)
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

import urllib2
import cStringIO
import tempfile
import random
import csv
import os
import numpy as np
import pytest
from contextlib import closing
import networkx as nx

import makeunitdb
from ndtype import ANNOTATION, UINT32
from params import Params
from ramon import H5AnnotationFile, setField, getField, queryField, makeAnno, createSpecificSynapse
from postmethods import putAnnotation, getAnnotation, getURL, postURL
import kvengine_to_test
import site_to_test
#from ndgraph import genGraphRAMON
SITE_HOST = site_to_test.site

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['ANNO1']
p.channel_type = ANNOTATION
p.datatype = UINT32

class Test_GraphGen:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, channel_list=p.channels, public=True, readonly=0, ximagesize=100, yimagesize=100, zimagesize=100)

    cutout1 = "0/2,5/1,3/1,3"
    cutout2 = "0/1,3/4,6/2,5"
    cutout3 = "0/4,6/2,5/5,7"
    cutout4 = "0/6,8/5,9/2,4"

    syn_segments1 = [[7, 3],]
    syn_segments2 = [[7, 4],]
    syn_segments3 = [[3, 9],]
    syn_segments4 = [[5, 4],]

    f1 = createSpecificSynapse(1, syn_segments1, cutout1)
    putid = putAnnotation(p, f1)
    f2 = createSpecificSynapse(2, syn_segments2, cutout2)
    putid = putAnnotation(p, f2)
    f3 = createSpecificSynapse(3, syn_segments3, cutout3)
    putid = putAnnotation(p, f3)
    f4 = createSpecificSynapse(4, syn_segments4, cutout4)
    putid = putAnnotation(p, f4)

  def teardown_class(self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)
    #os.remove("/tmp/GeneratedGraph.tar.gz")

  def test_checkTotal(self):
    """Test the original/non-specific dataset"""
    syn_segments = [[7, 3], [7, 12], [3, 9], [5, 12]]
    truthGraph = nx.Graph()
    truthGraph.add_edges_from(syn_segments)

    url = 'http://{}/ndgraph/{}/{}/'.format(SITE_HOST, p.token, p.channels[0])
    graphFile = urllib2.urlopen(url)
    with open(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]), "wb") as f:
        f.write(graphFile.read())
    outputGraph = nx.read_graphml(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]))
    assert(nx.is_isomorphic(outputGraph, truthGraph))

  def test_checkType(self):
    """Test the export to different data types"""
    syn_segments = [[7, 3], [7, 12], [3, 9], [5, 12]]
    truthGraph = nx.Graph()
    truthGraph.add_edges_from(syn_segments)

    url = 'http://{}/ndgraph/{}/{}/{}/'.format(
        SITE_HOST, p.token, p.channels[0], 'adjlist')
    graphFile = urllib2.urlopen(url)
    with open(("/tmp/{}_{}.adjlist").format(p.token, p.channels[0]), "wb") as f:
        f.write(graphFile.read())
    outputGraph = nx.read_adjlist(("/tmp/{}_{}.adjlist").format(p.token, p.channels[0]))
    assert(nx.is_isomorphic(outputGraph, truthGraph))

  def test_checkCutout(self):
    """Test the cutout arguement of graphgen"""

    syn_segments = [[7, 3], [7, 4], [5, 4]]
    truthGraph = nx.Graph()
    truthGraph.add_edges_from(syn_segments)

    url = 'http://{}/ndgraph/{}/{}/{}/{},{}/{},{}/{},{}/'.format(
        SITE_HOST, p.token, p.channels[0], 'graphml', 0, 7, 0, 8, 1, 4)
    graphFile = urllib2.urlopen(url)
    with open(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]), "wb") as f:
        f.write(graphFile.read())
    outputGraph = nx.read_graphml(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]))
    assert(nx.is_isomorphic(outputGraph, truthGraph))

  def test_ErrorHandling(self):
    """Invalid graphtype"""
    syn_segments = [[7, 3], [7, 12], [3, 9], [5, 12]]
    truthGraph = nx.Graph()
    truthGraph.add_edges_from(syn_segments)

    url = 'http://{}/ndgraph/{}/{}/{}/'.format(
        SITE_HOST, p.token, p.channels[0], 'foograph')
    graphFile = urllib2.urlopen(url)
    with open(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]), "wb") as f:
        f.write(graphFile.read())
    outputGraph = nx.read_graphml(("/tmp/{}_{}.graphml").format(p.token, p.channels[0]))
    assert(nx.is_isomorphic(outputGraph, truthGraph))

    """Invalid token"""
    url = 'http://{}/ndgraph/{}/{}/{}/{},{}/{},{}/{},{}/'.format(
        SITE_HOST, 'foo', p.channels[0], 'graphml', 0, 7, 0, 7, 0, 7)
    assert (getURL(url) >= 500)
