import pandas as pd
import streamlit as st
import os
from github_utils import push_to_github

# Créer le dossier data/ s'il n'existe pas
os.makedirs("data", exist_ok=True)
CLIENTS_FILE = "data/clients.csv"

@st.cache_data
def load_clients_cache(_invalidate=False):
    try:
        return pd.read_csv(CLIENTS_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Client_ID", "Nom", "Prénom", "Email", "Téléphone"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des clients : {e}")
        return pd.DataFrame(columns=["Client_ID", "Nom", "Prénom", "Email", "Téléphone"])

def save_client(nom, prenom, email, telephone):
    try:
        clients = load_clients_cache(_invalidate=True)
        new_id = clients["Client_ID"].max() + 1 if not clients.empty else 1
        new_client = pd.DataFrame([{
            "Client_ID": new_id,
            "Nom": nom,
            "Prénom": prenom,
            "Email": email,
            "Téléphone": telephone
        }])
        clients = pd.concat([clients, new_client], ignore_index=True)
        clients.to_csv(CLIENTS_FILE, index=False)
        with open(CLIENTS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/clients.csv", content, f"Ajout/modification de client {nom} {prenom}")
        load_clients_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l’enregistrement du client : {e}")
        return False

def delete_client(nom, prenom):
    try:
        clients = load_clients_cache(_invalidate=True)
        if clients[(clients["Nom"].str.lower() == nom.lower()) & (clients["Prénom"].str.lower() == prenom.lower())].empty:
            return False
        clients = clients[~((clients["Nom"].str.lower() == nom.lower()) & (clients["Prénom"].str.lower() == prenom.lower()))]
        clients.to_csv(CLIENTS_FILE, index=False)
        with open(CLIENTS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/clients.csv", content, f"Suppression du client {nom} {prenom}")
        load_clients_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression du client : {e}")
        return False

def upload_clients(file):
    try:
        uploaded_clients = pd.read_csv(file)
        current_clients = load_clients_cache(_invalidate=True)
        expected_columns = ["Client_ID", "Nom", "Prénom", "Email", "Téléphone"]
        if not all(col in uploaded_clients.columns for col in expected_columns):
            return False
        if not current_clients.empty:
            merged_clients = pd.concat([current_clients, uploaded_clients], ignore_index=True)
            merged_clients = merged_clients.drop_duplicates(subset=["Nom", "Prénom"], keep="last")
        else:
            merged_clients = uploaded_clients
        merged_clients["Client_ID"] = range(1, len(merged_clients) + 1)
        merged_clients.to_csv(CLIENTS_FILE, index=False)
        with open(CLIENTS_FILE, "r") as f:
            content = f.read()
        push_to_github("data/clients.csv", content, "Upload de clients.csv")
        load_clients_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors du chargement de clients.csv : {e}")
        return False