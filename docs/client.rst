Client
========

Client is the class handling the Transmission JSON-RPC client protocol.

Torrent ids
-----------

Many functions in Client takes torrent id.
You can find torrent-ids spec in `official docs
<https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#31-torrent-action-requests>`_

.. note::

    It's recommended that you use torrent's ``info_hash`` as torrent id. The torrent's ``info_hash`` will never change.

Client
------

.. automodule:: transmission_rpc

.. autofunction:: from_url

.. autoclass:: Client
    :members:

.. autoclass:: PortTestResult
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: __init__, __new__

Timeouts
--------

Since most methods results in HTTP requests against Transmission, it is
possible to provide a argument called ``timeout``. Default timeout is 30 seconds.


.. toctree::
   :maxdepth: 2
   :caption: Contents:
