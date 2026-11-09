from backend.database.db import initialize_database,create_memory,list_memories,delete_memory

def test_memory_crud_smoke():
    initialize_database()
    user = "test-user-crud"
    memory_id = create_memory(user,"I prefer concise answers.","preference",4)
    assert any(item["id"] == memory_id for item in list_memories(user))
    assert delete_memory(memory_id,user)
    assert not any(item["id"] == memory_id for item in list_memories(user))
