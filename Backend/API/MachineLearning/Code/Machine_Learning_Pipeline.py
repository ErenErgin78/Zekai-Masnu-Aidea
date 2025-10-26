# ============================================================
# 🌿 Crop Recommendation — Multi-Model + Cross-Validation + Optuna (Final, Cleaned)
# ============================================================
# Prefers: Crop_recommendation_cleaned.csv
# Fallbacks: Crop_recommendation.csv (auto-clean if needed) or user path
# Models: Logistic Regression, Random Forest, LightGBM, XGBoost, CatBoost (if available)
# Selection: Best Test F1 (after 5-fold CV reporting)
# Artifacts: model_outputs/{cv_results.csv, test_results.csv, *.pkl, summary.json}
# ============================================================

import os
import json
import time
import joblib
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")

RANDOM_STATE = 42

# ---------- Optional imports guarded ----------
def _safe_import_lgbm():
    try:
        from lightgbm import LGBMClassifier
        return LGBMClassifier
    except Exception:
        return None

def _safe_import_xgb():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier
    except Exception:
        return None

def _safe_import_cat():
    try:
        from catboost import CatBoostClassifier
        return CatBoostClassifier
    except Exception:
        return None

def _safe_import_optuna():
    try:
        import optuna
        return optuna
    except Exception:
        return None

# ---------- Data utilities ----------
def load_prefer_clean():
    import os
    
    # Scriptin bulunduğu dizini al
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Data klasörü yolunu oluştur
    data_dir = os.path.join(current_dir, "Data")
    
    # Olası dosya konumları - sadece Data klasörü içinde
    candidates = [
        os.path.join(data_dir, "Crop_recommendation_cleaned.csv")
    ]
    
    for file_path in candidates:
        if os.path.exists(file_path):
            print(f"[DATA] Found dataset at: {file_path}")
            try:
                df = pd.read_csv(file_path)
            except Exception:
                try:
                    df = pd.read_csv(file_path, sep=';')
                except Exception:
                    df = pd.read_csv(file_path, sep=',')
            df = _ensure_clean(df)
            return df, f"Loaded: {file_path}"
    
    raise FileNotFoundError(
        f"Dataset not found in Data folder. Please place CSV file in: {data_dir}"
    )

def _ensure_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Standardize columns
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    if 'label' not in df.columns:
        raise ValueError("Expected a 'label' column in the dataset.")
    # Convert non-label numeric like '1.234,56' -> 1234.56
    num_cols = [c for c in df.columns if c != 'label']
    for c in num_cols:
        s = df[c].astype(str)
        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        # Try numeric; if conversion makes NaNs explode, fallback to original if already numeric-like
        converted = pd.to_numeric(s, errors='coerce')
        if converted.notna().mean() >= 0.95:  # accept if >=95% convertible
            df[c] = converted
        else:
            # Try direct numeric without replacement
            df[c] = pd.to_numeric(df[c], errors='ignore')
    # Drop rows with NA in any feature or label
    df = df.dropna(subset=num_cols + ['label']).reset_index(drop=True)
    return df

def split_and_scale(X, y_enc, test_size=0.2, random_state=RANDOM_STATE):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=test_size, random_state=random_state, stratify=y_enc
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    return X_train, X_test, y_train, y_test, X_train_s, X_test_s, scaler

# ---------- Models ----------
def define_models():
    LGBMClassifier = _safe_import_lgbm()
    XGBClassifier = _safe_import_xgb()
    CatBoostClassifier = _safe_import_cat()

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, multi_class='ovr', n_jobs=-1, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=None, n_jobs=-1, random_state=RANDOM_STATE
        ),
    }
    if XGBClassifier is not None:
        models["XGBoost"] = XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.9, colsample_bytree=0.9, random_state=RANDOM_STATE,
            eval_metric='mlogloss', tree_method="hist"
        )
    if LGBMClassifier is not None:
        models["LightGBM"] = LGBMClassifier(
            n_estimators=320, max_depth=-1, learning_rate=0.07,
            num_leaves=60, subsample=0.9, colsample_bytree=0.9,
            min_child_samples=20, reg_lambda=2.0, reg_alpha=0.3,
            random_state=RANDOM_STATE, n_jobs=-1
        )
    if CatBoostClassifier is not None:
        models["CatBoost"] = CatBoostClassifier(
            iterations=300, depth=8, learning_rate=0.05, loss_function='MultiClass',
            random_seed=RANDOM_STATE, verbose=False
        )
    return models

