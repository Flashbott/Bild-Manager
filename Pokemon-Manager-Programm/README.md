# Pokémon-Manager – zentrale Projektdokumentation

Stand: 22.11.2026  
Aktuelle Programmversion: 0.3.1

Diese README ist die zentrale Nachschlagequelle für den Pokémon-Manager und den dazugehörigen Druckablauf. Sie beschreibt sowohl die Bedienung für Julian als auch die spätere Pflege und Aktualisierung durch den Entwickler.

## 1. Zweck

Der Pokémon-Manager unterstützt Julians lokalen Arbeitsablauf:

1. Bilddateien werden wie gewohnt im Browser gesucht und gespeichert.
2. Mehrere gespeicherte Bilder werden im Manager ausgewählt.
3. Die App prüft Dateiformat, Lesbarkeit, Bildgröße und mögliche Duplikate.
4. Nach einer sichtbaren Prüfung und Bestätigung werden neue Bilder in den **Arbeitsbestand** kopiert.
5. **Druckauswahl aktualisieren** erzeugt den Index und die HTML-Auswahlseite neu.
6. **Auswahlseite öffnen** öffnet die gerenderte Auswahl- und Druckansicht im Browser.

In der Benutzeroberfläche wird der technische Unterordner `S1` verständlich als
**Arbeitsbestand** bezeichnet. Dadurch muss Julian keinen internen Ordnernamen kennen.

Vor jeder Änderung am Arbeitsbestand, am `Index` oder an der HTML-Auswahl erzeugt die App automatisch eine geprüfte lokale Sicherung. Es werden maximal fünf Sicherungsstände behalten.

Die App lädt keine Dateien selbstständig aus dem Internet herunter. Die Internetrecherche und das Speichern der Bilder bleiben bewusst im Browser. Die App verschiebt keine Originale und löscht keine Bilder.

## 2. Installation auf Julians Rechner

Für die Installation wird nur diese Datei verschickt:

    C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\Pokemon-Manager-Setup.exe

Vorgehen:

1. Setup-Datei auf Julians Rechner kopieren.
2. Setup per Doppelklick starten.
3. Die Installation erfolgt pro Benutzer und benötigt normalerweise keine Administratorrechte.
4. Pokémon-Manager über das Startmenü öffnen.
5. Beim ersten Start direkt den gewünschten Arbeitsordner auswählen oder anlegen. Es ist kein fester Julian-Pfad voreingestellt.

Das Setup enthält die Python-Laufzeit, die benötigten Bibliotheken, die App und den Generator. Python muss auf Julians Rechner nicht separat installiert werden.

Das Setup enthält nicht Julians bisherige Bildsammlung. Wenn Julian mit einem leeren Bestand startet, ist das beabsichtigt. Die App legt fehlende Arbeitsordner selbst an.

Die Installationsdatei enthält außerdem die Bedienungsanleitung und diese README. Der ausgewählte Arbeitsordner bleibt eine separate Datenablage und muss bei einem neuen Rechner bewusst gewählt oder neu aufgebaut werden.

## 3. Sprache

Deutsch ist die Standardsprache der Anwendung und des Installationsprogramms.

Oben rechts in der App befindet sich das Dropdown **Sprache**. Dort kann zusätzlich Englisch ausgewählt werden. Die Auswahl wird in folgender Datei gespeichert:

    %APPDATA%\PokemonManager\config.json

Die Druck- und Auswahlseite bleibt für den schulischen Ablauf deutsch.

## 4. Bedienung für Julian

### Neue Bilder auswählen und übernehmen

1. Bild im Browser speichern, zum Beispiel im Ordner `Downloads`.
2. Pokémon-Manager öffnen.
3. **Bilder auswählen …** anklicken.
4. Eine oder mehrere Bilddateien auswählen.
5. In der Importprüfung die Vorschau und den Status kontrollieren.
6. Nach dem Bestätigen werden gültige neue Bilder automatisch in den Arbeitsbestand kopiert.
7. Danach **Druckauswahl aktualisieren** anklicken.
8. Mit **Auswahlseite öffnen** die Druckseite öffnen.

Unterstützte Bildformate sind PNG, JPG, JPEG, GIF, BMP und WebP.

Die App erkennt exakte Duplikate über einen SHA-256-Hash. Originaldateien bleiben am ursprünglichen Speicherort erhalten.

### Sicherungen und Wiederherstellung

- **Sicherung erstellen** legt jederzeit einen geprüften Sicherungsstand an.
- Vor der automatischen Übernahme, vor der Aktualisierung der Druckauswahl und vor einer Wiederherstellung wird automatisch gesichert.
- **Wiederherstellen …** zeigt die letzten fünf gültigen Sicherungen mit Zeitpunkt, Anlass, Dateizahl und Größe.
- Die Wiederherstellung schützt die aktuelle Datenlage zusätzlich durch eine Vorab-Sicherung.
- Sicherungen enthalten `S1`, `Index`, `Pokemon-Bilder-Auswahl.html` sowie ein Manifest mit SHA-256-Prüfsummen und einer unkritischen Konfigurationskopie.

