---
id: EPIC-001
title: "Persistenz, Multi-Tenant & CRM für den Angebotsgenerator"
status: DONE
created: 2026-05-19
completed: 2026-05-19
project: kochfabrik-studio
sprints: []
---

# EPIC-001: Persistenz, Multi-Tenant & CRM für den Angebotsgenerator

## Beschreibung

KOCHfabrik Studio ist heute zustandslos: Angebote leben nur client-seitig
im JS-`A`-Objekt, PDFs sind transient, Auth ist `KF_USERS`-Env + Cookie.
Es gibt kein Wiederfinden, keine Kundenhistorie, keine Mandantentrennung.

Dieses Epic führt eine echte Persistenz-Schicht ein: jedes Angebot +
sein Chat-Verlauf werden in PostgreSQL gespeichert und im Chatbot-Editor
**exakt an gleicher Stelle** wiederherstellbar. Kunden und Angebote
bekommen fortlaufende Nummern (Kundennummer `100001-A`, A = AI). Dashboard
und Bibliothek zeigen je eingeloggtem User ausschließlich dessen eigene
Daten (Multi-Tenant). OAuth2 (Microsoft/Google) wird design-kompatibel
vorbereitet, aber noch nicht gebaut (manuelle User bleiben).

## Scope

### Was drin ist
- PostgreSQL-Container (eigener Coolify-Service, mtdc-postgres-Muster)
  + DB-Layer (SQLAlchemy/asyncpg), Schema-Migration
- Schema: `users`, `customers` (Kundennummer fortlaufend `100001-A`),
  `offers` (eigene fortlaufende Angebotsnummer, Owner-User, Customer-FK,
  vollständiger Angebot-State als JSON, created/updated), `chat_messages`
  (Offer-FK, role, content, ts) — atomare Nummern-Sequenzen
- Angebot speichern + exakt im Chatbot-Editor rekonstruieren (State +
  Chat-Verlauf, „da weitermachen wo aufgehört")
- Multi-Tenant-Scoping: alle Reads/Writes auf den eingeloggten User
- index.html (Dashboard): echte KPIs + letzte Angebote
- bibliothek.html: vollständiges, durchsuchbares/filterbares Archiv
  (Angebote + Kunden), Wiederöffnen → Chatbot mit exaktem State
- Kundendatensatz (1 Kunde : n Angebote)
- Auth-Abstraktion, die spätere OAuth2-Integration nicht blockiert

### Was NICHT drin ist
- OAuth2-Login/Registrierung (Microsoft/Google) — eigener späterer
  Sprint, jetzt nur design-kompatibel vorbereitet
- Rollen-/Rechtemodell über simple Tenant-Trennung hinaus
- Rechnungs-/Buchhaltungs-/Kalkulationslogik (Engine-Sache)
- Datenmigration (kein Altbestand vorhanden)

## Sprint-Zuordnung

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 1 | Postgres-Container + DB-Layer + Schema; Kunden-/Angebotsnummer-Sequenzen; Angebot speichern/laden | L |
| Sprint 2 | Multi-Tenant-Scoping (Owner aus Cookie); Chat-History persistieren + exakte Wiederherstellung im Chatbot | M |
| Sprint 3 | Dashboard (KPIs + letzte Angebote) + Bibliothek (suchbares Archiv, differenziert); Kunden-CRM-Ansicht | M |
| Sprint 4 (später) | OAuth2 Microsoft/Google Login/Registrierung auf der vorbereiteten Auth-Abstraktion | M |

> Sprint-Zuordnung ist grob. Details bestimmt `/sprint-plan`.

## Akzeptanzkriterien

1. Eigener Postgres-Container live; Schema migriert; App nutzt DB statt
   nur Client-State.
2. Jeder Kunde erhält fortlaufende Kundennummer `100001-A` (A = AI),
   jedes Angebot eine eigene fortlaufende Angebotsnummer — atomar,
   kollisionsfrei, über alle Angebote gezählt.
3. Angebot + Chat-Verlauf werden gespeichert und beim Wiederöffnen
   exakt im Chatbot-Editor rekonstruiert (gleicher State, gleiche Stelle).
4. Multi-Tenant: ein User sieht in Dashboard/Bibliothek ausschließlich
   eigene Angebote/Kunden.
5. index.html = echte KPIs + letzte Angebote aus der DB;
   bibliothek.html = vollständiges durchsuchbares Archiv aus der DB.
6. Auth-Abstraktion vorhanden, die spätere OAuth2-Integration erlaubt;
   manuelle User funktionieren unverändert.

## Fortschritt

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 1 | DB-Fundament + Angebot-Persistenz + Nummern | ✅ DONE (live-verifiziert, master b0c7f36) |
| Sprint 2 | Multi-Tenant + Chat-History + Wiederherstellung | ✅ DONE (live-verifiziert, master 69a6e8a) |
| Sprint 3 | Dashboard + Bibliothek + Kunden-CRM | ✅ DONE (live + Playwright, master 52196cd) |
| Sprint 4 | OAuth2 (Microsoft/Google) | ✅ DONE (Code ready, master 6784307; Live-OAuth braucht IdP-Creds) |
