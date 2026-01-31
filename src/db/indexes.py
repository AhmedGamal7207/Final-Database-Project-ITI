from typing import Dict, List, Set, Any
import re
import numpy as np

class IndexManager:
    def __init__(self):
        # Inverted Index: word -> set of keys
        self.inverted_index: Dict[str, Set[str]] = {}
        # Simple Vector Index: key -> vector (not optimized for search, just storage)
        self.vectors: Dict[str, np.ndarray] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def _get_embedding(self, text: str) -> np.ndarray:
        # deterministic hash-based embedding for demo purpose
        # In real world, use a model like SentenceTransformer
        # Dimensions = 10
        seed = abs(hash(text)) % (2**32)
        rng = np.random.default_rng(seed)
        return rng.random(10)

    def update(self, key: str, value: Any, old_value: Any = None):
        # Only index string values
        if isinstance(old_value, str):
            for word in self._tokenize(old_value):
                if word in self.inverted_index:
                    self.inverted_index[word].discard(key)
                    if not self.inverted_index[word]:
                        del self.inverted_index[word]

        if isinstance(value, str):
            # Update Inverted Index
            for word in self._tokenize(value):
                if word not in self.inverted_index:
                    self.inverted_index[word] = set()
                self.inverted_index[word].add(key)
            
            # Update Vector Index
            self.vectors[key] = self._get_embedding(value)

    def remove(self, key: str, value: Any):
        if isinstance(value, str):
            for word in self._tokenize(value):
                if word in self.inverted_index:
                    self.inverted_index[word].discard(key)
            self.vectors.pop(key, None)

    def search(self, query: str) -> List[str]:
        words = self._tokenize(query)
        if not words:
            return []
        
        # Intersection of all query words
        result_keys = None
        for word in words:
            keys = self.inverted_index.get(word, set())
            if result_keys is None:
                result_keys = set(keys)
            else:
                result_keys &= keys
        
        return list(result_keys) if result_keys else []
    
    def vector_search(self, query: str, top_k: int = 5) -> List[str]:
        # Brute-force cosine similarity
        q_vec = self._get_embedding(query)
        scores = []
        for k, v_vec in self.vectors.items():
            # cosine sim
            sim = np.dot(q_vec, v_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(v_vec) + 1e-9)
            scores.append((sim, k))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        return [k for s, k in scores[:top_k]]
