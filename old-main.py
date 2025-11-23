#Костыльно-Ориентированные Программирование <3

import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_filters
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.states.sync.context import StateContext
from telebot.states.asyncio.middleware import StateMiddleware
bot = AsyncTeleBot


class Chats:
    globalchat = []
    communitychats = [[],[]]

class UserData:
    username = ['bittjs','df']
    chat_id = [1296374036,7687856888]

class States(StatesGroup):
    NoneState = State()
    ChatState = State()
    SetNameState = State()

async def error_handler(message, text):
    print('error: "' + text + '" for', message.from_user.id, '(' + message.from_user.first_name + ') | message: ' + message.text)
    await bot.send_message(message.chat.id, '❗️Что то пошло не так, обратитесь напрямую к @bittjs')
    #добавить логгинг ошибок и приписание к ним айдищников
    
@bot.message_handler(commands=['setname'])
async def setname_q(message):
    await bot.send_message(message.chat.id, "Какой ник вы хотите поставить?")
    await bot.set_state(user_id=message.from_user.id, state=States.SetNameState, chat_id=message.chat.id)

#надо ли в чате предупреждать о смене имени?
#добавить разделение в консоли замены существующего имени и показывать прошлое
@bot.message_handler(state=States.SetNameState)
async def setname_a(message):
    name = message.text
    if len(name) >  32:
        await bot.send_message(message.chat.id, '❗️Введённое имя сликшом большое. Лимит - 32 символа.')
    else:
        if len(UserData.chat_id) == len(UserData.username):
            if message.chat.id in UserData.chat_id:
                UserData.username.remove(UserData.username[UserData.chat_id.index(message.chat.id)])
                UserData.chat_id.remove(message.chat.id)
            UserData.username.append(name)
            UserData.chat_id.append(message.chat.id)
            print(name, 'добавлен с id:', message.chat.id)
            await bot.send_message(str(message.chat.id), 'Теперь вы будете отображаться как: ' + name)
        else:
            await error_handler(message, 'Lists not linked')
        await bot.set_state(user_id=message.from_user.id, state=States.ChatState, chat_id=message.chat.id)
# в зависимости от кур стэйта менять его

@bot.message_handler(commands=['start','help'])
async def start(message):
    helptext = 'Добро пожаловать, это бот-команата!\nЧтобы получить возможность войти, укажите свой ник через /setname\nДля присоеденения: /join\nДля выхода: /leave'
    await bot.reply_to(message, helptext)

@bot.message_handler(commands=['join'])
async def join(message):
    if message.chat.id not in UserData.chat_id:
        await bot.send_message(message.chat.id, '❗️Вероятно у вас не задан Никнейм, используйте /setname')
    else:
        chat = message.text.split()[1:]
        if len(chat) > 1:
            await bot.reply_to(message, '❗️Неверный параметр чата')
        else:
            if not chat:
                if message.chat.id not in Chats.globalchat: 
                    Chats.globalchat.append(message.chat.id)
                    name = UserData.username[UserData.chat_id.index(message.chat.id)]
                    print(name + ' joined the global room')
                    await bot.set_state(user_id=message.from_user.id, state=States.ChatState, chat_id=message.chat.id)
                    await bot.reply_to(message, 'Ваш чат был успешно добавлен!')
                    await sysmsg(message, name, Chats.globalchat, 'join')
                else: await bot.reply_to(message, '❗️Вы уже находитесь в чате')
            else:
                chatid = int(chat[0])
                if chatid <= len(Chats.communitychats):
                    if message.chat.id not in Chats.communitychats[chatid-1]:
                        Chats.communitychats[chatid-1].append(message.chat.id)
                        name = UserData.username[UserData.chat_id.index(message.chat.id)]
                        print(name, 'joined room_id:', chatid)
                        await bot.set_state(user_id=message.from_user.id, state=States.ChatState, chat_id=message.chat.id)
                        await bot.reply_to(message, 'Ваш чат был успешно добавлен!')
                        await sysmsg(message, name, Chats.communitychats[chatid-1], 'join')
                    else: await bot.reply_to(message, '❗️Вы уже находитесь в чате')

@bot.message_handler(commands=['leave'])
async def leave(message):
    name = UserData.username[UserData.chat_id.index(message.chat.id)]
    if message.chat.id in Chats.globalchat:
        Chats.globalchat.remove(message.chat.id)
        print(name + ' left the room')
        await bot.set_state(user_id=message.from_user.id, state=States.NoneState, chat_id=message.chat.id)
        await bot.reply_to(message, 'Вы успешно вышли из комнаты.')
        await sysmsg(message, name, Chats.globalchat, 'leave')
    else: 
        for innerchat in Chats.communitychats:
            if message.chat.id in innerchat:
                innerchat.remove(message.chat.id)
                await bot.set_state(user_id=message.from_user.id, state=States.NoneState, chat_id=message.chat.id)
                await bot.reply_to(message, 'Вы успешно вышли из комнаты.')
                await sysmsg(message, name, innerchat, 'leave')
            else: await bot.reply_to(message, '❗️Вы не находитесь в комнате.')

async def sysmsg(message, name, chatgroup, type):
    for chat in chatgroup:
        match type:
            case 'join':
                await bot.send_message(chat, '- ' + name + ' врывается в комнату! -')
            case 'leave':
                await bot.send_message(chat, '- ' + name + ' ливает с позором -')
            case 'user':
                if chat != message.chat.id:
                    await bot.send_message(chat, name + ': ' + message.text)
    if type == 'user': print(name + ': ' + message.text)

#после лива "index expected at least 1 argument, got 0"
@bot.message_handler(func=lambda message: True, state=States.ChatState)
async def chat_loop(message):
    name = UserData.username[UserData.chat_id.index(message.chat.id)]
    if message.chat.id in Chats.globalchat:
        await sysmsg(message,name,Chats.globalchat, 'user')
    else: 
        for innerchat in Chats.communitychats:
            if message.chat.id in innerchat:
                await sysmsg(message,name,innerchat, 'user')
                
'''
@bot.message_handler(func=lambda message: True, state=States.ChatState, content_types=["text","photo", "documents"])
async def chat_loop(message):
    name = UserData.username[UserData.chat_id.index(message.chat.id)]
    if message.chat.id in Chats.globalchat:
        for chat in Chats.globalchat:
            if chat != message.chat.id:
                print(1)
                if message.content_type == "text":
                    await bot.send_message(chat, name + ': ' + message.text)
                    print(name + ': ' + message.text)
                else:
                    await bot.send_message(chat, name + ':')
                    match message.content_type:
                        case 'photo':
                            await bot.send_photo(message.chat.id, message.photo.file_id)
                            print(name + ' sent photo ')
'''

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.setup_middleware(StateMiddleware(bot))
asyncio.run(bot.polling())