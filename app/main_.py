import telebot
import re
import datetime
from settings import tg_api_key, tg_chat
from repository import EventRepository, ParticipantRepository, UserRepository

bot = telebot.TeleBot(str(tg_api_key), parse_mode="HTML")


def get_join_keyboard():
    keyboard_join = telebot.types.InlineKeyboardMarkup(row_width=1)
    key_approve = telebot.types.InlineKeyboardButton(text='Записаться/Слиться', callback_data='join')
    keyboard_join.add(key_approve)
    return keyboard_join


def send_direct(chat, message):
    try:
        bot.send_message(chat, message)
    except:
        pass


@bot.message_handler(commands=['mute'])
def mute_user(message):
    telegram_tag = message.from_user.username

    if not telegram_tag:
        faq_url = 'https://telegram.org/faq#q-what-are-usernames-how-do-i-get-one'
        msg = f'Что бы записаться на мероприятие, <a href="{faq_url}">настрой</a> никнейм'
        send_direct(message.from_user.id, msg)
        return

    ur = UserRepository()
    user = ur.get_user(tg=telegram_tag)
    if not user:
        return

    mute = user.get("fields").get("mute", None)

    if mute:
        ur.toggle_mute(telegram_tag, False)
        bot.reply_to(message, '<strong>Тихий режим</strong> отключен.')
    else:
        ur.toggle_mute(telegram_tag, True)
        bot.reply_to(message, '<strong>Тихий режим</strong> включен.')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    ur = UserRepository()

    reply = '<b>Привет! Я — электронный помощник для поиска группы</b>\n\n'
    reply += '👑<b>Если вы ищете еще людей:</b>\n\n'
    reply += 'вводите команду <u>/lfg</u>, вот ее формат: \n\n'
    reply += '<code>/lfg [мероприятие] +N [дата] [время мск]</code>\n\n'
    reply += 'Например:\n\n'
    reply += '<code>/lfg вог мастер +5 25.08.2021 17:00</code>\n\n'
    reply += '<code>Вместо даты вы можете</code> использовать слова ‘завтра’, ‘сегодня’ или ‘сейчас’\n\n'
    reply += '💪<b>Если вы хотите присоединиться к другой команде:</b>\n\n'
    reply += 'Жмите кнопку под интересующим вас постом. Я бот умный, но мне нужно время на принятие запроса, ' \
             'так что жмите один раз и ждите пару секунд. Спамить не надо :)\n\n '
    reply += '⚠️Важное:\n\n'
    reply += 'Я работаю только со стражами, у которых настроен никнейм в телеграме.\n\n'
    reply += 'Чтобы получать уведомления, напиши в ЛС @gfm_lfg_bot команду <code>/start</code>\n\n'
    reply += 'Отключить уведомления можно через <code>/mute</code>\n\n'
    reply += '☠️<b>Удаление поста</b>: если лидер нажмет "Слиться", мероприяте будет удалено!\n\n'
    reply += 'Удачи в бою!'

    telegram_tag = message.from_user.username
    if telegram_tag:
        user = ur.get_user(tg=telegram_tag)
        if not user:
            ur.add_user(tg_chat_id=message.from_user.id, tg=telegram_tag)

    # bot.reply_to(message, reply)
    send_direct(message.from_user.id, reply)


