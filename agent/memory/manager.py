import json
import os
import time

class MemoryManager:
    def __init__(self, data_dir="data/memories"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.index_file = os.path.join(self.data_dir, "index.json")
        self.memories = self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return []

    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.memories, f, indent=2)

    def save(self, content, tags=None):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        memory_id = len(self.memories) + 1
        entry = {
            "id": memory_id,
            "timestamp": timestamp,
            "content": content,
            "tags": tags or []
        }
        self.memories.append(entry)
        self._save_index()
        return f"Memory saved with ID {memory_id}"

    def retrieve_relevant(self, query):
        # Simple keyword matching for now
        results = []
        words = query.lower().split()
        for mem in self.memories:
            if any(w in mem['content'].lower() for w in words):
                results.append(mem['content'])
        return "\n".join(results[-3:]) # Return top 3 recent relevant
