import sys, os
import argparse
import csv

sys.path.append(os.path.abspath('../django/'))
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import django
django.setup()

from ocpuser.models import *

def getPublicTokens():
    return Token.objects.filter(public=1)

def populateChannels(tokenobj):
    # get the corresponding project
    projobj = tokenobj.project

    # get all channels for project
    channelobjs = Channel.objects.filter(project=projobj)
    channels = {} # channel --> metadata
    for channelobj in channelobjs:
        channels[channelobj.channel_name] = {
            'desc': channelobj.channel_description,
            'channeltype': channelobj.channel_type,
            'datatype': channelobj.channel_datatype,
        }

    return channels

def main():

    parser = argparse.ArgumentParser(description="Write out all public tokens, their associated channels, and some brief metadata to csv.")
    parser.add_argument('filename', action='store', help='Output file path.')
    parser.add_argument('--delimiter', action='store', default=',', help='The CSV delimiter (specify "|" for easy creating of markdown tables)')

    result = parser.parse_args()

    tokenobjs = getPublicTokens()
    tokens = {} # token --> channels --> metadata

    for tokenobj in tokenobjs:
        tokens[tokenobj.token_name] = populateChannels(tokenobj)

    with open(result.filename, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter='{}'.format(result.delimiter))
        csvwriter.writerow(['token','channel','desc','channel type','data type'])
        for token in tokens.keys():
            for channel in tokens[token].keys():
                chandict = tokens[token][channel]
                csvwriter.writerow([token, channel, chandict['desc'], chandict['channeltype'], chandict['datatype']])

if __name__ == '__main__':
    main()
