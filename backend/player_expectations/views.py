from __future__ import annotations

import datetime
from collections import Counter, defaultdict

from django.db.models import Case, CharField, Count, F, Q, TextField, Value, When

# -----------------------------
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlayerExpectationsAbsa, PlayerExpectationsConfusions

SENTIMENT_ORDER = ["positive", "neutral", "negative"]

# ---------- shared helpers ----------


def _parse_date_safe(value: str | None):
    if not value:
        return None
    v = value.strip()
    # try several common formats; add more if your data needs it
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def _base_rows():
    """
    Load only the fields we need and normalize (lowercase sentiment, trim aspect).
    We keep this small so each view can reuse it.
    """
    qs = PlayerExpectationsAbsa.objects.values(
        "dominant_aspect", "dominant_sentiment", "release_date"
    )
    rows = []
    for r in qs:
        aspect = (r["dominant_aspect"] or "").strip()
        sentiment = (r["dominant_sentiment"] or "").strip().lower()
        date = _parse_date_safe(r["release_date"])
        if aspect and sentiment:
            rows.append({"aspect": aspect, "sentiment": sentiment, "date": date})
    return rows


# ---------- 1) Aspect frequency (top 10 overall) ----------
@require_GET
def aspect_frequency_view(request):
    rows = _base_rows()
    counts = Counter(r["aspect"] for r in rows).most_common(10)
    data = dict(counts)
    return JsonResponse({"data": data})


# -------- 2) Aspect + sentiment breakdown (top 10 aspects by positive count) --------
@require_GET
def aspect_sentiment_view(request):
    rows = _base_rows()

    # Get top aspects based on overall frequency (same as aspect_frequency_view)
    overall_counts = Counter(r["aspect"] for r in rows).most_common(10)
    top_aspects = [a for a, _ in overall_counts]

    # Count aspect + sentiment pairs
    aspect_sentiment_counts = Counter((r["aspect"], r["sentiment"]) for r in rows)

    # Build list and sort according to top_aspects order + sentiment order
    items = [
        {"dominant_aspect": a, "dominant_sentiment": s, "count": c}
        for (a, s), c in aspect_sentiment_counts.items()
        if a in top_aspects
    ]

    items.sort(
        key=lambda x: (
            top_aspects.index(x["dominant_aspect"]),
            (
                SENTIMENT_ORDER.index(x["dominant_sentiment"])
                if x["dominant_sentiment"] in SENTIMENT_ORDER
                else 99
            ),
        )
    )
    return JsonResponse({"data": items})


# ---------- 3) Trend over time (month × sentiment) ----------
@require_GET
def trend_over_time_view(request):
    rows = _base_rows()
    trend = defaultdict(lambda: {s: 0 for s in SENTIMENT_ORDER})
    for r in rows:
        if not r["date"]:
            continue
        month_key = r["date"].strftime("%Y-%m")  # "YYYY-MM"
        if r["sentiment"] in SENTIMENT_ORDER:
            trend[month_key][r["sentiment"]] += 1

    data = [{"month": m, **trend[m]} for m in sorted(trend.keys())]
    return JsonResponse({"data": data})


# ---------- 4) Sentiment pie (overall distribution) ----------
@require_GET
def sentiment_pie_view(request):
    rows = _base_rows()
    counts = Counter(r["sentiment"] for r in rows)
    data = {
        k: counts.get(k, 0) for k in SENTIMENT_ORDER
    }  # stable order if needed on client
    return JsonResponse({"data": data})


# ---------- 5) Heatmap: positive counts per aspect per year ----------
@require_GET
def heatmap_view(request):
    rows = _base_rows()
    heat = defaultdict(dict)  # {year: {aspect: count}}

    # collect all aspects & years (including None)
    all_aspects = set()
    all_years = set()

    for r in rows:
        if r["sentiment"] == "positive":
            all_aspects.add(r["aspect"])
            year = r["date"].year if r["date"] else "Unknown"
            all_years.add(year)
            heat[year][r["aspect"]] = heat[year].get(r["aspect"], 0) + 1

    # fill zeros for missing aspect-year combos
    for year in all_years:
        for aspect in all_aspects:
            heat[year].setdefault(aspect, 0)

    return JsonResponse({"data": heat})


