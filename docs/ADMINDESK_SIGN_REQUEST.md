# AdminDesk RDGen signing request marker

**This file is not a certificate and does not contain secrets.**

Request number: 0

To request a signed test build, first have an *authorized* Signing API configured
in GitHub repository secrets (SIGN_BASE_URL and SIGN_API_KEY), set repository
variable ADMINDESK_SIGN_EXPECTED_PUBLISHER to the expected legal publisher,
and set repository variable ADMINDESK_ENABLE_PILOT_SIGNING to true.

Then, on the branch experiment/admindesk-152-windows-generator, edit
`Request number` above and commit with the EXACT commit message:

    [sign AdminDesk pilot]

Both the exact message and enabled variable are required to activate the
signing path. All other pushes remain unsigned. No production releases
are published; artifacts are short-lived.

Do not commit credentials, certificates, or API tokens.
