"""CLIP-based hybrid similarity manager for the Image Ranking System.

Three-layer similarity:
  1. CLIP visual  – image embeddings, cosine similarity (what the image looks like)
  2. CLIP text    – prompt text through the CLIP text encoder (semantic intent)
  3. Tag overlap  – structured Jaccard on parsed artist / role / style buckets

Tag parsing uses a base vocabulary (curated) PLUS a dataset-specific vocabulary
discovered automatically from the prompts during index build, so the system
adapts to any dataset without manual maintenance.
"""

import os
import sys
import re
import json
import subprocess
import threading
from collections import Counter
from typing import List, Optional, Dict, Callable, Tuple

# ---------------------------------------------------------------------------
# Dependency auto-installer
# ---------------------------------------------------------------------------

_REQUIRED_PACKAGES = [
    ("torch",       "torch"),
    ("open_clip",   "open-clip-torch"),
    ("numpy",       "numpy"),
    ("PIL",         "Pillow"),
    ("torchvision", "torchvision"),
]
_deps_checked = False
_deps_lock = threading.Lock()


def _ensure_dependencies() -> bool:
    global _deps_checked
    with _deps_lock:
        if _deps_checked:
            return True
        missing = []
        for import_name, pip_name in _REQUIRED_PACKAGES:
            try:
                __import__(import_name)
            except ImportError:
                missing.append(pip_name)
        if missing:
            print(f"[SimilarityManager] Missing packages: {missing}. Installing into {sys.executable}…")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                )
                print(f"[SimilarityManager] Packages installed: {missing}")
            except subprocess.CalledProcessError as e:
                print(f"[SimilarityManager] pip install failed: {e.stderr.decode(errors='replace')}")
                return False
        _deps_checked = True
        return True

# ---------------------------------------------------------------------------
# Lazy CLIP model loader
# ---------------------------------------------------------------------------

_clip_model = None
_clip_preprocess = None
_clip_device = None
_model_lock = threading.Lock()


def _load_clip_model():
    global _clip_model, _clip_preprocess, _clip_device
    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _clip_device
    with _model_lock:
        if _clip_model is not None:
            return _clip_model, _clip_preprocess, _clip_device
        try:
            if not _ensure_dependencies():
                raise RuntimeError("Required packages could not be installed.")
            import torch, numpy as np, open_clip
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[SimilarityManager] Loading OpenCLIP model on {device}…")
            model, _, preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="openai")
            model = model.to(device)
            model.eval()
            _clip_model, _clip_preprocess, _clip_device = model, preprocess, device
            print("[SimilarityManager] Model loaded successfully.")
        except Exception as e:
            print(f"[SimilarityManager] ERROR loading model: {e}")
            raise
    return _clip_model, _clip_preprocess, _clip_device

# ---------------------------------------------------------------------------
# Base vocabulary (curated seed lists – common SD terms)
# ---------------------------------------------------------------------------

_BASE_ARTISTS = frozenset([
    'bill sienkiewicz', 'boris vallejo', 'michael kaluta', 'bernie wrightson',
    'dave mckean', 'luis royo', 'aleksi briclot', 'marc silvestri', 'greg land',
    'charlie bowater', 'joe madureira', 'raymond swanland', 'phillipe druillet',
    'henry asencio', 'simon bisley', 'carne griffiths', 'ethan van sciver',
    'rodney matthews', 'michael whelan', 'frank frazetta', 'alphonse mucha',
    'artgerm', 'greg rutkowski', 'wlop', 'ilya kuvshinov', 'gustav klimt',
    'hr giger', 'zdzislaw beksinski', 'john william waterhouse', 'alan lee',
    'tony diterlizzi', 'donato giancola', 'keith parkinson', 'larry elmore',
    'clyde caldwell', 'jeff easley', 'brom', 'wayne barlowe', 'michael parkes',
    'jim burns', 'john berkey', 'john howe', 'boris',
])

_BASE_ROLES = frozenset([
    'vampire', 'empress', 'dancer', 'gypsy', 'noble', 'priestess', 'sorceress',
    'succubus', 'valkyrie', 'necromancer', 'dominatrix', 'warrior', 'victorian',
    'witch', 'wizard', 'knight', 'queen', 'princess', 'goddess', 'demon',
    'angel', 'hunter', 'assassin', 'mage', 'ranger', 'rogue', 'cleric',
    'barbarian', 'paladin', 'druid', 'monk', 'bard', 'warlock', 'shaman',
    'viking', 'pirate', 'ninja', 'samurai', 'elf', 'dark elf', 'faerie',
])

