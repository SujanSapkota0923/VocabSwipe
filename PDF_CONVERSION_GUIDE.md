# PDF to Vocabulary Converter - Quick Guide

## For Future PDF Conversions

### Quick Start

1. **Place your PDF** in an accessible location (Desktop, Downloads, etc.)

2. **Run the converter script:**

   ```bash
   cd /Users/sujan/Desktop/Projects/VocabSwipe
   source venv/bin/activate
   python convert_pdf_to_vocab.py <path_to_your_pdf>
   ```

3. **Upload the generated file** to VocabSwipe

### Examples

```bash
# Convert a PDF from Desktop
python convert_pdf_to_vocab.py ~/Desktop/vocabulary.pdf

# Convert with custom output name
python convert_pdf_to_vocab.py ~/Desktop/words.pdf my_custom_name

# Convert from current directory
python convert_pdf_to_vocab.py vocabulary_list.pdf
```

### What the Script Does

✅ Automatically detects PDF format (numbered or line-by-line)  
✅ Extracts all vocabulary words  
✅ Removes duplicates and artifacts  
✅ Creates both CSV and TXT files  
✅ Shows preview of extracted words  
✅ Estimates upload time

### Output Files

The script creates two files:

- `filename.csv` - CSV format with header
- `filename.txt` - Plain text (one word per line)

Both work with VocabSwipe's auto-fetch feature!

### Supported PDF Formats

1. **Numbered format**: `1word2word3word...`
2. **Line-by-line**: One word per line
3. **Mixed formats**: Automatically detects best approach

### Troubleshooting

**No words extracted?**

- Check if PDF is text-based (not scanned image)
- Try opening PDF to verify it contains readable text
- Some PDFs may need OCR (Optical Character Recognition) first

**Wrong words extracted?**

- Open the generated `.txt` file to verify
- Edit manually if needed (just delete bad lines)
- Re-save and upload

**Upload takes too long?**

- This is normal for large word lists
- ~0.5 seconds per word for API fetching
- 3000 words = ~25 minutes
- Don't close the browser during upload!

### Pro Tips

💡 **Test with small files first** - Try with 10-20 words to verify format  
💡 **Check the preview** - Script shows first/last words before saving  
💡 **Edit if needed** - TXT files are easy to manually edit  
💡 **Keep originals** - Don't delete the PDF after conversion

---

## File Location

The converter script is located at:

```
/Users/sujan/Desktop/Projects/VocabSwipe/convert_pdf_to_vocab.py
```

Keep this file for future use!
