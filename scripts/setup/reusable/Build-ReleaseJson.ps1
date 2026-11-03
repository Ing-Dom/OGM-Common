# This script maintains release/data/openknx-release.json, a machine readable
# description of the release next to content.xml. It is called in three steps:
#    Build-ReleaseJson.ps1 Init -AppName <name> -Label <release-indication> -EtsXml <src/xml-file>
#        from Build-Release-Preprocess.ps1, creates the file
#    Build-ReleaseJson.ps1 AddProduct -PioEnv <pio-environment> -ProductName <product-name> ...
#        from Build-Step.ps1, appends one firmware product
#    Build-ReleaseJson.ps1 Finish -Version <app-version>
#        from Build-Release-Postprocess.ps1, adds appId, version and build time
#
# A variant is identified by its AppId, its label is "release" or "dev". Beta is not a variant
# but the state of a version, marked by ApplicationName ending with "-Beta" in op:ETS.
#
# If the project contains openknx-app.json, appName and label are taken from the variant
# with the AppId of include/knxprod.h, i.e.
#    "title": "RaumController",
#    "variants": { "0xA012": { "label": "release" }, "0xA011": { "label": "dev", "name": "..." } }
# (name defaults to title). Deviations from op:ETS in the ETS xml (ProductName, BuildSuffix)
# are reported. Without openknx-app.json, appName is -AppName and label is derived from
# BuildSuffix (none = release), or -Label if op:ETS is not available.
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
  [string]$EtsXml,

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
$appJson = "openknx-app.json"
if (![string]::IsNullOrEmpty($ProjectDir)) {
  $releaseJson = Join-Path $ProjectDir $releaseJson
  $buildInfo = Join-Path $ProjectDir $buildInfo
  $knxprodHeader = Join-Path $ProjectDir $knxprodHeader
  $appJson = Join-Path $ProjectDir $appJson
  if (![string]::IsNullOrEmpty($EtsXml)) { $EtsXml = Join-Path $ProjectDir $EtsXml }
}

