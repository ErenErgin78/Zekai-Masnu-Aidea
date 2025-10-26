#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Label Makine Öğrenmesi Analiz Scripti
final5.csv dosyasına Binary Relevance ile multi-label classification uygular
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, hamming_loss, jaccard_score
from sklearn.multioutput import MultiOutputClassifier
import warnings
warnings.filterwarnings('ignore')

# Model dosyalarının yolu
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "Backend", "API", "MachineLearning", "Code", "model_outputs")

def train_multi_label_models(X, y_multi_label, crop_names):
    """Multi-label modelleri eğitir - Binary Relevance ile"""
    print("🔄 Multi-label model eğitimi başlıyor...")
    
    try:
        from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
        from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, AdaBoostClassifier, BaggingClassifier
        from sklearn.linear_model import LogisticRegression, RidgeClassifier, SGDClassifier
        from sklearn.svm import SVC
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.naive_bayes import GaussianNB
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
        from sklearn.neural_network import MLPClassifier
        import xgboost as xgb
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_multi_label, test_size=0.2, random_state=42
        )
        
        # Feature scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print(f"📊 Eğitim seti: {X_train.shape[0]} örnek")
        print(f"📊 Test seti: {X_test.shape[0]} örnek")
        print(f"📊 Label sayısı: {y_multi_label.shape[1]}")
        
        # Farklı algoritmalar
        models_and_params = {
            'RandomForest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'estimator__n_estimators': [50, 100],
                    'estimator__max_depth': [None, 10, 20],
                    'estimator__min_samples_split': [2, 5]
                }
            },
            'LogisticRegression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {
                    'estimator__C': [0.1, 1, 10],
                    'estimator__penalty': ['l1', 'l2'],
                    'estimator__solver': ['liblinear', 'saga']
                }
            },
            'SVM': {
                'model': SVC(random_state=42, probability=True),
                'params': {
                    'estimator__C': [0.1, 1, 10],
                    'estimator__kernel': ['rbf', 'poly'],
                    'estimator__gamma': ['scale', 'auto']
                }
            },
            'XGBoost': {
                'model': xgb.XGBClassifier(random_state=42, eval_metric='mlogloss'),
                'params': {
                    'estimator__n_estimators': [50, 100],
                    'estimator__max_depth': [3, 6],
                    'estimator__learning_rate': [0.1, 0.2]
                }
            },
            'ExtraTrees': {
                'model': ExtraTreesClassifier(random_state=42),
                'params': {
                    'estimator__n_estimators': [50, 100],
                    'estimator__max_depth': [None, 10, 20],
                    'estimator__min_samples_split': [2, 5]
                }
            },
            'GradientBoosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'estimator__n_estimators': [50, 100],
                    'estimator__max_depth': [3, 5],
                    'estimator__learning_rate': [0.1, 0.2]
                }
            },
            'KNN': {
                'model': KNeighborsClassifier(),
                'params': {
                    'estimator__n_neighbors': [3, 5, 7],
                    'estimator__weights': ['uniform', 'distance'],
                    'estimator__metric': ['euclidean', 'manhattan']
                }
            },
            'DecisionTree': {
                'model': DecisionTreeClassifier(random_state=42),
                'params': {
                    'estimator__max_depth': [None, 10, 20],
                    'estimator__min_samples_split': [2, 5],
                    'estimator__min_samples_leaf': [1, 2]
                }
            }
        }
        
        best_model = None
        best_score = 0
        best_name = ""
        results = {}
        
        print(f"🔄 {len(models_and_params)} farklı algoritma test edilecek...")
        
        for i, (name, config) in enumerate(models_and_params.items(), 1):
            print(f"\n[{i}/{len(models_and_params)}] 🔄 {name} eğitiliyor...")
            
            try:
                # SVM için özel kontrol - tek sınıflı label'ları kontrol et
                if name == 'SVM':
                    # y_train'i numpy array'e çevir
                    y_train_array = np.array(y_train)
                    
                    # Her label için sınıf sayısını kontrol et
                    single_class_labels = []
                    for i in range(y_train_array.shape[1]):
                        unique_classes = np.unique(y_train_array[:, i])
                        if len(unique_classes) == 1:
                            single_class_labels.append(i)
                    
                    if len(single_class_labels) > 0:
                        print(f"   ⚠️ {len(single_class_labels)} label tek sınıflı, SVM atlanıyor...")
                        continue
                
                # Multi-output classifier
                multi_model = MultiOutputClassifier(config['model'], n_jobs=-1)
                
                # Grid search
                grid_search = GridSearchCV(
                    multi_model, 
                    config['params'], 
                    cv=3,  # 3-fold CV
                    scoring='f1_macro',
                    n_jobs=-1,
                    verbose=0
                )
                
                # Modeli eğit
                grid_search.fit(X_train_scaled, y_train)
                
                # En iyi modeli al
                best_model_cv = grid_search.best_estimator_
                
                # Tahminler
                y_pred = best_model_cv.predict(X_test_scaled)
                
                # Metrikler
                accuracy = accuracy_score(y_test, y_pred)
                f1_micro = f1_score(y_test, y_pred, average='micro')
                f1_macro = f1_score(y_test, y_pred, average='macro')
                hamming = hamming_loss(y_test, y_pred)
                jaccard = jaccard_score(y_test, y_pred, average='macro', zero_division=0)
                
                results[name] = {
                    'accuracy': accuracy,
                    'f1_micro': f1_micro,
                    'f1_macro': f1_macro,
                    'hamming_loss': hamming,
                    'jaccard_score': jaccard,
                    'best_params': grid_search.best_params_,
                    'model': best_model_cv,
                    'predictions': y_pred
                }
                
                print(f"✅ {name}:")
                print(f"   Accuracy: {accuracy:.4f}")
                print(f"   F1-Micro: {f1_micro:.4f}")
                print(f"   F1-Macro: {f1_macro:.4f}")
                print(f"   Hamming Loss: {hamming:.4f}")
                print(f"   Jaccard Score: {jaccard:.4f}")
                
                # En iyi modeli güncelle (F1-Macro'ya göre)
                if f1_macro > best_score:
                    best_score = f1_macro
                    best_model = best_model_cv
                    best_name = name
                    
            except Exception as e:
                print(f"❌ {name} hatası: {e}")
                results[name] = {'error': str(e)}
        
        print(f"\n🏆 En iyi model: {best_name} (F1-Macro: {best_score:.4f})")
        
        # Sonuçları sırala
        successful_results = {k: v for k, v in results.items() if 'error' not in v}
        sorted_results = sorted(successful_results.items(), key=lambda x: x[1]['f1_macro'], reverse=True)
        
        print("\n📊 MODEL SIRALAMASI (F1-Macro'ya göre):")
        for i, (name, result) in enumerate(sorted_results, 1):
            print(f"{i:2d}. {name:20s} - F1-Macro: {result['f1_macro']:.4f}, Accuracy: {result['accuracy']:.4f}")
        
        # Metadata oluştur
        metadata = {
            'best_model': best_name,
            'best_f1_macro': best_score,
            'feature_names': list(X.columns),
            'crop_names': crop_names,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'all_results': results,
            'top_models': sorted_results[:3]  # En iyi 3 model
        }
        
        # En iyi modeli kaydet
        model_save_path = os.path.join(os.path.dirname(__file__), "multi_label_model.pkl")
        
        complete_model = {
            'model': best_model,
            'scaler': scaler,
            'metadata': metadata
        }
        
        joblib.dump(complete_model, model_save_path)
        print(f"✅ En iyi model kaydedildi: {model_save_path}")
        
        return best_model, scaler, metadata, results, X_test, y_test
        
    except Exception as e:
        print(f"❌ Model eğitimi hatası: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, None

def prepare_multi_label_data(df):
    """Multi-label veriyi hazırlar"""
    print("🔄 Multi-label veri hazırlama başlıyor...")
    
    # Label sütunlarını ayır
    label_columns = [col for col in df.columns if col.startswith('label_')]
    feature_columns = [col for col in df.columns if not col.startswith('label_')]
    
    print(f"📊 Özellik sütunları: {len(feature_columns)}")
    print(f"📊 Label sütunları: {len(label_columns)}")
    
    # Özellikler ve label'ları ayır
    X = df[feature_columns]
    y_multi_label = df[label_columns]
    
    # Crop isimlerini çıkar
    crop_names = [col.replace('label_', '') for col in label_columns]
    
    print(f"📊 Özellik sayısı: {X.shape[1]}")
    print(f"📊 Örnek sayısı: {X.shape[0]}")
    print(f"🌱 Ürün sayısı: {len(crop_names)}")
    
    # Tek sınıflı label'ları kontrol et
    single_class_labels = []
    for i, crop in enumerate(crop_names):
        unique_values = np.unique(y_multi_label.iloc[:, i])
        if len(unique_values) == 1:
            single_class_labels.append(crop)
    
    if single_class_labels:
        print(f"⚠️ Tek sınıflı ürünler bulundu: {single_class_labels}")
        print("Bu ürünler analizden çıkarılacak...")
        
        # Tek sınıflı label'ları çıkar
        valid_labels = []
        for i, crop in enumerate(crop_names):
            if crop not in single_class_labels:
                valid_labels.append(i)
        
        y_multi_label = y_multi_label.iloc[:, valid_labels]
        crop_names = [crop for crop in crop_names if crop not in single_class_labels]
        
        print(f"✅ Geçerli ürün sayısı: {len(crop_names)}")
    else:
        print("✅ Tüm ürünler çok sınıflı")
    
    # Kategorik sütunları sayısal değerlere dönüştür
    categorical_columns = X.select_dtypes(include=['object']).columns
    if len(categorical_columns) > 0:
        print(f"🔄 Kategorik sütunlar işleniyor: {list(categorical_columns)}")
        for col in categorical_columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            print(f"✅ {col} sütunu sayısal değerlere dönüştürüldü")
    else:
        print("✅ Kategorik sütun bulunamadı")
    
    # Tüm sütunları sayısal tipe dönüştür
    X = X.astype(float)
    
    # Eksik değerleri kontrol et ve doldur
    print(f"🔍 Eksik değer kontrolü:")
    missing_values = X.isnull().sum()
    if missing_values.sum() > 0:
        print("⚠️ Eksik değerler bulundu, ortalama ile dolduruluyor...")
        X = X.fillna(X.mean())
    else:
        print("✅ Eksik değer yok")
    
    # Sonsuz değerleri kontrol et
    inf_values = np.isinf(X.select_dtypes(include=[np.number])).sum()
    if inf_values.sum() > 0:
        print("⚠️ Sonsuz değerler bulundu, NaN ile değiştiriliyor...")
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.mean())
    
    return X, y_multi_label, crop_names

