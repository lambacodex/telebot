# ============================================
# 🤖 Telegram Bot - Escucha pasiva con Webhooks
# ============================================

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicializar FastAPI ---
app = FastAPI()

# --- Variables del bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

# Validar variables de entorno
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN debe estar configurada como variable de entorno")
if not OWNER_ID:
    raise ValueError("❌ OWNER_ID debe estar configurada como variable de entorno")

# --- Crear la aplicación de telegram ---
application = Application.builder().token(BOT_TOKEN).build()

# --- Lista de palabras clave ---
KEYWORDS = [
    "nesecito",
    "necesito",
    "pedido", 
    "solicito",
    "quiero",
    "busco",
    "me interesa"
]

# ============================================
# Manejador de mensajes
# ============================================
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
                logger.info(f"✅ Mensaje enviado al owner desde usuario {user_id}")
                
    except Exception as e:
        logger.error(f"❌ Error en handle_message: {e}")

# --- Registrar el handler ---
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ============================================
# INICIALIZACIÓN CRÍTICA - Esto faltaba
# ============================================
@app.on_event("startup")
async def startup_event():
    """Inicializar el bot cuando FastAPI inicia"""
    try:
        await application.initialize()
        await application.start()
        logger.info("✅ Bot de Telegram inicializado correctamente")
    except Exception as e:
        logger.error(f"❌ Error al inicializar bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Detener el bot cuando FastAPI se cierra"""
    try:
        await application.stop()
        await application.shutdown()
        logger.info("✅ Bot de Telegram detenido correctamente")
    except Exception as e:
        logger.error(f"❌ Error al detener bot: {e}")

# ============================================
# Endpoints para Webhook (VERSIÓN FUNCIONAL)
# ============================================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Endpoint principal para recibir mensajes de Telegram
    """
    try:
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.get("/set-webhook")
async def set_webhook():
    """
    Configurar el webhook en Telegram automáticamente
    """
    try:
        webhook_url = "https://telebot-v0nc.onrender.com/webhook"
        result = await application.bot.set_webhook(webhook_url)
        
        # Verificar el webhook configurado
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "webhook_set": result,
            "url": webhook_url,
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count
            },
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/")
async def root():
    return {
        "status": "Bot is running! 🚀",
        "service": "Telegram Bot - Escucha Pasiva",
        "endpoints": {
            "webhook": "POST /webhook",
            "set_webhook": "GET /set-webhook", 
            "health": "GET /health"
        },
        "instructions": "Visita /set-webhook para configurar el bot"
    }

@app.get("/health")
async def health():
    return {"status": "healthy ✅", "bot": "running"}

# ============================================
# Endpoint alternativo con token (para compatibilidad)
# ============================================
@app.post("/webhook/{token}")
async def telegram_webhook_with_token(token: str, request: Request):
    """
    Endpoint alternativo con token en URL (para compatibilidad)
    """
    if token != BOT_TOKEN:
        return Response(status_code=403)
    
    try:
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Error en webhook con token: {e}")
        return {"status": "error"}, 500
