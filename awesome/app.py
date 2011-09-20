from Zope2.Startup.run import configure
from Zope2 import startup
import os

root_dir = os.path.join(os.path.basename(__file__), "..")
conf_dir = os.path.join(root_dir, "zope", "etc", "zope.conf")

if not os.path.exists(conf_dir):
    os.system("%(root_dir)s/bin/mkzopeinstance -u zopeadmin:zopeadmin -d %(root_dir)s/zope")

configure(conf_dir)
startup()

# mod_wsgi looks for the special name 'application'.
from ZPublisher.WSGIPublisher import publish_module as application
