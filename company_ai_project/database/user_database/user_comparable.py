import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
import os
from company_ai_project.saved_data import user_data
from common_script import common

database = os.path.join(
    os.path.abspath(os.path.dirname(user_data.__file__)),
    'user_comparable_database.db'
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
    COMPARE = '🔄'
    WEBSITE = '🌐'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '📝'
    JSON = '📄'
    STATS = '📊'


class _UserComparableDB:
    """Handles operations for the user_comparable table with JSON data storage."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_comparable_table()

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

    def create_user_comparable_table(self) -> None:
        """Create the user_comparable table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_comparable (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_website TEXT NOT NULL,
                    client_website TEXT NOT NULL,
                    jsondata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_website ON user_comparable(user_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_website ON user_comparable(client_website)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_both_websites ON user_comparable(user_website, client_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON user_comparable(created_at DESC)')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_comparable_timestamp 
                AFTER UPDATE ON user_comparable
                BEGIN
                    UPDATE user_comparable 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            #self._print_important(f"{Icons.DATABASE} User comparable table initialized", COLORS["green"])

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

    def _normalize_website(self, website: str) -> str:
        """Normalize website URL for consistent storage."""
        if not website:
            return ""

        website = common.format_website_url(website)
        '''
        website = website.strip().lower()

        # Remove protocol and www
        if website.startswith('https://'):
            website = website[8:]
        elif website.startswith('http://'):
            website = website[7:]

        if website.startswith('www.'):
            website = website[4:]

        # Remove trailing slash
        website = website.rstrip('/')
        '''
        return website

    def insert_comparison(
            self,
            user_website: str,
            client_website: str,
            json_data: Any,
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a new comparison record.

        Args:
            user_website: The user's website URL
            client_website: The client's website URL
            json_data: JSON data to store (dict, list, or JSON string)
            replace: If True, replace existing comparison for same websites

        Returns:
            Comparison record if successful, None if failed
        """
        # Normalize websites
        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        if not normalized_user or not normalized_client:
            self._print_important(f"{Icons.ERROR} Invalid website URL provided", COLORS["red"])
            return None

        # Validate JSON
        is_valid, json_result = self._validate_json(json_data)
        if not is_valid:
            self._print_important(f"{Icons.ERROR} {json_result}", COLORS["red"])
            return None

        # Check if comparison already exists
        existing = self.get_comparison_by_websites(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_comparable 
                        SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_website = ? AND client_website = ?
                    ''', (json_result, normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated comparison: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_comparison_by_websites(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Comparison already exists: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_comparable (user_website, client_website, jsondata)
                        VALUES (?, ?, ?)
                    ''', (normalized_user, normalized_client, json_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    self._print_important(
                        f"{Icons.SUCCESS} Inserted comparison #{record_id}: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_comparison_by_id(record_id)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in insert_comparison: {e}", COLORS["red"])
            return None

    def get_comparison_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comparison record by ID.

        Args:
            record_id: Record ID

        Returns:
            Comparison record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM user_comparable WHERE id = ?', (record_id,))
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
                    self._print_important(f"{Icons.WARNING} Comparison not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_by_id: {e}", COLORS["red"])
            return None

    def get_comparison_by_websites(
            self,
            user_website: str,
            client_website: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get comparison record by user and client websites.

        Args:
            user_website: User website URL
            client_website: Client website URL

        Returns:
            Comparison record or None if not found
        """
        normalized_user = self._normalize_website(user_website)
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
                    WHERE user_website = ? AND client_website = ?
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
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_by_websites: {e}", COLORS["red"])
            return None

    def update_comparison_json(
            self,
            record_id: int,
            json_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update JSON data for a comparison record.

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
                    UPDATE user_comparable 
                    SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json_result, record_id))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated JSON for comparison #{record_id}",
                        COLORS["green"]
                    )
                    return self.get_comparison_by_id(record_id)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Comparison not found: ID {record_id}",
                        COLORS["yellow"]
                    )
                    return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_comparison_json: {e}", COLORS["red"])
            return None

    def delete_comparison(self, identifier: Any) -> bool:
        """
        Delete comparison record by ID or websites.

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
                    cursor.execute('DELETE FROM user_comparable WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by websites
                    normalized_user = self._normalize_website(identifier[0])
                    normalized_client = self._normalize_website(identifier[1])
                    cursor.execute('''
                        DELETE FROM user_comparable 
                        WHERE user_website = ? AND client_website = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this website
                    normalized = self._normalize_website(identifier)
                    cursor.execute('''
                        DELETE FROM user_comparable 
                        WHERE user_website = ? OR client_website = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} comparison record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching comparison records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_comparison: {e}", COLORS["red"])
            return False

    def get_user_comparisons(self, user_website: str) -> List[Dict[str, Any]]:
        """
        Get all comparisons for a specific user website.

        Args:
            user_website: User website URL

        Returns:
            List of comparison records
        """
        normalized_user = self._normalize_website(user_website)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
                    WHERE user_website = ?
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

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} comparisons for user: {normalized_user}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_comparisons: {e}", COLORS["red"])
            return []

    def get_client_comparisons(self, client_website: str) -> List[Dict[str, Any]]:
        """
        Get all comparisons for a specific client website.

        Args:
            client_website: Client website URL

        Returns:
            List of comparison records
        """
        normalized_client = self._normalize_website(client_website)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
                    WHERE client_website = ?
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

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} comparisons for client: {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_client_comparisons: {e}", COLORS["red"])
            return []

    def get_all_comparisons(
            self,
            limit: Optional[int] = None,
            offset: int = 0,
            return_json_ready: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get comparison records with optional pagination.
        If limit is None, returns all records.

        Args:
            limit: Maximum number of records to return (None = all)
            offset: Number of records to skip
            return_json_ready: If True, returns dates as ISO format strings for JSON serialization

        Returns:
            List of comparison records
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if limit is None:
                    # Get all records
                    cursor.execute('''
                        SELECT * FROM user_comparable 
                        ORDER BY created_at DESC
                    ''')
                else:
                    # Get limited records
                    cursor.execute('''
                        SELECT * FROM user_comparable 
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)

                    # Handle date fields for JSON serialization
                    for field in ['created_at', 'updated_at']:
                        if record.get(field):
                            field_value = record[field]

                            if return_json_ready:
                                # Convert datetime to ISO format string for JSON serialization
                                if isinstance(field_value, datetime):
                                    record[field] = field_value.isoformat()
                                elif isinstance(field_value, str):
                                    # Try to parse and convert to ISO format
                                    try:
                                        # Clean and parse the string
                                        cleaned = field_value.replace('Z', '').replace('+00:00', '').strip()
                                        # Try common formats
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                                            try:
                                                dt = datetime.strptime(cleaned, fmt)
                                                record[field] = dt.isoformat()
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            # If no format worked, keep original
                                            pass
                                    except Exception:
                                        pass
                            else:
                                # Keep as datetime objects
                                if isinstance(field_value, str):
                                    try:
                                        cleaned = field_value.replace('Z', '').replace('+00:00', '').strip()
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                                            try:
                                                record[field] = datetime.strptime(cleaned, fmt)
                                                break
                                            except ValueError:
                                                continue
                                    except Exception:
                                        pass

                    records.append(record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} comparison records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_comparisons: {e}", COLORS["red"])
            return []

    def search_comparisons(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search comparisons by website URLs.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in. If None, searches both websites.
                         Options: ['user_website', 'client_website']

        Returns:
            List of matching comparison records
        """
        if not search_text:
            self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
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
                    SELECT * FROM user_comparable 
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
                    f"{Icons.SEARCH} Found {len(records)} comparisons matching '{search_text}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_comparisons: {e}", COLORS["red"])
            return []

    def get_comparison_count(self) -> Dict[str, int]:
        """
        Get statistics about comparison records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM user_comparable')
                total = cursor.fetchone()[0]

                # Count of unique user websites
                cursor.execute('SELECT COUNT(DISTINCT user_website) FROM user_comparable')
                unique_users = cursor.fetchone()[0]

                # Count of unique client websites
                cursor.execute('SELECT COUNT(DISTINCT client_website) FROM user_comparable')
                unique_clients = cursor.fetchone()[0]

                # Most recent comparison
                cursor.execute('SELECT MAX(created_at) FROM user_comparable')
                most_recent = cursor.fetchone()[0]

                stats = {
                    'total_comparisons': total,
                    'unique_user_websites': unique_users,
                    'unique_client_websites': unique_clients,
                    'most_recent': most_recent
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.STATS} Comparison stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_count: {e}", COLORS["red"])
            return {}

    def clear_all_comparisons(self) -> bool:
        """
        Clear all comparison records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM user_comparable')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM user_comparable')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} comparison records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_comparisons: {e}", COLORS["red"])
            return False

    def batch_insert_comparisons(
            self,
            comparisons: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Insert multiple comparison records in a batch.

        Args:
            comparisons: List of dictionaries with user_website, client_website, and jsondata

        Returns:
            List of inserted records (or None for failed ones)
        """
        results = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for i, comp in enumerate(comparisons):
                    try:
                        # Validate required fields
                        if not all(key in comp for key in ['user_website', 'client_website', 'jsondata']):
                            self._print_important(
                                f"{Icons.ERROR} Comparison #{i} missing required fields",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        normalized_user = self._normalize_website(comp['user_website'])
                        normalized_client = self._normalize_website(comp['client_website'])

                        # Validate JSON
                        is_valid, json_result = self._validate_json(comp['jsondata'])
                        if not is_valid:
                            self._print_important(
                                f"{Icons.ERROR} Comparison #{i}: {json_result}",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        # Insert record
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_comparable 
                            (user_website, client_website, jsondata)
                            VALUES (?, ?, ?)
                        ''', (normalized_user, normalized_client, json_result))

                        record_id = cursor.lastrowid
                        results.append(self.get_comparison_by_id(record_id))

                    except Exception as e:
                        self._print_important(
                            f"{Icons.ERROR} Error processing comparison #{i}: {e}",
                            COLORS["red"]
                        )
                        results.append(None)

                conn.commit()

                success_count = sum(1 for r in results if r is not None)
                self._print_important(
                    f"{Icons.SUCCESS} Batch insert complete: {success_count}/{len(comparisons)} successful",
                    COLORS["green"]
                )

                return results

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in batch_insert_comparisons: {e}", COLORS["red"])
            return [None] * len(comparisons)






class UserComparableDB:
    """Handles operations for the user_comparable table with JSON data storage."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_comparable_table()

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

    def create_user_comparable_table(self) -> None:
        """Create the user_comparable table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_comparable (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_unique_name TEXT NOT NULL,
                    client_unique_name TEXT NOT NULL,
                    jsondata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_unique_name ON user_comparable(user_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_unique_name ON user_comparable(client_unique_name)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_both_names ON user_comparable(user_unique_name, client_unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON user_comparable(created_at DESC)')

            # Create trigger to auto-update updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_comparable_timestamp 
                AFTER UPDATE ON user_comparable
                BEGIN
                    UPDATE user_comparable 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            ''')

            conn.commit()
            #self._print_important(f"{Icons.DATABASE} User comparable table initialized", COLORS["green"])

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

    def insert_comparison(
            self,
            user_unique_name: str,
            client_unique_name: str,
            json_data: Any,
            replace: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a new comparison record.

        Args:
            user_unique_name: The user's unique name
            client_unique_name: The client's unique name
            json_data: JSON data to store (dict, list, or JSON string)
            replace: If True, replace existing comparison for same names

        Returns:
            Comparison record if successful, None if failed
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

        # Check if comparison already exists
        existing = self.get_comparison_by_names(normalized_user, normalized_client)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if existing and replace:
                    # Update existing record
                    cursor.execute('''
                        UPDATE user_comparable 
                        SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (json_result, normalized_user, normalized_client))

                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Updated comparison: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_comparison_by_names(normalized_user, normalized_client)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Comparison already exists: {normalized_user} ↔ {normalized_client}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO user_comparable (user_unique_name, client_unique_name, jsondata)
                        VALUES (?, ?, ?)
                    ''', (normalized_user, normalized_client, json_result))

                    conn.commit()
                    record_id = cursor.lastrowid

                    self._print_important(
                        f"{Icons.SUCCESS} Inserted comparison #{record_id}: {normalized_user} ↔ {normalized_client}",
                        COLORS["green"]
                    )

                    return self.get_comparison_by_id(record_id)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in insert_comparison: {e}", COLORS["red"])
            return None

    def get_comparison_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comparison record by ID.

        Args:
            record_id: Record ID

        Returns:
            Comparison record or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM user_comparable WHERE id = ?', (record_id,))
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
                    self._print_important(f"{Icons.WARNING} Comparison not found: ID {record_id}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_by_id: {e}", COLORS["red"])
            return None

    def get_comparison_by_names(
            self,
            user_unique_name: str,
            client_unique_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get comparison record by user and client unique names.

        Args:
            user_unique_name: User unique name
            client_unique_name: Client unique name

        Returns:
            Comparison record or None if not found
        """
        normalized_user = self._normalize_name(user_unique_name)
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
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
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_by_names: {e}", COLORS["red"])
            return None

    def update_comparison_json(
            self,
            record_id: int,
            json_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update JSON data for a comparison record.

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
                    UPDATE user_comparable 
                    SET jsondata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json_result, record_id))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated JSON for comparison #{record_id}",
                        COLORS["green"]
                    )
                    return self.get_comparison_by_id(record_id)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Comparison not found: ID {record_id}",
                        COLORS["yellow"]
                    )
                    return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_comparison_json: {e}", COLORS["red"])
            return None

    def delete_comparison(self, identifier: Any) -> bool:
        """
        Delete comparison record by ID or names.

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
                    cursor.execute('DELETE FROM user_comparable WHERE id = ?', (identifier,))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, tuple) and len(identifier) == 2:
                    # Delete by names
                    normalized_user = self._normalize_name(identifier[0])
                    normalized_client = self._normalize_name(identifier[1])
                    cursor.execute('''
                        DELETE FROM user_comparable 
                        WHERE user_unique_name = ? AND client_unique_name = ?
                    ''', (normalized_user, normalized_client))
                    deleted_count = cursor.rowcount

                elif isinstance(identifier, str):
                    # Delete all records with this name
                    normalized = self._normalize_name(identifier)
                    cursor.execute('''
                        DELETE FROM user_comparable 
                        WHERE user_unique_name = ? OR client_unique_name = ?
                    ''', (normalized, normalized))
                    deleted_count = cursor.rowcount

                else:
                    self._print_important(f"{Icons.ERROR} Invalid identifier type", COLORS["red"])
                    return False

                conn.commit()

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} comparison record(s)",
                        COLORS["green"]
                    )
                    return True
                else:
                    self._print_important(
                        f"{Icons.WARNING} No matching comparison records found",
                        COLORS["yellow"]
                    )
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in delete_comparison: {e}", COLORS["red"])
            return False

    def get_user_comparisons(self, user_unique_name: str) -> List[Dict[str, Any]]:
        """
        Get all comparisons for a specific user.

        Args:
            user_unique_name: User unique name

        Returns:
            List of comparison records
        """
        normalized_user = self._normalize_name(user_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
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

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} comparisons for user: {normalized_user}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_comparisons: {e}", COLORS["red"])
            return []

    def get_client_comparisons(self, client_unique_name: str) -> List[Dict[str, Any]]:
        """
        Get all comparisons for a specific client.

        Args:
            client_unique_name: Client unique name

        Returns:
            List of comparison records
        """
        normalized_client = self._normalize_name(client_unique_name)

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM user_comparable 
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

                self._print_important(
                    f"{Icons.INFO} Found {len(records)} comparisons for client: {normalized_client}",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_client_comparisons: {e}", COLORS["red"])
            return []

    def get_all_comparisons(
            self,
            limit: Optional[int] = None,
            offset: int = 0,
            return_json_ready: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get comparison records with optional pagination.
        If limit is None, returns all records.

        Args:
            limit: Maximum number of records to return (None = all)
            offset: Number of records to skip
            return_json_ready: If True, returns dates as ISO format strings for JSON serialization

        Returns:
            List of comparison records
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if limit is None:
                    # Get all records
                    cursor.execute('''
                        SELECT * FROM user_comparable 
                        ORDER BY created_at DESC
                    ''')
                else:
                    # Get limited records
                    cursor.execute('''
                        SELECT * FROM user_comparable 
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                rows = cursor.fetchall()
                records = []

                for row in rows:
                    record = dict(row)

                    # Handle date fields for JSON serialization
                    for field in ['created_at', 'updated_at']:
                        if record.get(field):
                            field_value = record[field]

                            if return_json_ready:
                                # Convert datetime to ISO format string for JSON serialization
                                if isinstance(field_value, datetime):
                                    record[field] = field_value.isoformat()
                                elif isinstance(field_value, str):
                                    # Try to parse and convert to ISO format
                                    try:
                                        # Clean and parse the string
                                        cleaned = field_value.replace('Z', '').replace('+00:00', '').strip()
                                        # Try common formats
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                                            try:
                                                dt = datetime.strptime(cleaned, fmt)
                                                record[field] = dt.isoformat()
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            # If no format worked, keep original
                                            pass
                                    except Exception:
                                        pass
                            else:
                                # Keep as datetime objects
                                if isinstance(field_value, str):
                                    try:
                                        cleaned = field_value.replace('Z', '').replace('+00:00', '').strip()
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                                            try:
                                                record[field] = datetime.strptime(cleaned, fmt)
                                                break
                                            except ValueError:
                                                continue
                                    except Exception:
                                        pass

                    records.append(record)

                self._print_important(
                    f"{Icons.INFO} Retrieved {len(records)} comparison records",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_comparisons: {e}", COLORS["red"])
            return []

    def search_comparisons(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search comparisons by unique names.

        Args:
            search_text: Text to search for
            search_fields: Fields to search in. If None, searches both names.
                         Options: ['user_unique_name', 'client_unique_name']

        Returns:
            List of matching comparison records
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
                    SELECT * FROM user_comparable 
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
                    f"{Icons.SEARCH} Found {len(records)} comparisons matching '{search_text}'",
                    COLORS["blue"]
                )
                return records

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_comparisons: {e}", COLORS["red"])
            return []

    def get_comparison_count(self) -> Dict[str, int]:
        """
        Get statistics about comparison records.

        Returns:
            Dictionary with count statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute('SELECT COUNT(*) FROM user_comparable')
                total = cursor.fetchone()[0]

                # Count of unique user names
                cursor.execute('SELECT COUNT(DISTINCT user_unique_name) FROM user_comparable')
                unique_users = cursor.fetchone()[0]

                # Count of unique client names
                cursor.execute('SELECT COUNT(DISTINCT client_unique_name) FROM user_comparable')
                unique_clients = cursor.fetchone()[0]

                # Most recent comparison
                cursor.execute('SELECT MAX(created_at) FROM user_comparable')
                most_recent = cursor.fetchone()[0]

                stats = {
                    'total_comparisons': total,
                    'unique_user_names': unique_users,
                    'unique_client_names': unique_clients,
                    'most_recent': most_recent
                }

                if self.debug:
                    self._print_important(
                        f"{Icons.STATS} Comparison stats: {total} total, "
                        f"{unique_users} unique users, {unique_clients} unique clients",
                        COLORS["blue"]
                    )

                return stats

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_comparison_count: {e}", COLORS["red"])
            return {}

    def clear_all_comparisons(self) -> bool:
        """
        Clear all comparison records from the table.

        Returns:
            True if successful, False if error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM user_comparable')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM user_comparable')
                conn.commit()

                self._print_important(
                    f"{Icons.TRASH} Cleared all {count_before} comparison records",
                    COLORS["green"]
                )
                return True

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in clear_all_comparisons: {e}", COLORS["red"])
            return False

    def batch_insert_comparisons(
            self,
            comparisons: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Insert multiple comparison records in a batch.

        Args:
            comparisons: List of dictionaries with user_unique_name, client_unique_name, and jsondata

        Returns:
            List of inserted records (or None for failed ones)
        """
        results = []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for i, comp in enumerate(comparisons):
                    try:
                        # Validate required fields
                        if not all(key in comp for key in ['user_unique_name', 'client_unique_name', 'jsondata']):
                            self._print_important(
                                f"{Icons.ERROR} Comparison #{i} missing required fields",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        normalized_user = self._normalize_name(comp['user_unique_name'])
                        normalized_client = self._normalize_name(comp['client_unique_name'])

                        # Validate JSON
                        is_valid, json_result = self._validate_json(comp['jsondata'])
                        if not is_valid:
                            self._print_important(
                                f"{Icons.ERROR} Comparison #{i}: {json_result}",
                                COLORS["red"]
                            )
                            results.append(None)
                            continue

                        # Insert record
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_comparable 
                            (user_unique_name, client_unique_name, jsondata)
                            VALUES (?, ?, ?)
                        ''', (normalized_user, normalized_client, json_result))

                        record_id = cursor.lastrowid
                        results.append(self.get_comparison_by_id(record_id))

                    except Exception as e:
                        self._print_important(
                            f"{Icons.ERROR} Error processing comparison #{i}: {e}",
                            COLORS["red"]
                        )
                        results.append(None)

                conn.commit()

                success_count = sum(1 for r in results if r is not None)
                self._print_important(
                    f"{Icons.SUCCESS} Batch insert complete: {success_count}/{len(comparisons)} successful",
                    COLORS["green"]
                )

                return results

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in batch_insert_comparisons: {e}", COLORS["red"])
            return [None] * len(comparisons)