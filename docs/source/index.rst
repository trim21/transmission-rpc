.. transmission-rpc documentation master file, created by
    sphinx-quickstart on Fri Oct  5 09:29:21 2018.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

Welcome to transmission-rpc's documentation!
============================================

:code:`transmission-rpc` is a python3 library
to help your control your transmission daemon remotely.

quick start
-------------------------

.. code-block:: python

    from transmission_rpc import Client

    torrent_url = 'http://releases.ubuntu.com/' + \
                  '18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent'
    c = Client(host='localhost', port=9091, username='transmission', password='password')
    c.add_torrent(torrent_url)

    ########

    from transmission_rpc import Client

    c = Client(username='transmission', password='password')

    torrent_url = 'magnet:?xt=urn:btih:e84213a794f3ccd890382a54' + \
                  'a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso'
    c.add_torrent(torrent_url)

    ########

    from transmission_rpc import Client
    import requests

    c = Client(username='trim21', password='123456')

    torrent_url = 'http://releases.ubuntu.com/' + \
                  '18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent'
    r = requests.get(torrent_url)

    # client will base64 the torrent content for you.
    c.add_torrent(r.content)

    # or use a file-like object
    with open('a', 'wb') as f:
        f.write(r.content)
    with open('a', 'rb') as f:
        c.add_torrent(f)

:code:`client.add_torrent` support a url string,
file-like object(object with :code:`read()` method)
or base64 encoded torrent file content.


Arguments
-------------------

Each method has it own arguments.
You can pass arguments as kwargs when you call methods.

But in python, :code:`-` can't be used in a variable name,
so you need to replace :code:`-` with :code:`_`.

For example, :code:`torrent-add` method support arguments :code:`download-dir`,
you should call method like this.

.. code-block :: python

    from transmission_rpc import Client

    Client().add_torrent(torrent_url, download_dir='/path/to/download/dir')

:code:`transmission-rpc` will put
:code:`{"download-dir": "/path/to/download/dir"}` in arguments.


helper
------------

If you want to know what kwargs you can use for a method,
you can use :meth:`transmission_rpc.utils.get_arguments`
to get support arguments.
For example, transmission 2.94 is rpc version 15,
so just call :code:`print(get_arguments('torrent-add', 15))`

rpc method and class method are not same, but reversed

you can find rpc version by transmission version from
`transmission rpc docs <https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#5-protocol-versions>`_



.. toctree::
    :maxdepth: 2
    :caption: Contents:

    client.rst
    torrent.rst
    session.rst
    errors.rst
    utils.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
