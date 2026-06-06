# Concierge for Home Assistant (Concierge) – Spezifikation V2.1

Concierge for Home Assistant provides least privilege access to the "home assistant" smart home automation system.


## Leitprinzip

Concierge exponiert ausschließlich explizit freigegebene Informationen und Aktionen aus Home Assistant und erzwingt Least-Privilege-Zugriff durch deklarative Konfiguration.

Concierge ist bewusst klein, verständlich, wartungsarm, zustandsarm und sicherheitsorientiert aufgebaut.

---

# 1. Zielsetzung

Concierge for Home Assistant (Concierge) ist ein eigenständiger Dienst, der vor Home Assistant geschaltet wird und ausgewählte Informationen und Funktionen kontrolliert exponiert.

Concierge dient als Sicherheits-, Berechtigungs- und Präsentationsschicht zwischen Benutzern und Home Assistant.

Home Assistant bleibt das System of Record und führt weiterhin Automationen, Integrationen und Geräteverwaltung aus.

Concierge definiert:

* welche Informationen sichtbar sind
* welche Aktionen erlaubt sind
* welche Benutzer Zugriff haben
* wie die Benutzeroberfläche aussieht

Concierge ersetzt nicht Home Assistant, sondern ergänzt dessen fehlende feingranulare Berechtigungsverwaltung.

---

# 2. Architektur

```text
User
 ↓
Concierge for Home Assistant (Concierge)
 ↓
Home Assistant REST API
 ↓
Geräte / Automationen / Entitäten
```

Beispiel Deployment:

```text
https://concierge.example.meinedomain.com
```

---

# 3. Designprinzipien

## Least Privilege

Jeder Benutzer erhält ausschließlich die Rechte, die für seinen Anwendungsfall erforderlich sind.

## Whitelist statt Blacklist

Concierge arbeitet ausschließlich mit expliziten Freigaben.

Alles, was nicht freigegeben ist, gilt als verboten.

## Home Assistant vollständig verstecken

Benutzer erhalten niemals:

* Home-Assistant-Tokens
* Home-Assistant-URLs
* Home-Assistant-Dashboards
* direkten API-Zugriff

## Konfiguration statt Programmierung

Freigaben sollen deklarativ konfigurierbar sein.

Neue Benutzer oder Ansichten sollen ohne Codeänderungen möglich sein.

## Minimalismus

Concierge soll bewusst klein, verständlich und wartungsarm bleiben.

Grundsätze:

* möglichst wenige Abhängigkeiten
* keine unnötigen Frameworks
* keine komplexe Build-Pipeline
* keine JavaScript-Frameworks
* möglichst wenige transitive Dependencies

Concierge priorisiert Einfachheit und Wartbarkeit gegenüber Funktionsumfang.

---

# 4. Technologiestack

## Backend

* Python
* Flask
* Werkzeug

## Frontend

* Server Side Rendering mit Jinja2
* HTML
* CSS
* Vanilla JavaScript

Keine Frontend-Frameworks.

## Home Assistant Kommunikation

* requests

## Konfiguration

* YAML

## Deployment

* Docker
* gunicorn

## Explizit ausgeschlossen

* FastAPI
* Node.js
* npm
* React
* Vue
* Svelte
* Angular
* TypeScript
* Frontend-Build-Pipeline
* Plugin-System

---

# 5. Home Assistant Integration

## Kommunikation

Home Assistant REST API.

Authentifizierung über ein globales Long-Lived Access Token.

## Unterstützte Operationen

### Entität lesen

```http
GET /api/states/<entity_id>
```

### Service ausführen

```http
POST /api/services/<domain>/<service>
```

Beispiel:

```json
{
  "entity_id": "script.garage_trigger"
}
```

## Zugriffskonzept

Concierge führt ausschließlich vorkonfigurierte Lese- und Schreiboperationen aus.

Concierge erlaubt niemals:

* beliebige API-Requests
* beliebige Service-Aufrufe
* direkte Weiterleitung von Benutzer-Requests an Home Assistant

Alle erlaubten Aktionen werden explizit in der Konfiguration definiert.

---

# 6. Sicherheitsmodell

## Grundregel

Benutzer interagieren ausschließlich mit Concierge.

Niemals direkt mit Home Assistant.

## Netzwerk (Out of Scope)

Netzwerkzugriffskontrolle ist nicht Aufgabe von Concierge.

Mögliche Deployments:

* Tailscale
* WireGuard
* Reverse Proxy
* VPN
* Firewall-Regeln
* IP-Allowlists
* Zero-Trust-Lösungen

