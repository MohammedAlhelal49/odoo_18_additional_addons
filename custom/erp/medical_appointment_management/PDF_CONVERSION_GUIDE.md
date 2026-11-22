# PDF Conversion Guide for Documentation

## Overview
You now have 4 markdown files that need to be converted to PDF:

1. **USER_MANUAL.md** (English) → **USER_MANUAL.pdf**
2. **USER_MANUAL_AR.md** (Arabic) → **USER_MANUAL_AR.pdf**
3. **FEATURES_REPORT.md** (English) → **FEATURES_REPORT.pdf**
4. **FEATURES_REPORT_AR.md** (Arabic) → **FEATURES_REPORT_AR.pdf**

---

## Method 1: Using Pandoc (Recommended for Linux/Mac)

### Install Pandoc
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc

# Or download from https://pandoc.org/installing.html
```

### Install wkhtmltopdf (for better PDF generation)
```bash
# macOS
brew install --cask wkhtmltopdf

# Ubuntu/Debian
sudo apt-get install wkhtmltopdf
```

### Convert Markdown to PDF
```bash
# Basic conversion
pandoc USER_MANUAL.md -o USER_MANUAL.pdf

# With styling and table of contents
pandoc USER_MANUAL.md \
  -o USER_MANUAL.pdf \
  --toc \
  --toc-depth=2 \
  --from markdown \
  --to pdf \
  -V geometry:margin=1in \
  -V fontsize=11pt

# For Arabic files (with proper font support)
pandoc USER_MANUAL_AR.md \
  -o USER_MANUAL_AR.pdf \
  --toc \
  --toc-depth=2 \
  --from markdown \
  --to pdf \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V mainfont="Arial" \
  --pdf-engine=wkhtmltopdf
```

---

## Method 2: Using VS Code Extensions

### Option A: Markdown PDF Extension
1. Install "Markdown PDF" by yzane in VS Code
2. Open the markdown file
3. Right-click → "Markdown PDF: Export (pdf)"
4. Select output location

### Option B: Markdown All in One
1. Install "Markdown All in One" by Yu Zhang
2. Open the markdown file
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Type "Markdown: Print to HTML"
5. Save as PDF from print dialog

---

## Method 3: Using Online Tools

### Option A: CloudConvert
1. Visit https://cloudconvert.com/md-to-pdf
2. Upload markdown file
3. Configure options:
   - Input: Markdown
   - Output: PDF
   - Quality: High
4. Download PDF

### Option B: Markdown to PDF Online
1. Visit https://md2pdf.netlify.app/
2. Paste content or upload file
3. Download PDF

### Option C: Pandoc Online
1. Visit https://pandoc.org/try/
2. Paste markdown content
3. Select "From: Markdown" and "To: PDF"
4. Copy/download output

---

## Method 4: Using Python

### Install Required Libraries
```bash
pip install markdown2 pdfkit
# Also need wkhtmltopdf installed on system
```

### Python Script
```python
#!/usr/bin/env python3
import pdfkit
import os

# Define files to convert
files = {
    'USER_MANUAL.md': 'USER_MANUAL.pdf',
    'USER_MANUAL_AR.md': 'USER_MANUAL_AR.pdf',
    'FEATURES_REPORT.md': 'FEATURES_REPORT.pdf',
    'FEATURES_REPORT_AR.md': 'FEATURES_REPORT_AR.pdf',
}

# Options for pdfkit
options = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'enable-local-file-access': None,
}

# Convert each file
for md_file, pdf_file in files.items():
    if os.path.exists(md_file):
        print(f"Converting {md_file} to {pdf_file}...")
        try:
            pdfkit.from_file(md_file, pdf_file, options=options)
            print(f"✓ Successfully created {pdf_file}")
        except Exception as e:
            print(f"✗ Error converting {md_file}: {e}")
    else:
        print(f"✗ File not found: {md_file}")

print("\nConversion complete!")
```

Save as `convert_to_pdf.py` and run:
```bash
python3 convert_to_pdf.py
```

---

## Method 5: Using Node.js

### Install Required Packages
```bash
npm install -g markdown-pdf
# or
npm install -g md-to-pdf
```

### Convert Files
```bash
# Using markdown-pdf
markdown-pdf USER_MANUAL.md -o USER_MANUAL.pdf
markdown-pdf USER_MANUAL_AR.md -o USER_MANUAL_AR.pdf
markdown-pdf FEATURES_REPORT.md -o FEATURES_REPORT.pdf
markdown-pdf FEATURES_REPORT_AR.md -o FEATURES_REPORT_AR.pdf

