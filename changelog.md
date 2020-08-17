## [Unreleased](https://github.com/Trim21/transmission-rpc/compare/v3.0.0...HEAD)

## [v3.0.0](https://github.com/Trim21/transmission-rpc/compare/v3.0.0a4...v3.0.0) - 2020-08-17

### Bug Fixes
- **client:** failed to add url which is http url but not end with 'torrent' ([#16](https://github.com/Trim21/transmission-rpc/issues/16))

### Code Refactoring
- return File instead of return dict ([#23](https://github.com/Trim21/transmission-rpc/issues/23))
- Client will use [`yarl`](https://github.com/aio-libs/yarl) to build url

### BREAKING CHANGES

`Torrent.files()` will return `List[File]`
`Client.get_files()` will return `Dict[int, List[File]]`
Client args `address` and `user` is not available anymore

### Features
- check rpc version for kwargs

## [v3.0.0a4](https://github.com/Trim21/transmission-rpc/compare/v3.0.0a3...v3.0.0a4) - 2020-08-17

### Code Refactoring
- remove kwargs checker as a ValueError will be raised
- return File instead of return dict ([#23](https://github.com/Trim21/transmission-rpc/issues/23))

### BREAKING CHANGES

`Torrent.files()` will return `List[File]`
`Client.get_files()` will return `Dict[int, List[File]]`

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
