import csv
from pathlib import Path


BASE_DIR = Path(__file__).parent
SOURCE = BASE_DIR / "data" / "retail_sales_dirty.csv"
CLEANED = BASE_DIR / "data" / "retail_sales_cleaned.csv"
QUALITY_LOG = BASE_DIR / "data" / "data_quality_log.csv"


def clean_data():
    with SOURCE.open(newline="", encoding="utf-8") as source_file:
        rows = list(csv.DictReader(source_file))

    cleaned_rows = []
    seen_rows = set()
    quality_log = []

    for source_row_number, row in enumerate(rows, start=2):
        original = tuple(row[field] for field in row)
        if original in seen_rows:
            quality_log.append(
                {
                    "Issue": "Duplicate",
                    "Field_Row": f"row {source_row_number}",
                    "Evidence": "Exact duplicate of an earlier complete record",
                    "Decision": "Remove duplicate",
                    "Reason": "No transaction ID exists; retained the first identical record",
                }
            )
            continue
        seen_rows.add(original)

        original_region = row["Region"]
        normalized_region = original_region.strip().title()
        if normalized_region != original_region:
            quality_log.append(
                {
                    "Issue": "Category consistency",
                    "Field_Row": f"Region, row {source_row_number}",
                    "Evidence": repr(original_region),
                    "Decision": "Standardize",
                    "Reason": f"Same region label standardized to {normalized_region}",
                }
            )
            row["Region"] = normalized_region

        original_category = row["Category"]
        if original_category == "Electronic":
            row["Category"] = "Electronics"
            quality_log.append(
                {
                    "Issue": "Category consistency",
                    "Field_Row": f"Category, row {source_row_number}",
                    "Evidence": "Electronic vs Electronics",
                    "Decision": "Standardize",
                    "Reason": "Both labels refer to the same product category",
                }
            )

        cleaned_rows.append(row)

    quality_log.extend(
        [
            {
                "Issue": "Missing value",
                "Field_Row": "Sales, row 33",
                "Evidence": "Blank Sales; Cost=640.22 and Profit=165.21",
                "Decision": "Flag",
                "Reason": "Do not infer Sales without a source record; Cost + Profit would be 805.43",
            },
            {
                "Issue": "Missing value",
                "Field_Row": "Profit, row 34",
                "Evidence": "Blank Profit; Sales=4113.60 and Cost=2321.79",
                "Decision": "Flag",
                "Reason": "Do not infer Profit without a source record; Sales - Cost would be 1791.81",
            },
            {
                "Issue": "Suspicious value",
                "Field_Row": "Quantity, row 79",
                "Evidence": "Quantity=-2",
                "Decision": "Investigate",
                "Reason": "May represent a return; changing it would alter sales volume",
            },
            {
                "Issue": "Suspicious value",
                "Field_Row": "Discount, row 57",
                "Evidence": "Discount=2.50 while most values are between 0 and 0.30",
                "Decision": "Investigate",
                "Reason": "Unit is unconfirmed; do not change 2.50 to 0.025 by assumption",
            },
        ]
    )

    with CLEANED.open("w", newline="", encoding="utf-8") as cleaned_file:
        writer = csv.DictWriter(cleaned_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(cleaned_rows)

    with QUALITY_LOG.open("w", newline="", encoding="utf-8") as log_file:
        fieldnames = ["Issue", "Field_Row", "Evidence", "Decision", "Reason"]
        writer = csv.DictWriter(log_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(quality_log)


if __name__ == "__main__":
    clean_data()