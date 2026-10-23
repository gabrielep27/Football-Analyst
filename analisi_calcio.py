import pandas as pd
import streamlit as st

# Impostazione pagina
st.set_page_config(
    page_title="Football Analytics by G.P.",
    page_icon="⚽",
    layout="wide"
)

# --- HEADER PRINCIPALE ---
st.markdown("""
    <div style='background: linear-gradient(135deg, #1e1e2f 0%, #0f1016 100%); padding: 22px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #2d2d44;'>
        <h1 style='color: #ffffff; text-align: center; font-family: sans-serif; margin: 0 0 8px 0;'>⚽ Football Analytics by G.P. ⚽</h1>
        <p style='text-align: center; color: #94a3b8; font-size: 15px; margin: 0;'>Piattaforma professionale di analisi dati e responsi statistici</p>
    </div>
""", unsafe_allow_html=True)

# Mappatura Campionati Nazionali
campionati_nazionali = {
    "Serie A (Italia)": "I1.csv",
    "Premier League (Inghilterra)": "E0.csv",
    "La Liga (Spagna)": "SP1.csv",
    "Bundesliga (Germania)": "D1.csv",
    "Ligue 1 (Francia)": "F1.csv"
}

# --- SIDEBAR: "CHI ANALIZZO?" ---
st.sidebar.header("🔍 CHI ANALIZZO?")

campionato_scelto = st.sidebar.selectbox("Seleziona Campionato:", list(campionati_nazionali.keys()))
file_csv = campionati_nazionali[campionato_scelto]

tipo_competizione = st.sidebar.selectbox("Seleziona Competizione:", ["Campionato Nazionale", "Coppe Europee (UEFA)"])

