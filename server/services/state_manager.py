"""
State management for email tracking and todo tasks
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
EMAIL_STATE_FILE = DATA_DIR / "email_state.json"
TASKS_FILE = DATA_DIR / "tasks.json"

DATA_DIR.mkdir(exist_ok=True)

class StateManager:
    def __init__(self):
        self.email_states = self._load_email_states()
        self.tasks = self._load_tasks()
    
    def _load_email_states(self):
        if EMAIL_STATE_FILE.exists():
            with open(EMAIL_STATE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_email_states(self):
        with open(EMAIL_STATE_FILE, 'w') as f:
            json.dump(self.email_states, f, indent=2)
    
    def _load_tasks(self):
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def _save_tasks(self):
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    def acknowledge_email(self, thread_id: str):
        if thread_id not in self.email_states:
            self.email_states[thread_id] = {}
        self.email_states[thread_id]['acknowledged'] = True
        self.email_states[thread_id]['acknowledged_at'] = datetime.now().isoformat()
        self._save_email_states()
        return self.email_states[thread_id]
    
    def mark_analyzed(self, thread_id: str):
        if thread_id not in self.email_states:
            self.email_states[thread_id] = {}
        self.email_states[thread_id]['analyzed'] = True
        self.email_states[thread_id]['analyzed_at'] = datetime.now().isoformat()
        self._save_email_states()
        return self.email_states[thread_id]
    
    def get_email_state(self, thread_id: str):
        return self.email_states.get(thread_id, {'acknowledged': False, 'analyzed': False, 'tasks_added': []})
    
    def get_all_email_states(self):
        return self.email_states
    
    def add_task(self, task: Dict, thread_id: Optional[str] = None):
        task_id = f"task_{len(self.tasks) + 1}_{datetime.now().timestamp()}"
        new_task = {
            'id': task_id,
            'action': task.get('action', ''),
            'due_date': task.get('due_date'),
            'time_estimate': task.get('time_estimate'),
            'priority': task.get('priority', 'normal'),
            'completed': False,
            'thread_id': thread_id,
            'created_at': datetime.now().isoformat()
        }
        self.tasks.append(new_task)
        self._save_tasks()
        if thread_id:
            if thread_id not in self.email_states:
                self.email_states[thread_id] = {}
            if 'tasks_added' not in self.email_states[thread_id]:
                self.email_states[thread_id]['tasks_added'] = []
            self.email_states[thread_id]['tasks_added'].append(task_id)
            self._save_email_states()
        return new_task
    
    def add_tasks_bulk(self, tasks: List[Dict], thread_id: Optional[str] = None):
        return [self.add_task(task, thread_id) for task in tasks]
    
    def get_tasks(self, filter_completed: Optional[bool] = None):
        if filter_completed is None:
            return self.tasks
        return [t for t in self.tasks if t['completed'] == filter_completed]
    
    def get_task(self, task_id: str):
        return next((t for t in self.tasks if t['id'] == task_id), None)
    
    def toggle_task(self, task_id: str):
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                if task['completed']:
                    task['completed_at'] = datetime.now().isoformat()
                else:
                    task.pop('completed_at', None)
                self._save_tasks()
                return task
        return None
    
    def delete_task(self, task_id: str):
        original_length = len(self.tasks)
        self.tasks = [t for t in self.tasks if t['id'] != task_id]
        if len(self.tasks) < original_length:
            self._save_tasks()
            return True
        return False
    
    def update_task(self, task_id: str, updates: Dict):
        for task in self.tasks:
            if task['id'] == task_id:
                task.update(updates)
                task['updated_at'] = datetime.now().isoformat()
                self._save_tasks()
                return task
        return None

state_manager = StateManager()
