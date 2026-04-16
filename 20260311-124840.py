"""
tracker.py — Core transaction & budget management for FinTrack.
Handles add/edit/delete transactions, budget CRUD, sample data generation.
"""

import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich import box
from rich.columns import Columns
from rich.text import Text
from rich.progress import track

console = Console()

# ── CATEGORY DEFINITIONS ─────────────────────────────────────
EXPENSE_CATEGORIES = [
    "🍔 Food & Dining",
    "🚗 Transport",
    "🏠 Housing & Rent",
    "💊 Healthcare",
    "🎮 Entertainment",
    "👗 Shopping",
    "📚 Education",
    "💡 Utilities",
    "✈️ Travel",
    "💇 Personal Care",
    "📱 Subscriptions",
    "🐾 Pets",
    "🎁 Gifts",
    "🔧 Maintenance",
    "❓ Other",
]

INCOME_CATEGORIES = [
    "💼 Salary",
    "💰 Freelance",
    "📈 Investments",
    "🏪 Business",
    "🎁 Gifts Received",
    "🏦 Bank Interest",
    "🏠 Rental Income",
    "💸 Bonus",
    "❓ Other Income",
]

SAMPLE_DESCRIPTIONS = {
    "🍔 Food & Dining":    ["Zomato order","Pizza delivery","Restaurant dinner","Grocery store","Cafe coffee","Swiggy order","Lunch at office"],
    "🚗 Transport":        ["Uber ride","Petrol fill","Auto rickshaw","Metro card recharge","Bus pass","Ola cab","Toll charge"],
    "🏠 Housing & Rent":   ["Monthly rent","Maintenance charge","Water bill","House insurance"],
    "💊 Healthcare":       ["Doctor consultation","Medicine purchase","Lab test","Dental checkup","Pharmacy"],
    "🎮 Entertainment":    ["Netflix subscription","Movie tickets","Gaming top-up","Concert tickets","OTT platform"],
    "👗 Shopping":         ["Amazon order","Myntra clothes","Flipkart purchase","Local market","Electronics"],
    "📚 Education":        ["Online course","Books purchase","Udemy course","Workshop fee"],
    "💡 Utilities":        ["Electricity bill","Internet bill","Gas cylinder","Mobile recharge"],
    "✈️ Travel":           ["Flight tickets","Hotel booking","Trip expenses","Visa fees"],
    "💇 Personal Care":    ["Haircut","Spa","Skincare","Gym membership"],
    "📱 Subscriptions":    ["Spotify","Hotstar","Adobe CC","YouTube Premium","Cloud storage"],
    "💼 Salary":           ["Monthly salary","Salary credit","Payroll"],
    "💰 Freelance":        ["Project payment","Client invoice","Consulting fee"],
    "📈 Investments":      ["Dividend received","Mutual fund return","Stock profit"],
    "💸 Bonus":            ["Performance bonus","Festival bonus","Annual appraisal"],
}


