import pandas as pd
import streamlit as st
import os
from github_utils import push_to_github

# Créer le dossier data/ s'il n’existe pas
os.makedirs("data", exist_ok=True)
DEPENSES_FILE = "data/depenses.csv"

@st.cache_data
def load_depenses_cache(_invalidate=False):
    try:
        return pd.read_csv(DEPENSES_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des dépenses : {e}")
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])

def get_depenses_affichage():
    depenses = load_depenses_cache(_invalidate=True)
    if depenses.empty:
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])
    return depenses[["Depense_ID", "Date", "Nom", "Prix"]]

def get_depense_details(depense_id):
    depenses = load_depenses_cache(_invalidate=True)
    if depenses[depenses["Depense_ID"] == depense_id].empty:
        return pd.DataFrame()
    return depenses[depenses["Depense_ID"] == depense_id][["Depense_ID", "Date", "Nom", "Prix"]]

def save_depense(date, nom, prix):
    try:
        depenses = load_depenses_cache(_invalidate=True)
        new_depense_id = int(depenses["Depense_ID"].max() + 1 if not depenses.empty else 1)
        new_depense = pd.DataFrame([{
            "Depense_ID": new_depense_id,
            "Date": date,
            "Nom": nom,
            "Prix": prix
        }])
        depenses = pd.concat([depenses, new_depense], ignore_index=True)
        depenses.to_csv(DEPENSES_FILE, index=False)
        with open(DEPENSES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/depenses.csv", content, f"Ajout de la dépense {nom} (ID {new_depense_id})")
        load_depenses_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l’enregistrement de la dépense : {e}")
        return False

def delete_depense(depense_id):
    try:
        depenses = load_depenses_cache(_invalidate=True)
        if depenses[depenses["Depense_ID"] == depense_id].empty:
            return False
        depenses = depenses[depenses["Depense_ID"] != depense_id]
        depenses.to_csv(DEPENSES_FILE, index=False)
        with open(DEPENSES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/depenses.csv", content, f"Suppression de la dépense ID {depense_id}")
        load_depenses_cache.clear()
        return True
    except Exception as e:
        return False

def upload_depenses(file):
    try:
        uploaded_depenses = pd.read_csv(file)
        current_depenses = load_depenses_cache(_invalidate=True)
        expected_cols = ["Depense_ID", "Date", "Nom", "Prix"]
        if not all(col in uploaded_depenses.columns for col in expected_cols):
            st.error("Colonnes manquantes dans le fichier CSV.")
            return False
        if not current_depenses.empty:
            merged_depenses = pd.concat([current_depenses, uploaded_depenses], ignore_index=True)
            merged_depenses = merged_depenses.drop_duplicates(subset=["Depense_ID", "Date", "Nom"], keep="last")
        else:
            merged_depenses = uploaded_depenses
        merged_depenses["Depense_ID"] = range(1, len(merged_depenses) + 1)
        merged_depenses.to_csv(DEPENSES_FILE, index=False)
        with open(DEPENSES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/depenses.csv", content, "Upload de depenses.csv")
        load_depenses_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors du chargement de depenses.csv : {e}")
        return False