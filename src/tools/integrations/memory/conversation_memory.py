"""
Persistent conversation memory system.
Stores and retrieves conversation context across bot restarts.
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

from src.log_service import get_logger


@dataclass
class ConversationEntry:
    """Single conversation entry."""
    timestamp: datetime
    chat_id: int
    user_id: Optional[int]
    role: str  # 'user' or 'assistant'
    content: str
    message_id: Optional[int] = None
    thread_id: Optional[int] = None


class ConversationMemory:
    """
    Persistent conversation memory system.
    Stores conversations in JSON files and provides context retrieval.
    """
    
    def __init__(self, storage_dir: str = "conversation_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # In-memory cache for active conversations
        self._memory_cache: Dict[int, List[ConversationEntry]] = defaultdict(list)
        
        # Configuration
        self.max_entries_per_chat = 50  # Keep last 50 messages per chat
        self.max_context_age_hours = 24  # Only consider messages from last 24 hours
        self.auto_save_interval = 10  # Auto-save every 10 messages
        self._save_counter = 0
        
        self.logger = get_logger("conversation_memory")
        
        # Load existing conversations on startup
        asyncio.create_task(self._load_conversations())
    
    async def _load_conversations(self) -> None:
        """Load existing conversations from disk."""
        try:
            for chat_file in self.storage_dir.glob("chat_*.json"):
                chat_id = int(chat_file.stem.replace("chat_", ""))
                
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to ConversationEntry objects
                entries = []
                for entry_data in data.get("entries", []):
                    entry = ConversationEntry(
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                        chat_id=entry_data["chat_id"],
                        user_id=entry_data.get("user_id"),
                        role=entry_data["role"],
                        content=entry_data["content"],
                        message_id=entry_data.get("message_id"),
                        thread_id=entry_data.get("thread_id")
                    )
                    
                    # Only load recent entries
                    if self._is_recent(entry.timestamp):
                        entries.append(entry)
                
                if entries:
                    self._memory_cache[chat_id] = entries
                    self.logger.info(f"Loaded {len(entries)} conversation entries for chat {chat_id}")
                
        except Exception as e:
            self.logger.error(f"Error loading conversations: {e}")
    
    async def add_message(
        self,
        chat_id: int,
        role: str,
        content: str,
        user_id: Optional[int] = None,
        message_id: Optional[int] = None,
        thread_id: Optional[int] = None
    ) -> None:
        """Add a message to conversation memory."""
        entry = ConversationEntry(
            timestamp=datetime.now(),
            chat_id=chat_id,
            user_id=user_id,
            role=role,
            content=content,
            message_id=message_id,
            thread_id=thread_id
        )
        
        # Add to cache
        self._memory_cache[chat_id].append(entry)
        
        # Trim old entries
        self._trim_conversation(chat_id)
        
        # Auto-save periodically
        self._save_counter += 1
        if self._save_counter >= self.auto_save_interval:
            await self._save_conversation(chat_id)
            self._save_counter = 0
        
        self.logger.debug(f"Added {role} message to chat {chat_id}: {content[:50]}...")
    
    async def get_conversation_context(
        self,
        chat_id: int,
        max_entries: int = 10,
        include_thread_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for a chat.
        
        Args:
            chat_id: Chat ID to get context for
            max_entries: Maximum number of entries to return
            include_thread_id: If provided, only include messages from this thread
            
        Returns:
            List of conversation entries in AutoGen format
        """
        entries = self._memory_cache.get(chat_id, [])
        
        # Filter by thread if specified
        if include_thread_id is not None:
            entries = [e for e in entries if e.thread_id == include_thread_id]
        
        # Get recent entries
        recent_entries = entries[-max_entries:] if entries else []
        
        # Convert to AutoGen format
        context = []
        for entry in recent_entries:
            context.append({
                "role": entry.role,
                "content": entry.content,
                "timestamp": entry.timestamp.isoformat(),
                "message_id": entry.message_id
            })
        
        self.logger.debug(f"Retrieved {len(context)} context entries for chat {chat_id}")
        return context
    
    async def get_last_assistant_message(self, chat_id: int) -> Optional[str]:
        """Get the last assistant message from a chat."""
        entries = self._memory_cache.get(chat_id, [])
        
        # Find last assistant message
        for entry in reversed(entries):
            if entry.role == "assistant":
                return entry.content
        
        return None
    
    async def find_recent_topic(self, chat_id: int, keywords: List[str]) -> Optional[str]:
        """
        Find recent messages containing specific keywords.
        
        Args:
            chat_id: Chat ID to search
            keywords: Keywords to search for
            
        Returns:
            Content of the most recent message containing keywords
        """
        entries = self._memory_cache.get(chat_id, [])
        
        # Search recent entries for keywords
        for entry in reversed(entries[-20:]):  # Check last 20 messages
            content_lower = entry.content.lower()
            if any(keyword.lower() in content_lower for keyword in keywords):
                return entry.content
        
        return None
    
    def _trim_conversation(self, chat_id: int) -> None:
        """Trim conversation to max entries and remove old entries."""
        entries = self._memory_cache.get(chat_id, [])
        
        # Remove old entries
        cutoff_time = datetime.now() - timedelta(hours=self.max_context_age_hours)
        entries = [e for e in entries if e.timestamp > cutoff_time]
        
        # Keep only recent entries
        if len(entries) > self.max_entries_per_chat:
            entries = entries[-self.max_entries_per_chat:]
        
        self._memory_cache[chat_id] = entries
    
    def _is_recent(self, timestamp: datetime) -> bool:
        """Check if timestamp is within the recent context window."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_context_age_hours)
        return timestamp > cutoff_time
    
    async def _save_conversation(self, chat_id: int) -> None:
        """Save conversation to disk."""
        try:
            entries = self._memory_cache.get(chat_id, [])
            if not entries:
                return
            
            # Convert to serializable format
            data = {
                "chat_id": chat_id,
                "last_updated": datetime.now().isoformat(),
                "entries": [
                    {
                        **asdict(entry),
                        "timestamp": entry.timestamp.isoformat()
                    }
                    for entry in entries
                ]
            }
            
            chat_file = self.storage_dir / f"chat_{chat_id}.json"
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Saved {len(entries)} entries for chat {chat_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving conversation for chat {chat_id}: {e}")
    
    async def save_all_conversations(self) -> None:
        """Save all active conversations to disk."""
        for chat_id in self._memory_cache.keys():
            await self._save_conversation(chat_id)
        
        self.logger.info(f"Saved all conversations for {len(self._memory_cache)} chats")
    
    async def cleanup(self) -> None:
        """Cleanup and save all conversations."""
        await self.save_all_conversations()
        self.logger.info("Conversation memory cleanup completed")


# Global instance
_conversation_memory: Optional[ConversationMemory] = None


def get_conversation_memory() -> ConversationMemory:
    """Get the global conversation memory instance."""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory