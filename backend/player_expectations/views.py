import pandas as pd
from django.http import JsonResponse
import os


def player_expectations_data(request):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'data', 'ABSA_results.csv')
    df = pd.read_csv(csv_path)

    if 'dominant_aspect' not in df.columns or 'dominant_sentiment' not in df.columns:
        return JsonResponse({'error': '缺少字段'}, status=400)

    # 处理时间
    if 'release_date' in df.columns:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['year'] = df['release_date'].dt.year
        df['month'] = df['release_date'].dt.to_period('M').dt.to_timestamp()

    # Top 10 aspects（按positive排序）
    top_aspects = (
        df[df['dominant_sentiment'] == 'positive']
        ['dominant_aspect'].value_counts()
        .nlargest(10)
        .index
    )

    # aspect + sentiment breakdown
    # ✅ 1. 统计每个 aspect + sentiment 的数量
    aspect_sentiment_long = (
        df[df['dominant_sentiment'].notna()]  # 避免 NaN
        .groupby(['dominant_aspect', 'dominant_sentiment'])
        .size()
        .reset_index(name='count')
    )

    # ✅ 2. 找出 positive 数最多的前10个 aspect
    top_positive_aspects = (
        aspect_sentiment_long[aspect_sentiment_long['dominant_sentiment'] == 'positive']
        .sort_values(by='count', ascending=False)
        .head(10)['dominant_aspect']
        .tolist()
    )

    # ✅ 3. 过滤只保留这10个 aspect
    filtered_df = aspect_sentiment_long[
        aspect_sentiment_long['dominant_aspect'].isin(top_positive_aspects)
    ].copy()

    # ✅ 4. 保证 sentiment 顺序
    sentiment_order = ['positive', 'neutral', 'negative']
    filtered_df['dominant_sentiment'] = pd.Categorical(
        filtered_df['dominant_sentiment'], categories=sentiment_order, ordered=True
    )

    # ✅ 5. 保证 aspect 顺序：按 positive 数量降序排列
    filtered_df['dominant_aspect'] = pd.Categorical(
        filtered_df['dominant_aspect'], categories=top_positive_aspects, ordered=True
    )

    # ✅ 6. 排序
    filtered_df = filtered_df.sort_values(['dominant_aspect', 'dominant_sentiment'])

    # ✅ 7. 转为 list of dicts
    aspect_sentiment_list = filtered_df.to_dict(orient='records')

    # Aspect frequency
    aspect_freq = df['dominant_aspect'].value_counts().nlargest(10).to_dict()

    # Time trend
    trend = (
        df.dropna(subset=['month'])
        .groupby(['month', 'dominant_sentiment'])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    trend['month'] = trend['month'].astype(str)
    trend_data = trend.to_dict(orient='records')

    # Sentiment pie
    sentiment_dist = df['dominant_sentiment'].value_counts().to_dict()

    # Heatmap Data: Positive mentions per aspect per year
    heatmap_data = (
        df[df['dominant_sentiment'] == 'positive']
        .pivot_table(index='dominant_aspect', columns='year', aggfunc='size', fill_value=0)
    )
    heatmap_dict = heatmap_data.to_dict()

    return JsonResponse({
        'aspectFrequency': aspect_freq,
        'aspectSentiment': aspect_sentiment_list,
        'trendOverTime': trend_data,
        'sentimentPie': sentiment_dist,
        'heatmap': heatmap_dict,
    }, safe=False)
