import importlib
import sys
from pathlib import Path
from typing import List

from aiogram import Router
from loguru import logger


async def load_routers() -> List[Router]:
    routers = []
    base_path = Path(__file__).parent
    root = base_path.parent.parent.parent.resolve()
    print(base_path)
    print(root)

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    for file in base_path.rglob("*.py"):
        if file.name == "__init__.py":
            continue

        name = (
            file.relative_to(root)
            .with_suffix("")
            .as_posix()
            .replace("/", ".")
        )

        try:
            module = importlib.import_module(name)
            found = [obj for obj in module.__dict__.values() if isinstance(obj, Router)]
            if found:
                routers.extend(found)
                logger.success(f"Загружено {len(found)} роутеров из {name}")
            else:
                logger.warning(f"В модуле {name} роутеров не найдено")
        except Exception as e:
            logger.error(f"Ошибка импорта {name}: {e}")

    return routers
