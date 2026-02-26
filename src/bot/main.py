import asyncio
import logging
import sys
import os

# Add project root to path to ensure correct imports
sys.path.append(os.getcwd())

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Import settings and database models
from src.core.config import settings
from src.api.v1.dependencies import SessionLocal
from src.db.models import Game

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Handles the /start command. Includes a subtle 'Papers, Please' easter egg.
    """
    logger.info(f"User {message.from_user.id} started the bot.")
    welcome_text = (
        f"Greetings, Inspector {message.from_user.full_name}. 🛂\n\n"
        f"Welcome to GamePulse. I am here to track game prices and discounts across multiple stores.\n\n"
        f"Commands available:\n"
        f"/search <title> - Search for a specific game\n"
        f"/status - Check system health and collection size\n"
        f"/games - List all tracked games"
    )
    await message.answer(welcome_text)


@dp.message(Command("status"))
async def status_handler(message: Message) -> None:
    """
    Handles the /status command. Returns collection count and system health.
    """
    logger.info(f"User {message.from_user.id} requested system status.")
    db = SessionLocal()
    try:
        games_count = db.query(Game).count()
        await message.answer(f"🟢 Collection: {games_count} games\n\nDatabase: Connected\nScraper: Ready")
    except Exception as e:
        logger.error(f"Database error in status: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


@dp.message(Command("search"))
async def search_handler(message: Message) -> None:
    """
    Handles the /search command. Expects a query: /search witcher
    """
    # Extract query from the message text
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        await message.answer("Please provide a game title. Example: /search witcher")
        return
        
    query = command_parts[1]
    
    if len(query) < 2:
        await message.answer("Search query is too short. Please enter at least 2 characters.")
        return

    logger.info(f"User {message.from_user.id} searched for: {query}")
    
    db = SessionLocal()
    try:
        # Case-insensitive search using ilike
        games = db.query(Game).filter(Game.title.ilike(f"%{query}%")).limit(5).all()

        if not games:
            await message.answer(f"🔍 No games found matching '{query}'.")
            return

        response_text = f"🔍 Search results for '{query}':\n\n"
        for game in games:
            response_text += f"🔹 {game.title.title()}\n"

            # Iterate through all store listings for this game
            for listing in game.listings:
                if listing.prices:
                    # Get the most recent price record (last in the list)
                    latest_price = listing.prices[-1]
                    price_info = f"{latest_price.price} {latest_price.currency}"

                    if latest_price.discount_percent > 0:
                        price_info += f" (📉 -{latest_price.discount_percent}%)"

                    response_text += f"   └ 🏪 {listing.store.name}: {price_info}\n"
                else:
                    response_text += (
                        f"   └ 🏪 {listing.store.name}: Waiting for price...\n"
                    )
            response_text += "\n"

        await message.answer(response_text)
    except Exception as e:
        logger.error(f"Database error during search: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


@dp.message(Command("games"))
async def games_handler(message: Message) -> None:
    """
    Handles the /games command. Fetches games, stores, and latest prices.
    """
    logger.info(f"User {message.from_user.id} requested the games list.")

    db = SessionLocal()
    try:
        games = db.query(Game).limit(10).all()

        if not games:
            await message.answer(
                "📭 The database is currently empty. Run the scraper first."
            )
            return

        response_text = "🎮 Tracked Games & Prices:\n\n"
        for game in games:
            response_text += f"🔹 {game.title.title()}\n"

            # Iterate through all store listings for this game
            for listing in game.listings:
                if listing.prices:
                    # Get the most recent price record (last in the list)
                    latest_price = listing.prices[-1]
                    price_info = f"{latest_price.price} {latest_price.currency}"

                    if latest_price.discount_percent > 0:
                        price_info += f" (📉 -{latest_price.discount_percent}%)"

                    response_text += f"   └ 🏪 {listing.store.name}: {price_info}\n"
                else:
                    response_text += (
                        f"   └ 🏪 {listing.store.name}: Waiting for price...\n"
                    )
            response_text += "\n"

        await message.answer(response_text)
    except Exception as e:
        logger.error(f"Database error: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


async def main() -> None:
    """
    Main entry point for the Telegram bot.
    """
    logger.info("Starting PricesPleaseBot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())