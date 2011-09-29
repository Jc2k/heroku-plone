Plone on Heroku
===============

TL;DR
-----

I got Zope 2.13.8 and Plone 4.1 running, but updates currently fail because of
skins causing SyntaxErrors :( You can't deploy your app in one push without
blowing some timeouts on the git push. The 'slug' is nearly 40mb. Far from
the hard limit, but around the point heroku tell you to start trimming your fat.

RelStorage is close, but not quite working.

Has potential, but not ready for Plone at this time.


My amazing adventure with Heroku
--------------------------------

I saw offmessage blog about Django on Heroku and wondered: Can a Plone fit
in there?

To pull this off I need to make Zope and Plone deployable with only virtualenv
to hand, and the port number and RelStorage configuration needs to be set when
the zope instance is started.

All the documentation i've found on Python Heroku shows virtualenv is at the
heart of it. The 'slug' (a bundle of your application and its virtualenv) are
then copied to any nodes in the cluster running your app.

No sign of buildout.

Currently the only really supported mechanism for doing Plone is Buildout. What
does Buildout do for us that we'll have to recreate by hand when using
virtualenv?

The first step is to convert a fresh build into a requirements.txt. I ran
buildout, caught its output and grepping for 'Getting distribution for'. That
got me all the eggs (and versions) i needed, then I just use vim to trim the
fat so 200 lines of this::

    Getting distribution for 'foo==1'.
    Getting distribution for 'baz==2'.

became this 'requirements.txt'::

    foo==1
    baz==2

The one inclued with this repositoty is for Plone 4.1 and Zope 2.13.8.

To get a local environment I just do::

    virtualenv .
    ./bin/pip install -r requirements.txt

Easy if you are old school::

    ./bin/mkzopeinstance -u admin:password zope

This will create a zope instance in the zope directory.

At this point I made a script that would run mkzopeinstance if no instance
existed and then start it. This got around the next problem with having no
buildout: virtualenv doesnt have any sort of post install so there is no way to
bake the zope instance into your deployment.

Now I could::

    ./bin/python runner.py

and get Plone. Then I made the script rewrite zope.conf and start up so that
the port wasn't hard coded to 8080 and updated Procfile::

    web: ./bin/python runner.py -p $PORT

The zope.conf was also wired to use a temporary in memory database.

And i git pushed.

**It hit a deployment timeout.**

If your virtualenv takes too long to build it will abort. So I wrote
``sort_dependencies.py``. Horrible horrible script. It builds a graph of all
the eggs it finds in your virtualenv and then lists them (and their version
pin) sorted by their dependencies. Then I batched my requirements and did
multiple git pushes.

**Zope actually deployed**

So I pushed again with some Plone.

**The site is still running**

So I push again.

**It failed with SyntaxError**

Long suffering SysAdmins will tell you how their buildouts are **FULL** of
errors. If you are one of those programmers who likes to turn on ``-Wall
-Werror``.. Never ever run a Plone buildout ever. One common error is
SyntaxError. It occurs because some lovely person out there made a file which
looks like python but isn't quite python and gave it the same extension as
python. Hello, skins. The python packaging system will happily do a syntax
check of all these 'python' files and tell you they are invalid. Its annoying
but harmless in buildout - and we have done our best to ignore it.
Unfortunately when you try to push to Heroku it seems to check the existing
slug and find loads of these skins and blow up with::

    SyntaxError: ("'return' outside function", ('./lib/python2.7/site-packages/Products/CMFPlone/skins/plone_deprecated/renderBase.py', 8, None, "return context.absolute_url()+'/'\n"))
    SyntaxError: ("'return' outside function", ('./lib/python2.7/site-packages/Products/CMFPlone/skins/plone_login/login.py', 18, None, "return context.restrictedTraverse('external_login_return')()\n"))
    SyntaxError: ("'return' outside function", ('./lib/python2.7/site-packages/Products/CMFPlone/skins/plone_login/require_login.py', 20, None, 'return portal.restrictedTraverse(login)()\n'))
     !     Heroku push rejected, failed to compile Python app

These errors are happening before any new requirements are loaded, so its
existing stuff breaking not the new stuff currently being pushed.

**There doesn't seem to be anyway to recover an app that is in this state**.

So I trashed that environemnt and started again.

To try and get round having to do multiple pushed I tried to ``pip bundle``
Plone. Turns out bundling all your dependencies in your repo and pushing that
just triggers a different timeout. Boo.

This time I was able to get Plone going in 2 pushes - the first with Zope
2.13.8, the second with Plone 4.1. And it worked. I had Plone running on
Heroku. But just like before I can no longer push to that app.

So I trashed that environment and started again - this time I was going to play
with RelStorage.

I disabled Plone in my requirements.txt and built Zope again. Reshuffling my
test scripts to push on GitHub had broken the runner. 7 or 8 pushes later and
it was working again - backed up my assumptions about Plone being to blame
for the eventual non-updateableness of my app.

Incidentally to see why your app didn't start just use ``~/bin/heroku logs``::

    2011-09-21T20:28:28+00:00 heroku[web.1]: Starting process with command `./bin/python runner.py -p 54808`
    2011-09-21T20:28:29+00:00 app[web.1]: sh: /app/../bin/mkzopeinstance: not found
    2011-09-21T20:28:29+00:00 app[web.1]: Traceback (most recent call last):
    2011-09-21T20:28:29+00:00 app[web.1]:   File "runner.py", line 99, in <module>
    2011-09-21T20:28:29+00:00 heroku[web.1]: Process exited
    2011-09-21T20:28:29+00:00 heroku[web.1]: State changed from starting to crashed

A good build would look like this::

    2011-09-21T20:33:54+00:00 heroku[web.1]: Starting process with command `./bin/python runner.py -p 55375`
    2011-09-21T20:33:54+00:00 app[web.1]: {'PATH': 'bin:/usr/local/bin:/usr/bin:/bin', 'PYTHONUNBUFFERED': 'true', 'PORT': '55375', 'HOME': '/app'}
    2011-09-21T20:33:55+00:00 app[web.1]: /app/zope/bin/runzope -X debug-mode=on
    2011-09-21T20:33:56+00:00 app[web.1]: 2011-09-21 20:33:56 INFO ZServer HTTP server started at Wed Sep 21 20:33:56 2011
    2011-09-21T20:33:56+00:00 app[web.1]: 2011-09-21 20:33:56 INFO Zope Ready to handle requests
    2011-09-21T20:33:56+00:00 heroku[web.1]: State changed from starting to up

But DATABASE_URL was not set.

I added a new folder called django_bait which had a settings.py. The folder
structure was now::

    requirements.txt
    runner.py
    Procfile
    django_bait/
        settings.py

Heroku detected the settings.py, decided this was a Django app and updated it
with DB settings.

To see a file that Heroku has fiddled with you can cat it::

    ~/bin/heroku run cat django_bait/settings.py

And happily my assumption that DATABASE_URL should be in os.environ was backed
up::

    import os, sys, urlparse
    urlparse.uses_netloc.append('postgres')
    urlparse.uses_netloc.append('mysql')
    try:
        if os.environ.has_key('DATABASE_URL'):
            url = urlparse.urlparse(os.environ['DATABASE_URL'])
            DATABASES['default'] = {
                'NAME':     url.path[1:],
                'USER':     url.username,
                'PASSWORD': url.password,
                'HOST':     url.hostname,
                'PORT':     url.port,
            }
            if url.scheme == 'postgres':
                DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
            if url.scheme == 'mysql':
                DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
    except:
        print "Unexpected error:", sys.exc_info()

So where is my DATABASE_URL!?

It looks like you need a bit of django_bait to get a DATABASE_URL.... I started
yet another app but with django_bait in place from the start and it has a
DATABASE_URL \o/

Starting up the app now yields::

    2011-09-21T21:07:33+00:00 heroku[web.1]: State changed from starting to up
    2011-09-21T21:07:34+00:00 app[web.1]: Traceback (most recent call last):
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/bin/runzope", line 9, in <module>
    2011-09-21T21:07:34+00:00 app[web.1]:     load_entry_point('Zope2==2.13.8', 'console_scripts', 'runzope')()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/run.py", line 21, in run
    2011-09-21T21:07:34+00:00 app[web.1]:     starter.prepare()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/__init__.py", line 86, in prepare
    2011-09-21T21:07:34+00:00 app[web.1]:     self.startZope()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/__init__.py", line 259, in startZope
    2011-09-21T21:07:34+00:00 app[web.1]:     Zope2.startup()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/__init__.py", line 47, in startup
    2011-09-21T21:07:34+00:00 app[web.1]:     _startup()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/App/startup.py", line 81, in startup
    2011-09-21T21:07:34+00:00 app[web.1]:     DB = dbtab.getDatabase('/', is_root=1)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/datatypes.py", line 287, in getDatabase
    2011-09-21T21:07:34+00:00 app[web.1]:     db = factory.open(name, self.databases)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/datatypes.py", line 185, in open
    2011-09-21T21:07:34+00:00 app[web.1]:     DB = self.createDB(database_name, databases)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/Zope2/Startup/datatypes.py", line 182, in createDB
    2011-09-21T21:07:34+00:00 app[web.1]:     return ZODBDatabase.open(self, databases)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/ZODB/config.py", line 101, in open
    2011-09-21T21:07:34+00:00 app[web.1]:     storage = section.storage.open()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/relstorage/config.py", line 33, in open
    2011-09-21T21:07:34+00:00 app[web.1]:     return RelStorage(adapter, name=config.name, options=options)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/relstorage/storage.py", line 167, in __init__
    2011-09-21T21:07:34+00:00 app[web.1]:     self._adapter.schema.prepare()
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/relstorage/adapters/schema.py", line 949, in prepare
    2011-09-21T21:07:34+00:00 app[web.1]:     self.connmanager.open_and_call(callback)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/relstorage/adapters/connmanager.py", line 76, in open_and_call
    2011-09-21T21:07:34+00:00 app[web.1]:     res = callback(conn, cursor)
    2011-09-21T21:07:34+00:00 app[web.1]:   File "/app/lib/python2.7/site-packages/relstorage/adapters/schema.py", line 939, in callback
    2011-09-21T21:07:34+00:00 app[web.1]:     self.install_procedures(cursor)
    2011-09-21T21:07:34+00:00 app[web.1]:     cursor.execute("CREATE LANGUAGE plpgsql")
    2011-09-21T21:07:34+00:00 app[web.1]:
    2011-09-21T21:07:34+00:00 heroku[web.1]: Process exited
    2011-09-21T21:07:35+00:00 heroku[web.1]: State changed from up to crashed

Bummer. Maybe i'll just run my site out of RAM... What didn't show up in that
log but did show up when i did ``~/bin/heroku run bin/python runner.py debug``
was::

    psycopg2.ProgrammingError: must be owner of database foobarbaz

Fixed by downgrading to RelStorage 1.4.x - this version doesn't need the
stored procedures.

Now to sort out URLs.

http://old.zope.org/Members/4am/SiteAccess2/vhosting

I added a SiteRoot object to ``/Plone`` with the default settings.

I added a DTMLMethod to the ``/`` called penguin that contained::

    Is there a path, and does it start with 'Z'?
    <dtml-let stack="REQUEST['TraversalRequestNameStack']">
      <dtml-if "stack and stack[-1]=='Z'">
        Get rid of 'Z':     <dtml-call "stack.pop()">
        Put it back logically: <dtml-call "REQUEST.setVirtualRoot('Z')">
      <dtml-else>
        <dtml-call "REQUEST['TraversalRequestNameStack'].append('Plone')">
      </dtml-if>
    </dtml-let>

I added an AccessRule to ``/`` and told it to use the ``penguin`` method.

Now anyone accessing the root of my app will get ``/Plone``. To get to the ZMI
you go to ``/Z/manage``.

Weaponising
-----------

In an ideal world I would create a single egg that contained the runner and all
the requirements. You would do something like this in your requirements::

    heroku-plone [zope-2.13.8]

And then you would push::

    heroku-plone [plone-4.1]

This would get around managing a 230 line requirements.txt in multiple projects
and currently is enough to work around the too-much-at-once limit of heroku.

Unfortunately pip doesnt support ``extras_requires`` so this doesnt work!!

The next option is to create a meta-package for each supported plone version:

    heroku-zope-2-13-8
    heroku-plone-4-1

Much messier but still hides away the requirements.txt.


