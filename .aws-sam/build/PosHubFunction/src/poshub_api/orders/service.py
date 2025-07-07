from .schemas import OrderIn, OrderOut


class OrderService:
    def __init__(self):
        self.orders = {}

    async def create_order(self, order: OrderIn) -> OrderOut:
        self.orders[order.orderId] = order
        return order

    async def get_order(self, order_id: str):
        return self.orders.get(order_id)
