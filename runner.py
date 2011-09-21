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

# This is a startup command to run from Procfile (on heroku or foreman)
# It will let you run a Zope instance from virtualenv, too.
# It expects to be passed a port to listen to on the command line
# It expects that DATABASE_URL is available.

import os, sys, optparse, urlparse


# Zope configuration to poke variables into when web process is started
rel_storage = """
    <relstorage>
      <postgresql>
        dsn dbname='%(db_name)s' user='%(db_username)s' host='%(db_host)s' password='%(db_password)s'
      </postgresql>
    </relstorage>
    """

temp_storage = """
    <temporarystorage>
      name temporary storage for main data
    </temporarystorage>
    container-class Products.TemporaryFolder.TemporaryContainer
    """

zope_conf = """
instancehome %(instance_home)s

<http-server>
  address %(port)s
</http-server>

%%import relstorage
<zodb_db main>
    %(storage)s

    mount-point /
</zodb_db>

<zodb_db temporary>
    <temporarystorage>
      name temporary storage for sessioning
    </temporarystorage>
    mount-point /temp_folder
    container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>

"""


# Allow process start to be customized
p = optparse.OptionParser()
p.add_option("-p", "--port")
# p.add_option("-d", "--database-url") better than enivornment variable? does it even work?
options, args = p.parse_args()


# It looks like the postgres database to point at might come from DATABASE_URL env
# database_url = 'postgress://username:password@hostname/database'
database_url = os.environ.get("DATABASE_URL", None)


# Figure out directory structure based on where this script is
root_dir = os.path.join(os.getcwd(), os.path.dirname(__file__))
instance_home = os.path.join(root_dir, "zope")
conf_file = os.path.join(instance_home, "etc", "zope.conf")
zdctl = os.path.join(root_dir, "bin", "zopectl")


# If there is no zope instance, create one
if not os.path.exists(conf_file):
    os.system("%(root_dir)s/bin/mkzopeinstance -u zopeadmin:zopeadmin -d %(instance_home)s" % dict(root_dir=root_dir, instance_home=instance_home))


# Generate a zope conf for '/' - either RelStorage or temporarystorage
if database_url:
    db = urlparse.urlparse(os.environ.get("DATABASE_URL", 'postgres://username:password@hostname/database'))

    storage = rel_storage % dict(
        db_username=db.username,
        db_password=db.password,
        db_host=db.hostname,
        db_name=db.path[1:],
        )

else:
    storage = temp_storage


# Rewrite zope.conf according to the port we are supposd to listen on and storage backend
open(conf_file, "w").write(zope_conf % dict(
    instance_home=instance_home,
    port=options.port,
    storage=storage,
    ))

print os.environ

# Actually start zope - think i might prefer to import things by hand here long term
os.environ["INSTANCE_HOME"] = instance_home
os.environ["PYTHON"] = sys.executable
os.execvp(zdctl, [zdctl, "-C", conf_file, "fg"])


