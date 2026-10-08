# MongoDB persistence and local retrieval

MongoDB Atlas stores the school documents only. Similarity search runs locally
in Python because the MVP contains just 15 sections. No Atlas Search or Vector
Search index, search service, or paid API is required by this retrieval path.

Use the existing `MONGODB_URI` setting from the environment or project-root
`.env`. Never paste or log its value. The Atlas user needs database access and
Atlas Network Access must allow your connection. Run commands from project root.

Database: `nyc_school_navigator`. Collection: `school_sections`.
Each document contains `_id`, `content`, `metadata`, and a 384-dimensional
embedding from `sentence-transformers/all-MiniLM-L6-v2`.
Document `_id` is `<DBN>:<section>`; reingestion updates existing sections.
This stores one current version per school/category; historical years would
require extending that identity.

## Commands

Run all unit tests (no live MongoDB or model download required):

```bash
uv run pytest
```

Search the 15 documents already stored, without rewriting them:

```bash
uv run tests/smoke_mongo.py --search-only
```

Optional persistence check, writing all sections twice and verifying no duplicates:

```bash
uv run tests/smoke_mongo.py --ingest-only
```

Full ingestion and local retrieval smoke check:

```bash
uv run tests/smoke_mongo.py
```

The smoke check verifies all 15 school/category identities. Search returns three
results with finite cosine scores in descending order, preserving source metadata
and omitting embeddings from output. No index creation or readiness wait is needed.

## Retrieval flow

`retrieve_sections(query, top_k=5)`:

1. Rejects empty queries and non-positive/non-integer `top_k` values.
2. Uses the existing `embed_sections()` function to embed the question locally
   with the same model and normalization as stored sections.
3. Reads documents via `collection.find()`, including text, metadata, and embeddings.
4. Computes cosine similarity with NumPy:
   `dot(query, document) / (norm(query) * norm(document))`.
5. Sorts descending by score and returns at most `top_k` records containing
   `_id`, `content`, `metadata`, and `score`.

Cosine compares vector directions: 1 means aligned, 0 means orthogonal, and -1
means opposite. These are raw cosine values, not the previous Atlas search scores.
They measure semantic similarity, not factual confidence or school quality.
For normalized vectors cosine equals the dot product, but computing both norms
explicitly also handles non-unit vectors correctly.

Empty collections return an empty list. Invalid stored vectors (zero, non-finite,
or dimensions different from the query) raise a clear error rather than silently
producing incorrect rankings. NumPy already exists through SentenceTransformers;
no dependency changes were needed.

This reads and scores the entire tiny corpus on each query. It is sufficient for
15 sections; scaling to a large corpus is outside this MVP task.
