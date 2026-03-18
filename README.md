# Personalized Finance Chatbot

A comprehensive, intelligent financial assistant built with **FastAPI**, **MongoDB**, and **Large Language Models (LLMs)**. The chatbot provides personalized financial advice, real-time market data, and goal tracking using Retrieval-Augmented Generation (RAG) and structured financial calculators.

## Features

- **Conversational Financial AI**: Natural language interactions powered by LLMs (integrates with Google Gemini / OpenAI).
- **RAG-based Knowledge Retrieval**: Uses FAISS and sentence-transformers to fetch accurate financial context from local documents (e.g., rules on emergency funds, mutual funds, etc.).
- **Real-Time Market Data**: Fetches live stock prices, Fixed Deposit rates, and Mutual Fund NAVs using `yfinance` and web scraping.
- **Personalized Risk Profiling**: Tailors advice based on the user's age, income, savings, and risk appetite.
- **Intent Classification**: Automatically routes queries to calculators, real-time fetchers, or educational RAG pipelines.
- **Financial Calculators**: Built-in math parsing for answering quantitative financial questions directly.
- **Goal Tracking System**: Dedicated endpoints to create, track, and save towards personal financial goals (stored in MongoDB).
- **Safety & Fallback Mechanisms**: Validates queries for safety and gracefully handles unsupported or off-topic questions.

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: MongoDB (PyMongo)
- **AI & NLP**: `google-generativeai`, `openai`, `sentence-transformers`, `faiss-cpu`
- **Data Fetching**: `yfinance`, `alpha_vantage`, `BeautifulSoup`
- **Other**: Pydantic, Uvicorn, Python-dotenv

## Project Structure

- `src/app.py`: Main FastAPI application, routing, and endpoints.
- `src/llm.py`: LLM integration and prompting logic.
- `src/retriever.py`: FAISS-based document retrieval.
- `src/realtime.py`: Live data fetchers for stocks and MFs.
- `src/profiling.py`: Logic to calculate user risk profiles.
- `src/intent_classifier.py`: Intent routing logic.
- `src/calculator.py`: Financial math parsing.
- `frontend/`: Contains the user interface for the application.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Finance_bot
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   # Add other relevant keys if necessary
   ```

5. **Start MongoDB**:
   Ensure you have MongoDB running locally on `mongodb://localhost:27017`.

## Running the Application

Start the FastAPI development server:

```bash
uvicorn src.app:app --reload
```

The API will be available at `http://127.0.0.1:8000`. 
API Documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

## Key Endpoints

- `POST /chat`: Main chat endpoint. Accepts a query and optional user profile to return personalized financial answers.
- `POST /goal`: Create a new financial goal for a user.
- `POST /goal/save`: Save progress (amount) towards a specific goal.
- `GET /goal/{user}`: Retrieve all active goals for a given user.

## License

This project is licensed under the MIT License.
