import os
import re
import difflib
from datetime import datetime
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple

# RAG Service for schema retrieval
from .rag import rag_service

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

# --- CONFIGURATION (Loaded from Environment) ---
API_KEY = os.getenv("LLM_API_KEY")
API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")


# ─────────────────────────────────────────────
# FILLER / STOP WORDS to ignore during parsing
# ─────────────────────────────────────────────
FILLER_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "please", "show", "tell", "give", "display", "list", "get", "find",
    "fetch", "retrieve", "can", "you", "me", "my", "i", "want", "need",
    "would", "like", "to", "see", "view", "know", "let", "check",
    "what", "which", "who", "whom", "how", "do", "does", "did",
    "from", "in", "of", "on", "at", "for", "with", "by", "about",
    "there", "their", "out", "up", "it", "its", "this", "that",
    "these", "those", "here", "where", "when", "just", "only",
    "also", "too", "so", "if", "or", "and", "but", "not", "no",
    "yes", "ok", "okay", "sure", "right", "all", "every", "each",
    "some", "any", "many", "much", "more", "most", "few",
    "has", "have", "had", "having", "will", "shall", "should",
    "could", "might", "may", "must", "vs", "than",
}

# ────────────────────────────────
# INTENT KEYWORDS
# ────────────────────────────────
COUNT_KEYWORDS = ["count", "how many", "number of", "total number", "hw many", "howmany", "cnt", "num of"]
SUM_KEYWORDS = ["sum", "total amount", "total items", "total value", "total of", "grand total", "sum of"]
AVG_KEYWORDS = ["average", "avg", "mean"]
MIN_KEYWORDS = ["minimum", "min", "lowest", "smallest", "least"]
MAX_KEYWORDS = ["maximum", "max", "highest", "largest", "greatest", "biggest", "most expensive", "top value"]
LIST_KEYWORDS = ["list", "show", "display", "give", "tell", "get", "fetch", "lst", "shw", "giv", "view", "see", "retrieve"]
META_TABLE_KEYWORDS = ["table", "tables", "database", "schema", "structure", "db"]

# Words that follow "total" to indicate SUM rather than COUNT
TOTAL_SUM_FOLLOWERS = {"amount", "value", "items", "price", "cost", "revenue", "sales", "quantity", "sum", "of"}

# Common typo corrections for SQL-related words
TYPO_MAP = {
    "usrs": "users", "usr": "users", "usres": "users", "uers": "users", "uesrs": "users",
    "prodcts": "products", "prducts": "products", "produt": "products", "prdcts": "products",
    "custmers": "customers", "custmer": "customers", "customrs": "customers", "customes": "customers",
    "studnts": "students", "stdnts": "students", "studens": "students", "studets": "students",
    "ordrs": "orders", "oder": "orders", "oders": "orders", "ordes": "orders",
    "nme": "name", "nmes": "names", "naem": "name", "nmae": "name",
    "emal": "email", "emial": "email", "eamil": "email",
    "cty": "city", "citys": "cities", "citi": "city",
    "dept": "department", "deparment": "department", "departmnt": "department",
    "amout": "amount", "amnt": "amount", "ammount": "amount",
    "totl": "total", "ttal": "total",
    "gretaer": "greater", "graeter": "greater",
    "lss": "less", "les": "less",
    "shw": "show", "shwo": "show", "sho": "show",
    "giv": "give", "gve": "give",
    "lst": "list", "lis": "list",
    "hw": "how", "howw": "how",
    "pencl": "pencil", "pencel": "pencil", "pencol": "pencil",
    "brought": "bought", "brougt": "bought", "broght": "bought",
    "chenai": "chennai", "chenni": "chennai",
}


