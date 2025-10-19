# ============================================================
# 🌲 Random Forest — Crop Recommendation Model (Enhanced)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, 
    classification_report, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
import warnings
warnings.filterwarnings('ignore')

# ---------- 1. Veri Yükleme ----------
FILE_PATH = r"C:\Users\HUSOCAN\Desktop\Projelerim\Zekai-Masnu-Aidea\Backend\API\MachineLearning\Data\Crop_recommendation_cleaned.csv"
df = pd.read_csv(FILE_PATH)

print("✅ Veri yüklendi:", df.shape)
print("🧾 Sütunlar:", df.columns.tolist())
print("🌱 Eşsiz ürünler:", df['label'].nunique())
print(df['label'].value_counts())

# ---------- 2. Sayısal dönüşüm kontrolü ----------
numeric_cols = df.columns.drop('label')

for col in numeric_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors='coerce')

print("\n📊 Veri tipleri (dönüşüm sonrası):")
print(df.dtypes)

# ---------- 3. X / y Ayırma ve Encoding ----------
X = df.drop(columns=['label'])
y = df['label']

# Label encoding for better visualization
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ---------- 4. Train-Test Split ----------
X_train, X_test, y_train, y_test, y_train_encoded, y_test_encoded = train_test_split(
    X, y, y_encoded, test_size=0.2, random_state=42, stratify=y
)
print(f"📊 Train: {X_train.shape}, Test: {X_test.shape}")

# ---------- 5. Scaling ----------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✅ Scaling uygulandı")

# ---------- 6. Çoklu Model Tanımlama ----------
def get_models():
    """Farklı sınıflandırma modellerini döndürür"""
    models = {
        'Random Forest': RandomForestClassifier(random_state=42, n_jobs=-1),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, multi_class='ovr'),
        'SVM': SVC(random_state=42, probability=True),
        'K-Nearest Neighbors': KNeighborsClassifier(n_jobs=-1)
    }
    return models

# ---------- 7. Hiperparametre Grid'leri ----------
def get_param_grids():
    """Her model için hiperparametre grid'lerini döndürür"""
    param_grids = {
        'Random Forest': {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2']
        },
        'Decision Tree': {
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'criterion': ['gini', 'entropy']
        },
        'Logistic Regression': {
            'C': [0.1, 1, 10, 100],
            'solver': ['liblinear', 'saga'],
            'penalty': ['l1', 'l2']
        },
        'SVM': {
            'C': [0.1, 1, 10, 100],
            'kernel': ['linear', 'rbf', 'poly'],
            'gamma': ['scale', 'auto']
        },
        'K-Nearest Neighbors': {
            'n_neighbors': [3, 5, 7, 9, 11],
            'weights': ['uniform', 'distance'],
            'metric': ['euclidean', 'manhattan', 'minkowski']
        }
    }
    return param_grids

# ---------- 8. Cross Validation Fonksiyonu ----------
def perform_cross_validation(models, X, y, cv=5):
    """Her model için cross validation skorlarını hesaplar"""
    cv_results = {}
    cv = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    
    for name, model in models.items():
        print(f"🔍 {name} için Cross Validation yapılıyor...")
        
        # Scaling gerektiren modeller için kontrol
        if name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
            X_data = X_train_scaled
        else:
            X_data = X_train
            
        cv_scores = cross_val_score(model, X_data, y, cv=cv, scoring='accuracy', n_jobs=-1)
        cv_results[name] = {
            'mean_score': cv_scores.mean(),
            'std_score': cv_scores.std(),
            'all_scores': cv_scores
        }
        print(f"   {name} CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    return cv_results

# ---------- 9. Hiperparametre Optimizasyonu ----------
def perform_hyperparameter_tuning(models, param_grids, X, y):
    """Her model için GridSearchCV ile hiperparametre optimizasyonu"""
    best_models = {}
    tuning_results = {}
    
    for name, model in models.items():
        print(f"\n🎯 {name} için Hiperparametre Optimizasyonu...")
        
        if name not in param_grids:
            print(f"   ⚠ {name} için parametre grid tanımlı değil, normal eğitim yapılıyor...")
            if name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
                model.fit(X_train_scaled, y_train)
            else:
                model.fit(X_train, y_train)
            best_models[name] = model
            tuning_results[name] = {'best_score': None, 'best_params': 'No optimization'}
            continue
        
        # Scaling gerektiren modeller için kontrol
        if name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
            X_data = X_train_scaled
        else:
            X_data = X_train
            
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grids[name],
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_data, y_train)
        
        best_models[name] = grid_search.best_estimator_
        tuning_results[name] = {
            'best_score': grid_search.best_score_,
            'best_params': grid_search.best_params_
        }
        
        print(f"   ✅ En iyi parametreler: {grid_search.best_params_}")
        print(f"   🏆 En iyi CV skoru: {grid_search.best_score_:.4f}")
    
    return best_models, tuning_results

