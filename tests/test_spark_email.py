"""Token-email delivery + recovery endpoint — no network, providers monkeypatched."""
import pytest
from fastapi.testclient import TestClient

import spark_billing as billing
import spark_email
import trend_api


@pytest.fixture(autouse=True)
def clean_env(tmp_path, monkeypatch):
    for var in ("RESEND_API_KEY", "SMTP_HOST", "SMTP_PORT", "SMTP_USER",
                "SMTP_PASS", "SPARK_EMAIL_FROM", "SPARK_PUBLIC_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(billing, "_DB_PATH", tmp_path / "users.db")
    yield


def test_unconfigured_send_is_soft_noop():
    assert not spark_email.email_configured()
    assert spark_email.send_token_email("a@b.com", "spk_x") is False


def test_resend_path_sends_token(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    sent = {}

    class FakeResp:
        def raise_for_status(self):
            pass

    def fake_post(url, **kwargs):
        sent["url"] = url
        sent.update(kwargs)
        return FakeResp()

    monkeypatch.setattr(spark_email.requests, "post", fake_post)
    assert spark_email.email_configured()
    assert spark_email.send_token_email("buyer@x.com", "spk_tok123") is True
    assert sent["url"] == spark_email.RESEND_API
    assert sent["json"]["to"] == ["buyer@x.com"]
    assert "spk_tok123" in sent["json"]["text"]
    assert "Bearer re_test_key" == sent["headers"]["Authorization"]


def test_resend_failure_returns_false_never_raises(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")

    def boom(url, **kwargs):
        raise spark_email.requests.ConnectionError("provider down")

    monkeypatch.setattr(spark_email.requests, "post", boom)
    assert spark_email.send_token_email("buyer@x.com", "spk_tok") is False


def test_smtp_path_sends_token(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls["host"], calls["port"] = host, port

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            calls["tls"] = True

        def login(self, user, password):
            calls["login"] = (user, password)

        def send_message(self, msg):
            calls["msg"] = msg

    monkeypatch.setattr(spark_email.smtplib, "SMTP", FakeSMTP)
    assert spark_email.send_token_email("buyer@x.com", "spk_tok456") is True
    assert calls["host"] == "smtp.example.com" and calls["port"] == 587
    assert calls["tls"] is True
    assert "login" not in calls  # no SMTP_USER -> no login attempt
    assert "spk_tok456" in calls["msg"].get_content()
    assert calls["msg"]["To"] == "buyer@x.com"


def test_checkout_webhook_emails_the_token(monkeypatch):
    sent = []
    monkeypatch.setattr(billing.spark_email, "send_token_email",
                        lambda to, token: sent.append((to, token)) or True)
    billing.handle_webhook_event({
        "type": "checkout.session.completed",
        "data": {"object": {"customer_details": {"email": "buyer@x.com"},
                            "customer": "cus_1", "subscription": "sub_1"}},
    })
    user = billing.user_by_email("buyer@x.com")
    assert user and user["plan"] == "pro"
    assert sent == [("buyer@x.com", user["token"])]


def test_webhook_survives_email_blowup(monkeypatch):
    def boom(to, token):
        raise RuntimeError("smtp exploded")

    monkeypatch.setattr(billing.spark_email, "send_token_email", boom)
    billing.handle_webhook_event({
        "type": "checkout.session.completed",
        "data": {"object": {"customer_details": {"email": "buyer@x.com"}}},
    })
    assert billing.user_by_email("buyer@x.com")["plan"] == "pro"


def test_recover_endpoint_no_account_enumeration(monkeypatch):
    sent = []
    monkeypatch.setattr(trend_api.spark_email, "send_token_email",
                        lambda to, token: sent.append((to, token)) or True)
    client = TestClient(trend_api.app)
    token = billing.issue_token("known@x.com", plan="pro")

    known = client.post("/api/token/recover", json={"email": "known@x.com"})
    unknown = client.post("/api/token/recover", json={"email": "nobody@x.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()          # indistinguishable responses
    assert token not in known.text                 # token only ever travels by email
    assert sent == [("known@x.com", token)]


def test_recover_endpoint_rejects_garbage_email():
    client = TestClient(trend_api.app)
    assert client.post("/api/token/recover", json={"email": "not-an-email"}).status_code == 400
