import os
import json
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput, View, Button
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Chargement des variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

CHANNEL_ROLE_RECEPTION = int(os.getenv("CHANNEL_ROLE_RECEPTION"))
ROLE_REQUEST_REVIEW_CHANNEL_ID = int(os.getenv("ROLE_REQUEST_REVIEW_CHANNEL_ID"))
COMMUNAUTE_ROLE_ID = int(os.getenv("COMMUNAUTE_ROLE_ID"))
MEMBRE_VERIFIE_ROLE_ID = int(os.getenv("MEMBRE_VERIFIE_ROLE_ID"))

# Fichier pour stocker les demandes en attente
pending_requests_file = "pending_requests.json"

# Intents avec message_content activé si besoin pour les interactions
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

streamers = load_json("streamer.json", [])
live_data = load_json("live.json", {})
twitch_token_data = load_json("token.json", {})
pending_requests = load_json(pending_requests_file, {})

async def get_twitch_token():
    global twitch_token_data

    print("Contenu actuel de twitch_token_data:", twitch_token_data)

    if not twitch_token_data or "access_token" not in twitch_token_data or "expires_at" not in twitch_token_data:
        print("❌ token.json vide ou incomplet. Requête vers Twitch pour un nouveau token.")
        twitch_token_data = {}

    expires_at_str = twitch_token_data.get("expires_at", "1970-01-01T00:00:00")

    try:
        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(f"Erreur parsing date expires_at : {e}")
        expires_at = datetime(1970, 1, 1)

    now = datetime.utcnow()
    print(f"now: {now}, expires_at: {expires_at}")

    if not twitch_token_data or now > expires_at:
        print("➡️ Récupération d’un nouveau token Twitch...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": TWITCH_CLIENT_ID,
                    "client_secret": TWITCH_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                }
            ) as resp:
                token_json = await resp.json()
                print("✅ Réponse Twitch :", token_json)

                twitch_token_data = {
                    "access_token": token_json.get("access_token"),
                    "expires_at": (
                        datetime.utcnow() + timedelta(seconds=token_json.get("expires_in", 0))
                    ).strftime("%Y-%m-%dT%H:%M:%S")
                }
                save_json("token.json", twitch_token_data)
                print("💾 Token sauvegardé dans token.json !")
    else:
        print("✅ Token Twitch encore valide.")

    return twitch_token_data["access_token"]

@tasks.loop(minutes=10)
async def check_streams():
    access_token = await get_twitch_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.twitch.tv/helix/streams",
            headers=headers,
            params={"user_login": streamers}
        ) as resp:
            data = await resp.json()

    current_live = {stream["user_login"]: stream for stream in data.get("data", [])}

    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        print("❌ Canal Discord introuvable pour l'annonce des streams.")
        return

    for streamer in streamers:
        was_live = streamer in live_data
        is_live = streamer in current_live

        if is_live and not was_live:
            stream = current_live[streamer]
            embed = discord.Embed(
                title=f"{stream['user_name']} est en live sur Twitch !",
                description=f"**{stream['title']}**",
                url=f"https://twitch.tv/{streamer}",
                color=0x9146FF,
            )

            embed.set_author(
                name="🔴 Nouveau live détecté !",
                icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png"
            )

            embed.add_field(
                name="🎮 Jeu / Catégorie",
                value=stream.get("game_name", "Inconnu"),
                inline=True
            )

            embed.add_field(
                name="👥 Spectateurs",
                value=f"{stream['viewer_count']} 🔥",
                inline=True
            )

            thumbnail_url = stream["thumbnail_url"].replace("{width}", "1280").replace("{height}", "720")
            embed.set_image(url=thumbnail_url)

            embed.set_footer(text=f"En direct depuis {stream['started_at']}")

            msg = await channel.send(embed=embed)
            live_data[streamer] = {
                "message_id": msg.id,
                "stream_id": stream["id"]
            }
            save_json("live.json", live_data)

        elif not is_live and was_live:
            try:
                msg = await channel.fetch_message(live_data[streamer]["message_id"])
                await msg.delete()
            except Exception:
                pass
            live_data.pop(streamer, None)
            save_json("live.json", live_data)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    if not check_streams.is_running():
        check_streams.start()

    channel = bot.get_channel(CHANNEL_ROLE_RECEPTION)
    print(f"Vérification du canal pour envoi du message de rôle : {channel}")
    if channel:
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.components:
                # Vérifie si message avec boutons déjà présents
                for row in message.components:
                    for comp in row.children:
                        if comp.custom_id in ("join_community", "request_verified"):
                            print("Message avec boutons déjà présent, pas d'envoi.")
                            return  # Quitte la fonction on_ready
        # Si aucun message trouvé, on envoie un nouveau message avec boutons
        print("✅ Envoi du message avec boutons car aucun existant trouvé.")
        embed = discord.Embed(
            title="Bienvenue sur Solaryinc",
            description="Choisis une des options ci-dessous pour rejoindre la communauté ou faire une demande de membre vérifié.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://solaryinc.net/assets/logo-Deyl0ZDP.png")
        embed.set_footer(text="Solaryinc | Rôle communautaire automatisé")
        await channel.send(embed=embed, view=RoleRequestView())

