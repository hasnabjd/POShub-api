from fastapi import APIRouter, HTTPException
from .service import OrderService
from .schemas import OrderIn, OrderOut

router = APIRouter()
order_service = OrderService()

@router.post("/orders", response_model=OrderOut)
async def create_order(order: OrderIn):
    """
    Crée une commande en mémoire.
    """
    return await order_service.create_order(order)

@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: str):
    """
    Récupère une commande par son ID ou retourne 404.
    """
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order 