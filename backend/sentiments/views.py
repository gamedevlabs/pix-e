from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd

class SentimentData(APIView):
    def get(self, request):
        df = pd.read_csv('../df_with_sentiments_explicit.csv')
        # Replace NaN values with None, which JSON can handle as null
        # Convert DataFrame to dictionary, handling NaN values by converting them to None
        data = df.where(pd.notna(df), None).to_dict(orient='records')
        return Response(data)
        return Response(df.to_dict(orient='records'))