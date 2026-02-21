import json
import os
import datetime

MEMORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../personality/memory_network.json'))

class MemoryManager:
    def __init__(self):
        self.file_path = MEMORY_FILE
        self.graph = self._load_graph()

    def _load_graph(self):
        if not os.path.exists(self.file_path):
            return {"nodes": [], "edges": []}
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"nodes": [], "edges": []}

    def _save_graph(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.graph, f, indent=2)

    def find_node(self, label):
        """Find a node by label (case-insensitive)."""
        label_lower = label.lower()
        for node in self.graph.get("nodes", []):
            if node.get("label", "").lower() == label_lower:
                return node
        return None

    def add_node(self, node_id, node_type, label, properties=None):
        """Adds a new node if it doesn't exist."""
        existing = self.find_node(label)
        if existing:
            # Update properties if needed
            if properties:
                existing.setdefault("properties", {}).update(properties)
                self._save_graph()
            return existing

        new_node = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "properties": properties or {},
            "created_at": datetime.datetime.now().isoformat()
        }
        self.graph.setdefault("nodes", []).append(new_node)
        self._save_graph()
        return new_node

    def add_edge(self, source_id, target_id, relation, weight=1.0):
        """Adds a relationship edge."""
        # Check if edge exists
        for edge in self.graph.get("edges", []):
            if edge["source"] == source_id and edge["target"] == target_id and edge["relation"] == relation:
                edge["weight"] = weight # Update weight
                self._save_graph()
                return edge

        new_edge = {
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": weight,
            "created_at": datetime.datetime.now().isoformat()
        }
        self.graph.setdefault("edges", []).append(new_edge)
        self._save_graph()
        return new_edge

    def get_related(self, node_id):
        """Returns all nodes connected to the given node_id."""
        related = []
        for edge in self.graph.get("edges", []):
            if edge["source"] == node_id:
                related.append({"relation": edge["relation"], "target": edge["target"], "weight": edge["weight"]})
            elif edge["target"] == node_id:
                related.append({"relation": f"inverse_{edge['relation']}", "target": edge["source"], "weight": edge["weight"]})
        return related

if __name__ == "__main__":
    # Test
    mm = MemoryManager()
    print(f"Loaded {len(mm.graph.get('nodes', []))} nodes.")
    # Example usage:
    # mm.add_node("test_concept", "concept", "Self-Improvement", {"status": "active"})