_BASE_STYLES = frozenset([
    'comicbook', 'comic book', 'landscape painting', 'epic fantasy character art',
    'western cartoon illustration', 'western comic illustration',
    'graphic novel illustration', 'artistic comicbook portrait art',
    'highly detailed comicbook illustration', 'artistic landscape painting',
    'concept art', 'digital art', 'oil painting', 'watercolor', 'anime', 'manga',
    'illustration', 'fantasy art', 'dark fantasy', 'painterly', 'photorealistic',
    'hyperrealistic', 'portrait art', 'fantasy character', 'cover art',
])

_BASE_SETTINGS = frozenset([
    'castle', 'forest', 'underdark', 'dungeon', 'ruins', 'throne room',
    'battlefield', 'garden', 'moonlight', 'mist', 'fog', 'mountain', 'ocean',
    'desert', 'cave', 'tavern', 'city', 'cemetery', 'graveyard', 'swamp',
    'jungle', 'tundra', 'volcano',
])

# ---------------------------------------------------------------------------
# Vocabulary discovery via CLIP text classification
# ---------------------------------------------------------------------------

# CLIP is asked to classify unknown terms against these bucket descriptions.
# More specific descriptions outperform generic ones in zero-shot classification.
_BUCKET_DESCRIPTIONS = {
    'artists': "the name of a visual artist, painter, illustrator, or comic book artist",
    'roles':   "a character archetype, fantasy role, occupation, or creature type",
    'styles':  "an artistic style, visual technique, medium, or aesthetic",
    'settings': "a physical location, environment, landscape, or architectural setting",
}

# Tuning knobs
_DISCOVERY_MIN_FREQUENCY = 2      # term must appear in at least N prompts
_DISCOVERY_MIN_LENGTH    = 3      # ignore very short tokens
_DISCOVERY_CONFIDENCE    = 0.58   # min cosine similarity to assign a bucket


def _extract_all_terms(prompts: List[str]) -> Counter:
    """Extract all (term, weight) pairs from a list of prompts and count term frequency."""
    term_counts: Counter = Counter()
    for prompt in prompts:
        if not prompt:
            continue
        pos = prompt.split('Negative prompt:')[0]
        pos = re.sub(r'<[^>]+>', '', pos)
        # weighted terms
        for term, _ in re.findall(r'\(([^()]+):(\d+\.?\d*)\)', pos):
            t = term.strip().lower().replace('_', ' ')
            if len(t) >= _DISCOVERY_MIN_LENGTH:
                term_counts[t] += 1
        # unweighted remainder
        remainder = re.sub(r'\([^()]*\)', '', pos).split('Steps:')[0]
        for phrase in re.split(r'[,\n]', remainder):
            t = phrase.strip().lower().replace('_', ' ')
            if len(t) >= _DISCOVERY_MIN_LENGTH:
                term_counts[t] += 1
    return term_counts


def _is_known(term: str) -> bool:
    """Return True if the term is already in any base vocabulary."""
    for vocab in (_BASE_ARTISTS, _BASE_ROLES, _BASE_STYLES, _BASE_SETTINGS):
        if term in vocab:
            return True
        # also check if any vocab entry is contained in the term (substring match)
        for entry in vocab:
            if entry in term:
                return True
    return False


def _discover_vocabulary_from_prompts(prompts: List[str]) -> Dict[str, Dict[str, float]]:
    """Discover dataset-specific terms not in the base vocabulary and classify them.

    Uses the CLIP text encoder to assign each unknown term to the most fitting
    bucket (artists / roles / styles / settings).  Terms with low confidence
    are discarded rather than misclassified.

    Returns:
        {bucket: {term: confidence_score}}  – merged per-bucket discovery results
    """
    discovered: Dict[str, Dict[str, float]] = {
        'artists': {}, 'roles': {}, 'styles': {}, 'settings': {}
    }

    if not _ensure_dependencies():
        print("[SimilarityManager] Skipping vocabulary discovery – dependencies unavailable.")
        return discovered

    # Collect candidate terms
    term_counts = _extract_all_terms(prompts)
    candidates = [
        t for t, count in term_counts.items()
        if count >= _DISCOVERY_MIN_FREQUENCY and not _is_known(t)
        and not re.fullmatch(r'[\d\s\W]+', t)   # skip purely numeric/punctuation terms
    ]

    if not candidates:
        print("[SimilarityManager] No new vocabulary candidates found.")
        return discovered

    print(f"[SimilarityManager] Classifying {len(candidates)} vocabulary candidates…")

    try:
        import torch, numpy as np, open_clip
        model, _, device = _load_clip_model()
        tokenizer = open_clip.get_tokenizer("ViT-B-32")

        # Encode bucket descriptions once
        bucket_names = list(_BUCKET_DESCRIPTIONS.keys())
        bucket_texts = list(_BUCKET_DESCRIPTIONS.values())
        bucket_tokens = tokenizer(bucket_texts).to(device)
        with torch.no_grad():
            bucket_vecs = model.encode_text(bucket_tokens)
            bucket_vecs = bucket_vecs / bucket_vecs.norm(dim=-1, keepdim=True)
        bucket_vecs_np = bucket_vecs.cpu().numpy().astype(np.float32)  # (4, 512)

        # Classify candidates in batches of 64
        BATCH = 64
        for start in range(0, len(candidates), BATCH):
            batch = candidates[start:start + BATCH]
            tokens = tokenizer(batch).to(device)
            with torch.no_grad():
                term_vecs = model.encode_text(tokens)
                term_vecs = term_vecs / term_vecs.norm(dim=-1, keepdim=True)
            term_vecs_np = term_vecs.cpu().numpy().astype(np.float32)  # (B, 512)

            # cosine similarities: (B, 4)
            sims = (term_vecs_np @ bucket_vecs_np.T + 1.0) / 2.0

            for i, term in enumerate(batch):
                best_idx  = int(sims[i].argmax())
                best_conf = float(sims[i, best_idx])
                if best_conf >= _DISCOVERY_CONFIDENCE:
                    bucket = bucket_names[best_idx]
                    discovered[bucket][term] = round(best_conf, 3)

        total = sum(len(v) for v in discovered.values())
        per_bucket = {b: len(v) for b, v in discovered.items() if v}
        print(f"[SimilarityManager] Vocabulary discovery complete: "
              f"{total} new terms classified {per_bucket}")

    except Exception as e:
        print(f"[SimilarityManager] Vocabulary discovery error: {e}")

    return discovered

