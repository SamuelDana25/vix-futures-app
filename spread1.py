import pandas as pd
import streamlit as st
import altair as alt
import plotly.graph_objects as go
import datetime

# Titre de l'application
st.title("📈 Visualisation du Spread1 des Futures du VIX")

# 1. Charger le fichier CSV
st.header("Étape 1 : Chargement des données")
uploaded_file = st.file_uploader("Téléchargez votre fichier CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    # Chemin du fichier par défaut
    default_file = "fichier_fusionne.csv"
    try:
        df = pd.read_csv(default_file)
        st.write(f"Fichier par défaut chargé : {default_file}")
    except FileNotFoundError:
        st.error(f"Le fichier par défaut '{default_file}' n'a pas été trouvé dans le dossier.")
        st.stop()  # Ar

    st.write("Données chargées :")
    st.write(df.head())  # Afficher les premières lignes pour vérifier

    # 2. Supprimer les lignes où 'Open' est égal à 0
    st.header("Étape 2 : Suppression des lignes où 'Open' est égal à 0")
    df = df[df['Open'] != 0]
    st.write("Données après suppression des lignes où 'Open' est égal à 0 :")
    st.write(df.head())

    # 3. Nettoyer et préparer les données
    st.header("Étape 3 : Nettoyage et préparation des données")
    # Convertir la colonne 'Trade Date' en datetime
    df['Trade Date'] = pd.to_datetime(df['Trade Date'])
    st.write("Colonne 'Trade Date' convertie en datetime :")
    st.write(df['Trade Date'].head())

    # Extraire le mois et l'année de la colonne 'Futures'
    df['Futures'] = df['Futures'].str.extract(r'(\w{3} \d{4})')
    st.write("Colonne 'Futures' extraite :")
    st.write(df['Futures'].head())

    # Convertir la colonne 'Futures' en datetime pour faciliter les comparaisons
    df['Futures'] = pd.to_datetime(df['Futures'], format='%b %Y')
    st.write("Colonne 'Futures' convertie en datetime :")
    st.write(df['Futures'].head())

    # 4. Calculer le spread1 et identifier les dates de changement de future
    st.header("Étape 4 : Calcul du spread1 et identification des dates de changement de future")
    # Trier les données par date de trade et par future
    df = df.sort_values(by=['Trade Date', 'Futures'])
    st.write("Données triées par 'Trade Date' et 'Futures' :")
    st.write(df.head())

    # Créer une nouvelle colonne pour stocker le spread1
    df['spread1'] = None

    # Liste pour stocker les dates de changement de future
    change_dates = []

    # Boucler sur chaque date de trade
    st.write("Début de la boucle sur les dates de trade...")
    previous_future = None
    for trade_date in df['Trade Date'].unique():
        # Filtrer les données pour la date de trade actuelle
        current_data = df[df['Trade Date'] == trade_date]
        
        # Vérifier s'il y a au moins deux futures pour cette date
        if len(current_data) >= 2:
            # Trier les futures par mois pour s'assurer qu'ils sont dans l'ordre
            current_data = current_data.sort_values(by='Futures')
            
            # Identifier le future actuel (premier future de la liste)
            current_future = current_data.iloc[0]['Futures']
            
            # Vérifier si le future a changé par rapport à la date précédente
            if previous_future is not None and current_future != previous_future:
                change_dates.append(trade_date)  # Ajouter la date de changement à la liste
            
            # Mettre à jour le future précédent
            previous_future = current_future
            
            # Calculer le spread1 entre le future suivant et le current future
            spread1 = current_data.iloc[1]['Open'] - current_data.iloc[0]['Open']
            
            # Stocker le spread1 dans la colonne correspondante
            df.loc[(df['Trade Date'] == trade_date), 'spread1'] = spread1

    # 5. Filtrer les valeurs NaN (où le spread1 n'a pas pu être calculé)
    st.header("Étape 5 : Filtrage des valeurs NaN")
    df_spread = df.dropna(subset=['spread1'])
    st.write("Données après filtrage des NaN :")
    st.write(df_spread.head())

   # 6. Tracer le graphique principal et les graphiques par année
    st.header("Étape 6 : Tracé des graphiques")

    # Préparer les données pour le graphique
    chart_data = df_spread[['Trade Date', 'spread1']]

    # Ajouter une colonne 'Year' pour faciliter la séparation par année
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

    # Ajouter des lignes verticales pour les dates de changement de future
    vertical_lines = alt.Chart(pd.DataFrame({'change_dates': change_dates})).mark_rule(
        color='red', strokeWidth=1, strokeDash=[5, 5]  # Ligne rouge en pointillés
    ).encode(
        x='change_dates:T'  # Colonne des dates de changement
    )

    # Combiner le graphique du spread1 et les lignes verticales
    final_chart = line_chart + vertical_lines

    # Afficher le graphique principal dans Streamlit
    st.altair_chart(final_chart, use_container_width=True)

    # --- Graphiques par année ---
    st.subheader("Graphiques par année")

    # Créer un sélecteur d'année
    selected_year = st.selectbox("Sélectionnez une année", chart_data['Year'].unique())

    # Filtrer les données pour l'année sélectionnée
    year_data = chart_data[chart_data['Year'] == selected_year]

    # Créer un graphique Altair pour l'année sélectionnée
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

    # Ajouter des lignes verticales pour les dates de changement de future (pour l'année sélectionnée)
    year_change_dates = [date for date in change_dates if date.year == selected_year]
    year_vertical_lines = alt.Chart(pd.DataFrame({'change_dates': year_change_dates})).mark_rule(
        color='red', strokeWidth=1, strokeDash=[5, 5]  # Ligne rouge en pointillés
    ).encode(
        x='change_dates:T'  # Colonne des dates de changement
    )

    # Combiner le graphique du spread1 et les lignes verticales pour l'année
    final_year_chart = year_chart + year_vertical_lines

    # Afficher le graphique de l'année sélectionnée dans Streamlit
    st.altair_chart(final_year_chart, use_container_width=True)

    st.success("Graphiques interactifs tracés avec succès !")

