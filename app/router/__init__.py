from fastapi import APIRouter

from app.router import admin, auth, chat, customer, driver

router = APIRouter()

for feature_router in (
    auth.router,
    customer.router,
    driver.router,
    chat.router,
    admin.router,
):
    router.include_router(feature_router)
