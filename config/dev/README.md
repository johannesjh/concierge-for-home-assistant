# Dev-Setup Anleitung

Lokales Testsetup mit Home Assistant und Concierge for Home Assistant in Docker.

## Voraussetzungen

- Docker und Docker Compose installiert
- `just` installiert (`brew install just` / `apt install just`)
- `uv` installiert (`curl -LsSf https://astral.sh/uv | sh`)

---

## Erster Start (Einmalig)

### Schritt 1: Nur Home Assistant starten

```bash
docker compose -f config/dev/docker-compose.yml up -d homeassistant
```

Startet nur Home Assistant (Port 8123), noch ohne Concierge.

> Hinweis: HA braucht beim ersten Start ca. 30–60 Sekunden.

### Schritt 2: Home Assistant einrichten

1. Browser öffnen: http://localhost:8123
2. Onboarding durchlaufen:
   - Name, Benutzername, Passwort eingeben
   - Standort überspringen oder setzen
   - Statistiken ablehnen

### Schritt 3: Long-Lived Access Token erstellen

1. Unten links **Benutzerprofil** klicken
2. Tab **"Sicherheit"** wählen
3. Ganz nach unten scrollen zu **"Langlebige Zugriffstoken"**
4. **"Token erstellen"** klicken, Namen eingeben (z.B. `cfh-dev`)
5. Token kopieren – **wird nur einmal angezeigt!**

### Schritt 4: Secrets einrichten

```bash
just setup
```

HA Token aus Schritt 3 eingeben. Flask Secret wird automatisch generiert.
Beide Werte werden in `config/dev/secrets/` gespeichert.

### Schritt 5: Stack vollständig starten

```bash
just up
```

Startet Home Assistant (Port 8123) und Concierge (Port 8000).

### Schritt 6: Concierge einloggen

Browser öffnen: http://localhost:8000

Zugangsdaten aus `config/dev/secrets/users.yaml`:
- Benutzername: `user`
- Passwort: `test`

> Möchtest du ein eigenes Passwort festlegen? Generiere einen Hash mit `just hash-password` und trage ihn in `config/dev/secrets/users.yaml` ein.

---

## Täglicher Workflow

```bash
just up       # Stack starten
just down     # Stack stoppen
just logs     # Logs beobachten (Ctrl+C zum Beenden)
just rebuild  # Concierge neu bauen nach Code- oder Config-Änderungen
```

---

## Demo-Entitäten

Die Datei `config/dev/ha-config/configuration.yaml` definiert folgende Test-Entitäten:

| Entität | Typ | Card-Typ | Beschreibung |
|---|---|---|---|
| `script.garage_trigger` | Script | action | Simuliertes Tastrelais (öffnet/schließt Garage) |
| `input_boolean.test_schalter` | Input Boolean | toggle | Simulierter Schalter zum Testen der Toggle-Card |
| `input_number.test_temperatur` | Input Number | sensor | Simulierter Temperatursensor (°C) |
| `input_boolean.test_fenster` | Input Boolean | status | Simulierter Fensterstatus (offen/geschlossen) |

Das Garagentor wird als Tastrelais modelliert – ein einziger Script-Aufruf,
kein Status, kein Cover. Entspricht dem realen Verhalten.

Damit sind alle vier Card-Typen (action, toggle, sensor, status) im Dashboard vertreten.

---

## Probleme

### Concierge zeigt "nicht verfügbar" für alle Cards

HA ist noch nicht bereit oder das Token ist falsch.

Prüfen:
```bash
just logs
```

Token neu setzen:
```bash
just setup
just down && just up
```

### Login funktioniert nicht

Cookie-Problem bei HTTP. Sicherstellen dass `CFH_INSECURE_COOKIE=true` gesetzt ist
(ist in `config/dev/docker-compose.yml` bereits konfiguriert).

### HA startet nicht

```bash
just logs
```

Häufige Ursache: Port 8123 bereits belegt.

```bash
lsof -i :8123
```

---

## Verzeichnisstruktur

```
config/dev/
├── docker-compose.yml       # HA + Concierge Dev-Stack
├── config.yaml              # Concierge-Konfiguration für Dev (eingecheckt, keine echten Secrets)
├── ha-config/
│   └── configuration.yaml   # Demo-Entitäten (eingecheckt)
├── secrets/
│   ├── ha_token             # Nicht eingecheckt – wird mit `just setup` befüllt
│   └── flask_secret_key     # Nicht eingecheckt – wird mit `just setup` generiert
└── README.md                # Diese Datei
```
