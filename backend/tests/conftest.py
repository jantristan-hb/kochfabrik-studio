"""Sprint 1 Test-Fixtures. DB-Tests laufen nur wenn
TEST_DATABASE_URL gesetzt (sonst skip — headless ohne lokale PG).
Binding-Gate ist die Live-Smoke gegen den realen kf-studio-pg."""
import os

import pytest

DB_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not DB_URL,
                              reason="TEST_DATABASE_URL nicht gesetzt")
