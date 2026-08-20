import json
from pathlib import Path


ARCHITECTURE_FILE = "architecture.json"


def load_architecture():
    architecture_path = Path(ARCHITECTURE_FILE)

    if not architecture_path.exists():
        raise FileNotFoundError(
            f"Architecture file not found: {ARCHITECTURE_FILE}"
        )

    with architecture_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def create_directories(root_path, directories):
    for directory in directories:
        directory_path = root_path / directory

        if directory_path.exists():
            print(f"↳ Directory already exists: {directory}")
        else:
            directory_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {directory}")


def create_files(root_path, files):
    for file in files:
        file_path = root_path / file

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            print(f"↳ File already exists: {file}")
        else:
            file_path.touch()
            print(f"✓ Created file: {file}")


def print_tree(path, prefix=""):
    items = sorted(
        path.iterdir(),
        key=lambda item: (item.is_file(), item.name.lower())
    )

    for index, item in enumerate(items):

        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "

        print(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension)


def main():

    root_path = Path.cwd()

    print("=" * 60)
    print("FLASK SHOP PROJECT GENERATOR")
    print("=" * 60)

    print(f"\nRoot directory: {root_path}")

    architecture = load_architecture()

    print("\nCreating directories...")
    create_directories(
        root_path,
        architecture.get("directories", [])
    )

    print("\nCreating files...")
    create_files(
        root_path,
        architecture.get("files", [])
    )

    print("\n" + "=" * 60)
    print("PROJECT STRUCTURE CREATED")
    print("=" * 60)

    print_tree(root_path)


if __name__ == "__main__":
    main()