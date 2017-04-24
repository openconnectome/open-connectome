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

import os
import re
import string
import random
import MySQLdb
import json
import subprocess
import django.http
from django.core.urlresolvers import get_script_prefix
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.template import Context
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token as User_Token
from django.conf import settings
import django.forms
from datetime import datetime
from contextlib import closing
from webservices import ndwsrest
from webservices import ndwsjson
from ndproj.ndprojdb import NDProjectsDB
from ndlib.ndtype import IMAGE, ANNOTATION, TIMESERIES, UINT8, UINT16, UINT32, UINT64, INT8, INT16, INT32, INT64, FLOAT32, ND_VERSION, SCHEMA_VERSION, MYSQL, S3_FALSE, S3_TRUE, REDIS
from models import Project
from models import Dataset
from models import Token
from models import Channel
from models import Backup
from ndproj.nddataset import NDDataset
from ndproj.ndproject import NDProject
from ndproj.ndchannel import NDChannel
from ndproj.ndtoken import NDToken
from forms import ProjectForm
from forms import DatasetForm
from forms import TokenForm
from forms import ChannelForm
from forms import BackupForm
from forms import dataUserForm
from webservices.ndwserror import NDWSError
import logging
logger = logging.getLogger("neurodata")


# Helpers
''' Base url redirects to projects page'''
def default(request):
    return redirect(getProjects)

''' Token Auth '''
@login_required(login_url='/nd/accounts/login/')
def getUserToken(request):
  u=request.user
  # u = User.objects.get(username=user) 
  is_tokened = User_Token.objects.filter(user=u)
  if not is_tokened:
    token = User_Token.objects.create(user=u)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = "attachment; filename=\"{}.pem\"".format(str(u))
    response.write(token)
    return response
  else: 
    response = HttpResponse("You have already downloaded your token, please contact the site administrator if you have lost it")
    return response

''' Little welcome message'''
@login_required(login_url='/nd/accounts/login/')
def getProjects(request):

    try:
        if request.method == 'POST':
            if 'filter' in request.POST:
                # filter projects based on input value
                userid = request.user.id
                filteroption = request.POST.get('filteroption')
                filtervalue = (request.POST.get('filtervalue')).strip()

                # get the visible data sets
                if request.user.is_superuser:
                    visible_datasets = NDDataset.all_list()
                else:
                    visible_datasets = NDDataset.public_list | NDDataset.user_list(userid)

                visible_datasets.sort()

                projs = defaultdict(list)

                dbs = defaultdict(list)

                for db in visible_datasets:
                    proj = Project.objects.filter(dataset_id=db.dataset_name, user_id=userid) | Project.objects.filter(dataset_id=db.dataset_name, public=1)
                    if proj:
                        dbs[db.dataset_name].append(proj)
                    else:
                        dbs[db.dataset_name].append(None)

                if request.user.is_superuser:
                    visible_projects = Project.objects.all()
                else:
                    visible_projects = Project.objects.filter(user_id=userid) | Project.objects.filter(public=1)

                context = {
                    'databases': dbs.iteritems(),
                    'projects': visible_projects.values_list(flat=True)
                }
                return render(request, 'projects.html', context)

            elif 'delete_data' in request.POST:

                username = request.user.username
                project_to_delete = (request.POST.get('project_name')).strip()

                reftokens = Token.objects.filter(project_id=project_to_delete)
                if reftokens:
                    messages.error(request, 'Project cannot be deleted. Please delete all tokens for this project first.')
                    return redirect(getProjects)

                else:
                    pr = NDProject.fromName(project_to_delete)
                    if pr:
                        if pr.user_id == request.user.id or request.user.is_superuser:
                            # Delete project from the table followed  by the database.
                            # deleting a project is super dangerous b/c you may delete it out from other tokens on other servers.So, only delete when it's on the same server for now
                            pr.delete()
                            messages.success(request,"Project deleted")
                        else:
                            messages.error(request,"Cannot delete.  You are not owner of this project or not superuser.")
                    else:
                        messages.error( request,"Project not found.")
                    return redirect(getProjects)

            elif 'delete' in request.POST:
                username = request.user.username
                project_to_delete = (request.POST.get('project_name')).strip()

                reftokens = Token.objects.filter(project_id=project_to_delete)
                if reftokens:
                    messages.error(request, 'Project cannot be deleted. Please delete all tokens for this project first.')
                    return redirect(getProjects)
                else:
                    pr = NDProject.fromName(project_to_delete)
                    if proj:
                        if pr.user_id == request.user.id or request.user.is_superuser:
                            pr.delete()
                            messages.success(request,"Project deleted")
                        else:
                            messages.error(request,"Cannot delete.  You are not owner of this project or not superuser.")
                    else:
                        messages.error( request,"Project not found.")
                    return redirect(getProjects)

            elif 'info' in request.POST:
                #GET PROJECT INFO -----------
                token = (request.POST.get('roptions')).strip()
                return HttpResponse(ndwsrest.projInfo(token), content_type="product/hdf5" )

            elif 'update' in request.POST:
                project_to_update = (request.POST.get('project_name')).strip()
                request.session["project_name"] = project_to_update
                return redirect(updateProject)

            elif 'tokens' in request.POST:
                projname = (request.POST.get('project_name')).strip()
                request.session["project"] = projname
                return redirect(getTokens)

            elif 'channels' in request.POST:
                projname=(request.POST.get('project_name')).strip()
                request.session["project"] = projname
                return redirect(getChannels)

            elif 'backup' in request.POST:
                projname=(request.POST.get('project_name')).strip()
                request.session["project"] = projname
                return redirect(backupProject)

            else:
                # Invalid POST
                messages.error(request,"Unrecognized POST")
                return redirect(getProjects)

        else:
            # GET Projects
            userid = request.user.id

            # get the visible data sets
            if request.user.is_superuser:
                visible_datasets=Dataset.objects.all()
            else:
                visible_datasets=Dataset.objects.filter(user_id=userid) | Dataset.objects.filter(public=1)

            dbs = defaultdict(list)

            for db in visible_datasets:
                proj = Project.objects.filter(dataset_id=db.dataset_name, user_id=userid) | Project.objects.filter(dataset_id=db.dataset_name, public=1)
                if proj:
                    dbs[db.dataset_name].append(proj)
                else:
                    dbs[db.dataset_name].append(None)

            if request.user.is_superuser:
                visible_projects = Project.objects.all()
            else:
                visible_projects = Project.objects.filter(user_id=userid) | Project.objects.filter(public=1)

            context = {
                'databases': sorted(dbs.iteritems()),
                'projects':visible_projects
            }
            return render(request, 'projects.html', context)

    except NDWSError, e:

        messages.error(request,"Exception in administrative interface = {}".format(e))

        # GET Projects
        username = request.user.username
        all_datasets= Dataset.objects.all()
        dbs = defaultdict(list)
        for db in all_datasets:
            proj = Project.objects.filter(dataset_id=db.dataset_name, user_id = request.user)
            if proj:
                dbs[db.dataset_name].append(proj)
            else:
                dbs[db.dataset_name].append(None)

        all_projects = Project.objects.values_list('project_name',flat= True)

        context = {
            'databases': dbs.iteritems(),
            'projects': all_projects
        }
        return render(request, 'projects.html', context)


