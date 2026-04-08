from company_ai_project import saved_data
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading

# Database path - using the same database_old as your CompanyDB
database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'certification_database.db'
)

# Thread lock for safe printing
print_lock = threading.Lock()


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
    ROBOT = '🤖'


class CertificationDB:
    """Database management class for certification-related data with single table."""

    def __init__(self, db_path: str = database) -> None:
        """
        Initialize the CertificationDB instance.

        Args:
            db_path: Path to the SQLite database_old file
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create the certifications table if it doesn't exist."""
        self.create_certifications_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        return sqlite3.connect(self.db_path)

    def create_certifications_table(self) -> None:
        """Create the certifications table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT UNIQUE NOT NULL,
                    certification_name TEXT NOT NULL,
                    certification_data TEXT,  -- Store as string (not JSON)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for better performance
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_certifications_unique_name ON certifications (unique_name)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_certifications_name ON certifications (certification_name)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_certifications_updated ON certifications (updated_at)')

            # Create trigger to automatically update updated_at timestamp
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_certifications_timestamp
                AFTER UPDATE ON certifications
                FOR EACH ROW
                BEGIN
                    UPDATE certifications
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END
            ''')
            conn.commit()

    def generate_unique_name(self, certification_name: str) -> str:
        """
        Generate a human-readable unique name for certification.

        Args:
            certification_name: Name of the certification

        Returns:
            Generated unique name
        """
        # Clean the certification name
        unique_name = certification_name.lower().replace(' ', '_').replace('.', '').replace('-', '_')

        # Remove any consecutive underscores and trim
        unique_name = '_'.join(filter(None, unique_name.split('_')))
        return unique_name

    def insert_certification(
            self,
            certification_name: str,
            certification_data: Optional[str] = None,  # Changed to string
            unique_name: str = "",
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new certification into the database.

        Args:
            certification_name: Name of the certification
            certification_data: Certification data as a string
            unique_name: Unique identifier for the certification (optional, will be generated if not provided)
            replace: If True, replace existing certification with same unique_name (default: False)

        Returns:
            Certification data if successful, empty dict if failed
        """
        if not unique_name:
            unique_name = self.generate_unique_name(certification_name)

        # Check if certification with same unique_name already exists
        existing_certification = self.get_certification(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If replace is True and certification exists, update it
                if replace and existing_certification:
                    cursor.execute('''
                        UPDATE certifications 
                        SET certification_name = ?, certification_data = ?, updated_at = ?
                        WHERE unique_name = ?
                    ''', (certification_name, certification_data, datetime.now(), unique_name))

                    safe_print(f"{Icons.SUCCESS} Updated existing certification '{unique_name}'", COLORS["green"])
                    return self.get_certification(unique_name) or {}

                # If replace is False and certification exists, return it
                elif existing_certification and not replace:
                    safe_print(
                        f"{Icons.WARNING} Certification '{unique_name}' already exists. Use replace=True to update.",
                        COLORS["yellow"])
                    return existing_certification

                # Insert new certification (id auto-increments)
                else:
                    now = datetime.now()

                    cursor.execute('''
                        INSERT INTO certifications 
                        (unique_name, certification_name, certification_data, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (unique_name, certification_name, certification_data, now, now))

                    safe_print(f"{Icons.SUCCESS} Added new certification '{unique_name}' with id {cursor.lastrowid}", COLORS["green"])
                    return self.get_certification(unique_name) or {}

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error inserting/updating certification: {e}", COLORS["red"])
            return existing_certification or {}

    def get_certification(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a certification by its unique name.

        Args:
            unique_name: Unique identifier for the certification

        Returns:
            Certification data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM certifications WHERE unique_name = ?",
                    (unique_name,)
                )
                row = cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    result = dict(zip(columns, row))
                    # certification_data is already a string, no JSON parsing needed
                    return result
                return None
        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving certification: {e}", COLORS["red"])
            return None

    def get_certification_by_id(self, cert_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a certification by its ID.

        Args:
            cert_id: ID of the certification

        Returns:
            Certification data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM certifications WHERE id = ?",
                    (cert_id,)
                )
                row = cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    result = dict(zip(columns, row))
                    return result
                return None
        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving certification by ID: {e}", COLORS["red"])
            return None

    def update_certification(
            self,
            unique_name: str,
            **kwargs: Any
    ) -> bool:
        """
        Update certification information.

        Args:
            unique_name: Unique identifier for the certification
            **kwargs: Fields to update and their new values
                     (can include: certification_name, certification_data)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            safe_print(f"{Icons.WARNING} No fields provided for update", COLORS["yellow"])
            return False

        try:
            # Build the SET part of the query
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(unique_name)  # For the WHERE clause

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE certifications SET {set_clause} WHERE unique_name = ?",
                    values
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Updated certification '{unique_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Certification '{unique_name}' not found for update", COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error updating certification: {e}", COLORS["red"])
            return False

    def update_certification_by_id(
            self,
            cert_id: int,
            **kwargs: Any
    ) -> bool:
        """
        Update certification information by ID.

        Args:
            cert_id: ID of the certification
            **kwargs: Fields to update and their new values
                     (can include: certification_name, certification_data, unique_name)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            safe_print(f"{Icons.WARNING} No fields provided for update", COLORS["yellow"])
            return False

        try:
            # Build the SET part of the query
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(cert_id)  # For the WHERE clause

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE certifications SET {set_clause} WHERE id = ?",
                    values
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Updated certification with ID {cert_id}", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Certification with ID {cert_id} not found for update", COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error updating certification by ID: {e}", COLORS["red"])
            return False

    def get_all_certifications(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all certifications from the database.

        Args:
            limit: Maximum number of certifications to retrieve (optional)
            offset: Number of certifications to skip (optional)

        Returns:
            List of certification dictionaries or empty list if none found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM certifications ORDER BY id"
                params = []

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                if rows:
                    columns = [description[0] for description in cursor.description]
                    result = []
                    for row in rows:
                        cert_dict = dict(zip(columns, row))
                        result.append(cert_dict)
                    return result

                safe_print(f"{Icons.INFO} No certifications found", COLORS["cyan"])
                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving all certifications: {e}", COLORS["red"])
            return []

    def search_certifications(
            self,
            search_term: str,
            search_fields: List[str] = ['certification_name', 'unique_name'],
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search certifications and return results.

        Args:
            search_term: Text to search for
            search_fields: List of fields to search in
            limit: Maximum number of results to return (optional)

        Returns:
            List of matching certifications
        """
        try:
            if not search_fields:
                search_fields = ['certification_name', 'unique_name']

            search_conditions = " OR ".join([f"{field} LIKE ?" for field in search_fields])
            search_params = [f"%{search_term}%"] * len(search_fields)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM certifications WHERE {search_conditions} ORDER BY id"

                if limit:
                    query += " LIMIT ?"
                    search_params.append(limit)

                cursor.execute(query, search_params)
                rows = cursor.fetchall()

                if rows:
                    columns = [description[0] for description in cursor.description]
                    result = []
                    for row in rows:
                        cert_dict = dict(zip(columns, row))
                        result.append(cert_dict)

                    safe_print(f"{Icons.INFO} Found {len(result)} certifications matching '{search_term}'",
                               COLORS["cyan"])
                    return result

                safe_print(f"{Icons.INFO} No certifications found matching '{search_term}'", COLORS["cyan"])
                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error searching certifications: {e}", COLORS["red"])
            return []

    def update_certification_data(
            self,
            unique_name: str,
            certification_data: str,  # Changed to string
            merge: bool = False  # merge doesn't make sense for strings, but kept for compatibility
    ) -> bool:
        """
        Update only the certification data.

        Args:
            unique_name: Unique identifier for the certification
            certification_data: New certification data as a string
            merge: Not used for strings, kept for compatibility

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in database
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE certifications 
                    SET certification_data = ?
                    WHERE unique_name = ?
                ''', (certification_data, unique_name))

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Updated certification data for '{unique_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.ERROR} Failed to update certification data for '{unique_name}'", COLORS["red"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error updating certification data: {e}", COLORS["red"])
            return False

    def delete_certification(self, unique_name: str) -> bool:
        """
        Delete a certification.

        Args:
            unique_name: Unique identifier for the certification

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM certifications WHERE unique_name = ?",
                    (unique_name,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted certification '{unique_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Certification '{unique_name}' not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting certification: {e}", COLORS["red"])
            return False

    def delete_certification_by_id(self, cert_id: int) -> bool:
        """
        Delete a certification by ID.

        Args:
            cert_id: ID of the certification

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM certifications WHERE id = ?",
                    (cert_id,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted certification with ID {cert_id}", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Certification with ID {cert_id} not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting certification by ID: {e}", COLORS["red"])
            return False

    def certification_exists(self, unique_name: str) -> bool:
        """
        Check if a certification exists.

        Args:
            unique_name: Unique identifier for the certification

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM certifications WHERE unique_name = ?",
                    (unique_name,)
                )
                exists = cursor.fetchone() is not None
                return exists

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error checking certification existence: {e}", COLORS["red"])
            return False

    def get_certification_count(self) -> int:
        """
        Get the total number of certifications in the database.

        Returns:
            Number of certifications
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM certifications")
                count = cursor.fetchone()[0]
                return count

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error getting certification count: {e}", COLORS["red"])
            return 0

    def clear_all_certifications(self) -> bool:
        """
        Delete all certifications from the database.

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM certifications")
                # Reset auto-increment counter
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='certifications'")

                safe_print(f"{Icons.SUCCESS} Cleared all certifications", COLORS["green"])
                return True

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error clearing certifications: {e}", COLORS["red"])
            return False

    def get_recent_certifications(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get certifications updated in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent certifications
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM certifications 
                    WHERE updated_at >= datetime('now', ?) 
                    ORDER BY updated_at DESC
                ''', (f'-{days} days',))

                rows = cursor.fetchall()
                if rows:
                    columns = [description[0] for description in cursor.description]
                    result = []
                    for row in rows:
                        cert_dict = dict(zip(columns, row))
                        result.append(cert_dict)
                    return result

                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error getting recent certifications: {e}", COLORS["red"])
            return []