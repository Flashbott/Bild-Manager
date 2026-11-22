# Pokémon-Manager – Release-Checkliste

Diese Checkliste gilt für jede weitergegebene Setup-Datei.

## Vor dem Build

- [ ] Arbeitskopie und Änderungsgrund dokumentiert.
- [ ] `VERSION.json` enthält die Zielversion.
- [ ] README, Projektdokumentation und Fahrplan sind aktuell.
- [ ] Keine Bilder, Backups, PINs oder lokalen Konfigurationen im Programmordner eingecheckt.
- [ ] Neue oder geänderte deutsche Texte sind UTF-8-korrekt.

## Build und Tests

- [ ] `python -m unittest discover -s tests -p "test_*.py"` erfolgreich.
- [ ] `Installer\build_setup.ps1` erfolgreich.
- [ ] PyInstaller-Ausgabe wurde erzeugt.
- [ ] Inno-Setup wurde ohne Fehler erstellt.
- [ ] temporärer Buildordner `Release\dist` ist nach der Prüfung entfernt oder ausdrücklich als Buildartefakt ignoriert.

## Release-Nachweis

- [ ] `Pokemon-Manager-Setup.exe` existiert.
- [ ] `.sha256` wurde aus genau dieser Setup-Datei berechnet.
- [ ] Hash in `.sha256`, `release-manifest.json` und Release-Notizen stimmt überein.
- [ ] Version und AppId stimmen mit `VERSION.json` und `PokemonManager.iss` überein.
- [ ] Signaturstatus ist ehrlich dokumentiert.
- [ ] Installationsanleitung liegt im Release-Anleitungsordner.

## Erstlauf und Update

- [ ] Setup auf einem sauberen Windows-Benutzerkonto gestartet.
- [ ] Deutsch ist sichtbar voreingestellt.
- [ ] Erststart fragt nach einem frei wählbaren Arbeitsordner.
- [ ] `Eingang`, `S1`, `Index`, `Backups` und Protokollordner werden angelegt.
- [ ] Dateiauswahl startet im Eingangs-/Downloads-Kontext.
- [ ] Bestätigte gültige Bilder werden automatisch kopiert; Originale bleiben erhalten.
- [ ] Druckauswahl wird aktualisiert und der Druckbutton ist am Seitenende vorhanden.
- [ ] Neue Setup-Datei aktualisiert eine vorhandene Installation ohne vorherige Deinstallation.
- [ ] Arbeitsdaten und Sprache bleiben nach dem Update erhalten.

## Abschluss

- [ ] Git-Status geprüft.
- [ ] Nur Programmdateien und Dokumentation committen.
- [ ] Commit-Hash in der Projektdokumentation vermerken.
- [ ] Externes GitHub-Pushen nur nach ausdrücklicher Freigabe und mit konkretem Remote.