@login_required(login_url='/nd/accounts/login/')
def getDatasets(request):

    try:

        userid = request.user.id
        if request.user.is_superuser:
            visible_datasets = NDDataset.all_list()
        else:
            visible_datasets = NDDataset.public_list | NDDataset.user_list(userid)

        if request.method == 'POST':

            if 'filter' in request.POST:
                filtervalue = (request.POST.get('filtervalue')).strip()
                visible_datasets = visible_datasets.filter(dataset_name=filtervalue)
                context = {
                    'dts': visible_datasets,
                }
                return render(request, 'datasets.html', context)
                #return render_to_response('datasets.html', { 'dts': visible_datasets })

            elif 'delete' in request.POST:

                # delete specified dataset
                ds = (request.POST.get('dataset_name')).strip()
                ds_to_delete = Dataset.objects.get(dataset_name=ds)

                # Check for projects with that dataset
                proj = Project.objects.filter(dataset_id=ds_to_delete.dataset_name)
                if proj:
                    messages.error(request, 'Dataset cannot be deleted. Please delete all projects for this dataset first.')
                else:
                    if ds_to_delete.user_id == request.user.id or request.user.is_superuser:
                        ds_to_delete.delete()
                        messages.success(request, 'Deleted Dataset ' + ds)
                    else:
                        messages.error(request,"Cannot delete.  You are not owner of this dataset or not superuser.")

                    # refresh to remove deleted
                    if request.user.is_superuser:
                        visible_datasets = Dataset.objects.all()
                    else:
                        # KL TODO Fix queryset bug
                        visible_datasets = Dataset.objects.filter(user=request.user.id) | Dataset.objects.filter(public=1)
                context = {
                    'dts': visible_datasets
                }
                return render(request, 'datasets.html', context)

            elif 'update' in request.POST:
                ds = (request.POST.get('dataset_name')).strip()
                request.session["dataset_name"] = ds
                return redirect(updateDataset)

            else:
                # load datasets
                context = { 'dts': visible_datasets }
                return render(request, 'datasets.html', context)

        else:
            # GET datasets
            context = { 'dts': visible_datasets }
            return render(request, 'datasets.html', context)

    except NDWSError, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        context = { 'dts': visible_datasets }
        return render(request, 'datasets.html', context)

@login_required(login_url='/nd/accounts/login/')
def getAllTokens(request):

    if 'filter' in request.POST:
        del request.session['filter']
    if 'project' in request.session:
        del request.session['project']

    return getTokens(request)


@login_required(login_url='/nd/accounts/login/')
def getChannels(request):

    username = request.user.username

    try:
        if request.method == 'POST':

            if 'delete' in request.POST:
                # Delete the channel from the project
                channel_to_delete = (request.POST.get('channel')).strip()
                prname = request.session["project"]
                pr = NDProject.fromName(prname)
                ch = pr.getChannelObj(channel_to_delete)
                if ch:
                    if pr.user_id == request.user.id or request.user.is_superuser:
                        ch.delete()
                        messages.success(request,"Channel deleted " + channel_to_delete)
                    else:
                        messages.error(request,"Cannot delete.  You are not owner of this token or not superuser.")
                else:
                    messages.error(request,"Unable to delete " + channel_to_delete)
                return redirect(getChannels)

            # update form populated with channel fields
            elif 'update' in request.POST:
                channel = (request.POST.get('channel')).strip()
                request.session["channel_name"] = channel
                return redirect(updateChannel)

            # add using the update channel form with no initial data
            elif 'add' in request.POST:
                # must remove channel_name context to add a new one.  otherwise, it's an update
                if "channel_name" in request.session:
                    del ( request.session["channel_name"] )
                return redirect(updateChannel)

            elif 'backtochannels' in request.POST:
                return redirect(getChannels)

            elif 'backtoprojects' in request.POST:
                return redirect(getProjects)


            else:
                # Unrecognized Option
                messages.error(request,"Invalid request")
                return redirect(getChannels)

        else:
            # GET tokens for the specified project
            username = request.user.username
            if "project" in request.session:
                proj = request.session["project"]
                all_channels = Channel.objects.filter(project_id=proj)
            else:
                # Unrecognized Option
                messages.error(request, "Must have a project context to look at channels.")
                return redirect(getChannels)
            context = {
                'channels': all_channels,
                'project': proj
            }
            return render(request, 'channels.html', context)

    except NDWSError as e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        # datasets = pd.getDatasets()
        context = {
            'channels': all_channels,
            'project': proj
        }
        return render(request, 'projects.html', context)
        #return render_to_response('projects.html', context)


