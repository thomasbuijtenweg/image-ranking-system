"""Enhanced Data Manager with image binning support - tier bounds system removed."""

import os
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager
from core.data_persistence import DataPersistence
from core.algorithm_settings import AlgorithmSettings
from core.similarity_manager import SimilarityManager


class DataManager:
    """Handles data persistence and ranking statistics with image binning."""
    
    def __init__(self):
        self.weight_manager = WeightManager()
        self.data_persistence = DataPersistence()
        self.algorithm_settings = AlgorithmSettings()
        self.similarity_manager = SimilarityManager()
        self.reset_data()
    
    def reset_data(self):
        """Reset all data to initial state."""
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        self.metadata_cache = {}
        self.binned_images = set()  # Track binned image filenames
        self.weight_manager.reset_to_defaults()
        self.algorithm_settings.reset_to_defaults()
    
    def bin_image(self, image_name: str) -> bool:
        """
        Mark an image as binned and remove it from active ranking.
        
        Args:
            image_name: Name of the image to bin
            
        Returns:
            True if successfully binned, False if already binned
        """
        # Ensure binned_images exists
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        
        if image_name in self.binned_images:
            return False
        
        self.binned_images.add(image_name)
        print(f"Image '{image_name}' has been binned")
        return True
    
    def purge_binned_image_votes(self, binned_image: str) -> Dict[str, Any]:
        """
        Remove all vote history involving a binned image from active images.
        
        For every active (non-binned) image that was previously compared against
        the binned image, this method:
        - Removes all matchup_history entries involving the binned image
        - Removes the binned image from tested_against
        - Recalculates wins, losses, votes from remaining matchup history
        - Replays tier progression from the remaining matchup history
        
        Args:
            binned_image: Name of the image that was binned
            
        Returns:
            Dict with purge statistics
        """
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        
        affected_images = 0
        total_votes_removed = 0
        
        for img_name, stats in self.image_stats.items():
            # Skip the binned image itself and any other binned images
            if img_name == binned_image or img_name in self.binned_images:
                continue
            
            # Check if this image has any matchup history with the binned image
            matchup_history = stats.get('matchup_history', [])
            original_len = len(matchup_history)
            
            # Filter out all matchups involving the binned image
            filtered_history = [
                (opponent, won, vote_num) for opponent, won, vote_num in matchup_history
                if opponent != binned_image
            ]
            
            votes_removed = original_len - len(filtered_history)
            if votes_removed == 0:
                continue
            
            affected_images += 1
            total_votes_removed += votes_removed
            
            # Remove binned image from tested_against
            tested_against = stats.get('tested_against', set())
            if isinstance(tested_against, set):
                tested_against.discard(binned_image)
            elif isinstance(tested_against, list):
                stats['tested_against'] = set(t for t in tested_against if t != binned_image)
            
            # Recalculate stats from the filtered matchup history
            new_wins = sum(1 for _, won, _ in filtered_history if won)
            new_losses = sum(1 for _, won, _ in filtered_history if not won)
            new_votes = new_wins + new_losses
            
            # Replay tier progression from scratch
            new_tier = 0
            new_tier_history = [0]
            for _, won, _ in filtered_history:
                new_tier += 1 if won else -1
                new_tier_history.append(new_tier)
            
            # Capture old tier before overwriting
            old_tier = stats['current_tier']
            
            # Apply recalculated values
            stats['matchup_history'] = filtered_history
            stats['wins'] = new_wins
            stats['losses'] = new_losses
            stats['votes'] = new_votes
            stats['current_tier'] = new_tier
            stats['tier_history'] = new_tier_history
            
            print(f"  Purged {votes_removed} vote(s) involving '{binned_image}' from '{img_name}' "
                  f"(tier: {old_tier} -> {new_tier})")
        
        print(f"Vote purge complete for '{binned_image}': "
              f"{affected_images} images affected, {total_votes_removed} votes removed")
        
        return {
            'affected_images': affected_images,
            'total_votes_removed': total_votes_removed
        }
    
    def purge_all_binned_image_votes(self) -> Dict[str, Any]:
        """
        Purge stale votes for all currently binned images.
        
        Cleans up save files where images were binned before the vote-purge
        feature existed. Idempotent - safe to run multiple times.
        
        Returns:
            Dict with purge statistics
        """
        if not self.binned_images:
            print("No binned images found - nothing to purge")
            return {'total_affected': 0, 'total_removed': 0, 'binned_processed': 0}
        
        total_affected = 0
        total_removed = 0
        
        for binned_image in list(self.binned_images):
            # Check if any active image still has matchup history with this binned image
            has_stale_votes = any(
                binned_image in [opp for opp, _, _ in stats.get('matchup_history', [])]
                for img_name, stats in self.image_stats.items()
                if img_name != binned_image and img_name not in self.binned_images
            )
            
            if has_stale_votes:
                result = self.purge_binned_image_votes(binned_image)
                total_affected += result['affected_images']
                total_removed += result['total_votes_removed']
        
        if total_removed > 0:
            print(f"Purge complete: {total_removed} stale vote(s) removed "
                  f"from {total_affected} image(s) across {len(self.binned_images)} binned image(s)")
        else:
            print("Purge complete: no stale votes found (already clean)")
        
        return {
            'total_affected': total_affected,
            'total_removed': total_removed,
            'binned_processed': len(self.binned_images)
        }
    
    def is_image_binned(self, image_name: str) -> bool:
        """Check if an image is binned."""
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        return image_name in self.binned_images
    
    def get_active_images(self) -> list:
        """Get list of active (non-binned) image names."""
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        return [img for img in self.image_stats.keys() if img not in self.binned_images]
    
    def get_binned_images(self) -> list:
        """Get list of binned image names."""
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        return list(self.binned_images)
    
    def get_active_image_count(self) -> int:
        """Get count of active (non-binned) images."""
        return len(self.get_active_images())
    
    def get_binned_image_count(self) -> int:
        """Get count of binned images."""
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        return len(self.binned_images)
    
    def has_pair_been_tested(self, img1: str, img2: str) -> bool:
        """Check if two images have already been tested against each other."""
        if img1 not in self.image_stats or img2 not in self.image_stats:
            return False
    
        # Check if img2 is in img1's tested_against set
        return img2 in self.image_stats[img1].get('tested_against', set())    
    
    def record_vote(self, winner: str, loser: str) -> None:
        """Record a vote between two images."""
        self.vote_count += 1
        self.image_stats[winner]['tested_against'].add(loser)
        self.image_stats[loser]['tested_against'].add(winner)    
        
        # Calculate target tiers (no bounds checking - tiers can move freely)
        winner_current_tier = self.image_stats[winner].get('current_tier', 0)
        loser_current_tier = self.image_stats[loser].get('current_tier', 0)
        
        winner_target_tier = winner_current_tier + 1
        loser_target_tier = loser_current_tier - 1
        
        # Update winner stats
        winner_stats = self.image_stats[winner]
        winner_stats['votes'] += 1
        winner_stats['wins'] += 1
        winner_stats['current_tier'] = winner_target_tier
        winner_stats['tier_history'].append(winner_target_tier)
        winner_stats['last_voted'] = self.vote_count
        winner_stats['matchup_history'].append((loser, True, self.vote_count))
        
        # Update loser stats
        loser_stats = self.image_stats[loser]
        loser_stats['votes'] += 1
        loser_stats['losses'] += 1
        loser_stats['current_tier'] = loser_target_tier
        loser_stats['tier_history'].append(loser_target_tier)
        loser_stats['last_voted'] = self.vote_count
        loser_stats['matchup_history'].append((winner, False, self.vote_count))
    
    def save_to_file(self, filename: str, filter_state: Optional[Dict[str, Any]] = None) -> bool:
        """Save all ranking data including tested pairs and optional filter state."""
        # Convert sets to lists for JSON serialization
        serializable_stats = {}
        for img_name, stats in self.image_stats.items():
            stats_copy = stats.copy()
            # Convert set to list for JSON
            if 'tested_against' in stats_copy:
                stats_copy['tested_against'] = list(stats_copy['tested_against'])
            serializable_stats[img_name] = stats_copy
        
        # Prepare core data
        core_data = {
            'image_folder': self.image_folder,
            'vote_count': self.vote_count,
            'image_stats': serializable_stats,  # Use serializable version
            'metadata_cache': self.metadata_cache,
            'binned_images': list(self.binned_images)
        }
        
        # Gather all settings
        weight_data = self.weight_manager.export_to_data()
        algorithm_settings = self.algorithm_settings.export_settings()
        
        # Prepare complete save data with optional filter state
        save_data = self.data_persistence.prepare_save_data(
            core_data, weight_data, algorithm_settings, filter_state)
        
        # Save to file
        return self.data_persistence.save_to_file(filename, save_data)

    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """Load ranking data including tested pairs."""
        # Load data from file
        success, data, error_msg = self.data_persistence.load_from_file(filename)
        if not success:
            return False, error_msg
        
        # Validate and fix data
        data = self.data_persistence.validate_and_fix_data(data)
        
        # Extract core data
        core_data = self.data_persistence.extract_core_data(data)
        self.image_folder = core_data['image_folder']
        self.vote_count = core_data['vote_count']
        self.image_stats = core_data['image_stats']
        self.metadata_cache = core_data['metadata_cache']
        self.binned_images = core_data['binned_images']
        
        # Convert tested_against lists back to sets
        for img_name, stats in self.image_stats.items():
            if 'tested_against' in stats and isinstance(stats['tested_against'], list):
                stats['tested_against'] = set(stats['tested_against'])
            elif 'tested_against' not in stats:
                stats['tested_against'] = set()  # Add missing field for old saves
        
        # Load other settings
        self.weight_manager.load_from_data(data)
        self.algorithm_settings.load_settings(data)
        
        # Load similarity cache if one exists for this folder
        if self.image_folder:
            self.similarity_manager.load_cache(self.image_folder)
        
        # Update existing images with strategic timing
        self._update_existing_images_with_strategic_timing()
        
        # Initialize all image stats (ensures tested_against field exists)
        for image_filename in self.image_stats:
            self.initialize_image_stats(image_filename)
        
        return True, ""
    
    def get_pair_stats(self) -> Dict[str, Any]:
        """Get statistics about tested pairs."""
        total_pairs_tested = 0
        total_possible_pairs = 0
        
        active_images = self.get_active_images()
        total_possible_pairs = len(active_images) * (len(active_images) - 1) // 2
        
        # Count unique tested pairs
        tested_pairs = set()
        for img_name, stats in self.image_stats.items():
            if not self.is_image_binned(img_name):  # Only count active images
                tested_against = stats.get('tested_against', set())
                for other_img in tested_against:
                    if not self.is_image_binned(other_img):  # Only count active pairs
                        # Add normalized pair (sorted order to avoid duplicates)
                        pair = tuple(sorted([img_name, other_img]))
                        tested_pairs.add(pair)
        
        total_pairs_tested = len(tested_pairs)
        
        coverage_percentage = (total_pairs_tested / max(total_possible_pairs, 1)) * 100
        
        return {
            'total_pairs_tested': total_pairs_tested,
            'total_possible_pairs': total_possible_pairs,
            'coverage_percentage': coverage_percentage,
            'untested_pairs_remaining': total_possible_pairs - total_pairs_tested
        }
    
    def get_tier_distribution(self) -> Dict[int, int]:
        """Get the distribution of ACTIVE images across tiers."""
        if not hasattr(self, 'binned_images'):
            self.binned_images = set()
        
        tier_counts = defaultdict(int)
        for img_name, stats in self.image_stats.items():
            if img_name not in self.binned_images:  # Only active images
                tier_counts[stats['current_tier']] += 1
        return dict(tier_counts)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics with enhanced error handling and backward compatibility."""
        try:
            # Ensure binned_images exists
            if not hasattr(self, 'binned_images'):
                self.binned_images = set()
            
            active_images = self.get_active_images()
            total_active_images = len(active_images)
            total_binned_images = len(self.binned_images)
            total_images = total_active_images + total_binned_images
            
            if not active_images:
                return {
                    'total_images': total_images,  # For backward compatibility
                    'total_active_images': 0,
                    'total_binned_images': total_binned_images,
                    'total_votes': self.vote_count,
                    'avg_votes_per_image': 0,  # For backward compatibility
                    'avg_votes_per_active_image': 0,
                    'tier_distribution': {}
                }
            
            total_votes = self.vote_count
            
            # Calculate average votes per active image
            try:
                total_active_votes = sum(
                    self.image_stats[img]['votes'] for img in active_images
                    if img in self.image_stats
                )
                avg_votes_per_active_image = total_active_votes / total_active_images
            except (KeyError, ZeroDivisionError, TypeError) as e:
                print(f"Error calculating average votes per active image: {e}")
                avg_votes_per_active_image = 0
            
            # Calculate average votes per total image (for backward compatibility)
            try:
                total_all_votes = sum(
                    self.image_stats[img]['votes'] for img in self.image_stats
                    if img in self.image_stats
                )
                avg_votes_per_image = total_all_votes / total_images if total_images > 0 else 0
            except (KeyError, ZeroDivisionError, TypeError) as e:
                print(f"Error calculating average votes per total image: {e}")
                avg_votes_per_image = 0
            
            return {
                'total_images': total_images,  # For backward compatibility
                'total_active_images': total_active_images,
                'total_binned_images': total_binned_images,
                'total_votes': total_votes,
                'avg_votes_per_image': avg_votes_per_image,  # For backward compatibility
                'avg_votes_per_active_image': avg_votes_per_active_image,
                'tier_distribution': self.get_tier_distribution()
            }
            
        except Exception as e:
            print(f"Error in get_overall_statistics: {e}")
            # Return safe defaults
            return {
                'total_images': len(self.image_stats),
                'total_active_images': 0,
                'total_binned_images': 0,
                'total_votes': self.vote_count,
                'avg_votes_per_image': 0,
                'avg_votes_per_active_image': 0,
                'tier_distribution': {}
            }
    
    # Weight manager delegations
    def get_left_weights(self) -> Dict[str, float]:
        return self.weight_manager.get_left_weights()
    
    def get_right_weights(self) -> Dict[str, float]:
        return self.weight_manager.get_right_weights()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        self.weight_manager.set_left_weights(weights)
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        self.weight_manager.set_right_weights(weights)
    
    def get_left_priority_preferences(self) -> Dict[str, bool]:
        return self.weight_manager.get_left_priority_preferences()
    
    def get_right_priority_preferences(self) -> Dict[str, bool]:
        return self.weight_manager.get_right_priority_preferences()
    
    def set_left_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        self.weight_manager.set_left_priority_preferences(preferences)
    
    def set_right_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        self.weight_manager.set_right_priority_preferences(preferences)
    
    def initialize_image_stats(self, image_filename: str) -> None:
        """Initialize stats for a new image with strategic placement."""
        if image_filename not in self.image_stats:
            strategic_last_voted = self._calculate_strategic_last_voted(image_filename)
            
            self.image_stats[image_filename] = {
                'votes': 0,
                'wins': 0,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': strategic_last_voted,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None,
                'tested_against': set()
            }
        else:
            # Ensure required fields exist
            required_fields = {
                'votes': 0,
                'wins': 0,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': -1,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None,
                'tested_against': set()
            }
            
            for field, default_value in required_fields.items():
                if field not in self.image_stats[image_filename]:
                    self.image_stats[image_filename][field] = default_value
        
        self.restore_metadata_from_cache(image_filename)
    
    def _calculate_strategic_last_voted(self, image_filename: str) -> int:
        """Calculate strategic last_voted value for a new image."""
        if not self.image_stats or image_filename in self.image_stats:
            return 0
        
        highest_last_voted = -1
        for stats in self.image_stats.values():
            last_voted = stats.get('last_voted', -1)
            if last_voted > highest_last_voted:
                highest_last_voted = last_voted
        
        if highest_last_voted == -1:
            return 0
        elif highest_last_voted == 0:
            return 0
        else:
            return 1 + (highest_last_voted // 2)
    
    def get_image_stats(self, image_filename: str) -> Dict[str, Any]:
        """Get statistics for a specific image."""
        return self.image_stats.get(image_filename, {})
    
    def _update_existing_images_with_strategic_timing(self) -> None:
        """Update existing images that have never been voted on to use strategic timing."""
        if not self.image_stats:
            return
        
        highest_last_voted = -1
        for stats in self.image_stats.values():
            last_voted = stats.get('last_voted', -1)
            if last_voted > highest_last_voted:
                highest_last_voted = last_voted
        
        if highest_last_voted == -1:
            return
        
        strategic_value = 0 if highest_last_voted == 0 else 1 + (highest_last_voted // 2)
        
        updated_count = 0
        for image_filename, stats in self.image_stats.items():
            if stats.get('last_voted', -1) == -1:
                stats['last_voted'] = strategic_value
                updated_count += 1
        
        if updated_count > 0:
            print(f"Updated {updated_count} never-voted images with strategic timing")
    
    def set_image_metadata(self, image_filename: str, prompt: Optional[str] = None, 
                          display_metadata: Optional[str] = None) -> None:
        """Set metadata for an image and update cache."""
        if image_filename in self.image_stats:
            if prompt is not None:
                self.image_stats[image_filename]['prompt'] = prompt
            if display_metadata is not None:
                self.image_stats[image_filename]['display_metadata'] = display_metadata
            
            self.update_metadata_cache(image_filename, prompt, display_metadata)
    
    def update_metadata_cache(self, image_filename: str, prompt: Optional[str] = None, 
                             display_metadata: Optional[str] = None) -> None:
        """Update the metadata cache for an image."""
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    
                    if image_filename not in self.metadata_cache:
                        self.metadata_cache[image_filename] = {}
                    
                    cache_entry = self.metadata_cache[image_filename]
                    
                    if prompt is not None:
                        cache_entry['prompt'] = prompt
                    if display_metadata is not None:
                        cache_entry['display_metadata'] = display_metadata
                    
                    cache_entry['last_modified'] = current_mtime
        except OSError:
            pass

    def restore_metadata_from_cache(self, image_filename: str) -> None:
        """Restore metadata from cache if available and valid."""
        if image_filename not in self.metadata_cache:
            return
        
        cached_data = self.metadata_cache[image_filename]
        
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    cached_mtime = cached_data.get('last_modified', 0)
                    
                    if abs(current_mtime - cached_mtime) < 1.0:
                        stats = self.image_stats[image_filename]
                        stats['prompt'] = cached_data.get('prompt')
                        stats['display_metadata'] = cached_data.get('display_metadata')
                        return
        except (OSError, KeyError):
            pass
        
        del self.metadata_cache[image_filename]
