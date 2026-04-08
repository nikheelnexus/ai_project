import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock

# Thread-safe print lock
print_lock = Lock()
import os
from company_ai_project.saved_data import user_data

database = os.path.join(
    os.path.abspath(os.path.dirname(user_data.__file__)),
    'user_email_database.db'
)

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
    EMAIL = '📧'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '📝'
    JSON = '📄'
    STATS = '📊'
    TYPE = '🏷️'


class UserEmailDB:
    """Handles operations for the user_email table with JSON data storage."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_email_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys if needed in the future
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_user_email_table(self) -> None:
        """Create the user_email table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_email (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_unique_name TEXT NOT NULL,
                    client_unique_name TEXT NOT NULL,
                    email_type TEXT NOT NULL,
                    jsondata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_unique_name ON user_email(user_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_unique_name ON user_email(client_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_type ON user_email(email_type)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_user_client_type ON user_email(user_unique_name, client_unique_name, email_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON user_email(created_at DESC)')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_email_timestamp 
                AFTER UPDATE ON user_email
                BEGIN
                    UPDATE user_email 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            #self._print_important(f"{Icons.DATABASE} User email table initialized", COLORS["green"])

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

    def insert_email(
            self,
            user_unique_name: str,
            client_unique_name: str,
            email_type: str,
            json_data: Any,
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a new email record.

        Args:
            user_unique_name: The user's unique name
            client_unique_name: The client's unique name
            email_type: Type/category of email (e.g., 'invoice', 'newsletter', 'support')
            json_data: JSON data to store (dict, list, or JSON string)
            replace: If True, replace existing email for same names and type

        Returns:
            Email record if successful, None if failed
        """
        # Normalize names
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)
        normalized_type = email_type.strip().lower()

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid name provided", COLORS["red"])
            return None

        if not normalized_type:
            self._print_important(f"{Icons.ERROR} Email type cannot be empty", COLORS["red"])
            return None

        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        # Check if email already exists
        existing = self.get_email_by_names_type(normalized_user, normalized_client, normalized_type)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_email 
                        SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_unique_name = ? AND client_unique_name = ? AND email_type = ?
                    ''', (json_result, normalized_user, normalized_client, normalized_type))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated email: {normalized_user} → {normalized_client} ({normalized_type})",
                        COLORS["green"]
                    )

                    return self.get_email_by_names_type(normalized_user, normalized_client, normalized_type)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Email already exists: {normalized_user} → {normalized_client} ({normalized_type})",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_email (user_unique_name, client_unique_name, email_type, jsondata)
                        VALUES (?, ?, ?, ?)
                    ''', (normalized_user, normalized_client, normalized_type, json_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    self._print_important(
                        f"{Icons.SUCCESS} Inserted email #{record_id}: {normalized_user} → {normalized_client} ({normalized_type})",
                        COLORS["green"]
                    )

                    return self.get_email_by_id(record_id)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in insert_email: {e}", COLORS["red"])
            return None

    def get_email_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get email record by ID.

        Args:
            record_id: Record ID

        Returns:
            Email record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM user_email WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    record = dict(row)
                    # Parse JSON data
                    try:
                        record['jsondata'] = json.loads(record['jsondata'])
                    except json.JSONDecodeError:
                        pass  # Keep as string if can't parse

                    # Parse timestamps
                    for field in ['created_at', 'updated_at']:
                        if record[field] and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                            except ValueError:
                                pass

                    return record

                if self.debug:
                    self._print_important(f"{Icons.WARNING} Email not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_email_by_id: {e}", COLORS["red"])
            return None

    def get_email_by_names_type(
            self,
            user_unique_name: str,
            client_unique_name: str,
            email_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get email record by user unique name, client unique name, and email type.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name
            email_type: Email type

        Returns:
            Email record or None if not found
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)
        normalized_type = email_type.strip().lower()

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_email 
                    WHERE user_unique_name = ? AND client_unique_name = ? AND email_type = ?
                ''', (normalized_user, normalized_client, normalized_type))

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
            self._print_important(f"{Icons.ERROR} Database error in get_email_by_names_type: {e}", COLORS["red"])
            return None

    def get_emails_by_user_and_client(
            self,
            user_unique_name: str,
            client_unique_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get all email records between a specific user and client.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name

        Returns:
            List of email records
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_email 
                    WHERE user_unique_name = ? AND client_unique_name = ?
                    ORDER BY created_at DESC
                ''', (normalized_user, normalized_client))

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

                #self._print_important(
                #    f"{Icons.INFO} Found {len(records)} emails between {normalized_user} → {normalized_client}",
                #    COLORS["blue"]
                #)
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_emails_by_user_and_client: {e}", COLORS["red"])
            return []

    def update_email_json(
            self,
            record_id: int,
            json_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update JSON data for an email record.

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
                    UPDATE user_email 
                    SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json_result, record_id))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated JSON for email #{record_id}",
                        COLORS["green"]
                    )
                    return self.get_email_by_id(record_id)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Email not found: ID {record_id}",
                        COLORS["yellow"]
                    )
                    return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_email_json: {e}", COLORS["red"])
            return None

    def delete_email(self, identifier: Any) -> bool:
        """
        Delete email record by ID, names and type, or single name.

        Args:
            identifier: Can be:
                       - int: Record ID
                       - tuple: (user_unique_name, client_unique_name, email_type)
                       - str: Single name (deletes all records with that name)

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if isinstance(identifier, int):
                    # Delete by ID
                    cursor.execute('DELETE FROM user_email WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 3:
                    # Delete by names and type
                    normalized_user = self._normalize_name(identifier[0])
                    normalized_client = self._normalize_name(identifier[1])
                    normalized_type = identifier[2].strip().lower()

                    cursor.execute('''
                        DELETE FROM user_email 
                        WHERE user_unique_name = ? AND client_unique_name = ? AND email_type = ?
                    ''', (normalized_user, normalized_client, normalized_type))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this name
                    normalized = self._normalize_name(identifier)
                    cursor.execute('''
                        DELETE FROM user_email 
                        WHERE user_unique_name = ? OR client_unique_name = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} email record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching email records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_email: {e}", COLORS["red"])
            return False

    def get_user_emails(self, user_unique_name: str, email_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all emails sent by a specific user.

        Args:
            user_unique_name: User unique name
            email_type: Optional filter by email type

        Returns:
            List of email records
        """
        normalized_user = self._normalize_name(user_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if email_type:
                    normalized_type = email_type.strip().lower()
                    cursor.execute('''
                        SELECT * FROM user_email 
                        WHERE user_unique_name = ? AND email_type = ?
                        ORDER BY created_at DESC
                    ''', (normalized_user, normalized_type))
                else:
                    cursor.execute('''
                        SELECT * FROM user_email 
                        WHERE user_unique_name = ?
                        ORDER BY created_at DESC
                    ''', (normalized_user,))

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

                type_filter = f" of type '{email_type}'" if email_type else ""
                self._print_important(
                    f"{Icons.INFO} Found {len(records)} emails from user {normalized_user}{type_filter}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_emails: {e}", COLORS["red"])
            return []

    def get_client_emails(self, client_unique_name: str, email_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all emails received by a specific client.

        Args:
            client_unique_name: Client unique name
            email_type: Optional filter by email type

        Returns:
            List of email records
        """
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if email_type:
                    normalized_type = email_type.strip().lower()
                    cursor.execute('''
                        SELECT * FROM user_email 
                        WHERE client_unique_name = ? AND email_type = ?
                        ORDER BY created_at DESC
                    ''', (normalized_client, normalized_type))
                else:
                    cursor.execute('''
                        SELECT * FROM user_email 
                        WHERE client_unique_name = ?
                        ORDER BY created_at DESC
                    ''', (normalized_client,))

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

                type_filter = f" of type '{email_type}'" if email_type else ""
                self._print_important(
                    f"{Icons.INFO} Found {len(records)} emails to client {normalized_client}{type_filter}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_client_emails: {e}", COLORS["red"])
            return []

    def get_emails_by_type(self, email_type: str) -> List[Dict[str, Any]]:
        """
        Get all emails of a specific type.

        Args:
            email_type: Email type to filter by

        Returns:
            List of email records
        """
        normalized_type = email_type.strip().lower()

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_email 
                    WHERE email_type = ?
                    ORDER BY created_at DESC
                ''', (normalized_type,))

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
                    f"{Icons.TYPE} Found {len(records)} emails of type '{normalized_type}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_emails_by_type: {e}", COLORS["red"])
            return []

    def get_all_emails(
            self,
            limit: int = 100,
            offset: int = 0,
            email_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all email records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            email_type: Optional filter by email type

        Returns:
            List of email records
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if email_type:
                    normalized_type = email_type.strip().lower()
                    cursor.execute('''
                        SELECT * FROM user_email 
                        WHERE email_type = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (normalized_type, limit, offset))
                else:
                    cursor.execute('''
                        SELECT * FROM user_email 
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

                type_filter = f" of type '{email_type}'" if email_type else ""
                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} email records{type_filter}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_emails: {e}", COLORS["red"])
            return []

    def search_emails(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search emails by names or type.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in. If None, searches all fields.
                         Options: ['user_unique_name', 'client_unique_name', 'email_type']

        Returns:
            List of matching email records
        """
        if not search_text:
            #self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Normalize search text
        search_text = search_text.strip().lower()

        # Default fields to search
        if search_fields is None:
            search_fields = ['user_unique_name', 'client_unique_name', 'email_type']

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build WHERE clause
                where_conditions = []
                params = []

                for field in search_fields:
                    if field in ['user_unique_name', 'client_unique_name', 'email_type']:
                        where_conditions.append(f"{field} LIKE ?")
                        params.append(f'%{search_text}%')

                if not where_conditions:
                    return []

                where_clause = " OR ".join(where_conditions)
                query = f'''
                    SELECT * FROM user_email 
                    WHERE ({where_clause})
                    ORDER BY created_at DESC
                '''

                cursor.execute(query, params)
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
                    f"{Icons.SEARCH} Found {len(records)} emails matching '{search_text}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_emails: {e}", COLORS["red"])
            return []

    def get_email_count(self) -> Dict[str, int]:
        """
        Get statistics about email records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM user_email')
                total = cursor.fetchone()[0]

                # Count of unique user names
                cursor.execute('SELECT COUNT(DISTINCT user_unique_name) FROM user_email')
                unique_users = cursor.fetchone()[0]

                # Count of unique client names
                cursor.execute('SELECT COUNT(DISTINCT client_unique_name) FROM user_email')
                unique_clients = cursor.fetchone()[0]

                # Count of unique email types
                cursor.execute('SELECT COUNT(DISTINCT email_type) FROM user_email')
                unique_types = cursor.fetchone()[0]

                # Most common email type
                cursor.execute(
                    'SELECT email_type, COUNT(*) as count FROM user_email GROUP BY email_type ORDER BY count DESC LIMIT 1')
                most_common_type_result = cursor.fetchone()
                most_common_type = most_common_type_result[0] if most_common_type_result else None
                most_common_type_count = most_common_type_result[1] if most_common_type_result else 0

                # Most recent email
                cursor.execute('SELECT MAX(created_at) FROM user_email')
                most_recent = cursor.fetchone()[0]

                stats = {
                    'total_emails': total,
                    'unique_user_names': unique_users,
                    'unique_client_names': unique_clients,
                    'unique_email_types': unique_types,
                    'most_common_type': most_common_type,
                    'most_common_type_count': most_common_type_count,
                    'most_recent': most_recent
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.STATS} Email stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients, "
                        f"{unique_types} types",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_email_count: {e}", COLORS["red"])
            return {}

    def clear_all_emails(self) -> bool:
        """
        Clear all email records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM user_email')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM user_email')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} email records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_emails: {e}", COLORS["red"])
            return False

    def batch_insert_emails(
            self,
            emails: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Insert multiple email records in a batch.

        Args:
            emails: List of dictionaries with user_unique_name, client_unique_name, email_type, and jsondata

        Returns:
            List of inserted records (or None for failed ones)
        """
        results = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for i, email in enumerate(emails):
                    try:
                        # Validate required fields
                        if not all(key in email for key in ['user_unique_name', 'client_unique_name', 'email_type', 'jsondata']):
                            self._print_important(
                                f"{Icons.ERROR} Email #{i} missing required fields",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        normalized_user = self._normalize_name(email['user_unique_name'])
                        normalized_client = self._normalize_name(email['client_unique_name'])
                        normalized_type = email['email_type'].strip().lower()

                        # Validate JSON
                        is_valid, json_result = self._validate_json(email['jsondata'])
                        if not is_valid:
                            self._print_important(
                                f"{Icons.ERROR} Email #{i}: {json_result}",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        # Insert record
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_email 
                            (user_unique_name, client_unique_name, email_type, jsondata)
                            VALUES (?, ?, ?, ?)
                        ''', (normalized_user, normalized_client, normalized_type, json_result))

                        record_id = cursor.lastrowid
                        results.append(self.get_email_by_id(record_id))

                    except Exception as e:
                        self._print_important(
                            f"{Icons.ERROR} Error processing email #{i}: {e}",
                            COLORS["red"]
                        )
                        results.append(None)

                conn.commit()

                success_count = sum(1 for r in results if r is not None)
                self._print_important(
                    f"{Icons.SUCCESS} Batch insert complete: {success_count}/{len(emails)} successful",
                    COLORS["green"]
                )

                return results

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in batch_insert_emails: {e}", COLORS["red"])
            return [None] * len(emails)

    def get_email_types(self) -> List[str]:
        """
        Get all unique email types in the database_old.

        Returns:
            List of email types
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT DISTINCT email_type FROM user_email ORDER BY email_type')
                rows = cursor.fetchall()

                types = [row[0] for row in rows]

                self._print_important(
                    f"{Icons.TYPE} Found {len(types)} unique email types",
                    COLORS["blue"]
                )
                return types

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_email_types: {e}", COLORS["red"])
            return []

    def get_email_summary(self, email_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for emails.

        Args:
            email_type: Optional filter by email type

        Returns:
            Dictionary with summary statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if email_type:
                    normalized_type = email_type.strip().lower()
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT user_unique_name) as unique_senders,
                            COUNT(DISTINCT client_unique_name) as unique_receivers,
                            MIN(created_at) as first_email,
                            MAX(created_at) as last_email
                        FROM user_email 
                        WHERE email_type = ?
                    ''', (normalized_type,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT user_unique_name) as unique_senders,
                            COUNT(DISTINCT client_unique_name) as unique_receivers,
                            MIN(created_at) as first_email,
                            MAX(created_at) as last_email
                        FROM user_email
                    ''')

                row = cursor.fetchone()

                summary = {
                    'total_emails': row[0],
                    'unique_senders': row[1],
                    'unique_receivers': row[2],
                    'first_email': row[3],
                    'last_email': row[4],
                    'email_type': email_type
                }

                return summary

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_email_summary: {e}", COLORS["red"])
            return {}