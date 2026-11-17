// Validate a transitional token when present; otherwise allow GitHub OIDC.
// Never print or persist credentials.
import { readFile } from 'node:fs/promises';

const { name } = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
const token = process.env.NODE_AUTH_TOKEN || process.env.NPM_TOKEN;
if (typeof token !== 'string' || !token) {
  if (process.env.ACTIONS_ID_TOKEN_REQUEST_URL && process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN) {
    console.log('::notice::No npm token provided; publishing will rely on npm trusted publishing.');
    process.exit(0);
  }
  throw new Error(
    'NPM_TOKEN is missing. Add a repository secret named NPM_TOKEN with permission to publish this package.',
  );
}

const whoami = await fetch('https://registry.npmjs.org/-/whoami', {
  headers: { Authorization: `Bearer ${token}` },
  signal: AbortSignal.timeout(30_000),
});
if (!whoami.ok) {
  throw new Error(
    `npm token authentication failed (HTTP ${whoami.status}). Check the NPM_TOKEN repository secret.`,
  );
}
const identity = await whoami.json();
if (typeof identity.username !== 'string' || !identity.username) {
  throw new Error('npm whoami did not return a username.');
}

const escapedName = name.replace('/', '%2f');
const collaborators = await fetch(`https://registry.npmjs.org/-/package/${escapedName}/collaborators`, {
  headers: { Authorization: `Bearer ${token}` },
  signal: AbortSignal.timeout(30_000),
});
if (!collaborators.ok) {
  throw new Error(
    `npm collaborator check failed (HTTP ${collaborators.status}). The NPM_TOKEN secret must be able to publish ${name}.`,
  );
}
const access = await collaborators.json();
const permission = access[identity.username];
if (permission !== 'write' && permission !== 'read-write' && permission !== true) {
  throw new Error(`npm token for ${identity.username} cannot publish ${name}.`);
}
console.log(`npm accepted the repository NPM_TOKEN for ${name} as ${identity.username}.`);