@login_required(login_url='/nd/accounts/login/')
def getTokens(request):

    username = request.user.username

    try:
        if request.method == 'POST':
            if 'filter' in request.POST:
                # Filter tokens based on an input value
                filteroption = request.POST.get('filteroption')
                filtervalue = (request.POST.get('filtervalue')).strip()
                all_tokens = Token.objects.filter(token_name=filtervalue)
                proj=""
                context = {
                    'tokens': all_tokens,
                    'project': proj
                }
                return render(request, 'tokens.html', context)

            elif 'delete' in request.POST:
                # Delete the token from the token table
                token_to_delete = (request.POST.get('token')).strip()
                token = Token.objects.get(token_name=token_to_delete)
                if token:
                    if token.user_id == request.user.id or request.user.is_superuser:
                        token.delete()
                        messages.success(request,"Token deleted " + token_to_delete)
                    else:
                        messages.error(request,"Cannot delete.  You are not owner of this token or not superuser.")
                else:
                    messages.error(request,"Unable to delete " + token_to_delete)
                return redirect(getTokens)

            elif 'downloadtoken' in request.POST:
                # Download the token in a test file
                token = (request.POST.get('token')).strip()
                response = HttpResponse(token,content_type='text/html')
                response['Content-Disposition'] = 'attachment; filename="nd.token"'
                return response

            elif 'update' in request.POST:
                # update project token
                token = (request.POST.get('token')).strip()
                request.session["token_name"] = token
                return redirect(updateToken)

            # redirect to add a token
            elif 'add' in request.POST:
                return redirect(createToken)

            elif 'backtoprojects' in request.POST:
                return redirect(getProjects)

            else:
                # Unrecognized Option
                messages.error(request,"Invalid request")
                return redirect(getTokens)

        else:
            # GET tokens for the specified project
            username = request.user.username
            if "project" in request.session:
                proj = request.session["project"]
                all_tokens = Token.objects.filter(project_id=proj)
            else:
                proj=""
                all_tokens = Token.objects.all()

            context = {
                'tokens': all_tokens,
                'project': proj
            }
            return render(request, 'tokens.html', context)
            #return render_to_response('tokens.html', { 'tokens': all_tokens, 'project': proj })

    except NDWSError as e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        # datasets = pd.getDatasets()

        context = {
            'dts': datasets
        }
        return render(request, 'datasets.html', context)
        #return render_to_response('datasets.html', { 'dts': datasets })


@login_required(login_url='/nd/accounts/login/')
def createProject(request):

    try:

        if request.method == 'POST':
            if 'createproject' in request.POST:

                form = ProjectForm(request.POST)

                if form.is_valid():
                    new_project = form.save(commit=False)
                    new_project.user_id = request.user.id
                    if request.POST.get('legacy') == 'yes':
                        new_project.nd_version = '0.0'
                    else:
                        new_project.nd_version = ND_VERSION
                    new_project.schema_version = SCHEMA_VERSION
                    # TODO input from form
                    new_project.mdengine = MYSQL
                    if new_project.kvengine == REDIS:
                      new_project.s3backend = S3_TRUE
                    else:
                      new_project.kvegnine = S3_FALSE
                    pr = NDProject(new_project)
                    try:
                        # create a database when not linking to an existing databases
                        if not request.POST.get('nocreate') == 'on':
                            pr.create()
                        else:
                            pr.create(create_table=False)
                        if 'token' in request.POST:
                            tk = NDToken(Token ( token_name = new_project.project_name, token_description = 'Default token for public project', project_id=new_project, user_id=request.user.id, public=new_project.public))
                            tk.create()

                    except Exception as e:
                        pr.delete()
                        logger.error("Failed to create project {}. Error {}".format(new_project.project_name, e))
                        messages.error(request,"Failed to create project {}. Error {}".format(new_project.project_name, e))

                    return redirect(getProjects)
                else:
                    context = {
                        'form': form
                    }
                    return render(request, 'createproject.html', context)

            else:
                return redirect(getProjects)

        else:
            '''Show the Create Project form'''

            form = ProjectForm()

            # restrict datasets to user visible fields
            form.fields['dataset'].queryset = Dataset.objects.filter(user_id=request.user.id) | Dataset.objects.filter(public=1)

            context = {
                'form': form
            }
            return render(request, 'createproject.html', context)

    except Exception as e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)


@login_required(login_url='/nd/accounts/login/')
def createDataset(request):

    try:
        if request.method == 'POST':
            if 'createdataset' in request.POST:
                form = DatasetForm(request.POST)
                if form.is_valid():
                    new_dataset=form.save(commit=False)
                    new_dataset.user_id=request.user.id
                    new_dataset.save()
                    return redirect(getDatasets)
                else:
                    context = {'form': form}
                    return render(request, 'createdataset.html', context)
            elif 'backtodatasets' in request.POST:
                return redirect(getDatasets)
            else:
                messages.error(request,"Unkown POST request.")
                return redirect(getDatasets)
        else:
            '''Show the Create datasets form'''
            form = DatasetForm()
            context = {
                'form': form
            }
            return render(request, 'createdataset.html', context)

    except Exception as e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getDatasets)


