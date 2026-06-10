# US-011 — Positionsblock-Struktur

> Eigenes Doc (nicht US-007s LAYOUT-ANALYSE.md editiert) — vermeidet
> Cross-Branch-Konflikt im Spike-Stack (US-011 hat zwei unabhängige
> Eltern: US-007-Doc + US-008-Modell).

## Aufbau im Referenz-Muster (RAUMKARUSSELL, GEN 2)

Pro Cateringkonzept-Abschnitt ein **Positionsblock**, darin Zeilen:

| Spalte | Quelle | Beispiel |
|--------|--------|----------|
| Bezeichnung | Text links | `Mobiles Grillequipment ab 100 PAX` |
| Menge | rechtsbündig | `1`, `3` |
| Einzelpreis | rechtsbündig | `195,00` |
| Gesamt | rechtsbündig | `195,00`, `119,70` |

**Zwei Zeilentypen:**
- **Sub-Header** (`is_header=True`) — preislose Strukturzeile, z. B.
  `1x Live Cooking/BBQ Station im Beach & 1 Foodtruck`. Gruppiert die
  folgenden Positionen, keine Menge/Preis-Spalten.
- **Position** — Bezeichnung + Menge + Einzelpreis + Gesamt.

Pro Block optional eine **Zwischensumme** (`Positionsblock.zwischensumme`).

## Modell-Abbildung (`angebot_model.py`)

```python
Position(bezeichnung, menge, einzelpreis, gesamt, is_header=False)
Positionsblock(typ, titel, positionen=[Position…], zwischensumme)
Angebot.bloecke: list[Positionsblock]
```
`typ ∈ {speisen, getraenke, personal, logistik}` — entspricht den
Positions-Sektionen echter Angebote. Preise sind reine Strukturfelder
(keine KOCHfabrik-Kalkulation — Epic Non-Goal).

## Repeater-Band (aus US-009)

`build_angebot_template.py` vermisst die getroffenen Positions-Elemente
und schreibt `_meta.repeater` ins Template:

```json
"repeater": {"positionen": {"page": "2", "y0": …, "y1": …, "row_h": …}}
```

→ **Sprint 3** rendert `Angebot.bloecke` in dieses Band (Zeilen-Vorlage
× N Positionen, Sub-Header ohne Preisspalten). Sprint 2 liefert nur
Struktur + Band-Spec, kein Positions-Rendering (FEATURE-ARCH Non-Goal).

## Verify

```bash
cd phase0/scripts && python3 -c "from angebot_model import load; a=load('../fixtures/angebot_example.json'); assert sum(len(b.positionen) for b in a.bloecke)>0; assert any(p.is_header for b in a.bloecke for p in b.positionen)"
```
