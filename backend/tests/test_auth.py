"""Authentication tests: register, login, refresh flow, logout, role guards."""

from .conftest import TEST_PASSWORD, auth_headers, make_user


def test_register_returns_token_pair(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": "new@test.pk", "password": "strong-pass-1", "role": "ngo"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["role"] == "ngo"


def test_register_duplicate_email_conflict(client, db):
    make_user(db, email="dup@test.pk")
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Dup", "email": "dup@test.pk", "password": "strong-pass-1"},
    )
    assert res.status_code == 409


def test_register_password_is_hashed(client, db):
    from app.models import User

    client.post(
        "/api/v1/auth/register",
        json={"name": "Hash Check", "email": "hash@test.pk", "password": "strong-pass-1"},
    )
    user = db.query(User).filter(User.email == "hash@test.pk").first()
    assert user is not None
    assert user.password_hash != "strong-pass-1"
    assert user.password_hash.startswith("$2b$")


def test_login_success(client, db):
    make_user(db, role="authority", email="auth@test.pk")
    res = client.post("/api/v1/auth/login", json={"email": "auth@test.pk", "password": TEST_PASSWORD})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["role"] == "authority"


def test_login_wrong_password_401(client, db):
    make_user(db, email="wrong@test.pk")
    res = client.post("/api/v1/auth/login", json={"email": "wrong@test.pk", "password": "nope"})
    assert res.status_code == 401


def test_login_unknown_email_401(client, db):
    res = client.post("/api/v1/auth/login", json={"email": "nobody@test.pk", "password": "whatever"})
    assert res.status_code == 401


def test_refresh_flow_issues_new_access_token(client, db):
    make_user(db, role="ngo", email="refresh@test.pk")
    login = client.post("/api/v1/auth/login", json={"email": "refresh@test.pk", "password": TEST_PASSWORD})
    refresh_token = login.json()["refresh_token"]

    res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200, res.text
    new_access = res.json()["access_token"]
    assert new_access

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "refresh@test.pk"


def test_refresh_with_invalid_token_401(client, db):
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})
    assert res.status_code == 401


def test_refresh_with_access_token_401(client, db):
    make_user(db, email="accesstest@test.pk")
    login = client.post("/api/v1/auth/login", json={"email": "accesstest@test.pk", "password": TEST_PASSWORD})
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": login.json()["access_token"]})
    assert res.status_code == 401


def test_refresh_token_cannot_access_api(client, db):
    """A refresh-type token must be rejected as an API credential."""
    make_user(db, email="reftest2@test.pk")
    login = client.post("/api/v1/auth/login", json={"email": "reftest2@test.pk", "password": TEST_PASSWORD})
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['refresh_token']}"},
    )
    assert res.status_code == 401


def test_me_requires_auth(client, db):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_returns_200(client, db):
    user = make_user(db)
    res = client.post("/api/v1/auth/logout", headers=auth_headers(client, user))
    assert res.status_code == 200


def test_role_guard_public_cannot_list_users(client, db):
    user = make_user(db, role="public")
    res = client.get("/api/v1/users", headers=auth_headers(client, user))
    assert res.status_code == 403


def test_role_guard_authority_can_list_users(client, db):
    user = make_user(db, role="authority")
    res = client.get("/api/v1/users", headers=auth_headers(client, user))
    assert res.status_code == 200
    assert "items" in res.json()
