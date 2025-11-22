# -*- coding: utf-8 -*-
"""

    mslib.modulename
    ~~~~~~~~~~~~~~~~

    Text line as description

    This file is part of MSS.

    :copyright: Copyright 2017 Main Contributor
    :copyright: Copyright 2017-2025 by the MSS team, see AUTHORS.
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

#Linux
#python3 heading_linter.py to see the errors
#python3 heading_linter.py --fix to fix them

#!/usr/bin/env python3
"""
Improved linter that checks and fixes Sphinx heading underline lengths.
Now shows exact file path, line numbers, expected length, actual length.
"""

import argparse
import glob
import os
import re
import sys

VALID_CHARS = "= - ` : \" ~ ^ _ * + # < >".split()
UNDERLINE_RE = re.compile(r'^(\s*)([=\-`:\"~^_*+#<>])\2{2,}\s*$')


def scan_repo(patterns):
    files = []

    if not patterns:
        for root, dirs, filenames in os.walk("."):
            for skip in (".git", "__pycache__", ".ipynb_checkpoints"):
                if skip in dirs:
                    dirs.remove(skip)

            for filename in filenames:
                if filename.endswith(".py") or filename.endswith(".rst"):
                    files.append(os.path.join(root, filename))

        return sorted(files)

    for p in patterns:
        files.extend(glob.glob(p, recursive=True))
    return sorted(set(files))


def is_docstring(line):
    stripped = line.strip()
    return stripped in ('"""', "'''") or stripped.startswith('"""') or stripped.startswith("'''")


def process_file(path, fix=False):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        print(f"Skipping unreadable file: {path}")
        return 0

    errors = 0
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # --------------------------
        # CASE 1: title + underline
        # --------------------------
        if i + 1 < len(lines):
            underline = lines[i + 1]

            if not is_docstring(line) and not is_docstring(underline):
                m = UNDERLINE_RE.match(underline)

                if m:
                    indent, ch = m.group(1), m.group(2)
                    title = line.rstrip("\n")
                    stripped_title = title.strip()

                    if stripped_title:
                        expected = len(stripped_title)
                        actual = len(underline.strip())

                        if expected != actual:
                            errors += 1
                            print(
                                f"{path}:{i+2}: ERROR — underline length mismatch\n"
                                f"  Title:      '{stripped_title}'\n"
                                f"  Expected:   {expected}\n"
                                f"  Actual:     {actual}\n"
                            )

                            if fix:
                                new_lines.append(line)
                                new_lines.append(f"{indent}{ch * expected}\n")
                                i += 2
                                continue

        # --------------------------
        # CASE 2: overline + title + underline
        # --------------------------
        if i + 2 < len(lines):
            over, title, under = lines[i], lines[i + 1], lines[i + 2]

            if (not is_docstring(over) and not is_docstring(title)
                    and not is_docstring(under)):

                m1 = UNDERLINE_RE.match(over)
                m2 = UNDERLINE_RE.match(under)

                if m1 and m2:
                    indent1, ch1 = m1.group(1), m1.group(2)
                    indent2, ch2 = m2.group(1), m2.group(2)
                    stripped = title.strip()

                    if stripped:
                        expected = len(stripped)

                        over_len = len(over.strip())
                        under_len = len(under.strip())

                        fix_needed = False

                        if over_len != expected:
                            errors += 1
                            fix_needed = True
                            print(
                                f"{path}:{i+1}: ERROR — OVERLINE mismatch\n"
                                f"  Title:      '{stripped}'\n"
                                f"  Expected:   {expected}\n"
                                f"  Actual:     {over_len}\n"
                            )

                        if under_len != expected:
                            errors += 1
                            fix_needed = True
                            print(
                                f"{path}:{i+3}: ERROR — UNDERLINE mismatch\n"
                                f"  Title:      '{stripped}'\n"
                                f"  Expected:   {expected}\n"
                                f"  Actual:     {under_len}\n"
                            )

                        if fix and fix_needed:
                            new_lines.append(f"{indent1}{ch1 * expected}\n")
                            new_lines.append(title)
                            new_lines.append(f"{indent2}{ch2 * expected}\n")
                            i += 3
                            continue

        # Normal line
        new_lines.append(line)
        i += 1

    # Write fixes
    if fix and errors > 0:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✔ Fixed: {path}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Sphinx heading underline linter")
    parser.add_argument("files", nargs="*", help="Files or patterns")
    parser.add_argument("--fix", action="store_true", help="Fix errors automatically")
    args = parser.parse_args()

    files = scan_repo(args.files)
    print(f"Checking {len(files)} files...\n")

    total = 0
    for f in files:
        if not os.path.isdir(f):
            total += process_file(f, fix=args.fix)

    print("\n--------------------------------------")
    if total == 0:
        print("✔ No heading underline errors found!")
    else:
        print(f"✖ Total Errors Found: {total}")
        print("Run: python heading_linter.py --fix   to fix them.")

    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()

