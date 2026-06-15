import csv
import io


def generate_summary_csv(summaries: list[dict]) -> bytes:
    """
    Generate a CSV file from multiple document summaries.
    Returns CSV as bytes (for HTTP response).

    Columns: Document Name | Summary | Keywords | Highlights
    """
    buffer = io.StringIO()

    # Define columns
    fieldnames = [
        "Document Name",
        "Summary",
        "Keywords",
        "Highlights"
    ]

    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        quoting=csv.QUOTE_ALL  # Quote all fields to handle commas in text
    )

    # Write header row
    writer.writeheader()

    # Write one row per document
    for doc in summaries:
        writer.writerow({
            "Document Name": doc.get("name", "Unknown"),
            "Summary": doc.get("summary", ""),
            # Join lists as semicolon-separated strings
            "Keywords": " | ".join(doc.get("keywords", [])),
            "Highlights": " || ".join(doc.get("highlights", [])),
        })

    # Return as bytes
    buffer.seek(0)
    return buffer.read().encode("utf-8-sig")  # utf-8-sig for Excel compatibility