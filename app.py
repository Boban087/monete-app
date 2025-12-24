import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CoinValue", layout="wide")

if 'sessione_acquisto' not in st.session_state:
    st.session_state.sessione_acquisto = []

def load_data():
    return pd.read_csv('database_monete.csv')

try:
    df_monete = load_data()
except:
    st.error("File database_monete.csv non trovato!")
    st.stop()

st.sidebar.header("Prezzi Metalli")
prezzo_ag_g = st.sidebar.number_input("Argento (€/g)", min_value=0.0, value=0.85, step=0.01, format="%.2f")
prezzo_au_g = st.sidebar.number_input("Oro (€/g)", min_value=0.0, value=70.0, step=0.01, format="%.2f")

oz_troy = 31.1035
st.sidebar.write(f"Ag: **{(prezzo_ag_g * oz_troy):.2f} €/oz**")
st.sidebar.write(f"Au: **{(prezzo_au_g * oz_troy):.2f} €/oz**")

if 'last_upd' not in st.session_state:
    st.session_state.last_upd = datetime.now().strftime("%d/%m/%Y %H:%M")

if st.sidebar.button("Aggiorna Orario"):
    st.session_state.last_upd = datetime.now().strftime("%d/%m/%Y %H:%M")

st.sidebar.caption(f"Aggiornata al {st.session_state.last_upd}")

tab1, tab2 = st.tabs(["📊 Listino", "🛒 Acquisto"])

with tab1:
    df_l = df_monete.copy()
    df_l['Valore fusione'] = ((df_l['Peso_g'] * (df_l['Titolo_Ag']/1000) * prezzo_ag_g) + (df_l['Peso_g'] * (df_l['Titolo_Au']/1000) * prezzo_au_g)).round(2)
    st.dataframe(df_l, use_container_width=True, hide_index=True)

with tab2:
    with st.form("form_acquisto"):
        c1, c2, c3 = st.columns([3, 1, 1])
        
        opzioni_monete = df_monete.apply(lambda x: f"{x['Descrizione']} ({x['Anni']})", axis=1).tolist()
        scelta_label = c1.selectbox("Moneta", opzioni_monete)
        idx_moneta = opzioni_monete.index(scelta_label)
        
        qta = c2.number_input("Quantità", min_value=1, value=1)
        prezzo_pagato = c3.number_input("Prezzo acquisto (€)", min_value=0.0, step=1.0)
        
        if st.form_submit_button("Aggiungi"):
            m = df_monete.iloc[idx_moneta]
            v_fus = ((m['Peso_g'] * (m['Titolo_Ag']/1000) * prezzo_ag_g) + (m['Peso_g'] * (m['Titolo_Au']/1000) * prezzo_au_g)) * qta
            
            spread_perc = ((prezzo_pagato - v_fus) / v_fus * 100) if v_fus > 0 else 0
            
            st.session_state.sessione_acquisto.append({
                'Moneta': scelta_label,
                'Quantità': qta,
                'Valore fusione (€)': round(v_fus, 2),
                'Prezzo acquisto (€)': round(prezzo_pagato, 2),
                'Spread (%)': f"{spread_perc:.2f}%"
            })
            st.rerun()

    if st.session_state.sessione_acquisto:
        df_a = pd.DataFrame(st.session_state.sessione_acquisto)
        
        tot_q = df_a['Quantità'].sum()
        tot_f = df_a['Valore fusione (€)'].sum()
        tot_p = df_a['Prezzo acquisto (€)'].sum()
        
        tot_spread_perc = ((tot_p - tot_f) / tot_f * 100) if tot_f > 0 else 0
        
        riga_totale = pd.DataFrame([{
            'Moneta': 'TOTALE',
            'Quantità': tot_q,
            'Valore fusione (€)': round(tot_f, 2),
            'Prezzo acquisto (€)': round(tot_p, 2),
            'Spread (%)': f"{tot_spread_perc:.2f}%"
        }])
        
        df_finale = pd.concat([df_a, riga_totale], ignore_index=True)
        st.dataframe(df_finale, use_container_width=True, hide_index=True)
        
        if st.button("Resetta Tabella Acquisto"):
            st.session_state.sessione_acquisto = []
            st.rerun()
