from sentence_transformers import SentenceTransformer, util
import torch
model = SentenceTransformer('all-MiniLM-L6-v2')
model.max_seq_length = 256
import numpy as np
import re

category_anchors = {
    "study": ["academics", "grades", "homework", "GPA", "learning", "studying", "rigor", "coursework", "professors"],
    "social": ["parties", "friends", "community", "social life", "fun", "vibe", "nightlife", "events", "hanging out", "meeting people"],
    "clubs": ["clubs", "sports", "activities", "organizations", "intramurals", "student groups", "societies"],
    "opportunities": ["career", "jobs", "internships", "research", "networking", "co-op", "mentorship"],
    "food": ["food", "cafeteria", "dining", "meal plan", "canteen", "snacks", "dining hall"]
}

EXPLICIT_KEYWORDS = {
    "study": ["academic", "academics", "study", "studying", "rigor", "gpa"],
    "social": ["social", "party", "parties", "friends", "community", "fun", "vibe", "nightlife"],
    "clubs": ["club", "clubs", "society", "societies", "intramural", "intramurals", "sports", "team"],
    "opportunities": ["internship", "internships", "career", "job", "jobs", "research", "network", "networking", "co-op"],
    "food": ["food", "dining", "cafeteria", "meal", "meals", "canteen"]
}
def _explicit_boosts(user_input: str, boost=0.15):
    text = user_input.lower()
    bumps = {}
    for cat, tokens in EXPLICIT_KEYWORDS.items():
        if any(t in text for t in tokens):
            bumps[cat] = bumps.get(cat, 0.0) + boost
    return bumps

anchor_embeddings = {
    category: model.encode(words, convert_to_tensor=True) # Encode each category's anchor words
    for category, words in category_anchors.items() # Create embeddings for each category's anchor words 
}

def softmax(x):
    e_x = np.exp(x - np.max(x))  # improves numerical stability
    return e_x / e_x.sum()

def get_priorities_from_text(user_input, top_n=3, manual_weights=None, min_threshold=0.12):
    input_embedding = model.encode(user_input, convert_to_tensor=True)

    # 1) base similarity
    scores = {}
    for category, embeddings in anchor_embeddings.items():
        sim = util.cos_sim(input_embedding, embeddings)
        avg = float(sim.mean())
        scores[category] = avg

    # 2) explicit keyword bumps
    for cat, bump in _explicit_boosts(user_input, boost=0.15).items():
        scores[cat] = scores.get(cat, 0.0) + bump

    # 3) manual checkbox boosts
    if manual_weights:
        for cat, bump in manual_weights.items():
            scores[cat] = scores.get(cat, 0.0) + bump

    # prune very low signals, then take top_n
    pruned = {c: s for c, s in scores.items() if s >= min_threshold}
    if not pruned:
        return []

    top = sorted(pruned.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # softmax to weights
    raw = np.array([s for _, s in top], dtype=float)
    w = softmax(raw)
    return [(cat, float(round(wi, 4))) for (cat, _), wi in zip(top, w)]

_TAG_EMB_CACHE = {}

def _normalize_tag(t: str) -> str:
    """Lowercase, strip leading '#', remove odd punctuation/spaces."""
    t = (t or "").strip().lower()
    if t.startswith("#"):
        t = t[1:]
    # keep letters/numbers/spaces/dashes/underscores/slashes
    t = re.sub(r"[^a-z0-9\-\_/ ]", "", t)
    # collapse whitespace -> single space
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _embed_tag(tag: str):
    """Memoize individual tag embeddings for speed."""
    key = _normalize_tag(tag)
    if not key:
        return None
    if key in _TAG_EMB_CACHE:
        return _TAG_EMB_CACHE[key]
    emb = model.encode(key, convert_to_tensor=True)
    _TAG_EMB_CACHE[key] = emb
    return emb

def _mean_pool_tensors(tensors):
    return torch.stack(tensors, dim=0).mean(dim=0) if tensors else None

def build_college_tag_vector(raw_tags):
    """
    Build a single mean-pooled embedding for a college's tag list.
    Call this once when you assemble college data (e.g., in get_college_stats()).
    """
    vecs = []
    for t in raw_tags or []:
        emb = _embed_tag(t)
        if emb is not None:
            vecs.append(emb)
    return _mean_pool_tensors(vecs)

def tag_similarity_boost_from_vec(query_text: str, tag_vec, alpha: float = 0.6) -> float:
    """
    Compute a small additive bonus from similarity between query and a precomputed tag vector.
    - cosine s in [-1, 1] -> [0, 1] via (s+1)/2
    - bonus = alpha * normalized_similarity
    => bonus in [0, alpha]
    """
    if not query_text or tag_vec is None:
        return 0.0
    q = model.encode(query_text, convert_to_tensor=True)
    s = float(util.cos_sim(q, tag_vec).item())        # [-1, 1]
    s01 = max(0.0, (s + 1.0) / 2.0)                   # [0, 1]
    return round(alpha * s01, 2)

# Optional for “why” explanation:
def top_similar_tags(query_text: str, tags, k=3):
    if not query_text or not tags:
        return []
    q = model.encode(query_text, convert_to_tensor=True)
    scored = []
    for t in tags:
        emb = _embed_tag(t)
        if emb is None:
            continue
        s = float(util.cos_sim(q, emb).item())
        scored.append((t, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in scored[:k]]