class NLPEngine:
    def __init__(self):
        self.client = None
        if API_KEY and "PASTE" not in API_KEY:
            try:
                self.client = OpenAI(api_key=API_KEY, base_url=API_URL)
                print(f"Llama 3 (70B) initialized via {API_URL}")
            except Exception as e:
                print(f"Failed to initialize LLM client: {e}")

    # ──────────────────────────────
    # SECURITY: SELECT-only guard
    # ──────────────────────────────
    def _validate_sql_safety(self, sql: str) -> Tuple[bool, str]:
        """Validates that SQL query is read-only (SELECT only)."""
        sql_upper = sql.upper().strip()

        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
            "CREATE", "REPLACE", "MERGE", "GRANT", "REVOKE",
            "EXEC", "EXECUTE", "CALL", "PRAGMA"
        ]

        for keyword in forbidden_keywords:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False, f"🚫 Security Error: '{keyword}' operations are not allowed. Only SELECT queries are permitted."

        sql_clean = re.sub(r"--.*", "", sql_upper).strip()
        if not sql_clean.startswith("SELECT"):
            return False, "🚫 Security Error: Only SELECT queries are allowed. No data modifications permitted."

        return True, ""

    # ──────────────────────────────
    # COLUMN VALIDATION
    # ──────────────────────────────
    def _validate_sql_columns(self, sql: str, schema: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
        """Validates that all table.column references in the SQL actually exist in the schema.
        Returns (is_valid, error_message, list_of_bad_refs)."""
        # Build a lookup: table_name_lower -> set of column_names_lower
        schema_lookup = {}
        for t in schema:
            cols = {c["name"].lower() for c in t["columns"]}
            schema_lookup[t["name"].lower()] = cols

        # Remove string literals and comments to avoid false positives
        clean_sql = re.sub(r"'[^']*'", "''", sql)  # remove string values
        clean_sql = re.sub(r"--.*", "", clean_sql)   # remove comments
        clean_sql = re.sub(r'[`"\[\]]', '', clean_sql)  # remove quotes

        # Extract alias -> table mapping from FROM/JOIN clauses
        # Pattern: table_name alias  or  table_name AS alias
        alias_map = {}  # alias_lower -> table_name_lower
        # Match: FROM table_name alias, JOIN table_name alias, FROM table_name AS alias
        alias_patterns = re.findall(
            r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+ON|\s+WHERE|\s+LEFT|\s+RIGHT|\s+INNER|\s+OUTER|\s+CROSS|\s+JOIN|\s+GROUP|\s+ORDER|\s+LIMIT|\s*$|\s*,)',
            clean_sql,
            re.IGNORECASE
        )
        for table_name, alias in alias_patterns:
            tn = table_name.lower()
            al = alias.lower()
            # Skip if the "alias" is actually a SQL keyword
            sql_keywords = {'on', 'where', 'left', 'right', 'inner', 'outer', 'cross', 'join',
                           'group', 'order', 'having', 'limit', 'union', 'select', 'and', 'or'}
            if al not in sql_keywords and tn in schema_lookup:
                alias_map[al] = tn
            # Also map full table name to itself
            if tn in schema_lookup:
                alias_map[tn] = tn

        # Extract all alias.column references
        col_refs = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b', clean_sql)
        
        bad_refs = []
        for table_or_alias, col_name in col_refs:
            ta_lower = table_or_alias.lower()
            cn_lower = col_name.lower()
            
            # Resolve alias to actual table name
            actual_table = alias_map.get(ta_lower)
            if actual_table is None:
                continue  # Unknown alias, skip (might be a subquery alias)
            
            # Check if the column exists in this table
            if actual_table in schema_lookup:
                if cn_lower not in schema_lookup[actual_table]:
                    # Build helpful error message
                    valid_cols = sorted(schema_lookup[actual_table])
                    bad_refs.append(f"{table_or_alias}.{col_name} (table '{actual_table}' has columns: {', '.join(valid_cols)})")

        if bad_refs:
            return False, f"Invalid column references: {'; '.join(bad_refs)}", bad_refs
        
        return True, "", []

    # ──────────────────────────────
    # TYPO CORRECTION
    # ──────────────────────────────
    def _fix_typos(self, text: str) -> str:
        """Fix common typos using the typo map and fuzzy matching."""
        words = text.split()
        corrected = []
        
        # Get all words from TYPO_MAP keys for fuzzy matching
        typo_keys = list(TYPO_MAP.keys())
        
        for w in words:
            low_w = w.lower()
            # 1. Exact match in TYPO_MAP
            if low_w in TYPO_MAP:
                corrected.append(TYPO_MAP[low_w])
                continue
                
            # 2. Fuzzy match against TYPO_MAP keys (high confidence)
            close_typos = difflib.get_close_matches(low_w, typo_keys, n=1, cutoff=0.8)
            if close_typos:
                corrected.append(TYPO_MAP[close_typos[0]])
                continue
            
            # 3. No match, keep original
            corrected.append(w)
            
        return " ".join(corrected)

    # ──────────────────────────────
    # INTENT DETECTION
    # ──────────────────────────────
    def _detect_intent(self, query: str) -> str:
        """
        Detect the primary intent from the query.
        Returns: 'count', 'sum', 'avg', 'min', 'max', 'list', 'meta_tables', or 'unknown'
        """
        q = query.lower()

        # Meta: asking about tables/schema
        has_list = any(w in q for w in LIST_KEYWORDS)
        has_table = any(w in q for w in META_TABLE_KEYWORDS)
        if has_list and has_table and not self._has_data_table_mention(q):
            return "meta_tables"

        # Check SUM FIRST (more specific multi-word patterns like "total amount")
        for kw in SUM_KEYWORDS:
            if kw in q:
                return "sum"

        # Check COUNT (single-word patterns like "count", "how many")
        for kw in COUNT_KEYWORDS:
            if kw in q:
                return "count"

        # Handle bare "total" — SUM if followed by a sum-like word, else COUNT
        if "total" in q:
            words = q.split()
            for i, w in enumerate(words):
                if w == "total" and i + 1 < len(words) and words[i + 1] in TOTAL_SUM_FOLLOWERS:
                    return "sum"
            return "count"  # bare "total" with no sum-follower = count

        for kw in AVG_KEYWORDS:
            if kw in q:
                return "avg"
        for kw in MIN_KEYWORDS:
            if kw in q:
                return "min"
        for kw in MAX_KEYWORDS:
            if kw in q:
                return "max"

        return "list"  # default: retrieve rows

    def _has_data_table_mention(self, query: str) -> bool:
        """Check if query mentions any actual data table (not meta words)."""
        # Will be checked against dynamic schema later; simple keyword check here
        data_words = ["users", "user", "customers", "customer", "students", "student",
                       "orders", "order", "products", "product", "info", "items"]
        return any(w in query for w in data_words)

    # ──────────────────────────────
    # SCHEMA-AWARE TABLE DETECTION
    # ──────────────────────────────
    def _find_tables(self, query: str, schema: List[Dict]) -> Dict[str, Dict]:
        """Find all tables mentioned in the query — supports fuzzy/plural matching."""
        found = {}
        q = query.lower()

        for table in schema:
            t_name = table["name"].lower()     
            t_singular = t_name.rstrip("s") if t_name.endswith("s") else t_name

            # Direct or singular match
            if re.search(rf"\b{re.escape(t_name)}\b", q) or re.search(rf"\b{re.escape(t_singular)}\b", q):
                found[table["name"]] = table
                continue

            # Alias mapping: common synonym detection
            aliases = self._get_table_aliases(t_name)
            match_found = False
            for alias in aliases:
                if re.search(rf"\b{re.escape(alias)}\b", q):
                    found[table["name"]] = table
                    match_found = True
                    break
            
            if match_found:
                continue

            # Column mention as a hint for table
            for col in table["columns"]:
                c_name = col["name"].lower()
                if re.search(rf"\b{re.escape(c_name)}\b", q):
                    # Skip very generic matches unless table is already likely
                    if c_name in ("id", "name", "type", "city", "email"):
                        # If query has "per [column]", then it's a strong hint
                        if re.search(rf"(?:per|each|by)\s+{re.escape(c_name)}", q):
                             found[table["name"]] = table
                             break
                        continue
                    found[table["name"]] = table
                    break

        return found

    def _get_table_aliases(self, table_name: str) -> List[str]:
        """Return common aliases for known table names."""
        alias_map = {
            "users": ["person", "people", "user", "usr", "usrs", "who", "names"],
            "customers": ["customer", "client", "clients", "buyer", "buyers", "custmer", "custmers"],
            "students": ["student", "stdnt", "studnt", "stdnts", "studnts", "pupil", "pupils"],
            "orders": ["order", "purchase", "purchases", "oder", "oders", "ordrs", "transaction", "transactions"],
            "user_products": ["product", "products", "item", "items", "purchase", "purchases", "bought", "brought", "purchased", "prodcts", "prdcts"],
            "users_info": ["user info", "user detail", "user details", "profile", "profiles",
                            "location", "locations", "users info", "details of user", "user profile"],
        }
        return alias_map.get(table_name, [])

    # ──────────────────────────────
    # COLUMN DETECTION
    # ──────────────────────────────
    def _find_columns(self, query: str, found_tables: Dict[str, Dict], schema: List[Dict]) -> List[str]:
        """Detect which specific columns the user is asking about."""
        q = query.lower()
        columns = []

        search_tables = list(found_tables.values()) if found_tables else schema

        # Collect table name words to avoid treating table-reference words as column selections
        table_words = set()
        for t in schema:
            tn = t["name"].lower()
            table_words.add(tn)
            table_words.add(tn.rstrip("s"))
            for alias in self._get_table_aliases(tn):
                table_words.update(alias.split())

        for table in search_tables:
            for col in table["columns"]:
                c_name = col["name"].lower()

                # Skip internal columns unless explicitly mentioned
                if c_name in ("password_hash",):
                    continue

                # Direct match
                if re.search(rf"\b{re.escape(c_name)}s?\b", q):
                    # Context check: don't let "name" in "product name" wrongly trigger users table
                    if c_name == "name" and re.search(r"\b(product|item)\s+names?\b", q):
                        if table["name"] not in ("user_products",):
                            continue

                    # ID columns only if explicitly mentioned
                    if c_name in ("id", "user_id", "customer_id") and not re.search(r"\bids?\b", q):
                        continue

                    # Skip if the column name is the same word used to reference the table
                    # e.g., "product" column shouldn't be selected when user says "list all products"
                    if c_name in table_words or c_name.rstrip("s") in table_words:
                        # Only skip if it's not specifically used as a column reference
                        # e.g., "show product names" should detect "product" as table, "name" as column
                        if not re.search(rf"\b{re.escape(c_name)}s?\s+(name|detail|info|column)", q):
                            continue

                    columns.append(f"{table['name']}.{col['name']}")
                    continue

                # Plural/singular variations (city → cities, etc.)
                if c_name.endswith("y") and re.search(rf"\b{re.escape(c_name[:-1])}ies\b", q):
                    columns.append(f"{table['name']}.{col['name']}")
                    continue

                # "username" ↔ "name" bidirectional match
                if c_name == "username" and re.search(r"\bnames?\b", q):
                    columns.append(f"{table['name']}.{col['name']}")
                elif c_name == "name" and re.search(r"\busernames?\b", q):
                    columns.append(f"{table['name']}.{col['name']}")

        return list(dict.fromkeys(columns))  # unique, preserving order

    # ──────────────────────────────
    # FILTER (WHERE) DETECTION
    # ──────────────────────────────
    def _detect_filters(self, query: str, found_tables: Dict[str, Dict], schema: List[Dict]) -> List[str]:
        """Detect WHERE clause conditions from the query."""
        q = query.lower()
        wheres = []

        search_tables = list(found_tables.values()) if found_tables else schema

        # Collect metadata to avoid using table/col names as filter values
        all_table_names = set()
        all_col_names = set()
        for t in schema:
            tn = t["name"].lower()
            all_table_names.update([tn, tn.rstrip("s"), tn + "s"])
            for c in t["columns"]:
                cn = c["name"].lower()
                all_col_names.update([cn, cn.rstrip("s"), cn + "s"])
                if cn.endswith("y"):
                    all_col_names.add(cn[:-1] + "ies")

        stops = FILLER_WORDS | all_table_names | all_col_names | {
            "records", "everything", "alone", "simply", "quantity", "amount",
            "number", "count", "sum", "total", "average", "avg", "minimum",
            "min", "maximum", "max", "live", "lives", "living", "whose",
            "details", "named", "called", "info", "information", "record",
            "detail", "bought", "purchase", "limit", "top", "first",
        }

        # ── Numeric filters ──
        num_patterns = [
            (r"(?:more than|greater than|above|over|>)\s*(\d+(?:\.\d+)?)", ">"),
            (r"(?:less than|smaller than|below|under|<)\s*(\d+(?:\.\d+)?)", "<"),
            (r"(?:exactly|equal to|equals|=)\s*(\d+(?:\.\d+)?)", "="),
            (r"(?:at least|>=)\s*(\d+(?:\.\d+)?)", ">="),
            (r"(?:at most|<=)\s*(\d+(?:\.\d+)?)", "<="),
        ]

        for pattern, op in num_patterns:
            m = re.search(pattern, q)
            if m:
                value = m.group(1)
                # Detect which numeric column this refers to
                num_col = self._find_best_numeric_column(q, search_tables)
                if num_col:
                    wheres.append(f"{num_col} {op} {value}")
                    # Ensure the table is in found_tables
                    t_name = num_col.split(".")[0]
                    for t in schema:
                        if t["name"] == t_name:
                            found_tables[t_name] = t

        # ── GPA-specific patterns ──
        gpa_match = re.search(r"\bgpa\s*(?:>|greater than|more than|above|over)\s*(\d+(?:\.\d+)?)", q)
        if not gpa_match:
            gpa_match = re.search(r"(?:>|greater than|more than|above|over)\s*(\d+(?:\.\d+)?)\s*gpa", q)
        if gpa_match and not any("gpa" in w for w in wheres):
            for t in search_tables:
                if any(c["name"].lower() == "gpa" for c in t["columns"]):
                    wheres.append(f"{t['name']}.gpa > {gpa_match.group(1)}")
                    found_tables[t["name"]] = t
                    break

        # ── ID filtering: "id 1", "id is 5" ──
        id_match = re.search(r"\bids?\s*(?:is|:|=)?\s*(\d+)\b", q)
        if id_match:
            id_val = id_match.group(1)
            if found_tables:
                first_table = list(found_tables.keys())[0]
                wheres.append(f"{first_table}.id = {id_val}")

        # ── Text value detection (e.g., "Chennai", "Pen", "Alice") ──
        words = re.findall(r"\b\w+\b", q)
        used_words = set()

        for word in words:
            if word in used_words or word in stops or len(word) <= 2:
                continue
            # Skip numbers (handled above)
            if word.isdigit():
                continue
            # Skip close matches to stop words
            close = difflib.get_close_matches(word, list(stops), n=1, cutoff=0.8)
            if close:
                continue

            best_col = self._find_best_text_column(word, q, search_tables)
            if best_col:
                wheres.append(f"LOWER({best_col}) = '{word}'")
                used_words.add(word)
                t_name = best_col.split(".")[0]
                for t in schema:
                    if t["name"] == t_name:
                        found_tables[t_name] = t

        # ── LIKE / SEARCH detection ──
        if any(kw in q for kw in ["starts with", "begins with"]):
            for i, w in enumerate(wheres):
                if "LOWER(" in w and "= '" in w:
                    wheres[i] = re.sub(r"= '([^']+)'", r"LIKE '\1%'", w)
        elif any(kw in q for kw in ["contains", "includes", "has"]):
            for i, w in enumerate(wheres):
                if "LOWER(" in w and "= '" in w:
                    wheres[i] = re.sub(r"= '([^']+)'", r"LIKE '%\1%'", w)

        return wheres

    def _find_best_numeric_column(self, query: str, tables: List[Dict]) -> Optional[str]:
        """Find the best numeric column for a comparison."""
        q = query.lower()
        # Priority: explicitly mentioned numeric column names
        numeric_types = {"INTEGER", "INT", "REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL", "NUMBER"}

        # Check if a specific column name is mentioned
        for table in tables:
            for col in table["columns"]:
                c_name = col["name"].lower()
                c_type = str(col["type"]).upper()
                if any(nt in c_type for nt in numeric_types) and c_name not in ("id", "user_id", "customer_id"):
                    if re.search(rf"\b{re.escape(c_name)}\b", q):
                        return f"{table['name']}.{col['name']}"

        # Fallback: first numeric non-ID column
        for table in tables:
            for col in table["columns"]:
                c_type = str(col["type"]).upper()
                c_name = col["name"].lower()
                if any(nt in c_type for nt in numeric_types) and c_name not in ("id", "user_id", "customer_id"):
                    return f"{table['name']}.{col['name']}"

        return None

    def _find_best_text_column(self, word: str, query: str, tables: List[Dict]) -> Optional[str]:
        """Find the best text column to match a filter value against."""
        q = query.lower()

        # 1. Explicit pattern: "[column] is [word]" or "[column] [word]"
        for table in tables:
            for col in table["columns"]:
                c_name = col["name"].lower()
                if re.search(rf"\b{re.escape(c_name)}\b\s+(?:is\s+)?{re.escape(word)}", q):
                    return f"{table['name']}.{col['name']}"

        # 2. Contextual: "named [word]" or "called [word]"
        if re.search(rf"\b(?:named|called|is)\b\s+{re.escape(word)}", q):
            for table in tables:
                col_names = [c["name"].lower() for c in table["columns"]]
                if "name" in col_names:
                    return f"{table['name']}.name"
                if "username" in col_names:
                    return f"{table['name']}.username"

        # 3. Location: "from [word]" or "in [word]" or "lives in [word]"
        if re.search(rf"\b(?:from|in|at|living in|lives in)\b\s+{re.escape(word)}", q):
            for table in tables:
                col_names = [c["name"].lower() for c in table["columns"]]
                if "city" in col_names:
                    return f"{table['name']}.city"
                if "location" in col_names:
                    return f"{table['name']}.location"
                if "address" in col_names:
                    return f"{table['name']}.address"

        # 4. Department: "from [word]" with department column or "[word] department/dept"
        if re.search(rf"\b(?:department|dept)\b", q) or re.search(rf"\b{re.escape(word)}\s+(?:department|dept|students?)\b", q):
            for table in tables:
                col_names = [c["name"].lower() for c in table["columns"]]
                if "department" in col_names:
                    return f"{table['name']}.department"

        # 5. Known city names
        city_names = {"chennai", "mumbai", "delhi", "bangalore", "hyderabad", "pune", "kolkata",
                      "london", "paris", "nyc", "new york", "tokyo", "berlin", "sydney"}
        if word in city_names:
            for table in tables:
                col_names = [c["name"].lower() for c in table["columns"]]
                if "city" in col_names:
                    return f"{table['name']}.city"

        # 6. Fallback: first TEXT/VARCHAR column (not ID-like)
        for table in tables:
            for col in table["columns"]:
                c_type = str(col["type"]).upper()
                c_name = col["name"].lower()
                if any(t in c_type for t in ["TEXT", "CHAR", "VARCHAR"]) and c_name not in ("password_hash", "email"):
                    return f"{table['name']}.{col['name']}"

        return None

    # ──────────────────────────────
    # JOIN BUILDER
    # ──────────────────────────────
    def _build_join(self, t1: Dict, t2: Dict) -> Optional[str]:
        """Build a JOIN clause between two tables."""
        t1n = t1["name"].lower()
        t2n = t2["name"].lower()

        # 1. Foreign key based
        for col in t1["columns"]:
            if "foreign_key" in col and col["foreign_key"].startswith(t2["name"]):
                target_pk = col["foreign_key"].split(".")[1]
                return f"{t1['name']}.{col['name']} = {t2['name']}.{target_pk}"

        for col in t2["columns"]:
            if "foreign_key" in col and col["foreign_key"].startswith(t1["name"]):
                target_pk = col["foreign_key"].split(".")[1]
                return f"{t2['name']}.{col['name']} = {t1['name']}.{target_pk}"

        # 2. Convention-based (e.g., users.id = orders.user_id)
        t1_singular = t1n.rstrip("s") if t1n.endswith("s") else t1n
        t2_singular = t2n.rstrip("s") if t2n.endswith("s") else t2n
        t1_cols = [c["name"].lower() for c in t1["columns"]]
        t2_cols = [c["name"].lower() for c in t2["columns"]]

        if f"{t1_singular}_id" in t2_cols:
            return f"{t1['name']}.id = {t2['name']}.{t1_singular}_id"
        if f"{t2_singular}_id" in t1_cols:
            return f"{t2['name']}.id = {t1['name']}.{t2_singular}_id"
        if "user_id" in t2_cols and t1n in ("users", "customers"):
            return f"{t1['name']}.id = {t2['name']}.user_id"
        if "user_id" in t1_cols and t2n in ("users", "customers"):
            return f"{t2['name']}.id = {t1['name']}.user_id"
        if "customer_id" in t2_cols and t1n in ("customers",):
            return f"{t1['name']}.id = {t2['name']}.customer_id"
        if "customer_id" in t1_cols and t2n in ("customers",):
            return f"{t2['name']}.id = {t1['name']}.customer_id"

        # 3. ID-to-ID (e.g., users.id = users_info.id)
        if "id" in t1_cols and "id" in t2_cols:
            return f"{t1['name']}.id = {t2['name']}.id"

        return None

    # ──────────────────────────────
    # GROUP BY DETECTION
    # ──────────────────────────────
    def _detect_group_by(self, query: str, target_columns: List[str], found_tables: Dict) -> Optional[str]:
        """Detect GROUP BY clause."""
        q = query.lower()

        if "per " not in q and "each " not in q and "group by" not in q and "by " not in q:
            return None

        # "per city" → GROUP BY city
        group_match = re.search(r"(?:per|each|by)\s+(\w+)", q)
        if group_match:
            group_word = group_match.group(1).rstrip("s")
            
            # 1. Match to an actual column
            for t in found_tables.values():
                for c in t["columns"]:
                    c_name = c["name"].lower()
                    if c_name == group_word or c_name == group_match.group(1):
                        return f"{t['name']}.{c['name']}"
                    # Match ID columns (e.g. "per user" -> "user_id")
                    if c_name == f"{group_word}_id":
                        return f"{t['name']}.{c_name}"

            # 2. Match to a table name (singular or plural)
            for t_name, t in found_tables.items():
                t_lower = t_name.lower()
                if t_lower == group_word or t_lower.rstrip("s") == group_word or t_lower == group_match.group(1):
                    # Prefer primary key or foreign key in this table
                    cols = [c["name"].lower() for c in t["columns"]]
                    if "id" in cols:
                        return f"{t['name']}.id"
                    if f"{group_word}_id" in cols:
                        return f"{t['name']}.{group_word}_id"

        # 3. Specific entity fallback (highly common)
        if "per user" in q or "each user" in q or "by user" in q:
             for t in found_tables.values():
                 cols = [c["name"].lower() for c in t["columns"]]
                 if "user_id" in cols:
                     return f"{t['name']}.user_id"
                 if "id" in cols and t["name"].lower() == "users":
                     return f"{t['name']}.id"

        # Fallback: first target column
        if target_columns:
            return target_columns[0]

        return None

    # ──────────────────────────────
    # SORT / LIMIT DETECTION
    # ──────────────────────────────
    def _detect_order_and_limit(self, query: str) -> Tuple[Optional[str], Optional[int]]:
        """Detect ORDER BY and LIMIT."""
        q = query.lower()
        order = None
        limit = None

        # Limit
        l_match = re.search(r"(?:top|limit|first)\s*(\d+)", q)
        if l_match:
            limit = int(l_match.group(1))

        # Order
        if any(kw in q for kw in ["order by", "ordered by", "sort", "ascending", "descending",
                                    "highest", "lowest", "top", "bottom"]):
            if any(kw in q for kw in ["descending", "desc", "highest", "top", "maximum", "most", "largest"]):
                order = "DESC"
            elif any(kw in q for kw in ["ascending", "asc", "lowest", "least", "smallest"]):
                order = "ASC"
            else:
                order = ""  # default ordering

        return order, limit

    # ──────────────────────────────
    # PROJECTION BUILDER
    # ──────────────────────────────
    def _build_projection(self, intent: str, query: str, target_columns: List[str],
                           found_tables: Dict, group_by: Optional[str]) -> str:
        """Build the SELECT projection."""
        q = query.lower()

        if intent == "count":
            if group_by:
                return f"{group_by}, COUNT(*)"
            return "COUNT(*)"

        if intent == "sum":
            # Find a numeric column to sum
            for t in found_tables.values():
                for c in t["columns"]:
                    c_type = str(c["type"]).upper()
                    c_name = c["name"].lower()
                    if any(nt in c_type for nt in ["REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL", "INTEGER", "INT"]):
                        if c_name not in ("id", "user_id", "customer_id"):
                            col_ref = f"{t['name']}.{c['name']}"
                            if group_by:
                                return f"{group_by}, SUM({col_ref})"
                            return f"SUM({col_ref})"
            return "SUM(*)"

        if intent == "avg":
            for t in found_tables.values():
                for c in t["columns"]:
                    c_type = str(c["type"]).upper()
                    c_name = c["name"].lower()
                    if any(nt in c_type for nt in ["REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL", "INTEGER", "INT"]):
                        if c_name not in ("id", "user_id", "customer_id"):
                            col_ref = f"{t['name']}.{c['name']}"
                            if group_by:
                                return f"{group_by}, AVG({col_ref})"
                            return f"AVG({col_ref})"
            return "AVG(*)"

        if intent == "min":
            for t in found_tables.values():
                for c in t["columns"]:
                    c_type = str(c["type"]).upper()
                    c_name = c["name"].lower()
                    if any(nt in c_type for nt in ["REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL", "INTEGER", "INT"]):
                        if c_name not in ("id", "user_id", "customer_id"):
                            return f"MIN({t['name']}.{c['name']})"
            return "MIN(*)"

        if intent == "max":
            for t in found_tables.values():
                for c in t["columns"]:
                    c_type = str(c["type"]).upper()
                    c_name = c["name"].lower()
                    if any(nt in c_type for nt in ["REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL", "INTEGER", "INT"]):
                        if c_name not in ("id", "user_id", "customer_id"):
                            return f"MAX({t['name']}.{c['name']})"
            return "MAX(*)"

        # List / select intent
        if not target_columns:
            return "*"

        # Determine if user wants specific columns or all data
        is_restrictive = any(w in q for w in ["only", "just", "specifically", "restricted to"])
        has_broad_keyword = any(w in q for w in ["all", "details", "everything", "records", "complete", "full"])

        # Count how many column names are explicitly mentioned
        explicit_mentions = 0
        for col_ref in target_columns:
            col_name = col_ref.split(".")[-1].lower()
            if re.search(rf"\b{re.escape(col_name)}s?\b", q):
                if col_name not in ("id",):  # skip very generic matches
                    explicit_mentions += 1

        if has_broad_keyword and not is_restrictive and explicit_mentions == 0:
            return "*"

        if explicit_mentions > 0 or is_restrictive:
            return ", ".join(target_columns)

        return "*"

    # ──────────────────────────────────────────────────────
    # SMART SCHEMA ANALYZER FOR MES
    # ──────────────────────────────────────────────────────
    def _analyze_mes_schema(self, schema: List[Dict[str, Any]]) -> str:
        """
        Analyzes the actual database schema to auto-detect MES-relevant columns.
        Returns a text block that tells the LLM which actual columns to use.
        """
        hints = []
        
        # Define patterns to detect MES-relevant columns
        time_patterns = {
            'production_time': ['production_time', 'planned_time', 'operating_time', 'run_time', 'runtime', 'prod_time', 'total_time', 'available_time'],
            'downtime': ['downtime', 'down_time', 'breakdown', 'idle_time', 'stop_time', 'stoppage'],
            'units_produced': ['units_produced', 'produced_qty', 'output_qty', 'quantity_produced', 'total_produced', 'production_qty', 'good_count', 'output_count', 'total_output'],
            'defects': ['defects', 'defect', 'reject_qty', 'rejects', 'defective', 'scrap', 'bad_qty', 'reject_count', 'scrap_qty', 'bad_count', 'ng_count'],
            'good_qty': ['good_qty', 'good_count', 'ok_qty', 'pass_qty', 'passed_count'],
            'machine_id': ['machine_id', 'equipment_id', 'asset_id', 'machine_no', 'equipment_no'],
            'date_col': ['production_date', 'log_time', 'timestamp', 'date', 'created_at', 'record_date', 'work_date', 'shift_date', 'log_date'],
            'shift': ['shift', 'shift_id', 'shift_name', 'shift_no'],
            'machine_name': ['machine_name', 'equipment_name', 'asset_name'],
        }
        
        # Time unit detection patterns
        time_unit_hints = {
            'hours': ['_hours', '_hrs', '_hr'],
            'minutes': ['_min', '_minutes', '_mins'],
            'seconds': ['_seconds', '_sec', '_secs'],
            'milliseconds': ['_ms', '_milliseconds', '_millis'],
        }
        
        found = {}  # category -> [(table, column, time_unit)]
        
        for table in schema:
            table_name = table['name']
            for col in table['columns']:
                col_name = col['name'].lower()
                col_name_full = col['name']
                
                for category, patterns in time_patterns.items():
                    for pattern in patterns:
                        if pattern in col_name:
                            # Detect time unit if this is a time-related column
                            time_unit = None
                            if category in ['production_time', 'downtime']:
                                for unit, suffixes in time_unit_hints.items():
                                    for suffix in suffixes:
                                        if suffix in col_name:
                                            time_unit = unit
                                            break
                                    if time_unit:
                                        break
                                if not time_unit:
                                    # Check the column type for hints
                                    col_type = str(col.get('type', '')).lower()
                                    if 'time' in col_type or 'interval' in col_type:
                                        time_unit = 'unknown'
                                    else:
                                        time_unit = 'unknown (check data)'
                            
                            if category not in found:
                                found[category] = []
                            found[category].append((table_name, col_name_full, time_unit))
                            break
        
        # Build hints text
        if found:
            hints.append("📋 SCHEMA ANALYSIS HINTS (auto-detected from your database):")
            
            if 'production_time' in found:
                for table, col, unit in found['production_time']:
                    unit_note = f" (unit: {unit})" if unit else ""
                    hints.append(f"  - Production Time: `{table}`.`{col}`{unit_note}")
            
            if 'downtime' in found:
                for table, col, unit in found['downtime']:
                    unit_note = f" (unit: {unit})" if unit else ""
                    hints.append(f"  - Downtime: `{table}`.`{col}`{unit_note}")
            
            if 'units_produced' in found:
                for table, col, _ in found['units_produced']:
                    hints.append(f"  - Units Produced: `{table}`.`{col}`")
            
            if 'defects' in found:
                for table, col, _ in found['defects']:
                    hints.append(f"  - Defects/Scrap: `{table}`.`{col}`")
            
            if 'good_qty' in found:
                for table, col, _ in found['good_qty']:
                    hints.append(f"  - Good Quantity: `{table}`.`{col}`")
            
            if 'machine_id' in found:
                for table, col, _ in found['machine_id']:
                    hints.append(f"  - Machine ID: `{table}`.`{col}`")
            
            if 'machine_name' in found:
                for table, col, _ in found['machine_name']:
                    hints.append(f"  - Machine Name: `{table}`.`{col}`")
            
            if 'date_col' in found:
                for table, col, _ in found['date_col']:
                    hints.append(f"  - Date Column: `{table}`.`{col}`")
            
            if 'shift' in found:
                for table, col, _ in found['shift']:
                    hints.append(f"  - Shift: `{table}`.`{col}`")
            
            # Add time unit conversion warnings
            prod_times = found.get('production_time', [])
            downtimes = found.get('downtime', [])
            if prod_times and downtimes:
                prod_unit = prod_times[0][2]
                down_unit = downtimes[0][2]
                if prod_unit and down_unit and prod_unit != down_unit and prod_unit != 'unknown' and down_unit != 'unknown':
                    hints.append(f"  ⚠️ TIME UNIT MISMATCH: Production time is in {prod_unit} but downtime is in {down_unit}.")
                    hints.append(f"     You MUST convert them to the same unit before calculating Availability or OEE.")
                    if prod_unit == 'hours' and down_unit == 'minutes':
                        hints.append(f"     Convert downtime to hours: `{downtimes[0][1]}` / 60")
                    elif prod_unit == 'minutes' and down_unit == 'hours':
                        hints.append(f"     Convert downtime to minutes: `{downtimes[0][1]}` * 60")
            
            # Detect join keys
            hints.append("  🔗 Detected JOIN keys:")
            all_columns = {}
            for table in schema:
                for col in table['columns']:
                    col_lower = col['name'].lower()
                    if col_lower not in all_columns:
                        all_columns[col_lower] = []
                    all_columns[col_lower].append(table['name'])
            
            for col_name, tables in all_columns.items():
                if len(tables) > 1 and ('_id' in col_name or col_name == 'id'):
                    hints.append(f"    - `{col_name}` appears in: {', '.join(tables)}")
        
        return "\n                ".join(hints) if hints else "No specific MES column patterns detected. Analyze the SCHEMA section to determine correct columns."

    # ──────────────────────────────────────────────────────
    # MAIN ENTRY: generate_sql
    # ──────────────────────────────────────────────────────
    def generate_sql(self, natural_query: str, schema: List[Dict[str, Any]] = None, dialect: str = "sqlite", history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Intelligent intent-understanding NLP engine.
        Converts natural language to SELECT-only SQL using LLM or heuristic fallback.
        Uses RAG to retrieve only relevant tables for large schemas.
        """
        if not schema:
            return {"sql": "", "thought": "No schema provided.", "confidence": 0}

        query_lower = natural_query.lower().strip()
        
        # ── QUALITY GUARD: Reject too short or nonsensical queries ──
        if len(query_lower) < 2:
            return {
                "sql": "-- Not Found", 
                "thought": "Your question seems incomplete. Can you complete it?", 
                "confidence": 0,
                "model": "Quality Guard"
            }
        
        # ── RAG: Index schema if not already indexed ──
        rag_active = False
        if rag_service.is_available or (not rag_service.is_available and len(schema) > 5):
            rag_service.index_schema(schema)

        if self.client:
            try:
                # ── RAG: Retrieve only relevant tables for the LLM ──
                if rag_service.is_available and len(schema) > 5:
                    llm_schema = rag_service.retrieve_relevant_tables(natural_query, schema)
                    rag_active = True
                    print(f"🔍 RAG active: {len(llm_schema)}/{len(schema)} tables selected for LLM")
                else:
                    llm_schema = schema
                
                # Build schema text from RAG-filtered or full schema
                schema_text = ""
                for table in llm_schema:
                    cols = [f"{c['name']} ({c['type']})" for c in table["columns"]]
                    schema_text += f"\nTable: {table['name']}\nColumns: {', '.join(cols)}\n"

                relationships_text = ""
                for table in llm_schema:
                    for col in table["columns"]:
                        if "foreign_key" in col:
                            relationships_text += f"- {table['name']}.{col['name']} = {col['foreign_key']}\n"
                
                current_date = datetime.now()
                current_year = current_date.year
                current_month = current_date.month
                current_date_str = current_date.strftime('%Y-%m-%d')

                # ── SMART SCHEMA ANALYSIS: Auto-detect MES columns ──
                schema_analysis = self._analyze_mes_schema(llm_schema)

                system_prompt = f"""
                You are an expert Manufacturing Execution System (MES) SQL generator.
                Your job is to generate accurate, read-only SELECT queries based STRICTLY on the provided SCHEMA below.
                
                🚨 ABSOLUTE RULE: ONLY use table names and column names that appear in the SCHEMA section below.
                NEVER invent, assume, or hallucinate table/column names. If a column doesn't exist, DO NOT use it.

                🚨 CRITICAL RESPONSE RULES:
                - Respond ONLY with JSON: {{"sql": "...", "thought": "brief technical note", "suggested_chart": "bar|line|area|pie|none"}}
                - The "thought" field must be SHORT (max 1 sentence). Do NOT write explanations or paragraphs.
                - Example good thought: "Joined production and maintenance tables for OEE."
                - Example bad thought: "To calculate OEE, we need to join the production table..."

                🔒 GLOBAL SQL RULES:
                - ONLY generate SELECT queries. NEVER use DROP, DELETE, UPDATE, INSERT.
                - Always use NULLIF(denominator, 0) for division to prevent errors.
                - Use COALESCE(value, 0) for columns that may be NULL (especially from LEFT JOINs).
                - Multiply by 100 only once at the end for percentage metrics.
                - Use >= and < for date filtering (e.g., date_col >= '2026-01-01' AND date_col < '2026-02-01').
                - Use LEFT JOIN when related data may not exist for every record.
                - Use GROUP BY when aggregation (SUM, AVG, COUNT) is required.
                - Respond with valid SQL matching the {dialect} dialect.
                - Use table aliases (e.g., p, m, mc) to avoid ambiguous column names.

                🧮 OPERATOR RULE (CRITICAL):
                1. Perform all division operations first, wrapped in parentheses.
                2. After division is completed, apply multiplication.
                3. Never rely on default SQL left-to-right behavior.

                🔢 PERCENTAGE CALCULATION PROTOCOL:
                ROUND((numerator / NULLIF(denominator,0)) * 100, 2)
                - Division MUST happen first inside parentheses. Multiply * 100 last.
                - Never Sum Percentages. Always calculate from aggregated raw data.
                - Every division MUST use NULLIF(denominator,0).

                ⏱️ TIME UNIT HANDLING:
                - Time columns may store values in hours, minutes, seconds, or milliseconds.
                - Check the column name for hints: '_hours', '_min', '_minutes', '_seconds', '_ms', '_milliseconds'.
                - When comparing or combining time values from different columns, normalize to the SAME unit.
                - If column name contains 'hours' → value is in hours.
                - If column name contains 'min' or 'minutes' → value is in minutes.
                - If column name contains 'seconds' → divide by 60 to get minutes, divide by 3600 to get hours.
                - If column name contains 'ms' or 'milliseconds' → divide by 60000 to get minutes.
                - When calculating ratios (like Availability), both numerator and denominator must be in the SAME unit — no conversion needed if they come from the same unit.

                📅 DATE FILTER RULES:
                - Look at the SCHEMA to find the correct date/datetime column (it could be named: production_date, log_time, timestamp, date, created_at, etc.)
                - If user says "January" without a year → use {current_year}: date_col >= '{current_year}-01-01' AND date_col < '{current_year}-02-01'
                - If user says "February" → date_col >= '{current_year}-02-01' AND date_col < '{current_year}-03-01'
                - If user asks for multiple months (e.g., "January and February"), combine the date ranges using OR wrapped in parentheses: ((date_col >= '{current_year}-01-01' AND date_col < '{current_year}-02-01') OR (date_col >= '{current_year}-02-01' AND date_col < '{current_year}-03-01')). NEVER use AND between two different date ranges for the same column.
                - If user says "January 2026" → date_col >= '2026-01-01' AND date_col < '2026-02-01'
                - If user says "this month" → use {current_year}-{current_month:02d}-01 as start
                - If user says "last month" → calculate previous month
                - If no date is specified → DO NOT assume a date filter.
                - CURRENT DATE: {current_date_str}

                🎯 MES METRIC FORMULAS (adapt column names from SCHEMA below):
                Study the SCHEMA carefully. Identify which columns represent:
                - **Production/planned time**: columns with names like 'production_time', 'planned_time', 'operating_time', 'run_time'
                - **Downtime**: columns with names like 'downtime', 'breakdown', 'idle_time' (may be in a separate table)
                - **Units produced**: columns like 'units_produced', 'produced_qty', 'output_qty', 'quantity'
                - **Defects/rejects**: columns like 'defects', 'reject_qty', 'defective', 'scrap', 'bad_qty'
                - **Good units**: if column exists, use it. Otherwise: units_produced - defects
                - **Machine ID**: columns like 'machine_id', 'equipment_id', 'asset_id'
                - **Date/Time**: columns like 'production_date', 'log_time', 'timestamp', 'date'

                Then apply these formulas using the ACTUAL column names from the schema:

                - **Availability %**: ROUND(((SUM(production_time) - COALESCE(SUM(downtime),0)) / NULLIF(SUM(production_time),0)) * 100, 2)
                  → If downtime is in a different table, use LEFT JOIN.

                - **Quality %**: ROUND(((SUM(units_produced) - COALESCE(SUM(defects),0)) / NULLIF(SUM(units_produced),0)) * 100, 2)
                  → If a 'good_qty' column exists, use: ROUND((SUM(good_qty) / NULLIF(SUM(units_produced),0)) * 100, 2)

                - **OEE % = Availability × Quality / 100**:
                  ROUND(
                    ((SUM(production_time) - COALESCE(SUM(downtime),0)) / NULLIF(SUM(production_time),0))
                    * ((SUM(units_produced) - COALESCE(SUM(defects),0)) / NULLIF(SUM(units_produced),0))
                    * 100, 2
                  ) AS oee_percentage

                - **Defect/Scrap Rate %**: ROUND((COALESCE(SUM(defects),0) / NULLIF(SUM(units_produced),0)) * 100, 2)

                - **Throughput**: SUM(units_produced) or SUM(units_produced) / NULLIF(SUM(time), 0) for per-hour

                - **MTBF**: SUM(production_time) / NULLIF(COUNT(downtime_events), 0)

                - **MTTR**: SUM(downtime) / NULLIF(COUNT(downtime_events), 0)

                🧠 SEMANTIC MAPPING:
                - "machine X" or "machine_id X" → WHERE machine_id_column = X
                - "machine-wise" → GROUP BY machine_id_column
                - "shift-wise" → GROUP BY shift_column
                - "daily" → GROUP BY date_column
                - "monthly" → GROUP BY MONTH(date_column), YEAR(date_column)
                - "product-wise" → GROUP BY product_id_column
                - Scrap / defects / rejects → defect/reject column
                - Downtime / breakdown → downtime column (may be in separate table)
                - Efficiency → OEE
                - "CNC" / "Robot" → machine name filter

                {schema_analysis}

                RELATIONSHIPS:
                {relationships_text if relationships_text else "No explicit foreign keys. Use column name matching (e.g., machine_id appears in multiple tables)."}
                
                SCHEMA (USE ONLY THESE TABLES AND COLUMNS):
                {schema_text}

                SAFETY VALIDATION:
                Before returning SQL:
                - Ensure only SELECT is used.
                - Ensure ALL table and column names in the SQL exist in the SCHEMA above.
                - Ensure proper JOIN keys (match column names across tables).
                - Ensure no ambiguous column names (use table aliases).
                - Ensure no cartesian joins.
                - Double check: does the table ACTUALLY have that column? Re-read the SCHEMA.

                Respond ONLY with JSON: {{"sql": "...", "thought": "brief technical note", "suggested_chart": "bar|line|area|pie|none"}}
                - Use "none" if results are scalar (e.g., just a count) or if not applicable.
                - If the user explicitly asks for a chart type (e.g. "show as pie chart"), you MUST respect that in suggested_chart.
                """

                # Prepare messages with history
                messages = [{"role": "system", "content": system_prompt}]
                if history:
                    for entry in history[-5:]: # Use last 5 messages for context
                        role = "user" if entry["type"] == "user" else "assistant"
                        content = entry["content"]
                        # If bot message has SQL, prepend it to content to help AI see previous query logic
                        if entry.get("sql"):
                            content = f"[Previous SQL: {entry['sql']}] {content}"
                        messages.append({"role": role, "content": content})
                
                messages.append({"role": "user", "content": natural_query})

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                import json
                result = json.loads(response.choices[0].message.content)
                sql_out = result.get("sql", "").strip()

                # ── VALIDATION + RETRY LOOP (max 1 retry for column errors) ──
                max_retries = 1
                for attempt in range(max_retries + 1):
                    if not sql_out:
                        break

                    # 1. TABLE VALIDATION
                    valid_tables = [t["name"].lower() for t in schema]
                    rag_tables = [t["name"].lower() for t in llm_schema]
                    all_valid = set(valid_tables + rag_tables)
                    
                    clean_sql = re.sub(r'["`\'\[\]]', '', sql_out)
                    potential_tables = [t.split('.')[-1] for t in re.findall(r"FROM\s+([a-zA-Z0-9_\.]+)", clean_sql, re.IGNORECASE)]
                    join_tables = [t.split('.')[-1] for t in re.findall(r"JOIN\s+([a-zA-Z0-9_\.]+)", clean_sql, re.IGNORECASE)]
                    
                    sql_keywords = {'select', 'where', 'group', 'order', 'having', 'limit', 'union', 'case', 'when', 'then', 'else', 'end', 'as', 'on', 'and', 'or', 'not', 'in', 'is', 'null', 'between', 'like', 'exists'}
                    referenced_tables = [t for t in potential_tables + join_tables if t.lower() not in sql_keywords]
                    
                    missing_tables = [t for t in referenced_tables if t.lower() not in all_valid]
                    
                    if missing_tables:
                        err_msg = f"⚠️ LLM REJECTED (attempt {attempt+1}): Non-existent tables: {missing_tables}\nSQL: {sql_out}"
                        print(err_msg)
                        sql_out = None
                        break  # Table errors → fall through to heuristic

                    # 2. COLUMN VALIDATION (new!)
                    cols_valid, col_error, bad_refs = self._validate_sql_columns(sql_out, schema)
                    
                    if not cols_valid:
                        print(f"⚠️ LLM COLUMN ERROR (attempt {attempt+1}): {col_error}")
                        
                        if attempt < max_retries:
                            # RETRY: Ask the LLM to fix its mistake with explicit feedback
                            retry_msg = (
                                f"ERROR: Your SQL has invalid column references. "
                                f"{col_error}. "
                                f"Re-read the SCHEMA carefully and fix the SQL. "
                                f"Only use columns that ACTUALLY EXIST in each table. "
                                f"Respond ONLY with the corrected JSON."
                            )
                            messages.append({"role": "assistant", "content": response.choices[0].message.content})
                            messages.append({"role": "user", "content": retry_msg})
                            
                            print(f"🔄 Retrying LLM with column error feedback...")
                            response = self.client.chat.completions.create(
                                model=MODEL_NAME,
                                messages=messages,
                                response_format={"type": "json_object"},
                                temperature=0.05
                            )
                            result = json.loads(response.choices[0].message.content)
                            sql_out = result.get("sql", "").strip()
                            continue  # Re-validate the new SQL
                        else:
                            print(f"⚠️ LLM still has column errors after retry. Falling back to heuristic.")
                            sql_out = None
                            break

                    # 3. SAFETY VALIDATION
                    is_safe, error_msg = self._validate_sql_safety(sql_out)
                    if not is_safe:
                        print(f"⚠️ SQL REJECTED (Safety): {error_msg}")
                        sql_out = None
                        break
                    
                    # ✅ ALL VALIDATIONS PASSED
                    model_display = "GPT-4o" if "gpt-4o" in MODEL_NAME.lower() else "Llama 3.3 (70B)"
                    rag_note = f" [RAG: {len(llm_schema)}/{len(schema)} tables]" if rag_active else ""
                    retry_note = " (auto-corrected)" if attempt > 0 else ""
                    return {
                        "sql": sql_out,
                        "thought": f"{model_display}{rag_note}{retry_note} {result.get('thought', '')}",
                        "confidence": 0.99 if attempt == 0 else 0.95,
                        "suggested_chart": result.get("suggested_chart", "none"),
                        "model": model_display,
                        "rag_active": rag_active,
                        "rag_tables_used": len(llm_schema) if rag_active else len(schema),
                        "total_tables": len(schema)
                    }
                
            except Exception as e:
                err = f"LLM Error: {e}\n"
                print(err)
                with open("debug_error.txt", "a", encoding="utf-8") as f:
                    f.write(err)
                
                # If it's a rate limit error, propagate it instead of silent fallback
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    return {
                        "sql": "-- Error",
                        "thought": "LLM API Rate Limit Exceeded. Please wait a minute and try again.",
                        "confidence": 0,
                        "model": "Error Guard"
                    }

        # ── 2. ROBUST HEURISTIC ENGINE (FALLBACK) ──

        # Step A: Fix typos
        corrected_query = self._fix_typos(query_lower)

        # Step B: Detect intent
        intent = self._detect_intent(corrected_query)

        # Step C: Meta-query
        if intent == "meta_tables":
            if dialect == "mysql":
                meta_sql = "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys') AND TABLE_TYPE = 'BASE TABLE'"
            elif dialect == "postgresql":
                meta_sql = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
            else:
                meta_sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            
            return {
                "sql": meta_sql,
                "thought": f"Heuristic Engine: DB Schema Listing.",
                "confidence": 0.95,
                "model": "Smart Heuristic"
            }

        # Step D: Find tables
        found_tables = self._find_tables(corrected_query, schema)

        if not found_tables:
            return {"sql": "-- Not Found", "thought": "Couldn't identify target table.", "confidence": 0}

        # Step E: Find columns
        target_columns = self._find_columns(corrected_query, found_tables, schema)

        # Step F: Detect filters
        wheres = self._detect_filters(corrected_query, found_tables, schema)

        # Step G: Detect GROUP BY
        group_by = self._detect_group_by(corrected_query, target_columns, found_tables)

        # Step H: Build projection
        proj = self._build_projection(intent, corrected_query, target_columns, found_tables, group_by)

        # Step I: Build FROM + Multi-Table JOINs
        all_found = list(found_tables.values())
        t1 = all_found[0]
        
        # Pick anchor table (the one with the most columns or directly mentioned)
        sql = f"SELECT {proj} FROM {t1['name']}"
        joined_tables = {t1['name'].lower()}
        
        remaining = [t for t in all_found if t["name"].lower() not in joined_tables]
        
        # Iteratively join tables
        max_iterations = len(remaining) * 2
        while remaining and max_iterations > 0:
            max_iterations -= 1
            t_to_join = remaining.pop(0)
            
            # Try to join with any ALREADY joined table
            found_path = False
            for already_joined_name in list(joined_tables):
                t_base = next(t for t in all_found if t["name"].lower() == already_joined_name)
                join_cond = self._build_join(t_base, t_to_join)
                if join_cond:
                    sql += f" JOIN {t_to_join['name']} ON {join_cond}"
                    joined_tables.add(t_to_join['name'].lower())
                    found_path = True
                    break
            
            if not found_path:
                # If no direct join, put back at end of queue (maybe it needs an intermediate table)
                remaining.append(t_to_join)

        # Final check for unjoined tables
        for t in remaining:
             sql += f" CROSS JOIN {t['name']}" # Fallback to cross join if no relationship found

        # Step J: WHERE
        if wheres:
            sql += " WHERE " + " AND ".join(list(dict.fromkeys(wheres)))

        # Step K: GROUP BY
        if group_by:
            sql += f" GROUP BY {group_by}"

        # Step L: ORDER BY + LIMIT
        order_dir, limit = self._detect_order_and_limit(corrected_query)
        if order_dir is not None:
            sql += f" ORDER BY 1 {order_dir}".rstrip()
        if limit:
            sql += f" LIMIT {limit}"

        # Step M: Detect suggested chart from query keywords for heuristic mode
        suggested_chart = "none"
        if any(w in query_lower for w in ["pie chart", "piechart"]):
            suggested_chart = "pie"
        elif any(w in query_lower for w in ["line chart", "trend", "over time"]):
            suggested_chart = "line"
        elif any(w in query_lower for w in ["area chart"]):
            suggested_chart = "area"
        elif any(w in query_lower for w in ["bar chart", "chart", "graph", "histogram"]):
            suggested_chart = "bar"

        print(f"DEBUG: Generated SQL: {sql}")
        return {
            "sql": sql,
            "thought": f"Heuristic Engine: Intent='{intent}'. Analyzed keywords, logic, and relationships to build query.",
            "confidence": 0.85,
            "suggested_chart": suggested_chart,
            "model": "Smart Heuristic"
        }


# Singleton instance
nlp_engine = NLPEngine()
