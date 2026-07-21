#!/usr/bin/env python3
"""CLI entry point for the B2B Lead Generation Agent."""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.table import Table

from src.agent import LeadGenAgent
from src.models import LeadRequest

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="B2B Lead Generation Agent — find company candidates via Apify scrapers.",
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        help='Target company description / search keyword (e.g. "AI startup", "Luxury hotel")',
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="Geographic location (e.g. 'San Francisco, USA')",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=10,
        help="Number of companies to find (default: 10)",
    )
    parser.add_argument(
        "--industry",
        default=None,
        help="Optional LinkedIn industry ID code(s), e.g. '4' or '4,13'. "
        "Only applied when searching via LinkedIn.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a formatted table",
    )
    return parser


def print_table(result) -> None:
    console.print(f"\n[bold]Source selection:[/bold] {result.source_selection.reasoning}")
    console.print(f"[bold]Sources used:[/bold] {', '.join(result.source_selection.sources)}")
    console.print(f"[bold]Found:[/bold] {result.total_found} companies\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Company Name", min_width=25)
    table.add_column("Website", min_width=25)
    table.add_column("Source", width=12)
    table.add_column("Extra", min_width=20)

    for idx, c in enumerate(result.candidates, 1):
        extra_parts = []
        if c.linkedin_url:
            extra_parts.append("LinkedIn")
        if c.phone:
            extra_parts.append(c.phone)
        if c.employee_count:
            extra_parts.append(f"{c.employee_count} employees")
        if c.address:
            extra_parts.append(c.address[:40])

        table.add_row(
            str(idx),
            c.company_name,
            c.website or "—",
            c.source,
            " | ".join(extra_parts) or "—",
        )

    console.print(table)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    request = LeadRequest(
        target_company=args.target,
        location=args.location,
        company_count=args.count,
        industry=args.industry,
    )

    console.print(f"[bold green]Starting lead generation...[/bold green]")
    console.print(f"  Target:    {request.target_company}")
    console.print(f"  Location:  {request.location}")
    console.print(f"  Count:     {request.company_count}")
    if request.industry:
        console.print(f"  Industry:  {request.industry}")

    try:
        agent = LeadGenAgent()
        result = agent.run(request)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    if args.json:
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    else:
        print_table(result)


if __name__ == "__main__":
    main()
