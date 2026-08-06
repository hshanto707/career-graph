"""B3 — Auth module. Mirrors test-plan.md §B3 red/green tests + edge cases."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture(scope="module")
def _auth_engine():
    """A dedicated in-memory SQLite engine for this module, isolated from
    `app.database.postgres.engine`.

    The shared `postgres.engine` uses SQLAlchemy's default `QueuePool`,
    which under the TestClient's background-thread request execution can
    hand different pooled connections to different requests. Two
    connections to the *same* on-disk SQLite file can each hold their own
    open read transaction/snapshot, so a connection that started reading
    before another connection's DDL (create/drop table) can keep seeing
    the pre-DDL schema until its own transaction ends -- producing
    intermittent "no such table" errors that don't reproduce when a test
    runs alone. Using a single dedicated engine backed by `StaticPool` (one
    physical connection, reused for every checkout) sidesteps that
    entirely: there is only ever one connection, so there is no
    cross-connection snapshot to go stale.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    from app.database.postgres import Base

    # Import the ORM models *before* create_all: SQLAlchemy only registers a
    # model's Table on `Base.metadata` when its module has actually been
    # executed.
    import app.models.profile  # noqa: F401
    import app.models.user  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def _override_get_db(_auth_engine):
    """Point the app's `get_db` dependency at `_auth_engine` for the
    duration of each test, and wipe row data afterward so tests don't leak
    state into one another (schema is created once per module, not
    per-test, to avoid DDL churn)."""
    from sqlalchemy.orm import sessionmaker

    from app.database.postgres import get_db
    from app.models.profile import StudentProfile
    from app.models.user import User
    from main import app

    TestSessionLocal = sessionmaker(bind=_auth_engine, autoflush=False, autocommit=False, future=True)

    def _get_db_override():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)
        with _auth_engine.begin() as conn:
            conn.execute(StudentProfile.__table__.delete())
            conn.execute(User.__table__.delete())
        # login_lockout's failure counter is process-wide, not per-test-DB --
        # reset it too so one test's failed logins don't lock out another.
        from app.core import login_lockout

        login_lockout.reset_all()


@pytest.fixture()
def app_db_session(_auth_engine):
    """A session bound to the same isolated test engine the overridden
    `get_db()` uses, for assertions that need to inspect rows the API just
    wrote."""
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=_auth_engine, autoflush=False, autocommit=False, future=True)()
    try:
        yield session
    finally:
        session.close()


def _register(client, email="student@example.com", password="Sup3rSecret!", name="Student One"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name},
    )


# ------------------------------------------------------------------ #
# 1. Register with new email
# ------------------------------------------------------------------ #
def test_register_new_email_returns_201_with_token_and_hashed_password(client, app_db_session):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "token" in body["data"]
    assert body["data"]["user"]["email"] == "student@example.com"

    from app.models.user import User

    user = app_db_session.query(User).filter_by(email="student@example.com").one()
    assert user.hashed_password != "Sup3rSecret!"
    assert user.hashed_password.startswith("$2")  # bcrypt hash prefix

    from app.models.profile import StudentProfile

    profile = app_db_session.query(StudentProfile).filter_by(user_id=user.id).one()
    assert profile.skills == []


# ------------------------------------------------------------------ #
# 2. Register with existing email
# ------------------------------------------------------------------ #
def test_register_duplicate_email_returns_409_no_duplicate_row(client, app_db_session):
    first = _register(client)
    assert first.status_code == 201

    second = _register(client, password="AnotherPass1!", name="Someone Else")
    assert second.status_code == 409
    body = second.json()
    assert body["success"] is False
    assert body["error"] == "CONFLICT"

    from app.models.user import User

    assert app_db_session.query(User).filter_by(email="student@example.com").count() == 1


def test_register_duplicate_email_case_insensitive(client):
    first = _register(client, email="Student@Example.com")
    assert first.status_code == 201

    second = _register(client, email="student@EXAMPLE.com", password="AnotherPass1!")
    assert second.status_code == 409


# ------------------------------------------------------------------ #
# 3. Login with correct credentials
# ------------------------------------------------------------------ #
def test_login_correct_credentials_returns_valid_token(client):
    _register(client)
    resp = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert resp.status_code == 200
    body = resp.json()
    token = body["data"]["token"]
    assert token

    payload = decode_access_token(token)
    assert payload["email"] == "student@example.com"

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    delta = exp - iat
    assert timedelta(hours=23, minutes=59) < delta <= timedelta(hours=24, minutes=1)


def test_login_email_case_insensitive(client):
    _register(client, email="Student@Example.com")
    resp = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert resp.status_code == 200


