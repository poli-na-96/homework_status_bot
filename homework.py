"""Бот проверки статуса домашних работ в Яндес.Практикум."""

import logging
import os
import requests
import telegram
import time

from dotenv import load_dotenv

from exceptions import EndPointError, UnexpectedStatusError, TokenError

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


logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(message)s',
    level=logging.DEBUG,
    encoding='utf-8'
    )


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    tokens = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for token in tokens:
        if token not in globals():
            logging.critical(
                'Критическая ошибка: недоступны переменные окружения!'
            )
            return False
    global PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    if (PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or
            TELEGRAM_CHAT_ID is None):
        logging.critical(
            'Критическая ошибка: недоступны переменные окружения!'
        )
        return False
    return True


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id, message)
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
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
    except Exception:
        logging.error(
            'Ошибка! Cбой при запросе к эндпоинту!'
        )
        message = 'Cбой при запросе к эндпоинту!'
        send_message(bot, message)
    if api_answer.status_code != 200:
        logging.error('Ошибка! Недоступен эндпоинт!')
        message = 'Недоступен эндпоинт!'
        send_message(bot, message)
        raise EndPointError
    response = api_answer.json()
    return response


def check_response(response):
    """Функция возвращает информацию обо всех домашних работах."""
    try:
        homeworks = response['homeworks']
        if type(homeworks) is not list:
            raise TypeError
    except KeyError:
        logging.error(
            'Ошибка! Отсутствие ожидаемых ключей в ответе API!'
        )
        message = 'Отсутствие ожидаемых ключей в ответе API!'
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        send_message(bot, message)
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
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_statuses = {}
    if check_tokens() is False:
        message = ('Критическая ошибка: отсутствуют'
                   'переменные окружения. Работа программы приостановлена.')
        send_message(bot, message)
        raise TokenError
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
