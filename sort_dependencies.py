# Copyright 2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Dirty dirty little tool to for making a dependency-sorted requirements.txt

import os
from glob import glob
from pkginfo.utils import get_metadata
import pkg_resources

def first(generator):
    try:
        return generator.next()
    except StopIteration:
        pass

versions = {}
deps = {}

for x in glob("lib/python2.6/site-packages/*.egg-info"):
    p = get_metadata(x)
    versions[p.name] = p.version

    reqpath = os.path.join(x, "requires.txt")
    if os.path.exists(reqpath):
        r = open(reqpath).read().splitlines()
        deps[p.name] = []
        for line in r:
            if not line:
                continue
            try:
                deps[p.name].append(first(pkg_resources.parse_requirements(line)).project_name)
            except ValueError:
                pass

state = {}
ordered = []

def visit(name):
    if state.get(name, "missing") == "installing":
        # Can't believe there is one
        #raise ValueError("Cyclic dependency")
        return

    if state.get(name, "missing") == "installed":
        return

    state[name] = "installing"

    for dep in deps.get(name, []):
        visit(dep)

    ordered.append(name)

    state[name] = "installed"

visit("Plone")

for pkg in ordered:
    if pkg in versions:
        print "%s==%s" % (pkg, versions[pkg])
    else:
        print pkg

print "================"

# Interestingly theese werent reffed...
unreffed = set(deps.keys()) - set(ordered)
for pkg in unreffed:
    print pkg