def needs_scaling(model_name: str) -> bool:
    return model_name in {"Logistic Regression"}

# ---------- CV helper ----------
def compute_cv(model, name, X, y, Xs=None, cv=5, scoring='f1_weighted'):
    data = Xs if needs_scaling(name) else X
    kf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, data, y, cv=kf, scoring=scoring, n_jobs=-1)
    return scores

# ---------- Optuna tuning for LightGBM & XGBoost ----------
def tune_with_optuna(name, base_model, X, y, Xs=None, n_trials=30):
    optuna = _safe_import_optuna()
    if optuna is None:
        return base_model, None  # Optuna not available

    if name.lower().startswith("lightgbm"):
        LGBMClassifier = _safe_import_lgbm()
        if LGBMClassifier is None:
            return base_model, None

        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 150, 500),
                "max_depth": trial.suggest_int("max_depth", -1, 14),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 20, 120),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 40),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 2.0),
                "random_state": RANDOM_STATE,
                "n_jobs": -1
            }
            model = LGBMClassifier(**params)
            data = Xs if Xs is not None else X
            kf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
            scores = cross_val_score(model, data, y, cv=kf, scoring='f1_weighted', n_jobs=-1)
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        best_params = study.best_params
        tuned = LGBMClassifier(**best_params)
        return tuned, best_params

    if name.lower().startswith("xgboost"):
        XGBClassifier = _safe_import_xgb()
        if XGBClassifier is None:
            return base_model, None

        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 150, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 2.0),
                "random_state": RANDOM_STATE,
                "eval_metric": "mlogloss",
                "tree_method": "hist"
            }
            from xgboost import XGBClassifier
            model = XGBClassifier(**params)
            data = Xs if Xs is not None else X
            kf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
            scores = cross_val_score(model, data, y, cv=kf, scoring='f1_weighted', n_jobs=-1)
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        best_params = study.best_params
        tuned = XGBClassifier(**best_params)
        return tuned, best_params

    return base_model, None

