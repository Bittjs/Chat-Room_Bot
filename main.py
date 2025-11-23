import asyncio
from telebot.async_telebot import AsyncTeleBot
from typing import List

from UserManager import UserStates, UserManager
from ChatRoomManager import ChatRoomsManager
from config import BOT_TOKEN
class ChatBot:
    def __init__(self, token: str):
        self.bot = AsyncTeleBot(token)
        self.rooms_manager = ChatRoomsManager()
        self.users = UserManager()
        self._register_commands()

    def _register_commands(self) -> None:
        self.bot.message_handler(commands=['start', 'help'])(self._handle_start)
        self.bot.message_handler(commands=['setname','name'])(self._handle_setname_start)
        self.bot.message_handler(commands=['join'])(self._handle_join)
        self.bot.message_handler(commands=['leave'])(self._handle_leave)
        self.bot.message_handler(commands=['rooms', 'list'])(self._handle_list_rooms)
        self.bot.message_handler(commands=['createroom', 'create'])(self._handle_create_room_start)
        self.bot.message_handler(commands=['deleteroom', 'delete'])(self._handle_delete_room)
        self.bot.message_handler(commands=['stats'])(self._handle_stats)

        self.bot.message_handler(
            func=lambda message: self.users.get_state(message.from_user.id) == UserStates.SETTING_NAME
        )(self._handle_setname_finish)
        
        self.bot.message_handler(
            func=lambda message: self.users.get_state(message.from_user.id) == UserStates.CREATING_ROOM
        )(self._handle_create_room_finish)
        
        self.bot.message_handler(
            func=lambda message: self.users.get_state(message.from_user.id) == UserStates.CHAT
        )(self._handle_chat_message)

        self.bot.message_handler(
            func=lambda message: self.users.get_state(message.from_user.id) == UserStates.CONFIRMING
        )(self._handle_confirmation)

    async def register_check(self, message) -> bool:

        user_id = message.from_user.id

        if not self.users.is_registered(user_id):
            await self.bot.send_message(
                message.chat.id,
                "❌ Сначала установите никнейм через /setname"
            )
            return False
        else: 
            return True

    async def _handle_start(self, message):
        global_count = self.rooms_manager.get_global_room_count()
        total_users = self.rooms_manager.get_total_users_count()
        total_rooms = len(self.rooms_manager.rooms)
        
        help_text = (
            "✨ Добро пожаловать в Chat-Room Bot\n\n"

            "📝 Для начала установи себе ник: /setname\n\n"

            "📊 Статистика:\n"
            f"   👥 Участников в комнатах: {total_users}\n"
            f"   🌐 В глобальном чате: {global_count}\n"
            f"   🛋 Активных комнат: {total_rooms}\n\n"

            "🖥 Основные команды:\n"
            "   /join - войти в глобальную комнату\n"
            "   /join N - войти в комнату с ID N\n"
            "   /leave - выйти из текущей комнаты\n"
            "   /rooms - список всех доступных комнат\n"
            "   /stats - подробная статистика\n\n"

            "🏠 Управление комнатами:\n"
            "   /createroom - создать комнату\n"
            "   /deleteroom - удалить свою комнату\n"
            "Комнаты автоматически удаляются, когда выходит последний участник"
        )
        #append admin commands later
        await self.bot.reply_to(message, help_text)

    async def _handle_stats(self, message):
        global_count = self.rooms_manager.get_global_room_count()
        total_users = self.rooms_manager.get_total_users_count()
        total_rooms = len(self.rooms_manager.rooms)
        total_room_users = 0
        for room in self.rooms_manager.rooms.values():
            total_room_users =+ room.get_member_count()
        
        stats_text = (
            "📊 Cтатистика:\n\n"

            f"👥 Общее количество пользователей: {total_users}\n"
        )
        
        if total_rooms > 0:
            stats_text += (
                f"🌐 Участников в глобальном чате: {global_count} - {(global_count//total_users)*100}%\n"
                f"📋 Участников в отдельных комнатах: {total_room_users} - {(total_room_users//total_users)*100}%\n"
                f"🏠 Всего комнат активно: {total_rooms}\n\n"
                "📈 Статистика по комнатам:\n"
            )
            for room in self.rooms_manager.rooms.values():
                creator_name = self.users.get_username(room.creator_id)
                stats_text += (
                    f"   🏠 #{room.room_id} '{room.name}': "
                    f"{room.get_member_count()} участников\n"
                    f"      Создатель: {creator_name}\n"
                )
        else:
            stats_text += "Активных комнат нет 🚬\n"

        await self.bot.reply_to(message, stats_text)

    async def _broadcast_name_change(self, user_id: int, old_name: str, new_name: str):
        room = self.rooms_manager.get_user_room(user_id)

        if user_id in self.rooms_manager.global_room:
            await self._broadcast_system_message(
                self.rooms_manager.global_room, user_id,
                f"🌐 - {old_name} сменил(а) ник на {new_name}!"
            )
        elif room:
            if room:
                await self._broadcast_system_message(
                    room.members, user_id,
                    f"🌐 - {old_name} сменил(а) ник на {new_name}!"
                )

    async def _handle_setname_start(self, message):
        await self.bot.send_message(message.chat.id, "Какой никнейм вы хотите использовать?")
        self.users.set_state(message.from_user.id, UserStates.SETTING_NAME)

    async def _handle_setname_finish(self, message):
        new_name = message.text.strip()
        
        if len(new_name) > 16:
            await self.bot.send_message(message.chat.id, "❌ Слишком длинное имя - Максимум 16 символов")
            return

        user_id = message.from_user.id
        
        if self.users.is_registered(user_id):
            actual_old_name = self.users.update_username(user_id, new_name)
            log_message = f"📝 Смена ника: {actual_old_name}  {new_name} (ID: {user_id})"
            
            await self._broadcast_name_change(user_id, actual_old_name, new_name)
        else:
            self.users.register_user(user_id, new_name)
            log_message = f"📝 Новый пользователь: {new_name} (ID: {user_id})"

        print(log_message)
        
        await self.bot.send_message(message.chat.id, f"✅ Теперь вы отображаетесь как: {new_name}")
        self.users.set_state(user_id, UserStates.NONE)

    async def _handle_join(self, message):
        user_id = message.from_user.id
        
        if not await self.register_check(message): return

        command_parts = message.text.split()
        username = self.users.get_username(user_id)

        # global room join handling
        if len(command_parts) == 1 or command_parts[1] == 'global':
            if user_id not in self.rooms_manager.global_room:
                await self._handle_leave(message)
                
                self.rooms_manager.global_room.append(user_id)
                self.users.set_state(user_id, UserStates.CHAT)
                await self.bot.reply_to(message, "✅ Вы присоединились к глобальной комнате!")
                await self._broadcast_system_message(
                    self.rooms_manager.global_room, user_id,
                    f"🌐 - {username} врывается в глобальную комнату!"
                )
                print(f"📝 {username} присоединился к глобальной комнате")
            else:
                await self.bot.reply_to(message, "❌ Вы уже в глобальной комнате!")

        # private rooms join handling
        elif len(command_parts) >= 2:
            try:
                room_id = int(command_parts[1])
                room = self.rooms_manager.get_room(room_id)
                
                if not room:
                    await self.bot.reply_to(message, "❌ Комната не найдена!")
                    return
                
                current_room = self.rooms_manager.get_user_room(user_id)
                if current_room and current_room.room_id == room_id:
                    await self.bot.reply_to(message, f"❌ Вы уже находитесь в комнате '{room.name}'!")
                    return
                await self._handle_leave(message, silent=True)
                
                if self.rooms_manager.join_room(user_id, room_id):
                    self.users.set_state(user_id, UserStates.CHAT)
                    await self.bot.reply_to(message, f"✅ Вы присоединились к комнате '{room.name}'!")
                    await self._broadcast_system_message(
                        room.members, user_id,
                        f"🌐 - {username} присоединяется к комнате!"
                    )
                    print(f"📝 {username} присоединился к комнате '{room.name}' (ID: {room_id})")
            except ValueError:
                await self.bot.reply_to(message, "❌ Неверный ID комнаты! Используйте: /join <номер_комнаты>")

    async def _handle_confirmation(self, message):
        return

    async def _handle_leave(self, message, silent=False):
        if not await self.register_check(message): 
            return

        user_id = message.from_user.id
        username = self.users.get_username(user_id)
        room = self.rooms_manager.get_user_room(user_id)
        had_room = False

        # global room leave handling
        if user_id in self.rooms_manager.global_room:
            self.rooms_manager.global_room.remove(user_id)
            had_room = True

            await self._broadcast_system_message(
                self.rooms_manager.global_room,
                user_id,
                f"🌐 - {username} покидает комнату"
            )
            print(f"📝 {username} покинул глобальную комнату")

        # private room leave handling
        elif room:
            if user_id in room.members:
                room.members.remove(user_id)
                had_room = True
                await self._broadcast_system_message(
                    room.members,
                    user_id,
                    f"🌐 - {username} покинул комнату"
                )
                if len(room.members) == 0:
                    await self.bot.send_message(user_id, f"🌐 - Комната удалена")
                    print(f"📝 {room.name}, {room.room_id} удалена {username}")
                    self.rooms_manager.delete_room(room.room_id)

                print(f"📝 {username} покинул комнату {room.name}, {room.room_id}")

        if had_room:
            self.users.set_state(user_id, UserStates.NONE)
            await self.bot.reply_to(message, "✅ Вы покинули комнату")
        else:
            if not silent:
                await self.bot.reply_to(message, "❌ Вы не находитесь в комнате!")


    async def _handle_list_rooms(self, message):
        """Показать список доступных комнат"""
        user_id = message.from_user.id
        available_rooms = self.rooms_manager.get_available_rooms(user_id)
        
        if not available_rooms:
            await self.bot.reply_to(message, "Нет доступных комнат 🚬")
            return

        rooms_text = "🛋 Доступные комнаты:\n\n"
        for room in available_rooms:
            creator_name = self.users.get_username(room.creator_id)
            member_count = room.get_member_count()
            rooms_text += (
                f"Комната #{room.room_id}\n"
                f"   Название: {room.name}\n"
                f"   👥 Участников: {member_count}\n"
                f"   👤 Создатель: {creator_name}\n"
                f"   ➕ Присоединиться: /join {room.room_id}\n\n"
            )

        await self.bot.reply_to(message, rooms_text)

    async def _handle_create_room_start(self, message):
        user_id = message.from_user.id
        
        if not await self.register_check(message): return

        if self.rooms_manager.is_user_room_creator(user_id):
                existing_room = self.rooms_manager.get_user_created_room(user_id)
                if existing_room:
                    await self.bot.reply_to(
                        message,
                        f"❌ У вас уже есть активная комната!\n"
                        f"🏠 Комната: '{existing_room.name}' (ID: {existing_room.room_id})\n\n"
                        "Чтобы создать новую комнату, сначала удалите текущую через /deleteroom"
                    )
                    return

        await self.bot.reply_to(
            message,
            "Введите название для вашей комнаты:"
        )
        self.users.set_state(user_id, UserStates.CREATING_ROOM)

    async def _handle_create_room_finish(self, message):
            user_id = message.from_user.id
            room_name = message.text.strip()

            if len(room_name) > 16:
                await self.bot.reply_to(message, "❌ Слишком длинное название - Максимум 16 символов")
                return

            await self._handle_leave(message, silent=True)

            room_id = self.rooms_manager.create_room(room_name, user_id)
            room = self.rooms_manager.get_room(room_id)
            
            if room:
                room.add_member(user_id)
                self.users.set_state(user_id, UserStates.CHAT)

                await self.bot.reply_to(
                    message,
                    f"✅ Комната '{room_name}' создана!\n"
                    f"ID комнаты: {room_id}\n\n"
                    "💡 Вы были автоматически добавлены в созданную комнату\n"
                    "💡 Комната автоматически удалится, когда из неё выйдут все участники"
                )
                
                print(f"🏠 Создана новая комната: '{room_name}' (ID: {room_id}) создателем {self.users.get_username(user_id)}")
            else:
                await self.bot.reply_to(message, "❌ Ошибка при создании комнаты!")
    
    async def _handle_delete_room(self, message):
        user_id = message.from_user.id
        
        if not await self.register_check(message): return

        room = self.rooms_manager.get_user_created_room(user_id)
        
        if not room:
            await self.bot.reply_to( message, "❌ У вас нет активных комнат для удаления!")
            return

        room_name = room.name
        room_id = room.room_id
        member_count = room.get_member_count()
        username = self.users.get_username(user_id)

        if member_count > 0:
            await self._broadcast_system_message(
                room.members, user_id,
                f"🌐 - Комната {room_name} удалена создателем {username}\n"
                f"{member_count} участников были выгнаны из комнаты"
            )

        self.rooms_manager.delete_room(room_id)
        
        for member_id in room.members:
                self.users.set_state(member_id, UserStates.NONE)

        await self.bot.reply_to(
            message,
            f"✅ Комната '{room_name}' успешно удалена!\n\n"
            f"📊 Статистика удаления:\n"
            f"   🏠 Название: {room_name}\n"
            f"   🔢 ID: {room_id}\n"
            f"   👥 Участников: {member_count}\n"
            f"   🗑️ Удалено: {username}"
        )
        
        print(f"📝 Комната {room_name}, {room_id} удалена пользователем {username}")

    async def _handle_chat_message(self, message):
        """Обработчик сообщений в чате"""
        user_id = message.from_user.id
        
        if not self.users.is_registered(user_id):
            return

        username = self.users.get_username(user_id)
        text = message.text
        room = self.rooms_manager.get_user_room(user_id)

        if user_id in self.rooms_manager.global_room:
            await self._broadcast_chat_message(
                self.rooms_manager.global_room, user_id, username, text
            )
            print(f"Global 💬 {username}: {text}")

        elif room:
            await self._broadcast_chat_message(
                room.members, user_id, username, text
            )
            print(f"{room.name}, {room.room_id} 💬 {username}: {text}")

    async def _broadcast_system_message(self, recipients: List[int], excluded_user_id: int, message: str):
        for user_id in recipients:
            if user_id != excluded_user_id:
                try:
                    await self.bot.send_message(user_id, message)
                except Exception as e:
                    print(f"Ошибка отправки системного сообщения пользователю {user_id}: {e}")

    async def _broadcast_chat_message(self, recipients: List[int], sender_id: int, username: str, text: str):
        for user_id in recipients:
            if user_id != sender_id:
                try:
                    await self.bot.send_message(user_id, f"{username}: {text}")
                except Exception as e:
                    print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

    def run(self):
        print("Chat-Room-Bot запущен 👍")
        print("Ctrl + C в терминале чтобы остановить")
        asyncio.run(self.bot.polling())
        print("Chat-Room-Bot оффлайн 💤")

if __name__ == "__main__":
    print("Пытается стартануть...")
    
    try:
        ChatBot(BOT_TOKEN).run()
    except:
        print("🚨 Увы: BOT_TOKEN неверен или отсутствует")