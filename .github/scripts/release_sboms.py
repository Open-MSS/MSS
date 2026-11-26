"""
Writes the SBOMs (CycloneDX 1.6, JSON) of the MSS conda packages for all platforms from pixi.lock, as the workflow
sbom.yml attaches them to a release: one file <package>-<version>-<platform>.cdx.json per package and platform.

    pixi exec --spec "python>=3.11" python .github/scripts/release_sboms.py <version> <output directory>

Needs the pixi extension pixi-sbom: pixi global install "pixi-sbom==1.15.0"

Each package is described by the lock environment that is solved like it (pixi.toml, [environments]): the packages
locked and tested for the release. An installation from conda-forge is solved on its own and can get other
versions. The package environments also hold the test dependencies, which the packages don't ship; they are
excluded with everything only they need; the repository itself (open-mss, installed editable) is removed. An SBOM lists
the third-party dependencies of its package, not the other mss-* packages it is built from.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import tomllib
import uuid

REPOSITORY = pathlib.Path(__file__).resolve().parents[2]
# lock environment -> conda package
PACKAGES = {
    "default": "mss",
    "msutils": "mss-utils",
    "msapi": "mss-mscolab-api",
    "mswms": "mss-mswms",
    "mscolab": "mss-mscolab",
    "msidp": "mss-msidp",
    "msui": "mss-msui",
}
# every feature of a package environment is one of these: what the package ships, or what only its tests need
RUNTIME_FEATURES = ("utils", "api", "werkzeug", "server", "saml", "mswms", "mscolab", "msidp", "msui")
TEST_FEATURES = ("test", "qttest", "ncotest")
SUPPLIER = {"name": "Open-MSS", "url": ["https://github.com/Open-MSS/MSS"]}
SCOPE = ("The pixi.lock environment {environment} of MSS {version} on {platform}, as locked and tested for the "
         "release, without its test dependencies. An installation from conda-forge is solved on its own and can get "
         "other versions.")


def dependency_names(table):
    """The conda and PyPI dependencies of a feature, or of the default feature (the top level of pixi.toml),
    also the platform-specific ones"""
    names = set()
    for part in [table, *table.get("target", {}).values()]:
        names.update(part.get("dependencies", {}))
        names.update(part.get("pypi-dependencies", {}))
    return names


def excluded_packages(pixi, environment):
    """
    The dependencies of the test features of the environment, to be left out of its SBOM

    pixi-sbom drops an excluded name also where a shipped package needs it, so a name that a runtime feature (or
    the default feature) of the environment declares as well stops the run, as does a feature that is neither.
    """
    definition = pixi["environments"][environment]
    features = definition if isinstance(definition, list) else definition.get("features", [])
    unknown = sorted(set(features) - set(RUNTIME_FEATURES) - set(TEST_FEATURES))
    if unknown:
        sys.exit(f"environment {environment}: feature {', '.join(unknown)} is neither in RUNTIME_FEATURES nor in "
                 f"TEST_FEATURES of {pathlib.Path(__file__).name}")
    runtime = dependency_names(pixi)
    test = set()
    for feature in features:
        (test if feature in TEST_FEATURES else runtime).update(dependency_names(pixi["feature"][feature]))
    both = sorted(test & runtime)
    if both:
        sys.exit(f"environment {environment}: {', '.join(both)} is a test and a runtime dependency")
    return sorted(test)


def normalized(name):
    """A PyPI name as PEP 503 compares it: open_mss, Open.MSS and open-mss are one package"""
    return re.sub(r"[-_.]+", "-", name).lower()


def remove_component(document, name):
    """
    Removes the component name and hangs what it depends on under the root

    For the repository itself (open-mss, installed editable): pixi-sbom's --exclude also drops what is reached only
    through it, in the msapi environment e.g. python with openssl and the other base packages.
    """
    refs = {component["bom-ref"] for component in document["components"]
            if normalized(component["name"]) == normalized(name)}
    if not refs:
        sys.exit(f"no component {name} in the SBOM of {document['metadata']['component']['name']}")
    document["components"] = [component for component in document["components"] if component["bom-ref"] not in refs]
    depends_on = {}
    for entry in document.get("dependencies", []):
        if entry["ref"] in refs:
            depends_on.update(dict.fromkeys(entry.get("dependsOn", [])))
    dependencies = []
    for entry in document.get("dependencies", []):
        if entry["ref"] in refs:
            continue
        if "dependsOn" in entry:
            kept = [ref for ref in entry["dependsOn"] if ref not in refs]
            if entry["ref"] == document["metadata"]["component"]["bom-ref"]:
                kept += [ref for ref in depends_on if ref not in kept and ref not in refs]
            entry["dependsOn"] = kept
        dependencies.append(entry)
    document["dependencies"] = dependencies
    return document


def describe_release(document, package, version, environment, platform, license_id):
    """Names the package, its release, supplier and license on the root instead of the workspace (MSS, no version)"""
    # unique for every document, also for the same package of another release
    document["serialNumber"] = uuid.uuid4().urn
    metadata = document["metadata"]
    metadata["authors"] = [{"name": SUPPLIER["name"]}]
    metadata["supplier"] = SUPPLIER
    metadata["component"].update({
        "name": package,
        "version": version,
        "purl": f"pkg:conda/{package}@{version}?channel=conda-forge",
        "supplier": SUPPLIER,
        "licenses": [{"license": {"id": license_id}}],
    })
    metadata.setdefault("properties", []).append(
        {"name": "open-mss:scope",
         "value": SCOPE.format(environment=environment, version=version, platform=platform)})
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", help="release version, e.g. 12.0.0")
    parser.add_argument("output", type=pathlib.Path, help="output directory")
    args = parser.parse_args()

    if subprocess.run(["pixi", "sbom", "--version"], capture_output=True).returncode != 0:
        sys.exit('needs the pixi extension pixi-sbom: pixi global install "pixi-sbom==1.15.0"')
    pyproject = tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))
    pixi = tomllib.loads((REPOSITORY / "pixi.toml").read_text(encoding="utf-8"))
    missing = sorted(set(PACKAGES) - set(pixi["environments"]))
    if missing:
        sys.exit(f"pixi.toml has no environment {', '.join(missing)}")
    platforms = set(pixi["workspace"]["platforms"])

    args.output.mkdir(parents=True, exist_ok=True)
    # no SBOM of an earlier run is left beside the new ones
    for old in args.output.glob("*.cdx.json"):
        old.unlink()
    with tempfile.TemporaryDirectory() as work:
        for environment, package in PACKAGES.items():
            directory = pathlib.Path(work, environment)
            excludes = [option for name in excluded_packages(pixi, environment) for option in ("--exclude", name)]
            subprocess.run(
                ["pixi", "sbom", "--no-config", "--lockfile", str(REPOSITORY / "pixi.lock"),
                 "-e", environment, "--all-platforms", "--format", "cyclonedx", "--spec-version", "1.6",
                 # the packages are conda-forge packages, as pixi audit checks them; a PyPI name of a conda package
                 # can differ, it is only recorded as the extra reference the lock has, never looked up
                 "--primary-purl", "conda", "--pypi-mapping", "lock", *excludes, "--output", str(directory)],
                check=True)
            files = sorted(directory.glob("sbom-*.cdx.json"))
            written = set()
            for file in files:
                document = remove_component(json.loads(file.read_text(encoding="utf-8")), pyproject["project"]["name"])
                properties = {item["name"]: item["value"] for item in document["metadata"].get("properties", [])}
                platform = properties["pixi:platform"]
                written.add(platform)
                describe_release(document, package, args.version, environment, platform,
                                 pyproject["project"]["license"])
                target = args.output / f"{package}-{args.version}-{platform}.cdx.json"
                target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            if written != platforms:
                sys.exit(f"environment {environment}: SBOMs for {', '.join(sorted(written)) or 'no platform'}, "
                         f"the workspace has {', '.join(sorted(platforms))}")
            print(f"{package}: {len(files)} platforms")


if __name__ == "__main__":
    main()
