#!/usr/bin/env python3
"""
ALGO TERMINAL  —  Bloomberg-style ES Futures Algorithm Dashboard
"""

import os, sys, subprocess, threading
from datetime import datetime
from pathlib import Path

import pandas as pd
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button, DataTable, Footer, Header,
    Label, Static, ListView, ListItem
)

BASE_DIR = Path(__file__).parent
PYTHON   = str(BASE_DIR / ".venv312" / "Scripts" / "python.exe")

from algo_configs import ALGO_CONFIGS

# ── Dynamic Algo Registry ────────────────────────────────────────────────────
# We map the high-level configs to the actual scripts and results
def get_dynamic_algos():
    algos = []
    for c in ALGO_CONFIGS:
        # Clone the config to avoid mutating the original
        a = c.copy()
        # Ensure description is 'desc' for the UI
        a["desc"] = c.get("description", "No description available.")
        # Identify the script path - use the one in the config or fall back to generated
        if not a.get("script") or not Path(a["script"]).exists():
            # Try to find it in generated_algos
            gen_path = BASE_DIR / "generated_algos" / f"algo_{int(a['id']):03d}.py"
            if gen_path.exists():
                a["script"] = str(gen_path)
            else:
                # Fallback to simple name if it's there
                gen_path_simple = BASE_DIR / "generated_algos" / f"algo_{a['id']}.py"
                if gen_path_simple.exists():
                    a["script"] = str(gen_path_simple)

        # Identify CSV path if not explicitly set
        if not a.get("csv") or not Path(a["csv"]).exists():
            res_path = BASE_DIR / "results" / f"algo_{a['id']}_trades.csv"
            if res_path.exists():
                a["csv"] = str(res_path)
        
        algos.append(a)
    return algos

ALGOS = get_dynamic_algos()


def load_stats(csv_path: str | None) -> dict | None:
    if not csv_path or not Path(csv_path).exists():
        return None
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return None
        wins   = df[df["result"] == "WIN"]
        losses = df[df["result"] == "LOSS"]
        gp = wins["pnl"].sum()   if len(wins)   else 0.0
        gl = losses["pnl"].sum() if len(losses) else 0.0
        pf = abs(gp / gl)        if gl != 0     else float("inf")
        eq   = df["pnl"].cumsum()
        peak = eq.cummax()
        dd   = (eq - peak).min()
        return {
            "total_pnl":     df["pnl"].sum(),
            "win_rate":      len(wins) / len(df) * 100,
            "profit_factor": pf,
            "total_trades":  len(df),
            "avg_win":       wins["pnl"].mean()   if len(wins)   else 0.0,
            "max_drawdown":  dd,
            "df":            df,
        }
    except Exception:
        return None


# ── Stat box widget ───────────────────────────────────────────────────────────
class StatBox(Widget):
    def __init__(self, label: str, box_id: str):
        super().__init__(id=box_id, classes="stat-box")
        self._label = label

    def compose(self) -> ComposeResult:
        yield Label(self._label, classes="stat-label")
        yield Label("  —", classes="stat-value")

    def set(self, value: str, color: str = "#ffb300"):
        self.query_one(".stat-value", Label).update(f"[{color}]{value}[/{color}]")

    def reset(self):
        self.query_one(".stat-value", Label).update("  —")


