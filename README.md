# FAQ Assistant

Semantic FAQ system using vector embeddings and similarity search. 
Routes questions to a local knowledge base or generative AI based on relevance.

---

## Setup

### Prerequisites

- Docker
- Docker Compose
- OpenAI API key

### Installation

**1. Clone the repository:**

```bash
git clone https://github.com/danieldutu/semantic-faq-assistant.git
cd faq-assistant
```

**2. Configure environment:**

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

**3. Build and start the containers:**

```bash
docker-compose up -d --build
```

**4. Seed the database:**

```bash
docker-compose exec app python scripts/seed_database.py --force
```

**Note:**
- The `--force` flag automatically reseeds without prompting (required for non-interactive Docker environments)
- Embeddings are generated asynchronously by Celery workers (default behavior)
- Use `--sync` flag if you want synchronous/blocking embedding generation

---
## System Architecture

```mermaid
graph TD
    A[User Question] --> B[Authentication]
    B --> C[LangChain AI Router]
    C -->|IT-related| D[Similarity Search]
    C -->|Off-topic| E[Compliance Response]
    D -->|score ≥ 0.65| F[FAQ Answer]
    D -->|score < 0.65| G[OpenAI Generative Response]
    
    style A fill:#e1f5ff
    style F fill:#c8e6c9
    style G fill:#fff9c4
    style E fill:#ffccbc
```

**Response Types:**
- **local**: FAQ Database Match
- **openai**: Generative AI Response  
- **compliance**: Off-topic Rejection

**Input:** User question text  
**Output:** Answer with source indication and similarity score

**Important note:** 
AI Router was integrated into the core flow to **filter off-topic questions before similarity search**, **improving** the **challenge** requirements by **avoiding wasteful embedding generation** and **database queries for irrelevant questions**.

---

## Configuration

All configuration parameters are in `.env` file. Key parameters:

### Basic Settings

- **OPENAI_API_KEY**: Your OpenAI API key (required)
- **API_SECRET_KEY**: API authentication secret (required)
- **DATABASE_URL** (`postgresql://faq_user:faq_password@postgres:5432/faq_db`): PostgreSQL connection string
- **SIMILARITY_THRESHOLD** (`0.65`): Minimum similarity score for FAQ matches

### Model Configuration

- **EMBEDDING_MODEL** (`text-embedding-3-small`): OpenAI embedding model for vector generation
- **CHAT_MODEL** (`gpt-4o-mini`): OpenAI model for generative fallback responses

**Supported Embedding Models:**
- `text-embedding-3-small` (1536 dimensions) - Default, cost-effective
- `text-embedding-3-large` (3072 dimensions) - Higher quality, more expensive
- `text-embedding-ada-002` (1536 dimensions) - Legacy model

**Important:** Changing the embedding model requires database migration. See [Changing Embedding Models](#changing-embedding-models) below.

### Service URLs

- **CELERY_BROKER_URL** (`redis://redis:6379/0`): Celery message broker
- **CELERY_RESULT_BACKEND** (`redis://redis:6379/0`): Celery result storage

---

## Usage

Run the system using Docker:

```bash
# Start all services
docker-compose up -d

# Health check
curl http://localhost:8000/health

# Ask a question (IT-related - should match FAQ)
curl -X POST http://localhost:8000/ask-question -H "Content-Type: application/json" -H "Authorization: Bearer faq-assistant-secret-key-2024" -d '{"user_question": "How do I reset my password?"}'

# Off-topic question (should return compliance response)
curl -X POST http://localhost:8000/ask-question -H "Content-Type: application/json" -H "Authorization: Bearer faq-assistant-secret-key-2024" -d '{"user_question": "What is the weather today?"}'
```

---

## API Endpoints

### `POST /ask-question`

Submit a question and get an answer.

**Authentication**: Required (Bearer token in Authorization header)

**Request:**
```json
{
  "user_question": "How do I reset my account?"
}
```

**Responses:**

**Local Match** (similarity ≥ 0.65):
```json
{
  "source": "local",
  "matched_question": "How can I restore my account to its default settings?",
  "answer": "In the account settings, there should be an option labeled 'Restore Default'.",
  "similarity_score": 0.92
}
```

**OpenAI Fallback** (similarity < 0.65):
```json
{
  "source": "openai",
  "matched_question": "N/A",
  "answer": "To integrate with Slack, you'll typically need to...",
  "similarity_score": 0.54
}
```

**Compliance Response** (off-topic):
```json
{
  "source": "compliance",
  "matched_question": "N/A",
  "answer": "This is not really what I was trained for, therefore I cannot answer. Try again.",
  "similarity_score": null
}
```

### `GET /health`

Check system health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

##  Scripts

### Create Embeddings

Generate embeddings for FAQs without vectors:

```bash
docker-compose exec app python scripts/create_embeddings.py

# Options:
#   --dry-run           Preview without executing
#   --collection NAME   Process specific collection only
#   --sync              Use synchronous mode instead of async (Celery is default)
```

**Note:** Embeddings are generated asynchronously by Celery workers by default for better performance.

### Update Embeddings

Token-efficient updates for modified FAQs:

```bash
docker-compose exec app python scripts/update_embeddings.py

# Options:
#   --dry-run   Preview without executing
#   --force     Regenerate all embeddings
#   --sync      Use synchronous mode instead of async (Celery is default)
```

**Note:** Embeddings are generated asynchronously by Celery workers by default for better performance.

### Add Collection

Add new FAQ collection from JSON file:

```bash
docker-compose exec app python scripts/add_collection.py faqs.json --name "collection_name" --description "Collection description"

# Options:
#   --dry-run   Preview without executing
#   --sync      Use synchronous mode instead of async (Celery is default)
```

**Note:** Embeddings are generated asynchronously by Celery workers by default for better performance.

**JSON Format:**
```json
[
  {
    "question": "How do I do X?",
    "answer": "You can do X by..."
  }
]
```

---


## Interactive Documentation

Navigate to the following URLs when services are running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Development

### Local Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Run API locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U faq_user -d faq_db

# Useful queries
SELECT id, question FROM faqs;
SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;
```

---

## Changing Embedding Models

The system validates that the configured embedding model matches the database schema dimension on startup. If there's a mismatch, the application will fail to start with a clear error message.

### Prerequisites

**Important:** Changing embedding models will **delete all existing embeddings** and require regeneration. This is necessary because vector dimensions are incompatible between models.

### Migration Steps

**1. Backup your data** (optional but recommended):
```bash
docker-compose exec postgres pg_dump -U faq_user faq_db > backup.sql
```

**2. Update the migration script:**

Edit `scripts/migrate_embedding_dimension.sql` and change line 26 to match your target model:
```sql
ALTER TABLE faqs ADD COLUMN embedding vector(3072);  -- For text-embedding-3-large
```

**3. Update your `.env` file:**
```bash
EMBEDDING_MODEL=text-embedding-3-large  # Or your desired model
```

**4. Run the migration:**
```bash
docker-compose exec postgres psql -U faq_user -d faq_db -f /app/scripts/migrate_embedding_dimension.sql
```

**5. Restart the application:**
```bash
docker-compose restart app
```

The startup validation will confirm the dimension matches.

**6. Regenerate all embeddings:**
```bash
docker-compose exec app python scripts/create_embeddings.py
```

This will generate new embeddings for all FAQs using the new model. With Celery workers, this happens asynchronously.

### Validation

Check that embeddings were regenerated successfully:
```bash
docker-compose exec postgres psql -U faq_user -d faq_db -c "SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL;"
```

The application logs will show:
```
✓ Embedding dimension validation passed: 3072D
```

---


