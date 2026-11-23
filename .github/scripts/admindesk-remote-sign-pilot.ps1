# Authenticode signing via an RDGen-compatible API.
# Certificate owner must explicitly authorize signing AdminDesk.
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('InnerBinaries','Installers')]
  [string]$Stage,
  [Parameter(Mandatory = $true)]
  [string]$Path
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($env:PILOT_SIGN_BASE_URL) -or
    [string]::IsNullOrWhiteSpace($env:PILOT_SIGN_API_KEY) -or
    [string]::IsNullOrWhiteSpace($env:PILOT_SIGN_EXPECTED_PUBLISHER)) {
  throw 'SIGN_BASE_URL, SIGN_API_KEY, and ADMINDESK_SIGN_EXPECTED_PUBLISHER are required.'
}
$baseUrl = $env:PILOT_SIGN_BASE_URL.Trim().TrimEnd('/')
if (-not $baseUrl.StartsWith('https://', [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Signing API must use HTTPS.'
}
if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
  throw "Input directory does not exist: $Path"
}
$extensions = if ($Stage -eq 'InnerBinaries') { @('.exe','.dll') } else { @('.exe','.msi') }
$files = @(Get-ChildItem -LiteralPath $Path -File | Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() })
if ($files.Count -lt 1) { throw "No signable files at $Path" }
if ($Stage -eq 'Installers') {
  if (@($files | Where-Object { $_.Extension -eq '.exe' }).Count -lt 1) { throw 'Missing EXE installer.' }
  if (@($files | Where-Object { $_.Extension -eq '.msi' }).Count -lt 1) { throw 'Missing MSI installer.' }
}
$work = Join-Path $env:RUNNER_TEMP ("admindesk-sign-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work -Force | Out-Null
try {
  $unsigned = Join-Path $work 'unsigned.zip'
  $signed = Join-Path $work 'signed.zip'
  Compress-Archive -LiteralPath @($files | ForEach-Object { $_.FullName }) -DestinationPath $unsigned -CompressionLevel Fastest
  # Key stays in the GitHub Actions secret env, never in command arguments in the YAML.
  $curlArgs = @('--fail','--silent','--show-error','--retry','2','--connect-timeout','30','--max-time','900','-X','POST','-F',"file=@$unsigned",'-H',"X-API-KEY: $env:PILOT_SIGN_API_KEY","$baseUrl/sign/",'-o',"$signed")
  & curl.exe @curlArgs
  if ($LASTEXITCODE -ne 0) { throw "Signing API failed (curl exit code $LASTEXITCODE)." }
  if (-not (Test-Path -LiteralPath $signed -PathType Leaf)) { throw 'No signed ZIP returned.' }
  Add-Type -AssemblyName System.IO.Compression
  $archive = [System.IO.Compression.ZipFile]::OpenRead($signed)
  try {
    $expected = @($files | ForEach-Object { $_.Name })
    $names = @($archive.Entries | ForEach-Object { $_.FullName })
    if ($names.Count -ne $expected.Count) { throw 'Signing response file count mismatch.' }
    foreach ($entry in $archive.Entries) {
      if ($entry.FullName -ne [System.IO.Path]::GetFileName($entry.FullName) -or $expected -cnotcontains $entry.FullName) {
        throw 'Signing response contains an unexpected path or filename.'
      }
    }
    if (@($names | Select-Object -Unique).Count -ne $expected.Count) { throw 'Duplicate filenames in signing response.' }
  }
  finally { $archive.Dispose() }

  $extract = Join-Path $work 'verified'
  New-Item -ItemType Directory -Path $extract -Force | Out-Null
  Expand-Archive -LiteralPath $signed -DestinationPath $extract -Force
  $publisher = $env:PILOT_SIGN_EXPECTED_PUBLISHER.Trim()
  foreach ($original in $files) {
    $candidate = Join-Path $extract $original.Name
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Signed response missing $($original.Name)" }
    $sig = Get-AuthenticodeSignature -LiteralPath $candidate
    if ($sig.Status -ne 'Valid' -or $null -eq $sig.SignerCertificate) {
      throw "Invalid Authenticode signature on $($original.Name): $($sig.Status)"
    }
    if (-not $sig.SignerCertificate.Subject.Contains($publisher)) {
      throw "Unexpected publisher on $($original.Name): $($sig.SignerCertificate.Subject)"
    }
    Write-Host "Verified $($original.Name): $($sig.SignerCertificate.Subject)"
  }
  # Fail-closed: replace unsigned files only after verifying all returned files.
  foreach ($original in $files) {
    Copy-Item -LiteralPath (Join-Path $extract $original.Name) -Destination $original.FullName -Force
  }
  Write-Host "Signing and verification succeeded for $($files.Count) $Stage files."
}
finally { Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue }
