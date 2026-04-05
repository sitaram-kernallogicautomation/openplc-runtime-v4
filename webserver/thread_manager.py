"""
Thread Manager for OpenPLC Runtime

Provides centralized thread management, tracking, and monitoring capabilities.
This module helps prevent thread leaks and provides visibility into thread usage.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from webserver.logger import get_logger

logger, _ = get_logger("thread_manager", use_buffer=False)


class ThreadType(Enum):
    """Types of threads in the system."""
    COMPILATION = "compilation"
    MONITOR = "monitor"
    WEBSOCKET = "websocket"
    LOG_SERVER = "log_server"
    STREAM_OUTPUT = "stream_output"
    UNKNOWN = "unknown"


@dataclass
class ThreadInfo:
    """Information about a tracked thread."""
    thread_id: int
    name: str
    thread_type: ThreadType
    daemon: bool
    alive: bool
    start_time: float
    last_check: float = field(default_factory=time.time)


class ThreadManager:
    """
    Centralized thread manager for tracking and monitoring threads.
    
    This class provides:
    - Thread registration and tracking
    - Thread health monitoring
    - Thread statistics
    - Leak detection
    """

    def __init__(self):
        self._threads: Dict[int, ThreadInfo] = {}
        self._lock = threading.Lock()
        self._enabled = True

    def register_thread(
        self,
        thread: threading.Thread,
        thread_type: ThreadType = ThreadType.UNKNOWN,
        name: Optional[str] = None,
    ) -> bool:
        """
        Register a thread for tracking.
        
        Args:
            thread: The thread to register
            thread_type: Type of thread
            name: Optional name override
            
        Returns:
            True if registered successfully, False otherwise
        """
        if not self._enabled:
            return False

        with self._lock:
            thread_id = thread.ident
            if thread_id is None:
                # Thread hasn't started yet
                logger.warning("Cannot register thread that hasn't started")
                return False

            if thread_id in self._threads:
                logger.warning("Thread %d already registered", thread_id)
                return False

            thread_name = name or thread.name or f"Thread-{thread_id}"
            thread_info = ThreadInfo(
                thread_id=thread_id,
                name=thread_name,
                thread_type=thread_type,
                daemon=thread.daemon,
                alive=thread.is_alive(),
                start_time=time.time(),
            )

            self._threads[thread_id] = thread_info
            logger.debug(
                "Registered thread: %s (ID: %d, Type: %s)",
                thread_name,
                thread_id,
                thread_type.value,
            )
            return True

    def unregister_thread(self, thread_id: int) -> bool:
        """
        Unregister a thread from tracking.
        
        Args:
            thread_id: The thread ID to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if not self._enabled:
            return False

        with self._lock:
            if thread_id not in self._threads:
                return False

            thread_info = self._threads.pop(thread_id)
            logger.debug("Unregistered thread: %s (ID: %d)", thread_info.name, thread_id)
            return True

    def update_thread_status(self, thread_id: int) -> bool:
        """
        Update the status of a tracked thread.
        
        Args:
            thread_id: The thread ID to update
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if thread_id not in self._threads:
                return False

            thread_info = self._threads[thread_id]
            thread_info.alive = threading._active.get(thread_id) is not None
            thread_info.last_check = time.time()
            return True

    def get_thread_count(self, thread_type: Optional[ThreadType] = None) -> int:
        """
        Get the count of tracked threads.
        
        Args:
            thread_type: Optional filter by thread type
            
        Returns:
            Number of threads
        """
        with self._lock:
            if thread_type is None:
                return len(self._threads)

            return sum(
                1
                for info in self._threads.values()
                if info.thread_type == thread_type
            )

    def get_thread_stats(self) -> Dict:
        """
        Get statistics about tracked threads.
        
        Returns:
            Dictionary with thread statistics
        """
        with self._lock:
            stats = {
                "total_tracked": len(self._threads),
                "by_type": {},
                "alive": 0,
                "daemon": 0,
            }

            for thread_info in self._threads.values():
                # Count by type
                type_name = thread_info.thread_type.value
                stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

                # Count alive and daemon threads
                if thread_info.alive:
                    stats["alive"] += 1
                if thread_info.daemon:
                    stats["daemon"] += 1

            return stats

    def get_all_threads(self) -> List[ThreadInfo]:
        """
        Get information about all tracked threads.
        
        Returns:
            List of ThreadInfo objects
        """
        with self._lock:
            return list(self._threads.values())

    def cleanup_dead_threads(self) -> int:
        """
        Remove dead threads from tracking.
        
        Returns:
            Number of threads removed
        """
        removed = 0
        with self._lock:
            dead_threads = [
                thread_id
                for thread_id, thread_info in self._threads.items()
                if not thread_info.alive
                and threading._active.get(thread_id) is None
            ]

            for thread_id in dead_threads:
                self._threads.pop(thread_id)
                removed += 1

        if removed > 0:
            logger.debug("Cleaned up %d dead thread(s)", removed)

        return removed

    def disable(self):
        """Disable thread tracking."""
        self._enabled = False
        logger.info("Thread tracking disabled")

    def enable(self):
        """Enable thread tracking."""
        self._enabled = True
        logger.info("Thread tracking enabled")


# Global thread manager instance
_thread_manager = ThreadManager()


def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance."""
    return _thread_manager


def register_thread(
    thread: threading.Thread,
    thread_type: ThreadType = ThreadType.UNKNOWN,
    name: Optional[str] = None,
) -> bool:
    """Convenience function to register a thread."""
    return _thread_manager.register_thread(thread, thread_type, name)


def unregister_thread(thread_id: int) -> bool:
    """Convenience function to unregister a thread."""
    return _thread_manager.unregister_thread(thread_id)
