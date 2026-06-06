# Produktion (config/prod)

Dieses Verzeichnis enthält die Konfiguration für den Produktivbetrieb von Concierge for Home Assistant.

Concierge wird als einziger Container gestartet und bindet sich an eine **bereits laufende Home Assistant Instanz** an – HA selbst wird hier nicht verwaltet.

## Voraussetzungen

- Docker & Docker Compose
- `just` installiert (`brew install just` / `apt install just`)
- `uv` installiert (`curl -LsSf https://astral.sh/uv | sh`)
- Eine laufende Home Assistant Instanz mit bekannter URL
- Ein Long-Lived Access Token für Home Assistant

## Verzeichnisstruktur

```
config/prod/
├── docker-compose.yml       # Concierge Produktiv-Stack
├── config.yaml              # Produktivkonfiguration (nicht eingecheckt, enthält Zugangsdaten)
├── config.yaml.template     # Vorlage – wird von `just setup prod` verwendet
├── secrets/
│   ├── ha_token             # Nicht eingecheckt – wird mit `just setup prod` befüllt
│   └── flask_secret_key     # Nicht eingecheckt – wird mit `just setup prod` generiert
└── README.md                # Diese Datei
```

## Einrichtungsanleitung (Einmalig)

### Schritt 1: HA Token erstellen

In Home Assistant:
1. Profil (unten links) → Sicherheit → Token erstellen
2. Token kopieren – **wird nur einmal angezeigt!**

### Schritt 2: Setup ausführen

```bash
just setup prod
```

Fragt interaktiv ab:
- **Home Assistant URL** (z.B. `http://192.168.1.10:8123`)
- **HA Token** aus Schritt 1

Erstellt automatisch `config/prod/config.yaml` aus dem Template und legt die Secrets an.

### Schritt 3: Benutzer und Passwörter konfigurieren

Passwort-Hash erstellen:

```bash
just hash-password
```

Den ausgegebenen Hash sowie Benutzernamen und Rollen in `config/prod/secrets/users.yaml` eintragen. Das Schema der Konfigurationsdatei ist in [`config.schema.json`](../../config.schema.json) dokumentiert.

### Schritt 4: Container starten

```bash
just up prod
```

## Täglicher Workflow

```bash
just up prod      # Container starten
just down prod    # Container stoppen
just logs prod    # Logs beobachten (Ctrl+C zum Beenden)
just rebuild prod # Concierge neu bauen nach Code- oder Config-Änderungen
```
