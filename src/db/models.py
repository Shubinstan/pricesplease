# src/db/models.py
import uuid
from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import ForeignKey, String, DateTime, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# 1. Base Class
class Base(DeclarativeBase):
    pass

# 2. Enum for Listing Status
class ListingStatus(str, Enum):
    ACTIVE = "active"       # Link is working, price is monitored
    BROKEN = "broken"       # 404 Not Found
    PENDING = "pending"     # New game, needs normalizer check

# 3. Master Table: Unique Games
class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), index=True) # Normalized title
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True) # E.g., the-witcher-3
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship: One Game -> Many Listings
    listings: Mapped[List["GameListing"]] = relationship(back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(title='{self.title}')>"

# 4. Reference Table: Stores
class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True) # 1=Steam, 2=Epic, etc.
    name: Mapped[str] = mapped_column(String(50), unique=True)
    base_url: Mapped[str] = mapped_column(String(255))
    
    listings: Mapped[List["GameListing"]] = relationship(back_populates="store")

# 5. Variant Table: Specific Store Listings
class GameListing(Base):
    __tablename__ = "game_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id"))
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    
    # Store-specific data
    remote_id: Mapped[str] = mapped_column(String(100)) # e.g., AppID in Steam
    listing_title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    status: Mapped[ListingStatus] = mapped_column(default=ListingStatus.ACTIVE)
    
    # Relationships
    game: Mapped["Game"] = relationship(back_populates="listings")
    store: Mapped["Store"] = relationship(back_populates="listings")
    prices: Mapped[List["PriceHistory"]] = relationship(back_populates="listing", cascade="all, delete-orphan")

    # Constraints: remote_id must be unique per store
    __table_args__ = (
        Index('ix_store_remote_id', 'store_id', 'remote_id', unique=True),
    )

# 6. Time-Series: Price History
class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # FIX: Using UUID to match GameListing.id
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_listings.id", ondelete="CASCADE"), index=True)
    
    # Using Numeric(10, 2) is best practice for precise money representation in Postgres
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    listing: Mapped["GameListing"] = relationship(back_populates="prices")