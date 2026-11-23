# Local Authenticode signing for the isolated AdminDesk RDGen pilot.
# This uses an AdminDesk-owned self-signed test certificate, never RDGen's certificate.
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('Preflight','InnerBinaries','Installers')]
  [string]$Stage,
  [string]$Path
)

$ErrorActionPreference = 'Stop'
$timestampUrl = 'http://timestamp.digicert.com'
$thumbprint = ($env:PILOT_SELF_SIGN_EXPECTED_THUMBPRINT -replace '\s','').ToUpperInvariant()
$expectedSubject = $env:PILOT_SELF_SIGN_EXPECTED_SUBJECT

if ($thumbprint -notmatch '^[A-F0-9]{40}$') {
  throw 'PILOT_SELF_SIGN_EXPECTED_THUMBPRINT must be a 40-character SHA-1 thumbprint.'
}
if ([string]::IsNullOrWhiteSpace($expectedSubject)) {
  throw 'PILOT_SELF_SIGN_EXPECTED_SUBJECT is required.'
}

$certPath = "Cert:\CurrentUser\My\$thumbprint"
$rootPath = "Cert:\CurrentUser\Root\$thumbprint"
$publisherPath = "Cert:\CurrentUser\TrustedPublisher\$thumbprint"

if ($Stage -eq 'Preflight') {
  if ([string]::IsNullOrWhiteSpace($env:ADMINDESK_SELF_SIGN_PFX_BASE64) -or
      [string]::IsNullOrWhiteSpace($env:ADMINDESK_SELF_SIGN_PFX_PASSWORD)) {
    throw 'Missing ADMINDESK_SELF_SIGN_PFX_BASE64 or ADMINDESK_SELF_SIGN_PFX_PASSWORD secret.'
  }

  $tempPfx = Join-Path $env:RUNNER_TEMP ("admindesk-self-sign-" + [guid]::NewGuid().ToString('N') + '.pfx')
  $tempCer = Join-Path $env:RUNNER_TEMP ("admindesk-self-sign-" + [guid]::NewGuid().ToString('N') + '.cer')
  try {
    $bytes = [Convert]::FromBase64String($env:ADMINDESK_SELF_SIGN_PFX_BASE64)
    [IO.File]::WriteAllBytes($tempPfx, $bytes)
    $securePassword = ConvertTo-SecureString -String $env:ADMINDESK_SELF_SIGN_PFX_PASSWORD -AsPlainText -Force

    $existing = Get-ChildItem -Path 'Cert:\CurrentUser\My' |
      Where-Object { $_.Thumbprint -eq $thumbprint } |
      Select-Object -First 1
    if ($null -eq $existing -or -not $existing.HasPrivateKey) {
      Import-PfxCertificate -FilePath $tempPfx -CertStoreLocation 'Cert:\CurrentUser\My' -Password $securePassword -Exportable | Out-Null
    }

    if (-not (Test-Path -LiteralPath $certPath)) {
      throw 'The PFX does not contain the expected certificate thumbprint.'
    }
    $cert = Get-Item -LiteralPath $certPath
    if (-not $cert.HasPrivateKey) {
      throw 'The imported certificate does not have its private key.'
    }
    if ($cert.Subject -ne $expectedSubject) {
      throw "Certificate subject mismatch. Expected '$expectedSubject', received '$($cert.Subject)'."
    }
    if ($cert.NotAfter -le (Get-Date)) {
      throw 'The self-signing certificate has expired.'
    }

    $ekuExtension = $cert.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.37' } | Select-Object -First 1
    $ekuOids = @()
    if ($null -ne $ekuExtension) {
      $ekuOids = @($ekuExtension.EnhancedKeyUsages | ForEach-Object { $_.Value })
    }
    if ($ekuOids -notcontains '1.3.6.1.5.5.7.3.3') {
      throw 'The certificate is not valid for Code Signing (missing Code Signing EKU).'
    }

    Export-Certificate -Cert $cert -FilePath $tempCer -Force | Out-Null
    if (-not (Test-Path -LiteralPath $rootPath)) {
      Import-Certificate -FilePath $tempCer -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    }
    if (-not (Test-Path -LiteralPath $publisherPath)) {
      Import-Certificate -FilePath $tempCer -CertStoreLocation 'Cert:\CurrentUser\TrustedPublisher' | Out-Null
    }

    Write-Host "Self-signing certificate preflight passed: $($cert.Subject)"
    Write-Host "Certificate thumbprint: $($cert.Thumbprint)"
    Write-Host 'The certificate is trusted only in this temporary Actions runner.'
  }
  finally {
    Remove-Item -LiteralPath $tempPfx -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempCer -Force -ErrorAction SilentlyContinue
    Remove-Variable securePassword -ErrorAction SilentlyContinue
    $env:ADMINDESK_SELF_SIGN_PFX_BASE64 = $null
    $env:ADMINDESK_SELF_SIGN_PFX_PASSWORD = $null
  }
  exit 0
}

