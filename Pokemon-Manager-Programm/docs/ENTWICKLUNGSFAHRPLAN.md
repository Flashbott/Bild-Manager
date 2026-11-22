# Pokémon-Manager – Entwicklungsfahrplan und Bauplan

Stand: **22.11.2026**  
Ausgangspunkt: **Version 0.3.1 / Commit b66efac**

Dieses Dokument beschreibt die sinnvolle Reihenfolge für die weitere Softwareentwicklung. Es ist ein Arbeitsplan, keine automatische Freigabe für externe Dienste, Downloads, Veröffentlichungen oder irreversible Datenänderungen.

## 1. Leitbild

Julian soll Bilder mit möglichst wenigen, verständlichen Klicks auswählen und drucken können. Die Anwendung soll dabei stabil, nachvollziehbar, datensparsam und für Erwachsene wartbar bleiben.

## 2. Prioritäten

### P0 – Stabilität vor neuen Funktionen

Fehler bei Arbeitsordner, Import, Sicherung, Wiederherstellung und Druckausgabe haben Vorrang vor Komfortfunktionen.

### P1 – Kindgerechte Bedienung

Texte, Schaltflächen, Reihenfolge und Fehlermeldungen werden so gestaltet, dass sie ohne technische Vorkenntnisse verständlich sind.

### P2 – Wartbarkeit und Verteilung

Build, Tests, Dokumentation, Signierung und spätere Updates sollen reproduzierbar sein.

### P3 – Erweiterungen

Internet-Download, automatische Online-Updates und weitere Datenquellen kommen erst nach einer gesonderten fachlichen, rechtlichen und technischen Entscheidung.

## 3. Roadmap

| Zielversion | Schwerpunkt | Ergebnis | Status |
|---|---|---|---|
| 0.3.1 | Übergabefähige Basis | freier Arbeitsordner, automatische Bildübernahme, deutschsprachiges Setup, Backup/PIN, Dokumentation | erledigt |
| 0.4.x | Bedienung vereinfachen | kindgerechter Erststart-Assistent, größere Statusmeldungen, bessere Erklärung bei Fehlern, weniger doppelte Aktionen | geplant |
| 0.5.x | Stabilität erhöhen | Rechte- und Speicherprüfung, sichere Importtransaktion, bessere Protokollansicht, Testfälle für beschädigte Dateien und Abbruch | geplant |
| 0.6.x | Verteilung absichern | Code-Signatur, veröffentlichte Release-Ablage, standardisierte Prüfsummenprüfung, Installations- und Update-Test auf sauberem Benutzerkonto | geplant |
| 0.7.x | Optionale Komfortdienste | nur nach Freigabe: unterstützte Bildquellen, URL-/Lizenzprüfung, Download in den Arbeitsordner | Entscheidung offen |
| 1.0.0 | stabiler Regelbetrieb | dokumentierter Supportprozess, vollständiger Erstlauf, Update-/Restore-Probe und freigegebene Benutzeroberfläche | Ziel |

## 4. Konkreter Backlog

| ID | Aufgabe | Abnahmekriterium | Priorität |
|---|---|---|---|
| PM-UX-01 | Erststart als sichtbare Drei-Schritt-Anleitung gestalten | Kind kann Ordner wählen, Bilder wählen und Druckauswahl öffnen, ohne README zu benötigen | P1 |
| PM-UX-02 | Fehlermeldungen vereinfachen | Jede Meldung nennt Problem, nächsten Klick und ob Daten verändert wurden | P1 |
| PM-IMP-01 | Import als Transaktion absichern | Bei Abbruch bleiben Arbeitsbestand und Index unverändert; Teilkopien werden aufgeräumt | P0 |
| PM-IMP-02 | Schreibrechte und freien Speicher prüfen | Vor dem Kopieren erscheint eine verständliche Warnung mit Lösungsvorschlag | P0 |
| PM-BACK-01 | Wiederherstellung mit Testdaten wiederholen | Sicherung wird verifiziert, aktuelle Daten werden vorab gesichert und Ergebnis wird protokolliert | P0 |
| PM-TEST-01 | GUI- und Installer-Erstlauf automatisieren | frischer Benutzerzustand, Ordnerwahl, Import, Update und Abbruch sind reproduzierbar geprüft | P0 |
| PM-REL-01 | Code-Signatur beschaffen | Windows zeigt beim normalen Erststart keinen unbekannten Herausgeber wegen fehlender Signatur | P2 |
| PM-REL-02 | GitHub-Repository einrichten | Remote, Sichtbarkeit, Branchregel und Ausschluss lokaler Bilddaten sind dokumentiert und freigegeben | P2 |
| PM-NET-01 | Internet-Download fachlich entscheiden | Quelle, Nutzungsbedingungen, Dateiformate, Fehlerverhalten und Datenschutz sind vor Implementierung geklärt | P3 |

