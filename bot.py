from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
import os
import asyncio
import random
import traceback
import smtplib
from email.mime.text import MIMEText
from flask import Flask
from threading import Thread
import re

# ===============================
# SERVIDOR WEB (RENDER)
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
# CONFIGURAÇÕES DO BOT E EMAIL
# ===============================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Variáveis para o envio de email (Configuradas no Render)
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")

# Estados da conversa
RECEBENDO_COMPROVANTE, CONFIRMANDO_DADOS = range(2)

# ===============================
# SISTEMA DE LOGS POR EMAIL
# ===============================
def enviar_email_erro(erro_texto):
    if not EMAIL_REMETENTE or not EMAIL_SENHA or not EMAIL_DESTINATARIO:
        print("Credenciais de email não configuradas. Erro não enviado.")
        return
    
    msg = MIMEText(f"🚨 Ocorreu um erro no seu Bot do Telegram:\n\n{erro_texto}")
    msg['Subject'] = '🚨 Erro Crítico no Bot'
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
            smtp.send_message(msg)
        print("Email de erro enviado com sucesso!")
    except Exception as e:
        print(f"Falha ao enviar email: {e}")

async def manipulador_de_erros(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Exceção detectada pelo manipulador de erros!")
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    print(tb_string)
    # Dispara o email em segundo plano para não travar o bot
    Thread(target=enviar_email_erro, args=(tb_string,)).start()

# ===============================
# FLUXOS DO MENU E CLIENTE
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agora usamos botões Inline (transparentes)
    keyboard = [
        [InlineKeyboardButton("📌 Informações do evento", callback_data='info')],
        [InlineKeyboardButton("💳 Chave PIX", callback_data='pix')],
        [InlineKeyboardButton("✅ Enviar Comprovante e Nomes", callback_data='comprar')],
        [InlineKeyboardButton("❓ Dúvidas Frequentes", callback_data='duvidas')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    texto = "Fala galopeiro! 🐎\nEscolha uma opção abaixo:"
    
    # Verifica se veio de um comando /start ou de um botão (Callback)
    if update.message:
        await update.message.reply_text(texto, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(texto, reply_markup=reply_markup)

async def botoes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Avisa o Telegram que o botão foi clicado
    
    dados = query.data

    if dados == 'info':
        await query.message.reply_text("Aqui vão as informações sobre o evento... (ainda não informado)")
    elif dados == 'pix':
        await query.message.reply_text("Chave PIX: sua-chave@email.com\n\nQuando fizer o pagamento, clique em '✅ Enviar Comprovante e Nomes' no menu principal.")
    elif dados == 'duvidas':
        await query.message.reply_text("Dúvidas Frequentes:\n- Prazo 24h\n- Pagamento via PIX")

# ===============================
# FLUXO DE COMPRA E CONFIRMAÇÃO
# ===============================
async def pedir_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Ótimo! Para confirmar sua entrada, por favor envie a **foto do comprovante do PIX** e escreva os **nomes das pessoas na legenda da foto**.\n\n⚠️ (Para cancelar, digite /cancelar)"
    )
    return RECEBENDO_COMPROVANTE

async def receber_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Guarda os dados da mensagem temporariamente
    context.user_data['mensagem_compra'] = update.message
    
    # Extrai o texto (seja da legenda da foto ou mensagem de texto puro)
    texto_nomes = update.message.caption if update.message.caption else update.message.text
    
    keyboard = [
        [InlineKeyboardButton("✅ Sim, confirmar", callback_data='confirma_sim')],
        [InlineKeyboardButton("❌ Não, enviar de novo", callback_data='confirma_nao')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Você enviou os seguintes dados para a lista:\n\n{texto_nomes}\n\nPodemos confirmar e enviar para aprovação?",
        reply_markup=reply_markup
    )
    return CONFIRMANDO_DADOS

async def processar_confirmacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirma_nao':
        await query.message.reply_text("Sem problemas. Envie a foto com os nomes novamente ou digite /cancelar.")
        return RECEBENDO_COMPROVANTE
        
    elif query.data == 'confirma_sim':
        user = query.from_user
        username = f"@{user.username}" if user.username else user.first_name
        user_id = user.id
        
        # Gera o número do ingresso
        codigo_ingresso = f"#GALOPE-{random.randint(1000, 9999)}"
        
        mensagem_original = context.user_data.get('mensagem_compra')
        
        # Encaminha a foto pro grupo
        await context.bot.forward_message(
            chat_id=ADMIN_ID,
            from_chat_id=mensagem_original.chat_id,
            message_id=mensagem_original.message_id
        )
        
        # Manda os dados pro admin com o ID escondido para podermos aprovar
        texto_admin = (
            f"🎟️ [NOVA VENDA PARA APROVAR]\n"
            f"👤 Cliente: {username}\n"
            f"🎫 Ingresso Gerado: {codigo_ingresso}\n"
            f"🆔 ID: {user_id}\n\n"
            f"👉 RESPONDA ESTA MENSAGEM com /aprovar ou /rejeitar"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=texto_admin)

        await query.edit_message_text(f"✅ Seus dados foram enviados com sucesso!\nO seu código de ingresso é **{codigo_ingresso}**.\n\nAguarde, nossa equipe vai conferir o PIX e te enviar a aprovação por aqui em breve!")
        
        # Limpa os dados e encerra
        context.user_data.clear()
        return ConversationHandler.END

async def cancelar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envio cancelado.")
    await start(update, context)
    return ConversationHandler.END

# ===============================
# APROVAÇÃO PELO GRUPO (ADMIN)
# ===============================
async def admin_aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verifica se o administrador está respondendo a uma mensagem do bot
    if not update.message.reply_to_message:
        await update.message.reply_text("Você precisa RESPONDER a mensagem de uma venda usando /aprovar.")
        return

    texto_original = update.message.reply_to_message.text
    
    # Extrai o ID do usuário que estava na mensagem (ex: "🆔 ID: 123456")
    match = re.search(r"🆔 ID: (\d+)", texto_original)
    if match:
        user_id = int(match.group(1))
        # Extrai o número do ingresso
        match_ingresso = re.search(r"🎫 Ingresso Gerado: (#GALOPE-\d+)", texto_original)
        ingresso = match_ingresso.group(1) if match_ingresso else "Ingresso Confirmado"
        
        try:
            # Envia mensagem no privado do cliente
            await context.bot.send_message(
                chat_id=user_id, 
                text=f"🎉 **PAGAMENTO APROVADO!** 🎉\n\nSua entrada está garantida. Guarde o seu código: **{ingresso}**\nNos vemos no evento!"
            )
            await update.message.reply_text("✅ Cliente notificado da APROVAÇÃO com sucesso!")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao avisar o cliente: {e}")
    else:
        await update.message.reply_text("Não consegui encontrar o ID do cliente nessa mensagem.")

async def admin_rejeitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    texto_original = update.message.reply_to_message.text
    match = re.search(r"🆔 ID: (\d+)", texto_original)
    if match:
        user_id = int(match.group(1))
        try:
            await context.bot.send_message(
                chat_id=user_id, 
                text="❌ **Atenção:** Houve um problema com a conferência do seu pagamento ou comprovante. Por favor, inicie o atendimento novamente ou chame um administrador."
            )
            await update.message.reply_text("❌ Cliente notificado da REJEIÇÃO.")
        except Exception as e:
            await update.message.reply_text(f"Erro: {e}")

# ===============================
# MAIN
# ===============================
def main():
    print("Iniciando Bot...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Configura o tratador de erros para mandar email
    application.add_error_handler(manipulador_de_erros)

    # Fluxo de Compra
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(pedir_comprovante, pattern='^comprar$')],
        states={
            RECEBENDO_COMPROVANTE: [MessageHandler(filters.ALL & ~filters.COMMAND, receber_dados)],
            CONFIRMANDO_DADOS: [CallbackQueryHandler(processar_confirmacao, pattern='^confirma_')]
        },
        fallbacks=[CommandHandler("cancelar", cancelar_compra)]
    )

    application.add_handler(conv_handler)
    
    # Comandos Administrativos (Só funcionam em grupos)
    application.add_handler(CommandHandler("aprovar", admin_aprovar, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("rejeitar", admin_rejeitar, filters=filters.ChatType.GROUPS))
    
    # Comandos Básicos
    application.add_handler(CommandHandler("start", start))
    
    # Lida com os outros botões do menu Inline
    application.add_handler(CallbackQueryHandler(botoes_menu, pattern='^(info|pix|duvidas)$'))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    keep_alive()
    main()
