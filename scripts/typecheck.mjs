#!/usr/bin/env node
// Type-checks the current app with tsrs (Rust port of the TypeScript 7 checker) where it ships a
// native binary: macOS arm64 and Linux x64/arm64. Windows and Intel Mac have no tsrs build, so
// this falls back to the regular `typescript` package (`tsc`). Force the fallback with
// TYPECHECK=tsc. Extra arguments are passed through. `typescript` stays installed either way
// because `next build` and typescript-eslint need it.
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(join(process.cwd(), 'package.json'));
const TSRS_PLATFORMS = new Set(['darwin-arm64', 'linux-x64', 'linux-arm64']);

function bin(pkg, name) {
  const manifest = require.resolve(`${pkg}/package.json`);
  const { bin } = require(manifest);
  return join(dirname(manifest), typeof bin === 'string' ? bin : bin[name]);
}

const args = ['--noEmit', ...process.argv.slice(2)];
const wantTsrs = process.env.TYPECHECK !== 'tsc' && TSRS_PLATFORMS.has(`${process.platform}-${process.arch}`);
let tool = 'tsc';
let entry;
if (wantTsrs) {
  try {
    entry = bin('tsrs', 'tsrs');
    tool = 'tsrs';
  } catch {
    console.warn('typecheck: tsrs is not installed; falling back to tsc');
  }
} else if (process.env.TYPECHECK !== 'tsc') {
  console.warn(`typecheck: no tsrs build for ${process.platform}-${process.arch}; using tsc`);
}
entry ??= bin('typescript', 'tsc');

const result = spawnSync(process.execPath, [entry, ...args], { stdio: 'inherit' });
if (result.error) throw result.error;
process.exit(result.status ?? 1);
