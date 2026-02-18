import os
import re
import difflib
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

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
    # MAIN ENTRY: generate_sql
    # ──────────────────────────────────────────────────────
    def generate_sql(self, natural_query: str, schema: List[Dict[str, Any]] = None, dialect: str = "sqlite") -> Dict[str, Any]:
        """
        Intelligent intent-understanding NLP engine.
        Converts natural language to SELECT-only SQL using LLM or heuristic fallback.
        """
        if not schema:
            return {"sql": "", "thought": "No schema provided.", "confidence": 0}

        query_lower = natural_query.lower().strip()

        if self.client:
            try:
                # Build schema text
                schema_text = ""
                for table in schema:
                    cols = [f"{c['name']} ({c['type']})" for c in table["columns"]]
                    schema_text += f"\nTable: {table['name']}\nColumns: {', '.join(cols)}\n"

                # --- Advanced Join Enrichment ---
                # Build an explicit relationship list for the LLM to understand connections better
                relationships_text = ""
                for table in schema:
                    for col in table["columns"]:
                        if "foreign_key" in col:
                            relationships_text += f"- {table['name']}.{col['name']} = {col['foreign_key']}\n"
                
                # Add implicit relationships (convention based)
                relationships_text += "- users_info.id = users.id\n"
                relationships_text += "- orders.customer_id = customers.id\n"

                system_prompt = f"""
                You are a highly advanced Text-to-SQL AI with enterprise-grade security.
                🔒 RULE 1: ONLY generate SELECT queries. NEVER modify data.
                🔒 RULE 2: When listing database tables, EXCLUDE system/internal tables.
                🔒 RULE 3: STRICT MODE - You MUST use ONLY the table and column names provided in the SCHEMA.
                🔒 RULE 4: RELATIONSHIPS - Use the explicit relationships provided below to perform JOINs.
                🔒 RULE 5: MULTI-TABLE JOINS - If a query involves columns from multiple tables, ensure you use the correct JOIN path.
                
                🎯 DB DIALECT: {dialect}
                
                RELATIONSHIPS:
                {relationships_text}
                
                SCHEMA:
                {schema_text}

                ### EXAMPLE JOINS:
                - "Show all shoppers and their orders" -> SELECT * FROM users JOIN orders ON users.id = orders.user_id
                - "Find products bought by Alice" -> SELECT user_products.* FROM user_products JOIN users ON user_products.user_id = users.id WHERE users.username = 'Alice'
                - "How many orders from Chennai?" -> SELECT COUNT(*) FROM orders JOIN customers ON orders.customer_id = customers.id WHERE customers.city = 'Chennai'

                Respond ONLY with JSON: {{"sql": "...", "thought": "..."}}
                """

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": natural_query}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                import json
                result = json.loads(response.choices[0].message.content)
                sql_out = result.get("sql", "").strip()

                if sql_out:
                    # Validate that the table in the SQL actually exists in the schema
                    valid_tables = [t["name"].lower() for t in schema]
                    potential_tables = re.findall(r"FROM\s+(\w+)", sql_out, re.IGNORECASE)
                    join_tables = re.findall(r"JOIN\s+(\w+)", sql_out, re.IGNORECASE)
                    
                    all_tables_exist = all(t.lower() in valid_tables for t in potential_tables + join_tables)

                    if all_tables_exist:
                        is_safe, error_msg = self._validate_sql_safety(sql_out)
                        if not is_safe:
                            return {"sql": "-- Not Found", "thought": error_msg, "confidence": 0}

                        model_display = "GPT-4o" if "gpt-4o" in MODEL_NAME.lower() else "Llama 3.3 (70B)"
                        return {
                            "sql": sql_out,
                            "thought": f"{model_display} Joined tables: {', '.join(potential_tables + join_tables)}. {result.get('thought', '')}",
                            "confidence": 0.99,
                            "model": model_display
                        }
                    else:
                        print(f"LLM Hallucinated tables: {potential_tables}. Falling back.")
                
            except Exception as e:
                print(f"LLM Error: {e}")

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

        print(f"DEBUG: Generated SQL: {sql}")
        return {
            "sql": sql,
            "thought": f"Heuristic Engine: Intent='{intent}'. Analyzed keywords, logic, and relationships to build query.",
            "confidence": 0.85,
            "model": "Smart Heuristic"
        }


# Singleton instance
nlp_engine = NLPEngine()
