import os
import shutil
from pathlib import Path
from app.graphrag_service import graphrag_service
from app.config import settings


def migrate_graphrag_knowledge():
    old_path = "./nsf_graphrag_knowledge"
    new_path = settings.graphrag_working_dir

    if Path(old_path).exists() and old_path != new_path:
        print(f"Migrating GraphRAG knowledge base from {old_path} to {new_path}")

        if Path(new_path).exists():
            shutil.rmtree(new_path)

        shutil.copytree(old_path, new_path)
        print("✅ GraphRAG knowledge base migrated")
    else:
        print("No existing GraphRAG knowledge base found or already in correct location")


def cleanup_old_files():
    old_files = [
        "app.py",
        "nsf_doc_scanner.py",
        "nsf_ingest.py",
        "query.py"
    ]

    print("Cleaning up old files...")
    for file in old_files:
        if Path(file).exists():
            backup_dir = Path("backup_old_files")
            backup_dir.mkdir(exist_ok=True)
            shutil.move(file, backup_dir / file)
            print(f"Moved {file} to backup_old_files/")

    print("✅ Old files backed up")


def main():
    print("NSF AI App Migration Script")
    print("=" * 30)

    migrate_graphrag_knowledge()

    choice = input("\nMove old files to backup folder? (y/N): ")
    if choice.lower() == 'y':
        cleanup_old_files()

    print("\n🎉 Migration complete!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and fill in your values")
    print("2. Run: python scripts/setup_database.py")
    print("3. Start API: uvicorn app.main:app --reload")
    print("4. Start frontend: chainlit run frontend/chat_interface.py")


if __name__ == "__main__":
    main()