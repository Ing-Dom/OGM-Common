# Arbeitsdateien aus der Cloud-Session (Konzept Toolbox-Datenmodell)

Orphan-Branch nur zum Transport, nach dem Abholen löschen. Kein Bezug zum Code von OGM-Common.

- `beispiel/` Beispiel-Ausgaben des Aggregators (devices.json, applications.json, releases.json) und die
  `openknx-release.json` aus dem RaumController-Testlauf des Branches `release-json`.
- `analyse/` Statische Analyse der OAM-Repos: `analyse.py` (re-runnable, klont fehlende Repos selbst),
  `report.md` (deutscher Bericht), `result.json` (Rohdaten je OAM und Produkt).
- `test/` Testumgebung für `release-json`: `Build-Release-Test.ps1` (reduzierte Build-Release-Variante
  für OAM-RaumController), `testproj/` (minimales PlatformIO-Projekt für prepare.py mit echter Toolchain;
  `lib/` muss auf OGM-Common, OGM-HardwareConfig und knx zeigen), `baseline-out/` und `branch-out/`
  (entpackte Release-Zips mit v1- bzw. release-json-Skripten, Unterschied nur `data/openknx-release.json`),
  `pstest/`, `pstest2/` (Unit-Tests der drei Schritte von Build-ReleaseJson.ps1 mit pwsh).

Nicht enthalten, weil öffentlich und reproduzierbar: die Clones unter /home/user/openknx (OGM-Common,
OGM-HardwareConfig, OFM-Network, knx, OAM-LogicModule, OAM-RaumController, OpenKNX-UP1, OpenKNX.github.io,
OpenKNX.Toolbox, OpenKNX.Toolbox.Lib, OpenKNX.wiki, OpenKNXproducer) sowie die 45 OAM-Clones und Caches der Analyse.

Konzeptdokumente (Claude Docs, unabhängig von der Session):
- Diskussionspapier: https://claude.ai/artifact/HT3ze6YdVZ6ij7DNZLbudy
- Arbeitsdokument mit Herleitung: https://claude.ai/artifact/T9vdfrD9Lv65PERhVxvCcK
- Onepager Vorteile openknx-release.json: https://claude.ai/artifact/NtLyYWgVN7g8qbW79psRCh
