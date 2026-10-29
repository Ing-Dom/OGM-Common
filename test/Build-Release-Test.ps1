$settings = scripts/OpenKNX-Build-Settings.ps1 $args[0]
$releaseIndication = $settings["appRelease"]
lib/OGM-Common/scripts/setup/reusable/Build-Release-Preprocess.ps1 $args[0]
if (!$?) { exit 1 }
if (Test-Path -Path scripts/data -PathType Container) {
    Copy-Item scripts/data/* release/data/
    if (!$?) { exit 1 }
}
lib/OGM-Common/scripts/setup/reusable/Build-Step.ps1 release_DEVICE_REG1_BASE firmware-OpenKNX-REG1-BASE rp2040-tp
if (!$?) { exit 1 }
lib/OGM-Common/scripts/setup/reusable/Build-Step.ps1 release_DEVICE_REG1_LAN_TP_BASE firmware-OpenKNX-REG1-LAN-TP-BASE esp32-tpip
if (!$?) { exit 1 }
Remove-Item -Path release/OTA-Upload-Firmware-*.ps1 -ErrorAction SilentlyContinue -Force
lib/OGM-Common/scripts/setup/reusable/Build-Release-Postprocess.ps1 $args[0]
if (!$?) { exit 1 }
