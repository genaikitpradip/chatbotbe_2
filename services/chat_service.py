# import uuid
# from typing import List, Optional
# from datetime import datetime
# from database import get_database
# from models import Chat, Message, MessageRole, FileInfo
# from services.ai_service import ai_service
# import logging

# logger = logging.getLogger(__name__)

# class ChatService:
#     def __init__(self):
#         self.db = None
    
#     def get_db(self):
#         if self.db is None:
#             self.db = get_database()
#         return self.db

#     async def create_chat(self, title: str = "New Chat") -> Chat:
#         """Create a new chat session"""
#         chat_id = str(uuid.uuid4())
#         chat = Chat(
#             id=chat_id,
#             title=title,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#             message_count=0
#         )
        
#         db = self.get_db()
#         chat_dict = chat.model_dump(by_alias=True)
#         chat_dict["_id"] = chat_id  # Ensure _id is set correctly
#         await db.chats.insert_one(chat_dict)
        
#         logger.info(f"Created new chat: {chat_id}")
#         return chat

#     async def get_all_chats(self) -> List[Chat]:
#         """Get all chat sessions"""
#         db = self.get_db()
#         cursor = db.chats.find().sort("updated_at", -1)
#         chats = []
        
#         async for chat_doc in cursor:
#             # Handle MongoDB _id field
#             if "_id" in chat_doc:
#                 chat_doc["id"] = chat_doc["_id"]
#             chat = Chat(**chat_doc)
#             chats.append(chat)
        
#         return chats

#     async def get_chat(self, chat_id: str) -> Optional[Chat]:
#         """Get a specific chat"""
#         db = self.get_db()
#         chat_doc = await db.chats.find_one({"_id": chat_id})
        
#         if chat_doc:
#             # Handle MongoDB _id field
#             if "_id" in chat_doc:
#                 chat_doc["id"] = chat_doc["_id"]
#             return Chat(**chat_doc)
#         return None

#     async def get_chat_messages(self, chat_id: str) -> List[Message]:
#         """Get all messages for a chat"""
#         db = self.get_db()
#         cursor = db.messages.find({"chat_id": chat_id}).sort("timestamp", 1)
#         messages = []
        
#         async for msg_doc in cursor:
#             message = Message(**msg_doc)
#             messages.append(message)
        
#         return messages

#     async def add_message(self, chat_id: str, role: MessageRole, content: str, 
#                          file_info: Optional[FileInfo] = None) -> Message:
#         """Add a message to a chat"""
#         message = Message(
#             chat_id=chat_id,
#             role=role,
#             content=content,
#             file=file_info,
#             timestamp=datetime.utcnow()
#         )
        
#         db = self.get_db()
#         await db.messages.insert_one(message.model_dump())
        
#         # Update chat's updated_at and message count
#         await db.chats.update_one(
#             {"_id": chat_id},
#             {
#                 "$set": {"updated_at": datetime.utcnow()},
#                 "$inc": {"message_count": 1}
#             }
#         )
        
#         return message

#     async def rename_chat(self, chat_id: str, new_title: str) -> bool:
#         """Rename a chat"""
#         db = self.get_db()
#         result = await db.chats.update_one(
#             {"_id": chat_id},
#             {
#                 "$set": {
#                     "title": new_title,
#                     "updated_at": datetime.utcnow()
#                 }
#             }
#         )
        
#         return result.modified_count > 0

#     async def delete_chat(self, chat_id: str) -> bool:
#         """Delete a chat and all its messages"""
#         db = self.get_db()
        
#         # Delete all messages
#         await db.messages.delete_many({"chat_id": chat_id})
        
#         # Delete chat
#         result = await db.chats.delete_one({"_id": chat_id})
        
#         logger.info(f"Deleted chat: {chat_id}")
#         return result.deleted_count > 0

#     async def process_message(self, chat_id: str, content: str,
#                                original_content: Optional[str] = None,  # the actual user input 
#                             file_info: Optional[FileInfo] = None,
#                             web_search_results: Optional[str] = None,  # ✅ new arg (optional)
#                             image_path: Optional[str] = None) -> tuple[Message, Message]:
#         """Process a user message and generate AI response"""
#         # Add user message
#         user_message = await self.add_message(chat_id, MessageRole.USER, original_content or content, file_info)

#             # 2. Optional: Save web search results as a system message
#         if web_search_results:
#             await self.add_message(
#                 chat_id,
#                 MessageRole.SYSTEM,
#                 web_search_results
#             )
        
#         # Get conversation history
#         messages = await self.get_chat_messages(chat_id)
        
#         # Generate AI response
#         ai_response_content = await ai_service.generate_response(messages, image_path)
        
#         # Add AI response
#         ai_message = await self.add_message(chat_id, MessageRole.ASSISTANT, ai_response_content)
        
#         # Auto-generate title for first message
#         if len(messages) <= 2:  # First user message + AI response
#             try:
#                 title = await ai_service.generate_chat_title(content, ai_response_content)
#                 await self.rename_chat(chat_id, title)
#             except Exception as e:
#                 logger.error(f"Error generating chat title: {e}")
        
#         return user_message, ai_message

# chat_service = ChatService()

import uuid
from typing import List, Optional, Tuple, Iterator
from datetime import datetime
import logging
from database import get_database
from models import Chat, Message, MessageRole, FileInfo, TTSRequest
from services.ai_service import ai_service
from elevenlabs.client import ElevenLabs
from config import settings


logger = logging.getLogger(__name__)

ELEVEN_API_KEY = settings.eleven_labs_api_key
if not ELEVEN_API_KEY:
    raise RuntimeError("Missing ELEVENLABS_API_KEY in environment")

client = ElevenLabs(api_key=ELEVEN_API_KEY)




class ChatService:
    def __init__(self):
        self.db = None
        api_key = settings.eleven_labs_api_key
        if not api_key:
            raise RuntimeError("Missing ELEVENLABS_API_KEY")
        self.eleven = ElevenLabs(api_key=api_key)
    
    def get_db(self):
        if self.db is None:
            self.db = get_database()
        return self.db

    # ---------- Chats ----------

    async def create_chat(self, owner_id: str, title: str = "New Chat") -> Chat:
        chat_id = str(uuid.uuid4())
        now = datetime.utcnow()
        chat = Chat(
            id=chat_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0,
            owner_id=owner_id
        )
        db = self.get_db()
        data = chat.model_dump(by_alias=True)
        data["_id"] = chat_id
        await db.chats.insert_one(data)
        logger.info(f"Created new chat: {chat_id} for owner {owner_id}")
        return chat

    async def get_all_chats(self, owner_id: str) -> List[Chat]:
        db = self.get_db()
        cursor = db.chats.find({"owner_id": owner_id}).sort("updated_at", -1)
        items: List[Chat] = []
        async for doc in cursor:
            doc["id"] = doc.get("_id", "")
            items.append(Chat(**doc))
        return items

    async def get_chat(self, owner_id: str, chat_id: str) -> Optional[Chat]:
        db = self.get_db()
        doc = await db.chats.find_one({"_id": chat_id, "owner_id": owner_id})
        if not doc:
            return None
        doc["id"] = doc.get("_id", "")
        return Chat(**doc)

    async def rename_chat(self, owner_id: str, chat_id: str, new_title: str) -> bool:
        db = self.get_db()
        result = await db.chats.update_one(
            {"_id": chat_id, "owner_id": owner_id},
            {"$set": {"title": new_title, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def delete_chat(self, owner_id: str, chat_id: str) -> bool:
        db = self.get_db()
        await db.messages.delete_many({"chat_id": chat_id, "owner_id": owner_id})
        result = await db.chats.delete_one({"_id": chat_id, "owner_id": owner_id})
        logger.info(f"Deleted chat: {chat_id} for owner {owner_id}")
        return result.deleted_count > 0

    # ---------- Messages ----------

    async def get_chat_messages(self, owner_id: str, chat_id: str) -> List[Message]:
        db = self.get_db()
        cursor = db.messages.find({"chat_id": chat_id, "owner_id": owner_id}).sort("timestamp", 1)
        items: List[Message] = []
        async for doc in cursor:
            items.append(Message(**doc))
        return items

    async def add_message(
        self,
        owner_id: str,
        chat_id: str,
        role: MessageRole,
        content: str,
        file_info: Optional[FileInfo] = None
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            file=file_info,
            timestamp=datetime.utcnow(),
            owner_id=owner_id
        )
        db = self.get_db()
        await db.messages.insert_one(message.model_dump())
        await db.chats.update_one(
            {"_id": chat_id, "owner_id": owner_id},
            {"$set": {"updated_at": datetime.utcnow()}, "$inc": {"message_count": 1}}
        )
        return message

    # ---------- Orchestration ----------

    async def process_message(
        self,
        owner_id: str,
        chat_id: str,
        content: str,
        *,
        original_content: Optional[str] = None,
        file_info: Optional[FileInfo] = None,
        web_search_results: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Tuple[Message, Message]:
        # User message
        user_message = await self.add_message(
            owner_id=owner_id,
            chat_id=chat_id,
            role=MessageRole.USER,
            content=original_content or content,
            file_info=file_info
        )

        # Optional: web search system message
        if web_search_results:
            await self.add_message(
                owner_id=owner_id,
                chat_id=chat_id,
                role=MessageRole.SYSTEM,
                content=web_search_results
            )

        # Gather history
        messages = await self.get_chat_messages(owner_id, chat_id)

        # Get AI response
        ai_content = await ai_service.generate_response(messages, image_path)

        # Save AI message
        ai_message = await self.add_message(
            owner_id=owner_id,
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            content=ai_content
        )

        # Auto-title if first round
        if len(messages) <= 2:
            try:
                title = await ai_service.generate_chat_title(content, ai_content)
                await self.rename_chat(owner_id, chat_id, title)
            except Exception as e:
                logger.error(f"Error generating chat title: {e}")

        return user_message, ai_message
    # ---------- TTS Integration ----------
    def elevenlabs_audio_stream(self, req: TTSRequest) -> Iterator[bytes]:
        """
        Yield audio chunks from ElevenLabs as they arrive.
        This avoids loading the entire file into memory.
        """
        # convert() returns a generator/iterable of bytes
        try:
            audio_iter = client.text_to_speech.convert(
                text=req.text,
                voice_id=req.voice_id,
                model_id=req.model_id,
                output_format=req.output_format,
            )
            for chunk in audio_iter:
                yield chunk
        except Exception as e:
            # Raising inside a generator won’t format a proper HTTP 500,
            # so we re-raise to be caught in the route.
            raise RuntimeError(f"ElevenLabs convert() failed: {e}") from e


chat_service = ChatService()
