# Statische Analyse: Vollständigkeit von `openknx-release.json` je OAM

Stand: 2026-10-28 13:04 UTC. Analysiert mit `analyse.py` (OGM-Common Branch `release-json`, Build-ReleaseJson.ps1 / prepare.py).

Die Analyse bildet statisch nach, was ein Release-Build tun würde: Build-Step-Aufrufe aus `scripts/Build-Release.ps1`, Build-Flags des jeweiligen `[env:...]` (aufgelöst mit `pio project config`), Präprozessorlauf des Host-g++ über `#include <hardware.h>` mit diesen Defines (OGM-HardwareConfig am in `dependencies.txt` gepinnten Commit), Auswertung von `DEVICE_ID`/`DEVICE_NAME`, sowie `compileWith` für die appId.

## Übersicht

- OAM-Repos laut Regel: 45 (analysiert: 45, nicht analysiert: 0, archiviert: 0)
- Release-Produkte (Build-Step-Aufrufe) gesamt: 210, davon `ok` (vollständig und Gerät aus OGM-HardwareConfig): 110, JSON vollständig, aber Gerät nicht aus dem Register: 25, unvollständig: 75
- OAMs ohne OGM-HardwareConfig in dependencies.txt (Analyse mit v1-Spitze): 19 (GW-REG1-Dali, OAM-BinaryClock, OAM-BinaryInput, OAM-BusPowerSupply, OAM-Dummy, OAM-ElectricDoorDrive, OAM-EnoceanGateway, OAM-EnoceanGateway_V2, OAM-FanControl, OAM-GuideLight, OAM-HeatingActuator, OAM-LeakageSensor, OAM-LedDimmer-AB, OAM-OneWireModule, OAM-PresenceModule, OAM-SensorModule, OAM-SwitchActuator, OAM-TouchRound, OAM-VirtualButton)
- OAMs mit `../OGM-Common/...`-Aufrufen in Build-Release.ps1: 31
- Gründe (Mehrfachnennung je Produkt möglich):
  - `device-id-not-string-literal`: 36
  - `no-device-define`: 27
  - `device-in-oam-header`: 21
  - `env-missing`: 6
  - `device-in-legacy-common-header`: 6
  - `no-device-name`: 6
  - `device-in-build-flags`: 3
  - `hwconfig-pin-unresolved`: 1

| OAM | Build-Skripte | compileWith | HWConfig-Pin | Produkte | ok | JSON vollst. | fehlend | Hauptgrund |
|---|---|---|---|---:|---:|---:|---:|---|
| BEM-GardenControl | reusable | openknxproducer | 2af139a ✓ | 1 | 1 | 1 | 0 | - |
| GW-REG1-Dali | missing-build-release | – | – (tip) | 0 | 0 | 0 | 0 | kein Build-Release.ps1 |
| OAM-AccessControl | reusable-sibling-path | openknxproducer | a9e034d ✓ | 2 | 1 | 1 | 1 | no-device-define |
| OAM-Aircondition | reusable-sibling-path | openknxproducer | a9e034d ✓ | 6 | 4 | 6 | 0 | device-in-build-flags |
| OAM-BinaryClock | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 0 | 1 | no-device-define |
| OAM-BinaryInput | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 1 | 0 | device-in-oam-header |
| OAM-BusPowerSupply | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 1 | 0 | device-in-oam-header |
| OAM-ClimateControl | reusable | openknxproducer | a9e034d ✓ | 5 | 4 | 4 | 1 | no-device-define |
| OAM-Dummy | template-no-build-step | openknxproducer | – (tip) | 0 | 0 | 0 | 0 | Build-Release.ps1 ohne Build-Step (Template) |
| OAM-ElectricDoorDrive | reusable-sibling-path | openknxproducer | – (tip) | 4 | 0 | 0 | 4 | env-missing |
| OAM-EnoceanGateway | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 0 | 1 | no-device-define |
| OAM-EnoceanGateway_V2 | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 0 | 1 | no-device-define |
| OAM-FanControl | missing-build-release | – | – (tip) | 0 | 0 | 0 | 0 | kein Build-Release.ps1 |
| OAM-GuideLight | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 1 | 0 | device-in-oam-header |
| OAM-HeatingActuator | reusable-sibling-path | openknxproducer | – (tip) | 2 | 0 | 2 | 0 | device-in-oam-header |
| OAM-Homematic | reusable-sibling-path | openknxproducer | 2af139a ✓ | 2 | 2 | 2 | 0 | - |
| OAM-IOHomeControl | reusable | openknxproducer | 51dc43e ✓ | 4 | 2 | 2 | 2 | device-id-not-string-literal |
| OAM-IP-Router | reusable-sibling-path | openknxproducer | 7dad5ab ✓ | 2 | 2 | 2 | 0 | - |
| OAM-InfraredGateway | reusable-sibling-path | openknxproducer | c3ef707 ✓ | 1 | 1 | 1 | 0 | - |
| OAM-InternetServices | reusable-sibling-path | openknxproducer | a9e034d ✓ | 3 | 3 | 3 | 0 | - |
| OAM-LeakageSensor | reusable-sibling-path | openknxproducer | – (tip) | 1 | 0 | 1 | 0 | device-in-oam-header |
| OAM-LedDimmer-AB | reusable-sibling-path | openknxproducer | – (tip) | 7 | 0 | 7 | 0 | device-in-oam-header |
| OAM-LogicModule | reusable | openknxproducer | ac57a3a ✓ | 18 | 16 | 17 | 1 | device-id-not-string-literal |
| OAM-Meter | reusable-sibling-path | openknxproducer | 15b4c95 ✓ | 12 | 11 | 11 | 1 | device-id-not-string-literal |
| OAM-ModbusGateway | reusable-sibling-path | openknxproducer | d1bb66c ✓ | 3 | 3 | 3 | 0 | - |
| OAM-NeoPixel | reusable | openknxproducer | 0c5a94d ✓ | 42 | 14 | 14 | 28 | device-id-not-string-literal |
| OAM-Nuki | reusable-sibling-path | openknxproducer | f2250e1 ✓ | 2 | 1 | 1 | 1 | device-id-not-string-literal |
| OAM-OneWireModule | missing-build-release | – | – (tip) | 0 | 0 | 0 | 0 | kein Build-Release.ps1 |
| OAM-PresenceModule | reusable | openknxproducer | – (tip) | 10 | 0 | 0 | 10 | no-device-define |
| OAM-REG1-Schaltaktor-4x | reusable-sibling-path | openknxproducer | 7dad5ab ✓ | 1 | 1 | 1 | 0 | - |
| OAM-RaumController | reusable | openknxproducer | a9e034d ✓ | 24 | 23 | 23 | 1 | no-device-define |
| OAM-SensorModule | reusable-sibling-path | openknxproducer | – (tip) | 18 | 0 | 4 | 14 | no-device-define |
| OAM-ShutterController | reusable | openknxproducer | 15b4c95 ✓ | 4 | 3 | 3 | 1 | no-device-define |
| OAM-SmartHomeBridge | reusable-sibling-path | openknxproducer | a9e034d ✓ | 4 | 4 | 4 | 0 | - |
| OAM-Sonos | reusable-sibling-path | openknxproducer | a9e034d ✓ | 4 | 4 | 4 | 0 | - |
| OAM-SonosNFCPlayer | reusable-sibling-path | openknxproducer | a9e034d ✓ | 1 | 0 | 1 | 0 | device-in-build-flags |
| OAM-StateEngine | reusable-sibling-path | openknxproducer | 2af139a ✓ | 7 | 4 | 4 | 3 | device-id-not-string-literal |
| OAM-SwitchActuator | reusable-sibling-path | openknxproducer | – (tip) | 2 | 0 | 2 | 0 | device-in-oam-header |
| OAM-TouchRound | reusable | openknxproducer | – (tip) | 1 | 0 | 0 | 1 | no-device-define |
| OAM-UP1-8xSensor | reusable-sibling-path | openknxproducer | bdac6b9 ✓ | 1 | 1 | 1 | 0 | - |
| OAM-UP1-Taster | reusable-sibling-path | openknxproducer | 77d38d0 ✗ (tip) | 1 | 0 | 1 | 0 | hwconfig-pin-unresolved |
| OAM-VirtualButton | reusable | openknxproducer | – (tip) | 3 | 0 | 0 | 3 | no-device-define |
| OAM-WeatherWN90LP | reusable-sibling-path | openknxproducer | ac57a3a ✓ | 1 | 1 | 1 | 0 | - |
| SOM-UP | reusable-sibling-path | openknxproducer | 6a4c306 ✓ | 4 | 3 | 4 | 0 | device-in-oam-header |
| SEN-UP1-8xTH | reusable-sibling-path | openknxproducer | bdac6b9 ✓ | 1 | 1 | 1 | 0 | - |

