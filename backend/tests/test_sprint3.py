"""Sprint 3 — Akzeptanz (US-012..017). Graceful/Registrierung immer;
DB-Integration live gegen kf-studio-pg (binding gate)."""
import backend.app as a


def test_s3_endpoints_registered():
    paths = {getattr(r, "path", "") for r in a.app.routes}
    assert "/api/stats" in paths
    assert "/api/kunden" in paths
    assert "/api/kunde/{customer_id}" in paths


def test_store_s3_api_present():
    from backend import store
    for fn in ("stats", "list_customers", "get_customer"):
        assert callable(getattr(store, fn))
    import inspect
    sig = inspect.signature(store.list_offers)
    assert "q" in sig.parameters and "status" in sig.parameters
