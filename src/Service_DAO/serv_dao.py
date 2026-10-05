
# Service DAO


from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

JSONDB_URI = 'db_incidents.json'
MONGODB_URI = '******' # database: 'info_sinistre_auto'
DB_COLLECTION = 'incidents'


# Initialisation de la base de données
#    initialiser_db_JSON()
mongoClient = MongoClient(MONGODB_URI)
mongodb = mongoClient.info_sinistre_auto[DB_COLLECTION]



######################################################################################
##### DB = FICHIER JSON ##############################################################


# Récupérer le prochain id_incident à utiliser dans la bd
def get_next_id_JSON(documents):
    # chercher dans les données pour le dernier id_incident et ajouter 1
    # s'il n'y a aucun document enregistré, retourner 0
    id_list = [doc.get("id_incident") for doc in documents if doc.get("id_incident") is not None]
    next_id = max(id_list) + 1 if id_list else 0
    return next_id


# Initialisation de la base de données
def initialiser_db_JSON():
    if not os.path.exists(JSONDB_URI) or os.path.getsize(JSONDB_URI) == 0:
        # si la db n'existe pas, la créer
        data = { DB_COLLECTION: [] }
        with open(JSONDB_URI, 'w', encoding='utf-8') as fout:
            json.dump(data, fout, indent=4)
    print("- Base de données initialisée")


