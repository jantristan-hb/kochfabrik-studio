# TEST — Sprint 3 (pytest + JS-check)

> `backend/tests/test_sprint3.py`. DB-Tests via TEST_DATABASE_URL
> (conftest S2-Fixtures). Binding-Gate bleibt Live-Smoke.

## US-012 {#us-012-stats-endpoint}
```python
@needs_db
@pytest.mark.asyncio
async def test_stats_owner_scoped():
    from backend.store import save_offer, stats
    await save_offer("a@s3.de", {"kunde":"K","veranstaltung":{},
        "bloecke":[{"zwischensumme":100.0}]})
    await save_offer("b@s3.de", {"kunde":"Z","veranstaltung":{}})
    s = await stats("a@s3.de")
    assert s["angebote"]==1 and s["kunden"]==1
    assert s["volumen"]==100.0 and len(s["letzte"])<=5
def test_stats_endpoint_registered():
    import backend.app as a
    assert any(getattr(r,"path","")=="/api/stats" for r in a.app.routes)
```

## US-013 {#us-013-kunden-endpoints}
```python
@needs_db
@pytest.mark.asyncio
async def test_kunden_list_and_detail_owner():
    from backend.store import save_offer, list_customers, get_customer
    r=await save_offer("a@s3.de",{"kunde":"KundeK","veranstaltung":{}})
    ks=await list_customers("a@s3.de")
    assert any(k["name"]=="KundeK" for k in ks)
    cid=[k["customer_id"] for k in ks if k["name"]=="KundeK"][0]
    d=await get_customer("a@s3.de",cid)
    assert d and any(o["offer_id"]==r["offer_id"] for o in d["angebote"])
    assert await get_customer("b@s3.de",cid) is None      # fremd
```

## US-014 {#us-014-angebote-filter}
```python
@needs_db
@pytest.mark.asyncio
async def test_list_offers_filter():
    from backend.store import save_offer, list_offers
    await save_offer("a@s3.de",{"kunde":"Sommerfirma",
        "veranstaltung":{"anlass":"Sommerfest"}})
    assert len(await list_offers("a@s3.de", q="somm"))>=1
    assert await list_offers("a@s3.de", q="zzznope")==[]
    assert len(await list_offers("a@s3.de"))>=1            # abwärtskompat
```

## US-015 / US-016 / US-017 {#us-015-dashboard}{#us-016-bibliothek}{#us-017-kunden-crm}
```bash
# JS-Syntax + Verdrahtung (kein DB):
for p in index bibliothek kunden; do
  python3 - "$p" <<'PY'
import re,sys;h=open(f"web/{sys.argv[1]}.html").read()
open("/tmp/x.js","w").write("\n".join(re.findall(r"<script>(.*?)</script>",h,re.S)) or "void 0")
PY
  node --check /tmp/x.js || exit 1
done
grep -q "/api/stats" web/index.html
grep -q "/api/angebote" web/bibliothek.html
grep -q "/api/kunden" web/kunden.html
grep -q "chat.html?offer=" web/bibliothek.html web/index.html web/kunden.html
# client.html unverändert (US-017 Regression):
git diff --quiet -- web/client.html && echo "client.html unangetastet OK"
```

**Fixtures:** conftest (S2) `needs_db` + async session. store.* binden
zur Importzeit an DATABASE_URL → CI: DATABASE_URL=TEST_DATABASE_URL.
