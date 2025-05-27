import pandas as pd
import streamlit as st
import os
from datetime import datetime
from client_fonction import load_clients_cache, find_client_id
from produit_fonction import load_produits_cache, find_produit_id

def load_ventes():
    """
    Charge le csv ventes s'il existe ou le crée sinon.
    """
    ventes_file = "data/ventes.csv"
    try:
        ventes = pd.read_csv(ventes_file)
        expected_columns = ["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"]
        if not all(col in ventes.columns for col in expected_columns):
            st.error("Colonnes incorrectes dans ventes.csv")
            ventes = pd.DataFrame(columns=expected_columns)
        return ventes
    except FileNotFoundError:
        st.warning("Aucune base de données ventes trouvée, création d'un fichier vide.")
        os.makedirs("data", exist_ok=True)
        ventes = pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])
        ventes.to_csv(ventes_file, index=False)
        return ventes
    except pd.errors.ParserError:
        st.error("Erreur de format dans le fichier ventes.csv")
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"])

@st.cache_data
def load_ventes_cache(_invalidate=None):
    """
    Garde en mémoire les données. Utilise un paramètre pour invalider le cache.
    """
    return load_ventes()

def generate_vente_id():
    """
    Génère un Vente_ID unique basé sur le maximum des ID existants.
    """
    ventes = load_ventes_cache()
    if ventes.empty:
        return 1
    return ventes["Vente_ID"].max() + 1

def save_vente(date, client_nom, client_prenom, produit_nom, quantite, prix_total):
    """
    Ajoute une vente au DataFrame et sauvegarde dans data/ventes.csv.
    Le prix_total est calculé comme Quantité * Prix au kg du produit.
    """
    ventes = load_ventes_cache(_invalidate=True)

    # Valider la date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        st.error("La date doit être au format AAAA-MM-JJ")
        return False

    # Valider le client
    client_id = find_client_id(client_nom, client_prenom)
    if client_id is None:
        st.error("Client non trouvé")
        return False

    # Valider le produit
    produit_id = find_produit_id(produit_nom)
    if produit_id is None:
        st.error("Produit non trouvé")
        return False

    # Valider la quantité
    try:
        quantite = float(quantite)
        if quantite <= 0:
            st.error("La quantité doit être positive")
            return False
    except ValueError:
        st.error("La quantité doit être un nombre valide")
        return False

    # Valider le prix total
    try:
        prix_total = float(prix_total)
        if prix_total < 0:
            st.error("Le prix total ne peut pas être négatif")
            return False
    except ValueError:
        st.error("Le prix total doit être un nombre valide")
        return False

    # Générer un nouvel ID
    new_id = generate_vente_id()

    # Créer une nouvelle ligne
    new_vente = pd.DataFrame({
        "Vente_ID": [new_id],
        "Date": [date],
        "Client_ID": [client_id],
        "Produit_ID": [produit_id],
        "Quantité": [quantite],
        "Prix": [prix_total]
    })

    # Ajouter la ligne avec pd.concat
    ventes = pd.concat([ventes, new_vente], ignore_index=True)

    # Sauvegarder dans data/ventes.csv
    try:
        ventes.to_csv("data/ventes.csv", index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de la vente : {e}")
        return False

def find_vente_id(vente_id):
    """
    Vérifie si une vente avec le Vente_ID donné existe.
    Retourne True si la vente existe, False sinon.
    """
    ventes = load_ventes_cache()
    matching_ventes = ventes[ventes["Vente_ID"] == vente_id]
    if matching_ventes.empty:
        st.error(f"Aucune vente trouvée avec l'ID {vente_id}")
        return False
    return True

def delete_vente(vente_id):
    """
    Supprime une vente du DataFrame basé sur son Vente_ID.
    """
    if not find_vente_id(vente_id):
        return False

    ventes = load_ventes_cache(_invalidate=True)

    # Supprimer la ligne avec le Vente_ID
    ventes = ventes[ventes["Vente_ID"] != vente_id]

    # Sauvegarder le DataFrame mis à jour
    try:
        ventes.to_csv("data/ventes.csv", index=False)
        st.cache_data.clear()
        st.success(f"Vente (ID: {vente_id}) supprimée avec succès !")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la vente : {e}")
        return False

def get_ventes_affichage():
    """
    Retourne un DataFrame des ventes avec les noms des clients et produits à la place des ID.
    """
    ventes = load_ventes_cache(_invalidate=True)
    clients = load_clients_cache(_invalidate=True)
    produits = load_produits_cache(_invalidate=True)

    if ventes.empty:
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Produit", "Quantité", "Prix"])

    try:
        # Vérifier les colonnes nécessaires dans ventes
        if not all(col in ventes.columns for col in ["Vente_ID", "Date", "Client_ID", "Produit_ID", "Quantité", "Prix"]):
            st.error("Colonnes manquantes dans ventes.csv")
            return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Produit", "Quantité", "Prix"])

        # Initialiser les colonnes Client et Produit
        ventes["Client"] = "Inconnu"
        ventes["Produit"] = "Inconnu"

        # Fusionner avec clients pour obtenir Nom et Prénom
        if not clients.empty and all(col in clients.columns for col in ["Client_ID", "Nom", "Prénom"]):
            clients["Client"] = clients["Nom"].fillna("") + " " + clients["Prénom"].fillna("")
            clients["Client"] = clients["Client"].str.strip()
            ventes = ventes.merge(
                clients[["Client_ID", "Client"]],
                on="Client_ID",
                how="left",
                suffixes=("", "_client")
            )
            # Remplacer les valeurs manquantes par "Inconnu"
            ventes["Client"] = ventes["Client_client"].fillna("Inconnu")
            ventes = ventes.drop(columns=["Client_client"], errors="ignore")
        else:
            st.warning("Aucun client disponible ou colonnes manquantes dans clients.csv")

        # Fusionner avec produits pour obtenir Nom
        if not produits.empty and all(col in produits.columns for col in ["Produit_ID", "Nom"]):
            ventes = ventes.merge(
                produits[["Produit_ID", "Nom"]],
                on="Produit_ID",
                how="left"
            )
            ventes["Produit"] = ventes["Nom"].fillna("Inconnu")
            ventes = ventes.drop(columns=["Nom"], errors="ignore")
        else:
            st.warning("Aucun produit disponible ou colonnes manquantes dans produits.csv")

        # Sélectionner les colonnes finales
        colonnes_affichage = ["Vente_ID", "Date", "Client", "Produit", "Quantité", "Prix"]
        ventes = ventes[colonnes_affichage]

        return ventes

    except Exception as e:
        st.error(f"Erreur lors de la préparation de l'affichage des ventes : {e}")
        return pd.DataFrame(columns=["Vente_ID", "Date", "Client", "Produit", "Quantité", "Prix"])