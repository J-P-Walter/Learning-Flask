import json
import requests
from flask_babel import _
from app import app


#Currently not set up since I don't want to give my card to Microsoft
def translate(text, source_language, dest_language):
    #Still coding as if it did work: checks if key is saved
    if 'MS_TRANSLATOR_KEY' not in app.config or not app.config['MS_TRANSLATOR_KEY']:
        return _('ERROR: translation service not configured')
    #gets key to be passed as auth header for validation
    auth = {
        'Ocp-Apim-Subscription-Key': app.config['MS_TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'westus2'}
    #Sends request to API
    r = requests.post(
        'https://api.cognitive.microsofttranslator.com'
        '/translate?api-version=3.0&from={}&to={}'.format(
            source_language, dest_language), headers=auth, json=[{'Text': text}])
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return r.json()[0]['translations'][0]['text']