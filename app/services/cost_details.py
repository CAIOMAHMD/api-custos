import time
import requests
import pandas as pd
from app.core.auth import get_token

def gerar_relatorio_cost_details(subscription_id, start, end):
    url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        "/providers/Microsoft.CostManagement/generateCostDetailsReport"
        "?api-version=2025-03-01"
    )

    payload = {
        "metric": "ActualCost",
        "timePeriod": {"start": start, "end": end}
    }

    headers = {"Authorization": f"Bearer {get_token()}"}

    # inicia operação
    r = requests.post(url, json=payload, headers=headers)
    operation_url = r.headers["Location"]

    # polling até terminar
    while True:
        status = requests.get(operation_url, headers=headers).json()
        if "blobLink" in status:
            break
        time.sleep(2)

    # baixa CSV
    df = pd.read_csv(status["blobLink"])
    df["SubscriptionId"] = subscription_id
    return df
