"""
Web App qui collecte les inputs (date, heure, localisation) et affiche
les données collectées par le service d'intégration à l'utilisateur
via un dashboard
"""
from routes import app
import os

from apscheduler.schedulers.background import BackgroundScheduler
import requests

if __name__ == '__main__':
    # Si le déploiement est sur Render (ie variable d'environnement
    # SERV_DATA_RENDER existe) alors appeler les services périodiquement
    # pour éviter qu'ils ne se désactivent
    if os.getenv("SERV_DATA_RENDER"):

        def keep_warm():
            for uri in ["SERV_AUTH_RENDER",
                        "SERV_COLLECTE_RENDER",
                        "SERV_DAO_RENDER",
                        "SERV_DATA_RENDER"]:
                try:
                    # obtenir le lien depuis la variable d'environnement
                    # correspondante sur Render
                    requests.get(f"{os.getenv(uri)}/health", timeout=5)
                except:
                    pass

        keep_warm()
        scheduler = BackgroundScheduler()
        scheduler.add_job(keep_warm, 'interval', minutes=10)
        scheduler.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
