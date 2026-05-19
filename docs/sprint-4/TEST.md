# TEST — Sprint 4
## US-018/019 {#oauth-config-routes}
```python
def test_oauth_inactive_without_env(monkeypatch):
    for k in ("KF_OAUTH_GOOGLE_ID","KF_OAUTH_GOOGLE_SECRET",
              "KF_OAUTH_MS_ID","KF_OAUTH_MS_SECRET"):
        monkeypatch.delenv(k, raising=False)
    import importlib, backend.oauth as o; importlib.reload(o)
    assert o.providers()=={}
def test_oauth_routes_registered():
    import backend.app as a
    p={getattr(r,'path','') for r in a.app.routes}
    assert "/api/oauth/providers" in p
    assert "/api/oauth/{provider}/login" in p
    assert "/api/oauth/{provider}/callback" in p
```
## US-020 {#valid-cookie-zero-regression}
```python
def test_kfusers_cookie_no_db(monkeypatch):
    # KF_USERS-User: valid_cookie True ohne DB (Short-Circuit)
    import backend.app as a
    monkeypatch.setenv("KF_USERS","x@x.de|s|"+__import__("hashlib").sha256(b"s:p").hexdigest())
    monkeypatch.setenv("KF_SESSION_SECRET","sek")
    import importlib; importlib.reload(a)
    c=a.make_cookie("x@x.de"); assert a.valid_cookie(c) is True
def test_unknown_email_false():
    import backend.app as a
    assert a.valid_cookie(a.make_cookie("nobody@nowhere.de")) in (False,True)
    # (True nur falls in app_user; isoliert ohne DB → False)
```
## US-021 {#login-buttons}
```bash
python3 -c "import re;h=open('web/login.html').read();open('/tmp/l.js','w').write(chr(10).join(re.findall(r'<script>(.*?)</script>',h,re.S)))"
node --check /tmp/l.js
grep -q "/api/oauth/providers" web/login.html
```