@bot.callback_query_handler(lambda call: call.data in ['join'])
def prove_callback(call):
    telegram_tag = call.from_user.username

    if not telegram_tag:
        faq_url = 'https://telegram.org/faq#q-what-are-usernames-how-do-i-get-one'
        msg = f'Что бы записаться на мероприятие, <a href="{faq_url}">настрой</a> никнейм'
        send_direct(call.from_user.id, msg)
        return

    pr = ParticipantRepository()
    er = EventRepository()
    ur = UserRepository()

    event = er.get_event(tg_post_id=call.message.message_id)
    if not event:
        return

    event_id = event.get('id')
    event_data = event.get('fields')
    disc = event_data.get("disc", None)

    leader_user = ur.get_user(tg=event_data.get("tg"))
    mute = leader_user.get("fields").get("mute", None)

    date = datetime.datetime.strptime(event_data.get("date"), '%Y-%m-%dT%H:%M:%S.%fZ')

    participants = pr.get_event_participants(tg_post_id=call.message.message_id)
    slots = int(event_data.get("slots"))

    deleted = False

    reply_list = ''

    if event_data.get("tg") == telegram_tag:
        if not mute:
            send_direct(call.from_user.id, 'Ты слился, мероприяте было удалено')

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        er.delete(record=event_id)
        return

    participants_list = list()

    if participants:
        for p in participants:
            user = p.get('fields').get('tg')

            if user == telegram_tag:
                record = p.get('id')
                pr.del_participant(record=record)
                deleted = True

                if leader_user and not mute:
                    leader_msg = f'С вашего мероприятия <code>{event_data.get("name")}</code> слился @{telegram_tag}'
                    send_direct(leader_user.get("fields").get("tg_chat_id"), leader_msg)
            else:
                participants_list.append(user)
                reply_list += f'@{user}\n'

    free_space = slots - len(participants_list)

    if not deleted and free_space > 0:
        pr.add_participant(event_id=event_id, tg=telegram_tag, tg_post_id=call.message.message_id)
        reply_list += f'@{telegram_tag}\n'
        free_space -= 1

        if leader_user and not mute:
            leader_msg = f'На ваше мероприятие <code>{event_data.get("name")}</code> записался @{telegram_tag}'
            send_direct(leader_user.get("fields").get("tg_chat_id"), leader_msg)

    reply = f'<b>Мероприятие:</b> {event_data.get("name")}\n'
    reply += f'<b>Мест:</b> {free_space}\n'
    reply += f'<b>Когда:</b> {date.strftime("%d.%m.%Y, %H:%M")} МСК\n'
    reply += f'<b>Лидер:</b> @{event_data.get("tg")}\n'
    if disc:
        reply += f'<b>Discord:</b> <a href="https://{disc}">{disc}</a>\n'

    if reply_list:
        reply += f'<b>Записались:</b>\n'
        reply += reply_list

    if reply != call.message.message_id:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=reply,
            reply_markup=get_join_keyboard()
        )


@bot.message_handler(commands=['lfg'])
def lfg(message):
    event_rep = EventRepository()
    text = message.text[5:]

    reg_name_stack = r'^(.*)\+([0-9]+)'
    reg_date = r'[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9]\.[0-9]{2,4}'
    reg_time = r'(([01]\d|2[0-3]):([0-5]\d)|24:00)'
    reg_disc = r'discord.gg/(.*)'

    # достаем название и количество участников (-1)
    q = re.search(reg_name_stack, text)
    leader = message.from_user.username

    if not q:
        bot.reply_to(message, 'Страж, я тебя не понял.\nФормат команды: /lfg [мероприятие] +N [дата] [время]')
        return

    if not leader:
        faq_url = 'https://telegram.org/faq#q-what-are-usernames-how-do-i-get-one'
        bot.reply_to(message, f'Что бы создавать мероприятия, <a href="{faq_url}">настрой</a> никнейм')
        return

    name = q.group(1)
    slots = int(q.group(2))

    if slots > 12:
        slots = 12

    if slots < 1:
        bot.reply_to(message, 'Страж, я тебя не понял.\nФормат команды: /lfg [мероприятие] +N [дата] [время]')
        return

    # достаем дату
    date_query = re.search(reg_date, text)
    now = False

    if date_query:
        date = datetime.datetime.strptime(date_query.group(0), '%d.%m.%Y')
    elif 'послезавтра' in text:
        date = datetime.datetime.today() + datetime.timedelta(days=2)
    elif 'завтра' in text:
        date = datetime.datetime.today() + datetime.timedelta(days=1)
    else:
        tzinfo = datetime.timezone(datetime.timedelta(hours=+3))
        date = datetime.datetime.now(tzinfo)
        now = True

    # достаем время
    time_query = re.search(reg_time, text)

    if time_query:
        now = False
        hour = int(time_query.group(2))
        minute = int(time_query.group(3))
        date = date.replace(hour=hour, minute=minute)

    if not now and not time_query:
        bot.reply_to(message, 'Страж, я тебя не понял.\nФормат команды: /lfg [мероприятие] +N [дата] [время]')
        return

    # discord
    disc_query = re.search(reg_disc, text)

    reply = f'<b>Мероприятие:</b> {name}\n'
    reply += f'<b>Мест:</b> {slots}\n'
    reply += f'<b>Когда:</b> 🔥Прямо сейчас!🔥\n' if now else f'<b>Когда:</b> {date.strftime("%d.%m.%Y, %H:%M")} МСК\n'
    reply += f'<b>Лидер:</b> @{leader}\n'
    disc = ""
    if disc_query:
        disc = disc_query.group(0)
        reply += f'<b>Discord:</b> <a href="https://{disc}">{disc}</a>\n'

    ms = bot.send_message(tg_chat, reply, reply_markup=get_join_keyboard())
    event_rep.add_event(name=name, slots=slots, date=date, tg_post_id=ms.message_id, tg=leader, disc=disc)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
