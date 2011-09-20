import os, sys, optparse

p = optparse.OptionParser()
p.add_option("-p", "--port")
options, args = p.parse_args()


# Zope configuration to poke variables into when web process is started
zope_conf = """
instancehome %(instance_home)s

<http-server>
  address %(port)s
</http-server>

<zodb_db main>
#    <filestorage>
#      path %(instance_home)s/var/Data.fs
#    </filestorage>
    <temporarystorage>
      name temporary storage for main data
    </temporarystorage>
    mount-point /
    container-class Products.TemporaryFolder.TemporaryContainer
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
    port=p.port,
    ))


# Actually start zope
os.environ["INSTANCE_HOME"] = instance_home
os.environ["PYTHON"] = sys.executable
os.execvp(zdctl, [zdctl, "-C", conf_file, "fg"])


