# Changelog

## 2.0.3 (2025-05-16)

Full Changelog: [v2.0.2...v2.0.3](https://github.com/hanzoai/python-sdk/compare/v2.0.2...v2.0.3)

### Bug Fixes

* **package:** support direct resource imports ([dd95dad](https://github.com/hanzoai/python-sdk/commit/dd95dadc573369de39916f8bf4bd0e36fbe3feaf))
* **perf:** optimize some hot paths ([6da686a](https://github.com/hanzoai/python-sdk/commit/6da686a68775c8d364e16790752773392ed21329))
* **perf:** skip traversing types for NotGiven values ([5eade63](https://github.com/hanzoai/python-sdk/commit/5eade63f698e112a8c2a07fb7f3466bff33fdc39))
* **pydantic v1:** more robust ModelField.annotation check ([c060430](https://github.com/hanzoai/python-sdk/commit/c0604303395ca27f73f16ea4bc4d05841acba51d))


### Chores

* broadly detect json family of content-type headers ([11bc5fd](https://github.com/hanzoai/python-sdk/commit/11bc5fd48e6536cbec838b676c64ce7a175f6b09))
* **ci:** add timeout thresholds for CI jobs ([a283e86](https://github.com/hanzoai/python-sdk/commit/a283e8611476e227244e75d30c0340aa6afd67a1))
* **ci:** fix installation instructions ([d92f111](https://github.com/hanzoai/python-sdk/commit/d92f1116f14aaaa9bb2c8a5b186b37dc5781a7d7))
* **ci:** only use depot for staging repos ([15b3705](https://github.com/hanzoai/python-sdk/commit/15b3705165b138b4827f9fa18fa9b7b8966ab5bb))
* **ci:** upload sdks to package manager ([51807ff](https://github.com/hanzoai/python-sdk/commit/51807ff9c91fbf15152c4d8850eec0e9a300e685))
* **client:** minor internal fixes ([8b19fe5](https://github.com/hanzoai/python-sdk/commit/8b19fe5acf34e3f9d7da0b6b8739cc893fe784ed))
* **internal:** avoid errors for isinstance checks on proxies ([ef6b7d3](https://github.com/hanzoai/python-sdk/commit/ef6b7d319cee29263bac020390d6b3ec513648a4))
* **internal:** base client updates ([d417414](https://github.com/hanzoai/python-sdk/commit/d417414c3430003fed22f62c10de07c0088588a2))
* **internal:** bump pyright version ([c7706f0](https://github.com/hanzoai/python-sdk/commit/c7706f0871c28d186e5f249d24eb3a2a93b23cb2))
* **internal:** codegen related update ([697ab40](https://github.com/hanzoai/python-sdk/commit/697ab40b8cd1bedf4cf7398a35408ca364e33d52))
* **internal:** expand CI branch coverage ([fd3cd26](https://github.com/hanzoai/python-sdk/commit/fd3cd268f6d853b66702f5e05934b0b7deb29abf))
* **internal:** fix list file params ([e2d6428](https://github.com/hanzoai/python-sdk/commit/e2d64282e2feaa9e239f434e2644d1a5e5271ede))
* **internal:** import reformatting ([3a69aa9](https://github.com/hanzoai/python-sdk/commit/3a69aa9c55cc2bd2289335ce353c9da067a1b4f6))
* **internal:** minor formatting changes ([c4357ac](https://github.com/hanzoai/python-sdk/commit/c4357ac7f204b602cb29c4d4beb9bd1ca99773fc))
* **internal:** reduce CI branch coverage ([56b4e45](https://github.com/hanzoai/python-sdk/commit/56b4e459a37ed1510622d2ff2127d789ddaa9893))
* **internal:** refactor retries to not use recursion ([25ce097](https://github.com/hanzoai/python-sdk/commit/25ce0973aaa11be64968f6236ec101ce524dc855))
* **internal:** slight transform perf improvement ([#24](https://github.com/hanzoai/python-sdk/issues/24)) ([f35d86d](https://github.com/hanzoai/python-sdk/commit/f35d86ddeba896b99c00874cbd3bfba0086741cd))
* **internal:** update models test ([77dbb5e](https://github.com/hanzoai/python-sdk/commit/77dbb5e3520be7aabad5a8e1259ab060d8d3dfca))
* **internal:** update pyright settings ([bbb302d](https://github.com/hanzoai/python-sdk/commit/bbb302d80ca7a6cf3b5bf2a58fdaac4f3a6e7e2e))
* slight wording improvement in README ([#25](https://github.com/hanzoai/python-sdk/issues/25)) ([b42f098](https://github.com/hanzoai/python-sdk/commit/b42f098ec1005979a4ee2cb1bd2bb394c16ae2a3))

## 2.0.2 (2025-04-04)

Full Changelog: [v2.0.1...v2.0.2](https://github.com/hanzoai/python-sdk/compare/v2.0.1...v2.0.2)

### Chores

* **internal:** minor test fixes ([#20](https://github.com/hanzoai/python-sdk/issues/20)) ([da1ba8f](https://github.com/hanzoai/python-sdk/commit/da1ba8fe0fdc7bb73c401b28c8535c3f6d564ede))
* **internal:** remove trailing character ([#22](https://github.com/hanzoai/python-sdk/issues/22)) ([572b121](https://github.com/hanzoai/python-sdk/commit/572b12185e2a7bd746163243314618021be6f1be))

## 2.0.1 (2025-03-28)

Full Changelog: [v2.0.0...v2.0.1](https://github.com/hanzoai/python-sdk/compare/v2.0.0...v2.0.1)

### Chores

* update SDK settings ([#17](https://github.com/hanzoai/python-sdk/issues/17)) ([01f71f1](https://github.com/hanzoai/python-sdk/commit/01f71f1ddb19bae7479b1375bfc247ce0e74802e))

## 2.0.0 (2025-03-27)

Full Changelog: [v1.1.0...v2.0.0](https://github.com/hanzoai/python-sdk/compare/v1.1.0...v2.0.0)

### Features

* **api:** api update ([#14](https://github.com/hanzoai/python-sdk/issues/14)) ([bd5f39c](https://github.com/hanzoai/python-sdk/commit/bd5f39c1eb8f8fdf04443ee8b448184b80759785))

## 1.1.0 (2025-03-26)

Full Changelog: [v1.0.0...v1.1.0](https://github.com/hanzoai/python-sdk/compare/v1.0.0...v1.1.0)

### Features

* **api:** api update ([#12](https://github.com/hanzoai/python-sdk/issues/12)) ([d37d657](https://github.com/hanzoai/python-sdk/commit/d37d657eea2988c528bb1cb7560f6e0ab2f1e61e))
* **api:** update via SDK Studio ([#4](https://github.com/hanzoai/python-sdk/issues/4)) ([e5137ed](https://github.com/hanzoai/python-sdk/commit/e5137ed411811a52ff9b7cc0e44a678ef3f3065e))
* **api:** update via SDK Studio ([#6](https://github.com/hanzoai/python-sdk/issues/6)) ([8da866d](https://github.com/hanzoai/python-sdk/commit/8da866dea4cc031c8388be2e013f79f96f6f2950))


### Bug Fixes

* **ci:** ensure pip is always available ([#9](https://github.com/hanzoai/python-sdk/issues/9)) ([42dc32d](https://github.com/hanzoai/python-sdk/commit/42dc32d241c11794317fa4a89ee7e1a15a58855b))
* **ci:** remove publishing patch ([#10](https://github.com/hanzoai/python-sdk/issues/10)) ([339a613](https://github.com/hanzoai/python-sdk/commit/339a6135e50161ae8acacaf7d1d7381a6d77428d))


### Chores

* go live ([#1](https://github.com/hanzoai/python-sdk/issues/1)) ([c1f495e](https://github.com/hanzoai/python-sdk/commit/c1f495ea0e560ada8c76c571b42928bf8e1b5ee5))
* go live ([#11](https://github.com/hanzoai/python-sdk/issues/11)) ([7e1b48c](https://github.com/hanzoai/python-sdk/commit/7e1b48ce65cba77dd8fbd7e019d3913c492a87a6))
* **internal:** codegen related update ([#8](https://github.com/hanzoai/python-sdk/issues/8)) ([ebc4649](https://github.com/hanzoai/python-sdk/commit/ebc4649173ca01aeb26903c6fe32adad0be49491))
* update SDK settings ([#3](https://github.com/hanzoai/python-sdk/issues/3)) ([beb5358](https://github.com/hanzoai/python-sdk/commit/beb53583fcdb15983f09a73be166dbbca30fb93f))

## 0.1.0-alpha.1 (2025-03-15)

Full Changelog: [v0.0.1-alpha.0...v0.1.0-alpha.1](https://github.com/hanzoai/python-sdk/compare/v0.0.1-alpha.0...v0.1.0-alpha.1)

### Features

* **api:** update via SDK Studio ([#4](https://github.com/hanzoai/python-sdk/issues/4)) ([e5137ed](https://github.com/hanzoai/python-sdk/commit/e5137ed411811a52ff9b7cc0e44a678ef3f3065e))


### Chores

* go live ([#1](https://github.com/hanzoai/python-sdk/issues/1)) ([c1f495e](https://github.com/hanzoai/python-sdk/commit/c1f495ea0e560ada8c76c571b42928bf8e1b5ee5))
* update SDK settings ([#3](https://github.com/hanzoai/python-sdk/issues/3)) ([beb5358](https://github.com/hanzoai/python-sdk/commit/beb53583fcdb15983f09a73be166dbbca30fb93f))
