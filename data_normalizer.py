from typing import List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class NormalizedRecord:
    name: str
    fields: dict


@dataclass
class DataWarning:
    description: str


class DataNormalizer:
    """
    Normalizes Monday.com items WITHOUT assuming column IDs.
    Uses column TITLES so tables remain untouched.
    """

    DEAL_FIELD_ALIASES = {
        "stage": ["stage", "deal stage", "status"],
        "value": ["amount", "amount in rupees", "deal value"],
        "sector": ["sector"],
        "close_date": ["close date", "probable end date", "expected close"]
    }

    WORK_ORDER_ALIASES = {
        "status": ["execution status", "status"],
        "sector": ["sector"],
        "revenue": ["amount in rupees", "amount"],
        "close_date": ["data delivery date", "end date"]
    }

    def normalize_items(
        self,
        items: List[dict],
        column_mapping=None,
        time_range=None
    ) -> Tuple[List[NormalizedRecord], List[DataWarning]]:

        valid_records = []
        warnings = []

        for item in items:
            # Build {column_title_lower: value}
            title_map = {}
            for col in item.get("column_values", []):
                title = col.get("column", {}).get("title", "").lower()
                value = col.get("text") or col.get("value")
                title_map[title] = value

            fields = {}

            # Resolve deal fields
            for target, aliases in self.DEAL_FIELD_ALIASES.items():
                fields[target] = self._resolve(title_map, aliases)

            # Resolve work-order fields (optional overlap)
            for target, aliases in self.WORK_ORDER_ALIASES.items():
                fields.setdefault(target, self._resolve(title_map, aliases))

            # Parse numbers & dates safely
            fields["value"] = self._parse_float(fields.get("value"))
            fields["revenue"] = self._parse_float(fields.get("revenue"))
            fields["close_date"] = self._parse_date(fields.get("close_date"))

            # REQUIRED CHECK (engine contract)
            if not fields.get("sector") or not (fields.get("stage") or fields.get("status")):
                continue

            valid_records.append(
                NormalizedRecord(
                    name=item.get("name", "Unnamed"),
                    fields=fields
                )
            )

        if not valid_records:
            warnings.append(
                DataWarning(
                    description=f"{len(items)} records excluded due to missing required values"
                )
            )

        return valid_records, warnings

    def _resolve(self, title_map: dict, aliases: list):
        for alias in aliases:
            for title, value in title_map.items():
                if alias in title:
                    return value
        return None

    def _parse_float(self, value):
        try:
            if isinstance(value, str):
                return float(value.replace(",", ""))
            return float(value)
        except Exception:
            return 0.0

    def _parse_date(self, value):
        try:
            if isinstance(value, dict) and "date" in value:
                return datetime.fromisoformat(value["date"])
            if isinstance(value, str):
                return datetime.fromisoformat(value)
        except Exception:
            return None