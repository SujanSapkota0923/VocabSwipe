"""Turn an uploaded word file into rows ready for the database.

Accepted shapes, one word per line or row:

    word
    word, meaning
    word, meaning 1; meaning 2; meaning 3

Commas inside a quoted field are respected, so `word, "a, b", c` keeps the
comma. A word with no meaning is flagged so the dictionary lookup can fill it
in later.
"""

import csv
import io

MAX_WORDS = 20000
MAX_MEANINGS = 3
WORD_MAX_LENGTH = 255
TEXT_EXTENSIONS = ('txt', 'csv', 'tsv')
SHEET_EXTENSIONS = ('xlsx', 'xlsm')


class ParseError(Exception):
    """The file could not be read at all."""


def _clean(value):
    return ' '.join(str(value).split()) if value is not None else ''


def _split_meanings(raw):
    """Meanings are separated by ';', or by '|' for files exported that way."""
    if not raw:
        return []
    parts = raw.replace('|', ';').split(';')
    return [m for m in (_clean(p) for p in parts) if m][:MAX_MEANINGS]


def _looks_like_header(cells):
    joined = ' '.join(_clean(c).lower() for c in cells[:2])
    return 'word' in joined or 'meaning' in joined or 'definition' in joined


def _row_to_entry(cells):
    """One spreadsheet row or one split text line -> entry dict, or None."""
    word = _clean(cells[0] if cells else '')[:WORD_MAX_LENGTH]
    if not word or word.lower() in ('nan', 'none', 'word'):
        return None

    meanings = []
    for cell in cells[1:]:
        meanings.extend(_split_meanings(_clean(cell)))
    meanings = meanings[:MAX_MEANINGS]

    return {'word': word, 'meanings': meanings, 'needs_fetch': not meanings}


def _decode(raw_bytes):
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ParseError('The file is not readable text.')


def _parse_text(raw_bytes, delimiter):
    text = _decode(raw_bytes)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    rows = list(csv.reader(lines, delimiter=delimiter))
    if rows and _looks_like_header(rows[0]):
        rows = rows[1:]

    entries = []
    for row in rows:
        # A bare word list has no delimiter at all, which csv gives back as one cell.
        entry = _row_to_entry(row)
        if entry:
            entries.append(entry)
        if len(entries) >= MAX_WORDS:
            break
    return entries


def _parse_sheet(file):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise ParseError('Spreadsheet support is not available.') from exc

    file.seek(0)
    try:
        workbook = load_workbook(file, read_only=True, data_only=True)
    except Exception as exc:
        raise ParseError(f'The spreadsheet could not be opened: {exc}') from exc

    try:
        sheet = workbook.active
        entries = []
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            cells = [c for c in row] if row else []
            if index == 0 and _looks_like_header(cells):
                continue
            entry = _row_to_entry(cells)
            if entry:
                entries.append(entry)
            if len(entries) >= MAX_WORDS:
                break
        return entries
    finally:
        workbook.close()


def parse_vocabulary_file(file):
    """Parse an uploaded file.

    Returns {'data': [{'word', 'meanings', 'needs_fetch'}, ...],
             'needs_api_fetch': bool}
    Raises ParseError when the file cannot be read.
    """
    name = getattr(file, 'name', '') or ''
    extension = name.rsplit('.', 1)[-1].lower() if '.' in name else 'txt'

    if extension in SHEET_EXTENSIONS:
        entries = _parse_sheet(file)
    elif extension in TEXT_EXTENSIONS or extension == '':
        file.seek(0)
        raw = file.read()
        if isinstance(raw, str):
            raw = raw.encode('utf-8')
        entries = _parse_text(raw, delimiter='\t' if extension == 'tsv' else ',')
    else:
        raise ParseError(f'Unsupported file type ".{extension}". Use .csv, .txt or .xlsx.')

    # Keep the first spelling of a repeated word so the deck has no duplicates.
    seen = set()
    unique = []
    for entry in entries:
        key = entry['word'].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)

    return {
        'data': unique,
        'needs_api_fetch': any(entry['needs_fetch'] for entry in unique),
    }
