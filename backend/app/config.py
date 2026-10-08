import os

CATEGORIES = ["Electronics", "Home & Garden", "Fashion", "Sports & Outdoors", "Beauty & Personal Care",
              "Toys & Games", "Books & Media", "Automotive", "Home Services", "Professional Services"]
REVISABLE = ["title", "description", "attributes", "tags"]
SEVERITIES = ["critical", "major", "minor", "info"]


class Config:
    # mysql://user:pass@host:3306/dbname   (or sqlite:///path.db / sqlite:///:memory: for local dev & tests)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///listing_reviewer.db")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    DOCS_DIR = os.getenv("DOCS_DIR", os.path.join(os.path.dirname(__file__), "..", "docs"))
