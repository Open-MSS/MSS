unamestr=`uname`
# only if we don't execute in a docker environment
if [[ "$(cat /proc/1/sched | head -n 1)" = "systemd (1, #threads: 1)" ]] && [[ "$unamestr" == 'Linux' ]]; then
    msscmd="$CONDA_PREFIX/bin/mss"
    $msscmd -m
    echo "menue entry ($msscmd -m): done"
else
    echo "called in a container"
fi
