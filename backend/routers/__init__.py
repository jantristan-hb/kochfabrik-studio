"""Router-Pakete (US-053 Modularisierung). app.py komponiert per
include_router; Router importieren NICHT auf app.py (kein Zyklus —
geteilter Zustand lebt in backend.engine_glue)."""
