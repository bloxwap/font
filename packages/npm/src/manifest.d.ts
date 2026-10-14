/** Content-addressed inventory of the built package. Scripts use ISO 15924 tags. */
export interface FontFace {
 readonly path: string;
 readonly family: string;
 readonly weight: number | readonly [number, number];
 readonly style: 'normal' | 'italic';
 readonly scripts: readonly string[];
 readonly version: string;
 readonly packageVersion: string;
 readonly bytes: number;
 readonly sha256: string;
 readonly format: 'woff2' | 'ttf';
 readonly axes: Readonly<Record<string, number | { min: number; default: number; max: number }>>;
 readonly registrationName?: string;
 /** Committed static WOFF2 path, relative to the source repository. */
 readonly source?: string;
 readonly sourceWeight?: number;
 readonly variableSource?: string;
 readonly variableSourceSha256?: string;
 readonly generation?: 'decode-static-woff2-and-register';
 readonly sourceSha256?: string;
}
export interface FontManifest {
 readonly schemaVersion: 1;
 readonly package: '@bloxwap/font';
 readonly version: string;
 readonly license: 'OFL-1.1';
 readonly generator: string;
 readonly faces: readonly FontFace[];
}
declare const manifest: FontManifest;
export default manifest;
