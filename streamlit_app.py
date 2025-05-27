import streamlit as st 
import pandas as pd
from client_fonction import save_client, delete_client, load_clients_cache
from produit_fonction import save_produit, delete_produit, modificate_price, load_produits_cache
from ventes_fonction import save_vente, delete_vente, load_ventes_cache, get_ventes_affichage
from depenses_fonction import save_depense, delete_depense, load_depenses_cache
from statistiques_fonction import get_dernier_benefice, plot_benefice_evolution, datetime, relativedelta, plot_chiffre_affaires_vs_depenses
from statistiques_fonction import plot_chiffre_affaires_per_client, plot_depenses_per_name, plot_chiffre_affaires_per_product

st.title("Gestion maraichage")

sous_partie = ["Ventes", "Dépenses", "Clients", "Produits", "Statistiques"]

selected_parties = st.selectbox("Menu : ", sous_partie)

if selected_parties == "Clients":
    st.header("Liste des clients")
    show_clients = st.checkbox("Afficher la liste des clients")
    if show_clients:
        clients = load_clients_cache()
        if not clients.empty:
            st.dataframe(clients)
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
            else:
                st.error("Erreur lors de la suppression du client")

elif selected_parties == "Produits":
    st.header("Liste des produits")
    show_produits = st.checkbox("Afficher la liste des produits")
    if show_produits:
        produits = load_produits_cache(_invalidate=True)  # Forcer le rechargement
        if not produits.empty:
            st.dataframe(produits)
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
            else:
                st.error("Erreur lors de l'ajout du produit")

    # Formulaire pour supprimer un produit
    st.header("Supprimer un produit")
    with st.form(key="delete_produit_form"):
        nom_produit_del = st.text_input("Nom du produit")
        delete_button = st.form_submit_button("Supprimer le produit")

        if delete_button:
            if delete_produit(nom_produit_del):
                st.success("Produit supprimé avec succès !")
            else:
                st.error("Erreur lors de la suppression du produit")

    # Formulaire pour modifier le prix d'un produit
    st.header("Modifier le prix d'un produit")
    with st.form(key="modify_price_form"):
        produits = load_produits_cache()
        produit_options = {row["Nom"]: row["Nom"] for _, row in produits.iterrows()}
        nom_produit = st.selectbox("Sélectionner un produit", list(produit_options.keys()))
        nouveau_prix = st.number_input("Nouveau prix (€/kg)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Modifier le prix")

        if submit_button:
            if modificate_price(nom_produit, nouveau_prix):
                st.success("Prix modifié avec succès !")
            else:
                st.error("Erreur lors de la modification du prix")


elif selected_parties == "Ventes":
    st.header("Liste des ventes")
    show_ventes = st.checkbox("Afficher la liste des ventes")
    if show_ventes:
        try:
            ventes_df = get_ventes_affichage()
            if not ventes_df.empty:
                st.dataframe(ventes_df)
            else:
                st.write("Aucune donnée vente à afficher.")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage des ventes : {e}")

    # Formulaire pour ajouter une vente
    st.header("Ajouter une vente")
    with st.form(key="vente_form"):
        date = st.date_input("Date de la vente")
        clients = load_clients_cache()
        client_options = [f"{row['Nom']} {row['Prénom']}" for _, row in clients.iterrows()]
        client_selection = st.selectbox("Client", client_options)
        produits = load_produits_cache()
        produit_options = {row["Nom"]: row["Nom"] for _, row in produits.iterrows()}
        produit_nom = st.selectbox("Produit", list(produit_options.keys()))
        quantite = st.number_input("Quantité (kg)", min_value=0.0, step=0.1)
        
        # Calculer le prix total
        prix_unitaire = produits[produits["Nom"] == produit_nom]["Prix (au Kg)"].iloc[0] if produit_nom in produit_options else 0.0
        prix_total = quantite * prix_unitaire
        st.write(f"Prix total (€) : {prix_total:.2f}")
        submit_button = st.form_submit_button("Enregistrer la vente")

        if submit_button:
            # Extraire nom et prénom du client
            client_nom, client_prenom = client_selection.split(" ", 1) if " " in client_selection else (client_selection, "")
            date_str = date.strftime("%Y-%m-%d")
            if save_vente(date_str, client_nom, client_prenom, produit_nom, quantite, prix_total):
                st.success("Vente ajoutée avec succès !")
            else:
                st.error("Erreur lors de l'ajout de la vente")

    # Formulaire pour supprimer une vente
    st.header("Supprimer une vente")
    with st.form(key="delete_vente_form"):
        vente_id = st.number_input("ID de la vente", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la vente")

        if delete_button:
            if delete_vente(vente_id):
                st.success("Vente supprimée avec succès !")
            else:
                st.error("Erreur lors de la suppression de la vente")

elif selected_parties == "Dépenses":
    st.header("Liste des dépenses")
    show_depenses = st.checkbox("Afficher la liste des dépenses")
    if show_depenses:
        depenses = load_depenses_cache(_invalidate=True)
        if not depenses.empty:
            st.dataframe(depenses)
        else:
            st.write("Aucune donnée dépense à afficher.")

    # Formulaire pour ajouter une dépense
    st.header("Ajouter une dépense")
    with st.form(key="depense_form"):
        date = st.date_input("Date de la dépense")
        nom_depense = st.text_input("Nom de la dépense")
        prix_depense = st.number_input("Prix (€)", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("Enregistrer la dépense")

        if submit_button:
            date_str = date.strftime("%Y-%m-%d")
            if save_depense(date_str, nom_depense, prix_depense):
                st.success("Dépense ajoutée avec succès !")
            else:
                st.error("Erreur lors de l'ajout de la dépense")

    # Formulaire pour supprimer une dépense
    st.header("Supprimer une dépense")
    with st.form(key="delete_depense_form"):
        depense_id = st.number_input("ID de la dépense", min_value=1, step=1)
        delete_button = st.form_submit_button("Supprimer la dépense")

        if delete_button:
            if delete_depense(depense_id):
                st.success("Dépense supprimée avec succès !")
            else:
                st.error("Erreur lors de la suppression de la dépense")


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