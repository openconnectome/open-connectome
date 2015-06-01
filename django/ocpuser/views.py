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


# RBTODO createproject doesn't throw an error to the browser

import django.http
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.template import Context
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.forms.models import inlineformset_factory
import django.forms

import ocpcaprivate
import ocpcarest
import ocpcaproj
import string
import random
import MySQLdb

from models import Project
from models import Dataset
from models import Token
from models import Channel

from forms import ProjectForm
from forms import DatasetForm
from forms import TokenForm
from forms import ChannelForm
from forms import dataUserForm

from django.core.urlresolvers import get_script_prefix
import os
import subprocess
from ocpcaerror import OCPCAError

import logging
logger=logging.getLogger("ocp")

# Helpers

''' Base url just redirects to welcome'''
def default(request):
  return redirect(get_script_prefix()+'profile', {"user":request.user})

''' Little welcome message'''
@login_required(login_url='/ocp/accounts/login/')
def profile(request):

  try:
    if request.method == 'POST':
      if 'filter' in request.POST:
        #FILTER PROJECTS BASED ON INPUT VALUE
        userid = request.user.id
        filteroption = request.POST.get('filteroption')
        filtervalue = (request.POST.get('filtervalue')).strip()
        
        pd = ocpcaproj.OCPCAProjectsDB()

        # get the visible data sets
        if request.user.is_superuser:
          visible_datasets=Dataset.objects.all()
        else:
          visible_datasets=Dataset.objects.filter(user_id=userid) | Dataset.objects.filter(public=1)

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

        return render_to_response('profile.html', { 'databases': dbs.iteritems() ,'projects': visible_projects.values_list(flat=True) },context_instance=RequestContext(request))

      elif 'delete_data' in request.POST:

        pd = ocpcaproj.OCPCAProjectsDB()
        username = request.user.username
        project_to_delete = (request.POST.get('project_name')).strip()
                
        reftokens = Token.objects.filter(project_id=project_to_delete)
        if reftokens:
          messages.error(request, 'Project cannot be deleted. Please delete all tokens for this project first.')
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
        else:
          proj = Project.objects.get(project_name=project_to_delete)
          if proj:
            if proj.user_id == request.user.id or request.user.is_superuser:
              #Delete project from the table followed  by the database.
              # deleting a project is super dangerous b/c you may delete it out from other tokens.
              #  on other servers.  So, only delete when it's on the same server for now
              pd.deleteOCPCADB(project_to_delete)
              proj.delete()          
              messages.success(request,"Project deleted")
            else:
              messages.error(request,"Cannot delete.  You are not owner of this project or not superuser.")
          else:
            messages.error( request,"Project not found.")
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')

      elif 'delete' in request.POST:
        pd = ocpcaproj.OCPCAProjectsDB()
        username = request.user.username
        project_to_delete = (request.POST.get('project_name')).strip()
                
        reftokens = Token.objects.filter(project_id=project_to_delete)
        if reftokens:
          messages.error(request, 'Project cannot be deleted. Please delete all tokens for this project first.')
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
        else:
          proj = Project.objects.get(project_name=project_to_delete)
          if proj:
            if proj.user_id == request.user.id or request.user.is_superuser:
              #Delete project from the table followed  by the database.
              # RBTODO deleting a project is super dangerous b/c you may delete it out from other tokens.
              #  on other servers.  So, only delete when it's on the same server for now
              #if proj.getKVServer()==proj.getDBHost():
              #   pd.deleteOCPCADB(project_to_delete)
              proj.delete()          
              messages.success(request,"Project deleted")
            else:
              messages.error(request,"Cannot delete.  You are not owner of this project or not superuser.")
          else:
            messages.error( request,"Project not found.")
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
      
      elif 'info' in request.POST:
      #GET PROJECT INFO -----------TODO
        token = (request.POST.get('roptions')).strip()
        return HttpResponse(ocpcarest.projInfo(token), content_type="product/hdf5" )
      
      elif 'update' in request.POST:
        project_to_update =(request.POST.get('project_name')).strip() 
        request.session["project_name"] = project_to_update
        return redirect(updateproject)
      
      elif 'tokens' in request.POST:
        projname=(request.POST.get('project_name')).strip()
        request.session["project"] = projname
        return redirect(get_tokens)

      elif 'channels' in request.POST:
        projname=(request.POST.get('project_name')).strip()
        request.session["project"] = projname
        return redirect(get_channels)

      elif 'backup' in request.POST:
        path = ocpcaprivate.backuppath + '/' + request.user.username
        if not os.path.exists(path):
          os.mkdir( path, 0755 )
        # Get the database information
        pd = ocpcaproj.OCPCAProjectsDB()
        db = (request.POST.get('project_name')).strip()
        ofile = path +'/'+ db +'.sql'
        outputfile = open(ofile, 'w')
        dbuser =ocpcaprivate.dbuser
        passwd =ocpcaprivate.dbpasswd

        p = subprocess.Popen(['mysqldump', '-u'+ dbuser, '-p'+ passwd, '--single-transaction', '--opt', db], stdout=outputfile).communicate(None)
        messages.success(request, 'Sucessfully backed up database '+ db)
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')

      else:
        # Invalid POST
        messages.error(request,"Unrecognized POST")
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')

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

      return render_to_response('profile.html', { 'databases': sorted(dbs.iteritems()) ,'projects':visible_projects },context_instance=RequestContext(request))
    
  except OCPCAError, e:

    messages.error(request,"Unknown exception in administrative interface = {}".format(e)) 

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
    return render_to_response('profile.html', { 'databases': dbs.iteritems() ,'projects':all_projects },context_instance=RequestContext(request))
    

