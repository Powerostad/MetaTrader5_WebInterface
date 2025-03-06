import MetaTrader5 as mt5
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mt5_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mt5_api")


class MetaTraderSingleton:
    """
    Singleton class for MetaTrader 5 connection management.
    Ensures only one connection exists throughout the application.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new MetaTraderSingleton instance")
            cls._instance = super(MetaTraderSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not MetaTraderSingleton._initialized:
            logger.info("Initializing MetaTraderSingleton")
            self.connected = False
            self.authorized = False
            self._initialize_mt5()
            MetaTraderSingleton._initialized = True

    def _initialize_mt5(self) -> bool:
        """Initialize the MetaTrader 5 terminal."""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"Failed to initialize MT5: {error}")
                return False
            logger.info("MetaTrader 5 initialized successfully")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Exception during MT5 initialization: {str(e)}")
            return False

    def login(self, account_id: int = None, password: str = None, server: str = None) -> bool:
        """Login to a MetaTrader account."""
        try:
            if not self.connected:
                if not self._initialize_mt5():
                    return False

            # Attempt login
            if account_id and password and server:
                self.authorized = mt5.login(account_id, password=password, server=server)
            else:
                self.authorized = mt5.login()
            if not self.authorized:
                error = mt5.last_error()
                logger.error(f"Login failed: {error}")
                return False

            logger.info(f"Logged in successfully to account {account_id} on server {server}")
            return True
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}")
            return False

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Retrieve account information."""
        if not self._check_connection():
            return None

        try:
            account_info = mt5.account_info()
            if account_info is None:
                error = mt5.last_error()
                logger.error(f"Failed to retrieve account info: {error}")
                return None

            # Convert named tuple to dictionary
            return account_info._asdict()
        except Exception as e:
            logger.error(f"Exception retrieving account info: {str(e)}")
            return None

    def buy(self, symbol: str, volume: float, price: Optional[float] = None,
            deviation: int = 20, stop_loss: Optional[float] = None,
            take_profit: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Place a buy order."""
        if not self._check_connection():
            return None

        try:
            if price is None:
                price = mt5.symbol_info_tick(symbol).ask

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": deviation,
                "magic": 0,
                "comment": "Buy order via API",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add optional stop loss and take profit if provided
            if stop_loss is not None:
                request["sl"] = stop_loss
            if take_profit is not None:
                request["tp"] = take_profit

            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Buy order failed: {result}")
                return {"success": False, "error": f"Code: {result.retcode}", "result": result._asdict()}

            logger.info(f"Buy order successful: {symbol}, volume: {volume}")
            return {"success": True, "result": result._asdict()}
        except Exception as e:
            logger.error(f"Exception placing buy order: {str(e)}")
            return {"success": False, "error": str(e)}

    def sell(self, symbol: str, volume: float, price: Optional[float] = None,
             deviation: int = 20, stop_loss: Optional[float] = None,
             take_profit: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Place a sell order."""
        if not self._check_connection():
            return None

        try:
            if price is None:
                price = mt5.symbol_info_tick(symbol).bid

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": deviation,
                "magic": 0,
                "comment": "Sell order via API",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add optional stop loss and take profit if provided
            if stop_loss is not None:
                request["sl"] = stop_loss
            if take_profit is not None:
                request["tp"] = take_profit

            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Sell order failed: {result}")
                return {"success": False, "error": f"Code: {result.retcode}", "result": result._asdict()}

            logger.info(f"Sell order successful: {symbol}, volume: {volume}")
            return {"success": True, "result": result._asdict()}
        except Exception as e:
            logger.error(f"Exception placing sell order: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_positions(self) -> Optional[Dict[str, Any]]:
        """Get all open positions."""
        if not self._check_connection():
            return None

        try:
            positions = mt5.positions_get()
            if positions is None:
                error = mt5.last_error()
                logger.error(f"Failed to get positions: {error}")
                return {"success": False, "error": str(error)}

            # Convert positions to dictionaries
            positions_list = [position._asdict() for position in positions]
            return {"success": True, "positions": positions_list}
        except Exception as e:
            logger.error(f"Exception getting positions: {str(e)}")
            return {"success": False, "error": str(e)}

    def close_position(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Close a specific position by ticket."""
        if not self._check_connection():
            return None

        try:
            # Get position details
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return {"success": False, "error": f"Position with ticket {ticket} not found"}

            position = position[0]

            # Determine action based on position type
            if position.type == mt5.POSITION_TYPE_BUY:
                deal_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                deal_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask

            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": deal_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": 0,
                "comment": "Close position via API",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order to close position
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close position: {result}")
                return {"success": False, "error": f"Code: {result.retcode}", "result": result._asdict()}

            logger.info(f"Position {ticket} closed successfully")
            return {"success": True, "result": result._asdict()}
        except Exception as e:
            logger.error(f"Exception closing position: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a symbol."""
        if not self._check_connection():
            return None

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                error = mt5.last_error()
                logger.error(f"Failed to get symbol info for {symbol}: {error}")
                return {"success": False, "error": str(error)}

            return {"success": True, "info": symbol_info._asdict()}
        except Exception as e:
            logger.error(f"Exception getting symbol info: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_historical_data(self, symbol: str, timeframe: str, from_date, to_date=None, count=None) -> Optional[
        Dict[str, Any]]:
        """Get historical price data for a symbol."""
        if not self._check_connection():
            return None

        # Map string timeframe to MT5 constants
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1,
            "MN1": mt5.TIMEFRAME_MN1
        }

        if timeframe not in timeframe_map:
            return {"success": False, "error": f"Invalid timeframe: {timeframe}"}

        try:
            # Get historical data
            rates = mt5.copy_rates_range(symbol, timeframe_map[timeframe], from_date, to_date if to_date else from_date)
            if rates is None or len(rates) == 0:
                error = mt5.last_error()
                logger.error(f"Failed to get historical data: {error}")
                return {"success": False, "error": str(error)}

            # Convert rates to dictionaries
            rates_list = [{"time": rate[0], "open": rate[1], "high": rate[2],
                           "low": rate[3], "close": rate[4], "tick_volume": rate[5],
                           "spread": rate[6], "real_volume": rate[7]} for rate in rates]

            return {"success": True, "data": rates_list}
        except Exception as e:
            logger.error(f"Exception getting historical data: {str(e)}")
            return {"success": False, "error": str(e)}

    def _check_connection(self) -> bool:
        """Check if MT5 is connected and initialized."""
        if not self.connected:
            logger.error("MetaTrader 5 is not initialized")
            return False

        if not self.authorized:
            logger.error("Not logged into MetaTrader 5 account")
            return False

        return True

    def disconnect(self) -> bool:
        """Disconnect from MetaTrader 5."""
        try:
            mt5.shutdown()
            logger.info("Disconnected from MetaTrader 5")
            self.connected = False
            self.authorized = False
            return True
        except Exception as e:
            logger.error(f"Exception during disconnect: {str(e)}")
            return False


# For testing
if __name__ == "__main__":
    # Test singleton pattern
    mt = MetaTraderSingleton()
    mt2 = MetaTraderSingleton()
    print(f"Singleton instances are the same: {mt is mt2}")

    # Test login
    success = mt.login(account_id=12345678, password="your_password", server="your_server")
    print(f"Login success: {success}")

    if success:
        # Test getting account info
        account_info = mt.get_account_info()
        print(f"Account info: {account_info}")

        # Test disconnecting
        mt.disconnect()