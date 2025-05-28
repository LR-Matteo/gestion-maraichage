import streamlit as st
from github import Github
import base64
import os

def push_to_github(file_path, content, commit_message):
    """
    Pousse un fichier modifié vers le dépôt GitHub.
    Args:
        file_path (str): Chemin du fichier (ex. 'data/clients.csv').
        content (str): Contenu du fichier (CSV sous forme de string).
        commit_message (str): Message du commit.
    Returns:
        bool: True si succès, False sinon.
    """
    try:
        # Récupérer les secrets
        github_token = st.secrets["github"]["token"]
        repo_name = st.secrets["github"]["repo"]

        # Initialiser le client GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        # Vérifier si le fichier existe dans le dépôt
        try:
            file = repo.get_contents(file_path)
            # Mettre à jour le fichier
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=file.sha,
                branch="master"
            )
        except:
            # Créer le fichier s'il n'existe pas
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch="master"
            )
        return True
    except Exception as e:
        st.error(f"Erreur lors du push vers GitHub : {e}")
        return False