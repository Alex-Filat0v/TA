1. Установка зависимостей:
```zsh
pip install -r requirements.txt
```
2. Запуск сервера:
```zsh
python app.py
```
3. Тестирование приложения:

3.1 Эндпоинт для получения всех ордеров на покупку:
```zsh
http://127.0.0.1:8000/analyzes/buy_orders
```
Ожидает получить куки в raw, в виде:
```zsh
{
    "steamLoginSecure": "YOUR_steamLoginSecure",
    "sessionid": "YOUR_sessionid"
}
```

3.2 Эндпоинт для выставления предмета на продажу
```zsh
http://127.0.0.1:8000/placement/sell_orders
```
Ожидает получить куки в raw, а также имя предмета на продажу, цену и количество ордеров на этот предмет, в виде:
```zsh
{
    "steamLoginSecure": "YOUR_steamLoginSecure",
    "sessionid": "YOUR_sessionid"
    "item_name": "Sticker | ALEX | Berlin 2019",
    "price": "12",
    "quantity": "3"
}
```
