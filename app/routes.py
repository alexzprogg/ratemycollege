from flask import Blueprint, render_template, request, redirect, url_for
from .models import Review
import json
from flask import jsonify
import os
from app import db
from .nlp_utils import extract_trending_hashtags
from .recommender_utils import (
    get_priorities_from_text,
    build_college_tag_vector,
    tag_similarity_boost_from_vec,
)
from .embedding_utils import upsert_review_embedding

def calculate_avg_ratings(reviews):
    categories = ['food', 'social', 'clubs', 'study', 'opportunities']
    avg_ratings = {}
    for category in categories:
        values = [getattr(r, category) for r in reviews if getattr(r, category) not in (None, 0)]
        if values:
            avg_ratings[category] = round(sum(values) / len(values), 1)
        else:
            avg_ratings[category] = None  # None means not rated yet
    return avg_ratings


COLLEGE_JSON_PATH = os.path.join(os.path.dirname(__file__), '../data/colleges.json')

def get_college_stats():
    college_display_names = {
        "uc": "University College",
        "trinity": "Trinity College",
        "victoria": "Victoria College",
        "stmikes": "St. Michael’s College",
        "woods": "Woodsworth College",
        "innis": "Innis College",
        "new": "New College"
    }

    college_data = []
    for college_key, display_name in college_display_names.items():
        reviews = Review.query.filter_by(college_name=college_key).all()

        if reviews:
            # Compute the average rating per review (only over non-zero categories)
            per_review_avgs = []
            for r in reviews:
                scores = [r.food, r.social, r.clubs, r.study, r.opportunities]
                valid_scores = [s for s in scores if s is not None]
                if valid_scores:
                    per_review_avgs.append(sum(valid_scores) / len(valid_scores))

            # Count how many categories across all reviews actually got rated
            category_ratings = calculate_avg_ratings(reviews)
            num_valid_categories = sum(1 for score in category_ratings.values() if score is not None)

            # Require at least 3 categories to be rated to include in Top-Rated
            if per_review_avgs and num_valid_categories >= 3:
                avg_score = round(sum(per_review_avgs) / len(per_review_avgs), 2)
            else:
                avg_score = None  # Will be excluded from top-rated list
            has_few_ratings = len(reviews) < 3 or num_valid_categories < 3
            hashtags = extract_trending_hashtags(reviews, num_topics=3, num_words=4)[:3]
            # NEW: normalize + vectorize once per college
            clean_tags = []
            for t in hashtags or []:
                if isinstance(t, str) and t.startswith('#'):
                    t = t[1:]
                if t:
                    clean_tags.append(t)

            tag_vec = build_college_tag_vector(clean_tags)  # may return None if no tags

            college_data.append({
                'name': display_name,
                'avg_rating': round(avg_score, 2) if avg_score is not None else None,
                'id': college_key,
                'hashtags': hashtags,
                'clean_tags': clean_tags,      # (optional: handy for display)
                'tag_vec': tag_vec,            # 👈 store the vector
                'category_ratings': category_ratings,
                'has_few_ratings': has_few_ratings
            })
        else:
            college_data.append({
                'name': display_name,
                'avg_rating': None,
                'id': college_key,
                'hashtags': [],
                'category_ratings': {},
                'has_few_ratings': True  # No reviews means few ratings
            })

    return sorted(college_data, key=lambda x: x['avg_rating'] or 0, reverse=True)

with open(COLLEGE_JSON_PATH) as f:
    college_info = json.load(f)


main = Blueprint('main', __name__) # This creates a blueprint named 'main' for organizing routes


@main.route('/')
def home():
    all_reviews = Review.query.all()
    trending_hashtags = extract_trending_hashtags(all_reviews) 

    all_college_stats = get_college_stats()
    top_colleges = [c for c in all_college_stats if not c['has_few_ratings']][:3] # Get top 3 colleges with sufficient ratings

    return render_template('home.html', top_colleges=top_colleges, trending_tags=trending_hashtags)

@main.route('/admin/clear_reviews')
def clear_reviews():
    Review.query.delete()
    db.session.commit()
    return "All reviews deleted."

@main.route('/colleges')
def colleges():
    college_data = get_college_stats()
    return render_template('colleges.html', colleges=college_data)