### Administrator-PIN

Beim ersten Start kann der Eigentümer eine vierstellige Administrator-PIN einrichten. Sie wird nicht im Klartext gespeichert und gilt nur für dieses Windows-Benutzerkonto. Die PIN ist nur für geschützte Verwaltungsaktionen erforderlich:

- Arbeitsordner wechseln;
- Sicherung wiederherstellen;
- Administrator-PIN verwalten.

Der normale Bildimport, die Prüfung, die Übernahme in den Arbeitsbestand, die Aktualisierung der Druckauswahl und die Druckauswahl bleiben ohne PIN nutzbar. Die PIN bzw. das lokale App-Passwort kann später über **⚙ Einstellungen und Verwaltung → Administration …** geändert werden. Vor der Übergabe an Julian sollte der Eigentümer die PIN einmalig einrichten und sicher aufbewahren.

### Druckseite bedienen

Auf der gerenderten Auswahlseite können einzelne Pokémon über die Checkbox ausgewählt werden. Die Seite bietet unter anderem:

- **Alle auswählen**
- **Nur neue auswählen**
- **Auswahl löschen**
- Filter für alle oder nur neue Bilder
- Druckvorschau
- ganz unten **Druckauftrag starten**

Vor dem Druck die vollständige Druckvorschau prüfen. Die Ausgabe ist für A4-Hochformat mit zwei Spalten und drei Zeilen, also sechs Bildern pro Seite, ausgelegt.

## 5. Arbeitsordner und Zuständigkeiten

Der beim ersten Start gewählte Arbeitsordner ist die Datenablage. Dort speichert die App Bilddateien, Druckauswahl, Index, Protokolle und automatische Sicherungen. Bestehende Bilder werden bei der Auswahl eines Ordners nicht gelöscht. In der Entwicklungsumgebung lautet der aktuelle Pfad:

    C:\Codex\Julian\Pokémon

Die App legt folgende Ordner an:

| Ordner | Zweck |
|---|---|
| `Eingang` | optionaler Sammelordner für neue Bilder |
| `S1` | technischer Unterordner für den führenden Bildbestand; in der App **Arbeitsbestand** |
| `Index` | technischer und lesbarer Bildindex |
| `Archiv` | allgemeine Projektablage |
| `Protokolle` | JSONL-Protokoll der Manager-Aktionen |
| `Backups` | automatisch verwaltete, geprüfte Sicherungsstände; standardmäßig fünf |
| `Hilfsdateien` | Generator und technische Hilfsdateien |
| `Release` | Setup- und Build-Ausgaben in der Entwicklungsumgebung |

Wichtige Ergebnisdateien:

    <gewählter Arbeitsordner>\Pokemon-Bilder-Auswahl.html
    <gewählter Arbeitsordner>\Index\pokemon-index.md
    <gewählter Arbeitsordner>\Index\pokemon-index.json

Die HTML-Datei sollte nicht von Hand bearbeitet werden. Änderungen am Bildbestand werden über **Bilder auswählen …** eingepflegt und anschließend mit **Druckauswahl aktualisieren** in die Auswahlseite übernommen.

## 6. Spätere Updates der App

Ein separates Updateprogramm ist aktuell nicht notwendig. Das neue Setup ist zugleich die Update-Datei.

### Update erstellen

1. Änderungen im App-Code durchführen.
2. Die zentrale Versionsdatei erhöhen:

       C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\VERSION.json

   Beispiel: `0.3.1` → `0.4.0`.
3. Optional die festgelegten Build-Abhängigkeiten installieren:

       C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Installer\build_setup.ps1 -InstallDependencies

4. Den Build ausführen:

       C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Installer\build_setup.ps1

5. Die neue Datei entsteht hier:

       C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\Pokemon-Manager-Setup.exe

6. Vor der Übergabe Prüfsumme und Manifest prüfen. Für Julian genügt anschließend die neue Setup-Datei; die Prüfsummendatei kann zur Kontrolle mitgegeben werden.

### Update installieren

1. Pokémon-Manager schließen.
2. Neue Setup-Datei per Doppelklick starten.
3. Die alte Version nicht vorher deinstallieren.
4. Nach Abschluss die App über das Startmenü starten.

Die Installationskennung und der Installationspfad bleiben gleich. Dadurch ersetzt das Setup die Programmdateien und erhält normalerweise:

- Bilder und Index im gewählten Arbeitsordner;
- Sprache und Projektpfad in `%APPDATA%\PokemonManager\config.json`;
- Protokolle im Ordner `Protokolle`.

Die gleiche Inno-Setup-AppId bleibt über Versionen erhalten. Dadurch ist das Setup als manuelle Update-Datei verwendbar. Die App prüft weiterhin nicht online auf neue Versionen und lädt keine Updates automatisch herunter.

Nicht erforderlich für ein Update sind Python, die Build-Werkzeuge, der Ordner `Release\dist` und die Dateien `*.spec` oder `*.iss`.

### Release-Sicherheit