# Chercher un incident à partir du id_reclamation
def select_id_reclamation_JSON(info_dossier):
    # récupérer le data de la collection
    with open(JSONDB_URI, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    documents = data.get(DB_COLLECTION, [])

    # collecter les inputs du nouveau document
    u_id_reclamation = info_dossier.get("id_reclamation")

    # trouver le id_reclamation dans la bd
    for doc in documents:
        doc_id_reclamation = doc.get("info_dossier").get("id_reclamation")
        if u_id_reclamation in doc_id_reclamation:
            return doc

    # id_reclamation non trouvé
    return None


# Chercher un incident à partir des champs date + heure + latitude + longitude
def select_incident_JSON(info_dossier):

    # récupérer le data de la base de données
    with open(JSONDB_URI, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    documents = data.get(DB_COLLECTION, [])

    # trouver l'incident dans la bd
    for doc in documents:
        dossier = doc.get("info_dossier", {})
        # vérifier si la combinaison (date + heure + latitude + longitude) existe déjà
        if (
            dossier.get("date") == info_dossier.get("date") and
            dossier.get("heure") == info_dossier.get("heure") and
            dossier.get("latitude") == info_dossier.get("latitude") and
            dossier.get("longitude") == info_dossier.get("longitude")
        ):
            return doc

    # retourner None s'il n'existe pas
    return None


# Insérer un nouvel incident à la bd
def insert_incident_JSON(nouvel_incident):
    # récupérer le data de la collection
    with open(JSONDB_URI, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    documents = data.get(DB_COLLECTION, [])

    # trouver le prochain id
    next_id = get_next_id_JSON(documents)
    nouvel_incident['id_incident'] = next_id

    # ajouter le nouveau document dans la collection
    documents.append(nouvel_incident)

    # commit le changement à la collection
    with open(JSONDB_URI, 'w', encoding='utf-8') as fout:
        json.dump(data, fout, indent=4)

    return nouvel_incident


# Modifier un incident déjà existant de la bd
def update_incident_JSON(incident):
    # récupérer le data de la collection
    with open(JSONDB_URI, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    documents = data.get(DB_COLLECTION, [])

    # retirer le document existant de la bd
    documents = [doc for doc in documents if doc.get("id_incident") != incident["id_incident"]]

    # ajouter le document modifié dans la collection
    documents.append(incident)

    # commit le changement à la collection
    with open(JSONDB_URI, 'w', encoding='utf-8') as fout:
        json.dump(data, fout, indent=4)


# Ajouter un id_réclamation à un incident déjà existant
def update_reclamation_JSON(id_incident, id_reclamation):
    incident_modifie = None

    # récupérer le data de la collection
    with open(JSONDB_URI, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    documents = data.get(DB_COLLECTION, [])

    # ajouter le id_reclamation à l'incident correspondant
    for doc in documents:
        if doc.get("id_incident") == id_incident:
            dossier = doc["info_dossier"]
            dossier["id_reclamation"].append(id_reclamation["id_reclamation"])
            incident_modifie = doc
            break

    # commit le changement à la collection
    with open(JSONDB_URI, 'w', encoding='utf-8') as fout:
        json.dump(data, fout, indent=4)

    return incident_modifie



######################################################################################
##### DB = MONGO DB ##################################################################


# Récupérer le prochain id_incident à utiliser dans la bd
def get_next_id_MONGODB():
    # récupérer la liste des "id_incident", et la convertir en liste python
    documents = list(mongodb.find({}, {"id_incident": 1, "_id": 0}))
    id_list = [doc["id_incident"] for doc in documents if "id_incident" in doc] or None

    # chercher dans les données pour le dernier id_incident et ajouter 1
    # s'il n'y a aucun document enregistré, retourner 0
    next_id = max(id_list) + 1 if id_list else 0
    return next_id


# Chercher un incident à partir du id_reclamation
def select_id_reclamation_MONGODB(info_dossier):
    # collecter le id_reclamation recherché
    u_id_reclamation = info_dossier.get("id_reclamation")
    if u_id_reclamation is None:
        return None

    # récupérer la liste des incidents, et la convertir en liste python
    documents = list(mongodb.find({}, {"_id": 0}))

    # trouver le id_reclamation dans la bd
    for doc in documents:
        doc_id_reclamation = doc.get("info_dossier").get("id_reclamation")
        if u_id_reclamation in doc_id_reclamation:
            return doc

    # id_reclamation non trouvé
    return None


# Chercher un incident à partir des 4 champs date + heure + latitude + longitude
def select_incident_MONGODB(info_dossier):
    # trouver l'incident dans la bd seulement en fonction des 4 champs
    query = {
        "info_dossier.date": info_dossier["date"],
        "info_dossier.heure": info_dossier["heure"],
        "info_dossier.latitude": info_dossier["latitude"],
        "info_dossier.longitude": info_dossier["longitude"]
    }
    doc = mongodb.find_one(query, {"_id": 0})

    # retourner le document trouvé ou None s'il n'existe pas
    return doc if doc else None


def insert_incident_MONGODB(nouvel_incident):
    # trouver le prochain id
    next_id = get_next_id_MONGODB()
    nouvel_incident['id_incident'] = next_id

    # ajouter le nouveau document dans la collection
    mongodb.insert_one(nouvel_incident)
    nouvel_incident.pop('_id', None)  # retirer le champ "_id" de mongoDB

    # retourner le nouvel incident
    return nouvel_incident


# Modifier un incident déjà existant de la bd
def update_incident_MONGODB(incident):
    # remplacer le document initial dans la collection avec le document modifié
    resultat = mongodb.replace_one({"id_incident": incident["id_incident"]}, incident)

    # retourner le document modifié
    return incident


def update_reclamation_MONGODB(id_incident, id_reclamation):
    update_data = {"$push": {"info_dossier.id_reclamation": id_reclamation["id_reclamation"]}}
    resultat = mongodb.update_one({"id_incident": id_incident}, update_data)

    if resultat.modified_count == 1:
        return select_id_reclamation_MONGODB(id_reclamation)

    return None



######################################################################################
##### ROUTES #########################################################################

# Chercher un incident à partir des infos "info_dossier"
@app.route('/dao/incidents', methods=['GET'])
def chercher_incident():
    # récupérer le payload info_dossier
    info_dossier = request.get_json()

    # si le id_réclamation fourni existe déjà, retourner l'incident correspondant
    incident = select_id_reclamation_MONGODB(info_dossier)
    if incident is not None:
        return incident, 200

    # si l'incident existe déjà, retourner l'incident correspondant
    incident = select_incident_MONGODB(info_dossier)
    if incident is not None:
        return incident, 210

    return jsonify({"erreur": "404 - Document non trouvé"}), 404


# Ajouter un incident à la bd
@app.route('/dao/incidents', methods=['POST'])
def creer_incident():
    # récupérer le payload
    jsondata = request.get_json()

    # insérer le nouveau document dans la collection (#id auto-généré)
    nouvel_incident = insert_incident_MONGODB(jsondata)

    # retourner le nouveau document avec le code de succès 201
    return nouvel_incident, 201


# Modifier un incident existant à la bd
@app.route('/dao/incidents', methods=['PUT'])
def modifier_incident():
    # récupérer le payload
    jsondata = request.get_json()

    # modifier le document existant dans la db
    update_incident_MONGODB(jsondata)

    # retourner le nouveau document avec le code de succès 201
    return jsonify(jsondata), 201


# Ajouter un id_reclamation à un incident existant à la bd
@app.route('/dao/incidents/<int:id_incident>/reclamation', methods=['PATCH'])
def ajouter_reclamation(id_incident):
    # récupérer le payload
    id_reclamation = request.get_json()

    # modifier le document existant dans la db, uniquement pour ajouter un id_reclamation
    incident = update_reclamation_MONGODB(id_incident, id_reclamation)

    # retourner le nouveau document avec le code de succès 201
    return incident, 201

# route utilisée pour garder les services déployés en ligne actifs (spin
# down automatique par défaut)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5601))
    app.run(debug=True, port=port, host='0.0.0.0')
