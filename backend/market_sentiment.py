from newsapi import NewsApiClient
from textblob import TextBlob
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

load_dotenv()

class MarketSentimentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY", "")
        self.newsapi = NewsApiClient(api_key=self.api_key) if self.api_key else None
        self.cache = {
            "sentiment": 0.0,
            "headlines": [],
            "timestamp": None
        }
        self.cache_duration = 30 * 60  # 30 minutes in seconds

    async def get_market_sentiment(self):
        """Get overall market sentiment from news"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_market_sentiment_sync)

    def _get_market_sentiment_sync(self):
        """Synchronous version of market sentiment analysis"""
        # Check cache
        if self._is_cache_valid():
            return self.cache["sentiment"], self.cache["headlines"]

        if not self.newsapi:
            print("NewsAPI key not configured")
            return 0.0, ["NewsAPI not configured"]

        try:
            # Fetch top business and economic news from US sources
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Get top business headlines
            business_news = self.newsapi.get_top_headlines(
                category='business',
                country='us',
                language='en',
                page_size=20
            )

            # Get economic/political keywords + Central Bank announcements
            keywords_news = self.newsapi.get_everything(
                q='(Federal Reserve OR "Fed rate" OR "interest rate cut" OR "Bank of Canada" OR "BoC rate" OR "World Bank" OR inflation OR GDP OR unemployment OR stock market OR economy)',
                from_param=yesterday,
                language='en',
                sort_by='relevancy',
                page_size=15
            )

            # Get High-Impact "Robust" News (Trump, War, Tech CEOs)
            robust_news = self.newsapi.get_everything(
                q='(Trump OR "Civil War" OR "Ukraine War" OR "Gaza War" OR "Elon Musk" OR "Jensen Huang" OR "Mark Zuckerberg" OR "Sam Altman" OR "Tim Cook")',
                from_param=yesterday,
                language='en',
                sort_by='relevancy',
                page_size=10
            )

            # Combine articles
            all_articles = []
            if business_news.get('articles'):
                all_articles.extend(business_news['articles'])
            if keywords_news.get('articles'):
                all_articles.extend(keywords_news['articles'])
            if robust_news.get('articles'):
                all_articles.extend(robust_news['articles'])

            if not all_articles:
                return 0.0, ["No recent market news found"]

            # Analyze sentiment
            total_polarity = 0
            count = 0
            top_headlines = []

            for article in all_articles[:40]:  # Analyze top 40 to include robust news
                title = article.get('title', '')
                description = article.get('description', '')
                text = f"{title} {description}"
                
                if text.strip():
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity
                    total_polarity += polarity
                    count += 1
                    
                    # Store top 5 headlines
                    if len(top_headlines) < 5:
                        sentiment_label = "Positive" if polarity > 0.1 else "Negative" if polarity < -0.1 else "Neutral"
                        top_headlines.append(f"{title} ({sentiment_label})")

            avg_sentiment = total_polarity / count if count > 0 else 0.0

            # Update cache
            self.cache = {
                "sentiment": avg_sentiment,
                "headlines": top_headlines,
                "timestamp": datetime.now()
            }

            return avg_sentiment, top_headlines

        except Exception as e:
            print(f"Error fetching market news: {e}")
            return 0.0, [f"Error fetching market news: {str(e)[:50]}"]

    def _is_cache_valid(self):
        """Check if cache is still valid"""
        if not self.cache["timestamp"]:
            return False
        
        elapsed = (datetime.now() - self.cache["timestamp"]).total_seconds()
        return elapsed < self.cache_duration

    def get_market_mood_label(self, sentiment):
        """Convert sentiment score to human-readable label"""
        if sentiment > 0.15:
            return "Positive", "🟢"
        elif sentiment < -0.15:
            return "Negative", "🔴"
        else:
            return "Neutral", "🟡"
