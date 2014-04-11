magfest
=======

This is the webapp that MAGFest uses to track things like registration, events, staffers, groups, dealers, jobs, game checkouts, etc.

If you want to run a development server to play around with it, there are two supporter approachs: running it locally and running on Vagrant.


Setting Up a Local Dev Environment
==================================

Linux is currently the only supported development platform.  Theoretically this codebase should work on other platforms, but this has not been tested.

Here's what you need installed before you can run this:
* Python 3.3 (with source headers)
* Postgresql 9.0 or later

Let's start by getting all of the Python dependencies installed.  We'll clone the repo, make a virtualenv, install distribute, and then install all of our Python dependencies:

```bash
$ git clone https://github.com/omegacon/magfest
$ cd magfest
$ python3.3 -m venv env
$ ./env/bin/python distribute_setup.py
$ ./env/bin/python setup.py develop
```

Now we need to create a Postgresql database.  The default username, password, and database name is "omegacon", so we'll go ahead and do that, e.g.

```bash
$ sudo -i
$ sudo -i -u postgres
$ createuser --superuser --pwprompt omegacon
$ createdb --owner=omegacon omegacon
```

Now we're ready to create all of our database tables, which we can do by running the init_db script.  After that we can actually start the server:

```bash
$ ./env/bin/python uber/init_db.py
$ ./env/bin/python uber/run_server.py
```

Now we can go to http://localhost:23232/ and log in with the email address "magfest@example.com" and the password "magfest".

If you'd live to override any of the default configuration settings, you can create a "development.conf" file in the top-level directory of the repo, and any values you put there will override the default values.  For example, suppose we were running remotely on a cloud server like Rackspace, so instead of binding to localhost, we'd instead bind to our local IP address and tell the web server to issue its redirects appropriately, e.g.

```
hostname = "12.34.56.78"
url_root = "http://12.34.56.78:23232"
```

If you'd like to insert about 10,000 attendees with realistic shifts and whatnot, you can run the following command (warning, this takes 5-10 minutes to insert everything):

```bash
$ ./env/bin/python uber/tests/import_test_data.py
```

Alternatively, you could insert directly with the sql file in the same directory as that script (though you'll need to start with an empty database for this to work), e.g.

```bash
$ psql --host=localhost --username=omegacon --password omegacon < uber/tests/test_data.sql
```


Running on Vagrant
==================
[Vagrant](http://www.vagrantup.com/) is a great way to provide portable development environments by letting you install a local VM and have it automatically configured with all of the software and dependencies you need to start developing.  If you're already running Linux, we recommend you just develop locally, so this section assumes you are using Windows.  Here's what you'll need to install to get your dev environment up and running:
* [TortoiseGit](https://code.google.com/p/tortoisegit/) for checking out this repo
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads) for running your development VM
* [Vagrant](http://www.vagrantup.com/downloads.html) itself
* [Putty](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html) for SSH-ing into your development machine once it's up and running

First, use TortoiseGit to check out this repo: ``https://github.com/omegacon/magfest``

Next open up a DOS prompt and change into the ``magfest`` directory that was created when you cloned your repo, and type ``vagrant up``.  This does a bunch of different things:
* downloads a VirtualBox image of an Ubuntu server from the internet
* starts up the VM and installs all necessary OS dependencies
* creates a database filled with test data
* sets up a Python virtualenv with all of the necessary Python packages needed to run Uber

Now that you have your VM, the only thing left to do is log into your server and start Uber.  Since I don't currently have a Windows machine to test on, I'm a little fuzzy on the best way to do that.  I'll fill in the details as soon as I get that figured out, but in the meantime here are some links:
* http://stackoverflow.com/questions/9885108/ssh-to-vagrant-box-in-windows
* http://www.robertpate.net/blog/2013/getting-the-vagrant-ssh-command-to-work-on-windows/

Once you've logged in, you can run the following command to run Uber:

```bash
python uber/run_server.py
```

After running this command, you can go to http://localhost:23232/ and log in with the email address "magfest@example.com" and the password "magfest".

Now you're ready to do development; every time you edit one of the Python files that make up Uber, the process will restart automatically, so you'll see the change as soon as you refresh your browser.  The only thing to watch out for is that if you make a syntax error, the process will stop altogether since it can't restart without being valid.  In that case you'll have to re-run the above command to re-start the server (after fixing your syntax error).