@login_required(login_url='/nd/accounts/login/')
def updateDataset(request):

    try:
        # Get the dataset to update
        ds = request.session["dataset_name"]
        if request.method == 'POST':
            if 'updatedataset' in request.POST:
                ds_update = get_object_or_404(Dataset,dataset_name=ds)

                if ds_update.user_id == request.user.id or request.user.is_superuser:

                    form = DatasetForm(data=request.POST or None,instance=ds_update)
                    if form.is_valid():
                        form.save()
                        messages.success(request, 'Sucessfully updated dataset')
                        del request.session["dataset_name"]
                        return redirect(getDatasets)
                    else:
                        # invalid form
                        context = {'form': form}
                        return redirect(request, 'updatedataset.html', context)

                else:
                    messages.error(request,"Cannot update.  You are not owner of this dataset or not superuser.")
                    return redirect(getDatasets)

            elif 'backtodatasets' in request.POST:
                return redirect(getDatasets)
            else:
                # unrecognized option
                return redirect(getDatasets)
        else:
            print "Getting the update form"
            if "dataset_name" in request.session:
                ds = request.session["dataset_name"]
            else:
                ds = ""
            ds_to_update = Dataset.objects.filter(dataset_name=ds)

            data = {
                'dataset_name': ds_to_update[0].dataset_name,
                'ximagesize':ds_to_update[0].ximagesize,
                'yimagesize':ds_to_update[0].yimagesize,
                'zimagesize':ds_to_update[0].zimagesize,
                'xoffset':ds_to_update[0].xoffset,
                'yoffset':ds_to_update[0].yoffset,
                'zoffset':ds_to_update[0].zoffset,
                'public':ds_to_update[0].public,
                'xvoxelres':ds_to_update[0].xvoxelres,
                'yvoxelres':ds_to_update[0].yvoxelres,
                'zvoxelres':ds_to_update[0].zvoxelres,
                'scalinglevels':ds_to_update[0].scalinglevels,
                'scalingoption':ds_to_update[0].scalingoption,
                'dataset_description':ds_to_update[0].dataset_description,
            }
            form = DatasetForm(initial=data)
            context = {'form': form}
            return render(request, 'updatedataset.html', context)
            #return render_to_response('updatedataset.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))

        return redirect(getDatasets)


@login_required(login_url='/nd/accounts/login/')
def updateChannel(request):

    try:
        prname = request.session['project']
        pr = Project.objects.get(project_name = prname)

        if request.method == 'POST':

            if 'updatechannel' in request.POST:

                chname = request.session["channel_name"]
                channel_to_update = get_object_or_404(Channel, channel_name=chname, project_id=pr)
                form = ChannelForm(data=request.POST or None, instance=channel_to_update)

                if form.is_valid():
                    newchannel = form.save(commit=False)

                else:
                    # Invalid form
                    context = {'form': form, 'project': prname}
                    return render(request, 'updatechannel.html', context)

            elif 'propagatechannel' in request.POST:

                chname = request.session["channel_name"]
                channel_to_update = get_object_or_404(Channel,channel_name=chname,project_id=pr)
                form = ChannelForm(data=request.POST or None, instance=channel_to_update)

                # KL TODO/ RB TODO add propagate to the UI
                #      messages.error(request,"Propagate not yet implemented in self-admin UI.")
                #      return HttpResponseRedirect(get_script_prefix()+'nduser/channels/')

                context = {'form': form, 'project': prname}
                form.add_error(None,[u"Propagate not yet implemented in self-admin UI."])
                return render(request, 'updatechannel.html', context)

            elif 'createchannel' in request.POST:
                form = ChannelForm(data=request.POST or None)

                if form.is_valid():

                    new_channel = form.save( commit=False )

                    # populate the channel type and data type from choices
                    combo = request.POST.get('channelcombo')
                    if combo=='tu:8':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = UINT8
                    elif combo=='tu:16':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = UINT16
                    elif combo=='tu:32':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = UINT32
                    elif combo=='ti:8':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = INT8
                    elif combo=='ti:16':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = INT16
                    elif combo=='ti:32':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = INT32
                    elif combo=='a:32':
                        new_channel.channel_type = ANNOTATION
                        new_channel.channel_datatype = UINT32
                    elif combo=='tf:32':
                        new_channel.channel_type = TIMESERIES
                        new_channel.channel_datatype = FLOAT32
                    else:
                        logger.error("Illegal channel combination requested: {}.".format(combo))
                        messages.error(request,"Illegal channel combination requested or none selected.")
                        return redirect(getChannels)

                    if pr.user_id == request.user.id or request.user.is_superuser:

                        # if there is no default channel, make this default
                        if not Channel.objects.filter(project_id=pr, default=True):
                            new_channel.default = True
                        
                        ch = NDChannel(new_channel)

                        try:
                            if not request.POST.get('nocreate') == 'on':
                                ch.create()
                            else:
                                ch.save()
                        except Exception, e:
                            ch.delete()
                            logger.error("Failed to create channel. Error {}".format(e))
                            messages.error(request,"Failed to create channel. {}".format(e))

                        return redirect(getChannels)

                    else:
                        messages.error(request,"Cannot update. You are not owner of this token or not superuser.")
                        return redirect(getChannels)

                else:
                    # Invalid form
                    context = {'form': form, 'project': prname}
                    return render(request, 'createchannel.html', context)

            else:
                # unrecognized option
                return redirect(getChannels)

            if pr.user_id == request.user.id or request.user.is_superuser:

                # if setting the default channel, remove previous default
                if newchannel.default == True:
                    olddefault = Channel.objects.filter(default=True, project_id=pr)
                    for od in olddefault:
                        od.default = False
                        od.save()

                # if there is no default channel, make this default
                if not Channel.objects.filter(project_id=pr):
                    newchannel.default = True

                newchannel.save()
                return redirect(getChannels)

            else:
                messages.error(request,"Cannot update. You are not owner of this token or not superuser.")
                return redirect(getChannels)

        else:
            if "channel_name" in request.session:
                chname = request.session["channel_name"]
                channel_to_update = Channel.objects.filter(project_id=pr).filter(channel_name=chname)
                data = {
                    'channel_name': channel_to_update[0].channel_name,
                    'channel_type':channel_to_update[0].channel_type,
                    'channel_datatype': channel_to_update[0].channel_datatype,
                    'channel_description':channel_to_update[0].channel_description,
                    'readonly':channel_to_update[0].readonly,
                    'resolution':channel_to_update[0].resolution,
                    'default':channel_to_update[0].default,
                    'exceptions':channel_to_update[0].exceptions,
                    'propagate':channel_to_update[0].propagate,
                    'starttime':channel_to_update[0].starttime,
                    'endtime':channel_to_update[0].endtime,
                    'startwindow':channel_to_update[0].startwindow,
                    'endwindow':channel_to_update[0].endwindow,
                    'project': pr
                }
                form = ChannelForm(initial=data)
                context = {'form': form, 'project': prname }
                return render(request, 'updatechannel.html', context)
            else:
                data = {
                    'project': pr
                }
                form = ChannelForm(initial=data)
                context = {'form': form, 'project': prname }
                return render(request, 'createchannel.html', context)

    except Exception as e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)


