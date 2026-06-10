# Sprint 2 — FEATURE-ARCH (EPIC-001 · Template-Extraktion + Datenmodell)

## Scope

Aus einem echten KOCHfabrik-Muster-Angebot ein **pixelgenaues,
parametrisierbares Template** extrahieren und ein **striktes
Angebots-Datenmodell** definieren. Das ist die Grundlage, auf der
Sprint 3 (Renderer + Pixel-Diff-Gate), Sprint 4 (Fiktiv-Korpus) und
Sprint 5 (Chat-Flow) aufsetzen.

### Goals
- 1 Referenz-Muster identifiziert + Layout vermessen (alle invarianten Blöcke)
- `angebot_model.py` — vollständiges, JSON-roundtrip-stabiles Datenmodell
- `angebot_template.elements.json` — Faithful-Template mit Skalar-Tokens
  + Positionszeilen-Repeater, invariante Blöcke verbatim
- Felder-Mapping (Modell → Template-Tokens)
- Konformität: befülltes PDF wird von `kf_classify` als `angebot` erkannt

### Non-Goals (bewusst NICHT in Sprint 2)
- Positionszeilen-**Rendering** (Daten→PDF) → Sprint 3
- Pixel-Diff-Gate gegen echte Muster → Sprint 3
- Echte KOCHfabrik-Preisliste / Kalkulationslogik → Folge-Scope (Epic Non-Goal)
- Chat/Frontend → Sprint 5
- Jede Änderung am eingefrorenen Präsentationsgenerator (Freeze bleibt grün)

## Architektur

```
Referenz-Muster.pdf
   │  extract.py (bestehende Faithful-Extraktion, UNVERÄNDERT)
   ▼
elements.json ──► build_angebot_template.py
                     │  Skalar→{TOKEN}, Positionszeilen→{POSITIONEN}-Repeater,
                     │  Letterhead/Bank/Footer verbatim
                     ▼
              angebot_template.elements.json   ◄── Single Template

angebot_example.json ──► angebot_model.load() ──► Angebot (dataclass)
                                                      │
                              angebot_fill.fill(angebot, template)
                                                      │ Skalar-Tokens ersetzt
                                                      ▼
                              gefüllte elements.json ──► reconstruct.js ──► PDF
                                                      │
                                          verify_angebot → kf_classify == 'angebot'
```

Wiederverwendung statt Neubau: `extract.py`/`reconstruct.js` unverändert
(Engine-Regel CLAUDE.md), `build_cover_template.py` als Bauplan-Vorlage,
`compose_offer.swap_ph` als Token-Swap-Muster, `kf_classify` als Gate.

## Datenmodell (Skizze)

```python
@dataclass
class Position:      bezeichnung:str; menge:float; einzelpreis:float; gesamt:float
@dataclass
class Positionsblock: typ:str  # speisen|getraenke|personal|logistik
                      positionen:list[Position]; zwischensumme:float
@dataclass
class Veranstaltung: anlass:str; datum:str; beginn:str; personen:int
                     ort:str; konzept:str
@dataclass
class Angebot:       kunde:str; adresse:str; angebots_nr:str; datum:str
                     kundennr:str; lieferdatum:str; ansprechpartner:str
                     veranstaltung:Veranstaltung
                     bloecke:list[Positionsblock]; pauschalen:list[...]
```

## Entscheidungen

| Entscheidung | Begründung |
|---|---|
| Template aus echtem Muster extrahieren (nicht from-scratch) | User-Entscheid; max. Aufbau-Treue, Reuse der Faithful-Engine |
| stdlib `@dataclass` statt pydantic | Spike, keine neue Dependency, JSON reicht |
| Preislogik nur strukturell | Echte KF-Preisliste = Epic Non-Goal, braucht KOCHfabrik-Input |
| `kf_classify` als Konformitäts-Gate | bereits 33/33-verifiziert, deterministisch |

## Risiken

| Risiko | Mitigation |
|---|---|
| Mehrere Layout-Generationen → welches Muster? | US-007 clustert, wählt jüngste/vollständigste 1 Referenz |
| Positionszeilen-Repeater im Faithful-Format komplex | Sprint 2 nur Spec/Struktur; Rendering erst Sprint 3 |
| `extract.py` darf nicht verändert werden (Engine-Regel) | nur darüber-liegende Skripte, Engine read-only |

## Epic-Alignment

**Epic:** EPIC-001 — KOCHfabrik Angebotsgenerator.
**Adressiert:** Sprint-2-Zeile der Epic-Sprint-Zuordnung (Template-
Extraktion + Datenmodell). **Nächste Iteration:** Sprint 3 = Renderer
Daten→PDF + Pixel-Diff-Gate gegen ≥3 echte Muster (Akzeptanzkriterium 1).
**Carry-Over-Bezug:** absorbiert die DEFERRED-Richtung „Eingabe-Kapselung:
Prompt/Formular statt Kunden-PDF" aus Sprint 1.
