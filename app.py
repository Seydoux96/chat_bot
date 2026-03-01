from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import json
import os

app = Flask(__name__)

#Fichier
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

MEMBRES = [
    "Moussa KAMA", "Lamine THIAM", "Aliou MANÉ", "Ahmadou FAYE",
    "Souhaibou BADIANE", "Mamadou SIDIBÉ", "S Saliou SÉNE",
    "Alioune DIEYE", "S Saliou DIOP", "Thierno FAYE",
    "Diadia MBOUP", "Doudou GUEYE", "Mbaye DIAKHATÉ",
    "Pape NDOYE", "Aziz NDIAYE", "Massamba DIOUM",
    "Abd khadre CAMARA", "Adama DIÉDHIOU", "Pape MANÉ",
    "Dame SECK", "Youssoupha TALL", "Alioune FALL",
    "Alassane MANÉ", "Ousmane DIANKHA", "Kabir Bathily",
    "Malick GUEYE", "Khadim SOCK", "Cheikhouna MBAYE",
    "Bébé Dame"
]

session = {
    "step": None,
    "mode": None,
    "repetition": None,
    "revision": None,
    "beuyites": None
}

def date_complete():
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

    now = datetime.now()
    return f"{jours[now.weekday()]} {now.day} {mois[now.month-1]} {now.year}"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming = request.form.get("Body").strip()
    from_number = request.form.get("From")

    response = MessagingResponse()
    data = load_data()

    if from_number not in data:
        data[from_number] = {
            "membres": [],
            "session": {"step": None,
                "mode": None,
                "repetition": None,
                "revision": None,
                "beuyites": None}
        }

    user = data[from_number]

    # CONFIG
    if incoming.lower() == "config":
        user["session"]["step"] = "config_menu"
        save_data(data)
        response.message(
            "⚙️ CONFIGURATION\n\n"
            "1 - Ajouter membre\n"
            "2 - Supprimer membre\n"
            "3 - Voir membres\n"
            "4 - Retour"
        )
        return str(response)

    if user["session"]["step"] == "config_menu":
        if incoming == "1":
            user["session"]["step"] = "ajout_membre"
            save_data(data)
            response.message("Entrez le nom complet du membre :")
        elif incoming == "2":
            user["session"]["step"] = "supprimer_membre"
            save_data(data)
            response.message(liste_membres(user["membres"]))
        elif incoming == "3":
            response.message(liste_membres(user["membres"]))
        elif incoming == "4":
            user["session"]["step"] = None
            save_data(data)
            response.message("Retour menu principal.")
        return str(response)

    if user["session"]["step"] == "ajout_membre":
        user["membres"].append(incoming)
        user["session"]["step"] = None
        save_data(data)
        response.message("✅ Membre ajouté.")
        return str(response)

    if user["session"]["step"] == "supprimer_membre":
        try:
            index = int(incoming) - 1
            membre = user["membres"].pop(index)
            user["session"]["step"] = None
            save_data(data)
            response.message(f"❌ {membre} supprimé.")
        except:
            response.message("Numéro invalide.")
        return str(response)

    # LANCEMENT
    if incoming.lower() == "pv":
        if not user["membres"]:
            response.message("⚠️ Aucun membre enregistré. Tapez 'config' d'abord.")
            return str(response)
        
        """ session.update({
            "step": "choix_mode",
            "mode": None,
            "repetition": None,
            "revision": None,
            "beuyites": None
        }) """
        user["session"]["step"] == "choix_mode"
        response.message(
            f"📋 *PV RÉPÉTITION DU {date_complete()}*\n\n"
            "Choisissez le type :\n"
            "1 - Répétition\n"
            "2 - Révision\n"
            "3 - Les deux"
        )
        return str(response)

    # CHOIX MODE
    if user["session"]["step"] == "choix_mode":
        if incoming == "1":
            user["session"]["mode"] = "repetition"
            user["session"]["step"] = "saisie_repetition"
            response.message("Entrez : Auteur - Khassida (pour la répétition)")
        elif incoming == "2":
            user["session"]["mode"] = "revision"
            user["session"]["step"] = "saisie_revision"
            response.message("Entrez : Auteur - Khassida (pour la révision)")
        elif incoming == "3":
            user["session"]["mode"] = "les_deux"
            user["session"]["step"] = "saisie_repetition"
            response.message("Entrez : Auteur - Khassida (pour la répétition)")
        return str(response)

    # SAISIE REPETITION
    if user["session"]["step"] == "saisie_repetition":
        user["session"]["repetition"] = incoming
        user["session"]["step"] = "saisie_beuyites"
        response.message(
            "Entrez le nombre de beuyites et le nombre de pages\n"
            "Format : 40 (9 pages)"
        )
        return str(response)

    # SAISIE BEUYITES
    if user["session"]["step"] == "saisie_beuyites":
        user["session"]["beuyites"] = incoming
        if user["session"]["mode"] == "les_deux":
            user["session"]["step"] = "saisie_revision"
            response.message("Entrez : Auteur - Khassida (pour la révision)")
        else:
            user["session"]["step"] = "choix_presents"
            response.message(liste_membres())
        return str(response)

    # SAISIE REVISION
    if user["session"]["step"] == "saisie_revision":
        user["session"]["revision"] = incoming
        user["session"]["step"] = "choix_presents"
        response.message(liste_membres())
        return str(response)

    # CHOIX PRESENTS
    if user["session"]["step"] == "choix_presents":
        numeros = incoming.split()
        presents = set(int(n) for n in numeros if n.isdigit())
        message_final = generer_pv(presents)
        user["session"]["step"] = None
        response.message(message_final)
        return str(response)

    response.message("Tapez 'pv' pour commencer.")
    return str(response)

def liste_membres():
    texte = "Entrez les numéros des présents (ex: 1 5 9 14)\n\n"
    for i, membre in enumerate(MEMBRES, start=1):
        texte += f"{i}- {membre}\n"
    return texte

def generer_pv(presents):
    texte = f"📋 *PV RÉPÉTITION DU {date_complete()}*\n\nTHEME:\n"

    if user["session"]["mode"] in ["les_deux"]:
        texte += "Répétition\n"
        texte += f"- {user["session"]['repetition']}\n"

    if user["session"]["mode"] in ["repetition"]:
        texte += "Répétition\n"
        texte += f"- {user["session"]['repetition']}\n\n"

    if user["session"]["mode"] in ["revision", "les_deux"]:
        texte += "Révision\n"
        texte += f"- {user["session"]['revision']}\n\n"

    texte += "Présents:\n"

    for i, membre in enumerate(MEMBRES, start=1):
        statut = "✅" if i in presents else "❌"
        texte += f"{i}- {membre} {statut}\n\n"

    if user["session"]["mode"] in ["repetition", "les_deux"]:
        texte += "Nbre de beuyites répétés :\n"
        texte += f"{user["session"]['repetition'].split('-')[-1].strip()} : {user["session"]['beuyites']}\n\n"
        texte += "Heure Répétition 20h30 - 22h30\n"

    return texte

if __name__ == "__main__":
    app.run(debug=True)
