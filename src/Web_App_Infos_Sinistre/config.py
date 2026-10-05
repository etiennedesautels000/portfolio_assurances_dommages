"""
Configuration settings for the Flask application.

This file stores settings that should be the same across your entire app,
like security keys and database connections. Keeping settings separate from
your main code is a best practice!
"""

import os

# URI dynamiques: si l'URI n'existe pas dans les variables d'environnement
# (définies manuellement dans l'environnement virtuel de Render) alors
# utiliser localhost et port définis dans le service
root_data = os.getenv("SERV_DATA_RENDER", "http://127.0.0.1:5010")
root_auth = os.getenv("SERV_AUTH_RENDER", "http://127.0.0.1:5602")


URI_SERV_DATA = {
    'chercher_incident': f'{root_data}/data',
    'creer_incident': f'{root_data}/data',
    'ajouter_reclamation': f'{root_data}/data/reclamation'
}

URI_AUTH_SERVICE = f'{root_auth}/auth/login'

class Config(object):
    """
    Main configuration class for the Flask app.

    Flask uses this class to configure itself when the app starts.
    You can create different Config classes (like ConfigDev, ConfigProduction)
    for different environments (development vs. live servers).
    """

    # SECRET_KEY: A security token used to encrypt sensitive data (like form tokens)
    # It tries to get the key from your computer's environment variables first.
    # If not found, it uses the default string (not secure in production!).
    # In real projects, never hardcode secrets—always use environment variables.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Le renard saute la barriere'
