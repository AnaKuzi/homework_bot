## Homework Bot - Бот для проверки статуса ревью проектов в Яндекс.Практикум

Бот "общается" с API Яндекс.Практикум.

Можно запустить на ПК и на Heroku, достаточно запустить бота, прописать токены.
Каждые 10 минут бот проверяет API Яндекс.Практикум. И присылает в телеграм статус ревью.

У API Практикум.Домашка есть лишь один эндпоинт: 
```
https://practicum.yandex.ru/api/user_api/homework_statuses/
```
Получить токен по адресу: 
```
https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a.
```

### Принцип работы API
Когда ревьюер проверяет вашу домашнюю работу, он присваивает ей один из статусов:

 - "Работа проверена: ревьюеру всё понравилось. Ура!",
 - "Работа взята на проверку ревьюером.",
 - "Работа проверена: у ревьюера есть замечания."

### Запуск

* Клонируем проект:

```
git clone https://github.com/TsekovDavid/homework_bot.git
```

* Устанавливаем виртуальное окружение

```
python3 -m venv venv
```

* Активируем виртуальное окружение

windows
```
source venv/Scripts/activate
```
macos
```
. venv/bin/activate
```

* Устанавливаем зависимости

```
pip3 install -r requirements.txt
```

* Создайте файл .env и пропишите в нем токены:

```
PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
CHAT_TOKEN=<TELEGRAM_CHAT_ID>
```

* Запускаем бота

```
python homework.py
```

Бот будет работать, и каждые 10 минут проверять статус вашей домашней работы.
