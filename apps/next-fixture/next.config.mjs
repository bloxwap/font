// `bun run build` type-checks with tsrs first (../../scripts/typecheck.mjs), so Next skips its own pass.
export default { output: 'export', typescript: { ignoreBuildErrors: true }, turbopack: { root: new URL('../..',import.meta.url).pathname } };