@login_required(login_url='/ocp/accounts/login/')
def get_datasets(request):

  try:

    pd = ocpcaproj.OCPCAProjectsDB()

    userid = request.user.id
    if request.user.is_superuser:
      visible_datasets=Dataset.objects.all()
    else:
      visible_datasets= Dataset.objects.filter(user_id=userid) | Dataset.objects.filter(public=1)

    if request.method == 'POST':

      if 'filter' in request.POST:
        filtervalue = (request.POST.get('filtervalue')).strip()
        visible_datasets = visible_datasets.filter(dataset_name=filtervalue)
        return render_to_response('datasets.html', { 'dts': visible_datasets },context_instance=RequestContext(request))

      elif 'delete' in request.POST:

        #delete specified dataset
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
            visible_datasets=Dataset.objects.all()
          else:
            visible_datasets=Dataset.objects.filter(user=request.user.id) | Dataset.objects.filter(public=1)

        return render_to_response('datasets.html', { 'dts': visible_datasets },context_instance=RequestContext(request))
      elif 'update' in request.POST:
        ds = (request.POST.get('dataset_name')).strip()
        request.session["dataset_name"] = ds
        return redirect(updatedataset)

      else:
        #Load datasets
        return render_to_response('datasets.html', { 'dts': visible_datasets },context_instance=RequestContext(request))

    else:
      # GET datasets
      return render_to_response('datasets.html', { 'dts': visible_datasets },context_instance=RequestContext(request))

  except OCPCAError, e:
    messages.error(request, "Unknown exception in administrative interface = {}".format(e)) 
    return render_to_response('datasets.html', { 'dts': visible_datasets },context_instance=RequestContext(request))    

@login_required(login_url='/ocp/accounts/login/')
def get_alltokens(request):

  if 'filter' in request.POST:
    del request.session['filter']
  if 'project' in request.session:
    del request.session['project']

  return get_tokens(request)


