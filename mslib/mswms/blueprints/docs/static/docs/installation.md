# MSWMS installation

The MSS Web Map Service (MSWMS) is included in the
[conda-forge `mss` package](https://anaconda.org/conda-forge/mss).

## Project installation

Install [Pixi](https://pixi.sh/latest/) for your operating system. Use a
dedicated system user for the server, for example `mss`, and log in as that
user before creating a project in its home directory.

The following commands use a POSIX shell:

```sh
cd ~
pixi init MSWMS
cd MSWMS
pixi add mss
pixi shell
```

For later sessions, return to this project directory and activate its
environment with `pixi shell`.

## Start MSWMS

Configure `mswms_settings.py` for your forecast data and layers as described
in the [MSWMS documentation](https://mss.readthedocs.io/en/stable/mswms.html).
The configuration module is found through `PYTHONPATH`. Before starting
the server, add the directory containing that file to `PYTHONPATH`; replace
`/path/to/config` below with that directory:

```sh
export PYTHONPATH=/path/to/config
mswms
```

With the default address and port, check the WMS capabilities at
<http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>.
The server runs in the foreground; stop it with Ctrl+C.

This built-in server is for development only. For production, use a WSGI
server such as Waitress or Apache with mod_wsgi, as described in
[WMS Server Deployment](https://mss.readthedocs.io/en/stable/mswms.html#wms-server-deployment).

## Update the installation

Stop the server and run the following in the project directory to update
MSS within the version constraints in the project manifest:

```sh
pixi update mss
```

To upgrade to the latest package versions, disregarding those constraints:

```sh
pixi upgrade mss
```

Restart MSWMS after updating.
