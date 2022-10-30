from transmission_rpc import Client

torrent_url = "http://releases.ubuntu.com/18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent"
c = Client(host="localhost", port=9091, username="transmission", password="password")
c.add_torrent(torrent_url)

########

from transmission_rpc import Client

c = Client(username="transmission", password="password")

torrent_url = "magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso"
c.add_torrent(torrent_url)

########

import requests

from transmission_rpc import Client

c = Client(username="trim21", password="123456")

torrent_url = "http://releases.ubuntu.com/18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent"
r = requests.get(torrent_url)

# client will base64 the torrent content for you.
c.add_torrent(r.content)

# or use a file-like object
with open("a", "wb") as f:
    f.write(r.content)
with open("a", "rb") as f:
    c.add_torrent(f)
