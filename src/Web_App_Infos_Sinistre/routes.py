"""
URL routing and request handling for the Flask application.

Routes are URLs that users can visit (like /index or /form_projet_input).
Each route has a function that decides what to display when someone visits that URL.

Routes are like "addresses" for your web application!
"""
import json

from flask import Flask, render_template, flash, redirect, session, request
# Flask: The main framework
# render_template: Converts HTML template files into complete web pages
# flash: Displays temporary messages to users (like "Success!" or "Error!")
# redirect: Sends users to a different URL after an action (like after form submission)
from flask_cors import CORS

from datetime import datetime, timedelta
from functools import wraps

import requests
# HTTP framework

from config import Config, URI_AUTH_SERVICE, URI_SERV_DATA, root_data, root_auth  # Import configuration settings
from forms import InfosInputForm, FormAjoutReclamation, FormCollecteDonnees
from util import validate_search_inputs, build_search_payload

# Create the Flask application object
# This object represents your entire web application
app = Flask(__name__)

# Tell Flask to use our Config class for settings
# This loads SECRET_KEY and other configuration values
app.config.from_object(Config)

CORS(app)


# Décorateur pour vérifier que l'utilisateur possède un token valide
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'auth_token' not in session:
            flash('Veuillez d\'abord vous connecter.', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    """Route d'accueil - affiche les options de login ou recherche"""
    return render_template('index.html', api_docs_url=root_data,
                           api_auth_docs_url=root_auth)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route de connexion - envoie les identifiants au service d'auth"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validation basique
        if not username or not password:
            flash('Nom d\'utilisateur et mot de passe requis.', 'danger')
            return redirect('/login')

        try:
            # Envoi des identifiants au service d'authentification
            auth_payload = {
                'username': username,
                'password': password
            }
            auth_response = requests.post(URI_AUTH_SERVICE, json=auth_payload)

            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                token = auth_data.get('token')

                if token:
                    # Stockage du token en session
                    session['auth_token'] = token
                    session['username'] = username
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(hours=24)

                    flash(f'Bienvenue {username}!', 'success')
                    return redirect('/infos_sinistre')
                else:
                    flash('Identifiants invalides.', 'danger')

        except requests.exceptions.RequestException as e:
            flash(f'Erreur de connexion au service d\'authentification: {str(e)}', 'danger')

        return redirect('/login')

    return render_template('login.html')


@app.route('/infos_sinistre', methods=['GET', 'POST'])
@token_required
def form_info_sinistre():
    """Route de recherche d'incident - affiche le formulaire de recherche"""
    inputForm = InfosInputForm()
    if inputForm.validate_on_submit():
        # Validation des inputs selon les règles métier
        if not validate_search_inputs(inputForm):
            flash('Vous devez fournir soit un ID de réclamation, soit (date + heure + coordonnées).', 'danger')
            return render_template('form_infos_input.html', form=inputForm)

        # Préparation du payload
        payload = build_search_payload(inputForm)

        # Stockage temporaire des données de recherche en session
        session['search_payload'] = payload

        try:
            # Envoi de la requête GET à serv_data avec le token
            headers = {'Authorization': f'Bearer {session.get("auth_token")}'}
            response = requests.get(
                URI_SERV_DATA['chercher_incident'],
                json=payload,
                headers=headers
            )

            # Gestion des codes de réponse
            if response.status_code == 200 or (response.status_code == 210 and payload['id_reclamation'] is None):
                # Incident trouvé et complet
                resultat = response.json()
                # Stockage temporaire du résultat de la recherche en session
                session['incident_data'] = resultat
                return redirect('/afficher_resultat')

            elif response.status_code == 210:
                # Incident trouvé mais ID réclamation manquant
                resultat = response.json()
                session['incident_data'] = resultat
                return redirect('/ajouter_reclamation')

            elif response.status_code == 404:
                # Incident non trouvé - proposer la création
                return redirect('/collecter_donnees')

            else:
                flash(f'Erreur serveur (code {response.status_code}).', 'danger')

        except requests.exceptions.RequestException as e:
            flash(f'Erreur de connexion à serv_data: {str(e)}', 'danger')

    return render_template('form_infos_input.html', form=inputForm)


@app.route('/afficher_resultat', methods=['GET'])
@token_required
def afficher_resultat():
    """Route pour afficher les résultats d'une recherche/création"""
    incident_data = session.get('incident_data')

    if not incident_data:
        flash('Aucune donnée à afficher. Veuillez rechercher à nouveau.', 'warning')
        return redirect('/infos_sinistre')

    return render_template('infos_output.html', data=incident_data)


@app.route('/ajouter_reclamation', methods=['GET', 'POST'])
@token_required
def ajouter_reclamation():
    """Route pour ajouter un ID réclamation à un incident existant"""
    incident_data = session.get('incident_data')
    search_payload = session.get('search_payload')

    if not incident_data or not search_payload:
        flash('Données manquantes. Veuillez rechercher à nouveau.', 'warning')
        return redirect('/infos_sinistre')

    form = FormAjoutReclamation()

    if form.validate_on_submit():
        option = form.options.data

        # On ajoute l'identifiant de réclamation dans l'incident SI
        # l'utilisateur choisit cette option.
        if option == 'Ajouter':
            try:
                # Préparation du payload et du header pour le PATCH
                patch_payload = {
                    **search_payload,
                    'id_incident': incident_data.get('id_incident')
                }
                headers = {'Authorization': f'Bearer {session.get("auth_token")}'}

                # Envoi de la requête PATCH
                patch_response = requests.patch(
                    URI_SERV_DATA['ajouter_reclamation'],
                    json=patch_payload,
                    headers=headers
                )

                # Gestion des codes de réponse
                if patch_response.status_code == 200:
                    flash('ID réclamation ajouté avec succès.', 'success')
                    session['incident_data'] = patch_response.json()
                else:
                    flash(f'Erreur lors de l\'ajout (code {patch_response.status_code}).', 'danger')

            except requests.exceptions.RequestException as e:
                flash(f'Erreur de connexion: {str(e)}', 'danger')

        # Dans tous les cas, afficher le résultat
        return redirect('/afficher_resultat')

    return render_template('form_ajout_reclamation.html',
                           form=form,
                           id_reclamation=search_payload["id_reclamation"],
                           id_incident = incident_data.get('id_incident'))


@app.route('/collecter_donnees', methods=['GET', 'POST'])
@token_required
def collecter_donnees():
    """Route pour collecter les données d'un nouvel incident"""
    search_payload = session.get('search_payload')
    if not search_payload:
        flash('Données manquantes. Veuillez rechercher à nouveau.', 'warning')
        return redirect('/infos_sinistre')

    form = FormCollecteDonnees()

    if form.validate_on_submit():
        option = form.options.data

        if option == 'Oui' and None not in search_payload.values():
            try:
                # Envoi de la requête POST pour créer l'incident
                headers = {'Authorization': f'Bearer {session.get("auth_token")}'}
                post_response = requests.post(
                    URI_SERV_DATA['creer_incident'],
                    json=search_payload,
                    headers=headers
                )

                if post_response.status_code == 201:
                    resultat = post_response.json()
                    session['incident_data'] = resultat
                    flash('Incident créé et données collectées.', 'success')
                    return redirect('/afficher_resultat')
                else:
                    flash(f'Erreur lors de la création (code {post_response.status_code}).', 'danger')

            except requests.exceptions.RequestException as e:
                flash(f'Erreur de connexion: {str(e)}', 'danger')

        elif None in search_payload.values():
            # Valeurs manquantes dans le formulaire de recherche
            flash('Valeurs manquantes dans le formulaire de recherche.', 'info')
            return redirect('/infos_sinistre')
        else:
            # L'utilisateur a choisi "Non"
            flash('Opération annulée.', 'info')
            return redirect('/infos_sinistre')

    return render_template('form_collecte_donnees.html', form=form)

# route utilisée pour garder les services déployés en ligne actifs (spin
# down automatique par défaut)
@app.route('/health', methods=['GET'])
def health():
    return 'ok', 200
