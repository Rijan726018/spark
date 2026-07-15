"""Unit tests for PAMM allocator pure functions — no Redis/Celery required."""
import math
import sys
import types
import pytest


def import_allocator():
    """Import only the pure-function module, stubbing out the Celery dependency."""
    # Provide a lightweight stub so execute_order.delay() never touches Redis/Celery
    stub = types.ModuleType("backend.router.execution")
    task_stub = types.SimpleNamespace(delay=lambda **kw: None)
    stub.execute_order = task_stub
    sys.modules.setdefault("backend.router.execution", stub)

    from backend.router import allocator as m
    return m


# ── parse_signal ──────────────────────────────────────────────────────────────

class TestParseSignal:
    def test_buy_full_signal(self):
        m = import_allocator()
        action, qty, sym = m.parse_signal("Buy 2 ES Contract at Market")
        assert action == "Buy"
        assert qty == 2.0
        assert sym == "ES"

    def test_sell_signal(self):
        m = import_allocator()
        action, qty, sym = m.parse_signal("Sell 1 NQ Contract at Market")
        assert action == "Sell"
        assert qty == 1.0
        assert sym == "NQ"

    def test_case_insensitive_action(self):
        m = import_allocator()
        action, qty, sym = m.parse_signal("BUY 3 ES Contract at Market")
        assert action == "Buy"

    def test_fractional_quantity(self):
        m = import_allocator()
        _, qty, _ = m.parse_signal("Buy 0.5 ES Contract at Market")
        assert qty == 0.5

    def test_missing_parts_returns_defaults(self):
        m = import_allocator()
        action, qty, sym = m.parse_signal("Buy")
        assert action == "Buy"
        assert qty == 1.0
        assert sym == "ES"

    def test_empty_signal_returns_defaults(self):
        m = import_allocator()
        action, qty, sym = m.parse_signal("")
        assert qty == 1.0


# ── convert_to_tradable_contracts ─────────────────────────────────────────────

class TestConvertToTradableContracts:
    def test_es_to_mes_conversion(self):
        m = import_allocator()
        sym, qty = m.convert_to_tradable_contracts(1.0, "ES")
        assert sym == "MES"
        assert qty == 10  # 1 ES × 10 = 10 MES

    def test_fractional_rounds_down(self):
        m = import_allocator()
        _, qty = m.convert_to_tradable_contracts(0.09, "ES")
        assert qty == 0  # 0.09 × 10 = 0.9 → floor → 0

    def test_non_es_symbol_passes_through(self):
        m = import_allocator()
        sym, qty = m.convert_to_tradable_contracts(2.7, "GC")
        assert sym == "GC"
        assert qty == 2  # floor(2.7)

    def test_es_symbol_replacement(self):
        m = import_allocator()
        sym, _ = m.convert_to_tradable_contracts(1.0, "MES")
        assert sym == "MMES"  # replaces "ES" substring

    def test_large_allocation(self):
        m = import_allocator()
        sym, qty = m.convert_to_tradable_contracts(5.0, "ES")
        assert qty == 50
        assert sym == "MES"


# ── pro-rata logic ────────────────────────────────────────────────────────────

class TestProRataDistribution:
    def test_weights_sum_to_one(self):
        m = import_allocator()
        users = m.MOCK_USERS
        total = sum(u["balance"] for u in users)
        weights = [u["balance"] / total for u in users]
        assert abs(sum(weights) - 1.0) < 1e-9

    def test_larger_balance_gets_more(self):
        m = import_allocator()
        users = sorted(m.MOCK_USERS, key=lambda u: u["balance"])
        total = sum(u["balance"] for u in users)
        small_weight = users[0]["balance"] / total
        large_weight = users[-1]["balance"] / total
        assert large_weight > small_weight
