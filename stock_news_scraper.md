# Stock News Scraper AI Agent System

This document outlines the steps to create an AI agent system that can browse specific URLs, scrape financial news data, and present it in a specific format, using a main orchestrator and sub-agents.

## 1. Set up the development environment

1. Create a new Python virtual environment
2. Install required libraries:
   - `requests` for making HTTP requests
   - `beautifulsoup4` for parsing HTML
   - `pandas` for data manipulation
   - `sqlalchemy` for database operations
   - `llama-cpp-python` for running the local Llama 3.1 8b model
   - `apscheduler` for scheduling tasks
3. Set up git version control

## 2. Design the database schema

1. Use SQLAlchemy ORM to define the database schema:
-  Create a models.py file with the following tables:

    Stocks (id, ticker_symbol, company_name)
    NewsArticles (id, title, content, publication_date, source_url, stock_id)
    SentimentAnalysis (id, article_id, sentiment_score, key_metrics)
    DerivedMetrics (id, stock_id, metric_name, value, date)

-  Implement relationships between tables (e.g., one-to-many between Stocks and NewsArticles)
2. Use Alembic for database migrations

## 3. Implement the AIToolkit class

Create an `AIToolkit` class that contains all the tools needed by the AI agents:

1. Web scraping methods:
   - Fetch HTML content from a given URL
   - Parse HTML using BeautifulSoup
   - Extract relevant information (headline, news content, date, source)
2. Database operations:
   - Insert new articles
   - Retrieve existing articles
   - Update derived metrics
3. NLP methods using locally hosted Llama 3.1 8b:
   - Use llama-cpp-python to load the Llama 3.1 8b model 
   - Implement custom prompts for financial news analysis
   - Use batching for efficient processing of multiple articles
   - Summarize article content
   - Extract key information (sentiment, mentioned companies, financial metrics)
4. Derivative metric calculations:
   - Implement moving averages for sentiment trends
   - Analyze news frequency
   - Use TF-IDF for keyword extraction
5. Visualization tools:
   - Use Matplotlib for generating charts; Implement Plotly for interactive visualizations
   - Create sentiment trend charts
   - Plot news frequency graphs
   - Generate word cloud images with WordCloud 

## 4. Develop the sub-agents

Create specialized sub-agents for different tasks:

1. `NewsScraperAgent`:
   - Implement URL generation based on stock symbols
   - Use asyncio for concurrent scraping of multiple sources
   - Implement rate limiting and respect robots.txt
   - Responsible for scraping news from specified URLs
   - Uses AIToolkit for web scraping and database operations
2. `NLPAgent`:
   - Use threading for parallel processing of articles
   - Use a queue system for managing NLP tasks
   - Implement batching for efficient use of the Llama model
   - Processes scraped news using the local Llama 3.1 8b model
   - Uses AIToolkit for NLP methods and database operations
3. `MetricsAgent`:
   - Calculates derivative metrics based on processed news data
   - Implement real-time metric updates
   - Uses AIToolkit for metric calculations and database operations
4. `ReportingAgent`:
   - Use Jinja2 templates for report generation
   - Implement asynchronous report generation
   - Generates reports and visualizations
   - Uses AIToolkit for visualization tools and database operations

## 5. Implement the main orchestrator agent

Create a `MainOrchestrator` class that:

1. Create an orchestrator.py file with the MainOrchestrator class:
   - Use the Observer pattern for coordinating sub-agents
   - Implement a state machine for managing the overall workflow
   - Use asyncio for managing concurrent tasks
2. Implement scheduling using APScheduler:
   - Use BackgroundScheduler for running tasks
   - Implement custom job stores for persistence
3. Develop a RESTful API using FastAPI:
   - Implement endpoints for adding/removing stocks
   - Create endpoints for triggering scraping runs
   - Develop endpoints for retrieving reports and visualizations

## 6. Set up the Llama 3.1 8b model

1. Download and set up the Llama 3.1 8b model locally
2. Create a custom system prompt for financial news analysis
3. Implement a method in AIToolkit to interact with the model:
   - Use context management for efficient resource handling
   - Implement temperature and top-p sampling for diverse outputs
   - Use logging to track model interactions and performance


## 7. Implement the main workflow

In the `MainOrchestrator` class, implement the main workflow:

1. Fetch list of stocks to monitor
2. For each stock:
   - Generate appropriate URL
   - Use `NewsScraperAgent` to fetch and store new articles
   - Use `NLPAgent` to process new articles with Llama 3.1 8b
   - Use `MetricsAgent` to calculate derivative metrics
3. Use `ReportingAgent` to generate reports and visualizations

Use asyncio.gather for concurrent execution of sub-agent tasks
Implement error handling and retries for each step
Use a message queue (e.g., RabbitMQ) for task distribution

Implement data validation at each step:
   - Use Pydantic models for data validation
   - Implement custom validators for financial data

Develop a caching layer for intermediate results:
   - Use Redis for caching frequently accessed data
   - Implement TTL (Time To Live) for cached items

## 8. Develop the user interface

Implement a command-line interface in the `MainOrchestrator` class for:

1. Adding/removing stocks to monitor
2. Manually triggering scraping runs
3. Generating and displaying reports
4. Visualizing trends and metrics

OR

Build an actual application using Dash or Gradio/Streamlit/Taipy

## 9. Ensure ethical and legal compliance

1. Implement rate limiting in the `NewsScraperAgent`
2. Respect robots.txt files and website terms of service
3. Implement data retention policies in the database operations

## 10. Test and refine

1. Develop unit tests for each sub-agent and the AIToolkit
2. Perform integration testing of the entire system
3. Conduct thorough testing with various stock symbols and news sources
4. Refine the system based on test results and real-world performance

## 11. Document and deploy

1. Write comprehensive documentation for the project
2. Set up a deployment pipeline (e.g., using Docker for containerization)
3. Consider local deployment options for running the Llama 3.1 8b model

By following these steps, you'll create a robust AI agent system capable of scraping, analyzing, and reporting on financial news for specific stocks, using a main orchestrator and specialized sub-agents, with local NLP processing using Llama 3.1 8b.