# ============================================
# 🤖 Telegram Bot - Escucha pasiva con Webhooks
# Compatible con Render (Python 3.11+)
# ============================================

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import os

# --- Inicializar FastAPI ---
app = FastAPI()

# --- Variables de entorno ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

if not BOT_TOKEN or not OWNER_ID:
    raise ValueError("❌ BOT_TOKEN y OWNER_ID deben estar configuradas como variables de entorno")

# --- Crear aplicación de telegram ---
application = Application.builder().token(BOT_TOKEN).build()

# --- Palabras clave ---
KEYWORDS = [
    "nesecito",
    "necesito",
    "pedido",
    "solicito",
    "quiero",
    "busco",
    "me interesa"
]

# --- Manejador de mensajes ---
async def handle_message(update: Update, context):
    if update.message and update.message.text:
        text = update.message.text.lower()
        if any(k in text for k in KEYWORDS):
            user = update.message.from_user
            username = f"@{user.username}" if user.username else "Sin username"
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
            user_id = user.id
            profile_link = f"https://t.me/{user.username}" if user.username else "Sin enlace"

            message = (
                f"📩 *Nuevo mensaje detectado*\n\n"
                f"👤 *Nombre:* {fullname}\n"
                f"🆔 *ID:* `{user_id}`\n"
                f"🔗 *Perfil:* {profile_link}\n"
                f"🏷️ *Username:* {username}\n\n"
                f"💬 *Mensaje:* {update.message.text}"
            )

            await context.bot.send_message(
                chat_id=int(OWNER_ID),
                text=message,
                parse_mode="Markdown"
            )

# --- Registrar manejador ---
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Endpoint de Webhook ---
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return Response(status_code=403)

    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}