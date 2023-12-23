"""Бот проверки статуса домашних работ в Яндекс.Практикум."""

import logging
import os
import requests
import sys
import telegram
import time

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import EndPointError, UnexpectedStatusError, StatusCodeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.critical(
            'Критическая ошибка: недоступны переменные окружения!'
        )
        return False
    return True


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(
            'Сообщение отправлено!'
        )
    except Exception:
        logging.error(
            'Ошибка! Сообщение не отправлено!'
        )


def get_api_answer(timestamp):
    """Функция делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
    except Exception:
        logging.error(
            'Ошибка! Cбой при запросе к эндпоинту!'
        )
        message = 'Cбой при запросе к эндпоинту!'
        raise EndPointError(message)
    if api_answer.status_code != HTTPStatus.OK:
        logging.error('Ошибка! Код ответа сервера не соотвествует ожидаемому!')
        message = 'Код ответа не соотвествует ожидаемому!'
        raise StatusCodeError(message)
    response = api_answer.json()
    return response


def check_response(response):
    """Функция возвращает информацию обо всех домашних работах."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error(
            'Ошибка! Отсутствие ожидаемых ключей в ответе API!'
        )
        message = 'Отсутствие ожидаемых ключей в ответе API!'
        raise KeyError(message)
    if type(homeworks) is not list:
        raise TypeError
    return homeworks


def parse_status(homework):
    """Функция извлекает из конкретной домашней работы статус этой работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        logging.error('Ошибка! Неожиданный статус домашней работы!')
        raise UnexpectedStatusError
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    """Логгер проекта."""
    logging.basicConfig(
        format='%(asctime)s, %(levelname)s, %(message)s, %(lineno)s',
        level=logging.DEBUG,
        encoding='utf-8'
    )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        message = ('Критическая ошибка: отсутствуют'
                   'переменные окружения. Работа программы приостановлена.')
        send_message(bot, message)
        sys.exit('Отсутствуют переменные окружения.')
    timestamp = int(time.time())
    current_statuses = {}
    while True:
        try:
            api_resp = get_api_answer(timestamp)
            homeworks = check_response(api_resp)
            for homework in homeworks:
                homework_id = homework.get('id')
                new_status = parse_status(homework)
                status = current_statuses.get(homework_id)
                if new_status != status:
                    current_statuses[homework_id] = new_status
                    send_message(bot, new_status)
                else:
                    logging.debug(
                        'Статус работы не изменился.'
                    )

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
