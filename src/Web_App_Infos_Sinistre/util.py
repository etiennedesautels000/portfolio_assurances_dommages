# Fonctions utilitaires

def validate_search_inputs(form):
    """
    Valide que les inputs respectent les règles métier:
    - SOIT un ID réclamation
    - SOIT date + heure + coordonnées
    """
    has_id_reclamation = form.id_reclamation.data is not None and form.id_reclamation.data.strip() != ''
    has_date = form.date.data is not None
    has_heure = form.heure.data is not None
    has_coords = form.lat.data is not None and form.long.data is not None

    # Une des deux conditions doit être vraie
    option1 = has_id_reclamation and not (has_date or has_heure or has_coords)
    option2 = (has_date and has_heure and has_coords) and not has_id_reclamation
    option3 = has_id_reclamation and has_date and has_heure and has_coords

    return option1 or option2 or option3


def build_search_payload(form):
    """Construit le payload de recherche avec les données du formulaire"""
    date = form.date.data.strftime("%Y-%m-%d") if form.date.data else None
    heure = form.heure.data.strftime("%H:%M") if form.heure.data else None

    payload = {
        "id_reclamation": form.id_reclamation.data if form.id_reclamation.data else None,
        "date": date,
        "heure": heure,
        "latitude": form.lat.data,
        "longitude": form.long.data
    }

    return payload
    # # Nettoyer les None du payload
    # return {k: v for k, v in payload.items() if v is not None}
    #
