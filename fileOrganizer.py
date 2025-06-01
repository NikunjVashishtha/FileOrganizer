import os
import shutil
import json
import argparse
import sys
import time

builtInFileTypes = {
  "audio": ["mp3", "wav", "aac", "flac", "ogg", "m4a", "wma", "alac", "aiff", "amr"],
  "video": ["mp4", "mkv", "avi", "mov", "flv", "wmv", "webm", "mpeg", "mpg", "3gp", "m4v", "ts"],
  "image": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "webp", "ico", "heic", "raw"],
  "document": ["pdf", "docx", "txt", "doc", "odt", "rtf", "md", "epub", "xls", "xlsx", "ppt", "pptx", "csv", "tsv", "json", "xml", "tex", "log"],
  "archive": ["zip", "rar", "tar", "gz", "7z", "bz2", "xz", "iso", "tgz", "tar.gz", "lz", "lzma"],
  "code": ["py", "js", "html", "css", "java", "c", "cpp", "php", "rb", "go", "ts", "jsx", "tsx", "cs", "swift", "kt", "rs", "sh", "bat", "pl", "scala", "lua", "m", "h", "json", "xml", "yml", "yaml", "ini", "sql", "ipynb"],
  "database": ["db", "sql", "sqlite", "mdb", "accdb", "dbf", "sqlite3"],
  "spreadsheet": ["xls", "xlsx", "csv", "ods", "tsv", "xlsm", "numbers"],
  "presentation": ["ppt", "pptx", "odp", "key"],
  "executable": ["exe", "bat", "sh", "msi", "apk", "app", "com", "jar", "gadget", "wsf", "bin", "command", "run"],
  "font": ["ttf", "otf", "woff", "woff2", "eot", "fon", "fnt"]
}

def parse_args():
    # Parse command-line arguments using argparse
    parser = argparse.ArgumentParser(
        description="Organize files in a directory by file type.",
        usage="%(prog)s [-h] [-d DIRECTORY] [-s] [-f FILETYPES_JSON]"
    )
    parser.add_argument(
        "-d", "--dir", dest="directory", help="Directory to organize"
    )
    parser.add_argument(
        "-s", "--noverbose", action="store_false", dest="verbose", default=True, help="Disable verbose output"
    )
    parser.add_argument(
        "-f", "--filetypes", dest="filetypes", help="Path to custom file types JSON file", default="fileTypes.json"
    )
    parser.add_argument(
        "positional_directory", nargs="?", help="Directory to organize (positional argument)"
    )
    return parser.parse_args()

def safe_move(src, dst):
    # Move file safely, appending a number if a file with the same name exists
    base = os.path.basename(src)
    dst_path = os.path.join(dst, base)
    if os.path.exists(dst_path):
        name, ext = os.path.splitext(base)
        i = 1
        while True:
            new_name = f"{name}_{i}{ext}"
            new_dst_path = os.path.join(dst, new_name)
            if not os.path.exists(new_dst_path):
                dst_path = new_dst_path
                break
            i += 1
    shutil.move(src, dst_path)
    return dst_path

def organize(directory, fileTypes, verbose=True):
    # Organize files in the given directory according to fileTypes mapping
    script_path = os.path.abspath(__file__)
    if not os.path.exists(directory):
        print(f"\u001b[31mDirectory {directory} does not exist.\u001b[0m")
        return
    moved_count = 0
    skipped_count = 0
    skipped_items = []
    start_time = time.time()
    try:
        for item in os.listdir(directory):
            # Skip hidden files and directories
            if item.startswith('.'):
                skipped_count += 1
                skipped_items.append(item)
                if verbose:
                    print(f"\u001b[33mSkipping hidden file or directory {item}\u001b[0m")
                continue
            item_path = os.path.join(directory, item)
            # Skip the script itself
            if os.path.abspath(item_path) == script_path:
                skipped_count += 1
                skipped_items.append(item)
                if verbose:
                    print(f"\u001b[33mSkipping self: {item}\u001b[0m")
                continue
            if os.path.isfile(item_path):
                # Skip files already in a subdirectory
                if os.path.dirname(item_path) != os.path.abspath(directory):
                    skipped_count += 1
                    skipped_items.append(item)
                    continue
                # Get file extension (if any)
                if '.' in item:
                    ext = item.rsplit('.', 1)[-1].lower()
                else:
                    ext = ""
                # Determine category for the extension
                category_found = False
                for category, extensions in fileTypes.items():
                    if ext in extensions:
                        ext = category
                        category_found = True
                        break
                if not category_found or not ext:
                    ext = "unknown"
                ext_dir = os.path.join(directory, ext)
                # Create category directory if it doesn't exist
                if not os.path.exists(ext_dir):
                    try:
                        os.makedirs(ext_dir)
                    except Exception as e:
                        print(f"\u001b[31mFailed to create directory {ext_dir}: {e}\u001b[0m")
                        skipped_count += 1
                        skipped_items.append(item)
                        continue
                # Move file to category directory
                try:
                    safe_move(item_path, ext_dir)
                    moved_count += 1
                    if verbose:
                        print(f"\u001b[32mMoved {item} to {ext_dir}\u001b[0m")
                except Exception as e:
                    print(f"\u001b[31mError moving {item}: {e}\u001b[0m")
                    skipped_count += 1
                    skipped_items.append(item)
            elif os.path.isdir(item_path):
                # Skip subdirectories
                if os.path.abspath(item_path) == os.path.abspath(directory):
                    continue
                skipped_count += 1
                skipped_items.append(item)
                if verbose:
                    print(f"\u001b[33mSkipping directory {item}\u001b[0m")
    except NotADirectoryError:
        print(f"\u001b[31m{directory} is not a directory\u001b[0m")
    except KeyboardInterrupt:
        print("\u001b[31mProcess interrupted by user.\u001b[0m")
    except Exception as e:
        print(f"\u001b[31mUnexpected error: {e}\u001b[0m")
    else:
        elapsed = time.time() - start_time
        print("\u001b[32mOrganization complete.\u001b[0m")
        print(f"\u001b[32mTotal files moved: {moved_count}\u001b[0m")
        print(f"\u001b[33mTotal files/folders skipped: {skipped_count}\u001b[0m")
        if skipped_items:
            print("\u001b[33mSkipped items:\u001b[0m")
            for s in skipped_items:
                print(f"  - {s}")
        print(f"\u001b[32mTime taken: {elapsed:.2f} seconds\u001b[0m")

if __name__ == "__main__":
    try:
        args = parse_args()
        # Determine directory to organize from arguments or prompt
        if args.directory:
            directory = args.directory
        elif args.positional_directory:
            directory = args.positional_directory
        else:
            print("Directory not specified. Defaulting to current directory.")
            directory = os.getcwd()
        # Load fileTypes JSON mapping or use built-in if not provided
        if args.filetypes and args.filetypes != "fileTypes.json":
            filetypes_path = args.filetypes
            if not os.path.isabs(filetypes_path):
                filetypes_path = os.path.join(os.path.dirname(__file__), filetypes_path)
            try:
                with open(filetypes_path, "r", encoding="utf-8") as f:
                    fileTypesToUse = json.load(f)
            except Exception as e:
                print(f"Failed to load file types from {filetypes_path}: {e}")
                sys.exit(1)
        else:
            fileTypesToUse = builtInFileTypes
        # Start organizing files
        organize(directory, fileTypesToUse, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")