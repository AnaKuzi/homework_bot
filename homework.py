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

from exceptions import (AnotherEndpointException, HTTPRequestError,
                        SendMessageException)

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

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler('anakuzibot.log', encoding='UTF-8')
    ],
)
logger = logging.getLogger(__name__)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Начинаем отправку сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        raise SendMessageException(f'Ошибка при отправке сообщения {error}')
    else:
        logger.info(f'Отправлено сообщение: {message}')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logger.info('Начинаем делать запрос к API')
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        status = response.status_code
        if status == HTTPStatus.OK:
            return response.json()
        else:
            raise HTTPRequestError(
                'Начинаем поиск ошибки'
                f'Проверяем значение status_code: {response.status_code}'
                f'Проверяем значение reason: {response.reason}'
                f'Проверяем значение сообщения: {response.text}'
                f'Проверяем ссылку endpoint-а: {ENDPOINT}'
                f'Проверяем значение headers: {HEADERS}'
                f'Проверяем значения params: {params}'
            )
    except json.decoder.JSONDecodeError as error:
        raise error(
            'Ошибка преобразования типа данных')
    except RequestException as error:
        raise error(f'Нет доступа к {ENDPOINT}')
    except Exception as error:
        raise AnotherEndpointException(
            f'Ошибка при запросе к {ENDPOINT}: {error}')


def check_response(response: dict) -> list:
    """Проверяет API на корректность."""
    logger.info('Начинаем проверку ответа сервера')
    if not isinstance(response, dict):
        raise TypeError('Ответ не является словарем')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response.keys():
        raise KeyError('Ключа homeworks не существует')
    if 'current_date' not in response.keys():
        raise KeyError('Ключа current_date не существует')
    if not isinstance(homeworks, list):
        raise KeyError('В homeworks лежит не список')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Статус неизвестен: {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность элементов окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют переменные окружения')
        sys.exit('Выполнение программы остановлено')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != old_message:
                    send_message(bot, message)
                    old_message = message
                    current_timestamp = response.get('current_date')
                else:
                    logger.debug('Новый статус отсутствует')
        # Ниже я убрала часть кастомных эксепшенов,
        # так как у меня появлялась ошибка Function is too complex,
        # я пока не знаю, как сократить функцию
        except SendMessageException as error:
            logger.error(
                f'Ошибка при отправке сообщения {error}')
        except HTTPRequestError as error:
            logger.error(
                f'Ошибка {error}'
                f'Эндпоинт {response.url} недоступен. '
                f'Код ответа API: {response.status_code}')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != old_message:
                send_message(bot, message)
                old_message = message
                logger.error(message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
