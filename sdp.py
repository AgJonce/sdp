import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests
import csv
import re
import os
from io import BytesIO
from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Conexão com banco
conn = sqlite3.connect("sdp.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabela corrigida
cursor.execute("""
CREATE TABLE IF NOT EXISTS estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_registro TEXT NOT NULL,
    latitude TEXT,
    longitude TEXT,
    rua TEXT,
    endereco TEXT,
    problema TEXT,
    tipo_problema TEXT,
    descricao TEXT,
    status TEXT
)
""")

conn.commit()

# Função do mapa
def exibir_mapa():
    localizacao = [-20.7029, -42.0105]

    mapa = folium.Map(location=localizacao, zoom_start=15)
    mapa_interativo = st_folium(mapa, width=725, height=500)

    return mapa_interativo

# Função para obter endereço
def obter_nome_rua_com_numero(lat, lon):
    geolocator = Nominatim(user_agent="meu_app")

    try:
        location = geolocator.reverse((lat, lon), language='pt', timeout=10)

        if location:
            endereco = location.raw.get('address', {})
            numero = endereco.get('house_number', 'S/N')
            rua = endereco.get('road', 'Rua não encontrada')
            endereco_completo = location.address

            return rua, numero, endereco_completo

    except Exception as e:
        return "Erro", "Erro", str(e)

    return "Não encontrado", "Não encontrado", "Não encontrado"

def registrar_problema(localizacao, tipo_problema, descricao, rua, numero, endereco):
    data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inserir no banco
    cursor.execute("""
    INSERT INTO estoque (
        data_registro, latitude, longitude, rua, endereco,
        problema, tipo_problema, descricao, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_registro,
        str(localizacao[0]),
        str(localizacao[1]),
        rua,
        f"{rua}, {numero}",
        tipo_problema,
        tipo_problema,
        descricao,
        "Não atendido"
    ))

    conn.commit()

    # Feedback no Streamlit
    st.success("✅ Problema registrado com sucesso!")

    st.write(f"📍 Rua: {rua}, Número: {numero}")
    st.write(f"⚠️ Tipo de Problema: {tipo_problema}")
    st.write(f"📝 Descrição: {descricao}")
    st.write(f"📅 Data de Registro: {data_registro}")
    st.write(f"📊 Status: Não atendido")
