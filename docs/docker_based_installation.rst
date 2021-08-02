Installation based on Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use images `from the docker hub <https://hub.docker.com/r/openmss/mss>`_. based on our `repository <https://github.com/Open-MSS/dockerhub>`_

Build settings are based on the stable branch. Our openmss/mss:latest has any update in the stable branch.


You can start server and client by loading the image ::

 $ xhost +local:docker
 $ docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix openmss/mss:latest  /bin/bash
 $ /opt/conda/envs/mssenv/bin/mss &
 $ /opt/conda/envs/mssenv/bin/mswms --port 80 &
 $ /opt/conda/envs/mssenv/bin/mscolab &
 $ curl http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1
 $ curl http://localhost:8083/status

The WMS server initialized by demodata, and the mscolab server and the userinterface can be started by ::

 $  xhost +local:docker
 $  docker run -d --net=host -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix openmss/mss:latest MSS

