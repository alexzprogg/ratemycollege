from app import db # Importing db from app package to use SQLAlchemy ORM for database operations.


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(100), nullable=False)
    user = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    food = db.Column(db.Integer)
    social = db.Column(db.Integer)
    clubs = db.Column(db.Integer)
    study = db.Column(db.Integer)
    opportunities = db.Column(db.Integer)
    tags = db.Column(db.Text)  # <-- NEW: store tags as a JSON-encoded list
    rated_categories = db.Column(db.Text) # <-- NEW: store rated categories as a JSON-encoded list

class ReviewEmbedding(db.Model):
    __tablename__ = "review_embedding"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), unique=True, nullable=False)
    model = db.Column(db.String(64), nullable=False, default='all-MiniLM-L6-v2')
    dim = db.Column(db.Integer, nullable=False)
    vector = db.Column(db.LargeBinary, nullable=False)  # raw bytes of the float32 array

    # optional, handy relationship
    review = db.relationship("Review", backref=db.backref("embedding", uselist=False)) # one-to-one relationship


