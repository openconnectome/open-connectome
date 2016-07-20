FROM ubuntu:14.04
ARG BRANCH
ENV TRAVIS_BRANCH $BRANCH
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
RUN if [ ! -z "$TRAVIS_BRANCH" ]; then cd /home/travis/build/neurodata/ndstore/setup; 	./ndstore_install.sh "$TRAVIS_BRANCH"; else cd /home/neurodata; git clone https://github.com/neurodata/ndstore.git; cd /home/neurodata/ndstore; git checkout microns; git submodule init; git submodule update; cd /home/neurodata/ndstore/setup; ./ndstore_install.sh; fi

# open the port
EXPOSE 80

USER neurodata