# ---------- (Optional) 6) Top confusions -------------
SENTENCE_COUNT_FIELD = "agreement"  # any non-null field to count rows


def _clean_aspect(s: str | None) -> str:
    if not s:
        return ""
    # trim whitespace and strip leading/trailing single/double quotes
    return s.strip().strip('"').strip("'")


@require_GET
def top_confusions_view(request):
    """
    Returns:
      {"topConfusions": [{"pair": "A → B", "count": N}, ...]}
    """
    qs = (
        PlayerExpectationsConfusions.objects
        # agreement of "no" or "no." (case-insensitive):
        .filter(agreement__iregex=r"^\s*no(\.|$)")
        .exclude(model_aspect__isnull=True)
        .exclude(gpt_aspect__isnull=True)
        .values("model_aspect", "gpt_aspect")
        .annotate(count=Count(SENTENCE_COUNT_FIELD))
        .order_by("-count", "model_aspect", "gpt_aspect")[:10]
    )

    # Post-process to mimic your Pandas cleaning & formatting
    confusions_list = []
    for row in qs:
        model_aspect = _clean_aspect(row["model_aspect"])
        gpt_aspect = _clean_aspect(row["gpt_aspect"])
        confusions_list.append(
            {
                "pair": f"{model_aspect} \u2192 {gpt_aspect}",  # " → "
                "count": row["count"],
            }
        )

    return JsonResponse({"data": confusions_list})


class SentimentData(APIView):
    """
    GET /api/sentiments?type=explicit|implicit|all|not_assigned  (default: explicit)
    """

    COMMON = [
        "unnamed_0",
        "appid",
        "name",
        "release_date",
        "required_age",
        "price",
        "dlc_count",
        "categories",
        "genres",
        "user_score",
        "positive",
        "negative",
        "tags",
        "review_text",
        "dominant_aspect",
        "dominant_sentiment",
    ]

    def get(self, request):
        t = (request.query_params.get("type") or "explicit").lower()

        # 1) One base queryset with NON-colliding annotations
        base = PlayerExpectationsAbsa.objects.annotate(
            # explicit_expectations when has_explicit == "true", else expectations
            expectations_out=Case(
                When(has_explicit__iexact="true", then=F("explicit_expectations")),
                default=F("expectations"),
                output_field=TextField(),
            ),
            expectation_type_out=Case(
                When(has_explicit__iexact="true", then=Value("explicit")),
                default=Value("implicit"),
                output_field=CharField(),
            ),
        )

        # 2) Not-assigned definition applied to the resolved expectations
        not_assigned = (
            Q(expectations_out__isnull=True)
            | Q(expectations_out__exact="")
            | Q(expectations_out__exact="[]")
        )

        # 3) Apply filters per type
        if t == "explicit":
            qs = base.filter(has_explicit__iexact="true").exclude(not_assigned)
        elif t == "implicit":
            qs = base.exclude(has_explicit__iexact="true").exclude(not_assigned)
        elif t == "all":
            qs = base.exclude(not_assigned)
        elif t == "not_assigned":
            qs = base.filter(not_assigned)
        else:
            return Response(
                {
                    "error": "Invalid type parameter. "
                    "Use 'explicit', 'implicit', 'all', or 'not_assigned'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) Select fields + the safe annotation names
        rows = list(qs.values(*self.COMMON, "expectations_out", "expectation_type_out"))

        # 5) Rename keys to the public API names (avoid ORM conflicts entirely)
        for r in rows:
            r["expectations"] = r.pop("expectations_out")
            r["expectation_type"] = r.pop("expectation_type_out")

        return Response({"data": rows})
