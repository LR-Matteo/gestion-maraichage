import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from client_fonction import save_client, delete_client, load_clients_cache, upload_clients
from produit_fonction import save_produit, delete_produit, load_produits_cache, modificate_price, upload_produits
from ventes_fonction import save_vente, delete_vente, get_ventes_affichage, get_vente_details, upload_ventes, load_ventes_cache
from depenses_fonction import save_depense, delete_depense, load_depenses_cache, get_depenses_affichage, get_depense_details, upload_depenses
from statistiques_fonction import (
    plot_benefice_evolution,
    get_dernier_benefice,
    plot_chiffre_affaires_vs_depenses,
    plot_chiffre_affaires_per_product,
    plot_chiffre_affaires_per_client,
    plot_depenses_per_name
)
from github_utils import push_to_github
import os

# Créer le dossier data/ s'il n'existe pas
os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="Gestion Maraîchage", layout="wide")
st.title("Gestion Maraîchage")

# Menu
sous_partie = ["Ventes", "Dépenses", "Clients", "Produits", "Statistiques", "Gestion des données"]
selected_partie = st.selectbox("Menu : ", sous_partie)

if selected_partie == "Clients":
    st.header("Liste des clients")
    show_clients = st.checkbox("Afficher la liste des clients")
    if show_clients:
        clients = load_clients_cache(_invalidate=True)
        if not clients.empty:
            st.dataframe(clients[["Client_ID", "Nom", "Prénom", "Email", "Téléphone"]])
            csv = clients.to_csv(index=False)
            st.download_button(
                label="Télécharger clients.csv",
                data=csv,
                file_name="clients.csv",
                mime="text/csv"
            )
        else:
            st.write("Aucune donnée client à afficher.")
    
    st.header("Ajouter un client")
    with st.form(key="client_form"):
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email (optionnel)")
        telephone = st.text_input("Téléphone (optionnel)")
        submit_button = st.form_submit_button("Enregistrer le client")
        if submit_button:
            if nom and prenom:
                if save_client(nom, prenom, email, telephone):
                    st.success("Client ajouté avec succès !")
                else:
                    st.error("Erreur lors de l'ajout du client")
            else:
                st.error("Veuillez remplir le nom et le prénom.")

    st.header("Supprimer un client")
    with st.form(key="delete_client_form"):
        nom_del = st.text_input("Nom du client")
        prenom_del = st.text_input("Prénom du client")
        delete_button = st.form_submit_button("Supprimer le client")
        if delete_button:
            if nom_del and prenom_del:
                if delete_client(nom_del, prenom_del):
                    st.success("Client supprimé avec succès !")
                else:
                    st.error("Client non trouvé ou erreur lors de la suppression.")
            else:
                st.error("Veuillez entrer le nom et le prénom.")

elif selected_partie == "Produits":
    st.header("Liste des produits")
    show_produits = st.checkbox("Afficher la liste des produits")
    if show_produits:
        produits = load_produits_cache(_invalidate=True)
        if not produits.empty:
            st.dataframe(produits[["Produit_ID", "Nom", "Prix (au Kg)"]])
            csv = produits.to_csv(index=False)
            st.download_button(
                label="Télécharger produits.csv",
                data=csv,
                file_name="produits.csv",
                mime="text/csv"
            )
        else:
            st.write("Aucune donnée produit à afficher.")
    
    st.header("Ajouter un produit")
    with st.form(key="produit_form"):
        nom_produit = st.text_input("Nom du produit")
        prix_produit = st.number_input("Prix (€/kg)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Enregistrer le produit")
        if submit_button:
            if nom_produit and prix_produit > 0:
                if save_produit(nom_produit, prix_produit):
                    st.success("Produit ajouté avec succès !")
                else:
                    st.error("Erreur lors de l’ajout du produit")
            else:
                st.error("Veuillez remplir le nom et un prix valide.")

    st.header("Supprimer un produit")
    with st.form(key="delete_produit_form"):
        produits = load_produits_cache()
        produit_options = produits["Nom"].tolist() if not produits.empty else []
        nom_produit_del = st.selectbox("Produit à supprimer", produit_options)
        delete_button = st.form_submit_button("Supprimer le produit")
        if delete_button:
            if nom_produit_del:
                if delete_produit(nom_produit_del):
                    st.success("Produit supprimé avec succès !")
                else:
                    st.error("Produit non trouvé ou erreur lors de la suppression.")
            else:
                st.error("Veuillez sélectionner un produit.")

    st.header("Modifier le prix d’un produit")
    with st.form(key="modify_price_form"):
        produits = load_produits_cache()
        produit_options = produits["Nom"].tolist() if not produits.empty else []
        nom_produit = st.selectbox("Produit à modifier", produit_options)
        nouveau_prix = st.number_input("Nouveau prix (€/kg)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Modifier le prix")
        if submit_button:
            if nom_produit and nouveau_prix > 0:
                if modificate_price(nom_produit, nouveau_prix):
                    st.success("Prix modifié avec succès !")
                else:
                    st.error("Produit non trouvé ou erreur lors de la modification.")
            else:
                st.error("Veuillez sélectionner un produit et un prix valide.")

