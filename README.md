# 📬 Bot Telegram → Email Pro

Envoie un message texte ou vocal depuis Telegram → Claude rédige l'email → il arrive sur ta boîte pro.

---

## Stack

- **python-telegram-bot** — réception des messages
- **Claude API (Anthropic)** — transcription vocale + rédaction email
- **Resend** — envoi de l'email

---

## Setup en 4 étapes

### 1. Créer ton bot Telegram

1. Ouvre Telegram, cherche **@BotFather**
2. Envoie `/newbot`
3. Choisis un nom (ex: `Pedro Mail Bot`) et un username (ex: `pedromailbot`)
4. Copie le **token** fourni → c'est ton `TELEGRAM_TOKEN`

---

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Remplis `.env` avec :
- `TELEGRAM_TOKEN` → token de @BotFather
- `ANTHROPIC_API_KEY` → clé sur [console.anthropic.com](https://console.anthropic.com)
- `RESEND_API_KEY` → clé sur [resend.com](https://resend.com) (gratuit jusqu'à 3 000 mails/mois)
- `YOUR_EMAIL` → ton adresse pro (destinataire)
- `FROM_EMAIL` → adresse expéditeur vérifiée sur Resend
- `ALLOWED_USER_ID` → ton ID Telegram (lance le bot, envoie `/start`, il te l'affiche)

---

### 3. Lancer en local

```bash
pip install -r requirements.txt
python bot.py
```

---

### 4. Héberger sur Railway (gratuit pour usage perso)

1. Va sur [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
2. Upload ce dossier ou connecte ton repo
3. Dans **Variables**, ajoute toutes les variables de ton `.env`
4. Railway détecte automatiquement Python et lance `bot.py`

---

## Utilisation

| Action | Ce que tu envoies | Résultat |
|---|---|---|
| Rappel rapide | `Rappel demain appeler Dupont` | Email [RAPPEL] dans ta boîte |
| Brouillon à transférer | `Brouillon pour retard livraison client Martin` | Email [BROUILLON] prêt à forwarder |
| Message vocal | 🎤 n'importe quelle note vocale | Idem, transcrit automatiquement |

---

## Coûts estimés (usage perso, ~5 msg/jour)

| Service | Coût |
|---|---|
| Telegram | Gratuit |
| Claude API | ~$0.50–1/mois |
| Resend | Gratuit (< 3 000 mails) |
| Railway | Gratuit (hobby tier) |

**Total : quasi gratuit.**