if (-not (Test-Path -LiteralPath $certPath)) {
  throw 'Self-signing certificate is not installed. The preflight step must run first.'
}
$cert = Get-Item -LiteralPath $certPath
if (-not $cert.HasPrivateKey) {
  throw 'The self-signing certificate private key is unavailable.'
}
if ($cert.Subject -ne $expectedSubject) {
  throw 'The installed self-signing certificate subject does not match the configured subject.'
}
if (-not (Test-Path -LiteralPath $rootPath) -or -not (Test-Path -LiteralPath $publisherPath)) {
  throw 'The self-signed certificate is not trusted in this temporary runner.'
}
if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Container)) {
  throw "Signing input directory does not exist: $Path"
}

$extensions = if ($Stage -eq 'InnerBinaries') { @('.exe','.dll') } else { @('.exe','.msi') }
$files = @(Get-ChildItem -LiteralPath $Path -File | Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() })
if ($files.Count -lt 1) { throw "No signable files found in $Path" }
if ($Stage -eq 'Installers') {
  if (@($files | Where-Object { $_.Extension -eq '.exe' }).Count -lt 1) { throw 'Missing EXE installer.' }
  if (@($files | Where-Object { $_.Extension -eq '.msi' }).Count -lt 1) { throw 'Missing MSI installer.' }
}

$signTool = $null
$command = Get-Command 'signtool.exe' -ErrorAction SilentlyContinue
if ($null -ne $command) {
  $signTool = $command.Source
}
else {
  $sdkRoot = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Windows Kits\10\bin'
  if (Test-Path -LiteralPath $sdkRoot) {
    $candidate = Get-ChildItem -LiteralPath $sdkRoot -Filter 'signtool.exe' -File -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
      Sort-Object -Property FullName -Descending |
      Select-Object -First 1
    if ($null -ne $candidate) { $signTool = $candidate.FullName }
  }
}
if ([string]::IsNullOrWhiteSpace($signTool)) {
  throw 'signtool.exe was not found on the Windows runner.'
}

foreach ($file in $files) {
  Write-Host "Signing $($file.Name)"
  & $signTool sign /sha1 $thumbprint /s My /fd SHA256 /tr $timestampUrl /td SHA256 /v $file.FullName
  if ($LASTEXITCODE -ne 0) {
    throw "signtool sign failed for $($file.Name) with exit code $LASTEXITCODE."
  }

  & $signTool verify /pa /all /v $file.FullName
  if ($LASTEXITCODE -ne 0) {
    throw "signtool verify failed for $($file.Name) with exit code $LASTEXITCODE."
  }

  $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
  if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate) {
    throw "Invalid Authenticode signature for $($file.Name): $($signature.Status)"
  }
  if ($signature.SignerCertificate.Thumbprint.ToUpperInvariant() -ne $thumbprint) {
    throw "Unexpected signing thumbprint on $($file.Name)."
  }
  if ($signature.SignerCertificate.Subject -ne $expectedSubject) {
    throw "Unexpected signing subject on $($file.Name)."
  }
  if ($null -eq $signature.TimeStamperCertificate) {
    throw "The signature for $($file.Name) has no trusted timestamp."
  }
  Write-Host "Verified $($file.Name): $($signature.SignerCertificate.Subject)"
}

Write-Host "Self-signing and timestamp verification succeeded for $($files.Count) $Stage files."
