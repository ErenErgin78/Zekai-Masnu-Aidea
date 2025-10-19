# ============================================================
# 🤖 Crop & Soil — Classification Pipeline
# ============================================================
# Ön hazırlık pipeline'ından sonra çalıştırılacak modelleme kısmı
# - Çoklu sınıflandırma modelleri
# - Cross-validation + hiperparametre optimizasyonu
# - Model değerlendirme ve karşılaştırma
# - En iyi modeli kaydetme
# ============================================================

# ---------- IMPORTS ----------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import sys
import os

# Scikit-learn modelleri
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, f1_score, precision_score, recall_score
)

# ---------- DATA YÜKLEME ----------
def load_cleaned_data():
    """Temizlenmiş veriyi ve objeleri yükler"""
    try:
        # Data_Cleaning modülünden verileri al
        from Data_Cleaning import load_and_clean_data
        df, X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler = load_and_clean_data()
        
        print("✅ Temizlenmiş veri başarıyla yüklendi")
        return df, X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler
    
    except ImportError:
        print("❌ Data_Cleaning modülü bulunamadı, dosyayı doğrudan yüklemeye çalışıyorum...")
        
        # Alternatif: Temizlenmiş CSV'den yükle
        CLEAN_PATH = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea\Backend\API\MachineLearning\Data\Crop_Soil_Final.csv"
        SCALER_PATH = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea\Backend\API\MachineLearning\Data\scaler.pkl"
        
        if os.path.exists(CLEAN_PATH):
            df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig", sep=";")
            print(f"✅ Temizlenmiş veri dosyadan yüklendi: {df.shape}")
            
            # Train-test split
            TARGET_COL = "Crop_Type"
            X = df.drop(columns=[TARGET_COL])
            y = df[TARGET_COL]
            
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42, stratify=y
            )
            
            # Scaler yükle
            if os.path.exists(SCALER_PATH):
                scaler = joblib.load(SCALER_PATH)
                # Scaling uygula
                num_cols = X_train.select_dtypes(include=[np.number]).columns
                X_train_scaled = scaler.transform(X_train[num_cols])
                X_test_scaled = scaler.transform(X_test[num_cols])
            else:
                print("❌ Scaler bulunamadı, scaling uygulanamıyor")
                X_train_scaled, X_test_scaled = None, None
            
            return df, X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler
        else:
            raise FileNotFoundError("Temizlenmiş veri dosyası bulunamadı. Önce Data_Cleaning.py'yi çalıştırın.")

# ---------- 1) MODEL SETUP ----------
def setup_models():
    """Modelleri ve hiperparametre grid'lerini hazırla"""
    
    # Temel modeller
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, multi_class='ovr'),
        'Random Forest': RandomForestClassifier(random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'SVM': SVC(random_state=42, probability=True),
        'K-Nearest Neighbors': KNeighborsClassifier()
    }

    # Hiperparametre grid'leri
    param_grids = {
        'Logistic Regression': {
            'C': [0.1, 1, 10],
            'solver': ['liblinear', 'saga']
        },
        'Random Forest': {
            'n_estimators': [100, 200],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5]
        },
        'Gradient Boosting': {
            'n_estimators': [100, 200],
            'learning_rate': [0.05, 0.1],
            'max_depth': [3, 5]
        },
        'SVM': {
            'C': [0.1, 1, 10],
            'kernel': ['linear', 'rbf']
        },
        'K-Nearest Neighbors': {
            'n_neighbors': [3, 5, 7],
            'weights': ['uniform', 'distance']
        }
    }
    
    return models, param_grids

