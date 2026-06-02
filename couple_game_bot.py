"""
🔥 Couple Game Bot +18 — Bot Telegram privé pour couples adultes
Usage : python couple_game_bot.py
Dépendances : pip install python-telegram-bot==20.7
"""

import os
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ──────────────────────────────────────────────
# 🔑  CONFIGURATION
# ──────────────────────────────────────────────
BOT_TOKEN = "8321290945:AAHegvnNP88DKrlhbI2IhxynY7_Qu-eSfY0"          # @BotFather → /newbot
ALLOWED_CHAT_IDS: set[int] = set()        # Rempli dynamiquement au /start
ADMIN_ID = 0                              # Ton user ID Telegram (facultatif)

# ──────────────────────────────────────────────
# 🎲  CONTENU DU JEU
# ──────────────────────────────────────────────

CATEGORIES = {
    "🌶️ Piment doux":   "soft",
    "🔥 Torride":        "hot",
    "💣 Sans limites":   "wild",
    "🎭 Roleplay":       "roleplay",
    "💬 Vérité":         "truth",
    "🃏 Défi":           "dare",
}

QUESTIONS: dict[str, list[str]] = {
    "soft": [
        "Fais un câlin à ton partenaire pendant 60 secondes sans parler.",
        "Dis trois choses que tu adores chez l'autre.",
        "Masse les épaules de ton partenaire pendant 2 minutes.",
        "Embrasse ton partenaire dans le cou pendant 10 secondes.",
        "Chuchote quelque chose de doux à l'oreille de l'autre.",
        "Tiens la main de ton partenaire et ferme les yeux 30 secondes.",
        "Danse lentement ensemble pendant une chanson.",
        "Écris un message tendre et lis-le à voix haute.",
    ],
    "hot": [
        "Embrasse ton partenaire passionnément pendant 30 secondes.",
        "Enlève un vêtement de ton partenaire lentement.",
        "Souffle doucement dans le cou de l'autre pendant 20 secondes.",
        "Donne un massage des pieds à ton partenaire pendant 3 minutes.",
        "Chuchote ta fantaisie préférée à l'oreille de l'autre.",
        "Embrasse lentement l'intérieur du poignet de ton partenaire.",
        "Regarde l'autre dans les yeux sans cligner pendant 1 minute.",
        "Décris ce que tu veux lui faire ce soir.",
    ],
    "wild": [
        "Ton partenaire choisit ce que tu dois faire ensuite — sans refus possible.",
        "Passe 5 minutes les yeux bandés et laisse l'autre décider.",
        "Lis à voix haute ton fantasme le plus secret.",
        "Lance un dé : le chiffre = le nombre de minutes de massage en zone surprise.",
        "Laisse l'autre choisir ta tenue pour la prochaine heure.",
        "Joue à «oui» pendant 10 minutes — tu ne peux que dire oui.",
        "Raconte un souvenir intime en détail.",
        "Swap : chacun joue le rôle de l'autre pendant 5 minutes.",
    ],
    "roleplay": [
        "Scénario : inconnus dans un bar — séduisez-vous mutuellement.",
        "Scénario : prof/étudiant — une leçon très particulière.",
        "Scénario : médecin/patient — bilan de santé approfondi 😏.",
        "Scénario : chef/serveur — le service est très personnalisé.",
        "Scénario : détective/suspect — l'interrogatoire devient chaud.",
        "Scénario : astronaute/alien — premier contact interplanétaire.",
        "Scénario : patron/secrétaire — heures supplémentaires.",
        "Scénario : vampire/victime — une morsure consentie.",
    ],
    "truth": [
        "Quelle est la chose la plus osée que tu aies faite?",
        "Décris ton fantasme que tu n'as jamais avoué.",
        "Quel est l'endroit le plus insolite où tu as eu envie de l'autre?",
        "Qu'est-ce que tu aimerais essayer en couple mais tu n'as pas osé demander?",
        "Quelle partie du corps de l'autre te rend fou/folle?",
        "Raconte ta première pensée intime sur l'autre.",
        "Quel film ou série t'a mis(e) dans l'ambiance le plus vite?",
        "Quelle est ta zone érogène préférée?",
    ],
    "dare": [
        "Envoie un message sensuel à l'autre via Telegram — maintenant.",
        "Fais un strip-tease improvisé de 30 secondes.",
        "Prends une photo artistique et envoie-la à l'autre.",
        "Imite le meilleur baiser de film que tu connais.",
        "Fais semblant d'être dans un film romantique pendant 2 minutes.",
        "Dis 5 compliments physiques très précis sur l'autre.",
        "Invente et lis un poème érotique de 4 vers.",
        "Chante un couplet d'une chanson romantique en regardant l'autre.",
    ],
}

