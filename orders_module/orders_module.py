import httpx
from httpx import Response
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup


class OrdersModule:
    """
    Класс для работы с ордерами.

    Метод analyze_buy_orders проводит анализ текущих ордеров на покупку.

    Метод create_sell_order выставляет ордер на продажу предмета по указанной цене и в указанном количестве.

    Магические методы __aenter__ и __aexit__ помогают реализовать асинхронное использование объекта класса внутри
    контекстного менеджера async with.
    """

    def __init__(self, cookies: Dict[str, str]):
        """
        Магический метод инициализации экземпляра класса, принимает в себя куки пользователя.

        Стандартные значения:

        BASE_URL - url на стим.

        HEADERS - заголовок, в котором установлен User-Agent.

        APPID - номер игры CS внутри стима
        """

        self.cookies = cookies
        self.client: Optional[httpx.AsyncClient] = None
        self.APPID = 730
        self.BASE_URL = "https://steamcommunity.com"
        self.HEADERS = {"User-Agent":
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                        " Chrome/136.0.0.0 Safari/537.36"}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=20)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.client.aclose()

    async def _create_get_request(self, url: str, headers: Dict[str, str] = None) -> Response:
        """
        Метод создания GET запроса по указанному url
        """
        if headers is None:
            headers = self.HEADERS
        return await self.client.get(url, headers=headers, cookies=self.cookies)

    @staticmethod
    async def _validate_response(response: Response) -> Response | None:
        """
        Метод валидации ответа на запрос
        """
        if response.status_code != 200:
            return None
        return response

    @staticmethod
    async def _json_conversion(response: Response) -> Any | None:
        """
        Метод конвертации ответа в json формат
        """
        try:
            data = response.json()
        except:
            return None
        return data

    async def analyze_buy_orders(self) -> dict:
        """
        Метод получения активных ордеров на покупку пользователя.

        :return: Возвращает словарь с ключом "buy_orders" и "total_amount", содержащий список ордеров и общую сумму ордеров, а в случае ошибки возвращает словарь с ключом "error".
        """
        buy_orders = []
        total_amount = 0

        # Задаем ссылку на получение списка ордеров
        orders_url = f"{self.BASE_URL}/market/mylistings/"

        # Делаем асинхронный запрос по этой ссылке и проводим его валидацию
        response = await self._create_get_request(orders_url)
        if await self._validate_response(response) is None:
            return {"error": f"Ошибка при запросе страницы steam: {response.status_code}"}

        # Конвертируем ответ от стима в json формат
        response_json = await self._json_conversion(response)
        if response_json is None:
            return {"error": "Ошибка при попытке конвертировать ответ от steam в json формат"}

        # Ищем ордера на полученной странице в поле results_html
        html = response_json.get("results_html", "")
        if not html:
            return {"error": "Ордера не найдены"}

        # Парсим наши ордера в виде html с помощью BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Из каждого ордера извлекаем нужные нам данные и добавляем их в список
        for row in soup.select('div[id^="mybuyorder_"]'):
            try:
                item_name = row.select_one(".market_listing_item_name").get_text(strip=True)
                price = row.select_one(".market_listing_price").get_text(strip=True)[3:]
                quantity = row.select_one(".market_listing_buyorder_qty").get_text(strip=True)

                # Считаем общую сумму ордеров
                price_without_currency = ''.join(dig if (dig.isdigit() or dig == ',')
                                                 else '' for dig in price)
                total_amount += float(price_without_currency.replace(',', '.')) * int(quantity)

                buy_orders.append({
                    "item_name": item_name,
                    "price": price,
                    "quantity": quantity,
                })
            except Exception as e:
                return {"error": f"При попытке парсинга данных произошла непредвиденная ошибка: {e}"}

        return {"buy_orders": buy_orders, "total_amount": total_amount}

    async def create_sell_order(self, item_name: str, price: float, quantity: int) -> dict:
        """
        Метод выставления ордера на продажу предмета по названию, цене и количеству.

        :param item_name: Название предмета.
        :param price: Цена за единицу.
        :param quantity: Количество предметов, которые нужно продать.

        :return: Возвращает словарь с ключом "result", содержищий сообщение об успещно выполненной операции, а в случае ошибки, словарь с ключом "error".
        """
        results = []

        # Получаем steam_id пользователя из куки и ссылку на его инвентарь
        steam_id = self.cookies.get('steamLoginSecure', '').split('%7C')[0]
        inventory_url = f"{self.BASE_URL}/inventory/{steam_id}/730/2?l=russian&count=1000"

        # Создаем новый заголовок для запросов, расширяя стандартный HEADERS
        headers = {
            **self.HEADERS,
            "Referer": f"{self.BASE_URL}/market/",
            "Origin": self.BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        }

        # Делаем асинхронный запрос по ссылке на инвентарь пользователя и проводим его валидацию
        response = await self._create_get_request(inventory_url, headers)
        if await self._validate_response(response) is None:
            return {"error": f"Ошибка при получении инвентаря: {response.status_code}"}

        # Конвертируем полученный результат в json
        response_json = await self._json_conversion(response)
        if response_json is None:
            return {"error": "Ошибка при конвертации инвентаря в json"}

        # Получаем список всех предметов из инвентаря и их описание
        items = response_json.get("assets", [])
        descriptions = {}
        for description in response_json.get("descriptions", []):
            descriptions[f"{description['classid']}_{description['instanceid']}"] = description

        # Находим assetid нужного(ых) предмета(ов) по названию
        items_for_sale = []
        for item in items:
            desc_id = f"{item['classid']}_{item['instanceid']}"
            desc = descriptions.get(desc_id, {})
            # Если название предмета в описании совпадает с указанным предметом, добавляем его в список на продажу
            if desc.get("market_hash_name") == item_name:
                items_for_sale.append(item)
                if len(items_for_sale) >= quantity:
                    break

        # Если предмета на продажу нет в инвентаре возвращаем ошибку
        if not items_for_sale:
            return {"error": f"Предмет '{item_name}' не найден в инвентаре"}

        # Выставляем каждый предмет на продажу
        for item in items_for_sale[:quantity]:
            payload = {
                "appid": self.APPID,
                "contextid": 2,
                "assetid": item["assetid"],
                "amount": 1,
                "price": int(price * 100),
                "sessionid": self.cookies.get('sessionid')
            }

            # Формируем ссылку на продажу и отправляем запрос на выставление предмета на тп
            sell_url = f"{self.BASE_URL}/market/sellitem/"
            response = await self.client.post(sell_url, data=payload, headers=headers, cookies=self.cookies)

            # Пытаемся конвертировать ответ от стима в json
            response_json = await self._json_conversion(response)
            if response_json is None:
                results.append({"warning": f"Ошибка при конвертации ответа в json"})
            results.append(response_json)

        return {"result": results}
