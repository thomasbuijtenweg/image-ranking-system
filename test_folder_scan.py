#!/usr/bin/env python3
"""
Standalone test script to debug folder scanning issues.

Run this script to test if the folder scanning is working correctly:
    python test_folder_scan.py /path/to/your/image/folder
"""

import os
import sys
from pathlib import Path

def test_folder_scanning(folder_path: str):
    """
    Test function to debug folder scanning issues.
    
    Args:
        folder_path: Path to test
    """
    print(f"\n🔍 TESTING FOLDER SCANNING")
    print(f"=" * 50)
    print(f"Path: {folder_path}")
    
    # Test basic path existence
    if not os.path.exists(folder_path):
        print("❌ ERROR: Path does not exist!")
        return []
    
    if not os.path.isdir(folder_path):
        print("❌ ERROR: Path is not a directory!")
        return []
    
    # Test permissions
    if not os.access(folder_path, os.R_OK):
        print("❌ ERROR: No read permission!")
        return []
    
    print("✅ Basic path checks passed")
    
    # Supported extensions (from your application)
    supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    extensions_lower = set(ext.lower() for ext in supported_extensions)
    
    print(f"Looking for extensions: {extensions_lower}")
    
    image_files = []
    
    try:
        # Use os.walk to scan all subdirectories
        dir_count = 0
        for root, dirs, files in os.walk(folder_path, followlinks=False):
            dir_count += 1
            
            # Calculate depth for better display
            depth = root.replace(folder_path, '').count(os.sep)
            indent = "  " * depth
            
            print(f"\n{indent}📁 Directory: {os.path.basename(root) if root != folder_path else 'ROOT'}")
            print(f"{indent}   Full path: {root}")
            print(f"{indent}   Subdirectories: {dirs}")
            print(f"{indent}   Total files: {len(files)}")
            
            # Skip hidden directories
            original_dirs = dirs[:]
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            if len(dirs) != len(original_dirs):
                hidden_dirs = [d for d in original_dirs if d.startswith('.')]
                print(f"{indent}   Skipping hidden dirs: {hidden_dirs}")
            
            # Count and list image files in this directory
            dir_images = []
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                # Check extension
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in extensions_lower):
                    # Get relative path from the base folder
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, folder_path)
                    
                    # Normalize path separators for consistency
                    relative_path = relative_path.replace(os.sep, '/')
                    
                    image_files.append(relative_path)
                    dir_images.append(file)
            
            if dir_images:
                print(f"{indent}   ✅ Found {len(dir_images)} image files:")
                for img in dir_images:
                    print(f"{indent}      • {img}")
            else:
                print(f"{indent}   ❌ No image files found")
        
        print(f"\n📊 SCAN SUMMARY:")
        print(f"=" * 50)
        print(f"Directories scanned: {dir_count}")
        print(f"Total image files: {len(image_files)}")
        
        if image_files:
            print(f"\n📋 ALL IMAGES FOUND:")
            for i, img in enumerate(image_files, 1):
                print(f"  {i:3d}. {img}")
        else:
            print("\n❌ NO IMAGES FOUND!")
            print("\nPossible reasons:")
            print("• No supported image formats in the folder")
            print("• All images are hidden files (start with '.')")
            print("• Permission issues")
            print("• Images are in unsupported formats")
            print(f"• Supported formats: {', '.join(supported_extensions)}")
        
        return sorted(image_files)
        
    except OSError as e:
        print(f"❌ ERROR scanning directory {folder_path}: {e}")
        return []


def show_folder_structure(folder_path: str, max_depth: int = 3):
    """
    Show the folder structure to help understand the layout.
    
    Args:
        folder_path: Path to analyze
        max_depth: Maximum depth to show
    """
    print(f"\n🌳 FOLDER STRUCTURE (max depth: {max_depth}):")
    print(f"=" * 50)
    
    try:
        for root, dirs, files in os.walk(folder_path):
            # Calculate depth
            depth = root.replace(folder_path, '').count(os.sep)
            
            if depth > max_depth:
                continue
            
            indent = "  " * depth
            folder_name = os.path.basename(root) if root != folder_path else "ROOT"
            
            print(f"{indent}📁 {folder_name}/")
            
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Show some files (limit to avoid spam)
            visible_files = [f for f in files if not f.startswith('.')]
            if visible_files:
                for file in visible_files[:5]:  # Show first 5 files
                    print(f"{indent}  📄 {file}")
                if len(visible_files) > 5:
                    print(f"{indent}  ... and {len(visible_files) - 5} more files")
            
            # If we're at max depth, show subdirectory names but don't recurse
            if depth == max_depth and dirs:
                print(f"{indent}  📁 ... and {len(dirs)} subdirectories")
                dirs.clear()  # Prevent recursion
    
    except OSError as e:
        print(f"❌ ERROR analyzing folder structure: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_folder_scan.py <folder_path>")
        print("\nExample:")
        print("  python test_folder_scan.py /path/to/your/images")
        print("  python test_folder_scan.py C:\\Users\\YourName\\Pictures")
        return
    
    folder_path = sys.argv[1]
    
    # Show folder structure first
    show_folder_structure(folder_path)
    
    # Test the scanning
    files = test_folder_scanning(folder_path)
    
    print(f"\n🏁 FINAL RESULT:")
    print(f"=" * 50)
    if files:
        print(f"✅ SUCCESS: Found {len(files)} image files")
        print(f"Images are in subfolders: {any('/' in f for f in files)}")
    else:
        print("❌ FAILED: No images found")
    
    return files


if __name__ == "__main__":
    main()
