import csv

def parse_csv(file_path: str) -> list[dict]:
    rows = []
    with open(file_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows