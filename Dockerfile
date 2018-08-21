##################################################################################
# Dockerfile to run Memcached Containers
# Based on miniconda3 Image
# docker build -t mss_img .
# docker run -d --net=host --name mss_1  mss_img
# # simple test
# curl "http://localhost:18081/?service=WMS&request=GetCapabilities&version=1.1.1"
#
# For the mss ui:
# xhost +local:docker
# docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix dreimark/mss:latest  /bin/bash
# mss&
# mswms
#
##################################################################################

# Set the base image debian with miniconda
FROM continuumio/miniconda3

# install a libgl1 mesa package
RUN apt-get --yes update
RUN apt-get --yes upgrade

# install packages for qt X 
RUN apt-get --yes install libgl1-mesa-glx python-xpyb libx11-xcb1 libxi6 xfonts-scalable
# get keyboard working for mss
RUN apt-get --yes update 
RUN DEBIAN_FRONTEND=noninteractive apt-get --yes install xserver-xorg-video-dummy  

# Set the file maintainer (your name - the file's author)
MAINTAINER Maintaner Reimar Bauer

# Set up conda-forge channel
RUN conda config --add channels conda-forge
RUN conda config --add channels defaults

# create some desktop user directories
RUN mkdir -p /root/.local/share/applications/
RUN mkdir -p /root/.local/share/icons/hicolor/48x48/apps/

# first place to look for config and data
# if there is no data attached run demodata
RUN mkdir /srv/mss

# Install MSS
RUN conda install mss -y

ENV PYTHONPATH="/srv/mss:/root/mss"

# Run demodata
# server based on demodata until you mount a data volume on /srv/mss
# also you can replace the data in the demodata dir /root/mss.
RUN demodata

EXPOSE 18081
CMD mswms --port 18081