function Write-Warn($text) {
  Write-Host "WARNING: $text" -ForegroundColor Yellow
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

# returns the AppId (OpenKnxId << 8 | ApplicationNumber) from include/knxprod.h or $null
function Get-AppId {
  $openKnxId = Get-KnxprodDefine "MAIN_OpenKnxId"
  $appNumber = Get-KnxprodDefine "MAIN_ApplicationNumber"
  if ($null -eq $openKnxId -or $null -eq $appNumber) { return $null }
  return ($openKnxId -shl 8) -bor $appNumber
}

# returns the attributes of op:ETS from the ETS xml as hashtable or $null
function Get-EtsAttributes {
  if ([string]::IsNullOrEmpty($EtsXml) -or !(Test-Path -Path $EtsXml -PathType Leaf)) { return $null }
  $xml = New-Object System.Xml.XmlDocument
  $xml.Load($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($EtsXml))
  $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
  $ns.AddNamespace("op", "http://github.com/OpenKNX/OpenKNXproducer")
  $node = $xml.SelectSingleNode("//op:ETS", $ns)
  if ($null -eq $node) { return $null }
  $result = @{}
  foreach ($attribute in $node.Attributes) { $result[$attribute.Name] = $attribute.Value }
  return $result
}

# returns the label derived from BuildSuffix of op:ETS (none = release) or $null
function Get-SuffixLabel($ets) {
  if ($null -eq $ets) { return $null }
  $suffix = $ets["BuildSuffix"]
  if ($null -eq $suffix) { $suffix = "" }
  if ($suffix.Contains("%")) { return $null }
  $suffixLabel = $suffix.TrimStart("-").ToLowerInvariant()
  if ($suffixLabel -eq "") { $suffixLabel = "release" }
  return $suffixLabel
}

# returns $true if ApplicationName of op:ETS (default ProductName) ends with "-Beta", $null if unknown
function Get-BetaState($ets) {
  if ($null -eq $ets) { return $null }
  $applicationName = $ets["ApplicationName"]
  if ($null -eq $applicationName) { $applicationName = $ets["ProductName"] }
  if ($null -eq $applicationName -or $applicationName.Contains("%")) { return $null }
  return $applicationName.EndsWith("-Beta", [System.StringComparison]::OrdinalIgnoreCase)
}

# returns @{ appName; label } from the variant in openknx-app.json matching the AppId of
# include/knxprod.h, reports deviations from op:ETS; $null if no variant applies
function Get-AppVariant($ets) {
  $app = Get-Content -Path $appJson -Raw -Encoding UTF8 | ConvertFrom-Json
  $appId = Get-AppId
  if ($null -eq $appId) {
    Write-Warn "$appJson not applied, MAIN_OpenKnxId/MAIN_ApplicationNumber not found in $knxprodHeader"
    return $null
  }
  $appIdText = "0x{0:X4}" -f $appId
  $variant = $null
  if ($app.variants) {
    foreach ($property in $app.variants.PSObject.Properties) {
      if ([Convert]::ToInt32($property.Name, 16) -eq $appId) { $variant = $property.Value }
    }
  }
  if ($null -eq $variant) {
    Write-Warn "AppId $appIdText from $knxprodHeader is missing in variants of $appJson"
    return $null
  }
  $result = @{ appName = $variant.name; label = $variant.label }
  if ([string]::IsNullOrEmpty($result.appName)) { $result.appName = $app.title }
  if ([string]::IsNullOrEmpty($result.appName)) { Write-Warn "$appJson has neither name for variant $appIdText nor title" }
  if ([string]::IsNullOrEmpty($result.label)) { Write-Warn "$appJson has no label for variant $appIdText" }
  elseif ($result.label -eq "beta") {
    Write-Warn "label 'beta' of variant $appIdText in ${appJson}: beta is not a variant, mark the version by ApplicationName ending with '-Beta' in op:ETS"
  }

  if ($null -eq $ets) {
    Write-Warn "op:ETS not found in '$EtsXml', ProductName and BuildSuffix not checked against $appJson"
    return $result
  }
  # ETS shows ProductName with BuildSuffixText, the label corresponds to BuildSuffix (none = release)
  $productName = $ets["ProductName"]
  if ($productName -and !$productName.Contains("%") -and $result.appName -and $productName -cne $result.appName) {
    Write-Warn "ProductName '$productName' in $EtsXml differs from name '$($result.appName)' of variant $appIdText in $appJson"
  }
  $suffixLabel = Get-SuffixLabel $ets
  if ($suffixLabel -eq "beta") {
    Write-Warn "BuildSuffix '$($ets["BuildSuffix"])' in ${EtsXml}: beta is not a variant, mark the version by ApplicationName ending with '-Beta' in op:ETS"
  }
  elseif ($suffixLabel -and $result.label -and $result.label -ne "beta" -and $suffixLabel -ne $result.label.ToLowerInvariant()) {
    Write-Warn "BuildSuffix '$($ets["BuildSuffix"])' in $EtsXml does not match label '$($result.label)' of variant $appIdText in $appJson"
  }
  return $result
}

try {
  switch ($Step) {
    "Init" {
      $ets = $null
      try { $ets = Get-EtsAttributes }
      catch { Write-Warn "op:ETS in '$EtsXml' could not be read: $_" }
      $suffixLabel = Get-SuffixLabel $ets
      if ($suffixLabel) { $Label = $suffixLabel }
      if (Test-Path -Path $appJson -PathType Leaf) {
        try {
          $variant = Get-AppVariant $ets
          if ($variant) {
            if ($variant.appName) { $AppName = $variant.appName }
            if ($variant.label) { $Label = $variant.label }
          }
        }
        catch {
          Write-Warn "$appJson could not be evaluated: $_"
        }
      }
      $release = [ordered]@{ formatVersion = 1; appName = $AppName; label = $Label }
      $beta = Get-BetaState $ets
      if ($null -ne $beta) { $release.beta = $beta }
      $release.products = @()
      Write-ReleaseJson $release
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
      $appId = Get-AppId
      if ($null -ne $appId) {
        $release.appId = "0x{0:X4}" -f $appId
      }
      else {
        Write-Host "MAIN_OpenKnxId/MAIN_ApplicationNumber not found in $knxprodHeader, $releaseJson has no appId"
      }
      $release.appName = $json.appName
      $release.label = $json.label
      if ($null -ne $json.beta) { $release.beta = $json.beta }
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
