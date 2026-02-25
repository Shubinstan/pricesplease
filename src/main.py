from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api.v1.dependencies import get_db
from src.core.config import settings
from src.db.models import Game
from src.schemas.game import GameScrapeRequest
from src.services.crud import process_scraped_game

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    @app.get("/health", tags=["System"])
    def health_check(db: Session = Depends(get_db)):
        try:
            db.execute(text("SELECT 1"))
            games_count = db.query(Game).count()
            return {"collection": f"Games in collection: {games_count}"}
        except Exception as e:
            return {"error": "db_connection_failed", "details": str(e)}

    # --- NEW ENDPOINT ---
    @app.post("/api/v1/games/parse", tags=["Scraper Integration"])
    def parse_game_webhook(payload: GameScrapeRequest, db: Session = Depends(get_db)):
        """
        Webhook to receive data from parsers.
        Normalizes the title and saves the game and its price.
        """
        game = process_scraped_game(
            db=db,
            store_id=payload.store_id,
            store_name=payload.store_name,
            raw_title=payload.raw_title,
            remote_id=payload.remote_id,
            url=str(payload.url),
            # Pass new fields to CRUD
            price=payload.price,
            currency=payload.currency,
            discount_percent=payload.discount_percent
        )
        
        return {
            "status": "success",
            "message": "Game and price successfully processed",
            "normalized_title": game.title,
            "game_id": game.id
        }

    return app

app = create_app()