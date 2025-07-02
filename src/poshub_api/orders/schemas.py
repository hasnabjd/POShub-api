from datetime import datetime
from pydantic import BaseModel, Field

class OrderIn(BaseModel):
    orderId: str = Field(..., title="Orderid")
    createdAt: datetime = Field(..., title="Createdat")
    totalAmount: float = Field(..., gt=0, title="Totalamount")
    currency: str = Field(..., title="Currency")

class OrderOut(BaseModel):
    orderId: str = Field(..., title="Order ID")
    createdAt: datetime = Field(..., title="Created At")
    totalAmount: float = Field(..., title="Total Amount")
    currency: str = Field(..., title="Currency") 