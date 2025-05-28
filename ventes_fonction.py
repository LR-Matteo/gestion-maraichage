import pandas as pd
import streamlit as st
from client_fonction import load_clients_cache
from produit_fonction import load_produits_cache

# Chemin vers le fichier ventes.csv
VENTES_FILE = "data/ventes.csv"

@st.cache_data
def load_ventes_cache(_invalidate=False):
    """
    Charge les données des ventes depuis ventes.csv avec mise en cache.
    """
    try:
        ventes = pd.read_csv(VENTES_FILE)
        return ventes
    except FileNotFoundError:
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des ventes : {e}")
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])

def save_vente(date, client_nom, client_prenom, produits, quantites, prix_totaux):
    """
    Enregistre une vente avec plusieurs produits dans ventes.csv.
    Args:
        date (str): Date de la vente (format YYYY-MM-DD).
        client_nom (str): Nom du client.
        client_prenom (str): Prénom du client.
        produits (list): Liste des noms de produits.
        quantites (list): Liste des quantités correspondantes.
        prix_totaux (list): Liste des prix totaux par produit.
    Returns:
        bool: True si succès, False sinon.
    """
    try:
        ventes = load_ventes_cache(_invalidate=True)
        clients = load_clients_cache(_invalidate=True)
        produits_df = load_produits_cache(_invalidate=True)

        # Trouver l'ID du client
        client = clients[(clients["Nom"].str.lower() == client_nom.lower()) & 
                         (clients["Prénom"].str.lower() == client_prenom.lower())]
        if client.empty:
            return False
        client_id = client.iloc[0]["Client_ID"]

        # Générer un nouveau Vente_ID
        new_vente_id = ventes["Vente_ID"].max() + 1 if not ventes.empty else 1

        # Créer une ligne pour chaque produit
        new_rows = []
        for produit_nom, quantite, prix in zip(produits, quantites, prix_totaux):
            produit = produits_df[produits_df["Nom"] == produit_nom]
            if produit.empty:
                return False
            produit_id = produit.iloc[0]["Produit_ID"]
            
            new_row = {
                "Vente_ID": new_vente_id,
                "Date": date,
                "Client_ID": client_id,
                "Produit_ID": produit_id,
                "Quantité": quantite,
                "Prix": prix
            }
            new_rows.append(new_row)

        # Ajouter les nouvelles lignes
        new_ventes = pd.DataFrame(new_rows)
        ventes = pd.concat([ventes, new_ventes], ignore_index=True)
        
        # Sauvegarder
        ventes.to_csv(VENTES_FILE, index=False)
        
        # Invalider le cache
        load_ventes_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement de la vente : {e}")
        return False

def delete_vente(vente_id):
    """
    Supprime toutes les lignes associées à un Vente_ID dans ventes.csv.
    """
    try:
        ventes = load_ventes_cache(_invalidate=True)
        if ventes[ventes["Vente_ID"] == vente_id].empty:
            return False
        
        ventes = ventes[ventes["Vente_ID"] != vente_id]
        ventes.to_csv(VENTES_FILE, index=False)
        
        load_ventes_cache.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la vente : {e}")
        return False

def get_ventes_affichage():
    """
    Retourne un DataFrame pour l'affichage des ventes regroupées par commande.
    Colonnes : Vente_ID, Date, Client, Prix total.
    """
    try:
        ventes = load_ventes_cache(_invalidate=True)
        clients = load_clients_cache(_invalidate=True)
        if ventes.empty or clients.empty:
            return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Prix total"])

        # Regrouper par Vente_ID, Date, Client_ID pour calculer le prix total
        ventes_grouped = ventes.groupby(["Vente_ID", "Date", "Client_ID"], as_index=False)["Prix"].sum()
        ventes_grouped = ventes_grouped.rename(columns={"Prix": "Prix total"})

        # Fusionner avec clients pour obtenir le nom complet
        clients["Client"] = clients["Nom"].str.cat(clients["Prénom"], sep=" ", na_rep="").str.strip()
        ventes_grouped = ventes_grouped.merge(
            clients[["Client_ID", "Client"]],
            on="Client_ID",
            how="left"
        )
        ventes_grouped["Client"] = ventes_grouped["Client"].fillna("Inconnu")

        # Formater la date
        ventes_grouped["Date"] = pd.to_datetime(ventes_grouped["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

        # Retourner les colonnes dans l'ordre souhaité
        return ventes_grouped[["Vente_ID", "Date", "Client", "Prix total"]]
    except Exception as e:
        st.error(f"Erreur lors de la récupération des ventes : {e}")
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Prix total"])

def get_vente_details(vente_id):
    """
    Retourne les détails des produits pour un Vente_ID donné.
    Colonnes : Produit, Quantité, Prix unitaire, Prix total.
    """
    try:
        ventes = load_ventes_cache(_invalidate=True)
        produits = load_produits_cache(_invalidate=True)
        
        # Filtrer les lignes pour ce Vente_ID
        vente = ventes[ventes["Vente_ID"] == vente_id]
        if vente.empty:
            return pd.DataFrame(columns=["Produit", "Quantité", "Prix unitaire", "Prix total"])

        # Fusionner avec produits pour obtenir les noms et prix unitaires
        vente = vente.merge(
            produits[["Produit_ID", "Nom", "Prix (au Kg)"]],
            on="Produit_ID",
            how="left"
        )
        vente["Produit"] = vente["Nom"].fillna("Inconnu")
        vente["Prix unitaire"] = vente["Prix (au Kg)"].fillna(0.0)
        
        # Sélectionner et renommer les colonnes
        details = vente[["Produit", "Quantité", "Prix unitaire", "Prix"]]
        details = details.rename(columns={"Prix": "Prix total"})
        
        return details
    except Exception as e:
        st.error(f"Erreur lors de la récupération des détails de la vente : {e}")
        return pd.DataFrame(columns=["Produit", "Quantité", "Prix unitaire", "Prix total"])