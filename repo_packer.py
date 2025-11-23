import os

def pack_repo(output_file="_PROJECT_DUMP.txt", ignore_dirs=None, ignore_exts=None):
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.next', 'venv', 'env', '.venv'}
    if ignore_exts is None:
        ignore_exts = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.zip', '.tar', '.gz', '.lock'}

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(f"# PROJECT DUMP\n")
        outfile.write(f"# Generated to provide context to LLMs\n\n")

        for root, dirs, files in os.walk("."):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in ignore_exts:
                    continue
                
                # Skip the output file itself
                if file == output_file or file == os.path.basename(__file__):
                    continue

                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                        content = infile.read()
                        
                        # Write file header
                        outfile.write(f"\n{'='*50}\n")
                        outfile.write(f"FILE: {file_path}\n")
                        outfile.write(f"{'='*50}\n")
                        outfile.write(content)
                        outfile.write("\n")
                        
                    print(f"Packed: {file_path}")
                except Exception as e:
                    print(f"Skipped (Error): {file_path} - {str(e)}")

    print(f"\nDone! All code packed into: {output_file}")

if __name__ == "__main__":
    pack_repo()