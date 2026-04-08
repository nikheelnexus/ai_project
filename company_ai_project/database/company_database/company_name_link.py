import sqlite3
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid, os
from common_script import website_script, common
from threading import Lock

from company_ai_project import saved_data

database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'company_name_link.db'
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
    COMPANY = '🏢'
    WEBSITE = '🌐'
    SEARCH = '🔍'
    TRASH = '🗑️'
    UPDATE = '🔄'
    VALIDATION = '🔍'


class CompanyNameLink:
    """Handles operations for the companies table with name link functionality."""

    def __init__(self, db_path: str = database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_company_table()

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

    def create_company_table(self) -> None:
        """Create the companies table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    unique_name TEXT UNIQUE,
                    company_name TEXT,
                    website TEXT,
                    domain TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')

    def _extract_domain(self, website: str) -> str:
        """Extract domain from website URL."""
        if not website:
            return ""
        website = website.lower().replace("https://", "").replace("http://", "").replace("www.", "")
        return website.split('/')[0]

    def _check_website_valid(self, website: str) -> bool:
        """Check if website link is working using website_script.check_link_status()."""
        if not website:
            return False
        try:
            # Use your existing website_script method
            is_working, status_info = website_script.check_link_status(website)
            if not is_working:
                self._print_important(f"{Icons.ERROR} Website invalid: {website} - {status_info}", COLORS["red"])
            return is_working
        except Exception as e:
            if self.debug:
                self._print_important(f"{Icons.ERROR} Error checking website {website}: {e}", COLORS["red"])
            return False

    def generate_unique_name(self, company_name: str, website: str) -> str:
        """Generate unique name from company name and website."""
        company_slug = company_name.lower().replace(' ', '-').replace('.', '')
        domain = self._extract_domain(website)
        return f"{company_slug}-{domain}"

    def _get_company_by_website(self, website: str) -> Optional[Dict[str, Any]]:
        """Get company by website."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies WHERE website = ?', (website,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_company(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get company by unique name."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies WHERE unique_name = ?', (unique_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_company_by_unique_name(
            self,
            unique_name: str,
            company_name: Optional[str] = None,
            website: Optional[str] = None,
            domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a company's information using unique_name as identifier.

        Args:
            unique_name: The unique identifier of the company to update
            company_name: New company name (optional, keep existing if None)
            website: New website URL (optional, keep existing if None)
            domain: New domain (optional, auto-extracted from website if not provided)

        Returns:
            Updated company data if successful, empty dict if not found
        """
        # First check if company exists
        existing_company = self.get_company(unique_name)
        if not existing_company:
            self._print_important(
                f"{Icons.ERROR} Company with unique_name '{unique_name}' not found",
                COLORS["red"]
            )
            return {}

        # Use existing values if new ones not provided
        new_company_name = company_name if company_name is not None else existing_company['company_name']
        new_website = website if website is not None else existing_company['website']

        # Format and validate website if it's being updated
        if website is not None:
            formatted_website = website_script.format_website_url(new_website)
            if not formatted_website:
                self._print_important(f"{Icons.ERROR} Invalid website format: {new_website}", COLORS["red"])
                return {}
            new_website = formatted_website

            # Optionally validate the new website
            if not self._check_website_valid(new_website):
                self._print_important(
                    f"{Icons.WARNING} New website may not be valid: {new_website}",
                    COLORS["yellow"]
                )

        # Extract domain if needed
        if domain is not None:
            new_domain = domain
        elif new_website:
            new_domain = self._extract_domain(new_website)
        else:
            new_domain = existing_company.get('domain', '')

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE companies 
                    SET company_name = ?, website = ?, domain = ?, updated_at = ?
                    WHERE unique_name = ?
                ''', (new_company_name, new_website, new_domain, datetime.now(), unique_name))

                conn.commit()

                if cursor.rowcount > 0:
                    self._print_important(
                        f"{Icons.UPDATE} Updated company: {unique_name} -> {new_company_name}",
                        COLORS["green"]
                    )
                    return self.get_company(unique_name)
                else:
                    self._print_important(
                        f"{Icons.ERROR} Failed to update company: {unique_name}",
                        COLORS["red"]
                    )
                    return {}

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return {}


    def insert_company(
            self,
            company_name: str,
            website: str,
            unique_name: str = '',
            domain: Optional[str] = None,
            replace: bool = False
    ) -> dict:
        """
        Insert a new company into the database_old.

        Args:
            company_name: Name of the company
            website: Company website URL
            unique_name: Unique identifier for the company (optional, will be generated if not provided)
            domain: Domain extracted from website (optional)
            replace: If True, replace existing company with same website (default: False)

        Returns:
            Company data if successful, empty dict if website invalid
        """
        if not company_name:
            self._print_important(f"{Icons.ERROR} Company name is required", COLORS["red"])
            return {}
        formatted_website = website_script.format_website_url(website)
        if not formatted_website:
            self._print_important(f"{Icons.ERROR} Invalid website format: {website}", COLORS["red"])
            return {}

        # Only validate website for NEW companies (not existing ones)
        if not self._get_company_by_website(formatted_website):
            # Check if website is valid
            if not self._check_website_valid(formatted_website):
                self._print_important(f"{Icons.ERROR} Website not valid/working: {formatted_website}", COLORS["red"])
                return {}  # Return empty dict to indicate failure

        # Rest of the code remains the same
        if not domain and formatted_website:
            domain = self._extract_domain(formatted_website)
        if not unique_name:
            unique_name = self.generate_unique_name(company_name, formatted_website)

        # Check if a company with the same website already exists
        existing_company_by_website = self._get_company_by_website(formatted_website)

        # Also check by unique_name for backward compatibility
        existing_company_by_unique_name = self.get_company(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # If replace is True and a company with the same website exists, update it
                if replace and existing_company_by_website:
                    cursor.execute('''
                        UPDATE companies 
                        SET company_name = ?, unique_name = ?, domain = ?, updated_at = ?
                        WHERE website = ?
                    ''', (company_name, unique_name, domain, datetime.now(), formatted_website))
                    conn.commit()
                    self._print_important(f"{Icons.UPDATE} Updated company: {company_name} -> {formatted_website}",
                                          COLORS["green"])
                    return self._get_company_by_website(formatted_website)

                # If replace is False and a company with the same website exists, return it
                elif existing_company_by_website and not replace:
                    self._print_important(
                        f"{Icons.WARNING} Company already exists: {company_name} -> {formatted_website}",
                        COLORS["yellow"])
                    return existing_company_by_website

                # If no company with same website exists, but one with same unique_name exists
                elif existing_company_by_unique_name and not replace:
                    self._print_important(f"{Icons.WARNING} Company with unique name exists: {unique_name}",
                                          COLORS["yellow"])
                    return existing_company_by_unique_name

                # Insert new company
                else:
                    company_id = str(uuid.uuid4())
                    now = datetime.now()

                    cursor.execute('''
                        INSERT INTO companies 
                        (id, unique_name, company_name, website, domain, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (company_id, unique_name, company_name, formatted_website, domain, now, now))
                    conn.commit()

                    self._print_important(f"{Icons.SUCCESS} Inserted new company: {company_name} ({unique_name})",
                                          COLORS["green"])
                    return self.get_company(unique_name)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", COLORS["red"])
            return existing_company_by_website or existing_company_by_unique_name or {}

    def delete_company(self, identifier: str) -> bool:
        """Delete company by unique_name or website."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Try to delete by unique_name first, then by website
                cursor.execute('DELETE FROM companies WHERE unique_name = ? OR website = ?',
                               (identifier, identifier))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.TRASH} Deleted company: {identifier}", COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Company not found: {identifier}", COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", COLORS["red"])
            return False

    def update_company(self, identifier: str, company_name: str, website: str,
                       domain: Optional[str] = None) -> bool:
        """Update company by unique_name or website."""
        formatted_website = website_script.format_website_url(website)
        if not formatted_website:
            self._print_important(f"{Icons.ERROR} Invalid website format: {website}", COLORS["red"])
            return False

        # Validate website using your method
        if formatted_website and not self._check_website_valid(formatted_website):
            formatted_website = ""  # Make it blank if not working

        if not domain and formatted_website:
            domain = self._extract_domain(formatted_website)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE companies 
                    SET company_name = ?, website = ?, domain = ?, updated_at = ?
                    WHERE unique_name = ? OR website = ?
                ''', (company_name, formatted_website, domain, datetime.now(), identifier, identifier))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.UPDATE} Updated company: {identifier} -> {company_name}",
                                          COLORS["green"])
                else:
                    self._print_important(f"{Icons.WARNING} Update failed - company not found: {identifier}",
                                          COLORS["yellow"])
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", COLORS["red"])
            return False

    def check_website_status(self, website: str) -> tuple[bool, Dict[str, Any]]:
        """
        Check website status using your existing website_script method.

        Args:
            website: The URL to check

        Returns:
            Tuple of (is_working, status_info)
        """
        try:
            is_working, status_info = website_script.check_link_status(website)
            if is_working:
                self._print_important(f"{Icons.SUCCESS} Website accessible: {website}", COLORS["green"])
            else:
                self._print_important(f"{Icons.ERROR} Website inaccessible: {website} - {status_info}", COLORS["red"])
            return is_working, status_info
        except Exception as e:
            if self.debug:
                self._print_important(f"{Icons.ERROR} Error in check_website_status: {e}", COLORS["red"])
            return False, {"error": str(e)}

    def validate_all_websites(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate all company websites in the database_old and return results.

        Returns:
            Dictionary with 'valid' and 'invalid' lists of company data
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies WHERE website IS NOT NULL AND website != ""')
                rows = cursor.fetchall()
                companies = [dict(row) for row in rows]

                valid_companies = []
                invalid_companies = []

                self._print_important(f"{Icons.VALIDATION} Validating {len(companies)} company websites...",
                                      COLORS["blue"])

                for company in companies:
                    if self._check_website_valid(company['website']):
                        valid_companies.append(company)
                    else:
                        invalid_companies.append(company)

                if invalid_companies:
                    self._print_important(f"{Icons.WARNING} Found {len(invalid_companies)} invalid websites",
                                          COLORS["yellow"])
                    for invalid_company in invalid_companies[:3]:  # Show first 3 invalid
                        self._print_important(
                            f"   {Icons.ERROR} {invalid_company['company_name']} -> {invalid_company['website']}",
                            COLORS["red"])
                    if len(invalid_companies) > 3:
                        self._print_important(f"   ... and {len(invalid_companies) - 3} more invalid websites",
                                              COLORS["gray"])

                self._print_important(
                    f"{Icons.SUCCESS} Validation complete: {len(valid_companies)} valid, {len(invalid_companies)} invalid",
                    COLORS["green"])

                return {
                    "valid": valid_companies,
                    "invalid": invalid_companies
                }

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error in validate_all_websites: {e}", COLORS["red"])
            return {"valid": [], "invalid": []}

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get all companies with full details.

        Returns:
            List of company dictionaries with all details
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies ORDER BY company_name')
                rows = cursor.fetchall()
                companies = [dict(row) for row in rows]

                return companies

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Error getting companies: {e}", COLORS["red"])
            return []

    def search_companies(self, search_text: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search companies based on text across multiple fields.

        Args:
            search_text: Text to search for
            search_fields: List of fields to search in. If None, searches all fields.
                         Options: ['company_name', 'unique_name', 'website', 'domain']

        Returns:
            List of matching company dictionaries
        """
        if not search_text:
            # self._print_important(f"{Icons.WARNING} Empty search text provided", COLORS["yellow"])
            return []

        # Default fields to search if not specified
        if search_fields is None:
            search_fields = ['company_name', 'unique_name', 'website', 'domain']

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build the WHERE clause with multiple OR conditions
                where_conditions = []
                params = []

                for field in search_fields:
                    if field in ['company_name', 'unique_name', 'website', 'domain']:
                        where_conditions.append(f"{field} LIKE ?")
                        params.append(f'%{search_text}%')

                if not where_conditions:
                    # self._print_important(f"{Icons.ERROR} No valid search fields specified", COLORS["red"])
                    return []

                where_clause = " OR ".join(where_conditions)
                query = f'SELECT * FROM companies WHERE {where_clause} ORDER BY company_name'

                cursor.execute(query, params)
                rows = cursor.fetchall()
                companies = [dict(row) for row in rows]

                return companies

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Error searching companies: {e}", COLORS["red"])
            return []

    def get_companies_count(self) -> int:
        """Get total number of companies in the database_old."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM companies')
            count = cursor.fetchone()[0]
            if self.debug:
                self._print_important(f"{Icons.INFO} Total companies in database_old: {count}", COLORS["blue"])
            return count

    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company by ID."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies WHERE id = ?', (company_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_companies_by_date(self, limit: int = None, order_by: str = 'DESC', sort_by: str = 'updated_at') -> List[
        Dict[str, Any]]:
        """
        Get list of companies ordered by date (latest updated first by default)

        :param limit: Optional limit on number of companies to return
        :param order_by: 'DESC' for latest first, 'ASC' for oldest first
        :param sort_by: 'created_at' or 'updated_at' (default: 'updated_at')
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = f'''
                SELECT id, unique_name, company_name, website, domain, 
                       created_at, updated_at
                FROM companies
                ORDER BY {sort_by} {order_by}
            '''

            if limit is not None:
                query += f' LIMIT {limit}'

            cursor.execute(query)
            rows = cursor.fetchall()

            companies = []
            for row in rows:
                company_dict = {
                    'id': row[0],
                    'unique_name': row[1],
                    'company_name': row[2],
                    'website': row[3],
                    'domain': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                }
                companies.append(company_dict)

            return companies
