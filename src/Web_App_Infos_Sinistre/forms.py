from flask_wtf import FlaskForm  # Base class for all Flask forms
from wtforms import (SubmitField, IntegerField, FloatField, RadioField,
                     DateField, TimeField, StringField)  # Field types
from wtforms.validators import Optional, data_required  # Validation rules


class InfosInputForm(FlaskForm):
    """
    Formulaire d'insertion de données:
    -id_reclamation (nullable)
    -Date (nullable)
    -Heure (nullable)
    -Lat (nullable)
    -Long (nullable)
    -Niveau de zoom (default 15)
    """
    id_reclamation = StringField("Identifiant de réclamation", validators=[Optional()])
    date = DateField("Date", validators=[Optional()])
    heure = TimeField("Heure", validators=[Optional()])
    lat = FloatField("Latitude", validators=[Optional()])
    long = FloatField("Longitude", validators=[Optional()])

    submit = SubmitField("Sauvegarder")

class FormAjoutReclamation(FlaskForm):
    """
    Formulaire donnant l'option à l'utilisateur d'ajouter la réclamation
    """
    options = RadioField('Choose an option:',
                         choices=[('Ajouter', 'Ajouter'), ('Ne pas ajouter', 'Ne pas ajouter')],
                         validators= [data_required()])
    submit = SubmitField("Sauvegarder")


class FormCollecteDonnees(FlaskForm):
    """
    Formulaire donnant l'option à l'utilisateur de collecter les informations
    """
    options = RadioField('Choose an option:',
                         choices=[('Oui', 'Oui'), ('Non', 'Non')],
                         validators= [data_required()])
    submit = SubmitField("Sauvegarder")