# or using md-to-pdf
md-to-pdf USER_MANUAL.md
md-to-pdf USER_MANUAL_AR.md
md-to-pdf FEATURES_REPORT.md
md-to-pdf FEATURES_REPORT_AR.md
```

---

## Method 6: Using Google Docs

### For Each Markdown File:
1. Create a new Google Doc
2. Copy the markdown content
3. Paste into Google Doc (it will auto-format some elements)
4. File → Download → PDF Document

---

## Best Practices for PDF Generation

### For Markdown to PDF:
✅ Use **Pandoc** for most professional output
✅ Always test with **table of contents** enabled
✅ Set **proper margins** (1 inch recommended)
✅ Use **Unicode UTF-8 encoding** (especially for Arabic)
✅ Choose **readable font size** (11pt minimum)

### For Arabic Documents:
⚠️ Ensure font supports **right-to-left (RTL) text**
⚠️ Use fonts like: **Arial**, **DejaVu**, **Noto Sans Arabic**
⚠️ Test PDF rendering for **text direction**
⚠️ Verify **diacritical marks** display correctly

### File Organization:
```
medical_appointment_management/
├── USER_MANUAL.md
├── USER_MANUAL.pdf          (generated)
├── USER_MANUAL_AR.md
├── USER_MANUAL_AR.pdf       (generated)
├── FEATURES_REPORT.md
├── FEATURES_REPORT.pdf      (generated)
├── FEATURES_REPORT_AR.md
├── FEATURES_REPORT_AR.pdf   (generated)
└── PDF_CONVERSION_GUIDE.md
```

---

## Recommended Workflow

### Step 1: Install Tools
```bash
# For macOS
brew install pandoc
brew install --cask wkhtmltopdf

# For Linux
sudo apt-get install pandoc wkhtmltopdf

# For Windows
choco install pandoc wkhtmltopdf
```

### Step 2: Convert All Files
```bash
# Create a batch script for convenience
cat > convert_docs.sh << 'EOF'
#!/bin/bash

# Convert English Documents
pandoc USER_MANUAL.md -o USER_MANUAL.pdf \
  --toc --toc-depth=2 \
  -V geometry:margin=1in -V fontsize=11pt

pandoc FEATURES_REPORT.md -o FEATURES_REPORT.pdf \
  --toc --toc-depth=2 \
  -V geometry:margin=1in -V fontsize=11pt

# Convert Arabic Documents
pandoc USER_MANUAL_AR.md -o USER_MANUAL_AR.pdf \
  --toc --toc-depth=2 \
  -V geometry:margin=1in -V fontsize=11pt \
  -V mainfont="Arial"

pandoc FEATURES_REPORT_AR.md -o FEATURES_REPORT_AR.pdf \
  --toc --toc-depth=2 \
  -V geometry:margin=1in -V fontsize=11pt \
  -V mainfont="Arial"

echo "✓ All PDFs generated successfully!"
EOF

chmod +x convert_docs.sh
./convert_docs.sh
```

### Step 3: Verify Output
- Check all 4 PDFs are created
- Open each PDF and verify:
  - Content displays correctly
  - Table of contents works
  - Arabic text renders properly
  - Images/formatting preserved

---

## Troubleshooting

### Issue: "command not found: pandoc"
**Solution:** Install pandoc using your package manager
```bash
brew install pandoc  # macOS
sudo apt-get install pandoc  # Linux
```

### Issue: Arabic text not rendering correctly
**Solution:** Specify font and PDF engine
```bash
pandoc INPUT.md -o OUTPUT.pdf \
  -V mainfont="Arial" \
  --pdf-engine=wkhtmltopdf
```

### Issue: "wkhtmltopdf not found"
**Solution:** Install wkhtmltopdf
```bash
brew install --cask wkhtmltopdf  # macOS
sudo apt-get install wkhtmltopdf  # Linux
```

### Issue: Markdown conversion loses formatting
**Solution:** Use enhanced Pandoc options
```bash
pandoc INPUT.md -o OUTPUT.pdf \
  --from markdown+smart \
  --to pdf \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V urlcolor=blue
```

### Issue: Tables don't format properly
**Solution:** Use standalone option
```bash
pandoc INPUT.md -o OUTPUT.pdf \
  --standalone \
  --table-of-contents
```

---

## File Sizes & Performance

| File | Size (Markdown) | Est. PDF Size | Conversion Time |
|------|-----------------|---------------|-----------------|
| USER_MANUAL | ~80 KB | ~200-300 KB | <2 seconds |
| USER_MANUAL_AR | ~90 KB | ~250-350 KB | <2 seconds |
| FEATURES_REPORT | ~120 KB | ~300-400 KB | <3 seconds |
| FEATURES_REPORT_AR | ~130 KB | ~350-450 KB | <3 seconds |

---

## Next Steps

1. **Choose your preferred method** from the options above
2. **Install required tools** (Pandoc recommended)
3. **Generate PDFs** using the command or script
4. **Verify output quality** by opening each PDF
5. **Store PDFs** in the same directory as markdown files
6. **Share PDFs** with users for training and reference

---

## Support & Resources

- **Pandoc Documentation:** https://pandoc.org/
- **Markdown Syntax:** https://commonmark.org/
- **PDF Best Practices:** https://en.wikipedia.org/wiki/PDF
- **UTF-8 & Arabic Support:** https://www.unicode.org/reports/tr29/

---

**Created:** October 19, 2026
**Last Updated:** October 19, 2026
**Status:** Ready to Use
