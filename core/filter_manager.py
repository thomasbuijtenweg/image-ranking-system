"""Filter manager for prompt-based image filtering."""

from typing import Dict, List, Set, Any, Optional
from collections import defaultdict


class FilterManager:
    """Manages filtering of images based on prompt word and CLIP tag criteria."""

    CLIP_BUCKETS = ('artists', 'roles', 'styles', 'settings')

    def __init__(self, data_manager, prompt_analyzer):
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer

        # Filter state — shared by prompt-word and CLIP-tag sources
        self.include_words: Set[str] = set()
        self.exclude_words: Set[str] = set()
        self.filter_logic = 'AND'  # 'AND' or 'OR'

        # Prompt-text word index
        self.word_index: Dict[str, Set[str]] = {}  # word -> set of image names
        self.index_built = False

        # CLIP tag index — flat (all buckets merged) + per-bucket
        self.clip_tag_index: Dict[str, Set[str]] = {}           # term -> images
        self.clip_tag_index_by_bucket: Dict[str, Dict[str, Set[str]]] = {
            b: {} for b in self.CLIP_BUCKETS
        }
        self.clip_index_built = False
    
    def build_word_index(self) -> None:
        """Build index of words to images for fast filtering."""
        self.word_index.clear()
        
        for image_name, stats in self.data_manager.image_stats.items():
            # Skip binned images
            if self.data_manager.is_image_binned(image_name):
                continue
                
            prompt = stats.get('prompt')
            if not prompt:
                continue
            
            # Extract words from prompt
            main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
            words = self.prompt_analyzer.extract_words(main_prompt)
            
            # Add to index
            for word in set(words):  # Use set to avoid duplicates
                if word not in self.word_index:
                    self.word_index[word] = set()
                self.word_index[word].add(image_name)
        
        self.index_built = True
        print(f"FilterManager: Built word index with {len(self.word_index)} unique words")

    def build_clip_index(self) -> None:
        """Build index of CLIP tags to images for fast filtering.

        Reads prompt_tags from the similarity manager (populated when the
        CLIP index is built). Each tag term is added to a flat index and
        to a per-bucket index so the UI can filter by bucket.
        """
        self.clip_tag_index.clear()
        for b in self.CLIP_BUCKETS:
            self.clip_tag_index_by_bucket[b].clear()

        sm = self.data_manager.similarity_manager
        if not sm or not sm.prompt_tags:
            # Don't mark as built — leave clip_index_built = False so the
            # next access retries once the similarity index has been loaded
            # or the async build completes.
            print("FilterManager: No CLIP tags available yet — will retry on next access.")
            return

        for image_name, tag_dict in sm.prompt_tags.items():
            if self.data_manager.is_image_binned(image_name):
                continue
            for bucket in self.CLIP_BUCKETS:
                for term in tag_dict.get(bucket, {}):
                    term_lower = term.lower()
                    # flat index
                    self.clip_tag_index.setdefault(term_lower, set()).add(image_name)
                    # per-bucket index
                    self.clip_tag_index_by_bucket[bucket].setdefault(
                        term_lower, set()).add(image_name)

        total = len(self.clip_tag_index)
        print(f"FilterManager: Built CLIP tag index with {total} unique terms")
        self.clip_index_built = True

    def rebuild_index_if_needed(self) -> None:
        """Rebuild prompt-word index if images have changed."""
        if not self.index_built or not self.word_index:
            self.build_word_index()

    def rebuild_clip_index_if_needed(self) -> None:
        """Rebuild CLIP tag index if not yet built."""
        if not self.clip_index_built:
            self.build_clip_index()
    
    def add_include_word(self, word: str) -> bool:
        """Add a word to the include filter."""
        word_lower = word.lower().strip()
        if not word_lower:
            return False
        
        # Remove from exclude if present
        self.exclude_words.discard(word_lower)
        
        # Add to include
        self.include_words.add(word_lower)
        return True
    
    def add_exclude_word(self, word: str) -> bool:
        """Add a word to the exclude filter."""
        word_lower = word.lower().strip()
        if not word_lower:
            return False
        
        # Remove from include if present
        self.include_words.discard(word_lower)
        
        # Add to exclude
        self.exclude_words.add(word_lower)
        return True
    
    def remove_include_word(self, word: str) -> bool:
        """Remove a word from the include filter."""
        word_lower = word.lower().strip()
        if word_lower in self.include_words:
            self.include_words.remove(word_lower)
            return True
        return False
    
    def remove_exclude_word(self, word: str) -> bool:
        """Remove a word from the exclude filter."""
        word_lower = word.lower().strip()
        if word_lower in self.exclude_words:
            self.exclude_words.remove(word_lower)
            return True
        return False
    
    def clear_filters(self) -> None:
        """Clear all filters."""
        self.include_words.clear()
        self.exclude_words.clear()
    
    def set_filter_logic(self, logic: str) -> None:
        """Set filter logic to 'AND' or 'OR'."""
        if logic in ['AND', 'OR']:
            self.filter_logic = logic
    
    def is_active(self) -> bool:
        """Check if any filters are active."""
        return len(self.include_words) > 0 or len(self.exclude_words) > 0
    
    def get_filtered_images(self) -> List[str]:
        """Get list of active images matching current filters.

        An image matches a word if that word appears in its prompt text
        (word_index) OR in its CLIP tags (clip_tag_index).  This lets users
        mix prompt-word and CLIP-tag filters freely in the same include/exclude
        sets.
        """
        self.rebuild_index_if_needed()
        self.rebuild_clip_index_if_needed()

        if not self.is_active():
            return self.data_manager.get_active_images()

        all_active = set(self.data_manager.get_active_images())

        def _images_for_word(word: str) -> Set[str]:
            """Images that have this word in prompt text OR CLIP tags."""
            return (self.word_index.get(word, set())
                    | self.clip_tag_index.get(word, set()))

        # Apply include filters
        if self.include_words:
            if self.filter_logic == 'AND':
                matching = all_active.copy()
                for word in self.include_words:
                    matching &= _images_for_word(word)
            else:  # OR
                matching = set()
                for word in self.include_words:
                    matching |= _images_for_word(word)
                matching &= all_active
        else:
            matching = all_active.copy()

        # Apply exclude filters (always AND logic)
        for word in self.exclude_words:
            matching -= _images_for_word(word)

        return list(matching)
    
    def get_word_frequency(self, word: str) -> int:
        """Get frequency of a word in active images."""
        self.rebuild_index_if_needed()
        word_lower = word.lower().strip()
        return len(self.word_index.get(word_lower, set()))
    
    def search_words(self, pattern: str, limit: int = 50) -> List[tuple]:
        """
        Search for words matching a pattern.
        Returns list of (word, frequency) tuples.
        """
        self.rebuild_index_if_needed()
        pattern_lower = pattern.lower().strip()
        
        if not pattern_lower:
            # Return all words sorted by frequency
            results = [(word, len(images)) for word, images in self.word_index.items()]
        else:
            # Return matching words
            results = [
                (word, len(images)) 
                for word, images in self.word_index.items() 
                if pattern_lower in word
            ]
        
        # Sort by frequency (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def search_clip_words(self, pattern: str, bucket: Optional[str] = None,
                          limit: int = 100) -> List[tuple]:
        """Search CLIP tag terms matching a pattern, optionally filtered by bucket.

        Args:
            pattern: Substring to match (case-insensitive). Empty = return all.
            bucket:  One of 'artists'/'roles'/'styles'/'settings', or None for all.
            limit:   Maximum results.

        Returns:
            List of (term, frequency) tuples sorted by frequency descending.
        """
        self.rebuild_clip_index_if_needed()
        pattern_lower = pattern.lower().strip()

        if bucket and bucket in self.clip_tag_index_by_bucket:
            source = self.clip_tag_index_by_bucket[bucket]
        else:
            source = self.clip_tag_index

        if not pattern_lower:
            results = [(term, len(imgs)) for term, imgs in source.items()]
        else:
            results = [(term, len(imgs)) for term, imgs in source.items()
                       if pattern_lower in term]

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_clip_bucket_counts(self) -> Dict[str, int]:
        """Return the number of unique terms per CLIP bucket."""
        self.rebuild_clip_index_if_needed()
        return {b: len(self.clip_tag_index_by_bucket[b]) for b in self.CLIP_BUCKETS}

    def invalidate_clip_index(self) -> None:
        """Force the CLIP index to be rebuilt on next access."""
        self.clip_index_built = False
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get statistics about current filters."""
        total_active = len(self.data_manager.get_active_images())
        filtered_images = self.get_filtered_images()
        filtered_count = len(filtered_images)
        
        return {
            'total_active_images': total_active,
            'filtered_image_count': filtered_count,
            'filtered_percentage': (filtered_count / total_active * 100) if total_active > 0 else 0,
            'include_words': list(self.include_words),
            'exclude_words': list(self.exclude_words),
            'filter_logic': self.filter_logic,
            'is_active': self.is_active(),
            'total_unique_words': len(self.word_index),
            'total_clip_terms': len(self.clip_tag_index),
            'clip_bucket_counts': self.get_clip_bucket_counts()
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export filter state for saving."""
        return {
            'include_words': list(self.include_words),
            'exclude_words': list(self.exclude_words),
            'filter_logic': self.filter_logic
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import filter state from save."""
        self.include_words = set(state.get('include_words', []))
        self.exclude_words = set(state.get('exclude_words', []))
        self.filter_logic = state.get('filter_logic', 'AND')
