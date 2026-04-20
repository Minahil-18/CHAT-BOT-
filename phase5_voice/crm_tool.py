"""
CRM Tool - Customer Relationship Management
Stores and retrieves user profiles, preferences, and trip history
"""

import sqlite3
import os
from typing import Optional, Dict, List, Any

class CRMTool:
    """CRM system for managing user information and preferences"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                preferred_destination TEXT,
                budget_level TEXT,
                travel_style TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY,
                season TEXT,
                accommodation_type TEXT,
                dietary_preferences TEXT,
                mobility_needs TEXT,
                group_size INTEGER,
                currency TEXT,
                language TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                user_id TEXT,
                destination TEXT,
                start_date TEXT,
                end_date TEXT,
                budget REAL,
                status TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, name: str, email: str = "", phone: str = "", user_id: str = None) -> Dict[str, Any]:
        """Create a new user profile"""
        try:
            # Auto-generate user_id if not provided
            if not user_id:
                import uuid
                user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (user_id, name, email, phone)
                VALUES (?, ?, ?, ?)
            """, (user_id, name, email, phone))
            
            cursor.execute("INSERT INTO preferences (user_id) VALUES (?)", (user_id,))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"User {name} created", "user_id": user_id}
        except sqlite3.IntegrityError:
            return {"success": False, "message": f"User {user_id} already exists"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile and preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return None
            
            user_dict = dict(user)
            cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
            prefs = cursor.fetchone()
            if prefs:
                user_dict["preferences"] = dict(prefs)
            
            conn.close()
            return user_dict
        except Exception as e:
            return None
    
    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                return {"success": False, "message": f"User {user_id} not found"}
            
            user_fields = {"name", "email", "phone", "preferred_destination", "budget_level", "travel_style"}
            pref_fields = {"season", "accommodation_type", "dietary_preferences", "mobility_needs", "group_size", "currency", "language"}
            
            user_updates = {k: v for k, v in kwargs.items() if k in user_fields}
            if user_updates:
                set_clause = ", ".join([f"{k} = ?" for k in user_updates.keys()]) + ", updated_at = CURRENT_TIMESTAMP"
                values = list(user_updates.values()) + [user_id]
                cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            
            pref_updates = {k: v for k, v in kwargs.items() if k in pref_fields}
            if pref_updates:
                set_clause = ", ".join([f"{k} = ?" for k in pref_updates.keys()])
                values = list(pref_updates.values()) + [user_id]
                cursor.execute(f"UPDATE preferences SET {set_clause} WHERE user_id = ?", values)
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"User {user_id} updated"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def add_trip(self, user_id: str, trip_id: str, destination: str, start_date: str, end_date: str, budget: float = 0.0, notes: str = "") -> Dict[str, Any]:
        """Add a trip to user's history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                return {"success": False, "message": f"User {user_id} not found"}
            
            cursor.execute("""
                INSERT INTO trips (trip_id, user_id, destination, start_date, end_date, budget, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (trip_id, user_id, destination, start_date, end_date, budget, "planned", notes))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"Trip to {destination} added", "trip_id": trip_id}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_user_trips(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all trips for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            trips = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return trips
        except Exception as e:
            return []
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
            prefs = cursor.fetchone()
            
            conn.close()
            return dict(prefs) if prefs else None
        except Exception as e:
            return None


# Tool definitions for LLM
CRM_TOOLS = [
    {
        "name": "create_user",
        "description": "Create a new user profile in the CRM system. user_id is auto-generated if not provided.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "user_id": {"type": "string", "description": "Optional - auto-generated if not provided"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_user",
        "description": "Retrieve a user's profile and preferences",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"]
        }
    },
    {
        "name": "update_user",
        "description": "Update user profile or preferences",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "preferred_destination": {"type": "string"},
                "budget_level": {"type": "string"},
                "travel_style": {"type": "string"},
                "season": {"type": "string"},
                "accommodation_type": {"type": "string"},
                "group_size": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "add_trip",
        "description": "Add a trip to user's travel history",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "trip_id": {"type": "string"},
                "destination": {"type": "string"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "budget": {"type": "number"},
                "notes": {"type": "string"}
            },
            "required": ["user_id", "trip_id", "destination", "start_date", "end_date"]
        }
    },
    {
        "name": "get_user_trips",
        "description": "Get all trips for a user",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"]
        }
    }
]
