from typing import Optional, List, Tuple

class ChatRoom:
    def __init__(self, room_id: int, name: str, creator_id: int, is_public: bool = True):
        self.room_id = room_id
        self.name = name
        self.creator_id = creator_id
        self.is_public = is_public
        self.members: List[int] = []

    def add_member(self, user_id: int) -> bool:
        if user_id not in self.members:
            self.members.append(user_id)
            return True
        return False

    def remove_member(self, user_id: int) -> bool:
        if user_id in self.members:
            self.members.remove(user_id)
            return True
        return False

    def get_member_count(self) -> int:
        return len(self.members)

    def is_member(self, user_id: int) -> bool:
        return user_id in self.members
    
    def is_creator(self, user_id: int) -> bool:
        return user_id == self.creator_id

    def is_empty(self) -> bool:
        return len(self.members) == 0

class ChatRoomsManager:
    def __init__(self):
        self.global_room: List[int] = []
        self.rooms: dict[int, ChatRoom] = {}  # room_id -> ChatRoom
        self.next_room_id = 1

    def create_room(self, name: str, creator_id: int, is_public: bool = True) -> int:
        room_id = self.next_room_id
        self.rooms[room_id] = ChatRoom(room_id, name, creator_id, is_public)
        self.next_room_id += 1
        return room_id

    def delete_room(self, room_id: int) -> bool:
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False

    def cleanup_empty_rooms(self) -> List[ChatRoom]:
        empty_rooms = []
        rooms_to_delete = []
        
        for room_id, room in self.rooms.items():
            if room.is_empty():
                empty_rooms.append(room)
                rooms_to_delete.append(room_id)
        
        for room_id in rooms_to_delete:
            self.delete_room(room_id)
            
        return empty_rooms

    def get_room(self, room_id: int) -> Optional[ChatRoom]:
        return self.rooms.get(room_id)

    def get_public_rooms(self) -> List[ChatRoom]:
        return [room for room in self.rooms.values() if room.is_public]

    def get_user_room(self, user_id: int) -> Optional[ChatRoom]:
        for room in self.rooms.values():
            if room.is_member(user_id):
                return room
        return None

    def join_room(self, user_id: int, room_id: int) -> bool:
        room = self.get_room(room_id)
        if room and room.is_public:
            current_room = self.get_user_room(user_id)
            if current_room:
                current_room.remove_member(user_id)
            return room.add_member(user_id)
        return False

    def leave_room(self, user_id: int, room_id: int) -> bool:
        room = self.get_room(room_id)
        if room:
            room.remove_member(user_id)
            return True
        return False

    def get_available_rooms(self, user_id: int) -> List[ChatRoom]:
        user_room = self.get_user_room(user_id)
        user_room_ids = [user_room.room_id] if user_room else []
        return [room for room in self.get_public_rooms() if room.room_id not in user_room_ids]

    def get_global_room_count(self) -> int:
        return len(self.global_room)

    def get_total_users_count(self) -> int:
        all_users = set(self.global_room)
        for room in self.rooms.values():
            all_users.update(room.members)
        return len(all_users)
    
    def is_user_room_creator(self, user_id: int) -> bool:
        for room in self.rooms.values():
            if room.is_creator(user_id):
                return True
        return False

    def get_user_created_room(self, user_id: int) -> Optional[ChatRoom]:
        for room in self.rooms.values():
            if room.is_creator(user_id):
                return room
        return None