import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000/custos"

st.set_page_config(page_title="Azure Cost Dashboard", layout="wide")

st.title("💰 Azure Cost Dashboard")
st.caption("Custos reais por subscription, recurso, grupo de recursos e TAGs dinâmicas (Tag Name + Tag Value).")

# ---------------------------------------------------------
# FUNÇÃO PARA CARREGAR DADOS DA API
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    resp = requests.get(API_URL)
    resp.raise_for_status()
    data = resp.json()

    rows = []

    for sub in data:
        sub_id = sub.get("subscriptionId")
        sub_data = sub.get("data")

        if sub_data is None or "properties" not in sub_data:
            continue

        props = sub_data["properties"]
        columns = [c["name"] for c in props["columns"]]

        for row in props["rows"]:
            row_dict = dict(zip(columns, row))
            row_dict["SubscriptionId"] = sub_id
            rows.append(row_dict)

    if not rows:
        return pd.DataFrame(), [], []

    df = pd.DataFrame(rows)

    # Converter UsageDate (YYYYMMDD → datetime)
    if "UsageDate" in df.columns:
        df["UsageDate"] = pd.to_datetime(
            df["UsageDate"].astype(str),
            format="%Y%m%d",
            errors="coerce"
        )

    # Converter Cost
    if "Cost" in df.columns:
        df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")

    # Parse de ResourceId
    def parse_resource_id(resource_id):
        if not isinstance(resource_id, str):
            return pd.Series([None, None, None, None])
        parts = resource_id.split("/")
        rg = parts[4] if len(parts) > 4 else None
        provider = parts[6] if len(parts) > 6 else None
        rtype = parts[7] if len(parts) > 7 else None
        rname = parts[8] if len(parts) > 8 else None
        return pd.Series([rg, provider, rtype, rname])

    df[["ResourceGroup", "Provider", "ResourceType", "ResourceName"]] = df["ResourceId"].apply(parse_resource_id)

    # ---------------------------------------------------------
    # TAGs DINÂMICAS — extrair Tag Name + Tag Value
    # ---------------------------------------------------------
    def extract_tag_pairs(tag_list):
        pairs = []
        if isinstance(tag_list, list):
            for item in tag_list:
                clean = item.replace('"', '')
                if ":" in clean:
                    key, value = clean.split(":", 1)
                    pairs.append((key.strip(), value.strip()))
        return pairs

    df["TagPairs"] = df["Tags"].apply(extract_tag_pairs)

    # Listas globais de Tag Names e Tag Values
    all_pairs = df["TagPairs"]

    tag_names = sorted({k for row in all_pairs for (k, v) in row})
    tag_values = sorted({v for row in all_pairs for (k, v) in row})

    return df, tag_names, tag_values


# ---------------------------------------------------------
# CARREGAR DADOS
# ---------------------------------------------------------
df, tag_names, tag_values = load_data()

if df.empty:
    st.warning("Nenhum dado retornado pela API.")
    st.stop()

# ---------------------------------------------------------
# FILTRO DE PERÍODO
# ---------------------------------------------------------
st.sidebar.header("Período")

periodo = st.sidebar.radio(
    "Selecionar período",
    ["Últimos 7 dias", "Mensal (Mês atual)"],
    index=1
)

df_filtered = df.copy()

if "UsageDate" in df_filtered and df_filtered["UsageDate"].notna().any():
    hoje = df_filtered["UsageDate"].max()

    if periodo == "Últimos 7 dias":
        df_filtered = df_filtered[df_filtered["UsageDate"] >= hoje - pd.Timedelta(days=7)]

    elif periodo == "Mensal (Mês atual)":
        df_filtered = df_filtered[
            (df_filtered["UsageDate"].dt.month == hoje.month) &
            (df_filtered["UsageDate"].dt.year == hoje.year)
        ]