Spalte `Build-Skripte`: `reusable` = alle Aufrufe gehen an `lib/OGM-Common/scripts/setup/reusable/`; `reusable-sibling-path` = mindestens ein Aufruf geht an `../OGM-Common/scripts/setup/reusable/` (Schwesterverzeichnis). Das funktioniert nur, wenn `lib/OGM-Common` und `../OGM-Common` derselbe Stand sind: Build-Release-Preprocess.ps1 ruft `lib/OGM-Common/scripts/setup/reusable/Build-ReleaseJson.ps1 Init` mit festem Pfad auf, Build-Step.ps1 dagegen `$PSScriptRoot/Build-ReleaseJson.ps1`. `template-no-build-step` = Build-Release.ps1 entspricht dem Template ohne Build-Step; `missing-build-release` = Datei fehlt.

## Bedeutung der Gründe

- `ok`: deviceId und deviceName werden aus OGM-HardwareConfig aufgelöst, die wiederverwendbaren Skripte aus `lib/OGM-Common/scripts/setup/reusable` werden benutzt, Feature-Set ist gültig, appId ist zu erwarten.
- `no-device-define`: das env setzt kein `-D DEVICE_*`; prepare.py findet keine DEVICE_ID -> Produkt ohne deviceId/deviceName.
- `device-not-in-hwconfig`: ein `DEVICE_*`-Define ist gesetzt, aber kein Header im durchsuchten Satz (OGM-HardwareConfig am Pin, include/ und src/ des OAM, OFM-Libs) definiert dafür eine DEVICE_ID.
- `device-in-oam-header`: DEVICE_ID wird aufgelöst, stammt aber aus `include/hardware.h` des OAM (bzw. einem anderen OAM-Header) und nicht aus OGM-HardwareConfig -> nicht im Hardware-Register.
- `device-in-lib-header`: DEVICE_ID stammt aus einem OFM-Modul-Header.
- `device-in-legacy-common-header`: DEVICE_ID stammt aus `include/OpenKNXHardware.h` des alten, gepinnten OGM-Common (dort ohne DEVICE_NAME).
- `device-in-build-flags`: DEVICE_ID/DEVICE_NAME werden direkt als `-D` in platformio.ini gesetzt (JSON wird gefüllt, Gerät steht aber in keinem Header-Register).
- `device-id-not-string-literal`: DEVICE_ID ist in OGM-HardwareConfig als Makro-Ausdruck definiert (z. B. `PREFIX_ID "-DD-Meter"`). prepare.py greift mit `^#define DEVICE_ID "(.*)"$` auf die `-dM`-Ausgabe zu, in der der Ausdruck unexpandiert steht -> keine deviceId, obwohl die Firmware einen gültigen String sieht (Spalte `deviceIdExpanded` in result.json). Fix gehört nach prepare.py (Makro expandieren) oder in die Header.
- Spalte `JSON vollst.`: Produkte, bei denen alle Felder gefüllt würden, unabhängig davon, ob das Gerät aus OGM-HardwareConfig stammt (`ok` + `device-in-*`-Fälle mit DEVICE_NAME).
- `no-device-name`: DEVICE_ID vorhanden, aber kein DEVICE_NAME.
- `custom-build-scripts`: Build-Release.ps1 nutzt projektlokale Kopien / andere Skripte statt der wiederverwendbaren aus OGM-Common (Build-ReleaseJson.ps1 wird nicht aufgerufen).
- `missing-build-release` / `template-no-build-step`: kein `scripts/Build-Release.ps1` bzw. nur das Template ohne Build-Step-Aufrufe (keine Produkte).
- `env-missing`: Build-Step referenziert ein env, das es in platformio.ini (inkl. extra_configs) nicht gibt.
- `invalid-featureset`: Feature-Set wird von Build-Step.ps1 nicht akzeptiert (Build bricht ab).
- `kaenx-appid-unknown` / `appid-unknown`: compileWith = kaenxcreator ohne eingechecktes include/knxprod.h mit MAIN_OpenKnxId/MAIN_ApplicationNumber bzw. kein KNX-Tool -> appId fehlt voraussichtlich.
- `preprocess-failed`: Host-Präprozessor scheiterte und auch die textuelle Suche fand keine DEVICE_ID.
- `hwconfig-pin-unresolved`: der in dependencies.txt gepinnte OGM-HardwareConfig-Commit ist nicht auffindbar; es wurde die Spitze von v1 verwendet.

## Was wo angepasst werden muss

### `no-device-define` (27)

- OAM-AccessControl / env `release_R503` / Produkt `AB-SmartHouse-AccessControl` [always]: Defines im env: BOARD_AB_SMARTHOUSE_FINGERPRINT_V13
- OAM-BinaryClock / env `release_AB_SMARTHOUSE_CLK_WALL_BIN` / Produkt `AB-SmartHouse-BinaryClock` [always]: Defines im env: BOARD_AB_SMARTHOUSE_CLK_WALL_BIN
- OAM-ClimateControl / env `release_OpenKNX_REG1_Controller2040` / Produkt `OpenKNX-REG1-BASE-V0` [always]: Defines im env: OKNXHW_REG1_CONTROLLER2040
- OAM-EnoceanGateway / env `build` / Produkt `firmware` [always]: Defines im env: BOARD_ENOCEAN
- OAM-EnoceanGateway_V2 / env `release_EnoceanGateway_RP2040` / Produkt `EnoceanGateway_RP2040` [always]: Defines im env: keine Hardware-Defines
- OAM-PresenceModule / env `release_RP2040_devel` / Produkt `DeveloperBoard-JustForTesters` [always]: Defines im env: BOARD_MASIFI_HFPM_DEVEL
- OAM-PresenceModule / env `release_1TE_RP2040_SmartMF` / Produkt `1TE-RP2040-SmartMF` [always]: Defines im env: BOARD_SMARTMF_1TE_RP2040
- OAM-PresenceModule / env `release_RealPresence` / Produkt `RealPresence` [always]: Defines im env: BOARD_MASIFI_HFPM_DEVEL2
- OAM-PresenceModule / env `release_RealPresence_v20` / Produkt `RealPresence_v2.0` [always]: Defines im env: BOARD_MASIFI_HFPM_V20
- OAM-PresenceModule / env `release_Sensormodul_v40_RP2040` / Produkt `Sensormodul-v4x-RP2040` [always]: Defines im env: BOARD_MASIFI_V40
- OAM-PresenceModule / env `release_Sensormodul_v31_SAMD` / Produkt `Sensormodul-v31-SAMD` [Release]: Defines im env: BOARD_MASIFI_V31
- OAM-PresenceModule / env `release_Sensormodul_v30_SAMD` / Produkt `Sensormodul-v30-SAMD` [Release]: Defines im env: BOARD_MASIFI_V3
- OAM-RaumController / env `release_BOARD_SMARTMF_RealPresence_V1_2` / Produkt `SmartMF-RealPresence-v1.2` [Release]: Defines im env: BOARD_MASIFI_HFPM_V20
- OAM-SensorModule / env `release_Sensormodul_v40_RP2040` / Produkt `SmartMF-Sensormodul-RP2040` [Big]: Defines im env: BOARD_MASIFI_V40
- OAM-SensorModule / env `release_1TE_RP2040_SmartMF` / Produkt `SmartMF-1TE-RP2040` [Big]: Defines im env: BOARD_SMARTMF_1TE_RP2040
- OAM-SensorModule / env `release_UP1_SENSOR_1KANAL` / Produkt `SEN-UP1-8XTH` [Big]: Defines im env: BOARD_UP1_SENSOR_1KANAL
- OAM-SensorModule / env `release_RealPresence` / Produkt `RealPresence` [Big]: Defines im env: BOARD_MASIFI_HFPM_DEVEL2
- OAM-SensorModule / env `release_RealPresence_v20` / Produkt `RealPresence_v2.0` [Big]: Defines im env: BOARD_MASIFI_HFPM_V20
- OAM-SensorModule / env `release_Sensormodul_v40_RP2040_Vpm` / Produkt `Sensormodul-v4x-RP2040` [Vpm]: Defines im env: BOARD_MASIFI_V40
- OAM-SensorModule / env `release_1TE_RP2040_SmartMF_Vpm` / Produkt `SmartMF-1TE-RP2040` [Vpm]: Defines im env: BOARD_SMARTMF_1TE_RP2040
- OAM-SensorModule / env `release_Sensormodul_v40_RP2040_Wire` / Produkt `Sensormodul-v4x-RP2040` [OneWire]: Defines im env: BOARD_MASIFI_V40
- OAM-SensorModule / env `release_1TE_RP2040_SmartMF_Wire` / Produkt `SmartMF-1TE-RP2040` [OneWire]: Defines im env: BOARD_SMARTMF_1TE_RP2040
- OAM-ShutterController / env `release_OpenKNX_REG1_Controller2040` / Produkt `OpenKNX-REG1-BASE-V0` [always]: Defines im env: OKNXHW_REG1_CONTROLLER2040
- OAM-TouchRound / env `release_RP2350` / Produkt `TouchRound-RP2350` [always]: Defines im env: keine Hardware-Defines
- OAM-VirtualButton / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [always]: Defines im env: BOARD_SIRSYDOM_PIPICO_BCU_CONNECTOR
- OAM-VirtualButton / env `release_1TE_RP2040_SmartMF` / Produkt `1TE-RP2040-SmartMF` [always]: Defines im env: BOARD_SMARTMF_1TE_RP2040
- OAM-VirtualButton / env `release_OpenKNX_REG1_Base` / Produkt `OpenKNX-REG1-Base` [always]: Defines im env: BOARD_OPENKNX_REG1_BASE

