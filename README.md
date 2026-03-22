# 🎮 GamePulse Bot (Prices, Please!)

GamePulse is an asynchronous Telegram bot built with Python that acts as a real-time video game price aggregator. It scrapes, normalizes, and tracks game prices across major digital storefronts like Steam and Epic Games Store, delivering the best deals directly to your Telegram chat.

## ✨ Features

- **Cross-Platform Aggregation:** Searches for games on Steam and Epic Games Store simultaneously using asynchronous tasks (`asyncio.gather`), significantly reducing wait times.
- **Dynamic Web Scraping:** Utilizes `Playwright` to render JavaScript-heavy storefronts and extract accurate pricing data.
- **Advanced Bot-Protection Bypass:** Implements User-Agent spoofing to bypass Cloudflare/Epic Games protections and injects custom cookies to bypass Steam's 18+ age gates.
- **Real-Time Data Normalization:** Automatically detects local currencies (e.g., RON, EUR, UAH) and converts them to a unified currency (USD) on the fly before saving to the database.
- **Database Caching:** Stores search results and pricing history in a relational database using `SQLAlchemy` to provide instant responses for previously searched games.
- **Interactive UI:** Uses Telegram's Inline Keyboards for a seamless user experience.

## 🛠 Tech Stack

- **Language:** Python 3.10+
- **Bot Framework:** `aiogram` 3.x
- **Web Scraping:** `Playwright` (Async API)
- **Database:** PostgreSQL / SQLite (via `SQLAlchemy`)
- **Concurrency:** `asyncio`

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/gamepulse.git](https://github.com/yourusername/gamepulse.git)
   cd gamepulse
