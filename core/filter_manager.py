"""Filter manager for prompt-based image filtering."""

from typing import Dict, List, Set, Any, Optional
from collections import defaultdict


class FilterManager:
    """Manages filtering of images based on prompt word criteria."""
    
    def __init__(self, data_manager, prompt_analyzer):
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer
        
        # Filter state
        self.include_words: Set[str] = set()
        self.exclude_words: Set[str] = set()
        self.filter_logic = 'AND'  # 'AND' or 'OR'
        
        # Cached word index for performance
        self.word_index: Dict[str, Set[str]] = {}  # word -> set of image names
        self.index_built = False
    
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
    
    def rebuild_index_if_needed(self) -> None:
        """Rebuild index if images have changed."""
        if not self.index_built or not self.word_index:
            self.build_word_index()
    
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
        """Get list of active images matching current filters."""
        self.rebuild_index_if_needed()
        
        # If no filters, return all active images
        if not self.is_active():
            return self.data_manager.get_active_images()
        
        # Get all active images
        all_active = set(self.data_manager.get_active_images())
        
        # Apply include filters
        if self.include_words:
            if self.filter_logic == 'AND':
                # Image must have ALL include words
                matching = all_active.copy()
                for word in self.include_words:
                    word_images = self.word_index.get(word, set())
                    matching &= word_images  # Intersection
            else:  # OR logic
                # Image must have ANY include word
                matching = set()
                for word in self.include_words:
                    word_images = self.word_index.get(word, set())
                    matching |= word_images  # Union
                matching &= all_active  # Only active images
        else:
            matching = all_active.copy()
        
        # Apply exclude filters (always AND logic for excludes)
        for word in self.exclude_words:
            word_images = self.word_index.get(word, set())
            matching -= word_images  # Remove images with excluded word
        
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
            'total_unique_words': len(self.word_index)
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
