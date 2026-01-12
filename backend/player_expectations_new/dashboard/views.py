#   backend/player_expectations_new/dashboard/views.py
"""
views defines several read-only (GET) API endpoints for the “compare dashboard”.

What it does (high level):
Reads query parameters from the URL (app_ids, languages, polarity, etc.)
Builds SQL WHERE clauses
Runs a few SQL aggregation queries (counts, averages, grouped totals)

Returns the results as JSON for the frontend charts
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from player_expectations_new.constants import (
AESTHETIC_CODE_TO_TEXT,
FEATURE_CODE_TO_TEXT,
PAIN_CODE_TO_TEXT,
POSITIVE_LABELS,
NEGATIVE_LABELS,
NEUTRAL_LABELS
)


DashboardPolarity = str  # "any" | "rec" | "nrec"
DashboardLanguage = str  # "all" | "english" | "schinese"

# Checks whether a DB table has a given column.
#cache the result because i dont change my tables
@lru_cache(maxsize=128)
def _table_has_column(table: str, col: str) -> bool:
    with connection.cursor() as cur:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
    return col in cols

#input:string, output: int
def _parse_int(s: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if s is None or s == "":
        return default
    try:
        return int(s)
    except Exception:
        return default

# Turns "10, 20, 30" into [10, 20, 30].
def _parse_csv_ints(s: Optional[str]) -> List[int]:
    if not s:
        return []
    out: List[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except Exception:
            continue
    return out

#Turns "english, schinese" into ["english", "schinese"].
def _parse_csv_str(s: Optional[str]) -> List[str]:
    if not s:
        return []
    out: List[str] = []
    for part in s.split(","):
        part = part.strip()
        if part:
            out.append(part)
    return out

"""
Builds a safe SQL "IN (...)" fragment with placeholders.
Example:
values=[10,20] -> ("IN (%s,%s)", [10,20])
"""
def _in_clause(values: Sequence[Any]) -> Tuple[str, List[Any]]:
    if not values:
        return "IN (NULL)", []
    placeholders = ",".join(["%s"] * len(values))
    return f"IN ({placeholders})", list(values)

# Assigns raw sentiment the respective bucket...implicite positve -> positve
def _sentiment_bucket(sentiment_v2: Optional[str]) -> str:
    if not sentiment_v2:
        return "missing"
    s = sentiment_v2.strip().lower()
    if not s:
        return "missing"
    if s in POSITIVE_LABELS:
        return "positive"
    if s in NEGATIVE_LABELS:
        return "negative"
    if s in NEUTRAL_LABELS:
        return "neutral"
    return "missing"

# converts the polarity query param into an SQL filter (or no filter).
# AND at the start so it can be easily added to WHERE clauses
def _recommendation_clause(polarity: DashboardPolarity) -> Tuple[str, List[Any]]:
    p = (polarity or "any").strip().lower()
    if p == "rec":
        return "AND COALESCE(t.voted_up,0) = 1", []
    if p == "nrec":
        return "AND COALESCE(t.voted_up,0) = 0", []
    return "", []

# Builds a WHERE clause for queries that only touch the review table (thesis_dataset).
def _base_review_where(
    app_ids: List[int],
    languages: List[str],
    polarity: DashboardPolarity,
) -> Tuple[str, List[Any]]:
    where_sql = "WHERE 1=1" # this is so that we can just append any filters with AND, even the first
    params: List[Any] = []

    if app_ids:
        clause, p = _in_clause(app_ids)
        where_sql += f" AND t.app_id {clause}"
        params.extend(p)

    if languages:
        if _table_has_column("thesis_dataset", "language"):
            clause, p = _in_clause([x.lower() for x in languages])
            where_sql += f" AND LOWER(COALESCE(t.language,'')) {clause}"
            params.extend(p)

    rec_clause, rec_params = _recommendation_clause(polarity)
    where_sql += f" {rec_clause}"
    params.extend(rec_params)

    return where_sql, params

# builds a WHERE clause for queries that join multiple tables (review_quotes, quote_code_sentiment, etc.)
def _base_mentions_where(
    app_ids: List[int],
    languages: List[str],
    polarity: DashboardPolarity,
) -> Tuple[str, List[Any]]:
    where_sql = "WHERE 1=1"
    params: List[Any] = []

    if app_ids:
        clause, p = _in_clause(app_ids)
        where_sql += f" AND t.app_id {clause}"
        params.extend(p)

    if languages:
        if _table_has_column("thesis_dataset", "language"):
            clause, p = _in_clause([x.lower() for x in languages])
            where_sql += f" AND LOWER(COALESCE(t.language,'')) {clause}"
            params.extend(p)

    rec_clause, rec_params = _recommendation_clause(polarity)
    where_sql += f" {rec_clause}"
    params.extend(rec_params)

    return where_sql, params

#converts a numeric code into a human freindly label using the right lookup table.
def _code_text(coarse: str, code_int: int) -> str:
    if coarse == "Game Features":
        return FEATURE_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    if coarse == "Pain Points":
        return PAIN_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    if coarse == "Game Aesthetics":
        return AESTHETIC_CODE_TO_TEXT.get(code_int, "UNKNOWN")
    return "UNKNOWN"

# These sets define which codes are considered "top-level" in each category.
FEATURE_TOP_LEVEL = {10, 20, 30, 40, 50, 60, 70, 800, 90, 100, 110, 120, 130}
PAIN_TOP_LEVEL = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150}
AESTHETIC_TOP_LEVEL = {1, 2, 3, 4, 5, 6, 7, 8}

#True if code_int is a top-level code for the given coarse category.
def _is_top_level(coarse: str, code_int: int) -> bool:
    if coarse == "Game Features":
        return code_int in FEATURE_TOP_LEVEL
    if coarse == "Pain Points":
        return code_int in PAIN_TOP_LEVEL
    if coarse == "Game Aesthetics":
        return code_int in AESTHETIC_TOP_LEVEL
    return False

#Groups subcodes under a parent code.
def _parent_code_int(coarse: str, code_int: int) -> int:
    if coarse in ("Game Features", "Pain Points"):
        if code_int >= 0:
            return (code_int // 10) * 10
        return code_int
    return code_int

# Returns basic KPI numbers for the selected filters..needed for kpi row
@require_GET
def compare_kpis(request):
    app_ids = _parse_csv_ints(request.GET.get("app_ids"))
    languages = _parse_csv_str(request.GET.get("languages"))
    polarity = (request.GET.get("polarity") or "any").strip().lower()

    where_sql, params = _base_review_where(app_ids, languages, polarity)

    # 1) Reviews + recommended count
    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              COUNT(1) AS reviews,
              SUM(CASE WHEN COALESCE(t.voted_up,0)=1 THEN 1 ELSE 0 END) AS recommended
            FROM thesis_dataset t
            {where_sql}
            """,
            params,
        )
        row = cur.fetchone() or (0, 0)
        reviews = int(row[0] or 0)
        recommended = int(row[1] or 0)

    # Recommended rate is recommended / reviews (avoid divide by zero)
    rec_rate = (recommended / reviews) if reviews else 0.0

    # 2) Mentions total (join-level query)
    m_where, m_params = _base_mentions_where(app_ids, languages, polarity)
    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(1)
            FROM thesis_dataset t
            JOIN review_quotes rq ON rq.recommendation_id = t.recommendation_id
            JOIN quote_code_sentiment qcs ON qcs.quote_id = rq.quote_id
            {m_where}
            """,
            m_params,
        )
        mentions_total = int((cur.fetchone() or [0])[0] or 0)

    mentions_per_review = (mentions_total / reviews) if reviews else 0.0

    return JsonResponse(
        {
            "reviews": reviews,
            "recommended_rate": rec_rate,
            "mentions_total": mentions_total,
            "mentions_per_review": mentions_per_review,
        }
    )

#Returns how many mentions fall into each sentiment bucket
@require_GET
def compare_sentiment_distribution(request):
    app_ids = _parse_csv_ints(request.GET.get("app_ids"))
    languages = _parse_csv_str(request.GET.get("languages"))
    polarity = (request.GET.get("polarity") or "any").strip().lower()

    where_sql, params = _base_mentions_where(app_ids, languages, polarity)

    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              qcs.sentiment_v2,
              COUNT(1) AS n
            FROM thesis_dataset t
            JOIN review_quotes rq ON rq.recommendation_id = t.recommendation_id
            JOIN quote_code_sentiment qcs ON qcs.quote_id = rq.quote_id
            {where_sql}
            GROUP BY qcs.sentiment_v2
            """,
            params,
        )
        rows = cur.fetchall()

    detailed: Dict[str, int] = {}
    buckets = {"positive": 0, "neutral": 0, "negative": 0, "missing": 0}

    for sentiment_v2, n in rows:
        key = (sentiment_v2 or "").strip() or "missing"
        cnt = int(n or 0)
        detailed[key] = detailed.get(key, 0) + cnt
        buckets[_sentiment_bucket(sentiment_v2)] += cnt

    total = sum(buckets.values()) or 0
    shares = {k: (v / total if total else 0.0) for k, v in buckets.items()}

    return JsonResponse(
        {
            "total": total,
            "buckets": buckets,
            "shares": shares,
            "detailed": detailed,
        }
    )

