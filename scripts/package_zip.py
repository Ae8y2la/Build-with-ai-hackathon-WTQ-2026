import os
import zipfile
import sys

def package_submission():
    zip_filename = "submission.zip"
    
    # Exclude these exact directories
    exclusions = {".env", ".cache", "venv", "__pycache__", "train", "test", "tests"}
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. output/ folder
        if os.path.exists("output"):
            for root, dirs, files in os.walk("output"):
                for file in files:
                    fpath = os.path.join(root, file)
                    zipf.write(fpath, arcname=fpath)
                    
        # 2. demo/ folder (if present)
        if os.path.exists("demo"):
            for root, dirs, files in os.walk("demo"):
                for file in files:
                    fpath = os.path.join(root, file)
                    zipf.write(fpath, arcname=fpath)
                    
        # 3. source/ folder (maps project root into source/)
        for root, dirs, files in os.walk("."):
            # Don't descend into excluded dirs or hidden dirs
            dirs[:] = [d for d in dirs if d not in exclusions and not d.startswith('.')]
            
            # Normalize path
            r = root.lstrip(".\\/")
            
            # Exclude output, demo, and template so they aren't duplicated inside source/
            if r == "output" or r.startswith("output\\") or r.startswith("output/"):
                continue
            if r == "demo" or r.startswith("demo\\") or r.startswith("demo/"):
                continue
            if r == "template" or r.startswith("template\\") or r.startswith("template/"):
                continue
                
            for file in files:
                if file == zip_filename:
                    continue
                if file == ".env":
                    continue
                    
                fpath = os.path.join(root, file)
                # Map to source/...
                arcname = os.path.join("source", r, file) if r else os.path.join("source", file)
                zipf.write(fpath, arcname=arcname)
                
    # Size check
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"Created {zip_filename} ({size_mb:.2f} MB)")
    
    if size_mb > 15:
        print(f"Error: {zip_filename} exceeds 15 MB limit!")
        sys.exit(1)
    else:
        print("Packaging successful! Zip is within size limits.")

if __name__ == "__main__":
    package_submission()