@login_required(login_url='/ocp/accounts/login/')
def get_channels(request):

  #RBTODO check default for uniqueness
  #RBTODO make default T/F and prepopulate
  username = request.user.username
  pd = ocpcaproj.OCPCAProjectsDB()  

  try:
    if request.method == 'POST':
      if 'filter' in request.POST:
        # Filter channels based on an input value
        filteroption = request.POST.get('filteroption')
        filtervalue = (request.POST.get('filtervalue')).strip()
        all_channels = Channel.objects.filter(project_id='TODO').filter(token_name=filtervalue)
        return render_to_response('channel.html', { 'channels': all_channels, 'project': proj },context_instance=RequestContext(request))

      elif 'delete' in request.POST:
        # Delete the channel from the project
        channel_to_delete = (request.POST.get('channel')).strip()
        prname = request.session["project"]
        pr = Project.objects.get(project_name=prname)
        ch = Channel.objects.get(channel_name=channel_to_delete, project_id=pr )
        if ch:
          if pr.user_id == request.user.id or request.user.is_superuser:
            pd.deleteOCPCAChannel(pr, ch.channel_name)
            ch.delete()
            messages.success(request,"Channel deleted " + channel_to_delete)
          else:
            messages.error(request,"Cannot delete.  You are not owner of this token or not superuser.")
        else:
          messages.error(request,"Unable to delete " + channel_to_delete)
        return redirect(get_channels)

      # update form populated with channel fields
      elif 'update' in request.POST:
        channel = (request.POST.get('channel')).strip()
        request.session["channel_name"] = channel
        return redirect(updatechannel)

      # add using the update channel form with no initial data
      elif 'add' in request.POST:
        # must remove channel_name context to add a new one.  otherwise, it's an update
        if "channel_name" in request.session:
          del ( request.session["channel_name"] )
        return redirect(updatechannel)

      elif 'backtochannels' in request.POST:
        return redirect(get_channels)

      elif 'backtoprojects' in request.POST:
        return redirect(profile)


      else:
        # Unrecognized Option
        messages.error(request,"Invalid request")
        return redirect(get_channels)

    else:
      # GET tokens for the specified project
      username = request.user.username
      if "project" in request.session:
        proj = request.session["project"]
        all_channels = Channel.objects.filter(project_id=proj)
      else:
        # Unrecognized Option
        messages.error("Must have a project context to look at channels.")
        return redirect(get_channels)
      print all_channels
      return render_to_response('channel.html', { 'channels': all_channels, 'project': proj },context_instance=RequestContext(request))
    
  except OCPCAError, e:
    messages.error("Unknown exception in administrative interface = {}".format(e)) 
    datasets = pd.getDatasets()
    return render_to_response('profile.html',context,context_instance=RequestContext(request))
 

