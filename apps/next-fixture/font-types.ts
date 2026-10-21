import manifest from '@bloxwap/font/manifest';
import type { FontFace } from '@bloxwap/font/manifest';
import sans from '@bloxwap/font-native/BloxwapSans';
export const semiBoldAsset: number = sans['BloxwapSans-SemiBold'];
export const nativeFaces: readonly FontFace[] = manifest.faces.filter(face => face.format === 'ttf');
