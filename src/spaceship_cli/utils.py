"""
Utility functions for the Spaceship CLI.
"""

from typing import Any, Optional
from rich.console import Console
from rich.table import Table

console = Console()


def print_output(
    data: Any,
    output_format: str = "table",
    table: Optional[Table] = None,
) -> None:
    """
    Print output in either table or JSON format.

    Args:
        data: The raw data to print (for JSON output).
        output_format: The desired output format ("table" or "json").
        table: A rich Table object (for table output).
    """
    if output_format == "json":
        console.print_json(data=data)
        return

    if table:
        console.print(table)
    else:
        # Fallback if no table is provided but format is table
        console.print(data)
