"""Import M1-1's ORIGINAL SECOM rows into Firestore.

Usage (from backend/):
  python scripts/import_secom.py ../data/raw/secom.data ../data/raw/secom_labels.data

This creates one data document per nonmissing sensor_001 measurement (1,561
expected in the M1-1 source). Six missing sensor_001 readings are intentionally
omitted; quality rates calculated from this collection will therefore cover the
imported labeled records, NOT necessarily all 1,567 original inspections.
"""
import argparse
import math
import sys
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.firestore_db import get_db
from services.data_summary import invalidate_summary


def parse_files(data_path: Path, labels_path: Path):
    with data_path.open(encoding="utf-8") as sensors, labels_path.open(encoding="utf-8") as labels:
        for i, pair in enumerate(zip_longest(sensors, labels), 1):
            sensor_row, label_row = pair
            if sensor_row is None or label_row is None:
                raise ValueError("Input files have unequal row counts")
            tokens = sensor_row.split()
            if not tokens:
                raise ValueError(f"Empty sensor row: {i}")
            raw = tokens[0]
            if raw.lower() == "nan":
                continue
            value = float(raw)
            if not math.isfinite(value):
                continue
            first, rest = label_row.strip().split(maxsplit=1)
            status = int(first)
            if status not in (-1, 1):
                raise ValueError(f"Bad quality label on row {i}: {status}")
            timestamp = datetime.strptime(rest.strip('"'), "%d/%m/%Y %H:%M:%S")
            yield f"secom_{i:04d}", {
                "date": timestamp.date().isoformat(),
                "recorded_at": timestamp.isoformat(),
                "value": value,
                "memo": "UCI SECOM 원본 / sensor_001 (익명 변수, 단위 미공개)",
                "quality_label": status,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sensor_file", type=Path)
    parser.add_argument("label_file", type=Path)
    parser.add_argument("--confirm", action="store_true", help="Actually write to Firestore")
    args = parser.parse_args()
    if not args.sensor_file.exists() or not args.label_file.exists():
        parser.error("Both original input files must exist")
    rows = list(parse_files(args.sensor_file, args.label_file))
    print(f"Parsed {len(rows)} nonmissing sensor_001 samples; first: {rows[0][0] if rows else '-'}")
    if not args.confirm:
        print("DRY RUN ONLY. Append --confirm to upload these documents to Firestore.")
        return
    db = get_db()
    for start in range(0, len(rows), 400):
        batch = db.batch()
        for doc_id, data in rows[start:start + 400]:
            batch.set(db.collection("data").document(doc_id), data)
        batch.commit()
        print(f"Committed {min(start+400, len(rows))}/{len(rows)}")
    invalidate_summary()
    print("Import complete. GET /api/data/summary now reflects Firestore data.")


if __name__ == "__main__":
    main()
