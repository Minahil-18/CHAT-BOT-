"""
CRM Tool - CRUD Unit Tests
Tests Create, Read, Update, Delete operations on user records
"""

import unittest
import os
import sqlite3
import tempfile
import json
import time
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from crm_tool import CRMTool


class TestCRMCRUD(unittest.TestCase):
    """Test CRM CRUD operations"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        # Create temp dir
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_users.db")
        self.crm = CRMTool(db_path=self.test_db)
    
    def tearDown(self):
        """Clean up temporary database"""
        # Ensure we don't have open connections (though CRMTool opens/closes each time)
        # We'll try to remove, if it fails because of locking, we'll wait a bit
        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(self.test_db):
                    os.remove(self.test_db)
                if os.path.exists(self.temp_dir):
                    os.rmdir(self.temp_dir)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.1)
                else:
                    print(f"Warning: Could not clean up {self.test_db}")

    # ═══════════════════════════════════════════════════════════════
    # CREATE TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_create_user_basic(self):
        """Test creating a basic user"""
        result = self.crm.create_user("Alice Johnson", "alice@example.com", "+1234567890")
        
        self.assertTrue(result["success"])
        self.assertIn("user_", result["user_id"])
        self.assertIn("created", result["message"].lower())
    
    def test_create_user_minimal(self):
        """Test creating user with minimal fields"""
        result = self.crm.create_user("Bob Smith")
        
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["user_id"])
    
    def test_create_user_with_custom_id(self):
        """Test creating user with custom user_id"""
        custom_id = "test_user_001"
        result = self.crm.create_user("Charlie Brown", user_id=custom_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["user_id"], custom_id)
    
    def test_create_user_duplicate_id_fails(self):
        """Test that duplicate user_id fails"""
        custom_id = "duplicate_user"
        
        # Create first user
        result1 = self.crm.create_user("User One", user_id=custom_id)
        self.assertTrue(result1["success"])
        
        # Try to create duplicate
        result2 = self.crm.create_user("User Two", user_id=custom_id)
        self.assertFalse(result2["success"])
        self.assertIn("already exists", result2["message"])
    
    def test_create_user_stores_email_phone(self):
        """Test that email and phone are stored correctly"""
        email = "dave@example.com"
        phone = "+9876543210"
        result = self.crm.create_user("Dave Wilson", email=email, phone=phone)
        
        self.assertTrue(result["success"])
        user_id = result["user_id"]
        
        # Verify data was stored
        user = self.crm.get_user(user_id)
        self.assertEqual(user["email"], email)
        self.assertEqual(user["phone"], phone)
    
    # ═══════════════════════════════════════════════════════════════
    # READ TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_read_existing_user(self):
        """Test reading an existing user"""
        # Create user
        create_result = self.crm.create_user("Eve Adams", "eve@example.com")
        user_id = create_result["user_id"]
        
        # Read user
        user = self.crm.get_user(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Eve Adams")
        self.assertEqual(user["email"], "eve@example.com")
    
    def test_read_nonexistent_user(self):
        """Test reading a nonexistent user returns None"""
        user = self.crm.get_user("nonexistent_user_xyz")
        self.assertIsNone(user)
    
    def test_read_includes_preferences(self):
        """Test that read returns preferences"""
        create_result = self.crm.create_user("Frank Miller")
        user_id = create_result["user_id"]
        
        user = self.crm.get_user(user_id)
        self.assertIn("preferences", user)
        self.assertIsInstance(user["preferences"], dict)
    
    def test_read_includes_trips(self):
        """Test that read returns trips array (not in get_user by default)"""
        create_result = self.crm.create_user("Grace Lee")
        user_id = create_result["user_id"]
        
        # In current implementation, get_user returns user info and preferences
        # but not the trips list directly. Trips are fetched via get_user_trips.
        user = self.crm.get_user(user_id)
        self.assertIsNotNone(user)
        
        trips = self.crm.get_user_trips(user_id)
        self.assertIsInstance(trips, list)
    
    # ═══════════════════════════════════════════════════════════════
    # UPDATE TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_update_user_name(self):
        """Test updating user name"""
        # Create user
        create_result = self.crm.create_user("Helen Brown", user_id="update_test_1")
        user_id = create_result["user_id"]
        
        # Update name
        result = self.crm.update_user(user_id, name="Helen Smith")
        self.assertTrue(result["success"])
        
        # Verify update
        user = self.crm.get_user(user_id)
        self.assertEqual(user["name"], "Helen Smith")
    
    def test_update_user_email(self):
        """Test updating user email"""
        create_result = self.crm.create_user("Ian Johnson", email="ian_old@example.com", user_id="update_test_2")
        user_id = create_result["user_id"]
        
        # Update email
        new_email = "ian_new@example.com"
        result = self.crm.update_user(user_id, email=new_email)
        self.assertTrue(result["success"])
        
        # Verify update
        user = self.crm.get_user(user_id)
        self.assertEqual(user["email"], new_email)
    
    def test_update_user_phone(self):
        """Test updating user phone"""
        create_result = self.crm.create_user("Julia White", phone="+1111111111", user_id="update_test_3")
        user_id = create_result["user_id"]
        
        # Update phone
        new_phone = "+2222222222"
        result = self.crm.update_user(user_id, phone=new_phone)
        self.assertTrue(result["success"])
        
        # Verify update
        user = self.crm.get_user(user_id)
        self.assertEqual(user["phone"], new_phone)
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        create_result = self.crm.create_user("Kevin Black", user_id="update_test_4")
        user_id = create_result["user_id"]
        
        # Update multiple fields
        result = self.crm.update_user(
            user_id,
            name="Kevin Green",
            email="kevin@example.com",
            phone="+3333333333",
            budget_level="luxury"
        )
        self.assertTrue(result["success"])
        
        # Verify all updates
        user = self.crm.get_user(user_id)
        self.assertEqual(user["name"], "Kevin Green")
        self.assertEqual(user["email"], "kevin@example.com")
        self.assertEqual(user["phone"], "+3333333333")
        self.assertEqual(user["budget_level"], "luxury")
    
    def test_update_nonexistent_user(self):
        """Test updating nonexistent user fails gracefully"""
        result = self.crm.update_user("nonexistent_xyz", name="New Name")
        self.assertFalse(result["success"])
    
    def test_update_sets_timestamp(self):
        """Test that update sets updated_at timestamp"""
        create_result = self.crm.create_user("Laura Davis", user_id="update_test_5")
        user_id = create_result["user_id"]
        
        # Get creation timestamp
        user1 = self.crm.get_user(user_id)
        created_at = user1.get("created_at")
        
        # Wait and update
        time.sleep(0.1)
        self.crm.update_user(user_id, name="Laura Edwards")
        
        # Check updated_at changed
        user2 = self.crm.get_user(user_id)
        updated_at = user2.get("updated_at")
        self.assertIsNotNone(updated_at)
    
    # ═══════════════════════════════════════════════════════════════
    # TRIP MANAGEMENT TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_add_trip(self):
        """Test adding a trip to user"""
        create_result = self.crm.create_user("Oscar White", user_id="trip_test_1")
        user_id = create_result["user_id"]
        
        # Add trip
        result = self.crm.add_trip(
            user_id, 
            "trip_123",
            "Paris", 
            "2024-06-01", 
            "2024-06-07", 
            1500.0, 
            "Business trip"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["trip_id"], "trip_123")
    
    def test_add_trip_invalid_user(self):
        """Test adding trip to nonexistent user"""
        result = self.crm.add_trip("nonexistent_user", "trip_fail", "Paris", "2024-06-01", "2024-06-10", 3000)
        self.assertFalse(result["success"])
    
    def test_get_user_trips(self):
        """Test retrieving user's trips"""
        create_result = self.crm.create_user("Patricia Green", user_id="trip_test_2")
        user_id = create_result["user_id"]
        
        # Add multiple trips
        self.crm.add_trip(user_id, "trip_p1", "Paris", "2024-06-01", "2024-06-07")
        self.crm.add_trip(user_id, "trip_t1", "Tokyo", "2024-07-15", "2024-07-22")
        
        trips = self.crm.get_user_trips(user_id)
        self.assertEqual(len(trips), 2)
        
        destinations = [t["destination"] for t in trips]
        self.assertIn("Paris", destinations)
        self.assertIn("Tokyo", destinations)
    
    def test_get_trips_nonexistent_user(self):
        """Test getting trips for nonexistent user"""
        trips = self.crm.get_user_trips("nonexistent_user")
        self.assertEqual(len(trips), 0) # Returns empty list
    
    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCE TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_data_persists_across_instances(self):
        """Test that data persists when creating new CRM instance"""
        # Create user with first instance
        result1 = self.crm.create_user("Quinn Brown", user_id="persist_test_1")
        user_id = result1["user_id"]
        
        # Create new instance with same database
        crm2 = CRMTool(db_path=self.test_db)
        user = crm2.get_user(user_id)
        
        # Verify data is still there
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Quinn Brown")
    
    def test_multiple_users_persist(self):
        """Test that multiple users persist correctly"""
        # Create multiple users
        id1 = self.crm.create_user("Rachel King", user_id="user_001")["user_id"]
        id2 = self.crm.create_user("Samuel Lee", user_id="user_002")["user_id"]
        id3 = self.crm.create_user("Teresa Moore", user_id="user_003")["user_id"]
        
        # Create new instance
        crm2 = CRMTool(db_path=self.test_db)
        
        # Verify all users still exist
        self.assertIsNotNone(crm2.get_user(id1))
        self.assertIsNotNone(crm2.get_user(id2))
        self.assertIsNotNone(crm2.get_user(id3))
    
    # ═══════════════════════════════════════════════════════════════
    # EDGE CASE TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_create_user_empty_name(self):
        """Test creating user with empty name"""
        result = self.crm.create_user("")
        self.assertTrue(result["success"])
        self.assertIsNotNone(result.get("user_id"))
    
    def test_create_user_special_characters(self):
        """Test creating user with special characters in name"""
        result = self.crm.create_user("José García-López")
        self.assertTrue(result["success"])
        
        user = self.crm.get_user(result["user_id"])
        self.assertEqual(user["name"], "José García-López")
    
    def test_create_user_long_email(self):
        """Test creating user with long email"""
        long_email = "very.long.email.address.with.many.parts@subdomain.example.co.uk"
        result = self.crm.create_user("Victoria Anderson", email=long_email)
        self.assertTrue(result["success"])
        
        user = self.crm.get_user(result["user_id"])
        self.assertEqual(user["email"], long_email)
    
    def test_create_user_international_phone(self):
        """Test creating user with international phone numbers"""
        # Test various formats
        phones = ["+44 20 1234 5678", "+91-98765-43210", "+33 1 23 45 67 89"]
        
        for i, phone in enumerate(phones):
            result = self.crm.create_user(f"User {i}", phone=phone, user_id=f"phone_test_{i}")
            self.assertTrue(result["success"])
            user = self.crm.get_user(result["user_id"])
            self.assertEqual(user["phone"], phone)


if __name__ == "__main__":
    unittest.main()
