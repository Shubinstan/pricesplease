import asyncio
import logging
import sys
import os

# Add project root to path to ensure correct imports
sys.path.append(os.getcwd())

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

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
    """Handles the /start command."""
    logger.info(f"User {message.from_user.id} started the bot.")
    welcome_text = (
        f"Greetings, Inspector {message.from_user.full_name}. 🛂\n\n"
        f"Welcome to GamePulse. I am here to track game prices and discounts.\n\n"
        f"Commands available:\n"
        f"/search <title> - Search for a specific game\n"
        f"/status - Check system health and collection size\n"
        f"/games - List all tracked games"
    )
    await message.answer(welcome_text)


@dp.message(Command("status"))
async def status_handler(message: Message) -> None:
    """Handles the /status command."""
    db = SessionLocal()
    try:
        games_count = db.query(Game).count()
        await message.answer(
            f"🟢 Collection: {games_count} games\n\nDatabase: Connected\nScraper: Ready"
        )
    except Exception as e:
        logger.error(f"Database error in status: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


@dp.message(Command("search"))
async def search_handler(message: Message) -> None:
    """Handles the /search command with Live Scraping fallback."""
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) < 2:
        await message.answer("Please provide a game title. Example: /search witcher")
        return

    query = command_parts[1]

    if len(query) < 2:
        await message.answer(
            "Search query is too short. Please enter at least 2 characters."
        )
        return

    logger.info(f"User {message.from_user.id} searched for: {query}")

    db = SessionLocal()
    try:
        # 1. First, search in our local database
        games = db.query(Game).filter(Game.title.ilike(f"%{query}%")).limit(10).all()

        # 2. If the database is empty for this query, trigger LIVE SEARCH
        if not games:
            loading_msg = await message.answer(
                f"⏳ Searching for '{query}' in stores. This might take a few seconds..."
            )

            custom_env = os.environ.copy()
            custom_env["PYTHONIOENCODING"] = "utf-8"

            # Run the scraper as a background process
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "src/services/scraper.py",
                query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=custom_env,
            )

            stdout, stderr = (
                await process.communicate()
            )  # Wait until the scraper finishes its job

            if stdout:
                logger.info(
                    f"Scraper Output:\n{stdout.decode('utf-8', errors='replace')}"
                )
            if stderr:
                logger.error(
                    f"Scraper Error:\n{stderr.decode('utf-8', errors='replace')}"
                )

            # 3. Check the database again after the scraper has finished
            games = (
                db.query(Game).filter(Game.title.ilike(f"%{query}%")).limit(10).all()
            )

            # Delete the "Searching..." loading message
            await loading_msg.delete()

            if not games:
                await message.answer(
                    f"🔍 Unfortunately, the game '{query}' was not found in stores either."
                )
                return

        # 4. Create Inline Keyboard with the results
        keyboard = []
        for game in games:
            # callback_data is limited to 64 bytes. UUID is 36 chars.
            button = InlineKeyboardButton(
                text=game.title.title(), callback_data=f"game_{game.id}"
            )
            keyboard.append([button])  # One button per row

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer(
            f"🔍 Found {len(games)} games for '{query}'. Please choose:",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Database error during search: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


@dp.callback_query(F.data.startswith("game_"))
async def game_selection_handler(callback: CallbackQuery) -> None:
    """Handles clicks on the game inline buttons."""
    # Extract the UUID from the callback data (e.g., "game_1234-5678-...")
    game_id = callback.data.split("_")[1]

    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()

        if not game:
            await callback.message.edit_text("❌ Game not found in database anymore.")
            await callback.answer()
            return

        response_text = f"🎮 **{game.title.title()}**\n\n"

        if not game.listings:
            response_text += "No store listings found yet."
        else:
            for listing in game.listings:
                if listing.prices:
                    latest_price = listing.prices[-1]
                    price_info = f"{latest_price.price} {latest_price.currency}"

                    if latest_price.discount_percent > 0:
                        price_info += f" (📉 -{latest_price.discount_percent}%)"

                    response_text += f"   └ 🏪 {listing.store.name}: {price_info}\n"
                else:
                    response_text += (
                        f"   └ 🏪 {listing.store.name}: Waiting for price...\n"
                    )

        # Edit the original message to show the details instead of buttons
        await callback.message.edit_text(response_text)

        # Acknowledge the callback to stop the loading spinner on the button
        await callback.answer()

    except Exception as e:
        logger.error(f"Database error during callback: {e}")
        await callback.answer("❌ Error fetching game details.", show_alert=True)
    finally:
        db.close()


@dp.message(Command("games"))
async def games_handler(message: Message) -> None:
    """Handles the /games command."""
    db = SessionLocal()
    try:
        games = db.query(Game).limit(10).all()

        if not games:
            await message.answer("📭 The database is currently empty.")
            return

        response_text = "🎮 Tracked Games:\n\n"
        for game in games:
            response_text += f"🔹 {game.title.title()}\n"
        await message.answer(response_text)
    except Exception as e:
        logger.error(f"Database error: {e}")
        await message.answer("❌ Error connecting to the database.")
    finally:
        db.close()


async def main() -> None:
    """Main entry point for the Telegram bot."""
    logger.info("Starting PricesPleaseBot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