## 5. Bauplan für jede Änderung

1. **Auftrag klären:** Problem, Zielgruppe, betroffene Dateien und Abgrenzung notieren.
2. **Bestand prüfen:** README, Architektur, Tests, UI-Review und Versionsstand lesen.
3. **Schnittstelle entwerfen:** Bedienwortlaut, Datenfluss, Fehlerfälle und Rückweg festlegen.
4. **Ändern:** kleine, nachvollziehbare Änderung im Programmordner; Benutzerdaten bleiben unangetastet.
5. **Testen:** Unit-Tests, UTF-8-Prüfung, statische Suche nach festen Pfaden und – bei UI-Änderungen – gerenderte Sichtprüfung.
6. **Paketieren:** Version erhöhen, Build-Skript ausführen, Setup erzeugen.
7. **Release prüfen:** Hash, Manifest, Release-Notizen, README und Installationsinhalt vergleichen.
8. **Dokumentieren:** Änderungsgrund, Teststatus, offene Punkte und Rollback-Möglichkeit festhalten.
9. **Versionieren:** nur Programmdateien und Dokumentation committen; Bilddaten, Backups und lokale Arbeitsstände ausgeschlossen lassen.
10. **Veröffentlichen:** erst nach ausdrücklicher Freigabe an ein konkretes GitHub-Remote pushen.

## 6. Definition of Done

Eine Version gilt erst dann als fertig, wenn alle Punkte erfüllt sind:

- gewünschtes Verhalten ist im Quellcode umgesetzt;
- deutsche Texte sind verständlich und UTF-8-korrekt;
- relevante Tests laufen erfolgreich;
- Fehler- und Abbruchpfade sind geprüft;
- Setup lässt sich erzeugen;
- Setup-Version, `VERSION.json`, Release-Notizen und Manifest stimmen überein;
- SHA-256 wurde aus der fertigen Setup-Datei berechnet;
- Installations- und Updateverhalten sind auf einem sauberen Testkonto geprüft oder ausdrücklich als offen markiert;
- Benutzerdaten werden nicht in den Programmordner kopiert;
- Dokumentation und Roadmap sind aktualisiert;
- Commit enthält keine lokalen Bilddateien, Backups oder geheimen Einstellungen.

## 7. Technische Entscheidungen, die vor Erweiterungen geklärt werden müssen

### GitHub

Das öffentliche Repository [Flashbott/Bild-Manager](https://github.com/Flashbott/Bild-Manager) ist eingerichtet. Der aktuelle Stand liegt auf `main`. Vor jedem weiteren Push bleiben die Prüfung des Git-Status und der Ausschluss von Bilddaten, Backups, lokalen Konfigurationen und Build-Artefakten verpflichtend.

### Code-Signatur

Für einen vertrauenswürdigeren Windows-Erststart wird ein Authenticode-Zertifikat benötigt. Kosten, Zertifikatsinhaber, Signaturprozess und Schlüsselaufbewahrung sind offen.

### Internet-Download

Ein Download aus dem Internet darf nicht einfach als allgemeine Websuche umgesetzt werden. Vorher müssen erlaubte Quellen, Urheberrecht, Dateigrößen, Malware-Risiken, URL-Validierung, Abbruch und Speicherung geklärt werden.

### Automatische Updates

Der aktuelle Weg ist ein manuelles Setup mit gleicher AppId. Ein Online-Update-Check ist eine neue externe Schnittstelle und braucht deshalb eine eigene Freigabe, Datenschutzbetrachtung und sichere Signaturprüfung.

## 8. Empfohlene nächste drei Schritte

1. **PM-TEST-01:** Erstlauf des aktuellen Installers auf einem sauberen Benutzerkonto durchführen.
2. **PM-UX-01:** Die erste Oberfläche mit dem Kind testen und nur die drei wirklich benötigten Aktionen sichtbar machen.
3. **PM-REL-02:** GitHub-Repository weiter pflegen und für künftige Releases eine nachvollziehbare Release-Ablage einrichten.
