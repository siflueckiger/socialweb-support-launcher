"""
URL Extractor for socialweb Support Pages
Version 3.0 - Optimized

Extracts URLs from Excel and creates semicolon-separated TXT output
"""

import pandas as pd
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Tuple, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class URLProcessor:
    """Handles URL processing and modification"""

    SUPPORT_PATH = '/login/support/'
    REMOVE_PREFIXES = ('https://', 'http://', 'www.')

    @classmethod
    def clean_url(cls, url: str) -> str:
        """Remove protocol and www prefix from URL"""
        if not url:
            return ""

        url = url.strip()
        for prefix in cls.REMOVE_PREFIXES:
            if url.startswith(prefix):
                url = url[len(prefix):]

        return url

    @classmethod
    def add_support_path(cls, url: str) -> str:
        """Add /login/support/ path to URL if not already present"""
        if not url or pd.isna(url):
            return ""

        url = str(url).strip()
        if not url:
            return ""

        clean_url = cls.clean_url(url)

        # Check if support path already exists
        if cls.SUPPORT_PATH in clean_url or clean_url.endswith('/login/support'):
            return clean_url

        # Parse URL
        temp_url = 'https://' + clean_url
        parsed = urlparse(temp_url)

        if not parsed.netloc:
            return f"{clean_url.rstrip('/')}{cls.SUPPORT_PATH}"

        # Build new path
        current_path = parsed.path.strip('/')

        if 'login/support' in current_path:
            new_path = f"/{current_path}" if current_path else ''
        else:
            new_path = f"/{current_path}{cls.SUPPORT_PATH}" if current_path else cls.SUPPORT_PATH

        # Reconstruct URL
        netloc = parsed.netloc.removeprefix('www.')
        result = f"{netloc}{new_path}"

        # Add query and fragment if present
        if parsed.query:
            result += f"?{parsed.query}"
        if parsed.fragment:
            result += f"#{parsed.fragment}"

        return result


class CustomURLProvider:
    """Provides custom URLs to be included"""

    @staticmethod
    def get_custom_entries() -> List[Tuple[str, str, str, str]]:
        """Returns list of custom URL entries"""
        return [
            ("Oberli Pascal", "POB", "pob.socialweb.ch/", "Oberli Pascal"),
            ("Fonseka Pius", "PIF", "pif.socialweb.ch/", "Fonseka Pius"),
            ("Flückiger Simon", "SIM", "sim.socialweb.ch/", "Flückiger Simon"),
            ("Lehmann Sandra", "SAL", "sal.socialweb.ch/", "Lehmann Sandra"),
            ("Ambrosetti Chiara", "CHA", "cha.socialweb.ch/", "Ambrosetti Chiara"),
            ("Moix Xenia", "XEM", "xem.socialweb.ch/", "Moix Xenia"),
            ("Toma Marijana", "MAT", "mat.socialweb.ch/", "Toma Marijana"),
            ("Daniel Schmocker", "DAS", "das.socialweb.ch/", "Daniel Schmocker"),
            ("Team", "Team", "team.socialweb.ch/", "Team"),
            ("Standard", "Standard", "standard.socialweb.ch/", "Standard"),
            ("Handbuch", "Handbuch", "handbuch.socialweb.ch/", "Handbuch")
        ]