Der Build erzeugt zusätzlich:

    C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\Pokemon-Manager-Setup.exe.sha256
    C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\release-manifest.json
    C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Release\RELEASE_NOTES_0.3.1.md

Die Version ist noch nicht code-signiert. Die SHA-256-Prüfsumme dokumentiert die Integrität; eine spätere Authenticode-Signierung kann ergänzt werden, ohne den Updateablauf grundsätzlich zu ändern.

## 7. Technische Hauptdateien

| Datei | Aufgabe |
|---|---|
| `App\pokemon_manager.py` | deutsche Desktop-Oberfläche, Sprachwahl, Importprüfung und Aktionen |
| `App\pokemon_engine.py` | Verbindung zwischen App und Generator |
| `Hilfsdateien\pokemon_auswahl_aktualisieren.py` | Index- und HTML-Erzeugung |
| `Installer\PokemonManager.spec` | PyInstaller-Paketdefinition |
| `Installer\PokemonManager.iss` | deutschsprachige Inno-Setup-Definition |
| `Installer\build_setup.ps1` | Build, Tests, Setup, Prüfsumme, Manifest und Release-Notizen |
| `Installer\requirements-build.txt` | festgelegte Build-Versionen von Pillow und PyInstaller |
| `VERSION.json` | zentrale Versions- und Schemaangaben |
| `App\pokemon_backup.py` | Sicherungen, Prüfsummen, Aufbewahrung und Wiederherstellung |
| `App\pokemon_security.py` | lokale PIN-Richtlinie mit Hashing und Windows-DPAPI |
| `App\README.md` | kurze technische App-Anleitung; diese Datei ist die zentrale Gesamtdokumentation |

## 8. Aktueller Prüfstand

Stand 22.11.2026:

- `VERSION.json` steht auf `0.3.1`; der Quelltext ist syntaxgeprüft.
- Acht automatisierte Tests laufen erfolgreich: Sicherung/Wiederherstellung, Aufbewahrung von fünf Ständen, PIN, Konfiguration, freie Erststart-Ordnerauswahl, Generator/Druckbutton und UTF-8.
- Die gepackte Windows-Anwendung startet sichtbar mit deutscher Oberfläche, Version `0.3.1`, freier Erststart-Ordnerauswahl, Sicherungs- und Administrationsbereich.
- Der aktuelle Projektbestand enthält 52 Bilddateien in `S1`.
- Die vorhandene HTML-Auswahlseite enthält weiterhin den unteren Button **Druckauftrag starten**.
- Der lokale Git-Stand wird nach der Abschlussprüfung als neuer Commit auf Branch `main` gesichert; Bilddaten, Backups, Index und Build-Ausgaben sind nicht versioniert.
- Die neue PyInstaller-Ausgabe liegt unter `Pokemon-Manager-Programm\Release\dist\Pokemon-Manager`.

Der Installer ist nicht code-signiert; Windows kann beim ersten Start deshalb einen SmartScreen-Hinweis anzeigen. Ein Erstlauf mit Julians tatsächlichem Windows-Benutzerkonto und Drucker bleibt zusätzlich sinnvoll.

## 9. Änderungsverlauf

### Version 0.3.1 · 22.11.2026

- Programmdateien in einem eigenen Ordner `Pokemon-Manager-Programm` gebündelt und Benutzerdaten davon getrennt;
- festen Entwicklungsordner entfernt; der Arbeitsordner wird beim ersten Start frei ausgewählt oder neu angelegt;
- App-Bedienelemente bleiben bis zur Auswahl eines Arbeitsordners geschützt deaktiviert;
- Erklärung des Arbeitsordners und der dort angelegten Unterordner verbessert;
- Build- und Release-Nachweise auf den aktuellen Installer aktualisiert.

### Version 0.3.0 · 22.11.2026

- automatische, geprüfte Sicherungen mit Aufbewahrung von fünf Ständen ergänzt;
- Wiederherstellungsdialog und PIN-Schutz für sensible Verwaltungsaktionen ergänzt;
- atomare Ausgaben für Index, JSON und HTML ergänzt;
- gebündelten Generator in der veröffentlichten App priorisiert;
- Build auf zentrale Version, feste Abhängigkeiten, Tests, SHA-256 und Release-Manifest umgestellt;
- README und Anleitung in das Installationspaket aufgenommen.

### Version 0.2.0 · 22.11.2026

- Spracharchitektur mit Deutsch als Standardsprache ergänzt.
- Optionalen Sprachwechsel auf Englisch ergänzt.
- Spracheinstellung dauerhaft gespeichert.
- Installer-Assistent auf Deutsch festgelegt.
- Updateablauf und zentrale Bedienungsdokumentation ergänzt.

### Version 0.1.0 · 22.11.2026

- Erste installierbare Windows-Version des Pokémon-Managers.
- Importprüfung, Duplikaterkennung, Bilderübernahme und Aktualisierung der Druckauswahl umgesetzt.
- HTML-Druckseite mit Druckvorschau und Druckbutton angebunden.