@login_required(login_url='/nd/accounts/login/')
def updateToken(request):

    try:
        # Get the dataset to update
        token = request.session["token_name"]
        if request.method == 'POST':
            if 'updatetoken' in request.POST:
                token_update = get_object_or_404(Token,token_name=token)
                form = TokenForm(data=request.POST or None, instance=token_update)
                if form.is_valid():
                    newtoken = form.save( commit=False )
                    if newtoken.user_id == request.user.id or request.user.is_superuser:
                        # if you changed the token name, delete old token
                        newtoken.save()
                        if newtoken.token_name != token:
                            deltoken = Token.objects.filter(token_name=token)
                            deltoken.delete()
                        messages.success(request, 'Sucessfully updated Token')
                        del request.session["token_name"]
                    else:
                        messages.error(request,"Cannot update.  You are not owner of this token or not superuser.")
                    #return HttpResponseRedirect(get_script_prefix()+'nduser/token/')
                    return redirect(getTokens)
                else:
                    #Invalid form
                    context = {'form': form}
                    #return render_to_response('updatetoken.html', context)
                    return render(request, 'updatetoken.html', context)
            elif 'backtotokens' in request.POST:
                #unrecognized option
                #return HttpResponseRedirect(get_script_prefix()+'nduser/token/')
                return redirect(getTokens)
            else:
                #unrecognized option
                return redirect(getTokens)
                #return HttpResponseRedirect(get_script_prefix()+'nduser/token/')
        else:
            print "Getting the update form"
            if "token_name" in request.session:
                token = request.session["token_name"]
            else:
                token = ""
            token_to_update = Token.objects.filter(token_name=token)
            data = {
                'token_name': token_to_update[0].token_name,
                'token_description':token_to_update[0].token_description,
                'project':token_to_update[0].project_id,
                'public':token_to_update[0].public,
            }
            form = TokenForm(initial=data)
            context = {'form': form}
            return render(request, 'updatetoken.html', context)
            #return render_to_response('updatetoken.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)
        #return redirect(get_script_prefix()+'projects', {"user":request.user})


