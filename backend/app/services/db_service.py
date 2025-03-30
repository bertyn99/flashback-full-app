import sqlite3
import json
import asyncio
from typing import List, Dict, Any

class DatabaseService:
    def __init__(self, db_path: str = '../../tasks.db'):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tasks table to store upload and processing information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    original_filename TEXT,
                    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    chapters TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            # Processed chapters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_chapters (
                    task_id TEXT,
                    chapter_index INTEGER,
                    script TEXT,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                )
            ''')
            
            conn.commit()

    async def store_task(self, task_id: str, filename: str, chapters: List[Dict[str, Any]]):
        """Store task information"""
        def _sync_store():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO tasks (task_id, original_filename, chapters) VALUES (?, ?, ?)',
                    (task_id, filename, json.dumps(chapters))
                )
                conn.commit()
        
        return await asyncio.to_thread(_sync_store)

    async def get_chapters(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve chapters for a specific task"""
        def _sync_get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT chapters FROM tasks WHERE task_id = ?', (task_id,))
                result = cursor.fetchone()
                return json.loads(result[0]) if result else []
        
        return await asyncio.to_thread(_sync_get)

    async def store_processed_chapter(
        self, 
        task_id: str, 
        chapter_index: int, 
        script: str, 
        audio_path: str, 
        video_path: str
    ):
        """Store processed chapter information"""
        def _sync_store():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO processed_chapters 
                    (task_id, chapter_index, script, audio_path, video_path, status) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, chapter_index, script, audio_path, video_path, 'completed'))
                conn.commit()
        
        return await asyncio.to_thread(_sync_store)

    async def get_processed_chapters(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve processed chapters for a task"""
        def _sync_get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM processed_chapters WHERE task_id = ? ORDER BY chapter_index', 
                    (task_id,)
                )
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return await asyncio.to_thread(_sync_get)

# Create a singleton instance
db_service = DatabaseService()