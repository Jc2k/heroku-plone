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
