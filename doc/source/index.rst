.. transmission-rpc documentation master file, created by
   sphinx-quickstart on Fri Oct  5 09:29:21 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to transmission-rpc's documentation!
============================================

:code:`transmission-rpc` is a python library to help your control your transmission deamon remotely.

quickstart
----------

.. code-block:: python

    from transmission_rpc import client

    torrent_url = 'http://releases.ubuntu.com/' + \
                  '18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent'
    c = client.Client(address='localhost', port=9091,
                      user='transmission', password='password')
    c.add_torrent(torrent_url)



.. code-block:: python

    from transmission_rpc import client

    c = client.Client(address='localhost', port=9091,
                      user='transmission', password='password')

    torrent_url = 'magnet:?xt=urn:btih:e84213a794f3ccd890382a54' + \
                  'a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso'
    c.add_torrent(torrent_url)

you can also give a url starts with :code:`file://`.

python2 support will be deprecated in future version.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    client.rst
    session.rst
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
