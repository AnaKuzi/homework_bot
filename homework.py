import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
str_fmt = '[%(asctime)s] [%(levelname)s] > %(message)s'
date_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(fmt=str_fmt, datefmt=date_fmt)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Отправлено сообщение: {message}')
    except telegram.TelegramError:
        logger.error('Не удалось отправить сообщение.')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        status = response.status_code
        if status == HTTPStatus.OK:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                logger.error('Ошибка преобразования типа данных')
        else:
            logger.error(
                f'{ENDPOINT} не доступен. Код ответа API: {status}'
            )
            raise AssertionError
    except RequestException:
        logger.exception(f'Ошибка запроса {ENDPOINT}.')


def check_response(response):
    """Проверяет API на корректность."""
    if not isinstance(response, dict):
        logger.error('Ответ не является словарем')
        raise TypeError
    if not response:
        logger.error('Словарь пуст')
        raise KeyError
    if 'homeworks' not in response:
        logger.error('Ключа homeworks не существует')
    if not isinstance(response.get('homeworks'), list):
        logger.error('В homeworks лежит не список')
        raise KeyError
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'Статус неизвестен: {homework_status}')
        raise KeyError
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность элементов окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens:
        logger.critical('Отсутствуют переменные окружения')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.info('Статус ответа не изменен')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
