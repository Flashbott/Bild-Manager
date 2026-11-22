# Pokémon-Manager

Stand: **22.11.2026** · Version: **0.3.1** · Ziel: **Windows x64**

Der Pokémon-Manager unterstützt Julian beim Auswählen, Prüfen, Verwalten und Drucken von Pokémon-Bildern. Die Anwendung ist deutschsprachig voreingestellt, arbeitet mit einem frei wählbaren Arbeitsordner und wird als Windows-Setup verteilt.

## Schnellstart

Die aktuelle Installationsdatei liegt lokal hier:

`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\Pokemon-Manager-Setup.exe`

Nach der Installation fragt die App beim ersten Start nach dem Arbeitsordner. Dort werden die Bilddaten und die erzeugte Druckauswahl gespeichert. Es gibt keinen fest eingebauten Entwicklungsordner.

## Dokumentation

- [Zentrale Programmdokumentation](Pokemon-Manager-Programm/README.md)
- [Projekt- und Architekturdokumentation](Pokemon-Manager-Programm/docs/PROJEKTDOKUMENTATION.md)
- [Entwicklungsfahrplan und Bauplan](Pokemon-Manager-Programm/docs/ENTWICKLUNGSFAHRPLAN.md)
- [Release-Checkliste](Pokemon-Manager-Programm/docs/RELEASE-CHECKLIST.md)
- [Bedienungsanleitung für die Druckauswahl](Pokemon-Manager-Programm/Gebrauchsanweisung_Pokemon-Auswahl.html)

## Repository-Struktur

`Pokemon-Manager-Programm` enthält ausschließlich Quellcode, Tests, technische Hilfsdateien, Installationsdefinitionen, Dokumentation und die erzeugte Setup-Datei. Die lokalen Bild- und Arbeitsdaten liegen getrennt im Projektordner und gehören nicht in ein öffentliches GitHub-Repository.

Der wichtigste Entwicklungsordner ist:

`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm`

## Build

Aus dem Programmordner:

```powershell
.\Installer\build_setup.ps1
```

Der Build führt die Tests aus, erstellt die PyInstaller-Anwendung, erzeugt das deutschsprachige Inno-Setup, berechnet SHA-256 und schreibt Manifest sowie Release-Notizen nach `Release`.

Aktueller Nachweis: 8 automatisierte Tests erfolgreich, Installer-Version 0.3.1, SHA-256-Prüfsumme im Release-Manifest vermerkt. Die Datei ist derzeit nicht code-signiert.

## GitHub-Hinweis

Der lokale Projektstand ist dokumentiert und in mehreren nachvollziehbaren Commits auf `main` gesichert. Für dieses lokale Repository ist aktuell kein GitHub-Remote hinterlegt. Vor einer Veröffentlichung müssen Repository-URL, Sichtbarkeit und der Ausschluss der Bild- und Benutzerdaten ausdrücklich festgelegt werden.