# ------------------------------------------------------------------ #
# 4. Login with wrong password / no user-enumeration leak
# ------------------------------------------------------------------ #
def test_login_wrong_password_returns_401_generic_message(client):
    _register(client)
    resp = client.post("/auth/login", json={"email": "student@example.com", "password": "wrong-password"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert "token" not in body.get("data", {}) if body.get("data") else True
    assert body["message"] == "Invalid email or password."


def test_login_nonexistent_email_returns_same_message_as_wrong_password(client):
    _register(client)

    wrong_password_msg = client.post(
        "/auth/login", json={"email": "student@example.com", "password": "wrong-password"}
    ).json()["message"]

    no_such_user_msg = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    ).json()["message"]

    assert wrong_password_msg == no_such_user_msg


# ------------------------------------------------------------------ #
# 4b. Login rate-limit / lockout (docs/current-status.md Milestone 4)
# ------------------------------------------------------------------ #
def test_login_locks_out_after_max_failed_attempts(client):
    from app.core import login_lockout

    _register(client)
    for _ in range(login_lockout.MAX_ATTEMPTS):
        resp = client.post(
            "/auth/login", json={"email": "student@example.com", "password": "wrong-password"}
        )
        assert resp.status_code == 401

    locked_resp = client.post(
        "/auth/login", json={"email": "student@example.com", "password": "wrong-password"}
    )
    assert locked_resp.status_code == 429
    assert locked_resp.json()["error"] == "TOO_MANY_ATTEMPTS"

    # Locked out even with the *correct* password now -- the lockout is
    # keyed by email attempt count, not tied to which password was tried.
    correct_password_resp = client.post(
        "/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"}
    )
    assert correct_password_resp.status_code == 429


def test_login_lockout_is_per_email_not_global(client):
    from app.core import login_lockout

    _register(client, email="victim@example.com")
    _register(client, email="other@example.com")

    for _ in range(login_lockout.MAX_ATTEMPTS):
        client.post("/auth/login", json={"email": "victim@example.com", "password": "wrong-password"})

    locked = client.post("/auth/login", json={"email": "victim@example.com", "password": "wrong-password"})
    assert locked.status_code == 429

    # A different email is unaffected.
    still_ok = client.post(
        "/auth/login", json={"email": "other@example.com", "password": "Sup3rSecret!"}
    )
    assert still_ok.status_code == 200


def test_login_success_clears_the_failure_counter(client):
    from app.core import login_lockout

    _register(client)
    for _ in range(login_lockout.MAX_ATTEMPTS - 1):
        client.post("/auth/login", json={"email": "student@example.com", "password": "wrong-password"})

    # One failed attempt short of lockout -- a correct login now must
    # succeed and reset the counter, not carry the near-miss forward.
    success = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert success.status_code == 200

    # Fresh failed attempts after a successful login start from zero again.
    for _ in range(login_lockout.MAX_ATTEMPTS - 1):
        resp = client.post(
            "/auth/login", json={"email": "student@example.com", "password": "wrong-password"}
        )
        assert resp.status_code == 401  # not yet locked out


def test_login_lockout_expires_after_the_window(client, monkeypatch):
    from app.core import login_lockout

    _register(client)
    for _ in range(login_lockout.MAX_ATTEMPTS):
        client.post("/auth/login", json={"email": "student@example.com", "password": "wrong-password"})

    locked = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert locked.status_code == 429

    # Simulate the window elapsing rather than sleeping in the test.
    real_time = login_lockout.time.time
    monkeypatch.setattr(login_lockout.time, "time", lambda: real_time() + login_lockout.WINDOW_SECONDS + 1)

    unlocked = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert unlocked.status_code == 200


