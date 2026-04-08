import sqlite3
import requests
from typing import Optional, Dict, Any, List
from common_script import website_script, common
from datetime import datetime
from threading import Lock
import os
# Thread-safe print lock
print_lock = Lock()

from company_ai_project import saved_data

database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'link_database.db'
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
    LINK = '🔗'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '🔄'


class LinkTable:
    """Handles operations for the link table."""

    def __init__(self, db_path: str = database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database_old connection with WAL mode enabled."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False  # Only if using multiple threads
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds timeout
        return conn

    def _check_link_valid(self, link: str) -> tuple[bool, dict]:
        """
        Check if link is working using website_script.check_link_status().

        Returns:
            Tuple of (is_working, status_info)
        """
        if not link:
            return False, {"error": "Empty link"}
        try:
            # Use your existing website_script method
            is_working, status_info = website_script.check_link_status(link)
            if not is_working:
                self._print_important(f"{Icons.ERROR} Link invalid: {link} - {status_info}", COLORS["red"])
            return is_working, status_info
        except Exception as e:
            if self.debug:
                self._print_important(f"{Icons.ERROR} Error checking link {link}: {e}", COLORS["red"])
            return False, {"error": str(e)}

    def create_table(self) -> None:
        """Create the link table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS link (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT NOT NULL,
                    link TEXT NOT NULL,
                    link_overview TEXT,
                    is_working BOOLEAN DEFAULT 0,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(unique_name, link),
                    FOREIGN KEY (unique_name) REFERENCES companies (unique_name) ON DELETE CASCADE
                )
            ''')

            # Check if is_working column exists and add it if it doesn't (for existing databases)
            cursor.execute("PRAGMA table_info(link)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'is_working' not in columns:
                cursor.execute('ALTER TABLE link ADD COLUMN is_working BOOLEAN DEFAULT 0')
            if 'last_checked' not in columns:
                cursor.execute('ALTER TABLE link ADD COLUMN last_checked TIMESTAMP')

    def insert_link(
            self,
            unique_name: str,
            link: str,
            link_overview: Optional[str] = None,
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new link into the database. Only working links are allowed.

        Args:
            unique_name: Unique identifier for the company
            link: Link URL
            link_overview: Overview of the link (optional)
            replace: If True, replace existing link with same unique_name and link (default: False)

        Returns:
            Link data if successful, empty dict if link is invalid or not working
        """
        formatted_link = website_script.format_website_url(link)
        if not formatted_link:
            self._print_important(f"{Icons.ERROR} Invalid link format: {link}", COLORS["red"])
            return {}

        # Check if the link is working
        is_working, status_info = self._check_link_valid(formatted_link)

        # ONLY allow working links - no option to add broken links
        if not is_working:
            self._print_important(f"{Icons.ERROR} Cannot insert non-working link: {formatted_link} - {status_info}",
                                  COLORS["red"])
            return {}

        # Check if a link with the same unique_name and link already exists
        existing_link = self._get_link_by_unique_name_and_link(unique_name, formatted_link)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if we should auto-update the overview (existing overview is empty and new overview has value)
                should_auto_update_overview = (existing_link and
                                               link_overview and
                                               not existing_link.get('link_overview'))

                # If replace is True OR (auto-update overview condition is met), update the link
                if (replace or should_auto_update_overview) and existing_link:
                    # Prepare update fields dynamically
                    update_fields = ['is_working = ?', 'last_checked = CURRENT_TIMESTAMP',
                                     'updated_at = CURRENT_TIMESTAMP']
                    update_values = [is_working]

                    # Only update link_overview if we have a new value
                    if link_overview is not None:
                        update_fields.append('link_overview = ?')
                        update_values.append(link_overview)

                    query = f'''
                        UPDATE link 
                        SET {', '.join(update_fields)}
                        WHERE unique_name = ? AND link = ?
                    '''
                    update_values.extend([unique_name, formatted_link])

                    cursor.execute(query, update_values)
                    conn.commit()

                    if replace:
                        self._print_important(
                            f"{Icons.UPDATE} Updated link: {unique_name} -> {formatted_link} (working: {is_working})",
                            COLORS["green"])
                    else:
                        self._print_important(
                            f"{Icons.UPDATE} Auto-updated empty link overview for: {unique_name} -> {formatted_link}",
                            COLORS["green"])

                    return self._get_link_by_unique_name_and_link(unique_name, formatted_link)

                # If replace is False and a link with the same unique_name and link exists, return it
                elif existing_link and not replace:
                    self._print_important(f"{Icons.WARNING} Link already exists: {unique_name} -> {formatted_link}",
                                          COLORS["yellow"])
                    return existing_link

                # Insert new link
                else:
                    cursor.execute('''
                        INSERT INTO link 
                        (unique_name, link, link_overview, is_working, last_checked)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (unique_name, formatted_link, link_overview, is_working))
                    conn.commit()
                    self._print_important(
                        f"{Icons.SUCCESS} Inserted link: {unique_name} -> {formatted_link} (working: {is_working})",
                        COLORS["green"])
                    return self._get_link_by_unique_name_and_link(unique_name, formatted_link)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return existing_link or {}

    def replace_all_links(
            self,
            unique_name: str,
            links: List[Dict[str, str]],  # List of dicts with 'url' and optionally 'overview'
            clear_if_empty: bool = True,
            enforce_working: bool = True  # New parameter to enforce working links only
    ) -> List[Dict[str, Any]]:
        """
        Replace ALL links for a company with a new set of links.

        Args:
            unique_name: Unique identifier for the company
            links: List of link dictionaries with 'url' key and optional 'overview' key
            clear_if_empty: If True and links list is empty, delete all links (default: True)
            enforce_working: If True, only insert working links; if False, allow broken links (default: True)

        Returns:
            List of inserted/updated link data (only working links if enforce_working is True)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                results = []

                # Start transaction
                cursor.execute('BEGIN TRANSACTION')

                # Delete all existing links for this unique_name
                cursor.execute('''
                    DELETE FROM link 
                    WHERE unique_name = ?
                ''', (unique_name,))

                deleted_count = cursor.rowcount
                self._print_important(f"{Icons.UPDATE} Deleted {deleted_count} existing links for: {unique_name}",
                                      COLORS["yellow"])

                # Insert all new links
                skipped_count = 0
                for link_data in links:
                    url = link_data.get('url', '')
                    overview = link_data.get('overview')

                    formatted_url = website_script.format_website_url(url)
                    if not formatted_url:
                        self._print_important(f"{Icons.WARNING} Skipping invalid link: {url}", COLORS["yellow"])
                        continue

                    # Check if the link is working
                    is_working, status_info = self._check_link_valid(formatted_url)

                    # If enforce_working is True and link is not working, skip it
                    if enforce_working and not is_working:
                        self._print_important(f"{Icons.WARNING} Skipping non-working link: {formatted_url}",
                                              COLORS["yellow"])
                        skipped_count += 1
                        continue

                    cursor.execute('''
                        INSERT INTO link 
                        (unique_name, link, link_overview, is_working, last_checked)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (unique_name, formatted_url, overview, is_working))

                    # Get the inserted link
                    cursor.execute('''
                        SELECT * FROM link 
                        WHERE unique_name = ? AND link = ?
                    ''', (unique_name, formatted_url))

                    row = cursor.fetchone()
                    if row:
                        results.append(dict(zip([column[0] for column in cursor.description], row)))

                    self._print_important(
                        f"{Icons.SUCCESS} Added link: {unique_name} -> {formatted_url} (working: {is_working})",
                        COLORS["green"])

                # If no links provided and clear_if_empty is True, we've already cleared them
                if not links and clear_if_empty:
                    self._print_important(
                        f"{Icons.UPDATE} No new links provided, cleared all existing links for: {unique_name}",
                        COLORS["yellow"])
                elif skipped_count > 0:
                    self._print_important(
                        f"{Icons.WARNING} Skipped {skipped_count} non-working links for: {unique_name}",
                        COLORS["yellow"])

                conn.commit()
                return results

        except sqlite3.Error as e:
            conn.rollback()
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return []

    def _get_link_by_unique_name_and_link(self, unique_name: str, link: str) -> Optional[Dict[str, Any]]:
        """Get link by unique_name and link."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM link WHERE unique_name = ? AND link = ?', (unique_name, link))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_link(self, unique_name: str, link: str) -> bool:
        """Delete link by unique_name and link."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM link WHERE unique_name = ? AND link = ?', (unique_name, link))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.TRASH} Deleted link: {unique_name} -> {link}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Link not found: {unique_name} -> {link}", COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def delete_all_links(self, unique_name: str) -> int:
        """Delete all links by unique_name.

        Args:
            unique_name: The unique name whose links should be deleted

        Returns:
            int: Number of links deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM link WHERE unique_name = ?', (unique_name,))
                conn.commit()
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    self._print_important(
                        f"{Icons.TRASH} Deleted {deleted_count} link(s) for: {unique_name}",
                        COLORS["green"]
                    )
                else:
                    self._print_important(
                        f"{Icons.WARNING} No links found for: {unique_name}",
                        COLORS["yellow"]
                    )
                return deleted_count
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return 0

    def update_link(
            self,
            unique_name: str,
            old_link: str,
            new_link: str,
            link_overview: Optional[str] = None,
            enforce_working: bool = True
    ) -> bool:
        """
        Update link by unique_name and old link.

        Args:
            unique_name: Unique identifier for the company
            old_link: Current link URL
            new_link: New link URL
            link_overview: New overview (optional)
            enforce_working: If True, only update to working links; if False, allow broken links (default: True)
        """
        formatted_new_link = website_script.format_website_url(new_link)
        if not formatted_new_link:
            self._print_important(f"{Icons.ERROR} Invalid new link format: {new_link}", COLORS["red"])
            return False

        # Check if the new link is working
        is_working, status_info = self._check_link_valid(formatted_new_link)

        # If enforce_working is True and new link is not working, don't update
        if enforce_working and not is_working:
            self._print_important(
                f"{Icons.ERROR} Cannot update to non-working link: {formatted_new_link} - {status_info}", COLORS["red"])
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE link 
                    SET link = ?, link_overview = ?, is_working = ?, last_checked = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE unique_name = ? AND link = ?
                ''', (formatted_new_link, link_overview, is_working, unique_name, old_link))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(
                        f"{Icons.UPDATE} Updated link: {unique_name} -> {old_link} to {formatted_new_link} (working: {is_working})",
                        COLORS["green"])
                else:
                    self._print_important(
                        f"{Icons.WARNING} Link update failed - not found: {unique_name} -> {old_link}",
                        COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", COLORS["red"])
            return False

    def update_link_status(self, unique_name: str, link: str, is_working: Optional[bool] = None) -> bool:
        """
        Update the status of a specific link.

        Args:
            unique_name: Unique identifier for the company
            link: Link URL to check
            is_working: If provided, set status manually; otherwise auto-check

        Returns:
            True if update was successful, False otherwise
        """
        formatted_link = website_script.format_website_url(link)
        if not formatted_link:
            return False

        if is_working is None:
            # Auto-check the link
            working_status, status_info = self._check_link_valid(formatted_link)
        else:
            working_status = is_working

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE link 
                    SET is_working = ?, last_checked = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE unique_name = ? AND link = ?
                ''', (working_status, unique_name, formatted_link))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(
                        f"{Icons.UPDATE} Updated status for: {unique_name} -> {formatted_link} to {working_status}",
                        COLORS["green"]
                    )
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Status update failed: {e}", COLORS["red"])
            return False

    def get_links_by_unique_name(self, unique_name: str, only_working: bool = False) -> List[Dict[str, Any]]:
        """
        Get all links for a specific company.

        Args:
            unique_name: Unique identifier for the company
            only_working: If True, only return links that are working (is_working = 1)
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if only_working:
                cursor.execute('SELECT * FROM link WHERE unique_name = ? AND is_working = 1', (unique_name,))
            else:
                cursor.execute('SELECT * FROM link WHERE unique_name = ?', (unique_name,))
            rows = cursor.fetchall()
            links = [dict(row) for row in rows]
            return links

    def get_link_by_id(self, link_id: int) -> Optional[Dict[str, Any]]:
        """Get link by ID."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM link WHERE id = ?', (link_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def validate_all_links(self, unique_name: str, update_status: bool = True) -> List[Dict[str, Any]]:
        """
        Validate all links for a company and optionally update their status in the database.

        Args:
            unique_name: Unique identifier for the company
            update_status: If True, update the database with the current status

        Returns:
            List of valid links
        """
        all_links = self.get_links_by_unique_name(unique_name)
        valid_links = []
        invalid_links = []

        self._print_important(f"{Icons.INFO} Validating {len(all_links)} links for: {unique_name}", COLORS["blue"])

        for link_data in all_links:
            is_working, status_info = self._check_link_valid(link_data['link'])

            # Update the link status in the database if requested
            if update_status:
                self.update_link_status(unique_name, link_data['link'], is_working)

            if is_working:
                valid_links.append(link_data)
            else:
                invalid_links.append(link_data['link'])

        if invalid_links:
            self._print_important(f"{Icons.WARNING} Found {len(invalid_links)} invalid links for {unique_name}",
                                  COLORS["yellow"])
            for invalid_link in invalid_links[:5]:  # Show first 5 invalid links
                self._print_important(f"   {Icons.ERROR} {invalid_link}", COLORS["red"])
            if len(invalid_links) > 5:
                self._print_important(f"   ... and {len(invalid_links) - 5} more invalid links", COLORS["gray"])

        self._print_important(
            f"{Icons.SUCCESS} Validation complete: {len(valid_links)} valid, {len(invalid_links)} invalid",
            COLORS["green"])
        return valid_links

    def check_link_status(self, link: str) -> tuple[bool, Dict[str, Any]]:
        """
        Check link status using your existing website_script method.

        Args:
            link: The URL to check

        Returns:
            Tuple of (is_working, status_info)
        """
        try:
            is_working, status_info = website_script.check_link_status(link)
            if is_working:
                self._print_important(f"{Icons.SUCCESS} Link accessible: {link}", COLORS["green"])
            else:
                self._print_important(f"{Icons.ERROR} Link inaccessible: {link} - {status_info}", COLORS["red"])
            return is_working, status_info
        except Exception as e:
            if self.debug:
                self._print_important(f"{Icons.ERROR} Error in check_link_status: {e}", COLORS["red"])
            return False, {"error": str(e)}

    def search_links(
            self,
            search_text: str,
            exact_match: bool = False,
            only_working: bool = False
    ) -> List[Dict]:
        """
        Search for links across all columns and return results as dictionaries.

        Args:
            search_text: Text to search for
            exact_match: If True, performs exact match search; if False, performs partial match
            only_working: If True, only return working links (is_working = 1)

        Returns:
            List of dictionaries containing matching rows
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if exact_match:
                # Exact match search
                if only_working:
                    query = '''
                        SELECT * FROM link 
                        WHERE (unique_name = ? OR link = ? OR link_overview = ?)
                        AND is_working = 1
                    '''
                    params = (search_text, search_text, search_text)
                else:
                    query = '''
                        SELECT * FROM link 
                        WHERE unique_name = ? OR link = ? OR link_overview = ?
                    '''
                    params = (search_text, search_text, search_text)
                search_type = "exact"
            else:
                # Partial match search (case-insensitive)
                search_pattern = f'%{search_text}%'
                if only_working:
                    query = '''
                        SELECT * FROM link 
                        WHERE (LOWER(unique_name) LIKE LOWER(?) OR LOWER(link) LIKE LOWER(?) OR LOWER(link_overview) LIKE LOWER(?))
                        AND is_working = 1
                    '''
                    params = (search_pattern, search_pattern, search_pattern)
                else:
                    query = '''
                        SELECT * FROM link 
                        WHERE LOWER(unique_name) LIKE LOWER(?) OR LOWER(link) LIKE LOWER(?) OR LOWER(link_overview) LIKE LOWER(?)
                    '''
                    params = (search_pattern, search_pattern, search_pattern)
                search_type = "partial"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            # Convert to list of dictionaries
            results = []
            for row in rows:
                result_dict = dict(zip(column_names, row))
                results.append(result_dict)

            if self.debug:
                status = "working " if only_working else ""
                self._print_important(
                    f"{Icons.SEARCH} Search ({search_type}): '{search_text}' found {len(results)} {status}results",
                    COLORS["blue"])

            return results

    def get_all_links(self, only_working: bool = False) -> List[Dict[str, Any]]:
        """
        Get all links from the database.

        Args:
            only_working: If True, only return links that are working (is_working = 1)
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if only_working:
                cursor.execute('SELECT * FROM link WHERE is_working = 1')
            else:
                cursor.execute('SELECT * FROM link')
            rows = cursor.fetchall()
            links = [dict(row) for row in rows]
            return links

    def get_links_count(self, only_working: bool = False) -> int:
        """
        Get total number of links in the database.

        Args:
            only_working: If True, count only working links (is_working = 1)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if only_working:
                cursor.execute('SELECT COUNT(*) FROM link WHERE is_working = 1')
            else:
                cursor.execute('SELECT COUNT(*) FROM link')
            count = cursor.fetchone()[0]
            if self.debug:
                status = "working " if only_working else ""
                self._print_important(f"{Icons.INFO} Total {status}links in database: {count}", COLORS["blue"])
            return count

    def get_broken_links(self) -> List[Dict[str, Any]]:
        """Get all broken links (is_working = 0) from the database."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM link WHERE is_working = 0')
            rows = cursor.fetchall()
            links = [dict(row) for row in rows]
            if self.debug:
                self._print_important(f"{Icons.INFO} Found {len(links)} broken links", COLORS["yellow"])
            return links

    def get_links_by_status(self, is_working: bool) -> List[Dict[str, Any]]:
        """
        Get all links with a specific working status.

        Args:
            is_working: True for working links, False for broken links
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM link WHERE is_working = ?', (1 if is_working else 0,))
            rows = cursor.fetchall()
            links = [dict(row) for row in rows]
            status_text = "working" if is_working else "broken"
            if self.debug:
                self._print_important(f"{Icons.INFO} Found {len(links)} {status_text} links", COLORS["blue"])
            return links

    def update_all_link_statuses(self, unique_name: Optional[str] = None) -> Dict[str, int]:
        """
        Update status for all links or links for a specific company.

        Args:
            unique_name: If provided, only update links for this company

        Returns:
            Dictionary with counts of total, working, and broken links
        """
        if unique_name:
            links = self.get_links_by_unique_name(unique_name)
        else:
            links = self.get_all_links()

        total = len(links)
        working = 0
        broken = 0

        self._print_important(f"{Icons.INFO} Updating status for {total} links...", COLORS["blue"])

        for link_data in links:
            is_working, status_info = self._check_link_valid(link_data['link'])
            self.update_link_status(link_data['unique_name'], link_data['link'], is_working)

            if is_working:
                working += 1
            else:
                broken += 1

        self._print_important(
            f"{Icons.SUCCESS} Status update complete: {working} working, {broken} broken out of {total} total",
            COLORS["green"]
        )

        return {
            "total": total,
            "working": working,
            "broken": broken
        }

    def get_unique_names(self) -> list:
        """Get a list of all unique names from the companies table.

        :return: List of unique names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT unique_name unique_name FROM link')
            results = cursor.fetchall()
            all_list = [row[0] for row in results]
            all_list = list(set(all_list))
            return all_list


class FilterLinkTable:
    """Handles operations for the filter_link table."""

    def __init__(self, db_path: str = database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_table()

    def _print_important(self, message: str, color: str = COLORS["white"]) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            safe_print(message, color)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with WAL mode enabled."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def create_table(self) -> None:
        """Create the filter_link table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filter_link (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT NOT NULL,
                    link TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(unique_name, link),
                    FOREIGN KEY (unique_name) REFERENCES companies (unique_name) ON DELETE CASCADE
                )
            ''')

    # ------------------------------------------------------------------ #
    #  INSERT                                                              #
    # ------------------------------------------------------------------ #

    def insert_filter_link(
            self,
            unique_name: str,
            link: str,
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new filter link into the database.

        Args:
            unique_name: Unique identifier for the company
            link: Link URL to filter
            replace: If True, touch updated_at on duplicate; if False, return existing (default: False)

        Returns:
            Filter link data dict if successful, else empty dict
        """
        formatted_link = website_script.format_website_url(link)
        if not formatted_link:
            self._print_important(f"{Icons.ERROR} Invalid link format: {link}", COLORS["red"])
            return {}

        is_working, status_info = website_script.check_link_status(formatted_link)
        if not is_working:
            self._print_important(f"{Icons.ERROR} Link inaccessible: {formatted_link} - {status_info}", COLORS["red"])
            return {}

        existing = self._get_filter_link_by_unique_name_and_link(unique_name, formatted_link)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if replace and existing:
                    cursor.execute('''
                        UPDATE filter_link
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE unique_name = ? AND link = ?
                    ''', (unique_name, formatted_link))
                    conn.commit()
                    self._print_important(
                        f"{Icons.UPDATE} Touched filter_link: {unique_name} -> {formatted_link}",
                        COLORS["green"]
                    )
                    return self._get_filter_link_by_unique_name_and_link(unique_name, formatted_link)

                elif existing and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Filter link already exists: {unique_name} -> {formatted_link}",
                        COLORS["yellow"]
                    )
                    return existing

                else:
                    cursor.execute('''
                        INSERT INTO filter_link (unique_name, link)
                        VALUES (?, ?)
                    ''', (unique_name, formatted_link))
                    conn.commit()
                    self._print_important(
                        f"{Icons.SUCCESS} Inserted filter_link: {unique_name} -> {formatted_link}",
                        COLORS["green"]
                    )
                    return self._get_filter_link_by_unique_name_and_link(unique_name, formatted_link)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return existing or {}

    def insert_many_filter_links(
            self,
            unique_name: str,
            links: List[str],
            skip_existing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Bulk-insert multiple filter links for a company in a single transaction.

        Args:
            unique_name: Unique identifier for the company
            links: List of URL strings
            skip_existing: If True, silently skip duplicates; if False, raise on conflict (default: True)

        Returns:
            List of successfully inserted filter link dicts
        """
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')

                for link in links:
                    formatted_link = website_script.format_website_url(link)
                    if not formatted_link:
                        self._print_important(f"{Icons.WARNING} Skipping invalid link: {link}", COLORS["yellow"])
                        continue

                    try:
                        cursor.execute('''
                            INSERT INTO filter_link (unique_name, link)
                            VALUES (?, ?)
                        ''', (unique_name, formatted_link))
                        self._print_important(
                            f"{Icons.SUCCESS} Inserted filter_link: {unique_name} -> {formatted_link}",
                            COLORS["green"]
                        )
                    except sqlite3.IntegrityError:
                        if skip_existing:
                            self._print_important(
                                f"{Icons.WARNING} Skipping existing filter_link: {unique_name} -> {formatted_link}",
                                COLORS["yellow"]
                            )
                        else:
                            raise

                conn.commit()

                # Fetch all inserted rows
                cursor.execute('SELECT * FROM filter_link WHERE unique_name = ?', (unique_name,))
                column_names = [d[0] for d in cursor.description]
                results = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Bulk insert failed: {e}", COLORS["red"])

        return results

    # ------------------------------------------------------------------ #
    #  READ                                                                #
    # ------------------------------------------------------------------ #

    def _get_filter_link_by_unique_name_and_link(
            self, unique_name: str, link: str
    ) -> Optional[Dict[str, Any]]:
        """Internal: fetch a single row by (unique_name, link)."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM filter_link WHERE unique_name = ? AND link = ?',
                (unique_name, link)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_filter_link_by_id(self, filter_link_id: int) -> Optional[Dict[str, Any]]:
        """Get a filter link by its primary key ID."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM filter_link WHERE id = ?', (filter_link_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_filter_links_by_unique_name(self, unique_name: str) -> List[Dict[str, Any]]:
        """Get all filter links for a specific company."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM filter_link WHERE unique_name = ?', (unique_name,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_filter_links(self) -> List[Dict[str, Any]]:
        """Get every row from filter_link."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM filter_link')
            return [dict(row) for row in cursor.fetchall()]

    def get_filter_links_count(self, unique_name: Optional[str] = None) -> int:
        """
        Get total number of filter links.

        Args:
            unique_name: If provided, count only for that company; otherwise count all.

        Returns:
            Row count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if unique_name:
                cursor.execute('SELECT COUNT(*) FROM filter_link WHERE unique_name = ?', (unique_name,))
            else:
                cursor.execute('SELECT COUNT(*) FROM filter_link')
            count = cursor.fetchone()[0]
            if self.debug:
                scope = f"for '{unique_name}'" if unique_name else "total"
                self._print_important(f"{Icons.INFO} Filter links {scope}: {count}", COLORS["blue"])
            return count

    def is_link_filtered(self, unique_name: str, link: str) -> bool:
        """
        Check whether a specific link is already in the filter_link table.

        Args:
            unique_name: Unique identifier for the company
            link: URL to check

        Returns:
            True if filtered, False otherwise
        """
        formatted_link = website_script.format_website_url(link) or link
        result = self._get_filter_link_by_unique_name_and_link(unique_name, formatted_link)
        return result is not None

    def search_filter_links(self, search_text: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search filter_link rows by unique_name or link.

        Args:
            search_text: Text to search for
            exact_match: If True, exact equality; if False, LIKE partial match (default: False)

        Returns:
            List of matching row dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if exact_match:
                query = '''
                    SELECT * FROM filter_link
                    WHERE unique_name = ? OR link = ?
                '''
                params = (search_text, search_text)
                search_type = "exact"
            else:
                pattern = f'%{search_text}%'
                query = '''
                    SELECT * FROM filter_link
                    WHERE LOWER(unique_name) LIKE LOWER(?)
                       OR LOWER(link) LIKE LOWER(?)
                '''
                params = (pattern, pattern)
                search_type = "partial"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            column_names = [d[0] for d in cursor.description]
            results = [dict(zip(column_names, row)) for row in rows]

            if self.debug:
                self._print_important(
                    f"{Icons.SEARCH} Search ({search_type}): '{search_text}' found {len(results)} results",
                    COLORS["blue"]
                )
            return results

    # ------------------------------------------------------------------ #
    #  UPDATE                                                              #
    # ------------------------------------------------------------------ #

    def update_filter_link(self, unique_name: str, old_link: str, new_link: str) -> bool:
        """
        Replace the URL of an existing filter link.

        Args:
            unique_name: Unique identifier for the company
            old_link: Existing URL to replace
            new_link: New URL

        Returns:
            True if updated, False otherwise
        """
        formatted_new_link = website_script.format_website_url(new_link)
        if not formatted_new_link:
            self._print_important(f"{Icons.ERROR} Invalid new link format: {new_link}", COLORS["red"])
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE filter_link
                    SET link = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE unique_name = ? AND link = ?
                ''', (formatted_new_link, unique_name, old_link))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(
                        f"{Icons.UPDATE} Updated filter_link: {unique_name} -> {old_link} to {formatted_new_link}",
                        COLORS["green"]
                    )
                else:
                    self._print_important(
                        f"{Icons.WARNING} Filter link not found: {unique_name} -> {old_link}",
                        COLORS["yellow"]
                    )
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", COLORS["red"])
            return False

    # ------------------------------------------------------------------ #
    #  DELETE                                                              #
    # ------------------------------------------------------------------ #

    def delete_filter_link(self, unique_name: str, link: str) -> bool:
        """
        Delete a single filter link by (unique_name, link).

        Args:
            unique_name: Unique identifier for the company
            link: URL to remove

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM filter_link WHERE unique_name = ? AND link = ?',
                    (unique_name, link)
                )
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(
                        f"{Icons.TRASH} Deleted filter_link: {unique_name} -> {link}",
                        COLORS["green"]
                    )
                else:
                    self._print_important(
                        f"{Icons.WARNING} Filter link not found: {unique_name} -> {link}",
                        COLORS["yellow"]
                    )
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def delete_filter_link_by_id(self, filter_link_id: int) -> bool:
        """
        Delete a single filter link by primary key ID.

        Args:
            filter_link_id: Row ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM filter_link WHERE id = ?', (filter_link_id,))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.TRASH} Deleted filter_link id={filter_link_id}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Filter link id={filter_link_id} not found", COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def delete_all_filter_links_by_unique_name(self, unique_name: str) -> int:
        """
        Delete ALL filter links for a given company.

        Args:
            unique_name: Unique identifier for the company

        Returns:
            Number of rows deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM filter_link WHERE unique_name = ?', (unique_name,))
                conn.commit()
                deleted = cursor.rowcount
                self._print_important(
                    f"{Icons.TRASH} Deleted {deleted} filter_links for: {unique_name}",
                    COLORS["green"]
                )
                return deleted
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete all failed: {e}", COLORS["red"])
            return 0

    def replace_all_filter_links(
            self,
            unique_name: str,
            links: List[str],
            clear_if_empty: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Atomically replace ALL filter links for a company with a new list.

        Args:
            unique_name: Unique identifier for the company
            links: List of URL strings to set as the new filter list
            clear_if_empty: If True and links is empty, wipe existing rows (default: True)

        Returns:
            List of current filter link dicts after replacement
        """
        if not links and not clear_if_empty:
            self._print_important(
                f"{Icons.WARNING} No links provided and clear_if_empty=False; nothing changed.",
                COLORS["yellow"]
            )
            return self.get_filter_links_by_unique_name(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION')

                cursor.execute('DELETE FROM filter_link WHERE unique_name = ?', (unique_name,))
                deleted_count = cursor.rowcount
                self._print_important(
                    f"{Icons.UPDATE} Deleted {deleted_count} existing filter_links for: {unique_name}",
                    COLORS["yellow"]
                )

                for link in links:
                    formatted_link = website_script.format_website_url(link)
                    if not formatted_link:
                        self._print_important(f"{Icons.WARNING} Skipping invalid link: {link}", COLORS["yellow"])
                        continue
                    cursor.execute('''
                        INSERT INTO filter_link (unique_name, link)
                        VALUES (?, ?)
                    ''', (unique_name, formatted_link))
                    self._print_important(
                        f"{Icons.SUCCESS} Added filter_link: {unique_name} -> {formatted_link}",
                        COLORS["green"]
                    )

                conn.commit()

                cursor.execute('SELECT * FROM filter_link WHERE unique_name = ?', (unique_name,))
                column_names = [d[0] for d in cursor.description]
                return [dict(zip(column_names, row)) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            conn.rollback()
            self._print_important(f"{Icons.ERROR} Replace all failed: {e}", COLORS["red"])
            return []

    def get_unique_names(self) -> list:
        """Get a list of all unique names from the companies table.

        :return: List of unique names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT unique_name unique_name FROM filter_link')
            results = cursor.fetchall()
            all_list = [row[0] for row in results]
            all_list = list(set(all_list))
            return all_list



