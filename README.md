# MetaTrader 5 REST API

A FastAPI-based REST API for interacting with MetaTrader 5, designed with a singleton pattern to maintain a single connection to the MetaTrader 5 terminal.

## Features

- Connect to MetaTrader 5 account
- Get account information
- Place buy and sell orders
- Get open positions
- Close positions
- Get symbol information
- Get historical price data

## Requirements

- Python 3.9+
- MetaTrader 5 terminal installed
- FastAPI
- Uvicorn

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/metatrader-api.git
   cd metatrader-api
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and set your API key:
   ```
   cp .env.example .env
   # Edit .env file to set your API key
   ```

## Running the API

1. Start the MetaTrader 5 terminal

2. Start the API server:
   ```
   python run.py
   ```

3. The API is now available at http://localhost:8000

## API Endpoints

- **POST /login**: Login to MetaTrader 5 account
- **GET /account**: Get account information
- **POST /order/buy**: Place a buy order
- **POST /order/sell**: Place a sell order
- **GET /positions**: Get all open positions
- **POST /position/close**: Close a specific position
- **GET /symbol/{symbol}**: Get symbol information
- **POST /historical-data**: Get historical price data
- **POST /disconnect**: Disconnect from MetaTrader 5
- **GET /health**: Health check endpoint

## Authentication

All endpoints except /health require API key authentication. Include your API key in the request header:

```
X-API-Key: your-api-key-here
```
## Docker Support

Build and run with Docker:

```
docker build -t metatrader-api .
docker run -p 8000:8000 --env-file .env metatrader-api
```

Note: Running MetaTrader 5 in Docker requires additional setup due to Wine dependencies.

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.