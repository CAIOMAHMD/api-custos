#!/bin/bash

echo "🔍 Finalizando processos antigos..."
pkill -f "uvicorn" 2>/dev/null
pkill -f "streamlit" 2>/dev/null

echo "🚀 Iniciando API FastAPI (Uvicorn)..."

nohup uvicorn app.main:app --reload --port 8000 > logs_api.txt 2>&1 &

sleep 2

echo "📊 Iniciando Dashboard Streamlit..."

nohup streamlit run dashboard/streamlit_app.py --server.port 8501 > logs_streamlit.txt 2>&1 &

echo ""
echo "✨ Tudo rodando!"
echo "API:       http://localhost:8000"
echo "Dashboard: http://localhost:8501"
echo ""
echo "📄 Logs:"
echo " - logs_api.txt"
echo " - logs_streamlit.txt"
