
# Solaryinc-Bot

Bot Discord Python pour la communauté Solaryinc : gestion des rôles, inscriptions via DM, approbation automatique par le staff et alertes Twitch en temps réel.

## Fonctionnalités

- Gestion des rôles Discord via boutons interactifs.
- Système d'inscription pour nouveaux membres :
  - Formulaire en DM : pseudo, email, acceptation des règles et politique de confidentialité.
  - Validation ou refus automatique par le staff.
- Alertes Twitch :
  - Annonce des streams en live.
  - Mise à jour des messages en cas de changement de titre, catégorie ou heure de début.
  - Suppression automatique si le stream se termine.
- Notifications automatisées aux utilisateurs après validation ou refus.

## Prérequis

- Python 3.11+
- Bibliothèques :
  - `discord.py`
  - `requests` (pour Twitch API)
  - Autres dépendances listées dans `requirements.txt`

## Installation

1. Cloner le dépôt :
