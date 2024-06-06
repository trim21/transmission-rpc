# Transmission-rpc Readme

[![PyPI](https://img.shields.io/pypi/v/transmission-rpc)](https://pypi.org/project/transmission-rpc/)
[![Documentation Status](https://readthedocs.org/projects/transmission-rpc/badge/)](https://transmission-rpc.readthedocs.io/)
[![ci](https://github.com/Trim21/transmission-rpc/workflows/ci/badge.svg)](https://github.com/Trim21/transmission-rpc/actions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/transmission-rpc)](https://pypi.org/project/transmission-rpc/)
[![Codecov branch](https://img.shields.io/codecov/c/github/Trim21/transmission-rpc/master)](https://codecov.io/gh/Trim21/transmission-rpc/branch/master)

`transmission-rpc` is a python wrapper on top of [transmission](https://github.com/transmission/transmission) JSON RPC protocol,
hosted on GitHub at [github.com/trim21/transmission-rpc](https://github.com/trim21/transmission-rpc)

## Introduction

`transmission-rpc` is a python module implementing the json-rpc client protocol for the BitTorrent client Transmission.

Support 14 <= rpc version <= 17 (2.40 <= transmission version <= 4.0.6),
should works fine with newer rpc version but some new feature may be missing.

## versioning

`transmission-rpc` follow [Semantic Versioning](https://semver.org/),
report an issue if you found unexpected API break changes at same major version.

## Install

```console
pip install transmission-rpc -U
```

## Documents

<https://transmission-rpc.readthedocs.io/en/stable/>

## Contributing

All kinds of PRs (docs, feature, bug fixes and eta...) are most welcome.

### Setup Local Development Environment

At first, you need to install [python](https://python.org/), [poetry](https://python-poetry.org/) and [task](https://taskfile.dev/) (or you can also run command in `taskfile.yaml` directly).

It's recommended to python3.10 as local development python version.

```shell
poetry install --sync
poetry run pre-commit install # install git pre-commit hooks
```

### Lint

```shell
task lint
```

### Testing

You need to have a transmission daemon running

then add a `.env` file

```shell
export TR_HOST="..."
export TR_PORT="..."
export TR_USER="..."
export TR_PASS="..."
```

```shell
task test
```

## License

`transmission-rpc` is licensed under the MIT license.
