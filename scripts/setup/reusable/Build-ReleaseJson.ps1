# This script maintains release/data/openknx-release.json, a machine readable
# description of the release next to content.xml. It is called in three steps:
#    Build-ReleaseJson.ps1 Init -AppName <name> -Label <release-indication>
#        from Build-Release-Preprocess.ps1, creates the file
#    Build-ReleaseJson.ps1 AddProduct -PioEnv <pio-environment> -ProductName <product-name> ...
#        from Build-Step.ps1, appends one firmware product
#    Build-ReleaseJson.ps1 Finish -Version <app-version>
#        from Build-Release-Postprocess.ps1, adds appId, version and build time
#
# Problems are only reported as warnings, this script never fails a build.
#
# This file does not require any changes and is project-independent.

param (
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidateSet("Init", "AddProduct", "Finish")]
  [string]$Step,

  # Init
  [string]$AppName,
  [string]$Label,

  # AddProduct
  [string]$PioEnv,
  [string]$ProductName,
  [string]$Processor,
  [string]$FeatureSet,
  [string]$FirmwareDir,
  [string]$FirmwareName,
  [string]$OtaName,
  [switch]$WithIP,
  [switch]$WithTP,

  # Finish
  [string]$Version,

  [string]$ProjectDir
)

$ErrorActionPreference = "Stop"

$releaseJson = "release/data/openknx-release.json"
$buildInfo = ".pio/build/$PioEnv/openknx-build.json"
$knxprodHeader = "include/knxprod.h"
if (![string]::IsNullOrEmpty($ProjectDir)) {
  $releaseJson = Join-Path $ProjectDir $releaseJson
  $buildInfo = Join-Path $ProjectDir $buildInfo
  $knxprodHeader = Join-Path $ProjectDir $knxprodHeader
}

function Read-ReleaseJson {
  return Get-Content -Path $releaseJson -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Write-ReleaseJson($content) {
  # UTF-8 without BOM, independent of the PowerShell version
  $path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($releaseJson)
  $text = ($content | ConvertTo-Json -Depth 5) + "`n"
  [System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))
}

# returns the numeric value of a #define from include/knxprod.h or $null
function Get-KnxprodDefine($name) {
  if (Test-Path -Path $knxprodHeader -PathType Leaf) {
    $line = Select-String -Path $knxprodHeader -Pattern "#define $name " | Select-Object -First 1
    if ($line) { return [int]$line.ToString().Split()[-1] }
  }
  return $null
}

try {
  switch ($Step) {
    "Init" {
      Write-ReleaseJson ([ordered]@{ formatVersion = 1; appName = $AppName; label = $Label; products = @() })
      Write-Host "Created $releaseJson" -ForegroundColor Blue
    }
    "AddProduct" {
      $product = [ordered]@{ name = $ProductName }
      # device identity as resolved by scripts/pio/prepare.py during the firmware build
      if (Test-Path -Path $buildInfo -PathType Leaf) {
        $info = Get-Content -Path $buildInfo -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($info.deviceId) { $product.deviceId = $info.deviceId }
        if ($info.deviceName) { $product.deviceName = $info.deviceName }
      }
      if (!$product.Contains("deviceId")) {
        Write-Host "No DEVICE_ID known for $PioEnv, $ProductName is listed without deviceId/deviceName in $releaseJson"
      }
      $product.processor = $Processor
      $product.featureSet = $FeatureSet
      $upload = @("usb")
      if ($WithIP) { $upload += "ota" }
      if ($WithTP) { $upload += "knx" }
      $product.upload = $upload
      $product.firmware = "$FirmwareDir/$FirmwareName"
      if ($WithIP) { $product.ota = "$FirmwareDir/$OtaName" }
      $release = Read-ReleaseJson
      $release.products = @($release.products) + @($product)
      Write-ReleaseJson $release
    }
    "Finish" {
      $json = Read-ReleaseJson
      $release = [ordered]@{ formatVersion = $json.formatVersion }
      $openKnxId = Get-KnxprodDefine "MAIN_OpenKnxId"
      $appNumber = Get-KnxprodDefine "MAIN_ApplicationNumber"
      if ($null -ne $openKnxId -and $null -ne $appNumber) {
        $release.appId = "0x{0:X4}" -f (($openKnxId -shl 8) -bor $appNumber)
      }
      else {
        Write-Host "MAIN_OpenKnxId/MAIN_ApplicationNumber not found in $knxprodHeader, $releaseJson has no appId"
      }
      $release.appName = $json.appName
      $release.label = $json.label
      $release.version = $Version
      $release.built = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
      $release.products = @($json.products)
      Write-ReleaseJson $release
      Write-Host "Finished $releaseJson" -ForegroundColor Blue
    }
  }
}
catch {
  Write-Host "WARNING: $Step of $releaseJson failed: $_" -ForegroundColor Yellow
}
