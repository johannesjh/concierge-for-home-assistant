# Concierge for Home Assistant

Least privilege access for smart homes.


## Kernziele

Concierge for Home Assistant ermöglicht es, Home Assistant sicher nach außen zu präsentieren, ohne die volle Komplexität und Angriffsfläche der Original-Instanz freizugeben.

- Sicherheit: Home Assistant bleibt hinter Concierge mit strikter Zugriffskontrolle. Der direkte Zugang zur HA-API ist für Endnutzer nicht möglich.
- Einfachheit: Nur relevante Informationen und Funktionen werden exponiert.
- Multi-User & Berechtigungen: Unterschiedliche Nutzer erhalten maßgeschneiderte Zugriffe.
- PWA-fähig: Die Oberfläche ist als Progressive Web App (PWA) auf mobilen Geräten installierbar.

Beispiel-Usecase: Ich möchte, dass meine Kinder die Garage öffnen und schließen können und auch eine Beleuchtung ein- und ausschalten, aber sie sollen auf weitere Funktionen und Entitäten des HomeAssistant keinen Zugriff haben.


## Designprinzipien

- Least Privilege: Nur explizit freigegebene Entitäten und Dienste sind zugänglich.
- Whitelist statt Blacklist: Alles, was nicht explizit erlaubt ist, ist verboten.
- Vollständige Abstraktion: Home Assistant ist für den Endbenutzer nicht direkt sichtbar, sondern ausschließlich die per Whitelist festgelegten Entitäten.
- Konfiguration statt Programmierung: Concierge wird deklarativ konfiguriert über eine `config.yaml` Datei. Es sind keine Programmierkenntnisse notwendig, um Benutzer und Entitäten hinzuzufügen.

## Installation

### Docker (Empfohlen)
Die einfachste Art, Concierge zu betreiben, ist mittels Docker. Ein fertiges Image wird automatisch bei jedem Release über GitHub Packages gebaut.

Beispiel für docker-compose.yml:
```yaml
services:
  cfh:
    image: ghcr.io/johannesjh/concierge-for-home-assistant:latest
    restart: always
    volumes:
      - ./config/prod:/config/prod
    environment:
      - CONFIG_PATH=/config/prod
    ports:
      - "8080:8080"
```
Hinweis: In dem gemappten Ordner (hier `./config/prod`) werden deine `config.yaml` sowie die Unterordner mit den sensiblen Zugangsdaten (wie `secrets/`) erwartet.

### TrueNAS SCALE
Concierge lässt sich einfach als Custom App unter TrueNAS SCALE via Docker-Compose einrichten.
1. Erstelle ein Dataset für die Konfigurationsdaten.
2. Mappe dieses Dataset auf /config/prod/ im Container.
3. Definiere die Umgebungsvariable CONFIG_PATH auf den internen Pfad /config/prod/.


## Konfiguration

Die Konfiguration erfolgt über eine config.yaml Datei. Das Schema ist in [config.schema.json](config.schema.json) definiert. Sensible Zugangsdaten, wie Benutzer-Passwörter (in `secrets/users.yaml`) und API-Token, werden in einem separaten `secrets/` Verzeichnis verwaltet.

Weitere Details findest du in der [Specification.md](Specification.md).


## Entwicklung

Das Projekt ist in der Freizeit erstellt, mit freiwilligem persönlichem Einsatz. Aus eigenem Bedarf, und hoffentlich nützt es auch weiteren Personen.

Contributions welcome. 

Dieses Projekt wird unter Verwendung von KI-Agenten entwickelt. Ausgangslage für die Zusammenarbeit mit KI-Agenten sind folgende Dokumente:

- [`Specification.md`](Specification.md): Fachliche Spezifikation; dieses Dokument beschreibt die Ziele, Architektur, Designprinzipien und Anforderungen des Projekts.
- [`AGENTS.md`](AGENTS.md): Todo-Liste und Arbeitsanweisungen für KI-Agenten; hier werden neue Aufgaben eingetragen und iterativ abgearbeitet.


## Lizenz

Dieses Projekt steht unter der GNU Affero General Public License v3.0 (AGPLv3). Den vollständigen Text der Lizenz findest du in der Datei [LICENSE](LICENSE) im Root-Verzeichnis des Projekts.
