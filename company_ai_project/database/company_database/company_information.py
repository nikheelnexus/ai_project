import sqlite3
import requests
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import os
from company_ai_project import saved_data

database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'company_information_database.db'
)

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class Icons:
    """Unicode icons for status messages."""
    SUCCESS = '✅'
    ERROR = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    DATABASE = '💾'


class CompanyInformationTable:
    """Handles operations for the company_information table with separate columns for each data field."""

    def __init__(self, db_path: str=database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        # Define the schema for the specific company_data fields
        self.field_definitions = {
            'product_range': 'TEXT',  # JSON array
            'product_list': 'TEXT',  # JSON array of objects
            'industry': 'TEXT',  # JSON array
            'certifications': 'TEXT',  # JSON array
            'contact_email': 'TEXT',  # JSON array
            'country': 'TEXT',  # JSON array
            'city': 'TEXT',  # JSON array
            'office_location': 'TEXT',
            'office_country': 'TEXT'
        }
        self.create_table()
        # self._print_important(f"{Icons.DATABASE} CompanyInformationTable initialized", Colors.BLUE)

    def _print_important(self, message: str, color: str = Colors.RESET) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            print(f"{color}{message}{Colors.RESET}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with WAL mode enabled."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False  # Only if using multiple threads
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds timeout
        return conn

    def create_table(self) -> None:
        """Create the company_information table with separate columns for each field."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create table with all fields
            columns_sql = []
            columns_sql.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
            columns_sql.append("unique_name TEXT UNIQUE NOT NULL")

            # Add all defined fields as columns
            for field_name, field_type in self.field_definitions.items():
                columns_sql.append(f"{field_name} {field_type}")

            # Add timestamp columns
            columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns_sql.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            # Add JSON backup column (optional, for backward compatibility)
            columns_sql.append("company_data_json TEXT")

            # Create the table
            create_sql = f'''
                CREATE TABLE IF NOT EXISTS company_information (
                    {', '.join(columns_sql)},
                    FOREIGN KEY (unique_name) REFERENCES companies (unique_name) ON DELETE CASCADE
                )
            '''

            cursor.execute(create_sql)

            # Create indexes for frequently searched fields
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_unique_name ON company_information(unique_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON company_information(country)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry ON company_information(industry)')

        # self._print_important(f"{Icons.SUCCESS} Company information table with separate columns ready", Colors.GREEN)

    def _convert_value_for_storage(self, value: Any) -> Union[str, None]:
        """Convert values for storage in SQLite."""
        if value is None:
            return None
        elif isinstance(value, (list, dict)):
            return json.dumps(value) if value else None
        else:
            return str(value)

    def _parse_stored_value(self, value: Any, field_name: str) -> Any:
        """Parse stored values back to original format."""
        if value is None:
            return None

        # All specified fields contain JSON array data
        if value and field_name in self.field_definitions:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If it's not valid JSON, return as string
                return value
        return value

    def insert_company_information(
            self,
            unique_name: str,
            company_data: Dict[str, Any],
            replace: bool = False
    ) -> Dict[str, Any]:
        """
        Insert new company information into the database.

        Args:
            unique_name: Unique identifier for the company
            company_data: Company information data as dict
            replace: If True, replace existing company information with same unique_name (default: False)

        Returns:
            Company information data if successful
        """
        # Check if company information with the same unique_name already exists
        existing_info = self._get_company_information_by_unique_name(unique_name)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Prepare column values
                columns = ['unique_name']
                placeholders = ['?']
                values = [unique_name]

                # Add all fields from company_data
                for field in self.field_definitions.keys():
                    value = company_data.get(field)
                    stored_value = self._convert_value_for_storage(value)
                    columns.append(field)
                    placeholders.append('?')
                    values.append(stored_value)

                # Add JSON backup
                company_data_json = json.dumps(company_data)
                columns.append('company_data_json')
                placeholders.append('?')
                values.append(company_data_json)

                # If replace is True and company information with the same unique_name exists, update it
                if replace and existing_info:
                    # Build update SQL
                    update_fields = []
                    update_values = []
                    for field in self.field_definitions.keys():
                        value = company_data.get(field)
                        stored_value = self._convert_value_for_storage(value)
                        update_fields.append(f"{field} = ?")
                        update_values.append(stored_value)

                    # Add JSON backup and updated_at
                    update_fields.append("company_data_json = ?")
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    update_values.append(company_data_json)
                    update_values.append(unique_name)

                    update_sql = f'''
                        UPDATE company_information 
                        SET {', '.join(update_fields)}
                        WHERE unique_name = ?
                    '''

                    cursor.execute(update_sql, update_values)
                    conn.commit()
                    self._print_important(f"{Icons.SUCCESS} UPDATED company information: {unique_name}", Colors.GREEN)
                    return self._get_company_information_by_unique_name(unique_name)

                # If replace is False and company information with the same unique_name exists, return it
                elif existing_info and not replace:
                    self._print_important(f"{Icons.WARNING} Company information already exists: {unique_name}",
                                          Colors.YELLOW)
                    return existing_info

                # Insert new company information
                else:
                    insert_sql = f'''
                        INSERT INTO company_information 
                        ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    '''

                    cursor.execute(insert_sql, values)
                    conn.commit()
                    self._print_important(f"{Icons.SUCCESS} INSERTED company information: {unique_name}", Colors.GREEN)
                    return self._get_company_information_by_unique_name(unique_name)

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error: {e}", Colors.RED)
            return existing_info or {}

    def _get_company_information_by_unique_name(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get company information by unique_name."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM company_information WHERE unique_name = ?', (unique_name,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse stored values back to original format
                for field in self.field_definitions.keys():
                    if field in result:
                        result[field] = self._parse_stored_value(result[field], field)

                # Parse JSON backup if needed
                if 'company_data_json' in result and result['company_data_json']:
                    try:
                        result['company_data'] = json.loads(result['company_data_json'])
                    except json.JSONDecodeError:
                        result['company_data'] = result['company_data_json']

                return result
            return None

    def delete_company_information(self, unique_name: str) -> bool:
        """Delete company information by unique_name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM company_information WHERE unique_name = ?', (unique_name,))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.SUCCESS} DELETED company information: {unique_name}", Colors.GREEN)
                else:
                    self._print_important(f"{Icons.WARNING} Company information not found: {unique_name}",
                                          Colors.YELLOW)
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Delete failed: {e}", Colors.RED)
            return False

    def update_company_information(self, unique_name: str, company_data: Dict[str, Any]) -> bool:
        """Update company information by unique_name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build update SQL
                update_fields = []
                update_values = []

                for field in self.field_definitions.keys():
                    value = company_data.get(field)
                    stored_value = self._convert_value_for_storage(value)
                    update_fields.append(f"{field} = ?")
                    update_values.append(stored_value)

                # Add JSON backup and updated_at
                company_data_json = json.dumps(company_data)
                update_fields.append("company_data_json = ?")
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(company_data_json)
                update_values.append(unique_name)

                update_sql = f'''
                    UPDATE company_information 
                    SET {', '.join(update_fields)}
                    WHERE unique_name = ?
                '''

                cursor.execute(update_sql, update_values)
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self._print_important(f"{Icons.SUCCESS} UPDATED company information: {unique_name}", Colors.GREEN)
                else:
                    self._print_important(
                        f"{Icons.WARNING} Company information update failed - not found: {unique_name}", Colors.YELLOW)
                return success
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Update failed: {e}", Colors.RED)
            return False

    def get_company_information(self, unique_name: str) -> Optional[Dict[str, Any]]:
        """Get company information by unique_name."""
        result = self._get_company_information_by_unique_name(unique_name)
        return result

    def get_all_company_information(self) -> List[Dict[str, Any]]:
        """Get all company information records."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM company_information')
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                # Parse stored values back to original format
                for field in self.field_definitions.keys():
                    if field in result:
                        result[field] = self._parse_stored_value(result[field], field)

                # Parse JSON backup if needed
                if 'company_data_json' in result and result['company_data_json']:
                    try:
                        result['company_data'] = json.loads(result['company_data_json'])
                    except json.JSONDecodeError:
                        result['company_data'] = result['company_data_json']

                results.append(result)

            return results

    def search_company_information_by_text(
            self,
            search_text: str,
            case_sensitive: bool = False,
            search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search company information by text across specific fields.

        Args:
            search_text: Text to search for
            case_sensitive: If True, perform case-sensitive search (default: False)
            search_fields: List of specific fields to search within.
                          If None, searches all string fields.

        Returns:
            List of matching company information records as dictionaries
        """
        if not search_text:
            #self._print_important(f"{Icons.WARNING} Empty search text provided", Colors.YELLOW)
            return []

        # If no specific fields provided, search all fields
        if search_fields is None:
            search_fields = list(self.field_definitions.keys())

        # Filter only fields that exist in our table
        valid_fields = [field for field in search_fields if field in self.field_definitions]
        if not valid_fields:
            self._print_important(f"{Icons.WARNING} No valid search fields provided", Colors.YELLOW)
            return []

        all_companies = self.get_all_company_information()
        matches = []

        # Normalize search text
        if not case_sensitive:
            search_text = search_text.lower()

        for company in all_companies:
            found_match = False

            for field in valid_fields:
                if field in company and company[field]:
                    field_value = company[field]

                    # Handle different field types
                    if isinstance(field_value, str):
                        text_to_search = field_value if case_sensitive else field_value.lower()
                        if search_text in text_to_search:
                            found_match = True
                            break

                    elif isinstance(field_value, list):
                        # Search in lists
                        for item in field_value:
                            if isinstance(item, str):
                                text_to_search = item if case_sensitive else item.lower()
                                if search_text in text_to_search:
                                    found_match = True
                                    break
                            elif isinstance(item, dict):
                                # Search in dictionaries (e.g., product_list items)
                                for key, value in item.items():
                                    if isinstance(value, str):
                                        text_to_search = value if case_sensitive else value.lower()
                                        if search_text in text_to_search:
                                            found_match = True
                                            break
                                if found_match:
                                    break
                        if found_match:
                            break

            if found_match:
                matches.append(company)

        self._print_important(f"{Icons.INFO} Found {len(matches)} matches for: '{search_text}'", Colors.BLUE)
        return matches

    def search_companies_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Search companies by country."""
        all_companies = self.get_all_company_information()
        matches = []
        country_lower = country.lower()

        for company in all_companies:
            if 'country' in company and company['country']:
                country_list = company['country']
                if isinstance(country_list, list):
                    for c in country_list:
                        if isinstance(c, str) and c.lower() == country_lower:
                            matches.append(company)
                            break

        return matches

    def search_companies_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """Search companies by industry."""
        all_companies = self.get_all_company_information()
        matches = []
        industry_lower = industry.lower()

        for company in all_companies:
            if 'industry' in company and company['industry']:
                industry_list = company['industry']
                if isinstance(industry_list, list):
                    for i in industry_list:
                        if isinstance(i, str) and i.lower() == industry_lower:
                            matches.append(company)
                            break

        return matches

    def get_companies_with_certification(self, certification: str) -> List[Dict[str, Any]]:
        """Get companies with specific certification."""
        all_companies = self.get_all_company_information()
        matches = []
        cert_lower = certification.lower()

        for company in all_companies:
            if 'certifications' in company and company['certifications']:
                cert_list = company['certifications']
                if isinstance(cert_list, list):
                    for c in cert_list:
                        if isinstance(c, str) and c.lower() == cert_lower:
                            matches.append(company)
                            break

        return matches

    def add_field(self, field_name: str, field_type: str = 'TEXT') -> bool:
        """
        Add a new field to the table dynamically.

        Args:
            field_name: Name of the field to add
            field_type: SQLite data type (default: TEXT)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'ALTER TABLE company_information ADD COLUMN {field_name} {field_type}')

                # Update field definitions
                self.field_definitions[field_name] = field_type

                self._print_important(f"{Icons.SUCCESS} Added field '{field_name}' to table", Colors.GREEN)
                return True
        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Failed to add field: {e}", Colors.RED)
            return False

    def get_column_values(
            self,
            column_name: str,
            unique_only: bool = False,
            flatten_lists: bool = False,
            remove_none: bool = True,
            sort_results: bool = False
    ) -> List[Any]:
        """
        Get all values for a specific column with various options.

        Args:
            column_name: Name of the column to retrieve values from
            unique_only: If True, return only unique values (default: False)
            flatten_lists: If True, flatten list columns into individual items (default: False)
            remove_none: If True, remove None/null values (default: True)
            sort_results: If True, sort the results (default: False)

        Returns:
            List of all values from the specified column

        Raises:
            ValueError: If column_name is not a valid column
        """
        # Validate column name
        valid_columns = list(self.field_definitions.keys()) + \
                        ['unique_name', 'id', 'created_at', 'updated_at', 'company_data_json']

        if column_name not in valid_columns:
            raise ValueError(
                f"Invalid column name: '{column_name}'. "
                f"Valid columns are: {valid_columns}"
            )

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Construct SQL query
                if unique_only:
                    sql = f'SELECT DISTINCT {column_name} FROM company_information'
                else:
                    sql = f'SELECT {column_name} FROM company_information'

                cursor.execute(sql)
                rows = cursor.fetchall()

                # Extract and process values
                values = []
                for row in rows:
                    value = row[0]

                    # Skip None/null values if requested
                    if remove_none and value is None:
                        continue
                    if remove_none and value == "":
                        continue

                    # Parse JSON values if needed
                    if column_name in self.field_definitions and value:
                        parsed_value = self._parse_stored_value(value, column_name)

                        if flatten_lists and isinstance(parsed_value, list):
                            # Flatten the list into individual items
                            for item in parsed_value:
                                if not remove_none or (item is not None and item != ""):
                                    values.append(item)
                        else:
                            values.append(parsed_value)
                    elif value is not None:
                        values.append(value)

                # Sort if requested
                if sort_results:
                    try:
                        values.sort()
                    except TypeError:
                        # If values are not comparable (e.g., mixed types), skip sorting
                        pass

                return values

        except sqlite3.Error as e:
            self._print_important(
                f"{Icons.ERROR} Database error getting values for column '{column_name}': {e}",
                Colors.RED
            )
            return []

    def get_column_statistics(self, column_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            column_name: Name of the column to analyze

        Returns:
            Dictionary with column statistics
        """
        values = self.get_column_values(
            column_name,
            unique_only=False,
            flatten_lists=True,
            remove_none=True
        )

        unique_values = self.get_column_values(
            column_name,
            unique_only=True,
            flatten_lists=True,
            remove_none=True
        )

        stats = {
            'column_name': column_name,
            'total_count': len(values),
            'unique_count': len(set(str(v) for v in values)),  # Convert to string for hashing
            'empty_count': sum(1 for v in values if v in [None, ""]),
            'unique_values_sample': unique_values[:10],  # First 10 unique values
            'most_common': None,
            'data_type': None
        }

        # Determine most common value (excluding None/empty)
        if values:
            from collections import Counter
            counter = Counter(str(v) for v in values if v not in [None, ""])
            if counter:
                most_common = counter.most_common(1)[0]
                stats['most_common'] = {
                    'value': most_common[0],
                    'count': most_common[1]
                }

            # Determine data type
            sample_value = next((v for v in values if v not in [None, ""]), None)
            if sample_value:
                stats['data_type'] = type(sample_value).__name__

        return stats

    # Example usage methods for common columns:
    def get_all_countries(self, unique_only: bool = True) -> List[str]:
        """Get all countries (flattened from lists)."""
        values = self.get_column_values(
            'country',
            unique_only=unique_only,
            flatten_lists=True,
            remove_none=True,
            sort_results=True
        )
        # Filter to ensure only strings
        final = [v for v in values if isinstance(v, str)]
        final = list(set(final))
        final.sort()
        return final

    def get_all_industries(self, unique_only: bool = True) -> List[str]:
        """Get all industries (flattened from lists)."""
        values = self.get_column_values(
            'industry',
            unique_only=unique_only,
            flatten_lists=True,
            remove_none=True,
            sort_results=True
        )
        # Filter to ensure only strings
        final = [v for v in values if isinstance(v, str)]
        final = list(set(final))
        final.sort()
        return final

    def get_all_certifications(self, unique_only: bool = True) -> List[str]:
        """Get all certifications (flattened from lists)."""
        values = self.get_column_values(
            'certifications',
            unique_only=unique_only,
            flatten_lists=True,
            remove_none=True,
            sort_results=True
        )
        # Filter to ensure only strings
        final = [v for v in values if isinstance(v, str)]
        final = list(set(final))
        final.sort()
        return final

    def get_all_cities(self, unique_only: bool = True) -> List[str]:
        """Get all cities (flattened from lists)."""
        values = self.get_column_values(
            'city',
            unique_only=unique_only,
            flatten_lists=True,
            remove_none=True,
            sort_results=True
        )
        # Filter to ensure only strings
        final = [v for v in values if isinstance(v, str)]
        final = list(set(final))
        final.sort()
        return final

    def get_all_product_names(self, unique_only: bool = True) -> List[str]:
        """
        Get all product names from product_list.

        Args:
            unique_only: If True, return only unique product names

        Returns:
            List of product names
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT product_list FROM company_information WHERE product_list IS NOT NULL AND product_list != ""')
                rows = cursor.fetchall()

                product_names = []
                for row in rows:
                    product_list_json = row[0]
                    if product_list_json:
                        try:
                            product_list = json.loads(product_list_json)
                            if isinstance(product_list, list):
                                for product in product_list:
                                    if isinstance(product, dict) and 'name' in product:
                                        product_name = product['name']
                                        if product_name and (not unique_only or product_name not in product_names):
                                            product_names.append(product_name)
                        except json.JSONDecodeError:
                            continue

                if unique_only:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_list = []
                    for name in product_names:
                        if name not in seen:
                            seen.add(name)
                            unique_list.append(name)
                    return unique_list

                return product_names

        except sqlite3.Error as e:
            self._print_important(f"{Icons.ERROR} Database error getting product names: {e}", Colors.RED)
            return []

    def get_all_product_ranges(self, unique_only: bool = True) -> List[str]:
        """Get all product ranges (flattened from lists)."""
        values = self.get_column_values(
            'product_range',
            unique_only=unique_only,
            flatten_lists=True,
            remove_none=True,
            sort_results=True
        )
        # Filter to ensure only strings
        final = [v for v in values if isinstance(v, str)]
        final = list(set(final))
        final.sort()
        return final