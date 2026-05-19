# BDD — Sprint 3

## US-012: Stats-Endpoint {#us-012-stats-endpoint}
### Szenario: KPIs owner-scoped
**Given** User A hat 2 Angebote (1 Kunde), B hat 1
**When** A `GET /api/stats`
**Then** `{angebote:2, kunden:1, volumen:Σ zwischensummen, letzte:[≤5
A-Angebote]}` — nichts von B
### Szenario: DB-Ausfall graceful
**Given** DB down **When** `/api/stats` **Then** 503 + Nullwerte, kein 5xx

## US-013: Kunden-Endpoints {#us-013-kunden-endpoints}
### Szenario: Kundenliste + Detail owner-scoped
**Given** A hat Kunde K mit 2 Angeboten
**When** A `GET /api/kunden` dann `GET /api/kunde/{K}`
**Then** Liste enthält K (angebote:2); Detail = K + seine 2 Angebote
### Szenario: Fremder Kunde
**Given** Kunde K gehört A **When** B `GET /api/kunde/{K}` **Then** 404

## US-014: Angebote-Filter {#us-014-angebote-filter}
### Szenario: Suche + Status
**Given** A: Angebote „Sommerfest"(draft), „Gala"(final)
**When** `GET /api/angebote?q=somm` / `?status=final`
**Then** nur passende; leere Filter = alle (abwärtskompat)

## US-015: Dashboard {#us-015-dashboard}
### Szenario: echte KPIs + letzte
**Given** eingeloggt, /api/stats liefert Daten
**When** index.html lädt
**Then** KPI-Kacheln = echte Zahlen, "Zuletzt"-Tabelle = stats.letzte,
Klick → chat.html?offer={id}
### Szenario: leer
**Given** keine Angebote **Then** Empty-State, kein Platzhalter-Müll

## US-016: Bibliothek {#us-016-bibliothek}
### Szenario: Suche/Filter
**Given** Archiv mit Angeboten
**When** Suchtext/Status-Filter
**Then** Tabelle live gefiltert (debounced), Zeile → chat.html?offer=
### Szenario: 401 **Then** redirect /login.html

## US-017: Kunden-CRM {#us-017-kunden-crm}
### Szenario: Liste → Detail → Wiederöffnen
**Given** Kunden vorhanden
**When** kunden.html → Kunde klicken → Angebot klicken
**Then** Kundenliste, dann dessen Angebote, dann chat.html?offer={id}
### Szenario: client.html unangetastet
**Then** client.html („Client Research") unverändert funktionsfähig
