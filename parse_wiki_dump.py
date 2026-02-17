#!/usr/bin/env python3
"""
Parse Wikipedia XML dump and convert to Parquet format.
Extracts page titles and text content.
"""

import bz2
import xml.etree.ElementTree as ET
from pathlib import Path
import polars as pl

# Define the Wikipedia dump namespace
NS = {'wiki': 'http://www.mediawiki.org/xml/export-0.10/'}

def parse_wiki_dump(bz2_file_path: str, output_dir: str, batch_size: int = 50000):
    """
    Parse Wikipedia XML dump from BZ2 file and write to Parquet in batches.
    
    Args:
        bz2_file_path: Path to the BZ2-compressed XML file
        output_dir: Directory to write the Parquet files
        batch_size: Number of pages to process before writing to disk
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    batch_num = 0
    total_pages = 0
    
    print(f"Reading from: {bz2_file_path}")
    print(f"Parsing XML dump (batch size: {batch_size})...")
    
    with bz2.open(bz2_file_path, 'rt', encoding='utf-8') as f:
        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag == f"{{{NS['wiki']}}}page":
                try:
                    # Extract title
                    title_elem = elem.find('wiki:title', NS)
                    title = title_elem.text if title_elem is not None else None
                    
                    # Extract text content
                    revision = elem.find('wiki:revision', NS)
                    text = None
                    if revision is not None:
                        text_elem = revision.find('wiki:text', NS)
                        text = text_elem.text if text_elem is not None else None
                    
                    if title:  # Only include entries with a title
                        pages.append({
                            'title': title,
                            'text': text
                        })
                    
                    # Write batch to disk when threshold is reached
                    if len(pages) >= batch_size:
                        batch_num += 1
                        total_pages += len(pages)
                        _write_batch(pages, output_dir, batch_num)
                        print(f"  Written batch {batch_num} ({len(pages)} pages, total: {total_pages})")
                        pages = []
                
                finally:
                    # Clear the element to free memory
                    elem.clear()
    
    # Write remaining pages
    if pages:
        batch_num += 1
        total_pages += len(pages)
        _write_batch(pages, output_dir, batch_num)
        print(f"  Written batch {batch_num} ({len(pages)} pages, total: {total_pages})")
    
    print(f"✓ Done! Written {total_pages} pages to {output_dir} in {batch_num} batch(es)")


def _write_batch(pages: list, output_dir: Path, batch_num: int):
    """Write a batch of pages to a Parquet file."""
    df = pl.DataFrame(pages)
    output_file = output_dir / f"wiki_data_batch_{batch_num:05d}.parquet"
    df.write_parquet(output_file)


if __name__ == "__main__":
    input_file = "/mnt/wd/wiki-data/active/basedir/enwiki/20230501/enwiki-20230501-pages-articles-multistream.xml.bz2"
    output_directory = "/mnt/samsung/wiki-data/"
    
    parse_wiki_dump(input_file, output_directory)