### `device-id-not-string-literal` (36)

- OAM-IOHomeControl / env `release_OpenKNX_XIAO_S3_SX1262_TP` / Produkt `OpenKNX-XIAO-S3-SX1262-TP` [always]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-IOHomeControl/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-IOHomeControl / env `release_OpenKNX_XIAO_S3_SX1262_IP` / Produkt `OpenKNX-XIAO-S3-SX1262-IP` [always]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-IOHomeControl/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-LogicModule / env `release_DEVICE_REG2_PIPICO_V1_DD_METER` / Produkt `OpenKNX-REG2-PiPico-V1-DeviceDisplay-Meter` [Release]: `#define DEVICE_ID PREFIX_ID "-DD-Meter"` -> "REG2-PP-V1-DD-Meter" in OAM-LogicModule/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/REG2/PiPico.h (Define: DEVICE_REG2_PIPICO_V1_DD_METER)
- OAM-Meter / env `release_DEVICE_REG2_PIPICO_V1_DD_METER` / Produkt `OpenKNX-REG2-PiPico-V1-DeviceDisplay-Meter` [always]: `#define DEVICE_ID PREFIX_ID "-DD-Meter"` -> "REG2-PP-V1-DD-Meter" in OAM-Meter/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/REG2/PiPico.h (Define: DEVICE_REG2_PIPICO_V1_DD_METER)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2350_V1` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-2350"` -> "OKNXIAO-V1-KNeoPix-2350" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V1` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_TPWIFI` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V1_TPWIFI` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2350_V15` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-2350"` -> "OKNXIAO-V15-KNeoPix-2350" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V15` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32S3"` -> "OKNXIAO-V15-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_TPWIFI` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V15_TPWIFI` [table:miniTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32S3"` -> "OKNXIAO-V15-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2350_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-2350"` -> "OKNXIAO-V1-KNeoPix-2350" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2040_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-2040"` -> "OKNXIAO-V1-KNeoPix-2040" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_IP` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V1_IP` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_TPWIFI` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V1_TPWIFI` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32S3"` -> "OKNXIAO-V1-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2350_V15` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-2350"` -> "OKNXIAO-V15-KNeoPix-2350" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-RP2040_V15` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-2040"` -> "OKNXIAO-V15-KNeoPix-2040" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V15` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32S3"` -> "OKNXIAO-V15-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_IP` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V15_IP` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32S3"` -> "OKNXIAO-V15-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_TPWIFI` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32S3_V15_TPWIFI` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32S3"` -> "OKNXIAO-V15-KNeoPix-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_RP2040_MINI_V1` / Produkt `OpenKNX-XIAO-RP2040-Mini_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-Mini-2040"` -> "OKNXIAO-V1-Mini-2040" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_RP2040_MINI_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_RP2350_MINI_V1` / Produkt `OpenKNX-XIAO-RP2350-Mini_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-Mini-2350"` -> "OKNXIAO-V1-Mini-2350" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_RP2350_MINI_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1` / Produkt `OpenKNX-XIAO-ESP32S3-Mini_V1` [table:standardTargets (default)]: `#define DEVICE_ID PREFIX_ID "V1-Mini-ESP32S3"` -> "OKNXIAO-V1-Mini-ESP32S3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C3_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32C3"` -> "OKNXIAO-V1-KNeoPix-ESP32C3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C5_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32C5"` -> "OKNXIAO-V1-KNeoPix-ESP32C5" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V1` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C6_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-KNeoPix-ESP32C6"` -> "OKNXIAO-V1-KNeoPix-ESP32C6" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C3_V15` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32C3"` -> "OKNXIAO-V15-KNeoPix-ESP32C3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C5_V15` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32C5"` -> "OKNXIAO-V15-KNeoPix-ESP32C5" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V15` / Produkt `OpenKNX-XIAO-KNeoPiX-ESP32C6_V15` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V15-KNeoPix-ESP32C6"` -> "OKNXIAO-V15-KNeoPix-ESP32C6" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V15)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_ESP32C3_MINI_V1` / Produkt `OpenKNX-XIAO-ESP32C3-Mini_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-Mini-ESP32C3"` -> "OKNXIAO-V1-Mini-ESP32C3" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32C3_MINI_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_ESP32C5_MINI_V1` / Produkt `OpenKNX-XIAO-ESP32C5-Mini_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-Mini-ESP32C5"` -> "OKNXIAO-V1-Mini-ESP32C5" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32C5_MINI_V1)
- OAM-NeoPixel / env `release_OKNXHW_OPENKNXIAO_ESP32C6_MINI_V1` / Produkt `OpenKNX-XIAO-ESP32C6-Mini_V1` [table:fullTargets]: `#define DEVICE_ID PREFIX_ID "V1-Mini-ESP32C6"` -> "OKNXIAO-V1-Mini-ESP32C6" in OAM-NeoPixel/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32C6_MINI_V1)
- OAM-Nuki / env `release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1` / Produkt `OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1` [always]: `#define DEVICE_ID PREFIX_ID "-Mini"` -> "OKNXIAO-V1-Mini" in OAM-Nuki/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1)
- OAM-StateEngine / env `release_REG2_PIPICO_V1` / Produkt `OpenKNX-REG2-PiPico-V1` [always]: `#define DEVICE_ID PREFIX_ID` -> "REG2-PP-V1" in OAM-StateEngine/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/REG2/PiPico.h (Define: DEVICE_REG2_PIPICO_V1)
- OAM-StateEngine / env `release_XIAO_MINI_RP2040_V1` / Produkt `OpenKNX-OpenKNXiao-V1-Mini-RP2040` [always]: `#define DEVICE_ID PREFIX_ID "V1-Mini-2040"` -> "OKNXIAO-V1-Mini-2040" in OAM-StateEngine/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_RP2040_MINI_V1)
- OAM-StateEngine / env `release_XIAO_MINI_ESP32_V1` / Produkt `OpenKNX-OpenKNXiao-V1-Mini-ESP32` [always]: `#define DEVICE_ID PREFIX_ID "V1-Mini-ESP32S3"` -> "OKNXIAO-V1-Mini-ESP32S3" in OAM-StateEngine/lib/OGM-HardwareConfig/include/HardwareConfig/OpenKNX/Xiao.h (Define: OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1)

### `device-in-oam-header` (21)

