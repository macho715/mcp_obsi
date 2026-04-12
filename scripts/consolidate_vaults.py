import os
import shutil
from pathlib import Path


def consolidate_vaults():
    sources = ["vault", "vault-test", "vault-test2", "vault-test3"]
    target_dir = r"C:\Users\jichu\Downloads\valut"

    print(f"Target Directory: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    file_map = {}  # relative_path -> (source_path, mtime)

    for source in sources:
        if not os.path.exists(source):
            print(f"Source not found: {source}")
            continue

        print(f"Scanning source: {source}")
        source_path = Path(source)

        for root, _, files in os.walk(source):
            for file in files:
                filepath = Path(root) / file
                rel_path = filepath.relative_to(source_path)
                mtime = os.path.getmtime(filepath)

                if rel_path not in file_map:
                    file_map[rel_path] = (filepath, mtime)
                else:
                    existing_mtime = file_map[rel_path][1]
                    if mtime > existing_mtime:
                        file_map[rel_path] = (filepath, mtime)

    print(f"Total unique files to merge: {len(file_map)}")

    copied = 0
    for rel_path, (src_filepath, _mtime) in file_map.items():
        dest_path = Path(target_dir) / rel_path
        os.makedirs(dest_path.parent, exist_ok=True)
        shutil.copy2(src_filepath, dest_path)
        copied += 1

    print(f"Successfully consolidated {copied} files into {target_dir}")


if __name__ == "__main__":
    consolidate_vaults()
