from pydantic import BaseModel, HttpUrl

class GameScrapeRequest(BaseModel):
    """
    Incoming data schema from the scraper.
    Validates data before it hits the database.
    """
    store_id: int
    store_name: str
    raw_title: str
    remote_id: str
    url: HttpUrl
    # New fields for pricing
    price: float
    currency: str = "USD"
    discount_percent: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": 1,
                "store_name": "Steam",
                "raw_title": "The Witcher 3: Wild Hunt",
                "remote_id": "292030",
                "url": "https://store.steampowered.com/app/292030/",
                "price": 19.99,
                "currency": "USD",
                "discount_percent": 50
            }
        }