class RoleRequestView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 Rejoindre la communauté", style=discord.ButtonStyle.primary, custom_id="join_community")
    async def join_community(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] Bouton 'join_community' cliqué par {interaction.user}")
        await send_role_form(interaction, "communauté")

    @discord.ui.button(label="✅ Demande de membre vérifié", style=discord.ButtonStyle.success, custom_id="request_verified")
    async def request_verified(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] Bouton 'request_verified' cliqué par {interaction.user}")
        if discord.utils.get(interaction.user.roles, id=COMMUNAUTE_ROLE_ID) is None:
            await interaction.response.send_message(
                "Tu dois d'abord rejoindre la communauté avant de pouvoir demander le rôle vérifié.",
                ephemeral=True
            )
            return
        await send_role_form(interaction, "membre vérifié")

async def send_role_form(interaction: discord.Interaction, role_type: str):
    print(f"[DEBUG] Envoi du formulaire pour rôle {role_type} à {interaction.user}")

    class RoleFormModal(Modal, title=f"Demande de rôle {role_type}"):
        pseudo = TextInput(label="Ton pseudo", placeholder="ex: NouchOW", required=True)
        email = TextInput(label="Ton adresse mail", placeholder="ex: contact@solaryinc.net", required=True)

        async def on_submit(self, interaction: discord.Interaction):
            print(f"[DEBUG] Formulaire soumis par {interaction.user} pour rôle {role_type}")
            staff_channel = bot.get_channel(ROLE_REQUEST_REVIEW_CHANNEL_ID)

            embed = discord.Embed(
                title=f"📥 Nouvelle demande de rôle : {role_type}",
                description=f"**Demandeur :** {interaction.user.mention}\n\n"
                            f"**🧑 Pseudo** : `{self.pseudo.value}`\n"
                            f"**📧 Email** : `{self.email.value}`",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url="https://solaryinc.net/assets/logo-Deyl0ZDP.png")
            embed.set_footer(text="Demande en attente de validation | Solaryinc")

            if staff_channel is not None:
                # Envoyer message dans le salon staff avec vue décision
                view = create_admin_decision_view(interaction.user.id, role_type)
                await staff_channel.send(embed=embed, view=view)
                print(f"[DEBUG] Message envoyé dans le salon admin ID : {ROLE_REQUEST_REVIEW_CHANNEL_ID}")
            else:
                print("❌ Salon d'administration introuvable")

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "✅ Ta demande a été envoyée à l’équipe. Tu recevras une réponse bientôt.",
                    ephemeral=True
                )

    try:
        await interaction.response.send_modal(RoleFormModal())
    except discord.errors.InteractionResponded:
        await interaction.followup.send_modal(RoleFormModal())
    except Exception as e:
        print(f"❌ Erreur inattendue lors de l’envoi du modal : {e}")

def create_admin_decision_view(user_id: int, role_name: str) -> discord.ui.View:
    class AdminDecisionView(View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="✅ Valider", style=discord.ButtonStyle.success, custom_id="admin_accept")
        async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
            await process_admin_decision(interaction, True, user_id, role_name)

        @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger, custom_id="admin_reject")
        async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
            await process_admin_decision(interaction, False, user_id, role_name)

    return AdminDecisionView()

async def process_admin_decision(interaction: discord.Interaction, accepted: bool, user_id: int, role_name: str):
    guild = interaction.guild
    member = guild.get_member(user_id)
    if member is None:
        await interaction.response.send_message("Utilisateur introuvable sur le serveur.", ephemeral=True)
        return

    role_id = COMMUNAUTE_ROLE_ID if role_name == "communauté" else MEMBRE_VERIFIE_ROLE_ID
    role = guild.get_role(role_id)

    if accepted:
        if role not in member.roles:
            await member.add_roles(role, reason=f"Demande de rôle {role_name} acceptée")
        await interaction.response.send_message(f"Le rôle {role.name} a été attribué à {member.mention}.", ephemeral=True)
        try:
            await member.send(f"🎉 Ta demande pour le rôle '{role_name}' a été acceptée. Bienvenue !")
        except Exception:
            pass
    else:
        await interaction.response.send_message(f"La demande de rôle '{role_name}' de {member.mention} a été refusée.", ephemeral=True)
        try:
            await member.send(f"❌ Ta demande pour le rôle '{role_name}' a été refusée. N'hésite pas à contacter un modérateur pour plus d'infos.")
        except Exception:
            pass

    # Optionnel : suppression du message de demande ou mise à jour
    await interaction.message.delete()

bot.run(DISCORD_TOKEN)
