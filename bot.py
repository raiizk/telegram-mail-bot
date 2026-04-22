"""
Bot Telegram → Email Pro
Envoie un message texte ou vocal → Claude rédige l'email → Resend l'envoie sur ta boîte pro.
"""

import os
import json
from dotenv import load_dotenv
load_dotenv()
import base64
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
import anthropic
import resend as resend_lib

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Config (variables d'environnement) ───────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
RESEND_KEY      = os.environ["RESEND_API_KEY"]
YOUR_EMAIL      = os.environ["YOUR_EMAIL"]       # ta boîte pro : pedro@banquemigros.ch
FROM_EMAIL      = os.environ["FROM_EMAIL"]       # expéditeur vérifié sur Resend
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID") or "0")  # ton ID Telegram (voir /start)

# ─── Clients ──────────────────────────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
resend_lib.api_key = RESEND_KEY

# ─── Prompt système ───────────────────────────────────────────────────────────
SYSTEM = """
Tu es l'assistant mail personnel de Pedro, basé en Suisse romande.
Quand il t'envoie une note rapide (texte ou vocal depuis la voiture),
tu dois rédiger un email professionnel complet, prêt à l'envoi ou au transfert.

Règles de rédaction :
- Email en français, professionnel mais naturel
- Si c'est un rappel pour Pedro lui-même → sujet commence par "[RAPPEL]"
- Si c'est un brouillon à transférer à quelqu'un → sujet commence par "[BROUILLON]"
- Corps complet : salutation, développement clair, formule de politesse, signature "Pedro"
- Adapte le ton selon le contexte (bancaire = formel, événementiel = chaleureux)

Réponds UNIQUEMENT avec ce JSON strict, sans markdown, sans explication autour :
{
  "subject": "Objet complet de l'email",
  "body": "Corps complet en texte brut (\\n pour sauts de ligne)",
  "type": "rappel ou brouillon",
  "summary": "1 courte phrase résumant l'email rédigé"
}
"""

# ─── Fonctions core ───────────────────────────────────────────────────────────

def parse_result(raw: str) -> dict:
    """Parse la réponse JSON de Claude proprement."""
    text = raw.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def draft_from_text(text: str) -> dict:
    """Rédige un email depuis un message texte."""
    response = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": text}]
    )
    return parse_result(response.content[0].text)


def draft_from_voice(audio_bytes: bytes) -> dict:
    """Transcrit un message vocal OGG et rédige l'email."""
    b64 = base64.standard_b64encode(audio_bytes).decode()
    response = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "audio",
                    "source": {
                        "type": "base64",
                        "media_type": "audio/ogg",
                        "data": b64
                    }
                },
                {
                    "type": "text",
                    "text": "Transcris ce message vocal puis rédige l'email correspondant."
                }
            ]
        }]
    )
    return parse_result(response.content[0].text)


def send_email(subject: str, body: str):
    """Envoie l'email via Resend."""
    html = body.replace("\n", "<br>")
    resend_lib.Emails.send({
        "from": FROM_EMAIL,
        "to": [YOUR_EMAIL],
        "subject": subject,
        "html": f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; 
                    line-height: 1.6; max-width: 600px; color: #333;">
            {html}
        </div>
        """
    })


# ─── Handlers Telegram ────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"👋 Bonjour Pedro !\n\n"
        f"Ton ID Telegram : `{uid}`\n\n"
        "Envoie-moi un *message texte ou vocal* et je rédige ton email pro directement.\n\n"
        "Exemples :\n"
        "• _« Rappel demain appeler fournisseur pour devis fleurs »_\n"
        "• _« Brouillon pour excuser retard livraison au client Dupont »_\n"
        "• _« Préparer mail de suivi pour la réunion de vendredi avec l'équipe »_",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Accès non autorisé.")
        return

    msg = await update.message.reply_text("⏳ Rédaction en cours…")
    try:
        result = draft_from_text(update.message.text)
        send_email(result["subject"], result["body"])
        await msg.edit_text(
            f"✅ Email envoyé sur ta boîte pro !\n\n"
            f"📧 *{result['subject']}*\n"
            f"_{result['summary']}_",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Erreur texte : %s", e)
        await msg.edit_text(f"❌ Erreur : {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    msg = await update.message.reply_text("🎤 Transcription & rédaction…")
    try:
        voice_file = await update.message.voice.get_file()
        voice_bytes = bytes(await voice_file.download_as_bytearray())

        result = draft_from_voice(voice_bytes)
        send_email(result["subject"], result["body"])
        await msg.edit_text(
            f"✅ Email envoyé sur ta boîte pro !\n\n"
            f"📧 *{result['subject']}*\n"
            f"_{result['summary']}_",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Erreur vocal : %s", e)
        await msg.edit_text(f"❌ Erreur : {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    logger.info("✅ Bot démarré — en attente de messages…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
