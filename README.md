# Solaryinc Discord Bot

Bot Python pour la communauté Solaryinc : gestion des rôles Discord, inscriptions via DM, alertes Twitch en live.

## Fonctionnalités

- Gestion des rôles Discord via boutons interactifs.
- Système d'inscription pour nouveaux membres :
  - Formulaire en DM : pseudo, email, acceptation des règles et politique de confidentialité.
  - Validation ou refus automatique par le staff.
- Alertes Twitch :
  - Annonce des streams en live.
  - Mise à jour ou suppression automatique des messages si le stream change ou se termine.
- Liste des streamers Twitch modifiable dans `streamer.json`.

## Prérequis

- Python 3.11+
- Virtualenv (recommandé)
  - `discord.py`
  - `requests` (pour Twitch API)
  - Autres dépendances listées dans `requirements.txt`

## Installation

1. Cloner le dépôt dans `/opt/Solaryinc_BOT/` :
2. Créer un environnement virtuel et l’activer :
   
 ```bash
cd /opt/Solaryinc_BOT
python3 -m venv venv
source venv/bin/activate
 ```
3. Installer les dépendances Python :
 ```bash   
   pip install -r requirements.txt
 ```

4. Créer un fichier `.env` à la racine du projet et renseigner les variables suivantes :

## Fichier `.env`


   ```bash
# Discord bot token
DISCORD_TOKEN = 
# Twitch API credentials (Token is automatically generated)
TWITCH_CLIENT_ID = 
TWITCH_CLIENT_SECRET = 
# twitch announcement channel ID
DISCORD_CHANNEL_ID = 
# Discord roles channel ID
CHANNEL_ROLE_RECEPTION = 
# Discord role verification channel ID
ROLE_REQUEST_REVIEW_CHANNEL_ID = 
# Discord Roles IDs
COMMUNAUTE_ROLE_ID = 
MEMBRE_VERIFIE_ROLE_ID =
   ```
5. Ajouter ou supprimer des streamers Twitch dans `streamer.json` pour gérer les alertes.

## Lancer le bot

Depuis `/opt/Solaryinc_BOT/` et avec le venv activé :
```bash
python app.py
```
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/bdd1a970-2be2-441c-9b2e-f01cda1b03f7" />

