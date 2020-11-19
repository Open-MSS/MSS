Installation based on Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since 1.7.4 mss is on the `docker hub <https://hub.docker.com/r/dreimark/mss/>`_.

Build settings are based on the stable branch. Our latest is any update in the stable repo.

You can start server and client by loading the image ::

 $ xhost +local:docker
 $ docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix dreimark/mss:latest  /bin/bash
 $ /opt/conda/envs/mssenv/bin/mss &
 $ /opt/conda/envs/mssenv/bin/mswms --port 80 &
 $ /opt/conda/envs/mssenv/bin/mscolab &
 $ curl http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1
 $ curl http://localhost:8083

The userinterface and both servers can be started by ::

 $  xhost +local:docker
 $  docker run -d --net=host -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix dreimark/mss:latest \
   /opt/conda/envs/mssenv/bin/mss
 $ docker exec replace_by_container /bin/sh -c "/scripts/script.sh"

