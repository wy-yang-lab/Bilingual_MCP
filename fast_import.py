#!/usr/bin/env python3
"""
Fast batch importer for large TBX files with progress reporting
"""
import xml.etree.ElementTree as ET
import sqlite3
import sys
import os
import time
from pathlib import Path

# Add the data directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

def fast_import_tbx(tbx_file, db_file="terms.db"):
    """Fast import with batch operations and progress reporting."""
    print(f"🚀 Fast importing {tbx_file}...")
    
    # Initialize database
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        
        # Create tables
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
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_term ON terms(source_term)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_lang ON terms(source_lang)")
        
        conn.commit()
    
    print(f"📊 Database initialized: {db_file}")
    
    # Parse TBX file
    print(f"🔍 Parsing TBX file...")
    tree = ET.parse(tbx_file)
    root = tree.getroot()
    
    term_entries = root.findall(".//termEntry")
    total_entries = len(term_entries)
    print(f"📋 Found {total_entries} term entries to process")
    
    # Batch import
    batch_size = 1000
    batch_data = []
    processed = 0
    imported_terms = 0
    
    start_time = time.time()
    
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        
        for i, entry in enumerate(term_entries):
            # Extract terms from this entry
            en_terms = []
            jp_terms = []
            domain = ""
            definition = ""
            
            # Get domain/definition
            subject_field = entry.find(".//descrip[@type='subjectField']")
            if subject_field is not None:
                domain = subject_field.text or ""
            
            definition_field = entry.find(".//descrip[@type='definition']")
            if definition_field is not None:
                definition = definition_field.text or ""
            
            # Extract terms by language
            lang_sets = entry.findall(".//langSet")
            
            for lang_set in lang_sets:
                lang = lang_set.get('lang') or lang_set.get('{http://www.w3.org/XML/1998/namespace}lang')
                if not lang:
                    continue
                
                # Normalize language
                if lang.lower().startswith('en'):
                    normalized_lang = 'en'
                elif lang.lower().startswith('ja'):
                    normalized_lang = 'jp'
                else:
                    continue
                
                # Extract terms using NTIG format
                terms = []
                for ntig in lang_set.findall(".//ntig"):
                    for term_grp in ntig.findall(".//termGrp"):
                        term_elem = term_grp.find("term")
                        if term_elem is not None and term_elem.text:
                            terms.append(term_elem.text.strip())
                
                # Store terms by language
                if normalized_lang == 'en':
                    en_terms.extend(terms)
                elif normalized_lang == 'jp':
                    jp_terms.extend(terms)
            
            # Create term pairs if we have both languages
            if en_terms and jp_terms:
                for en_term in en_terms:
                    for jp_term in jp_terms:
                        # EN -> JP
                        batch_data.append((
                            'en', 'jp', en_term, jp_term, 'preferred', 
                            domain, os.path.basename(tbx_file), definition
                        ))
                        # JP -> EN
                        batch_data.append((
                            'jp', 'en', jp_term, en_term, 'preferred',
                            domain, os.path.basename(tbx_file), definition
                        ))
            
            processed += 1
            
            # Batch insert when we reach batch_size or end of data
            if len(batch_data) >= batch_size or i == total_entries - 1:
                if batch_data:
                    cursor.executemany("""
                        INSERT INTO terms 
                        (source_lang, target_lang, source_term, target_term, 
                         term_type, domain, source_file, definition)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch_data)
                    
                    imported_terms += len(batch_data)
                    batch_data = []
                    
                    # Commit every batch
                    conn.commit()
                
                # Progress report
                elapsed = time.time() - start_time
                progress = (processed / total_entries) * 100
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_entries - processed) / rate if rate > 0 else 0
                
                print(f"⏳ Progress: {processed:,}/{total_entries:,} entries ({progress:.1f}%) "
                      f"| {imported_terms:,} terms | {rate:.0f} entries/sec | ETA: {eta:.0f}s")
    
    elapsed = time.time() - start_time
    print(f"\n✅ Import complete!")
    print(f"📊 Processed: {processed:,} entries")
    print(f"📊 Imported: {imported_terms:,} term pairs")
    print(f"⏱️ Time: {elapsed:.1f} seconds")
    print(f"🚀 Rate: {processed/elapsed:.0f} entries/sec")
    
    return imported_terms

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python fast_import.py <tbx_file>")
        return
    
    tbx_file = sys.argv[1]
    if not os.path.exists(tbx_file):
        print(f"❌ File not found: {tbx_file}")
        return
    
    imported = fast_import_tbx(tbx_file)
    
    # Show final database stats
    with sqlite3.connect("terms.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM terms")
        total_terms = cursor.fetchone()[0]
        
        cursor.execute("SELECT source_lang, COUNT(*) FROM terms GROUP BY source_lang")
        lang_counts = dict(cursor.fetchall())
    
    print(f"\n📈 Final Database Stats:")
    print(f"   Total terms: {total_terms:,}")
    print(f"   By language: {lang_counts}")

if __name__ == "__main__":
    main() 