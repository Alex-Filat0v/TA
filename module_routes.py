from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orders_module.orders_module import OrdersModule


module_router = APIRouter()


class SellOrderRequest(BaseModel):
    """
    Валидатор входящих данных при запросе на продажу предмета.
    """
    steamLoginSecure: str
    sessionid: str
    item_name: str
    price: float
    quantity: int


@module_router.post("/analyzes/buy_orders")
async def analyze_buy_orders(cookies: dict) -> dict:
    """
    Эндпоинт, который возвращает список ордеров пользователя на покупку.

    :param cookies: Куки, такие как steamLoginSecure и sessionid.

    :return: Возвращает словарь всех ордеров пользователя, либо ошибку
    """
    async with OrdersModule(cookies) as orders_module:
        result = await orders_module.analyze_buy_orders()

        if not result or "error" in result:
            raise HTTPException(status_code=400, detail=f"Ошибка при запросе: {result['error']}")
        return result


@module_router.post("/placement/sell_orders")
async def analyze_sell_orders(data: SellOrderRequest) -> dict:
    """
    Эндпоинт, который выставляет предметы на продажу.

    :param data: Тело запроса пользователя, которое включает в себя куки, имя предмета, цену и количество для ордера.

    :return: Возвращает словарь с успешно выставленными предметами, либо ощибку
    """
    cookies = {
        "steamLoginSecure": data.steamLoginSecure,
        "sessionid": data.sessionid,
    }

    async with OrdersModule(cookies) as orders_module:
        result = await orders_module.create_sell_order(item_name=data.item_name,
                                                       price=data.price, quantity=data.quantity)

        if not result or "error" in result:
            raise HTTPException(status_code=400, detail=f"Ошибка при выставлении ордера: {result['error']}")
        return result
