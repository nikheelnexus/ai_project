import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import hashlib
import re
from threading import Lock
import os
from company_ai_project.saved_data import user_data

database = os.path.join(
    os.path.abspath(os.path.dirname(user_data.__file__)),
    'user.db'
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
    USER = '👤'
    EMAIL = '📧'
    WEBSITE = '🌐'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '🔄'
    VALIDATION = '🔍'
    PASSWORD = '🔒'
    LOGIN = '🔑'


class UserDB:
    """Handles operations for the users table with comprehensive user management."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_user_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database_old connection."""
        return sqlite3.connect(self.db_path)

    def create_user_table(self) -> None:
        """Create the users table if it doesn't exist with all required columns and indexes."""
        try:

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # First, create the table with all columns
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        full_name TEXT,
                        website TEXT,
                        password_hash TEXT,
                        is_active INTEGER DEFAULT 1,
                        is_admin INTEGER DEFAULT 0,
                        last_login TIMESTAMP DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Check existing columns and add missing ones
                self._add_missing_columns(cursor)

                # Create indexes
                self._create_indexes(cursor)

                conn.commit()

        except Exception as e:
            safe_print(f"{Icons.ERROR} Error creating user table: {e}", COLORS["red"])
            raise

    def _add_missing_columns(self, cursor) -> None:
        """Add missing columns to the users table."""
        try:
            # Get current table schema
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [col[1] for col in cursor.fetchall()]

            # Define all required columns with their types and defaults
            required_columns = {
                'password_hash': 'TEXT',
                'is_active': 'INTEGER DEFAULT 1',
                'is_admin': 'INTEGER DEFAULT 0',
                'last_login': 'TIMESTAMP DEFAULT NULL',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }

            # Add missing columns
            for column, column_def in required_columns.items():
                if column not in existing_columns:
                    try:
                        cursor.execute(f'ALTER TABLE users ADD COLUMN {column} {column_def}')
                    except Exception as e:
                        safe_print(f"{Icons.WARNING} Could not add column {column}: {e}", COLORS["yellow"])

        except Exception as e:
            safe_print(f"{Icons.ERROR} Error adding missing columns: {e}", COLORS["red"])

    def _create_indexes(self, cursor) -> None:
        """Create necessary indexes on the users table."""
        try:
            # Create basic indexes
            indexes = [
                ('idx_users_username', 'username'),
                ('idx_users_email', 'email'),
                ('idx_users_is_active', 'is_active'),
                ('idx_users_is_admin', 'is_admin')
            ]

            for idx_name, column in indexes:
                try:
                    cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON users({column})')
                except Exception as e:
                    if "no such column" in str(e):
                        safe_print(f"{Icons.WARNING} Cannot create index {idx_name}: column {column} doesn't exist",
                                   COLORS["yellow"])
                    else:
                        safe_print(f"{Icons.ERROR} Error creating index {idx_name}: {e}", COLORS["red"])

        except Exception as e:
            safe_print(f"{Icons.ERROR} Error creating indexes: {e}", COLORS["red"])

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_username(self, username: str) -> tuple[bool, str]:
        """Validate username format and rules."""
        if not username:
            return False, "Username cannot be empty"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 50:
            return False, "Username cannot exceed 50 characters"

        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            return False, "Username can only contain letters, numbers, underscores, dots, and hyphens"

        return True, ""

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = uuid.uuid4().hex
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

    def _check_password(self, hashed_password: str, user_password: str) -> bool:
        """Verify password against hash."""
        password_hash, salt = hashed_password.split(':')
        return password_hash == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

    def _validate_website(self, website: str) -> str:
        """Validate and format website URL."""
        if not website:
            return ""

        website = website.strip()
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        # Basic URL validation
        pattern = r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        if re.match(pattern, website):
            return website
        return ""

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email only.

        Args:
            email: User's email address

        Returns:
            User dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                # Set row_factory to sqlite3.Row to get dictionary-like rows
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Only search by email
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                row = cursor.fetchone()

                if row:
                    # Now row is a sqlite3.Row object which can be converted to dict
                    user_dict = dict(row)
                    # Convert timestamp strings to datetime objects
                    for field in ['last_login', 'created_at', 'updated_at']:
                        if user_dict.get(field) and isinstance(user_dict[field], str):
                            try:
                                user_dict[field] = datetime.fromisoformat(user_dict[field])
                            except ValueError:
                                pass
                    self._print_important(f"{Icons.USER} Found user: {user_dict.get('email', 'Unknown')}",
                                          COLORS["green"])
                    return user_dict

                if self.debug:
                    self._print_important(f"{Icons.WARNING} User not found: {email}", COLORS["yellow"])
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user: {e}", COLORS["red"])
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()

                if row:
                    user_dict = dict(row)
                    # Convert timestamps
                    for field in ['last_login', 'created_at', 'updated_at']:
                        if user_dict[field] and isinstance(user_dict[field], str):
                            try:
                                user_dict[field] = datetime.fromisoformat(user_dict[field])
                            except ValueError:
                                pass
                    return user_dict
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_by_id: {e}", COLORS["red"])
            return None

    def insert_user(
            self,
            email: str,
            password: str,
            first_name: str,
            last_name: str,
            website: Optional[str] = None,
            is_admin: bool = False,
            replace: bool = False
    ) -> dict:
        """
        Insert a new user into the database_old.
        Username is auto-generated from first and last name.
        """
        # Validate email
        if not self._validate_email(email):
            safe_print(f"{Icons.ERROR} Invalid email format: {email}", COLORS["red"])
            return {}

        # Validate password
        if not password or len(password) < 6:
            safe_print(f"{Icons.ERROR} Password must be at least 6 characters", COLORS["red"])
            return {}

        # Validate names
        if not first_name or not first_name.strip():
            safe_print(f"{Icons.ERROR} First name is required", COLORS["red"])
            return {}

        if not last_name or not last_name.strip():
            safe_print(f"{Icons.ERROR} Last name is required", COLORS["red"])
            return {}

        # Generate username from first and last name
        username = self._generate_username(first_name, last_name)

        # Check if username already exists, if so, add numbers
        original_username = username
        counter = 1
        while self._username_exists(username):
            username = f"{original_username}{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                username = f"{original_username}{int(datetime.now().timestamp())}"
                break

        # Create full name
        full_name = f"{first_name} {last_name}".strip()

        # Validate and format website
        formatted_website = self._validate_website(website) if website else ""

        # Check if user already exists by email
        existing_user = self.get_user(email)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # First, ensure the table has all required columns
                self._ensure_table_columns(cursor)

                # If replace is True and user exists, update it
                if replace and existing_user:
                    # Hash password
                    password_hash = self._hash_password(password)

                    # Try to update with password_hash column first
                    try:
                        cursor.execute('''
                            UPDATE users 
                            SET username = ?, full_name = ?, website = ?, password_hash = ?,
                                is_admin = ?, updated_at = ?
                            WHERE email = ?
                        ''', (
                            username,
                            full_name,
                            formatted_website,
                            password_hash,
                            1 if is_admin else 0,
                            datetime.now(),
                            email
                        ))
                    except sqlite3.OperationalError as e:
                        if "no such column" in str(e):
                            # Fallback: update without password_hash
                            safe_print(f"{Icons.WARNING} password_hash column missing, updating without it",
                                       COLORS["yellow"])
                            cursor.execute('''
                                UPDATE users 
                                SET username = ?, full_name = ?, website = ?,
                                    is_admin = ?, updated_at = ?
                                WHERE email = ?
                            ''', (
                                username,
                                full_name,
                                formatted_website,
                                1 if is_admin else 0,
                                datetime.now(),
                                email
                            ))
                        else:
                            raise

                    conn.commit()
                    return self.get_user(email)

                # If user exists and not replacing
                elif existing_user and not replace:
                    safe_print(f"{Icons.WARNING} User already exists: {email}", COLORS["yellow"])
                    return existing_user

                # Insert new user
                else:
                    # Hash password
                    password_hash = self._hash_password(password)
                    user_id = str(uuid.uuid4())
                    now = datetime.now()

                    # Try to insert with all columns
                    try:
                        cursor.execute('''
                            INSERT INTO users 
                            (id, username, email, full_name, website, password_hash, 
                             is_admin, created_at, updated_at, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            user_id,
                            username,
                            email,
                            full_name,
                            formatted_website,
                            password_hash,
                            1 if is_admin else 0,
                            now,
                            now,
                            1
                        ))
                    except sqlite3.OperationalError as e:
                        if "no such column" in str(e):
                            # Fallback: insert without password_hash
                            safe_print(f"{Icons.WARNING} password_hash column missing, inserting without it",
                                       COLORS["yellow"])
                            cursor.execute('''
                                INSERT INTO users 
                                (id, username, email, full_name, website, 
                                 is_admin, created_at, updated_at, is_active)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                user_id,
                                username,
                                email,
                                full_name,
                                formatted_website,
                                1 if is_admin else 0,
                                now,
                                now,
                                1
                            ))
                        else:
                            raise

                    conn.commit()
                    return self.get_user(email)

        except sqlite3.IntegrityError as e:
            safe_print(f"{Icons.ERROR} User already exists (email not unique): {e}", COLORS["red"])
            return existing_user or {}
        except sqlite3.Error as e:
            safe_print(f"{Icons.ERROR} Database error in insert_user: {e}", COLORS["red"])
            return {}

    def _ensure_table_columns(self, cursor) -> None:
        """Ensure all required columns exist in the users table."""
        try:
            # Check if password_hash column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'password_hash' not in columns:
                safe_print(f"{Icons.WARNING} Adding password_hash column to users table", COLORS["yellow"])
                cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')

            # Check and add other essential columns if missing
            essential_columns = {
                'is_active': 'INTEGER DEFAULT 1',
                'is_admin': 'INTEGER DEFAULT 0',
                'last_login': 'TIMESTAMP DEFAULT NULL',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }

            for column, column_def in essential_columns.items():
                if column not in columns:
                    safe_print(f"{Icons.WARNING} Adding {column} column to users table", COLORS["yellow"])
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column} {column_def}')

        except Exception as e:
            safe_print(f"{Icons.ERROR} Error ensuring table columns: {e}", COLORS["red"])

    def _generate_username(self, first_name: str, last_name: str) -> str:
        """
        Generate a username from first and last name.

        Args:
            first_name: User's first name
            last_name: User's last name

        Returns:
            Generated username
        """
        # Clean names: remove special characters, convert to lowercase
        first_clean = re.sub(r'[^a-zA-Z0-9]', '', first_name).lower()
        last_clean = re.sub(r'[^a-zA-Z0-9]', '', last_name).lower()

        # If names are too short, use full names
        if len(first_clean) < 2:
            first_clean = first_name.lower().replace(' ', '')
        if len(last_clean) < 2:
            last_clean = last_name.lower().replace(' ', '')

        # Generate possible username combinations
        username_options = [
            f"{first_clean}.{last_clean}",  # john.doe
            f"{first_clean}{last_clean}",  # johndoe
            f"{first_clean[0]}{last_clean}",  # jdoe
            f"{first_clean}{last_clean[0]}",  # johnd
        ]

        # Try each option until we find one that doesn't exist
        for username in username_options:
            if not self._username_exists(username):
                return username

        # If all options exist, add timestamp
        return f"{first_clean}{last_clean}{int(datetime.now().timestamp() % 10000)}"

    def _username_exists(self, username: str) -> bool:
        """
        Check if a username already exists in the database_old.

        Args:
            username: Username to check

        Returns:
            True if username exists
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def update_user(
            self,
            identifier: str,
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update user fields.

        Args:
            identifier: Username or email of user to update
            **kwargs: Fields to update (username, email, full_name, website, is_active, is_admin)

        Returns:
            Updated user data or None if failed
        """
        # Get existing user
        existing_user = self.get_user(identifier)
        if not existing_user:
            self._print_important(f"{Icons.ERROR} User not found: {identifier}", COLORS["red"])
            return None

        # Prepare update fields
        update_fields = []
        update_values = []

        # Handle each possible field update
        if 'username' in kwargs and kwargs['username'] != existing_user['username']:
            is_valid, error_msg = self._validate_username(kwargs['username'])
            if not is_valid:
                self._print_important(f"{Icons.ERROR} Invalid username: {error_msg}", COLORS["red"])
                return None
            update_fields.append('username = ?')
            update_values.append(kwargs['username'])

        if 'email' in kwargs and kwargs['email'] != existing_user['email']:
            if not self._validate_email(kwargs['email']):
                self._print_important(f"{Icons.ERROR} Invalid email format: {kwargs['email']}", COLORS["red"])
                return None
            update_fields.append('email = ?')
            update_values.append(kwargs['email'])

        if 'full_name' in kwargs:
            update_fields.append('full_name = ?')
            update_values.append(kwargs['full_name'] or None)

        if 'website' in kwargs:
            formatted_website = self._validate_website(kwargs['website']) if kwargs['website'] else ""
            update_fields.append('website = ?')
            update_values.append(formatted_website)

        if 'is_active' in kwargs:
            update_fields.append('is_active = ?')
            update_values.append(1 if kwargs['is_active'] else 0)

        if 'is_admin' in kwargs:
            update_fields.append('is_admin = ?')
            update_values.append(1 if kwargs['is_admin'] else 0)

        if 'password' in kwargs and kwargs['password']:
            if len(kwargs['password']) < 6:
                self._print_important(f"{Icons.ERROR} Password must be at least 6 characters", COLORS["red"])
                return None
            password_hash = self._hash_password(kwargs['password'])
            update_fields.append('password_hash = ?')
            update_values.append(password_hash)

        # If nothing to update
        if not update_fields:
            self._print_important(f"{Icons.WARNING} No fields to update for user: {identifier}", COLORS["yellow"])
            return existing_user

        # Add updated_at and identifier
        update_fields.append('updated_at = ?')
        update_values.append(datetime.now())
        update_values.append(existing_user['id'])

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = f'''
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                '''

                cursor.execute(query, update_values)
                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(f"{Icons.UPDATE} Updated user: {identifier}", COLORS["green"])
                    return self.get_user_by_id(existing_user['id'])
                else:
                    self._print_important(f"{Icons.WARNING} No changes made to user: {identifier}", COLORS["yellow"])
                    return existing_user

        except sqlite3.IntegrityError as e:
            self._print_important(f"{Icons.ERROR} Update failed (username or email not unique): {e}", COLORS["red"])
            return None
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in update_user: {e}", COLORS["red"])
            return None

    def delete_user(self, identifier: str) -> bool:
        """
        Delete user by username, email, or ID.

        Args:
            identifier: Username, email, or ID of user to delete

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Try to delete by username, email, or ID
                cursor.execute('''
                    DELETE FROM users 
                    WHERE username = ? OR email = ? OR id = ?
                ''', (identifier, identifier, identifier))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(f"{Icons.TRASH} Deleted user: {identifier}", COLORS["green"])
                    return True
                else:
                    self._print_important(f"{Icons.WARNING} User not found: {identifier}", COLORS["yellow"])
                    return False

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            User data if authenticated, None if failed
        """
        # Try to find user by email
        user = self.get_user(email)
        if not user:
            self._print_important(f"{Icons.ERROR} Authentication failed: User not found", COLORS["red"])
            return None

        if not user.get('is_active'):
            self._print_important(f"{Icons.ERROR} Authentication failed: User is inactive", COLORS["red"])
            return None

        # Check password
        if not self._check_password(user['password_hash'], password):
            self._print_important(f"{Icons.ERROR} Authentication failed: Invalid password", COLORS["red"])
            return None

        # Update last login time
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET last_login = ? WHERE id = ?',
                    (datetime.now(), user['id'])
                )
                conn.commit()
        except sqlite3.Error:
            pass  # Non-critical error

        self._print_important(f"{Icons.LOGIN} User authenticated: {user['email']}", COLORS["green"])
        return user

    def get_all_users(
            self,
            active_only: bool = True,
            include_admins: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all users with optional filters.

        Args:
            active_only: If True, only return active users
            include_admins: If False, exclude admin users

        Returns:
            List of user dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = 'SELECT * FROM users WHERE 1=1'
                params = []

                if active_only:
                    query += ' AND is_active = 1'

                if not include_admins:
                    query += ' AND is_admin = 0'

                query += ' ORDER BY username'

                cursor.execute(query, params)
                rows = cursor.fetchall()

                users = []
                for row in rows:
                    user_dict = dict(row)
                    # Convert timestamps
                    for field in ['last_login', 'created_at', 'updated_at']:
                        if user_dict[field] and isinstance(user_dict[field], str):
                            try:
                                user_dict[field] = datetime.fromisoformat(user_dict[field])
                            except ValueError:
                                pass
                    users.append(user_dict)

                #self._print_important(f"{Icons.USER} Retrieved {len(users)} users", COLORS["blue"])
                return users

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_all_users: {e}", COLORS["red"])
            return []

    def search_users(
            self,
            search_text: str,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search users based on text across multiple fields.

        Args:
            search_text: Text to search for
            search_fields: List of fields to search in. If None, searches all fields.
                         Options: ['username', 'email', 'full_name', 'website']

        Returns:
            List of matching user dictionaries
        """
        if not search_text:
            self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Default fields to search
        if search_fields is None:
            search_fields = ['username', 'email', 'full_name']

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build WHERE clause
                where_conditions = []
                params = []

                for field in search_fields:
                    if field in ['username', 'email', 'full_name', 'website']:
                        where_conditions.append(f"{field} LIKE ?")
                        params.append(f'%{search_text}%')

                if not where_conditions:
                    return []

                where_clause = " OR ".join(where_conditions)
                query = f'''
                    SELECT * FROM users 
                    WHERE ({where_clause}) 
                    ORDER BY username
                '''

                cursor.execute(query, params)
                rows = cursor.fetchall()

                users = []
                for row in rows:
                    user_dict = dict(row)
                    # Convert timestamps
                    for field in ['last_login', 'created_at', 'updated_at']:
                        if user_dict[field] and isinstance(user_dict[field], str):
                            try:
                                user_dict[field] = datetime.fromisoformat(user_dict[field])
                            except ValueError:
                                pass
                    users.append(user_dict)

                #self._print_important(f"{Icons.SEARCH} Found {len(users)} users matching '{search_text}'",
                #                      COLORS["blue"])
                return users

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in search_users: {e}", COLORS["red"])
            return []

    def get_user_count(self, active_only: bool = False) -> int:
        """
        Get total number of users.

        Args:
            active_only: If True, only count active users

        Returns:
            Number of users
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if active_only:
                    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
                else:
                    cursor.execute('SELECT COUNT(*) FROM users')

                count = cursor.fetchone()[0]

                if self.debug:
                    status = "active " if active_only else ""
                    self._print_important(f"{Icons.INFO} Total {status}users: {count}", COLORS["blue"])

                return count

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_count: {e}", COLORS["red"])
            return 0

    def change_password(self, identifier: str, old_password: str, new_password: str) -> bool:
        """
        Change user password with old password verification.

        Args:
            identifier: Username or email
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully
        """
        # Verify old password first
        user = self.authenticate_user(identifier, old_password)
        if not user:
            return False

        # Validate new password
        if len(new_password) < 6:
            self._print_important(f"{Icons.ERROR} New password must be at least 6 characters", COLORS["red"])
            return False

        # Update password
        result = self.update_user(identifier, password=new_password)
        if result:
            self._print_important(f"{Icons.PASSWORD} Password changed for user: {identifier}", COLORS["green"])
            return True

        return False

    def reset_password(self, identifier: str, new_password: str) -> bool:
        """
        Reset user password (admin function - no old password required).

        Args:
            identifier: Username or email
            new_password: New password

        Returns:
            True if password reset successfully
        """
        if len(new_password) < 6:
            self._print_important(f"{Icons.ERROR} New password must be at least 6 characters", COLORS["red"])
            return False

        result = self.update_user(identifier, password=new_password)
        if result:
            self._print_important(f"{Icons.PASSWORD} Password reset for user: {identifier}", COLORS["green"])
            return True

        return False

    def toggle_user_status(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Toggle user active/inactive status.

        Args:
            identifier: Username or email

        Returns:
            Updated user data or None if failed
        """
        user = self.get_user(identifier)
        if not user:
            return None

        new_status = not user['is_active']
        result = self.update_user(identifier, is_active=new_status)

        if result:
            status_text = "activated" if new_status else "deactivated"
            self._print_important(f"{Icons.UPDATE} User {status_text}: {identifier}", COLORS["green"])

        return result

    def promote_to_admin(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Promote user to admin."""
        return self.update_user(identifier, is_admin=True)

    def demote_from_admin(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Remove admin privileges from user."""
        return self.update_user(identifier, is_admin=False)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username (internal use only).

        Args:
            username: Username

        Returns:
            User dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()

                if row:
                    user_dict = dict(row)
                    # Convert timestamps
                    for field in ['last_login', 'created_at', 'updated_at']:
                        if user_dict[field] and isinstance(user_dict[field], str):
                            try:
                                user_dict[field] = datetime.fromisoformat(user_dict[field])
                            except ValueError:
                                pass
                    return user_dict
                return None

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in get_user_by_username: {e}", COLORS["red"])
            return None