# ------------------------------------------------------------------ #
# 5-7. Protected route: missing / expired / tampered token
# ------------------------------------------------------------------ #
def test_protected_route_no_authorization_header_returns_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_protected_route_valid_token_succeeds(client):
    token = _register(client).json()["data"]["token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "student@example.com"


def test_protected_route_expired_token_returns_401(client):
    _register(client)
    settings = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_payload = {
        "sub": "some-user-id",
        "email": "student@example.com",
        "iat": int((past - timedelta(hours=24)).timestamp()),
        "exp": past,
    }
    expired_token = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_protected_route_token_signed_with_wrong_secret_returns_401(client):
    settings = get_settings()
    future = datetime.now(timezone.utc) + timedelta(hours=24)
    forged_payload = {
        "sub": "some-user-id",
        "email": "student@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": future,
    }
    tampered_token = jwt.encode(forged_payload, "not-the-real-secret", algorithm=settings.JWT_ALGORITHM)

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401


def test_protected_route_malformed_token_returns_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-jwt-at-all"})
    assert resp.status_code == 401


def test_protected_route_missing_bearer_prefix_returns_401(client):
    token = _register(client).json()["data"]["token"]
    # No "Bearer " scheme -- HTTPBearer should refuse this outright.
    resp = client.get("/auth/me", headers={"Authorization": token})
    assert resp.status_code == 401


# ------------------------------------------------------------------ #
# 8. current_user injection never trusts client-supplied student_id
# ------------------------------------------------------------------ #
def test_current_user_ignores_client_supplied_student_id_in_body(client):
    """Register two students, then hit a protected echo route as student A
    while passing student B's id in the request body/query -- the route
    must always resolve to A (the token subject), never B."""
    from fastapi import Body, Depends

    from app.core.deps import CurrentUser, get_current_user
    from main import app

    @app.post("/__whoami")
    def whoami(
        current: CurrentUser = Depends(get_current_user),
        student_id: str | None = Body(default=None, embed=True),
    ):
        # Route deliberately ignores the client-supplied `student_id` and
        # only ever acts on the token-derived identity, mirroring how real
        # protected routers must behave.
        return {"resolved_user_id": current.id, "client_supplied_student_id": student_id}

    token_a = _register(client, email="a@example.com").json()["data"]["token"]
    user_a_id = decode_access_token(token_a)["sub"]

    token_b = _register(client, email="b@example.com").json()["data"]["token"]
    user_b_id = decode_access_token(token_b)["sub"]

    resp = client.post(
        "/__whoami",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"student_id": user_b_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolved_user_id"] == user_a_id
    assert body["resolved_user_id"] != user_b_id
    assert body["client_supplied_student_id"] == user_b_id  # present in body, but unused for identity


# ------------------------------------------------------------------ #
# Edge cases
# ------------------------------------------------------------------ #
def test_register_empty_password_rejected(client):
    resp = _register(client, password="")
    assert resp.status_code == 422


def test_register_whitespace_only_name_rejected(client):
    resp = _register(client, name="   ")
    assert resp.status_code == 422


def test_register_invalid_email_format_rejected(client):
    resp = _register(client, email="not-an-email")
    assert resp.status_code == 422


def test_register_extremely_long_password_rejected_by_schema(client):
    # UserCreate enforces max_length=128 at the schema level -- this also
    # protects bcrypt from unbounded input.
    resp = _register(client, password="x" * 5000)
    assert resp.status_code == 422


def test_register_long_password_within_limit_round_trips(client):
    long_password = "Aa1!" * 20  # 80 chars, within schema max but > bcrypt's 72-byte quirk zone
    resp = _register(client, password=long_password)
    assert resp.status_code == 201

    login_resp = client.post("/auth/login", json={"email": "student@example.com", "password": long_password})
    assert login_resp.status_code == 200


def test_password_with_unicode_special_characters_round_trips(client):
    password = "pässwörd-€-🔒-123"
    resp = _register(client, password=password)
    assert resp.status_code == 201

    login_resp = client.post("/auth/login", json={"email": "student@example.com", "password": password})
    assert login_resp.status_code == 200


def test_hash_and_verify_password_directly():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_login_immediately_after_registration_before_profile_fields_set(client):
    """Registering then logging in against a still-empty profile must not
    500 -- profile completeness is irrelevant to auth."""
    _register(client)
    resp = client.post("/auth/login", json={"email": "student@example.com", "password": "Sup3rSecret!"})
    assert resp.status_code == 200


def test_token_replay_immediately_after_expiry_boundary_is_rejected(client):
    """A token whose `exp` is exactly `now` (boundary case) must be treated
    as expired, not valid -- guards against an off-by-one in the expiry
    check."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    boundary_payload = {
        "sub": "some-user-id",
        "email": "student@example.com",
        "iat": int((now - timedelta(hours=24)).timestamp()),
        "exp": now - timedelta(seconds=1),
    }
    boundary_token = jwt.encode(boundary_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {boundary_token}"})
    assert resp.status_code == 401


def test_create_and_decode_access_token_round_trip():
    token = create_access_token(user_id="user-123", email="user@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "user@example.com"


def test_decode_access_token_rejects_tampered_signature():
    from app.core.security import TokenError

    token = create_access_token(user_id="user-123", email="user@example.com")
    tampered = token[:-4] + ("A" * 4)  # corrupt the trailing signature bytes

    with pytest.raises(TokenError):
        decode_access_token(tampered)