# ---------- 2) MODEL EĞİTİMİ VE OPTİMİZASYONU ----------
def train_and_evaluate_models(X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, use_scaled=True):
    """Tüm modelleri eğitir, optimize eder ve değerlendirir"""
    
    models, param_grids = setup_models()
    results = {}
    best_models = {}
    
    # Scaling gerektiren modeller
    scaling_models = ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']
    
    for model_name, model in models.items():
        print(f"\n🎯 {model_name} eğitiliyor...")
        
        # Veri seçimi
        if model_name in scaling_models and use_scaled and X_train_scaled is not None:
            X_tr = X_train_scaled
            X_te = X_test_scaled
            print(f"   Scaled data kullanılıyor")
        else:
            X_tr = X_train
            X_te = X_test
            print(f"   Normal data kullanılıyor")
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_tr, y_train, cv=cv, scoring='accuracy')
        
        print(f"   CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Hiperparametre optimizasyonu
        if model_name in param_grids:
            print(f"   Hiperparametre optimizasyonu başlatılıyor...")
            grid_search = GridSearchCV(
                model, param_grids[model_name], 
                cv=5, scoring='accuracy', n_jobs=-1, verbose=0
            )
            grid_search.fit(X_tr, y_train)
            
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_
            
            print(f"   Best params: {best_params}")
            print(f"   Best CV Score: {best_score:.4f}")
        else:
            best_model = model
            best_model.fit(X_tr, y_train)
            best_score = cv_scores.mean()
            best_params = "No optimization"
        
        # Test seti değerlendirmesi
        y_pred = best_model.predict(X_te)
        test_accuracy = accuracy_score(y_test, y_pred)
        test_f1 = f1_score(y_test, y_pred, average='weighted')
        test_precision = precision_score(y_test, y_pred, average='weighted')
        test_recall = recall_score(y_test, y_pred, average='weighted')
        
        print(f"   Test Accuracy: {test_accuracy:.4f}")
        print(f"   Test F1-Score: {test_f1:.4f}")
        
        # Sonuçları kaydet
        results[model_name] = {
            'model': best_model,
            'cv_score': best_score,
            'test_accuracy': test_accuracy,
            'test_f1': test_f1,
            'test_precision': test_precision,
            'test_recall': test_recall,
            'best_params': best_params
        }
        
        best_models[model_name] = best_model
    
    return results, best_models

# ---------- 3) MODEL KARŞILAŞTIRMA ----------
def compare_models(results):
    """Modelleri görsel olarak karşılaştır"""
    metrics_df = pd.DataFrame({
        'Model': list(results.keys()),
        'CV_Score': [results[m]['cv_score'] for m in results],
        'Test_Accuracy': [results[m]['test_accuracy'] for m in results],
        'Test_F1': [results[m]['test_f1'] for m in results]
    }).sort_values('Test_Accuracy', ascending=False)
    
    print("\n" + "="*60)
    print("🏆 MODEL KARŞILAŞTIRMA SONUÇLARI")
    print("="*60)
    print(metrics_df.round(4))
    
    # Görselleştirme
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Accuracy karşılaştırması
    metrics_df.set_index('Model')[['CV_Score', 'Test_Accuracy']].plot(
        kind='bar', ax=axes[0], color=['skyblue', 'lightcoral']
    )
    axes[0].set_title('Model Performans Karşılaştırması\nCV Score vs Test Accuracy')
    axes[0].set_ylabel('Score')
    axes[0].tick_params(axis='x', rotation=45)
    
    # F1-Score karşılaştırması
    metrics_df.set_index('Model')['Test_F1'].plot(
        kind='bar', ax=axes[1], color='lightgreen'
    )
    axes[1].set_title('Model F1-Score Karşılaştırması\n(Weighted)')
    axes[1].set_ylabel('F1-Score')
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    return metrics_df

# ---------- 4) EN İYİ MODEL DEĞERLENDİRMESİ ----------
def evaluate_best_model(best_model, best_model_name, X_test, X_test_scaled, y_test):
    """En iyi modeli detaylı değerlendir"""
    
    print(f"\n⭐ EN İYİ MODEL: {best_model_name}")
    
    # Doğru veri setini seç
    if best_model_name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
        X_te_eval = X_test_scaled
    else:
        X_te_eval = X_test

    y_pred_best = best_model.predict(X_te_eval)

    print(f"📊 Test Accuracy: {accuracy_score(y_test, y_pred_best):.4f}")
    print(f"🎯 Test F1-Score: {f1_score(y_test, y_pred_best, average='weighted'):.4f}")

    print("\n📋 DETAYLI CLASSIFICATION REPORT:")
    print(classification_report(y_test, y_pred_best))

    # Confusion Matrix
    plt.figure(figsize=(10, 8))
    cm = confusion_matrix(y_test, y_pred_best)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=np.unique(y_test), 
                yticklabels=np.unique(y_test))
    plt.title(f'Confusion Matrix - {best_model_name}')
    plt.xlabel('Tahmin Edilen')
    plt.ylabel('Gerçek Değer')
    plt.tight_layout()
    plt.show()
    
    return y_pred_best

# ---------- 5) FEATURE IMPORTANCE ----------
def plot_feature_importance(best_model, best_model_name, X_train):
    """Feature importance grafiği çiz"""
    if hasattr(best_model, 'feature_importances_'):
        plt.figure(figsize=(10, 6))
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=True)
        
        plt.barh(feature_importance['feature'], feature_importance['importance'])
        plt.title(f'{best_model_name} - Feature Importance')
        plt.xlabel('Importance')
        plt.tight_layout()
        plt.show()
        
        print("\n🔍 EN ÖNEMLİ 10 FEATURE:")
        print(feature_importance.tail(10).sort_values('importance', ascending=False))
    else:
        print(f"⚠ {best_model_name} modeli feature_importance_ attribute'una sahip değil")

