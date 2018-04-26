##################################################################################
# Dockerfile to run Memcached Containers
# Based on miniconda Image
# docker build -t mss_img .
# docker run -d --net=host --name mss_1  mss_img
# # simple test
# curl "http://localhost:18081/?service=WMS&request=GetCapabilities&version=1.1.1"
##################################################################################

# Set the base image debian with miniconda
FROM continuumio/miniconda3

# install a libgl1 mesa package
RUN apt-get --yes update
RUN apt-get --yes upgrade
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
