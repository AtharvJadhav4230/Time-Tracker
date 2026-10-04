param(
    [string]$ProjectDirectory = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = "Stop"
$ProjectDirectory = (Resolve-Path -LiteralPath $ProjectDirectory).Path
$builder = Join-Path $ProjectDirectory "build_release.ps1"
$python = Join-Path $ProjectDirectory ".venv\Scripts\python.exe"
$originalLocation = (Get-Location).Path
$taskTemporaryRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$outside = Join-Path $taskTemporaryRoot ("release caller with spaces " + [guid]::NewGuid())
New-Item -ItemType Directory -Path $outside | Out-Null

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}
function Check-Artifacts {
    param([string]$Version, [string]$Label)
    $release = Join-Path $ProjectDirectory "release"
    $installer = Join-Path $release "LocalTimeTracker-Setup-$Version-x64.exe"
    $archive = Join-Path $release "LocalTimeTracker-$Version-portable-x64.zip"
    foreach ($artifact in @($installer, $archive)) {
        Assert-True (Test-Path -LiteralPath $artifact) "Missing artifact: $artifact"
        Assert-True ((Get-Item -LiteralPath $artifact).Length -gt 10000) "Empty artifact: $artifact"
    }
    $lines = @(Get-Content -LiteralPath (Join-Path $release "SHA256SUMS.txt"))
    Assert-True ($lines.Count -eq 2) "Expected installer and portable checksum entries."
    foreach ($artifact in @($installer, $archive)) {
        $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
        $expected = "$hash *$([System.IO.Path]::GetFileName($artifact))"
        Assert-True ($lines -contains $expected) "Checksum mismatch: $artifact"
    }
    $extracted = Join-Path $outside ("extracted " + $Label)
    Expand-Archive -LiteralPath $archive -DestinationPath $extracted
    foreach ($name in @("LocalTimeTracker.exe", "portable.mode", "PORTABLE_NOTICE.txt",
                         "config.example.json", "LICENSE", "PRIVACY.md", "CHANGELOG.md", "LEGAL.md")) {
        Assert-True (Test-Path -LiteralPath (Join-Path $extracted $name)) "Portable file missing: $name"
    }
    $notice = Get-Content -LiteralPath (Join-Path $extracted "PORTABLE_NOTICE.txt") -Raw
    Assert-True (-not $notice.Contains("{{VERSION}}")) "Unexpanded portable version."
    Assert-True ($notice.Contains($Version)) "Portable notice version mismatch."
    $packagedExe = Join-Path $extracted "LocalTimeTracker.exe"
    $builtExe = Join-Path $ProjectDirectory "dist\LocalTimeTracker\LocalTimeTracker.exe"
    Assert-True ((Get-FileHash $packagedExe).Hash -eq (Get-FileHash $builtExe).Hash) "Portable executable differs from the final built/signed executable."
    $metadata = (Get-Item -LiteralPath $packagedExe).VersionInfo
    Assert-True ($metadata.FileVersion -eq $Version) "Executable FileVersion mismatch: $($metadata.FileVersion)"
    Assert-True ($metadata.ProductVersion -eq $Version) "Executable ProductVersion mismatch."
    foreach ($name in @("data", "reports", "config.json", "preferences.json")) {
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $extracted $name))) "Portable package unexpectedly contains user data: $name"
    }
    Write-Host "PASS [$Label]: installer, portable contents, version metadata, final executable and both checksums."
}
try {
    Set-Location -LiteralPath $ProjectDirectory
    $version = & $python -c "import timetracker; print(timetracker.__version__)"
    if ($LASTEXITCODE -ne 0) { throw "Unable to read source version." }
    $version = ([string]$version).Trim()
    foreach ($location in @($ProjectDirectory, $outside)) {
        Set-Location -LiteralPath $location
        $rejected = $false
        try { & $builder -Version "0.0.0" }
        catch {
            if ($_.Exception.Message -notmatch "does not match") { throw }
            $rejected = $true
        }
        Assert-True $rejected "Mismatched release version was not rejected."
        Assert-True ((Get-Location).Path -eq $location) "Failed preflight did not restore caller directory."
    }
    Write-Host "PASS: mismatch preflight from checkout and an outside directory with spaces."
    foreach ($entry in @(
        @{ Directory = $ProjectDirectory; Label = "checkout" },
        @{ Directory = $outside; Label = "outside" }
    )) {
        Set-Location -LiteralPath $entry.Directory
        & $builder -Version $version
        Assert-True ((Get-Location).Path -eq $entry.Directory) "Successful build did not restore caller directory."
        Check-Artifacts -Version $version -Label $entry.Label
    }
}
finally {
    Set-Location -LiteralPath $originalLocation
    if (Test-Path -LiteralPath $outside) {
        Remove-Item -LiteralPath $outside -Recurse -Force
    }
}