"""
Returns monthly time series data:
  - review count and recommended_rate by month
  - mentions sentiment buckets by month

fix note:
- write '%%Y-%%m' instead of '%Y-%m' because Django debug formatting can treat % as formatting tokens.
    """
@require_GET
def compare_timeseries(request):
    app_ids = _parse_csv_ints(request.GET.get("app_ids"))
    languages = _parse_csv_str(request.GET.get("languages"))
    polarity = (request.GET.get("polarity") or "any").strip().lower()

    r_where, r_params = _base_review_where(app_ids, languages, polarity)

    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              strftime('%%Y-%%m', datetime(COALESCE(t.timestamp_created,0), 'unixepoch')) AS ym,
              COUNT(1) AS reviews,
              SUM(CASE WHEN COALESCE(t.voted_up,0)=1 THEN 1 ELSE 0 END) AS recommended
            FROM thesis_dataset t
            {r_where}
            GROUP BY ym
            ORDER BY ym ASC
            """,
            r_params,
        )
        review_rows = cur.fetchall()

    # Convert rows into a dictionary for easy merging later
    review_by_month: Dict[str, Dict[str, Any]] = {}
    for ym, reviews, recommended in review_rows:
        key = str(ym or "unknown")
        rv = int(reviews or 0)
        rec = int(recommended or 0)
        review_by_month[key] = {
            "reviews": rv,
            "recommended_rate": (rec / rv if rv else 0.0),
        }

    m_where, m_params = _base_mentions_where(app_ids, languages, polarity)

    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              strftime('%%Y-%%m', datetime(COALESCE(t.timestamp_created,0), 'unixepoch')) AS ym,
              qcs.sentiment_v2,
              COUNT(1) AS n
            FROM thesis_dataset t
            JOIN review_quotes rq ON rq.recommendation_id = t.recommendation_id
            JOIN quote_code_sentiment qcs ON qcs.quote_id = rq.quote_id
            {m_where}
            GROUP BY ym, qcs.sentiment_v2
            ORDER BY ym ASC
            """,
            m_params,
        )
        mention_rows = cur.fetchall()

    mentions_by_month: Dict[str, Dict[str, int]] = {}
    for ym, sentiment_v2, n in mention_rows:
        key = str(ym or "unknown")
        if key not in mentions_by_month:
            mentions_by_month[key] = {"positive": 0, "neutral": 0, "negative": 0, "missing": 0}
        mentions_by_month[key][_sentiment_bucket(sentiment_v2)] += int(n or 0)

    months = sorted(set(review_by_month.keys()) | set(mentions_by_month.keys()))

    data: List[Dict[str, Any]] = []
    for m in months:
        r = review_by_month.get(m, {"reviews": 0, "recommended_rate": 0.0})
        s = mentions_by_month.get(m, {"positive": 0, "neutral": 0, "negative": 0, "missing": 0})
        data.append(
            {
                "month": m,
                "reviews": int(r["reviews"]),
                "recommended_rate": float(r["recommended_rate"]),
                "mentions": s,
            }
        )

    return JsonResponse({"data": data})