- OAM-BinaryInput / env `release_AB_SMARTHOUSE_BI_REG6_16CH` / Produkt `ABSmartHouse-BinaryInput` [always]: DEVICE_ID "AB-BIN-16CH" aus OAM-BinaryInput/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_BI_REG6_16CH)
- OAM-BusPowerSupply / env `release_AB_SMARTHOUSE_BPS_REG6` / Produkt `AB-SmartHouse-BusPowerSupply-REG6` [always]: DEVICE_ID "AB-BPS-RED" aus OAM-BusPowerSupply/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_BPS_REG6)
- OAM-GuideLight / env `release_ABSmartHouse_GuideLight` / Produkt `AB-SmartHouse_GuideLight` [always]: DEVICE_ID "AB-DIM-GL" aus OAM-GuideLight/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_GUIDE_LIGHT)
- OAM-HeatingActuator / env `release_AB_SMARTHOUSE_HTA_REG6_12CH` / Produkt `AB-SmartHouse-HeatingActuator-REG6-12CH` [always]: DEVICE_ID "AB-HTA-12CH" aus OAM-HeatingActuator/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_HTA_REG6_12CH)
- OAM-HeatingActuator / env `release_AB_SMARTHOUSE_HTA_UP_1CH` / Produkt `AB-SmartHouse-HeatingActuator-UP_1CH` [always]: DEVICE_ID "AB-HTA-1CH" aus OAM-HeatingActuator/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_HTA_UP_1CH)
- OAM-LeakageSensor / env `release_ABSmartHouse_LeakageSensor` / Produkt `AB-SmartHouse_LeakageSensor` [always]: DEVICE_ID "AB-DIM-GL" aus OAM-LeakageSensor/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_LEAKAGE_SENSOR)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CV_UP_6CH` / Produkt `AB-SmartHouse_CV_UP_6CH` [always]: DEVICE_ID "AB-DIM-CV-UP-6CH" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CV_UP_6CH)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CV_UP_6CH_CS` / Produkt `AB-SmartHouse_CV_UP_6CH_CS` [always]: DEVICE_ID "AB-DIM-CV-UP-6CH-CS" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CV_UP_6CH_CS)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CV_REG_12CH` / Produkt `AB-SmartHouse_CV_REG_12CH` [always]: DEVICE_ID "AB-DIM-CV-REG-12CH" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CV_REG_12CH)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CV_REG_12CH_CS` / Produkt `AB-SmartHouse_CV_REG_12CH_CS` [always]: DEVICE_ID "AB-DIM-CV-REG-12CH-CS" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CV_REG_12CH_CS)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CC_UP_8CH` / Produkt `AB-SmartHouse_CC_UP_8CH` [always]: DEVICE_ID "AB-DIM-CC-UP-8CH" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CC_UP_8CH)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CC_UP_16CH` / Produkt `AB-SmartHouse_CC_UP_16CH` [always]: DEVICE_ID "AB-DIM-CC-UP-16CH" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CC_UP_16CH)
- OAM-LedDimmer-AB / env `release_ABSmartHouse_CC_REG_12CH` / Produkt `AB-SmartHouse_CC_REG_12CH` [always]: DEVICE_ID "AB-DIM-CC-REG-12CH" aus OAM-LedDimmer-AB/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_CC_REG_12CH)
- OAM-LogicModule / env `release_AB_TouchRound_RP2350` / Produkt `AB-TouchRound-RP2350` [Release]: DEVICE_ID "AB-TOUCH-ROUND" aus OAM-LogicModule/include/hardware.h (Define: BOARD_AB_TOUCH_ROUND_RP2350)
- OAM-SensorModule / env `release_UP1_PM_HF` / Produkt `UP1-PM-HF` [Big]: DEVICE_ID "UP1-PM-HF" aus OAM-SensorModule/include/hardware.h (Define: DEVICE_UP1_PM_HF)
- OAM-SensorModule / env `release_PresenceMultiSensor_ABSmartHouse` / Produkt `AB-SmartHouse-PresenceMultiSensor` [Big]: DEVICE_ID "AB-PRE" aus OAM-SensorModule/include/hardware.h (Define: BOARD_AB_PRE)
- OAM-SensorModule / env `release_PresenceMR16_ABSmartHouse` / Produkt `AB-SmartHouse-PresenceMR16` [Big]: DEVICE_ID "AB-PRE-MR16" aus OAM-SensorModule/include/hardware.h (Define: BOARD_AB_PRE_MR16)
- OAM-SensorModule / env `release_PresenceWall_ABSmartHouse` / Produkt `AB-SmartHouse-PresenceWall` [Big]: DEVICE_ID "AB-PRE-WALL" aus OAM-SensorModule/include/hardware.h (Define: BOARD_AB_PRE_WALL)
- OAM-SwitchActuator / env `release_AB_SMARTHOUSE_SA_REG6_8CH` / Produkt `AB-SmartHouse-SwitchActuator-REG6-8CH` [always]: DEVICE_ID "AB-SWA-8CH" aus OAM-SwitchActuator/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_SA_REG6_8CH)
- OAM-SwitchActuator / env `release_AB_SMARTHOUSE_SA_REG6_6CH_CS` / Produkt `AB-SmartHouse-SwitchActuator-REG6-6CH-CS` [always]: DEVICE_ID "AB-SWA-6CH-CS" aus OAM-SwitchActuator/include/hardware.h (Define: BOARD_AB_SMARTHOUSE_SA_REG6_6CH_CS)
- SOM-UP / env `release_DEV_BOARD` / Produkt `firmware_DEV_BOARD` [Dev]: DEVICE_ID "MASIFI-SENSOR-BREAKOUT" aus SOM-UP/include/hardware.h (Define: DEVICE_MASIFI_SENSOR_BREAKOUT)

### `device-in-build-flags` (3)

- OAM-Aircondition / env `release_AZDelivery_DevKit_C_V4_TP` / Produkt `Aircondition-AZDelivery_DevKit_C_V4_TP` [always]: -D DEVICE_ID="AZD-ESP32-DevKit-V4", DEVICE_NAME="AZDelivery ESP32 Board Dev Kit C V4" in platformio.ini
- OAM-Aircondition / env `release_AZDelivery_DevKit_C_V4_IP` / Produkt `Aircondition-AZDelivery_DevKit_C_V4_IP` [always]: -D DEVICE_ID="AZD-ESP32-DevKit-V4", DEVICE_NAME="AZDelivery ESP32 Board Dev Kit C V4" in platformio.ini
- OAM-SonosNFCPlayer / env `release_ESP32_Sonos_NFC_Player_HSU` / Produkt `ESP32-Sonos-NFC-Player-HSU` [always]: -D DEVICE_ID="ESP32-SONSO-NFC-PLAYER", DEVICE_NAME="ESP32x20Sonosx20NFCx20Player" in platformio.ini

### `device-in-legacy-common-header` (6)

- OAM-PresenceModule / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [always]: DEVICE_ID "PiPico-BCU-Connector" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_PIPICO_BCU_CONNECTOR)
- OAM-PresenceModule / env `release_OpenKNX_REG1_BASE_V0` / Produkt `OpenKNX-REG1-BASE-V0` [always]: DEVICE_ID "REG1-Base-V0" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_REG1_BASE_V0)
- OAM-PresenceModule / env `release_OpenKNX_REG1_BASE_V1` / Produkt `OpenKNX-REG1-BASE-V1` [always]: DEVICE_ID "REG1-Base-V1" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_REG1_BASE_V1)
- OAM-SensorModule / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [Big]: DEVICE_ID "PiPico-BCU-Connector" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_PIPICO_BCU_CONNECTOR)
- OAM-SensorModule / env `release_OpenKNX_REG1_BASE_V0` / Produkt `OpenKNX-REG1-Base-V0` [Big]: DEVICE_ID "REG1-Base-V0" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_REG1_BASE_V0)
- OAM-SensorModule / env `release_OpenKNX_REG1_BASE_V1` / Produkt `OpenKNX-REG1-Base-V1` [Big]: DEVICE_ID "REG1-Base-V1" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h (Define: DEVICE_REG1_BASE_V1)

### `no-device-name` (6)