# ---------- Main ----------
def main():
    # 1) Load data (prefer cleaned)
    df, note = load_prefer_clean()
    print(f"[DATA] {note} | shape={df.shape}")
    print(f"[DATA] columns={list(df.columns)}")

    # 2) Prepare X/y
    X = df.drop(columns=['label'])
    y = df['label']
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 3) Split + Scale
    X_train, X_test, y_train, y_test, X_train_s, X_test_s, scaler = split_and_scale(X, y_enc)

    # 4) Define models
    models = define_models()

    # 5) (Optional) Optuna tuning for LGBM and XGB
    tuned_models = {}
    best_params_log = {}
    for name, model in models.items():
        data_for_tuning = X_train_s if needs_scaling(name) else X_train
        tuned, params = tune_with_optuna(name, model, X_train, y_train, Xs=data_for_tuning, n_trials=30)
        tuned_models[name] = tuned
        if params is not None:
            best_params_log[name] = params
            print(f"[OPTUNA] {name} best params: {params}")
        else:
            print(f"[OPTUNA] {name} skipped or unchanged.")

    # 6) CV scores (5-fold) for all tuned models
    cv_rows = []
    for name, model in tuned_models.items():
        data = X_train_s if needs_scaling(name) else X_train
        scores = compute_cv(model, name, X_train, y_train, Xs=data, cv=5, scoring='f1_weighted')
        cv_rows.append({
            "Model": name,
            "CV_F1_mean": float(np.mean(scores)),
            "CV_F1_std": float(np.std(scores)),
            "CV_Scores": [float(s) for s in scores],
        })
        print(f"[CV] {name}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")

    cv_df = pd.DataFrame(cv_rows).sort_values("CV_F1_mean", ascending=False)

    # 7) Fit on train & evaluate on test set
    eval_rows = []
    best = {"name": None, "f1": -1, "model": None, "scaled": False}
    for name, model in tuned_models.items():
        if needs_scaling(name):
            model.fit(X_train_s, y_train)
            y_pred = model.predict(X_test_s)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        prec = precision_score(y_test, y_pred, average='weighted')
        rec = recall_score(y_test, y_pred, average='weighted')

        eval_rows.append({
            "Model": name,
            "Test_Accuracy": float(acc),
            "Test_F1": float(f1),
            "Test_Precision": float(prec),
            "Test_Recall": float(rec)
        })
        print(f"[TEST] {name}: acc={acc:.4f} f1={f1:.4f} prec={prec:.4f} rec={rec:.4f}")

        if f1 > best["f1"]:
            best.update({"name": name, "f1": f1, "model": model, "scaled": needs_scaling(name)})

    eval_df = pd.DataFrame(eval_rows).sort_values("Test_F1", ascending=False)

    # 8) Save artifacts
    outputs = Path("model_outputs"); outputs.mkdir(exist_ok=True, parents=True)
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    cv_df.to_csv(outputs / "cv_results.csv", index=False)
    eval_df.to_csv(outputs / "test_results.csv", index=False)

    joblib.dump(best["model"], outputs / f"best_model_{best['name'].replace(' ', '_')}_{ts}.pkl")
    joblib.dump(scaler, outputs / f"scaler_{ts}.pkl")
    joblib.dump(le, outputs / f"label_encoder_{ts}.pkl")

    with open(outputs / f"best_params_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(best_params_log, f, ensure_ascii=False, indent=2)

    summary = {
        "data_note": note,
        "cv_top": cv_df.head(5).to_dict(orient="records"),
        "test_top": eval_df.head(5).to_dict(orient="records"),
        "best_model": best["name"],
        "best_f1": float(best["f1"]),
    }
    with open(outputs / f"summary_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 9) SHAP (optional quick summary for tree-based best model)
    try:
        import shap
        if "forest" in best["name"].lower() or "boost" in best["name"].lower() or "gbm" in best["name"].lower() or "catboost" in best["name"].lower():
            data = X_train if not best["scaled"] else X_train_s
            # Use TreeExplainer when available
            explainer = shap.TreeExplainer(best["model"])
            sv = explainer.shap_values(data[:500])  # sample
            np.save(outputs / f"shap_values_{ts}.npy", sv if isinstance(sv, np.ndarray) else np.array(sv, dtype=object))
            print("[SHAP] Saved sample SHAP values.")
    except Exception as e:
        print(f"[SHAP] Skipped: {e}")
        
    # 10) Visualization Section
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.metrics import confusion_matrix

        viz_dir = outputs  # Kaydedilecek klasör

        # === 1. Korelasyon Matrisi ===
        plt.figure(figsize=(10, 8))
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            sns.heatmap(numeric_df.corr(), annot=True, cmap="YlGnBu", fmt=".2f", linewidths=0.5)
            plt.title("Korelasyon Matrisi – Sayısal Özellikler", fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(viz_dir / "corr_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("[VIZ] Korelasyon matrisi kaydedildi")

        # === 2. Model F1 Karşılaştırması (Test Sonuçları) ===
        plt.figure(figsize=(10, 6))
        # Renk paletini iyileştir
        colors = sns.color_palette("viridis", len(eval_df))
        bars = plt.bar(range(len(eval_df)), eval_df["Test_F1"], color=colors, alpha=0.8)
        
        # Değerleri çubukların üzerine yaz
        for i, (bar, row) in enumerate(zip(bars, eval_df.itertuples())):
            plt.text(i, bar.get_height() + 0.01, f'{row.Test_F1:.3f}', 
                    ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(range(len(eval_df)), [m[:15] + '...' if len(m) > 15 else m for m in eval_df["Model"]], rotation=45)
        plt.ylabel("F1 Skoru")
        plt.title("Model Karşılaştırması – F1 Skoru (Test Seti)", fontsize=14, fontweight='bold')
        plt.ylim(0, 1.1)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(viz_dir / "model_f1_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("[VIZ] Model F1 karşılaştırması kaydedildi")

        # === 3. Confusion Matrix (Best Model) ===
        y_pred_best = (
            best["model"].predict(X_test_s)
            if best["scaled"]
            else best["model"].predict(X_test)
        )
        
        cm = confusion_matrix(y_test, y_pred_best)
        plt.figure(figsize=(12, 10))
        
        # Normalize confusion matrix
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        sns.heatmap(cm_normalized, annot=True, fmt=".2f", cmap="Greens", 
                   xticklabels=le.classes_, yticklabels=le.classes_,
                   cbar_kws={'label': 'Doğruluk Oranı'})
        
        plt.title(f"Confusion Matrix – {best['name']}\n(Normalize)", fontsize=14, fontweight='bold')
        plt.xlabel("Tahmin Edilen Sınıf")
        plt.ylabel("Gerçek Sınıf")
        plt.tight_layout()
        plt.savefig(viz_dir / "confusion_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("[VIZ] Confusion matrix kaydedildi")

        # === 4. Feature Importance (eğer tree-based ise) ===
        if hasattr(best["model"], "feature_importances_"):
            feat_imp = pd.DataFrame({
                "Feature": X.columns,
                "Importance": best["model"].feature_importances_
            }).sort_values(by="Importance", ascending=True)  # Son çubuğun en üstte olması için
            
            plt.figure(figsize=(10, 8))
            bars = plt.barh(range(len(feat_imp)), feat_imp["Importance"], 
                           color=sns.color_palette("YlGn", len(feat_imp)))
            
            # Değerleri çubukların sonuna yaz
            for i, (bar, imp) in enumerate(zip(bars, feat_imp["Importance"])):
                plt.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2, 
                        f'{imp:.4f}', va='center', fontsize=9)
            
            plt.yticks(range(len(feat_imp)), feat_imp["Feature"])
            plt.xlabel("Özellik Önem Skoru")
            plt.title(f"Feature Importance – {best['name']}", fontsize=14, fontweight='bold')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            plt.savefig(viz_dir / "feature_importance.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("[VIZ] Feature importance grafiği kaydedildi")

        # === 5. SHAP Summary Plot (sadece LightGBM, XGB, RF vb.) ===
        try:
            import shap
            if any(k in best["name"].lower() for k in ["forest", "boost", "gbm", "catboost"]):
                data_for_shap = X_train_s if best["scaled"] else X_train
                explainer = shap.TreeExplainer(best["model"])
                shap_values = explainer.shap_values(data_for_shap[:200])  # Daha küçük örneklem
                
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, data_for_shap[:200], 
                                feature_names=X.columns.tolist(), show=False)
                plt.title("SHAP Summary Plot – Özellik Katkıları", fontsize=14, fontweight='bold')
                plt.tight_layout()
                plt.savefig(viz_dir / "shap_summary.png", dpi=300, bbox_inches='tight')
                plt.close()
                print("[VIZ] SHAP summary plot kaydedildi")
                
        except Exception as e:
            print(f"[WARN] SHAP plot skipped: {e}")

        print("[VIZ] Tüm görseller başarıyla oluşturuldu ve kaydedildi.")

    except Exception as e:
        print(f"[VIZ] Görsel oluşturma hatası: {e}")

    print("\n" + "="*50)
    print("🏆 SONUÇ ÖZETİ")
    print("="*50)
    print(f"En İyi Model: {best['name']}")
    print(f"En İyi F1 Skoru: {best['f1']:.4f}")
    print(f"Toplam Model Sayısı: {len(tuned_models)}")
    print(f"Veri Boyutu: {df.shape}")
    print(f"Çıktı Klasörü: {outputs.resolve()}")
    print("="*50)

if __name__ == "__main__":
    main()