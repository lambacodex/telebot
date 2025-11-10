# ============================================
# 🤖 Telegram Bot - Escucha pasiva con Webhooks
# Desarrollado por: [Tu nombre o alias]
# Descripción:
#   Este bot escucha los mensajes de un grupo de Telegram.
#   Si el mensaje contiene palabras clave como "necesito", "pedido", etc.,
#   reenviará ese mensaje completo a tu chat privado junto con los datos del usuario.
# ============================================

# --- Importaciones necesarias ---
from fastapi import FastAPI, Request, Response       # Para crear el servidor web (endpoint de webhook)
from telegram import Update                          # Representa una actualización de Telegram (mensaje, comando, etc.)
from telegram.ext import Application, MessageHandler, filters  # Motor del bot
import os                                             # Para leer variables de entorno

# --- Inicializar FastAPI (servidor HTTP) ---
app = FastAPI()

# --- Variables del bot desde las variables de entorno ---
# Debes configurarlas en tu hosting (Deta, Railway, etc.)
BOT_TOKEN = os.getenv("BOT_TOKEN")   # Token que te da @BotFather
OWNER_ID = os.getenv("OWNER_ID")   # Tu ID personal de Telegram (para reenviarte los mensajes)

# --- Crear la aplicación de python-telegram-bot ---
# 'Application' es el núcleo del bot; maneja los updates, handlers y contexto
application = Application.builder().token(BOT_TOKEN).build()

# --- Lista de palabras clave a detectar ---
# Puedes añadir, quitar o modificar las que quieras.
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
# Función que maneja cada mensaje recibido
# ============================================
async def handle_message(update: Update, context):
    """
    Esta función se ejecuta cada vez que el bot recibe un mensaje en el grupo.
    Si el mensaje contiene alguna palabra clave, reenvía los detalles al propietario.
    """
    # Verificamos que haya texto (para evitar errores con stickers, fotos, etc.)
    if update.message and update.message.text:
        text = update.message.text.lower()  # Convertimos a minúsculas para comparación insensible a mayúsculas

        # Si el mensaje contiene alguna palabra clave de la lista...
        if any(k in text for k in KEYWORDS):
            user = update.message.from_user  # Usuario que envió el mensaje

            # --- Recopilar información del usuario ---
            username = f"@{user.username}" if user.username else "Sin username"
            fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
            user_id = user.id
            profile_link = f"https://t.me/{user.username}" if user.username else "Sin enlace"

            # --- Crear mensaje de reporte ---
            message = (
                f"📩 *Nuevo mensaje detectado*\n\n"
                f"👤 *Nombre:* {fullname}\n"
                f"🆔 *ID:* `{user_id}`\n"
                f"🔗 *Perfil:* {profile_link}\n"
                f"🏷️ *Username:* {username}\n\n"
                f"💬 *Mensaje:* {update.message.text}"
            )

            # --- Enviar mensaje al propietario ---
            await context.bot.send_message(
                chat_id=int(OWNER_ID),
                text=message,
                parse_mode="Markdown"
            )

            # Nota: el bot no responde en el grupo (modo pasivo)


# --- Registrar el handler (escucha de mensajes de texto que no sean comandos) ---
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ============================================
# Endpoint del webhook
# ============================================
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """
    Endpoint que Telegram usará para enviar actualizaciones (mensajes, etc.).
    Verifica que el token de la URL coincida con el del bot.
    """
    if token != BOT_TOKEN:
        # Seguridad básica: si el token no coincide, se rechaza la petición
        return Response(status_code=403)

    # Convertimos el cuerpo JSON en un objeto Update de Telegram
    body = await request.json()
    update = Update.de_json(body, application.bot)

    # Enviamos la actualización a la cola interna del bot para procesarla
    await application.update_queue.put(update)

    # Respondemos a Telegram para confirmar que todo fue recibido correctamente
    return {"ok": True}


# ============================================
# Instrucciones de despliegue (resumen)
# ============================================
# 1. Crea tu app en Deta Space (Python / FastAPI)
# 2. Añade tus variables de entorno:
#      BOT_TOKEN = el token del bot (@BotFather)
#      OWNER_ID = tu ID personal (usa @userinfobot)
# 3. Despliega el proyecto.
# 4. Obtén tu URL pública (por ejemplo: https://mi-bot.deta.app)
# 5. Configura el webhook:
#      curl -F "url=https://mi-bot.deta.app/webhook/<TU_TOKEN>" https://api.telegram.org/bot<TU_TOKEN>/setWebhook
# 6. Añade el bot a tu grupo y desactiva la privacidad con /setprivacy → Disable.
# 7. Prueba enviando mensajes con las palabras clave (necesito, pedido, etc.).
