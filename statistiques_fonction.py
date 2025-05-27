import pandas as pd
import streamlit as st
from ventes_fonction import load_ventes_cache
from depenses_fonction import load_depenses_cache
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from client_fonction import load_clients_cache
from produit_fonction import load_produits_cache
from depenses_fonction import load_depenses_cache

def get_benefice_par_date():
    """
    Calcule le bénéfice (ventes - dépenses) par date.
    Retourne un DataFrame avec les colonnes Date et Benefice.
    """
    # Charger les ventes et dépenses
    ventes = load_ventes_cache(_invalidate=True)
    depenses = load_depenses_cache(_invalidate=True)

    if ventes.empty and depenses.empty:
        return pd.DataFrame(columns=["Date", "Benefice_Cumule"])

    # Filtrer les ventes validées
    ventes = ventes[ventes["Valide"] == True] if not ventes.empty else ventes

    # Agréger les ventes par date
    ventes_par_date = ventes.groupby("Date")["Prix"].sum().reset_index() if not ventes.empty else pd.DataFrame(columns=["Date", "Prix"])
    ventes_par_date.rename(columns={"Prix": "Ventes"}, inplace=True)

    # Agréger les dépenses par date
    depenses_par_date = depenses.groupby("Date")["Prix"].sum().reset_index() if not depenses.empty else pd.DataFrame(columns=["Date", "Prix"])
    depenses_par_date.rename(columns={"Prix": "Dépenses"}, inplace=True)

    # Fusionner les DataFrames sur la date
    merged = pd.merge(ventes_par_date, depenses_par_date, on="Date", how="outer").fillna(0)

    # Calculer le bénéfice
    merged["Benefice"] = merged["Ventes"] - merged["Dépenses"]

    try:
        # Convertir la date en datetime
        merged["Date"] = pd.to_datetime(merged["Date"], format="%Y-%m-%d", errors="coerce")
        # Supprimer les lignes avec des dates invalides
        merged = merged.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"Erreur lors de la conversion des dates : {e}")
        return pd.DataFrame(columns=["Date", "Benefice_Cumule"])

    # Trier par date
    merged = merged.sort_values("Date")

    # Calculer le bénéfice cumulé
    merged["Benefice_Cumule"] = merged["Benefice"].cumsum()

    return merged[["Date", "Benefice_Cumule"]]

def get_dernier_benefice():
    """
    Retourne le bénéfice cumulé à la dernière date et la date correspondante.
    """
    benefice_df = get_benefice_par_date()
    if benefice_df.empty:
        return 0.0, None
    dernier_benefice = benefice_df.iloc[-1]["Benefice_Cumule"]
    derniere_date = benefice_df.iloc[-1]["Date"]
    return dernier_benefice, derniere_date

def plot_benefice_evolution():
    """
    Crée un graphique interactif de l'évolution du bénéfice cumulé.
    Retourne une figure Plotly.
    """
    benefice_df = get_benefice_par_date()
    if benefice_df.empty:
        st.warning("Aucune donnée disponible pour afficher le graphique du bénéfice.")
        return None
    
    fig = px.line(
        benefice_df,
        x="Date",
        y="Benefice_Cumule",
        title="Évolution du bénéfice cumulé (€)",
        labels={"Benefice_Cumule": "Bénéfice cumulé (€)", "Date": "Date"},
        template="plotly_white"
    )
    
    # Personnaliser l'apparence
    fig.update_traces(
        line_color="#1f77b4",
        line_width=2,
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Bénéfice: %{y:.2f} €"
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Bénéfice cumulé (€)",
        hovermode="x unified",
        showlegend=False
    )
    
    return fig

