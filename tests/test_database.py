import os
import sqlite3
import pytest
from database import MemoryDatabase, DB_DIR

TEST_DB_PATH = os.path.join(DB_DIR, "test_memory.db")

@pytest.fixture
def db():
    # Setup
    database = MemoryDatabase(db_path=TEST_DB_PATH)
    yield database
    # Teardown
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_database_initialization(db):
    """Ensure that the database initializes correctly and does not contain conversations table."""
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Check memories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
        assert cursor.fetchone() is not None

        # Check temp_states table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temp_states'")
        assert cursor.fetchone() is not None

        # Ensure conversations table does NOT exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
        assert cursor.fetchone() is None

def test_save_and_search_memory(db):
    """Test saving a memory and retrieving it via vector search."""
    db.save_memory(key="test_fact_1", fact="Vansh loves coding in Python.", category="Personal", importance="HIGH")
    
    # We test the semantic search - it should return the fact even if words don't exactly match
    results = db.search_memories("What does Vansh like to program in?")
    assert len(results) > 0
    assert results[0]["fact"] == "Vansh loves coding in Python."
    assert results[0]["category"] == "Personal"
