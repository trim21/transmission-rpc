## [Unreleased](https://github.com/Trim21/transmission-rpc/compare/v3.0.0a3...HEAD)


## [v3.0.0a3](https://github.com/Trim21/transmission-rpc/compare/v3.0.0a2...v3.0.0a3) - 2020-07-03

### Bug Fixes
- **client:** failed to add url which is http url but not end with 'torrent' ([#16](https://github.com/Trim21/transmission-rpc/issues/16))


## [v3.0.0a2](https://github.com/Trim21/transmission-rpc/compare/v3.0.0a1...v3.0.0a2) - 2020-06-01


## [v3.0.0a1](https://github.com/Trim21/transmission-rpc/compare/v2.0.4...v3.0.0a1) - 2020-06-01

### Bug Fixes
- poetry bug
- cache with python version change

### Code Refactoring
- Client will use [`yarl`](https://github.com/aio-libs/yarl) to build url

### Features
- warn about arguments replace
- check rpc version for kwargs

### BREAKING CHANGE

Client args `address` and `user` is not available anymore


## [v2.0.4](https://github.com/Trim21/transmission-rpc/compare/v2.0.3...v2.0.4) - 2020-05-20

### Bug Fixes
- **client:** host parameter in `Client.__init__` works without address ([#6](https://github.com/Trim21/transmission-rpc/issues/6))


## [v2.0.3](https://github.com/Trim21/transmission-rpc/compare/v1.0.4...v2.0.3) - 2020-01-19

### Bug Fixes
- arguments will work
- build error from source
