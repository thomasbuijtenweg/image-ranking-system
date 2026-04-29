"""Enhanced Data Manager with image binning support - tier bounds system removed."""

import os
import time
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager
from core.data_persistence import DataPersistence
from core.algorithm_settings import AlgorithmSettings
from core.similarity_manager import SimilarityManager
from core.binning_service import BinningService
from core.cutline_service import CutlineService
from core.logging_setup import get_logger

log = get_logger(__name__)


class DataManager:
    """Handles data persistence and ranking statistics with image binning."""
    
    def __init__(self):
        self.weight_manager = WeightManager()
        self.data_persistence = DataPersistence()
        self.algorithm_settings = AlgorithmSettings()
        self.similarity_manager = SimilarityManager()
        self.binning = BinningService(self)
        self.cutline = CutlineService(self)
        self.reset_data()
    
    # binned_images is owned by BinningService; expose it here as a property
    # so existing callers that read or write data_manager.binned_images
    # continue to work transparently during the refactor.
    @property
    def binned_images(self) -> set:
        return self.binning.binned_images
    
    @binned_images.setter
    def binned_images(self, value) -> None:
        # Coerce to set in case a list or other iterable is assigned
        # (e.g. load paths that pass in the raw JSON-parsed list).
        self.binning.binned_images = value if isinstance(value, set) else set(value)
    
    def reset_data(self):
        """Reset all data to initial state."""
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        self.metadata_cache = {}
        self.binning.binned_images = set()  # Track binned image filenames
        self.weight_manager.reset_to_defaults()
        self.algorithm_settings.reset_to_defaults()
    
    def bin_image(self, image_name: str) -> bool:
        """Delegate: mark an image as binned. Returns False if already binned."""
        return self.binning.bin_image(image_name)
    
    def purge_binned_image_votes(self, binned_image: str, verbose: bool = True) -> Dict[str, Any]:
        """Delegate: remove all vote history involving a binned image from active images."""
        return self.binning.purge_binned_image_votes(binned_image, verbose=verbose)
    
    def purge_all_binned_image_votes(self) -> Dict[str, Any]:
        """Delegate: purge stale votes for all currently binned images."""
        return self.binning.purge_all_binned_image_votes()
    
    def export_top_images(self, n: int) -> list:
        """Delegate: prepare the top N images for export (full reset)."""
        return self.binning.export_top_images(n)

    def export_specific_images(self, names: list) -> list:
        """Delegate: export a caller-supplied list of images (full reset)."""
        return self.binning.export_specific_images(names)

    def is_image_binned(self, image_name: str) -> bool:
        """Delegate: check if an image is binned."""
        return self.binning.is_image_binned(image_name)
    
    def get_active_images(self) -> list:
        """Get list of active (non-binned) image names."""
        return [img for img in self.image_stats.keys() if img not in self.binned_images]
    
    def get_binned_images(self) -> list:
        """Delegate: get list of binned image names."""
        return self.binning.get_binned_images()
    
    def get_active_image_count(self) -> int:
        """Get count of active (non-binned) images."""
        return len(self.get_active_images())
    
    def get_binned_image_count(self) -> int:
        """Delegate: get count of binned images."""
        return self.binning.get_binned_image_count()
    
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
        """Save all ranking data with lossless space optimizations.

        Two fields are stripped before serialization and rebuilt on load:
          1. stats['tested_against']  — derivable from matchup_history (every
             opponent in the history is a tested pair by construction).
          2. metadata_cache[img]['prompt'] and ['display_metadata'] — these
             are already stored per-image in image_stats. The cache only
             needs 'last_modified' to validate the mtime on reload.
        """
        # Serialize image_stats, stripping tested_against (derivable on load).
        serializable_stats = {}
        for img_name, stats in self.image_stats.items():
            stats_copy = stats.copy()
            stats_copy.pop('tested_against', None)
            serializable_stats[img_name] = stats_copy

        # Slim metadata_cache to just the mtime per image. Prompt and
        # display_metadata are already in image_stats — no reason to store
        # them twice. Drop entries that have no mtime to store.
        minimal_cache = {
            name: {'last_modified': entry['last_modified']}
            for name, entry in self.metadata_cache.items()
            if isinstance(entry, dict) and 'last_modified' in entry
        }

        # Prepare core data
        core_data = {
            'image_folder': self.image_folder,
            'vote_count': self.vote_count,
            'image_stats': serializable_stats,
            'metadata_cache': minimal_cache,
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
        """Load ranking data including tested pairs.

        Emits step-by-step progress logging so the user can see what's
        happening — each numbered step prints what it's doing, how many
        items it's processing, and how long it took. A stuck step is
        easy to spot because the next [Load] line never appears.
        """
        t_start = time.perf_counter()
        log.info("[Load] ========== Loading save file ==========")
        log.info("[Load] File: %s", filename)

        # --- Step 1/8: read and parse JSON ---
        log.info("[Load] Step 1/8: Reading JSON file from disk...")
        t = time.perf_counter()
        success, data, error_msg = self.data_persistence.load_from_file(filename)
        if not success:
            log.error("[Load] FAILED at step 1: %s", error_msg)
            return False, error_msg
        log.info("[Load] Step 1/8: Parsed JSON in %.0f ms", (time.perf_counter()-t)*1000)

        # --- Step 2/8: validate/fix data ---
        log.info("[Load] Step 2/8: Validating data integrity...")
        t = time.perf_counter()
        data = self.data_persistence.validate_and_fix_data(data)
        log.info("[Load] Step 2/8: Validated in %.0f ms", (time.perf_counter()-t)*1000)

        # --- Step 3/8: extract core data ---
        log.info("[Load] Step 3/8: Extracting core data...")
        t = time.perf_counter()
        core_data = self.data_persistence.extract_core_data(data)
        self.image_folder   = core_data['image_folder']
        self.vote_count     = core_data['vote_count']
        self.image_stats    = core_data['image_stats']
        self.metadata_cache = core_data['metadata_cache']
        self.binned_images  = core_data['binned_images']
        n_images = len(self.image_stats)
        n_binned = len(self.binned_images)
        log.info("[Load] Step 3/8: %d images, %d binned, %d total votes | folder: %s",
                 n_images, n_binned, self.vote_count, self.image_folder)
        log.info("[Load] Step 3/8: Done in %.0f ms", (time.perf_counter()-t)*1000)

        # --- Step 4/8: rebuild tested_against ---
        log.info("[Load] Step 4/8: Rebuilding tested_against index for %d images...", n_images)
        t = time.perf_counter()
        legacy_count = 0
        derived_count = 0
        total_pairs = 0
        for img_name, stats in self.image_stats.items():
            if 'tested_against' in stats and isinstance(stats['tested_against'], list):
                # Old format
                stats['tested_against'] = set(stats['tested_against'])
                legacy_count += 1
            else:
                # New format — derive from matchup_history
                matchup_history = stats.get('matchup_history', [])
                stats['tested_against'] = {entry[0] for entry in matchup_history if entry}
                derived_count += 1
            total_pairs += len(stats['tested_against'])
        log.info("[Load] Step 4/8: Rebuilt in %.0f ms (%d legacy, %d derived, %d total pair entries)",
                 (time.perf_counter()-t)*1000, legacy_count, derived_count, total_pairs)

        # --- Step 5/8: load weights + algorithm settings ---
        log.info("[Load] Step 5/8: Loading weight manager and algorithm settings...")
        t = time.perf_counter()
        self.weight_manager.load_from_data(data)
        self.algorithm_settings.load_settings(data)
        log.info("[Load] Step 5/8: Done in %.0f ms", (time.perf_counter()-t)*1000)

        # --- Step 6/8: load similarity (CLIP) cache ---
        log.info("[Load] Step 6/8: Loading CLIP similarity cache...")
        t = time.perf_counter()
        if self.image_folder:
            loaded = self.similarity_manager.load_cache(self.image_folder)
            if loaded:
                n_emb = len(self.similarity_manager.filenames)
                log.info("[Load] Step 6/8: Loaded %d embeddings in %.0f ms",
                         n_emb, (time.perf_counter()-t)*1000)
            else:
                log.info("[Load] Step 6/8: No CLIP cache found for this folder (took %.0f ms to check)",
                         (time.perf_counter()-t)*1000)
        else:
            log.info("[Load] Step 6/8: Skipped (no image folder set)")

        # --- Step 7/8: purge stale votes from binned images ---
        if self.binned_images:
            log.info("[Load] Step 7/8: Purging stale votes from %d binned image(s)...", n_binned)
            t = time.perf_counter()
            self.purge_all_binned_image_votes()
            log.info("[Load] Step 7/8: Purge complete in %.0f ms", (time.perf_counter()-t)*1000)
        else:
            log.info("[Load] Step 7/8: No binned images to purge — skipped")

        # --- Step 8/8: initialise image stats + restore metadata ---
        log.info("[Load] Step 8/8: Initialising per-image stats for %d images...", n_images)
        t = time.perf_counter()
        self._update_existing_images_with_strategic_timing()
        # Loop with progress reporting every 500 images so large datasets
        # don't feel stuck during the per-image initialisation pass.
        progress_step = 500 if n_images >= 1000 else (100 if n_images >= 200 else 0)
        for i, image_filename in enumerate(self.image_stats):
            self.initialize_image_stats(image_filename)
            if progress_step and (i + 1) % progress_step == 0:
                log.debug("[Load]   ...processed %d/%d images (%.1fs elapsed)",
                          i + 1, n_images, time.perf_counter()-t)
        log.info("[Load] Step 8/8: Done in %.0f ms", (time.perf_counter()-t)*1000)

        total_ms = (time.perf_counter() - t_start) * 1000
        log.info("[Load] ========== Load complete in %.0f ms (%d images, %d votes) ==========",
                 total_ms, n_images, self.vote_count)
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
    
    # ------------------------------------------------------------------
    # Cutline zone methods
    # ------------------------------------------------------------------

    def get_cutline_tier(self) -> Optional[int]:
        """Delegate: return the tier value at the cutline position."""
        return self.cutline.get_cutline_tier()

    def _get_zone_min_votes(self, tier_distance: int) -> int:
        """Delegate: min votes required to confirm an image at `tier_distance` from cutline."""
        return self.cutline._get_zone_min_votes(tier_distance)

    def get_zone(self, image_name: str, cutline: Optional[int] = None) -> str:
        """Delegate: classify an image into a cutline zone."""
        return self.cutline.get_zone(image_name, cutline=cutline)

    def get_zone_counts(self) -> Dict[str, Any]:
        """Delegate: return a dict of zone counts and cutline metadata."""
        return self.cutline.get_zone_counts()

    def get_progress_summary(self) -> Dict[str, Any]:
        """Delegate: return zone counts plus resolution percentage."""
        return self.cutline.get_progress_summary()

    def get_tier_distribution(self) -> Dict[int, int]:
        """Get the distribution of ACTIVE images across tiers."""
        tier_counts = defaultdict(int)
        for img_name, stats in self.image_stats.items():
            if img_name not in self.binned_images:  # Only active images
                tier_counts[stats['current_tier']] += 1
        return dict(tier_counts)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics with enhanced error handling and backward compatibility."""
        try:
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
                log.error("Error calculating average votes per active image: %s", e)
                avg_votes_per_active_image = 0
            
            # Calculate average votes per total image (for backward compatibility)
            try:
                total_all_votes = sum(
                    self.image_stats[img]['votes'] for img in self.image_stats
                    if img in self.image_stats
                )
                avg_votes_per_image = total_all_votes / total_images if total_images > 0 else 0
            except (KeyError, ZeroDivisionError, TypeError) as e:
                log.error("Error calculating average votes per total image: %s", e)
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
            log.error("Error in get_overall_statistics: %s", e)
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
            log.info("Updated %d never-voted images with strategic timing", updated_count)
    
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
        """Update the metadata cache for an image.

        The cache now only records the file mtime — prompt and display_metadata
        are already stored per-image in image_stats, so duplicating them here
        would just bloat the save file. The prompt/display_metadata arguments
        are kept for API compatibility but are no longer written to the cache.
        """
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    
                    if image_filename not in self.metadata_cache:
                        self.metadata_cache[image_filename] = {}
                    
                    self.metadata_cache[image_filename]['last_modified'] = current_mtime
        except OSError:
            pass

    def restore_metadata_from_cache(self, image_filename: str) -> None:
        """Restore metadata from cache if available and valid.

        Safe for both legacy caches (which stored the full prompt) and the
        optimised cache (which stores only 'last_modified'). Never overwrites
        an existing image_stats value with None.
        """
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
                        # Only copy values actually present in the cache.
                        # Legacy caches include prompt/display_metadata;
                        # optimised caches do not, and image_stats already
                        # has the correct values from the save file.
                        if 'prompt' in cached_data and cached_data['prompt'] is not None:
                            stats['prompt'] = cached_data['prompt']
                        if 'display_metadata' in cached_data and cached_data['display_metadata'] is not None:
                            stats['display_metadata'] = cached_data['display_metadata']
                        return
        except (OSError, KeyError):
            pass
        
        del self.metadata_cache[image_filename]
