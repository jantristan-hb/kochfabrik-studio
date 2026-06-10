# US-016 — Pixel-Diff-Gate Report

DPI=100 · Toleranz(Referenz)=0.25 · Per-Pixel-Δ-Toleranz=0.06

## Referenz-Self-Round-Trip (Gate-relevant)

- **# 10_182_RAUMKARUSSELL GmbH_12_09_2026** — max-score `0.1656` (Seiten 8/8) → PASS (Toleranz 0.25)

## Fremd-Muster (informativ — GEN-1/3-Generalisierung = Sprint 4, NICHT Gate-relevant)

- # 9_745_HOWDENRE_11_06_2025 — max-score `1.0000` (Seiten 7/8)
- 10.06._INBOUND Services GmbH_Menü — max-score `1.0000` (Seiten 9/8)

## Interpretation

Der Renderer reproduziert das **Referenz-Template** (RAUMKARUSSELL, GEN 2) mit Modelldaten. Der Referenz-Self-Round-Trip ist der valide Treue-Indikator. Fremd-Muster anderer Generation/Länge weichen layout-bedingt ab — erwartet, adressiert in Sprint 4 (GEN-1/3-Token-Generalisierung + ggf. mehrere Templates).
