FROM ubuntu:14.04
MAINTAINER Kunal Lillaney <lillaney@jhu.edu>

#Remove pesky problems 
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -sf /bin/true /sbin/initctl
RUN echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d

# apt-get update and install packages
RUN apt-get update -y && apt-get install -y \
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
  mysql-server\
  libmysqlclient-dev\
  xfsprogs\
  supervisor\
  rabbitmq-server\
  uwsgi\
  uwsgi-plugin-python\
  liblapack-dev\
  wget\
  libmysqlclient-dev\
  rabbitmq-server\
  libssl-dev\
  libffi-dev\
  python-pytest
  
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
  django-cors-headers\
  libtiff

# make neurodata user
RUN groupadd -r neurodata && useradd -r -m -g neurodata neurodata

# make the logging directory
RUN mkdir /var/log/neurodata
RUN touch /var/log/neurodata/ndstore.log
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
USER root
RUN pip install -e git+git://github.com/unbit/uwsgi.git#egg=uwsgi
RUN pip freeze 
RUN pip install -U -r setup/requirements.txt

# build ocplib ctypes functions
WORKDIR /home/neurodata/ndstore/ndlib/c_version
RUN make -f makefile_LINUX  

# configure mysql
RUN chmod -R 755 /var/run/mysqld/
RUN cat /var/log/mysql/error.log
WORKDIR /home/neurodata/ndstore/django
RUN replace "127.0.0.1" "localhost" -- /etc/mysql/my.cnf
RUN service mysql restart
RUN chmod 777 /var/run/mysqld/mysqld.sock

#USER root
RUN service mysql start && mysql -u root -i -e "create user 'neurodata'@'localhost' identified by 'neur0data';" &&\
  mysql -u root -i -e "grant all privileges on *.* to 'neurodata'@'localhost' with grant option;" &&\
  mysql -u neurodata -pneur0data -i -e "CREATE DATABASE neurodjango;"

RUN /etc/init.d/mysql restart
#RUN mysqladmin -u neurodata -p neur0data status

# configure django
RUN cp /home/neurodata/ndstore/django/ND/settings.py.example /home/neurodata/ndstore/django/ND/settings.py
RUN cp /home/neurodata/ndstore/setup/docker_config/django/docker_settings_secret.py /home/neurodata/ndstore/django/ND/settings_secret.py

# django migrate
RUN chmod -R 777 /var/log/neurodata/
RUN python /home/neurodata/ndstore/django/manage.py migrate; echo "from django.contrib.auth.models import User; User.objects.create_superuser('neurodata', 'abc@xyz.com', 'neur0data')" | python /home/neurodata/ndstore/django/manage.py shell
RUN python /home/neurodata/ndstore/django/manage.py collectstatic --noinput

# move nginx config files and start service
RUN rm /etc/nginx/sites-enabled/default
RUN rm /etc/nginx/sites-available/default
RUN cp /home/neurodata/ndstore/setup/docker_config/nginx/ndstore.conf /etc/nginx/sites-available/default
RUN ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
RUN service nginx start

# move uwsgi config files and start service
RUN chown -R www-data:www-data /tmp/
RUN cp /home/neurodata/ndstore/setup/docker_config/uwsgi/ndstore.ini /etc/uwsgi/apps-available/ndstore.ini
RUN ln -s /etc/uwsgi/apps-available/ndstore.ini /etc/uwsgi/apps-enabled/ndstore.ini
#RUN service uwsgi start

# move celery config files and start service
RUN cp /home/neurodata/ndstore/setup/docker_config/celery/propagate.conf /etc/supervisor/conf.d/propagate.conf
RUN cp /home/neurodata/ndstore/setup/docker_config/celery/ingest.conf /etc/supervisor/conf.d/ingest.conf
RUN service supervisor start
RUN service rabbitmq-server start

# open the port
EXPOSE 80

USER neurodata
