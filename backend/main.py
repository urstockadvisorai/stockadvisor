from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from analyzer import StockAnalyzer
from email_notifier import EmailNotifier
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Stock Advisor API")

# Serve the built React UI (static files)
import os
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = StockAnalyzer()
email_notifier = EmailNotifier()

class MarketMood(BaseModel):
    sentiment: float
    label: str
    icon: str
    headlines: List[str]

class StockResponse(BaseModel):
    ticker: str
    price: float
    change_percent: float
    recommendation: str
    confidence_score: float
    reasoning: List[str]
    sentiment_score: float
    technical_score: float
    fundamental_score: float
    market_mood: Optional[MarketMood] = None

@app.get("/")
def read_root():
    return {"message": "Stock Advisor API is running"}

@app.get("/api/recommendations", response_model=List[StockResponse])
async def get_recommendations():
    """
    Get top stock recommendations based on technical and sentiment analysis.
    """
    try:
        recommendations = await analyzer.get_top_picks()
        # Send email notification for Strong Buy/Sell
        await email_notifier.send_alert(recommendations)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint to verify email configuration
@app.get("/api/test-email")
async def test_email_endpoint():
    """Send a dummy email to verify SMTP configuration."""
    dummy = [{
        "ticker": "TEST",
        "price": 1.23,
        "change_percent": 0.0,
        "recommendation": "Buy",
        "confidence_score": 70.0,
        "reasoning": ["Test email – buy signal"],
        "sentiment_score": 0.0,
        "technical_score": 0.0,
        "fundamental_score": 0.0,
    }]
    await email_notifier.send_alert(dummy)
    return {"status": "test email sent (if credentials are correct)"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
async def get_stock_detail(ticker: str):
    """
    Get detailed analysis for a specific stock.
    """
    try:
        analysis = await analyzer.analyze_stock(ticker)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
