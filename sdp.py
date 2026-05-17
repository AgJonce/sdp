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
CREATE TABLE IF NOT EXISTS sdp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_registro TEXT NOT NULL,
    latitude TEXT,
    longitude TEXT,
    rua TEXT,
    endereco TEXT,
    problema TEXT,
    tipo_problema TEXT,
    descricao TEXT,
    status TEXT,
    imagem TEXT
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

def registrar_problema(localizacao, tipo_problema, descricao, rua, numero, endereco,imagem):
    data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inserir no banco
    cursor.execute("""
    INSERT INTO sdp (
        data_registro, latitude, longitude, rua, endereco,
        problema, tipo_problema, descricao, status,imagem
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_registro,
        str(localizacao[0]),
        str(localizacao[1]),
        rua,
        f"{rua}, {numero}",
        tipo_problema,
        tipo_problema,
        descricao,
        "Não atendido",
        str(imagem.name) if imagem else None
    ))

    conn.commit()

    # Feedback no Streamlit
    st.success("✅ Problema registrado com sucesso!")

    st.write(f"📍 Rua: {rua}, Número: {numero}")
    st.write(f"⚠️ Tipo de Problema: {tipo_problema}")
    st.write(f"📝 Descrição: {descricao}")
    st.write(f"📅 Data de Registro: {data_registro}")
    st.write(f"📊 Status: Não atendido")
    st.write(f"📊 Imagem: {imagem}")

def sistema_de_problemas():
    st.title("📍 Sistema de Problemas Urbanos")

    menu = ["Registrar Problema", "Consultar Problemas"]
    opcao = st.sidebar.selectbox("Escolha uma opção", menu)

    if opcao == "Registrar Problema":
        st.subheader("Registrar novo problema")

        mapa = exibir_mapa()

        if mapa and mapa.get("last_clicked"):
            lat = mapa["last_clicked"]["lat"]
            lon = mapa["last_clicked"]["lng"]

            st.write(f"📌 Local selecionado: {lat}, {lon}")

            rua, numero, endereco = obter_nome_rua_com_numero(lat, lon)

            # 🔥 FORM COMEÇA AQUI
            with st.form("form_problema"):

                tipo_problema = st.selectbox(
                    "Tipo de problema",
                    [" ","Buraco na rua", "Iluminação", "Lixo", "Esgoto", "Outro"]
                )

                descricao = st.text_area("Descrição")

                imagem = st.file_uploader("Imagem")

                submitted = st.form_submit_button("Registrar Problema")

                if submitted:
                    registrar_problema(
                        [lat, lon],
                        tipo_problema,
                        descricao,
                        rua,
                        numero,
                        endereco,
                        imagem
                    )

    elif opcao == "Consultar Problemas":
        st.subheader("Problemas registrados")

        df = pd.read_sql("SELECT * FROM sdp", conn)

        if df.empty:
            st.warning("Nenhum problema registrado ainda.")
        else:
            st.dataframe(df)

            # Mapa com pontos
            mapa = folium.Map(location=[-20.7029, -42.0105], zoom_start=13)

            for _, row in df.iterrows():
                folium.Marker(
                    location=[float(row["latitude"]), float(row["longitude"])],
                    popup=f"{row['tipo_problema']} - {row['status']}"
                ).add_to(mapa)

            st_folium(mapa, width=700, height=500)
def main():
    sistema_de_problemas()

if __name__ == "__main__":
    main()
