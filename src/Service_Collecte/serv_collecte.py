'''
Ce service reçoit les données entrantes (lat + long +
date + heure) depuis Service_Data, collecte les données météo depuis leur source,
les traite et les renvoie à Service_Data au format JSON
'''

import jsonify
import os
from shapely.geometry import shape, Point

from datetime import datetime, timedelta
from operator import concat

from flask import Flask, request
from flask_cors import CORS
import requests

app = Flask(__name__)

CORS(app)


@app.route('/collecte_data', methods=['GET'])
def collecte_data():
    payload = request.get_json()
    print(payload)  # imprimer payload
    latitude = payload["latitude"]
    longitude = payload["longitude"]
    date_heure = f'{payload["date"]}T{payload["heure"]}'  # Format utilisé par l'API
    # conversion de la date au format datetime.date afin de pouvoir
    # effectuer une opération sur la date (soustraire 1 jour)
    date = datetime.strptime(date_heure, "%Y-%m-%dT%H:%M").date()

    ## Appel à l'API open-meteo
    URI_SERV_METEO = (f'https://archive-api.open-meteo.com/v1/archive?'
                      f'latitude={latitude}&'
                      f'longitude={longitude}&'
                      f'start_date={date - timedelta(days=1)}&'
                      f'end_date={date}&'
                      'daily=sunrise,sunset&'
                      'hourly=temperature_2m,rain,snowfall,cloud_cover,'
                      'wind_speed_10m,wind_direction_10m,weather_code&'
                      'timezone=auto')

    data_meteo = requests.get(URI_SERV_METEO).json()

    # Transformations
    # a. Ne conserver que les 24h précédant le sinistre pour l'analyse
    # Arrondir date_heure au début de l'heure (remplacer les 2
    # derniers caractères par 00)
    date_heure_arr = concat(date_heure[:-2], '00')
    heures = data_meteo["hourly"]["time"]  # liste des heures correspondant aux points de données
    index_heure = heures.index(date_heure_arr)

    # Données des 24h pertinentes
    temp = data_meteo["hourly"]["temperature_2m"][(index_heure - 23):(index_heure + 1)]
    pluie = data_meteo["hourly"]["rain"][(index_heure - 23):(index_heure + 1)]
    neige = data_meteo["hourly"]["snowfall"][(index_heure - 23):(index_heure + 1)]

    # b. Calculer le min/max de température, l'accumulation de pluie et de neige
    temp_min = min(temp)
    temp_max = max(temp)
    pluie_24h = sum(pluie)
    neige_24h = sum(neige)

    ## Zone de dégel
    # Chargement du fichier geoJSON
    URI_ZONE_DEGEL = ('https://ws.mapserver.transports.gouv.qc.ca/swtq?'
                      'service=wfs&'
                      'version=2.0.0&'
                      'request=getfeature&'
                      'typename=ms:zone_degel&'
                      'outfile=ZoneDegel&'
                      'srsname=EPSG:4326&'
                      'outputformat=geojson')
    data_degel = requests.get(URI_ZONE_DEGEL).json()

    # Création d'un objet Point contenant les coordonnées de l'incident
    point = Point(longitude, latitude)

    # On teste chaque poygone contenu dans le fichier geoJSON pour
    # déterminer si il contient les coordonnées renseignées, tant qu'on
    # n'a pas trouvé le bon
    trouve = False
    for feature in data_degel['features']:
        if not trouve:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                zone_degel = feature['properties']['zone']
                periode_degel = f'{feature['properties']['dat_debut_zone']} - {feature['properties']['dat_fin_zone']}'
                trouve = True

    # Cas où on trouve pas les coordonnées après avoir parcouru tous les polygones (i.e. coordonnées hors Québec):
    if not trouve:
        zone_degel = periode_degel = 'N/A'

    # Document JSON retourné par le service
    info_meteo = {
        'horaire': {
            'temperature_C': data_meteo["hourly"]["temperature_2m"][index_heure],
            'pluie_mm': data_meteo["hourly"]["rain"][index_heure],
            'neige_cm': data_meteo["hourly"]["snowfall"][index_heure],
            'couverture_nuageuse_pct': data_meteo["hourly"]["cloud_cover"][index_heure],
            'vitesse_vent_kmh': data_meteo["hourly"]["wind_speed_10m"][index_heure],
            'direction_vent_deg': data_meteo["hourly"]["wind_direction_10m"][index_heure],
            'code_WMO': data_meteo["hourly"]["weather_code"][index_heure]
        },
        'journalier': {
            'temperature_min_C': temp_min,
            'temperature_max_C': temp_max,
            'pluie_24h_mm': pluie_24h,
            'neige_24h_cm': neige_24h,
            'lever_soleil': data_meteo["daily"]["sunrise"][-1],
            'coucher_soleil': data_meteo["daily"]["sunset"][-1],
            'zone_degel': zone_degel,
            'periode_degel': periode_degel
        }
    }
    return info_meteo

# route utilisée pour garder les services déployés en ligne actifs (spin
# down automatique par défaut)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5020))
    app.run(debug=True, port=port, host='0.0.0.0')
