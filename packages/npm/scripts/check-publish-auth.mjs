// Verify the same package-scoped OIDC exchange that npm publish uses, even when
// the current version is already published. Never print or persist either token.
// https://api-docs.npmjs.com/#tag/OIDC
import { readFile } from 'node:fs/promises';

const { name } = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
const requestUrl = process.env.ACTIONS_ID_TOKEN_REQUEST_URL;
const requestToken = process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
if (!requestUrl || !requestToken) {
  throw new Error('GitHub OIDC credentials are missing. The publish job requires id-token: write.');
}

const url = new URL(requestUrl);
url.searchParams.set('audience', 'npm:registry.npmjs.org');
const identity = await fetch(url, {
  headers: { Authorization: `Bearer ${requestToken}` },
  signal: AbortSignal.timeout(30_000),
});
if (!identity.ok) {
  throw new Error(`GitHub OIDC token request failed (HTTP ${identity.status}).`);
}
const { value: idToken } = await identity.json();
if (typeof idToken !== 'string' || !idToken) {
  throw new Error('GitHub OIDC response did not contain an identity token.');
}

const exchange = await fetch(`https://registry.npmjs.org/-/npm/v1/oidc/token/exchange/package/${encodeURIComponent(name)}`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${idToken}` },
  signal: AbortSignal.timeout(30_000),
});
if (!exchange.ok) {
  throw new Error(`npm OIDC exchange failed (HTTP ${exchange.status}). Check the trusted publisher for ${name}: repository bloxwap/font, workflow publish_npm.yml, no environment, and permission to publish.`);
}
const result = await exchange.json();
if (typeof result.token !== 'string' || !result.token) {
  throw new Error('npm OIDC exchange did not return a publish token.');
}
console.log(`npm accepted this workflow's OIDC identity for ${name}.`);
