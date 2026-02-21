from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
import asyncio

# Pega o token da variável de ambiente do Render
TOKEN = os.getenv("TOKEN")

async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Criação do app
app = ApplicationBuilder().token(TOKEN).build()

# Handlers
app.add_handler(CommandHandler(["start", "iniciar"], iniciar))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))


# Inicialização compatível com Python 3.14
async def main():
    print("Bot rodando...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    asyncio.run(main())
