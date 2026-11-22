# Pokémon-Manager – Projekt- und Architekturdokumentation

Stand: **22.11.2026**  
Version: **0.3.1**  
Zielplattform: **Windows x64**  
Projektordner: `C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm`

## 1. Zweck und Zielgruppe

Der Pokémon-Manager macht aus gespeicherten Pokémon-Bildern eine geprüfte und druckbare Auswahl. Julian soll möglichst wenige Klicks benötigen und keine technischen Ordnernamen kennen müssen.

Die Oberfläche ist deshalb auf Deutsch voreingestellt, nutzt einfache Begriffe und zeigt den technischen Ordner `S1` im Alltag als **Arbeitsbestand** an.

## 2. Funktionsumfang der Version 0.3.1

- frei wählbarer Arbeitsordner beim ersten Start; kein fester Julian-Pfad;
- automatische Anlage der benötigten Unterordner;
- Standardsprache Deutsch, optional Englisch;
- Auswahl mehrerer Bilder direkt aus dem Downloads-Ordner;
- Prüfung von Format, Lesbarkeit, Bildgröße und Duplikaten;
- automatische Kopie gültiger neuer Bilder in den Arbeitsbestand nach der Dateiauswahl;
- Originaldateien bleiben am ursprünglichen Ort erhalten;
- Aktualisierung von Index und Druckauswahl über eine eigene Schaltfläche;
- gerenderte HTML-Druckseite mit Checkboxen, Druckvorschau und dem Button **Druckauftrag starten** am Seitenende;
- Zahnrad-Menü für seltene Verwaltungsfunktionen;
- Administrator-PIN für Ordnerwechsel, Wiederherstellung und PIN-Verwaltung;
- geprüfte Sicherungen mit maximal fünf Ständen;
- manuelles Update durch erneutes Ausführen des neuen Setups;
- SHA-256-Prüfsumme, Release-Manifest und Release-Notizen.

## 3. Bewusste Abgrenzungen

Die App lädt in Version 0.3.1 keine Bilder selbstständig aus dem Internet herunter. Die Suche und das Speichern aus dem Browser bleiben getrennt. Das schützt den einfachen Bedienablauf und vermeidet ungeklärte Quellen-, Lizenz- und Webseitenabhängigkeiten.

Außerdem gibt es derzeit keinen automatischen Online-Update-Check und keine automatische Übertragung auf ein GitHub-Repository. Updates werden bewusst als manuelle Setup-Datei verteilt.

## 4. Bedienablauf

### Erststart

1. Setup installieren und Pokémon-Manager starten.
2. Einen vorhandenen Ordner auswählen oder einen neuen Ordner anlegen.
3. Die App legt darin `Eingang`, `S1`, `Index`, `Archiv`, `Protokolle`, `Backups` und technische Hilfsordner an.
4. Die normalen Arbeitsfunktionen werden erst nach dieser Auswahl freigeschaltet.

### Bilder bis zum Druck

```text
Browser/Downloads
        │  Bilder auswählen …
        ▼
Importprüfung und Duplikaterkennung
        │  gültige neue Dateien automatisch kopieren
        ▼
Arbeitsbestand (technisch: S1)
        │  Druckauswahl aktualisieren
        ▼
Index + Pokemon-Bilder-Auswahl.html
        │  Auswahlseite öffnen
        ▼
Druckauswahl → Druckvorschau → Druckauftrag starten
```

## 5. Architektur

| Baustein | Datei/Ort | Verantwortung |
|---|---|---|
| Oberfläche | `App/pokemon_manager.py` | Tkinter-Fenster, Sprache, Dateiauswahl, Status, Menüs und Aktionen |
| Bild- und Projektlogik | `App/pokemon_manager.py` | Validierung, Hashes, Duplikate, Zielnamen, Arbeitsordner |
| Generator-Brücke | `App/pokemon_engine.py` | lädt den Generator aus dem Paket oder aus dem Projektordner |
| Index- und HTML-Generator | `Hilfsdateien/pokemon_auswahl_aktualisieren.py` | erzeugt Markdown-Index, JSON-Index und Druckauswahl |
| Sicherungen | `App/pokemon_backup.py` | Snapshot, Manifest, SHA-256-Prüfung, Wiederherstellung und Aufbewahrung |
| Sicherheit | `App/pokemon_security.py` | vierstellige PIN, Hashing und Windows-DPAPI-Schutz |
| Tests | `tests/` | Sicherung, PIN, Konfiguration, Generator und UTF-8 |
| Paketierung | `Installer/PokemonManager.spec` | PyInstaller-Bundle inklusive Laufzeit und Generator |
| Setup | `Installer/PokemonManager.iss` | deutschsprachiges, per Benutzer installierbares Inno-Setup |
| Build | `Installer/build_setup.ps1` | Tests, Paketierung, Setup, Prüfsumme, Manifest und Release-Notizen |

## 6. Datenablage und Verträge

### Programmablage

`Pokemon-Manager-Programm` enthält Quellcode, Tests, technische Hilfsdateien, Builddefinitionen und Dokumentation. Dort liegen keine Pokémon-Bilddaten.

Die veröffentlichte Datei ist:

