import yfinance as yf
import pandas as pd
import ta
import asyncio
from sentiment import SentimentAnalyzer
from market_sentiment import MarketSentimentAnalyzer

class StockAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.market_sentiment_analyzer = MarketSentimentAnalyzer()
        # List of major Canadian (TSX) and US (NASDAQ/NYSE) stocks to monitor
        self.tickers = [
            # Canadian (TSX)
            "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNR.TO", 
            "BNS.TO", "BMO.TO", "CP.TO", "SU.TO", "TRP.TO",
            "CM.TO", "CNQ.TO", "ATD.TO", "BCE.TO", "T.TO",
            
            # US - Big Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX",
            
            # US - AI & Robotics
            "NVDA",   # AI chips leader
            "TSLA",   # Robotics (Tesla Bot) + EVs
            "PLTR",   # AI software (Palantir)
            "AI",     # C3.ai (enterprise AI)
            "PATH",   # UiPath (robotic process automation)
            "UPST",   # Upstart (AI lending)
            
            # US - Semiconductors/Chips
            "AMD",    # AI/gaming chips
            "INTC",   # Intel
            "AVGO",   # Broadcom (AI chips)
            "QCOM",   # Qualcomm (mobile chips)
            "MU",     # Micron (memory chips)
            "AMAT",   # Applied Materials (chip equipment)
            "LRCX",   # Lam Research (chip equipment)
            "ASML",   # ASML (chip lithography - critical for advanced chips)
            
            # US - AR/VR Glasses & Metaverse
            "SNAP",   # Snapchat (AR glasses - Spectacles)
            "AAPL",   # Apple Vision Pro (already in list)
            "META",   # Meta Quest VR (already in list)
            
            # US - Rare Earth Metals & Mining
            "MP",     # MP Materials (rare earth mining - US-based)
            "LAC",    # Lithium Americas (lithium for batteries)
            "ALB",    # Albemarle (lithium leader)
            "SQM",    # Sociedad Química y Minera (lithium)
            "VALE",   # Vale (diversified mining, rare earths)
            
            # US - High Growth / Small Cap (Potential 5x-10x Gems)
            "RKLB",   # Rocket Lab (Space/Satellite launch - "The next SpaceX")
            "ASTS",   # AST SpaceMobile (5G from space - huge potential)
            "IONQ",   # IonQ (Quantum Computing leader)
            "SOFI",   # SoFi Technologies (Fintech/Banking growth)
            "PLUG",   # Plug Power (Hydrogen energy)
            "LCID",   # Lucid Group (EVs - risky but high reward)
            "JOBY",   # Joby Aviation (Flying taxis/eVTOL)
            
            # US - Finance & Consumer (keeping some for diversification)
            "JPM", "V", "WMT", "PG", "DIS",
            "COIN", "GME", "AMC", "HOOD",
            "UBER", "ABNB", "PYPL", "RBLX"
        ]

    async def get_top_picks(self):
        # Get market sentiment first
        market_sentiment, market_headlines = await self.market_sentiment_analyzer.get_market_sentiment()
        
        # 🚀 OPTIMIZATION: Fetch ALL history in one single request
        # This is 10x faster than looping through tickers
        try:
            data = await asyncio.to_thread(
                yf.download, 
                tickers=self.tickers, 
                period="6mo", 
                group_by='ticker', 
                threads=True,
                progress=False
            )
        except Exception as e:
            print(f"Bulk download failed: {e}")
            return []

        tasks = []
        for ticker in self.tickers:
            # Extract single stock history from the bulk dataframe
            try:
                hist = data[ticker]
                if hist.empty:
                    continue
                # Pass pre-fetched history to analyze_stock
                tasks.append(self.analyze_stock(ticker, market_sentiment, hist))
            except KeyError:
                continue
                
        results = await asyncio.gather(*tasks)
        
        # Filter for "Buy" or "Strong Buy" and sort by confidence
        recommendations = [
            r for r in results 
            if r["recommendation"] in ["Buy", "Strong Buy"]
        ]
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        # Add market mood to all recommendations
        mood_label, mood_icon = self.market_sentiment_analyzer.get_market_mood_label(market_sentiment)
        for rec in recommendations:
            rec["market_mood"] = {
                "sentiment": round(market_sentiment, 2),
                "label": mood_label,
                "icon": mood_icon,
                "headlines": market_headlines[:3]
            }
        
        return recommendations  # Return all recommendations

    async def analyze_stock(self, ticker, market_sentiment=0.0, hist=None):
        # Fetch data if not provided (fallback)
        try:
            stock = yf.Ticker(ticker)
            if hist is None:
                hist = stock.history(period="6mo")
            
            if hist.empty:
                return self._empty_response(ticker)

            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_percent = ((current_price - prev_close) / prev_close) * 100

            # Technical Analysis
            rsi = ta.momentum.RSIIndicator(hist["Close"]).rsi().iloc[-1]
            macd = ta.trend.MACD(hist["Close"]).macd_diff().iloc[-1]
            sma_50 = ta.trend.SMAIndicator(hist["Close"], window=50).sma_indicator().iloc[-1]
            
            technical_score = 0
            reasons = []

            # RSI Logic (More granular)
            if rsi < 30:
                technical_score += 30
                reasons.append(f"RSI is oversold ({rsi:.1f})")
            elif rsi < 45:
                technical_score += 15
                reasons.append(f"RSI is low ({rsi:.1f})")
            elif rsi > 70:
                technical_score -= 30
                reasons.append(f"RSI is overbought ({rsi:.1f})")
            elif rsi > 55:
                technical_score -= 15
                reasons.append(f"RSI is high ({rsi:.1f})")
            else:
                reasons.append(f"RSI is neutral ({rsi:.1f})")

            # MACD Logic
            if macd > 0:
                technical_score += 20
                reasons.append("MACD is positive")
            else:
                technical_score -= 20
                reasons.append("MACD is negative")

            # Trend Logic (SMA 50)
            if current_price > sma_50:
                technical_score += 10
                reasons.append("Price above 50-day SMA (Uptrend)")
            else:
                technical_score -= 10
                reasons.append("Price below 50-day SMA (Downtrend)")

            # Sentiment Analysis
            sentiment_score, news_summary = await self.sentiment_analyzer.analyze(ticker)
            reasons.extend(news_summary)

            # Fundamental Analysis
            fundamental_score = 0
            try:
                # Fetch fundamentals with a 10‑second timeout to avoid hanging on slow tickers
                async def _fetch_info(ticker_obj):
                    import asyncio
                    return await asyncio.wait_for(
                        asyncio.to_thread(lambda: ticker_obj.info),
                        timeout=10,
                    )
                info = await _fetch_info(stock)

                # P/E Ratio Analysis
                pe_ratio = info.get('trailingPE', None)
                if pe_ratio:
                    if pe_ratio < 15:
                        fundamental_score += 15
                        reasons.append(f"P/E ratio {pe_ratio:.1f} (Undervalued)")
                    elif pe_ratio < 25:
                        fundamental_score += 10
                        reasons.append(f"P/E ratio {pe_ratio:.1f} (Fair value)")
                    elif pe_ratio < 40:
                        fundamental_score += 5
                        reasons.append(f"P/E ratio {pe_ratio:.1f} (Slightly expensive)")
                    else:
                        reasons.append(f"P/E ratio {pe_ratio:.1f} (Overvalued)")
                else:
                    fundamental_score -= 10
                    reasons.append("⚠️ No P/E ratio (Unprofitable)")

                # Earnings Growth Analysis
                earnings_growth = info.get('earningsGrowth', None)
                if earnings_growth:
                    if earnings_growth > 0.20:
                        fundamental_score += 10
                        reasons.append(f"Earnings growth {earnings_growth*100:.1f}% (Strong)")
                    elif earnings_growth > 0.10:
                        fundamental_score += 5
                        reasons.append(f"Earnings growth {earnings_growth*100:.1f}% (Good)")
                    elif earnings_growth < 0:
                        fundamental_score -= 10
                        reasons.append(f"⚠️ Earnings declining {earnings_growth*100:.1f}%")

                # Revenue Growth Analysis
                revenue_growth = info.get('revenueGrowth', None)
                if revenue_growth:
                    if revenue_growth > 0.15:
                        fundamental_score += 5
                    elif revenue_growth > 0.05:
                        fundamental_score += 3

                # Profit Margin Analysis
                profit_margin = info.get('profitMargins', None)
                if profit_margin:
                    if profit_margin > 0.20:
                        fundamental_score += 5
                        reasons.append(f"Profit margin {profit_margin*100:.1f}% (Very profitable)")
                    elif profit_margin > 0.10:
                        fundamental_score += 3
                    elif profit_margin < 0:
                        fundamental_score -= 5
                        reasons.append(f"⚠️ Losing money (margin {profit_margin*100:.1f}%)")
            except Exception as e:
                print(f"Error fetching fundamentals for {ticker}: {e}")
                reasons.append("Fundamental data unavailable")

            # Combine Scores (50% technical, 30% sentiment, 20% fundamental)
            # Technical Range: -60 to +60 (RSI 30 + MACD 20 + SMA 10)
            # Sentiment Range: -20 to +20
            # Fundamental Range: -25 to +40 (P/E 15 + Earnings 10 + Revenue 5 + Margin 5 + penalties)
            
            # Normalize scores to 0-100 scale
            technical_normalized = ((technical_score + 60) / 120) * 100  # -60 to +60 → 0 to 100
            sentiment_normalized = ((sentiment_score + 1) / 2) * 100  # -1 to +1 → 0 to 100
            fundamental_normalized = ((fundamental_score + 25) / 65) * 100  # -25 to +40 → 0 to 100
            
            # Apply weights: 50% technical, 30% sentiment, 20% fundamental
            total_score = (technical_normalized * 0.5) + (sentiment_normalized * 0.3) + (fundamental_normalized * 0.2)
            
            # Adjust for market sentiment
            # If market is negative, reduce all scores slightly
            # If market is positive, boost all scores slightly
            market_adjustment = market_sentiment * 10  # -10 to +10 adjustment
            total_score += market_adjustment
            
            if market_sentiment < -0.2:
                reasons.append(f"⚠️ Market sentiment is negative ({market_sentiment:.2f})")
            elif market_sentiment > 0.2:
                reasons.append(f"✅ Market sentiment is positive ({market_sentiment:.2f})")
            
            # Cap score
            total_score = max(0, min(100, total_score))

            recommendation = "Hold"
            if total_score >= 85: # Increased threshold
                recommendation = "Strong Buy"
            elif total_score >= 65:
                recommendation = "Buy"
            elif total_score <= 25: # Increased threshold
                recommendation = "Strong Sell"
            elif total_score <= 45:
                recommendation = "Sell"

            return {
                "ticker": ticker,
                "price": round(current_price, 2),
                "change_percent": round(change_percent, 2),
                "recommendation": recommendation,
                "confidence_score": round(total_score, 1),
                "reasoning": reasons,
                "sentiment_score": round(sentiment_score, 2),
                "technical_score": round(technical_score, 2),
                "fundamental_score": round(fundamental_score, 2)
            }

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return self._empty_response(ticker)

    def _empty_response(self, ticker):
        return {
            "ticker": ticker,
            "price": 0.0,
            "change_percent": 0.0,
            "recommendation": "Neutral",
            "confidence_score": 0.0,
            "reasoning": ["Insufficient data"],
            "sentiment_score": 0.0,
            "technical_score": 0.0,
            "fundamental_score": 0.0
        }
