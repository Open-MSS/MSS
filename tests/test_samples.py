# -*- coding: utf-8 -*-
"""

    tests.test_samples
    ~~~~~~~~~~~~~~~~~~

    This module checks the sample files in docs/samples, which the documentation
    shows: the documentation refers only to existing samples and every sample is a
    valid file of its type. The tests in tests/_test_mswms, tests/_test_msui and
    tests/_test_plugins load the samples with the code that uses them.

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import json
import pathlib
import re

import pytest
import yaml

DOCS = pathlib.Path(__file__).parent.parent / "docs"
SAMPLES = DOCS / "samples"


def _samples(*patterns):
    return sorted({path for pattern in patterns for path in SAMPLES.rglob(pattern)})


def _ids(paths):
    return [str(path.relative_to(SAMPLES)) for path in paths]


def test_docs_refer_to_existing_samples():
    missing = []
    for rst in DOCS.rglob("*.rst"):
        for reference in re.findall(r"samples/[\w./-]*[\w/]", rst.read_text(encoding="utf-8")):
            if not (DOCS / reference).exists():
                missing.append(f"{rst.relative_to(DOCS)}: {reference}")
    assert missing == []


JSON_SAMPLES = _samples("*.json.sample")


@pytest.mark.parametrize("path", JSON_SAMPLES, ids=_ids(JSON_SAMPLES))
def test_json_sample_is_valid(path):
    json.loads(path.read_text(encoding="utf-8"))


SNIPPETS = _samples("snippets/*.sample")


@pytest.mark.parametrize("path", SNIPPETS, ids=_ids(SNIPPETS))
def test_json_snippet_is_valid(path):
    """A snippet is a part of msui_settings.json, a valid file with braces around it."""
    json.loads("{" + path.read_text(encoding="utf-8").strip().rstrip(",") + "}")


PYTHON_SAMPLES = _samples("*.py", "*.py.*", "*.wsgi")


@pytest.mark.parametrize("path", PYTHON_SAMPLES, ids=_ids(PYTHON_SAMPLES))
def test_python_sample_compiles(path):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


YAML_SAMPLES = _samples("*.yaml.sample")


@pytest.mark.parametrize("path", YAML_SAMPLES, ids=_ids(YAML_SAMPLES))
def test_yaml_sample_is_valid(path):
    assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)
