"""Unit tests for Singleton Design Pattern (DatabaseManager)."""
import threading
from atm_system.patterns.singleton import DatabaseManager


class TestSingletonPattern:
    """Verifies Singleton properties: uniqueness, thread-safety, reset capability."""

    def test_single_instance(self, test_db_path):
        """Two instantiations must point to the identical object in memory."""
        db1 = DatabaseManager(test_db_path)
        db2 = DatabaseManager(test_db_path)
        assert db1 is db2

    def test_thread_safe_singleton(self, test_db_path):
        """Concurrent threads must receive the exact same singleton instance."""
        instances = []

        def worker():
            inst = DatabaseManager(test_db_path)
            instances.append(inst)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 10
        first = instances[0]
        for inst in instances:
            assert inst is first

    def test_reset_instance(self, test_db_path, tmp_path):
        """reset_instance must disconnect and allow creating a fresh instance."""
        db1 = DatabaseManager(test_db_path)
        DatabaseManager.reset_instance()

        new_path = str(tmp_path / "another.db")
        db2 = DatabaseManager(new_path)
        assert db1 is not db2

    def test_database_operations(self, test_db):
        """Verify standard query execution through DatabaseManager."""
        cursor = test_db.execute("SELECT 1 AS test_val")
        row = cursor.fetchone()
        assert row["test_val"] == 1
