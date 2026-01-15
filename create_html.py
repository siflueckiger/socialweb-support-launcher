"""
HTML Generator for socialweb Support Pages
Version 4.0 - Optimized

Generates responsive HTML page from semicolon-separated TXT file
"""

import string
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class Entry:
    """Represents a support link entry"""

    def __init__(self, anzeigename: str, ergaenzung: str, webadresse: str, projektleitung: str = ""):
        self.anzeigename = anzeigename.strip()
        self.ergaenzung = ergaenzung.strip()
        self.webadresse = self._normalize_url(webadresse.strip())
        self.projektleitung = projektleitung.strip()

        # Compute derived properties
        self.sort_string = self._compute_sort_string()
        self.display_name = self._compute_display_name()
        self.display_title = self.display_name
        self.search_text = self._compute_search_text()

    def _normalize_url(self, url: str) -> str:
        """Add https:// if missing"""
        if url and not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url

    def _compute_sort_string(self) -> str:
        """Compute string used for sorting"""
        if self.anzeigename:
            return self.anzeigename
        return self.webadresse.replace('https://', '').replace('http://', '')

    def _compute_display_name(self) -> str:
        """Compute display name for the entry"""
        if self.anzeigename:
            return self.anzeigename
        return self.webadresse.replace('https://', '').replace('http://', '')

    def _compute_search_text(self) -> str:
        """Compute text used for searching"""
        url_clean = self.webadresse.replace('https://', '').replace('http://', '')
        return f"{self.anzeigename} {self.ergaenzung} {url_clean}"

    def get_first_letter(self) -> str:
        """Get first letter for grouping"""
        first_char = self.sort_string[0].upper() if self.sort_string else "#"
        return first_char if first_char in string.ascii_uppercase else "#"

    def get_url_display(self) -> str:
        """Get URL for display purposes"""
        return self.webadresse.replace('https://', '').replace('http://', '') if self.webadresse else ""

    def get_meta_parts(self) -> List[str]:
        """Get metadata parts for display"""
        parts = []
        if self.ergaenzung:
            parts.append(self.ergaenzung)
        url_display = self.get_url_display()
        if url_display:
            parts.append(url_display)
        return parts


class TXTParser:
    """Parses semicolon-separated TXT file"""

    @staticmethod
    def parse(file_path: Path) -> List[Entry]:
        """Parse TXT file and return list of entries"""
        entries = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Skip header (first line)
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(';')
                if len(parts) >= 3:
                    anzeigename = parts[0] if len(parts) > 0 else ""
                    ergaenzung = parts[1] if len(parts) > 1 else ""
                    webadresse = parts[2] if len(parts) > 2 else ""
                    projektleitung = parts[3] if len(parts) > 3 else ""

                    # Require at least name or URL
                    if anzeigename or webadresse:
                        entry = Entry(anzeigename, ergaenzung, webadresse, projektleitung)
                        entries.append(entry)

            logger.info(f"Parsed {len(entries)} entries from {file_path}")
            return entries

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            return []