# ---------------------------------------------------------
# FILTROS LATERAIS (GERAIS)
# ---------------------------------------------------------
st.sidebar.header("Filtros")

subs = st.sidebar.multiselect(
    "Subscriptions",
    sorted(df["SubscriptionId"].dropna().unique()),
    default=sorted(df["SubscriptionId"].dropna().unique())
)

rgs = st.sidebar.multiselect(
    "Resource Groups",
    sorted(df["ResourceGroup"].dropna().unique())
)

types = st.sidebar.multiselect(
    "Tipos de Recurso",
    sorted(df["ResourceType"].dropna().unique())
)

if subs:
    df_filtered = df_filtered[df_filtered["SubscriptionId"].isin(subs)]
if rgs:
    df_filtered = df_filtered[df_filtered["ResourceGroup"].isin(rgs)]
if types:
    df_filtered = df_filtered[df_filtered["ResourceType"].isin(types)]

# ---------------------------------------------------------
# FILTRO DE TAG REMOVIDO DA INTERFACE
# Mantém df_tag_filtered igual ao df_filtered
# ---------------------------------------------------------
df_tag_filtered = df_filtered.copy()

# ---------------------------------------------------------
# RESUMO GERAL (NÃO AFETADO POR TAG)
# ---------------------------------------------------------
st.subheader("📊 Resumo geral")

col1, col2, col3 = st.columns(3)

with col1:
    total_cost = df_filtered["Cost"].sum()
    currency = df_filtered["Currency"].mode().iloc[0] if "Currency" in df_filtered else ""
    st.metric("Total de custo (geral)", f"{total_cost:.2f} {currency}")

with col2:
    st.metric("Qtd. de recursos distintos", df_filtered["ResourceId"].nunique())

with col3:
    st.metric("Qtd. de Resource Groups", df_filtered["ResourceGroup"].nunique())

# ---------------------------------------------------------
# GRÁFICOS GERAIS (ANTIGOS RESTAURADOS)
# ---------------------------------------------------------
st.markdown("---")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📈 Top 10 Tipos de Recurso por Custo")
    chart_type = (
        df_filtered.groupby("ResourceType")["Cost"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(chart_type)

with col_g2:
    st.subheader("📊 Top 10 Resource Groups por Custo")
    chart_rg = (
        df_filtered.groupby("ResourceGroup")["Cost"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(chart_rg)

# ---------------------------------------------------------
# GRÁFICO DIÁRIO GERAL
# ---------------------------------------------------------
st.subheader("📅 Custo diário consolidado (geral)")
chart_daily = df_filtered.groupby("UsageDate")["Cost"].sum().sort_index()
st.line_chart(chart_daily)

# ---------------------------------------------------------
# RESULTADOS FILTRADOS POR TAG
# ---------------------------------------------------------
st.subheader("🔎 Resultados filtrados por TAG")

st.dataframe(
    df_tag_filtered[[
        "SubscriptionId",
        "ResourceGroup",
        "ResourceType",
        "ResourceName",
        "UsageDate",
        "Cost",
        "Tags"
    ]].sort_values("Cost", ascending=False),
    width="stretch"
)

# ---------------------------------------------------------
# AGRUPAMENTO POR TAG NAME + TAG VALUE
# ---------------------------------------------------------
st.subheader("📦 Custo agrupado por Tag Name + Tag Value")

tag_rows = []

for pairs, cost in zip(df_tag_filtered["TagPairs"], df_tag_filtered["Cost"]):
    for (k, v) in pairs:
        tag_rows.append({"TagName": k, "TagValue": v, "Cost": cost})

df_tags = pd.DataFrame(tag_rows)

if not df_tags.empty:
    st.dataframe(
        df_tags.groupby(["TagName", "TagValue"])["Cost"]
        .sum()
        .reset_index()
        .sort_values("Cost", ascending=False),
        width="stretch"
    )
else:
    st.info("Nenhuma TAG encontrada para o filtro atual.")
