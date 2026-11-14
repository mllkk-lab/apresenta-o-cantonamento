"""
Dashboard Streamlit – Modos de cantonamento da rede ferroviária francesa (SNCF)
Executar com:  streamlit run app.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

NOME_CSV = "cantonamento_ferroviario_pt_leve.csv"
RAIZ = Path(__file__).parent
# Procura o CSV na raiz do repositório e, se não achar, na pasta dados_sncf_sprint3/
CSV = next((c for c in (RAIZ / NOME_CSV, RAIZ / "dados_sncf_sprint3" / NOME_CSV) if c.exists()),
           RAIZ / NOME_CSV)

st.set_page_config(page_title="Cantonamento ferroviário – SNCF", layout="wide")

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "font.size": 10})


@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV, sep=";")
    # 2 trechos sem extensão são descartados nas análises em km
    d = df.dropna(subset=["extensao_km"]).copy()
    return df, d


df, d = carregar_dados()
km_total = d.extensao_km.sum()

# ------------------------------------------------------------------ Cabeçalho
st.title("Modos de cantonamento da rede ferroviária francesa")
st.caption("Análise exploratória dos dados da SNCF. A unidade de observação é o **trecho**, "
           "não a linha férrea: uma linha pode ter vários trechos com tecnologias diferentes.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trechos", f"{len(df):,}".replace(",", "."))
c2.metric("Linhas férreas", f"{df.codigo_linha.nunique():,}".replace(",", "."))
c3.metric("Extensão mapeada", f"{km_total:,.0f} km".replace(",", "."))
c4.metric("Modos de cantonamento", df.modo_cantonamento.nunique())

st.sidebar.header("Opções")
n_top = st.sidebar.slider("Quantidade de itens nos rankings", 5, 20, 10)
st.sidebar.markdown("Os valores em km ignoram os 2 trechos sem extensão informada.")

aba1, aba2, aba3 = st.tabs(["Famílias tecnológicas", "Modos de cantonamento", "Linhas"])

# ------------------------------------------------------------------ Gráfico 02
with aba1:
    fam = d.groupby("familia_tecnologica").agg(trechos=("id_trecho", "size"), km=("extensao_km", "sum"))
    fam["pct_trechos"] = fam.trechos / fam.trechos.sum() * 100
    fam["pct_km"] = fam.km / fam.km.sum() * 100
    fam = fam.sort_values("km", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(fam))
    ax.barh(y - .2, fam.pct_trechos, .4, label="% dos trechos", color="#8ecae6")
    ax.barh(y + .2, fam.pct_km, .4, label="% da quilometragem", color="#023047")
    ax.set_yticks(y, fam.index)
    ax.invert_yaxis()
    ax.set(xlabel="%", title="Famílias tecnológicas: contagem de trechos ≠ quilometragem")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("Contar trechos e somar quilômetros dão retratos diferentes. O bloco manual, por exemplo, "
                "tem poucos trechos, mas eles são longos, então pesa mais na quilometragem.")
    with st.expander("Ver tabela"):
        st.dataframe(fam.round(1).rename(columns={"trechos": "Trechos", "km": "km",
                                                  "pct_trechos": "% trechos", "pct_km": "% km"}))

# ------------------------------------------------------------------ Gráfico 03
with aba2:
    modo = d.groupby("modo_cantonamento").agg(trechos=("id_trecho", "size"), km=("extensao_km", "sum"))
    modo["pct_km"] = modo.km / km_total * 100
    modo = modo.sort_values("km", ascending=False)

    top = modo.head(n_top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 0.45 * n_top + 1.5))
    ax.barh(top.index.str.slice(0, 60), top.km, color="#219ebc")
    for i, (k, p) in enumerate(zip(top.km, top.pct_km)):
        ax.text(k, i, f" {k:,.0f} km ({p:.1f}%)", va="center", fontsize=8)
    ax.set(xlabel="km", title=f"Top {n_top} modos por quilometragem")
    ax.set_xlim(0, top.km.max() * 1.25)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander("Ver tabela completa (todos os modos)"):
        st.dataframe(modo.round(1).rename(columns={"trechos": "Trechos", "km": "km", "pct_km": "% km"}))

# ------------------------------------------------------------------ Gráfico 05
with aba3:
    lin = d.groupby(["codigo_linha", "nome_linha"]).agg(trechos=("id_trecho", "size"),
                                                        km=("extensao_km", "sum")).reset_index()
    lin = lin.sort_values("km", ascending=False)

    top_l = lin.head(n_top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 0.45 * n_top + 1.5))
    ax.barh(top_l.nome_linha.str.slice(0, 45), top_l.km, color="#fb8500")
    ax.set(xlabel="km", title=f"{n_top} maiores linhas por quilometragem mapeada")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander("Ver tabela"):
        st.dataframe(lin.head(n_top).round(1).rename(columns={"codigo_linha": "Código", "nome_linha": "Linha",
                                                              "trechos": "Trechos", "km": "km"}),
                     hide_index=True)
