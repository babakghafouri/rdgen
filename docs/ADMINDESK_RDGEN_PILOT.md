# AdminDesk 1.5.2 / RDGen Windows pilot

**EXPERIMENT ONLY. Do not merge into the RDGen master branch or replace any production AdminDesk release until the full Windows output has been reviewed.**

## Purpose

Test the RDGen Windows client generator against the actual AdminDesk 1.5.2 codebase (Persian RTL UI, dashboard, notifications, ads, RustDesk core), without rewriting the production AdminDesk repository.

## Pinned inputs

- RDGen experimental branch: `experiment/admindesk-152-windows-generator`
- Source: `babakghafouri/Admindesk`
- Exact source commit: `4bbb91323272d39cb8c36cac54718848e4becf0a`
- AdminDesk product version: `1.5.2+69`
- RustDesk core input: `1.5.1` ONLY
- Windows x64 workflow: `.github/workflows/generator-windows.yml`

**Important:** AdminDesk PR #33 (remove the advertising category picker) was still open when this snapshot was pinned; it is **not** part of this pilot source commit. Update only after separate verification, to avoid silent feature drift.

## Changes made

The generator Windows workflow now checks out the pinned AdminDesk source commit instead of fetching stock `rustdesk/rustdesk` at the selected tag. The original RDGen patches, build dependencies, packaging and signing steps are left intact for compatibility testing. A source-contract smoke test checks that the intended source and AdminDesk UI files exist.

**This does not mean the RDGen patches will succeed with AdminDesk.** Some patches are designed for unmodified upstream RustDesk source and may overwrite custom paths, generate inaccurate branding, or silently skip failures due to `continue-on-error`. A passing source-contract test does NOT mean the Windows EXE/MSI compiles.

## How to run the pilot

1. Review the experiment PR and source smoke test.
2. Configure a **separate** instance of the RDGen Django service to reference this repo/experimental branch; do not change `rdgen.crayoneater.org` or the production AdminDesk distribution.
3. Keep any custom server key or other secrets out of the repository and GitHub logs. The RDGen server requires `GHUSER`, `REPONAME`, `GHBRANCH`, `GHBEARER`, `GENURL`, and `ZIP_PASSWORD` plus matching GitHub Actions secrets; follow RDGen `setup.md`. Treat the shared encryption ZIP URL and uploaded private key material as sensitive.
4. In the generator select Windows x64, **RustDesk 1.5.1**, name `AdminDesk`, and the intended logo/server settings. Use a disposable test configuration; do not distribute output until verified.
5. Trigger the generator on this experimental branch. Inspect *every* compilation/patch/signing step and artifacts; if any stage fails or warning occurs, fix the pilot branch only.
6. Verify the full RTL layout, advertising carousel, notifications, custom server/key, login/connection flow, installer/uninstaller identity, and app version on a disposable Windows VM.
7. Verify all EXE, DLL and MSI Authenticode signatures independently with `Get-AuthenticodeSignature` or Windows SDK `signtool verify /pa /v`, including publisher and timestamp.

## Signing warning

The original RDGen Windows workflow uses `SIGN_BASE_URL` and `SIGN_API_KEY` secrets for a remote signing service. These secrets and the third-party publisher's certificate do **not** automatically transfer to a fork. **No key/certificate from Bayside Computer Systems Inc or any third party is granted by this fork.** The upstream workflow contains fallback-to-unsigned behavior and `continue-on-error: true` around signing; successful GitHub Actions status is NOT proof of a signed installer.

The independent SignPath Foundation application remains the primary requested path for an authorized, trusted AdminDesk publisher signature. No fake or self-signed publisher identity should be presented as trusted.

## Safety and rollback

- This experiment only modifies the RDGen fork, on an unmerged branch.
- No changes to AdminDesk `master`, its build workflow, its releases or its GitHub secrets.
- To revert the test, close the experiment PR and delete the experimental branch.
- Do not merge or publish a generated binary as the official AdminDesk build without separate release authorization.
