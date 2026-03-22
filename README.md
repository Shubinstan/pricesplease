# ⚙️ GamePulse: Data Ingestion & ETL Pipeline 

GamePulse is an asynchronous, fault-tolerant ETL (Extract, Transform, Load) pipeline built with Python. It is designed to extract, normalize, and store volatile pricing data from heavily protected digital storefronts (Steam, Epic Games Store). 

While it currently features a Telegram Bot as its primary user interface, the core architecture is built around robust data engineering principles, making the normalized dataset perfectly structured for future LLM integrations or RAG (Retrieval-Augmented Generation) pipelines.

## ✨ Core Architecture & Features

* **Concurrent Data Extraction:** Leverages `asyncio.gather` to execute parallel scraping tasks across multiple targets simultaneously, significantly reducing data ingestion latency.
* **Advanced Anti-Bot Evasion:** Uses `Playwright` to render JavaScript-heavy DOMs. Implements dynamic User-Agent spoofing to bypass Cloudflare/Epic Games protections and injects custom authentication cookies to bypass Steam's age-gate barriers.
* **Real-Time Data Normalization:** The transformation layer automatically detects varying local currencies (RON, EUR, UAH), sanitizes messy text using RegEx, and converts values to a unified USD format on the fly.
* **RAG-Ready Data Storage:** Cleaned and structured data is loaded into a relational database (PostgreSQL/SQLite) via `SQLAlchemy`. Custom indexes are utilized to ensure sub-second query responses.
* **Decoupled Bot Interface:** A Telegram interface built with `aiogram` 3.x acts as the frontend, querying the normalized database to provide users with instant, interactive UI responses via Inline Keyboards.

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Data Extraction:** Playwright (Async API)
* **Concurrency:** asyncio
* **Database & ORM:** PostgreSQL / SQLite, SQLAlchemy
* **Interface Layer:** aiogram 3.x

## 🚀 Installation & Setup

Clone the repository:
```bash
git clone [https://github.com/yourusername/gamepulse.git](https://github.com/yourusername/gamepulse.git)
cd gamepulse