- OAM-PresenceModule / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [always]: DEVICE_ID "PiPico-BCU-Connector" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h
- OAM-PresenceModule / env `release_OpenKNX_REG1_BASE_V0` / Produkt `OpenKNX-REG1-BASE-V0` [always]: DEVICE_ID "REG1-Base-V0" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h
- OAM-PresenceModule / env `release_OpenKNX_REG1_BASE_V1` / Produkt `OpenKNX-REG1-BASE-V1` [always]: DEVICE_ID "REG1-Base-V1" aus OAM-PresenceModule/lib/OGM-Common/include/OpenKNXHardware.h
- OAM-SensorModule / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [Big]: DEVICE_ID "PiPico-BCU-Connector" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h
- OAM-SensorModule / env `release_OpenKNX_REG1_BASE_V0` / Produkt `OpenKNX-REG1-Base-V0` [Big]: DEVICE_ID "REG1-Base-V0" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h
- OAM-SensorModule / env `release_OpenKNX_REG1_BASE_V1` / Produkt `OpenKNX-REG1-Base-V1` [Big]: DEVICE_ID "REG1-Base-V1" aus OAM-SensorModule/lib/OGM-Common/include/OpenKNXHardware.h

### `env-missing` (6)

- OAM-ElectricDoorDrive / env `release_SAMD` / Produkt `SAMD` [always]: env nicht in platformio.ini
- OAM-ElectricDoorDrive / env `release_PiPico_BCU_Connector` / Produkt `PiPico-BCU-Connector` [always]: env nicht in platformio.ini
- OAM-ElectricDoorDrive / env `release_MASIFI_SENSOR_BREAKOUT` / Produkt `Masifi-Sensor_Breakout` [always]: env nicht in platformio.ini
- OAM-ElectricDoorDrive / env `release_ESP32` / Produkt `ESP32` [always]: env nicht in platformio.ini
- OAM-SensorModule / env `release_Sensormodul_v31_SAMD_Wire` / Produkt `Sensormodul-v31-SAMD` [OneWire]: env nicht in platformio.ini
- OAM-SensorModule / env `release_Sensormodul_v30_SAMD_Wire` / Produkt `Sensormodul-v30-SAMD` [OneWire]: env nicht in platformio.ini

### `missing-build-release` (3)

- **GW-REG1-Dali**: scripts/Build-Release.ps1 fehlt
- **OAM-FanControl**: scripts/Build-Release.ps1 fehlt
- **OAM-OneWireModule**: scripts/Build-Release.ps1 fehlt

### `template-no-build-step` (1)

- **OAM-Dummy**: scripts/Build-Release.ps1 enthält keine Build-Step-Aufrufe (Pre/Post: ['reusable-sibling']/['reusable-sibling']; weitere Skripte: –; lokale Skripte: Build-Release-Package.ps1, Build-Release.ps1, OpenKNX-Build-Settings.ps1, OpenKNX-Build.ps1)

### `hwconfig-pin-unresolved` (1)

- OAM-UP1-Taster / env `release_UP1` / Produkt `firmware` [always]: Pin 77d38d0 (up1-tas-dev)

## Vollständige Produkte (`ok`)

- **BEM-GardenControl**: `GardenControl` (SMARTMF-GC)
- **OAM-AccessControl**: `UP1-SEN-8x` (UP1-SEN-8x)
- **OAM-Aircondition**: `Aircondition-OpenKNX-UP1-GW-UART` (UP1-GW-UART), `Aircondition-OpenKNX-UP1-WLAN-2xUART` (UP1-WLAN-2xUART), `Aircondition-Adafruit_Feather_ESP32_V2_TP` (ADF-ESP32-FEATHER-V2), `Aircondition-Adafruit_Feather_ESP32_V2_IP` (ADF-ESP32-FEATHER-V2)
- **OAM-ClimateControl**: `SMARTMF_SENSORMODUL` (SMARTMF-SEN-V4), `PiPico-BCU-Connector` (PiPico-BCU-Connector), `firmware_SMARTMF_1TE_REG` (SMARTMF-1TE-REG), `OpenKNX-REG1-BASE-V1` (REG1-Base)
- **OAM-Homematic**: `OpenKNX-REG1-Eth` (REG1-Eth), `OpenKNX-REG1-LAN-TP-Base` (REG1-LAN-TP-Base)
- **OAM-IOHomeControl**: `OpenKNX-REG1-ESP-V00-11-SX1276-TP` (REG1-DEV-LAN-TP-Base-V00-11), `OpenKNX-REG1-ESP-V00-11-SX1276-IP` (REG1-DEV-LAN-TP-Base-V00-11)
- **OAM-IP-Router**: `IP-Router-REG1-Eth` (REG1-Eth), `IP-Router-REG1-LAN-TP-Base` (REG1-LAN-TP-Base)
- **OAM-InfraredGateway**: `UP1-GW-IR` (UP1-GW-IR)
- **OAM-InternetServices**: `InternetServices-REG1-ETH` (REG1-Eth), `InternetServices-REG1-LAN-TP-Base` (REG1-LAN-TP-Base), `InternetServices-Adafruit_Feather_ESP32_V2_TP` (ADF-ESP32-FEATHER-V2)
- **OAM-LogicModule**: `SmartMF-1TE-RP2040` (SMARTMF-1TE-REG), `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-REG1-LAN-TP-BASE` (REG1-LAN-TP-Base), `OpenKNX-REG1-BASE-IP` (REG1-Base-IP), `OpenKNX-REG1-LAN-TP-BASE` (REG1-LAN-TP-Base), `OpenKNX-REG1-BASE-V0` (REG1-Base-V0), `OpenKNX-REG1-BASE` (REG1-Base), `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-UP1-SEN-8xTH` (SEN-UP1-8xTH), `OpenKNX-REG1-Multisensor` (REG1-SEN-Multi), `SmartMF-S0-Zaehlermodul` (SMARTMF-1TE-BE-3CH), `SmartMF-eHZ-Schnittstelle` (SMARTMF-2SML-3BE), `SmartMF-1TE-RP2040` (SMARTMF-1TE-REG), `SmartMF-Sensormodul-RP2040` (SMARTMF-SEN-V4), `SmartMF-RealPresence-V2` (SMARTMF-RP-V2), `OpenKNX-REG1-BASE-IP` (REG1-Base-IP)
- **OAM-Meter**: `OpenKNX-REG1-GW-RF868M` (REG1-GW-RF868M), `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-UP1-8xSensor` (SEN-UP1-8xTH), `OpenKNX-REG1-Basismodul-V0` (REG1-Base-V0), `OpenKNX-REG1-Basismodul` (REG1-Base), `OpenKNX-REG1-Basismodul-IP` (REG1-Base-IP), `OpenKNX-REG1-MultiSensor` (REG1-SEN-Multi), `OpenKNX-REG1-LAN-MultiSensor` (REG1-LAN-SEN-Multi), `OpenKNX-REG1-WIFI-MultiSensor` (REG1-LAN-SEN-Multi), `Smart-MF-eHZ-Schnittstelle` (SMARTMF-2SML-3BE), `Smart-MF-S0-Zaehlermodul` (SMARTMF-1TE-BE-3CH)
- **OAM-ModbusGateway**: `SMART-MF_Modbus_RTU_2TE` (SMARTMF-Modbus-RTU-3BE), `SMART-MF_Modbus_RTU_1TE` (SMARTMF-1TE-MODBUS), `SMART-MF_Modbus_RTU_AUSSEN` (SMARTMF-Modbus-Aussen)
- **OAM-NeoPixel**: `OpenKNX-UP1-GW-UART` (UP1-GW-UART), `Gledopto-GL-C-309WL-ESP32` (GL-C-309WL), `Gledopto-GL-C-017WL-ESP32` (GL-C-017WL), `Gledopto-GL-C-620WL-ESP32` (GL-C-620WL), `QuinLED-Dig2Go` (QuinLED-Dig2Go), `QuinLED-Dig-Uno-V3-WiFi` (QuinLED-Dig-Uno-V3-WiFi), `QuinLED-Dig-Uno-V3-Ethernet` (QuinLED-Dig-Uno-V3-Ethernet), `QuinLED-Dig-Uno-V3-WiFi-AE-Plus` (QuinLED-Dig-Uno-V3-WiFi-AE-Plus), `QuinLED-Dig-Quad-V3-WiFi` (QuinLED-Dig-Quad-V3-WiFi), `QuinLED-Dig-Quad-V3-Ethernet` (QuinLED-Dig-Quad-V3-Ethernet), `QuinLED-Dig-Quad-V3-WiFi-AE-Plus` (QuinLED-Dig-Quad-V3-WiFi-AE-Plus), `QuinLED-Dig-Octa-32-8L-WiFi` (QuinLED-Dig-Octa-32-8L-WiFi), `QuinLED-Dig-Octa-32-8L-Ethernet` (QuinLED-Dig-Octa-32-8L-Ethernet), `QuinLED-Dig-Next-2` (QuinLED-Dig-Next-2)
- **OAM-Nuki**: `Adafruit_Feather_ESP32_V2_TP` (ADF-ESP32-FEATHER-V2)
- **OAM-REG1-Schaltaktor-4x**: `firmware_REG1-SA-4xSELV` (REG1-SA-4xSELV)
- **OAM-RaumController**: `OpenKNX-UP1-PM-HF` (UP1-PM-HF), `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-REG1-BASE` (REG1-Base), `AB-SmartHouse-PresenceMultiSensor` (AB-PRE), `SmartMF-Sensormodul-RP2040` (SMARTMF-SEN-V4), `OpenKNX-UP1-PM-HF` (UP1-PM-HF), `SmartMF-1TE-REG` (SMARTMF-1Wire-1CH), `OpenKNX-UP1-PM-HF` (UP1-PM-HF), `OpenKNX-UP1-TAS-4x` (UP1-TAS-4x), `OpenKNX-REG1-BASE-V0` (REG1-Base-V0), `OpenKNX-REG1-BASE` (REG1-Base), `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-UP1-SEN-8x` (UP1-SEN-8x), `SmartMF-1TE-REG` (SMARTMF-1Wire-1CH), `SmartMF-Sensormodul-RP2040` (SMARTMF-SEN-V4), `SmartMF-RealPresence-v2` (SMARTMF-RP-V2), `OpenKNX-REG1-LAN-TP-BASE` (REG1-LAN-TP-Base), `OpenKNX-REG1-LAN-BASE` (REG1-LAN-Base), `AB-SmartHouse-PresenceMultiSensor` (AB-PRE), `AB-SmartHouse-PresenceMR16` (AB-PRE-MR16), `AB-SmartHouse-PresenceWall` (AB-PRE-WALL), `AB-SmartHouse-PresenceWall-Outside` (AB-PRE-WALL-OUT), `AB-SmartHouse-PushButtonsForGira` (AB-BUT-GIR)
- **OAM-ShutterController**: `firmware_SMARTMF_1TE_REG` (SMARTMF-1TE-REG), `OpenKNX-REG1-BASE-V1` (REG1-Base), `Sensormodul-v4.x-RP2040` (SMARTMF-SEN-V4)
- **OAM-SmartHomeBridge**: `SmartHomeBridge-REG1-LAN-TP-Base` (REG1-LAN-TP-Base), `SmartHomeBridge-REG1-LAN-Base` (REG1-LAN-Base), `SmartHomeBridge-Adafruit_Feather_ESP32_V2_TP` (ADF-ESP32-FEATHER-V2), `SmartHomeBridge-Adafruit_Feather_ESP32_V2_IP` (ADF-ESP32-FEATHER-V2)
- **OAM-Sonos**: `Sonos-REG1-LAN-TP-Base` (REG1-LAN-TP-Base), `Sonos-REG1-LAN-Base` (REG1-LAN-Base), `Sonos-Adafruit_Feather_ESP32_V2_TP` (ADF-ESP32-FEATHER-V2), `Sonos-Adafruit_Feather_ESP32_V2_IP` (ADF-ESP32-FEATHER-V2)
- **OAM-StateEngine**: `OpenKNX-PiPico-BCU-Connector` (PiPico-BCU-Connector), `OpenKNX-REG1-Base-V0` (REG1-Base-V0), `OpenKNX-REG1-Base` (REG1-Base), `SmartMF-1TE-REG` (SMARTMF-1TE-REG)
- **OAM-UP1-8xSensor**: `firmware` (SEN-UP1-8xTH)
- **OAM-WeatherWN90LP**: `firmware_UP1-GW-RS485` (UP1-GW-RS485)
- **SOM-UP**: `SmartMF-Soundmodul-REG` (SOM-UP-EXT-PWR), `SmartMF-Soundmodul-UP-EXT-PWR` (SOM-UP-EXT-PWR), `SmartMF-Soundmodul-UP` (SOM-UP)
- **SEN-UP1-8xTH**: `firmware` (SEN-UP1-8xTH)

