# Pokémon-Manager

Die vollständige, langfristige Projekt- und Bedienungsdokumentation steht in:

`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\README.md`

Die App steuert Julians lokalen Pokémon-Arbeitsablauf:

1. Bilddateien werden wie gewohnt im Browser gesucht und gespeichert.
2. Über **Bilder auswählen …** werden mehrere Dateien ausgewählt. Der Dialog startet standardmäßig im Downloads-Ordner. Nach dem Bestätigen prüft die App die Auswahl und kopiert gültige neue Bilder automatisch in den Arbeitsbestand. Originale werden nicht verschoben oder gelöscht.
3. Die Importprüfung zeigt Format, Lesbarkeit, Hash, mögliche Dubletten und den Übernahmestatus.
4. **Druckauswahl aktualisieren** erzeugt Index und HTML-Auswahlseite.
5. **Auswahlseite öffnen** öffnet die gerenderte Druck- und Auswahlansicht im Browser.

Der Arbeitsbestand liegt technisch weiterhin im Unterordner `S1`. Dieser interne Name
wird in der Oberfläche nicht mehr verwendet, damit der tägliche Ablauf verständlich bleibt.

Die App lädt selbst keine Internetdateien herunter, verschiebt keine Originale und löscht keine Bilder.
Die Datenablage wird beim ersten Start gewählt und danach in `%APPDATA%\PokemonManager\config.json` gespeichert.
Deutsch ist die Standardsprache der gesamten Anwendung. Über das Dropdown **Sprache** kann zusätzlich Englisch ausgewählt werden; die Druck- und Auswahlseite bleibt für den Schulablauf deutsch.

Vor jeder Änderung am Arbeitsbestand, am Index oder an der HTML-Auswahl wird automatisch eine geprüfte Sicherung unter `Backups` erstellt. Standardmäßig werden die fünf neuesten Sicherungen behalten. **Wiederherstellen …** liegt im Zahnrad-Menü und kann nach Eingabe der Administrator-PIN einen Sicherungsstand zurückspielen.

Die Administrator-PIN ist vierstellig, wird nicht im Klartext gespeichert und schützt nur sensible Verwaltungsaktionen. Der normale Bildimport und die Druckauswahl benötigen keine PIN. Der Eigentümer sollte die PIN vor der Übergabe an Julian einmalig über **⚙ Einstellungen und Verwaltung → Administration …** einrichten. Dort kann die PIN bzw. das lokale App-Passwort später auch geändert werden.

Die selten benötigten Funktionen **Arbeitsordner ändern**, **Eingangsordner öffnen**, **Sicherung erstellen**, **Wiederherstellen**, **Administration**, **Protokoll öffnen** und **Anleitung öffnen** befinden sich gesammelt hinter dem Zahnrad oben rechts.

## Installation

1. `Pokemon-Manager-Setup.exe` auf Julians Rechner kopieren und starten.
2. Die Installation erfolgt pro Benutzer und benötigt normalerweise keine Administratorrechte.
3. Beim ersten Start direkt einen eigenen Arbeitsordner auswählen oder neu anlegen. Es ist kein fester Julian-Pfad voreingestellt.
4. Danach kann die App über das Startmenü geöffnet werden.

Die App legt fehlende Arbeitsordner wie `Eingang`, `S1`, `Index`, `Archiv`, `Protokolle` und `Backups` selbstständig an.

Für spätere Programmänderungen wird die Versionsnummer in
`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\VERSION.json` erhöht und anschließend
`C:\Codex\Julian\Pokémon\Pokemon-Manager-Programm\Installer\build_setup.ps1` ausgeführt. Die daraus entstehende
`Pokemon-Manager-Setup.exe` ist zugleich Installations- und Update-Datei.

Der Build erzeugt außerdem eine SHA-256-Datei, ein Release-Manifest und Release-Notizen. Die App lädt keine Updates automatisch aus dem Internet.