## Authentifizierung

MVP:

* Benutzername
* Passwort

## Passwortspeicherung

Concierge speichert niemals Klartext-Passwörter.

Passwörter werden ausschließlich als Passwort-Hashes gespeichert.

Beispiel:

```yaml
users:
  user:
    password_hash: "scrypt:..."
```

Passwort-Hashing erfolgt über Werkzeug.

Concierge implementiert keine eigene Kryptographie.

## Passwort-Management

Concierge stellt ein CLI-Kommando bereit:

```bash
cfh hash-password
```

oder

```bash
docker run --rm concierge-for-home-assistant hash-password
```

## Sitzungen

Concierge verwendet signierte Flask-Cookie-Sessions.

Eigenschaften:

* HttpOnly
* Secure
* SameSite=Strict

Es werden keine serverseitigen Sessions gespeichert.

## Explizit ausgeschlossen

* JWT
* Redis
* Datenbankgestützte Sessions
* Serverseitiger Session Store

## CSRF-Schutz

Pflicht.

Umsetzung:

* SameSite=Strict Cookies
* CSRF-Token in der Session
* X-CSRF-Token Header bei schreibenden Requests

Keine zusätzliche CSRF-Framework-Abhängigkeit.

## Rate Limiting (Empfehlung)

Rate Limiting gehört nicht zum Verantwortungsbereich von Concierge.

Empfohlen wird die Umsetzung in vorgeschalteten Komponenten:

* Reverse Proxy
* API Gateway
* Firewall
* WAF

## Audit Logging

Alle Aktionen werden protokolliert.

Verwendung des Python Standard Library Logging Frameworks.

Ausgabe ausschließlich nach stdout.

Beispiel:

```text
2026-06-05T12:15:00
user=user
action=garage_open
result=success
```

## Health Check

Concierge bietet einen `/health` Endpunkt an, der die interne Integrität sowie die Erreichbarkeit der konfigurierten Home Assistant Instanz prüft. Er dient zur Überwachung durch Orchestrierungssysteme wie Docker oder TrueNAS.


---

# 7. Secrets

## Grundsatz

Concierge trennt Konfiguration und Secrets strikt.

## Konfiguration

Die Konfigurationsdatei darf enthalten:

* Benutzer
* Passwort-Hashes
* Rollen
* Views
* Cards
* Aktionen

Die Konfigurationsdatei darf niemals enthalten:

* Klartext-Passwörter
* Home-Assistant-Tokens
* Session-Secrets

## Secret-Dateien

Alle Secrets werden als Dateien in einem `secrets/`-Verzeichnis abgelegt, das via Bind-Mount in den Container eingebunden wird.

Beispiele:

```text
/app/secrets/ha_token
/app/secrets/flask_secret_key
/app/secrets/users.yaml
```

---

# 8. Berechtigungsmodell

## Benutzer

```yaml
users:
  user:
    roles:
      - garage_user
```

## Rollen

```yaml
roles:
  garage_user:
    views:
      - garage
```

## Views

```yaml
views:
  garage:
    cards:
      - garage_status
      - garage_open_button
```

---

# 9. UI-Konzept

## Dashboard-basiert

Jeder Benutzer sieht ausschließlich die ihm zugewiesenen Views.

## Kartenmodell

Die UI besteht aus Cards.

Beispiele:

* Status Card
* Action Card
* Sensor Card
* Toggle Card
* Text Card

---

# 10. Card Typen

## Status Card

```yaml
garage_status:
  type: status
  entity: cover.garage
```

## Action Card

```yaml
garage_open_button:
  type: action

  service:
    domain: script
    service: turn_on

  data:
    entity_id: script.garage_trigger
```

## Sensor Card

```yaml
outside_temp:
  type: sensor
  entity: sensor.outside_temperature
```

## Toggle Card

```yaml
terrace_light:
  type: toggle
  entity: light.terrace
```

---

# 11. Progressive Web App (PWA)

Concierge muss als installierbare Progressive Web App umgesetzt werden.

Ziele:

* Smartphone-Nutzung
* Installation auf iPhone und Android
* App-ähnliche Benutzererfahrung
* Direkter Zugriff vom Home-Bildschirm

## Pflichtbestandteile

* manifest.json
* Service Worker
* App Icons

## Mobile First

Die Benutzeroberfläche soll primär für Smartphones optimiert werden.

Desktop-Unterstützung ist erwünscht, aber nicht prioritär.

## Aktualisierung

MVP:

* manueller Refresh-Button
* Pull-to-Refresh

Nicht Bestandteil des MVP:

* WebSockets
* Server-Sent Events
* Live Streaming
* permanentes Polling

## Offline-Verhalten

Concierge benötigt grundsätzlich eine Verbindung zum Backend.

Offline-Unterstützung ist nicht erforderlich.

---

# 12. Konfigurationsdatei

Dateiformat:

```yaml
config.yaml
```

Beispiel:

```yaml
users:
  user:
    password_hash: "scrypt:..."
    roles:
      - garage_user

roles:
  garage_user:
    views:
      - garage

views:
  garage:
    title: Garage
    cards:
      - garage_status
      - garage_open_button

cards:

  garage_status:
    type: status
    entity: cover.garage

  garage_open_button:
    type: action

    service:
      domain: script
      service: turn_on

    data:
      entity_id: script.garage_trigger
```

---

# 13. Konfigurations-Reload

Die Konfiguration wird ausschließlich beim Start geladen.

Änderungen an der Konfiguration erfordern einen Neustart des Containers.

Hot Reload ist nicht Bestandteil des MVP.

---

# 14. API

## Login

```http
POST /api/login
```

## Logout

```http
POST /api/logout
```

## Aktuelle Session

```http
GET /api/me
```

## Verfügbare Views

```http
GET /api/views
```

## View laden

```http
GET /api/views/{view}
```

## Aktion ausführen

```http
POST /api/actions/{action}
```

Der Endpunkt darf ausschließlich vorkonfigurierte Aktionen ausführen.

---

# 15. Namensgebung

Concierge for Home Assistant - least privilege access for smart homes.


| Zweck                              | Name                                                 |
| ---------------------------------- | ---------------------------------------------------- |
| Produktname (kurz, GUI, informell) | `Concierge`                                          |
| Voller Titel                       | `Concierge for Home Assistant`                       |
| Untertitel / Slogan                | `Least privilege access for smart homes`             |
| Repository Name                    | `concierge-for-home-assistant`                       |
| GitHub Repository URL              | `github.com/johannesjh/concierge-for-home-assistant` |
| Python Distribution Name (PyPI)    | `concierge-for-home-assistant`                       |
| Python Import Name                 | `concierge_for_home_assistant`                       |
| Python Alias (Beispiel)            | `import concierge_for_home_assistant as cfh`         |
| Python Package Directory           | `concierge_for_home_assistant/`                      |
| Docker Image Name                  | `concierge-for-home-assistant`                       |
| OCI Container Name                 | `concierge-for-home-assistant`                       |
| Container Registry Pfad (Beispiel) | `ghcr.io/johannesjh/concierge-for-home-assistant`    |
| Flatpak / App ID                   | `io.github.johannesjh.Concierge`                     |
| Desktop File ID                    | `io.github.johannesjh.Concierge.desktop`             |
| PWA Application Name               | `Concierge`                                          |
| PWA Short Name                     | `Concierge`                                          |
| Interner Kurzname / Kürzel         | `cfh`                                                |


# 15. Nicht-Ziele

Concierge soll nicht:

* Home Assistant ersetzen
* Automationen verwalten
* Geräte konfigurieren
* Integrationen installieren
* Home Assistant Dashboards rendern
* generischen API-Zugriff erlauben
* Netzwerkzugriff kontrollieren
* Firewall-Funktionen bereitstellen
* Reverse Proxy ersetzen
* API Gateway ersetzen

---

# 16. MVP

Version 1.0 enthält:

* Docker Container
* Flask Backend
* YAML Konfiguration
* Passwort-Hashing über Werkzeug
* Benutzerverwaltung
* Rollen
* Views
* Status Cards
* Action Cards
* Home Assistant REST Integration
* Audit Logging
* Installierbare PWA
* Mobile-First UI
* Pull-to-Refresh
* Globales HA-Token als Secret

---

# 17. Explizit Out of Scope

Folgende Themen gehören nicht zum MVP:

* Passkeys / WebAuthn
* Multi-Faktor-Authentifizierung
* OAuth
* SSO
* Push Notifications
* Mehrere Home-Assistant-Instanzen
* Plugin-System
* Themes
* Dynamische Konfigurationsoberfläche
* WYSIWYG-Dashboard-Editor
* WebSockets
* Server-Sent Events
* Live Streaming
* Hot Reload

---

# Verantwortlichkeiten

## Concierge

* Authentifizierung
* Autorisierung
* Berechtigungen
* UI
* Audit Logging

## Home Assistant

* Entitäten
* Geräte
* Automationen
* Service Calls

Die Sicherheitsgrenze liegt vollständig in Concierge.
