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
    
    def purge_binned_image_votes(self, binned_image: str, verbose: bool = True) -> Dict[str, Any]:
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
                  f"(tier: {old_tier} -> {new_tier})") if verbose else None
        
        print(f"Vote purge complete for '{binned_image}': "
              f"{affected_images} images affected, {total_votes_removed} votes removed") if verbose else None
        
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
        n_binned = len(self.binned_images)
        # For bulk purges, emit a single progress line every ~20 images
        # instead of per-image spam. Threshold chosen so small datasets
        # still show per-image output for debugging.
        quiet = n_binned > 20
        progress_step = max(1, n_binned // 10)  # ~10 updates across the run

        for idx, binned_image in enumerate(list(self.binned_images)):
            # Check if any active image still has matchup history with this binned image
            has_stale_votes = any(
                binned_image in [opp for opp, _, _ in stats.get('matchup_history', [])]
                for img_name, stats in self.image_stats.items()
                if img_name != binned_image and img_name not in self.binned_images
            )

            if has_stale_votes:
                result = self.purge_binned_image_votes(binned_image, verbose=not quiet)
                total_affected += result['affected_images']
                total_removed += result['total_votes_removed']

            if quiet and (idx + 1) % progress_step == 0:
                print(f"  [Purge] ...processed {idx + 1}/{n_binned} binned images "
                      f"({total_removed} votes removed so far)")

        if total_removed > 0:
            print(f"Purge complete: {total_removed} stale vote(s) removed "
                  f"from {total_affected} image(s) across {n_binned} binned image(s)")
        else:
            print("Purge complete: no stale votes found (already clean)")

        return {
            'total_affected': total_affected,
            'total_removed': total_removed,
            'binned_processed': n_binned
        }
    
    def export_top_images(self, n: int) -> list:
        """Identify and prepare the top N images for export (full reset).

        Operation order is critical for correctness when exported images have
        voted against each other:

        1. Sort active images by tier (then wins as tiebreak), take top N.
        2. Mark ALL of them as binned atomically — before any purge runs.
           This ensures that when we purge image A's votes, image B (also
           exported) is already in binned_images and is safely skipped by
           purge_binned_image_votes(), preventing cross-vote corrections from
           distorting each other.
        3. Purge each exported image's vote history from the remaining active
           images in sequence.
        4. Fully wipe the exported images from image_stats, metadata_cache,
           and binned_images — as if they were never in the system.
        5. Return the list of filenames so the caller can move the files.

        Args:
            n: Number of top-ranked images to export.

        Returns:
            List of image filenames that were prepared for export.
        """
        active = self.get_active_images()
        if not active:
            return []

        n = min(n, len(active))

        # Step 1: Sort by tier desc, wins desc as tiebreak
        sorted_active = sorted(
            active,
            key=lambda img: (
                self.image_stats[img].get('current_tier', 0),
                self.image_stats[img].get('wins', 0)
            ),
            reverse=True
        )
        to_export = sorted_active[:n]

        print(f"\n[Export] Preparing to export top {len(to_export)} image(s)...")
        for img in to_export:
            tier  = self.image_stats[img].get('current_tier', 0)
            votes = self.image_stats[img].get('votes', 0)
            wins  = self.image_stats[img].get('wins', 0)
            print(f"  {img}  (tier={tier}, votes={votes}, wins={wins})")

        # Step 2: Mark ALL as binned atomically before any purge
        for img in to_export:
            self.bin_image(img)
        print(f"[Export] Marked {len(to_export)} image(s) as binned.")

        # Step 3: Purge each exported image's votes from remaining active images
        total_votes_removed = 0
        for img in to_export:
            result = self.purge_binned_image_votes(img)
            total_votes_removed += result['total_votes_removed']
        print(f"[Export] Vote purge complete — {total_votes_removed} vote(s) removed from active images.")

        # Step 4: Full wipe — remove from all data structures
        for img in to_export:
            self.image_stats.pop(img, None)
            self.binned_images.discard(img)
            self.metadata_cache.pop(img, None)
        print(f"[Export] Wiped {len(to_export)} image(s) from data. Export ready.\n")

        return to_export

    def export_specific_images(self, names: list) -> list:
        """Export a caller-supplied list of images (full reset).

        Same atomic bin-all → purge → wipe sequence as export_top_images,
        but the caller decides which images to include (e.g. after the user
        has toggled images in the preview window).

        Returns the list of names that were actually processed (skips any
        name not in image_stats or already binned).
        """
        active_set = set(self.get_active_images())
        to_export = [n for n in names if n in active_set]

        if not to_export:
            print("[Export] No valid images to export.")
            return []

        print(f"\n[Export] Exporting {len(to_export)} selected image(s)...")
        for img in to_export:
            tier  = self.image_stats[img].get('current_tier', 0)
            votes = self.image_stats[img].get('votes', 0)
            wins  = self.image_stats[img].get('wins', 0)
            print(f"  {img}  (tier={tier}, votes={votes}, wins={wins})")

        # Step 1: Mark ALL as binned atomically before any purge
        for img in to_export:
            self.bin_image(img)

        # Step 2: Purge votes from remaining active images
        total_removed = 0
        for img in to_export:
            result = self.purge_binned_image_votes(img)
            total_removed += result['total_votes_removed']
        print(f"[Export] Vote purge complete — {total_removed} vote(s) removed.")

        # Step 3: Full wipe
        for img in to_export:
            self.image_stats.pop(img, None)
            self.binned_images.discard(img)
            self.metadata_cache.pop(img, None)
        print(f"[Export] Wiped {len(to_export)} image(s) from data.\n")

        return to_export

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
        print(f"\n[Load] ========== Loading save file ==========")
        print(f"[Load] File: {filename}")

        # --- Step 1/8: read and parse JSON ---
        print("[Load] Step 1/8: Reading JSON file from disk...")
        t = time.perf_counter()
        success, data, error_msg = self.data_persistence.load_from_file(filename)
        if not success:
            print(f"[Load] FAILED at step 1: {error_msg}")
            return False, error_msg
        print(f"[Load] Step 1/8: Parsed JSON in {(time.perf_counter()-t)*1000:.0f} ms")

        # --- Step 2/8: validate/fix data ---
        print("[Load] Step 2/8: Validating data integrity...")
        t = time.perf_counter()
        data = self.data_persistence.validate_and_fix_data(data)
        print(f"[Load] Step 2/8: Validated in {(time.perf_counter()-t)*1000:.0f} ms")

        # --- Step 3/8: extract core data ---
        print("[Load] Step 3/8: Extracting core data...")
        t = time.perf_counter()
        core_data = self.data_persistence.extract_core_data(data)
        self.image_folder   = core_data['image_folder']
        self.vote_count     = core_data['vote_count']
        self.image_stats    = core_data['image_stats']
        self.metadata_cache = core_data['metadata_cache']
        self.binned_images  = core_data['binned_images']
        n_images = len(self.image_stats)
        n_binned = len(self.binned_images)
        print(f"[Load] Step 3/8: {n_images} images, {n_binned} binned, "
              f"{self.vote_count} total votes | folder: {self.image_folder}")
        print(f"[Load] Step 3/8: Done in {(time.perf_counter()-t)*1000:.0f} ms")

        # --- Step 4/8: rebuild tested_against ---
        print(f"[Load] Step 4/8: Rebuilding tested_against index for {n_images} images...")
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
        print(f"[Load] Step 4/8: Rebuilt in {(time.perf_counter()-t)*1000:.0f} ms "
              f"({legacy_count} legacy, {derived_count} derived, {total_pairs} total pair entries)")

        # --- Step 5/8: load weights + algorithm settings ---
        print("[Load] Step 5/8: Loading weight manager and algorithm settings...")
        t = time.perf_counter()
        self.weight_manager.load_from_data(data)
        self.algorithm_settings.load_settings(data)
        print(f"[Load] Step 5/8: Done in {(time.perf_counter()-t)*1000:.0f} ms")

        # --- Step 6/8: load similarity (CLIP) cache ---
        print("[Load] Step 6/8: Loading CLIP similarity cache...")
        t = time.perf_counter()
        if self.image_folder:
            loaded = self.similarity_manager.load_cache(self.image_folder)
            if loaded:
                n_emb = len(self.similarity_manager.filenames)
                print(f"[Load] Step 6/8: Loaded {n_emb} embeddings in "
                      f"{(time.perf_counter()-t)*1000:.0f} ms")
            else:
                print(f"[Load] Step 6/8: No CLIP cache found for this folder "
                      f"(took {(time.perf_counter()-t)*1000:.0f} ms to check)")
        else:
            print("[Load] Step 6/8: Skipped (no image folder set)")

        # --- Step 7/8: purge stale votes from binned images ---
        if self.binned_images:
            print(f"[Load] Step 7/8: Purging stale votes from {n_binned} binned image(s)...")
            t = time.perf_counter()
            self.purge_all_binned_image_votes()
            print(f"[Load] Step 7/8: Purge complete in {(time.perf_counter()-t)*1000:.0f} ms")
        else:
            print("[Load] Step 7/8: No binned images to purge — skipped")

        # --- Step 8/8: initialise image stats + restore metadata ---
        print(f"[Load] Step 8/8: Initialising per-image stats for {n_images} images...")
        t = time.perf_counter()
        self._update_existing_images_with_strategic_timing()
        # Loop with progress reporting every 500 images so large datasets
        # don't feel stuck during the per-image initialisation pass.
        progress_step = 500 if n_images >= 1000 else (100 if n_images >= 200 else 0)
        for i, image_filename in enumerate(self.image_stats):
            self.initialize_image_stats(image_filename)
            if progress_step and (i + 1) % progress_step == 0:
                print(f"[Load]   ...processed {i + 1}/{n_images} images "
                      f"({(time.perf_counter()-t):.1f}s elapsed)")
        print(f"[Load] Step 8/8: Done in {(time.perf_counter()-t)*1000:.0f} ms")

        total_ms = (time.perf_counter() - t_start) * 1000
        print(f"[Load] ========== Load complete in {total_ms:.0f} ms "
              f"({n_images} images, {self.vote_count} votes) ==========\n")
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
        """Return the tier value at the cutline position.

        The cutline tier T is the tier of the image that sits at position
        target_count when all active images are sorted by tier descending.
        Returns None when target_count is 0 (disabled) or the dataset is
        smaller than target_count.
        """
        target = self.algorithm_settings.target_count
        if target == 0:
            return None
        active = self.get_active_images()
        if len(active) < target:
            return None
        sorted_by_tier = sorted(
            active,
            key=lambda img: self.image_stats[img].get('current_tier', 0),
            reverse=True
        )
        return self.image_stats[sorted_by_tier[target - 1]].get('current_tier', 0)

    def _get_zone_min_votes(self, tier_distance: int) -> int:
        """Return the minimum votes required to confirm an image at tier_distance from cutline."""
        base  = self.algorithm_settings.zone_base_votes
        per_t = self.algorithm_settings.zone_votes_per_tier
        return max(1, base + round(tier_distance * per_t))

    def get_zone(self, image_name: str, cutline: Optional[int] = None) -> str:
        """Classify an image into a cutline zone.

        Returns one of:
          'eliminated'    – image is binned
          'disabled'      – target_count == 0 (cutline system off)
          'confirmed_in'  – tier >= cutline + buffer AND enough votes
          'confirmed_out' – tier <= cutline - (buffer + extra) AND enough votes
          'boundary'      – everything else (near cutline, or too few votes)

        PERFORMANCE: Callers that classify many images in a row should call
        get_cutline_tier() ONCE and pass the result in via the `cutline`
        parameter. When `cutline` is None, it is computed internally —
        but that internal call is O(N log N), so doing it per-image creates
        an O(N² log N) loop. Passing the precomputed value avoids that.

        Fix A — Hard minimum vote gate:
          No image can be confirmed_out until it has at least
          min_votes_before_cut votes. This prevents unlucky early
          matchups from sending low-vote images out of the pool.

        Fix B — Confidence-weighted extra tier buffer:
          Images that have JUST cleared the minimum threshold still
          carry an extra tier buffer that shrinks linearly to 0 as
          votes climb from min_votes_before_cut to 2× that value.
          This means a fresh image must be further below the cutline
          before it can be confirmed_out, even if it technically has
          enough votes to qualify.
        """
        if self.is_image_binned(image_name):
            return 'eliminated'
        if cutline is None:
            cutline = self.get_cutline_tier()
        if cutline is None:
            return 'disabled'
        stats  = self.get_image_stats(image_name)
        tier   = stats.get('current_tier', 0)
        votes  = stats.get('votes', 0)
        buffer = self.algorithm_settings.cutline_buffer_tiers
        min_cut_votes = self.algorithm_settings.min_votes_before_cut

        # --- Fix A: hard gate ---
        # Images below the threshold are never confirmed_out.
        # (confirmed_in is still allowed — a dominant image can be confirmed
        # in early since that direction only helps it, not harms it.)
        if votes < min_cut_votes:
            # Can still be confirmed_in if well above cutline
            if tier >= cutline + buffer:
                min_v = self._get_zone_min_votes(tier - cutline)
                if votes >= min_v:
                    return 'confirmed_in'
            return 'boundary'

        # --- Fix B: graduated extra out-buffer for recently-eligible images ---
        # Between min_cut_votes and 2× min_cut_votes the extra buffer shrinks
        # from cutline_buffer_tiers → 0 (linear).
        full_confidence_votes = min_cut_votes * 2
        if votes < full_confidence_votes:
            maturity = (votes - min_cut_votes) / max(full_confidence_votes - min_cut_votes, 1)
            extra_out_buffer = round(buffer * (1.0 - maturity))
        else:
            extra_out_buffer = 0

        effective_out_buffer = buffer + extra_out_buffer

        if tier >= cutline + buffer:
            min_v = self._get_zone_min_votes(tier - cutline)
            if votes >= min_v:
                return 'confirmed_in'
        elif tier <= cutline - effective_out_buffer:
            min_v = self._get_zone_min_votes(cutline - tier)
            if votes >= min_v:
                return 'confirmed_out'
        return 'boundary'

    def get_zone_counts(self) -> Dict[str, Any]:
        """Return a dict of zone counts and cutline metadata."""
        counts = {'confirmed_in': 0, 'boundary': 0, 'confirmed_out': 0,
                  'eliminated': 0, 'disabled': 0}
        # Compute cutline ONCE (it's O(N log N)) and reuse for every image.
        cutline = self.get_cutline_tier()
        for img in self.image_stats:
            zone = self.get_zone(img, cutline=cutline)
            counts[zone] = counts.get(zone, 0) + 1
        counts['cutline_tier']  = cutline
        counts['target_count']  = self.algorithm_settings.target_count
        counts['total_active']  = self.get_active_image_count()
        return counts

    def get_progress_summary(self) -> Dict[str, Any]:
        """Return zone counts plus resolution percentage."""
        counts    = self.get_zone_counts()
        resolved  = counts['confirmed_in'] + counts['confirmed_out'] + counts['eliminated']
        total     = counts['total_active'] + counts['eliminated']
        resolution = (resolved / total * 100.0) if total > 0 else 0.0
        counts['resolved']       = resolved
        counts['resolution_pct'] = round(resolution, 1)
        return counts

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