@login_required(login_url='/ocp/accounts/login/')
def get_tokens(request):

  username = request.user.username
  pd = ocpcaproj.OCPCAProjectsDB()  

  try:
    if request.method == 'POST':
      if 'filter' in request.POST:
        # Filter tokens based on an input value
        filteroption = request.POST.get('filteroption')
        filtervalue = (request.POST.get('filtervalue')).strip()
        all_tokens = Token.objects.filter(token_name=filtervalue)
        proj=""
        return render_to_response('token.html', { 'tokens': all_tokens, 'project': proj },context_instance=RequestContext(request))

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
        return redirect(get_tokens)

      elif 'downloadtoken' in request.POST:
        # Download the token in a test file
        token = (request.POST.get('token')).strip()
        response = HttpResponse(token,content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="ocpca.token"'
        return response

      elif 'update' in request.POST:
        # update project token
        token = (request.POST.get('token')).strip()
        request.session["token_name"] = token
        return redirect(updatetoken)

      # redirect to add a token
      elif 'add' in request.POST:
        # RBTODO prepopulate the project for the token
        # RBTODO make tokens captive to project button
        return redirect(createtoken)

      elif 'backtoprojects' in request.POST:
         return redirect(profile) 

      else:
        # Unrecognized Option
        messages.error(request,"Invalid request")
        return redirect(get_tokens)

    else:
      # GET tokens for the specified project
      username = request.user.username
      if "project" in request.session:
        proj = request.session["project"]
        all_tokens = Token.objects.filter(project_id=proj)
      else:
        proj=""
        all_tokens = Token.objects.all()
      return render_to_response('token.html', { 'tokens': all_tokens, 'project': proj },context_instance=RequestContext(request))
    
  except OCPCAError, e:
    messages.error("Unknown exception in administrative interface = {}".format(e)) 
    datasets = pd.getDatasets()
    return render_to_response('datasets.html', { 'dts': datasets },context_instance=RequestContext(request))


@login_required(login_url='/ocp/accounts/login/')
def createproject(request):

  pd = ocpcaproj.OCPCAProjectsDB()  

  if request.method == 'POST':
    if 'createproject' in request.POST:

      form = ProjectForm(request.POST)
      
      # restrict datasets to user visible fields
      form.fields['dataset'].queryset = Dataset.objects.filter(user_id=request.user.id) | Dataset.objects.filter(public=1)

      if form.is_valid():
        new_project=form.save(commit=False)
        new_project.user_id=request.user.id
        if request.POST.get('legacy') == 'yes':
          new_project.ocp_version='0.0'
        else:
          new_project.ocp_version=ocpcaproj.OCP_VERSION
        new_project.schema_version=ocpcaproj.SCHEMA_VERSION
        new_project.save()
        try:
          # create a database when not linking to an existing databases
          if not request.POST.get('nocreate') == 'on':
            pd.newOCPCAProject( new_project.project_name )
          if 'token' in request.POST:
            tk = Token ( token_name = new_project.project_name, token_description = 'Default token for public project', project_id=new_project, user_id=request.user.id, public=new_project.public ) 
            tk.save()

          ## RBTODO create a default channel

        except Exception, e:
          logger.error("Failed to create project.  Error {}".format(e))
          new_project.delete()

        return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile/')
      else:
        context = {'form': form}
        print form.errors
        return render_to_response('createproject.html',context,context_instance=RequestContext(request))

    else:
      #default
      return redirect(profile)
  else:
    '''Show the Create Project form'''

    form = ProjectForm()

    # restrict datasets to user visible fields
    form.fields['dataset'].queryset = Dataset.objects.filter(user_id=request.user.id) | Dataset.objects.filter(public=1)

    context = {'form': form}
    return render_to_response('createproject.html',context,context_instance=RequestContext(request))
      
@login_required(login_url='/ocp/accounts/login/')
def createdataset(request):
 
  if request.method == 'POST':
    if 'createdataset' in request.POST:
      form = DatasetForm(request.POST)
      if form.is_valid():
        new_dataset=form.save(commit=False)
        new_dataset.user_id=request.user.id
        new_dataset.save()
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/datasets')
      else:
        context = {'form': form}
        print form.errors
        return render_to_response('createdataset.html',context,context_instance=RequestContext(request))
    elif 'backtodatasets' in request.POST:
      return redirect(get_datasets)
    else:
      #default
      messages.error(request,"Unkown POST request.")
      return redirect(get_datasets)
  else:
    '''Show the Create datasets form'''
    form = DatasetForm()
    context = {'form': form}
    return render_to_response('createdataset.html',context,context_instance=RequestContext(request))


@login_required(login_url='/ocp/accounts/login/')
def updatedataset(request):

  # Get the dataset to update
  ds = request.session["dataset_name"]
  if request.method == 'POST':
    if 'UpdateDataset' in request.POST:
      ds_update = get_object_or_404(Dataset,dataset_name=ds)

      if ds_update.user_id == request.user.id or request.user.is_superuser:

        form = DatasetForm(data=request.POST or None,instance=ds_update)
        if form.is_valid():
          form.save()
          messages.success(request, 'Sucessfully updated dataset')
          del request.session["dataset_name"]
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/datasets')
        else:
          #Invalid form
          context = {'form': form}
          print form.errors
          return render_to_response('updatedataset.html',context,context_instance=RequestContext(request))

      else:
        messages.error(request,"Cannot update.  You are not owner of this dataset or not superuser.")
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/datasets')

    elif 'backtodatasets' in request.POST:
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/datasets')
    else:
      #unrecognized option
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/datasets')
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
      'starttime':ds_to_update[0].starttime,
      'endtime':ds_to_update[0].endtime,
      'dataset_description':ds_to_update[0].dataset_description,
            }
    form = DatasetForm(initial=data)
    context = {'form': form}
    return render_to_response('updatedataset.html',context,context_instance=RequestContext(request))


