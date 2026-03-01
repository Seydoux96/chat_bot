
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import json
import os

app = Flask(__name__)

# Fichier de données
DATA_FILE = "data.json"

def load_data():
    """Charge les données depuis le fichier JSON"""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Sauvegarde les données dans le fichier JSON"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Liste fixe des membres par défaut (utilisée pour l'initialisation)
MEMBRES_DEFAUT = [
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

def date_complete():
    """Retourne la date complète en français"""
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

    now = datetime.now()
    return f"{jours[now.weekday()]} {now.day} {mois[now.month-1]} {now.year}"

def formater_liste_membres(user_membres):
    """Formate la liste complète des membres"""
    if not user_membres:
        return "📭 Aucun membre enregistré."
    
    texte = "📋 *LISTE DES MEMBRES*\n\n"
    for i, membre in enumerate(user_membres, start=1):
        texte += f"{i}️⃣ {membre}\n"
    return texte

def formater_choix_presents(user_membres):
    """Formate la liste des membres pour le choix des présents"""
    texte = "👥 *SÉLECTIONNEZ LES PRÉSENTS*\n\n"
    texte += "Entrez les numéros séparés par des espaces (ex: 1 5 9 14)\n\n"
    for i, membre in enumerate(user_membres, start=1):
        texte += f"{i}️⃣ {membre}\n"
    return texte

def generer_pv(presents, user_membres, user_session):
    """Génère le PV complet"""
    # Compter les présents
    nombre_presents = len(presents)
    total_membres = len(user_membres)
    
    texte = f"📋 *PV RÉPÉTITION DU {date_complete()}*\n\n"
    texte += "🎯 *THÈME*\n"

    if user_session["mode"] in ["repetition", "les_deux"]:
        texte += "🔁 RÉPÉTITION\n"
        texte += f"• {user_session['repetition']}\n\n"

    if user_session["mode"] in ["revision", "les_deux"]:
        texte += "📚 RÉVISION\n"
        texte += f"• {user_session['revision']}\n\n"

    texte += "👥 *PRÉSENTS*\n"
    texte += f"({nombre_presents}/{total_membres} présents)\n\n"

    for i, membre in enumerate(user_membres, start=1):
        statut = "✅" if i in presents else "❌"
        texte += f"{i}️⃣ {membre} {statut}\n"

    if user_session["mode"] in ["repetition", "les_deux"]:
        # Extraction du titre du khassida pour les beuyites
        try:
            if " - " in user_session['repetition']:
                titre = user_session['repetition'].split(' - ')[-1].strip()
            else:
                titre = user_session['repetition']
        except:
            titre = user_session['repetition']
        
        texte += f"\n📊 *NOMBRE DE BEUYITES RÉPÉTÉS*\n"
        texte += f"{titre} : {user_session['beuyites']}\n\n"
        texte += "⏰ *HORAIRE*\n"
        texte += "20h30 - 22h30\n"

    return texte

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    # Récupération des données de la requête Twilio
    incoming = request.form.get("Body").strip()
    from_number = request.form.get("From")  # Format: "whatsapp:+221771253616"

    response = MessagingResponse()
    data = load_data()

    # Initialisation d'un nouvel utilisateur avec les membres par défaut
    if from_number not in data:
        data[from_number] = {
            "membres": MEMBRES_DEFAUT.copy(),  # Copie tous les membres par défaut
            "session": {
                "step": None,
                "mode": None,
                "repetition": None,
                "revision": None,
                "beuyites": None
            }
        }
        save_data(data)
        print(f"✅ Nouvel utilisateur créé: {from_number}")

    user = data[from_number]

    # ===== COMMANDE CONFIG =====
    if incoming.lower() == "config":
        user["session"]["step"] = "config_menu"
        save_data(data)
        response.message(
            "⚙️ *CONFIGURATION*\n\n"
            "1️⃣ - Ajouter un membre\n"
            "2️⃣ - Supprimer un membre\n"
            "3️⃣ - Voir tous les membres\n"
            "4️⃣ - Retour au menu principal"
        )
        return str(response)

    # ===== GESTION DU MENU CONFIG =====
    if user["session"]["step"] == "config_menu":
        if incoming == "1":
            user["session"]["step"] = "ajout_membre"
            save_data(data)
            response.message("📝 *AJOUTER UN MEMBRE*\n\nEntrez le nom complet du membre à ajouter :")
        
        elif incoming == "2":
            if not user["membres"]:
                response.message("📭 Aucun membre à supprimer.")
                return str(response)
            
            user["session"]["step"] = "supprimer_membre"
            save_data(data)
            response.message(
                "🗑️ *SUPPRIMER UN MEMBRE*\n\n"
                "Entrez le numéro du membre à supprimer :\n\n"
                f"{formater_liste_membres(user['membres'])}"
            )
        
        elif incoming == "3":
            response.message(formater_liste_membres(user["membres"]))
        
        elif incoming == "4":
            user["session"]["step"] = None
            save_data(data)
            response.message("✅ Retour au menu principal. Tapez 'pv' pour commencer.")
        
        else:
            response.message("❌ Option invalide. Choisissez 1, 2, 3 ou 4.")
        
        return str(response)

    # ===== AJOUT DE MEMBRE =====
    if user["session"]["step"] == "ajout_membre":
        # Vérifier si le membre existe déjà
        if incoming in user["membres"]:
            response.message(f"⚠️ '{incoming}' existe déjà dans la liste.")
            return str(response)
        
        user["membres"].append(incoming)
        user["session"]["step"] = "config_menu"
        save_data(data)
        response.message(
            f"✅ *MEMBRE AJOUTÉ*\n\n"
            f"'{incoming}' a été ajouté avec succès !\n\n"
            f"📊 Total: {len(user['membres'])} membres\n\n"
            "1️⃣ Ajouter un autre\n"
            "2️⃣ Supprimer\n"
            "3️⃣ Voir la liste\n"
            "4️⃣ Retour"
        )
        return str(response)

    # ===== SUPPRESSION DE MEMBRE =====
    if user["session"]["step"] == "supprimer_membre":
        try:
            index = int(incoming) - 1
            if 0 <= index < len(user["membres"]):
                membre = user["membres"].pop(index)
                user["session"]["step"] = "config_menu"
                save_data(data)
                response.message(
                    f"❌ *MEMBRE SUPPRIMÉ*\n\n"
                    f"'{membre}' a été retiré de la liste.\n\n"
                    f"📊 Restants: {len(user['membres'])} membres\n\n"
                    "1️⃣ Ajouter\n"
                    "2️⃣ Supprimer\n"
                    "3️⃣ Voir la liste\n"
                    "4️⃣ Retour"
                )
            else:
                response.message(f"❌ Numéro invalide. Choisissez entre 1 et {len(user['membres'])}.")
        except ValueError:
            response.message("❌ Veuillez entrer un numéro valide.")
        return str(response)

    # ===== LANCEMENT DU PV =====
    if incoming.lower() == "pv":
        if not user["membres"]:
            response.message("⚠️ Aucun membre enregistré. Tapez 'config' pour en ajouter.")
            return str(response)
        
        # Réinitialiser la session pour un nouveau PV
        user["session"] = {
            "step": "choix_mode",
            "mode": None,
            "repetition": None,
            "revision": None,
            "beuyites": None
        }
        save_data(data)
        
        response.message(
            f"📋 *PV RÉPÉTITION DU {date_complete()}*\n\n"
            "Choisissez le type :\n"
            "1️⃣ - Répétition seulement\n"
            "2️⃣ - Révision seulement\n"
            "3️⃣ - Les deux"
        )
        return str(response)

    # ===== CHOIX DU MODE =====
    if user["session"]["step"] == "choix_mode":
        if incoming == "1":
            user["session"]["mode"] = "repetition"
            user["session"]["step"] = "saisie_repetition"
            save_data(data)
            response.message(
                "🎤 *THÈME DE LA RÉPÉTITION*\n\n"
                "Entrez : Auteur - Khassida\n"
                "Exemple: Serigne Saliou - Khassida Jakhka"
            )
        
        elif incoming == "2":
            user["session"]["mode"] = "revision"
            user["session"]["step"] = "saisie_revision"
            save_data(data)
            response.message(
                "📖 *THÈME DE LA RÉVISION*\n\n"
                "Entrez : Auteur - Khassida\n"
                "Exemple: Serigne Saliou - Khassida Jakhka"
            )
        
        elif incoming == "3":
            user["session"]["mode"] = "les_deux"
            user["session"]["step"] = "saisie_repetition"
            save_data(data)
            response.message(
                "🎤 *THÈME DE LA RÉPÉTITION (1/2)*\n\n"
                "Entrez : Auteur - Khassida\n"
                "Exemple: Serigne Saliou - Khassida Jakhka"
            )
        
        else:
            response.message("❌ Option invalide. Choisissez 1, 2 ou 3.")
        
        return str(response)

    # ===== SAISIE DU THÈME DE RÉPÉTITION =====
    if user["session"]["step"] == "saisie_repetition":
        user["session"]["repetition"] = incoming
        user["session"]["step"] = "saisie_beuyites"
        save_data(data)
        response.message(
            "🔢 *NOMBRE DE BEUYITES*\n\n"
            "Entrez le nombre de beuyites et éventuellement les pages\n"
            "Format: 40 (9 pages) ou simplement 40"
        )
        return str(response)

    # ===== SAISIE DES BEUYITES =====
    if user["session"]["step"] == "saisie_beuyites":
        user["session"]["beuyites"] = incoming
        
        if user["session"]["mode"] == "les_deux":
            user["session"]["step"] = "saisie_revision"
            save_data(data)
            response.message(
                "📖 *THÈME DE LA RÉVISION (2/2)*\n\n"
                "Entrez : Auteur - Khassida\n"
                "Exemple: Serigne Saliou - Khassida Jakhka"
            )
        else:
            user["session"]["step"] = "choix_presents"
            save_data(data)
            response.message(formater_choix_presents(user["membres"]))
        
        return str(response)

    # ===== SAISIE DU THÈME DE RÉVISION =====
    if user["session"]["step"] == "saisie_revision":
        user["session"]["revision"] = incoming
        user["session"]["step"] = "choix_presents"
        save_data(data)
        response.message(formater_choix_presents(user["membres"]))
        return str(response)

    # ===== CHOIX DES PRÉSENTS =====
    if user["session"]["step"] == "choix_presents":
        try:
            # Traitement des numéros saisis
            numeros = incoming.replace(',', ' ').split()
            presents = set()
            invalides = []
            
            for n in numeros:
                if n.isdigit():
                    num = int(n)
                    if 1 <= num <= len(user["membres"]):
                        presents.add(num)
                    else:
                        invalides.append(n)
                else:
                    invalides.append(n)
            
            if not presents:
                response.message(
                    "❌ *AUCUN NUMÉRO VALIDE*\n\n"
                    "Veuillez entrer des numéros entre 1 et "
                    f"{len(user['membres'])}.\n\n"
                    f"{formater_choix_presents(user['membres'])}"
                )
                return str(response)
            
            if invalides:
                warning = f"⚠️ Numéros ignorés: {', '.join(invalides)}\n\n"
            else:
                warning = ""
            
            # Génération du PV final
            message_final = warning + generer_pv(presents, user["membres"], user["session"])
            
            # Réinitialisation complète de la session
            user["session"] = {
                "step": None,
                "mode": None,
                "repetition": None,
                "revision": None,
                "beuyites": None
            }
            save_data(data)
            
            response.message(message_final)
            
        except Exception as e:
            response.message(f"❌ Erreur inattendue: {str(e)}")
            print(f"Erreur: {e}")
        
        return str(response)

    # ===== MESSAGE D'ACCUEIL PAR DÉFAUT =====
    response.message(
        "👋 *Bienvenue sur le bot PV!*\n\n"
        "Commandes disponibles:\n"
        "• 📋 Tapez 'pv' pour créer un PV de répétition\n"
        "• ⚙️ Tapez 'config' pour gérer la liste des membres\n\n"
        "_Besoin d'aide? Contactez l'administrateur._"
    )
    return str(response)

if __name__ == "__main__":
    print("🚀 Bot WhatsApp PV démarré sur http://localhost:5000")
    print("📁 Fichier de données: data.json")
    app.run(debug=True, host='0.0.0.0', port=5000)