# ---------------------------------------------------------------------------
# SimilarityManager
# ---------------------------------------------------------------------------

class SimilarityManager:
    """Hybrid similarity: CLIP visual + CLIP text + structured tag overlap."""

    CACHE_SUFFIX = "_similarity.npz"
    VOCAB_SUFFIX = "_vocabulary.json"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}

    def __init__(self):
        self.embeddings:      Optional[object] = None   # np.ndarray (N, 512)
        self.text_embeddings: Optional[object] = None   # np.ndarray (N, 512)
        self.has_text:        Optional[object] = None   # np.ndarray (N,) bool
        self.filenames:       List[str] = []
        self._index:          Dict[str, int] = {}
        self.prompt_tags:     Dict[str, dict] = {}      # filename → tag dict
        self.discovered_vocab: Dict[str, Dict[str, float]] = {
            'artists': {}, 'roles': {}, 'styles': {}, 'settings': {}
        }
        self.cache_path: Optional[str] = None
        self.vocab_path: Optional[str] = None
        self.is_ready:   bool = False
        self.is_legacy:  bool = False
        self._build_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    def set_cache_path(self, image_folder: str) -> None:
        folder_name = os.path.basename(os.path.normpath(image_folder))
        parent_dir  = os.path.dirname(os.path.normpath(image_folder))
        self.cache_path = os.path.join(parent_dir, folder_name + self.CACHE_SUFFIX)
        self.vocab_path = os.path.join(parent_dir, folder_name + self.VOCAB_SUFFIX)
        print(f"[SimilarityManager] Cache path: {self.cache_path}")

    # ------------------------------------------------------------------
    # Vocabulary JSON sidecar helpers
    # ------------------------------------------------------------------

    def _save_vocab_json(self) -> None:
        """Write the discovered vocabulary to a human-readable JSON file."""
        if not self.vocab_path:
            return
        try:
            with open(self.vocab_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "_comment": (
                        "Auto-discovered vocabulary for this dataset. "
                        "You can add, remove, or correct entries. "
                        "Bucket keys: artists, roles, styles, settings. "
                        "Values are CLIP confidence scores (0-1). "
                        "Rebuilt automatically when you rebuild the index."
                    ),
                    "discovered": self.discovered_vocab,
                }, f, indent=2, ensure_ascii=False)
            total = sum(len(v) for v in self.discovered_vocab.values())
            print(f"[SimilarityManager] Vocabulary saved: {total} terms → {self.vocab_path}")
        except Exception as e:
            print(f"[SimilarityManager] Could not save vocabulary JSON: {e}")

    def _load_vocab_json(self) -> bool:
        """Load discovered vocabulary from JSON sidecar. Returns True on success."""
        if not self.vocab_path or not os.path.exists(self.vocab_path):
            return False
        try:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            disc = data.get("discovered", {})
            # Merge into self.discovered_vocab
            for bucket in ('artists', 'roles', 'styles', 'settings'):
                self.discovered_vocab[bucket] = dict(disc.get(bucket, {}))
            total = sum(len(v) for v in self.discovered_vocab.values())
            print(f"[SimilarityManager] Vocabulary loaded: {total} discovered terms.")
            return True
        except Exception as e:
            print(f"[SimilarityManager] Could not load vocabulary JSON: {e}")
            return False

    # ------------------------------------------------------------------
    # Load / save cache  (backward-compatible with old visual-only files)
    # ------------------------------------------------------------------

    def load_cache(self, image_folder: str) -> bool:
        self.set_cache_path(image_folder)
        if not self.cache_path or not os.path.exists(self.cache_path):
            print("[SimilarityManager] No existing cache found.")
            self.is_ready = False
            return False
        try:
            import numpy as np
            data = np.load(self.cache_path, allow_pickle=True)
            self.embeddings = data["embeddings"].astype(np.float32)
            self.filenames  = list(data["filenames"])
            self._index     = {name: i for i, name in enumerate(self.filenames)}

            if "text_embeddings" in data.files:
                self.text_embeddings = data["text_embeddings"].astype(np.float32)
                self.has_text        = data["has_text"].astype(bool)
                tags_json            = data["prompt_tags_json"]
                self.prompt_tags     = {
                    self.filenames[i]: json.loads(str(tags_json[i]))
                    for i in range(len(self.filenames))
                }
                has_count = int(self.has_text.sum())
                print(f"[SimilarityManager] Loaded cache: {len(self.filenames)} visual + "
                      f"{has_count} text embeddings + tags.")
            else:
                self.text_embeddings = None
                self.has_text        = None
                self.prompt_tags     = {}
                print(f"[SimilarityManager] Loaded cache: {len(self.filenames)} visual embeddings "
                      f"(no text/tags – rebuild for full hybrid).")

            # Load discovered vocabulary from JSON sidecar
            self._load_vocab_json()
            self.is_ready = True
            # Flag legacy caches so the UI can trigger an upgrade
            self.is_legacy = "text_embeddings" not in data.files
            return True
        except Exception as e:
            print(f"[SimilarityManager] Failed to load cache: {e}")
            self.is_ready = False
            return False

    def _save_cache(self) -> None:
        try:
            import numpy as np
        except ImportError:
            return
        if self.cache_path is None or self.embeddings is None:
            return
        try:
            tags_json = np.array(
                [json.dumps(self.prompt_tags.get(n, {})) for n in self.filenames],
                dtype=object
            )
            save_kwargs = dict(
                embeddings       = self.embeddings,
                filenames        = np.array(self.filenames, dtype=object),
                prompt_tags_json = tags_json,
            )
            if self.text_embeddings is not None:
                save_kwargs["text_embeddings"] = self.text_embeddings
                save_kwargs["has_text"]        = self.has_text
            np.savez_compressed(self.cache_path, **save_kwargs)
            print(f"[SimilarityManager] Cache saved ({len(self.filenames)} entries).")
        except Exception as e:
            print(f"[SimilarityManager] Failed to save cache: {e}")

    # ------------------------------------------------------------------
    # Prompt parsing (base vocab + discovered vocab)
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_prompt_for_embedding(prompt: str) -> str:
        if not prompt:
            return ''
        clean = prompt.split('Negative prompt:')[0]
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = re.sub(r'\(([^()]+):\d+\.?\d*\)', r'\1', clean)
        clean = re.sub(r'\b(Steps|Sampler|CFG scale|Seed|Size|Model hash|Model'
                       r'|Denoising|ADetailer|Hires|Version|Lora|Extra noise)'
                       r'\b.*', '', clean, flags=re.IGNORECASE)
        clean = clean.replace('_', ' ')
        return re.sub(r'\s+', ' ', clean).strip()[:300]

    @staticmethod
    def _parse_prompt_tags(prompt: str,
                           extra_vocab: Optional[Dict[str, Dict[str, float]]] = None) -> dict:
        """Parse prompt into bucket dicts, merging base + discovered vocabulary.

        Args:
            prompt:      Raw SD prompt string.
            extra_vocab: Discovered-vocab dict {bucket: {term: confidence}}.
                         When provided, terms in extra_vocab are matched after
                         the base vocabulary so base entries always take priority.

        Returns:
            {'artists': {name: weight}, 'roles': {name: weight},
             'styles':  {name: weight}, 'settings': {name: weight}}
        """
        result: dict = {'artists': {}, 'roles': {}, 'styles': {}, 'settings': {}}
        if not prompt:
            return result

        # Build lookup sets that include discovered terms
        artists_vocab  = _BASE_ARTISTS  | frozenset(extra_vocab.get('artists',  {}) if extra_vocab else {})
        roles_vocab    = _BASE_ROLES    | frozenset(extra_vocab.get('roles',    {}) if extra_vocab else {})
        styles_vocab   = _BASE_STYLES   | frozenset(extra_vocab.get('styles',   {}) if extra_vocab else {})
        settings_vocab = _BASE_SETTINGS | frozenset(extra_vocab.get('settings', {}) if extra_vocab else {})

        pos_prompt = prompt.split('Negative prompt:')[0]
        pos_prompt = re.sub(r'<[^>]+>', '', pos_prompt)

        weighted_terms: List[Tuple[str, float]] = []
        for term, weight in re.findall(r'\(([^()]+):(\d+\.?\d*)\)', pos_prompt):
            weighted_terms.append((term.strip().lower().replace('_', ' '), float(weight)))
        remaining = re.sub(r'\([^()]*\)', '', pos_prompt).split('Steps:')[0]
        for phrase in re.split(r'[,\n]', remaining):
            t = phrase.strip().lower().replace('_', ' ')
            if len(t) > 2:
                weighted_terms.append((t, 1.0))

        def _add(bucket: str, key: str, weight: float) -> None:
            if key not in result[bucket] or result[bucket][key] < weight:
                result[bucket][key] = weight

        for term, weight in weighted_terms:
            found = False
            for artist in artists_vocab:
                if artist in term:
                    _add('artists', artist, weight)
                    found = True
            if found:
                continue
            for role in roles_vocab:
                if role in term:
                    _add('roles', role, weight)
                    found = True
            if found:
                continue
            for style in styles_vocab:
                if style in term:
                    _add('styles', style, weight)
                    break
            for setting in settings_vocab:
                if setting in term:
                    _add('settings', setting, weight)
                    break

        return result

    # ------------------------------------------------------------------
    # Tag overlap scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _tag_overlap_score(tags_a: dict, tags_b: dict) -> float:
        """Weighted Jaccard across artist/role/style buckets → [0, 1]."""
        BUCKET_WEIGHTS = {'artists': 0.50, 'roles': 0.25, 'styles': 0.25}
        total_score = total_weight = 0.0
        for bucket, bw in BUCKET_WEIGHTS.items():
            da, db = tags_a.get(bucket, {}), tags_b.get(bucket, {})
            if not da and not db:
                continue
            total_weight += bw
            if not da or not db:
                continue
            shared = set(da) & set(db)
            intersection = sum(min(da[k], db[k]) for k in shared)
            union = sum(max(da.get(k, 0), db.get(k, 0)) for k in set(da) | set(db))
            if union > 0:
                total_score += bw * (intersection / union)
        return (total_score / total_weight) if total_weight > 0 else 0.5

    # ------------------------------------------------------------------
    # Embedding generation
    # ------------------------------------------------------------------

    def _embed_images(self, image_folder, image_names, progress_callback=None):
        import torch, numpy as np
        from PIL import Image
        model, preprocess, device = _load_clip_model()
        vectors, embedded = [], []
        total = len(image_names)
        for i, name in enumerate(image_names):
            if progress_callback:
                progress_callback(i, total, name)
            try:
                with Image.open(os.path.join(image_folder, name)).convert("RGB") as img:
                    tensor = preprocess(img).unsqueeze(0).to(device)
                with torch.no_grad():
                    vec = model.encode_image(tensor)
                    vec = vec / vec.norm(dim=-1, keepdim=True)
                vectors.append(vec.cpu().numpy().astype(np.float32).squeeze(0))
                embedded.append(name)
            except Exception:
                pass
        if progress_callback:
            progress_callback(total, total, "done")
        arr = (np.array(vectors, dtype=np.float32) if vectors
               else np.empty((0, 512), dtype=np.float32))
        return arr, embedded

    def _embed_prompt_texts(self, image_names, prompt_lookup, extra_vocab=None):
        """Embed cleaned prompts + parse tags.  Returns (vecs, has_text, tags_list)."""
        import torch, numpy as np, open_clip
        model, _, device = _load_clip_model()
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        vectors, has_text_flags, tags_list = [], [], []
        for name in image_names:
            raw = (prompt_lookup or {}).get(name, '') or ''
            tags = self._parse_prompt_tags(raw, extra_vocab)
            tags_list.append(tags)
            clean = self._clean_prompt_for_embedding(raw)
            if clean:
                try:
                    tokens = tokenizer([clean]).to(device)
                    with torch.no_grad():
                        vec = model.encode_text(tokens)
                        vec = vec / vec.norm(dim=-1, keepdim=True)
                    vectors.append(vec.cpu().numpy().astype(np.float32).squeeze(0))
                    has_text_flags.append(True)
                    continue
                except Exception:
                    pass
            vectors.append(np.zeros(512, dtype=np.float32))
            has_text_flags.append(False)
        return (np.array(vectors, dtype=np.float32),
                np.array(has_text_flags, dtype=bool),
                tags_list)

    # ------------------------------------------------------------------
    # Build / update index
    # ------------------------------------------------------------------

    def build_index(self, image_folder, image_names,
                    prompt_lookup=None, progress_callback=None, completion_callback=None):
        """Full rebuild with vocabulary discovery."""
        with self._build_lock:
            if not _ensure_dependencies():
                msg = (f"Could not install required packages. "
                       f"Run: {sys.executable} -m pip install "
                       f"torch open-clip-torch numpy Pillow torchvision")
                print(f"[SimilarityManager] {msg}")
                if completion_callback:
                    completion_callback(False, msg)
                return
            self.set_cache_path(image_folder)
            self.is_ready = False
            to_embed = [n for n in image_names
                        if os.path.splitext(n)[1].lower() in self.SUPPORTED_EXTENSIONS]
            print(f"[SimilarityManager] Building index for {len(to_embed)} images…")
            try:
                import numpy as np

                # Step 1: visual embeddings
                new_vecs, new_names = self._embed_images(
                    image_folder, to_embed, progress_callback)
                if not new_names:
                    if completion_callback:
                        completion_callback(False, "No images could be embedded.")
                    return

                # Step 2: vocabulary discovery from all available prompts
                all_prompts = list((prompt_lookup or {}).values())
                self.discovered_vocab = _discover_vocabulary_from_prompts(all_prompts)

                # Step 3: text embeddings + tag parsing (with discovered vocab)
                text_vecs, has_text_arr, tags_list = self._embed_prompt_texts(
                    new_names, prompt_lookup, extra_vocab=self.discovered_vocab)

                self.embeddings      = new_vecs
                self.text_embeddings = text_vecs
                self.has_text        = has_text_arr
                self.filenames       = new_names
                self._index          = {n: i for i, n in enumerate(new_names)}
                self.prompt_tags     = {n: tags_list[i] for i, n in enumerate(new_names)}
                self.is_ready  = True
                self.is_legacy = False
                self._save_cache()
                self._save_vocab_json()

                has_count = int(has_text_arr.sum())
                total_disc = sum(len(v) for v in self.discovered_vocab.values())
                msg = (f"Index built: {len(new_names)} images, "
                       f"{has_count} with text embeddings, "
                       f"{total_disc} vocabulary terms discovered.")
                print(f"[SimilarityManager] {msg}")
                if completion_callback:
                    completion_callback(True, msg)
            except Exception as e:
                msg = f"Index build failed: {e}"
                print(f"[SimilarityManager] ERROR – {msg}")
                if completion_callback:
                    completion_callback(False, msg)

    def build_index_async(self, image_folder, image_names,
                          prompt_lookup=None, progress_callback=None, completion_callback=None):
        t = threading.Thread(target=self.build_index,
                             args=(image_folder, image_names, prompt_lookup,
                                   progress_callback, completion_callback), daemon=True)
        t.start()
        return t

    def update_index(self, image_folder, image_names,
                     prompt_lookup=None, progress_callback=None, completion_callback=None):
        """Embed only new images.  Re-runs vocabulary discovery over ALL prompts."""
        with self._build_lock:
            existing = set(self.filenames)
            new_names = [n for n in image_names
                         if n not in existing
                         and os.path.splitext(n)[1].lower() in self.SUPPORTED_EXTENSIONS]
            if not new_names:
                print("[SimilarityManager] Index already up to date.")
                if completion_callback:
                    completion_callback(True, "Index already up to date.")
                return
            print(f"[SimilarityManager] Adding {len(new_names)} new images to index…")
            try:
                import numpy as np
                new_vecs, embedded = self._embed_images(
                    image_folder, new_names, progress_callback)
                if not embedded:
                    if completion_callback:
                        completion_callback(False, "No new images could be embedded.")
                    return

                # Re-run discovery over the full prompt set (new + existing)
                all_prompts = list((prompt_lookup or {}).values())
                self.discovered_vocab = _discover_vocabulary_from_prompts(all_prompts)

                text_vecs, has_text_arr, tags_list = self._embed_prompt_texts(
                    embedded, prompt_lookup, extra_vocab=self.discovered_vocab)

                self.embeddings = (np.vstack([self.embeddings, new_vecs])
                                   if self.embeddings is not None and len(self.embeddings) > 0
                                   else new_vecs)
                if self.text_embeddings is not None:
                    self.text_embeddings = np.vstack([self.text_embeddings, text_vecs])
                    self.has_text = np.concatenate([self.has_text, has_text_arr])
                else:
                    n_old = len(self.filenames)
                    self.text_embeddings = np.vstack([
                        np.zeros((n_old, 512), dtype=np.float32), text_vecs])
                    self.has_text = np.concatenate([
                        np.zeros(n_old, dtype=bool), has_text_arr])

                self.filenames.extend(embedded)
                self._index = {n: i for i, n in enumerate(self.filenames)}
                for i, n in enumerate(embedded):
                    self.prompt_tags[n] = tags_list[i]
                self.is_ready  = True
                self.is_legacy = False
                self._save_cache()
                self._save_vocab_json()

                total_disc = sum(len(v) for v in self.discovered_vocab.values())
                msg = (f"Added {len(embedded)} embeddings ({len(self.filenames)} total), "
                       f"{total_disc} vocabulary terms.")
                print(f"[SimilarityManager] {msg}")
                if completion_callback:
                    completion_callback(True, msg)
            except Exception as e:
                msg = f"Incremental update failed: {e}"
                print(f"[SimilarityManager] ERROR – {msg}")
                if completion_callback:
                    completion_callback(False, msg)

    def update_index_async(self, image_folder, image_names,
                           prompt_lookup=None, progress_callback=None, completion_callback=None):
        t = threading.Thread(target=self.update_index,
                             args=(image_folder, image_names, prompt_lookup,
                                   progress_callback, completion_callback), daemon=True)
        t.start()
        return t

    # ------------------------------------------------------------------
    # Hybrid similarity queries
    # ------------------------------------------------------------------

    def get_visual_similarity(self, a: str, b: str) -> float:
        if not self.is_ready or self.embeddings is None:
            return 0.5
        if a not in self._index or b not in self._index:
            return 0.5
        try:
            import numpy as np
            va = self.embeddings[self._index[a]]
            vb = self.embeddings[self._index[b]]
            return float(max(0.0, min(1.0, (np.dot(va, vb) + 1.0) / 2.0)))
        except Exception:
            return 0.5

    def get_text_similarity(self, a: str, b: str) -> float:
        if self.text_embeddings is None or self.has_text is None:
            return 0.5
        if a not in self._index or b not in self._index:
            return 0.5
        ia, ib = self._index[a], self._index[b]
        if not self.has_text[ia] or not self.has_text[ib]:
            return 0.5
        try:
            import numpy as np
            va = self.text_embeddings[ia]
            vb = self.text_embeddings[ib]
            return float(max(0.0, min(1.0, (np.dot(va, vb) + 1.0) / 2.0)))
        except Exception:
            return 0.5

    def get_tag_similarity(self, a: str, b: str) -> float:
        tags_a = self.prompt_tags.get(a, {})
        tags_b = self.prompt_tags.get(b, {})
        return self._tag_overlap_score(tags_a, tags_b)

    def get_hybrid_similarity(self, a: str, b: str,
                               w_visual=0.5, w_text=0.3, w_tags=0.2) -> dict:
        visual = self.get_visual_similarity(a, b)
        text   = self.get_text_similarity(a, b)
        tags   = self.get_tag_similarity(a, b)
        return {'hybrid': w_visual*visual + w_text*text + w_tags*tags,
                'visual': visual, 'text': text, 'tags': tags}

    def get_similar_images(self, query_image: str, candidate_list: List[str],
                           top_n: int = 20, w_visual: float = 0.5,
                           w_text: float = 0.3, w_tags: float = 0.2
                           ) -> List[Tuple[str, float]]:
        if not self.is_ready or self.embeddings is None:
            return [(n, 0.5) for n in candidate_list[:top_n]]
        if query_image not in self._index:
            return [(n, 0.5) for n in candidate_list[:top_n]]
        try:
            import numpy as np
            q_idx  = self._index[query_image]
            q_vis  = self.embeddings[q_idx]
            has_tex = (self.text_embeddings is not None
                       and self.has_text is not None
                       and bool(self.has_text[q_idx]))
            q_tex  = self.text_embeddings[q_idx] if has_tex else None
            q_tags = self.prompt_tags.get(query_image, {})
            results = []
            for name in candidate_list:
                if name not in self._index:
                    results.append((name, 0.5))
                    continue
                idx = self._index[name]
                vis = float(max(0.0, min(1.0,
                    (np.dot(q_vis, self.embeddings[idx]) + 1.0) / 2.0)))
                if has_tex and self.has_text[idx]:
                    tex = float(max(0.0, min(1.0,
                        (np.dot(q_tex, self.text_embeddings[idx]) + 1.0) / 2.0)))
                else:
                    tex = 0.5
                tag_score = self._tag_overlap_score(
                    q_tags, self.prompt_tags.get(name, {}))
                score = w_visual*vis + w_text*tex + w_tags*tag_score
                results.append((name, score))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_n]
        except Exception as e:
            print(f"[SimilarityManager] get_similar_images error: {e}")
            return [(n, 0.5) for n in candidate_list[:top_n]]

    def get_similarity_score(self, a: str, b: str) -> float:
        return self.get_visual_similarity(a, b)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        total_disc = sum(len(v) for v in self.discovered_vocab.values())
        return {
            "is_ready":             self.is_ready,
            "embedded_count":       len(self.filenames),
            "has_text_embeddings":  self.text_embeddings is not None,
            "has_tags":             bool(self.prompt_tags),
            "discovered_vocab_total": total_disc,
            "cache_path":           self.cache_path or "not set",
            "vocab_path":           self.vocab_path or "not set",
        }

    def count_missing(self, image_names: List[str]) -> int:
        return sum(1 for n in image_names if n not in self._index)

    def clear(self) -> None:
        self.embeddings = self.text_embeddings = self.has_text = None
        self.filenames, self._index, self.prompt_tags = [], {}, {}
        self.discovered_vocab = {'artists': {}, 'roles': {}, 'styles': {}, 'settings': {}}
        self.is_ready  = False
        self.is_legacy = False
        print("[SimilarityManager] Cleared in-memory state.")

    # ------------------------------------------------------------------
    # CLIP concept explanation (visual concepts vocabulary)
    # ------------------------------------------------------------------

    VISUAL_CONCEPTS = [
        "a portrait of a person", "a group of people", "a landscape",
        "an indoor scene", "an outdoor scene", "a fantasy scene",
        "a character in armor", "a character in robes", "a character with a weapon",
        "bright lighting", "dark lighting", "dramatic lighting", "soft lighting",
        "warm color palette", "cool color palette", "moody atmosphere",
        "photorealistic", "painterly style", "digital art", "concept art",
        "anime style", "illustration", "cinematic composition",
        "highly detailed", "stylized", "close-up face", "full body shot",
        "metallic surfaces", "fabric and cloth", "magic and glowing effects",
        "smoke and fog", "fire and light effects",
    ]

    _concept_emb_cache = None
    _concept_emb_lock  = threading.Lock()

    def _get_concept_embeddings(self):
        if SimilarityManager._concept_emb_cache is not None:
            return SimilarityManager._concept_emb_cache
        with SimilarityManager._concept_emb_lock:
            if SimilarityManager._concept_emb_cache is not None:
                return SimilarityManager._concept_emb_cache
            if not _ensure_dependencies():
                return None
            try:
                import torch, numpy as np, open_clip
                model, _, device = _load_clip_model()
                tokenizer = open_clip.get_tokenizer("ViT-B-32")
                tokens = tokenizer(self.VISUAL_CONCEPTS).to(device)
                with torch.no_grad():
                    vecs = model.encode_text(tokens)
                    vecs = vecs / vecs.norm(dim=-1, keepdim=True)
                SimilarityManager._concept_emb_cache = vecs.cpu().numpy().astype("float32")
            except Exception as e:
                print(f"[SimilarityManager] Could not compute concept embeddings: {e}")
                return None
        return SimilarityManager._concept_emb_cache

    def get_image_concepts(self, image_name: str, top_n: int = 5) -> List[Tuple[str, float]]:
        if not self.is_ready or image_name not in self._index:
            return []
        concept_embs = self._get_concept_embeddings()
        if concept_embs is None:
            return []
        try:
            import numpy as np
            img_vec = self.embeddings[self._index[image_name]]
            scores  = (concept_embs @ img_vec + 1.0) / 2.0
            scores  = scores.clip(0.0, 1.0)
            top     = scores.argsort()[::-1][:top_n]
            return [(self.VISUAL_CONCEPTS[i], float(scores[i])) for i in top]
        except Exception:
            return []

    def explain_similarity(self, a: str, b: str,
                           w_visual=0.5, w_text=0.3, w_tags=0.2) -> dict:
        hybrid     = self.get_hybrid_similarity(a, b, w_visual, w_text, w_tags)
        concepts_a = self.get_image_concepts(a)
        concepts_b = self.get_image_concepts(b)
        tags_a     = self.prompt_tags.get(a, {})
        tags_b     = self.prompt_tags.get(b, {})
        labels_a   = {l: s for l, s in concepts_a}
        labels_b   = {l: s for l, s in concepts_b}
        shared_vis = sorted(
            [(l, (labels_a[l]+labels_b[l])/2.0) for l in set(labels_a) & set(labels_b)],
            key=lambda x: x[1], reverse=True)
        shared_tags = {}
        for bucket in ('artists', 'roles', 'styles'):
            da, db = tags_a.get(bucket, {}), tags_b.get(bucket, {})
            shared = sorted([(k, (da[k]+db[k])/2.0) for k in set(da) & set(db)],
                            key=lambda x: x[1], reverse=True)
            if shared:
                shared_tags[bucket] = shared
        return {
            'hybrid': hybrid['hybrid'], 'visual': hybrid['visual'],
            'text': hybrid['text'],     'tags': hybrid['tags'],
            'concepts_a': concepts_a,   'concepts_b': concepts_b,
            'shared_visual': shared_vis, 'tags_a': tags_a, 'tags_b': tags_b,
            'shared_tags': shared_tags,
        }
