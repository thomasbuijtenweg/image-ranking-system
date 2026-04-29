"""Binning service — the rule book for soft-deleting images from the ranking.

This service owns everything about the "binned" status of images:
the set of binned filenames, the logic for binning + purging their vote
history from active images, and the export operations (which are
implemented as atomic bin-all → purge → wipe sequences).

Design notes:
- The service holds a back-reference to its DataManager because it needs
  to touch image_stats and metadata_cache when purging / exporting. That's
  by design: binning *is* a DataManager-scoped operation, not a standalone
  component.
- DataManager exposes every method here via one-line delegation shims for
  backward compatibility. Existing callers continue to use
  `data_manager.bin_image(...)` and that call flows through to this service.
- `binned_images` is owned here. DataManager exposes it via a property so
  that reading `data_manager.binned_images` and writing
  `data_manager.binned_images = new_set` both still work transparently.
"""

from typing import Any, Dict, List, TYPE_CHECKING

from core.logging_setup import get_logger

if TYPE_CHECKING:
    # Imported only for type hints — avoids a circular import at runtime,
    # since DataManager imports BinningService.
    from core.data_manager import DataManager

log = get_logger(__name__)


class BinningService:
    """Owns binned_images and implements bin / purge / export workflows."""

    def __init__(self, data_manager: "DataManager") -> None:
        self._dm = data_manager
        self.binned_images: set = set()

    # ------------------------------------------------------------------
    # Basic query + mutation
    # ------------------------------------------------------------------

    def bin_image(self, image_name: str) -> bool:
        """Mark an image as binned. Returns False if already binned."""
        if image_name in self.binned_images:
            return False
        self.binned_images.add(image_name)
        log.info("Image '%s' has been binned", image_name)
        return True

    def is_image_binned(self, image_name: str) -> bool:
        return image_name in self.binned_images

    def get_binned_images(self) -> list:
        return list(self.binned_images)

    def get_binned_image_count(self) -> int:
        return len(self.binned_images)

    # ------------------------------------------------------------------
    # Purging a binned image's vote history from active images
    # ------------------------------------------------------------------

    def purge_binned_image_votes(self, binned_image: str, verbose: bool = True) -> Dict[str, Any]:
        """Remove all vote history involving `binned_image` from active images.

        For every active (non-binned) image that was previously compared
        against the binned image, this method:
          - Removes all matchup_history entries involving the binned image
          - Removes the binned image from tested_against
          - Recalculates wins, losses, votes from remaining matchup history
          - Replays tier progression from the remaining matchup history
        """
        image_stats = self._dm.image_stats
        affected_images = 0
        total_votes_removed = 0

        for img_name, stats in image_stats.items():
            # Skip the binned image itself and any other binned images
            if img_name == binned_image or img_name in self.binned_images:
                continue

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

            old_tier = stats['current_tier']

            # Apply recalculated values
            stats['matchup_history'] = filtered_history
            stats['wins'] = new_wins
            stats['losses'] = new_losses
            stats['votes'] = new_votes
            stats['current_tier'] = new_tier
            stats['tier_history'] = new_tier_history

            if verbose:
                log.debug("  Purged %d vote(s) involving '%s' from '%s' (tier: %s -> %s)",
                          votes_removed, binned_image, img_name, old_tier, new_tier)

        if verbose:
            log.info("Vote purge complete for '%s': %d images affected, %d votes removed",
                     binned_image, affected_images, total_votes_removed)

        return {
            'affected_images': affected_images,
            'total_votes_removed': total_votes_removed,
        }

    def purge_all_binned_image_votes(self) -> Dict[str, Any]:
        """Purge stale votes for every currently-binned image.

        Cleans up save files where images were binned before the vote-purge
        feature existed. Idempotent — safe to run multiple times.
        """
        if not self.binned_images:
            log.info("No binned images found - nothing to purge")
            return {'total_affected': 0, 'total_removed': 0, 'binned_processed': 0}

        total_affected = 0
        total_removed = 0
        n_binned = len(self.binned_images)
        # For bulk purges, emit a single progress line every ~20 images
        # instead of per-image spam. Threshold chosen so small datasets
        # still show per-image output for debugging.
        quiet = n_binned > 20
        progress_step = max(1, n_binned // 10)  # ~10 updates across the run
        image_stats = self._dm.image_stats

        for idx, binned_image in enumerate(list(self.binned_images)):
            has_stale_votes = any(
                binned_image in [opp for opp, _, _ in stats.get('matchup_history', [])]
                for img_name, stats in image_stats.items()
                if img_name != binned_image and img_name not in self.binned_images
            )

            if has_stale_votes:
                result = self.purge_binned_image_votes(binned_image, verbose=not quiet)
                total_affected += result['affected_images']
                total_removed += result['total_votes_removed']

            if quiet and (idx + 1) % progress_step == 0:
                log.debug("  [Purge] ...processed %d/%d binned images (%d votes removed so far)",
                          idx + 1, n_binned, total_removed)

        if total_removed > 0:
            log.info("Purge complete: %d stale vote(s) removed from %d image(s) across %d binned image(s)",
                     total_removed, total_affected, n_binned)
        else:
            log.info("Purge complete: no stale votes found (already clean)")

        return {
            'total_affected': total_affected,
            'total_removed': total_removed,
            'binned_processed': n_binned,
        }

    # ------------------------------------------------------------------
    # Export operations — atomic bin-all → purge → wipe sequences
    # ------------------------------------------------------------------

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
        """
        active = self._dm.get_active_images()
        if not active:
            return []

        n = min(n, len(active))
        image_stats = self._dm.image_stats

        sorted_active = sorted(
            active,
            key=lambda img: (
                image_stats[img].get('current_tier', 0),
                image_stats[img].get('wins', 0),
            ),
            reverse=True,
        )
        to_export = sorted_active[:n]

        log.info("[Export] Preparing to export top %d image(s)...", len(to_export))
        for img in to_export:
            tier = image_stats[img].get('current_tier', 0)
            votes = image_stats[img].get('votes', 0)
            wins = image_stats[img].get('wins', 0)
            log.debug("  %s  (tier=%s, votes=%s, wins=%s)", img, tier, votes, wins)

        # Step 2: Mark ALL as binned atomically before any purge
        for img in to_export:
            self.bin_image(img)
        log.info("[Export] Marked %d image(s) as binned.", len(to_export))

        # Step 3: Purge each exported image's votes from remaining active images
        total_votes_removed = 0
        for img in to_export:
            result = self.purge_binned_image_votes(img)
            total_votes_removed += result['total_votes_removed']
        log.info("[Export] Vote purge complete \u2014 %d vote(s) removed from active images.",
                 total_votes_removed)

        # Step 4: Full wipe \u2014 remove from all data structures
        for img in to_export:
            image_stats.pop(img, None)
            self.binned_images.discard(img)
            self._dm.metadata_cache.pop(img, None)
        log.info("[Export] Wiped %d image(s) from data. Export ready.", len(to_export))

        return to_export

    def export_specific_images(self, names: list) -> list:
        """Export a caller-supplied list of images (full reset).

        Same atomic bin-all → purge → wipe sequence as export_top_images,
        but the caller decides which images to include (e.g. after the user
        has toggled images in the preview window).

        Returns the list of names that were actually processed (skips any
        name not in image_stats or already binned).
        """
        active_set = set(self._dm.get_active_images())
        to_export = [n for n in names if n in active_set]

        if not to_export:
            log.info("[Export] No valid images to export.")
            return []

        image_stats = self._dm.image_stats
        log.info("[Export] Exporting %d selected image(s)...", len(to_export))
        for img in to_export:
            tier = image_stats[img].get('current_tier', 0)
            votes = image_stats[img].get('votes', 0)
            wins = image_stats[img].get('wins', 0)
            log.debug("  %s  (tier=%s, votes=%s, wins=%s)", img, tier, votes, wins)

        # Step 1: Mark ALL as binned atomically before any purge
        for img in to_export:
            self.bin_image(img)

        # Step 2: Purge votes from remaining active images
        total_removed = 0
        for img in to_export:
            result = self.purge_binned_image_votes(img)
            total_removed += result['total_votes_removed']
        log.info("[Export] Vote purge complete \u2014 %d vote(s) removed.", total_removed)

        # Step 3: Full wipe
        for img in to_export:
            image_stats.pop(img, None)
            self.binned_images.discard(img)
            self._dm.metadata_cache.pop(img, None)
        log.info("[Export] Wiped %d image(s) from data.", len(to_export))

        return to_export
