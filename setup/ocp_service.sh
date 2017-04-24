#!/bin/bash
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

# Script to restart services in NeuroData

if [ $1 == "-h" ]; then
  echo "Usage: service(all | nginx) command(start | stop | restart)"
    exit 0
fi

if [ $1 == "all" ]; then
  declare -a service_arr=("nginx" "uwsgi" "celery" "supervisor" "rabbitmq-server" "redis")
elif [ $1 == "nginx" ]; then
  declare -a service_arr=("nginx" "uwsgi")
else
  echo "Incorrect service",$1
fi

for service in "${service_arr[@]}"
do
  sudo service $service $2
done
