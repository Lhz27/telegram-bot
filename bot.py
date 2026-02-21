from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import asyncio  # <-- Voltamos com o asyncio aqui
from flask import Flask
from threading import Thread

# ===============================
# SERVIDOR WEB (OBRIGATÓRIO NO RENDER)
# ===============================

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot está rodando 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ===============================
# TELEGRAM BOT
# ===============================

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📌 Informações"],
        ["💳 Chave PIX"],
        ["❓ Dúvidas Frequentes"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Olá 👋\nEscolha uma opção:",
        reply_markup=reply_markup
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📌 Informações":
        await update.message.reply_text("Aqui vão as informações...")
    elif text == "💳 Chave PIX":
        await update.message.reply_text("Chave PIX: sua-chave@email.com")
    elif text == "❓ Dúvidas Frequentes":
        await update.message.reply_text("Dúvidas Frequentes:\n- Prazo 24h\n- Pagamento via PIX")
    else:
        await update.message.reply_text("Use os botões abaixo 👇")

def main():
    print("Bot rodando...")
    
    # CORREÇÃO PARA O PYTHON 3.14 NO RENDER:
    # Cria e define o loop de eventos manualmente antes de rodar o bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = ApplicationBuilder().token(TOKEN).build()

    # Usando a função start correta
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    # Inicia o bot e o loop de mensagens automaticamente
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    keep_alive()  # abre a porta para o Render na thread do Flask
    main()        # inicia o bot e segura o processo principal
