# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import os
import logging
from .mt5_singleton import MetaTraderSingleton

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fastapi_app")

# API security
API_KEY = os.environ.get("MT5_API_KEY", "your-api-key-here")  # Set this via environment variable in production
api_key_header = APIKeyHeader(name="X-API-Key")

# Create FastAPI app
app = FastAPI(
    title="MetaTrader 5 API",
    description="REST API for interacting with MetaTrader 5",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


mt5_instance = MetaTraderSingleton()


class LoginRequest(BaseModel):
    account_id: int
    password: str
    server: str


class OrderRequest(BaseModel):
    symbol: str
    volume: float
    price: Optional[float] = None
    deviation: int = 20
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class ClosePositionRequest(BaseModel):
    ticket: int


class HistoricalDataRequest(BaseModel):
    symbol: str
    timeframe: str
    from_date: datetime.datetime
    to_date: Optional[datetime.datetime] = None
    count: Optional[int] = None


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


@app.post("/login", response_model=ApiResponse)
async def login(request: LoginRequest, api_key: str = Depends(verify_api_key)):
    """Login to MetaTrader 5 account."""
    logger.info(f"Login attempt for account {request.account_id} on server {request.server}")

    success = mt5_instance.login(
        account_id=request.account_id,
        password=request.password,
        server=request.server
    )

    if success:
        return {"success": True, "data": {"message": "Login successful"}}
    else:
        return {"success": False, "error": "Login failed"}


@app.get("/account", response_model=ApiResponse)
async def get_account_info(api_key: str = Depends(verify_api_key)):
    """Get account information."""
    logger.info("Getting account information")

    account_info = mt5_instance.get_account_info()
    if account_info:
        return {"success": True, "data": account_info}
    else:
        return {"success": False, "error": "Failed to retrieve account information"}


@app.post("/order/buy", response_model=ApiResponse)
async def buy_order(request: OrderRequest, api_key: str = Depends(verify_api_key)):
    """Place a buy order."""
    logger.info(f"Buy order request for {request.symbol}, volume: {request.volume}")

    result = mt5_instance.buy(
        symbol=request.symbol,
        volume=request.volume,
        price=request.price,
        deviation=request.deviation,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit
    )

    if result and result.get("success", False):
        return {"success": True, "data": result.get("result", {})}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.post("/order/sell", response_model=ApiResponse)
async def sell_order(request: OrderRequest, api_key: str = Depends(verify_api_key)):
    """Place a sell order."""
    logger.info(f"Sell order request for {request.symbol}, volume: {request.volume}")

    result = mt5_instance.sell(
        symbol=request.symbol,
        volume=request.volume,
        price=request.price,
        deviation=request.deviation,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit
    )

    if result and result.get("success", False):
        return {"success": True, "data": result.get("result", {})}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.get("/positions", response_model=ApiResponse)
async def get_positions(api_key: str = Depends(verify_api_key)):
    """Get all open positions."""
    logger.info("Getting open positions")

    result = mt5_instance.get_positions()
    if result and result.get("success", False):
        return {"success": True, "data": {"positions": result.get("positions", [])}}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.post("/position/close", response_model=ApiResponse)
async def close_position(request: ClosePositionRequest, api_key: str = Depends(verify_api_key)):
    """Close a specific position by ticket."""
    logger.info(f"Close position request for ticket: {request.ticket}")

    result = mt5_instance.close_position(request.ticket)
    if result and result.get("success", False):
        return {"success": True, "data": result.get("result", {})}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.get("/symbol/{symbol}", response_model=ApiResponse)
async def get_symbol_info(symbol: str, api_key: str = Depends(verify_api_key)):
    """Get detailed information about a symbol."""
    logger.info(f"Getting symbol info for: {symbol}")

    result = mt5_instance.get_symbol_info(symbol)
    if result and result.get("success", False):
        return {"success": True, "data": result.get("info", {})}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.post("/historical-data", response_model=ApiResponse)
async def get_historical_data(request: HistoricalDataRequest, api_key: str = Depends(verify_api_key)):
    """Get historical price data for a symbol."""
    logger.info(f"Getting historical data for {request.symbol}, timeframe: {request.timeframe}")

    result = mt5_instance.get_historical_data(
        symbol=request.symbol,
        timeframe=request.timeframe,
        from_date=request.from_date,
        to_date=request.to_date,
        count=request.count
    )

    if result and result.get("success", False):
        return {"success": True, "data": {"rates": result.get("data", [])}}
    else:
        error_msg = result.get("error") if result else "Unknown error"
        return {"success": False, "error": error_msg}


@app.post("/disconnect", response_model=ApiResponse)
async def disconnect(api_key: str = Depends(verify_api_key)):
    """Disconnect from MetaTrader 5."""
    logger.info("Disconnect request")

    success = mt5_instance.disconnect()
    if success:
        return {"success": True, "data": {"message": "Disconnected successfully"}}
    else:
        return {"success": False, "error": "Failed to disconnect"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)