class ExcelExtractor:
    """Extracts and processes Excel data"""

    COLUMN_MAPPING = {
        'anzeigename': ['anzeigename'],
        'ergaenzung': ['ergänzung'],
        'webadresse': ['webadresse'],
        'projektleitung': ['projekt', 'zuständigkeit']
    }

    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.df = None
        self.column_map = {}

    def load_data(self, sheet_name: int = 0) -> bool:
        """Load Excel file"""
        try:
            logger.info(f"Loading Excel file: {self.excel_path}")
            self.df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            logger.info(f"Found columns: {list(self.df.columns)}")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {self.excel_path}")
            return False
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            return False

    def map_columns(self) -> bool:
        """Map Excel columns to required fields"""
        if self.df is None:
            return False

        for field, keywords in self.COLUMN_MAPPING.items():
            matched = False
            for col in self.df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in keywords):
                    # Skip if it's a compound match we don't want
                    if field == 'anzeigename' and 'ergänzung' in col_lower:
                        continue
                    self.column_map[field] = col
                    matched = True
                    break

            if not matched:
                logger.error(f"Column not found for: {field}")
                return False

        logger.info("All required columns mapped successfully")
        return True

    def extract_entries(self) -> Set[Tuple[str, str, str, str]]:
        """Extract entries from DataFrame"""
        entries = set()
        processed_rows = 0

        for _, row in self.df.iterrows():
            webadresse = row[self.column_map['webadresse']]

            # Only process rows with socialweb.ch URLs
            if pd.notna(webadresse) and 'socialweb.ch' in str(webadresse).lower():
                processed_rows += 1

                anzeigename = self._get_value(row, 'anzeigename')
                ergaenzung = self._get_value(row, 'ergaenzung')
                projektleitung = self._get_value(row, 'projektleitung', default='Unbekannt')

                # Split multiple URLs by comma
                urls = [url.strip() for url in str(webadresse).split(',')]

                for url in urls:
                    if url and 'socialweb.ch' in url.lower():
                        modified_url = URLProcessor.add_support_path(url)
                        entry = (
                            anzeigename.strip(),
                            ergaenzung.strip(),
                            modified_url,
                            projektleitung.strip()
                        )
                        entries.add(entry)
                        logger.debug(f"Extracted: {anzeigename} - {modified_url}")

        logger.info(f"Processed {processed_rows} rows with socialweb.ch URLs")
        return entries

    def _get_value(self, row, field: str, default: str = "") -> str:
        """Get value from row with default"""
        value = row[self.column_map[field]]
        return str(value).strip() if pd.notna(value) else default


class TXTExporter:
    """Exports entries to semicolon-separated TXT file"""

    HEADER = "Anzeigename;Ergänzung Anzeigename;Webadresse Geschäftlich;Projektleitung / Zuständigkeit\n"

    @staticmethod
    def export(entries: List[Tuple[str, str, str, str]], output_path: Path) -> bool:
        """Export entries to TXT file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(TXTExporter.HEADER)
                for entry in entries:
                    line = f"{entry[0]};{entry[1]};{entry[2]};{entry[3]}\n"
                    f.write(line)

            logger.info(f"File saved: {output_path}")
            logger.info(f"File size: {output_path.stat().st_size} bytes")
            return True
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return False


def process_excel_to_txt(
    excel_path: str = "input.xlsx",
    output_path: str = "socialweb_export.txt",
    sheet_name: int = 0
) -> bool:
    """
    Main processing function

    Args:
        excel_path: Path to input Excel file
        output_path: Path to output TXT file
        sheet_name: Excel sheet index

    Returns:
        True if successful, False otherwise
    """
    excel_file = Path(excel_path)
    output_file = Path(output_path)

    # Extract from Excel
    extractor = ExcelExtractor(excel_file)
    if not extractor.load_data(sheet_name):
        return False

    if not extractor.map_columns():
        return False

    entries = extractor.extract_entries()

    # Add custom URLs
    custom_entries = CustomURLProvider.get_custom_entries()
    for entry in custom_entries:
        modified_url = URLProcessor.add_support_path(entry[2])
        entries.add((entry[0], entry[1], modified_url, entry[3]))
        logger.debug(f"Custom URL: {entry[0]} - {modified_url}")

    # Sort by display name
    sorted_entries = sorted(list(entries), key=lambda x: x[0].lower())

    # Export to TXT
    if not TXTExporter.export(sorted_entries, output_file):
        return False

    # Print summary
    logger.info("=" * 60)
    logger.info(f"Unique entries: {len(sorted_entries)}")
    logger.info("=" * 60)

    if sorted_entries:
        logger.info("First 5 entries:")
        for i, entry in enumerate(sorted_entries[:5], 1):
            logger.info(f"{i}. {entry[0]} | {entry[1]} | {entry[2]} | {entry[3]}")

    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("socialweb URL Extractor - Version 3.0 (Optimized)")
    print("=" * 60)

    # Use current directory by default
    current_dir = Path.cwd()
    excel_file = current_dir / "input.xlsx"
    output_file = current_dir / "socialweb_export.txt"

    print(f"Working directory: {current_dir}")
    print(f"Input file: {excel_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)

    if not excel_file.exists():
        print(f"\n❌ Error: File '{excel_file.name}' not found!")
        print(f"Please ensure '{excel_file.name}' is in the current directory:")
        print(f"  {current_dir}")
        return

    success = process_excel_to_txt(
        excel_path=str(excel_file),
        output_path=str(output_file)
    )

    if success:
        print("\n✅ Success! File ready for create_html.py")
    else:
        print("\n❌ Processing failed. Check logs above.")


if __name__ == "__main__":
    main()