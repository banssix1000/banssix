from defs import db, js, dr, bt
import telebot
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(js.getDict(dr.config, "bot"))
adicionando_bot = []

def readEditavel(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return str(e)

def getNameUser(userid):
    try:
        f = bot.get_chat(userid).first_name
        l = bot.get_chat(userid).last_name
        return f"{f} {l}" if l else f if f else "None"
    except:
        return "None"

def gerar_paginacao_bots(userid, pagina=1, por_pagina=3):
    bots = bt.get_bots(userid)
    total = len(bots)
    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina
    bots_pagina = bots[inicio:fim]

    texto = f"Seus bots (página {pagina}):"
    markup = InlineKeyboardMarkup()

    for b in bots_pagina:
        texto += f"\n\n@{b['bot_uname']}\n<code>{b['bot_id']}</code>"
        markup.add(
            InlineKeyboardButton("⚙️ Configurar", url=f"https://t.me/{b['bot_uname']}"),
            InlineKeyboardButton("🗑️ Excluir", callback_data=f"del_{b['bot_id']}")
        )

    botoes_nav = []
    if pagina > 1:
        botoes_nav.append(InlineKeyboardButton("⬅️", callback_data=f"pg_{pagina - 1}"))
    if fim < total:
        botoes_nav.append(InlineKeyboardButton("➡️", callback_data=f"pg_{pagina + 1}"))
    if botoes_nav:
        markup.add(*botoes_nav)

    return texto, markup

@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        userid = message.from_user.id
        db.insertUser(userid)
        msg_txt = readEditavel(dr.menu_txt)

        if "<name>" in msg_txt:
            msg_txt = msg_txt.replace("<name>", getNameUser(userid))
        
        if "<botname>" in msg_txt:
            msg_txt = msg_txt.replace("<botname>", f"<a href='tg://user?id={bot.get_me().id}'>{bot.get_me().full_name}</a>")

        mkp = InlineKeyboardMarkup(row_width=2)
        btn_suporte = InlineKeyboardButton('🆘 Suporte', url='https://t.me/CrowleyADM')
        btn_tutorial = InlineKeyboardButton('📺 Tutorial', url='https://youtube.com')
        btn_novo = InlineKeyboardButton("➕ Novo Bot", callback_data="comando_novo")
        btn_bots = InlineKeyboardButton("🤖 Meus Bots", callback_data="comando_bots")
        btn_deletar = InlineKeyboardButton("🗑️ Deletar Bot", callback_data="comando_deletar")
        mkp.add(btn_novo, btn_bots, btn_deletar)
        mkp.add(btn_suporte, btn_tutorial)

        bot.send_message(userid, msg_txt, reply_markup=mkp, parse_mode="HTML")
    except Exception as e:
        print(f"Erro no start_message: {e}")

@bot.message_handler(commands=['novo'])
def novo_bot(message):
    try:
        userid = message.from_user.id
        bot_token = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) == 2 else None

        if userid in adicionando_bot:
            return
        
        adicionando_bot.append(userid)

        if not bot_token:
            adicionando_bot.remove(userid)
            bot.send_message(userid, "Para adicionar um novo bot ao sistema, siga estas instruções:\n\n1. Abra o bot @BotFather no Telegram.\n2. Crie um novo bot usando o comando /newbot e siga as instruções para obter o Token do Bot.\n3. Após obter o token, volte aqui e envie o comando:\n\n/novo <bot_token>")
            return
        
        bot_id = None
        bot_uname = None

        try:
            bto = telebot.TeleBot(bot_token)
            bot_id = bto.get_me().id
            bot_uname = bto.get_me().username
        except:
            pass

        if not bot_id or not bot_uname:
            adicionando_bot.remove(userid)
            bot.send_message(userid, "Token inválido. Verifique o token inserido e tente novamente.")
            return
        
        try:
            msg_to_del = bot.send_message(userid, "⏳").message_id
        except:
            msg_to_del = None

        resultado = bt.new_bot(bot_token, bot_id, userid, bot_uname)

        try:
            bot.delete_message(userid, msg_to_del)
        except:
            pass

        if resultado == "EXISTENTE":
            adicionando_bot.remove(userid)
            bot.send_message(userid, "Esse bot já existe em nosso servidor. Para deletar, use o comando /deletar.")
            return
        
        if "SUCCESS" in resultado:
            adicionando_bot.remove(userid)
            msg = f"Bot adicionado com sucesso! Para configurar, clique no botão abaixo:"
            mkp = InlineKeyboardMarkup(row_width=1)
            btn = InlineKeyboardButton('Configurar Meu Bot', url=f"t.me/{bot_uname}")
            mkp.add(btn)
            bot.send_message(userid, msg, reply_markup=mkp)
            return
        else:
            adicionando_bot.remove(userid)
            bot.send_message(userid, resultado)
    except Exception as e:
        print(f"Erro ao inserir bot: {e}")

@bot.message_handler(commands=['deletar'])
def deletar_bot(message):
    try:
        userid = message.from_user.id
        bot_id = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) == 2 else None

        if not bot_id:
            bot.send_message(userid, "Use o comando nesse formato:\n\n/deletar <bot_id>")
            return
        
        if bt.delete_bot(userid, bot_id):
            bot.send_message(userid, "✅ Bot deletado do servidor com sucesso!")
        else:
            bot.send_message(userid, "Erro ao desativar o bot. Verifique se o ID está correto.")
    except Exception as e:
        print(e)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        userid = call.from_user.id
        data = call.data

        if data == "comando_novo":
            txt = """Vamos criar o seu bot gerenciador em apenas 2 passos!

1. Acesse o @BotFather e crie um novo bot usando o comando /newbot.
Após finalizar, você receberá um token exclusivo.

2. Volte aqui e envie o comando /novo seguido do token que o BotFather te deu.

Exemplo de envio do token:
/novo 123456789:AAH0xE4xmpl3-T0k3n-De-Mostrac4o

> Obs: o token acima é apenas um exemplo. Use o que você receber do BotFather.
Se estiver com dúvidas, confira o vídeo acima com o passo a passo completo.
"""
            bot.send_message(userid, txt, parse_mode="HTML")

        elif data == "comando_bots":
            texto, markup = gerar_paginacao_bots(userid, pagina=1)
            bot.send_message(userid, texto, parse_mode="HTML", reply_markup=markup)

        elif data.startswith("pg_"):
            pagina = int(data.split("_")[1])
            texto, markup = gerar_paginacao_bots(userid, pagina)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=texto,
                                  parse_mode="HTML",
                                  reply_markup=markup)

        elif data.startswith("del_"):
            bot_id = data.split("_", 1)[1]
            if bt.delete_bot(userid, bot_id):
                bot.send_message(userid, f"✅ Bot ID <code>{bot_id}</code> deletado com sucesso!", parse_mode="HTML")
            else:
                bot.send_message(userid, "Erro ao deletar o bot. Verifique se o ID está correto.")

        elif data == "comando_deletar":
            txt = (
                "Para deletar um bot do servidor, use este comando:\n\n"
                "<code>/deletar &lt;bot_id&gt;</code>\n\n"
                "Você pode ver o ID do seu bot usando o botão 'Meus Bots'."
            )
            bot.send_message(userid, txt, parse_mode="HTML")

    except Exception as e:
        print(f"Erro no callback_handler: {e}")

while True:
    try:
        bot.polling()
    except:
        time.sleep(10)
