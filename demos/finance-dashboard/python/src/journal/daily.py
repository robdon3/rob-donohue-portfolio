"""
Daily Journal — mirrors the Sheets Apps Script pattern:

  copyDataToJournal():
    - Read today's snapshot row from the control surface
    - Scan Journal date column only (ignore formula noise in other cols)
    - If today already exists → overwrite that row
    - Else → append after last real date row

Methodical by design: one day, one truth row. Re-run is safe (idempotent).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Sequence, Tuple

from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class JournalEntry:
    """One control-surface snapshot row (date + key totals)."""

    as_of: date
    assets: float
    liabilities: float
    investments: float
    net_worth: float
    note: str = ""

    def as_row(self) -> Tuple:
        return (
            self.as_of,
            self.assets,
            self.liabilities,
            self.investments,
            self.net_worth,
            self.note,
        )


@dataclass
class Journal:
    """
    In-memory stand-in for the Journal sheet.

    Column A is the only authority for "last used row" and same-day match —
    same reason as the Apps Script: other columns may hold formulas/spacers.
    """

    entries: List[JournalEntry] = field(default_factory=list)

    def last_date_index(self) -> int:
        """Index of last entry that has a real date, or -1 if empty."""
        return len(self.entries) - 1 if self.entries else -1

    def find_date(self, day: date) -> Optional[int]:
        for i, e in enumerate(self.entries):
            if e.as_of == day:
                return i
        return None

    def upsert(self, entry: JournalEntry) -> str:
        """
        Upsert by calendar day. Returns 'overwrite' | 'append'.

        This is the core of copyDataToJournal() — re-runnable without duplicates.
        """
        day = entry.as_of
        found = self.find_date(day)
        if found is not None:
            self.entries[found] = entry
            logger.info("journal overwrite as_of=%s row=%s", day, found + 1)
            return "overwrite"
        self.entries.append(entry)
        # Keep chronological order for display (script appends at end of real data)
        self.entries.sort(key=lambda e: e.as_of)
        logger.info("journal append as_of=%s rows=%s", day, len(self.entries))
        return "append"

    def to_records(self) -> List[dict]:
        return [
            {
                "as_of": e.as_of.isoformat(),
                "assets": e.assets,
                "liabilities": e.liabilities,
                "investments": e.investments,
                "net_worth": e.net_worth,
                "note": e.note,
            }
            for e in self.entries
        ]


def upsert_daily_snapshot(
    journal: Journal,
    as_of: date,
    assets: float,
    liabilities: float,
    investments: float,
    note: str = "",
) -> str:
    """Build entry from control totals and upsert — script-shaped API."""
    nw = assets + liabilities + investments
    entry = JournalEntry(
        as_of=as_of,
        assets=round(assets, 2),
        liabilities=round(liabilities, 2),
        investments=round(investments, 2),
        net_worth=round(nw, 2),
        note=note,
    )
    return journal.upsert(entry)


def journal_from_rows(rows: Sequence[dict]) -> Journal:
    j = Journal()
    for r in rows:
        raw = r.get("as_of")
        if isinstance(raw, date) and not isinstance(raw, datetime):
            d = raw
        else:
            d = date.fromisoformat(str(raw)[:10])
        j.entries.append(
            JournalEntry(
                as_of=d,
                assets=float(r["assets"]),
                liabilities=float(r["liabilities"]),
                investments=float(r["investments"]),
                net_worth=float(
                    r.get("net_worth", float(r["assets"]) + float(r["liabilities"]) + float(r["investments"]))
                ),
                note=str(r.get("note", "")),
            )
        )
    j.entries.sort(key=lambda e: e.as_of)
    return j