# ---------- 6) MODEL KAYDETME ----------
def save_pipeline(best_model, scaler, results, file_prefix='crop_soil'):
    """Eğitilmiş pipeline'ı kaydet"""
    
    # Modeli kaydet
    model_path = f"{file_prefix}_best_model.pkl"
    joblib.dump(best_model, model_path)
    
    # Scaler'ı kaydet
    scaler_path = f"{file_prefix}_scaler.pkl"
    joblib.dump(scaler, scaler_path)
    
    # Sonuçları kaydet
    results_path = f"{file_prefix}_training_results.csv"
    pd.DataFrame(results).T.to_csv(results_path)
    
    print(f"\n💾 MODEL KAYDEDİLDİ:")
    print(f"   Model: {model_path}")
    print(f"   Scaler: {scaler_path}")
    print(f"   Results: {results_path}")

# ---------- 7) TAHMİN FONKSİYONU ----------
def predict_new_sample(model, scaler, sample_data, feature_names):
    """Yeni örnekler için tahmin yapar"""
    # DataFrame'e çevir
    sample_df = pd.DataFrame([sample_data], columns=feature_names)
    
    # Scaling gerektiren model mi kontrol et
    model_name = type(model).__name__
    scaling_models = ['LogisticRegression', 'SVC', 'KNeighborsClassifier']
    
    if model_name in scaling_models:
        # Sayısal sütunları scale et
        num_cols = sample_df.select_dtypes(include=[np.number]).columns
        sample_df[num_cols] = scaler.transform(sample_df[num_cols])
    
    # Tahmin yap
    prediction = model.predict(sample_df)
    probability = model.predict_proba(sample_df) if hasattr(model, 'predict_proba') else None
    
    return prediction[0], probability[0] if probability is not None else None

# ---------- ANA İŞLEM FONKSİYONU ----------
def main():
    """Ana model eğitimi fonksiyonu"""
    print("🚀 Model eğitimi başlatılıyor...")
    
    # Veriyi yükle
    df, X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler = load_cleaned_data()
    
    # Model eğitimi
    results, best_models = train_and_evaluate_models(
        X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, use_scaled=True
    )
    
    # Model karşılaştırma
    metrics_comparison = compare_models(results)
    
    # En iyi modeli seç
    best_model_name = metrics_comparison.iloc[0]['Model']
    best_model = best_models[best_model_name]
    
    # En iyi modeli değerlendir
    y_pred_best = evaluate_best_model(best_model, best_model_name, X_test, X_test_scaled, y_test)
    
    # Feature importance
    plot_feature_importance(best_model, best_model_name, X_train)
    
    # Modeli kaydet
    save_pipeline(best_model, scaler, results, 'crop_soil')
    
    # Örnek tahmin
    print("\n🔮 ÖRNEK TAHMİN:")
    sample_features = {
        'Temperature': 25.0,
        'Humidity': 60.0,
        'Moisture': 45.0,
        'Nitrogen': 20.0,
        'Potassium': 15.0,
        'Phosphorous': 10.0
    }

    # One-hot encoded sütunları ekle (örnek)
    for col in X_train.columns:
        if col not in sample_features and col in ['Soil Type_Sandy', 'Fertilizer Name_Urea']:
            sample_features[col] = 1 if 'Sandy' in col or 'Urea' in col else 0

    prediction, probabilities = predict_new_sample(best_model, scaler, sample_features, X_train.columns)
    print(f"Örnek veri tahmini: {prediction}")
    if probabilities is not None:
        print(f"Sınıf olasılıkları: {dict(zip(best_model.classes_, probabilities.round(4)))}")
    
    # Sonuç özeti
    print("\n" + "="*60)
    print("✅ MODELLEME SÜRECİ TAMAMLANDI")
    print("="*60)
    print(f"🏆 En İyi Model: {best_model_name}")
    print(f"📈 Test Doğruluğu: {results[best_model_name]['test_accuracy']:.4f}")
    print(f"🎯 Test F1-Score: {results[best_model_name]['test_f1']:.4f}")
    print(f"📚 Toplam Model Sayısı: {len(results)}")
    print(f"🔢 Eğitim Örnekleri: {X_train.shape[0]}")
    print(f"🧪 Test Örnekleri: {X_test.shape[0]}")
    print(f"🎯 Sınıf Sayısı: {len(np.unique(y_train))}")
    print("="*60)

# Program başlangıcı
if __name__ == "__main__":
    main()