from fastapi import APIRouter
from app.core.config import SUBSCRIPTIONS
from app.services.cost_query import get_cost_query

router = APIRouter()

@router.get("/custos")
def custos_todas():
    return [
        {"subscriptionId": sub, "data": get_cost_query(sub)}
        for sub in SUBSCRIPTIONS
    ]

@router.get("/custos/{subscription_id}")
def custos_por_sub(subscription_id: str):
    return get_cost_query(subscription_id)
