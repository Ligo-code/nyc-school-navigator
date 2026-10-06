# NYC School Navigator

An AI-powered RAG assistant for answering focused questions using official New York City Public Schools documentation.

## Project Overview

NYC School Navigator is a small Retrieval-Augmented Generation (RAG) project designed to explore how reliably an AI system can retrieve and use information from official NYC Public Schools resources.

The project intentionally starts with a **very small and controlled scope**.

Rather than attempting to cover the entire NYC school system, the first version will focus on **one narrow topic and a small set of official source documents**. This makes it possible to inspect the full RAG pipeline, understand retrieval failures, and establish a meaningful evaluation baseline before expanding the system.

The initial goal is not to build a comprehensive school information platform. It is to build a small end-to-end RAG system whose behavior can be understood and measured.

## Problem Statement

Official NYC Public Schools information is often contained in long guides, policy documents, and other resources.

Even when the correct information exists in a document, finding the relevant section can require searching through many pages and understanding unfamiliar terminology.

A RAG system can help users ask questions in natural language and retrieve relevant information from these documents.

However, producing a plausible answer is not enough.

The project will also examine an important question:

> Did the system retrieve the information needed to answer the user's question?

This makes retrieval quality a central part of the project.

## MVP Scope

The first version of NYC School Navigator will deliberately remain small.

The MVP will:

1. Select a narrow NYC Public Schools topic.
2. Collect a small number of official documents relevant to that topic.
3. Extract and inspect their text.
4. Split the documents into searchable chunks.
5. Generate embeddings for those chunks.
6. Store the chunks, embeddings, and metadata in MongoDB Atlas.
7. Retrieve relevant chunks using MongoDB Atlas Vector Search.
8. Pass the retrieved context to an LLM.
9. Generate an answer grounded in the retrieved information.
10. Return source information with the answer.
11. Evaluate whether retrieval returned the expected source material.

The scope can be expanded only after this basic pipeline works reliably.

## Data Collection

For the initial MVP, source documents will be selected manually from official NYC Public Schools resources.

Because the dataset is intentionally small, the first version does **not** require a general-purpose web scraper.

Where official documents are available as downloadable files, they can be downloaded and processed directly. This keeps ingestion simple and makes it easier to inspect exactly what information enters the knowledge base.

More automated collection or scraping can be added later if the project grows beyond the initial dataset.

## Evaluation Dataset

The evaluation dataset will be created separately from the RAG knowledge base.

Instead of automatically generating evaluation questions from the source documents with an LLM, the initial questions will be **manually curated**.

This is intentional.

For a small MVP, manually written questions make it easier to control what is being tested and avoid creating evaluation questions that simply mirror the wording or structure of the source documents.

Each evaluation case can contain information such as:

```json
{
  "question": "How can a parent request an evaluation for their child?",
  "expected_source": "source-document-name",
  "category": "special_education"
}
```

The questions should represent realistic ways a parent or caregiver might ask for information.

## RAG Pipeline

```text
Official NYC Public Schools Documents
                |
                v
        Text Extraction
                |
                v
            Chunking
                |
                v
     SentenceTransformer Embeddings
                |
                v
          MongoDB Atlas
                |
                v
      Atlas Vector Search
                |
                v
          User Question
                |
                v
            Retrieval
                |
                v
        Retrieved Context
                |
                v
               LLM
                |
                v
      Grounded Answer + Sources
```

## Retrieval Evaluation

The first evaluation will focus primarily on **retrieval quality**.

For each manually curated question, the system will check whether the expected source material appears among the retrieved results.

Initial metrics may include:

* whether the expected source was retrieved
* rank of the expected source
* Hit@K

For example, if the expected information appears within the top 5 retrieved chunks, the evaluation case may count as a Hit@5.

This creates a simple baseline that can later be used to compare retrieval configurations.

## Retrieval Debugging

The project will keep retrieval behavior visible rather than treating the RAG pipeline as a black box.

For a query, debugging information may include:

```text
user question
retrieved chunks
source document
page number
chunk index
retrieval rank
similarity/relevance score
top_k
```

