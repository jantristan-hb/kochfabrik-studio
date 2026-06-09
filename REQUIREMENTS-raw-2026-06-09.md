# REQUIREMENTS-raw — Jans Brain-Dump, verbatim (2026-06-09)

> Original-Quelle der REQUIREMENTS.md. Nicht editieren — Archiv.

## Prompt 1 (Chat, 2026-06-09)

> analyiser das projekt auf bugs. schau dir die schriftarten, schriftgrößen der
> 200 beispiel pdfs an. wir wollen unsere generierten präsentationen exakt in
> der gleichen schriftart erstellen. wir wollen außerdem das ganze projekt
> einmal refactoren. lass uns ideation nutzen

## Rückfragerunde (Antworten, 2026-06-09)

- **Repo-Scope:** Beide Repos (kochfabrik-studio + pptxgenerator_v2)
- **Font-Kanon:** Open Sans kanonisch
- **Font-Treue (Server-Render vs. PPTX-Embedding):**
  > schau dir erstmal an wie wir die pptx rendern...
- **Refactor-Ziel:**
  > Tech-Debt abbauen, Struktur/Lesbarkeit, Verhalten strikt erhalten,
  > Vendoring-Modell überdenken, komplettes refactoring, neue ideenfindung,
  > ich hab das hart gevibecoded und es fehlt einiges aus der /epic checkliste.
  > wir brauchen saubere specs, nen sauberen techstack, saubere dokumente,
  > nen monorepo. schau dir an, wie wir präsentationen generieren, der user
  > soll sich live mit pngs präsentationen zusammenklicken können (die
  > suchfunktion gibts das her) etc.
