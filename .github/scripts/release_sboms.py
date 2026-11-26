# -*- coding: utf-8 -*-
"""

    .github.scripts.release_sboms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Writes the SBOMs (CycloneDX 1.6, JSON) of the MSS conda packages for all platforms from pixi.lock, as the
    workflow sbom.yml attaches them to a release: one file <package>-<version>-<platform>.cdx.json per package and
    platform.

        pixi exec --spec "python>=3.11" python .github/scripts/release_sboms.py <version> <output directory>

    Needs the pixi extension pixi-sbom: pixi global install "pixi-sbom==1.15.0"

    The SBOMs describe the checkout the script is in; the version is only their label. A release version (e.g.
    12.0.0) is refused unless the checkout is its tag and pixi.toml, pixi.lock and pyproject.toml are unchanged.

    Each package is described by the lock environment that is solved like it (pixi.toml, [environments]): the
    packages locked for the release. CI doesn't test every environment on every platform, and an installation from
    conda-forge is solved on its own and can get other versions. The package environments also hold the test
    dependencies, which the packages don't ship; they are excluded with everything only they need, and the run stops
    if a shipped package needs one of them. The repository itself (open-mss, installed editable) is removed. An SBOM
    lists the third-party dependencies of its package, not the other mss-* packages it is built from.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import argparse
import json
import pathlib
import re
import subprocess  # nosec B404  # runs pixi and git with a fixed argument list
import sys
import tempfile
import textwrap
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
# the others are applications
LIBRARIES = ("mss-utils", "mss-mscolab-api")
# the output layout (sbom-<platform>.cdx.json, the property pixi:platform) and the exclusion rules are those of
# this version; the workflow sbom.yml installs it
PIXI_SBOM_VERSION = "1.15.0"
# every feature of a package environment is one of these: what the package ships, or what only its tests need
RUNTIME_FEATURES = ("utils", "api", "werkzeug", "server", "saml", "mswms", "mscolab", "msidp", "msui")
TEST_FEATURES = ("test", "qttest", "ncotest")
SUPPLIER = {"name": "Open-MSS", "url": ["https://github.com/Open-MSS/MSS"]}
# a release version, as the workflow sbom.yml checks a tag
RELEASE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.]*")
# what the SBOMs are made of
SOURCES = ("pixi.toml", "pixi.lock", "pyproject.toml")
SCOPE = ("The pixi.lock environment {environment} of MSS {version} on {platform}, as locked for the release, "
         "without its test dependencies. An installation from conda-forge is solved on its own and can get other "
         "versions.")


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
    runtime = {exclusion_name(name) for name in dependency_names(pixi)}
    test = set()
    for feature in features:
        names = {exclusion_name(name) for name in dependency_names(pixi["feature"][feature])}
        (test if feature in TEST_FEATURES else runtime).update(names)
    both = sorted(test & runtime)
    if both:
        sys.exit(f"environment {environment}: {', '.join(both)} is a test and a runtime dependency")
    return sorted(test)


def normalized(name):
    """A PyPI name as PEP 503 compares it: open_mss, Open.MSS and open-mss are one package"""
    return re.sub(r"[-_.]+", "-", name).lower()


def exclusion_name(name):
    """
    A name as pixi-sbom 1.15.0's --exclude compares it: case-insensitive, "-" and "_" alike, but not "."

    --exclude backports-tarfile keeps backports.tarfile, so a test dependency is passed and compared in this form,
    not as PEP 503 normalizes it.
    """
    return name.lower().replace("_", "-")


def check_exclusion(complete, written, excluded, label):
    """
    Stops if the exclusion dropped a package that a shipped package needs

    complete is the SBOM of the same environment and platform without exclusions, written the one with them, label
    names both in a message. pixi-sbom's --exclude drops an excluded name everywhere, also where a runtime package
    depends on it, e.g. after a lock update, and with it what only excluded packages need. The shipped packages are
    those reached from the root without passing through an excluded one; none of them may depend on an excluded
    package. A component that is not reached from the root at all is not dropped. The written SBOM has to hold
    exactly the components of the complete one without the excluded and the dropped ones.
    """
    names = {component["bom-ref"]: component["name"] for component in complete["components"]}
    root = complete["metadata"]["component"]["bom-ref"]
    edges = {entry["ref"]: entry.get("dependsOn", []) for entry in complete.get("dependencies", [])}
    unknown = sorted({ref for refs in edges.values() for ref in refs if ref not in names})
    if unknown:
        sys.exit(f"SBOM of {label}: dependencies on refs that are no component: {', '.join(unknown)}")
    blocked = {ref for ref, name in names.items() if exclusion_name(name) in excluded}

    def reached(stop):
        found, todo = set(), list(edges.get(root, []))
        while todo:
            ref = todo.pop()
            if ref in found or ref in stop:
                continue
            found.add(ref)
            todo.extend(edges.get(ref, []))
        return found

    shipped = reached(blocked)
    needed = sorted({f"{names[ref]} (needed by {names[parent]})"
                     for parent in shipped for ref in edges.get(parent, []) if ref in blocked})
    if needed:
        sys.exit(f"SBOM of {label}: shipped packages need the excluded {', '.join(needed)}")
    dropped = blocked | (reached(set()) - shipped)
    expected = {name for ref, name in names.items() if ref not in dropped}
    got = {component["name"] for component in written["components"]}
    if expected != got:
        sys.exit(f"SBOM of {label}: the exclusion differs from the dependency graph: "
                 f"{', '.join(sorted(expected ^ got))}")


def remove_component(document, name, label):
    """
    Removes the component name and hangs what it depends on under the root; label names the SBOM in a message

    For the repository itself (open-mss, installed editable): pixi-sbom's --exclude also drops what is reached only
    through it, in the msapi environment e.g. python with openssl and the other base packages.
    """
    refs = {component["bom-ref"] for component in document["components"]
            if normalized(component["name"]) == normalized(name)}
    if not refs:
        sys.exit(f"no component {name} in the SBOM of {label}")
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
        "type": "library" if package in LIBRARIES else "application",
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


def git(*arguments):
    """The output of a git command in the repository, None if it fails"""
    command = ["git", "-C", str(REPOSITORY), *arguments]
    try:
        answer = subprocess.run(command, capture_output=True, text=True)  # nosec B603 B607  # fixed arguments
    except FileNotFoundError:
        sys.exit("needs git")
    return answer.stdout.strip() if answer.returncode == 0 else None


def check_release_checkout(version):
    """Stops if version is a release version and the checkout is not its tag, or its SBOM sources are changed"""
    if not RELEASE.fullmatch(version):
        return
    checkout = f"{version} is a release version: run in a clean checkout of its tag (git checkout {version})"
    head = git("rev-parse", "HEAD")
    if head is None or git("rev-parse", "--verify", "--quiet", f"refs/tags/{version}^{{commit}}") != head:
        sys.exit(f"{checkout}, the checkout is not the tag {version}")
    changed = git("status", "--porcelain", "--", *SOURCES)
    if changed is None or changed:
        sys.exit(f"{checkout}, changed: {changed}")


def main():
    # the usage part of the docstring, without its title and the license
    usage = textwrap.dedent(__doc__.split("This file is part of MSS.")[0]).strip().split("\n", 2)[2].strip()
    parser = argparse.ArgumentParser(description=usage, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", help="release version, e.g. 12.0.0")
    parser.add_argument("output", type=pathlib.Path, help="output directory")
    args = parser.parse_args()

    install = f'pixi global install "pixi-sbom=={PIXI_SBOM_VERSION}"'
    try:
        command = ["pixi", "sbom", "--version"]
        answer = subprocess.run(command, capture_output=True, text=True)  # nosec B603 B607  # fixed arguments
    except FileNotFoundError:
        sys.exit("needs pixi, see https://pixi.sh")
    if answer.returncode != 0:
        sys.exit(f"needs the pixi extension pixi-sbom: {install}")
    if answer.stdout.split()[-1:] != [PIXI_SBOM_VERSION]:
        sys.exit(f"needs pixi-sbom {PIXI_SBOM_VERSION}, found {answer.stdout.strip()}: {install}")
    check_release_checkout(args.version)
    pyproject = tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))
    pixi = tomllib.loads((REPOSITORY / "pixi.toml").read_text(encoding="utf-8"))
    missing = sorted(set(PACKAGES) - set(pixi["environments"]))
    if missing:
        sys.exit(f"pixi.toml has no environment {', '.join(missing)}")
    platforms = set(pixi["workspace"]["platforms"])

    args.output.mkdir(parents=True, exist_ok=True)
    # no SBOM of an earlier run is left beside the new ones; other files stay
    packages = "|".join(re.escape(package) for package in PACKAGES.values())
    own = re.compile(rf"({packages})-[^-]+-[a-z]+-[a-z0-9]+\.cdx\.json")
    for old in args.output.glob("*.cdx.json"):
        if own.fullmatch(old.name):
            old.unlink()
    with tempfile.TemporaryDirectory() as work:
        for environment, package in PACKAGES.items():
            excluded = excluded_packages(pixi, environment)
            directory = pathlib.Path(work, environment)
            complete_directory = pathlib.Path(work, f"{environment}-complete")
            for output, options in ((directory, [option for name in excluded for option in ("--exclude", name)]),
                                    (complete_directory, [])):
                command = ["pixi", "sbom", "--no-config", "--lockfile", str(REPOSITORY / "pixi.lock"),
                           "-e", environment, "--all-platforms", "--format", "cyclonedx", "--spec-version", "1.6",
                           # the packages are conda-forge packages, as pixi audit checks them; a PyPI name of a conda
                           # package can differ, it is only recorded as the extra reference the lock has, never
                           # looked up
                           "--primary-purl", "conda", "--pypi-mapping", "lock", *options, "--output", str(output)]
                subprocess.run(command, check=True)  # nosec B603 B607  # fixed arguments
            files = sorted(directory.glob("sbom-*.cdx.json"))
            written = set()
            for file in files:
                document = json.loads(file.read_text(encoding="utf-8"))
                complete = json.loads((complete_directory / file.name).read_text(encoding="utf-8"))
                properties = {item["name"]: item["value"] for item in document["metadata"].get("properties", [])}
                platform = properties["pixi:platform"]
                label = f"{package} (environment {environment}) on {platform}"
                check_exclusion(complete, document, set(excluded), label)
                document = remove_component(document, pyproject["project"]["name"], label)
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
