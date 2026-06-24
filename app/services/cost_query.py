import requests
from app.core.auth import get_token

def get_cost_query(subscription_id):
    url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        "/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
    )

    payload = {
        "type": "ActualCost",

        "dataSet": {
            "granularity": "Daily",

            "aggregation": {
                "totalCost": {"name": "Cost", "function": "Sum"}
            },

            # SOMENTE ResourceId é permitido aqui
            "grouping": [
                {"type": "Dimension", "name": "ResourceId"}
            ],

            # Traz TODAS as tags existentes
            "include": ["Tags"]
        },

        # Máximo permitido pelo Azure
        "timeframe": "TheLast12Months"
    }

    headers = {"Authorization": f"Bearer {get_token()}"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
    except Exception as e:
        return {"error": f"Erro ao chamar Azure: {e}"}

    if "error" in data:
        return {"error": data["error"]}

    if "properties" not in data:
        return {"error": "Azure retornou formato inválido", "raw": data}

    return data
