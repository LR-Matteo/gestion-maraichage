import pandas as pd
import streamlit as st
import os
from github_utils import push_to_github

# Créer le dossier data/ s'il n'existe pas
os.makedirs("data", exist_ok=True)
PRODUITS_FILE = "data/produits.csv"

@st.cache_data
def load_produits_cache(_invalidate=False):
    try:
        return pd.read_csv(PRODUITS_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Produit_ID", "Nom", "Prix (au Kg)"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des produits : {e}")
        return pd.DataFrame(columns=["Produit_ID", "Nom", "Prix (au Kg)"])

def save_produit(nom, prix):
    try:
        produits = load_produits_cache(_invalidate=True)
        new_id = produits["Produit_ID"].max() + 1 if not produits.empty else 1
        new_produit = pd.DataFrame([{
            "Produit_ID": new_id,
            "Nom": nom,
            "Prix (au Kg)": prix
        }])
        produits = pd.concat([produits, new_produit], ignore_index=True)
        produits.to_csv(PRODUITS_FILE, index=False)
        with open(PRODUITS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/produits.csv", content, f"Ajout/modification du produit {nom}")
        load_produits_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l’enregistrement du produit : {e}")
        return False

def delete_produit(nom):
    try:
        produits = load_produits_cache(_invalidate=True)
        if produits[produits["Nom"].str.lower() == nom.lower()].empty:
            return False
        produits = produits[produits["Nom"].str.lower() != nom.lower()]
        produits.to_csv(PRODUITS_FILE, index=False)
        with open(PRODUITS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/produits.csv", content, f"Suppression du produit {nom}")
        load_produits_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression du produit : {e}")
        return False

def modificate_price(nom, nouveau_prix):
    try:
        produits = load_produits_cache(_invalidate=True)
        if produits[produits["Nom"].str.lower() == nom.lower()].empty:
            return False
        produits.loc[produits["Nom"].str.lower() == nom.lower(), "Prix (au Kg)"] = nouveau_prix
        produits.to_csv(PRODUITS_FILE, index=False)
        with open(PRODUITS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/produits.csv", content, f"Modification du prix du produit {nom}")
        load_produits_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la modification du prix : {e}")
        return False

def upload_produits(file):
    try:
        uploaded_produits = pd.read_csv(file)
        current_produits = load_produits_cache(_invalidate=True)
        expected_columns = ["Produit_ID", "Nom", "Prix (au Kg)"]
        if not all(col in uploaded_produits.columns for col in expected_columns):
            return False
        if not current_produits.empty:
            merged_produits = pd.concat([current_produits, uploaded_produits], ignore_index=True)
            merged_produits = merged_produits.drop_duplicates(subset=["Nom"], keep="last")
        else:
            merged_produits = uploaded_produits
        merged_produits["Produit_ID"] = range(1, len(merged_produits) + 1)
        merged_produits.to_csv(PRODUITS_FILE, index=False)
        with open(PRODUITS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/produits.csv", content, "Upload de produits.csv")
        load_produits_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors du chargement de produits.csv : {e}")
        return False