This makes it possible to distinguish between different types of failures.

For example:

```text
Question
   |
   v
Was the relevant information retrieved?
   |
   +-- No  -> Retrieval / chunking / indexing problem
   |
   +-- Yes
         |
         v
Was it available in the context sent to the LLM?
         |
         +-- No  -> Ranking / context-selection problem
         |
         +-- Yes -> Generation / grounding problem
```

The initial MVP does not need to automate every failure category. The important part is preserving enough information to investigate failures.

## Baseline First

The first implementation will establish a simple baseline.

The project will avoid prematurely optimizing:

* chunk size
* chunk overlap
* `top_k`
* ranking strategies
* advanced retrieval techniques

Once the baseline works and evaluation results are available, individual parameters can be changed and compared against the baseline.

This keeps experiments measurable instead of changing several parts of the RAG pipeline at the same time.

## Technology Stack

| Component            | Technology                        |
| -------------------- | --------------------------------- |
| Programming Language | Python                            |
| User Interface       | Streamlit                         |
| RAG Framework        | LangChain                         |
| LLM                  | Open-source model, TBD            |
| Embeddings           | SentenceTransformers              |
| Database             | MongoDB Atlas                     |
| Retrieval            | MongoDB Atlas Vector Search       |
| Document Processing  | Python / document loaders         |
| Observability        | Langfuse                          |
| Evaluation           | Small custom retrieval evaluation |

The final open-source LLM will be selected later based on the project's resource constraints.

## Document Metadata

Each stored chunk will retain enough metadata to identify where it came from.

For example:

```json
{
  "document_title": "...",
  "source_url": "...",
  "page": 12,
  "category": "...",
  "chunk_index": 7
}
```

This metadata will support both source attribution and retrieval debugging.

## MVP Milestones

### Phase 1 — Data

* [ ] Select the initial topic
* [ ] Select the initial official source documents
* [ ] Download the source files
* [ ] Inspect document structure
* [ ] Extract text
* [ ] Define document metadata

### Phase 2 — Retrieval

* [ ] Implement baseline chunking
* [ ] Generate embeddings
* [ ] Store chunks and embeddings in MongoDB Atlas
* [ ] Configure Atlas Vector Search
* [ ] Implement retrieval
* [ ] Inspect retrieved chunks manually

### Phase 3 — Evaluation

* [ ] Create a small manually curated question set
* [ ] Define expected source information
* [ ] Run baseline retrieval evaluation
* [ ] Record retrieval rank and Hit@K
* [ ] Analyze failed cases

### Phase 4 — Generation

* [ ] Connect an open-source LLM
* [ ] Generate answers from retrieved context
* [ ] Return source information
* [ ] Handle insufficient retrieved context

### Phase 5 — Interface and Observability

* [ ] Add a minimal Streamlit interface
* [ ] Add basic Langfuse tracing
* [ ] Expose useful retrieval/debug information

## Out of Scope for the Initial MVP

The first version will **not** attempt to implement:

* comprehensive coverage of NYC Public Schools resources
* large-scale automated web scraping
* LLM-generated evaluation datasets
* complex retrieval optimization
* automated hyperparameter experiments
* multiple chunking strategies at once
* multilingual support
* advanced reranking
* agentic retrieval
* production-scale infrastructure

These can be considered only after the baseline system is working and measurable.

## Future Experiments

Once the MVP is stable, the baseline can support controlled experiments such as:

* different chunk sizes
* different chunk overlap
* different `top_k` values
* alternative chunking strategies
* reranking
* additional documents
* additional school-related topics
* multilingual queries
* improved insufficient-context handling

Each experiment should change a limited part of the pipeline and compare the result with the existing baseline.

## Project Goal

The goal of NYC School Navigator is to build a small, understandable RAG system based on real-world public information.

The project is designed not only to answer questions, but also to make it possible to investigate **why a RAG system succeeds or fails**.

The initial MVP therefore prioritizes:

**small scope → transparent retrieval → measurable baseline → controlled improvement**

rather than attempting to build a large feature-complete application immediately.
