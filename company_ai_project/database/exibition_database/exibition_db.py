
from company_ai_project.saved_data import exibitor_database
from company_ai_project import saved_data
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading
import json
import re
from urllib.parse import urlparse

database = os.path.join(
    os.path.abspath(os.path.dirname(exibitor_database.__file__)),
    'exhibitors_database.db'
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


class ExhibitorDB:
    """Database management class for exhibitor data."""

    def __init__(self, db_path: str = database) -> None:
        """
        Initialize the ExhibitorDB instance.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create the exhibitors table if it doesn't exist."""
        self.create_exhibitors_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def _extract_domain(self, website: str) -> str:
        """
        Extract domain from website URL.

        Args:
            website: Website URL

        Returns:
            Domain name without www and TLD
        """
        if not website:
            return "unknown"

        try:
            # Parse the URL
            parsed = urlparse(website if '://' in website else f'https://{website}')
            domain = parsed.netloc or parsed.path

            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Get the main domain name (remove TLD)
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # Return the domain name without TLD (e.g., 'google' from 'google.com')
                main_domain = domain_parts[-2]
            else:
                main_domain = domain_parts[0]

            # Clean up the domain
            main_domain = re.sub(r'[^a-z0-9-]', '', main_domain.lower())
            return main_domain if main_domain else "unknown"

        except Exception as e:
            safe_print(f"{Icons.WARNING} Error extracting domain from {website}: {e}", COLORS["yellow"])
            return "unknown"

    def generate_unique_name(self, company_name: str, website: str) -> str:
        """
        Generate unique name from company name and website.

        Args:
            company_name: Name of the company
            website: Company website URL

        Returns:
            Unique identifier string
        """
        # Create company slug
        company_slug = company_name.lower().strip()
        company_slug = re.sub(r'[^\w\s-]', '', company_slug)  # Remove special chars
        company_slug = re.sub(r'[-\s]+', '-', company_slug)   # Replace spaces/hyphens with single hyphen
        company_slug = company_slug.strip('-')

        # Extract domain
        domain = self._extract_domain(website)

        # Generate unique name
        unique_name = f"{company_slug}-{domain}"

        # Ensure it's not too long (SQLite has no strict limit but keep reasonable)
        if len(unique_name) > 200:
            unique_name = unique_name[:200]

        return unique_name

    def create_exhibitors_table(self) -> None:
        """Create the exhibitors table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exhibitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT UNIQUE NOT NULL,
                    exhibitor_name TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    company_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    company_website TEXT NOT NULL,
                    last_processed TIMESTAMP
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exhibitors_unique_name ON exhibitors (unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exhibitors_exhibitor_name ON exhibitors (exhibitor_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exhibitors_company_name ON exhibitors (company_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exhibitors_company_website ON exhibitors (company_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exhibitors_last_processed ON exhibitors (last_processed)')

            # Create trigger to automatically update updated_at timestamp
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_exhibitors_timestamp
                AFTER UPDATE ON exhibitors
                FOR EACH ROW
                BEGIN
                    UPDATE exhibitors
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END
            ''')
            conn.commit()
            safe_print(f"{Icons.SUCCESS} Exhibitors table initialized", COLORS["green"])

    def insert_exhibitor(
            self,
            company_name: str,
            company_website: str,
            exhibitor_name: str = 'common',
            company_data: Optional[Dict[str, Any]] = None,
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new exhibitor into the database.

        Args:
            exhibitor_name: Name of the exhibitor
            company_name: Name of the company
            company_website: Company website URL
            company_data: Dictionary with additional company data (will be stored as JSON)
            replace: If True, replace existing exhibitor with same company_name

        Returns:
            Exhibitor data if successful, empty dict if failed
        """
        # Generate unique name
        unique_name = self.generate_unique_name(company_name, company_website)

        # Check if exhibitor already exists by unique_name
        existing_exhibitor = self.get_exhibitor_by_unique_name(unique_name)

        # Also check by company_name for backward compatibility
        if not existing_exhibitor:
            existing_exhibitor = self.get_exhibitor_by_name(company_name)

        # Convert company_data to JSON string if provided
        company_data_json = json.dumps(company_data) if company_data else None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If replace is True and exhibitor exists, update it
                if replace and existing_exhibitor:
                    cursor.execute('''
                        UPDATE exhibitors 
                        SET exhibitor_name = ?, company_website = ?, company_data = ?, updated_at = ?, last_processed = ?
                        WHERE unique_name = ? OR company_name = ?
                    ''', (exhibitor_name, company_website, company_data_json, datetime.now(), datetime.now(),
                          unique_name, company_name))

                    safe_print(f"{Icons.SUCCESS} Updated existing exhibitor '{company_name}' (unique: {unique_name})",
                               COLORS["green"])
                    return self.get_exhibitor_by_unique_name(unique_name) or {}

                # If replace is False and exhibitor exists, return it
                elif existing_exhibitor and not replace:
                    safe_print(
                        f"{Icons.WARNING} Exhibitor '{company_name}' (unique: {unique_name}) already exists. Use replace=True to update.",
                        COLORS["yellow"])
                    return existing_exhibitor

                # Insert new exhibitor
                else:
                    now = datetime.now()
                    cursor.execute('''
                        INSERT INTO exhibitors 
                        (unique_name, exhibitor_name, company_name, company_data, company_website, created_at, updated_at, last_processed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (unique_name, exhibitor_name, company_name, company_data_json, company_website, now, now, now))

                    safe_print \
                        (f"{Icons.SUCCESS} Added new exhibitor '{exhibitor_name}' with id {cursor.lastrowid} (unique: {unique_name})",
                               COLORS["green"])
                    return self.get_exhibitor_by_id(cursor.lastrowid) or {}

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                # Handle duplicate unique_name
                safe_print \
                    (f"{Icons.WARNING} Unique name '{unique_name}' already exists. Trying with timestamp suffix...",
                           COLORS["yellow"])

                # Try with timestamp suffix
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_name = f"{unique_name}-{timestamp}"

                try:
                    now = datetime.now()
                    cursor.execute('''
                        INSERT INTO exhibitors 
                        (unique_name, exhibitor_name, company_name, company_data, company_website, created_at, updated_at, last_processed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (unique_name, exhibitor_name, company_name, company_data_json, company_website, now, now, now))

                    safe_print(f"{Icons.SUCCESS} Added new exhibitor with modified unique name: {unique_name}",
                               COLORS["green"])
                    return self.get_exhibitor_by_unique_name(unique_name) or {}

                except sqlite3.IntegrityError:
                    safe_print(f"{Icons.ERROR} Still failed to insert exhibitor with unique name", COLORS["red"])
                    return existing_exhibitor or {}
            else:
                safe_print(f"{Icons.ERROR} Integrity error: {e}", COLORS["red"])
                return existing_exhibitor or {}
        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error inserting/updating exhibitor: {e}", COLORS["red"])
            return existing_exhibitor or {}
        except json.JSONEncodeError as e:
            safe_print(f"{Icons.ERROR} Error encoding company_data to JSON: {e}", COLORS["red"])
            return existing_exhibitor or {}

    def get_exhibitor_by_unique_name(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an exhibitor by its unique name.

        Args:
            unique_name: Unique name of the exhibitor

        Returns:
            Exhibitor data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM exhibitors WHERE unique_name = ?",
                    (unique_name,)
                )
                row = cursor.fetchone()
                return row

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving exhibitor by unique name: {e}", COLORS["red"])
            return None
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return None

    def get_exhibitor_by_id(self, exhibitor_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an exhibitor by its ID.

        Args:
            exhibitor_id: ID of the exhibitor

        Returns:
            Exhibitor data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM exhibitors WHERE id = ?",
                    (exhibitor_id,)
                )
                row = cursor.fetchone()
                return row

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving exhibitor by ID: {e}", COLORS["red"])
            return None
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return None

    def get_exhibitor_by_name(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an exhibitor by company name.

        Args:
            company_name: Name of the company

        Returns:
            Exhibitor data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM exhibitors WHERE company_name = ?",
                    (company_name,)
                )
                row = cursor.fetchone()
                return row

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving exhibitor: {e}", COLORS["red"])
            return None
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return None

    def get_exhibitor_by_exhibitor_name(self, exhibitor_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an exhibitor by exhibitor name.

        Args:
            exhibitor_name: Name of the exhibitor

        Returns:
            Exhibitor data as a dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM exhibitors WHERE exhibitor_name = ?",
                    (exhibitor_name,)
                )
                row = cursor.fetchone()
                return row

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving exhibitor by exhibitor name: {e}", COLORS["red"])
            return None
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return None

    def update_exhibitor(
            self,
            exhibitor_id: int,
            **kwargs: Any
    ) -> bool:
        """
        Update exhibitor information.

        Args:
            exhibitor_id: ID of the exhibitor
            **kwargs: Fields to update (unique_name, exhibitor_name, company_name, company_website, company_data)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            safe_print(f"{Icons.WARNING} No fields provided for update", COLORS["yellow"])
            return False

        # Don't allow updating created_at or id
        forbidden_fields = ['id', 'created_at']
        for field in forbidden_fields:
            kwargs.pop(field, None)

        # If company_name or company_website is updated, regenerate unique_name
        if 'company_name' in kwargs or 'company_website' in kwargs:
            # Get current values
            current = self.get_exhibitor_by_id(exhibitor_id)
            if current:
                new_company_name = kwargs.get('company_name', current['company_name'])
                new_company_website = kwargs.get('company_website', current['company_website'])
                kwargs['unique_name'] = self.generate_unique_name(new_company_name, new_company_website)

        # Convert company_data to JSON if present
        if 'company_data' in kwargs and kwargs['company_data'] is not None:
            try:
                kwargs['company_data'] = json.dumps(kwargs['company_data'])
            except json.JSONEncodeError as e:
                safe_print(f"{Icons.ERROR} Error encoding company_data to JSON: {e}", COLORS["red"])
                return False

        # Add last_processed timestamp
        kwargs['last_processed'] = datetime.now()

        try:
            # Build the SET part of the query
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(exhibitor_id)  # For the WHERE clause

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE exhibitors SET {set_clause} WHERE id = ?",
                    values
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Updated exhibitor with ID {exhibitor_id}", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Exhibitor with ID {exhibitor_id} not found for update",
                               COLORS["yellow"])

                return success

        except sqlite3.IntegrityError as e:
            safe_print(f"{Icons.ERROR} Integrity error updating exhibitor: {e}", COLORS["red"])
            return False
        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error updating exhibitor: {e}", COLORS["red"])
            return False

    def update_last_processed(self, exhibitor_id: int) -> bool:
        """
        Update the last_processed timestamp for an exhibitor.

        Args:
            exhibitor_id: ID of the exhibitor

        Returns:
            True if successful, False otherwise
        """
        return self.update_exhibitor(exhibitor_id, last_processed=datetime.now())

    def update_company_data(self, exhibitor_id: int, company_data: Dict[str, Any]) -> bool:
        """
        Update the company_data JSON field for an exhibitor.

        Args:
            exhibitor_id: ID of the exhibitor
            company_data: Dictionary with company data to store as JSON

        Returns:
            True if successful, False otherwise
        """
        return self.update_exhibitor(exhibitor_id, company_data=company_data)

    def get_all_exhibitors(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            order_by: str = "company_name"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all exhibitors from the database.

        Args:
            limit: Maximum number of exhibitors to retrieve (optional)
            offset: Number of exhibitors to skip (optional)
            order_by: Field to order by (default: company_name)

        Returns:
            List of exhibitor dictionaries or empty list if none found
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                query = f"SELECT * FROM exhibitors ORDER BY {order_by}"
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
                    return rows

                safe_print(f"{Icons.INFO} No exhibitors found", COLORS["cyan"])
                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving exhibitors: {e}", COLORS["red"])
            return []
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return []

    def get_unprocessed_exhibitors(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get exhibitors that haven't been processed recently.

        Args:
            limit: Maximum number to retrieve (optional)

        Returns:
            List of unprocessed exhibitors
        """
        try:
            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                query = """
                    SELECT * FROM exhibitors 
                    WHERE last_processed IS NULL 
                    ORDER BY created_at
                """
                params = []

                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                if rows:
                    return rows

                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error retrieving unprocessed exhibitors: {e}", COLORS["red"])
            return []
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return []

    def search_exhibitors(
            self,
            search_term: str,
            search_fields: List[str] = ['unique_name', 'exhibitor_name', 'company_name', 'company_website'],
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search exhibitors and return results.

        Args:
            search_term: Text to search for
            search_fields: List of fields to search in
            limit: Maximum number of results to return (optional)

        Returns:
            List of matching exhibitors
        """
        try:
            if not search_fields:
                search_fields = ['unique_name', 'exhibitor_name', 'company_name', 'company_website']

            search_conditions = " OR ".join([f"{field} LIKE ?" for field in search_fields])
            search_params = [f"%{search_term}%"] * len(search_fields)

            with self._get_connection() as conn:
                # Register adapter to convert TEXT to dict when reading JSON
                def dict_factory(cursor, row):
                    d = {}
                    for idx, col in enumerate(cursor.description):
                        if col[0] == 'company_data' and row[idx]:
                            d[col[0]] = json.loads(row[idx])
                        else:
                            d[col[0]] = row[idx]
                    return d

                conn.row_factory = dict_factory
                cursor = conn.cursor()
                query = f"SELECT * FROM exhibitors WHERE {search_conditions} ORDER BY exhibitor_name"

                if limit:
                    query += " LIMIT ?"
                    search_params.append(limit)

                cursor.execute(query, search_params)
                rows = cursor.fetchall()

                if rows:
                    safe_print(f"{Icons.INFO} Found {len(rows)} exhibitors matching '{search_term}'",
                               COLORS["cyan"])
                    return rows

                safe_print(f"{Icons.INFO} No exhibitors found matching '{search_term}'", COLORS["cyan"])
                return []

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error searching exhibitors: {e}", COLORS["red"])
            return []
        except json.JSONDecodeError as e:
            safe_print(f"{Icons.ERROR} Error decoding company_data from JSON: {e}", COLORS["red"])
            return []

    def delete_exhibitor(self, exhibitor_id: int) -> bool:
        """
        Delete an exhibitor by ID.

        Args:
            exhibitor_id: ID of the exhibitor

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM exhibitors WHERE id = ?",
                    (exhibitor_id,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted exhibitor with ID {exhibitor_id}", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Exhibitor with ID {exhibitor_id} not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting exhibitor: {e}", COLORS["red"])
            return False

    def delete_exhibitor_by_name(self, company_name: str) -> bool:
        """
        Delete an exhibitor by company name.

        Args:
            company_name: Name of the company

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM exhibitors WHERE company_name = ?",
                    (company_name,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted exhibitor '{company_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Exhibitor '{company_name}' not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting exhibitor: {e}", COLORS["red"])
            return False

    def delete_exhibitor_by_unique_name(self, unique_name: str) -> bool:
        """
        Delete an exhibitor by unique name.

        Args:
            unique_name: Unique name of the exhibitor

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM exhibitors WHERE unique_name = ?",
                    (unique_name,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted exhibitor '{unique_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Exhibitor '{unique_name}' not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting exhibitor: {e}", COLORS["red"])
            return False

    def delete_exhibitor_by_exhibitor_name(self, exhibitor_name: str) -> bool:
        """
        Delete an exhibitor by exhibitor name.

        Args:
            exhibitor_name: Name of the exhibitor

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM exhibitors WHERE exhibitor_name = ?",
                    (exhibitor_name,)
                )

                success = cursor.rowcount > 0
                if success:
                    safe_print(f"{Icons.SUCCESS} Deleted exhibitor '{exhibitor_name}'", COLORS["green"])
                else:
                    safe_print(f"{Icons.WARNING} Exhibitor '{exhibitor_name}' not found for deletion",
                               COLORS["yellow"])

                return success

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error deleting exhibitor: {e}", COLORS["red"])
            return False

    def exhibitor_exists(self, company_name: str) -> bool:
        """
        Check if an exhibitor exists by company name.

        Args:
            company_name: Name of the company

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM exhibitors WHERE company_name = ?",
                    (company_name,)
                )
                exists = cursor.fetchone() is not None
                return exists

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error checking exhibitor existence: {e}", COLORS["red"])
            return False

    def exhibitor_exists_by_unique_name(self, unique_name: str) -> bool:
        """
        Check if an exhibitor exists by unique name.

        Args:
            unique_name: Unique name of the exhibitor

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM exhibitors WHERE unique_name = ?",
                    (unique_name,)
                )
                exists = cursor.fetchone() is not None
                return exists

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error checking exhibitor existence: {e}", COLORS["red"])
            return False

    def exhibitor_exists_by_exhibitor_name(self, exhibitor_name: str) -> bool:
        """
        Check if an exhibitor exists by exhibitor name.

        Args:
            exhibitor_name: Name of the exhibitor

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM exhibitors WHERE exhibitor_name = ?",
                    (exhibitor_name,)
                )
                exists = cursor.fetchone() is not None
                return exists

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error checking exhibitor existence: {e}", COLORS["red"])
            return False

    def get_exhibitor_count(self) -> int:
        """
        Get the total number of exhibitors in the database.

        Returns:
            Number of exhibitors
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM exhibitors")
                count = cursor.fetchone()[0]
                return count

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error getting exhibitor count: {e}", COLORS["red"])
            return 0

    def clear_all_exhibitors(self) -> bool:
        """
        Delete all exhibitors from the database.

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM exhibitors")
                # Reset auto-increment counter
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='exhibitors'")

                safe_print(f"{Icons.SUCCESS} Cleared all exhibitors", COLORS["green"])
                return True

        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Error clearing exhibitors: {e}", COLORS["red"])
            return False

