DARES_TIMER = {
    "Le défi des 7 baisers": "Échangez 7 baisers différents en 2 minutes (joue, front, cou, main, oreille, épaule… et le dernier au choix 🔥).",
    "Miroir miroir": "Imitez en miroir les gestes de l'autre pendant 90 secondes.",
    "Hot or Cold": "Un partenaire pense à une zone du corps, l'autre doit trouver en posant des baisers. «Chaud/Froid» comme réponse.",
    "Sculpteur & argile": "Un partenaire est «l'argile» et laisse l'autre poser ses mains là où il/elle veut pendant 60 sec (doux).",
    "La liste de 3": "Chacun écrit 3 choses qu'il aimerait recevoir ce soir. On échange et on lit.",
}

SPIN_BOTTLE = [
    "Embrasse la joue gauche de l'autre.",
    "Embrasse la joue droite de l'autre.",
    "Embrasse les lèvres pendant 5 secondes.",
    "Embrasse le front.",
    "Embrasse le cou.",
    "Embrasse la main.",
    "Donne un câlin.",
    "Chuchote quelque chose de doux.",
]

# ──────────────────────────────────────────────
# 🛡️  SÉCURITÉ / WHITELIST
# ──────────────────────────────────────────────

async def guard(update: Update) -> bool:
    """Autorise uniquement les chats enregistrés."""
    cid = update.effective_chat.id
    if not ALLOWED_CHAT_IDS:          # Premier /start : on enregistre tout
        return True
    if cid not in ALLOWED_CHAT_IDS:
        await update.effective_message.reply_text(
            "⛔ Accès refusé. Ce bot est privé."
        )
        return False
    return True

# ──────────────────────────────────────────────
# 📋  MENUS
# ──────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🎲 Carte aléatoire", callback_data="random")],
        [InlineKeyboardButton("📂 Choisir une catégorie", callback_data="categories")],
        [InlineKeyboardButton("⏱️ Défi chrono", callback_data="timer_dares")],
        [InlineKeyboardButton("🍾 Bouteille qui tourne", callback_data="spin")],
        [InlineKeyboardButton("📊 Score de la soirée", callback_data="score")],
        [InlineKeyboardButton("🔄 Réinitialiser", callback_data="reset")],
    ]
    return InlineKeyboardMarkup(buttons)

def categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(name, callback_data=f"cat_{key}")]
               for name, key in CATEGORIES.items()]
    buttons.append([InlineKeyboardButton("⬅️ Retour", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

def back_keyboard(extra: str = "") -> InlineKeyboardMarkup:
    row = []
    if extra:
        row.append(InlineKeyboardButton("🔁 Encore", callback_data=extra))
    row.append(InlineKeyboardButton("🏠 Menu", callback_data="menu"))
    return InlineKeyboardMarkup([row])

def score_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("➕ Point J1", callback_data="score_p1"),
            InlineKeyboardButton("➕ Point J2", callback_data="score_p2"),
        ],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(buttons)

# ──────────────────────────────────────────────
# 🎮  HANDLERS
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ALLOWED_CHAT_IDS.add(cid)

    # Init score
    if "score" not in context.chat_data:
        context.chat_data["score"] = {"p1": 0, "p2": 0}

    text = (
        "🔥 *Bienvenue dans le Jeu du Couple +18* 🔥\n\n"
        "Ce bot est réservé à un usage *privé entre adultes consentants*.\n"
        "En continuant, vous confirmez avoir *18 ans ou plus*.\n\n"
        "Choisissez une option ci-dessous pour commencer :"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await guard(update):
        return

    data = query.data

    # ── Menu principal ──
    if data == "menu":
        await query.edit_message_text(
            "🏠 *Menu principal*\nQue voulez-vous faire ?",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    # ── Carte aléatoire ──
    elif data == "random":
        cat = random.choice(list(QUESTIONS.keys()))
        card = random.choice(QUESTIONS[cat])
        cat_name = {v: k for k, v in CATEGORIES.items()}[cat]
        await query.edit_message_text(
            f"*{cat_name}*\n\n{card}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("random"),
        )

    # ── Catégories ──
    elif data == "categories":
        await query.edit_message_text(
            "📂 *Choisissez une catégorie :*",
            parse_mode="Markdown",
            reply_markup=categories_keyboard(),
        )

    elif data.startswith("cat_"):
        cat = data[4:]
        if cat not in QUESTIONS:
            await query.answer("Catégorie inconnue.")
            return
        card = random.choice(QUESTIONS[cat])
        cat_name = {v: k for k, v in CATEGORIES.items()}[cat]
        await query.edit_message_text(
            f"*{cat_name}*\n\n{card}",
            parse_mode="Markdown",
            reply_markup=back_keyboard(f"cat_{cat}"),
        )

    # ── Défis chrono ──
    elif data == "timer_dares":
        title, desc = random.choice(list(DARES_TIMER.items()))
        await query.edit_message_text(
            f"⏱️ *Défi Chrono*\n\n*{title}*\n\n{desc}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("timer_dares"),
        )

    # ── Bouteille ──
    elif data == "spin":
        action = random.choice(SPIN_BOTTLE)
        await query.edit_message_text(
            f"🍾 *La bouteille a tourné !*\n\n{action}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("spin"),
        )

    # ── Score ──
    elif data == "score":
        s = context.chat_data.get("score", {"p1": 0, "p2": 0})
        await query.edit_message_text(
            f"📊 *Score de la soirée*\n\n"
            f"Joueur 1 : *{s['p1']}* pts\n"
            f"Joueur 2 : *{s['p2']}* pts",
            parse_mode="Markdown",
            reply_markup=score_keyboard(),
        )

    elif data == "score_p1":
        context.chat_data.setdefault("score", {"p1": 0, "p2": 0})
        context.chat_data["score"]["p1"] += 1
        s = context.chat_data["score"]
        await query.edit_message_text(
            f"📊 *Score de la soirée*\n\n"
            f"Joueur 1 : *{s['p1']}* pts ✅\n"
            f"Joueur 2 : *{s['p2']}* pts",
            parse_mode="Markdown",
            reply_markup=score_keyboard(),
        )

    elif data == "score_p2":
        context.chat_data.setdefault("score", {"p1": 0, "p2": 0})
        context.chat_data["score"]["p2"] += 1
        s = context.chat_data["score"]
        await query.edit_message_text(
            f"📊 *Score de la soirée*\n\n"
            f"Joueur 1 : *{s['p1']}* pts\n"
            f"Joueur 2 : *{s['p2']}* pts ✅",
            parse_mode="Markdown",
            reply_markup=score_keyboard(),
        )

    # ── Reset ──
    elif data == "reset":
        context.chat_data["score"] = {"p1": 0, "p2": 0}
        await query.edit_message_text(
            "🔄 *Partie réinitialisée !*\nLe score a été remis à zéro.\nBonne soirée 🔥",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    await update.message.reply_text(
        "Utilisez /start pour afficher le menu 🏠",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 🚀  LANCEMENT
# ──────────────────────────────────────────────

def main():
    if BOT_TOKEN == "METS_TON_TOKEN_ICI":
        raise ValueError("❌ Remplace BOT_TOKEN par ton vrai token dans le fichier.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("✅ Bot démarré — appuie sur Ctrl+C pour arrêter.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
