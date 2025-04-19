# setup_fonts.py

import os
import urllib.request
import zipfile
import shutil
import time

# --- Constants for Font Setup ---
FONT_DIR = 'fonts'
# Define all required font files
REQUIRED_FONTS = {
    "regular": "DejaVuSans.ttf",
    "bold": "DejaVuSans-Bold.ttf",
    "italic": "DejaVuSans-Oblique.ttf", # Standard name for DejaVu Italic
    "bold_italic": "DejaVuSans-BoldOblique.ttf" # Standard name for DejaVu Bold Italic
}
FONT_PATHS = {key: os.path.join(FONT_DIR, fname) for key, fname in REQUIRED_FONTS.items()}

# URL for a specific stable release ZIP file from GitHub
FONT_URL = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
FONT_ZIP_PATH = os.path.join(FONT_DIR, 'dejavu-fonts-temp.zip')
FONT_EXTRACT_DIR = os.path.join(FONT_DIR, 'extracted_fonts')

def setup_fonts(force_download=False):
    """Checks for DejaVu fonts (Regular, Bold, Italic, BoldItalic) and downloads/installs them if missing."""
    print("\n--- Checking/Setting up required PDF fonts (DejaVu Sans variants) ---")
    os.makedirs(FONT_DIR, exist_ok=True)

    # Check if all required fonts exist
    all_fonts_exist = all(os.path.exists(path) for path in FONT_PATHS.values())

    if all_fonts_exist and not force_download:
        print("Required DejaVu fonts found.")
        return True

    if force_download:
        print("Forcing download/reinstallation of fonts...")
        # Clean up existing potentially incomplete set if forcing
        for path in FONT_PATHS.values():
            if os.path.exists(path): os.remove(path)
    else:
        print("One or more required DejaVu fonts not found. Attempting download...")

    # Clean up temp files from previous attempts if necessary
    if os.path.exists(FONT_ZIP_PATH): os.remove(FONT_ZIP_PATH)
    if os.path.exists(FONT_EXTRACT_DIR): shutil.rmtree(FONT_EXTRACT_DIR)

    # --- Download ---
    try:
        print(f"Downloading fonts archive from {FONT_URL}...")
        hdr = {'User-Agent': 'Mozilla/5.0'} # User agent can help avoid blocking
        req = urllib.request.Request(FONT_URL, headers=hdr)
        with urllib.request.urlopen(req) as response, open(FONT_ZIP_PATH, 'wb') as out_file:
            if response.status != 200: raise Exception(f"Download failed: HTTP {response.status}")
            shutil.copyfileobj(response, out_file)
        print(f"Download complete: {FONT_ZIP_PATH}")
    except Exception as e:
        print(f"ERROR: Failed to download fonts: {e}")
        if os.path.exists(FONT_ZIP_PATH): os.remove(FONT_ZIP_PATH)
        return False

    # --- Extract ---
    try:
        print(f"Extracting fonts from {FONT_ZIP_PATH}...")
        os.makedirs(FONT_EXTRACT_DIR, exist_ok=True)
        with zipfile.ZipFile(FONT_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(FONT_EXTRACT_DIR)
        print(f"Extraction complete into: {FONT_EXTRACT_DIR}")
    except Exception as e:
        print(f"ERROR: Failed to extract fonts: {e}")
        if os.path.exists(FONT_EXTRACT_DIR): shutil.rmtree(FONT_EXTRACT_DIR)
        if os.path.exists(FONT_ZIP_PATH): os.remove(FONT_ZIP_PATH)
        return False

    # --- Find and Move All Required Fonts ---
    fonts_moved_count = 0
    try:
        print("Searching for required .ttf files in extracted content...")
        # Walk through extracted files to find TTFs
        ttf_source_dir = None
        for root, dirs, files in os.walk(FONT_EXTRACT_DIR):
             # Check if *any* required font is in this directory
             if any(fname in files for fname in REQUIRED_FONTS.values()):
                  ttf_source_dir = root
                  print(f"Found potential TTF files in: {ttf_source_dir}")
                  break # Assume all TTFs are in the same directory

        if ttf_source_dir:
            for key, fname in REQUIRED_FONTS.items():
                src_path = os.path.join(ttf_source_dir, fname)
                dest_path = FONT_PATHS[key]
                if os.path.exists(src_path):
                     print(f"Moving {fname} to {FONT_DIR}...")
                     shutil.move(src_path, dest_path)
                     fonts_moved_count += 1
                else:
                     print(f"WARN: Expected font file '{fname}' not found in {ttf_source_dir}. Check archive contents.")
        else:
            print("ERROR: Could not locate directory containing required TTF files within the archive.")

    except Exception as e:
        print(f"ERROR: Failed during font moving process: {e}")

    # --- Cleanup ---
    finally:
        print("Cleaning up temporary download files...")
        if os.path.exists(FONT_ZIP_PATH):
            try: os.remove(FONT_ZIP_PATH); print(f"Removed {FONT_ZIP_PATH}")
            except OSError as e: print(f"Warning: Could not remove {FONT_ZIP_PATH}: {e}")
        if os.path.exists(FONT_EXTRACT_DIR):
            try: shutil.rmtree(FONT_EXTRACT_DIR); print(f"Removed {FONT_EXTRACT_DIR}")
            except OSError as e: print(f"Warning: Could not remove {FONT_EXTRACT_DIR}: {e}")

    # Final check if all required fonts are now present
    if all(os.path.exists(path) for path in FONT_PATHS.values()):
        print(f"All {len(REQUIRED_FONTS)} required fonts successfully installed/verified.")
        return True
    else:
        print(f"ERROR: Font installation failed. Missing {len(REQUIRED_FONTS) - fonts_moved_count} required font(s) after process.")
        return False

# Allow running this script directly for setup/update
if __name__ == "__main__":
    print("Running font setup directly...")
    # Use force_download=True to update/reinstall if needed when run directly
    success = setup_fonts(force_download=True)
    if success: print("Font setup completed successfully.")
    else: print("Font setup failed.")