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


import re

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")


#
# Routines to manipulate channels: 
#
#    convert from numerals to integers and back
#

class OCPCAChannels:

  def __init__( self, db ):
    """Do nothing on init.  Load the channels lazily"""
    self.db = db
    self.chanmap = None


  def getChannelID ( self, chanstr ):
    """Get a channel identifier from the string"""

    # load the map on first request
    if self.chanmap == None:
      self.chanmap = self.db.getChannels()

    try:
      return self.chanmap[chanstr]
    except:
      logger.error("Did not find channel %s" % (chanstr))
      raise OCPCAError("Did not find channel %s" % (chanstr))


  def rewriteToInts ( self, channels ):
    """Go throught the list of channels and rewrite all names to integer identifiers"""

    channames = None
    outchannels=[]
    
    for chan in channels:

      # integers are kept
      if re.match ('^\d+$', chan):
        outchannels.append( int(chan) )
      # anything else rewritten
      else:
        outchannels.append(self.getChannelID ( chan ))

    return outchannels

# end OCPCAChannel

def toID ( channel, db ):
  """Convert a single channel to an identifier"""

  # integers are kept
  if type(channel)==int or type(channel)==long or re.match ('^\d+$', channel):
    return channel
  else:
    ocpcachans = OCPCAChannels( db )
    return ocpcachans.getChannelID ( channel )
