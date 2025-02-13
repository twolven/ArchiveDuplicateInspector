import os
import hashlib
import zipfile
import pathlib
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog
import io
from typing import Dict, Set, List, Tuple
import logging
from tqdm import tqdm
import signal
import sys
from datetime import datetime

class ArchiveComparer:
    def __init__(self):
        self.folder_files: Dict[str, str] = {}  # path: hash
        self.archive_files: Dict[str, str] = {}  # path: hash
        self.chunk_size = 8192  # Optimal chunk size for reading files
        self.current_file = ""
        self.total_bytes_processed = 0
        self.total_bytes = 0
        self.start_time = None
        
    def format_size(self, size):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
    
    def format_time(self, seconds):
        """Convert seconds to human readable format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    def update_progress(self):
        """Update the progress display"""
        if self.start_time is None:
            return
        
        elapsed_time = datetime.now() - self.start_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        if self.total_bytes_processed > 0:
            progress = (self.total_bytes_processed / self.total_bytes) * 100
            speed = self.total_bytes_processed / elapsed_seconds
            remaining_bytes = self.total_bytes - self.total_bytes_processed
            eta = remaining_bytes / speed if speed > 0 else 0
            
            # Clear the line and update progress
            print(f"\r{' ' * 100}", end='')
            print(f"\rProcessing: {self.current_file[:50]}..." if len(self.current_file) > 50 else f"\rProcessing: {self.current_file}")
            print(f"Progress: {progress:.2f}% | "
                  f"Speed: {self.format_size(speed)}/s | "
                  f"Processed: {self.format_size(self.total_bytes_processed)} / {self.format_size(self.total_bytes)} | "
                  f"ETA: {self.format_time(eta)}", end='\r')
    
    def get_total_folder_size(self, folder_path: str) -> int:
        """Calculate total size of all files in folder"""
        total_size = 0
        try:
            for path in pathlib.Path(folder_path).rglob('*'):
                try:
                    if path.is_file():
                        total_size += path.stat().st_size
                except (PermissionError, OSError) as e:
                    logging.warning(f"Could not access {path}: {e}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
        return total_size

    def get_archive_size(self, archive_path: str) -> int:
        """Calculate total uncompressed size of archive"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                return sum(info.file_size for info in zip_file.filelist)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file using chunked reading."""
        sha256_hash = hashlib.sha256()
        file_size = os.path.getsize(file_path)
        processed_size = 0
        
        try:
            with open(file_path, "rb") as f:
                self.current_file = str(file_path)
                for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(byte_block)
                    processed_size += len(byte_block)
                    self.total_bytes_processed += len(byte_block)
                    self.update_progress()
            return sha256_hash.hexdigest()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
    
    def scan_folder(self, folder_path: str) -> None:
        """Scan folder and calculate hashes for all files."""
        self.start_time = datetime.now()
        self.total_bytes_processed = 0
        
        try:
            files = list(pathlib.Path(folder_path).rglob('*'))
            with ThreadPoolExecutor() as executor:
                future_to_file = {
                    executor.submit(self.calculate_file_hash, str(file)): file
                    for file in files if file.is_file()
                }
                
                for future in future_to_file:
                    file = future_to_file[future]
                    try:
                        self.folder_files[str(file)] = future.result()
                    except Exception as e:
                        logging.error(f"Error processing {file}: {e}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

    def scan_archive(self, archive_path: str) -> None:
        """Scan archive and calculate hashes for all files."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if not file_info.is_dir():
                        self.current_file = file_info.filename
                        self.update_progress()
                        
                        with zip_file.open(file_info) as f:
                            sha256_hash = hashlib.sha256()
                            for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                                sha256_hash.update(byte_block)
                                self.total_bytes_processed += len(byte_block)
                                self.update_progress()
                            
                        self.archive_files[file_info.filename] = sha256_hash.hexdigest()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

def main():
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nOperation cancelled by user.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create GUI for folder and file selection
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Select folder to compare against
        print("Please select folder to compare against...")
        folder_path = filedialog.askdirectory(title="Select folder to compare against")
        if not folder_path:
            print("No folder selected. Exiting.")
            return
        
        # Select archive file
        print("Please select archive file...")
        archive_path = filedialog.askopenfilename(
            title="Select archive file",
            filetypes=[("ZIP files", "*.zip")]
        )
        if not archive_path:
            print("No archive selected. Exiting.")
            return
        
        # Select output directory
        print("Please select output directory for extracted files...")
        output_path = filedialog.askdirectory(title="Select output directory for extracted files")
        if not output_path:
            print("No output directory selected. Exiting.")
            return
        
        # Initialize comparer
        comparer = ArchiveComparer()
        
        # Calculate total sizes
        print("\nCalculating total sizes...")
        comparer.total_bytes = comparer.get_total_folder_size(folder_path)
        comparer.total_bytes += comparer.get_archive_size(archive_path)
        
        # Scan folder and archive
        print("\nScanning folder...")
        comparer.scan_folder(folder_path)
        
        print("\n\nScanning archive...")
        comparer.total_bytes_processed = 0  # Reset for archive scanning
        comparer.start_time = datetime.now()
        comparer.scan_archive(archive_path)
        
        # Compare and extract files
        print("\n\nComparing files and extracting non-duplicates...")
        duplicates = []
        extracted = []
        
        # Create reverse lookup for folder hashes
        folder_hashes = {hash_value: path for path, hash_value in comparer.folder_files.items()}
        
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            for filename, file_hash in comparer.archive_files.items():
                if file_hash in folder_hashes.keys():
                    duplicates.append((filename, folder_hashes[file_hash]))
                else:
                    zip_file.extract(filename, output_path)
                    extracted.append(filename)
        
        # Generate report
        print("\n\nDiff Report:")
        print("-" * 50)
        print(f"\nArchive examined: {archive_path}")
        print(f"Compared against folder: {folder_path}")
        print(f"Files extracted to: {output_path}")
        print("-" * 50)
        
        print(f"\nDuplicate files found ({len(duplicates)}):")
        for archive_file, folder_file in duplicates:
            print(f"Archive: {archive_file}")
            print(f"Matches: {folder_file}\n")
        
        print(f"\nFiles extracted ({len(extracted)}):")
        for file in extracted:
            print(f"- {file}")
        
        # Summary statistics
        print("\nSummary:")
        print("-" * 50)
        print(f"Archive processed: {os.path.basename(archive_path)}")
        print(f"Total archive size: {comparer.format_size(comparer.get_archive_size(archive_path))}")
        print(f"Total folder size scanned: {comparer.format_size(comparer.get_total_folder_size(folder_path))}")
        print(f"Total files processed: {len(comparer.archive_files)}")
        print(f"Total duplicates: {len(duplicates)}")
        print(f"Total files extracted: {len(extracted)}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()