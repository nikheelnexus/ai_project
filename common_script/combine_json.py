from typing import List, Dict, Any
from difflib import SequenceMatcher


class UniversalJSONCombiner:
    """A simplified JSON combiner that merges data structures without metadata."""

    def __init__(self):
        self.field_similarity_threshold = 0.7
        self.key_merge_threshold = 0.8

    def combine_json_data(self, json_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple JSON objects into a single consolidated structure.
        """
        if not json_list:
            return {}

        # Start with first JSON object
        combined = json_list[0].copy()

        # Merge remaining objects
        for json_obj in json_list[1:]:
            combined = self._merge_objects(combined, json_obj)

        return combined

    def _merge_objects(self, target: Any, source: Any) -> Any:
        """Merge two objects based on their types."""
        if isinstance(target, dict) and isinstance(source, dict):
            return self._merge_dicts(target, source)
        elif isinstance(target, list) and isinstance(source, list):
            return self._merge_arrays(target, source)
        elif source is not None and target is None:
            return source
        elif target is not None and source is None:
            return target
        elif target != source:
            return self._resolve_value_conflict(target, source)
        else:
            return target

    def _merge_dicts(self, target: Dict, source: Dict) -> Dict:
        """Merge two dictionaries with fuzzy key matching."""
        result = target.copy()

        for source_key, source_value in source.items():
            # Find the best matching key in target
            best_match = None
            best_similarity = 0

            for target_key in result.keys():
                similarity = self._key_similarity(source_key, target_key)
                if similarity > best_similarity and similarity > self.key_merge_threshold:
                    best_match = target_key
                    best_similarity = similarity

            if best_match:
                # Merge values for similar keys
                result[best_match] = self._merge_objects(result[best_match], source_value)
            else:
                # Add as new key
                result[source_key] = source_value

        return result

    def _key_similarity(self, key1: str, key2: str) -> float:
        """Calculate similarity between two keys."""
        k1 = key1.lower().replace('_', '').replace('-', '')
        k2 = key2.lower().replace('_', '').replace('-', '')

        if k1 == k2:
            return 1.0

        return SequenceMatcher(None, k1, k2).ratio()

    def _merge_arrays(self, target: List, source: List) -> List:
        """Merge two arrays intelligently."""
        if not target:
            return source
        if not source:
            return target

        # Check if arrays contain objects that might be merged
        if (target and source and
                isinstance(target[0], dict) and isinstance(source[0], dict)):
            return self._merge_object_arrays(target, source)

        # Regular array merge with duplicate handling
        return self._smart_array_merge(target, source)

    def _merge_object_arrays(self, target: List[Dict], source: List[Dict]) -> List[Dict]:
        """Merge object arrays using content-based matching."""
        result = target.copy()

        for source_obj in source:
            matched = False

            # Try to find a matching object in target
            for i, target_obj in enumerate(result):
                if self._objects_similar(target_obj, source_obj):
                    # Merge matching objects
                    result[i] = self._merge_dicts(target_obj, source_obj)
                    matched = True
                    break

            if not matched:
                result.append(source_obj)

        return result

    def _objects_similar(self, obj1: Dict, obj2: Dict) -> bool:
        """Check if two objects are similar enough to merge."""
        if not obj1 or not obj2:
            return False

        common_keys = set(obj1.keys()) & set(obj2.keys())
        if not common_keys:
            return False

        similarity_score = 0
        total_weight = 0

        for key in common_keys:
            weight = 2.0 if key in ['id', 'name', 'title', 'email'] else 1.0

            if obj1[key] == obj2[key]:
                similarity_score += weight
            elif isinstance(obj1[key], str) and isinstance(obj2[key], str):
                str_similarity = self._string_similarity(obj1[key], obj2[key])
                similarity_score += str_similarity * weight

            total_weight += weight

        return (similarity_score / total_weight) > self.field_similarity_threshold

    def _smart_array_merge(self, target: List, source: List) -> List:
        """Merge arrays with duplicate removal."""
        combined = target + source
        seen = set()
        result = []

        for item in combined:
            item_hash = self._hash_item(item)
            if item_hash not in seen:
                seen.add(item_hash)
                result.append(item)

        return result

    def _hash_item(self, item: Any) -> str:
        """Create a hash for duplicate detection."""
        if isinstance(item, (dict, list)):
            return str(sorted(str(item).lower()))
        return str(item).lower()

    def _resolve_value_conflict(self, target: Any, source: Any) -> Any:
        """Resolve conflicting values."""
        # If both are strings, check similarity
        if isinstance(target, str) and isinstance(source, str):
            similarity = self._string_similarity(target, source)
            if similarity > self.field_similarity_threshold:
                return target
            return [target, source]

        # Handle different types
        if type(target) != type(source):
            return [target, source]

        # Default: keep both values in array
        return [target, source]

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity."""
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()

        if s1 == s2:
            return 1.0

        return SequenceMatcher(None, s1, s2).ratio()