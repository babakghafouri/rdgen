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

## Automated no-secret full Windows pilot

A dedicated workflow now allows testing the **real RDGen Windows packaging pipeline** without deploying the Django generator and without configuring any GitHub secrets:

- Workflow: `.github/workflows/admindesk-rdgen-full-pilot.yml`
- Trigger: a push to this exact experimental branch changing the pilot workflow/its dependencies, or manual dispatch.
- Core input: RustDesk `1.5.1`; source remains pinned to AdminDesk `4bbb91323272d39cb8c36cac54718848e4becf0a`.
- Synthetic, public JSON configuration is generated locally and encrypted using a fixed **public test-only password**. It contains no private key, account, remote desktop credential or personally identifiable information.
- Signing is OFF by default. An authorized opt-in signing request uses a configured remote Signing API. External generator callbacks and GitHub Release publication are always disabled in the pilot.
- On success it uploads `AdminDeskPilot.exe` and `AdminDeskPilot.msi` as short-lived pilot artifacts; the default is **UNSIGNED**. With authorized signing enabled, both must pass Authenticode verification before upload.
- The workflow fails if either installer file is missing, and logs SHA-256 and Authenticode status without suggesting unsigned files are trusted.
- The normal RDGen web-generated mode is unchanged by these pilot-specific branches.

This pilot is intentionally limited to Windows x64. **No GitHub Release is published.** A successful pipeline run establishes compile/package compatibility only; manual installation, remote-control testing and independently authorized code signing still remain necessary.

## Authorized code-signing with the same API protocol as RDGen

**Not currently signed.** The verified Windows x64 pilot compiles and packages both EXE and MSI, but those artifacts are deliberately unsigned unless an **authorized** signing server is configured.

The pilot can now POST a ZIP of compiled binaries to an RDGen-compatible signing server at `https://<authorized-server>/sign/`, unpack the signed files safely, verify each Authenticode signature on Windows, and only then replace the originals. It signs the inner EXE/DLL files first and the final installer EXE/MSI files second. The workflow fails if the service is missing, rejects a request, returns unexpected filenames, or signs as the wrong publisher. It never silently falls back to unsigned files when signing was requested.

### What must be connected first

The signing service must be operated by the owner of a trusted code-signing certificate, or by a provider who has **expressly agreed** to sign AdminDesk. Forking RDGen **does not** grant access to Bayside Computer Systems Inc's private key, USB token, service or GitHub secrets. Do not attempt to copy or impersonate their certificate.

In `babakghafouri/rdgen` open **Settings → Secrets and variables → Actions** and configure:

| Type | Name | Required value |
| --- | --- | --- |
| Repository secret | `SIGN_BASE_URL` | HTTPS base URL of your **authorized** RDGen-compatible Signing API, without `/sign/` |
| Repository secret | `SIGN_API_KEY` | Issued API authentication key, **not** a Windows/RustDesk server public key |
| Repository variable | `ADMINDESK_SIGN_EXPECTED_PUBLISHER` | Publisher name that should appear in the Authenticode certificate subject, e.g. your legal company name |

Do **not** put any of these secrets in a GitHub issue, commit, pull request or chat. The existing `SIGN_API_KEY` must belong to the authorized signing service; the RustDesk server connection key is unrelated to code signing.

### To request a signed Windows pilot

GitHub's **Run workflow** UI requires the workflow to exist on the repository's default branch. We intentionally keep this experiment off `master`, so use the push-based opt-in below instead:

1. First configure the two signing secrets and publisher variable listed above, using an authorized Signing API.
2. Add repository **variable** `ADMINDESK_ENABLE_PILOT_SIGNING` with value `true` (not a secret).
3. Open `docs/ADMINDESK_SIGN_REQUEST.md` in the branch `experiment/admindesk-152-windows-generator`.
4. Edit its request marker (e.g. increment the request number). Use GitHub's **Commit changes** and set the exact commit message to **`[sign AdminDesk pilot]`**. Commit directly to the experimental branch.
5. This explicitly triggers the existing push workflow with `pilot_sign=true`. The build signs inner EXE/DLL and final EXE/MSI, checks Authenticode and publisher, then uploads `AdminDesk-RDGen-signed-pilot-<run-number>` as a short-lived artifact.
6. Verify **Properties → Digital Signatures** and `Get-AuthenticodeSignature` on Windows, then reset `ADMINDESK_ENABLE_PILOT_SIGNING` to `false` to prevent unintended future signing requests.

The signed path requires BOTH the variable and the exact commit message. Regular pushes and test runs stay unsigned. If the signing secrets or publisher are missing, an explicitly requested signed build fails rather than publishing an unsigned file as signed.

If this workflow is later added to `master` as a separate approved launcher, manual **Run workflow** may be used with `pilot_sign=true` and the experimental branch selected.

If `pilot_sign` is false or omitted, builds stay **unsigned**, with artifact name `AdminDesk-RDGen-unsigned-pilot-<run-number>`. A signed pilot is not a production release. No external generator upload or release publication occurs in either mode.

**Current limitation:** We cannot produce a real certificate signature from the public fork or the screenshots alone. It requires an actual authorized signing API (or another approved signing provider) and its corresponding credentials. The earlier successfully signed original RDGen example used a certificate issued to *Bayside Computer Systems Inc*; it cannot legally or technically be assumed available to AdminDesk.

## Production generator setup (later)

## How to run the full web-generator path later

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