@main.route('/colleges/<college_name>', methods=["GET", "POST"])
def college_profile(college_name):
    if request.method == "POST":
        data = request.get_json() or {}
        rated = set(data.get("rated_categories", []))  # e.g., ["food","social"]

        def val(cat):
            # Only accept a number if the category was actually selected
            return int(data.get(cat)) if cat in rated and str(data.get(cat)).isdigit() else None

        review = Review(
            college_name=college_name.lower(),
            user=data.get("user"),
            text=data.get("text"),
            food=val("food"),
            social=val("social"),
            clubs=val("clubs"),
            study=val("study"),
            opportunities=val("opportunities"),
            tags=json.dumps(data.get("tags", [])),
            rated_categories=json.dumps(list(rated))
        )

        db.session.add(review)
        db.session.commit()
        upsert_review_embedding(review.id)
        return jsonify({"status": "success"}), 200

    reviews = Review.query.filter_by(college_name=college_name.lower()).all()
    avg_ratings = calculate_avg_ratings(reviews)
    college = college_info.get(college_name.lower(), {"name": college_name})

    return render_template(
    "college_profile.html",
    college=college,
    reviews=reviews,
    avg_ratings=avg_ratings,
    json=json  # ✅ allows use of json.loads in template
    )

@main.route('/generate_tags', methods=['POST'])
def generate_tags():
    from .nlp_utils import extract_tags_from_text

    data = request.get_json()
    text = data.get("text", "")
    tags = extract_tags_from_text(text)
    return jsonify({"tags": tags})

@main.route('/recommend', methods=['POST'])
def recommend():
    query = request.form.get("query", "").strip()

    # ✅ Get list of selected checkboxes (not just one)
    selected_categories = request.form.getlist("priority_categories")

    if not query and not selected_categories:
        return render_template('recommend_results.html', query="", preferences=[], recommendations=[])

    # ✅ Manual boosts: +0.25 weight for each selected category
    manual_weights = {}
    for cat in selected_categories:
        if cat in ['food', 'social', 'clubs', 'study', 'opportunities']:
            manual_weights[cat] = manual_weights.get(cat, 0) + 0.25

    # ✅ Get weighted priorities
    preferences = get_priorities_from_text(query, manual_weights=manual_weights)

    all_colleges = get_college_stats()

    # --- score & rank ---
    def score_and_explain(college, query_text, prefs):
        """
        Returns (final_score, cat_score, tag_bonus, contributions)
        where contributions = list of (category, weight, category_value, weighted_points)
        """
        contributions = []
        cat_score_num, cat_score_den = 0.0, 0.0

        for category, weight in (prefs or []):
            cat_value = float(college.get('category_ratings', {}).get(category) or 0.0)  # 0..10
            points = weight * cat_value
            contributions.append((category, round(weight, 4), round(cat_value, 2), round(points, 2)))
            cat_score_num += points
            cat_score_den += weight

        cat_score = (cat_score_num / cat_score_den) if cat_score_den else 0.0

        # Tag similarity bonus
        # NEW: use precomputed vector
        tag_vec = college.get('tag_vec')
        tag_bonus = tag_similarity_boost_from_vec(query_text or "", tag_vec, alpha=0.6)  # bonus ~0..0.6

        final = min(10.0, cat_score + tag_bonus)
        return round(final, 2), round(cat_score, 2), round(tag_bonus, 2), contributions

    filtered_colleges = [c for c in all_colleges if c.get('avg_rating') is not None]

    # If preferences ended up empty (e.g., blank query & no checkboxes), use a neutral default:
    effective_prefs = preferences if preferences else []

    for college in filtered_colleges:
        match_score, cat_score, tag_bonus, contribs = score_and_explain(college, query, effective_prefs)
        college['match_score'] = match_score
        college['cat_score'] = cat_score
        college['tag_bonus'] = tag_bonus
        college['contributions'] = contribs  # e.g. [('study', 0.52, 7.8, 4.06), ...]

    # ✅ Add "why this match?" explanation tags
    why_tags = []
    if college.get('clean_tags'):
        from .recommender_utils import top_similar_tags
        why_tags = top_similar_tags(query or "", college['clean_tags'], k=3)
    college['why_tags'] = why_tags
    
    ranked = sorted(filtered_colleges, key=lambda c: c['match_score'], reverse=True)
    
    return render_template(
        'recommend_results.html',
        query=query,
        preferences=preferences,      # keep original (may be empty); template can render it
        recommendations=ranked
    )




