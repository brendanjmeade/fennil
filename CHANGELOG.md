# CHANGELOG

<!-- version list -->

## v1.3.0 (2026-02-18)

### Bug Fixes

- Always show fault lines
  ([`58a87b9`](https://github.com/brendanjmeade/fennil/commit/58a87b9d2a21ffe2c1307336e903ab490e27eea4))

- Display SS TDE mesh and Slip lines
  ([`e960a0f`](https://github.com/brendanjmeade/fennil/commit/e960a0f4fa3921b395f4e17eff0fcea5356eba43))

- Fix bug removing first dataset
  ([`441e536`](https://github.com/brendanjmeade/fennil/commit/441e5360c09a33196dafff0eb7d22908fccf8eee))

- Switch str/mog from vectors to points
  ([`de10c73`](https://github.com/brendanjmeade/fennil/commit/de10c73f75e78632e5ad4ee1ff393348ef8c66cb))

- **dependencies**: Update python dependencies
  ([`d0b2fde`](https://github.com/brendanjmeade/fennil/commit/d0b2fde5eaf461e374fa1fa633c6faf836347f9d))

- **style**: Use spec styles
  ([`b0aa5f9`](https://github.com/brendanjmeade/fennil/commit/b0aa5f91ace563584dc7f4e8cca9b0d79906311c))

### Continuous Integration

- Exclude CHANGELOG.md from pre-commit
  ([`2874874`](https://github.com/brendanjmeade/fennil/commit/2874874bda74219154af46210c8fd692623561ed))

- Make release manual process
  ([`0b0d545`](https://github.com/brendanjmeade/fennil/commit/0b0d545923e03257e3c085b141526ac4af17e855))

### Features

- **ui**: New ui
  ([`7538193`](https://github.com/brendanjmeade/fennil/commit/7538193c452ae0d38cea8cc624041ee62ecc77f3))

- **viz**: Allow viz filtering based on dataset
  ([`f233404`](https://github.com/brendanjmeade/fennil/commit/f23340418a4e70cb83b7503cd9f10d7c0b720ccb))

- **viz**: Make viz dynamic
  ([`2234c25`](https://github.com/brendanjmeade/fennil/commit/2234c25529a1b312987e0a566ba4faecb5f1c3d6))

### Refactoring

- Bring util to root package
  ([`fa580b8`](https://github.com/brendanjmeade/fennil/commit/fa580b8da762e860faf411fd8a9bd4e96720511d))

- Create fields.py and FIELD_REGISTRY
  ([`496ce61`](https://github.com/brendanjmeade/fennil/commit/496ce6110b4da1b362789fef19cfed725b33c842))

- Move core2.py and builder2.py
  ([`b1892da`](https://github.com/brendanjmeade/fennil/commit/b1892da0d660d648d8325c51de72fdd49344f6fb))

- Remove old code
  ([`d6c728b`](https://github.com/brendanjmeade/fennil/commit/d6c728b9c182f0ea189ffca3bd6d00446375c049))

- Rename FieldRegistry methods
  ([`9a54d89`](https://github.com/brendanjmeade/fennil/commit/9a54d894b10bce4d39d7e96bccb77cba74ce66f9))

- **viz**: Normalize viz builders
  ([`c6fa12a`](https://github.com/brendanjmeade/fennil/commit/c6fa12ad33962081b89a17f90cc7b061d02354d3))


## v1.2.1 (2026-02-10)

### Bug Fixes

- Change default map view to zoomed out over pacific
  ([`f4afad3`](https://github.com/brendanjmeade/fennil/commit/f4afad3930d9a6147652a6e6727904761d48fa7d))

- Change velocity scale to x2 instead of x10
  ([`47d8cec`](https://github.com/brendanjmeade/fennil/commit/47d8cecf7ef87a5eb80ff999a63495b061f9fb8d))

- Fix clipped field in file_browser
  ([`3e9fc72`](https://github.com/brendanjmeade/fennil/commit/3e9fc723a759d74267f9c3efb632dceb90c49cc4))

- Fix utils import
  ([`290593f`](https://github.com/brendanjmeade/fennil/commit/290593fa33ae788f7b74e40fc2cad4620a83d6d8))

- Refactor core.py into separate files
  ([`38ca51b`](https://github.com/brendanjmeade/fennil/commit/38ca51bae2d0e8caa6404ac0431ee35658dc71ad))

- Reorder layers so meshes are on the bottom
  ([`419114d`](https://github.com/brendanjmeade/fennil/commit/419114d20bf23ec561d0219f9e23907cd809479d))

### Continuous Integration

- Bump python version
  ([`c430d0b`](https://github.com/brendanjmeade/fennil/commit/c430d0b5ff8f632a0736a01cec8fb10a494ce84a))

- Fix pre-commit
  ([`1229f69`](https://github.com/brendanjmeade/fennil/commit/1229f69fa7a9971fe26dac33d4c682837194ae99))

- Fix ruff errors
  ([`1bb79eb`](https://github.com/brendanjmeade/fennil/commit/1bb79eb669f2ff24fde82ab355045d8feb74a09e))

### Refactoring

- Create utils/ dir
  ([`4f1cf3e`](https://github.com/brendanjmeade/fennil/commit/4f1cf3edaa6cc7740b2cce19c17690d2ab4d3a1a))

- Extract constants
  ([`9342e14`](https://github.com/brendanjmeade/fennil/commit/9342e1492ec8e527824e2dd6d6b24e3d2da5bf1c))

- Make Dataset class
  ([`8f89f22`](https://github.com/brendanjmeade/fennil/commit/8f89f2207359b5ff6fd9bd00f76d30ce130d1975))

- Move file browser out of core.py
  ([`e4b49e8`](https://github.com/brendanjmeade/fennil/commit/e4b49e86f9db97523d34986ca9bcfe940b7a306d))

- Split layer.py into components
  ([`b3a8e9d`](https://github.com/brendanjmeade/fennil/commit/b3a8e9d2eb930f20c4b911ecedce95998e9da4ee))

- Split UI into components/ dir
  ([`1ec69df`](https://github.com/brendanjmeade/fennil/commit/1ec69df345d4601e55a2b3487688112393a69759))

## v1.2.0 (2026-02-03)

### Bug Fixes

- Bump trame-deckgl version to >=2.0.4
  ([`2dbe3bb`](https://github.com/brendanjmeade/fennil/commit/2dbe3bbce07c18e02cf2206e3289f81ff6bf4acd))

- Fix locs displaying on the map
  ([`268a9a5`](https://github.com/brendanjmeade/fennil/commit/268a9a537a45135b029db2c07d43c48f5abae643))

### Features

- Add fault lines, slip lines, fault projections, and meshed values
  ([`3b08907`](https://github.com/brendanjmeade/fennil/commit/3b08907a6fb51bbff614c0024749c5540c4b9641))

- Add file browser, remove hardcoded data
  ([`17dac4b`](https://github.com/brendanjmeade/fennil/commit/17dac4b2059212e1570fa64594f60116fc84e193))

- Add tooltip
  ([`d10c0ce`](https://github.com/brendanjmeade/fennil/commit/d10c0ce4be27adc9701c4a0cdfd0932a65a2989f))

## v1.1.0 (2026-01-30)

### Features

- Add scale buttons for velocity scale field
  ([`b134b4a`](https://github.com/brendanjmeade/fennil/commit/b134b4a46a1a2a1eecf8e5c4111a7e8698f42738))

## v1.0.0 (2026-01-22)

- Initial Release
