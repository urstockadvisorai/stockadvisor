from textblob import TextBlob
import yfinance as yf
import asyncio

class SentimentAnalyzer:
    async def analyze(self, ticker):
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, ticker)

    def _analyze_sync(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return 0.0, ["No recent news found"]

            total_polarity = 0
            count = 0
            headlines = []

            for item in news[:5]: # Analyze top 5 news items
                title = item.get('title', '')
                if title:
                    blob = TextBlob(title)
                    polarity = blob.sentiment.polarity
                    total_polarity += polarity
                    count += 1
                    headlines.append(f"News: {title} (Sentiment: {polarity:.2f})")

            avg_polarity = total_polarity / count if count > 0 else 0
            
            # Normalize polarity to be more impactful? 
            # TextBlob polarity is -1 to 1.
            
            return avg_polarity, headlines[:2] # Return score and top 2 headlines

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return 0.0, ["Error fetching news"]
