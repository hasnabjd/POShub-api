from fastapi import FastAPI
import httpx
from poshub_api.orders.router import router as orders_router
from poshub_api.demo.router import router as demo_router

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.http = httpx.AsyncClient(timeout=10.0)

@app.on_event("shutdown")
async def shutdown():
    await app.state.http.aclose()

# Inclusion des routers
app.include_router(orders_router)
app.include_router(demo_router) 