@login_required(login_url='/nd/accounts/login/')
def updateProject(request):

    try:
        proj_name = request.session["project_name"]
        if request.method == 'POST':

            if 'UpdateProject' in request.POST:
                proj_update = get_object_or_404(Project,project_name=proj_name)
                form = ProjectForm(data= request.POST or None,instance=proj_update)
                if form.is_valid():
                    newproj = form.save(commit=False)
                    if newproj.user_id == request.user.id or request.user.is_superuser:
                        if newproj.project_name != proj_name:
                            messages.error ("Cannot change the project name.  MySQL cannot rename databases.")
                        else:
                            newproj.save()
                            messages.success(request, 'Sucessfully updated project ' + proj_name)
                    else:
                        messages.error(request,"Cannot update.  You are not owner of this project or not superuser.")
                    del request.session["project_name"]
                    return redirect(getProjects)
                else:
                    #Invalid form
                    context = {'form': form}
                    return render(request, 'updateproject.html', context)
            elif 'backtoprojects' in request.POST:
                return redirect(getProjects)
            else:
                #unrecognized option
                messages.error(request,"Unrecognized Post")
                return redirect(getProjects)

        else:
            #Get: Retrieve project and display update project form.
            if "project_name" in request.session:
                proj = request.session["project_name"]
            else:
                proj = ""
            project_to_update = Project.objects.filter(project_name=proj)
            data = {
                'project_name': project_to_update[0].project_name,
                'project_description':project_to_update[0].project_description,
                'dataset':project_to_update[0].dataset_id,
                'public':project_to_update[0].public,
                'host':project_to_update[0].host,
                'kvengine':project_to_update[0].kvengine,
                'kvserver':project_to_update[0].kvserver,
            }
            form = ProjectForm(initial=data)
            context = {'form': form}
            return render(request, 'updateproject.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)

@login_required(login_url='/nd/accounts/login/')
def createToken(request):

    try:
        prname = request.session['project']
        pr = Project.objects.get ( project_name = prname )

        if request.method == 'POST':
            if 'createtoken' in request.POST:

                form = TokenForm(request.POST)

                # restrict projects to user visible fields
                form.fields['project'].queryset = Project.objects.filter(user_id=request.user.id) | Project.objects.filter(public=1)

                if form.is_valid():
                    new_token = form.save(commit=False)
                    new_token.user_id = request.user.id
                    new_token.save()
                    return redirect(getTokens)
                else:
                    context = {'form': form}
                    return render(request, 'createtoken.html', context)
            elif 'backtotokens' in request.POST:
                return redirect(getTokens)
            else:
                messages.error(request,"Unrecognized Post")
                redirect(getTokens)
        else:
            '''Show the Create datasets form'''

            data = {
                'project': pr
            }
            form = TokenForm( initial = data )
            context = {'form': form, 'project': prname }
            return render(request, 'createtoken.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)

@login_required(login_url='/nd/accounts/login/')
def backupProject(request):
    """Backup some or all channels of a project"""

    try:

        # perform a backup
        if request.method == 'POST':

            if 'backup' in request.POST:

                form = BackupForm(request.POST)

                # bind the project
                prname = request.session["project"]

                if not form.is_valid():

                    context = {'form': form, 'project': prname}
                    return render(request, 'backup.html', context)
                    #return render_to_response('backup.html', context)

                else:

                    new_backup=form.save(commit=False)

                    # backup to the local file system  -- only option for now
                    # if new_backup.protocol == 'local':
                    if True:

                        # Get the database information
                        dbname = (request.POST.get('project')).strip()
                        pr = Project.objects.get(project_name=prname)

                        if request.POST.get('allchans') == 'on':
                            channel ='all'
                        elif new_backup.channel != None:
                            channel = new_backup.channel.channel_name
                        else:
                            raise  NDWSError ("Cannot backup specified channel {}".format(new_backup.channel))

                        #RB restart here
                        upath = '{}/{}'.format(settings.BACKUP_PATH,request.user.username)
                        ppath = '{}/{}'.format(upath,dbname)
                        fpath = '{}/{}'.format(ppath,channel)
                        if not os.path.exists(upath):
                            os.mkdir( upath, 0755 )
                        if not os.path.exists(ppath):
                            os.mkdir( ppath, 0755 )
                        if not os.path.exists(fpath):
                            os.mkdir( fpath, 0755 )

                        # database output file
                        ofile = '{}/{}.sql'.format(fpath,datetime.now().isoformat())
                        dbuser = settings.DATABASES['default']['USER']
                        passwd = settings.DATABASES['default']['PASSWORD']
                        cmd = ['mysqldump', '-u'+ dbuser, '-p'+ passwd, '--single-transaction', '-h', pr.host, dbname]

                        # json metadata file
                        jfile = '{}/{}.json'.format(fpath,datetime.now().isoformat())

                        # set the filenames
                        new_backup.filename = ofile
                        new_backup.jsonfile = jfile

                        with closing ( open(jfile, 'w')) as jsonfp:
                            with closing ( NDProjectsDB() ) as projdb:
                                proj = projdb.loadToken ( pr )
                                jsonfp.write ( ndwsrest.jsonInfo(proj) )

                        # if not all channels were requested
                        if request.POST.get('allchans') == 'on':
                            new_backup.channel = None
                        else:
                            # get list of tables
                            with closing(MySQLdb.connect (host = pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = pr.project_name )) as newconn:
                                with closing ( newconn.cursor() ) as newcursor:

                                    # all channel tables have a common prefix with underscore
                                    sql = "SHOW TABLES like \'{}_%\'".format(channel)

                                    newcursor.execute(sql)
                                    tables = newcursor.fetchall()

                                for t in tables:
                                    cmd.append(t[0])

                        # backup now
                        if request.POST.get('async'):

                            outputfile = open(ofile, 'w')
                            p = subprocess.Popen(cmd, stdout=outputfile)

                            new_backup.status = 1
                            new_backup.protocol = 'MySQL'
                            new_backup.save()

                            messages.success(request, 'Initiated backup in background.  Project: {}'.format(dbname))

                            # create a thread to monitor
                            import threading
                            t = threading.Thread ( target=_monitorBackup, args=(p,new_backup,outputfile) )
                            t.start()
                            return redirect(backupProject)

                        else:

                            with closing (open(ofile, 'w')) as outputfile:

                                po = subprocess.Popen(cmd, stdout=outputfile)
                                po.communicate(None)
                                rc = po.returncode
                                if rc<0:
                                    raise NDWSError("Backup process failed. Status = {}".format(rc))

                            new_backup.status = 0
                            new_backup.protocol = 'MySQL'
                            new_backup.save()

                            messages.success(request, 'Sucessfully backed up database '+ dbname)
                            return redirect(getProjects)

                    elif new_backup.protocol == 's3':
                        raise NDWSError ("Unimplemented backup protocol: s3")
                    else:
                        raise NDWSError ("Unkown protocol {}".format(new_backup.protocol))

            elif 'restore' in request.POST:
                request.session["backupid"] = (request.POST.get('backupid')).strip()
                return redirect(restoreProject)

            elif 'backtoprojects' in request.POST:
                return redirect(getProjects)


            elif 'delete' in request.POST:

                buid = (request.POST.get('backupid')).strip()

                try:
                    bu_to_delete = Backup.objects.get ( backup_id=buid )
                except Backup.DoesNotExist:
                    # no backup found
                    raise

                #delete the files
                cmd = ['rm', bu_to_delete.filename ]
                po = subprocess.Popen(cmd)
                po.communicate(None)
                rc = po.returncode
                if rc<0:
                    raise NDWSError("Failed to delete backup file. Status = {}".format(rc))

                cmd = ['rm', bu_to_delete.jsonfile ]
                po = subprocess.Popen(cmd)
                po.communicate(None)
                rc = po.returncode
                if rc<0:
                    raise NDWSError("Failed to delete backup metadata file. Status = {}".format(rc))

                # remove the backup record
                bu_to_delete.delete()

                return redirect(backupProject)

        # show the backup page
        else:
            """show the backup form"""

            # bind the project
            prname = request.session["project"]
            pr = Project.objects.get(project_name=prname)

            # get all channel choices
            channels = Channel.objects.filter(project_id=pr)

            # list the backups
            backups = Backup.objects.filter(project_id=pr)

            data = {
                'project': pr,
            }
            form = BackupForm(initial=data)

            # restrict datasets to user visible fields
            form.fields['channel'].queryset = channels

            context = {'form': form, 'project': prname, 'channels': channels, 'backups': backups }
            return render(request, 'backup.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)


@login_required(login_url='/nd/accounts/login/')
def restoreProject ( request ):

    try:
        # perform a backup
        if request.method == 'POST':

            if 'createproject' in request.POST:
                """Create a new project from previous backup"""

                bu = Backup.objects.get ( backup_id=request.POST.get("buid") )
                pr = Project.objects.get ( project_name=bu.project_id )
                ds = Dataset.objects.get ( dataset_name=pr.dataset_id )

                jfp = open ( bu.jsonfile )
                projmd = json.load ( jfp )

                # setup the project
                newproj = Project()
                newproj.project_name = request.POST.get("project_name")
                newproj.project_description = request.POST.get("project_description")
                newproj.user_id = request.user.id
                newproj.public = request.POST.get("public")
                newproj.host = request.POST.get("host")
                newproj.kvengine = 'MySQL'
                newproj.kvserver = request.POST.get("host")
                newproj.dataset = ds

                # restore the DB
                dbuser = settings.DATABASES['default']['USER']
                passwd = settings.DATABASES['default']['PASSWORD']

                with closing(MySQLdb.connect (host = newproj.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'])) as newconn:
                    with closing ( newconn.cursor() ) as newcursor:

                        # all channel tables have a common prefix with underscore
                        sql = "CREATE DATABASE {}".format(newproj.project_name)

                        newcursor.execute(sql)

                # upload the backup file to the database
                inputfile = open ( bu.filename )
                cmd = ['mysql', '-u'+ dbuser, '-p'+ passwd, '-h', newproj.host, newproj.project_name ]

                #synchronously or asynchrnously
                if request.POST.get('async'):

                    po_process = subprocess.Popen(cmd, stdin=inputfile)

                    # indicate that we are restoring.
                    bu.status = 3
                    bu.save()

                    messages.success(request, 'Initiated restore in background')

                    # create a thread to monitor
                    import threading
                    t = threading.Thread ( target=_monitorRestore, args=(po_process,newproj,bu,inputfile) )
                    t.start()
                    return redirect(backupProject)

                else:
                    po = subprocess.Popen(cmd)
                    po.communicate(None)
                    rc = po.returncode
                    if rc<0:
                        raise NDWSError("Failed to backup file. Status = {}".format(rc))

                # Having restored the database, add the channels, project and token
                newproj.save()
                inputfile.close()

                # default token?
                if 'token' in request.POST:
                    tk = Token ( token_name = newproj.project_name, token_description = 'Default token for public project', project_id=newproj, user_id=request.user.id, public=newproj.public )
                    tk.save()

                # is it a single channel backup or a whole project?
                if bu.channel == None:
                    chanlist = projmd['channels']
                else:
                    chanlist = [bu.channel]

                # Create channels
                for chnm in projmd['channels']:
                    ch = Channel()
                    ch.project = newproj
                    ch.channel_name = chnm
                    ch.channel_description = projmd['channels'][chnm]['description']
                    ch.channel_type = projmd['channels'][chnm]['channel_type']
                    ch.channel_datatype = projmd['channels'][chnm]['datatype']
                    ch.resolution = projmd['channels'][chnm]['resolution']
                    ch.propagate = projmd['channels'][chnm]['propagate']
                    ch.readonly = projmd['channels'][chnm]['readonly']
                    ch.exceptions =   projmd['channels'][chnm]['exceptions']
                    ch.startwindow = projmd['channels'][chnm]['windowrange'][0]
                    ch.endwindow = projmd['channels'][chnm]['windowrange'][1]

                    ch.save()

                messages.success(request, 'Sucessfully restored database '+ newproj.project_name)
                return redirect(getProjects)

            if 'createchannel' in request.POST:
                """Add new channel to existing project"""

                #synchronously or asynchrnously
                if request.POST.get('casync'):

                    # set the in process backup state
                    bu = Backup.objects.get ( backup_id=request.POST.get("buid") )
                    bu.status=3
                    bu.save()
                    print "Save here in web thread Value = {}".format(bu.status)

                    # create a thread to monitor
                    import threading
                    t = threading.Thread ( target=_restoreOneChannel, args=(request,) )
                    t.start()
                    return redirect(backupProject)
                    #return HttpResponseRedirect(get_script_prefix()+'nduser/backupproject/')

                else:

                    _restoreOneChannel ( request )

                return redirect(getProjects)


            elif 'backtoprojects' in request.POST:
                return redirect(getProjects)

            else:
                raise NDWSError ( "Bad post option.  Contact NeuroData support." )

        else:
            """Show the restore form"""

            buid = request.session["backupid"]

            bu = Backup.objects.get( backup_id=buid )
            pr = Project.objects.get ( project_name = bu.project )
            if bu.channel == None:
                ch = None
            else:
                ch = Channel.objects.get ( project=bu.project, channel_name = bu.channel )

            # initialize the forms
            pform = ProjectForm(instance=pr)
            if ch:
                cform = ChannelForm(instance=ch)
            else:
                cform = False  # or None

            filename = bu.filename
            jsonfile = bu.jsonfile

            # get all channel choices
            cprojs = Project.objects.filter(dataset=pr.dataset, user=request.user.id)

            context = {'cform': cform, 'pform': pform, 'filename': filename, 'buid': buid, 'cprojects': cprojs, 'project_name': pr.project_name}
            return render(request, 'restore.html', context)

    except Exception, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        return redirect(getProjects)


def _restoreOneChannel ( request ):
    """Restore on channel.  This can be called directly or in a thread for async"""

    bu = Backup.objects.get ( backup_id=request.POST.get("buid") )
    pr = Project.objects.get ( project_name=request.POST.get("cproject") )
    ds = Dataset.objects.get ( dataset_name=pr.dataset_id )

    jfp = open ( bu.jsonfile )
    projmd = json.load ( jfp )

    # old channel name in backup
    oldchnm = bu.channel.channel_name
    oldch = projmd['channels'][bu.channel.channel_name]
    # new channel name specified in form
    chnm = request.POST.get("channel_name")

    ch = Channel()
    ch.project = pr
    ch.channel_name = chnm
    ch.channel_description = request.POST.get("channel_description")
    ch.channel_type = oldch['channel_type']
    ch.channel_datatype = oldch['datatype']
    ch.resolution = oldch['resolution']
    ch.propagate = oldch['propagate']
    ch.readonly = oldch['readonly']
    ch.exceptions = oldch['exceptions']
    ch.startwindow = oldch['windowrange'][0]
    ch.endwindow = oldch['windowrange'][1]

    # with the project and the channels, restore the channel
    dbuser = settings.DATABASES['default']['USER']
    passwd = settings.DATABASES['default']['PASSWORD']

    with closing(MySQLdb.connect (host = pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'])) as newconn:
        with closing ( newconn.cursor() ) as newcursor:

            # create a temporary table to house the restore
            dbname = pr.project_name+''.join(random.choice(string.lowercase) for x in range(20))
            sql = "CREATE DATABASE {}".format(dbname)

            newcursor.execute(sql)

            # restore the database to temporary table
            inputfile = open ( bu.filename )
            cmd = ['mysql', '-u'+ dbuser, '-p'+ passwd, '-h', pr.host, dbname ]
            subprocess.Popen(cmd, stdin=inputfile).communicate(None)

            # loop through the tables copying to new channel names.
            # all channel tables have a common prefix with underscore
            sql = "SHOW TABLES in {}".format(dbname)

            newcursor.execute(sql)
            tables = newcursor.fetchall()

            for tbl in tables:

                # Change the prefix from old channel name to new channel name
                newtbl = re.sub ('^{}'.format(oldchnm),'{}'.format(chnm), tbl[0])

                # create a channel in the target db
                sql = 'CREATE table {}.{} SELECT * FROM {}.{}'.format(pr.project_name,newtbl,dbname,tbl[0])
                newcursor.execute(sql)

            # drop temp database
            sql = 'DROP DATABASE {}'.format(dbname)
            newcursor.execute(sql)

    messages.success(request, 'Sucessfully restored channel: {} to project: {}  '.format(ch.channel_name, ch.project))

    # if it was async, clear the restoring state oon the backup
    if request.POST.get('casync'):
        bu.status=0
        bu.save()

    # having restored the db, save the channel
    ch.save()


def _monitorBackup ( popen_process, backup_model, fh ):
    """Track the state of the backup subprocess and update the required field"""

    # wait for the process to finish
    popen_process.communicate(None)
    rc = popen_process.returncode

    # backup failed
    if rc<0:
        backup_model.status = 2
    else:
        # update the state
        backup_model.status = 0
    backup_model.save()

    fh.close()

def _monitorRestore ( popen_process, project_model, backup_model, fh ):
    """Track the state of the restore subprocess and update the required field"""

    # wait for the process to finish
    popen_process.communicate(None)
    rc = popen_process.returncode

    # backup failed
    if rc<0:
        backup_model.status = 5
    else:
        # update the state
        backup_model.status = 0
    backup_model.save()
    project_model.save()

    fh.close()

@login_required(login_url='/nd/accounts/login/')
def downloadData(request):

    try:

        if request.method == 'POST':
            form = dataUserForm(request.POST)
            if form.is_valid():
                curtoken = request.POST.get('token')
                if curtoken == "other":
                    curtoken = request.POST.get('other')

                format = form.cleaned_data['format']
                resolution = form.cleaned_data['resolution']
                xmin=form.cleaned_data['xmin']
                xmax=form.cleaned_data['xmax']
                ymin=form.cleaned_data['ymin']
                ymax=form.cleaned_data['ymax']
                zmin=form.cleaned_data['zmin']
                zmax=form.cleaned_data['zmax']
                webargs = curtoken+"/"+format+"/"+str(resolution)+"/"+str(xmin)+","+str(xmax)+"/"+str(ymin)+","+str(ymax)+"/"+str(zmin)+","+str(zmax)+"/"

                if format == 'hdf5':
                    return django.http.HttpResponse(ndwsrest.getCutout(webargs), content_type="product/hdf5" )
                elif format == 'npz':
                    return django.http.HttpResponse(ndwsrest.getCutout(webargs), content_type="product/npz" )
                else:
                    return django.http.HttpResponse(ndwsrest.getCutout(webargs), content_type="product/zip" )

            else:
                return redirect(downloadData)
        else:
            # Load Download page with public tokens
            form = dataUserForm()
            tokens = NDToken.public_list()
            context = {'form': form ,'publictokens': tokens}
            return render(request, 'download.html', context)
    except NDWSError, e:
        messages.error(request, "Exception in administrative interface = {}".format(e))
        tokens = NDToken.public_list()
        return redirect(downloadData)
