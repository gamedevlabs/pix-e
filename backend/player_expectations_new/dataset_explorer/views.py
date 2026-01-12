# backend/player_expectations_new/dataset_explorer/views.py
"""
Dataset Explorer
defines ONE HTTP endpoint (GET) that het frontend calls to fetch:
page of reviews, quotes in those reviews, and code+sentiment pairs for these quotes

So the frontend code filters are her implement as on big sql query
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .efficientdbfix import SQLITE_DATASET_EXPLORER_INDEXES

from player_expectations_new.constants import GAME_NAMES, FEATURE_CODE_TO_TEXT, PAIN_CODE_TO_TEXT, AESTHETIC_CODE_TO_TEXT

#_parse_int: parse Integer from a string
def _parse_int(s: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if s is None or s == "":
        return default
    try:
        return int(s)
    except Exception:
        return default

#_parse_csv_ints: csv like "1,2,3" into [1,2,3].
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

#_recommended_clause: from reccomend to appropriate Database flag
def _recommended_clause(recommended: str) -> Tuple[str, List[Any]]:
    if recommended == "recommended":
        return "AND t.voted_up = 1", []
    if recommended == "not_recommended":
        return "AND t.voted_up = 0", []
    return "", []


# SQLite index initializer..could delete however if i change or add new data i want it easier repeated
_INDEXES_READY = False

def _ensure_sqlite_indexes() -> None:
    global _INDEXES_READY
    if _INDEXES_READY:
        return
    if connection.vendor != "sqlite": #sanity check that wereusing sqlite
        _INDEXES_READY = True
        return

    # Run the CREATE INDEX statements, then ANALYZE for better query plans.
    with connection.cursor() as cur:
        for stmt in SQLITE_DATASET_EXPLORER_INDEXES:
            cur.execute(stmt)
        cur.execute("ANALYZE")

    _INDEXES_READY = True



#---------------
# MAIN API ENDPOIINT
#---------------

@require_GET
def dataset_explorer_reviews(request):
    """
    GET /api/player-expectations-new/dataset-explorer/reviews/?page=1&page_size=100&...
    Returns reviews + extracted quotes with (code_int + code_text + sentiment_v2).
    """

    # Ensure critical indexes exist ..performance fix
    _ensure_sqlite_indexes()

    # 1) read paging inputs , and ensure we dont load too much
    page = max(1, _parse_int(request.GET.get("page"), 1) or 1)
    page_size = _parse_int(request.GET.get("page_size"), 100) or 100
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    # 2) read filters from query params
    q = (request.GET.get("q") or "").strip() # key word search
    recommended = (request.GET.get("recommended") or "all").strip()
    app_ids = _parse_csv_ints(request.GET.get("app_ids")) # games

    date_from = _parse_int(request.GET.get("date_from"))
    date_to = _parse_int(request.GET.get("date_to"))

    min_votes_up = _parse_int(request.GET.get("min_votes_up"))
    max_votes_up = _parse_int(request.GET.get("max_votes_up"))
    min_votes_funny = _parse_int(request.GET.get("min_votes_funny"))
    max_votes_funny = _parse_int(request.GET.get("max_votes_funny"))

    min_pf = _parse_int(request.GET.get("min_playtime_forever"))
    max_pf = _parse_int(request.GET.get("max_playtime_forever"))
    min_pr = _parse_int(request.GET.get("min_playtime_at_review"))
    max_pr = _parse_int(request.GET.get("max_playtime_at_review"))

    #forgot sort
    sort = (request.GET.get("sort") or "newest").strip()
    # Only allow known sort options (prevents SQL injection)
    if sort == "oldest":
        order_sql = "ORDER BY COALESCE(t.timestamp_created, 0) ASC, t.recommendation_id ASC"
    else:
        # default: newest
        order_sql = "ORDER BY COALESCE(t.timestamp_created, 0) DESC, t.recommendation_id DESC"

    # 3) Build SQL WHERE conditions, for better overview we create conditions substrings
    feature_codes = _parse_csv_ints(request.GET.get("feature_codes"))
    pain_codes = _parse_csv_ints(request.GET.get("pain_codes"))
    aesthetic_codes = _parse_csv_ints(request.GET.get("aesthetic_codes"))

    where_sql = "WHERE 1=1"
    params: List[Any] = []

    if app_ids:
        placeholders = ",".join(["%s"] * len(app_ids))
        where_sql += f" AND t.app_id IN ({placeholders})"
        params.extend(app_ids)

    if q:
        where_sql += " AND t.review_text_en LIKE %s"
        params.append("%" + q + "%")

    clause, clause_params = _recommended_clause(recommended)
    where_sql += f" {clause}"
    params.extend(clause_params)

    # COALESCE(field, 0) makes NULL behave like 0 so errors are not thrown
    if date_from is not None:
        where_sql += " AND COALESCE(t.timestamp_created, 0) >= %s"
        params.append(date_from)
    if date_to is not None:
        where_sql += " AND COALESCE(t.timestamp_created, 0) <= %s"
        params.append(date_to)

    if min_votes_up is not None:
        where_sql += " AND COALESCE(t.votes_up, 0) >= %s"
        params.append(min_votes_up)
    if max_votes_up is not None:
        where_sql += " AND COALESCE(t.votes_up, 0) <= %s"
        params.append(max_votes_up)

    if min_votes_funny is not None:
        where_sql += " AND COALESCE(t.votes_funny, 0) >= %s"
        params.append(min_votes_funny)
    if max_votes_funny is not None:
        where_sql += " AND COALESCE(t.votes_funny, 0) <= %s"
        params.append(max_votes_funny)

    if min_pf is not None:
        where_sql += " AND COALESCE(t.playtime_forever, 0) >= %s"
        params.append(min_pf)
    if max_pf is not None:
        where_sql += " AND COALESCE(t.playtime_forever, 0) <= %s"
        params.append(max_pf)
    if min_pr is not None:
        where_sql += " AND COALESCE(t.playtime_at_review, 0) >= %s"
        params.append(min_pr)
    if max_pr is not None:
        where_sql += " AND COALESCE(t.playtime_at_review, 0) <= %s"
        params.append(max_pr)

    # 4) COde filters
    # convert all selected codes into one list of "pairs": (coarse_category_name, code_int)
    # a review must contain ALL selected pairs somewhere
    selected_pairs: List[Tuple[str, int]] = []
    for c in feature_codes:
        selected_pairs.append(("Game Features", int(c)))
    for c in pain_codes:
        selected_pairs.append(("Pain Points", int(c)))
    for c in aesthetic_codes:
        selected_pairs.append(("Game Aesthetics", int(c)))

    if selected_pairs:
        # Build an OR list for the pairs: OR (..AND...) OR (..AND...)
        #Why? so we see how many codes a  review matches and if distinct = the selected filters..it is all incldueed
        ors: List[str] = []
        pair_params: List[Any] = []
        for coarse, code_int in selected_pairs:
            ors.append("(qcs.coarse_category = %s AND qcs.code_int = %s)")
            pair_params.extend([coarse, code_int])

        # Push down app_ids into the subquery too (reduces work)
        sub_app_sql = ""
        sub_app_params: List[Any] = []
        if app_ids:
            ph = ",".join(["%s"] * len(app_ids))
            sub_app_sql = f" AND rq.app_id IN ({ph})"
            sub_app_params.extend(app_ids)

        # idea:
        # 1) Join quotes -> quote_code_sentiment
        # 2) Keep only rows with a real sentiment ("true pairs")..missing is filtered out here
        # 3) Filter down to rows matching ANY selected pair (OR)
        # 4) GROUP BY recommendation_id, so per review
        # 5) HAVING count of distinct matched pairs == number of selected pairs
        #   => means ALL selected pairs are present (AND logic)
        where_sql += f"""
        AND t.recommendation_id IN (
            SELECT rq.recommendation_id
            FROM review_quotes rq
            JOIN quote_code_sentiment qcs
              ON qcs.quote_id = rq.quote_id
            WHERE qcs.sentiment_v2 IS NOT NULL
              AND qcs.sentiment_v2 <> ''
              {sub_app_sql}
              AND ({' OR '.join(ors)})
            GROUP BY rq.recommendation_id
            HAVING COUNT(DISTINCT (qcs.coarse_category || ':' || qcs.code_int)) = %s
        )
        """
        # sub_app_params first (matches subquery), then pair params, then finl count
        params.extend(sub_app_params)
        params.extend(pair_params)
        params.append(len(selected_pairs))

    # 5) Fetch the CURRENT review page + total count
    # Avoid running the heavy WHERE twice:
    # Use COUNT(*) OVER() to get total number of matching rows ignoring LIMIT/OFFSET
    with connection.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                t.recommendation_id,
                t.app_id,
                COALESCE(t.timestamp_created, 0) AS timestamp_created,
                COALESCE(t.voted_up, 0) AS voted_up,
                COALESCE(t.votes_up, 0) AS votes_up,
                COALESCE(t.votes_funny, 0) AS votes_funny,
                COALESCE(t.playtime_at_review, 0) AS playtime_at_review,
                COALESCE(t.playtime_forever, 0) AS playtime_forever,
                t.review_text_en,
                COUNT(1) OVER() AS total_count
            FROM thesis_dataset t
            {where_sql}
            {order_sql}
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, offset],
        )
        review_rows_with_total = cur.fetchall()

    # f return not empty, we get the total count, attatched to each row
    if review_rows_with_total:
        total = int(review_rows_with_total[0][-1] or 0)
        review_rows = [r[:-1] for r in review_rows_with_total]
    else:
        # exact total for empty page
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(1)
                FROM thesis_dataset t
                {where_sql}
                """,
                params,
            )
            total = int(cur.fetchone()[0] or 0)
        review_rows = []

    rec_ids = [r[0] for r in review_rows]

    # 6) Fetch quotes + (code, sentiment) pairs for these reviews
    # return quotes_by_rec[recommendation_id] = [ {quote_id, quote_text, coarse_category, codes:[...]} ]
    quotes_by_rec: Dict[str, List[Dict[str, Any]]] = {rid: [] for rid in rec_ids}
    quote_index: Dict[int, Dict[str, Any]] = {}

    if rec_ids:
        placeholders = ",".join(["%s"] * len(rec_ids))

        # 1) quotes of only the reviews on this page
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    rq.quote_id,
                    rq.recommendation_id,
                    rq.coarse_category,
                    rq.quote_text
                FROM review_quotes rq
                WHERE rq.recommendation_id IN ({placeholders})
                ORDER BY rq.quote_id ASC
                """,
                rec_ids,
            )
            for quote_id, rec_id, coarse_category, quote_text in cur.fetchall():
                qd = {
                    "quote_id": int(quote_id),
                    "coarse_category": coarse_category,
                    "quote_text": quote_text,
                    "codes": [],
                }
                quote_index[int(quote_id)] = qd
                quotes_by_rec[rec_id].append(qd)

        # 2) codes + sentiment_v2 (TRUE PAIRS ONLY) = exists +  not empty
        quote_ids = list(quote_index.keys())
        if quote_ids:
            q_placeholders = ",".join(["%s"] * len(quote_ids))
            with connection.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        qcs.quote_id,
                        qcs.coarse_category,
                        qcs.code_int,
                        qcs.sentiment_v2
                    FROM quote_code_sentiment qcs
                    WHERE qcs.quote_id IN ({q_placeholders})
                      AND qcs.sentiment_v2 IS NOT NULL
                      AND qcs.sentiment_v2 <> ''
                    ORDER BY qcs.quote_id ASC, qcs.code_int ASC
                    """,
                    quote_ids,
                )
                for quote_id, coarse_category, code_int, sentiment_v2 in cur.fetchall():
                    qid = int(quote_id)
                    if qid not in quote_index:
                        continue

                    code_int = int(code_int)

                    if coarse_category == "Game Features":
                        code_text = FEATURE_CODE_TO_TEXT.get(code_int, "UNKNOWN")
                    elif coarse_category == "Pain Points":
                        code_text = PAIN_CODE_TO_TEXT.get(code_int, "UNKNOWN")
                    elif coarse_category == "Game Aesthetics":
                        code_text = AESTHETIC_CODE_TO_TEXT.get(code_int, "UNKNOWN")
                    else:
                        code_text = "UNKNOWN"

                    quote_index[qid]["codes"].append(
                        {
                            "coarse_category": coarse_category,
                            "code_int": code_int,
                            "code_text": code_text,
                            "sentiment_v2": sentiment_v2,
                        }
                    )

        # 3) DROP quotes that have no true pairs
        for rec_id in list(quotes_by_rec.keys()):
            quotes_by_rec[rec_id] = [qq for qq in quotes_by_rec[rec_id] if qq.get("codes")]

    # Convert DB Rows into a json object
    results: List[Dict[str, Any]] = []
    for (
        recommendation_id,
        app_id,
        ts_created,
        voted_up,
        votes_up,
        votes_funny,
        playtime_at_review,
        playtime_forever,
        review_text_en,
    ) in review_rows:
        app_id_int = int(app_id)
        results.append(
            {
                "recommendation_id": recommendation_id,
                "app_id": app_id_int,
                "game_name": GAME_NAMES.get(app_id_int, f"App {app_id_int}"),
                "timestamp_created": int(ts_created),
                "voted_up": int(voted_up),
                "votes_up": int(votes_up),
                "votes_funny": int(votes_funny),
                "playtime_at_review": int(playtime_at_review),
                "playtime_forever": int(playtime_forever),
                "review_text_en": review_text_en,
                "quotes": quotes_by_rec.get(recommendation_id, []),
            }
        )

    # 8) transform json into HTTP response
    return JsonResponse(
        {
            "meta": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
            "data": results,
        }
    )
