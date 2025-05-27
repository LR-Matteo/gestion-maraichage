import pandas as pd
import streamlit as st
import os
from datetime import datetime

def load_depenses():
    """
    Charge le csv des dépenses s'il existe ou le créé sinon.
    """
    depenses_file = "data/dépenses.csv"
    try:
        depenses = pd.read_csv(depenses_file)
        expected_columns = ["Depense_ID", "Date", "Nom", "Prix"]
        if not all(col in depenses.columns for col in expected_columns):
            st.error("Colonnes incorrectes dans dépenses.csv")
            depenses = pd.DataFrame(columns=expected_columns)
        return depenses
    except FileNotFoundError:
        st.warning("Aucune base de données dépenses trouvée, création d'un fichier vide.")
        os.makedirs("data", exist_ok=True)
        depenses = pd.DataFrame(columns=["Depense_ID", "Date", "Prix"])
        depenses.to_csv(depenses_file, index=False)
        return depenses
    except pd.errors.ParserError:
        st.error("Erreur de format dans le fichier dépenses.csv")
        return pd.DataFrame(columns=["Depense_ID", "Date", "Nom", "Prix"])

@st.cache_data
def load_depenses_cache(_invalidate=None):
    """
    Garde en mémoire les données. Utilise un paramètre pour invalider le cache.
    """
    return load_depenses()

def generate_depense_id():
    """
    Génère un Depense_ID unique basé sur le maximum des ID existants.
    """
    depenses = load_depenses_cache()
    if depenses.empty:
        return 1
    return depenses["Depense_ID"].max() + 1

def save_depense(date, nom, prix):
    """
    Ajoute une dépense au DataFrame et sauvegarde dans data/dépenses.csv.
    """
    depenses = load_depenses_cache(_invalidate=True)

    # Vérifier la date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        erreur.error("La date doit être au format AAAA-MM-DD")
        return False

    # Vérifier le nom
    if not nom:
        erreur.error("Le nom de la dépense est obligatoire")
        return False

    # Valider le prix
    try:
        prix = float(prix)
        if prix < 0:
            erreur.error("Le prix ne peut pas être négatif")
            return False
    except ValueError:
        erreur.error("Le prix doit être un nombre valide")
        return False

    # Générer un nouvel ID
    new_id = generate_depense_id()

    # Créer une nouvelle ligne
    new_depense = pd.DataFrame({
        "Depense_ID": [new_id],
        "Date": [date],
        "Nom": [nom],
        "Prix": [prix]
    })

    # Ajouter la ligne avec pd.concat
    depenses = pd.concat([depenses, new_depense], ignore_index=True)

    # Sauvegarder dans data/depenses.csv
    try:
        depenses.to_csv("data/dépenses.csv", index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de la dépense : {e}")
        return False

def find_depense_id(depense_id):
    """
    Vérifie si une dépense avec le Depense_ID donné existe.
    Retourne True si la dépense existe, False sinon.
    """
    depenses = load_depenses_cache()
    matching_depenses = depenses[depenses["Depense_ID"] == depense_id]
    if matching_depenses.empty:
        st.error(f"Aucune dépense trouvée avec l'ID {depense_id}")
        return False
    return True

def delete_depense(depense_id):
    """
    Supprime une dépense du DataFrame basé sur son Depense_ID.
    """
    if not find_depense_id(depense_id):
        return False

    depenses = load_depenses_cache(_invalidate=True)

    # Supprimer la ligne avec le Depense_ID
    depenses = depenses[depenses["Depense_ID"] != depense_id]

    # Sauvegarder le DataFrame mis à jour
    try:
        depenses.to_csv("data/dépenses.csv", index=False)
        st.cache_data.clear()
        st.success(f"Dépense (ID: {depense_id}) supprimée avec succès !")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la dépense : {e}")
        return False