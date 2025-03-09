import pandas as pd
import streamlit as st
import altair as alt
import plotly.graph_objects as go
import datetime

st.title("📈 Visualisation du Spread1 des Futures du VIX")

st.header("Étape 1 : Chargement des données")
uploaded_file = st.file_uploader("Téléchargez votre fichier CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    default_file = "vix_fut.csv"
    try:
        df = pd.read_csv(default_file)
        st.write(f"Fichier par défaut chargé : {default_file}")
    except FileNotFoundError:
        st.error(f"Le fichier par défaut '{default_file}' n'a pas été trouvé dans le dossier.")
        st.stop() 

    st.write("Données chargées :")
    st.write(df.head())  

    st.header("Étape 2 : Suppression des lignes où 'Open' est égal à 0")
    df = df[df['Open'] != 0]
    st.write("Données après suppression des lignes où 'Open' est égal à 0 :")
    st.write(df.head())

    st.header("Étape 3 : Nettoyage et préparation des données")
    df['Trade Date'] = pd.to_datetime(df['Trade Date'])
    st.write("Colonne 'Trade Date' convertie en datetime :")
    st.write(df['Trade Date'].head())

    df['Futures'] = df['Futures'].str.extract(r'(\w{3} \d{4})')
    st.write("Colonne 'Futures' extraite :")
    st.write(df['Futures'].head())

    df['Futures'] = pd.to_datetime(df['Futures'], format='%b %Y')
    st.write("Colonne 'Futures' convertie en datetime :")
    st.write(df['Futures'].head())

    st.header("Étape 4 : Calcul du spread1 et identification des dates de changement de future")
    df = df.sort_values(by=['Trade Date', 'Futures'])
    st.write("Données triées par 'Trade Date' et 'Futures' :")
    st.write(df.head())

    df['spread1'] = None

    change_dates = []

    st.write("Début de la boucle sur les dates de trade...")
    previous_future = None
    for trade_date in df['Trade Date'].unique():
        current_data = df[df['Trade Date'] == trade_date]
        
        if len(current_data) >= 2:
            current_data = current_data.sort_values(by='Futures')
            current_future = current_data.iloc[0]['Futures']
            
            if previous_future is not None and current_future != previous_future:
                change_dates.append(trade_date)  # Ajouter la date de changement à la liste
            
            previous_future = current_future
            spread1 = current_data.iloc[1]['Open'] - current_data.iloc[0]['Open']
            
            df.loc[(df['Trade Date'] == trade_date), 'spread1'] = spread1

    st.header("Étape 5 : Filtrage des valeurs NaN")
    df_spread = df.dropna(subset=['spread1'])
    st.write("Données après filtrage des NaN :")
    st.write(df_spread.head())
    st.header("Étape 6 : Tracé des graphiques")
    chart_data = df_spread[['Trade Date', 'spread1']]
    chart_data['Year'] = chart_data['Trade Date'].dt.year

    # --- Graphique principal ---
    st.subheader("Graphique principal (toutes les années)")
    line_chart = alt.Chart(chart_data).mark_line().encode(
        x=alt.X('Trade Date:T', title='Date'),  # Colonne de date avec un titre
        y=alt.Y('spread1:Q', title='Spread1'),  # Colonne du spread1 avec un titre
        tooltip=['Trade Date', 'spread1']  # Infobulle pour l'interactivité
    ).properties(
        width=800,
        height=400,
        title='Spread1 des Futures du VIX avec Changements de Future (toutes les années)'
    ).interactive()  # Rendre le graphique interactif (zoom, défilement)
    change_dates = [pd.Timestamp(date) for date in change_dates]

    vertical_lines = alt.Chart(pd.DataFrame({'change_dates': change_dates})).mark_rule(
        color='red', strokeWidth=1, strokeDash=[5, 5]  # Ligne rouge en pointillés
    ).encode(
        x='change_dates:T'  # Colonne des dates de changement
    )
    final_chart = line_chart + vertical_lines
    st.altair_chart(final_chart, use_container_width=True)

    # --- Graphiques par année ---
    st.subheader("Graphiques par année")
    selected_year = st.selectbox("Sélectionnez une année", chart_data['Year'].unique())
    year_data = chart_data[chart_data['Year'] == selected_year]
    year_chart = alt.Chart(year_data).mark_line().encode(
        x=alt.X('Trade Date:T', title='Date'),  # Colonne de date avec un titre
        y=alt.Y('spread1:Q', title='Spread1'),  # Colonne du spread1 avec un titre
        tooltip=['Trade Date', 'spread1']  # Infobulle pour l'interactivité
    ).properties(
        width=800,
        height=400,
        title=f'Spread1 des Futures du VIX pour l\'année {selected_year}'
    ).interactive()  # Rendre le graphique interactif (zoom, défilement)
    year_change_dates = [date for date in change_dates if date.year == selected_year]

    year_change_dates = [date for date in change_dates if date.year == selected_year]
    year_vertical_lines = alt.Chart(pd.DataFrame({'change_dates': year_change_dates})).mark_rule(
        color='red', strokeWidth=1, strokeDash=[5, 5]  # Ligne rouge en pointillés
    ).encode(
        x='change_dates:T'  # Colonne des dates de changement
    )

    final_year_chart = year_chart + year_vertical_lines
    st.altair_chart(final_year_chart, use_container_width=True)

    st.success("Graphiques interactifs tracés avec succès !")

