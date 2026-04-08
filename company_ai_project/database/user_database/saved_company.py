import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
from threading import Lock

import os
from company_ai_project.saved_data import user_data
from common_script import common

database = os.path.join(
    os.path.abspath(os.path.dirname(user_data.__file__)),
    'saved_company_database.db'
)

# Thread-safe print lock
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
    SAVE = '💾'
    CHAT = '💬'
    MAIL = '✉️'
    COMPANY = '🏢'
    TRASH = '🗑️'
    UPDATE = '📝'
    SEARCH = '🔍'


class _SavedCompaniesTable:
    """Handles operations for the saved_companies table with chat and mail JSON data."""

    def __init__(self, db_path: str = database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys if needed
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_table(self) -> None:
        """Create the saved_companies table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_website TEXT NOT NULL,
                    client_website TEXT NOT NULL,
                    chat TEXT,  -- JSON data for chat
                    mail TEXT,  -- JSON data for mail
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_website, client_website)  -- Ensure unique combinations
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_user_website ON saved_companies(user_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_client_website ON saved_companies(client_website)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_saved_both_websites ON saved_companies(user_website, client_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_created_at ON saved_companies(created_at DESC)')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_saved_companies_timestamp 
                AFTER UPDATE ON saved_companies
                BEGIN
                    UPDATE saved_companies 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            # self._print_important(f"{Icons.DATABASE} Saved companies table initialized", COLORS["green"])

    def _validate_json(self, json_data: Any, field_name: str = "data") -> tuple[bool, str]:
        """Validate JSON data and convert to string if valid."""
        if json_data is None:
            return True, None

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
            return False, f"Invalid {field_name} JSON: {str(e)}"

    def _normalize_website(self, website: str) -> str:
        """Normalize website URL for consistent storage, handling trailing slashes."""
        if not website:
            return ""

        # First, use your existing format_website_url
        website = common.format_website_url(website)

        # Remove trailing slash if it exists (except for the protocol part)
        if website.endswith('/'):
            website = website[:-1]

        return website

    def _parse_record(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse database_old record for internal use (strings → Python objects).
        Use this when you need to work with the data in Python.
        """
        record = dict(row)

        # Parse JSON fields
        for field in ['chat', 'mail']:
            if record.get(field) and isinstance(record[field], str):
                try:
                    record[field] = json.loads(record[field])
                except json.JSONDecodeError:
                    pass  # Keep as string if can't parse

        # Parse timestamps to datetime objects
        for field in ['created_at', 'updated_at']:
            if record.get(field) and isinstance(record[field], str):
                try:
                    record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                except ValueError:
                    pass

        return record

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize record for JSON output (Python objects → JSON-safe types).
        Use this when you need to return data via API or save to JSON.
        """
        serialized = {}

        for key, value in record.items():
            if isinstance(value, datetime):
                # Convert datetime to ISO format string
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                # These are already JSON serializable if they contain JSON-safe types
                serialized[key] = value
            else:
                serialized[key] = value

        return serialized

    def save_company(
            self,
            user_website: str,
            client_website: str,
            chat_data: Optional[Any] = None,
            mail_data: Optional[Any] = None,
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Save or update a company with chat and mail data.

        Args:
            user_website: The user's website URL
            client_website: The client's website URL
            chat_data: JSON data for chat (dict, list, or JSON string)
            mail_data: JSON data for mail (dict, list, or JSON string)
            replace: If True, replace existing saved company

        Returns:
            Saved company record if successful, None if failed
        """
        # Normalize websites
        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid website URL provided", COLORS["red"])
            return None

        # Validate JSON data
        chat_valid, chat_result = self._validate_json(chat_data, "chat")
        if not chat_valid:
            self._print_important(f"{Icons.ERROR} {chat_result}", COLORS["red"])
            return None

        mail_valid, mail_result = self._validate_json(mail_data, "mail")
        if not mail_valid:
            self._print_important(f"{Icons.ERROR} {mail_result}", COLORS["red"])
            return None

        # Check if already exists
        existing = self.get_saved_company(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE saved_companies 
                        SET chat = ?, mail = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_website = ? AND client_website = ?
                    ''', (chat_result, mail_result, normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated saved company: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_saved_company(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Company already saved: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO saved_companies (user_website, client_website, chat, mail)
                        VALUES (?, ?, ?, ?)
                    ''', (normalized_user, normalized_client, chat_result, mail_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    self._print_important(
                        f"{Icons.SAVE} Saved company #{record_id}: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_saved_company_by_id(record_id)

        except sqlite3.IntegrityError as e:
            self._print_important(f"{Icons.ERROR} Database integrity error: {e}", COLORS["red"])
            return existing or None
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in save_company: {e}", COLORS["red"])
            return None

    def get_saved_company_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get saved company record by ID.

        Args:
            record_id: Record ID

        Returns:
            Saved company record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM saved_companies WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    return self._parse_record(dict(row))

                if self.debug:
                    self._print_important(f"{Icons.WARNING} Saved company not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_company_by_id: {e}", COLORS["red"])
            return None

    def get_saved_company(
            self,
            user_website: str,
            client_website: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get saved company record by user and client websites.

        Args:
            user_website: User website URL
            client_website: Client website URL

        Returns:
            Saved company record or None if not found
        """
        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE user_website = ? AND client_website = ?
                ''', (normalized_user, normalized_client))

                row = cursor.fetchone()

                if row:
                    return self._parse_record(dict(row))

                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_company: {e}", COLORS["red"])
            return None

    def update_chat_data(
            self,
            user_website: str,
            client_website: str,
            chat_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update chat data for a saved company.

        Args:
            user_website: User website URL
            client_website: Client website URL
            chat_data: New chat data

        Returns:
            Updated record or None if failed
        """
        # Validate chat data
        chat_valid, chat_result = self._validate_json(chat_data, "chat")
        if not chat_valid:
            self._print_important(f"{Icons.ERROR} {chat_result}", COLORS["red"])
            return None

        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE saved_companies 
                    SET chat = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_website = ? AND client_website = ?
                ''', (chat_result, normalized_user, normalized_client))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.CHAT} Updated chat data: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )
                    return self.get_saved_company(normalized_user, normalized_client)
                else:
                    # Try to create new record if doesn't exist
                    return self.save_company(
                        user_website=user_website,
                        client_website=client_website,
                        chat_data=chat_data,
                        mail_data=None
                    )

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_chat_data: {e}", COLORS["red"])
            return None

    def update_mail_data(
            self,
            user_website: str,
            client_website: str,
            mail_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update mail data for a saved company.

        Args:
            user_website: User website URL
            client_website: Client website URL
            mail_data: New mail data

        Returns:
            Updated record or None if failed
        """
        # Validate mail data
        mail_valid, mail_result = self._validate_json(mail_data, "mail")
        if not mail_valid:
            self._print_important(f"{Icons.ERROR} {mail_result}", COLORS["red"])
            return None

        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE saved_companies 
                    SET mail = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_website = ? AND client_website = ?
                ''', (mail_result, normalized_user, normalized_client))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.MAIL} Updated mail data: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )
                    return self.get_saved_company(normalized_user, normalized_client)
                else:
                    # Try to create new record if doesn't exist
                    return self.save_company(
                        user_website=user_website,
                        client_website=client_website,
                        chat_data=None,
                        mail_data=mail_data
                    )

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_mail_data: {e}", COLORS["red"])
            return None

    def delete_saved_company(self, identifier: Any) -> bool:
        """
        Delete saved company record.

        Args:
            identifier: Can be:
                       - int: Record ID
                       - tuple: (user_website, client_website)
                       - str: Single website (deletes all records with that website)

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if isinstance(identifier, int):
                    # Delete by ID
                    cursor.execute('DELETE FROM saved_companies WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by websites
                    normalized_user = self._normalize_website(identifier[0])
                    normalized_client = self._normalize_website(identifier[1])
                    cursor.execute('''
                        DELETE FROM saved_companies 
                        WHERE user_website = ? AND client_website = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this website
                    normalized = self._normalize_website(identifier)
                    cursor.execute('''
                        DELETE FROM saved_companies 
                        WHERE user_website = ? OR client_website = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} saved company record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching saved company records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_saved_company: {e}", COLORS["red"])
            return False

    def get_saved_companies_by_user(self, user_website: str) -> List[Dict[str, Any]]:
        """
        Get all saved companies for a specific user website.

        Args:
            user_website: User website URL

        Returns:
            List of saved company records
        """
        normalized_user = self._normalize_website(user_website)

        try:
            print(self.db_path)
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE user_website = ?
                    ORDER BY created_at DESC
                ''', (normalized_user,))

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} saved companies for user: {normalized_user}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_by_user: {e}", COLORS["red"])
            return []

    def get_saved_companies_by_client(self, client_website: str) -> List[Dict[str, Any]]:
        """
        Get all saved companies for a specific client website.

        Args:
            client_website: Client website URL

        Returns:
            List of saved company records
        """
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE client_website = ?
                    ORDER BY created_at DESC
                ''', (normalized_client,))

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} saved companies for client: {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_by_client: {e}", COLORS["red"])
            return []

    def get_all_saved_companies(
            self,
            limit: Optional[int] = None,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get saved company records with optional pagination.
        If limit is None, returns all records.

        Args:
            limit: Maximum number of records to return (None = all)
            offset: Number of records to skip

        Returns:
            List of saved company records as dictionaries with serializable types
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if limit is None:
                    cursor.execute('''
                        SELECT * FROM saved_companies 
                        ORDER BY created_at DESC
                    ''')
                else:
                    cursor.execute('''
                        SELECT * FROM saved_companies 
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                rows = cursor.fetchall()

                # Convert to list of dictionaries
                records = []
                for row in rows:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))

                    # Apply any additional parsing first
                    parsed_record = self._parse_record(row_dict)

                    # Then ensure all values are JSON serializable
                    serializable_record = {}
                    for key, value in parsed_record.items():
                        if value is None:
                            serializable_record[key] = None
                        elif hasattr(value, 'isoformat') and callable(value.isoformat):
                            # Handle datetime/date objects
                            serializable_record[key] = value.isoformat()
                        elif isinstance(value, (int, float, str, bool)):
                            serializable_record[key] = value
                        elif isinstance(value, (list, dict)):
                            # Recursively handle nested structures if any
                            serializable_record[key] = value
                        else:
                            # Convert anything else to string
                            serializable_record[key] = str(value)

                    records.append(serializable_record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} saved company records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_saved_companies: {e}", COLORS["red"])
            return []

    def search_saved_companies(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search saved companies by website URLs.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in. If None, searches both websites.
                         Options: ['user_website', 'client_website']

        Returns:
            List of matching saved company records
        """
        if not search_text:
            #self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Normalize search text
        search_text = search_text.strip().lower()

        # Default fields to search
        if search_fields is None:
            search_fields = ['user_website', 'client_website']

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build WHERE clause
                where_conditions = []
                params = []

                for field in search_fields:
                    if field in ['user_website', 'client_website']:
                        where_conditions.append(f"{field} LIKE ?")
                        params.append(f'%{search_text}%')

                if not where_conditions:
                    return []

                where_clause = " OR ".join(where_conditions)
                query = f'''
                    SELECT * FROM saved_companies 
                    WHERE ({where_clause})
                    ORDER BY created_at DESC
                '''

                cursor.execute(query, params)
                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.SEARCH} Found {len(records)} saved companies matching '{search_text}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_saved_companies: {e}", COLORS["red"])
            return []

    def get_saved_companies_count(self) -> Dict[str, int]:
        """
        Get statistics about saved company records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM saved_companies')
                total = cursor.fetchone()[0]

                # Count with chat data
                cursor.execute('SELECT COUNT(*) FROM saved_companies WHERE chat IS NOT NULL')
                with_chat = cursor.fetchone()[0]

                # Count with mail data
                cursor.execute('SELECT COUNT(*) FROM saved_companies WHERE mail IS NOT NULL')
                with_mail = cursor.fetchone()[0]

                # Count with both
                cursor.execute('SELECT COUNT(*) FROM saved_companies WHERE chat IS NOT NULL AND mail IS NOT NULL')
                with_both = cursor.fetchone()[0]

                # Unique user websites
                cursor.execute('SELECT COUNT(DISTINCT user_website) FROM saved_companies')
                unique_users = cursor.fetchone()[0]

                # Unique client websites
                cursor.execute('SELECT COUNT(DISTINCT client_website) FROM saved_companies')
                unique_clients = cursor.fetchone()[0]

                stats = {
                    'total_saved_companies': total,
                    'with_chat_data': with_chat,
                    'with_mail_data': with_mail,
                    'with_both_data': with_both,
                    'unique_user_websites': unique_users,
                    'unique_client_websites': unique_clients
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.INFO} Saved companies stats: {total} total, "
                        f"{with_chat} with chat, {with_mail} with mail, "
                        f"{unique_users} unique users, {unique_clients} unique clients",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_count: {e}", COLORS["red"])
            return {}

    def clear_all_saved_companies(self) -> bool:
        """
        Clear all saved company records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM saved_companies')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM saved_companies')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} saved company records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_saved_companies: {e}", COLORS["red"])
            return False

    def add_chat_message(
            self,
            user_website: str,
            client_website: str,
            message: Dict[str, Any],
            max_messages: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Add a chat message to saved company chat data.

        Args:
            user_website: User website URL
            client_website: Client website URL
            message: Chat message dictionary (should contain at least 'text' and 'timestamp')
            max_messages: Maximum number of messages to keep

        Returns:
            Updated record or None if failed
        """
        # Get existing chat data
        saved_company = self.get_saved_company(user_website, client_website)
        existing_chat = saved_company.get('chat') if saved_company else None

        # Prepare chat data
        if existing_chat and isinstance(existing_chat, dict):
            messages = existing_chat.get('messages', [])
        elif existing_chat and isinstance(existing_chat, list):
            messages = existing_chat
        else:
            messages = []

        # Add timestamp if not provided
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()

        # Add message
        messages.append(message)

        # Limit messages
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        # Update chat data
        chat_data = {
            'messages': messages,
            'last_updated': datetime.now().isoformat(),
            'message_count': len(messages)
        }

        return self.update_chat_data(user_website, client_website, chat_data)

    def get_chat_history(
            self,
            user_website: str,
            client_website: str,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a saved company.

        Args:
            user_website: User website URL
            client_website: Client website URL
            limit: Maximum number of messages to return

        Returns:
            List of chat messages
        """
        saved_company = self.get_saved_company(user_website, client_website)
        if not saved_company:
            return []

        chat_data = saved_company.get('chat')
        if not chat_data:
            return []

        if isinstance(chat_data, dict):
            messages = chat_data.get('messages', [])
        elif isinstance(chat_data, list):
            messages = chat_data
        else:
            return []

        # Return limited messages (most recent first)
        return messages[-limit:][::-1] if messages else []

    def get_companies_with_chat(self) -> List[Dict[str, Any]]:
        """
        Get all saved companies that have chat data.

        Returns:
            List of saved companies with chat data
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE chat IS NOT NULL
                    ORDER BY updated_at DESC
                ''')

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.CHAT} Found {len(records)} companies with chat data",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_companies_with_chat: {e}", COLORS["red"])
            return []

    def get_companies_with_mail(self) -> List[Dict[str, Any]]:
        """
        Get all saved companies that have mail data.

        Returns:
            List of saved companies with mail data
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE mail IS NOT NULL
                    ORDER BY updated_at DESC
                ''')

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.MAIL} Found {len(records)} companies with mail data",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_companies_with_mail: {e}", COLORS["red"])
            return []





class SavedCompaniesTable:
    """Handles operations for the saved_companies table."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys if needed
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_table(self) -> None:
        """Create the saved_companies table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_unique_name TEXT NOT NULL,
                    client_unique_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_unique_name, client_unique_name)  -- Ensure unique combinations
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_user_unique_name ON saved_companies(user_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_client_unique_name ON saved_companies(client_unique_name)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_saved_both_names ON saved_companies(user_unique_name, client_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_saved_created_at ON saved_companies(created_at DESC)')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_saved_companies_timestamp 
                AFTER UPDATE ON saved_companies
                BEGIN
                    UPDATE saved_companies 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            # self._print_important(f"{Icons.DATABASE} Saved companies table initialized", COLORS["green"])

    def _normalize_name(self, name: str) -> str:
        """Normalize name for consistent storage."""
        if not name:
            return ""

        name = name.strip().lower()
        return name

    def _parse_record(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse database record for internal use (strings → Python objects).
        Use this when you need to work with the data in Python.
        """
        record = dict(row)

        # Parse timestamps to datetime objects
        for field in ['created_at', 'updated_at']:
            if record.get(field) and isinstance(record[field], str):
                try:
                    record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                except ValueError:
                    pass

        return record

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize record for JSON output (Python objects → JSON-safe types).
        Use this when you need to return data via API or save to JSON.
        """
        serialized = {}

        for key, value in record.items():
            if isinstance(value, datetime):
                # Convert datetime to ISO format string
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                # These are already JSON serializable if they contain JSON-safe types
                serialized[key] = value
            else:
                serialized[key] = value

        return serialized

    def save_company(
            self,
            user_unique_name: str,
            client_unique_name: str,
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Save or update a company.

        Args:
            user_unique_name: The user's unique name
            client_unique_name: The client's unique name
            replace: If True, replace existing saved company

        Returns:
            Saved company record if successful, None if failed
        """
        # Normalize names
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid name provided", COLORS["red"])
            return None

        # Check if already exists
        existing = self.get_saved_company(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record (just update timestamp)
                    cursor.execute('''
                        UPDATE saved_companies 
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated saved company: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_saved_company(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Company already saved: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO saved_companies (user_unique_name, client_unique_name)
                        VALUES (?, ?)
                    ''', (normalized_user, normalized_client))

                    conn.commit()
                    record_id = cursor.lastrowid

                    self._print_important(
                        f"{Icons.SAVE} Saved company #{record_id}: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_saved_company_by_id(record_id)

        except sqlite3.IntegrityError as e:
            self._print_important(f"{Icons.ERROR} Database integrity error: {e}", COLORS["red"])
            return existing or None
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in save_company: {e}", COLORS["red"])
            return None

    def get_saved_company_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get saved company record by ID.

        Args:
            record_id: Record ID

        Returns:
            Saved company record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM saved_companies WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    return self._parse_record(dict(row))

                if self.debug:
                    self._print_important(f"{Icons.WARNING} Saved company not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_company_by_id: {e}", COLORS["red"])
            return None

    def get_saved_company(
            self,
            user_unique_name: str,
            client_unique_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get saved company record by user and client unique names.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name

        Returns:
            Saved company record or None if not found
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE user_unique_name = ? AND client_unique_name = ?
                ''', (normalized_user, normalized_client))

                row = cursor.fetchone()

                if row:
                    return self._parse_record(dict(row))

                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_company: {e}", COLORS["red"])
            return None

    def delete_saved_company(self, identifier: Any) -> bool:
        """
        Delete saved company record.

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
                    cursor.execute('DELETE FROM saved_companies WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by names
                    normalized_user = self._normalize_name(identifier[0])
                    normalized_client = self._normalize_name(identifier[1])
                    cursor.execute('''
                        DELETE FROM saved_companies 
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this name
                    normalized = self._normalize_name(identifier)
                    cursor.execute('''
                        DELETE FROM saved_companies 
                        WHERE user_unique_name = ? OR client_unique_name = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} saved company record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching saved company records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_saved_company: {e}", COLORS["red"])
            return False

    def get_saved_companies_by_user(self, user_unique_name: str) -> List[Dict[str, Any]]:
        """
        Get all saved companies for a specific user.

        Args:
            user_unique_name: User unique name

        Returns:
            List of saved company records
        """
        normalized_user = self._normalize_name(user_unique_name)

        try:
            print(self.db_path)
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE user_unique_name = ?
                    ORDER BY created_at DESC
                ''', (normalized_user,))

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} saved companies for user: {normalized_user}",
                    COLORS["blue"]
                 )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_by_user: {e}", COLORS["red"])
            return []

    def get_saved_companies_by_client(self, client_unique_name: str) -> List[Dict[str, Any]]:
        """
        Get all saved companies for a specific client.

        Args:
            client_unique_name: Client unique name

        Returns:
            List of saved company records
        """
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM saved_companies 
                    WHERE client_unique_name = ?
                    ORDER BY created_at DESC
                ''', (normalized_client,))

                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} saved companies for client: {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_by_client: {e}", COLORS["red"])
            return []

    def get_all_saved_companies(
            self,
            limit: Optional[int] = None,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get saved company records with optional pagination.
        If limit is None, returns all records.

        Args:
            limit: Maximum number of records to return (None = all)
            offset: Number of records to skip

        Returns:
            List of saved company records as dictionaries with serializable types
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if limit is None:
                    cursor.execute('''
                        SELECT * FROM saved_companies 
                        ORDER BY created_at DESC
                    ''')
                else:
                    cursor.execute('''
                        SELECT * FROM saved_companies 
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                rows = cursor.fetchall()

                # Convert to list of dictionaries
                records = []
                for row in rows:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))

                    # Apply any additional parsing first
                    parsed_record = self._parse_record(row_dict)

                    # Then ensure all values are JSON serializable
                    serializable_record = {}
                    for key, value in parsed_record.items():
                        if value is None:
                            serializable_record[key] = None
                        elif hasattr(value, 'isoformat') and callable(value.isoformat):
                            # Handle datetime/date objects
                            serializable_record[key] = value.isoformat()
                        elif isinstance(value, (int, float, str, bool)):
                            serializable_record[key] = value
                        elif isinstance(value, (list, dict)):
                            # Recursively handle nested structures if any
                            serializable_record[key] = value
                        else:
                            # Convert anything else to string
                            serializable_record[key] = str(value)

                    records.append(serializable_record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} saved company records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_saved_companies: {e}", COLORS["red"])
            return []

    def search_saved_companies(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search saved companies by unique names.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in. If None, searches both names.
                         Options: ['user_unique_name', 'client_unique_name']

        Returns:
            List of matching saved company records
        """
        if not search_text:
            self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Normalize search text
        search_text = search_text.strip().lower()

        # Default fields to search
        if search_fields is None:
            search_fields = ['user_unique_name', 'client_unique_name']

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build WHERE clause
                where_conditions = []
                params = []

                for field in search_fields:
                    if field in ['user_unique_name', 'client_unique_name']:
                        where_conditions.append(f"{field} LIKE ?")
                        params.append(f'%{search_text}%')

                if not where_conditions:
                    return []

                where_clause = " OR ".join(where_conditions)
                query = f'''
                    SELECT * FROM saved_companies 
                    WHERE ({where_clause})
                    ORDER BY created_at DESC
                '''

                cursor.execute(query, params)
                rows = cursor.fetchall()
                records = [self._parse_record(dict(row)) for row in rows]

                self._print_important(
                    f"{Icons.SEARCH} Found {len(records)} saved companies matching '{search_text}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_saved_companies: {e}", COLORS["red"])
            return []

    def get_saved_companies_count(self) -> Dict[str, int]:
        """
        Get statistics about saved company records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM saved_companies')
                total = cursor.fetchone()[0]

                # Unique user names
                cursor.execute('SELECT COUNT(DISTINCT user_unique_name) FROM saved_companies')
                unique_users = cursor.fetchone()[0]

                # Unique client names
                cursor.execute('SELECT COUNT(DISTINCT client_unique_name) FROM saved_companies')
                unique_clients = cursor.fetchone()[0]

                stats = {
                    'total_saved_companies': total,
                    'unique_user_names': unique_users,
                    'unique_client_names': unique_clients
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.INFO} Saved companies stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_saved_companies_count: {e}", COLORS["red"])
            return {}

    def clear_all_saved_companies(self) -> bool:
        """
        Clear all saved company records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM saved_companies')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM saved_companies')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} saved company records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_saved_companies: {e}", COLORS["red"])
            return False