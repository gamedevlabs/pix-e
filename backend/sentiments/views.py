from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import pandas as pd
import numpy as np
import os
import json

class SentimentData(APIView):
    def get(self, request):
        expectation_type = request.query_params.get('type', 'explicit')  # default to explicit

        # File paths
        explicit_path = '../df_with_sentiments_explicit.csv'
        implicit_path = '../ABSA_results.csv'
        drop_columns_explicit = ['has_explicit']  # Only drop has_explicit here
        drop_columns_implicit = ['explicit_expectations', 'has_explicit', 'ABSA_expectations']

        def load_csv(path, drop_cols, replace_explicit=False):
            if os.path.exists(path):
                df = pd.read_csv(path)
                
                # Filter out rows where has_explicit is false for the explicit dataset
                if replace_explicit and 'has_explicit' in df.columns:
                    df = df[df['has_explicit'] == True]

                # For explicit dataset: replace expectations column
                if replace_explicit and 'explicit_expectations' in df.columns:
                    df.drop(columns=['expectations'], errors='ignore', inplace=True)
                    df.rename(columns={'explicit_expectations': 'expectations'}, inplace=True)

                # Drop unnecessary columns
                df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore')
                return df
            else:
                return pd.DataFrame()

        print(f"Received expectation_type: {expectation_type}")
        print(f"Checking explicit_path: {explicit_path}, exists: {os.path.exists(explicit_path)}")
        print(f"Checking implicit_path: {implicit_path}, exists: {os.path.exists(implicit_path)}")

        # Load datasets
        df_explicit = load_csv(explicit_path, drop_columns_explicit, replace_explicit=True)
        df_implicit = load_csv(implicit_path, drop_columns_implicit)

        # Add 'expectation_type' column
        df_explicit['expectation_type'] = 'explicit'
        df_implicit['expectation_type'] = 'implicit'

        # Combine datasets into a single DataFrame for easier filtering
        df_all = pd.concat([df_explicit, df_implicit], ignore_index=True)

        print(f"df_explicit shape: {df_explicit.shape}, columns: {df_explicit.columns.tolist()}")
        print(f"df_implicit shape: {df_implicit.shape}, columns: {df_implicit.columns.tolist()}")
        print(f"df_all shape: {df_all.shape}, columns: {df_all.columns.tolist()}")

        # Filter dataset based on type
        if expectation_type == 'explicit':
            df = df_all[df_all['expectation_type'] == 'explicit'].copy()
        elif expectation_type == 'implicit':
            df = df_all[df_all['expectation_type'] == 'implicit'].copy()
        elif expectation_type == 'all':
            df = df_all.copy()
        elif expectation_type == 'not_assigned':
            # Filter for entries where 'expectations' is None or an empty string
            df = df_all[df_all['expectations'].isnull() | (df_all['expectations'] == '') | (df_all['expectations'] == '[]')].copy()
        else:
            return Response(
                {"error": "Invalid type parameter. Use 'explicit', 'implicit', 'all', or 'not_assigned'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"Final df shape before JSON conversion: {df.shape}, columns: {df.columns.tolist()}")
        print(f"Sample of final df head:")
        print(df.head())

        # Final cleaning before JSON serialization
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.astype(object).where(pd.notna(df), None)

        def make_json_safe(x):
            if isinstance(x, (np.generic, pd.Timestamp)):
                return x.item() if hasattr(x, 'item') else str(x)
            return x


        df = df.apply(lambda col: col.map(make_json_safe))

        # Serialize to JSON
        json_str = df.to_json(
            orient='records',
            force_ascii=False,
            date_format='iso',
            double_precision=15
        )
        print(f"Sample of json_str (first 500 chars): {json_str[:500]}")
        data = json.loads(json_str)
        return Response(data)
