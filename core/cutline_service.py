"""Cutline service — zone classification for the top-N cut system.

When the user sets a non-zero `target_count`, the system is trying to identify
the top N images. Every image is classified into one of five zones based on
its current tier vs the "cutline" (the tier of the image currently ranked Nth):

  'confirmed_in'  – safely above the cutline, well-tested
  'confirmed_out' – safely below the cutline, well-tested
  'boundary'      – near the cutline, or not yet well-tested
  'eliminated'    – binned (removed from consideration entirely)
  'disabled'      – target_count is 0, cutline system is off

Boundary images are the ones the algorithm prioritises for further voting.

Design notes:
- The service holds a back-reference to its DataManager because it needs
  algorithm_settings, image_stats, and the binning state.
- `get_cutline_tier()` does an O(N log N) sort — so `get_zone_counts()`
  computes it once and passes it into each per-image `get_zone()` call via
  the optional `cutline` parameter. Callers outside this service that loop
  should do the same (see `ranking_algorithm.select_next_pair`).
- DataManager exposes every method here via one-line delegation shims.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.data_manager import DataManager


class CutlineService:
    """Owns cutline-tier computation and per-image zone classification."""

    def __init__(self, data_manager: "DataManager") -> None:
        self._dm = data_manager

    # ------------------------------------------------------------------
    # Cutline tier: where is the Nth-ranked image?
    # ------------------------------------------------------------------

    def get_cutline_tier(self) -> Optional[int]:
        """Return the tier value at the cutline position.

        The cutline tier T is the tier of the image that sits at position
        target_count when all active images are sorted by tier descending.
        Returns None when target_count is 0 (disabled) or the dataset is
        smaller than target_count.
        """
        dm = self._dm
        target = dm.algorithm_settings.target_count
        if target == 0:
            return None
        active = dm.get_active_images()
        if len(active) < target:
            return None
        sorted_by_tier = sorted(
            active,
            key=lambda img: dm.image_stats[img].get('current_tier', 0),
            reverse=True,
        )
        return dm.image_stats[sorted_by_tier[target - 1]].get('current_tier', 0)

    # ------------------------------------------------------------------
    # Zone classification
    # ------------------------------------------------------------------

    def _get_zone_min_votes(self, tier_distance: int) -> int:
        """Minimum votes required to confirm an image at `tier_distance` from cutline."""
        settings = self._dm.algorithm_settings
        base = settings.zone_base_votes
        per_t = settings.zone_votes_per_tier
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
        dm = self._dm
        if dm.is_image_binned(image_name):
            return 'eliminated'
        if cutline is None:
            cutline = self.get_cutline_tier()
        if cutline is None:
            return 'disabled'
        stats = dm.get_image_stats(image_name)
        tier = stats.get('current_tier', 0)
        votes = stats.get('votes', 0)
        buffer = dm.algorithm_settings.cutline_buffer_tiers
        min_cut_votes = dm.algorithm_settings.min_votes_before_cut

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

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    def get_zone_counts(self) -> Dict[str, Any]:
        """Return a dict of zone counts and cutline metadata."""
        dm = self._dm
        counts = {'confirmed_in': 0, 'boundary': 0, 'confirmed_out': 0,
                  'eliminated': 0, 'disabled': 0}
        # Compute cutline ONCE (it's O(N log N)) and reuse for every image.
        cutline = self.get_cutline_tier()
        for img in dm.image_stats:
            zone = self.get_zone(img, cutline=cutline)
            counts[zone] = counts.get(zone, 0) + 1
        counts['cutline_tier'] = cutline
        counts['target_count'] = dm.algorithm_settings.target_count
        counts['total_active'] = dm.get_active_image_count()
        return counts

    def get_progress_summary(self) -> Dict[str, Any]:
        """Return zone counts plus resolution percentage."""
        counts = self.get_zone_counts()
        resolved = counts['confirmed_in'] + counts['confirmed_out'] + counts['eliminated']
        total = counts['total_active'] + counts['eliminated']
        resolution = (resolved / total * 100.0) if total > 0 else 0.0
        counts['resolved'] = resolved
        counts['resolution_pct'] = round(resolution, 1)
        return counts