# ---------- 10. Model Değerlendirme ----------
def evaluate_models(best_models, X_test, X_test_scaled, y_test):
    """Optimize edilmiş modelleri test setinde değerlendirir"""
    evaluation_results = {}
    
    for name, model in best_models.items():
        print(f"\n📊 {name} Değerlendiriliyor...")
        
        # Scaling gerektiren modeller için kontrol
        if name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
            X_test_data = X_test_scaled
        else:
            X_test_data = X_test
        
        y_pred = model.predict(X_test_data)
        y_pred_proba = model.predict_proba(X_test_data) if hasattr(model, 'predict_proba') else None
        
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        
        evaluation_results[name] = {
            'accuracy': accuracy,
            'f1_score': f1,
            'precision': precision,
            'recall': recall,
            'predictions': y_pred,
            'probabilities': y_pred_proba
        }
        
        print(f"   ✅ Test Accuracy: {accuracy:.4f}")
        print(f"   🎯 Test F1-Score: {f1:.4f}")
        print(f"   📍 Test Precision: {precision:.4f}")
        print(f"   🔄 Test Recall: {recall:.4f}")
    
    return evaluation_results

# ---------- 11. Model Karşılaştırma Görselleştirme ----------
def plot_model_comparison(evaluation_results, cv_results):
    """Modellerin performanslarını karşılaştıran grafikler oluşturur"""
    models = list(evaluation_results.keys())
    
    # Metrikleri hazırla
    test_accuracies = [evaluation_results[m]['accuracy'] for m in models]
    test_f1_scores = [evaluation_results[m]['f1_score'] for m in models]
    cv_accuracies = [cv_results[m]['mean_score'] if m in cv_results else 0 for m in models]
    
    # DataFrame oluştur
    comparison_df = pd.DataFrame({
        'Model': models,
        'Test_Accuracy': test_accuracies,
        'Test_F1_Score': test_f1_scores,
        'CV_Accuracy': cv_accuracies
    }).sort_values('Test_Accuracy', ascending=False)
    
    print("\n" + "="*70)
    print("🏆 MODEL PERFORMANS KARŞILAŞTIRMASI")
    print("="*70)
    print(comparison_df.round(4))
    
    # Grafikleri çiz
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Test Accuracy Karşılaştırması
    axes[0, 0].barh(comparison_df['Model'], comparison_df['Test_Accuracy'], color='skyblue')
    axes[0, 0].set_title('Test Accuracy Karşılaştırması\n(En İyiden En Kötüye)', fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('Accuracy')
    for i, v in enumerate(comparison_df['Test_Accuracy']):
        axes[0, 0].text(v + 0.01, i, f'{v:.3f}', va='center')
    
    # Test vs CV Accuracy
    x = np.arange(len(models))
    width = 0.35
    axes[0, 1].bar(x - width/2, comparison_df['Test_Accuracy'], width, label='Test Accuracy', alpha=0.7)
    axes[0, 1].bar(x + width/2, comparison_df['CV_Accuracy'], width, label='CV Accuracy', alpha=0.7)
    axes[0, 1].set_title('Test vs Cross-Validation Accuracy Karşılaştırması', fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Modeller')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(models, rotation=45, ha='right')
    axes[0, 1].legend()
    
    # F1-Score Karşılaştırması
    axes[1, 0].bar(comparison_df['Model'], comparison_df['Test_F1_Score'], color='lightgreen', alpha=0.7)
    axes[1, 0].set_title('Test F1-Score Karşılaştırması\n(Weighted)', fontsize=14, fontweight='bold')
    axes[1, 0].set_xlabel('Modeller')
    axes[1, 0].set_ylabel('F1-Score')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Precision-Recall Karşılaştırması
    precision_vals = [evaluation_results[m]['precision'] for m in models]
    recall_vals = [evaluation_results[m]['recall'] for m in models]
    
    axes[1, 1].bar(x - width/2, precision_vals, width, label='Precision', alpha=0.7, color='orange')
    axes[1, 1].bar(x + width/2, recall_vals, width, label='Recall', alpha=0.7, color='purple')
    axes[1, 1].set_title('Precision vs Recall Karşılaştırması\n(Weighted)', fontsize=14, fontweight='bold')
    axes[1, 1].set_xlabel('Modeller')
    axes[1, 1].set_ylabel('Score')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(models, rotation=45, ha='right')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.show()
    
    return comparison_df

# ---------- 12. En İyi Model Detaylı Analiz ----------
def detailed_best_model_analysis(best_model, best_model_name, X_test, X_test_scaled, y_test, le):
    """En iyi model için detaylı analiz yapar"""
    print(f"\n⭐ EN İYİ MODEL DETAYLI ANALİZ: {best_model_name}")
    print("="*60)
    
    # Doğru veri setini seç
    if best_model_name in ['Logistic Regression', 'SVM', 'K-Nearest Neighbors']:
        X_test_data = X_test_scaled
    else:
        X_test_data = X_test
    
    # Tahminler
    y_pred = best_model.predict(X_test_data)
    y_pred_original = le.inverse_transform(y_pred)
    y_test_original = le.inverse_transform(y_test)
    
    # Detaylı metrikler
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    
    print(f"📊 Test Accuracy: {accuracy:.4f}")
    print(f"🎯 Test F1-Score: {f1:.4f}")
    print(f"📍 Test Precision: {precision:.4f}")
    print(f"🔁 Test Recall: {recall:.4f}")
    
    # Classification Report
    print("\n📋 DETAYLI CLASSIFICATION REPORT:")
    print(classification_report(y_test_original, y_pred_original))
    
    # Confusion Matrix
    plt.figure(figsize=(12, 10))
    cm = confusion_matrix(y_test_original, y_pred_original)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=le.classes_, 
                yticklabels=le.classes_)
    plt.title(f'Confusion Matrix - {best_model_name}\n', fontsize=16, fontweight='bold')
    plt.xlabel('Tahmin Edilen Ürün')
    plt.ylabel('Gerçek Ürün')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
    
    return y_pred_original

# ---------- 13. Feature Importance Görselleştirme ----------
def plot_feature_importance(best_model, best_model_name, feature_names):
    """En iyi model için feature importance grafiği çizer"""
    if hasattr(best_model, 'feature_importances_'):
        plt.figure(figsize=(10, 8))
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        # Feature importance DataFrame
        feature_importance_df = pd.DataFrame({
            'feature': feature_names[indices],
            'importance': importances[indices]
        })
        
        # Grafik
        plt.barh(range(len(importances)), importances[indices], color='green', alpha=0.7)
        plt.yticks(range(len(importances)), feature_names[indices])
        plt.title(f'{best_model_name} - Feature Importance\n', fontsize=16, fontweight='bold')
        plt.xlabel('Importance Score')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        print("\n🔍 EN ÖNEMLİ 10 FEATURE:")
        print(feature_importance_df.head(10).round(4))
        
        return feature_importance_df
    else:
        print(f"⚠ {best_model_name} modeli feature_importance_ attribute'una sahip değil")
        return None

# ---------- 14. Model Kaydetme ----------
def save_best_model(best_model, best_model_name, scaler, le, results_df):
    """En iyi modeli ve diğer bileşenleri kaydeder"""
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f"best_model_{best_model_name.replace(' ', '_')}_{timestamp}.pkl"
    scaler_filename = f"scaler_{timestamp}.pkl"
    encoder_filename = f"label_encoder_{timestamp}.pkl"
    results_filename = f"model_results_{timestamp}.csv"
    
    # Modeli kaydet
    joblib.dump(best_model, model_filename)
    joblib.dump(scaler, scaler_filename)
    joblib.dump(le, encoder_filename)
    results_df.to_csv(results_filename, index=False)
    
    print(f"\n💾 MODELLER KAYDEDİLDİ:")
    print(f"   📁 Model: {model_filename}")
    print(f"   📁 Scaler: {scaler_filename}")
    print(f"   📁 Label Encoder: {encoder_filename}")
    print(f"   📁 Results: {results_filename}")

# ---------- 15. Ana İşlem Akışı ----------
def main():
    """Ana model eğitimi ve değerlendirme fonksiyonu"""
    print("🚀 GELİŞMİŞ SINIFLANDIRMA MODEL EĞİTİMİ BAŞLATILIYOR...")
    print("="*70)
    
    # Modelleri ve parametre grid'lerini al
    models = get_models()
    param_grids = get_param_grids()
    
    # 1. Cross Validation
    print("\n1️⃣ CROSS VALIDATION AŞAMASI")
    print("-" * 50)
    cv_results = perform_cross_validation(models, X_train, y_train_encoded, cv=5)
    
    # 2. Hiperparametre Optimizasyonu
    print("\n2️⃣ HİPERPARAMETRE OPTİMİZASYONU AŞAMASI")
    print("-" * 50)
    best_models, tuning_results = perform_hyperparameter_tuning(models, param_grids, X_train, y_train_encoded)
    
    # 3. Model Değerlendirme
    print("\n3️⃣ MODEL DEĞERLENDİRME AŞAMASI")
    print("-" * 50)
    evaluation_results = evaluate_models(best_models, X_test, X_test_scaled, y_test_encoded)
    
    # 4. Model Karşılaştırma
    print("\n4️⃣ MODEL KARŞILAŞTIRMA AŞAMASI")
    print("-" * 50)
    comparison_df = plot_model_comparison(evaluation_results, cv_results)
    
    # 5. En İyi Model Seçimi ve Detaylı Analiz
    best_model_name = comparison_df.iloc[0]['Model']
    best_model = best_models[best_model_name]
    
    print(f"\n🏆 EN İYİ MODEL SEÇİLDİ: {best_model_name}")
    print(f"📈 Test Accuracy: {comparison_df.iloc[0]['Test_Accuracy']:.4f}")
    print(f"🎯 Test F1-Score: {comparison_df.iloc[0]['Test_F1_Score']:.4f}")
    
    # Detaylı analiz
    y_pred_best = detailed_best_model_analysis(best_model, best_model_name, X_test, X_test_scaled, y_test_encoded, le)
    
    # Feature importance
    if best_model_name in ['Random Forest', 'Decision Tree']:
        feature_importance_df = plot_feature_importance(best_model, best_model_name, X.columns.values)
    
    # Model kaydetme
    save_best_model(best_model, best_model_name, scaler, le, comparison_df)
    
    # Sonuç özeti
    print("\n" + "="*70)
    print("✅ MODELLEME SÜRECİ TAMAMLANDI")
    print("="*70)
    print(f"🏆 En İyi Model: {best_model_name}")
    print(f"📈 Test Doğruluğu: {comparison_df.iloc[0]['Test_Accuracy']:.4f}")
    print(f"🎯 Test F1-Score: {comparison_df.iloc[0]['Test_F1_Score']:.4f}")
    print(f"📚 Toplam Model Sayısı: {len(models)}")
    print(f"🔢 Eğitim Örnekleri: {X_train.shape[0]}")
    print(f"🧪 Test Örnekleri: {X_test.shape[0]}")
    print(f"🌱 Ürün Çeşit Sayısı: {len(le.classes_)}")
    print("="*70)

# Program başlangıcı
if __name__ == "__main__":
    main()