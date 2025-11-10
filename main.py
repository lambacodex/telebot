from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import os
import logging
import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicializar FastAPI ---
app = FastAPI()

# --- Variables de entorno ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN debe estar configurada como variable de entorno")
if not OWNER_ID:
    raise ValueError("❌ OWNER_ID debe estar configurada como variable de entorno")

# --- Crear e inicializar aplicación de telegram ---
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
    try:
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
                logger.info(f"Mensaje enviado al owner para el usuario {user_id}")
    except Exception as e:
        logger.error(f"Error en handle_message: {e}")

# --- Registrar manejador ---
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Inicializar la aplicación ---
@app.on_event("startup")
async def startup_event():
    """Inicializar la aplicación de Telegram cuando FastAPI inicie"""
    await application.initialize()
    await application.start()
    logger.info("✅ Bot de Telegram inicializado")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar la aplicación de Telegram cuando FastAPI se detenga"""
    await application.stop()
    await application.shutdown()
    logger.info("❌ Bot de Telegram detenido")

# --- Endpoint de Webhook ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return {"status": "error"}, 500

# --- Endpoint para configurar webhook ---
@app.get("/set-webhook")
async def set_webhook():
    try:
        webhook_url = "https://telebot-v0nc.onrender.com/webhook"
        result = await application.bot.set_webhook(webhook_url)
        return {
            "webhook_set": result, 
            "url": webhook_url,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# --- Endpoint para verificar estado ---
@app.get("/")
async def root():
    return {
        "status": "Bot is running!",
        "service": "Telegram Bot",
        "endpoints": {
            "webhook": "/webhook",
            "set_webhook": "/set-webhook"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
