# orchestrator/memory.py

import json
import os

MEMORY_FILE = "memory_store.json"


class Memory:

    def __init__(self):
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w") as f:
                json.dump({}, f)

    def load(self):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_user_memory(self, user_id):
        data = self.load()
        return data.get(user_id, {})

    def update_user_memory(self, user_id, new_data):
        data = self.load()
        user_mem = data.get(user_id, {})

        user_mem.update(new_data)
        data[user_id] = user_mem

        self.save(data)