@login_required(login_url='/ocp/accounts/login/')
def updatechannel(request):

  prname = request.session['project']
  pr = Project.objects.get ( project_name = prname )
  pd = ocpcaproj.OCPCAProjectsDB()
  if request.method == 'POST':

    if 'updatechannel' in request.POST: 

      chname = request.session["channel_name"]
      channel_to_update = get_object_or_404(Channel,channel_name=chname,project_id=pr)
      form = ChannelForm(data=request.POST or None, instance=channel_to_update)

      if form.is_valid():
        newchannel = form.save(commit=False)

      else:
        #Invalid form
        context = {'form': form, 'project': prname}
        return render_to_response('updatechannel.html', context, context_instance=RequestContext(request))

    elif 'createchannel' in request.POST:

      form = ChannelForm(data=request.POST or None)

      if form.is_valid():

        new_channel = form.save( commit=False )

        # populate the channel type and data type from choices
        combo = request.POST.get('channelcombo')
        if combo=='i:8':
          new_channel.channel_type='IMAGES'
          new_channel.channel_datatype='uint8'
        elif combo=='i:16':
          new_channel.channel_type='IMAGES'
          new_channel.channel_datatype='uint16'
        elif combo=='i:32':
          new_channel.channel_type='RGB'
          new_channel.channel_datatype='uint32'
        elif combo=='a:32':
          new_channel.channel_type='ANNOTATIONS'
          new_channel.channel_datatype='uint32'
        elif combo=='p:32':
          new_channel.channel_type='PROBABILITY_MAPS'
          new_channel.channel_datatype='float32'
        elif combo=='t:8':
          new_channel.channel_type='TIMESERIES'
          new_channel.channel_datatype='uint8'
        elif combo=='t:16':
          new_channel.channel_type='TIMESERIES'
          new_channel.channel_datatype='uint16'
        else:
          logger.error("Illegal channel combination requested: {}.".format(combo))
          messages.error(request,"Illegal channel combination requested or none selected.")
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/channels')

        if pr.user_id == request.user.id or request.user.is_superuser:

          # if there is no default channel, make this default
          if not Channel.objects.filter(project_id=pr, default=True):
            new_channel.default = True

          new_channel.save()

          if not request.POST.get('nocreate') == 'on':

            try:
              # create the tables for the channel
              pd.newOCPCAChannel( pr.project_name, new_channel.channel_name)
            except Exception, e:
              logger.error("Failed to create channel. Error {}".format(e))
              messages.error(request,"Failed to create channel. {}".format(e))
              new_channel.delete()

          return HttpResponseRedirect(get_script_prefix()+'ocpuser/channels')

        else:
          messages.error(request,"Cannot update.  You are not owner of this token or not superuser.")
          return HttpResponseRedirect(get_script_prefix()+'ocpuser/channels')

      else:
        #Invalid form
        context = {'form': form, 'project': prname}
        return render_to_response('createchannel.html', context, context_instance=RequestContext(request))

    else:
      #unrecognized option
      return redirect(get_channels)

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
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/channels')

    else:
      messages.error(request,"Cannot update.  You are not owner of this token or not superuser.")
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/channels')

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
        'default':channel_to_update[0].default,
        'exceptions':channel_to_update[0].exceptions,
        'propagate':channel_to_update[0].propagate,
        'startwindow':channel_to_update[0].startwindow,
        'endwindow':channel_to_update[0].endwindow,
        'project': pr
      }
      form = ChannelForm(initial=data)
      context = {'form': form, 'project': prname }
      return render_to_response('updatechannel.html', context, context_instance=RequestContext(request))
    else:
      data = {
        'project': pr
      }
      form = ChannelForm(initial=data)
      context = {'form': form, 'project': prname }
      return render_to_response('createchannel.html', context, context_instance=RequestContext(request))


