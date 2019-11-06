##################################################################################
# Dockerfile to run Memcached Containers
# Based on miniconda3 Image
# docker build -t mswms .
# docker run -d --net=host --name mswms  mswms
#
# --- Read Capabilities ---
# curl "http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1"
#
# docker ps
# CONTAINER ID        IMAGE               COMMAND
# b0bc7275d77f        mswms               "/usr/bin/tini -- /b…"
#
# For the mss ui:
# xhost +local:docker
# docker run -d --net=host -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix \
# dreimark/mss:latest /opt/conda/envs/mssenv/bin/mss
#
# For the wms server:
# docker run -d --net=host  dreimark/mss:latest
# # --- Read Capabilities ---
# curl "http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1"
#
##################################################################################


# Set the base image debian with miniconda
FROM continuumio/miniconda3

MAINTAINER Reimar Bauer <rb.proj@gmail.com>

# install packages for qt X
RUN apt-get --yes update && apt-get --yes upgrade && apt-get --yes install \
  libgl1-mesa-glx \
  libx11-xcb1 \
  libxi6 \
  xfonts-scalable

# get keyboard working for mss gui
RUN apt-get --yes update && DEBIAN_FRONTEND=noninteractive \
  apt-get --yes install xserver-xorg-video-dummy \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Set up conda-forge channel
RUN conda config --add channels conda-forge && conda config --add channels defaults

# create some desktop user directories
# if there is no data attached e.g. demodata /srv/mss is the preferred dir
RUN mkdir -p /root/.local/share/applications/ \
  && mkdir -p /root/.local/share/icons/hicolor/48x48/apps/ \
  && mkdir /srv/mss

# Install Mission Support System Software
RUN conda create -n mssenv mss -y


# path for data and mss_wms_settings config
ENV PYTHONPATH="/srv/mss:/root/mss"
ENV PROJ_LIB="/opt/conda/envs/mssenv/share/proj"

# Run mswms and mscolab demodata
# server based on demodata until you mount a data volume on /srv/mss
# also you can replace the data in the demodata dir /root/mss.
RUN /opt/conda/envs/mssenv/bin/mswms_demodata
RUN /opt/conda/envs/mssenv/bin/mscolab_demodata

EXPOSE 80 8083
CMD ["/opt/conda/envs/mssenv/bin/mswms", "--port", "80"]
# ToDo fix after 1.9.1 release
# CMD ["/opt/conda/envs/mssenv/bin/mscolab"]