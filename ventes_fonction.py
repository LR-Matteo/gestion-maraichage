import pandas as pd
import streamlit as st
from client_fonction import load_clients_cache
from produit_fonction import load_produits_cache
import os
from github_utils import push_to_github

# Créer le dossier data/ s'il n’existe pas
os.makedirs("data", exist_ok=True)
VENTES_FILE = "data/ventes.csv"

@st.cache_data
def load_ventes_cache(_invalidate=False):
    try:
        return pd.read_csv(VENTES_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des ventes : {e}")
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])

def get_ventes_affichage():
    ventes = load_ventes_cache(_invalidate=True)
    clients = load_clients_cache(_invalidate=True)
    produits = load_produits_cache(_invalidate=True)
    if ventes.empty:
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Produits", "Total"])
    
    # Joindre les clients et produits
    ventes = ventes.merge(clients[["Client_ID", "Nom", "Prénom"]], on="Client_ID", how="left")
    ventes = ventes.merge(produits[["Produit_ID", "Nom"]], left_on="Produit_ID", right_on="Produit_ID", how="left")
    ventes["Client"] = ventes["Nom_x"] + " " + ventes["Prénom"]
    
    # Regrouper par Vente_ID pour afficher une ligne par vente
    grouped = ventes.groupby(["Vente_ID", "Date", "Client"]).agg({
        "Nom_y": lambda x: ", ".join(x.dropna()),
        "Prix": "sum"
    }).reset_index()
    grouped = grouped.rename(columns={"Nom_y": "Produits", "Prix": "Total"})
    return grouped[["Vente_ID", "Date", "Client", "Produits", "Total"]]

def get_vente_details(vente_id):
    ventes = load_ventes_cache(_invalidate=True)
    clients = load_clients_cache(_invalidate=True)
    produits = load_produits_cache(_invalidate=True)
    vente_details = ventes[ventes["Vente_ID"] == vente_id]
    if vente_details.empty:
        return pd.DataFrame()
    
    # Joindre les clients et produits pour les détails
    vente_details = vente_details.merge(clients[["Client_ID", "Nom", "Prénom"]], on="Client_ID", how="left")
    vente_details = vente_details.merge(produits[["Produit_ID", "Nom"]], left_on="Produit_ID", right_on="Produit_ID", how="left")
    vente_details["Client"] = vente_details["Nom_x"] + " " + vente_details["Prénom"]
    return vente_details[["Date", "Client", "Nom_y", "Quantité", "Prix"]].rename(columns={"Nom_y": "Produit"})

def save_vente(date, client_nom, client_prenom, produits, quantites, prix_totaux):
    try:
        ventes = load_ventes_cache(_invalidate=True)
        clients = load_clients_cache(_invalidate=True)
        produits_df = load_produits_cache(_invalidate=True)
        
        # Vérifier le client
        client = clients[(clients["Nom"].str.lower() == client_nom.lower()) & 
                        (clients["Prénom"].str.lower() == client_prenom.lower())]
        if client.empty:
            st.error("Client non trouvé.")
            return False
        client_id = client["Client_ID"].iloc[0]
        
        # Générer un nouvel ID de vente
        new_vente_id = int(ventes["Vente_ID"].max() + 1 if not ventes.empty else 1)
        
        # Créer une ligne par produit
        new_ventes = []
        for nom_produit, quantite, prix in zip(produits, quantites, prix_totaux):
            produit_row = produits_df[produits_df["Nom"] == nom_produit]
            if produit_row.empty:
                st.error(f"Produit {nom_produit} non trouvé.")
                continue
            produit_id = produit_row["Produit_ID"].iloc[0]
            new_ventes.append({
                "Vente_ID": new_vente_id,
                "Date": date,
                "Client_ID": client_id,
                "Produit_ID": produit_id,
                "Quantité": quantite,
                "Prix": prix
            })
        
        if not new_ventes:
            st.error("Aucun produit valide pour cette vente.")
            return False
        
        # Ajouter les nouvelles lignes
        new_ventes_df = pd.DataFrame(new_ventes)
        ventes = pd.concat([ventes, new_ventes_df], ignore_index=True)
        ventes.to_csv(VENTES_FILE, index=False)
        
        # Synchroniser avec GitHub
        with open(VENTES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/ventes.csv", content, f"Ajout de la vente ID {new_vente_id}")
        load_ventes_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l’enregistrement de la vente : {e}")
        return False

def delete_vente(vente_id):
    try:
        ventes = load_ventes_cache(_invalidate=True)
        if ventes[ventes["Vente_ID"] == vente_id].empty:
            st.error("Vente non trouvée.")
            return False
        ventes = ventes[ventes["Vente_ID"] != vente_id]
        ventes.to_csv(VENTES_FILE, index=False)
        with open(VENTES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/ventes.csv", content, f"Suppression de la vente ID {vente_id}")
        load_ventes_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la vente : {e}")
        return False

def upload_ventes(file):
    try:
        uploaded_ventes = pd.read_csv(file)
        current_ventes = load_ventes_cache(_invalidate=True)
        expected_cols = ["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"]
        if not all(col in uploaded_ventes.columns for col in expected_cols):
            st.error("Colonnes manquantes dans le fichier CSV.")
            return False
        if not current_ventes.empty:
            merged_ventes = pd.concat([current_ventes, uploaded_ventes], ignore_index=True)
            merged_ventes = merged_ventes.drop_duplicates(subset=["Vente_ID", "Produit_ID", "Client_ID", "Date"], keep="last")
        else:
            merged_ventes = uploaded_ventes
        merged_ventes.to_csv(VENTES_FILE, index=False)
        with open(VENTES_FILE, "r") as f:
            content = f.read()
        push_to_github("data/ventes.csv", content, "Upload de ventes.csv")
        load_ventes_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors du chargement de ventes.csv : {e}")