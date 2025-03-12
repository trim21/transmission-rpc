# Transmission-rpc Readme

[![PyPI](https://img.shields.io/pypi/v/transmission-rpc)](https://pypi.org/project/transmission-rpc/)
[![Documentation Status](https://readthedocs.org/projects/transmission-rpc/badge/)](https://transmission-rpc.readthedocs.io/)
[![test](https://github.com/trim21/transmission-rpc/actions/workflows/ci.yaml/badge.svg)](https://github.com/trim21/transmission-rpc/actions/workflows/ci.yaml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/transmission-rpc)](https://pypi.org/project/transmission-rpc/)
[![Codecov branch](https://img.shields.io/codecov/c/github/Trim21/transmission-rpc/master)](https://codecov.io/gh/Trim21/transmission-rpc/branch/master)

## Introduction

`transmission-rpc` is a python wrapper on top of [transmission](https://github.com/transmission/transmission) JSON RPC protocol,
hosted on GitHub at [github.com/trim21/transmission-rpc](https://github.com/trim21/transmission-rpc)

Support 2.40 (released 2011-10-05) <= transmission version <= 4.1.0-beta.1 (released 2024-12-13),
should works fine with newer rpc version but some new feature may be missing.

## versioning

`transmission-rpc` follow [Semantic Versioning](https://semver.org/),
report an issue if you found unexpected API break changes at same major version.

Due to the tradition of python packaging community,
dropping support for EOL python versions will not be considered breaking change.

## Install

```console
pip install transmission-rpc -U
```

## Documents

<https://transmission-rpc.readthedocs.io/en/stable/>

## Contributing

All kinds of PRs (docs, feature, bug fixes and eta...) are most welcome.

### Setup Local Development Environment

At first, you need to install [python>=3.10](https://python.org/), and [task](https://taskfile.dev/) (or you can also run command in `taskfile.yaml` directly).

It's recommended to python3.10 as local development python version.

```shell
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
# install git pre-commit hooks
pre-commit install
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