class HTMLTemplate:
    """Generates HTML content"""

    @staticmethod
    def get_styles() -> str:
        """Return CSS styles"""
        return '''
    html, body {
      margin: 0;
      padding: 0;
      height: 100vh;
      font-family: Arial, sans-serif;
      background-color: #f9f9f9;
    }

    .header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background-color: #ffffff;
      border-bottom: 2px solid #ccc;
      padding: 1rem 2rem;
      z-index: 1000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .header-content {
      max-width: 1800px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 2rem;
      flex-wrap: wrap;
    }

    .search-container {
      position: relative;
      flex: 1;
      min-width: 300px;
      max-width: 500px;
    }

    .search-box {
      padding: 10px 80px 10px 12px;
      border: 1px solid #ccc;
      border-radius: 6px;
      font-size: 14px;
      width: 100%;
      box-sizing: border-box;
    }

    .search-box:focus {
      outline: none;
      border-color: #007acc;
      box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.1);
    }

    .search-hint {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 11px;
      color: #999;
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 3px;
      pointer-events: none;
      transition: opacity 0.2s;
    }

    .search-box:focus + .search-hint {
      opacity: 0;
    }

    .nav-letters {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      flex: 2;
    }

    .nav-letters a,
    .nav-letters span {
      display: inline-block;
      width: 28px;
      height: 28px;
      text-align: center;
      line-height: 28px;
      text-decoration: none;
      border-radius: 4px;
      font-weight: bold;
      font-size: 13px;
    }

    .nav-letters a {
      color: #007acc;
      background-color: #f0f0f0;
      transition: all 0.2s ease;
    }

    .nav-letters a:hover {
      background-color: #e0e0e0;
    }

    .nav-letters a.active {
      color: #ffffff;
      background-color: #007acc;
    }

    .nav-letters span {
      color: #ccc;
    }

    .logout-button {
      background-color: #007acc;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      font-size: 13px;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      transition: background-color 0.3s ease;
      white-space: nowrap;
    }

    .logout-button:hover {
      background-color: #005fa3;
    }

    .content-area {
      margin-top: 120px;
      margin-bottom: 60px;
      padding: 2rem;
      max-width: 1800px;
      margin-left: auto;
      margin-right: auto;
    }

    section {
      margin-bottom: 3rem;
    }

    h2 {
      border-bottom: 1px solid #ccc;
      padding-bottom: 0.3rem;
      margin-top: 2rem;
      color: #333;
    }

    ul {
      column-count: 3;
      column-gap: 2rem;
      list-style: none;
      padding: 0;
    }

    li {
      margin: 0.3rem 0;
      margin-bottom: 1.3rem;
      break-inside: avoid;
    }

    .entry-link {
      font-weight: bold;
      color: #007acc;
      text-decoration: none;
      display: block;
    }

    .entry-link:hover {
      text-decoration: underline;
    }

    .entry-meta {
      font-size: 0.85em;
      color: #666;
      font-style: italic;
      margin-top: 0.2rem;
    }

    @media (max-width: 1200px) {
      ul {
        column-count: 2;
      }
    }

    @media (max-width: 768px) {
      .header-content {
        flex-direction: column;
        gap: 1rem;
      }

      .search-container {
        max-width: 100%;
      }

      .nav-letters {
        justify-content: center;
      }

      .content-area {
        margin-top: 200px;
      }

      ul {
        column-count: 1;
      }
    }

    .footer-bar {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #eef;
      color: #333;
      text-align: center;
      padding: 0.75rem 0;
      border-top: 1px solid #ccc;
      font-size: 0.9rem;
      z-index: 999;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    }
'''

    @staticmethod
    def get_javascript() -> str:
        """Return JavaScript code"""
        return '''
  document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll(".nav-letters a");
    const sections = document.querySelectorAll(".content-area section");
    const searchBox = document.querySelector(".search-box");
    const allListItems = document.querySelectorAll(".content-area li");

    // Keyboard shortcuts
    document.addEventListener("keydown", function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchBox.focus();
        searchBox.select();
      } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        searchBox.focus();
      } else if (e.key === 'Escape' && document.activeElement === searchBox) {
        searchBox.value = '';
        searchBox.blur();
        applyFilters();
      }
    });

    function updateActiveLetter() {
      let closest = null;
      let minOffset = Infinity;

      sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        const offset = Math.abs(rect.top - 140);
        if (rect.top >= 120 && offset < minOffset) {
          minOffset = offset;
          closest = section;
        }
      });

      if (closest) {
        const id = closest.querySelector("h2").id;
        navLinks.forEach(link => {
          link.classList.toggle("active", link.getAttribute("href") === "#" + id);
        });
      }
    }

    window.addEventListener("scroll", () => {
      window.requestAnimationFrame(updateActiveLetter);
    });

    navLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = link.getAttribute("href").substring(1);
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
          const offsetTop = targetSection.offsetTop - 130;
          window.scrollTo({ top: offsetTop, behavior: "smooth" });
        }
      });
    });

    if (location.hash) {
      const target = document.querySelector(location.hash);
      if (target) {
        setTimeout(() => {
          const offsetTop = target.offsetTop - 130;
          window.scrollTo({ top: offsetTop, behavior: "instant" });
          updateActiveLetter();
        }, 100);
      }
    } else {
      updateActiveLetter();
    }

    searchBox.addEventListener("keyup", applyFilters);

    function applyFilters() {
      const searchTerm = searchBox.value.toLowerCase();

      allListItems.forEach(li => {
        const searchText = li.dataset.searchText.toLowerCase();
        li.style.display = searchText.includes(searchTerm) ? "block" : "none";
      });

      sections.forEach(section => {
        const visibleLinks = section.querySelectorAll("li[style='display: block;']").length;
        section.style.display = visibleLinks > 0 ? "block" : "none";
      });
    }
  });
'''


