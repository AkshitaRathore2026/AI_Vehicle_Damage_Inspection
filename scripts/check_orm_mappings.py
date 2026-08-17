import sys
from pathlib import Path

from sqlalchemy.orm import configure_mappers

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base


def main() -> None:
    configure_mappers()
    print("ORM mappings configured successfully")
    print(sorted(Base.metadata.tables.keys()))


if __name__ == "__main__":
    main()
