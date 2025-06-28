# HealthFinder API Server

A FastAPI-based healthcare information search platform that provides comprehensive provider search capabilities, NPPES NPI Registry integration, and biomedical research tools.

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (Required)
- **uv** - Modern Python package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthfinder
   ```

2. **Install dependencies with uv**
   ```bash
   # Install all dependencies (includes dev dependencies)
   uv sync
   
   # Or install only runtime dependencies
   uv sync --no-dev
   ```

3. **Activate the virtual environment**
   ```bash
   # uv automatically creates and manages the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

### Running the Server

#### Method 1: Direct Python execution (Recommended for development)

```bash
cd server
python -m app.main
```

#### Method 2: Using uvicorn directly

```bash
cd server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Method 3: Using uv run

```bash
cd server
uv run python -m app.main
```

The server will start at: **http://localhost:8000**

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

## 📋 API Endpoints

### Core Endpoints
- `GET /` - API information and capabilities
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Provider Search (`/api/v1/providers`)
- `GET /search` - General provider search
- `GET /search/individual` - Individual providers (physicians, nurses, etc.)
- `GET /search/organizational` - Organizations (hospitals, clinics, etc.)
- `GET /search/by-taxonomy` - Search by specialty/taxonomy
- `GET /types` - Get all provider types
- `GET /{provider_id}` - Get provider details

### NPPES NPI Registry (`/api/v1/nppes`)
- `GET /search/basic` - Basic NPPES search
- `GET /search/individual` - Individual provider search
- `GET /search/organizational` - Organizational provider search
- `GET /search/by-npi/{npi}` - Search by NPI number
- `GET /validate/npi/{npi}` - Validate NPI number
- `POST /search/advanced` - Advanced search with full parameters

### Authentication (`/api/v1/auth`)
- `GET /google/url` - Get Google OAuth URL
- `POST /google/login` - Google OAuth login
- `GET /me` - Get current user
- `POST /logout` - Logout

## ⚙️ Configuration

The server uses environment variables for configuration. Create a `.env` file in the **server** directory:

```bash
cd server
cp .env.example .env  # If example exists, or create manually
```

### Environment Variables

#### Basic Configuration
```env
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=true
SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO
```

#### Database Configuration (SQLite - Default)
```env
# SQLite database (default, no additional config needed)
DB_TYPE=sqlite
SQLITE_DB_FILE=healthfinder.db
```

#### Database Configuration (PostgreSQL - Optional)
```env
# PostgreSQL database
DB_TYPE=postgres
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=healthfinder
POSTGRES_PORT=5432
```

#### OAuth Configuration (Optional)
```env
# Google OAuth (for authentication features)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### External API Keys (Optional)
```env
# For enhanced features
OPENAI_API_KEY=your-openai-key
BIOMCP_API_KEY=your-biomcp-key
PUBMED_API_KEY=your-pubmed-key
```

### Default Configuration
If no `.env` file is provided, the server will use these defaults:
- **Database**: SQLite (`server/data/healthfinder.db`)
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `8000`
- **Debug mode**: `False`
- **Log level**: `INFO`

## 🗄️ Database Setup

### SQLite (Default)
No setup required. The database file will be created automatically at `server/data/healthfinder.db`.

### PostgreSQL (Optional)
1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE healthfinder;
   ```
3. Update environment variables in `.env`
4. Tables will be created automatically on first run

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd server

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test categories
python -m pytest -m api          # API tests only
python -m pytest -m providers    # Provider tests only
python -m pytest -m nppes        # NPPES tests only

# Run with coverage
python -m pytest --cov=app --cov-report=html
```

## 🏗️ Development

### Project Structure
```
server/
├── app/
│   ├── api/          # API route modules
│   │   ├── providers.py    # Provider search endpoints
│   │   ├── nppes.py        # NPPES NPI registry endpoints
│   │   ├── auth.py         # Authentication endpoints
│   │   └── biomcp.py       # BioMCP integration
│   ├── clients/      # External API clients
│   │   ├── nppes.py        # NPPES client
│   │   └── practo.py       # Practo client
│   ├── core/         # Core application modules
│   │   ├── config.py       # Configuration management
│   │   └── db.py           # Database setup
│   ├── models/       # Pydantic data models
│   │   └── providers.py    # Provider-related models
│   └── main.py       # FastAPI application entry point
├── tests/            # Test suites
├── data/             # Database files (SQLite)
├── logs/             # Application logs
└── requirements-test.txt  # Test dependencies
```

### Key Features
- **Provider Search**: Search for healthcare providers by name, location, specialty
- **NPPES Integration**: Full integration with the National Provider Identifier registry
- **Multiple Provider Types**: Support for both individual and organizational providers
- **Advanced Filtering**: Search by taxonomy codes, location, specialties
- **Authentication**: Google OAuth integration
- **Comprehensive Testing**: 102 tests with 100% pass rate
- **Modern Stack**: FastAPI, Pydantic V2, SQLAlchemy 2.0

### Code Quality
```bash
# Run linting and formatting (if configured)
uv run black .
uv run isort .
uv run ruff check .
uv run mypy .
```

## 🔍 API Usage Examples

### Search for Providers
```bash
# Search by name and location
curl "http://localhost:8000/api/v1/providers/search?query=John Smith&state=CA"

# Search for hospitals in a city
curl "http://localhost:8000/api/v1/providers/search/organizational?city=Los Angeles&state=CA"

# Search by specialty
curl "http://localhost:8000/api/v1/providers/search/by-taxonomy?taxonomy_code=207Q00000X&state=NY"
```

### NPPES NPI Registry
```bash
# Look up provider by NPI
curl "http://localhost:8000/api/v1/nppes/search/by-npi/1234567890"

# Validate NPI number
curl "http://localhost:8000/api/v1/nppes/validate/npi/1234567890"

# Search individual providers
curl "http://localhost:8000/api/v1/nppes/search/individual?first_name=John&state=CA"
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   PORT=8001 python -m app.main
   ```

2. **Database connection errors**
   ```bash
   # Check database configuration in .env
   # For SQLite, ensure the data/ directory exists
   mkdir -p server/data
   ```

3. **Module import errors**
   ```bash
   # Ensure you're in the server directory
   cd server
   # Ensure virtual environment is activated
   source ../.venv/bin/activate
   ```

4. **Permission errors (macOS/Linux)**
   ```bash
   # Ensure proper permissions for log directory
   chmod 755 server/logs
   ```

### Performance Tips
- Use SQLite for development and small deployments
- Use PostgreSQL for production and high-traffic scenarios
- Enable debug mode only in development (`DEBUG=true`)
- Monitor logs in `server/logs/healthfinder.log`

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contributing guidelines here]

---

**Need help?** Check the API documentation at http://localhost:8000/docs or review the test files in `server/tests/` for usage examples.