def get_chiffre_affaires_et_depenses_par_mois(selected_months=None):
    """
    Calcule le chiffre d'affaires et les dépenses par mois et année.
    Retourne un DataFrame avec les colonnes Mois_Annee, Type (Ventes/Dépenses), Montant.
    Si selected_months est fourni, filtre sur ces mois (format 'Mois Année', ex. 'Mars 2025').
    """
    ventes = load_ventes_cache(_invalidate=True)
    depenses = load_depenses_cache(_invalidate=True)

    if ventes.empty and depenses.empty:
        return pd.DataFrame(columns=["Mois_Annee", "Type", "Montant"])

    # Filtrer les ventes validées
    ventes = ventes[ventes["Valide"] == True] if not ventes.empty else ventes

    # Convertir les dates en datetime
    try:
        if not ventes.empty:
            ventes["Date"] = pd.to_datetime(ventes["Date"], format="%Y-%m-%d", errors="coerce")
            ventes = ventes.dropna(subset=["Date"])
        if not depenses.empty:
            depenses["Date"] = pd.to_datetime(depenses["Date"], format="%Y-%m-%d", errors="coerce")
            depenses = depenses.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"Erreur lors de la conversion des dates : {e}")
        return pd.DataFrame(columns=["Mois_Annee", "Type", "Montant"])

    # Extraire Mois et Année
    if not ventes.empty:
        ventes["Mois_Annee"] = ventes["Date"].dt.strftime("%B %Y")  # Ex. "Mars 2025"
        ventes_par_mois = ventes.groupby("Mois_Annee")["Prix"].sum().reset_index()
        ventes_par_mois["Type"] = "Ventes"
        ventes_par_mois.rename(columns={"Prix": "Montant"}, inplace=True)
    else:
        ventes_par_mois = pd.DataFrame(columns=["Mois_Annee", "Montant", "Type"])

    if not depenses.empty:
        depenses["Mois_Annee"] = depenses["Date"].dt.strftime("%B %Y")
        depenses_par_mois = depenses.groupby("Mois_Annee")["Prix"].sum().reset_index()
        depenses_par_mois["Type"] = "Dépenses"
        depenses_par_mois.rename(columns={"Prix": "Montant"}, inplace=True)
    else:
        depenses_par_mois = pd.DataFrame(columns=["Mois_Annee", "Montant", "Type"])

    # Concaténer les données
    data = pd.concat([ventes_par_mois, depenses_par_mois], ignore_index=True).fillna(0)

    # Filtrer par mois sélectionnés si fourni
    if selected_months:
        data = data[data["Mois_Annee"].isin(selected_months)]

    # Trier par date pour l'ordre chronologique
    if not data.empty:
        data["Date"] = pd.to_datetime(data["Mois_Annee"], format="%B %Y")
        data = data.sort_values("Date")
        data = data[["Mois_Annee", "Type", "Montant"]]

    return data

def plot_chiffre_affaires_vs_depenses(selected_months=None):
    """
    Crée un bar plot du chiffre d'affaires et des dépenses par mois.
    Retourne une figure Plotly.
    """
    data = get_chiffre_affaires_et_depenses_par_mois(selected_months)
    if data.empty:
        st.warning("Aucune donnée disponible pour afficher le graphique des ventes et dépenses.")
        return None

    fig = px.bar(
        data,
        x="Mois_Annee",
        y="Montant",
        color="Type",
        barmode="group",
        title="Chiffre d'affaires et dépenses par mois (€)",
        labels={"Mois_Annee": "Mois", "Montant": "Montant (€)", "Type": "Type"},
        template="plotly_white"
    )

    # Personnaliser l'apparence
    fig.update_traces(
        hovertemplate="%{y:.2f} €<br>%{x}"
    )
    fig.update_layout(
        xaxis_title="Mois",
        yaxis_title="Montant (€)",
        hovermode="x unified",
        legend_title="Type",
        xaxis_tickangle=45
    )

    return fig

