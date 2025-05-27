import pandas as pd
import streamlit as st
import os

def load_produits():
    """
    Charge le csv produit s'il existe ou le créé sinon.
    """
    produits_file = "data/produits.csv"  # Uniformisé à produits.csv
    try:
        produits = pd.read_csv(produits_file)
        expected_columns = ["Produit_ID", "Nom", "Prix (au Kg)"]
        if not all(col in produits.columns for col in expected_columns):
            st.error("Colonnes incorrectes dans produits.csv")
            produits = pd.DataFrame(columns=expected_columns)
        return produits
    except FileNotFoundError:
        st.warning("Aucune base de données produits trouvée, création d'un fichier vide.")
        os.makedirs("data", exist_ok=True)
        produits = pd.DataFrame(columns=["Produit_ID", "Nom", "Prix (au Kg)"])
        produits.to_csv(produits_file, index=False)
        return produits
    except pd.errors.ParserError:
        st.error("Erreur de format dans le fichier produits.csv")
        return pd.DataFrame(columns=["Produit_ID", "Nom", "Prix (au Kg)"])

@st.cache_data
def load_produits_cache(_invalidate=None):
    """
    Garde en mémoire les données. Utilise un paramètre pour invalider le cache.
    """
    return load_produits()

def generate_produit_id():
    """
    Génère un Produit_ID unique basé sur le maximum des ID existants.
    """
    produits = load_produits_cache()  # Utilise le cache
    if produits.empty:
        return 1
    return produits["Produit_ID"].max() + 1

def check_produit_exists(nom):
    """
    Vérifie si un produit avec le même nom existe déjà.
    Retourne True si le produit existe, False sinon.
    """
    produits = load_produits_cache()
    matching_produits = produits[produits["Nom"].str.lower() == nom.lower()]
    return not matching_produits.empty

def save_produit(nom, prix):
    """
    Ajoute un produit au DataFrame et sauvegarde dans data/produits.csv.
    Vérifie si un produit avec le même nom existe déjà.
    """
    # Vérifier si le produit existe déjà
    if check_produit_exists(nom):
        st.error(f"Un produit avec le nom '{nom}' existe déjà.")
        return False
    
    produits = load_produits_cache(_invalidate=True)  # Forcer le rechargement
    
    # Valider les données
    if not nom:
        st.error("Le nom du produit est obligatoire")
        return False
    
    try:
        prix = float(prix)
        if prix < 0:
            st.error("Le prix ne peut pas être négatif")
            return False
    except ValueError:
        st.error("Le prix doit être un nombre valide")
        return False
    
    # Générer un nouvel ID
    new_id = generate_produit_id()
    
    # Créer une nouvelle ligne
    new_produit = pd.DataFrame({
        "Produit_ID": [new_id],
        "Nom": [nom],
        "Prix (au Kg)": [prix]
    })
    
    # Ajouter la ligne avec pd.concat
    produits = pd.concat([produits, new_produit], ignore_index=True)
    
    # Sauvegarder dans data/produits.csv
    try:
        produits.to_csv("data/produits.csv", index=False)
        st.cache_data.clear()  # Invalider le cache
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du produit : {e}")
        return False

def find_produit_id(nom):
    """
    Trouve le Produit_ID associé au nom.
    """
    produits = load_produits_cache()
    
    # Filtrer par nom (case-insensitive)
    matching_produits = produits[produits["Nom"].str.lower() == nom.lower()]
    
    if matching_produits.empty:
        st.error(f"Aucun produit trouvé avec le nom '{nom}'")
        return None
    
    if len(matching_produits) > 1:
        st.error(f"Plusieurs produits trouvés avec le nom '{nom}'. Veuillez préciser.")
        return None
    
    return matching_produits.iloc[0]["Produit_ID"]

def delete_produit(nom):
    """
    Supprime un produit du DataFrame basé sur son nom.
    """
    produit_id = find_produit_id(nom)
    
    if produit_id is None:
        return False
    
    produits = load_produits_cache(_invalidate=True)  # Forcer le rechargement
    
    # Supprimer la ligne avec le Produit_ID
    produits = produits[produits["Produit_ID"] != produit_id]  # Corrigé
    
    # Sauvegarder le DataFrame mis à jour
    try:
        produits.to_csv("data/produits.csv", index=False)
        st.cache_data.clear()
        st.success(f"Produit '{nom}' (ID: {produit_id}) supprimé avec succès !")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression du produit : {e}")
        return False

def modificate_price(nom, prix):
    """
    Modifie le prix d'un produit.
    """
    produit_id = find_produit_id(nom)
    
    if produit_id is None:
        return False
    
    produits = load_produits_cache(_invalidate=True)  # Forcer le rechargement
    
    # Valider le prix
    try:
        prix = float(prix)
        if prix < 0:
            st.error("Le prix ne peut pas être négatif")
            return False
    except ValueError:
        st.error("Le prix doit être un nombre valide")
        return False
    
    # Mettre à jour le prix
    produits.loc[produits["Produit_ID"] == produit_id, "Prix (au Kg)"] = prix
    
    # Sauvegarder le DataFrame
    try:
        produits.to_csv("data/produits.csv", index=False)
        st.cache_data.clear()
        st.success(f"Prix du produit '{nom}' mis à jour à {prix} €/kg")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du produit : {e}")
        return False