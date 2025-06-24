#!/usr/bin/env python3
"""
TBX (TermBase eXchange) Importer for Bilingual Checker MCP
Converts TBX files to SQLite database for fast terminology lookup
"""
import xml.etree.ElementTree as ET
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TBXImporter:
    """Imports TBX files into SQLite database."""
    
    def __init__(self, db_path: str = "terms.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create database tables for terminology."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Terms table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    term_type TEXT DEFAULT 'preferred',
                    domain TEXT,
                    source_file TEXT,
                    definition TEXT,
                    usage_note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for fast lookup
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_term ON terms(source_term)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_lang ON terms(source_lang)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_term_type ON terms(term_type)")
            
            # Rules table for terminology preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    replacement TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    description TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
    
    def import_tbx_file(self, tbx_file_path: str) -> int:
        """Import a single TBX file."""
        if not os.path.exists(tbx_file_path):
            logger.error(f"TBX file not found: {tbx_file_path}")
            return 0
        
        try:
            tree = ET.parse(tbx_file_path)
            root = tree.getroot()
            
            terms_imported = 0
            filename = os.path.basename(tbx_file_path)
            
            # Parse TBX structure
            # TBX format: <martif><body><termEntry><langSet><tig><term>
            for term_entry in root.findall(".//termEntry"):
                terms_imported += self._process_term_entry(term_entry, filename)
            
            logger.info(f"Imported {terms_imported} terms from {filename}")
            return terms_imported
            
        except ET.ParseError as e:
            logger.error(f"Error parsing TBX file {tbx_file_path}: {e}")
            return 0
    
    def _process_term_entry(self, term_entry, source_file: str) -> int:
        """Process a single termEntry from TBX."""
        domain = ""
        definition = ""
        
        # Extract domain/subject field
        subject_field = term_entry.find(".//descrip[@type='subjectField']")
        if subject_field is not None:
            domain = subject_field.text or ""
        
        # Extract definition
        definition_field = term_entry.find(".//descrip[@type='definition']")
        if definition_field is not None:
            definition = definition_field.text or ""
        
        # Extract terms by language
        lang_sets = term_entry.findall(".//langSet")
        term_data = {}
        
        for lang_set in lang_sets:
            lang = lang_set.get('lang') or lang_set.get('{http://www.w3.org/XML/1998/namespace}lang')
            if not lang:
                continue
            
            # Normalize language codes
            lang = self._normalize_lang_code(lang)
            
            # Extract terms - handle both TIG and NTIG formats
            terms = []
            
            # Try TIG format first (standard TBX)
            for tig in lang_set.findall(".//tig"):
                term_elem = tig.find("term")
                if term_elem is not None and term_elem.text:
                    # Get term type (preferred, admitted, deprecated)
                    term_type = "preferred"
                    term_note = tig.find(".//termNote[@type='termType']")
                    if term_note is not None:
                        term_type = term_note.text or "preferred"
                    
                    terms.append({
                        "text": term_elem.text.strip(),
                        "type": term_type
                    })
            
            # Try NTIG format (newer TBX format)
            for ntig in lang_set.findall(".//ntig"):
                for term_grp in ntig.findall(".//termGrp"):
                    term_elem = term_grp.find("term")
                    if term_elem is not None and term_elem.text:
                        # Get term type - NTIG uses different structure
                        term_type = "preferred"  # Default for NTIG
                        term_note = term_grp.find(".//termNote[@type='termType']")
                        if term_note is not None:
                            term_type = term_note.text or "preferred"
                        
                        terms.append({
                            "text": term_elem.text.strip(),
                            "type": term_type
                        })
            
            # Fallback: try direct term elements
            if not terms:
                for term_elem in lang_set.findall(".//term"):
                    if term_elem.text:
                        terms.append({
                            "text": term_elem.text.strip(),
                            "type": "preferred"
                        })
            
            if terms:
                term_data[lang] = terms
        
        # Create term pairs (EN <-> JP)
        terms_saved = 0
        
        if 'en' in term_data and 'jp' in term_data:
            terms_saved += self._save_term_pairs(
                term_data['en'], term_data['jp'], 
                domain, definition, source_file
            )
        
        return terms_saved
    
    def _save_term_pairs(self, en_terms: List[Dict], jp_terms: List[Dict], 
                        domain: str, definition: str, source_file: str) -> int:
        """Save English-Japanese term pairs to database."""
        saved_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create all possible EN->JP pairs
            for en_term in en_terms:
                for jp_term in jp_terms:
                    # EN -> JP
                    cursor.execute("""
                        INSERT INTO terms 
                        (source_lang, target_lang, source_term, target_term, 
                         term_type, domain, source_file, definition)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'en', 'jp', en_term['text'], jp_term['text'],
                        en_term['type'], domain, source_file, definition
                    ))
                    
                    # JP -> EN  
                    cursor.execute("""
                        INSERT INTO terms 
                        (source_lang, target_lang, source_term, target_term, 
                         term_type, domain, source_file, definition)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'jp', 'en', jp_term['text'], en_term['text'],
                        jp_term['type'], domain, source_file, definition
                    ))
                    
                    saved_count += 2
            
            conn.commit()
        
        return saved_count
    
    def _normalize_lang_code(self, lang: str) -> str:
        """Normalize language codes to our standard."""
        lang = lang.lower()
        if lang.startswith('en'):
            return 'en'
        elif lang.startswith('ja') or lang.startswith('jp'):
            return 'jp'
        return lang
    
    def import_directory(self, directory_path: str) -> int:
        """Import all TBX files from a directory."""
        dir_path = Path(directory_path)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return 0
        
        total_imported = 0
        tbx_files = list(dir_path.glob("*.tbx")) + list(dir_path.glob("*.xml"))
        
        if not tbx_files:
            logger.warning(f"No TBX files found in {directory_path}")
            return 0
        
        for tbx_file in tbx_files:
            total_imported += self.import_tbx_file(str(tbx_file))
        
        logger.info(f"Total terms imported: {total_imported}")
        return total_imported
    
    def add_custom_rule(self, language: str, pattern: str, replacement: str, 
                       rule_type: str = "preferred_synonym", severity: str = "warning",
                       description: str = ""):
        """Add custom terminology rule."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rules 
                (language, pattern, replacement, rule_type, severity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (language, pattern, replacement, rule_type, severity, description))
            conn.commit()
        
        logger.info(f"Added rule: {pattern} -> {replacement} ({language})")
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM terms")
            term_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM rules")
            rule_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT source_lang, COUNT(*) FROM terms GROUP BY source_lang")
            lang_stats = dict(cursor.fetchall())
            
            cursor.execute("SELECT DISTINCT source_file FROM terms WHERE source_file IS NOT NULL")
            source_files = [row[0] for row in cursor.fetchall()]
        
        return {
            "total_terms": term_count,
            "total_rules": rule_count,
            "languages": lang_stats,
            "source_files": source_files
        }

def main():
    """Command-line interface for TBX import."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import TBX files into terminology database")
    parser.add_argument("input", help="TBX file or directory to import")
    parser.add_argument("--db", default="terms.db", help="Database file path")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    importer = TBXImporter(args.db)
    
    if args.stats:
        stats = importer.get_stats()
        print("\n📊 Database Statistics:")
        print(f"  Total terms: {stats['total_terms']}")
        print(f"  Total rules: {stats['total_rules']}")
        print(f"  Languages: {stats['languages']}")
        print(f"  Source files: {len(stats['source_files'])}")
        return
    
    input_path = Path(args.input)
    if input_path.is_file():
        imported = importer.import_tbx_file(args.input)
    elif input_path.is_dir():
        imported = importer.import_directory(args.input)
    else:
        print(f"❌ Path not found: {args.input}")
        return
    
    print(f"✅ Import complete! {imported} terms added to database.")
    
    # Show final stats
    stats = importer.get_stats()
    print(f"\n📊 Database now contains {stats['total_terms']} terms")

if __name__ == "__main__":
    main() 