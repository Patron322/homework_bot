import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='UTF-8',
    stream=sys.stdout,
    filemode='a')

PRACTICUM_TOKEN = os.environ.get('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TIME_START = int(time.time())
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
          'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
          'TELEGRAM_TOKEN': TELEGRAM_TOKEN}


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('send message')
    except Exception as e:
        logging.error(f'Error: {e} send_message() error')


def start_message(bot, message):
    '''Стартовое сообщение'''
    message = 'Бот запущен'
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Отправляет запрос к API, возвращает ответ в виде словаря."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as e:
        logging.error = (f'Не удалось получить ответ API error: {e}.')
    except ValueError as e:
        logging.error = (f'Не удалось получить ответ API error: {e}.')
    response_json = response.json()
    if response.status_code != HTTPStatus.OK:
        resp_s_c = response.status_code
        if ['error'] in response_json:
            resp_err = response_json['error']
            logging.error(f'response error:{resp_err}, status code:{resp_s_c}')
        if ['code'] in response_json:
            resp_err = response_json['code']
            logging.error(f'response error:{resp_err}, status code:{resp_s_c}')
        else:
            logging.error(f'Endpoint != 200. error: {resp_s_c}.')
        raise
    logging.debug('Endpoint = 200.')
    return response_json


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) != dict:
        raise logging.error('TypeError - response API - not dict')
    if [0][0] in response:
        logging.error('IndexError - API response not include homework')
    if type(response['homeworks']) != list:
        raise TypeError(' - homework not list')
    return response.get('homeworks')


def parse_status(homework):
    """Составляет сообщение с именем работы и статусом ревью."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if type(homework_name) is None:
        TypeError('homework_name is None.')
    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.error(f'Unknown homework_status: {homework_status}.')
    verdict = HOMEWORK_STATUSES[homework_status]
    logging.info(f'verdict: {verdict}.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет токены."""
    if PRACTICUM_TOKEN and TELEGRAM_CHAT_ID and TELEGRAM_TOKEN is not None:
        logging.info('Tokens status: OK')
        return True
    else:
        for name, token in tokens.items():
            if token is None:
                logging.error(f'Token error: {name}')
            return False
    return None


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = TIME_START
        message = 'Бот запущен'
        start_message(bot, message)
    else:
        raise logging.error('error check_tokens in main')
    while True:
        try:
            response = get_api_answer(current_timestamp)  # dict
            mayby_hw = check_response(response)  # list
            if len(mayby_hw) > 0:
                for hw in mayby_hw:
                    result = parse_status(hw)
                    send_message(bot, result)
            if 'current_date' in response:
                resp_c_d = response['current_date']
                if not isinstance(resp_c_d, int):
                    raise logging.error('Bad current_date')
                current_timestamp = resp_c_d
            logging.debug('try OK')
            time.sleep(RETRY_TIME)
        except Exception as e:
            message = f'Ошибка в работе бота: {e}!'
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            time.sleep(RETRY_TIME)
        else:
            logging.debug('logging.debug')


if __name__ == '__main__':
    main()
