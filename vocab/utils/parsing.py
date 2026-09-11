import pandas as pd
import io
import csv


def parse_vocabulary_file(file):
    ext = file.name.split(".")[-1].lower()
    data = []
    needs_api_fetch = False  # Track if we need to fetch meanings from API

    # Try to read content for text-based formats
    if ext in ["txt", "csv"]:
        file.seek(0)
        try:
            content = file.read().decode("utf-8").splitlines()
        except UnicodeDecodeError:
            file.seek(0)
            content = file.read().decode("latin-1").splitlines()

        if not content:
            return {"data": [], "needs_api_fetch": False}

        # Skip header if first line looks like a header (contains "word" or "meaning")
        start_idx = 0
        if content and ("," in content[0] or ";" in content[0]):
            first_line = content[0].lower()
            if "word" in first_line or "meaning" in first_line:
                start_idx = 1

        for line in content[start_idx:]:
            if not line.strip():
                continue

            # Handle comma separated, semicolon separated, or just single word
            word = ""
            meanings = []

            if "," in line:
                parts = line.split(",", 1)
                word = parts[0].strip()
                meanings_raw = parts[1].strip()
                meanings = [m.strip() for m in meanings_raw.split(";") if m.strip()]
            elif ";" in line:
                parts = line.split(";", 1)
                word = parts[0].strip()
                meanings_raw = parts[1].strip()
                meanings = [m.strip() for m in meanings_raw.split(";") if m.strip()]
            else:
                word = line.strip()
                meanings = []  # No meaning found - will fetch from API

            if word and word.lower() != "word":
                # Track if any words need API fetching
                if not meanings:
                    needs_api_fetch = True
                data.append(
                    {"word": word, "meanings": meanings, "needs_fetch": not meanings}
                )

        return {"data": data, "needs_api_fetch": needs_api_fetch}

    elif ext == "xlsx":
        file.seek(0)
        try:
            df = pd.read_excel(file, header=None)
            if df.empty:
                return {"data": [], "needs_api_fetch": False}

            first_row = df.iloc[0].astype(str).str.lower().values
            start_row = 0
            if any("word" in s or "meaning" in s for s in first_row):
                start_row = 1

            for i in range(start_row, len(df)):
                row = df.iloc[i]
                word = str(row[0]).strip()
                meanings_raw = str(row[1]).strip() if len(row) > 1 else ""
                meanings = [m.strip() for m in meanings_raw.split(";") if m.strip()]
                if word and word.lower() != "nan" and word.lower() != "word":
                    # Track if this word needs API fetching
                    if not meanings:
                        needs_api_fetch = True
                    data.append(
                        {
                            "word": word,
                            "meanings": meanings,
                            "needs_fetch": not meanings,
                        }
                    )
        except Exception as e:
            print(f"Error parsing XLSX: {e}")

    return {"data": data, "needs_api_fetch": needs_api_fetch}
