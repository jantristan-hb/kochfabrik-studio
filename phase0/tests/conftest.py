"""pytest conftest — Script-Style-Tests aus Sammlung ausschließen.

Historische Tests (test_angebot_render.py etc.) sind als Standalone-
Scripts mit `raise SystemExit` geschrieben — laufen via
`python3 tests/<file>.py`, nicht via pytest. Diese hier explizit von
pytest-Collection ausschließen, damit `pytest tests/` neue
echte pytest-Tests crawled ohne SystemExit-Crashes.
"""
collect_ignore = [
    "test_angebot_render.py",
    "test_angebot_template.py",
    "test_empty_courses.py",
    "test_frame_pick.py",
    "test_kf_classify.py",
]
