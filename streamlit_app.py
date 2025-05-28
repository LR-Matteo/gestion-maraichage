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

st.title("Gestion Maraîchage")

# Menu
sous_partie = ["Ventes", "Dépenses", "Clients", "Produits", "Statistiques", "Gestion des données"]
selected_parties = st.selectbox("Menu : ", sous_partie)

# Alerte pour sauvegarder les données
st.warning("⚠️ Important : Téléchargez vos fichiers CSV après chaque modification pour éviter de perdre vos données en cas de redémarrage de l’application.")

if selected_parties == "Clients":
    st.header("Liste des clients")
    show_clients = st.checkbox("Afficher la liste des clients")
    if show_clients:
        clients = load_clients_cache(_invalidate=True)
        if not clients.empty:
            st.dataframe(clients)
            # Bouton pour télécharger clients.csv
            csv = clients.to_csv(index=False)
            st.download_button(
                label="Télécharger clients.csv",
                data=csv,
                file_name="clients.csv",
                mime="text/csv"
            )
        else:
            st.write("Aucune donnée client à afficher.")
    
    # Formulaire pour ajouter un client
    st.header("Ajouter un client")
    with st.form(key="client_form"):
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email (optionnel)")
        telephone = st.text_input("Téléphone (optionnel)")
        submit_button = st.form_submit_button("Enregistrer le client")

        if submit_button:
            if save_client(nom, prenom, email, telephone):
                st.success("Client ajouté avec succès !")
                st.info("N’oubliez pas de télécharger clients.csv pour sauvegarder vos modifications.")
            else:
                st.error("Erreur lors de l'ajout du client")

    # Formulaire pour supprimer un client
    st.header("Supprimer un client")
    with st.form(key="delete_client_form"):
        nom_del = st.text_input("Nom du client")
        prenom_del = st.text_input("Prénom du client")
        delete_button = st.form_submit_button("Supprimer le client")

        if delete_button:
            if delete_client(nom_del, prenom_del):
                st.success("Client supprimé avec succès !")
                st.info("N’oubliez pas de télécharger clients.csv pour sauvegarder vos modifications.")
            else:
                st.error("Erreur lors de la suppression du client")

elif selected_parties == "Produits":
    st.header("Liste des produits")
    show_produits = st.checkbox("Afficher la liste des produits")
    if show_produits:
        produits = load_produits_cache(_invalidate=True)
        if not produits.empty:
            st.dataframe(produits)
            # Bouton pour télécharger produits.csv
            csv = produits.to_csv(index=False)
            st.download_button(
                label="Télécharger produits.csv",
                data=csv,
                file_name="produits.csv",
                mime="text/csv"
            )
        else:
            st.write("Aucune donnée produit à afficher.")
    
    # Formulaire pour ajouter un produit
    st.header("Ajouter un produit")
    with st.form(key="produit_form"):
        nom_produit = st.text_input("Nom du produit")
        prix_produit = st.number_input("Prix (€/kg)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Enregistrer le produit")

        if submit_button:
            if save_produit(nom_produit, prix_produit):
                st.success("Produit ajouté avec succès !")
                st.info("N’oubliez pas de télécharger produits.csv pour sauvegarder vos modifications.")
            else:
                st.error("Erreur lors de l'ajout du produit")

    # Formulaire pour supprimer un produit
    st.header("Supprimer un produit")
    with st.form(key="delete_produit_form"):
        produits = load_produits_cache()
        produit_options = {row["Nom"]: row["Nom"] for _, row in produits.iterrows()}
        nom_produit_del = st.selectbox("Produit à supprimer", list(produit_options.keys()))
        delete_button = st.form_submit_button("Supprimer le produit")

        if delete_button:
            if delete_produit(nom_produit_del):
                st.success("Produit supprimé avec succès !")
                st.info("N’oubliez pas de télécharger produits.csv pour sauvegarder vos modifications.")
            else:
                st.error("Erreur lors de la suppression du produit")

    # Formulaire pour modifier le prix
    st.header("Modifier le prix d’un produit")
    with st.form(key="modify_price_form"):
        produits = load_produits_cache()
        produit_options = {row["Nom"]: row["Nom"] for _, row in produits.iterrows()}
        nom_produit = st.selectbox("Produit à modifier", list(produit_options.keys()))
        nouveau_prix = st.number_input("Nouveau prix (€/kg)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Modifier le prix")

        if submit_button:
            if modificate_price(nom_produit, nouveau_prix):
                st.success("Prix modifié avec succès !")
                st.info("N’oubliez pas de télécharger produits.csv pour sauvegarder vos modifications.")
            else:
                st.error("Erreur lors de la modification du prix")

