import pandas as pd
import streamlit as st

# Chemin vers le fichier depenses.csv
DEPENSES_FILE = "data/depenses.csv"

@st.cache_data
def load_depenses_cache(_invalidate=False):
    """
    Charge les données des dépenses depuis depenses.csv avec mise en cache.
    """
    try:
        depenses = pd.read_csv(DEPENSES_FILE)
        return depenses
    except FileNotFoundError:
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des dépenses : {e}")
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])

def save_depense(date, nom, prix):
    """
    Enregistre une nouvelle dépense dans depenses.csv.
    """
    try:
        depenses = load_depenses_cache(_invalidate=True)
        new_id = depenses["Depense_ID"].max() + 1 if not depenses.empty else 1
        new_depense = pd.DataFrame([{
            "Depense_ID": new_id,
            "Date": date,
            "Nom": nom,
            "Prix": prix
        }])
        depenses = pd.concat([depenses, new_depense], ignore_index=True)
        depenses.to_csv(DEPENSES_FILE, index=False)
        load_depenses_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement de la dépense : {e}")
        return False

def delete_depense(depense_id):
    """
    Supprime une dépense de depenses.csv.
    """
    try:
        depenses = load_depenses_cache(_invalidate=True)
        if depenses[depenses["Depense_ID"] == depense_id].empty:
            return False
        depenses = depenses[depenses["Depense_ID"] != depense_id]
        depenses.to_csv(DEPENSES_FILE, index=False)
        load_depenses_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la dépense : {e}")
        return False

def get_depenses_affichage():
    """
    Retourne un DataFrame pour l'affichage des dépenses regroupées par date.
    Colonnes : Date, Total.
    """
    try:
        depenses = load_depenses_cache(_invalidate=True)
        if depenses.empty:
            return pd.DataFrame(columns=["Date", "Total"])

        # Regrouper par Date pour calculer le total
        depenses_grouped = depenses.groupby("Date", as_index=False)["Prix"].sum()
        depenses_grouped = depenses_grouped.rename(columns={"Prix": "Total"})

        # Formater la date
        depenses_grouped["Date"] = pd.to_datetime(depenses_grouped["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

        return depenses_grouped[["Date", "Total"]]
    except Exception as e:
        st.error(f"Erreur lors de la récupération des dépenses : {e}")
        return pd.DataFrame(columns=["Date", "Total"])

def get_depense_details(date):
    """
    Retourne les détails des dépenses pour une date donnée.
    Colonnes : Nom, Prix.
    """
    try:
        depenses = load_depenses_cache(_invalidate=True)
        
        # Filtrer les dépenses pour la date donnée
        depense = depenses[depenses["Date"] == date]
        if depense.empty:
            return pd.DataFrame(columns=["Nom", "Prix"])

        # Sélectionner les colonnes pertinentes
        details = depense[["Nom", "Prix"]]
        
        return details
    except Exception as e:
        st.error(f"Erreur lors de la récupération des détails de la dépense : {e}")
        return pd.DataFrame(columns=["Nom", "Prix"])