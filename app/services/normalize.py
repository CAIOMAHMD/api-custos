import pandas as pd

def normalize_cost_details(df):
    df["UsageDate"] = pd.to_datetime(df["UsageDate"])
    df["Cost"] = df["Cost"].astype(float)
    return df[[
        "SubscriptionId",
        "ResourceId",
        "ResourceGroup",
        "UsageDate",
        "Cost",
        "Currency"
    ]]
