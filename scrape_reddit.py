import praw

reddit = praw.Reddit(
    client_id="0M_iBPWprRtgAPOmh6vyWA",
    client_secret="5Knjs7O7Y44WQyjVxmVnxjrRt9JrOA",
    user_agent="RateMyCollegeBot by RateMyCollegeBot"
)

search_terms = [
    "Trinity College UofT", "Innis College UofT", "UC UofT",
    "Woodsworth College UofT", "New College UofT",
    "St. Mike's UofT", "Victoria College UofT"
]

for term in search_terms:
    print(f"🔍 Searching for: {term}")
    for submission in reddit.subreddit("uoft+UofT").search(term, sort="top", time_filter="year", limit=5):
        print("------------------------------------------------")
        print("Title:", submission.title)
        print("Upvotes:", submission.score)
        print("URL:", submission.url)
        print("Text:", submission.selftext)
        print()