elif selected_partie == "Ventes":
    st.header("Liste des ventes")
    show_ventes = st.checkbox("Afficher la liste des ventes")
    if show_ventes:
        try:
            ventes = get_ventes_affichage()
            if not ventes.empty:
                st.write("Sélectionnez une vente pour voir les détails :")
                selected_ventes = []
                cols = st.columns([1, 2, 3, 2, 1])
                cols[0].write("Vente_ID")
                cols[1].write("Date")
                cols[2].write("Client")
                cols[3].write("Prix total (€)")
                cols[4].write("Détails")
                for index, row in ventes.iterrows():
                    cols = st.columns([1, 2, 3, 2, 1])
                    cols[0].write(row["Vente_ID"])
                    cols[1].write(row["Date"])
                    cols[2].write(row["Client"])
                    cols[3].write(f"{row['Total']:.2f}")
                    if cols[4].checkbox("Voir", key=f"detail_{row['Vente_ID']}"):
                        selected_ventes.append(row["Vente_ID"])
                for vente_id in selected_ventes:
                    st.subheader(f"Détails de la vente {vente_id}")
                    details = get_vente_details(vente_id)
                    if not details.empty:
                        st.dataframe(details)
                    else:
                        st.write("Aucun détail disponible.")
                csv = load_ventes_cache(_invalidate=True).to_csv(index=False)
                st.download_button(
                    label="Télécharger ventes.csv",
                    data=csv,
                    file_name="ventes.csv",
                    mime="text/csv"
                )
            else:
                st.write("Aucune donnée vente à afficher.")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage des ventes : {e}")

    st.header("Ajouter une vente")
    if "show_quantites" not in st.session_state:
        st.session_state.show_quantites = False
    if "selected_produits" not in st.session_state:
        st.session_state.selected_produits = []
    if "vente_form_reset" not in st.session_state:
        st.session_state.vente_form_reset = False

    with st.form(key="vente_form"):
        date = st.date_input("Date de la vente")
        clients = load_clients_cache(_invalidate=True)
        client_options = [f"{row['Nom']} {row['Prénom']}" for _, row in clients.iterrows()]
        client_selection = st.selectbox("Client", client_options, key="vente_client")
        produits = load_produits_cache(_invalidate=True)
        produit_options = produits["Nom"].tolist()
        temp_selected_produits = st.multiselect("Produits", produit_options, default=st.session_state.selected_produits, key="vente_produits")
        confirm_button = st.form_submit_button("Confirmer la sélection des produits")
        if confirm_button and temp_selected_produits:
            st.session_state.show_quantites = True
            st.session_state.selected_produits = temp_selected_produits
            st.session_state.vente_form_reset = False
        elif confirm_button:
            st.error("Veuillez sélectionner au moins un produit.")
        quantites = []
        prix_totaux = []
        total_commande = 0.0
        if st.session_state.show_quantites and not st.session_state.vente_form_reset:
            st.subheader("Saisir les quantités")
            for produit in st.session_state.selected_produits:
                st.write(f"**{produit}**")
                quantite = st.number_input(f"Quantité (kg) pour {produit}", min_value=0.0, step=0.1, key=f"quantite_{produit}")
                prix_unitaire = produits[produits["Nom"] == produit]["Prix (au Kg)"].iloc[0]
                prix = quantite * prix_unitaire
                st.write(f"Prix : {prix:.2f} € (Prix unitaire : {prix_unitaire:.2f} €/kg)")
                quantites.append(quantite)
                prix_totaux.append(prix)
                total_commande += prix
            st.write(f"**Prix total de la commande : {total_commande:.2f} €**")
        submit_button = st.form_submit_button("Enregistrer la vente")
        if submit_button and st.session_state.show_quantites:
            if not st.session_state.selected_produits or not all(q > 0 for q in quantites):
                st.error("Veuillez sélectionner au moins un produit avec une quantité valide.")
            else:
                client_nom, client_prenom = client_selection.split(" ", 1) if " " in client_selection else (client_selection, "")
                date_str = date.strftime("%Y-%m-%d")
                try:
                    if save_vente(date_str, client_nom, client_prenom, st.session_state.selected_produits, quantites, prix_totaux):
                        st.success("Vente ajoutée avec succès !")
                        st.session_state.show_quantites = False
                        st.session_state.selected_produits = []
                        st.session_state.vente_form_reset = True
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout de la vente")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement de la vente : {e}")

    st.header("Supprimer une vente")
    with st.form(key="delete_vente_form"):
        vente_id = st.number_input("ID de la vente", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la vente")
        if delete_button:
            try:
                if delete_vente(vente_id):
                    st.success("Vente supprimée avec succès !")
                else:
                    st.error("Vente non trouvée ou erreur lors de la suppression.")
            except Exception as e:
                st.error(f"Erreur lors de la suppression de la vente : {e}")

elif selected_partie == "Dépenses":
    st.header("Liste des dépenses")
    show_depenses = st.checkbox("Afficher la liste des dépenses")
    if show_depenses:
        try:
            depenses = get_depenses_affichage()
            if not depenses.empty:
                st.write("Sélectionnez une dépense pour voir les détails :")
                selected_depenses = []
                cols = st.columns([1, 2, 3, 2])
                cols[0].write("Depense_ID")
                cols[1].write("Date")
                cols[2].write("Total (€)")
                cols[3].write("Détails")
                for index, row in depenses.iterrows():
                    cols = st.columns([1, 2, 3, 2])
                    cols[0].write(row["Depense_ID"])
                    cols[1].write(row["Date"])
                    cols[2].write(f"{row['Total']:.2f}")
                    if cols[3].checkbox("Voir", key=f"detail_depense_{row['Depense_ID']}"):
                        selected_depenses.append(row["Depense_ID"])
                for depense_id in selected_depenses:
                    st.subheader(f"Détails de la dépense {depense_id}")
                    details = get_depense_details(depense_id)
                    if not details.empty:
                        st.dataframe(details)
                    else:
                        st.write("Aucun détail disponible.")
                csv = load_depenses_cache(_invalidate=True).to_csv(index=False)
                st.download_button(
                    label="Télécharger depenses.csv",
                    data=csv,
                    file_name="depenses.csv",
                    mime="text/csv"
                )
            else:
                st.write("Aucune donnée dépense à afficher.")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage des dépenses : {e}")

    st.header("Ajouter une dépense")
    if "show_prix_depenses" not in st.session_state:
        st.session_state.show_prix_depenses = False
    if "selected_depenses" not in st.session_state:
        st.session_state.selected_depenses = []
    if "depense_form_reset" not in st.session_state:
        st.session_state.depense_form_reset = False

    with st.form(key="depense_form"):
        date = st.date_input("Date de la dépense")
        noms_depenses = st.text_input("Noms des dépenses (séparés par des virgules)", placeholder="Engrais, Arrosage, Semences", key="depense_noms")
        confirm_button = st.form_submit_button("Confirmer la sélection des dépenses")
        reset_button = st.form_submit_button("Réinitialiser le formulaire")
        if confirm_button and noms_depenses:
            temp_selected_depenses = [nom.strip() for nom in noms_depenses.split(",") if nom.strip()]
            if temp_selected_depenses:
                st.session_state.show_prix_depenses = True
                st.session_state.selected_depenses = temp_selected_depenses
                st.session_state.depense_form_reset = False
            else:
                st.error("Veuillez entrer au moins un nom de dépense valide.")
        elif confirm_button:
            st.error("Veuillez entrer au moins un nom de dépense.")
        prix_depenses = []
        total_depenses = 0.0
        if st.session_state.show_prix_depenses and not st.session_state.depense_form_reset:
            st.subheader("Saisir les prix des dépenses")
            for nom in st.session_state.selected_depenses:
                prix = st.number_input(f"Prix (€) pour {nom}", min_value=0.0, step=0.1, key=f"prix_{nom}")
                prix_depenses.append(prix)
                total_depenses += prix
                st.write(f"Prix : {prix:.2f} €")
            st.write(f"**Total des dépenses : {total_depenses:.2f} €**")
        submit_button = st.form_submit_button("Enregistrer les dépenses")
        if submit_button and st.session_state.show_prix_depenses:
            if not st.session_state.selected_depenses or not all(p > 0 for p in prix_depenses):
                st.error("Veuillez entrer des prix valides pour toutes les dépenses.")
            else:
                date_str = date.strftime("%Y-%m-%d")
                try:
                    if save_depense(date_str, st.session_state.selected_depenses, prix_depenses):
                        st.success("Dépenses ajoutées avec succès !")
                        st.session_state.show_prix_depenses = False
                        st.session_state.selected_depenses = []
                        st.session_state.depense_form_reset = True
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'enregistrement des dépenses.")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement des dépenses : {e}")
        if reset_button:
            st.session_state.show_prix_depenses = False
            st.session_state.selected_depenses = []
            st.session_state.depense_form_reset = True
            if "depense_noms" in st.session_state:
                st.session_state.depense_noms = ""
            for nom in st.session_state.get("selected_depenses", []):
                if f"prix_{nom}" in st.session_state:
                    st.session_state[f"prix_{nom}"] = 0.0
            st.rerun()

    st.header("Supprimer une dépense")
    with st.form(key="delete_depense_form"):
        depense_id = st.number_input("ID de la dépense", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la dépense")
        if delete_button:
            try:
                if delete_depense(depense_id):
                    st.success("Dépense supprimée avec succès !")
                else:
                    st.error("Dépense non trouvée ou erreur lors de la suppression.")
            except Exception as e:
                st.error(f"Erreur lors de la suppression de la dépense : {e}")

elif selected_partie == "Gestion des données":
    st.header("Gestion des données")
    st.subheader("Télécharger les fichiers CSV")
    for file_name in ["clients.csv", "produits.csv", "ventes.csv", "depenses.csv"]:
        file_path = os.path.join("data", file_name)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"Télécharger {file_name}",
                    data=f,
                    file_name=file_name,
                    mime="text/csv"
                )
        else:
            st.warning(f"Fichier {file_name} non trouvé.")

    st.subheader("Charger des fichiers CSV")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    if uploaded_file:
        file_name = uploaded_file.name
        if file_name == "clients.csv":
            if upload_clients(uploaded_file):
                st.success("Clients mis à jour avec succès !")
            else:
                st.error("Erreur lors de la mise à jour des clients.")
        elif file_name == "produits.csv":
            if upload_produits(uploaded_file):
                st.success("Produits mis à jour avec succès !")
            else:
                st.error("Erreur lors de la mise à jour des produits.")
        elif file_name == "ventes.csv":
            if upload_ventes(uploaded_file):
                st.success("Ventes mises à jour avec succès !")
            else:
                st.error("Erreur lors de la mise à jour des ventes.")
        elif file_name == "depenses.csv":
            if upload_depenses(uploaded_file):
                st.success("Dépenses mises à jour avec succès !")
            else:
                st.error("Erreur lors de la mise à jour des dépenses.")
        else:
            st.error("Nom de fichier non reconnu. Utilisez : clients.csv, produits.csv, ventes.csv, ou depenses.csv.")

elif selected_partie == "Statistiques":
    st.header("Statistiques")
    st.subheader("Évolution du bénéfice cumulé")
    try:
        fig = plot_benefice_evolution()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Aucun graphique généré pour le bénéfice.")
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")
    
    try:
        dernier_benefice, derniere_date = get_dernier_benefice()
        if derniere_date:
            couleur = "green" if dernier_benefice >= 0 else "red"
            st.markdown(
                f"<h3 style='color:{couleur}'>Bénéfice au {derniere_date.strftime('%Y-%m-%d')} : {dernier_benefice:.2f} €</h3>",
                unsafe_allow_html=True
            )
        else:
            st.write("Aucune donnée disponible pour calculer le bénéfice.")
    except Exception as e:
        st.error(f"Erreur lors du calcul du bénéfice : {e}")
    
    st.subheader("Chiffre d’affaires et dépenses par mois")
    show_bar_plot = st.checkbox("Afficher le graphique des ventes et dépenses")
    if show_bar_plot:
        try:
            current_date = datetime.now()
            default_months = [
                (current_date - relativedelta.months(i)).strftime("%B %Y")
                for i in range(2, -1, -1)
            ]
            ventes = load_ventes_cache(_invalidate=True)
            depenses = load_depenses_cache(_invalidate=True)
            all_dates = []
            if not ventes.empty:
                ventes["Date"] = pd.to_datetime(ventes["Date"], errors="coerce")
                all_dates.extend(ventes["Date"].extend(ventes["Date"].dropna().tolist()))
            if not depenses.empty:
                depenses["Date"] = pd.to_datetime(depenses["Date"], errors="coerce")
                all_dates.extend(depenses["Date"].dropna().tolist())
            if all_dates:
                all_months = sorted(set(pd.to_datetime(all_dates).strftime("%B %Y")), reverse=True)
                other_months = [m for m in all_months if m not in default_months]
            else:
                all_months = []
                other_months = []
            st.write("Par défaut, les trois derniers mois sont affichés.")
            additional_months = st.multiselect(
                "Ajouter des mois antérieurs :",
                options=other_months,
                default=[],
                help="Sélectionnez les mois supplémentaires à inclure dans le graphique."
            )
            selected_months = default_months + additional_months
            selected_months = sorted(selected_months, key=lambda x: pd.to_datetime(x, format="%B %Y"))
            fig = plot_chiffre_affaires_vs_depenses(selected_months)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucun graphique généré pour les ventes et dépenses.")
        except Exception as e:
            st.error(f"Erreur lors de la génération du graphique : {e}")
    
    st.subheader("Chiffre d'affaires par produit")
    try:
        show_produit_plot = st.checkbox("Afficher le graphique du chiffre d'affaires par produit")
        if show_produit_plot:
            st.write("Sélectionnez une période (optionnel) :")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Date de début", value=None, key="produit_start")
            with col2:
                end_date = date_input("Date de fin", value=None, key="produit_end")
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
            if start_date and end_date and start_date > end_date:
                st.error("La date de début doit être antérieure à positieve la date de fin.")
            else:
                try:
                    fig = plot_chiffre_affaires_per_product(start_date_str, end_date_str)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Aucun tableau généré pour le chiffre d'affaires par produit")
                except:
                    pass
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")
    
    st.subheader("Chiffre d'affaires par client")
    try:
        show_client_plot = st.checkbox("Afficher le graphique du chiffre d'affaires par client")
        if show_client_plot:
            st.write("Sélectionnez une période (optionnel) :")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Date de début", value=None, key="client_start")
            with col2:
                end_date = st.date_input("Date de fin", value=None, key="client_end")
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
            if start_date and end_date and start_date > end_date:
                st.error("La date de début doit être antérieure à la date de fin.")
            else:
                try:
                    fig = plot_chiffre_affaires_per_client(start_date_str, end_date_str)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Aucun tableau généré pour le chiffre d'affaires par client.")
                except:
                    pass
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")
    
    st.subheader("Dépenses par type de dépense")

    try:
        show_depense_plot = st.checkbox("Afficher le graphique des dépenses par type")
        if show_depense_plot:
            st.write("Sélectionnez une période (optionnel) :")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Date de début", value=None, key="depense_start")
            with col2:
                end_date = st.date_input("Date de fin", value=None, key="depense_end")
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
            if start_date and end_date and start_date > end_date:
                st.error("La date de début doit être antérieure à la date de fin.")
            else:
                try:
                    fig = plot_depenses_per_name(start_date_str, end_date_str)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Aucun tableau généré pour les dépenses par type")
                except:
                    pass
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")