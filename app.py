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
prezzo_ag_g = st.sidebar.number_input("Argento (€/g)", min_value=0.0, value=2.0346, step=0.0001, format="%.4f")
prezzo_au_g = st.sidebar.number_input("Oro (€/g)", min_value=0.0, value=123.00, step=0.01, format="%.2f")

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
    # Preparo una chiave univoca per ritrovare i dati della moneta durante il ricalcolo
    df_monete['Chiave'] = df_monete.apply(lambda x: f"{x['Descrizione']} ({x['Anni']})", axis=1)
    
    with st.form("form_acquisto"):
        c1, c2, c3 = st.columns([3, 1, 1])
        
        scelta_label = c1.selectbox("Moneta", df_monete['Chiave'].tolist())
        qta = c2.number_input("Quantità", min_value=1, value=1)
        prezzo_pagato = c3.number_input("Prezzo acquisto (€)", min_value=0.0, step=1.0)
        
        if st.form_submit_button("Aggiungi"):
            m = df_monete[df_monete['Chiave'] == scelta_label].iloc[0]
            v_fus_totale = ((m['Peso_g'] * (m['Titolo_Ag']/1000) * prezzo_ag_g) + (m['Peso_g'] * (m['Titolo_Au']/1000) * prezzo_au_g)) * qta
            
            spread_perc = ((prezzo_pagato - v_fus_totale) / v_fus_totale * 100) if v_fus_totale > 0 else 0
            
            st.session_state.sessione_acquisto.append({
                'Moneta': scelta_label,
                'Quantità': qta,
                'Valore fusione (€)': round(v_fus_totale, 2),
                'Prezzo acquisto (€)': round(prezzo_pagato, 2),
                'Spread (%)': f"{spread_perc:.2f}%"
            })
            st.rerun()

    if st.session_state.sessione_acquisto:
        df_a = pd.DataFrame(st.session_state.sessione_acquisto)
        
        # TABELLA MODIFICABILE
        edited_df = st.data_editor(
            df_a,
            num_rows="dynamic", # Permette di eliminare righe
            use_container_width=True,
            hide_index=True,
            column_config={
                "Moneta": st.column_config.TextColumn(disabled=True),
                "Quantità": st.column_config.NumberColumn(min_value=1, step=1, required=True),
                "Prezzo acquisto (€)": st.column_config.NumberColumn(min_value=0.0, step=1.0, required=True),
                "Valore fusione (€)": st.column_config.NumberColumn(disabled=True),
                "Spread (%)": st.column_config.TextColumn(disabled=True)
            },
            key="editor_acquisti"
        )

        # Ricalcolo automatico in base alle modifiche fatte nella tabella
        lista_ricalcolata = []
        df_lookup = df_monete.set_index('Chiave')
        
        for index, row in edited_df.iterrows():
            nome_moneta = row['Moneta']
            # Verifica che la moneta esista (evita crash se si aggiungono righe vuote per sbaglio)
            if nome_moneta in df_lookup.index:
                m = df_lookup.loc[nome_moneta]
                nuova_qta = row['Quantità']
                nuovo_prezzo = row['Prezzo acquisto (€)']
                
                # Ricalcolo fusione
                v_fus_unitario = (m['Peso_g'] * (m['Titolo_Ag']/1000) * prezzo_ag_g) + (m['Peso_g'] * (m['Titolo_Au']/1000) * prezzo_au_g)
                v_fus_tot = v_fus_unitario * nuova_qta
                
                # Ricalcolo spread
                spread = ((nuovo_prezzo - v_fus_tot) / v_fus_tot * 100) if v_fus_tot > 0 else 0
                
                lista_ricalcolata.append({
                    'Moneta': nome_moneta,
                    'Quantità': nuova_qta,
                    'Valore fusione (€)': round(v_fus_tot, 2),
                    'Prezzo acquisto (€)': round(nuovo_prezzo, 2),
                    'Spread (%)': f"{spread:.2f}%"
                })
        
        # Aggiorno lo stato con i dati ricalcolati
        st.session_state.sessione_acquisto = lista_ricalcolata
        
        # Calcolo Totali sui dati aggiornati
        if lista_ricalcolata:
            df_fin = pd.DataFrame(lista_ricalcolata)
            tot_q = df_fin['Quantità'].sum()
            tot_f = df_fin['Valore fusione (€)'].sum()
            tot_p = df_fin['Prezzo acquisto (€)'].sum()
            tot_s_perc = ((tot_p - tot_f) / tot_f * 100) if tot_f > 0 else 0
            
            riga_totale = pd.DataFrame([{
                'Moneta': 'TOTALE',
                'Quantità': tot_q,
                'Valore fusione (€)': round(tot_f, 2),
                'Prezzo acquisto (€)': round(tot_p, 2),
                'Spread (%)': f"{tot_s_perc:.2f}%"
            }])
            
            st.markdown("---")
            st.dataframe(riga_totale, use_container_width=True, hide_index=True)
        
        if st.button("Resetta tutto"):
            st.session_state.sessione_acquisto = []
            st.rerun()

