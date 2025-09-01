import spacy
from collections import Counter
from gensim import corpora
from gensim.models import LdaModel
from collections import defaultdict, Counter 
from typing import List
import re 


try:
    from gensim import corpora
    from gensim.models import LdaModel
    HAS_GENSIM = True
except Exception:
    HAS_GENSIM = False

nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])  # leaner model, no NER or text categorization

# Common generic campus terms to downweight/ignore in tags/trends
CONTEXT_STOP = set({
    "college", "campus", "university", "student", "students", "class", "classes",
    "school", "program", "course", "courses", "building", "buildings", "toronto",
    "u", "uoft", "uni", "year", "first", "second", "third", "fourth"
})

def _normalize(s: str) -> str:
    # normalize whitespace & strip punctuation at edges
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".,!?;:'\"()[]{}")
    return s

def _is_good_token(tok):
    return tok.is_alpha and not tok.is_stop and tok.pos_ in {"NOUN", "PROPN", "ADJ"}


def _noun_phrases(doc):
    # yield cleaned noun chunks with >= 2 tokens preferred
    for chunk in doc.noun_chunks:
        toks = [t.lemma_.lower() for t in chunk if _is_good_token(t)]
        if len(toks) >= 2:
            phrase = _normalize(" ".join(toks))
            if phrase and phrase not in CONTEXT_STOP:
                yield phrase


def _unigrams(doc):
    for t in doc:
        if _is_good_token(t):
            lemma = t.lemma_.lower()
            if lemma and lemma not in CONTEXT_STOP:
                yield lemma

def _bigrams(tokens: List[str]):
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i+1]
        if a not in CONTEXT_STOP and b not in CONTEXT_STOP:
            yield f"{a} {b}"

def extract_tags_from_text(text: str, top_n: int = 5) -> List[str]:
    """
    Returns top_n clean tags from a single comment:
      - prefers multiword noun phrases and bigrams
      - falls back to unigram keywords
    """
    doc = nlp(text.lower())

    # candidates: noun phrases > bigrams > unigrams
    phrases = list(_noun_phrases(doc))
    toks = [t.lemma_.lower() for t in doc if _is_good_token(t)]
    bi = list(_bigrams(toks))
    uni = [u for u in _unigrams(doc)]

    # score: frequency, with phrase multiplier
    counts = Counter()
    for p in phrases:
        counts[p] += 3  # boost multiword phrases
    for b in bi:
        counts[b] += 2
    for u in uni:
        counts[u] += 1

    # de-duplicate by stem start (favor longer phrases when overlaps exist)
    seen = set()
    ordered = []
    for cand, _ in counts.most_common():
        key = cand.split()[0]  # crude overlap key
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cand)
        if len(ordered) >= top_n:
            break

    # Final: plain strings (no # here; UI can add # if it wants)
    return ordered

def preprocess_reviews(reviews):
    """
    For trending: return (keyword_lists, flat_keywords)
    We include both unigrams and bigrams to make LDA/topic counts richer.
    """
    all_keywords = []
    flat_keywords = []
    for r in reviews:
        if not r.text:
            continue
        doc = nlp(r.text.lower())
        toks = [t.lemma_.lower() for t in doc if _is_good_token(t)]
        if len(toks) >= 2:
            # include bigrams as tokens too
            bigrams = list(_bigrams(toks))
            tokens = toks + bigrams
            all_keywords.append(tokens)
            flat_keywords.extend(tokens)
    return all_keywords, flat_keywords

def extract_trending_hashtags(reviews, num_topics=5, num_words=5, top_n=5):
    """
    Combine simple frequency with (optional) LDA topic terms.
    Gracefully fallback to frequency-only if gensim not available or data too small.
    Returns tags WITH # for display convenience.
    """
    keyword_lists, flat_keywords = preprocess_reviews(reviews)
    if not keyword_lists:
        return []

    base_counts = Counter(flat_keywords)

    topic_terms = []
    if HAS_GENSIM and len(keyword_lists) >= 3:
        try:
            dictionary = corpora.Dictionary(keyword_lists)
            corpus = [dictionary.doc2bow(tokens) for tokens in keyword_lists]
            lda_model = LdaModel(
                corpus=corpus, id2word=dictionary,
                num_topics=max(1, min(num_topics, len(keyword_lists))),
                random_state=42, passes=8
            )
            for _, topic_str in lda_model.print_topics(num_words=num_words):
                # topic_str example: '0.04*"food" + 0.03*"study spaces" + ...'
                for part in topic_str.split('+'):
                    w = part.split('*')[1].strip().strip('"')
                    w_norm = _normalize(w)
                    if w_norm and w_norm not in CONTEXT_STOP:
                        topic_terms.append(w_norm)
        except Exception:
            # fallback silently
            pass

    combined = base_counts + Counter(topic_terms)

    # prefer multiword > unigram in ties
    def sort_key(item):
        word, freq = item
        return (freq, 1 if " " in word else 0)

    top = sorted(combined.items(), key=sort_key, reverse=True)
    final = []
    seen = set()
    for word, _ in top:
        if word in seen:
            continue
        seen.add(word)
        final.append(f"#{word}")
        if len(final) >= top_n:
            break
    return final