def get_chiffre_affaires_par_produit(start_date=None, end_date=None):
    """
    Calcule le chiffre d'affaires par produit.
    Filtre par période si start_date et end_date sont fournis (format 'YYYY-MM-DD').
    Retourne un DataFrame avec les colonnes Produit, Montant.
    """
    ventes = load_ventes_cache(_invalidate=True)
    produits = load_produits_cache(_invalidate=True)

    if ventes.empty or produits.empty:
        return pd.DataFrame(columns=["Produit", "Montant"])

    # Filtrer les ventes validées
    ventes = ventes[ventes["Valide"] == True]

    # Convertir les dates
    try:
        ventes["Date"] = pd.to_datetime(ventes["Date"], format="%Y-%m-%d", errors="coerce")
        ventes = ventes.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"Erreur lors de la conversion des dates : {e}")
        return pd.DataFrame(columns=["Produit", "Montant"])

    # Filtrer par période si spécifié
    if start_date and end_date:
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            ventes = ventes[(ventes["Date"] >= start_date) & (ventes["Date"] <= end_date)]
        except Exception as e:
            st.error(f"Erreur dans le filtrage des dates : {e}")
            return pd.DataFrame(columns=["Produit", "Montant"])

    # Fusionner avec produits pour obtenir les noms
    try:
        ventes = ventes.merge(
            produits[["Produit_ID", "Nom"]],
            on="Produit_ID",
            how="left"
        )
        ventes["Produit"] = ventes["Nom"].fillna("Inconnu")
    except Exception as e:
        st.error(f"Erreur lors de la fusion avec les produits : {e}")
        return pd.DataFrame(columns=["Produit", "Montant"])

    # Agréger par produit
    data = ventes.groupby("Produit")["Prix"].sum().reset_index()
    data.rename(columns={"Prix": "Montant"}, inplace=True)
    data = data.sort_values("Montant", ascending=False)

    return data[["Produit", "Montant"]]

def plot_chiffre_affaires_per_product(start_date=None, end_date=None):
    """
    Crée un bar plot du chiffre d'affaires par produit.
    Retourne une figure Plotly.
    """
    data = get_chiffre_affaires_par_produit(start_date, end_date)
    if data.empty:
        st.warning("Aucune donnée disponible pour afficher le chiffre d'affaires par produit.")
        return None

    fig = px.bar(
        data,
        x="Produit",
        y="Montant",
        title="Chiffre d'affaires par produit (€)",
        labels={"Produit": "Produit", "Montant": "Montant (€)"},
        template="plotly_white"
    )

    # Personnaliser l'apparence
    fig.update_traces(
        marker_color="#1f77b4",
        hovertemplate="%{x}: %{y:.2f} €"
    )
    fig.update_layout(
        xaxis_title="Produit",
        yaxis_title="Montant (€)",
        xaxis_tickangle=45,
        hovermode="x"
    )

    return fig

def get_chiffre_affaires_per_client(start_date=None, end_date=None):
    """
    Calcule le chiffre d'affaires par client.
    Filtre par période si start_date et end_date sont fournis (format 'YYYY-MM-DD').
    Retourne un DataFrame avec les colonnes Client, Montant.
    """
    ventes = load_ventes_cache(_invalidate=True)
    clients = load_clients_cache(_invalidate=True)

    if ventes.empty or clients.empty:
        return pd.DataFrame(columns=["Client", "Montant"])

    # Filtrer les ventes validées
    ventes = ventes[ventes["Valide"] == True]

    # Convertir les dates
    try:
        ventes["Date"] = pd.to_datetime(ventes["Date"], format="%Y-%m-%d", errors="coerce")
        ventes = ventes.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"Erreur lors de la conversion des dates : {e}")
        return pd.DataFrame(columns=["Client", "Montant"])

    # Filtrer par période si spécifié
    if start_date and end_date:
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            ventes = ventes[(ventes["Date"] >= start_date) & (ventes["Date"] <= end_date)]
        except Exception as e:
            st.error(f"Erreur dans le filtrage des dates : {e}")
            return pd.DataFrame(columns=["Client", "Montant"])

    # Fusionner avec clients pour obtenir les noms
    try:
        clients["Client"] = clients["Nom"].fillna("") + " " + clients["Prénom"].fillna("")
        clients["Client"] = clients["Client"].str.strip()
        ventes = ventes.merge(
            clients[["Client_ID", "Client"]],
            on="Client_ID",
            how="left"
        )
        ventes["Client"] = ventes["Client"].fillna("Inconnu")
    except Exception as e:
        st.error(f"Erreur lors de la fusion avec les clients : {e}")
        return pd.DataFrame(columns=["Client", "Montant"])

    # Agréger par client
    data = ventes.groupby("Client")["Prix"].sum().reset_index()
    data.rename(columns={"Prix": "Montant"}, inplace=True)
    data = data.sort_values("Montant", ascending=False)

    return data[["Client", "Montant"]]

