# -*- coding: utf-8 -*-
"""

    mslib.mscolab.api
    ~~~~~~~~~~~~~~~~~~

    The client/server contract for mscolab: request/response dataclasses
    (schemas.py, type hints only, not checked at runtime) and the
    endpoint-name registry (endpoints.py). This is the
    ONLY part of mslib.mscolab that mslib.msui may import from -- see
    ../CLAUDE.md and ../../../ARCHITECTURE.md.

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
