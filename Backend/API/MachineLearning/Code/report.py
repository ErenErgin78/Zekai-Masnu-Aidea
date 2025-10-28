import os
import json
import pandas as pd
import numpy as np

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def analyze_final5(csv_path: str):
    # Dosya varlığını kontrol et
    if not os.path.exists(csv_path):
        print(json.dumps({"error": f"File not found: {csv_path}"}, ensure_ascii=False, indent=2))
        return

    # CSV'yi güvenli şekilde oku
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(json.dumps({"error": f"CSV read error: {str(e)}"}, ensure_ascii=False, indent=2))
        return

    # Temel bilgiler
    info = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "nonnull_counts": df.notnull().sum().to_dict(),
        "memory_usage_bytes": df.memory_usage(deep=True).sum()
    }

    # Sayısal özet (ilk 15 sütun kısaltılmış gösterim)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    describe_short = {}
    if numeric_cols:
        describe_short = df[numeric_cols].describe().transpose().head(15).to_dict()

    # Kategorik özet (ilk 10 sütun için en sık 10 değer)
    object_cols = df.select_dtypes(include=["object"]).columns.tolist()
    categorical_summary = {}
    for col in object_cols[:10]:
        vc = df[col].astype(str).value_counts(dropna=False).head(10)
        categorical_summary[col] = vc.to_dict()

    # Korelasyon (yüksek korelasyonlu ilk 10 çift)
    high_corr_pairs = []
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr().abs()
        # Alt üçgen ve diyagonalı NaN yap
        corr_values = corr.values.copy()
        corr_values[np.tril_indices_from(corr_values, k=0)] = np.nan
        corr_upper = pd.DataFrame(corr_values, index=corr.index, columns=corr.columns)
        corr_pairs = (
            corr_upper.stack()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
                .rename(columns={"level_0": "col1", "level_1": "col2", 0: "corr"})
        )
        high_corr_pairs = corr_pairs.to_dict(orient="records")

    # IQR tabanlı kabaca aykırı değer sayıları (ilk 15 sayısal sütun)
    outlier_counts = {}
    for col in numeric_cols[:15]:
        series = df[col].dropna()
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr is None or iqr == 0:
            outlier_counts[col] = 0
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_counts[col] = int(((series < lower) | (series > upper)).sum())

    # Örnek satırlar
    n_sample = min(5, len(df))
    sample_rows = df.sample(n=n_sample, random_state=42).to_dict(orient="records") if n_sample > 0 else []

    # Çıktı (JSON olarak yazdır)
    result = {
        "info": info,
        "numeric_describe_head": describe_short,
        "categorical_summary_head": categorical_summary,
        "top10_high_corr_pairs": high_corr_pairs,
        "iqr_outlier_counts_head": outlier_counts,
        "sample_rows": sample_rows
    }
    # Numpy/Pandas türlerini JSON için dönüştür
    def to_python(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.ndarray,)):
            return o.tolist()
        return str(o)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=to_python))

if __name__ == "__main__":
    # Proje köküne göre yol
    csv_path = os.path.join(os.path.dirname(__file__), "final5.csv")
    analyze_final5(csv_path)