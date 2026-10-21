# Installation

## User installation

The Mission Support System (MSS), including the Web Map Service, Collaboration Server, and graphical user interface, is available as the [conda-forge `mss` package](https://anaconda.org/conda-forge/mss).

Install [Pixi](https://pixi.sh/latest/) for your operating system, then choose a global installation or add MSS to a project.

### Global installation

Install MSS globally when you want to start the client without setting up a project:

```sh
pixi global install mss
```

You can then start the applications from a terminal:

```sh
msui
mswms -h
mscolab -h
mssautoplot -h
```

To update the global installation:

```sh
pixi global update mss
```

### Project installation

Create a project and add MSS from conda-forge:

```sh
pixi init MSS
cd MSS
pixi shell
pixi add mss
```

Activate the project environment with `pixi shell` before starting MSS applications. The first `msui` launch may take longer while it sets up fonts.

```sh
msui
mswms -h
mscolab -h
mssautoplot -h
```

Update the project dependencies using the lock file:

```sh
pixi update mss
```

To upgrade to the latest package versions, disregarding the version constraints in the project manifest:

```sh
pixi upgrade mss
```

### Server installation

For an MSWMS or MSColab server, you may want to use a dedicated system user and install MSS in a Pixi project for that user. To try the built-in servers, start them in the project environment:

```sh
mswms &
mscolab start
```

Check the MSColab status at <http://127.0.0.1:8083/status> and the WMS capabilities at <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>.

See the [MSS installation guide](https://mss.readthedocs.io/en/stable/installation.html) for further details.
