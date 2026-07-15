"""Tests for the billing/access layer — no network, temp database."""
import hashlib
import hmac
import json
import time

import pytest

import spark_billing as billing


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(billing, "_DB_PATH", tmp_path / "users.db")
    yield


def test_issue_token_and_lookup():
    token = billing.issue_token("Trader@Example.com", plan="pro")
    assert token.startswith("spk_")
    user = billing.user_by_token(token)
    assert user["email"] == "trader@example.com"  # normalized
    assert user["plan"] == "pro"
    assert user["status"] == "active"


def test_reissue_keeps_same_token():
    t1 = billing.issue_token("a@b.com", plan="free")
    t2 = billing.issue_token("a@b.com", plan="pro")
    assert t1 == t2
    assert billing.user_by_token(t1)["plan"] == "pro"


def test_dev_mode_everyone_is_pro(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PRICE_ID", raising=False)
    assert not billing.live_mode()
    assert billing.effective_plan("") == "pro"
    assert billing.effective_plan("garbage") == "pro"


def test_live_mode_gates_by_plan(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_x")
    assert billing.live_mode()
    assert billing.effective_plan("") == "free"
    pro = billing.issue_token("pro@x.com", plan="pro")
    free = billing.issue_token("free@x.com", plan="free")
    assert billing.effective_plan(pro) == "pro"
    assert billing.effective_plan(free) == "free"


def test_dev_checkout_instantly_activates(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PRICE_ID", raising=False)
    out = billing.create_checkout_session("new@x.com", "http://s", "http://c")
    assert out["dev"] is True
    assert billing.user_by_token(out["token"])["plan"] == "pro"


def test_webhook_signature_roundtrip(monkeypatch):
    secret = "whsec_testsecret"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    payload = json.dumps({"type": "ping"}).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload,
                   hashlib.sha256).hexdigest()
    assert billing.verify_webhook(payload, f"t={ts},v1={sig}")
    assert not billing.verify_webhook(payload, f"t={ts},v1={'0'*64}")
    assert not billing.verify_webhook(payload, "")
    old = str(int(time.time()) - 9999)
    old_sig = hmac.new(secret.encode(), f"{old}.".encode() + payload,
                       hashlib.sha256).hexdigest()
    assert not billing.verify_webhook(payload, f"t={old},v1={old_sig}")


def test_subscription_cancel_downgrades(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_x")
    token = billing.issue_token("c@x.com", plan="pro", stripe_subscription="sub_123")
    assert billing.effective_plan(token) == "pro"
    billing.handle_webhook_event({
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_123"}},
    })
    assert billing.effective_plan(token) == "free"