class HTMLGenerator:
    """Main HTML generator class"""

    SAML_LOGOUT_URL = "https://login.microsoftonline.com/12c4861e-9d0e-4707-9b36-2d01976efcf3/saml2?SAMLRequest=fZFNS8QwEIb%2FSm85pU3T9CNhWxQWYWH1oOLBi2TzUQNtUjsp7M%2B33BURQS%2BBCe87z8y8O5DjMIlj6MMSH83HYiAm%2B%2FVxXkYXfIveY5xAZNkQeufT0ak5QLAx%2BMF5k6owZjlVrKlyg7kmBrOa1JifigpTTXJeV8YqW2Qbh6LksG%2FRW6F4ztiq5azhmJWWYkmYxZRXWhOqa8uKVQqwmIOHKH1sESW0xGvnvHkmjShqwdgrSl7MDJcpaUpQch4HD2IjtWiZvQgSHAgvRwMiKvF0e38Uq1BIADNv2%2F20TP97pjnEoMKAut2mFpfp5g4mL4ytCDWNwifFG7yeguOTrBnWtLFclyW3Zb7LfrquLR5WyGGf3IV5lPFvep7mlx%2Bnsb1IxeJhMspZZzTqpB5B%2B%2BWmH%2BRy7uewTGnw3zFtAX2xr7juWv2KvPsE"

    def __init__(self, entries: List[Entry]):
        self.entries = entries
        self.grouped = self._group_entries()

    def _group_entries(self) -> Dict[str, List[Entry]]:
        """Group entries by first letter"""
        grouped = defaultdict(list)
        sorted_entries = sorted(self.entries, key=lambda e: e.sort_string.lower())

        for entry in sorted_entries:
            letter = entry.get_first_letter()
            grouped[letter].append(entry)

        return dict(grouped)

    def generate(self, output_path: Path) -> bool:
        """Generate HTML file"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            total_entries = len(self.entries)

            html_parts = [
                self._get_header(),
                self._get_navigation(),
                self._get_content(),
                self._get_footer(timestamp, total_entries),
                '</body>\n</html>'
            ]

            html_content = ''.join(html_parts)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"✅ HTML file created: {output_path}")
            logger.info(f"📊 {total_entries} entries processed")
            return True

        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            return False

    def _get_header(self) -> str:
        """Generate HTML header"""
        return f'''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>socialweb Support-Links</title>
  <style>{HTMLTemplate.get_styles()}
  </style>
  <script>{HTMLTemplate.get_javascript()}
  </script>
</head>
<body>

  <header class="header">
    <div class="header-content">
      <div class="search-container">
        <input type="text" class="search-box" placeholder="Name, Ergänzung oder URL...">
        <span class="search-hint">Ctrl+K</span>
      </div>

      <div class="nav-letters">
'''

    def _get_navigation(self) -> str:
        """Generate navigation letters"""
        nav_html = []

        for letter in string.ascii_uppercase:
            if letter in self.grouped:
                nav_html.append(f'        <a href="#{letter}">{letter}</a>\n')
            else:
                nav_html.append(f'        <span>{letter}</span>\n')

        if "#" in self.grouped:
            nav_html.append('        <a href="#num">#</a>\n')
        else:
            nav_html.append('        <span>#</span>\n')

        nav_html.append('      </div>\n\n')
        nav_html.append(f'''      <a class="logout-button" href="{self.SAML_LOGOUT_URL}" target="_blank" rel="noopener noreferrer">
        SAML Logout
      </a>
    </div>
  </header>

  <main class="content-area">
''')

        return ''.join(nav_html)

    def _get_content(self) -> str:
        """Generate main content sections"""
        content_html = []

        for letter in sorted(self.grouped.keys()):
            section_id = "num" if letter == "#" else letter
            content_html.append(f'    <section>\n      <h2 id="{section_id}">{letter}</h2>\n      <ul>\n')

            for entry in self.grouped[letter]:
                content_html.append(self._render_entry(entry))

            content_html.append('      </ul>\n    </section>\n')

        return ''.join(content_html)

    def _render_entry(self, entry: Entry) -> str:
        """Render a single entry"""
        html = [f'        <li data-search-text="{entry.search_text}">\n']

        if entry.webadresse:
            html.append(f'          <a href="{entry.webadresse}" target="_blank" class="entry-link">{entry.display_title}</a>\n')
        else:
            html.append(f'          <span class="entry-link">{entry.display_title}</span>\n')

        meta_parts = entry.get_meta_parts()
        if meta_parts:
            html.append(f'          <div class="entry-meta">{", ".join(meta_parts)}</div>\n')

        html.append('        </li>\n')
        return ''.join(html)

    def _get_footer(self, timestamp: str, total_entries: int) -> str:
        """Generate footer"""
        return f'''  </main>

  <div class="footer-bar">
    Datei erstellt am: {timestamp} | Anzahl Einträge: {total_entries}
  </div>
'''


def generate_html(
    input_file: str = "socialweb_export.txt",
    output_file: str = "soc-support-tenant-liste.html"
) -> bool:
    """
    Main function to generate HTML from TXT file

    Args:
        input_file: Path to input TXT file
        output_file: Path to output HTML file

    Returns:
        True if successful, False otherwise
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Parse input file
    entries = TXTParser.parse(input_path)
    if not entries:
        logger.error("No entries to process")
        return False

    # Generate HTML
    generator = HTMLGenerator(entries)
    return generator.generate(output_path)


def main():
    """Main entry point"""
    print("=" * 60)
    print("socialweb HTML Generator - Version 4.0 (Optimized)")
    print("=" * 60)

    # Use current directory by default
    current_dir = Path.cwd()
    input_file = current_dir / "socialweb_export.txt"
    output_file = current_dir / "soc-support-tenant-liste.html"

    print(f"Working directory: {current_dir}")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)

    success = generate_html(
        input_file=str(input_file),
        output_file=str(output_file)
    )

    if success:
        print("\n✅ HTML file successfully created!")
    else:
        print("\n❌ Generation failed. Check logs above.")


if __name__ == "__main__":
    main()