from abc import ABC

from loguru import logger


class Service(ABC):
    def __init__(self):
        self.logger = logger.bind(name=self.__class__.__name__)