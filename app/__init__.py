from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
import os
import click
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Make `json.loads` available as a filter called 'fromjson'
    app.jinja_env.filters['fromjson'] = json.loads

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
    @app.cli.command("embed-all")
    def embed_all_cmd():
        """Embed all reviews and store vectors."""
        from .embedding_utils import batch_embed_all
        click.echo("⏳ Embedding all reviews...")
        batch_embed_all()
        click.echo("✅ Done embedding.")
    return app