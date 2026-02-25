from sqlalchemy.orm import Session
from src.db.models import Game, GameListing, Store, PriceHistory
from src.services.normalization import TitleNormalizer

def process_scraped_game(
    db: Session, store_id: int, store_name: str, raw_title: str, 
    remote_id: str, url: str, price: float, currency: str, discount_percent: int
):
    """
    Core business logic: Find or create the store, game, and listing, 
    then record the latest price.
    """
    # 1. Store
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        store = Store(id=store_id, name=store_name, base_url="https://example.com")
        db.add(store)
        db.commit()

    # 2. Game
    clean_title = TitleNormalizer.normalize(raw_title)
    slug = clean_title.replace(" ", "-")
    
    game = db.query(Game).filter(Game.slug == slug).first()
    if not game:
        game = Game(title=clean_title, slug=slug)
        db.add(game)
        db.commit()
        db.refresh(game)
        
    # 3. Listing
    listing = db.query(GameListing).filter(
        GameListing.store_id == store_id, 
        GameListing.remote_id == remote_id
    ).first()
    
    if not listing:
        listing = GameListing(
            game_id=game.id,
            store_id=store_id,
            remote_id=remote_id,
            listing_title=raw_title,
            url=str(url)
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)

    # 4. Price History (NEW)
    price_record = PriceHistory(
        listing_id=listing.id,
        price=price,
        currency=currency,
        discount_percent=discount_percent
    )
    db.add(price_record)
    db.commit()
        
    return game