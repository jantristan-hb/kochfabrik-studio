# PROGRESS.md — kochfabrik-studio

## Compact-Recovery
> Kontext verloren? Lies: 1) `docs/epics/EPIC-001-*.md` (Vorhaben),
> 2) diese Datei (Status), 3) `docs/sprint-{aktuell}/USER-STORIES.md`+
> `EXECUTE.md`. Repo: GitHub `master` (Deploy-Repo, Coolify
> yu2fqx0twmtqcp6zyx2e59si). Engine vendored aus pptxgenerator_v2.

**Projekt:** kochfabrik-studio (FastAPI, web/, vendored engine)
**Aktueller Sprint:** Sprint 1 TODO (EPIC-001)
**Status:** 0 Sprints done · Stack: FastAPI + Postgres (ab S1) + SQLAlchemy2

---

## Sprint 1 — DB-Fundament + Angebot-Persistenz + Nummernsequenz (2026-05-19)

| Story | Titel | Status |
|-------|-------|--------|
| US-001 | Postgres-Container + graceful Async-DB-Layer | TODO |
| US-002 | DB-Schema + Alembic-Migrationen | TODO |
| US-003 | Atomare Nummernsequenzen (100001-A + Angebot) | TODO |
| US-004 | Owner-scoped Repository/Service-Layer | TODO |
| US-005 | API-Endpoints + Integration Angebot-Generierung | TODO |

**Neue Tabellen:** app_user, customer, offer, chat_message, seq_counter
**Neuer Service:** Coolify Postgres `kf-studio-pg`

## Carry-Over → Sprint 2
<!-- auto-generated placeholder — /sprint-review aktualisiert -->
_(kein Übertrag — Sprint 1 noch nicht ausgeführt)_

---

## Epics

| ID | Titel | Status | Sprints |
|----|-------|--------|---------|
| EPIC-001 | Persistenz, Multi-Tenant & CRM | OPEN | S1 (geplant), S2-S4 (TODO) |

## Bekannte Lücken (nicht in S1)
- Chat-History-Restore (S2) · Dashboard/Bibliothek-UI (S3) · OAuth2 (S4)
- Such/Filter, RBAC — bewusst out-of-scope

## Aktueller Zustand (2026-05-19)
| Metrik | Wert |
|--------|------|
| DB | keine (S1 führt Postgres ein) |
| Auth | KF_USERS-Env + signiertes Cookie (kf_sess) |
| Persistenz | keine (Angebot nur client-seitig) — S1 behebt das |
