..
    Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
    Licensed under the MIT license.

Transmission RPC
################

Introduction
============

This is **transmissionrpc**. This module helps using Python to connect
to a Transmission_ JSON-RPC service. transmissionrpc is compatible with
Transmission 1.31 and later.

transmissionrpc is licensed under the MIT license.

.. _Transmission: http://www.transmissionbt.com/

Getting started
===============

Transmission is available at
`Python Package Index <http://pypi.python.org/pypi/transmissionrpc/>`_. To
install the transmissionrpc python module use easy_install or pip.

::

    $ easy_install transmissionrpc

.. NOTE::
	You might need administrator privileges to install python modules.

You may also download the tarball from `Python Package Index <http://pypi.python.org/pypi/transmissionrpc/>`_. Untar and install.

::

    $ tar -xzf transmissionrpc-0.12.tar.gz
    $ cd transmissionrpc-0.12
    $ python setup.py install

Dependecies
-----------

transmissionrpc has the following dependencies.

 * Python >= 2.6
 * Six >= 1.1.0, https://pypi.python.org/pypi/six/

Report a problem
----------------

Problems with transmissionrpc should be reported through the issue tracker at
bitbucket_. Please look through the `existing issues`_ before opening a
`new issue`_.

.. _existing issues: http://bitbucket.org/blueluna/transmissionrpc/issues/
.. _new issue: http://bitbucket.org/blueluna/transmissionrpc/issues/new/

Installing from source
======================

The source code
---------------

Transmission is hosted at bitbucket_ using mercurial_. To get a working copy,
run
::

   $ hg clone http://www.bitbucket.org/blueluna/transmissionrpc/

The source code will be fetched and stored the directory transmissionrpc.

Then install the module using
::

    $ python setup.py install

Or if you wish to further develop transmissionrpc itself use
::

	$ python setup.py develop

This will link this directory to the library as transmissionrpc.

.. _bitbucket: http://www.bitbucket.org/blueluna/transmissionrpc/
.. _mercurial: http://www.selenic.com/mercurial

Poking around
-------------

Now that transmissionrpc has been installed, run python and start to poke
around. Following will create a RPC client and list all torrents.

::

    >>> import transmissionrpc
    >>> tc = transmissionrpc.Client('localhost', port=9091)
    >>> tc.get_torrents()

List will return a dictionary of Torrent object indexed by their id. You might
not have any torrents yet. This can be remedied by adding an torrent.
::

    >>> tc.add_torrent('http://releases.ubuntu.com/8.10/ubuntu-8.10-desktop-i386.iso.torrent')
    {1: <Torrent 1 "ubuntu-8.10-desktop-i386.iso">}
    >>> tc.get_torrent(1)
    {1: <Torrent 1 "ubuntu-8.10-desktop-i386.iso">}

As you saw, the add_url and info calls also returns a dictionary with
``{<id>: <Torrent>, ...}``. More information about a torrent transfer can be
found in the Torrent object.
::

    >>> torrent = tc.get_torrent(1)[1]
    >>> torrent.name
    'ubuntu-8.10-desktop-i386.iso'
    >>> torrent.hashString
    '33820db6dd5e5928d23bc811bbac2f4ae94cb882'
    >>> torrent.status
    'downloading'
    >>> torrent.eta
    datetime.timedelta(0, 750)

Well, we weren't that interested in Ubuntu so lets stop the transfer and the
remove it.

::

    >>> tc.stop_torrent(1)
    >>> tc.remove_torrent('33820db6dd5e5928d23bc811bbac2f4ae94cb882')

See what we did there? most methods in transmissionrpc can take both torrent id
and torrent hash when referring to a torrent. lists and sequences are also
supported.

    >>> tc.get_torrents([2, 'caff87b88f50f46bc22da3a2712a6a4e9a98d91e'])
    {2: <Torrent 2 "ubuntu-8.10-server-amd64.iso">, 3: <Torrent 3 "ubuntu-8.10-alternate-amd64.iso">}
    >>> tc.get_torrents('1:3')
    {2: <Torrent 2 "ubuntu-8.10-server-amd64.iso">, 3: <Torrent 3 "ubuntu-8.10-alternate-amd64.iso">}

Continue to explore and have fun! For more in depth information read the module
reference.

A note about debugging information
----------------------------------

If you ever need to see what's going on inside transmissionrpc, you can change
the logging level of transmissionrpc. This is done with these easy steps
::

	>>> import logging
	>>> logging.getLogger('transmissionrpc').setLevel(logging.DEBUG)

Note that this will produce a whole lot of output! Other levels are (listed by
severity)

 * ``logging.ERROR``
 * ``logging.WARNING``
 * ``logging.INFO``
 * ``logging.DEBUG``

The default logging level of transmissionrpc is ``logging.ERROR``.

Module reference
================

.. toctree::
   :maxdepth: 2

   reference/transmissionrpc

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
