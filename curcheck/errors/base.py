class BaseError(Exception):
    """ Базовый класс """


class SiteConfigurationError(BaseError):
    def __init__(self, message: str) -> None:
        self.message = f"Ошибка конфигурации сайта: {message}"

        super().__init__(self.message)

