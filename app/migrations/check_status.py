# app/migrations/check_status.py
from pathlib import Path
import sqlite3
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

ROOT = Path(__file__).resolve().parents[2]
DB   = ROOT / "data" / "data.db"

console = Console()

def main():
    if not DB.exists():
        console.print(f"[red]DB not found:[/red] {DB}")
        return

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()

        # шапка
        console.print(Panel.fit(f"[bold cyan]SQLite check[/bold cyan]\n{DB}", border_style="cyan"))

        # проверим наличие колонки и посчитаем статусы
        tables = ["grants", "courses", "scholarships", "nonprofits"]
        t = Table(title="Status by table", box=box.SIMPLE_HEAVY)
        t.add_column("Table", style="bold")
        t.add_column("Has 'status' column?", justify="center")
        t.add_column("published", justify="right")
        t.add_column("draft", justify="right")
        t.add_column("other/NULL", justify="right")

        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cur.fetchall()]
            has_status = "status" in cols

            counts = defaultdict(int)
            if has_status:
                cur.execute(f"SELECT status, COUNT(*) FROM {table} GROUP BY status")
                for s, c in cur.fetchall():
                    counts[str(s)] += c

            # раскрасим
            has_col = "[green]yes[/green]" if has_status else "[red]no[/red]"
            pub = f"[green]{counts.get('published', 0)}[/green]"
            drf = f"[yellow]{counts.get('draft', 0)}[/yellow]"
            other = counts.get('None', 0) + sum(
                c for s, c in counts.items() if s not in ("published", "draft", "None")
            )
            other_s = f"[red]{other}[/red]" if other else "0"

            t.add_row(table, has_col, pub, drf, other_s)

        console.print(t)

        console.print("\nLegend: [green]published[/green], [yellow]draft[/yellow], [red]missing/other[/red]")

if __name__ == "__main__":
    main()
