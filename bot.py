from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import os
import asyncio
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
ADMIN_ID = os.getenv("ADMIN_ID")

RECEBENDO_COMPROVANTE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 👉 MUDE O TEXTO AQUI: Nomes dos botões do menu principal
    # Atenção: Se mudar aqui, tem que mudar lá embaixo no 'async def responder' também!
    keyboard = [
        ["📌 Informações do evento"],
        ["💳 Chave PIX"],
        ["✅ Enviar Comprovante e Nomes"],
        ["❓ Dúvidas Frequentes"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # 👉 MUDE O TEXTO AQUI: Mensagem de boas-vindas quando a pessoa abre o bot ou manda /start
    await update.message.reply_text(
        "Fala galopeiro!\nEscolha uma opção abaixo:",
        reply_markup=reply_markup
    )

# --- INÍCIO DO FLUXO DE COMPRA ---

async def pedir_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 👉 MUDE O TEXTO AQUI: O que o bot fala quando a pessoa clica em "Enviar Comprovante"
    await update.message.reply_text(
        "Ótimo! Para confirmar sua entrada, por favor envie a foto do comprovante do PIX e escreva os nomes das pessoas na legenda da foto.\n\n⚠️ (Se clicou sem querer, digite /cancelar para voltar ao menu)"
    )
    return RECEBENDO_COMPROVANTE

async def receber_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    if not ADMIN_ID:
        await update.message.reply_text("Erro no sistema: Administrador não configurado.")
        return ConversationHandler.END

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👆 [NOVA VENDA] Cliente: {username}"
    )

    # 👉 MUDE O TEXTO AQUI: O que o bot responde DEPOIS que a pessoa manda o comprovante
    await update.message.reply_text("Já recebemos o seu comprovante, muito obrigado! Em breve confirmamos sua entrada.")
    
    await start(update, context)
    return ConversationHandler.END

async def cancelar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 👉 MUDE O TEXTO AQUI: Mensagem caso a pessoa digite /cancelar na hora do comprovante
    await update.message.reply_text("Envio cancelado. Pode escolher outra opção no menu!")
    return ConversationHandler.END

# --- FIM DO FLUXO DE COMPRA ---

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 👇 As regras abaixo conectam os botões com as respostas 👇

    if text == "📌 Informações do evento":
        # 👉 MUDE O TEXTO AQUI: Resposta do botão de informações
        await update.message.reply_text("Aqui vão as informações sobre o evento... (ainda não informado)")
        
    elif text == "💳 Chave PIX":
        # 👉 MUDE O TEXTO AQUI: Resposta do botão da Chave PIX
        await update.message.reply_text("Chave PIX: sua-chave@email.com\n\nQuando fizer o pagamento, clique no botão '✅ Enviar Comprovante e Nomes' na tabela abaixo.")
        
    elif text == "❓ Dúvidas Frequentes":
        # 👉 MUDE O TEXTO AQUI: Resposta do botão de Dúvidas
        await update.message.reply_text("Dúvidas Frequentes:\n- Prazo 24h\n- Pagamento via PIX")
        
    else:
        # 👉 MUDE O TEXTO AQUI: Se a pessoa digitar qualquer texto aleatório que não é um botão
        await update.message.reply_text("Por favor, use os botões abaixo para navegar 👇")

def main():
    print("Bot rodando...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✅ Enviar Comprovante e Nomes$"), pedir_comprovante)],
        states={
            RECEBENDO_COMPROVANTE: [MessageHandler(filters.ALL & ~filters.COMMAND, receber_dados)]
        },
        fallbacks=[CommandHandler("cancelar", cancelar_compra)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    keep_alive()  
    main()
