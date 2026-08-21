import os
from flask import Flask
from dotenv import load_dotenv
from models import db
from services import ensure_current_schema, markdown_to_html, nl2br
from employees import bp as employees_bp
from social import bp as social_bp
from groups import bp as groups_bp
from media import bp as media_bp
from ai import bp as ai_bp

def create_app(config=None):
    load_dotenv()
    app=Flask(__name__)
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///ourteam.db'),SQLALCHEMY_TRACK_MODIFICATIONS=False,SECRET_KEY=os.getenv('SECRET_KEY','dev-only-change-me'),MAX_CONTENT_LENGTH=100*1024*1024,UPLOAD_FOLDER=os.path.join(app.root_path,'static','uploads'),DEFAULT_COMPANY=os.getenv('DEFAULT_COMPANY','OurTeam Industries'),DEFAULT_GPT_ENGINE=os.getenv('OPENROUTER_MODEL','openai/gpt-5.6-luna'),ALLOWED_GPT_ENGINES=['openai/gpt-5.6-luna'])
    if config: app.config.from_mapping(config)
    app.jinja_env.filters['nl2br']=nl2br
    app.jinja_env.filters['markdown']=markdown_to_html
    db.init_app(app)
    for blueprint in (employees_bp,social_bp,groups_bp,media_bp,ai_bp): app.register_blueprint(blueprint)
    return app

def initialize_database(app):
    with app.app_context():
        db.create_all()
        ensure_current_schema()
