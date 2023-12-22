"""Исключения."""


class EndPointError(Exception):
    """Недоступность эндпоинта."""

    pass


class UnexpectedStatusError(Exception):
    """Неожиданный статус домашней работы."""

    pass


class TokenError(Exception):
    """Ошибка в переменных окружения."""

    pass
