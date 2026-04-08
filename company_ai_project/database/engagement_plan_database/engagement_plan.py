import sqlite3
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import os
from company_ai_project import saved_data
from common_script import common

database = os.path.join(
    os.path.abspath(os.path.dirname(saved_data.__file__)),
    'engagement_plan.db'
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


class EngagementPlanDatabase:
    """Main database handler for engagement plans with multiple related tables."""

    def __init__(self, db_path: str = database, debug: bool = True) -> None:
        self.db_path = db_path
        self.debug = debug
        self.create_all_tables()
        self._print_important(f"{Icons.DATABASE} EngagementPlanDatabase initialized", Colors.BLUE)

    def _print_important(self, message: str, color: str = Colors.RESET) -> None:
        """Print important debug message if debug mode is enabled."""
        if self.debug:
            print(f"{color}{message}{Colors.RESET}")

    def _normalize_website(self, website: str) -> str:
        """Normalize website URL for consistent storage."""
        if not website:
            return ""
        website = common.format_website_url(website)
        return website

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with WAL mode enabled."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_json_string(self, data: Union[Dict, List, str]) -> str:
        """Ensure data is a JSON string for storage."""
        if isinstance(data, (dict, list)):
            try:
                return json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Failed to serialize data to JSON: {e}")
        elif isinstance(data, str):
            try:
                json.loads(data)
                return data
            except json.JSONDecodeError:
                try:
                    return json.dumps(data, ensure_ascii=False)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Failed to serialize data to JSON: {e}")
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    def _parse_json_from_db(self, data: str) -> Union[Dict, List, str]:
        """Parse JSON string from database."""
        if not isinstance(data, str):
            return data

        try:
            parsed = data
            while isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except json.JSONDecodeError:
                    break
            return parsed
        except Exception as e:
            self._print_important(
                f"{Icons.WARNING} Failed to parse JSON: {e}",
                Colors.YELLOW
            )
            return data

    def create_all_tables(self) -> None:
        """Create all necessary tables for the engagement plan system."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create engagement_plans table (main table)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS engagement_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_website TEXT NOT NULL,
                    company_website TEXT NOT NULL,
                    client_name TEXT,
                    user_company TEXT,
                    plan_meta_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_website, company_website)
                )
            ''')

            # Create phases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_plan_id INTEGER NOT NULL,
                    phase_number INTEGER NOT NULL,
                    phase_name TEXT NOT NULL,
                    duration_weeks INTEGER,
                    objective TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_plan_id) REFERENCES engagement_plans(id) ON DELETE CASCADE,
                    UNIQUE(engagement_plan_id, phase_number)
                )
            ''')

            # Create tasks table with start_time and end_time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase_id INTEGER NOT NULL,
                    task_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    description TEXT,
                    owner TEXT,
                    due_by_day INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    deliverable TEXT,
                    success_criteria TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE,
                    UNIQUE(phase_id, task_id)
                )
            ''')

            # Create task_dependencies table (many-to-many relationship for task dependencies)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    depends_on_task_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    UNIQUE(task_id, depends_on_task_id)
                )
            ''')

            # Create cross_phase_dependencies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cross_phase_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_plan_id INTEGER NOT NULL,
                    from_task TEXT NOT NULL,
                    to_task TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_plan_id) REFERENCES engagement_plans(id) ON DELETE CASCADE,
                    UNIQUE(engagement_plan_id, from_task, to_task)
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_engagement_plans_user ON engagement_plans(user_website)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_engagement_plans_company ON engagement_plans(company_website)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phases_plan_id ON phases(engagement_plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_phase_id ON tasks(phase_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_timeline ON tasks(start_time, end_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id)')

        #self._print_important(f"{Icons.SUCCESS} All tables created/verified", Colors.GREEN)

    # ==================== Engagement Plan Methods ====================

    def create_engagement_plan(self, user_website: str, company_website: str,
                               client_name: str = None, user_company: str = None,
                               plan_meta_version: str = None) -> int:
        """Create a new engagement plan."""
        # Normalize websites before storing
        user_website = self._normalize_website(user_website)
        company_website = self._normalize_website(company_website)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO engagement_plans 
                (user_website, company_website, client_name, user_company, plan_meta_version)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_website, company_website, client_name, user_company, plan_meta_version))

            plan_id = cursor.lastrowid
            self._print_important(f"{Icons.SUCCESS} Created engagement plan ID: {plan_id}", Colors.GREEN)
            return plan_id

    def get_engagement_plan(self, plan_id: int = None, user_website: str = None,
                            company_website: str = None) -> Optional[Dict]:
        """Get an engagement plan by ID or website pair."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if plan_id:
                cursor.execute('SELECT * FROM engagement_plans WHERE id = ?', (plan_id,))
            elif user_website and company_website:
                # Normalize websites for lookup
                user_website = self._normalize_website(user_website)
                company_website = self._normalize_website(company_website)
                cursor.execute('''
                    SELECT * FROM engagement_plans 
                    WHERE user_website = ? AND company_website = ?
                ''', (user_website, company_website))
            else:
                raise ValueError("Must provide either plan_id or both user_website and company_website")

            row = cursor.fetchone()
            return dict(row) if row else None

    def update_engagement_plan(self, plan_id: int, **kwargs) -> bool:
        """Update an engagement plan."""
        allowed_fields = ['user_website', 'company_website', 'client_name',
                          'user_company', 'plan_meta_version']

        updates = []
        params = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                # Normalize website fields if they're being updated
                if key in ['user_website', 'company_website'] and value:
                    value = self._normalize_website(value)
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(plan_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE engagement_plans 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)

            success = cursor.rowcount > 0
            if success:
                self._print_important(f"{Icons.SUCCESS} Updated engagement plan ID: {plan_id}", Colors.GREEN)
            return success

    def delete_engagement_plan(self, plan_id: int) -> bool:
        """Delete an engagement plan and all related data (cascade)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM engagement_plans WHERE id = ?', (plan_id,))
            success = cursor.rowcount > 0
            if success:
                self._print_important(f"{Icons.SUCCESS} Deleted engagement plan ID: {plan_id}", Colors.GREEN)
            return success

    # ==================== Phase Methods ====================

    def create_phase(self, engagement_plan_id: int, phase_number: int, phase_name: str,
                     duration_weeks: int = None, objective: str = None) -> int:
        """Create a new phase for an engagement plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO phases (engagement_plan_id, phase_number, phase_name, duration_weeks, objective)
                VALUES (?, ?, ?, ?, ?)
            ''', (engagement_plan_id, phase_number, phase_name, duration_weeks, objective))

            phase_id = cursor.lastrowid
            self._print_important(f"{Icons.SUCCESS} Created phase ID: {phase_id} for plan {engagement_plan_id}",
                                  Colors.GREEN)
            return phase_id

    def get_phases(self, engagement_plan_id: int) -> List[Dict]:
        """Get all phases for an engagement plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM phases 
                WHERE engagement_plan_id = ? 
                ORDER BY phase_number
            ''', (engagement_plan_id,))

            return [dict(row) for row in cursor.fetchall()]

    def update_phase(self, phase_id: int, **kwargs) -> bool:
        """Update a phase."""
        allowed_fields = ['phase_name', 'duration_weeks', 'objective']

        updates = []
        params = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(phase_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE phases 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)

            return cursor.rowcount > 0

    # ==================== Task Methods with Start/End Time ====================

    def create_task(self, phase_id: int, task_id: str, task_name: str,
                    description: str = None, owner: str = None, due_by_day: int = None,
                    start_time: str = None, end_time: str = None,
                    deliverable: str = None, success_criteria: str = None,
                    status: str = 'pending') -> int:
        """Create a new task in a phase with optional start and end times."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks 
                (phase_id, task_id, task_name, description, owner, due_by_day, 
                 start_time, end_time, deliverable, success_criteria, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (phase_id, task_id, task_name, description, owner, due_by_day,
                  start_time, end_time, deliverable, success_criteria, status))

            task_record_id = cursor.lastrowid
            self._print_important(f"{Icons.SUCCESS} Created task: {task_id}", Colors.GREEN)
            return task_record_id

    def get_tasks(self, phase_id: int = None, engagement_plan_id: int = None) -> List[Dict]:
        """Get tasks by phase_id or all tasks for an engagement plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if phase_id:
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE phase_id = ? 
                    ORDER BY due_by_day
                ''', (phase_id,))
            elif engagement_plan_id:
                cursor.execute('''
                    SELECT t.* FROM tasks t
                    JOIN phases p ON t.phase_id = p.id
                    WHERE p.engagement_plan_id = ?
                    ORDER BY p.phase_number, t.due_by_day
                ''', (engagement_plan_id,))
            else:
                return []

            return [dict(row) for row in cursor.fetchall()]

    def get_tasks_by_date_range(self, start_date: str, end_date: str,
                                engagement_plan_id: int = None) -> List[Dict]:
        """Get tasks that fall within a specific date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT t.*, p.phase_name, p.engagement_plan_id 
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE (t.start_time BETWEEN ? AND ? OR t.end_time BETWEEN ? AND ?)
            '''
            params = [start_date, end_date, start_date, end_date]

            if engagement_plan_id:
                query += ' AND p.engagement_plan_id = ?'
                params.append(engagement_plan_id)

            query += ' ORDER BY t.start_time'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_tasks_by_status_and_date(self, status: str, date: str = None) -> List[Dict]:
        """Get tasks by status, optionally filtered by date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if date:
                cursor.execute('''
                    SELECT t.*, p.phase_name, p.engagement_plan_id 
                    FROM tasks t
                    JOIN phases p ON t.phase_id = p.id
                    WHERE t.status = ? AND (t.start_time <= ? AND t.end_time >= ?)
                    ORDER BY t.start_time
                ''', (status, date, date))
            else:
                cursor.execute('''
                    SELECT t.*, p.phase_name, p.engagement_plan_id 
                    FROM tasks t
                    JOIN phases p ON t.phase_id = p.id
                    WHERE t.status = ?
                    ORDER BY t.start_time
                ''', (status,))

            return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_record_id: int, **kwargs) -> bool:
        """Update a task including start_time and end_time."""
        allowed_fields = ['task_name', 'description', 'owner', 'due_by_day',
                          'start_time', 'end_time', 'deliverable',
                          'success_criteria', 'status']

        updates = []
        params = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_record_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE tasks 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)

            return cursor.rowcount > 0

    def set_task_timeline(self, task_record_id: int, start_time: str = None,
                          end_time: str = None) -> bool:
        """Convenience method to set task start and end times."""
        updates = []
        params = []

        if start_time:
            updates.append("start_time = ?")
            params.append(start_time)
        if end_time:
            updates.append("end_time = ?")
            params.append(end_time)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_record_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE tasks 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)

            return cursor.rowcount > 0

    def get_task_timeline(self, task_record_id: int) -> Dict:
        """Get the timeline for a specific task."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, task_id, task_name, start_time, end_time, status
                FROM tasks 
                WHERE id = ?
            ''', (task_record_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== Task Dependencies Methods ====================

    def add_task_dependency(self, task_record_id: int, depends_on_task_id: int) -> bool:
        """Add a dependency between tasks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO task_dependencies (task_id, depends_on_task_id)
                    VALUES (?, ?)
                ''', (task_record_id, depends_on_task_id))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_task_dependencies(self, task_record_id: int) -> List[Dict]:
        """Get all dependencies for a task."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT td.*, t.task_id, t.task_name, t.start_time, t.end_time
                FROM task_dependencies td
                JOIN tasks t ON td.depends_on_task_id = t.id
                WHERE td.task_id = ?
            ''', (task_record_id,))

            return [dict(row) for row in cursor.fetchall()]

    def check_task_dependencies_met(self, task_record_id: int) -> tuple:
        """Check if all dependencies for a task are completed.
        Returns (bool, list_of_pending_dependencies)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.task_id, t.task_name, t.status
                FROM task_dependencies td
                JOIN tasks t ON td.depends_on_task_id = t.id
                WHERE td.task_id = ? AND t.status != 'completed'
            ''', (task_record_id,))

            pending = [dict(row) for row in cursor.fetchall()]
            return (len(pending) == 0, pending)

    # ==================== Cross Phase Dependencies Methods ====================

    def add_cross_phase_dependency(self, engagement_plan_id: int, from_task: str,
                                   to_task: str, dependency_type: str = 'sequential') -> bool:
        """Add a cross-phase dependency."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO cross_phase_dependencies 
                    (engagement_plan_id, from_task, to_task, dependency_type)
                    VALUES (?, ?, ?, ?)
                ''', (engagement_plan_id, from_task, to_task, dependency_type))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_cross_phase_dependencies(self, engagement_plan_id: int) -> List[Dict]:
        """Get all cross-phase dependencies for an engagement plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM cross_phase_dependencies
                WHERE engagement_plan_id = ?
            ''', (engagement_plan_id,))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== Timeline Analysis Methods ====================

    def get_phase_timeline(self, phase_id: int) -> Dict:
        """Get the overall timeline for a phase (earliest start, latest end)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    MIN(start_time) as phase_start,
                    MAX(end_time) as phase_end,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM tasks
                WHERE phase_id = ?
            ''', (phase_id,))

            return dict(cursor.fetchone())

    def get_plan_timeline(self, engagement_plan_id: int) -> Dict:
        """Get the overall timeline for an entire plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    MIN(t.start_time) as plan_start,
                    MAX(t.end_time) as plan_end,
                    COUNT(DISTINCT p.id) as total_phases,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE p.engagement_plan_id = ?
            ''', (engagement_plan_id,))

            return dict(cursor.fetchone())

    def get_overdue_tasks(self, current_date: str = None) -> List[Dict]:
        """Get tasks that are overdue (end_time passed but not completed)."""
        if not current_date:
            from datetime import datetime
            current_date = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, p.phase_name, p.engagement_plan_id 
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE t.end_time < ? AND t.status != 'completed'
                ORDER BY t.end_time
            ''', (current_date,))

            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_tasks(self, days_ahead: int = 7, current_date: str = None) -> List[Dict]:
        """Get tasks starting in the next X days."""
        if not current_date:
            from datetime import datetime, timedelta
            current_date = datetime.now()
            future_date = current_date + timedelta(days=days_ahead)
            current_date_str = current_date.isoformat()
            future_date_str = future_date.isoformat()
        else:
            # If current_date provided, calculate future_date similarly
            from datetime import datetime, timedelta
            current = datetime.fromisoformat(current_date)
            future = current + timedelta(days=days_ahead)
            current_date_str = current_date
            future_date_str = future.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, p.phase_name, p.engagement_plan_id 
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE t.start_time BETWEEN ? AND ?
                ORDER BY t.start_time
            ''', (current_date_str, future_date_str))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== Import/Export Methods ====================

    def import_from_json(self, user_website: str, company_website: str,
                         json_data: Union[Dict, str]) -> int:
        """
        Import an engagement plan from JSON structure.
        Returns the ID of the created engagement plan.
        """
        # Normalize websites
        user_website = self._normalize_website(user_website)
        company_website = self._normalize_website(company_website)

        # Parse JSON if string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        # Extract main plan data
        plan_data = data.get('engagement_plan', data)

        # Create engagement plan
        plan_id = self.create_engagement_plan(
            user_website=user_website,
            company_website=company_website,
            client_name=plan_data.get('client_name'),
            user_company=plan_data.get('user_company'),
            plan_meta_version=plan_data.get('meta', {}).get('version')
        )

        # Create phases and tasks
        phases = plan_data.get('phases', [])
        for phase in phases:
            phase_id = self.create_phase(
                engagement_plan_id=plan_id,
                phase_number=phase['phase_number'],
                phase_name=phase['phase_name'],
                duration_weeks=phase.get('duration_weeks'),
                objective=phase.get('objective')
            )

            # Create tasks for this phase
            tasks = phase.get('tasks', [])
            for task in tasks:
                task_record_id = self.create_task(
                    phase_id=phase_id,
                    task_id=task['task_id'],
                    task_name=task['task_name'],
                    description=task.get('description'),
                    owner=task.get('owner'),
                    due_by_day=task.get('due_by_day'),
                    start_time=task.get('start_time'),
                    end_time=task.get('end_time'),
                    deliverable=task.get('deliverable'),
                    success_criteria=task.get('success_criteria'),
                    status=task.get('status', 'pending')
                )

        # Handle task dependencies (need to map task_ids to database IDs)
        task_id_map = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.task_id FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE p.engagement_plan_id = ?
            ''', (plan_id,))
            for row in cursor.fetchall():
                task_id_map[row['task_id']] = row['id']

        # Add task dependencies
        for phase in phases:
            for task in phase.get('tasks', []):
                depends_on = task.get('depends_on', [])
                if depends_on and task['task_id'] in task_id_map:
                    for dep_task_id in depends_on:
                        if dep_task_id in task_id_map:
                            self.add_task_dependency(
                                task_id_map[task['task_id']],
                                task_id_map[dep_task_id]
                            )

        # Add cross-phase dependencies
        cross_deps = plan_data.get('cross_phase_dependencies', [])
        for dep in cross_deps:
            self.add_cross_phase_dependency(
                engagement_plan_id=plan_id,
                from_task=dep['from_task'],
                to_task=dep['to_task'],
                dependency_type=dep.get('type', 'sequential')
            )

        self._print_important(f"{Icons.SUCCESS} Successfully imported engagement plan ID: {plan_id}", Colors.GREEN)
        return plan_id

    def export_to_json(self, plan_id: int) -> Dict:
        """Export an engagement plan to JSON structure."""
        # Get main plan
        plan = self.get_engagement_plan(plan_id=plan_id)
        if not plan:
            return None

        # Get phases
        phases = self.get_phases(plan_id)

        # Get all tasks for this plan
        all_tasks = self.get_tasks(engagement_plan_id=plan_id)

        # Get cross-phase dependencies
        cross_deps = self.get_cross_phase_dependencies(plan_id)

        # Build task lookup by phase
        tasks_by_phase = {}
        task_id_to_task_id_map = {}  # Map DB task ID to original task_id

        for task in all_tasks:
            phase_id = task['phase_id']
            if phase_id not in tasks_by_phase:
                tasks_by_phase[phase_id] = []
            tasks_by_phase[phase_id].append(task)
            task_id_to_task_id_map[task['id']] = task['task_id']

        # Get dependencies for each task
        task_deps = {}
        for task in all_tasks:
            deps = self.get_task_dependencies(task['id'])
            if deps:
                task_deps[task['task_id']] = [
                    task_id_to_task_id_map[d['depends_on_task_id']]
                    for d in deps
                ]

        # Build phases structure
        phases_data = []
        for phase in phases:
            tasks_data = []
            for task in tasks_by_phase.get(phase['id'], []):
                task_dict = {
                    'task_id': task['task_id'],
                    'task_name': task['task_name'],
                    'description': task['description'],
                    'owner': task['owner'],
                    'due_by_day': task['due_by_day'],
                    'start_time': task['start_time'],
                    'end_time': task['end_time'],
                    'deliverable': task['deliverable'],
                    'success_criteria': task['success_criteria'],
                    'depends_on': task_deps.get(task['task_id'], []),
                    'status': task['status']
                }
                tasks_data.append(task_dict)

            phase_dict = {
                'phase_number': phase['phase_number'],
                'phase_name': phase['phase_name'],
                'duration_weeks': phase['duration_weeks'],
                'objective': phase['objective'],
                'tasks': tasks_data
            }
            phases_data.append(phase_dict)

        # Build cross-phase dependencies
        cross_deps_data = []
        for dep in cross_deps:
            dep_dict = {
                'from_task': dep['from_task'],
                'to_task': dep['to_task'],
                'type': dep['dependency_type']
            }
            cross_deps_data.append(dep_dict)

        # Build final JSON structure
        result = {
            'engagement_plan': {
                'client_name': plan['client_name'],
                'user_company': plan['user_company'],
                'phases': phases_data,
                'cross_phase_dependencies': cross_deps_data,
                'meta': {
                    'version': plan['plan_meta_version']
                }
            }
        }

        return result

    # ==================== Utility Methods ====================

    def get_plan_summary(self, plan_id: int) -> Dict:
        """Get a summary of an engagement plan with task counts by status and timeline info."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get task counts by status
            cursor.execute('''
                SELECT t.status, COUNT(*) as count
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE p.engagement_plan_id = ?
                GROUP BY t.status
            ''', (plan_id,))

            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

            # Get phase info with timeline
            cursor.execute('''
                SELECT p.phase_number, p.phase_name, 
                       (SELECT COUNT(*) FROM tasks WHERE phase_id = p.id) as task_count,
                       MIN(t.start_time) as phase_start,
                       MAX(t.end_time) as phase_end,
                       SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM phases p
                LEFT JOIN tasks t ON t.phase_id = p.id
                WHERE p.engagement_plan_id = ?
                GROUP BY p.id
                ORDER BY p.phase_number
            ''', (plan_id,))

            phases = [dict(row) for row in cursor.fetchall()]

            # Get overall plan timeline
            timeline = self.get_plan_timeline(plan_id)

            return {
                'plan_id': plan_id,
                'total_tasks': sum(status_counts.values()),
                'status_counts': status_counts,
                'phases': phases,
                'timeline': timeline,
                'overdue_tasks': len(self.get_overdue_tasks()),
                'upcoming_tasks': len(self.get_upcoming_tasks())
            }

    def get_complete_engagement_plan_json(self, user_website: str, company_website: str) -> Optional[Dict]:
        """
        Get the complete engagement plan as a JSON structure for a specific user and company.

        Args:
            user_website: The user's website
            company_website: The company's website

        Returns:
            Complete engagement plan JSON structure or None if not found
        """
        # Normalize websites for lookup
        user_website = self._normalize_website(user_website)
        company_website = self._normalize_website(company_website)

        # First get the engagement plan ID
        plan = self.get_engagement_plan(user_website=user_website, company_website=company_website)

        if not plan:
            self._print_important(
                f"{Icons.WARNING} No engagement plan found for {user_website} -> {company_website}",
                Colors.YELLOW
            )
            return None

        # Use the existing export_to_json method which already builds the complete structure
        return self.export_to_json(plan['id'])