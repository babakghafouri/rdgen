param(
  [Parameter(Mandatory = $true)]
  [string]$ArtifactDirectory,
  [string]$ExpectedPublisher = ""
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $ArtifactDirectory -PathType Container)) {
  throw "Artifact directory does not exist: $ArtifactDirectory"
}
$files = @(Get-ChildItem -LiteralPath $ArtifactDirectory -File -Recurse |
  Where-Object { $_.Extension -in @('.exe', '.msi') })
if ($files.Count -eq 0) { throw 'No EXE or MSI artifacts found to verify.' }
foreach ($file in $files) {
  $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
  if ($signature.Status -ne 'Valid') {
    throw "Unsigned or invalid Authenticode signature on $($file.Name): $($signature.Status)"
  }
  if ($null -eq $signature.SignerCertificate) {
    throw "No signer certificate for $($file.Name)"
  }
  if ($ExpectedPublisher -and $signature.SignerCertificate.Subject -notlike "*$ExpectedPublisher*") {
    throw "Unexpected signer on $($file.Name): $($signature.SignerCertificate.Subject)"
  }
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  Write-Host "Verified: $($file.Name)"
  Write-Host "Signer: $($signature.SignerCertificate.Subject)"
  Write-Host "SHA256: $hash"
}
Write-Host 'All Windows EXE/MSI signatures are valid. SmartScreen reputation is not guaranteed.'
