import pandas as pd
import streamlit as st
import os

def load_clients():
    """
    Charge le csv client s'il existe ou le créé sinon.
    """
    clients_file = "data/clients.csv"  # Uniformisé à clients.csv
    try:
        clients = pd.read_csv(clients_file)
        expected_columns = ["Client_ID", "Nom", "Prénom", "Email", "Téléphone"]
        if not all(col in clients.columns for col in expected_columns):
            st.error("Colonnes incorrectes dans clients.csv")
            clients = pd.DataFrame(columns=expected_columns)
        return clients
    except FileNotFoundError:
        st.warning("Aucune base de données client trouvée, création d'un fichier vide.")
        os.makedirs("data", exist_ok=True)
        clients = pd.DataFrame(columns=["Client_ID", "Nom", "Prénom", "Email", "Téléphone"])
        clients.to_csv(clients_file, index=False)
        return clients
    except pd.errors.ParserError:
        st.error("Erreur de format dans le fichier clients.csv")
        return pd.DataFrame(columns=["Client_ID", "Nom", "Prénom", "Email", "Téléphone"])

@st.cache_data
def load_clients_cache(_invalidate=None):
    """
    Garde en mémoire les données. Utilise un paramètre pour invalider le cache.
    """
    return load_clients()

def generate_client_id():
    """
    Génère un Client_ID unique basé sur le maximum des ID existants.
    """
    clients = load_clients_cache()  # Utilise le cache
    if clients.empty:
        return 1
    return clients["Client_ID"].max() + 1

def check_client_exists(nom, prenom):
    """
    Vérifie si un client avec le même nom et prénom existe déjà.
    Retourne True si le client existe, False sinon.
    """
    clients = load_clients_cache()
    matching_clients = clients[clients["Nom"].str.lower() == nom.lower()]
    if not matching_clients.empty:
        matching_clients = matching_clients[matching_clients["Prénom"].str.lower() == prenom.lower()]
        if not matching_clients.empty:
            return True
    return False

def save_client(nom, prenom, email="", telephone=""):
    """
    Ajoute un client au DataFrame et sauvegarde dans data/clients.csv.
    Vérifie si un client avec le même nom et prénom existe déjà.
    """
    # Vérifier si le client existe déjà
    if check_client_exists(nom, prenom):
        st.error(f"Un client avec le nom '{nom}' et le prénom '{prenom}' existe déjà.")
        return False
    
    clients = load_clients_cache(_invalidate=True)  # Forcer le rechargement
    
    # Valider les données
    if not nom:
        st.error("Le nom du client est obligatoire")
        return False
    
    # Générer un nouvel ID
    new_id = generate_client_id()
    
    # Créer une nouvelle ligne
    new_client = pd.DataFrame({
        "Client_ID": [new_id],
        "Nom": [nom],
        "Prénom": [prenom],
        "Email": [email],
        "Téléphone": [str(telephone)]
    })
    
    # Ajouter la ligne avec pd.concat
    clients = pd.concat([clients, new_client], ignore_index=True)
    
    # Sauvegarder dans data/clients.csv
    try:
        clients.to_csv("data/clients.csv", index=False)
        st.cache_data.clear()  # Invalider le cache globalement
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du client : {e}")
        return False

def find_client_id(nom, prenom):
    """
    Trouve le Client_ID correspondant à un nom et prénom.
    Filtre d'abord par nom, puis par prénom si plusieurs résultats.
    """
    clients = load_clients_cache()  # Utilise le cache
    
    matching_clients = clients[clients["Nom"].str.lower() == nom.lower()]
    
    if matching_clients.empty:
        st.error(f"Aucun client trouvé avec le nom '{nom}'")
        return None
    
    if len(matching_clients) > 1:
        matching_clients = matching_clients[matching_clients["Prénom"].str.lower() == prenom.lower()]
        
        if matching_clients.empty:
            st.error(f"Aucun client trouvé avec le nom '{nom}' et le prénom '{prenom}'")
            return None
        
        if len(matching_clients) > 1:
            st.error(f"Plusieurs clients trouvés avec le nom '{nom}' et le prénom '{prenom}'. Veuillez utiliser un identifiant unique.")
            return None
    
    return matching_clients.iloc[0]["Client_ID"]

def delete_client(nom, prenom):
    """
    Supprime un client du DataFrame basé sur son nom et prénom.
    """
    client_id = find_client_id(nom, prenom)
    
    if client_id is None:
        return False
    
    clients = load_clients_cache(_invalidate=True)  # Forcer le rechargement
    
    # Supprimer la ligne avec le Client_ID
    clients = clients[clients["Client_ID"] != client_id]  # Corrigé
    
    # Sauvegarder le DataFrame mis à jour
    try:
        clients.to_csv("data/clients.csv", index=False)
        st.cache_data.clear()  # Invalider le cache
        st.success(f"Client '{nom} {prenom}' (ID: {client_id}) supprimé avec succès !")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression du client : {e}")
        return False
