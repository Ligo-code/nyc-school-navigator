# NYC School Navigator

NYC School Navigator is a small Retrieval-Augmented Generation (RAG) application for comparing three New York City middle schools using official 2024–25 NYC School Quality Report data.

Users can ask questions in natural language about school enrollment, school quality, student experience, family experience, attendance, and selected student outcomes. The application retrieves relevant school data, generates a grounded answer with a local open-source language model, and exposes the retrieved evidence behind its citations.

The project intentionally keeps the dataset small so the complete RAG pipeline can remain understandable, inspectable, and measurable.

## Current MVP

The current version compares three NYC middle schools:

- The Christa McAuliffe School / I.S. 187 — `20K187`
- David A. Boody / I.S. 228 — `21K228`
- Mark Twain / I.S. 239 — `21K239`

The knowledge base currently uses official **2024–25 NYC School Quality Report** data.

Supported information includes:

- enrollment
- instruction and performance ratings
- safety and school climate ratings
- relationships with families
- learning environment
- student safety
- student support
- advising and planning
- family-school trust
- family communication
- family involvement
- average student attendance
- eighth-grade high school math credit
- eighth-grade high school science credit

The MVP does not currently include admissions rules, application deadlines, programs, seat availability, transfer rules, or live school information.

## Why This Project

Official school data contains useful information, but comparing schools across multiple metrics can require navigating structured reports and understanding how different measures relate to one another.

NYC School Navigator explores whether a small RAG system can make that information easier to query while preserving transparency about where an answer came from.

The goal is not simply to produce a plausible answer.

The system is designed around two questions:

1. Did retrieval find the information needed to answer the question?
2. Did the language model answer using the retrieved evidence?

Keeping these stages visible makes it easier to distinguish retrieval failures from generation failures and provides a baseline for controlled improvements.

## Architecture

The application has two main flows: data ingestion and question answering.

### Data ingestion

```text
NYC School Quality Report
        |
        v
    Excel Loader
        |
        v
   Normalization
        |
        v
 Semantic Sectioning
        |
        v
SentenceTransformer Embeddings
        |
        v
      MongoDB
```

Each school record is normalized and divided into five semantic sections:

```text
overview
school_quality
student_experience
family_experience
student_outcomes
```

With three schools, the current knowledge base contains **15 retrieval units**.

Each section contains human-readable content together with metadata identifying the school, DBN, section, source type, and source year.

Embeddings are generated locally with:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The vectors are normalized and stored with their corresponding sections in MongoDB.

### Question answering

```text
User Question
      |
      v
MiniLM Query Embedding
      |
      v
MongoDB School Sections
      |
      v
Local Cosine Similarity
      |
      v
Top-K Retrieved Sections
      |
      v
Grounded Prompt
      |
      v
Qwen3 4B via Ollama
      |
      v
Answer + Citations + Inspectable Evidence
      |
      v
Streamlit UI
```

MongoDB is used for persistence.

For the current small corpus, retrieval is intentionally performed locally rather than using a managed vector-search service. The application loads the stored school sections, compares their normalized embeddings with the query embedding using cosine similarity, ranks the results, and sends the highest-ranked sections to the language model.

This keeps the MVP simple, local, and inexpensive while preserving the ability to inspect retrieval behavior directly.

## Retrieval

The retrieval pipeline uses the same SentenceTransformer model for stored school sections and user questions:

```text
sentence-transformers/all-MiniLM-L6-v2
```

For each question:

1. The question is embedded locally.
2. Stored school sections are loaded from MongoDB.
3. Cosine similarity is calculated between the query and section embeddings.
4. Sections are ranked by similarity.
5. The highest-ranked sections are passed to the generation layer.

Retrieval results preserve:

- school name
- DBN
- semantic section
- source type
- source year
- similarity score
- retrieved content

This information is also available to the interface for evidence inspection.

## Local Answer Generation

Answer generation uses:

```text
qwen3:4b-instruct
```

through a local Ollama instance.

No paid LLM API is required for the current application.

The generation layer receives only the retrieved school context and instructs the model to answer from that information. When the supplied evidence does not contain enough information, the model is expected to say that the available school data does not provide the answer rather than inventing unsupported information.

