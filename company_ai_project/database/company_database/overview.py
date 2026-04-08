import sqlite3
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
import os
# Thread-safe print lock
print_lock = Lock()
from company_ai_project import saved_data

database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'overview_database.db'
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
    OVERVIEW = '📝'
    SMALL = '📋'
    TRASH = '🗑️'
    UPDATE = '🔄'


class OverviewTable:
    """Handles operations for the overview table with main and small overviews."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_table()
        SummaryTable()

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

    def create_table(self) -> None:
        """Create the overview table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS overview (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT UNIQUE NOT NULL,
                    overview TEXT,
                    small_overview TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (unique_name) REFERENCES companies (unique_name) ON DELETE CASCADE
                )
            ''')

    def insert_overview(
            self,
            unique_name: str,
            overview: Optional[str] = None,
            small_overview: Optional[str] = None,
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert or update overview with main and small overview columns.

        Args:
            unique_name: Unique identifier for the company
            overview: Main/complete overview (optional)
            small_overview: Small/condensed overview (optional)
            replace: If True, replace existing overview with same unique_name (default: False)

        Returns:
            Overview data if successful
        """
        # Check if an overview with the same unique_name already exists
        existing_overview = self._get_overview_by_unique_name(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If replace is True and an overview with the same unique_name exists, update it
                if replace and existing_overview:
                    # If only one type is provided, keep the existing one for the other type
                    final_overview = overview if overview is not None else existing_overview.get('overview')
                    final_small = small_overview if small_overview is not None else existing_overview.get(
                        'small_overview')

                    cursor.execute('''
                        UPDATE overview 
                        SET overview = ?, small_overview = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE unique_name = ?
                    ''', (final_overview, final_small, unique_name))
                    conn.commit()
                    self._print_important(f"{Icons.UPDATE} Updated overview: {unique_name}", COLORS["green"])
                    return self._get_overview_by_unique_name(unique_name)

                # If replace is False and an overview with the same unique_name exists, return it
                elif existing_overview and not replace:
                    self._print_important(f"{Icons.WARNING} Overview already exists: {unique_name}", COLORS["yellow"])
                    return existing_overview

                # Insert new overview
                else:
                    cursor.execute('''
                        INSERT INTO overview 
                        (unique_name, overview, small_overview)
                        VALUES (?, ?, ?)
                    ''', (unique_name, overview, small_overview))
                    conn.commit()
                    self._print_important(f"{Icons.SUCCESS} Inserted overview: {unique_name}", COLORS["green"])
                    return self._get_overview_by_unique_name(unique_name)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return existing_overview or {}

    def _get_overview_by_unique_name(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get overview by unique_name."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM overview WHERE unique_name = ?', (unique_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_overview(self, unique_name: str) -> bool:
        """Delete overview by unique_name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM overview WHERE unique_name = ?', (unique_name,))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.TRASH} Deleted overview: {unique_name}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Overview not found: {unique_name}", COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def update_overview(self, unique_name: str, overview: str, is_small: bool = False) -> bool:
        """Update either main overview or small overview."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if is_small:
                    cursor.execute('''
                        UPDATE overview 
                        SET small_overview = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE unique_name = ?
                    ''', (overview, unique_name))
                    self._print_important(f"{Icons.UPDATE} Updated small_overview: {unique_name}",
                                          COLORS["green"])
                else:
                    cursor.execute('''
                        UPDATE overview 
                        SET overview = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE unique_name = ?
                    ''', (overview, unique_name))
                    self._print_important(f"{Icons.UPDATE} Updated main overview: {unique_name}", COLORS["green"])

                conn.commit()
                success = cursor.rowcount > 0
                if not success:
                    self._print_important(f"{Icons.WARNING} Overview update failed - not found: {unique_name}",
                                          COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", COLORS["red"])
            return False

    def get_overview(self, unique_name: str, prefer_small: bool = False) -> Optional[Dict[str, Any]]:
        """Get overview by unique_name, with option to prefer small_overview over main overview."""
        overview_data = self._get_overview_by_unique_name(unique_name)

        if overview_data:
            # Determine which overview to use based on preference
            if prefer_small and overview_data.get('small_overview'):
                overview_data['preferred_overview'] = overview_data['small_overview']
                overview_data['overview_type'] = 'small'
            elif overview_data.get('overview'):
                overview_data['preferred_overview'] = overview_data['overview']
                overview_data['overview_type'] = 'main'
            elif overview_data.get('small_overview'):
                overview_data['preferred_overview'] = overview_data['small_overview']
                overview_data['overview_type'] = 'small'
            else:
                overview_data['preferred_overview'] = None
                overview_data['overview_type'] = 'none'

        return overview_data

    def get_main_overview(self, unique_name: str) -> Optional[str]:
        """Get only main overview by unique_name."""
        overview_data = self._get_overview_by_unique_name(unique_name)
        return overview_data.get('overview') if overview_data else None

    def get_small_overview(self, unique_name: str) -> Optional[str]:
        """Get only small overview by unique_name."""
        overview_data = self._get_overview_by_unique_name(unique_name)
        return overview_data.get('small_overview') if overview_data else None

    def generate_small_from_main(self, unique_name: str, max_length: int = 200) -> bool:
        """Generate small overview from main overview if main exists."""
        main_overview = self.get_main_overview(unique_name)

        if not main_overview:
            self._print_important(f"{Icons.WARNING} No main overview to generate from: {unique_name}", COLORS["yellow"])
            return False

        # Create a condensed version (first max_length characters)
        small_overview = main_overview[:max_length].strip()
        if len(main_overview) > max_length:
            small_overview += "..."

        return self.update_overview(unique_name, small_overview, is_small=True)

    def get_all_overviews(self, include_empty: bool = False) -> List[Dict[str, Any]]:
        """Get all overviews from the database_old."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if include_empty:
                    cursor.execute('SELECT * FROM overview ORDER BY unique_name')
                else:
                    cursor.execute('''
                        SELECT * FROM overview 
                        WHERE (overview IS NOT NULL AND overview != '') 
                           OR (small_overview IS NOT NULL AND small_overview != '')
                        ORDER BY unique_name
                    ''')

                rows = cursor.fetchall()
                overviews = [dict(row) for row in rows]

                return overviews

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Error getting overviews: {e}", COLORS["red"])
            return []

    def get_overviews_count(self) -> Dict[str, int]:
        """Get counts of different types of overviews."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Count total overviews
            cursor.execute('SELECT COUNT(*) FROM overview')
            total = cursor.fetchone()[0]

            # Count overviews with main only
            cursor.execute('''
                SELECT COUNT(*) FROM overview 
                WHERE (overview IS NOT NULL AND overview != '') 
                  AND (small_overview IS NULL OR small_overview = '')
            ''')
            main_only = cursor.fetchone()[0]

            # Count overviews with small only
            cursor.execute('''
                SELECT COUNT(*) FROM overview 
                WHERE (small_overview IS NOT NULL AND small_overview != '') 
                  AND (overview IS NULL OR overview = '')
            ''')
            small_only = cursor.fetchone()[0]

            # Count overviews with both
            cursor.execute('''
                SELECT COUNT(*) FROM overview 
                WHERE (overview IS NOT NULL AND overview != '') 
                  AND (small_overview IS NOT NULL AND small_overview != '')
            ''')
            both = cursor.fetchone()[0]

            # Count empty overviews
            cursor.execute('''
                SELECT COUNT(*) FROM overview 
                WHERE (overview IS NULL OR overview = '') 
                  AND (small_overview IS NULL OR small_overview = '')
            ''')
            empty = cursor.fetchone()[0]

            counts = {
                'total': total,
                'main_only': main_only,
                'small_only': small_only,
                'both': both,
                'empty': empty
            }

            if self.debug:
                safe_print(f"{Icons.INFO} Overview counts: {counts}", COLORS["blue"])

            return counts

    def search_overviews(self, search_term: str, search_in: str = "both") -> List[Dict[str, Any]]:
        """Search for overviews containing the search term."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                search_pattern = f"%{search_term}%"

                if search_in == "main":
                    cursor.execute('''
                        SELECT * FROM overview 
                        WHERE overview LIKE ?
                        ORDER BY unique_name
                    ''', (search_pattern,))
                elif search_in == "small":
                    cursor.execute('''
                        SELECT * FROM overview 
                        WHERE small_overview LIKE ?
                        ORDER BY unique_name
                    ''', (search_pattern,))
                else:  # search in both
                    cursor.execute('''
                        SELECT * FROM overview 
                        WHERE overview LIKE ? OR small_overview LIKE ?
                        ORDER BY unique_name
                    ''', (search_pattern, search_pattern))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Search failed: {e}", COLORS["red"])
            return []

    def get_unique_names(self) -> list:
        """Get a list of all unique names from the companies table.

        :return: List of unique names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT unique_name unique_name FROM overview')
            results = cursor.fetchall()
            return [row[0] for row in results]


class SummaryTable:
    """Handles operations for the summary table."""

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
        """Create the summary table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_name TEXT UNIQUE NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (unique_name) REFERENCES companies (unique_name) ON DELETE CASCADE
                )
            ''')

    def insert_summary(
            self,
            unique_name: str,
            summary: str,
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert or update summary.

        Args:
            unique_name: Unique identifier for the company
            summary: Summary text (required, must be unique)
            replace: If True, replace existing summary with same unique_name (default: False)

        Returns:
            Summary data if successful
        """
        # Check if a summary with the same unique_name already exists
        existing_summary = self._get_summary_by_unique_name(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If replace is True and a summary with the same unique_name exists, update it
                if replace and existing_summary:
                    cursor.execute('''
                        UPDATE summary 
                        SET summary = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE unique_name = ?
                    ''', (summary, unique_name))
                    conn.commit()
                    self._print_important(f"{Icons.UPDATE} Updated summary: {unique_name}", COLORS["green"])
                    return self._get_summary_by_unique_name(unique_name)

                # If replace is False and a summary with the same unique_name exists, return it
                elif existing_summary and not replace:
                    self._print_important(f"{Icons.WARNING} Summary already exists: {unique_name}", COLORS["yellow"])
                    return existing_summary

                # Insert new summary
                else:
                    cursor.execute('''
                        INSERT INTO summary 
                        (unique_name, summary)
                        VALUES (?, ?)
                    ''', (unique_name, summary))
                    conn.commit()
                    self._print_important(f"{Icons.SUCCESS} Inserted summary: {unique_name}", COLORS["green"])
                    return self._get_summary_by_unique_name(unique_name)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return existing_summary or {}

    def _get_summary_by_unique_name(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get summary by unique_name."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summary WHERE unique_name = ?', (unique_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_summary(self, unique_name: str) -> bool:
        """Delete summary by unique_name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM summary WHERE unique_name = ?', (unique_name,))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.TRASH} Deleted summary: {unique_name}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Summary not found: {unique_name}", COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def update_summary(self, unique_name: str, summary: str) -> bool:
        """Update summary for a company."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE summary 
                    SET summary = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE unique_name = ?
                ''', (summary, unique_name))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.UPDATE} Updated summary: {unique_name}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Summary update failed - not found: {unique_name}",
                                          COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", COLORS["red"])
            return False

    def get_summary(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get full summary data by unique_name."""
        return self._get_summary_by_unique_name(unique_name)

    def get_summary_text(self, unique_name: str) -> Optional[str]:
        """Get only the summary text by unique_name."""
        summary_data = self._get_summary_by_unique_name(unique_name)
        return summary_data.get('summary') if summary_data else None

    def get_all_summaries(self, include_empty: bool = False) -> List[Dict[str, Any]]:
        """Get all summaries from the database."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if include_empty:
                    cursor.execute('SELECT * FROM summary ORDER BY unique_name')
                else:
                    cursor.execute('''
                        SELECT * FROM summary 
                        WHERE summary IS NOT NULL AND summary != ''
                        ORDER BY unique_name
                    ''')

                rows = cursor.fetchall()
                summaries = [dict(row) for row in rows]
                return summaries

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Error getting summaries: {e}", COLORS["red"])
            return []

    def get_summaries_count(self) -> Dict[str, int]:
        """Get counts of summaries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Count total summaries
            cursor.execute('SELECT COUNT(*) FROM summary')
            total = cursor.fetchone()[0]

            # Count non-empty summaries
            cursor.execute('SELECT COUNT(*) FROM summary WHERE summary IS NOT NULL AND summary != ""')
            non_empty = cursor.fetchone()[0]

            # Count empty summaries
            empty = total - non_empty

            counts = {
                'total': total,
                'non_empty': non_empty,
                'empty': empty
            }

            if self.debug:
                safe_print(f"{Icons.INFO} Summary counts: {counts}", COLORS["blue"])

            return counts

    def search_summaries(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for summaries containing the search term."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                search_pattern = f"%{search_term}%"
                cursor.execute('''
                    SELECT * FROM summary 
                    WHERE summary LIKE ?
                    ORDER BY unique_name
                ''', (search_pattern,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Search failed: {e}", COLORS["red"])
            return []

    def summary_exists(self, unique_name: str) -> bool:
        """Check if a summary exists for the given unique_name."""
        return self.get_summary_text(unique_name) is not None

    def get_unique_names(self) -> list:
        """Get a list of all unique names from the companies table.

        :return: List of unique names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT unique_name unique_name FROM summary')
            results = cursor.fetchall()
            return [row[0] for row in results]





