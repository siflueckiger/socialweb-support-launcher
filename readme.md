# socialweb Support Pages Generator

A two-step Python workflow for generating responsive HTML support pages from Excel data.

## Overview

This toolkit extracts socialweb.ch URLs from an Excel file and generates a searchable, alphabetically-organized HTML page with keyboard shortcuts and responsive design.

## Files

- **`extract_url.py`** - Extracts URLs from Excel and creates semicolon-separated TXT output
- **`create_html.py`** - Generates responsive HTML page from the TXT file
- **`README.md`** - This documentation

## Requirements

```bash
pip install pandas openpyxl
```

## Workflow

### Step 1: Extract URLs from Excel

```bash
python extract_url.py
```

**Input:** `input.xlsx` (Excel file with columns for Anzeigename, Ergänzung, Webadresse, Projektleitung)

**Output:** `socialweb_export.txt` (semicolon-separated file)

**What it does:**
- Extracts entries containing `socialweb.ch` URLs
- Adds `/login/support/` path to URLs if not present
- Includes custom predefined URLs (team members, standard, handbuch)
- Removes duplicates and sorts alphabetically
- Handles multiple comma-separated URLs per row

### Step 2: Generate HTML

```bash
python create_html.py
```

**Input:** `socialweb_export.txt`

**Output:** `soc-support-tenant-liste.html`

**Features:**
- Alphabetical navigation with active letter highlighting
- Real-time search (filters by name, description, or URL)
- Responsive 3-column layout (adapts to mobile)
- Keyboard shortcuts: `Ctrl+K` or `/` for search, `Esc` to clear
- SAML logout button
- Footer with timestamp and entry count

## Input File Format

Your Excel file should contain these columns (case-insensitive):

| Column | Description |
|--------|-------------|
| **Anzeigename** | Display name for the entry |
| **Ergänzung** | Additional description/context |
| **Webadresse** | URL (must contain `socialweb.ch`) |
| **Projekt/Zuständigkeit** | Project lead or responsible person |



## Custom URLs

Custom URL (not in the input file) are defined in `extract_url.py` in the `CustomURLProvider` class.

## Output Structure

The generated HTML includes:

- **Fixed header** with search box, A-Z navigation, and logout button
- **Main content** with alphabetical sections (A-Z, #)
- **Three-column layout** for entries (responsive)
- **Fixed footer** with generation timestamp and entry count
