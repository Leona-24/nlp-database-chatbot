# Project Implementation Challenges & Solutions

This document outlines the critical technical obstacles encountered during the evolution of the NLP-to-MES-SQL Chatbot and the engineering strategies implemented to overcome them.

## 1. Metric Definition & Hallucination
**The Challenge:** 
The LLM frequently "hallucinated" column names (e.g., assuming a column named `oee` or `duration` existed) based on its general training data rather than the actual provided database schema. This led to SQL queries that failed immediately upon execution.

**The Solution:**
*   **Smart Schema Analysis:** Implemented a pre-processor (`_analyze_mes_schema`) that scans the physical database schema for synonyms and keywords.
*   **Explicit Hint Injection:** The results of the scan are injected into the prompt as "Ground Truth" hints, telling the LLM exactly which columns represent Production Time, Downtime, and Defects.
*   **Strict SQL Guardrails:** Added a post-generation validation layer that extracts table names from the generated SQL and cross-references them with the actual schema. If a hallucination is detected, the system automatically falls back to a deterministic Heuristic Engine.

## 2. Mathematical Precision in KPI Formulas
**The Challenge:**
Standard SQL math often led to "Double Multiplication" (multiplying by 100 twice) or "Sum of Percentages" errors. Dividing by zero during downtime fluctuations also caused the entire backend to crash with database errors.

**The Solution:**
*   **Standardized Operator Protocol:** Enforced a strict PEMDAS (Parentheses first) protocol in the LLM instructions: `ROUND((numerator / NULLIF(denominator, 0)) * 100, 2)`.
*   **Zero-Division Protection:** Every division operation is now programmatically wrapped with `NULLIF(den, 0)` to ensure queries return `NULL` instead of crashing.
*   **Aggregation First:** The prompt was updated to forbid summing percentages. Instead, the AI is forced to aggregate the raw data (SUM of numerator / SUM of denominator) first.

## 3. Date Filtering logic (AND vs OR)
**The Challenge:**
When users asked for multiple months (e.g., "January and February"), the LLM would generate a `WHERE` clause with an `AND` operator between two dates. This resulted in an empty dataset (0 rows) because no single record can exist in both January and February simultaneously.

**The Solution:**
*   **Date Prototype Logic:** Updated the `DATE FILTER RULES` in the system prompt to include a multi-month protocol.
*   **Logical Correction:** The AI is now instructed to use `OR` logic wrapped in parentheses: `((date >= 'Jan-01' AND date < 'Feb-01') OR (date >= 'Feb-01' AND date < 'Mar-01'))`.

## 4. Time Unit Discrepancies
**The Challenge:**
Physical machines log data in various units (Seconds, Minutes, Milliseconds). The LLM would often mix these up, for example, subtracting 600 seconds of downtime from 8 hours of production time without normalization, leading to impossible OEE percentages (e.g., negative or >1000%).

**The Solution:**
*   **Automatic Unit Detection:** The pre-processor detects column suffixes (like `_min`, `_sec`, `_ms`) from the live schema.
*   **Unit Normalization Prompt:** The LLM is given specific "Time Unit Handling" rules to check suffixes and convert all values to the same unit (typically Minutes) before performing any subtraction or ratio calculations.

---
*Created on: 2026-03-05*