@login_required(login_url='/ocp/accounts/login/')
def updatetoken(request):

  # Get the dataset to update
  token = request.session["token_name"]
  if request.method == 'POST':
    if 'UpdateToken' in request.POST:
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
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/token')
      else:
        #Invalid form
        context = {'form': form}
        print form.errors
        return render_to_response('updatetoken.html',context,context_instance=RequestContext(request))
    elif 'backtotokens' in request.POST:
      #unrecognized option
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/token')
    else:
      #unrecognized option
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/token')
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
    return render_to_response('updatetoken.html',context,context_instance=RequestContext(request))

@login_required(login_url='/ocp/accounts/login/')
def updateproject(request):

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
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
      else:
        #Invalid form
        context = {'form': form}
        return render_to_response('updateproject.html',context,context_instance=RequestContext(request))
    elif 'backtoprojects' in request.POST:
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
    else:
      #unrecognized option
      messages.error(request,"Unrecognized Post")
      return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
      
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
    return render_to_response('updateproject.html',context,context_instance=RequestContext(request))

@login_required(login_url='/ocp/accounts/login/')
def createtoken(request):

  if request.method == 'POST':
    if 'createtoken' in request.POST:

      form = TokenForm(request.POST)

      # restrict projects to user visible fields
      form.fields['project'].queryset = Project.objects.filter(user_id=request.user.id) | Project.objects.filter(public=1)

      if form.is_valid():
        new_token=form.save(commit=False)
        new_token.user_id=request.user.id
        new_token.save()
        return HttpResponseRedirect(get_script_prefix()+'ocpuser/profile')
      else:
        context = {'form': form}
        print form.errors
        return render_to_response('createtoken.html',context,context_instance=RequestContext(request))
    elif 'backtotokens' in request.POST:
       return redirect(get_tokens) 
    else:
      messages.error(request,"Unrecognized Post")
      redirect(get_tokens)
  else:
    '''Show the Create datasets form'''
    form = TokenForm()

    # restrict projects to user visible fields
    form.fields['project'].queryset = Project.objects.filter(user_id=request.user.id) | Project.objects.filter(public=1)

    context = {'form': form}
    return render_to_response('createtoken.html',context,context_instance=RequestContext(request))
      
