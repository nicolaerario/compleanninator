import telebot
from telebot import types
import os
from dotenv import load_dotenv
from database import db
from datetime import datetime

load_dotenv()

bot = telebot.TeleBot(os.environ["BOT_TOKEN"])
start_time = datetime.utcnow()

person = []


@bot.message_handler(commands=["start"])  # on /start
def send_welcome(message):
    bot.reply_to(message, "Ciao! Grazie per avermi aggiunto, usa /help per iniziare")


@bot.message_handler(commands=["help"])  # on /help
def send_help(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        chat_id = message.chat.id
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        add = types.InlineKeyboardButton("/add")
        remove = types.InlineKeyboardButton("/remove")
        list_command = types.InlineKeyboardButton("/list")
        markup.add(add, remove, list_command)  # creates a button keyboard on Telegram
        bot.send_message(
            chat_id, "Ecco i comandi che puoi utilizzare:", reply_markup=markup
        )


@bot.message_handler(commands=["add"])  # on /add
def add_birthday(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        person.clear()
        chat_id = message.chat.id
        msg = bot.send_message(
            chat_id,
            "Chi sarà il festeggiato?\n\nPuoi annullare l'operazione in qualsiasi momento scrivendo 'Cancella'",
        )
        bot.register_next_step_handler(msg, set_name)


def set_name(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        if message.text.upper() == "CANCELLA":
            bot.send_message(message.chat.id, "Va bene, annullo l'operazione")
        else:
            chat_id = message.chat.id
            name = message.text
            isUsed = False
            for x in db.extract_data():  # checks if the name is not already used
                if not isUsed:
                    if (name.upper(), str(chat_id)) == (x[0].upper(), x[2]):
                        isUsed = True
                        msg = bot.send_message(
                            chat_id, "Hai già usato questo nome, inseriscine un altro."
                        )
                        bot.register_next_step_handler(msg, set_name)
            if not isUsed:
                person.append(name)
                msg = bot.send_message(
                    chat_id, "Quando compie gli anni?\nEs: 13/01/2004"
                )
                bot.register_next_step_handler(msg, set_date)


def set_date(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        if message.text.upper() == "CANCELLA":
            bot.send_message(message.chat.id, "Va bene, annullo l'operazione")
        else:
            chat_id = message.chat.id
            date = message.text
            try:
                datetime.strptime(date, "%d/%m/%Y")  # validates the date
                person.append(date)
                person.append(chat_id)
                msg = bot.send_message(chat_id, "Confermi? Si o No")
                bot.register_next_step_handler(msg, confirm)
            except:  # if date not valid
                msg = bot.send_message(chat_id, "La data non è valida... Riprova")
                bot.register_next_step_handler(msg, set_date)


def confirm(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        chat_id = message.chat.id
        if message.text.upper() == "SI":
            try:
                db.insert_data(
                    person[0], person[1], person[2]
                )  # inserts data into the database
                bot.send_message(
                    chat_id, "È ufficiale! ti ricorderò di questo compleanno"
                )
            except:
                bot.send_message(chat_id, "Mi dispiace, qualcosa è andato storto")
            person.clear()
        elif message.text.upper() == "NO" or "CANCELLA":
            person.clear()
            bot.send_message(chat_id, "Va bene, non ti notificherò")
        else:
            msg = bot.send_message(chat_id, "La risposta deve essere o Si o No")
            bot.register_next_step_handler(msg, confirm)


@bot.message_handler(commands=["remove"])  # on /remove
def remove_birthday(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        person.clear()
        msg = bot.send_message(
            message.chat.id,
            "Chi era il festeggiato?\n\nPuoi annullare l'operazione in qualsiasi momento scrivendo 'Cancella'",
        )
        bot.register_next_step_handler(msg, remove_name)


def remove_name(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        if message.text.upper() == "CANCELLA":
            bot.send_message(message.chat.id, "Va bene, annullo l'operazione")
        else:
            chat_id = message.chat.id
            name = message.text
            person.append(name)
            person.append(chat_id)
            msg = bot.send_message(chat_id, "Confermi? Si o No")
            bot.register_next_step_handler(msg, remove_confirm)


def remove_confirm(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        chat_id = message.chat.id
        count = 0
        if message.text.upper() == "SI":
            try:
                for x in db.extract_data():
                    if (person[0].upper(), str(person[1])) == (
                        x[0].upper(),
                        x[2],
                    ):  # checks if the reminder exists
                        db.delete_data(x[0], person[1])
                        bot.send_message(
                            chat_id, "Va bene, non notificherò più questo compleanno"
                        )
                        count += 1
                if count == 0:  # if the reminder doesn't exist
                    bot.send_message(
                        chat_id, "Il compleanno che vuoi eliminare non esiste"
                    )
            except:
                bot.send_message(chat_id, "Mi dispiace, qualcosa è andato storto")
            person.clear()
        elif message.text.upper() == "NO" or "CANCELLA":
            person.clear()
            bot.send_message(chat_id, "Va bene, non lo annullerò")
        else:
            msg = bot.send_message(chat_id, "La risposta deve essere o Si o No")
            bot.register_next_step_handler(msg, confirm)


@bot.message_handler(commands=["list"])  # on /list
def list_birthdays(message):
    if datetime.utcfromtimestamp(message.date) < start_time:
        pass
    else:
        chat_id = message.chat.id
        msg_string = ""
        data = db.extract_data()
        for x in data:
            if x[2] == str(
                message.chat.id
            ):  # list the reminder of the person who requested
                msg_string += f"{x[0]}, {x[1]}\n"
        if msg_string != "":
            bot.send_message(chat_id, msg_string)
        else:
            bot.send_message(chat_id, "Non hai registrato nessun compleanno")


bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()
bot.polling()
