# Backend Project Structure

The NLP Backend is organized following industry best practices for FastAPI applications, ensuring scalability, maintainability, and clear separation of concerns.

## Directory Layout

```text
nlp_backend/
├── app/                        # Application core
│   ├── api/                    # API Layer
│   │   ├── endpoints/          # Route handlers (auth, query, etc.)
│   │   └── __init__.py
│   ├── core/                   # Global configuration and security
│   │   ├── config.py
│   │   └── security.py
│   ├── db/                     # Data Access Layer
│   │   └── database.py         # SQLAlchemy engines and session management
│   ├── schemas/                # Pydantic models (Request/Response)
│   │   ├── query.py
│   │   └── user.py
│   ├── services/               # Business Logic Layer
│   │   ├── nlp.py              # LLM and heuristic SQL generation
│   │   ├── rag.py              # Schema retrieval-augmented generation
│   │   └── visualization.py    # Chart generation (Static & Interactive)
│   ├── __init__.py
│   └── main.py                 # FastAPI entry point
├── data/                       # Database files and static assets
│   ├── backups/                # SQL dumps and historical data
│   ├── app.db                  # Main application database
│   └── auth.db                 # Authentication database
├── scripts/                    # Utility scripts for data seeding/maintenance
├── tests/                      # Test suite
│   └── fixtures/               # Test data samples
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (LLM Keys, etc.)
```

## Layers

1. **API Layer (`app/api`)**: Responsible for handling HTTP requests, validating inputs using Pydantic schemas, and returning responses.
2. **Business Logic Layer (`app/services`)**: Contains the "heavy lifting" code. NLP processing, Vektore retrieval, and chart generation live here.
3. **Data Access Layer (`app/db`)**: Manages database connections and raw SQL execution with security guards.
4. **Schemas Layer (`app/schemas`)**: Defines the data contracts between the frontend and backend.
5. **Core Layer (`app/core`)**: Handles global settings, environment variable loading, and authentication security.
