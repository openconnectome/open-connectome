FROM ubuntu:14.04
MAINTAINER Kunal Lillaney <lillaney@jhu.edu>

# apt-get update and install packages
RUN apt-get update && -y install \
  nginx\
  git\
  bash-completion\
  python-virtualenv\
  libhdf5-dev\
  libxslt1-dev\
  libmemcached-dev\
  g++\
  libjpeg-dev\
  virtualenvwrapper\
  python-dev\
  mysql-server-5.6\
  libmysqlclient-dev\
  xfsprogs\
  supervisor\
  rabbitmq-server\
  uwsgi\
  uwsgi-plugin-python\
  liblapack-dev\
  wget

# pip install packages
RUN pip install \
  cython\
  numpy
RUN pip install \
  django\
  pytest\
  posix_ipc\
  boto3\
  nibabel\
  networkx\
  requests\
  lxml\
  h5py\
  pylibmc\
  pillow\
  blosc\
  django-registration\
  django-celery\
  mysql-python\
  libtiff

# make neurodata user
RUN groupadd -r neurodata && useradd -r -m -g neurodata neurodata

# make the logging directory
RUN mkdir /var/log/neurodata
RUN chown www-data:www-data /var/log/neurodata
RUN chmod -R 777 /var/log/neurodata

# rest happens in user land
USER neurodata

# add github ssh key to known hosts
RUN mkdir ~/.ssh
RUN ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# clone the repo
WORKDIR /home/neurodata
RUN git clone https://github.com/neurodata/ndstore.git
WORKDIR /home/neurodata/ndstore
RUN git checkout microns
RUN git submodule init
RUN git submodule update

# build ocplib ctypes functions
WORKDIR /home/neurodata/ndstore/ndlib/c_version
RUN make -f makefile_LINUX  

# configure mysql
WORKDIR /home/neurodata/ndstore/django
USER root
RUN service mysql start && mysql -u root -i -e "create user 'neurodata'@'localhost' identified by 'neur0data';" &&\
  mysql -u root -i -e "grant all privileges on *.* to 'neurodata'@'localhost' with grant option;" &&\
  mysql -u neurodata -pneur0data -i -e "CREATE DATABASE neurodjango;"

# move nginx config files and start service
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /home/neurodata/ndstore/setup/docker_config/nginx/ndstore.conf /etc/nginx/sites-enabled/
RUN ln -s /home/neurodata/ndstore/setup/docker_config/nginx/nginx.conf /etc/nginx/
RUN service nginx start

# move uwsgi config files and start service
RUN ln -s /home/neurodata/ndstore/setup/docker_config/uwsgi/ndstore.ini /etc/uwsgi/apps-available/
RUN ln -s /home/neurodata/ndstore/setup/docker_config/uwsgi/ndstore.ini /etc/uwsgi/apps-enabled/
RUN service uwsgi start

# move celery config files and start service
RUN ln -s /home/neurodata/ndstore/setup/docker_config/celery/propagate.conf /etc/supervisor/conf.d/propagate.conf
RUN ln -s /home/neurodata/ndstore/setup/docker_config/celery/ingest.conf /etc/supervisor/conf.d/ingest.conf
RUN service supervisor start
RUN service rabbitmq-server start

# open the port
EXPOSE 80

USER neurodata