`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\Pokemon-Manager-Setup.exe`

Zusätzlich werden im `Release`-Ordner Prüfsumme, Manifest, Release-Notizen und eine Kopie der Anleitungen abgelegt. Der temporäre Ordner `Release\dist` wird nur während des Builds benötigt und nach der Prüfung entfernt.

### Gewählter Arbeitsordner

| Ordner/Datei | Bedeutung |
|---|---|
| `Eingang` | optionaler Sammelordner; der Dateidialog startet dort, sofern vorhanden |
| `S1` | führender Bildbestand, in der Oberfläche **Arbeitsbestand** |
| `Index` | lesbarer Markdown- und maschinenlesbarer JSON-Index |
| `Pokemon-Bilder-Auswahl.html` | gerenderte Auswahl- und Druckseite |
| `Archiv` | archivierte ältere Ausgaben |
| `Protokolle` | lokale JSONL-Aktionsprotokolle |
| `Backups` | geprüfte Sicherungsstände, standardmäßig maximal fünf |
| `Hilfsdateien` | technische projektbezogene Hilfsablage |

### Benutzereinstellungen

Sprache und zuletzt gewählter Arbeitsordner werden pro Windows-Benutzer in `%APPDATA%\PokemonManager\config.json` gespeichert. Ein fehlender Konfigurationsstand führt nicht zu einem Entwicklungsordner, sondern zum Erststart-Dialog.

## 7. Sicherheit und Datenintegrität

- Die App kopiert ausgewählte Originale; sie verschiebt oder löscht die Browserdateien nicht.
- Duplikate werden über SHA-256 erkannt.
- Vor Übernahme, Druckauswahl-Aktualisierung und Wiederherstellung wird eine Sicherung erstellt.
- Sicherungen enthalten die relevanten Arbeitsdaten und ein Manifest mit Prüfsummen.
- Wiederherstellung erfolgt über temporäre Verzeichnisse und eine zusätzliche Vorab-Sicherung.
- Die PIN wird nicht im Klartext gespeichert; unter Windows wird DPAPI genutzt.
- Der Installer ist noch nicht Authenticode-signiert. Deshalb kann Windows beim ersten Start einen SmartScreen-Hinweis anzeigen.

## 8. Build-, Update- und Releaseprozess

1. Änderung im Quellcode oder in der Dokumentation durchführen.
2. `VERSION.json` prüfen und bei einer Funktionsänderung erhöhen.
3. `python -m unittest discover -s tests -p "test_*.py"` ausführen.
4. `Installer\build_setup.ps1` ausführen.
5. Setup, SHA-256-Datei, Manifest und Release-Notizen prüfen.
6. Bei einem sauberen Windows-Testkonto installieren und Erststart mit frei wählbarem Arbeitsordner prüfen.
7. Erst danach den lokalen Git-Commit erstellen und – falls später ein Remote freigegeben ist – den Commit veröffentlichen.

Für Julian genügt beim Update die neue Datei `Pokemon-Manager-Setup.exe`. Die gleiche Inno-Setup-AppId ersetzt die Programmdateien; Arbeitsordner, Bilder, Backups und Sprache bleiben getrennt erhalten.

## 9. Qualitätssicherung 0.3.1

Nachgewiesen:

- 8 automatisierte Tests erfolgreich;
- Python-Syntax und UTF-8-Dokumente geprüft;
- PyInstaller-Build erfolgreich;
- Inno-Setup-Build erfolgreich;
- SHA-256 aus Setup, Prüfsummendatei, Manifest und Release-Notizen stimmt überein;
- Programmordner enthält keine Pokémon-Bilddateien;
- Arbeitsdaten liegen weiterhin getrennt im Projektordner.

Offen bzw. nicht Bestandteil des lokalen Abschlusses:

- Erstinstallation auf Julians tatsächlichem Rechner und Drucker;
- Authenticode-Signatur;
- Pflege des GitHub-Repositorys und Veröffentlichung weiterer Releases;
- Entscheidung über eine rechtssichere Internet-Download-Funktion.

## 10. Änderungsnachweis

| Version/Commit | Inhalt |
|---|---|
| `0.1.0` | erste installierbare Windows-Version, Importprüfung und Druckauswahl |
| `0.2.0` | deutsche Standardsprache, optionale Sprache, Update- und README-Grundlage |
| `0.3.0` | Backups, PIN, atomare Ausgaben, feste Build- und Release-Nachweise |
| `0.3.1` / `b66efac` | eigener Programmordner, freie Erststart-Ordnerauswahl, automatische Übernahme und Dokumentationsstand |

## 11. Pflegegrundsätze

- Fachliche Änderungen zuerst in der Bedienlogik und im UI-Review beschreiben.
- Technische Ordnernamen nicht ohne Übersetzung in die Kinderoberfläche übernehmen.
- Jede Änderung braucht mindestens einen passenden Test oder eine dokumentierte Begründung, warum kein Test möglich ist.
- Originalquellen und Benutzerdaten nicht in den Programmordner oder ein öffentliches Repository kopieren.
- Eine Release-Datei erst weitergeben, wenn Version, Build, Hash, Manifest und Anleitung zusammenpassen.
