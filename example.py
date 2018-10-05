if 1:
    from transmission_rpc import client
    import requests
    torrent_url = 'http://releases.ubuntu.com/' + \
                  '18.04/ubuntu-18.04.1-desktop-amd64.iso.torrent'
    c = client.Client(address='localhost', port=9091,
                      user='transmission', password='password')
    c.add_torrent(torrent_url)