The generation result contains:

```text
question
answer
sources
```

Each source includes a citation label and the evidence used to construct the LLM context.

## Inspectable Evidence

The Streamlit interface exposes the evidence behind generated answers.

A response may contain citations such as:

```text
[1]
[2]
```

Each citation corresponds to a retrieved school section.

Users can expand an evidence item to inspect:

- school name
- DBN
- semantic section
- source year
- retrieval score
- exact retrieved evidence supplied to the language model

The evidence is not regenerated or summarized by the LLM. It is the same retrieved section content used to build the generation context.

This makes the grounding process visible instead of treating the RAG pipeline as a black box.

## Example Questions

The application can answer questions such as:

```text
How many students are enrolled at The Christa McAuliffe School?
```

```text
What is Mark Twain's safety and school climate rating?
```

```text
Which school has the highest average student attendance?
```

```text
Which school has the highest percentage of eighth graders earning high school science credit?
```

```text
How does family-school trust compare across the three schools?
```

Questions outside the current dataset should produce an insufficient-context response.

For example:

```text
What is the admissions deadline for Mark Twain?
```

Admissions deadlines are not part of the current School Quality Report dataset.

## Evaluation

The project uses a manually curated evaluation set rather than generating evaluation questions automatically with an LLM.

This keeps the expected evidence under human control and makes retrieval failures easier to interpret.

The current evaluation set covers:

- overview facts
- school quality
- student experience
- family experience
- student outcomes
- cross-school comparisons
- multi-metric questions
- unsupported questions

A retrieval evaluation case can include:

```json
{
  "question": "Which school has the highest average student attendance?",
  "expected_section": "student_outcomes",
  "expected_dbns": ["20K187", "21K228", "21K239"]
}
```

Useful retrieval measures include:

- whether expected evidence was retrieved
- retrieval rank
- Hit@K

Generation can then be evaluated separately for factual correctness and grounding.

This separation helps distinguish cases where:

```text
Relevant evidence was not retrieved
        |
        v
Retrieval problem
```

from cases where:

```text
Relevant evidence was retrieved
        |
        v
Model produced an incorrect or unsupported answer
        |
        v
Generation / grounding problem
```

## Known Retrieval Limitation

The current baseline works well for focused factual questions and many single-metric comparisons.

A known limitation appears with some questions that combine several metrics across multiple schools.

For example, a question asking the system to compare all three schools simultaneously on attendance, family trust, and high school science credit may require evidence from several semantic sections and several schools.

A simple global top-k retrieval can overrepresent one school, leaving the language model without enough evidence for the full comparison.

This behavior is intentionally documented rather than hidden. It provides a concrete baseline case for the next retrieval improvement.

## Streamlit Interface

The Streamlit application provides:

- a focused natural-language question interface
- example questions
- generated answers
- citation labels
- expandable retrieved evidence
- retrieval metadata
- clear MVP scope information

The interface intentionally avoids presenting the system as a general-purpose chatbot. It is designed as a focused school-comparison tool backed by a controlled dataset.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Package / environment management | uv |
| User interface | Streamlit |
| Source data | NYC School Quality Report 2024–25 |
| Data processing | Python |
| Embeddings | SentenceTransformers / `all-MiniLM-L6-v2` |
| Persistence | MongoDB |
| Similarity search | Local cosine similarity |
| LLM | Qwen3 4B Instruct |
| Local model runtime | Ollama |
| Testing | pytest |
| Evaluation | Manually curated retrieval and answer evaluation |

The current MVP intentionally does **not** depend on LangChain, LangGraph, a paid LLM API, or MongoDB Atlas Vector Search for its RAG execution path.

## Project Structure

The main application responsibilities are separated into small modules:

```text
src/nyc_school_navigator/
├── ingestion/
│   ├── loaders.py
│   ├── normalizers.py
│   └── indexer.py
├── db/
│   └── mongo.py
├── retrieval.py
└── generation.py

tests/
├── unit and pipeline tests
├── MongoDB smoke checks
└── RAG smoke checks

streamlit_app.py
```