## Auffälligkeiten bei den aufgelösten DEVICE_IDs

- DEVICE_ID "PiPico-BCU-Connector": OAM-ClimateControl/release_PiPico_BCU_Connector -> "OpenKNX PiPico BCU Connector" (hwconfig); OAM-LogicModule/release_DEVICE_PIPICO_BCU_CONNECTOR -> "OpenKNX PiPico BCU Connector" (hwconfig); OAM-Meter/release_DEVICE_PIPICO_BCU_CONNECTOR -> "OpenKNX PiPico BCU Connector" (hwconfig); OAM-PresenceModule/release_PiPico_BCU_Connector -> "None" (common); OAM-RaumController/release_DEVICE_PIPICO_BCU_CONNECTOR -> "OpenKNX PiPico BCU Connector" (hwconfig); OAM-SensorModule/release_PiPico_BCU_Connector -> "None" (common); OAM-StateEngine/release_PiPico_BCU_Connector -> "OpenKNX PiPico BCU Connector" (hwconfig)
- DEVICE_ID "AB-DIM-GL": OAM-GuideLight/release_ABSmartHouse_GuideLight -> "AB-SmartHouse Orientierungslicht" (oam:include/hardware.h); OAM-LeakageSensor/release_ABSmartHouse_LeakageSensor -> "AB-SmartHouse Orientierungslicht" (oam:include/hardware.h)
- DEVICE_ID "REG1-Base-V0": OAM-LogicModule/release_DEVICE_REG1_BASE_V0 -> "OpenKNX REG1 Basismodul V0" (hwconfig); OAM-Meter/release_DEVICE_REG1_BASE_V0 -> "OpenKNX REG1 Basismodul V0" (hwconfig); OAM-PresenceModule/release_OpenKNX_REG1_BASE_V0 -> "None" (common); OAM-RaumController/release_DEVICE_REG1_BASE_V0 -> "OpenKNX REG1 Basismodul V0" (hwconfig); OAM-SensorModule/release_OpenKNX_REG1_BASE_V0 -> "None" (common); OAM-StateEngine/release_REG1_BASE_V0 -> "OpenKNX REG1 Basismodul V0" (hwconfig)
- DEVICE_ID "REG1-Base-V1": OAM-PresenceModule/release_OpenKNX_REG1_BASE_V1 -> "None" (common); OAM-SensorModule/release_OpenKNX_REG1_BASE_V1 -> "None" (common)
- DEVICE_ID "UP1-PM-HF": OAM-RaumController/release_DEVICE_UP1_PM_HF -> "OpenKNX UP1 Präsenzmelder+" (hwconfig); OAM-SensorModule/release_UP1_PM_HF -> "OpenKNX UP1 Präsenzmelder+" (oam:include/hardware.h)
- DEVICE_ID "AB-PRE": OAM-RaumController/release_PresenceMultiSensor_ABSmartHouse -> "AB-SmartHouse Presence MultiSensor" (hwconfig); OAM-SensorModule/release_PresenceMultiSensor_ABSmartHouse -> "AB-SmartHouse Presence MultiSensor" (oam:include/hardware.h)
- DEVICE_ID "AB-PRE-MR16": OAM-RaumController/release_PresenceMR16_ABSmartHouse -> "AB-SmartHouse Presence MR16" (hwconfig); OAM-SensorModule/release_PresenceMR16_ABSmartHouse -> "AB-SmartHouse Presence MR16" (oam:include/hardware.h)
- DEVICE_ID "AB-PRE-WALL": OAM-RaumController/release_PresenceWall_ABSmartHouse -> "AB-SmartHouse Presence Wall" (hwconfig); OAM-SensorModule/release_PresenceWall_ABSmartHouse -> "AB-SmartHouse Presence Wall" (oam:include/hardware.h)
- DEVICE_ID "SOM-UP-EXT-PWR": SOM-UP/release_SMARTMF_SOM_REG -> "Smart-MF Soundmodul REG" (hwconfig); SOM-UP/release_SMARTMF_SOM_UP_EXT_PWR -> "Smart-MF Soundmodul UP (Ext-Power)" (hwconfig)

