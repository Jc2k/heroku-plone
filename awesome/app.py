import os, sys, optparse, urlparse

p = optparse.OptionParser()
p.add_option("-p", "--port")
options, args = p.parse_args()


db = urlparse.urlparse(os.environ.get("DATABASE_URL", 'postgres://username:password@hostname/database'))


# Zope configuration to poke variables into when web process is started
zope_conf = """
instancehome %(instance_home)s

<http-server>
  address %(port)s
</http-server>

<zodb_db main>
    #<relstorage>
    #  <postgresql>
    #    dsn dbname='%(db_name)s' user='%(db_username)s' host='%(db_host)s' password='%(db_password)s'
    #  </postgresql>
    #</relstorage>

    <temporarystorage>
      name temporary storage for main data
    </temporarystorage>
    container-class Products.TemporaryFolder.TemporaryContainer

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

# Figure out directory structure based on where this script is
root_dir = os.path.join(os.path.dirname(__file__), "..")
instance_home = os.path.join(root_dir, "zope")
conf_file = os.path.join(instance_home, "etc", "zope.conf")
zdctl = os.path.join(root_dir, "bin", "zopectl")


# If there is no zope instance, create one
if not os.path.exists(conf_file):
    os.system("%(root_dir)s/bin/mkzopeinstance -u zopeadmin:zopeadmin -d %(instance_home)s" % dict(root_dir=root_dir, instance_home=instance_home))


# Rewrite zope.conf according to the port we are supposd to listen on
open(conf_file, "w").write(zope_conf % dict(
    instance_home=instance_home,
    port=options.port,
    db_username=db.username,
    db_password=db.password,
    db_host=db.hostname,
    db_name=db.path[1:],
    ))


# Actually start zope
os.environ["INSTANCE_HOME"] = instance_home
os.environ["PYTHON"] = sys.executable
os.execvp(zdctl, [zdctl, "-C", conf_file, "fg"])


