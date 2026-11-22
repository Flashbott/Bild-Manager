# Gebrauchsanweisung: Pokémon-Auswahl und Druck

Stand: 22.11.2026

## Zweck

Mit der Auswahlseite können Pokémon-Bilder aus dem Arbeitsbestand angesehen, einzeln ausgewählt und als Druckbogen ausgegeben werden. Der Arbeitsbestand liegt technisch im Unterordner `S1`.

Die Druckseite ist fest vorgegeben:

- A4-Hochformat
- zwei Spalten
- drei Zeilen
- sechs Bilder pro Seite
- proportional verkleinerte und zentrierte Bilder

## Schnellablauf

1. Neue Bilddateien im Browser speichern.
2. Im Pokémon-Manager **Bilder auswählen …** wählen und die Bilder prüfen.
3. Nach dem Bestätigen werden gültige neue Bilder automatisch in den Arbeitsbestand kopiert. Danach **Druckauswahl aktualisieren** wählen.
4. **Auswahlseite öffnen** wählen.
5. Bei den gewünschten Pokémon den Haken setzen.
6. Die Druckvorschau prüfen.
7. Ganz unten auf **Druckauftrag starten** klicken.

Vor Übernahme und Aktualisierung erstellt der Manager automatisch eine geprüfte Sicherung. Über **Sicherung erstellen** kann zusätzlich jederzeit manuell gesichert werden. Die normale Bildauswahl benötigt keine PIN; nur Ordnerwechsel, Administration und Wiederherstellung sind geschützt.

## Die Auswahlseite bedienen

### Kacheln

Jedes aktive Pokémon wird als eigene Kachel mit Bild, Namen und Checkbox angezeigt.

- Haken setzen: Bild für den Druck auswählen.
- Haken entfernen: Bild aus dem Druck herausnehmen.
- Blaue Umrandung: Das Bild ist ausgewählt.
- Grünes Kennzeichen **Neu**: Das Bild wurde beim letzten Aktualisierungslauf neu gefunden.

### Schaltflächen

- **Alle auswählen**: Wählt alle vorhandenen Pokémon aus.
- **Nur neue auswählen**: Wählt nur die mit **Neu** gekennzeichneten Bilder aus.
- **Auswahl löschen**: Entfernt alle Haken.
- **Ausgewählte Pokémon drucken**: Öffnet den Druckdialog mit ausschließlich den ausgewählten Bildern.

### Filter

- **Alle anzeigen**: Zeigt alle aktiven Pokémon.
- **Nur neue anzeigen**: Zeigt nur die beim letzten Aktualisierungslauf neu gefundenen Pokémon.

Der Filter ändert nur die Anzeige. Bereits gesetzte Haken bleiben erhalten.

## Neue Bilder ergänzen

Die technische Bildquelle des Arbeitsbestands ist:

    C:\Codex\Julian\Pokémon\S1

Unterstützte Bildformate:

- PNG
- JPG und JPEG
- GIF
- BMP
- WebP

Nach dem Ablegen neuer Bilder muss die Auswahlseite aktualisiert werden. Dafür genügt die Schaltfläche:

    Druckauswahl aktualisieren

Beim Aktualisieren werden:

1. alle Bilddateien im Arbeitsbestand (`S1`) eingelesen;
2. neue Dateien in den Index aufgenommen;
3. neue Einträge mit Neu markiert;
4. Umbenennungen über den SHA-256-Bildhash erkannt;
5. exakte Dubletten als zweite Kachel ausgeblendet;
6. die Auswahl-HTML neu erzeugt.

Die Originalbilder im Arbeitsbestand (`S1`) werden nicht verschoben, umbenannt oder gelöscht.

## Umbenennen von Dateien

Wenn eine Bilddatei umbenannt wird und der Bildinhalt gleich bleibt, erkennt der Generator die Änderung über den SHA-256-Hash. Nach **Druckauswahl aktualisieren** zeigt die HTML auf den neuen Dateinamen.

Beispiel:

    Tauboga.webp → Duselgur.webp

Der automatisch erzeugte Anzeigename wird ebenfalls angepasst. Ein im Markdown-Index bewusst gepflegter eigener Anzeigename bleibt erhalten.

## Indexdateien

### Führender Markdown-Index

    C:\Codex\Julian\Pokémon\Index\pokemon-index.md

Diese Datei ist die lesbare Übersicht mit Anzeigename, Dateipfad, Status, Neu-Kennzeichnung, Reihenfolge und SHA-256-Hash.

### Technischer JSON-Index

    C:\Codex\Julian\Pokémon\Index\pokemon-index.json

Diese Datei wird vom Generator für die technische Verarbeitung erzeugt.

### Aktualisierungsgenerator

    C:\Codex\Julian\Pokémon\Hilfsdateien\pokemon_auswahl_aktualisieren.py

Die HTML sollte nicht von Hand bearbeitet werden. Änderungen an Bildern oder Namen werden über den Arbeitsbestand (`S1`) und den Index eingepflegt und danach durch **Druckauswahl aktualisieren** neu erzeugt.

## Drucken

Im Druckdialog nach Möglichkeit einstellen:

- Papierformat: A4
- Ausrichtung: Hochformat
- Skalierung: 100 Prozent oder tatsächliche Größe
- Kopf- und Fußzeilen: deaktivieren, falls der Druckdialog diese anbietet

Die letzte Seite bleibt im 2×3-Raster. Nicht belegte Felder bleiben leer.

## Fehlerbehebung

### Ein neues Bild erscheint nicht

Prüfen:

1. Liegt die Datei direkt oder in einem Unterordner des Arbeitsbestands (`S1`)?
2. Hat sie eines der unterstützten Formate?
3. Wurde danach **Druckauswahl aktualisieren** ausgeführt?

### Ein Bild fehlt in der HTML

Die Datei kann im Markdown-Index den Status fehlt haben. Prüfen, ob sie noch unter dem dort eingetragenen Pfad vorhanden ist, und anschließend erneut aktualisieren lassen.

### Ein Bild erscheint doppelt

Exakt bytegleiche Dateien werden über ihren SHA-256-Hash erkannt und nicht als zweite Kachel angezeigt. Unterschiedliche Bilddateien oder unterschiedliche Bildformate werden nicht automatisch als identisch bewertet.

## Zugehöriges Werkzeugmodul

Das Layout stammt aus dem Werkzeugmodul:

    julian-pokemon-druckbogen

Führende Moduldatei:

    C:\Users\mpuet\.codex\skills\julian\modules\03_pokemon-druckbogen.md

Die Auswahl-HTML ergänzt dieses Modul um Indexpflege, Kachelauswahl und den Druck nur der angehakten Bilder.
