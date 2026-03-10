"""
RAG (Retrieval-Augmented Generation) Service for Schema-Aware NLP-to-SQL.

This module indexes database schema metadata using TF-IDF vectorization
and retrieves only the most relevant tables for a given natural language query
using cosine similarity.

This allows the LLM to focus on a small subset of the schema instead of the
entire database, dramatically improving accuracy and scalability for databases
with many tables.

Uses scikit-learn (TF-IDF + cosine similarity) — lightweight, fast, and
zero dependency conflicts.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ scikit-learn not installed. RAG will be disabled. Install with: pip install scikit-learn")


# ─────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────
# Number of tables to retrieve per query (top-K)
DEFAULT_TOP_K = 5
# Minimum similarity score to include a table (0.0 - 1.0, higher = more strict)
MIN_SIMILARITY_THRESHOLD = 0.05


# Common table relationship keywords to enrich embeddings
RELATIONSHIP_HINTS = {
    "user_id": "relates to users table, user identity, person",
    "customer_id": "relates to customers table, customer identity, client buyer",
    "order_id": "relates to orders table, order reference, purchase",
    "product_id": "relates to products table, product reference, item",
    "student_id": "relates to students table, student reference, learner",
    "seller_id": "relates to sellers table, seller reference, vendor merchant",
    "category_id": "relates to categories table, category reference, type",
    "employee_id": "relates to employees table, employee reference, worker staff",
    "department_id": "relates to departments table, department reference, division",
}


class RAGSchemaService:
    """
    Retrieval-Augmented Generation service for database schema.
    
    Indexes table schemas using TF-IDF vectorization and retrieves
    the most relevant tables for a given natural language query
    using cosine similarity.
    """

    def __init__(self):
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None
        self._table_documents: List[str] = []
        self._table_names: List[str] = []
        self._current_schema_hash: Optional[str] = None
        self._indexed_tables: set = set()

        if not RAG_AVAILABLE:
            print("⚠️ RAG Service: scikit-learn not available. Using full schema fallback.")
        else:
            print("✅ RAG Service: Initialized (TF-IDF + Cosine Similarity)")

    @property
    def is_available(self) -> bool:
        """Check if RAG service is ready to use."""
        return RAG_AVAILABLE and self._tfidf_matrix is not None

    def _compute_schema_hash(self, schema: List[Dict[str, Any]]) -> str:
        """Compute a hash of the schema to detect changes."""
        schema_str = json.dumps(schema, sort_keys=True, default=str)
        return hashlib.md5(schema_str.encode()).hexdigest()

    def _build_table_document(self, table: Dict[str, Any]) -> str:
        """
        Build a rich text document for a table that captures its semantic meaning.
        This is what gets vectorized with TF-IDF.
        """
        table_name = table["name"]
        columns = table.get("columns", [])

        # Start with table name and variations (repeat for higher weight)
        parts = [
            table_name,
            table_name,
            table_name,
        ]

        # Add singular/plural variations for better matching
        if table_name.endswith("s"):
            singular = table_name[:-1]
            parts.extend([singular, singular])
        else:
            parts.extend([table_name + "s", table_name + "s"])

        # Underscored names split into words (user_products -> user products)
        if "_" in table_name:
            parts.extend(table_name.replace("_", " ").split())

        # Add column names and types
        for col in columns:
            col_name = col["name"]
            col_type = str(col.get("type", "TEXT"))

            parts.append(col_name)
            
            # Underscored column names split
            if "_" in col_name:
                parts.extend(col_name.replace("_", " ").split())

            # Foreign key relationships
            if "foreign_key" in col:
                fk_target = col["foreign_key"]
                fk_table = fk_target.split(".")[0]
                parts.extend([fk_table, f"join {fk_table}", f"related {fk_table}"])

            # Add relationship hints for common FK patterns
            col_lower = col_name.lower()
            if col_lower in RELATIONSHIP_HINTS:
                parts.append(RELATIONSHIP_HINTS[col_lower])

        # Add semantic hints based on common table names
        semantic_hints = self._get_semantic_hints(table_name, columns)
        if semantic_hints:
            parts.append(semantic_hints)

        return " ".join(parts)

    def _get_semantic_hints(self, table_name: str, columns: List[Dict]) -> str:
        """Generate semantic hints to improve retrieval accuracy."""
        name_lower = table_name.lower()
        col_names = {c["name"].lower() for c in columns}
        hints = []

        # Table-name based hints
        hint_map = {
            "users": "user accounts people persons who names profiles person",
            "customers": "customers clients buyers purchasers client buyer customer",
            "orders": "orders purchases transactions buying shopping bought order purchase",
            "products": "products items goods merchandise things buy product item",
            "user_products": "products bought users purchases what users bought user product purchase",
            "students": "students pupils learners education student pupil academic",
            "employees": "employees workers staff personnel employee worker",
            "departments": "departments divisions teams groups department division",
            "categories": "categories types classifications category type kind",
            "sellers": "sellers vendors suppliers merchants seller vendor",
            "invoices": "invoices bills receipts payments invoice bill receipt",
            "payments": "payments transactions money billing payment paid pay",
            "inventory": "inventory stock warehouse supply available quantity material components",
            "users_info": "user details profiles information locations addresses user info detail location city address",
            
            # MES & Manufacturing Specific Table Hints
            "machines": "machines equipment assets devices tools machinery cnc robot printer lathe mill",
            "downtime_log": "downtime offline stops failures maintenance repair breakdown stopped down broken",
            "production_lines": "production lines assembly factory floor manufacturing routing work cell",
            "plants": "plants facilities factories locations sites buildings",
            "shifts": "shifts day night working hours schedule labor personnel roster",
            "defects": "defects scraps scrap quality rejects bad rejected failed damaged",
            "work_orders": "work orders jobs production planning routing mes tasks",
        }

        if name_lower in hint_map:
            hints.append(hint_map[name_lower])

        # Column-based hints
        if "city" in col_names or "location" in col_names or "address" in col_names:
            hints.append("location geographic where live city place area region")
        if "email" in col_names:
            hints.append("contact email address communication")
        if "price" in col_names or "amount" in col_names or "total_amount" in col_names:
            hints.append("pricing costs financial monetary money value price amount total")
        if "gpa" in col_names or "grade" in col_names or "score" in col_names:
            hints.append("academic performance grades scores gpa score grade")
        if "date" in col_names or "created_at" in col_names or "order_date" in col_names or "timestamp" in col_names:
            hints.append("temporal dates time when date created recently timestamp")
        if "name" in col_names or "username" in col_names:
            hints.append("named entities identifying people things name called who")
        if "quantity" in col_names or "count" in col_names or "actual_output" in col_names or "target_output" in col_names:
            hints.append("quantity count how many number amount production output pieces parts units")
            
        # MES / OEE Specific Column Hints
        if "duration" in col_names or "downtime" in col_names:
            hints.append("downtime offline duration time minutes hours availability stops oee")
        if "defect" in col_names or "scrap" in col_names or "good_output" in col_names:
            hints.append("quality defects scrap rejects yield oee bad parts good parts")
        if "cycle_time" in col_names or "ideal_cycle" in col_names:
            hints.append("performance speed rate cycle time oee throughput")

        return " ".join(hints)

    def index_schema(self, schema: List[Dict[str, Any]]) -> bool:
        """
        Index the database schema using TF-IDF vectorization.
        Only re-indexes if the schema has changed.
        
        Returns True if indexing was performed, False if skipped (no changes).
        """
        if not RAG_AVAILABLE:
            return False

        # Check if schema has changed
        new_hash = self._compute_schema_hash(schema)
        if new_hash == self._current_schema_hash and self._tfidf_matrix is not None:
            return False

        try:
            # Build documents for each table
            self._table_documents = []
            self._table_names = []

            for table in schema:
                doc = self._build_table_document(table)
                self._table_documents.append(doc)
                self._table_names.append(table["name"])

            if not self._table_documents:
                return False

            # Create TF-IDF vectorizer and fit on table documents
            self._vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words=None,  # We want table/column names to be kept
                ngram_range=(1, 2),  # Unigrams and bigrams for better matching
                max_features=10000,
                sublinear_tf=True,  # Apply sublinear tf scaling (1 + log(tf))
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(self._table_documents)

            self._current_schema_hash = new_hash
            self._indexed_tables = set(self._table_names)
            print(f"✅ RAG: Indexed {len(self._table_documents)} tables using TF-IDF.")
            print(f"   Tables: {', '.join(self._indexed_tables)}")
            return True

        except Exception as e:
            print(f"❌ RAG: Failed to index schema: {e}")
            self._tfidf_matrix = None
            return False

    def retrieve_relevant_tables(
        self,
        query: str,
        schema: List[Dict[str, Any]],
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant tables for a given natural language query.
        
        Args:
            query: The natural language query from the user
            schema: The full database schema (used as fallback)
            top_k: Maximum number of tables to return
            
        Returns:
            A filtered list of table schema dicts, containing only the most relevant tables.
        """
        # If RAG is not available or schema is small, return full schema
        if not self.is_available:
            return schema
        
        # For very small schemas (≤ top_k tables), RAG adds no value
        if len(schema) <= top_k:
            return schema

        try:
            # Ensure schema is indexed
            self.index_schema(schema)

            # Transform the query using the fitted TF-IDF vectorizer
            query_vector = self._vectorizer.transform([query])

            # Compute cosine similarity between query and all table documents
            similarities = cosine_similarity(query_vector, self._tfidf_matrix).flatten()

            # Get top-K indices sorted by similarity (descending)
            top_indices = similarities.argsort()[::-1][:top_k]

            # Filter by minimum similarity threshold
            relevant_tables = []
            for idx in top_indices:
                sim_score = similarities[idx]
                if sim_score >= MIN_SIMILARITY_THRESHOLD:
                    relevant_tables.append((self._table_names[idx], sim_score))

            if not relevant_tables:
                # No good matches found, fall back to full schema
                return schema

            # Build filtered schema preserving original table dicts
            relevant_names = {t[0] for t in relevant_tables}
            
            # Also include tables that are related via foreign keys to relevant tables
            for table in schema:
                if table["name"] in relevant_names:
                    for col in table.get("columns", []):
                        if "foreign_key" in col:
                            fk_table = col["foreign_key"].split(".")[0]
                            relevant_names.add(fk_table)
                            
            # Also check reverse: tables that have FKs pointing to relevant tables  
            for table in schema:
                for col in table.get("columns", []):
                    if "foreign_key" in col:
                        fk_table = col["foreign_key"].split(".")[0]
                        if fk_table in relevant_names:
                            relevant_names.add(table["name"])

            filtered_schema = [t for t in schema if t["name"] in relevant_names]

            # Log retrieval details
            detail_str = ", ".join([f"{name}({score:.2f})" for name, score in relevant_tables])
            print(f"🔍 RAG: Query '{query[:60]}' → {len(filtered_schema)}/{len(schema)} tables")
            print(f"   Scores: {detail_str}")

            return filtered_schema if filtered_schema else schema

        except Exception as e:
            print(f"⚠️ RAG: Retrieval failed ({e}), falling back to full schema.")
            return schema

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the RAG service."""
        return {
            "available": RAG_AVAILABLE,
            "initialized": self._vectorizer is not None,
            "collection_ready": self._tfidf_matrix is not None,
            "indexed_tables": len(self._indexed_tables),
            "table_names": list(self._indexed_tables),
            "schema_hash": self._current_schema_hash,
            "method": "TF-IDF + Cosine Similarity",
        }


# ─────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────
rag_service = RAGSchemaService()
