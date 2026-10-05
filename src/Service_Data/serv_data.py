'''
Ce service reçoit les données entrantes (lat + long + date + heure +
numéro de réclamation) et coordonne Service_DAO et Service_Collecte afin
de vérifier si un enregistrement existe déjà, collecter les données et
les enregistrer (le cas échéant)
'''
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests, jwt, os
from flasgger import Swagger

from config import URI_SERV_COLLECTE, URI_SERV_DAO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'le bonheur est dans le pré'
app.config['SWAGGER'] = {
    'title' : 'Info-Sinistre-Auto - Service Data',
    'version' : '1.0'
}
swagger = Swagger(app)

CORS(app)


# FONCTIONS UTILITAIRES

def recuperer_token_header():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]  # retourner uniquement le token
    return None

def verifier_token(token):
    try:
        jwt.decode(token, key=app.config['SECRET_KEY'], algorithms='HS256')
        return True
    except jwt.InvalidTokenError:
        return False


# ROUTES
@app.route('/')
@app.route('/index')
def index():
    return redirect('/apidocs')

@app.route('/data', methods=['GET'])
def chercher_incident():
    """
    Recherche d'un document en fonction des informations du dossier
    ---
    parameters:
      - in: header
        name: token
        type: string
        required: true
        description: Clé d'autentification
      - in: body
        name: payload
        description: Les informations concernant le dossier (id_reclamation, date, heure, latitude, longitude)
        schema:
            type: object
            properties:
                id_reclamation:
                    type: string
                    example: "ABC123"
                date:
                    type: string
                    format: date
                    example: "2025-12-31"
                heure:
                    type: string
                    format: time
                    example: "19:15"
                latitude:
                    type: number
                    format: float
                    example: 49.914
                longitude:
                    type: number
                    format: float
                    example: 74.963
    responses:
        200:
            description: Dossier trouvé avec le id_reclamation
        210:
            description: Dossier trouvé avec les informations de l'incident (date, heure, latitude, longitude)
        401:
            description: Non-autorisé. Token manquant, invalide ou expiré
        404:
            description: Dossier non trouvé
    """

    # vérifier le token
    token = recuperer_token_header()
    if not verifier_token(token):
        return jsonify({"message": "Erreur 401: Unauthorized. Token non fourni, invalide ou expiré"}), 401

    payload = request.get_json()
    response = requests.get(URI_SERV_DAO['chercher_incident'], json=payload)
    resultat = response.json()
    code = response.status_code
    return resultat, code

@app.route('/data/reclamation', methods=['PATCH'])
def ajouter_reclamation():
    """
    Ajouter un id_reclamation à un incident existant
    ---
    parameters:
      - in: header
        name: token
        type: string
        required: true
        description: Clé d'autentification
      - in: body
        name: payload
        description: id_reclamation, id_incident
        schema:
            type: object
            properties:
                id_reclamation:
                    type: string
                    example: "ABC123"
                id_incident:
                    type: number
                    format: integer
                    example: 1
    responses:
        200:
            description: Id_reclamation ajouté à l'incident
        401:
            description: Non-autorisé. Token manquant, invalide ou expiré
    """

    """Requête PATCH à serv_DAO pour ajouter id_reclamation à l'incident
    correspondant (si l'incident n'est pas trouvé avec id_reclamation
    mais qu'il est trouvé avec date/heure/lieu) """

    # vérifier le token
    token = recuperer_token_header()
    if not verifier_token(token):
        return jsonify({"message": "Erreur 401: Unauthorized. Token non fourni, invalide ou expiré"}), 401

    payload = request.get_json()
    id_reclamation = payload["id_reclamation"]
    id_incident = payload["id_incident"]

    # requête PATCH afin d'ajouter le id à la liste
    confirmation = requests.patch(URI_SERV_DAO['ajouter_reclamation'].format(id_incident),
                                  json={"id_reclamation":id_reclamation}).json() #la méthode format insère id_incident dans le placeholder {}
    return confirmation, 200

@app.route('/data', methods=['POST'])
def creer_incident():
    """
    Ajouté un nouveau document en fonction des informations du dossier
    ---
    parameters:
      - in: header
        name: token
        type: string
        required: true
        description: Clé d'autentification
      - in: body
        name: payload
        description: Les informations concernant le dossier (id_reclamation, date, heure, latitude, longitude)
        schema:
            type: object
            properties:
                id_reclamation:
                    type: string
                    example: "ABC123"
                date:
                    type: string
                    format: date
                    example: "2025-12-31"
                heure:
                    type: string
                    format: time
                    example: "19:15"
                latitude:
                    type: number
                    format: float
                    example: 49.914
                longitude:
                    type: number
                    format: float
                    example: 74.963
    responses:
        201:
            description: Dossier ajouté
        401:
            description: Non-autorisé. Token manquant, invalide ou expiré
    """

    # vérifier le token
    token = recuperer_token_header()
    if not verifier_token(token):
        return jsonify({"message": "Erreur 401: Unauthorized. Token non fourni, invalide ou expiré"}), 401

    # inputs utilisateur
    payload = request.get_json()
    latitude = payload["latitude"]
    longitude = payload["longitude"]
    date = payload["date"]
    heure = payload["heure"]

    # Appel au service de collecte de données
    info_meteo = requests.get(URI_SERV_COLLECTE, json={
        "latitude": latitude,
        "longitude": longitude,
        "date": date,
        "heure": heure
    }).json()

    # Consolidation des données utilisateur et des informations
    # collectées dans un document JSON
    payload['id_reclamation'] = [payload['id_reclamation']]
    info_sinistre = {'info_dossier': payload,
                     'info_meteo': info_meteo}

    # Envoi du document à Service_DAO afin de l'insérer dans la
    # collection (POST)
    nouvel_incident = requests.post(URI_SERV_DAO['creer_incident'], json=info_sinistre).json()

    # Réponse à la requête entrante avec le document JSON
    return nouvel_incident, 201

@app.route('/data', methods=['PUT'])
def modifier_incident():
    """
    Modifier un document existant
    ---
    parameters:
      - in: header
        name: token
        type: string
        required: true
        description: Clé d'autentification
      - in: body
        name: payload
        description: Les informations concernant le dossier (id_reclamation, date, heure, latitude, longitude)
        schema:
            type: object
            properties:
                id_reclamation:
                    type: string
                    example: "ABC123"
                date:
                    type: string
                    format: date
                    example: "2025-12-31"
                heure:
                    type: string
                    format: time
                    example: "19:15"
                latitude:
                    type: number
                    format: float
                    example: 49.914
                longitude:
                    type: number
                    format: float
                    example: 74.963
    responses:
        201:
            description: Dossier modifié
        401:
            description: Non-autorisé. Token manquant, invalide ou expiré
    """

    # vérifier le token
    token = recuperer_token_header()
    if not verifier_token(token):
        return jsonify({"message": "Erreur 401: Unauthorized. Token non fourni, invalide ou expiré"}), 401

    # inputs utilisateur
    payload = request.get_json()

    # Envoi du document à Service_DAO afin de modifier un enregistrement existant de la collection
    incident_modifie = requests.put(URI_SERV_DAO['modifier_incident'], json=payload).json()

    # Réponse à la requête entrante avec le document JSON
    return incident_modifie, 201

# route utilisée pour garder les services déployés en ligne actifs (spin
# down automatique par défaut)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(debug=True, port=port, host='0.0.0.0')
