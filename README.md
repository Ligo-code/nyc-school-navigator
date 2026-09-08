# NYC School Navigator

An AI-powered assistant designed to help families find and understand information from official New York City Public Schools resources.

## Project Overview

New York City families often need to navigate large amounts of school-related information across guides, policies, and other official resources. Finding an answer to a specific question may require searching through multiple documents and understanding unfamiliar terminology.

**NYC School Navigator** will use Retrieval-Augmented Generation (RAG) to help users ask questions in natural language and receive answers grounded in official school documentation.

In addition to the user-facing assistant, the project will include a simple evaluation and debugging layer to make the RAG pipeline more transparent and help identify retrieval problems.

## Problem Statement

Important information about public schools is available online, but it can be distributed across long documents and multiple resources.

Parents and caregivers may have questions such as:

* How can I request a special education evaluation for my child?
* What language assistance is available to families?
* How does middle or high school admission work?
* Where can I find information about services for students with disabilities?
* What rights do parents have during the special education process?

Instead of manually searching through multiple documents, users should be able to ask a question and receive a concise answer supported by relevant official sources.

## Proposed Solution

The application will:

1. Collect a small set of publicly available NYC Public Schools documents.
2. Extract and split the documents into searchable text chunks.
3. Generate embeddings for those chunks.
4. Store the chunks, embeddings, and source metadata in MongoDB Atlas.
5. Use MongoDB Atlas Vector Search to retrieve relevant information for a user's question.
6. Send the retrieved context to an open-source LLM.
7. Generate an answer grounded in the retrieved documents.
8. Display the answer together with its source information.

The project will also expose retrieval information for debugging and evaluation.

## Target Users

The primary users are parents and caregivers navigating the NYC public school system.

The initial prototype will focus on a limited set of topics covered by the selected documents rather than attempting to answer every possible question about NYC schools.

## Planned Features

### School Information Assistant

Users will be able to enter a school-related question and receive an AI-generated answer based on the available official documentation.

### Source-Grounded Answers

Answers will include source information so users can identify which document was used.

When the retrieved information is insufficient, the application should avoid inventing an answer.

### Semantic Retrieval

The system will use vector embeddings and MongoDB Atlas Vector Search to retrieve document sections based on semantic similarity rather than relying only on keyword matching.

### Retrieval Debug View

A developer/debug view will expose information such as:

* retrieved document chunks
* source document and page
* retrieval ranking
* similarity/relevance information
* retrieval configuration

This will help identify whether an incorrect answer originated from retrieval or from answer generation.

### RAG Evaluation

A small evaluation dataset will be created using realistic questions based on publicly available school FAQs and documentation.

The project will use this dataset to evaluate whether the RAG system retrieves the expected source material.

Possible experiments include comparing:

* different chunk sizes
* different chunk overlap
* different `top_k` values
* retrieval configurations

The goal is not only to build a RAG application, but also to measure and improve how reliably it retrieves relevant information.

## Planned Technology Stack

| Component                  | Technology                         |
| -------------------------- | ---------------------------------- |
| Programming Language       | Python                             |
| User Interface             | Streamlit                          |
| LLM Framework              | LangChain                          |
| LLM                        | Open-source model, final model TBD |
| Embeddings                 | SentenceTransformers               |
| Database                   | MongoDB Atlas                      |
| Retrieval                  | MongoDB Atlas Vector Search        |
| Document Processing        | pypdf / LangChain document loaders |
| Observability & Evaluation | Langfuse                           |

The final open-source LLM will be selected after testing models that can run within the project's free-resource requirements.

## Data Sources

The knowledge base will contain a small collection of publicly available documents from official NYC Public Schools resources.

Potential topics include:

* special education
* parent rights
* language access
* school admissions
* services for students with disabilities
* resources for families

Approximately **8–12 documents** are planned for the initial prototype.

Each stored chunk will retain metadata such as:

```text
document title
source
page number
category
source URL
chunk index
```

This metadata will allow retrieved information to be connected back to its original source.

The evaluation questions will be kept separate from the documents used as the RAG knowledge base.

## High-Level Architecture

```text
Official NYC Public Schools Documents
                |
                v
        Document Processing
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
User Question -> Retrieval
                |
                v
        Retrieved Context
                |
                v
        Open-Source LLM
                |
                v
      Grounded Answer + Sources
                |
                v
           Streamlit UI


        Observability / Evaluation
                |
                v
             Langfuse
        /                 \
     Traces             Evaluation
```

## Evaluation Approach

The project will include a small test set of realistic questions with expected source information.

For example:

```json
{
  "question": "How can a parent request an evaluation for their child?",
  "expected_source": "Special Education Family Guide",
  "category": "special_education"
}
```

The first version will establish a baseline retrieval configuration.

Subsequent experiments can modify parameters such as chunk size and the number of retrieved chunks and compare their performance.

Potential retrieval metrics include:

* whether the expected source appears in the retrieved results
* source rank
* Hit@K

Langfuse will be used to trace the RAG workflow and record information useful for analyzing retrieval and generation behavior.

## Project Scope

The initial goal is a small, functional end-to-end prototype.

### MVP

* [ ] Collect official source documents
* [ ] Extract document text
* [ ] Implement chunking
* [ ] Generate embeddings
* [ ] Store documents and embeddings in MongoDB Atlas
* [ ] Configure Atlas Vector Search
* [ ] Implement retrieval
* [ ] Connect an open-source LLM
* [ ] Build a simple Streamlit interface
* [ ] Return answers with source information
* [ ] Add basic Langfuse tracing
* [ ] Create a small evaluation dataset
* [ ] Run a baseline retrieval evaluation

### Possible Future Enhancements

* Compare different chunking strategies
* Add automated retrieval experiments
* Improve handling of questions with insufficient context
* Add multilingual questions
* Compare retrieval configurations
* Add additional NYC Public Schools topics and documents

## Project Goal

The goal of NYC School Navigator is to demonstrate how an open-source LLM can be combined with retrieval, vector search, prompt engineering, observability, and evaluation to build a useful AI application based on real-world public information.

Rather than evaluating the application only by whether an answer appears reasonable, the project will also examine **what information was retrieved and whether the correct source was available to the LLM when generating its answer**.
