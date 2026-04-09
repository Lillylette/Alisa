from flask import Flask, request, jsonify
import logging
import json
import random
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок
cities = {
    'москва': ['1540737/daa6e420d33102bf6947',
               '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f',
                 '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8",
              '3450494/aca7ed7acefde22341bdc']
}

# создаем словарь для хранения данных пользователей
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    
    # Проверяем наличие необходимых полей в запросе
    if not request.json or 'session' not in request.json or 'version' not in request.json:
        return jsonify({
            'response': {
                'text': 'Произошла ошибка. Попробуйте позже.',
                'end_session': True
            }
        })
    
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь для хранения имени пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # проверяем, существует ли пользователь в sessionStorage
    if user_id not in sessionStorage:
        sessionStorage[user_id] = {
            'first_name': None
        }

    # если поле имени пустое, то пользователь еще не представился
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем сообщении ищем имя
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя и спрашиваем про город
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я - Алиса. Какой город хочешь увидеть?'
            # добавляем кнопки с городами
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in cities.keys()
            ]
    # если знакомы с пользователем и он что-то написал
    else:
        # ищем город в сообщении пользователя
        city = get_city(req)
        
        # также проверяем текст сообщения на наличие названий городов
        if not city and 'request' in req and 'command' in req['request']:
            command_lower = req['request']['command'].lower()
            for known_city in cities.keys():
                if known_city in command_lower:
                    city = known_city
                    break
        
        # если город известен, показываем его
        if city and city in cities:
            res['response']['card'] = {
                'type': 'BigImage',
                'title': f'Это город {city.title()}!',
                'image_id': random.choice(cities[city])
            }
            res['response']['text'] = f'Вот город {city.title()}. Тебе нравится?'
            # добавляем кнопки для продолжения диалога
            res['response']['buttons'] = [
                {
                    'title': 'Другой город',
                    'hide': False
                },
                {
                    'title': 'Выйти',
                    'hide': False
                }
            ]
        # если город не найден
        else:
            # проверяем, хочет ли пользователь выйти
            if 'выйти' in req['request']['command'].lower() or 'пока' in req['request']['command'].lower():
                res['response']['text'] = f'До свидания, {sessionStorage[user_id]["first_name"].title()}! Было приятно пообщаться.'
                res['response']['end_session'] = True
            # проверяем, хочет ли пользователь другой город
            elif 'другой город' in req['request']['command'].lower():
                res['response']['text'] = 'Какой город хочешь увидеть?'
                res['response']['buttons'] = [
                    {
                        'title': city.title(),
                        'hide': True
                    } for city in cities.keys()
                ]
            else:
                res['response']['text'] = 'Первый раз слышу об этом городе. Попробуй еще разок! Назови один из городов: Москва, Нью-Йорк или Париж.'
                res['response']['buttons'] = [
                    {
                        'title': city.title(),
                        'hide': True
                    } for city in cities.keys()
                ]


def get_city(req):
    # проверяем наличие nlu и entities в запросе
    if 'request' not in req or 'nlu' not in req['request'] or 'entities' not in req['request']['nlu']:
        return None
    
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)
    return None


def get_first_name(req):
    # проверяем наличие nlu и entities в запросе
    if 'request' not in req or 'nlu' not in req['request'] or 'entities' not in req['request']['nlu']:
        return None
    
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # возвращаем имя, если оно есть
            return entity['value'].get('first_name', None)
    return None


if __name__ == '__main__':
    # Для Replit используем порт 8080
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
