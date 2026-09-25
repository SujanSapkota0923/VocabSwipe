# Offline helpers

Command-line tools for preparing word files before uploading them. The web app
does not import or need them. They use `PyPDF2`, which `requirements.txt` does
not install:

```bash
pip install PyPDF2
```

## `convert_pdf_to_vocab.py`

Extracts words from a text-based PDF and writes `<name>.csv` (with a `word`
header) and `<name>.txt` (one word per line). It handles numbered lists
(`1word2word3word…`) and one word per line, drops duplicates and shows a
preview.

```bash
python scripts/convert_pdf_to_vocab.py path/to/vocabulary.pdf [output_name]
```

Scanned PDFs have no text layer and need OCR first. Check the `.txt` output
and delete bad lines by hand before uploading.

## `split_vocab_file.py`

Splits a one-word-per-line file into smaller files (default 500 words each).
Useful for bare-word lists, because each word without a meaning costs a
dictionary lookup of about half a second.

```bash
python scripts/split_vocab_file.py words.txt [words_per_file]
```