@login_required(login_url='/ocp/accounts/login/')
def restoreproject(request):

  if request.method == 'POST':
   
    if 'RestoreProject' in request.POST:
      form = ProjectForm(request.POST)
      if form.is_valid():
        project = form.cleaned_data['project_name']
        description = form.cleaned_data['project_description']        
        dataset = form.cleaned_data['dataset']
        datatype = form.cleaned_data['datatype']
        overlayproject = form.cleaned_data['overlayproject']
        overlayserver = form.cleaned_data['overlayserver']
        resolution = form.cleaned_data['resolution']
        exceptions = form.cleaned_data['exceptions']        
        dbhost = form.cleaned_data['host']        
        kvengine=form.cleaned_data['kvengine']
        kvserver=form.cleaned_data['kvserver']
        propagate =form.cleaned_data['propagate']
        username = request.user.username
        nocreateoption = request.POST.get('nocreate')
        if nocreateoption =="on":
          nocreate = 1
        else:
          nocreate = 0
        new_project= form.save(commit=False)
        new_project.user = request.user
        new_project.save()
        # Get database info
        pd = ocpcaproj.OCPCAProjectsDB()
        
        bkupfile = request.POST.get('backupfile')
        path = ocpcaprivate.backuppath+ '/'+ request.user.username + '/' + bkupfile
        if os.path.exists(path):
          print "File exists"
        else:
          #TODO - Return error
          print "Error"
        proj=pd.loadProjectDB(project)
        
        
        #Create the database
        newconn = MySQLdb.connect (host = dbhost, user = ocpcaprivate.dbuser, passwd = ocpcaprivate.dbpasswd, db=ocpcaprivate.db )
        newcursor = newconn.cursor()
        
        try:
          sql = "Create database " + project  
          newcursor.execute(sql)
        except Exception:
          print("Database already exists")
          
          
      # close connection just to be sure
        newcursor.close()
        dbuser = ocpcaprivate.dbuser
        passwd = ocpcaprivate.dbpasswd
      
        proc = subprocess.Popen(["mysql", "--user=%s" % dbuser, "--password=%s" % passwd, project],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        proc.communicate(file(path).read())
        messages.success(request, 'Sucessfully restored database '+ project)
        return redirect(profile)
    
      else:
        #Invalid Form
        context = {'form': form}
        print form.errors
        return render_to_response('profile.html',context,context_instance=RequestContext(request))
    else:
      #Invalid post - redirect to profile for now
      return redirect(profile)
  else:        
      #GET DATA
    randtoken = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(64))
    form = ProjectForm(initial={'token': randtoken})
    path = ocpcaprivate.backuppath +'/'+ request.user.username
    if os.path.exists(path):
      file_list =os.listdir(path)   
    else:
      file_list={}
    context = Context({'form': form, 'flist': file_list})
    return render_to_response('restoreproject.html',context,context_instance=RequestContext(request))

@login_required(login_url='/ocp/accounts/login/')
def downloaddata(request):
  
  try:
    pd = ocpcaproj.OCPCAProjectsDB()
    
    if request.method == 'POST':
      form= dataUserForm(request.POST)
      if form.is_valid():
        curtoken=request.POST.get('token')
        if curtoken=="other":
          curtoken=request.POST.get('other')
          
        format = form.cleaned_data['format']
        resolution = form.cleaned_data['resolution']
        xmin=form.cleaned_data['xmin']
        xmax=form.cleaned_data['xmax']
        ymin=form.cleaned_data['ymin']
        ymax=form.cleaned_data['ymax']
        zmin=form.cleaned_data['zmin']
        zmax=form.cleaned_data['zmax']
        webargs= curtoken+"/"+format+"/"+str(resolution)+"/"+str(xmin)+","+str(xmax)+"/"+str(ymin)+","+str(ymax)+"/"+str(zmin)+","+str(zmax)+"/"
          
        if format=='hdf5':
          return django.http.HttpResponse(ocpcarest.getCutout(webargs), content_type="product/hdf5" )
        elif format=='npz':
          return django.http.HttpResponse(ocpcarest.getCutout(webargs), content_type="product/npz" )
        else:
          return django.http.HttpResponse(ocpcarest.getCutout(webargs), content_type="product/zip" )
          
      else:
        return redirect(downloaddata)
        #return render_to_response('download.html',context_instance=RequestContext(request))
    else:
      # Load Download page with public tokens                                           
      pd = ocpcaproj.OCPCAProjectsDB()
      form = dataUserForm()
      tokens = pd.getPublic ()
      context = {'form': form ,'publictokens': tokens}
      return render_to_response('download.html',context,context_instance=RequestContext(request))
      #return render_to_response('download.html', { 'dts': datasets },context_instance=\
      # RequestContext(request))                                                                
  except OCPCAError, e:
    messages.error("Unknown exception in administrative interface = {}".format(e)) 
    tokens = pd.getPublic ()
    return redirect(downloaddata)