@st.cache_data
def carica_dati(url_csv):
    base_url = "https://www.football-data.co.uk/mmz4281/2627/"
    try:
        df = pd.read_csv(base_url + url_csv)
        if 'Date' in df.columns:
            df['Date_Parsed'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        return df
    except:
        return None

with st.spinner("Caricamento dati in corso..."):
    df = carica_dati(file_csv)

if df is not None and not df.empty and 'HomeTeam' in df.columns:
    squadre = sorted(list(set(df['HomeTeam'].dropna().unique())))
    squadra_selezionata = st.sidebar.selectbox("Seleziona Squadra:", squadre)

    # Calcolo Metriche
    def calcola_statistiche(df_partite, nome_squadra):
        gare_casa = df_partite[df_partite['HomeTeam'] == nome_squadra].copy()
        gare_trasferta = df_partite[df_partite['AwayTeam'] == nome_squadra].copy()
        
        totale_partite = len(gare_casa) + len(gare_trasferta)
        if totale_partite == 0:
            return None

        tiri_totali = gare_casa['HS'].sum() + gare_trasferta['AS'].sum()
        tiri_in_porta = gare_casa['HST'].sum() + gare_trasferta['AST'].sum()
        corner = gare_casa['HC'].sum() + gare_trasferta['AC'].sum()
        falli = gare_casa['HF'].sum() + gare_trasferta['AF'].sum()
        parate = gare_casa['AST'].sum() + gare_trasferta['HST'].sum()
        gialli = gare_casa['HY'].sum() + gare_trasferta['AY'].sum()
        rossi = gare_casa['HR'].sum() + gare_trasferta['AR'].sum()

        return {
            "Squadra": nome_squadra,
            "Partite Considerate": totale_partite,
            "Media Tiri Totali": round(tiri_totali / totale_partite, 1),
            "Media Tiri in Porta": round(tiri_in_porta / totale_partite, 1),
            "Media Corner a Favore": round(corner / totale_partite, 1),
            "Media Falli Commessi": round(falli / totale_partite, 1),
            "Media Parate Portiere": round(parate / totale_partite, 1),
            "Media Cartellini Gialli": round(gialli / totale_partite, 1),
            "Media Cartellini Rossi": round(rossi / totale_partite, 1)
        }

    # Calcolo Classifica Generale
    def calcola_classifica(df_partite):
        punti = {}
        for _, row in df_partite.dropna(subset=['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']).iterrows():
            c, a = row['HomeTeam'], row['AwayTeam']
            gf, gs = int(row['FTHG']), int(row['FTAG'])
            
            if c not in punti: punti[c] = {'P': 0, 'Pt': 0, 'GF': 0, 'GS': 0}
            if a not in punti: punti[a] = {'P': 0, 'Pt': 0, 'GF': 0, 'GS': 0}
            
            punti[c]['P'] += 1
            punti[a]['P'] += 1
            punti[c]['GF'] += gf
            punti[c]['GS'] += gs
            punti[a]['GF'] += gs
            punti[a]['GS'] += gf
            
            if gf > gs:
                punti[c]['Pt'] += 3
            elif gf == gs:
                punti[c]['Pt'] += 1
                punti[a]['Pt'] += 1
            else:
                punti[a]['Pt'] += 3
                
        df_cl = pd.DataFrame.from_dict(punti, orient='index')
        df_cl['DR'] = df_cl['GF'] - df_cl['GS']
        df_cl = df_cl.sort_values(by=['Pt', 'DR', 'GF'], ascending=False).reset_index()
        df_cl.columns = ['Squadra', 'PG', 'Pt', 'GF', 'GS', 'DR']
        df_cl.index = df_cl.index + 1
        return df_cl

    stats = calcola_statistiche(df, squadra_selezionata)

    if stats:
        nome_comp_pulito = campionato_scelto.split('(')[0].strip()
        
        st.markdown(f"""
            <div style='padding: 14px 18px; border-left: 6px solid #3b82f6; background-color: #1e1e2f; border-radius: 6px; margin-bottom: 20px;'>
                <h2 style='margin: 0; color: #ffffff;'>🛡️ {squadra_selezionata}</h2>
                <p style='margin: 4px 0 0 0; color: #94a3b8;'>Competizione: <b>{nome_comp_pulito} ({tipo_competizione})</b> | Partite Analizzate: <b>{stats['Partite Considerate']}</b></p>
            </div>
        """, unsafe_allow_html=True)

        # Riquadri Metriche
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Tiri / gara", stats["Media Tiri Totali"])
        col2.metric("In Porta / gara", stats["Media Tiri in Porta"])
        col3.metric("Corner / gara", stats["Media Corner a Favore"])
        col4.metric("Falli / gara", stats["Media Falli Commessi"])
        col5.metric("Parate / gara", stats["Media Parate Portiere"])

        st.markdown("---")

        # --- ULTIME 5 PARTITE ---
        st.subheader("📅 Ultime 5 Partite (Stato di Forma)")
        
        if 'Date_Parsed' in df.columns:
            df_sorted = df.sort_values('Date_Parsed')
        else:
            df_sorted = df
            
        partite_squadra = df_sorted[(df_sorted['HomeTeam'] == squadra_selezionata) | (df_sorted['AwayTeam'] == squadra_selezionata)].tail(5)
        
        if not partite_squadra.empty:
            for _, row in partite_squadra.iterrows():
                is_home = row['HomeTeam'] == squadra_selezionata
                casa_team = row['HomeTeam']
                trasferta_team = row['AwayTeam']
                
                gf = int(row['FTHG'])
                gs = int(row['FTAG'])
                
                data_str = str(row['Date']) if 'Date' in row else ""
                luogo_tag = "🏠 In Casa" if is_home else "✈️ Fuori Casa"
                info_sinistra = f"{data_str} • {luogo_tag} • {tipo_competizione}"
                
                gf_squadra = gf if is_home else gs
                gs_squadra = gs if is_home else gf
                
                if gf_squadra > gs_squadra:
                    esito, colore_badge = "V", "#28a745"
                elif gf_squadra == gs_squadra:
                    esito, colore_badge = "N", "#ffc107"
                else:
                    esito, colore_badge = "P", "#dc3545"

                st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; align-items: center; background-color: #161b22; padding: 12px 18px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #30363d;'>
                        <span style='color: #8b949e; font-size: 13px; font-weight: 500;'>{info_sinistra}</span>
                        <span style='font-weight: bold; color: #c9d1d9; font-size: 15px;'>{casa_team} {gf} - {gs} {trasferta_team}</span>
                        <span style='background-color: {colore_badge}; color: white; padding: 3px 12px; border-radius: 4px; font-weight: bold; font-size: 13px;'>{esito}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna partita recente trovata.")

        st.markdown("---")

        # --- SEZIONE DISCIPLINARE + CLASSIFICA ---
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("⚠️ Analisi Disciplinare")
            st.metric("Media Cartellini Gialli / gara", stats["Media Cartellini Gialli"])
            st.metric("Media Cartellini Rossi / gara", stats["Media Cartellini Rossi"])

        with col_right:
            st.subheader(f"🏆 Classifica {nome_comp_pulito}")
            df_classifica = calcola_classifica(df)
            
            def evidenzia_squadra(row):
                if row['Squadra'] == squadra_selezionata:
                    return ['background-color: #1e3a8a; color: #ffffff; font-weight: bold;'] * len(row)
                return [''] * len(row)

            st.dataframe(
                df_classifica.style.apply(evidenzia_squadra, axis=1),
                use_container_width=True,
                height=320
            )

else:
    st.error("Nessun dato disponibile per i parametri selezionati.")