elif selected_parties == "Ventes":
    st.header("Liste des ventes")
    show_ventes = st.checkbox("Afficher la liste des ventes")
    if show_ventes:
        try:
            ventes = get_ventes_affichage()
            if not ventes.empty:
                st.write("Sélectionnez une vente pour voir les détails :")
                selected_ventes = []
                cols = st.columns([1, 2, 3, 2, 1])  # Vente_ID, Date, Client, Prix total, Sélection
                cols[0].write("Vente_ID")
                cols[1].write("Date")
                cols[2].write("Client")
                cols[3].write("Prix total (€)")
                cols[4].write("Détails")
                
                for index, row in ventes.iterrows():
                    with st.container():
                        cols = st.columns([1, 2, 3, 2, 1])
                        cols[0].write(row["Vente_ID"])
                        cols[1].write(row["Date"])
                        cols[2].write(row["Client"])
                        cols[3].write(f"{row['Prix total']:.2f}")
                        if cols[4].checkbox("Voir", key=f"detail_{row['Vente_ID']}"):
                            selected_ventes.append(row["Vente_ID"])
                
                # Afficher les détails pour les ventes sélectionnées
                for vente_id in selected_ventes:
                    st.subheader(f"Détails de la vente {vente_id}")
                    details = get_vente_details(vente_id)
                    if not details.empty:
                        st.dataframe(details)
                    else:
                        st.write("Aucun détail disponible pour cette vente.")
                
                # Bouton pour télécharger ventes.csv
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

    # Formulaire pour ajouter une vente
    st.header("Ajouter une vente")
    if "show_quantites" not in st.session_state:
        st.session_state.show_quantites = False
    if "selected_produits" not in st.session_state:
        st.session_state.selected_produits = []

    with st.form(key="vente_form"):
        date = st.date_input("Date de la vente")
        clients = load_clients_cache(_invalidate=True)
        client_options = [f"{row['Nom']} {row['Prénom']}" for _, row in clients.iterrows()]
        client_selection = st.selectbox("Client", client_options)
        
        produits = load_produits_cache(_invalidate=True)
        produit_options = list(produits["Nom"])
        temp_selected_produits = st.multiselect("Produits", produit_options, default=st.session_state.selected_produits)
        
        confirm_button = st.form_submit_button("Confirmer la sélection des produits")
        reset_button = st.form_submit_button("Réinitialiser le formulaire")

        if confirm_button and temp_selected_produits:
            st.session_state.show_quantites = True
            st.session_state.selected_produits = temp_selected_produits
        elif confirm_button:
            st.error("Veuillez sélectionner au moins un produit.")

        quantites = []
        prix_totaux = []
        total_commande = 0.0
        if st.session_state.show_quantites:
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
            if not st.session_state.selected_produits:
                st.error("Veuillez sélectionner au moins un produit.")
            else:
                client_nom, client_prenom = client_selection.split(" ", 1) if " " in client_selection else (client_selection, "")
                date_str = date.strftime("%Y-%m-%d")
                try:
                    if save_vente(date_str, client_nom, client_prenom, st.session_state.selected_produits, quantites, prix_totaux):
                        st.success("Vente ajoutée avec succès !")
                        st.info("N’oubliez pas de télécharger ventes.csv pour sauvegarder vos modifications.")
                        st.session_state.show_quantites = False
                        st.session_state.selected_produits = []
                    else:
                        st.error("Erreur lors de l'ajout de la vente")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement de la vente : {e}")

        if reset_button:
            st.session_state.show_quantites = False
            st.session_state.selected_produits = []
            st.rerun()

    # Formulaire pour supprimer une vente
    st.header("Supprimer une vente")
    with st.form(key="delete_vente_form"):
        vente_id = st.number_input("ID de la vente", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la vente")

        if delete_button:
            try:
                if delete_vente(vente_id):
                    st.success("Vente supprimée avec succès !")
                    st.info("N’oubliez pas de télécharger ventes.csv pour sauvegarder vos modifications.")
                else:
                    st.error("Erreur lors de la suppression de la vente")
            except Exception as e:
                st.error(f"Erreur lors de la suppression de la vente : {e}")

elif selected_parties == "Dépenses":
    st.header("Liste des dépenses")
    show_depenses = st.checkbox("Afficher")
    if show_depenses:
        try:
            depenses = get_depenses_affichage()
            if not depenses.empty:
                st.write("Sélectionnez une date pour voir les détails :")
                selected_dates = []
                cols = st.columns([3, 2, 1])  # Date, Total, Sélection
                cols[0].write("Date")
                cols[1].write("Total (€)")
                cols[2].write("Détails")
                
                for index, row in depenses.iterrows():
                    with st.container():
                        cols = st.columns([3, 2, 1])
                        cols[0].write(row["Date"])
                        cols[1].write(f"{row['Total']:.2f}")
                        if cols[2].checkbox("Voir", key=f"detail_depense_{row['Date']}"):
                            selected_dates.append(row["Date"])
                
                # Afficher les détails pour les dates sélectionnées
                for date in selected_dates:
                    st.subheader(f"Détails des dépenses du {date}")
                    details = get_depense_details(date)
                    if not details.empty:
                        st.dataframe(details)
                    else:
                        st.write("Aucun détail disponible pour cette date.")
                
                # Bouton pour télécharger depenses.csv
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

    # Formulaire pour ajouter une dépense
    st.header("Ajouter une dépense")
    if "show_prix_depenses" not in st.session_state:
        st.session_state.show_prix_depenses = False
    if "selected_depenses" not in st.session_state:
        st.session_state.selected_depenses = []

    with st.form(key="depense_form"):
        date = st.date_input("Date de la dépense")
        noms_depenses = st.text_input("Noms des dépenses (séparés par des virgules)", placeholder="Engrais, Arrosage, Semences")

        confirm_button = st.form_submit_button("Confirmer la sélection des dépenses")
        reset_button = st.form_submit_button("Réinitialiser le formulaire")

        if confirm_button and noms_depenses:
            temp_selected_depenses = [nom.strip() for nom in noms_depenses.split(",") if nom.strip()]
            if temp_selected_depenses:
                st.session_state.show_prix_depenses = True
                st.session_state.selected_depenses = temp_selected_depenses
            else:
                st.error("Veuillez entrer au moins un nom de dépense valide.")
        elif confirm_button:
            st.error("Veuillez entrer au moins un nom de dépense.")

        prix_depenses = []
        total_depenses = 0.0
        if st.session_state.show_prix_depenses:
            st.subheader("Saisir les prix des dépenses")
            for nom in st.session_state.selected_depenses:
                st.write(f"**{nom}**")
                prix = st.number_input(f"Prix (€) pour {nom}", min_value=0.0, step=0.1, key=f"prix_{nom}")
                prix_depenses.append(prix)
                total_depenses += prix
                st.write(f"Prix : {prix:.2f} €")
            
            st.write(f"**Total des dépenses : {total_depenses:.2f} €**")

        submit_button = st.form_submit_button("Enregistrer les dépenses")

        if submit_button and st.session_state.show_prix_depenses:
            if not st.session_state.selected_depenses:
                st.error("Aucune dépense sélectionnée.")
            else:
                date_str = date.strftime("%Y-%m-%d")
                try:
                    success = True
                    for nom, prix in zip(st.session_state.selected_depenses, prix_depenses):
                        if not save_depense(date_str, nom, prix):
                            success = False
                            st.error(f"Erreur lors de l'enregistrement de la dépense '{nom}'.")
                    if success:
                        st.success("Dépenses ajoutées avec succès !")
                        st.info("N’oubliez pas de télécharger depenses.csv pour sauvegarder vos modifications.")
                        st.session_state.show_prix_depenses = False
                        st.session_state.selected_depenses = []
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement des dépenses : {e}")

        if reset_button:
            st.session_state.show_prix_depenses = False
            st.session_state.selected_depenses = []
            st.rerun()

    # Formulaire pour supprimer une dépense
    st.header("Supprimer une dépense")
    with st.form(key="delete_depense_form"):
        depense_id = st.number_input("ID de la dépense", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la dépense")

        if delete_button:
            try:
                if delete_depense(depense_id):
                    st.success("Dépense supprimée avec succès !")
                    st.info("N’oubliez pas de télécharger depenses.csv pour sauvegarder vos modifications.")
                else:
                    st.error("Erreur lors de la suppression de la dépense")
            except Exception as e:
                st.error(f"Erreur lors de la suppression de la dépense : {e}")

elif selected_parties == "Gestion des données":
    st.header("Gestion des données")
    st.write("Utilisez cette section pour charger vos fichiers CSV sauvegardés ou télécharger les données actuelles.")

    # Upload des fichiers CSV
    st.subheader("Charger des fichiers CSV")
    with st.form(key="upload_form"):
        client_file = st.file_uploader("Charger clients.csv", type="csv")
        produit_file = st.file_uploader("Charger produits.csv", type="csv")
        vente_file = st.file_uploader("Charger ventes.csv", type="csv")
        depense_file = st.file_uploader("Charger depenses.csv", type="csv")
        submit_button = st.form_submit_button("Charger les fichiers")

        if submit_button:
            try:
                success = True
                if client_file:
                    if upload_clients(client_file):
                        st.success("clients.csv chargé avec succès !")
                    else:
                        success = False
                        st.error("Erreur lors du chargement de clients.csv")
                if produit_file:
                    if upload_produits(produit_file):
                        st.success("produits.csv chargé avec succès !")
                    else:
                        success = False
                        st.error("Erreur lors du chargement de produits.csv")
                if vente_file:
                    if upload_ventes(vente_file):
                        st.success("ventes.csv chargé avec succès !")
                    else:
                        success = False
                        st.error("Erreur lors du chargement de ventes.csv")
                if depense_file:
                    if upload_depenses(depense_file):
                        st.success("depenses.csv chargé avec succès !")
                    else:
                        success = False
                        st.error("Erreur lors du chargement de depenses.csv")
                if success and any([client_file, produit_file, vente_file, depense_file]):
                    st.info("Données chargées. Testez l’application pour vérifier.")
                elif not any([client_file, produit_file, vente_file, depense_file]):
                    st.warning("Aucun fichier sélectionné.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des fichiers : {e}")

    # Téléchargement de tous les CSV
    st.subheader("Télécharger tous les fichiers CSV")
    with st.form(key="download_all_form"):
        st.write("Cliquez pour télécharger tous les fichiers CSV actuels.")
        download_button = st.form_submit_button("Télécharger tous les CSV")

        if download_button:
            try:
                clients = load_clients_cache(_invalidate=True)
                produits = load_produits_cache(_invalidate=True)
                ventes = load_ventes_cache(_invalidate=True)
                depenses = load_depenses_cache(_invalidate=True)

                st.download_button(
                    label="Télécharger clients.csv",
                    data=clients.to_csv(index=False),
                    file_name="clients.csv",
                    mime="text/csv",
                    key="download_clients"
                )
                st.download_button(
                    label="Télécharger produits.csv",
                    data=produits.to_csv(index=False),
                    file_name="produits.csv",
                    mime="text/csv",
                    key="download_produits"
                )
                st.download_button(
                    label="Télécharger ventes.csv",
                    data=ventes.to_csv(index=False),
                    file_name="ventes.csv",
                    mime="text/csv",
                    key="download_ventes"
                )
                st.download_button(
                    label="Télécharger depenses.csv",
                    data=depenses.to_csv(index=False),
                    file_name="depenses.csv",
                    mime="text/csv",
                    key="download_depenses"
                )
            except Exception as e:
                st.error(f"Erreur lors du téléchargement des fichiers : {e}")




elif selected_parties == "Statistiques":
    st.header("Statistiques")
    
    # Graphique : Évolution du bénéfice
    st.subheader("Évolution du bénéfice cumulé")
    try:
        fig = plot_benefice_evolution()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Aucun graphique généré pour le bénéfice.")
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")
    
    # Afficher le dernier bénéfice
    try:
        dernier_benefice, derniere_date = get_dernier_benefice()
        if derniere_date:
            couleur = "green" if dernier_benefice >= 0 else "red"
            st.markdown(
                f"<h3 style='color:{couleur};'>Bénéfice au {derniere_date.strftime('%Y-%m-%d')} : {dernier_benefice:.2f} €</h3>",
                unsafe_allow_html=True
            )
        else:
            st.write("Aucune donnée disponible pour calculer le bénéfice.")
    except Exception as e:
        st.error(f"Erreur lors du calcul du bénéfice : {e}")

    # Graphique : Chiffre d'affaires et dépenses par mois
    st.subheader("Chiffre d'affaires et dépenses par mois")
    show_bar_plot = st.checkbox("Afficher le graphique des ventes et dépenses")
    if show_bar_plot:
        # Calculer les trois derniers mois par défaut
        current_date = datetime.now()
        default_months = [
            (current_date - relativedelta(months=i)).strftime("%B %Y")
            for i in range(2, -1, -1)  # Mars 2025, Février 2025, Janvier 2025
        ]

        # Obtenir tous les mois disponibles dans les données
        ventes = load_ventes_cache(_invalidate=True)
        depenses = load_depenses_cache(_invalidate=True)
        all_dates = []
        if not ventes.empty:
            ventes["Date"] = pd.to_datetime(ventes["Date"], errors="coerce")
            all_dates.extend(ventes["Date"].dropna().tolist())
        if not depenses.empty:
            depenses["Date"] = pd.to_datetime(depenses["Date"], errors="coerce")
            all_dates.extend(depenses["Date"].dropna().tolist())
        
        if all_dates:
            all_months = sorted(set(pd.to_datetime(all_dates).strftime("%B %Y")), reverse=True)
            # Inclure les mois antérieurs (excluant les trois derniers)
            other_months = [m for m in all_months if m not in default_months]
        else:
            all_months = []
            other_months = []

        # Sélection des mois à afficher
        st.write("Par défaut, les trois derniers mois sont affichés.")
        additional_months = st.multiselect(
            "Ajouter des mois antérieurs :",
            options=other_months,
            default=[],
            help="Sélectionnez les mois supplémentaires à inclure dans le graphique."
        )

        # Combiner les mois sélectionnés
        selected_months = default_months + additional_months
        selected_months = sorted(selected_months, key=lambda x: pd.to_datetime(x, format="%B %Y"))

        try:
            fig = plot_chiffre_affaires_vs_depenses(selected_months)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucun graphique généré pour les ventes et dépenses.")
        except Exception as e:
            st.error(f"Erreur lors de la génération du graphique : {e}")
    # Graphique : Chiffre d'affaires par produit
    st.subheader("Chiffre d'affaires par produit")
    show_produit_plot = st.checkbox("Afficher le graphique du chiffre d'affaires par produit")
    if show_produit_plot:
        # Sélection de la période
        st.write("Sélectionnez une période (optionnel) :")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Date de début", value=None, key="produit_start")
        with col2:
            end_date = st.date_input("Date de fin", value=None, key="produit_end")

        # Convertir les dates en chaînes si non nulles
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

        # Vérifier la validité des dates
        if start_date and end_date and start_date > end_date:
            st.error("La date de début doit être antérieure à la date de fin.")
        else:
            try:
                fig = plot_chiffre_affaires_per_product(start_date_str, end_date_str)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucun graphique généré pour le chiffre d'affaires par produit.")
            except Exception as e:
                st.error(f"Erreur lors de la génération du graphique : {e}")

    # Graphique : Chiffre d'affaires par client
    st.subheader("Chiffre d'affaires par client")
    show_client_plot = st.checkbox("Afficher le graphique du chiffre d'affaires par client")
    if show_client_plot:
        # Sélection de la période
        st.write("Sélectionnez une période (optionnel) :")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Date de début", value=None, key="client_start")
        with col2:
            end_date = st.date_input("Date de fin", value=None, key="client_end")

        # Convertir les dates en chaînes si non nulles
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

        # Vérifier la validité des dates
        if start_date and end_date and start_date_str:
            st.error("La date de début doit être antérieure à la date de fin.")
        else:
            try:
                fig = plot_chiffre_affaires_per_client(start_date_str, end_date_str)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucun tableau généré pour le chiffre d'affaires par client.")
            except Exception as e:
                st.error(f"Erreur lors de la génération du graphique : {e}")

    # Graphique : Dépenses par nom
    st.subheader("Dépenses par type de dépense")
    show_depense_plot = st.checkbox("Afficher le graphique des dépenses par type de")
    if show_depense_plot:
        # Sélection de la période
        st.write("Sélectionnez une période (optionnel) :")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Date de début", value=None, key="depense_start")
        with col2:
            end_date = st.date_input("Date de fin", value=None, key="depense_end")

        # Convertir les dates en chaînes si non nulles
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        # Vérifier la validité des dates
        if start_date and end_date and start_date_str > end_date_str:
            st.error("La date de début doit être antérieure à la date de fin.")
        else:
            try:
                fig = plot_depenses_per_name(start_date_str, end_date_str)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucun tableau généré pour les dépenses par type")
            except Exception as e:
                st.error(f"Erreur lors de la génération du graphique : {e}")