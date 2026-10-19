# Font canonical ownership evidence

The baseline is Font `dbf9824f2abdd0a70f929e2393a7780d61121e29`. The new scoped configuration explicitly names Font's 242 docs font binaries: 240 web fonts and two OG TTFs, totaling 83,545,680 bytes. All hashes and all 383 tracked docs files match that baseline. Runtime HIG packages, imports, archives and lockfile remain unchanged.

The actual HIG checker is checked out at `0e2394428a3971e677e0a97ef5259ac4ca1ec064`, independently of the unchanged runtime candidate `7c67a07c`, which predates the scoped CLI. Its source hash, the runtime archive hashes and validation outcomes are in [verification.json](verification.json); exact binary hashes are in [font-manifest.json](font-manifest.json).

The actual checker passes all 383 files with no violations, expired/unused exceptions or schema errors. Mutation checks used a separate temporary Git index so that the real tracked-file scanner saw the probes, while preserving the normal index and original sources:

- Removing the canonical list rejects all 242 binaries with `copied-font-binary`.
- Adding token/palette/control CSS inside `public/fonts/BloxwapSans/` still rejects all three HIG-owned definitions.
- Adding an undeclared font beside an existing family rejects that font.

The probes and temporary index were removed, and the normal checkout passes again. No CSS, component, directory or vendored HIG path is canonical. Existing sources confirm that the two OG TTFs are Font's own distribution assets (`apps/docs/lib/og-card.tsx`); this is not a native-fonts package workaround.

Existing checks pass: Bun 1.4 frozen install, owning vendor guard, lint, full typecheck, seven unit tests, production static export (27 HTML, 24 social cards, 52 @font-face rules), and actionlint. The existing HIG and accessibility specs pass all 24 cases across Chromium/WebKit, including keyboard, mobile navigation/layout, replacement fonts, user text spacing and 200% root text. Logs are included; no mirrored config tests were added.

Local preview used the existing static-export server on 127.0.0.1:43964. No deployment or publication was invoked. Physical rasterization/device certification and owner review are separate acceptance; browser automation is not those approvals. Remote CI status is reported on the draft PR.

Reproduction commands and the tooling/runtime pin distinction are in [docs/hig-ownership.md](../../docs/hig-ownership.md). When Font adds or renames a binary, review its ownership and update the individual canonical entry; other docs files remain checked.