## Hinweise je OAM (Warnungen)

- **GW-REG1-Dali**:
  - lib OFM-TimerModule could not be cloned
- **OAM-AccessControl**:
  - release_R503: non-DEVICE_ hardware defines: BOARD_AB_SMARTHOUSE_FINGERPRINT_V13
- **OAM-BinaryClock**:
  - release_AB_SMARTHOUSE_CLK_WALL_BIN: non-DEVICE_ hardware defines: BOARD_AB_SMARTHOUSE_CLK_WALL_BIN
- **OAM-BinaryInput**:
  - release_AB_SMARTHOUSE_BI_REG6_16CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_BI_REG6_16CH
- **OAM-BusPowerSupply**:
  - OGM-Common: pinned commit 3ce0b9e not found, using tip of v1
  - release_AB_SMARTHOUSE_BPS_REG6: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_BPS_REG6
- **OAM-ClimateControl**:
  - release_OpenKNX_REG1_Controller2040: non-DEVICE_ hardware defines: OKNXHW_REG1_CONTROLLER2040
- **OAM-EnoceanGateway**:
  - build: non-DEVICE_ hardware defines: BOARD_ENOCEAN
- **OAM-GuideLight**:
  - release_ABSmartHouse_GuideLight: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_GUIDE_LIGHT
- **OAM-HeatingActuator**:
  - release_AB_SMARTHOUSE_HTA_REG6_12CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_HTA_REG6_12CH
  - release_AB_SMARTHOUSE_HTA_UP_1CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_HTA_UP_1CH
- **OAM-IOHomeControl**:
  - release_OpenKNX_XIAO_S3_SX1262_TP: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32S3")
  - release_OpenKNX_XIAO_S3_SX1262_TP: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1 KNeoPix ESP32S3")
  - release_OpenKNX_XIAO_S3_SX1262_IP: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32S3")
  - release_OpenKNX_XIAO_S3_SX1262_IP: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1 KNeoPix ESP32S3")
- **OAM-InfraredGateway**:
  - OGM-Common: pinned commit 22091c3 not found, using tip of v1
- **OAM-LeakageSensor**:
  - release_ABSmartHouse_LeakageSensor: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_LEAKAGE_SENSOR
- **OAM-LedDimmer-AB**:
  - release_ABSmartHouse_CV_UP_6CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CV_UP_6CH
  - release_ABSmartHouse_CV_UP_6CH_CS: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CV_UP_6CH_CS
  - release_ABSmartHouse_CV_REG_12CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CV_REG_12CH
  - release_ABSmartHouse_CV_REG_12CH_CS: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CV_REG_12CH_CS
  - release_ABSmartHouse_CC_UP_8CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CC_UP_8CH
  - release_ABSmartHouse_CC_UP_16CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CC_UP_16CH
  - release_ABSmartHouse_CC_REG_12CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_CC_REG_12CH
- **OAM-LogicModule**:
  - release_DEVICE_REG2_PIPICO_V1_DD_METER: DEVICE_ID is not a string literal: `PREFIX_ID "-DD-Meter"` (expands to "REG2-PP-V1-DD-Meter")
  - release_DEVICE_REG2_PIPICO_V1_DD_METER: DEVICE_NAME is not a string literal: `PREFIX_NAME " DeviceDisplay Meter"` (expands to "OpenKNX REG2 PiPico V1 DeviceDisplay Meter")
  - release_AB_TouchRound_RP2350: DEVICE_ID set via non-DEVICE_ define BOARD_AB_TOUCH_ROUND_RP2350
- **OAM-Meter**:
  - release_DEVICE_REG2_PIPICO_V1_DD_METER: DEVICE_ID is not a string literal: `PREFIX_ID "-DD-Meter"` (expands to "REG2-PP-V1-DD-Meter")
  - release_DEVICE_REG2_PIPICO_V1_DD_METER: DEVICE_NAME is not a string literal: `PREFIX_NAME " DeviceDisplay Meter"` (expands to "OpenKNX REG2 PiPico V1 DeviceDisplay Meter")
- **OAM-NeoPixel**:
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-2350"` (expands to "OKNXIAO-V1-KNeoPix-2350")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix RP2350"` (expands to "OpenKNXiao V1 KNeoPix RP2350")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_TPWIFI: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_TPWIFI: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-2350"` (expands to "OKNXIAO-V15-KNeoPix-2350")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2350_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix RP2350"` (expands to "OpenKNXiao V1.5 KNeoPix RP2350")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V15-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_TPWIFI: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V15-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_TPWIFI: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-2040"` (expands to "OKNXIAO-V1-KNeoPix-2040")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix RP2040"` (expands to "OpenKNXiao V1 KNeoPix RP2040")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_IP: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V1_IP: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-2040"` (expands to "OKNXIAO-V15-KNeoPix-2040")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_RP2040_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix RP2040"` (expands to "OpenKNXiao V1.5 KNeoPix RP2040")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_IP: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32S3"` (expands to "OKNXIAO-V15-KNeoPix-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32S3_V15_IP: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32S3"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32S3")
  - release_OKNXHW_OPENKNXIAO_RP2040_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-2040"` (expands to "OKNXIAO-V1-Mini-2040")
  - release_OKNXHW_OPENKNXIAO_RP2040_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini RP2040"` (expands to "OpenKNXiao V1 Mini RP2040")
  - release_OKNXHW_OPENKNXIAO_RP2350_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-2350"` (expands to "OKNXIAO-V1-Mini-2350")
  - release_OKNXHW_OPENKNXIAO_RP2350_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini RP2350"` (expands to "OpenKNXiao V1 Mini RP2350")
  - release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-ESP32S3"` (expands to "OKNXIAO-V1-Mini-ESP32S3")
  - release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini ESP32S3"` (expands to "OpenKNXiao V1 Mini ESP32S3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32C3"` (expands to "OKNXIAO-V1-KNeoPix-ESP32C3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32C3"` (expands to "OpenKNXiao V1 KNeoPix ESP32C3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32C5"` (expands to "OKNXIAO-V1-KNeoPix-ESP32C5")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32C5"` (expands to "OpenKNXiao V1 KNeoPix ESP32C5")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-KNeoPix-ESP32C6"` (expands to "OKNXIAO-V1-KNeoPix-ESP32C6")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 KNeoPix ESP32C6"` (expands to "OpenKNXiao V1 KNeoPix ESP32C6")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32C3"` (expands to "OKNXIAO-V15-KNeoPix-ESP32C3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C3_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32C3"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32C3")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32C5"` (expands to "OKNXIAO-V15-KNeoPix-ESP32C5")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C5_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32C5"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32C5")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V15: DEVICE_ID is not a string literal: `PREFIX_ID "V15-KNeoPix-ESP32C6"` (expands to "OKNXIAO-V15-KNeoPix-ESP32C6")
  - release_OKNXHW_OPENKNXIAO_KNEOPIX_ESP32C6_V15: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1.5 KNeoPix ESP32C6"` (expands to "OpenKNXiao V1.5 KNeoPix ESP32C6")
  - release_OKNXHW_OPENKNXIAO_ESP32C3_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-ESP32C3"` (expands to "OKNXIAO-V1-Mini-ESP32C3")
  - release_OKNXHW_OPENKNXIAO_ESP32C3_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini ESP32C3"` (expands to "OpenKNXiao V1 Mini ESP32C3")
  - release_OKNXHW_OPENKNXIAO_ESP32C5_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-ESP32C5"` (expands to "OKNXIAO-V1-Mini-ESP32C5")
  - release_OKNXHW_OPENKNXIAO_ESP32C5_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini ESP32C5"` (expands to "OpenKNXiao V1 Mini ESP32C5")
  - release_OKNXHW_OPENKNXIAO_ESP32C6_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-ESP32C6"` (expands to "OKNXIAO-V1-Mini-ESP32C6")
  - release_OKNXHW_OPENKNXIAO_ESP32C6_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini ESP32C6"` (expands to "OpenKNXiao V1 Mini ESP32C6")
