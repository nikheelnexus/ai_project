import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock

# Thread-safe print lock (same as before)
print_lock = Lock()


def safe_print(message, color_code=""):
    """Thread-safe printing with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        if color_code:
            print(f"{color_code}[{timestamp}] {message}\033[0m")
        else:
            print(f"[{timestamp}] {message}")


# Color codes for different message types
COLORS = {
    "gray": "\033[90m",
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m"
}


class Icons:
    """Unicode icons for status messages."""
    SUCCESS = '✅'
    ERROR = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    DATABASE = '💾'
    COMPARE = '🔄'
    CHAT = '💬'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '📝'
    JSON = '📄'
    STATS = '📊'
    MESSAGE = '📨'
    THREAD = '🧵'
    USER = '👤'
    CLIENT = '👥'


class _UserChatDB:
    """Handles operations for the user_chat table with JSON data storage."""

    def __init__(self, db_path: str, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_chat_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_user_chat_table(self) -> None:
        """Create the user_chat table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    client_email TEXT NOT NULL,
                    jsondata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_email ON user_chat(user_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_client_email ON user_chat(client_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_client ON user_chat(user_email, client_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_created_at ON user_chat(created_at DESC)')

            # Create thread ID index for threaded chats
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_thread_id 
                ON user_chat(json_extract(jsondata, '$.thread_id'))
                WHERE json_extract(jsondata, '$.thread_id') IS NOT NULL
            ''')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_chat_timestamp 
                AFTER UPDATE ON user_chat
                BEGIN
                    UPDATE user_chat 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            # self._print_important(f"{Icons.DATABASE} User chat table initialized", COLORS["green"])

    def _validate_json(self, json_data: Any) -> tuple[bool, str]:
        """Validate JSON data and convert to string if valid."""
        try:
            if isinstance(json_data, str):
                # Try to parse to validate
                json.loads(json_data)
                return True, json_data
            else:
                # Convert to JSON string
                json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
                return True, json_str
        except (json.JSONDecodeError, TypeError) as e:
            return False, f"Invalid JSON data: {str(e)}"

    def _normalize_email(self, email: str) -> str:
        """Normalize email address for consistent storage."""
        if not email:
            return ""

        email = email.strip().lower()
        return email

    def insert_chat(
            self,
            user_email: str,
            client_email: str,
            json_data: Any,
            thread_id: Optional[str] = None,
            message_type: Optional[str] = "message",
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a new chat record.

        Args:
            user_email: The user's email address
            client_email: The client's email address
            json_data: JSON data to store (dict, list, or JSON string)
            thread_id: Optional thread ID for threaded conversations
            message_type: Type of message (e.g., 'message', 'system', 'notification')
            replace: If True, replace existing chat with same user and client

        Returns:
            Chat record if successful, None if failed
        """
        # Normalize emails
        normalized_user = self._normalize_email(user_email)
        normalized_client = self._normalize_email(client_email)

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid email address provided", COLORS["red"])
            return None

        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        # Add metadata to JSON if provided
        json_obj = json.loads(json_result) if isinstance(json_result, str) else json_data

        if not isinstance(json_obj, dict):
            json_obj = {"content": json_obj}

        # Add metadata if not already present
        if thread_id and 'thread_id' not in json_obj:
            json_obj['thread_id'] = thread_id
        if message_type and 'message_type' not in json_obj:
            json_obj['message_type'] = message_type

        # Add timestamp
        json_obj['timestamp'] = datetime.now().isoformat()

        # Convert back to JSON string
        json_result = json.dumps(json_obj, ensure_ascii=False, separators=(',', ':'))

        # Check if chat already exists (for same user-client pair without thread)
        existing = None
        if not thread_id:
            existing = self.get_chat_by_emails(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_chat 
                        SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_email = ? AND client_email = ?
                    ''', (json_result, normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated chat: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_chat_by_emails(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Chat already exists: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_chat (user_email, client_email, jsondata)
                        VALUES (?, ?, ?)
                    ''', (normalized_user, normalized_client, json_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    thread_info = f" (thread: {thread_id})" if thread_id else ""
                    self._print_important(
                        f"{Icons.SUCCESS} Inserted chat #{record_id}: {normalized_user} ↔ {normalized_client}{thread_info}",
                        COLORS["green"]
                    )

                    return self.get_chat_by_id(record_id)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in insert_chat: {e}", COLORS["red"])
            return None

    def get_chat_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get chat record by ID.

        Args:
            record_id: Record ID

        Returns:
            Chat record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM user_chat WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    return record

                if self.debug:
                    self._print_important(f"{Icons.WARNING} Chat not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_by_id: {e}", COLORS["red"])
            return None

    def get_chat_by_emails(
            self,
            user_email: str,
            client_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get chat record by user email and client email.

        Args:
            user_email: User email address
            client_email: Client email address

        Returns:
            Chat record or None if not found
        """
        normalized_user = self._normalize_email(user_email)
        normalized_client = self._normalize_email(client_email)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE user_email = ? AND client_email = ?
                ''', (normalized_user, normalized_client))

                row = cursor.fetchone()

                if row:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    return record

                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_by_emails: {e}", COLORS["red"])
            return None

    def get_chat_thread(
            self,
            thread_id: str,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all chat messages in a specific thread.

        Args:
            thread_id: Thread ID to search for
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records in the thread
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE json_extract(jsondata, '$.thread_id') = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (thread_id, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.THREAD} Found {len(records)} messages in thread '{thread_id}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_thread: {e}", COLORS["red"])
            return []

    def get_conversation_history(
            self,
            user_email: str,
            client_email: str,
            limit: int = 50,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history between a specific user and client.

        Args:
            user_email: User email address
            client_email: Client email address
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        normalized_user = self._normalize_email(user_email)
        normalized_client = self._normalize_email(client_email)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE (user_email = ? AND client_email = ?)
                       OR (user_email = ? AND client_email = ?)
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (normalized_user, normalized_client, normalized_client, normalized_user, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.CHAT} Found {len(records)} messages in conversation {normalized_user} ↔ {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_conversation_history: {e}", COLORS["red"])
            return []

    def get_user_chats(self, user_email: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all chats involving a specific user.

        Args:
            user_email: User email address
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        normalized_user = self._normalize_email(user_email)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE user_email = ? OR client_email = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (normalized_user, normalized_user, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.USER} Found {len(records)} chats involving user {normalized_user}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_chats: {e}", COLORS["red"])
            return []

    def update_chat_json(
            self,
            record_id: int,
            json_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update JSON data for a chat record.

        Args:
            record_id: Record ID
            json_data: New JSON data

        Returns:
            Updated record or None if failed
        """
        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE user_chat 
                    SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json_result, record_id))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated JSON for chat #{record_id}",
                        COLORS["green"]
                    )
                    return self.get_chat_by_id(record_id)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Chat not found: ID {record_id}",
                        COLORS["yellow"]
                    )
                    return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_chat_json: {e}", COLORS["red"])
            return None

    def delete_chat(self, identifier: Any) -> bool:
        """
        Delete chat record by ID or emails.

        Args:
            identifier: Can be:
                       - int: Record ID
                       - tuple: (user_email, client_email)
                       - str: Single email address (deletes all records with that email)

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if isinstance(identifier, int):
                    # Delete by ID
                    cursor.execute('DELETE FROM user_chat WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by emails
                    normalized_user = self._normalize_email(identifier[0])
                    normalized_client = self._normalize_email(identifier[1])

                    cursor.execute('''
                        DELETE FROM user_chat 
                        WHERE user_email = ? AND client_email = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this email
                    normalized = self._normalize_email(identifier)
                    cursor.execute('''
                        DELETE FROM user_chat 
                        WHERE user_email = ? OR client_email = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} chat record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching chat records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_chat: {e}", COLORS["red"])
            return False

    def get_all_chats(
            self,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all chat records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} chat records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_chats: {e}", COLORS["red"])
            return []

    def search_chats(
            self,
            search_text: str,
            search_in_json: bool = False,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search chats by email addresses or JSON content.

        Args:
            search_text: Text to search for
            search_in_json: If True, also search in JSON content
            limit: Maximum number of records to return

        Returns:
            List of matching chat records
        """
        if not search_text:
            #self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Normalize search text
        search_text = search_text.strip().lower()

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if search_in_json:
                    # Search in both email fields and JSON content
                    cursor.execute('''
                        SELECT * FROM user_chat 
                        WHERE user_email LIKE ? 
                           OR client_email LIKE ?
                           OR jsondata LIKE ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%', limit))
                else:
                    # Search only in email fields
                    cursor.execute('''
                        SELECT * FROM user_chat 
                        WHERE user_email LIKE ? OR client_email LIKE ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (f'%{search_text}%', f'%{search_text}%', limit))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                json_search = " and JSON" if search_in_json else ""
                self._print_important(
                    f"{Icons.SEARCH} Found {len(records)} chats matching '{search_text}'{json_search}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_chats: {e}", COLORS["red"])
            return []

    def get_chat_count(self) -> Dict[str, int]:
        """
        Get statistics about chat records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM user_chat')
                total = cursor.fetchone()[0]

                # Count of unique user emails
                cursor.execute('SELECT COUNT(DISTINCT user_email) FROM user_chat')
                unique_users = cursor.fetchone()[0]

                # Count of unique client emails
                cursor.execute('SELECT COUNT(DISTINCT client_email) FROM user_chat')
                unique_clients = cursor.fetchone()[0]

                # Count of unique conversations (user-client pairs)
                cursor.execute('''
                    SELECT COUNT(DISTINCT CASE 
                        WHEN user_email < client_email 
                        THEN user_email || '|' || client_email 
                        ELSE client_email || '|' || user_email 
                    END) 
                    FROM user_chat
                ''')
                unique_conversations = cursor.fetchone()[0]

                # Most active user
                cursor.execute('''
                    SELECT email, COUNT(*) as message_count FROM (
                        SELECT user_email as email FROM user_chat
                        UNION ALL
                        SELECT client_email as email FROM user_chat
                    )
                    GROUP BY email ORDER BY message_count DESC LIMIT 1
                ''')
                most_active_user_result = cursor.fetchone()
                most_active_user = most_active_user_result[0] if most_active_user_result else None
                most_active_user_count = most_active_user_result[1] if most_active_user_result else 0

                # Most recent chat
                cursor.execute('SELECT MAX(created_at) FROM user_chat')
                most_recent = cursor.fetchone()[0]

                stats = {
                    'total_chats': total,
                    'unique_user_emails': unique_users,
                    'unique_client_emails': unique_clients,
                    'unique_conversations': unique_conversations,
                    'most_active_user': most_active_user,
                    'most_active_user_count': most_active_user_count,
                    'most_recent': most_recent
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.STATS} Chat stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients, "
                        f"{unique_conversations} conversations",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_count: {e}", COLORS["red"])
            return {}

    def clear_all_chats(self) -> bool:
        """
        Clear all chat records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM user_chat')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM user_chat')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} chat records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_chats: {e}", COLORS["red"])
            return False

    def batch_insert_chats(
            self,
            chats: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Insert multiple chat records in a batch.

        Args:
            chats: List of dictionaries with user_email, client_email, and jsondata

        Returns:
            List of inserted records (or None for failed ones)
        """
        results = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for i, chat in enumerate(chats):
                    try:
                        # Validate required fields
                        if not all(key in chat for key in ['user_email', 'client_email', 'jsondata']):
                            self._print_important(
                                f"{Icons.ERROR} Chat #{i} missing required fields",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        normalized_user = self._normalize_email(chat['user_email'])
                        normalized_client = self._normalize_email(chat['client_email'])

                        # Validate JSON
                        is_valid, json_result = self._validate_json(chat['jsondata'])
                        if not is_valid:
                            self._print_important(
                                f"{Icons.ERROR} Chat #{i}: {json_result}",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        # Insert record
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_chat 
                            (user_email, client_email, jsondata)
                            VALUES (?, ?, ?)
                        ''', (normalized_user, normalized_client, json_result))

                        record_id = cursor.lastrowid
                        results.append(self.get_chat_by_id(record_id))

                    except Exception as e:
                        self._print_important(
                            f"{Icons.ERROR} Error processing chat #{i}: {e}",
                            COLORS["red"]
                        )
                        results.append(None)

                conn.commit()

                success_count = sum(1 for r in results if r is not None)
                self._print_important(
                    f"{Icons.SUCCESS} Batch insert complete: {success_count}/{len(chats)} successful",
                    COLORS["green"]
                )

                return results

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in batch_insert_chats: {e}", COLORS["red"])
            return [None] * len(chats)

    def get_active_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most active conversations (based on message count).

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT 
                        MIN(user_email, client_email) as email1,
                        MAX(user_email, client_email) as email2,
                        COUNT(*) as message_count,
                        MAX(created_at) as last_message_at
                    FROM user_chat
                    GROUP BY email1, email2
                    ORDER BY message_count DESC, last_message_at DESC
                    LIMIT ?
                ''', (limit,))

                rows = cursor.fetchall()
                conversations = []

                for row in rows:
                    conversation = {
                        'participant1': row[0],
                        'participant2': row[1],
                        'message_count': row[2],
                        'last_message': row[3]
                    }
                    conversations.append(conversation)

                self._print_important(
                    f"{Icons.CHAT} Found {len(conversations)} active conversations",
                    COLORS["blue"]
                )
                return conversations

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_active_conversations: {e}", COLORS["red"])
            return []

    def get_recent_chats_by_user(
            self,
            user_email: str,
            days: int = 7,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent chats for a specific user within a time period.

        Args:
            user_email: User email address
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recent chat records
        """
        normalized_user = self._normalize_email(user_email)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE (user_email = ? OR client_email = ?)
                      AND created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (normalized_user, normalized_user, f'-{days} days', limit))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.CHAT} Found {len(records)} recent chats for {normalized_user} in last {days} days",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_recent_chats_by_user: {e}", COLORS["red"])
            return []

    def delete_old_chats(self, days_old: int = 30) -> int:
        """
        Delete chat records older than specified days.

        Args:
            days_old: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    DELETE FROM user_chat 
                    WHERE created_at < datetime('now', ?)
                ''', (f'-{days_old} days',))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} chats older than {days_old} days",
                        COLORS["green"]
                    )
                else:
                    self._print_important(
                        f"{Icons.INFO} No chats older than {days_old} days found",
                        COLORS["blue"]
                    )

                return deleted_count

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_old_chats: {e}", COLORS["red"])
            return 0

    def get_chat_summary(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for chats.

        Args:
            user_email: Optional filter by user email

        Returns:
            Dictionary with summary statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if user_email:
                    normalized_user = self._normalize_email(user_email)
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT CASE 
                                WHEN user_email = ? THEN client_email 
                                ELSE user_email 
                            END) as unique_contacts,
                            MIN(created_at) as first_chat,
                            MAX(created_at) as last_chat
                        FROM user_chat 
                        WHERE user_email = ? OR client_email = ?
                    ''', (normalized_user, normalized_user, normalized_user))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT CASE 
                                WHEN user_email < client_email 
                                THEN user_email || '|' || client_email 
                                ELSE client_email || '|' || user_email 
                            END) as unique_conversations,
                            MIN(created_at) as first_chat,
                            MAX(created_at) as last_chat
                        FROM user_chat
                    ''')

                row = cursor.fetchone()

                summary = {
                    'total_chats': row[0],
                    'unique_contacts': row[1] if user_email else row[1],  # unique_conversations
                    'first_chat': row[2],
                    'last_chat': row[3],
                    'user_email': user_email
                }

                return summary

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_summary: {e}", COLORS["red"])
            return {}




class UserChatDB:
    """Handles operations for the user_chat table with JSON data storage."""

    def __init__(self, db_path: str, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_chat_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_user_chat_table(self) -> None:
        """Create the user_chat table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_unique_name TEXT NOT NULL,
                    client_unique_name TEXT NOT NULL,
                    jsondata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_unique_name ON user_chat(user_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_client_unique_name ON user_chat(client_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_client ON user_chat(user_unique_name, client_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_created_at ON user_chat(created_at DESC)')

            # Create thread ID index for threaded chats
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_thread_id 
                ON user_chat(json_extract(jsondata, '$.thread_id'))
                WHERE json_extract(jsondata, '$.thread_id') IS NOT NULL
            ''')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_chat_timestamp 
                AFTER UPDATE ON user_chat
                BEGIN
                    UPDATE user_chat 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            # self._print_important(f"{Icons.DATABASE} User chat table initialized", COLORS["green"])

    def _validate_json(self, json_data: Any) -> tuple[bool, str]:
        """Validate JSON data and convert to string if valid."""
        try:
            if isinstance(json_data, str):
                # Try to parse to validate
                json.loads(json_data)
                return True, json_data
            else:
                # Convert to JSON string
                json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
                return True, json_str
        except (json.JSONDecodeError, TypeError) as e:
            return False, f"Invalid JSON data: {str(e)}"

    def _normalize_name(self, name: str) -> str:
        """Normalize name for consistent storage."""
        if not name:
            return ""

        name = name.strip().lower()
        return name

    def insert_chat(
            self,
            user_unique_name: str,
            client_unique_name: str,
            json_data: Any,
            thread_id: Optional[str] = None,
            message_type: Optional[str] = "message",
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a new chat record.

        Args:
            user_unique_name: The user's unique name
            client_unique_name: The client's unique name
            json_data: JSON data to store (dict, list, or JSON string)
            thread_id: Optional thread ID for threaded conversations
            message_type: Type of message (e.g., 'message', 'system', 'notification')
            replace: If True, replace existing chat with same user and client

        Returns:
            Chat record if successful, None if failed
        """
        # Normalize names
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid name provided", COLORS["red"])
            return None

        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        # Add metadata to JSON if provided
        json_obj = json.loads(json_result) if isinstance(json_result, str) else json_data

        if not isinstance(json_obj, dict):
            json_obj = {"content": json_obj}

        # Add metadata if not already present
        if thread_id and 'thread_id' not in json_obj:
            json_obj['thread_id'] = thread_id
        if message_type and 'message_type' not in json_obj:
            json_obj['message_type'] = message_type

        # Add timestamp
        json_obj['timestamp'] = datetime.now().isoformat()

        # Convert back to JSON string
        json_result = json.dumps(json_obj, ensure_ascii=False, separators=(',', ':'))

        # Check if chat already exists (for same user-client pair without thread)
        existing = None
        if not thread_id:
            existing = self.get_chat_by_names(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_chat 
                        SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (json_result, normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated chat: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_chat_by_names(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Chat already exists: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_chat (user_unique_name, client_unique_name, jsondata)
                        VALUES (?, ?, ?)
                    ''', (normalized_user, normalized_client, json_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    thread_info = f" (thread: {thread_id})" if thread_id else ""
                    self._print_important(
                        f"{Icons.SUCCESS} Inserted chat #{record_id}: {normalized_user} ↔ {normalized_client}{thread_info}",
                        COLORS["green"]
                    )

                    return self.get_chat_by_id(record_id)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in insert_chat: {e}", COLORS["red"])
            return None

    def get_chat_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get chat record by ID.

        Args:
            record_id: Record ID

        Returns:
            Chat record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM user_chat WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    return record

                if self.debug:
                    self._print_important(f"{Icons.WARNING} Chat not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_by_id: {e}", COLORS["red"])
            return None

    def get_chat_by_names(
            self,
            user_unique_name: str,
            client_unique_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get chat record by user unique name and client unique name.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name

        Returns:
            Chat record or None if not found
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE user_unique_name = ? AND client_unique_name = ?
                ''', (normalized_user, normalized_client))

                row = cursor.fetchone()

                if row:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    return record

                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_by_names: {e}", COLORS["red"])
            return None

    def get_chat_thread(
            self,
            thread_id: str,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all chat messages in a specific thread.

        Args:
            thread_id: Thread ID to search for
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records in the thread
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE json_extract(jsondata, '$.thread_id') = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (thread_id, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.THREAD} Found {len(records)} messages in thread '{thread_id}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_thread: {e}", COLORS["red"])
            return []

    def get_conversation_history(
            self,
            user_unique_name: str,
            client_unique_name: str,
            limit: int = 50,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history between a specific user and client.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE (user_unique_name = ? AND client_unique_name = ?)
                       OR (user_unique_name = ? AND client_unique_name = ?)
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (normalized_user, normalized_client, normalized_client, normalized_user, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.CHAT} Found {len(records)} messages in conversation {normalized_user} ↔ {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_conversation_history: {e}", COLORS["red"])
            return []

    def get_user_chats(self, user_unique_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all chats involving a specific user.

        Args:
            user_unique_name: User unique name
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        normalized_user = self._normalize_name(user_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE user_unique_name = ? OR client_unique_name = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (normalized_user, normalized_user, limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.USER} Found {len(records)} chats involving user {normalized_user}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_chats: {e}", COLORS["red"])
            return []

    def update_chat_json(
            self,
            record_id: int,
            json_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update JSON data for a chat record.

        Args:
            record_id: Record ID
            json_data: New JSON data

        Returns:
            Updated record or None if failed
        """
        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE user_chat 
                    SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json_result, record_id))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated JSON for chat #{record_id}",
                        COLORS["green"]
                    )
                    return self.get_chat_by_id(record_id)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Chat not found: ID {record_id}",
                        COLORS["yellow"]
                    )
                    return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_chat_json: {e}", COLORS["red"])
            return None

    def delete_chat(self, identifier: Any) -> bool:
        """
        Delete chat record by ID or names.

        Args:
            identifier: Can be:
                       - int: Record ID
                       - tuple: (user_unique_name, client_unique_name)
                       - str: Single name (deletes all records with that name)

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if isinstance(identifier, int):
                    # Delete by ID
                    cursor.execute('DELETE FROM user_chat WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by names
                    normalized_user = self._normalize_name(identifier[0])
                    normalized_client = self._normalize_name(identifier[1])

                    cursor.execute('''
                        DELETE FROM user_chat 
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this name
                    normalized = self._normalize_name(identifier)
                    cursor.execute('''
                        DELETE FROM user_chat 
                        WHERE user_unique_name = ? OR client_unique_name = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} chat record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching chat records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_chat: {e}", COLORS["red"])
            return False

    def get_all_chats(
            self,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all chat records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of chat records
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} chat records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_chats: {e}", COLORS["red"])
            return []

    def search_chats(
            self,
            search_text: str,
            search_in_json: bool = False,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search chats by names or JSON content.

        Args:
            search_text: Text to search for
            search_in_json: If True, also search in JSON content
            limit: Maximum number of records to return

        Returns:
            List of matching chat records
        """
        if not search_text:
            #self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Normalize search text
        search_text = search_text.strip().lower()

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if search_in_json:
                    # Search in both name fields and JSON content
                    cursor.execute('''
                        SELECT * FROM user_chat 
                        WHERE user_unique_name LIKE ? 
                           OR client_unique_name LIKE ?
                           OR jsondata LIKE ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%', limit))
                else:
                    # Search only in name fields
                    cursor.execute('''
                        SELECT * FROM user_chat 
                        WHERE user_unique_name LIKE ? OR client_unique_name LIKE ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (f'%{search_text}%', f'%{search_text}%', limit))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                json_search = " and JSON" if search_in_json else ""
                self._print_important(
                    f"{Icons.SEARCH} Found {len(records)} chats matching '{search_text}'{json_search}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_chats: {e}", COLORS["red"])
            return []

    def get_chat_count(self) -> Dict[str, int]:
        """
        Get statistics about chat records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM user_chat')
                total = cursor.fetchone()[0]

                # Count of unique user names
                cursor.execute('SELECT COUNT(DISTINCT user_unique_name) FROM user_chat')
                unique_users = cursor.fetchone()[0]

                # Count of unique client names
                cursor.execute('SELECT COUNT(DISTINCT client_unique_name) FROM user_chat')
                unique_clients = cursor.fetchone()[0]

                # Count of unique conversations (user-client pairs)
                cursor.execute('''
                    SELECT COUNT(DISTINCT CASE 
                        WHEN user_unique_name < client_unique_name 
                        THEN user_unique_name || '|' || client_unique_name 
                        ELSE client_unique_name || '|' || user_unique_name 
                    END) 
                    FROM user_chat
                ''')
                unique_conversations = cursor.fetchone()[0]

                # Most active user
                cursor.execute('''
                    SELECT name, COUNT(*) as message_count FROM (
                        SELECT user_unique_name as name FROM user_chat
                        UNION ALL
                        SELECT client_unique_name as name FROM user_chat
                    )
                    GROUP BY name ORDER BY message_count DESC LIMIT 1
                ''')
                most_active_user_result = cursor.fetchone()
                most_active_user = most_active_user_result[0] if most_active_user_result else None
                most_active_user_count = most_active_user_result[1] if most_active_user_result else 0

                # Most recent chat
                cursor.execute('SELECT MAX(created_at) FROM user_chat')
                most_recent = cursor.fetchone()[0]

                stats = {
                    'total_chats': total,
                    'unique_user_names': unique_users,
                    'unique_client_names': unique_clients,
                    'unique_conversations': unique_conversations,
                    'most_active_user': most_active_user,
                    'most_active_user_count': most_active_user_count,
                    'most_recent': most_recent
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.STATS} Chat stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients, "
                        f"{unique_conversations} conversations",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_count: {e}", COLORS["red"])
            return {}

    def clear_all_chats(self) -> bool:
        """
        Clear all chat records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM user_chat')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM user_chat')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} chat records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_chats: {e}", COLORS["red"])
            return False

    def batch_insert_chats(
            self,
            chats: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Insert multiple chat records in a batch.

        Args:
            chats: List of dictionaries with user_unique_name, client_unique_name, and jsondata

        Returns:
            List of inserted records (or None for failed ones)
        """
        results = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for i, chat in enumerate(chats):
                    try:
                        # Validate required fields
                        if not all(key in chat for key in ['user_unique_name', 'client_unique_name', 'jsondata']):
                            self._print_important(
                                f"{Icons.ERROR} Chat #{i} missing required fields",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        normalized_user = self._normalize_name(chat['user_unique_name'])
                        normalized_client = self._normalize_name(chat['client_unique_name'])

                        # Validate JSON
                        is_valid, json_result = self._validate_json(chat['jsondata'])
                        if not is_valid:
                            self._print_important(
                                f"{Icons.ERROR} Chat #{i}: {json_result}",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        # Insert record
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_chat 
                            (user_unique_name, client_unique_name, jsondata)
                            VALUES (?, ?, ?)
                        ''', (normalized_user, normalized_client, json_result))

                        record_id = cursor.lastrowid
                        results.append(self.get_chat_by_id(record_id))

                    except Exception as e:
                        self._print_important(
                            f"{Icons.ERROR} Error processing chat #{i}: {e}",
                            COLORS["red"]
                        )
                        results.append(None)

                conn.commit()

                success_count = sum(1 for r in results if r is not None)
                self._print_important(
                    f"{Icons.SUCCESS} Batch insert complete: {success_count}/{len(chats)} successful",
                    COLORS["green"]
                )

                return results

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in batch_insert_chats: {e}", COLORS["red"])
            return [None] * len(chats)

    def get_active_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most active conversations (based on message count).

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT 
                        MIN(user_unique_name, client_unique_name) as name1,
                        MAX(user_unique_name, client_unique_name) as name2,
                        COUNT(*) as message_count,
                        MAX(created_at) as last_message_at
                    FROM user_chat
                    GROUP BY name1, name2
                    ORDER BY message_count DESC, last_message_at DESC
                    LIMIT ?
                ''', (limit,))

                rows = cursor.fetchall()
                conversations = []

                for row in rows:
                    conversation = {
                        'participant1': row[0],
                        'participant2': row[1],
                        'message_count': row[2],
                        'last_message': row[3]
                    }
                    conversations.append(conversation)

                self._print_important(
                    f"{Icons.CHAT} Found {len(conversations)} active conversations",
                    COLORS["blue"]
                )
                return conversations

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_active_conversations: {e}", COLORS["red"])
            return []

    def get_recent_chats_by_user(
            self,
            user_unique_name: str,
            days: int = 7,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent chats for a specific user within a time period.

        Args:
            user_unique_name: User unique name
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recent chat records
        """
        normalized_user = self._normalize_name(user_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_chat 
                    WHERE (user_unique_name = ? OR client_unique_name = ?)
                      AND created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (normalized_user, normalized_user, f'-{days} days', limit))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    records.append(record)

                self._print_important(
                    f"{Icons.CHAT} Found {len(records)} recent chats for {normalized_user} in last {days} days",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_recent_chats_by_user: {e}", COLORS["red"])
            return []

    def delete_old_chats(self, days_old: int = 30) -> int:
        """
        Delete chat records older than specified days.

        Args:
            days_old: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    DELETE FROM user_chat 
                    WHERE created_at < datetime('now', ?)
                ''', (f'-{days_old} days',))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} chats older than {days_old} days",
                        COLORS["green"]
                    )
                else:
                    self._print_important(
                        f"{Icons.INFO} No chats older than {days_old} days found",
                        COLORS["blue"]
                    )

                return deleted_count

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_old_chats: {e}", COLORS["red"])
            return 0

    def get_chat_summary(self, user_unique_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for chats.

        Args:
            user_unique_name: Optional filter by user unique name

        Returns:
            Dictionary with summary statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if user_unique_name:
                    normalized_user = self._normalize_name(user_unique_name)
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT CASE 
                                WHEN user_unique_name = ? THEN client_unique_name 
                                ELSE user_unique_name 
                            END) as unique_contacts,
                            MIN(created_at) as first_chat,
                            MAX(created_at) as last_chat
                        FROM user_chat 
                        WHERE user_unique_name = ? OR client_unique_name = ?
                    ''', (normalized_user, normalized_user, normalized_user))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT CASE 
                                WHEN user_unique_name < client_unique_name 
                                THEN user_unique_name || '|' || client_unique_name 
                                ELSE client_unique_name || '|' || user_unique_name 
                            END) as unique_conversations,
                            MIN(created_at) as first_chat,
                            MAX(created_at) as last_chat
                        FROM user_chat
                    ''')

                row = cursor.fetchone()

                summary = {
                    'total_chats': row[0],
                    'unique_contacts': row[1] if user_unique_name else row[1],  # unique_conversations
                    'first_chat': row[2],
                    'last_chat': row[3],
                    'user_unique_name': user_unique_name
                }

                return summary

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_chat_summary: {e}", COLORS["red"])
            return {}