The exact structure may evolve as the project grows, but retrieval, generation, persistence, and interface responsibilities are intentionally kept separate.

## Running Locally

### Prerequisites

The project requires:

- Python environment managed with `uv`
- access to the configured MongoDB database
- Ollama running locally
- the `qwen3:4b-instruct` model

Install project dependencies:

```bash
uv sync
```

### MongoDB

Configure the MongoDB connection through the project's environment configuration.

Do not commit credentials or connection strings to the repository.

The current knowledge base contains 15 semantic school sections: five sections for each of the three supported schools.

### Ollama

Start Ollama and make sure the required model is available:

```bash
ollama pull qwen3:4b-instruct
```

You can confirm installed models with:

```bash
ollama list
```

### Run the application

From the project root:

```bash
uv run streamlit run streamlit_app.py
```

Streamlit will provide the local application URL.

## Tests

Run the automated test suite with:

```bash
uv run pytest
```

The unit tests mock external runtime dependencies where appropriate so the regular test suite does not require an active Ollama generation call.

The project also contains smoke checks for integration behavior that can be run when the required local services and configuration are available.

## Design Decisions

### Small corpus first

The project deliberately starts with only three schools.

This makes it possible to inspect every stored section, understand retrieval failures, and establish an evaluation baseline before expanding the corpus.

### Semantic sections instead of arbitrary text chunks

The School Quality Report data is structured rather than long-form prose.

Instead of splitting text using arbitrary character or token boundaries, each school is represented through meaningful semantic sections such as `student_outcomes` and `family_experience`.

This preserves the relationship between metrics that belong together.

### MongoDB for persistence, local similarity for retrieval

The corpus currently contains only 15 retrieval units.

For this scale, local cosine similarity is simple, transparent, and sufficient. A managed vector-search service would add infrastructure without materially improving the MVP.

If the corpus grows substantially, vector indexing can be reconsidered.

### Local open-source generation

Qwen3 runs through Ollama on the local machine.

This keeps the MVP independent of paid model APIs and satisfies the project's goal of using an open-source language model.

### Evidence visibility

Retrieved evidence remains visible through the Streamlit interface.

This allows users and developers to inspect what information was actually available to the model when an answer was generated.

## Current Status

Implemented:

- [x] Load official 2024–25 School Quality Report data
- [x] Normalize records for three schools
- [x] Create semantic retrieval sections
- [x] Generate local SentenceTransformer embeddings
- [x] Store sections, metadata, and embeddings in MongoDB
- [x] Implement local cosine-similarity retrieval
- [x] Connect a local open-source LLM through Ollama
- [x] Generate grounded answers
- [x] Return citation metadata
- [x] Expose exact retrieved evidence
- [x] Build Streamlit interface
- [x] Add automated tests
- [x] Verify the complete retrieval-to-generation flow with a real smoke test

In progress:

- [ ] Run the complete manually curated evaluation set
- [ ] Record retrieval and answer-quality results
- [ ] Improve retrieval for multi-school, multi-metric comparison questions

## Future Work

Potential next steps include:

- comparison-aware retrieval for multi-school questions
- controlled experiments with different `top_k` values
- retrieval evaluation with Hit@K
- larger school coverage
- additional official NYC Public Schools datasets
- admissions and program information
- improved insufficient-context detection
- alternative retrieval strategies
- reranking if the corpus becomes large enough to justify it
- observability and tracing
- multilingual queries

These improvements should be introduced as controlled experiments rather than changing several parts of the RAG pipeline simultaneously.

## Scope and Limitations

NYC School Navigator is an educational prototype, not a comprehensive NYC school-selection platform.

The current application covers only three schools and only the metrics loaded from the 2024–25 School Quality Report.

It should not be used as the sole source for admissions decisions or other time-sensitive school information.

The project intentionally prioritizes:

```text
small scope
    ↓
transparent retrieval
    ↓
measurable baseline
    ↓
controlled improvement
```

The goal is not to hide RAG failures behind a polished answer.

The goal is to build a small system where those failures can be observed, understood, measured, and improved.