class FinanceTracker:
    """Handles transaction CRUD, budget management, and sample data."""

    def __init__(self, db):
        self.db = db

    def _get_currency(self):
        return self.db.get_setting("currency", "₹")

    # ── ADD TRANSACTION ──────────────────────────────────────
    def add_transaction(self):
        console.clear()
        console.print(Panel("[bold]💰 Add New Transaction[/]", border_style="green"))

        # Type
        t_type = Prompt.ask("Type", choices=["income", "expense"], default="expense")
        cats = INCOME_CATEGORIES if t_type == "income" else EXPENSE_CATEGORIES

        # Category picker
        console.print()
        table = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
        table.add_column("No.", style="yellow", width=4)
        table.add_column("Category")
        for i, c in enumerate(cats, 1):
            table.add_row(str(i), c)
        console.print(table)

        cat_choice = IntPrompt.ask(f"Category (1-{len(cats)})", default=1)
        cat_choice = max(1, min(cat_choice, len(cats)))
        category = cats[cat_choice - 1]

        # Amount
        cur = self._get_currency()
        amount = FloatPrompt.ask(f"Amount ({cur})")
        if amount <= 0:
            console.print("[red]Amount must be positive.[/]")
            Prompt.ask("Press Enter"); return

        # Description
        default_desc = random.choice(SAMPLE_DESCRIPTIONS.get(category, ["Transaction"]))
        description = Prompt.ask("Description", default=default_desc)

        # Date
        today = datetime.today().strftime("%Y-%m-%d")
        date_str = Prompt.ask("Date (YYYY-MM-DD)", default=today)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date format. Using today.[/]")
            date_str = today

        # Tags
        tags = Prompt.ask("Tags (comma-separated, optional)", default="")

        # Confirm
        console.print()
        console.print(Panel(
            f"[bold]Type:[/]        {t_type.upper()}\n"
            f"[bold]Category:[/]    {category}\n"
            f"[bold]Amount:[/]      {cur}{amount:,.2f}\n"
            f"[bold]Description:[/] {description}\n"
            f"[bold]Date:[/]        {date_str}\n"
            f"[bold]Tags:[/]        {tags or '—'}",
            title="[yellow]Confirm Transaction[/]",
            border_style="yellow"
        ))

        if Confirm.ask("Save this transaction?", default=True):
            txn_id = self.db.add_transaction(t_type, amount, category, description, date_str, tags)
            console.print(f"[bold green]✓ Transaction #{txn_id} saved![/]")
        else:
            console.print("[dim]Cancelled.[/]")

        Prompt.ask("\nPress Enter to continue")

    # ── VIEW TRANSACTIONS ────────────────────────────────────
    def view_transactions(self):
        console.clear()
        console.print(Panel("[bold]📋 View Transactions[/]", border_style="cyan"))

        # Filters
        console.print("[dim]Filters (leave blank to skip):[/]")
        type_filter  = Prompt.ask("Type (income/expense/all)", default="all")
        search       = Prompt.ask("Search keyword", default="")
        start        = Prompt.ask("Start date (YYYY-MM-DD)", default="")
        end          = Prompt.ask("End date (YYYY-MM-DD)", default="")
        limit_str    = Prompt.ask("Max rows to show", default="50")

        type_arg = None if type_filter == "all" else type_filter
        rows = self.db.get_transactions(
            type_=type_arg,
            start=start or None,
            end=end or None,
            limit=int(limit_str) if limit_str.isdigit() else 50,
            search=search or None,
        )

        console.clear()
        cur = self._get_currency()

        table = Table(
            title=f"Transactions ({len(rows)} records)",
            box=box.ROUNDED,
            border_style="cyan",
            show_lines=False,
        )
        table.add_column("ID",    style="dim",    width=5,  justify="right")
        table.add_column("Date",  style="white",  width=12)
        table.add_column("Type",  width=9)
        table.add_column("Category", width=22)
        table.add_column("Description", width=28, no_wrap=True)
        table.add_column("Amount", justify="right", width=14)
        table.add_column("Tags", style="dim", width=16)

        total_in, total_out = 0.0, 0.0

        for row in rows:
            is_income = row["type"] == "income"
            type_txt  = Text("↑ INCOME",  style="bold green") if is_income else Text("↓ EXPENSE", style="bold red")
            amt_txt   = Text(f"{cur}{row['amount']:,.2f}", style="green" if is_income else "red")
            if is_income: total_in  += row["amount"]
            else:          total_out += row["amount"]
            table.add_row(
                str(row["id"]),
                row["date"],
                type_txt,
                row["category"],
                row["description"] or "—",
                amt_txt,
                row["tags"] or "—",
            )

        console.print(table)
        console.print(
            f"\n  [green]Total Income:  {cur}{total_in:,.2f}[/]  "
            f"[red]Total Expenses: {cur}{total_out:,.2f}[/]  "
            f"[bold]Net: {cur}{total_in - total_out:,.2f}[/]"
        )
        console.print()

        # Sub-actions
        action = Prompt.ask("Action [D]elete  [E]dit  [Enter]=Back", default="")
        if action.upper() == "D":
            del_id = IntPrompt.ask("ID to delete")
            if self.db.delete_transaction(del_id):
                console.print("[green]✓ Deleted.[/]")
            else:
                console.print("[red]ID not found.[/]")
        elif action.upper() == "E":
            edit_id = IntPrompt.ask("ID to edit")
            self._edit_transaction(edit_id)

        Prompt.ask("Press Enter to continue")

    def _edit_transaction(self, id_: int):
        rows = self.db.get_transactions()
        row = next((r for r in rows if r["id"] == id_), None)
        if not row:
            console.print("[red]Transaction not found.[/]"); return
        console.print(f"[dim]Leave blank to keep current value[/]")
        amount = Prompt.ask(f"Amount ({row['amount']})", default=str(row["amount"]))
        desc   = Prompt.ask(f"Description ({row['description']})", default=row["description"] or "")
        date   = Prompt.ask(f"Date ({row['date']})", default=row["date"])
        tags   = Prompt.ask(f"Tags ({row['tags']})", default=row["tags"] or "")
        self.db.update_transaction(id_, amount=float(amount), description=desc, date=date, tags=tags)
        console.print("[green]✓ Updated.[/]")

    # ── BUDGET MANAGER ───────────────────────────────────────
    def budget_manager(self):
        while True:
            console.clear()
            console.print(Panel("[bold]🏦 Budget Manager[/]", border_style="yellow"))
            cur = self._get_currency()

            budgets = self.db.get_budgets()
            if budgets:
                table = Table(box=box.ROUNDED, border_style="yellow")
                table.add_column("Category",     width=24)
                table.add_column("Budget Limit", justify="right", width=14)
                table.add_column("This Month",   justify="right", width=14)
                table.add_column("Remaining",    justify="right", width=14)
                table.add_column("Used %",       justify="right", width=10)

                from datetime import date
                start = date.today().replace(day=1).strftime("%Y-%m-%d")

                for b in budgets:
                    spent = self.db.total_by_type("expense", start=start)
                    # Per-category spend
                    cat_rows = self.db.spending_by_category(start=start)
                    cat_spend = {r["category"]: r["total"] for r in cat_rows}
                    spent_cat = cat_spend.get(b["category"], 0.0)
                    remaining = b["limit_amount"] - spent_cat
                    pct       = (spent_cat / b["limit_amount"] * 100) if b["limit_amount"] else 0

                    remain_style = "red" if remaining < 0 else ("yellow" if pct > 70 else "green")
                    table.add_row(
                        b["category"],
                        f"{cur}{b['limit_amount']:,.0f}",
                        f"[red]{cur}{spent_cat:,.0f}[/]" if spent_cat > 0 else f"{cur}0",
                        f"[{remain_style}]{cur}{remaining:,.0f}[/]",
                        f"[{'red' if pct > 90 else 'yellow' if pct > 70 else 'green'}]{pct:.0f}%[/]"
                    )
                console.print(table)
            else:
                console.print("[dim]No budgets set yet.[/]\n")

            console.print("\n[1] Set Budget  [2] Delete Budget  [0] Back")
            choice = Prompt.ask("Choice", default="0")

            if choice == "1":
                cats = EXPENSE_CATEGORIES
                for i, c in enumerate(cats, 1):
                    console.print(f"  [yellow]{i}[/] {c}")
                idx = IntPrompt.ask(f"Category (1-{len(cats)})", default=1)
                idx = max(1, min(idx, len(cats)))
                cat = cats[idx - 1]
                limit = FloatPrompt.ask(f"Monthly budget for {cat} ({cur})")
                self.db.set_budget(cat, limit)
                console.print(f"[green]✓ Budget set: {cat} → {cur}{limit:,.0f}[/]")
                Prompt.ask("Press Enter")
            elif choice == "2":
                cat = Prompt.ask("Category name to delete")
                self.db.delete_budget(cat)
                console.print("[green]✓ Deleted.[/]")
                Prompt.ask("Press Enter")
            elif choice == "0":
                break

    # ── SAMPLE DATA ──────────────────────────────────────────
    def generate_sample_data(self):
        console.print()
        count = 0
        today = datetime.today()

        expense_data = [
            ("🍔 Food & Dining",   80,  900,  0.28),
            ("🚗 Transport",       50,  500,  0.18),
            ("🛍️ Shopping",        200, 3000, 0.12),
            ("💡 Utilities",       300, 1500, 0.08),
            ("🎮 Entertainment",   100, 800,  0.10),
            ("💊 Healthcare",      200, 2000, 0.06),
            ("📚 Education",       299, 2000, 0.05),
            ("📱 Subscriptions",   99,  599,  0.06),
            ("✈️ Travel",          1000,8000, 0.03),
            ("💇 Personal Care",   200, 1200, 0.04),
        ]

        # Generate 90 days of transactions
        for day_offset in track(range(90), description="[cyan]Generating sample data..."):
            txn_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")

            # Monthly salary on 1st
            if (today - timedelta(days=day_offset)).day == 1:
                self.db.add_transaction(
                    "income",
                    round(random.uniform(45000, 75000), 2),
                    "💼 Salary",
                    random.choice(SAMPLE_DESCRIPTIONS["💼 Salary"]),
                    txn_date,
                    "recurring"
                )
                count += 1

            # Occasional freelance
            if random.random() < 0.04:
                self.db.add_transaction(
                    "income",
                    round(random.uniform(5000, 25000), 2),
                    "💰 Freelance",
                    random.choice(SAMPLE_DESCRIPTIONS["💰 Freelance"]),
                    txn_date,
                    "freelance"
                )
                count += 1

            # Daily expenses
            for cat, min_amt, max_amt, prob in expense_data:
                if random.random() < prob:
                    descs = SAMPLE_DESCRIPTIONS.get(cat, ["Purchase"])
                    self.db.add_transaction(
                        "expense",
                        round(random.uniform(min_amt, max_amt), 2),
                        cat,
                        random.choice(descs),
                        txn_date,
                        ""
                    )
                    count += 1

        console.print(f"\n[bold green]✓ Generated {count} sample transactions over 90 days![/]")
        Prompt.ask("Press Enter to continue")