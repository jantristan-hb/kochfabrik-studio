# DELIVERY-FLOW — kochfabrik-studio

> **FEATURE-CI-DELIVERY (EPIC-009 §4) — „Kein roter Merge, kein blinder Deploy."**
> Dieses Dokument beschreibt den verbindlichen Auslieferungs-Pfad von einer
> Code-Änderung bis zur verifizierten Produktion: **PR → CI → Merge →
> manueller Deploy → Live-Verify**. Es hält außerdem die **Branch-Protection**
> (required check) und die **Admin-Bypass-Regel** fest.
>
> Erfüllt FEATURE-009 §8 Nr. 1 + 4 (EARS).

---

## 0. Überblick

```
Feature-Branch ──PR──▶ CI (Job "ci") ──grün──▶ Review ──Merge──▶ master
                          │                                         │
                          └─ rot ⇒ Merge BLOCKIERT                  │
                                                                    ▼
                                              manueller Coolify-Deploy (kein Webhook)
                                                                    │
                                                                    ▼
                                                LIVE_DEEP=1 ./tools/live_verify.sh
```

Es gibt **keinen Auto-Deploy**: Ein Merge nach master deployt nichts von allein.
Deploy ist immer ein **bewusster, manueller Schritt**.

---

## 1. PR → CI (required check)

- Jeder Code-Weg nach master läuft über einen **Pull Request**. Direkter Push
  auf master ist durch Branch-Protection blockiert.
- Beim Öffnen/Aktualisieren eines PR läuft die Pipeline
  `.github/workflows/ci.yml`, **Job `ci`** (ubuntu-latest, Python 3.12):
  1. `ruff check --select E9,F63,F7,F82 backend engine/scripts`
  2. `pytest backend/tests -q`
  3. `docker build -t kf-studio-sim .`
- Der Job-Name **`ci`** ist als **required status check** auf master gesetzt.
  Ein roter Check **blockiert den Merge** (EARS §8 Nr. 1).

### Protection-Zustand (master)

Gesetzt via (US-080, der einzige freigegebene Protection-Call):

```bash
gh api repos/jantristan-hb/kochfabrik-studio/branches/master/protection -X PUT --input - <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["ci"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON
```

- `required_status_checks.contexts = ["ci"]` — der CI-Job muss grün sein.
- `strict: false` — kein Zwang, den Branch vor Merge auf master-HEAD zu rebasen
  (vermeidet Re-Run-Schleifen bei paralleler Arbeit).
- `enforce_admins: false` — **bewusst** (siehe Admin-Bypass-Regel unten).

Zustand prüfen:

```bash
gh api repos/jantristan-hb/kochfabrik-studio/branches/master/protection \
  -q '.required_status_checks.contexts'
```

---

## 2. Admin-Bypass-Regel

`enforce_admins: false` erlaubt Repo-Admins, einen blockierten Merge zu
übergehen. Diese Möglichkeit ist **eng begrenzt**:

- **Erlaubt** ausschließlich für **Review-/Doc-Commits des Sprint-Workflows**
  (z. B. `PROGRESS.md`, `RETRO`, Sprint-Docs unter `docs/sprint-*/`), die keinen
  produktiven Code berühren und für die ein voller CI-Lauf keinen Mehrwert hat.
- **Niemals für Code.** Jede Änderung an `backend/`, `engine/`, `web/`,
  `Dockerfile`, `requirements.txt` oder der Pipeline selbst geht **immer** durch
  einen grünen CI-Lauf — kein Admin-Bypass.
- Der Bypass ist die Ausnahme, nicht der Normalfall. Im Zweifel: CI abwarten.

`enforce_admins` bleibt deshalb `false` (sonst wäre selbst der Doc-Bypass
unmöglich) — die Disziplin liegt in dieser Regel, nicht im Schalter.

---

## 3. Merge → manueller Deploy

Nach dem Merge nach master ist die Änderung **noch nicht live**. Deploy =
**manueller Coolify-API-Trigger** (kein Webhook):

```bash
source ~/work/.env
curl "https://coolify.flinkbase.com/api/v1/deploy?uuid=yu2fqx0twmtqcp6zyx2e59si&force=true" \
  -H "Authorization: Bearer $COOLIFY_TOKEN"
```

Ablauf, Vorbedingungen (Sim-Gate) und Rollback: **`docs/sprint-11/CUTOVER-RUNBOOK.md`**.

---

## 4. Live-Verify (LIVE_DEEP)

Nach dem Deploy wird die laufende Prod-Instanz verifiziert:

```bash
# Flache Verifikation (Health-Routen):
./tools/live_verify.sh

# Tiefe Verifikation (zusätzliche Modul-Routen / Deep-Checks):
LIVE_DEEP=1 ./tools/live_verify.sh
```

- Ohne `LIVE_DEEP` prüft das Skript die Basis-Gesundheit (`/api/health` →
  `200`/`db:true`, geschützte Routen → `401` = Route lebt).
- `LIVE_DEEP=1` aktiviert die **tiefe** Verifikation (eingeführt mit dem
  Präsentationsdesigner, Sprint 13). Erst ein grüner Deep-Verify schließt den
  Delivery-Flow ab.

---

## 5. Verweise

| Thema | Dokument |
|---|---|
| Cutover-Ablauf + Rollback | `docs/sprint-11/CUTOVER-RUNBOOK.md` |
| Sim-Gate / Live-Verify (Befehle) | `CLAUDE.md` → Abschnitt „Gates" |
| Backup / Restore | `docs/ops/BACKUP-CYCLE.md`, `docs/ops/RESTORE-RUNBOOK.md` |
| Pipeline-Definition | `.github/workflows/ci.yml` |
