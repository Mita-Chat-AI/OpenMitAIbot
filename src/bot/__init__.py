import asyncio
import warnings

# Подавляем предупреждение о ffmpeg/avconv от pydub ДО всех импортов
warnings.filterwarnings("ignore", message=".*Couldn't find ffmpeg or avconv.*", category=RuntimeWarning)

from .__main__ import main

asyncio.run(main())
