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
ADMIN_ID = os.getenv("ADMIN_ID") # Puxa o seu ID lá do Render

# Criamos um "estado" para o bot saber que está esperando um comprovante
RECEBENDO_COMPROVANTE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📌 Informações do evento"],
        ["💳 Chave PIX"],
        ["✅ Enviar Comprovante e Nomes"], # Botão Novo!
        ["❓ Dúvidas Frequentes"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Fala galopeiro!\nEscolha uma opção:",
        reply_markup=reply_markup
    )

# --- INÍCIO DO FLUXO DE COMPRA ---

async def pedir_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Quando a pessoa clica no botão, o bot pede os dados e "trava" esperando a resposta
    await update.message.reply_text(
        "Ótimo! Para confirmar sua entrada, por favor envie a **foto do comprovante do PIX** e escreva os **nomes das pessoas** na legenda da foto.\n\n(Se quiser cancelar o envio, digite /cancelar)"
    )
    return RECEBENDO_COMPROVANTE

async def receber_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Esta função é ativada assim que a pessoa manda a foto/texto
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    if not ADMIN_ID:
        await update.message.reply_text("Erro no sistema: Administrador não configurado.")
        return ConversationHandler.END

    # 1. Encaminha a mensagem EXATA que o cliente mandou (com foto e texto) para o seu chat privado
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    # 2. Manda uma mensagem extra para você com o @ do cliente, caso precise chamar ele no privado
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👆 [NOVA VENDA] Cliente: {username}"
    )

    # 3. Agradece o cliente
    await update.message.reply_text("Já recebemos o seu comprovante, muito obrigado!")
    
    # Retorna o menu inicial para o cliente
    await start(update, context)
    
    # Encerra o "modo de espera"
    return ConversationHandler.END

async def cancelar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envio cancelado. Pode escolher outra opção no menu!")
    return ConversationHandler.END

# --- FIM DO FLUXO DE COMPRA ---

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📌 Informações":
        await update.message.reply_text("Aqui vão as informações sobre o evento... (ainda não informado)")
    elif text == "💳 Chave PIX":
        await update.message.reply_text("Chave PIX: sua-chave@email.com\n\nQyando fizer o pagamento, clique no botão '✅ Enviar Comprovante e Nomes' na tabela abaixo.")
    elif text == "❓ Dúvidas Frequentes":
        await update.message.reply_text("Dúvidas Frequentes:\n- Prazo 24h\n- Pagamento via PIX")
    else:
        await update.message.reply_text("Use os botões abaixo 👇")

def main():
    print("Bot rodando...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = ApplicationBuilder().token(TOKEN).build()

    # O ConversationHandler gerencia o fluxo de receber os dados.
    # Ele pega a pessoa quando ela clica no botão e segura ela até ela mandar a foto/texto.
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✅ Enviar Comprovante e Nomes$"), pedir_comprovante)],
        states={
            # filters.ALL significa que aceita texto, foto, pdf, etc.
            RECEBENDO_COMPROVANTE: [MessageHandler(filters.ALL & ~filters.COMMAND, receber_dados)]
        },
        fallbacks=[CommandHandler("cancelar", cancelar_compra)]
    )

    # A ordem aqui importa: primeiro a conversa de compra, depois os comandos normais
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    keep_alive()  
    main()        
