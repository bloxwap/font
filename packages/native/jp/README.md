# @bloxwap/font-native-jp

Opt-in native static TTFs for BloxwapSansJP, BloxwapMonoJP. First published in 0.1.3. Web fonts are available separately in `@bloxwap/font`.

```sh
npm install @bloxwap/font-native-jp
```

Register selected faces with Expo or your React Native asset pipeline before rendering:

```js
const regular = require('@bloxwap/font-native-jp/assets/BloxwapSansJP/BloxwapSansJP-Regular.ttf');
// Or import the typed Metro map for every weight in this family:
const faces = require('@bloxwap/font-native-jp/BloxwapSansJP');
```

Use the exact registration key (for example `BloxwapSansJP-Regular`) as `fontFamily`, without `fontWeight` or `fontStyle` overrides. A family map bundles every face in that family; direct asset imports bundle only selected files. All nine weights (100–900) and available italics retain their existing registration names and binary bytes. Pixel uses ROND 50.

The inventory in `@bloxwap/font/manifest` records each native face's package, asset import path and SHA-256. Other scripts are separate opt-in packages: `@bloxwap/font-native-arabic`, `-hebrew`, `-armenian`, `-georgian`, `-jp`, `-kr`, `-sc`. They contain the corresponding Sans and Mono families.

From a source checkout, set `FONT_PYTHON` to the pinned font toolchain interpreter and run `node packages/npm/scripts/build.mjs` at the repository root, or run `npm pack` in this package. Generated assets and the license are assembled by that build.

See [Cross-platform typography](https://bloxwap.github.io/font/docs/cross-platform/) for registration, locale selection and accessibility guidance.

## License

SIL Open Font License 1.1 (`OFL-1.1`). See the included LICENSE. © 2026 Bloxwap, Inc.
