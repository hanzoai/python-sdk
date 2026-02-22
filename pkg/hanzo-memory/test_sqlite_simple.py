"""Simple test to verify SQLite backend integration."""

from hanzo_memory.memory import memory


def test_backend_availability():
    """Test that SQLite backend is available."""
    print("Testing SQLite backend availability...")

    # Check if SQLite backend is listed
    available_backends = memory.backends()
    print(f"Available backends: {list(available_backends.keys())}")

    if "sqlite" in available_backends:
        print("✅ SQLite backend is available!")

        # Try to access the backend
        try:
            sqlite_backend = memory["sqlite"]
            print("✅ Successfully accessed SQLite backend via indexing")
        except Exception as e:
            print(f"❌ Error accessing SQLite backend via indexing: {e}")

        try:
            sqlite_backend = memory.sqlite
            print("✅ Successfully accessed SQLite backend via attribute")
        except Exception as e:
            print(f"❌ Error accessing SQLite backend via attribute: {e}")

        return True
    else:
        print("❌ SQLite backend is NOT available!")
        return False


if __name__ == "__main__":
    success = test_backend_availability()
    if success:
        print("\n🎉 SQLite backend integration test passed!")
    else:
        print("\n❌ SQLite backend integration test failed!")
