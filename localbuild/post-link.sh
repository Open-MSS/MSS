unamestr=`uname`
# only if we don't execute in a docker environment
if [[ "$(cat /proc/1/sched | head -n 1)" = "systemd (1, #threads: 1)" ]] && [[ "$unamestr" == 'Linux' ]]; then
    msuicmd="$CONDA_PREFIX/bin/msui"
    $msuicmd -m
    echo "menue entry ($msuicmd -m): done"
else
    echo "called in a container"
fi
