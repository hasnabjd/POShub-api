from fastapi import APIRouter, Depends, HTTPException

from poshub_api.auth import User, require_orders_read, require_orders_write
from poshub_api.logging_config import get_logger

from .schemas import OrderIn, OrderOut
from .service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
logger = get_logger(__name__)
order_service = OrderService()


@router.post("/", response_model=OrderOut)
async def create_order(
    order: OrderIn, current_user: User = Depends(require_orders_write)
):
    """
    Crée une commande en mémoire.
    Requiert le scope: orders:write
    """
    logger.info(
        "Creating new order", order_id=order.id, username=current_user.username
    )
    try:
        result = await order_service.create_order(order)
        logger.info(
            "Order created successfully",
            order_id=order.id,
            username=current_user.username,
        )
        return result
    except Exception as e:
        logger.error(
            "Failed to create order",
            order_id=order.id,
            username=current_user.username,
            error=str(e),
        )
        raise


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str, current_user: User = Depends(require_orders_read)
):
    """
    Récupère une commande par son ID ou retourne 404.
    Requiert le scope: orders:read
    """
    logger.info(
        "Fetching order", order_id=order_id, username=current_user.username
    )
    try:
        order = await order_service.get_order(order_id)
        if not order:
            logger.warning(
                "Order not found",
                order_id=order_id,
                username=current_user.username,
            )
            raise HTTPException(status_code=404, detail="Order not found")
        logger.info(
            "Order retrieved successfully",
            order_id=order_id,
            username=current_user.username,
        )
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve order",
            order_id=order_id,
            username=current_user.username,
            error=str(e),
        )
        raise