def plot_chiffre_affaires_per_client(start_date=None, end_date=None):
    """
    Crée un bar plot du chiffre d'affaires par client.
    Retourne une figure Plotly.
    """
    data = get_chiffre_affaires_per_client(start_date, end_date)
    if data.empty:
        st.warning("Aucune donnée disponible pour afficher le chiffre d'affaires par client.")
        return None

    fig = px.bar(
        data,
        x="Client",
        y="Montant",
        title="Chiffre d'affaires par client (€)",
        labels={"Client": "Client", "Montant": "Montant (€)"},
        template="plotly_white"
    )

    # Personnaliser l'apparence
    fig.update_traces(
        marker_color="#2ca02c",
        hovertemplate="%{x}: %{y:.2f} €"
    )
    fig.update_layout(
        xaxis_title="Client",
        yaxis_title="Montant (€)",
        xaxis_tickangle=45,
        hovermode="x"
    )

    return fig

def get_depenses_per_name(start_date=None, end_date=None):
    """
    Calcule les dépenses par nom.
    Filtre par période si start_date et end_date sont fournis (format 'YYYY-MM-DD').
    Retourne un DataFrame avec les colonnes Nom, Montant.
    """
    depenses = load_depenses_cache(_invalidate=True)

    if depenses.empty:
        return pd.DataFrame(columns=["Nom", "Montant"])

    # Convertir les dates
    try:
        depenses["Date"] = pd.to_datetime(depenses["Date"], format="%Y-%m-%d", errors="coerce")
        depenses = depenses.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"Erreur lors de la conversion des dates : {e}")
        return pd.DataFrame(columns=["Nom", "Montant"])

    # Filtrer par période si spécifié
    if start_date and end_date:
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            depenses = depenses[(depenses["Date"] >= start_date) & (depenses["Date"] <= end_date)]
        except Exception as e:
            st.error(f"Erreur dans le filtrage des dates : {e}")
            return pd.DataFrame(columns=["Nom", "Montant"])

    # Agréger par nom
    data = depenses.groupby("Nom")["Prix"].sum().reset_index()
    data.rename(columns={"Prix": "Montant"}, inplace=True)
    data = data.sort_values("Montant", ascending=False)

    return data[["Nom", "Montant"]]

def plot_depenses_per_name(start_date=None, end_date=None):
    """
    Crée un bar plot des dépenses par nom.
    Retourne une figure Plotly.
    """
    data = get_depenses_per_name(start_date, end_date)
    if data.empty:
        st.warning("Aucune donnée disponible pour afficher les dépenses par nom.")
        return None

    fig = px.bar(
        data,
        x="Nom",
        y="Montant",
        title="Dépenses par type de dépense (€)",
        labels={"Nom": "Type de dépense", "Montant": "Montant (€)"},
        template="plotly_white"
    )

    # Personnaliser l'apparence
    fig.update_traces(
        marker_color="#d62728",
        hovertemplate="%{x}: %{y:.2f} €"
    )
    fig.update_layout(
        xaxis_title="Type de dépense",
        yaxis_title="Montant (€)",
        xaxis_tickangle=45,
        hovermode="x"
    )

    return fig