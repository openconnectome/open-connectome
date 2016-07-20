FROM ubuntu:14.04
MAINTAINER Kunal Lillaney <lillaney@jhu.edu>

#Remove pesky problems 
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -sf /bin/true /sbin/initctl
RUN echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d

# make neurodata user
RUN groupadd -r neurodata && useradd -r -m -g neurodata neurodata

# rest happens in user land
RUN apt-get update -y && apt-get install -y \
  git\
  bash-completion
USER neurodata

# clone the repo
WORKDIR /home/neurodata
RUN git clone https://github.com/neurodata/ndstore.git
WORKDIR /home/neurodata/ndstore
RUN git checkout travis_changes
RUN git submodule init
RUN git submodule update
USER root

WORKDIR /home/neurodata/ndstore/setup
RUN ./ndstore_install.sh

# open the port
EXPOSE 80

USER neurodata
