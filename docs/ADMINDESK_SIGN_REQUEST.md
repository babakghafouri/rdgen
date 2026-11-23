# AdminDesk RDGen signing request marker

**This file is not a certificate and does not contain secrets.**

Request number: 0
Self-sign request number: 2

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


To request a **self-signed test-only** build instead, first configure the
\`ADMINDESK_SELF_SIGN_PFX_BASE64\` and \`ADMINDESK_SELF_SIGN_PFX_PASSWORD\`
repository secrets, set the expected subject and thumbprint repository
variables, and set \`ADMINDESK_ENABLE_SELF_SIGNING\` to \`true\`.

Increment only \`Self-sign request number\` above and commit directly to the
experimental branch with the EXACT commit message:

    [self-sign AdminDesk pilot]

This selects the local AdminDesk self-signed certificate path, not the remote
RDGen signing API. The artifact is for isolated testing only and is not trusted
by other computers or a public CA. Set \`ADMINDESK_ENABLE_SELF_SIGNING\` back
to \`false\` after the test.

Never commit the PFX, its password, or its Base64 contents.
