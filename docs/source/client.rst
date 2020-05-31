.. transmission-rpc documentation master file, created by
   sphinx-quickstart on Fri Oct  5 09:29:21 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Client
========

Client is the class handling the Transmission JSON-RPC client protocol.

Torrent ids
------------

Many functions in Client takes torrent id.
You can find torrent-ids spec in `official docs
<https://github.com/transmission/transmission/blob/master/extras/rpc-spec.txt#L96-L101>`_

Timeouts
--------

Since most methods results in HTTP requests against Transmission, it is
possible to provide a argument called ``timeout``. Default timeout is 30 seconds.

.. automodule:: transmission_rpc.client
    :members:

.. autoclass:: Client
    :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents:
