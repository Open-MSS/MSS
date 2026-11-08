# MSColab installation

The MSS collaboration server (MSColab) is included in the
[conda-forge `mss` package](https://anaconda.org/conda-forge/mss).

## Project installation

Install [Pixi](https://pixi.sh/latest/) for your operating system. Use a
dedicated system user for the server, for example `mss`, and log in as that
user before creating a project in its home directory.

The following commands use a POSIX shell:

```sh
cd ~
pixi init MSColab
cd MSColab
pixi add mss
pixi shell
```

For later sessions, return to this project directory and activate its
environment with `pixi shell`.

## Start MSColab

MSColab requires a secret key. For a local start, generate one and pass it
in the environment before starting the server:

```sh
export MSCOLAB_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
mscolab start
```

The first start initializes the database, using SQLite by default. Check
the server status at <http://127.0.0.1:8083/status>. Stop the foreground
server with Ctrl+C.

For a persistent installation, keep the secret key private and reuse the
same value across all server processes and restarts. Configure the key
in the service environment rather than generating a new one for each
process.

For production setup, see
[Configuring Your MSColab Server](https://mss.readthedocs.io/en/stable/mscolab.html#configuring-your-mscolab-server)
and [Notes for server administrators](https://mss.readthedocs.io/en/stable/mscolab.html#notes-for-server-administrators)
in the [MSColab documentation](https://mss.readthedocs.io/en/stable/mscolab.html).

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

Restart MSColab after updating, using the same secret key.