def generate_multi_label_report(results, crop_names, X_test, y_test):
    """Multi-label analiz raporu oluşturur"""
    print("\n📝 Multi-label raporu oluşturuluyor...")
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("BINARY RELEVANCE MULTI-LABEL CLASSIFICATION RAPORU")
    report_lines.append("=" * 80)
    report_lines.append(f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Toplam Ürün Sayısı: {len(crop_names)}")
    report_lines.append("")
    
    # Model karşılaştırması
    report_lines.append("MODEL KARŞILAŞTIRMASI")
    report_lines.append("-" * 40)
    
    successful_results = {k: v for k, v in results.items() if 'error' not in v}
    sorted_results = sorted(successful_results.items(), key=lambda x: x[1]['f1_macro'], reverse=True)
    
    for i, (name, result) in enumerate(sorted_results, 1):
        report_lines.append(f"{i}. {name}")
        report_lines.append(f"   Accuracy: {result['accuracy']:.4f}")
        report_lines.append(f"   F1-Micro: {result['f1_micro']:.4f}")
        report_lines.append(f"   F1-Macro: {result['f1_macro']:.4f}")
        report_lines.append(f"   Hamming Loss: {result['hamming_loss']:.4f}")
        report_lines.append(f"   Jaccard Score: {result['jaccard_score']:.4f}")
        report_lines.append("")
    
    # Ürün bazlı performans
    if successful_results:
        best_model_name = sorted_results[0][0]
        best_result = successful_results[best_model_name]
        
        report_lines.append("ÜRÜN BAZLI PERFORMANS")
        report_lines.append("-" * 40)
        
        y_pred = best_result['predictions']
        
        # y_test'i numpy array'e çevir
        y_test_array = np.array(y_test)
        
        for i, crop in enumerate(crop_names):
            true_positives = np.sum((y_test_array[:, i] == 1) & (y_pred[:, i] == 1))
            false_positives = np.sum((y_test_array[:, i] == 0) & (y_pred[:, i] == 1))
            false_negatives = np.sum((y_test_array[:, i] == 1) & (y_pred[:, i] == 0))
            true_negatives = np.sum((y_test_array[:, i] == 0) & (y_pred[:, i] == 0))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            report_lines.append(f"{crop}:")
            report_lines.append(f"   Precision: {precision:.4f}")
            report_lines.append(f"   Recall: {recall:.4f}")
            report_lines.append(f"   F1-Score: {f1:.4f}")
            report_lines.append(f"   True Positives: {true_positives}")
            report_lines.append("")
    
    report_lines.append("=" * 80)
    report_lines.append("RAPOR SONU")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main():
    """Ana fonksiyon"""
    print("🚀 Multi-Label Makine Öğrenmesi Analizi Başlıyor...")
    print("=" * 60)
    
    try:
        # CSV dosyasını yükle
        csv_path = os.path.join(os.path.dirname(__file__), "final5.csv")
        print(f"📁 CSV dosyası yükleniyor: {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"✅ CSV yüklendi: {df.shape[0]} satır, {df.shape[1]} sütun")
        
        # Multi-label veriyi hazırla
        X, y_multi_label, crop_names = prepare_multi_label_data(df)
        
        # Multi-label modelleri eğit
        best_model, scaler, metadata, results, X_test, y_test = train_multi_label_models(
            X, y_multi_label, crop_names
        )
        
        if best_model is None:
            print("❌ Model eğitilemedi, işlem durduruluyor")
            return
        
        # Rapor oluştur
        report_content = generate_multi_label_report(results, crop_names, X_test, y_test)
        
        # Raporu dosyaya yaz
        report_path = os.path.join(os.path.dirname(__file__), "multi_label_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Rapor oluşturuldu: {report_path}")
        
        # Özet istatistikler
        print("\n📊 ÖZET İSTATİSTİKLER")
        print("-" * 30)
        print(f"Toplam Örnek: {len(X)}")
        print(f"Toplam Ürün: {len(crop_names)}")
        print(f"En İyi Model: {metadata['best_model']}")
        print(f"En İyi F1-Macro: {metadata['best_f1_macro']:.4f}")
        
        print("\n🎉 Multi-label analiz tamamlandı!")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
