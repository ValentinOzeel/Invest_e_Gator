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

## 2. Design the database schema

1. Create a SQLite database to store scraped news articles and derived metrics
2. Design tables for:
   - Stocks (ticker symbol, company name)
   - News articles (title, content, publication date, source URL)
   - Sentiment analysis (article ID, sentiment score, key metrics)
   - Derived metrics (stock symbol, metric name, value, date)

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
   - Summarize article content
   - Extract key information (sentiment, mentioned companies, financial metrics)
4. Derivative metric calculations:
   - Calculate sentiment over time
   - Analyze news frequency
   - Generate word clouds
5. Visualization tools:
   - Create sentiment trend charts
   - Plot news frequency graphs
   - Generate word cloud images

## 4. Develop the sub-agents

Create specialized sub-agents for different tasks:

1. `NewsScraperAgent`:
   - Responsible for scraping news from specified URLs
   - Uses AIToolkit for web scraping and database operations
2. `NLPAgent`:
   - Processes scraped news using the local Llama 3.1 8b model
   - Uses AIToolkit for NLP methods and database operations
3. `MetricsAgent`:
   - Calculates derivative metrics based on processed news data
   - Uses AIToolkit for metric calculations and database operations
4. `ReportingAgent`:
   - Generates reports and visualizations
   - Uses AIToolkit for visualization tools and database operations

## 5. Implement the main orchestrator agent

Create a `MainOrchestrator` class that:

1. Maintains a list of stock symbols to monitor
2. Coordinates the activities of sub-agents
3. Implements a scheduling system using `apscheduler`
4. Provides a command-line interface for user interactions

## 6. Set up the Llama 3.1 8b model

1. Download and set up the Llama 3.1 8b model locally
2. Create a custom system prompt for financial news analysis
3. Implement a method in AIToolkit to interact with the model

## 7. Implement the main workflow

In the `MainOrchestrator` class, implement the main workflow:

1. Fetch list of stocks to monitor
2. For each stock:
   - Generate appropriate URL
   - Use `NewsScraperAgent` to fetch and store new articles
   - Use `NLPAgent` to process new articles with Llama 3.1 8b
   - Use `MetricsAgent` to calculate derivative metrics
3. Use `ReportingAgent` to generate reports and visualizations

## 8. Develop the user interface

Implement a command-line interface in the `MainOrchestrator` class for:

1. Adding/removing stocks to monitor
2. Manually triggering scraping runs
3. Generating and displaying reports
4. Visualizing trends and metrics

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