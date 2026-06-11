# Sprint 13 — Retrospektive (2026-06-11)

## Was lief gut
- **Vom Feature-Wunsch zur live-fähigen Funktion in einem Tag:** Jans
  Prompt („Angebot hochladen → Slide-Vorschläge → Kombination aus Suche
  und Erstellung") wurde mittags geplant und abends war der komplette
  Designer implementiert — inklusive semantischem Live-Beweis
  (Vorspeise→„Finger Bites" 0.869, Hauptgang→„Dinner Menü" 0.899).
- **Wiederverwendung statt Neubau:** Die Suggest-API kombiniert nur
  Bestands-Bausteine (parse_offer_dishes, embed, bundle.rank,
  pick_frame) — null Duplikation, ADR-003-Regel gehalten (Sprint-12-
  Guard test_eine_bundle_ladestelle blieb grün und hat einmal korrekt
  angeschlagen).
- **Zwei-Ketten-Topologie mit Wartepunkt** funktionierte: API- und
  UI-Kette parallel, Lead-Merge `8fdb8cc` konfliktfrei, danach lief
  die UI-Restkette (064→066→067) in einem Rutsch ohne weitere
  Lead-Eingriffe durch.
- **Incident → Story im selben Sprint:** Der Korpus-Mount-Incident vom
  Vormittag wurde als US-068 eingeplant und der Deep-Check noch am
  selben Tag live gegen Prod bewiesen.

## Was lief schlecht / hätte besser sein können
- **Task-Board-Auto-Dispatcher:** Der Dispatcher verteilte pending/
  completed Tasks eigenmächtig an idle Agents — ein Dutzend Phantom-
  Assignments (US-064/066/067 vorzeitig, US-065/068 als Duplikate).
  Die Ownership-Disziplin der Agents fing ALLES ab, aber es kostete
  Lead-Aufmerksamkeit und Message-Volumen. Eine Fehlzuweisung (US-065
  an agent-us-068) wurde sogar ausgeführt — glücklicherweise korrekt
  und boundary-konform, aber auf dem fremden Ketten-Branch.
- Team-Task-Listen-Quirk: Tasks, die VOR TeamCreate angelegt wurden,
  landeten im Session-Scope und mussten im Team-Scope neu angelegt
  werden (Duplikat-Pflege).
- Mein US-065-Briefing war beim Versand bereits stale (Story fertig)
  — Nachrichten-Kreuzungen erzeugten 3 Klärungsrunden.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-061 | Router + Parsing | ✅ | — |
| US-062 | Top-N-Ranking | ✅ | 🔄 Indexmenge = globales Bundle (Ist-Laufzeitpfad statt menu_composition-Filter — per Ist-Code belegt); Pflicht-Gruppe aus static_slide.json |
| US-063 | Gerüst + Nav | ✅ | — (11 Nav-Links statt „≥5") |
| US-065 | Storyboard | ✅ | 🔄 von agent-us-068 implementiert (Dispatcher-Fehlzuweisung, Ergebnis korrekt); addToBoard() statt addSlide() |
| US-064 | Quelle + Karten | ✅ | nahm Board-CSS aus US-065-Boundary-Notiz mit (geplant) |
| US-066 | Suche | ✅ | — |
| US-067 | Download + E2E | ✅ | — |
| US-068 | LIVE_DEEP | ✅ | — |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 8 Stories | 8/8 (100%) |
| Effort | API M, UI-Kette L, US-068 S | Akkurat |
| Dependencies | 2 Ketten + Wartepunkt | Korrekt, Merge konfliktfrei |
| Scope | 8 | Passend (ein komplettes Feature) |

## Learnings (übertragbar)
- **Board-Auto-Dispatch ist mit Ketten-Topologie inkompatibel** —
  Gegenmittel, das funktionierte: Ownership VOR Spawn + explizite
  „nur auf Lead-Briefings reagieren, Board-Assignments ignorieren"-
  Klausel. Diese Klausel gehört künftig von Anfang an in jeden
  Ketten-Agenten-Prompt (EXECUTE.md-Lead-Regel ergänzt → S14).
- Tasks erst NACH TeamCreate anlegen (Scope-Falle).
- „In einem Rutsch nach USER-STORIES.md"-Delegation für Rest-Ketten
  reduziert Crossing-Rauschen massiv — der Agent meldete trotzdem
  jede Story einzeln mit SHA.
- Live-Smoke als Pflicht-Task-Schritt (nicht nur Mock-Tests) hat das
  Feature semantisch bewiesen — beibehalten für alle KI-Features.

## Spec-Erfüllung (EARS/Tests)
- EARS ohne grünen Verify: — (9/9; FEATURE-011 Nr. 1–4, FEATURE-012 Nr. 1–5)
- Pitfalls-Gegenprobe: sauber (kein np.load im Designer, embed gemockt
  + Beweis mit leerem Key, Nav 1-Zeile, kein timeout-Binary, Preview-
  Platzhalter statt Filter)
- Tests die sich als falsch herausstellten: —
- Tests die fehlten: — (Suite 113→143, +30)

## Spec-Sync (Code → Spec, aus E8.0)
- Specs auf `implemented`: KOCHFABRIK-FEATURE-011/012
- Abweichungen eingearbeitet: US-062-Indexmengen-Klärung → RETRO
  (Spec sagte bereits „Ist-Code übernehmen" — kein Spec-Fix nötig)
- TRACEABILITY (Sprint + Projekt) + EPIC-006 → DONE

## Offene technische Schulden
- D5 Text-Edit auf Slides (optionale Ausbaustufe, EPIC-006-Backlog)
- R-ID-Nachtrag für D6 in REQUIREMENTS (via /epic, gehört Jan)
- EPIC-007/008 (CI + Treue-Harness) → Sprint 14, Seed liegt
- Alt-Ordner-Entscheid (seit S12)