# ── Main app ──────────────────────────────────────────────────────────────────
class AlgoTerminal(App):

    TITLE    = "ALGO TERMINAL"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q",     "quit",          "Quit",         priority=True),
        Binding("r",     "run_backtest",   "Run Backtest"),
        Binding("c",     "open_chart",     "Chart"),
        Binding("up",    "focus_prev",     "Up",           show=False),
        Binding("down",  "focus_next",     "Down",         show=False),
    ]

    selected: reactive[int]  = reactive(0)
    running:  reactive[bool] = reactive(False)

    # ── Layout ────────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):

            # ── Left sidebar ─────────────────────────────────────────────────
            with Vertical(id="sidebar"):
                yield Static("  ALGORITHMS", id="sidebar-title")
                yield ListView(
                    *[self._make_item(a) for a in ALGOS],
                    id="algo-list",
                )

            # ── Right main panel ─────────────────────────────────────────────
            with Vertical(id="main-panel"):
                yield Static("", id="algo-header")
                yield Static("", id="algo-desc")

                # 3×2 stats grid
                with Container(id="stats-grid"):
                    yield StatBox("TOTAL P&L",      "s-pnl")
                    yield StatBox("WIN RATE",        "s-winrate")
                    yield StatBox("PROFIT FACTOR",   "s-pf")
                    yield StatBox("TOTAL TRADES",    "s-trades")
                    yield StatBox("AVG WIN",         "s-avgwin")
                    yield StatBox("MAX DRAWDOWN",    "s-dd")

                # Action row
                with Horizontal(id="action-bar"):
                    yield Button("  RUN BACKTEST  ", id="btn-run",   variant="primary")
                    yield Button("  OPEN CHART  ",   id="btn-chart")
                    yield Static("", id="status-msg")

                # Trade log
                yield Static("  RECENT TRADES", id="log-title")
                yield DataTable(id="trade-table", cursor_type="row")

        yield Footer()

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _make_item(a: dict) -> ListItem:
        # Use simple color coding for status
        dot = "[#30d158]●[/#30d158]" if a["status"] == "LIVE" else "[#ff3b30]○[/#ff3b30]"
        # Market name fallback
        market = a.get("market", "ES=F")
        # Format for clean alignment
        label = f"  {dot} [bold white]{a['id']}[/bold white]  [dim]{a['name'][:22]:<22}[/dim]"
        return ListItem(Label(label), id=f"algo-{a['id']}")

    # ── Mount ─────────────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        t = self.query_one("#trade-table", DataTable)
        t.add_columns("DATE/TIME", "SIDE", "ENTRY", "EXIT", "P&L", "RESULT")
        self._select(0)
        self.query_one("#algo-list", ListView).focus()

    # ── Selection ─────────────────────────────────────────────────────────────
    def _select(self, idx: int) -> None:
        self.selected = idx
        a = ALGOS[idx]

        self.query_one("#algo-header", Static).update(
            f"  [{a['id']}]  {a['name']}   |   {a['market']}   |   "
            f"{a['tf']}   |   [{'green' if a['status']=='LIVE' else 'yellow'}]{a['status']}[/]"
        )
        self.query_one("#algo-desc", Static).update(f"  [dim]{a['desc']}[/dim]")

        stats = load_stats(a["csv"])
        if stats:
            pnl_col = "green" if stats["total_pnl"] >= 0 else "red"
            self.query_one("#s-pnl",     StatBox).set(f"${stats['total_pnl']:>12,.0f}", pnl_col)
            self.query_one("#s-winrate", StatBox).set(f"  {stats['win_rate']:.1f}%")
            pf_str = f"  {stats['profit_factor']:.2f}" if stats["profit_factor"] != float("inf") else "  ∞"
            self.query_one("#s-pf",      StatBox).set(pf_str)
            self.query_one("#s-trades",  StatBox).set(f"  {stats['total_trades']}")
            self.query_one("#s-avgwin",  StatBox).set(f"${stats['avg_win']:>12,.0f}", "green")
            self.query_one("#s-dd",      StatBox).set(f"${stats['max_drawdown']:>12,.0f}", "red")
            self._fill_log(stats["df"])
        else:
            for sid in ["s-pnl","s-winrate","s-pf","s-trades","s-avgwin","s-dd"]:
                self.query_one(f"#{sid}", StatBox).reset()
            self.query_one("#trade-table", DataTable).clear()

        has_script = bool(a["script"])
        has_csv    = bool(a["csv"]) and Path(a["csv"]).exists() if a["csv"] else False
        self.query_one("#btn-run",   Button).disabled = not has_script or self.running
        self.query_one("#btn-chart", Button).disabled = not has_csv

    def _fill_log(self, df: pd.DataFrame) -> None:
        t = self.query_one("#trade-table", DataTable)
        t.clear()
        for _, row in df.tail(60).iloc[::-1].iterrows():
            try:
                dt_str = pd.to_datetime(row["entry_time"]).strftime("%m-%d  %H:%M")
            except Exception:
                dt_str = str(row["entry_time"])[:13]
            pnl     = row["pnl"]
            pnl_str = f"[green]+${pnl:,.0f}[/green]" if pnl >= 0 else f"[red]-${abs(pnl):,.0f}[/red]"
            res_str = "[green]WIN[/green]" if row["result"] == "WIN" else "[red]LOSS[/red]"
            side_str = ("[cyan]LONG[/cyan]" if row["direction"] == "LONG"
                        else "[magenta]SHORT[/magenta]")
            t.add_row(dt_str, side_str, f"{row['entry']:.2f}",
                      f"{row['exit']:.2f}", pnl_str, res_str)

    # ── Events ────────────────────────────────────────────────────────────────
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("algo-"):
            aid = item_id.split("-")[1]
            idx = next((i for i, a in enumerate(ALGOS) if a["id"] == aid), 0)
            self._select(idx)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run_backtest()
        elif event.button.id == "btn-chart":
            self.action_open_chart()

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_run_backtest(self) -> None:
        if self.running:
            return
        a = ALGOS[self.selected]
        if not a["script"]:
            return
        self.running = True
        self.query_one("#btn-run",   Button).disabled = True
        self.query_one("#status-msg", Static).update("  [yellow]Running backtest...[/yellow]")

        def _run():
            try:
                subprocess.run(
                    [PYTHON, a["script"]],
                    capture_output=True, text=True, timeout=180
                )
                self.call_from_thread(self._on_done)
            except Exception as e:
                self.call_from_thread(self._on_err, str(e))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self) -> None:
        self.running = False
        t = datetime.now().strftime("%H:%M:%S")
        self.query_one("#status-msg", Static).update(f"  [green]Done  {t}[/green]")
        self.query_one("#btn-run", Button).disabled = False
        self._select(self.selected)

    def _on_err(self, err: str) -> None:
        self.running = False
        self.query_one("#status-msg", Static).update(f"  [red]Error: {err[:60]}[/red]")
        self.query_one("#btn-run", Button).disabled = False

    def action_open_chart(self) -> None:
        a = ALGOS[self.selected]
        p = a.get("chart", "")
        if p and Path(p).exists():
            os.startfile(p)

    def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    AlgoTerminal().run()