- **OAM-Nuki**:
  - release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1: DEVICE_ID is not a string literal: `PREFIX_ID "-Mini"` (expands to "OKNXIAO-V1-Mini")
  - release_OKNXHW_OPENKNXIAO_ESP32S3_MINI_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME " Mini"` (expands to "OpenKNXiao V1 Mini")
- **OAM-PresenceModule**:
  - release_RP2040_devel: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_DEVEL
  - release_1TE_RP2040_SmartMF: non-DEVICE_ hardware defines: BOARD_SMARTMF_1TE_RP2040
  - release_RealPresence: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_DEVEL2
  - release_RealPresence_v20: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_V20
  - release_Sensormodul_v40_RP2040: non-DEVICE_ hardware defines: BOARD_MASIFI_V40
  - release_Sensormodul_v31_SAMD: non-DEVICE_ hardware defines: BOARD_MASIFI_V31
  - release_Sensormodul_v30_SAMD: non-DEVICE_ hardware defines: BOARD_MASIFI_V3
- **OAM-RaumController**:
  - release_BOARD_SMARTMF_RealPresence_V1_2: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_V20
- **OAM-SensorModule**:
  - release_Sensormodul_v40_RP2040: non-DEVICE_ hardware defines: BOARD_MASIFI_V40
  - release_1TE_RP2040_SmartMF: non-DEVICE_ hardware defines: BOARD_SMARTMF_1TE_RP2040
  - release_UP1_SENSOR_1KANAL: non-DEVICE_ hardware defines: BOARD_UP1_SENSOR_1KANAL
  - release_RealPresence: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_DEVEL2
  - release_RealPresence_v20: non-DEVICE_ hardware defines: BOARD_MASIFI_HFPM_V20
  - release_PresenceMultiSensor_ABSmartHouse: DEVICE_ID set via non-DEVICE_ define BOARD_AB_PRE
  - release_PresenceMR16_ABSmartHouse: DEVICE_ID set via non-DEVICE_ define BOARD_AB_PRE_MR16
  - release_PresenceWall_ABSmartHouse: DEVICE_ID set via non-DEVICE_ define BOARD_AB_PRE_WALL
  - release_Sensormodul_v40_RP2040_Vpm: non-DEVICE_ hardware defines: BOARD_MASIFI_V40
  - release_1TE_RP2040_SmartMF_Vpm: non-DEVICE_ hardware defines: BOARD_SMARTMF_1TE_RP2040
  - release_Sensormodul_v40_RP2040_Wire: non-DEVICE_ hardware defines: BOARD_MASIFI_V40
  - release_1TE_RP2040_SmartMF_Wire: non-DEVICE_ hardware defines: BOARD_SMARTMF_1TE_RP2040
- **OAM-ShutterController**:
  - lib OFM-UsbExchange referenced by platformio.ini but not in dependencies.txt (tip used)
  - release_OpenKNX_REG1_Controller2040: non-DEVICE_ hardware defines: OKNXHW_REG1_CONTROLLER2040
- **OAM-SonosNFCPlayer**:
  - release_ESP32_Sonos_NFC_Player_HSU: backslash escapes in build flag `-D DEVICE_NAME=\"ESP32\x20Sonos\x20NFC\x20Player\"`: the value depends on shell/SCons quoting
  - release_ESP32_Sonos_NFC_Player_HSU: backslash escapes in build flag `-D DEVICE_ID=\"ESP32-SONSO-NFC-PLAYER\"`: the value depends on shell/SCons quoting
- **OAM-StateEngine**:
  - release_REG2_PIPICO_V1: DEVICE_ID is not a string literal: `PREFIX_ID` (expands to "REG2-PP-V1")
  - release_REG2_PIPICO_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME` (expands to "OpenKNX REG2 PiPico V1")
  - release_XIAO_MINI_RP2040_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-2040"` (expands to "OKNXIAO-V1-Mini-2040")
  - release_XIAO_MINI_RP2040_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini RP2040"` (expands to "OpenKNXiao V1 Mini RP2040")
  - release_XIAO_MINI_ESP32_V1: DEVICE_ID is not a string literal: `PREFIX_ID "V1-Mini-ESP32S3"` (expands to "OKNXIAO-V1-Mini-ESP32S3")
  - release_XIAO_MINI_ESP32_V1: DEVICE_NAME is not a string literal: `PREFIX_NAME "V1 Mini ESP32S3"` (expands to "OpenKNXiao V1 Mini ESP32S3")
- **OAM-SwitchActuator**:
  - release_AB_SMARTHOUSE_SA_REG6_8CH: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_SA_REG6_8CH
  - release_AB_SMARTHOUSE_SA_REG6_6CH_CS: DEVICE_ID set via non-DEVICE_ define BOARD_AB_SMARTHOUSE_SA_REG6_6CH_CS
- **OAM-UP1-Taster**:
  - OGM-Common: pinned commit b7f860a not found, using tip of v1
  - OGM-HardwareConfig: pinned commit 77d38d0 not found, using tip of v1
- **OAM-VirtualButton**:
  - release_PiPico_BCU_Connector: non-DEVICE_ hardware defines: BOARD_SIRSYDOM_PIPICO_BCU_CONNECTOR
  - release_1TE_RP2040_SmartMF: non-DEVICE_ hardware defines: BOARD_SMARTMF_1TE_RP2040
  - release_OpenKNX_REG1_Base: non-DEVICE_ hardware defines: BOARD_OPENKNX_REG1_BASE
  - platformio.ini: pio failed: InvalidProjectConfError: Invalid '/home/user/openknx-analyse/repos/OAM-VirtualButton/platformio.ini' (project configuration file): 'No section: 'config:COMMON''

## Grenzen der statischen Analyse

- Der Präprozessor ist der Host-g++, nicht die Ziel-Toolchain. Toolchain-Makros wurden nachgestellt (`ARDUINO`, `ARDUINO_ARCH_RP2040`/`PICO_RP2040`/`PICO_RP2350`, `ESP32`/`ARDUINO_ARCH_ESP32`); Header, die auf andere Toolchain-/Board-Makros reagieren, könnten im echten Build anders auflösen.
- Nicht auffindbare Header (Arduino.h u. ä.) wurden durch leere Stubs ersetzt. Definiert ein solcher Header im echten Build DEVICE_ID, fehlt das hier. Die Stubs sind je Produkt in result.json (`preprocessor.stubs`) vermerkt.
- Include-Pfade: `-I` aus den Build-Flags, `include/`, `src/`, sowie `include/`/`src/` aller Libs aus dependencies.txt. Die echte LDF-Reihenfolge kann abweichen; Build-Flags aus `platformio.ini` wurden mit `pio project config` aufgelöst (bei `-DebugBuild` zusätzlich `debug_build_flags`).
- OFM-Module liegen als Spitze des in dependencies.txt genannten Branches vor (nicht am gepinnten Commit); nur OGM-Common und OGM-HardwareConfig wurden am gepinnten Commit ausgewertet. Beim echten Release-Build entscheidet der tatsächliche Stand im lib/-Verzeichnis des Entwicklers.
- Der Release-Build läuft lokal beim Entwickler; ob dessen OGM-Common bereits Build-ReleaseJson.ps1 enthält, ist nicht Teil der Analyse.
- Build-Release.ps1 wurde regulär geparst (Kommentare entfernt, `if ($releaseIndication -eq ...)`-Blöcke verfolgt). Build-Step-Aufrufe in Schleifen über Hashtable-Tabellen (`@{ Env = ...; Name = ...; Ext = ... }`, OAM-NeoPixel) wurden je Tabelle expandiert (`table:<name>`); andere dynamische Aufrufe werden nur markiert.
- appId: für `openknxproducer` wird angenommen, dass der Producer `include/knxprod.h` mit MAIN_OpenKnxId/MAIN_ApplicationNumber schreibt (ProcessInclude.cs). Für `kaenxcreator` ist nur ein eingechecktes knxprod.h als Hinweis verfügbar.
- GitHub-API war nicht verfügbar: Default-Branch/HEAD stammen aus dem Clone, der Archiv-Status aus releases.json.

## Nicht analysierte OAMs

- keine
