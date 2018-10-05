if 1:
    from transmission_rpc import Client, DEFAULT_PORT
    from transmission_rpc.utils import get_arguments

    print(get_arguments('torrent-add', 15))
    # c = Client(port=DEFAULT_PORT,
    #            user='transmission', password='password')

    # torrent_url = 'magnet:?xt=urn:btih:e84213a794f3ccd890382a54' + \
    #               'a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso'
    # c.add_torrent(torrent_url)
