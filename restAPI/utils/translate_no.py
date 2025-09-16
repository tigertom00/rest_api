import requests
from srv.settings import TRANSLATION_AUTH_KEY

START_URL = "http://10.20.30.202:5000/translate/start"
STOP_URL = "http://10.20.30.202:5000/translate/stop"
TRANSLATE_URL = "http://10.20.30.202:8080/trans_en_to_no"
HEADERS = {"Authorization": f"Bearer {TRANSLATION_AUTH_KEY}"}

def translate_no(fields):
    # Start server
    start_response = requests.get(START_URL, headers=HEADERS)
    if start_response.status_code != 200:
        raise Exception("Translation server could not be started")

    results = {}
    for field_name, text in fields.items():
        payload = {"text": text, "src_lang": "eng_Latn", "tgt_lang": "nob_Latn"}
        response = requests.post(TRANSLATE_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            results[field_name] = response.json().get("translation", text)
        else:
            results[field_name] = text  # fallback

    # Stop server
    requests.get(STOP_URL, headers=HEADERS)
    return results