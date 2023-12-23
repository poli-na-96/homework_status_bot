"""Исключения."""


class StatusCodeError(Exception):
    """Неожиданный статус домашней работы."""

    pass


class EndPointError(Exception):
    """Недоступность эндпоинта."""

    pass


class UnexpectedStatusError(Exception):
    """Неожиданный статус домашней работы."""

    pass