# Returns the "top codes" table (most frequent/mentioned codes), optionally filtered to top-level codes.
@require_GET
def compare_top_codes(request):
    app_ids = _parse_csv_ints(request.GET.get("app_ids"))
    languages = _parse_csv_str(request.GET.get("languages"))
    polarity = (request.GET.get("polarity") or "any").strip().lower()
    level = (request.GET.get("level") or "top").strip().lower()
    limit = max(5, min(_parse_int(request.GET.get("limit"), 20) or 20, 100))

    m_where, m_params = _base_mentions_where(app_ids, languages, polarity)

    # This query gives us counts per (coarse_category, code_int, sentiment_v2)
    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              qcs.coarse_category,
              qcs.code_int,
              qcs.sentiment_v2,
              COUNT(1) AS n
            FROM thesis_dataset t
            JOIN review_quotes rq ON rq.recommendation_id = t.recommendation_id
            JOIN quote_code_sentiment qcs ON qcs.quote_id = rq.quote_id
            {m_where}
            GROUP BY qcs.coarse_category, qcs.code_int, qcs.sentiment_v2
            """,
            m_params,
        )
        rows = cur.fetchall()

    agg: Dict[Tuple[str, int], Dict[str, Any]] = {}

    for coarse, code_int, sentiment_v2, n in rows:
        if coarse is None or code_int is None:
            continue
        coarse_s = str(coarse)
        code_i = int(code_int)

        if level == "top" and not _is_top_level(coarse_s, code_i):
            continue

        key = (coarse_s, code_i)
        if key not in agg:
            agg[key] = {
                "coarse_category": coarse_s,
                "code_int": code_i,
                "code_text": _code_text(coarse_s, code_i),
                "total": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "missing": 0,
            }

        cnt = int(n or 0)
        bucket = _sentiment_bucket(sentiment_v2)
        agg[key][bucket] += cnt
        agg[key]["total"] += cnt

    items: List[Dict[str, Any]] = []
    for v in agg.values():
        total = int(v["total"]) or 0
        pos = int(v["positive"])
        neg = int(v["negative"])
        net = (pos - neg) / total if total else 0.0
        items.append({**v, "net": net})

    # Sort so the most mentioned codes come first...for the graphs
    items.sort(key=lambda x: (x["total"], x["net"]), reverse=True)
    table = items[:limit]

    min_volume = 15
    candidates = [x for x in items if x["total"] >= min_volume] or items

    top_positive = sorted(candidates, key=lambda x: (x["net"], x["total"]), reverse=True)[:15]
    top_negative = sorted(candidates, key=lambda x: (x["net"], -x["total"]))[:15]

    return JsonResponse(
        {
            "level": level,
            "limit": limit,
            "table": table,
            "top_positive": top_positive,
            "top_negative": top_negative,
        }
    )


# Returns a row for every code in a dimension, so the frontend can build a “heatmap grid”.
#Even if a code has 0 mentions, we still return it (so the grid is stable).
@require_GET
def compare_heatmap_codes(request):
    dimension = (request.GET.get("dimension") or "").strip().lower()
    if dimension not in ("aesthetics", "features", "pain"):
        return JsonResponse({"detail": "dimension must be one of: aesthetics, features, pain"}, status=400)

    coarse = {
        "aesthetics": "Game Aesthetics",
        "features": "Game Features",
        "pain": "Pain Points",
    }[dimension]

    app_ids = _parse_csv_ints(request.GET.get("app_ids"))
    languages = _parse_csv_str(request.GET.get("languages"))
    polarity = (request.GET.get("polarity") or "any").strip().lower()

    if dimension == "aesthetics":
        codebook = AESTHETIC_CODE_TO_TEXT
    elif dimension == "features":
        codebook = FEATURE_CODE_TO_TEXT
    else:
        codebook = PAIN_CODE_TO_TEXT

    all_codes = sorted(int(k) for k in codebook.keys())

    m_where, m_params = _base_mentions_where(app_ids, languages, polarity)

    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              qcs.code_int,
              qcs.sentiment_v2,
              COUNT(1) AS n
            FROM thesis_dataset t
            JOIN review_quotes rq ON rq.recommendation_id = t.recommendation_id
            JOIN quote_code_sentiment qcs ON qcs.quote_id = rq.quote_id
            {m_where}
              AND qcs.coarse_category = %s
            GROUP BY qcs.code_int, qcs.sentiment_v2
            """,
            m_params + [coarse],
        )
        rows = cur.fetchall()

    agg: Dict[int, Dict[str, Any]] = {}
    for code_int, sentiment_v2, n in rows:
        if code_int is None:
            continue
        code_i = int(code_int)
        if code_i not in codebook:
            continue

        if code_i not in agg:
            agg[code_i] = {
                "code_int": code_i,
                "code_text": codebook.get(code_i, "UNKNOWN"),
                "total": 0,
                "buckets": {"positive": 0, "neutral": 0, "negative": 0, "missing": 0},
            }

        cnt = int(n or 0)
        b = _sentiment_bucket(sentiment_v2)
        agg[code_i]["buckets"][b] += cnt
        agg[code_i]["total"] += cnt

    out_rows: List[Dict[str, Any]] = []
    for code_i in all_codes:
        v = agg.get(
            code_i,
            {
                "code_int": code_i,
                "code_text": codebook.get(code_i, "UNKNOWN"),
                "total": 0,
                "buckets": {"positive": 0, "neutral": 0, "negative": 0, "missing": 0},
            },
        )
        total = int(v["total"]) or 0
        buckets = v["buckets"]
        shares = {k: (buckets[k] / total if total else 0.0) for k in buckets.keys()}
        net = ((buckets["positive"] - buckets["negative"]) / total) if total else 0.0

        out_rows.append(
            {
                "code_int": int(code_i),
                "code_text": str(v["code_text"]),
                "total": total,
                "buckets": buckets,
                "shares": shares,
                "net": float(net),
            }
        )

    return JsonResponse({"dimension": dimension, "rows": out_rows})
