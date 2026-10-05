import os

# URI dynamiques: si l'URI n'existe pas dans les variables d'environnement
# (définies manuellement dans l'environnement virtuel de Render) alors
# utiliser localhost et port définis dans le service
root_dao = os.getenv("SERV_DAO_RENDER", "http://127.0.0.1:5601")
root_collecte = os.getenv("SERV_COLLECTE_RENDER", "http://127.0.0.1:5020")

URI_SERV_DAO = {
    'chercher_incident': f'{root_dao}/dao/incidents',
    'creer_incident': f'{root_dao}/dao/incidents',
    'ajouter_reclamation': f'{root_dao}/dao/incidents/''{}''/reclamation',
    'modifier_incident': f'{root_dao}/dao/incidents'
}
URI_SERV_COLLECTE = f'{root_collecte}/collecte_data'