# Archive Duplicate Inspector

A high-performance Python tool for analyzing ZIP archives and extracting only unique files by comparing against an existing folder structure. Designed to handle large archives (50GB+) efficiently with real-time progress monitoring.

# About Archive Duplicate Inspector

This tool was developed to solve the challenge of managing large photo archives and backups from multiple sources. When consolidating photos and files from various backup services, cloud storage, or old drives, it's common to encounter duplicate files across multiple archives. Manually comparing and extracting unique files is time-consuming and puts unnecessary wear on SSDs through repeated write operations.

Archive Duplicate Inspector automates this process by:
- Reading and comparing files from ZIP archives against your existing collection
- Only extracting files that aren't already in your collection
- Providing detailed reports of duplicates and new files
- Minimizing disk writes by avoiding extraction of duplicates

This approach is particularly useful for:
- Photo collection management
- Backup consolidation
- Archive organization
- Storage optimization

By performing in-memory comparisons before extraction, the tool significantly reduces disk operations and saves time when processing large archives.

## Features

- Compare ZIP archives against existing folder structures
- Extract only non-duplicate files
- Real-time progress monitoring with ETA
- Memory-efficient processing using chunked reading
- Multi-threaded file hash calculation
- Graceful interrupt handling
- Detailed reporting of duplicates and extracted files
- Support for large archives (tested on 50GB+)

## Requirements

- Python 3.7+
- tqdm package (`pip install tqdm`)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/archive-inspector.git
cd archive-inspector
```

2. Install required package:
```bash
pip install tqdm
```

## Usage

Run the script:
```bash
python archive_inspector.py
```

The script will prompt you to:
1. Select the folder to compare against
2. Select the ZIP archive to analyze
3. Select the output directory for extracted files

## How It Works

1. **Folder Analysis**: 
   - Recursively scans the selected folder
   - Calculates SHA256 hashes for all files
   - Uses multi-threading for performance

2. **Archive Analysis**:
   - Scans the ZIP archive contents
   - Calculates hashes for all archived files
   - Maintains memory efficiency with chunked reading

3. **Comparison & Extraction**:
   - Compares file hashes between folder and archive
   - Extracts only files that don't exist in the folder
   - Generates detailed report of duplicates and extracted files

## Performance

- Tested successfully on archives exceeding 50GB
- Memory usage remains constant regardless of archive size
- Progress monitoring provides accurate ETA and processing speed
- Can be safely interrupted at any time with Ctrl+C

## Output

The script provides:
- Real-time progress monitoring
- Processing speed and ETA
- Detailed report of:
  - Archive processed
  - Comparison folder used
  - Extraction location
  - List of duplicate files
  - List of extracted files
  - Total statistics

## Example Output

```
Diff Report:
--------------------------------------------------

Archive examined: /path/to/large_archive.zip
Compared against folder: /path/to/existing/files
Files extracted to: /path/to/output

Duplicate files found (125):
Archive: document1.pdf
Matches: /existing/files/document1.pdf

Files extracted (45):
- unique_file1.pdf
- unique_file2.doc

Summary:
--------------------------------------------------
Archive processed: large_archive.zip
Total archive size: 52.34 GB
Total folder size scanned: 128.45 GB
Total files processed: 170
Total duplicates: 125
Total files extracted: 45
```

## Limitations

- Currently supports ZIP archives only
- Requires sufficient disk space for temporary hash calculations
- Progress cannot be resumed if interrupted

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses Python's zipfile library for archive handling
- Implements ThreadPoolExecutor for parallel processing
- Uses tqdm for progress display functionality