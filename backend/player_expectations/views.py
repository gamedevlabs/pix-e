from __future__ import annotations
import os

import pandas as pd
from django.http import JsonResponse

# -----------------------------
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Count
from .models import PlayerExpectationsAbsa, PlayerExpectationsConfusions

import datetime
from collections import Counter, defaultdict

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
    qs = PlayerExpectationsAbsa.objects.values("dominant_aspect", "dominant_sentiment", "release_date")
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

# ---------- 2) Aspect + sentiment breakdown (top 10 aspects by positive count) ----------
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
            SENTIMENT_ORDER.index(x["dominant_sentiment"]) if x["dominant_sentiment"] in SENTIMENT_ORDER else 99
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
    data = {k: counts.get(k, 0) for k in SENTIMENT_ORDER}  # stable order if needed on client
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
        .filter(agreement__iregex=r'^\s*no(\.|$)')
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
        gpt_aspect   = _clean_aspect(row["gpt_aspect"])
        confusions_list.append({
            "pair": f"{model_aspect} \u2192 {gpt_aspect}",  # " → "
            "count": row["count"],
        })

    return JsonResponse({"data": confusions_list})


def player_expectations_data(request):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "ABSA_results.csv")
    df = pd.read_csv(csv_path)

    if "dominant_aspect" not in df.columns or "dominant_sentiment" not in df.columns:
        return JsonResponse({"error": "缺少字段"}, status=400)

    # 处理时间
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
        df["year"] = df["release_date"].dt.year
        df["month"] = df["release_date"].dt.to_period("M").dt.to_timestamp()

    # Top 10 aspects（按positive排序）
    top_aspects = (
        df[df["dominant_sentiment"] == "positive"]["dominant_aspect"]
        .value_counts()
        .nlargest(10)
        .index
    )

    # aspect + sentiment breakdown
    # ✅ 1. 统计每个 aspect + sentiment 的数量
    aspect_sentiment_long = (
        df[df["dominant_sentiment"].notna()]  # 避免 NaN
        .groupby(["dominant_aspect", "dominant_sentiment"])
        .size()
        .reset_index(name="count")
    )

    # ✅ 2. 找出 positive 数最多的前10个 aspect
    top_positive_aspects = (
        aspect_sentiment_long[aspect_sentiment_long["dominant_sentiment"] == "positive"]
        .sort_values(by="count", ascending=False)
        .head(10)["dominant_aspect"]
        .tolist()
    )

    # ✅ 3. 过滤只保留这10个 aspect
    filtered_df = aspect_sentiment_long[
        aspect_sentiment_long["dominant_aspect"].isin(top_positive_aspects)
    ].copy()

    # ✅ 4. 保证 sentiment 顺序
    sentiment_order = ["positive", "neutral", "negative"]
    filtered_df["dominant_sentiment"] = pd.Categorical(
        filtered_df["dominant_sentiment"], categories=sentiment_order, ordered=True
    )

    # ✅ 5. 保证 aspect 顺序：按 positive 数量降序排列
    filtered_df["dominant_aspect"] = pd.Categorical(
        filtered_df["dominant_aspect"], categories=top_positive_aspects, ordered=True
    )

    # ✅ 6. 排序
    filtered_df = filtered_df.sort_values(["dominant_aspect", "dominant_sentiment"])

    # ✅ 7. 转为 list of dicts
    aspect_sentiment_list = filtered_df.to_dict(orient="records")

    # Aspect frequency
    aspect_freq = df["dominant_aspect"].value_counts().nlargest(10).to_dict()

    # Time trend
    trend = (
        df.dropna(subset=["month"])
        .groupby(["month", "dominant_sentiment"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    trend["month"] = trend["month"].astype(str)
    trend_data = trend.to_dict(orient="records")

    # Sentiment pie
    sentiment_dist = df["dominant_sentiment"].value_counts().to_dict()

    # Heatmap Data: Positive mentions per aspect per year
    heatmap_data = df[df["dominant_sentiment"] == "positive"].pivot_table(
        index="dominant_aspect", columns="year", aggfunc="size", fill_value=0
    )
    heatmap_dict = heatmap_data.to_dict()
    implicit_path = os.path.join(
        base_dir, "data", "confusions.csv"
    )
    eval_df = pd.read_csv(implicit_path)
    eval_df["agreement"] = eval_df["agreement"].str.lower()
    # Strip leading/trailing quotes from both columns
    eval_df["model_aspect"] = eval_df["model_aspect"].str.strip('"').str.strip("'")
    eval_df["gpt_aspect"] = eval_df["gpt_aspect"].str.strip('"').str.strip("'")

    df_disagree = eval_df[eval_df["agreement"].isin(["no", "no."])]
    print("df_disagree head:")
    print(df_disagree.head())
    print("df_disagree shape:", df_disagree.shape)

    confusion_pairs = (
        df_disagree.groupby(["model_aspect", "gpt_aspect"])
        .size()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )

    top_confusions = confusion_pairs.sort_values(by="count", ascending=False).head(10)
    top_confusions["pair"] = (
        top_confusions["model_aspect"] + " → " + top_confusions["gpt_aspect"]
    )
    confusions_list = top_confusions[["pair", "count"]].to_dict(orient="records")

    print("top_confusions:")
    print(top_confusions)
    print("confusions_list:")
    print(confusions_list)

    return JsonResponse(
        {
            "aspectFrequency": aspect_freq,
            "aspectSentiment": aspect_sentiment_list,
            "trendOverTime": trend_data,
            "sentimentPie": sentiment_dist,
            "heatmap": heatmap_dict,
            "topConfusions": confusions_list,
        },
        safe=False,
    )
