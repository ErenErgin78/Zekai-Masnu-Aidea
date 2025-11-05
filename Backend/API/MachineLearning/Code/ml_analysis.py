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

# Görselleştirme için opsiyonel importlar (kurulu değilse script çalışmaya devam eder)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except Exception:
    HAS_PLOTTING = False

# Model dosyalarının yolu
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "Backend", "API", "MachineLearning", "Code", "model_outputs")

def train_multi_label_models(X, y_multi_label, crop_names):
    """Multi-label modelleri eğitir - Binary Relevance ile

    Bu fonksiyon eğitim/test ayrımı, ölçekleme, model taraması ve
    GridSearch sonuçlarının özetini üretir. Üretilen ara bilgileri
    ayrıntılı rapora eklemek üzere döndürür.
    """
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
        # Eğitim/ölçekleme ve arama meta bilgileri rapora eklenecek
        training_info = {
            'train_size': int(X_train.shape[0]),
            'test_size': int(X_test.shape[0]),
            'num_features': int(X.shape[1]),
            'num_labels': int(y_multi_label.shape[1]),
            'scaler_means_head': [float(m) for m in (getattr(scaler, 'mean_', [])[:10] if hasattr(scaler, 'mean_') else [])],
            'scaler_scales_head': [float(s) for s in (getattr(scaler, 'scale_', [])[:10] if hasattr(scaler, 'scale_') else [])],
            'grid_search_summaries': {}
        }
        
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
                
                # GridSearch özetini derle (ilk 5 sonuç)
                cv_summary = []
                try:
                    cv_results = grid_search.cv_results_
                    means = cv_results.get('mean_test_score', [])
                    params_list = cv_results.get('params', [])
                    # En iyi 5 konfigürasyonu sırala
                    top_idx = np.argsort(means)[::-1][:5]
                    for idx in top_idx:
                        cv_summary.append({
                            'mean_test_score': float(means[idx]),
                            'params': params_list[idx]
                        })
                except Exception:
                    cv_summary = []

                results[name] = {
                    'accuracy': accuracy,
                    'f1_micro': f1_micro,
                    'f1_macro': f1_macro,
                    'hamming_loss': hamming,
                    'jaccard_score': jaccard,
                    'best_params': grid_search.best_params_,
                    'model': best_model_cv,
                    'predictions': y_pred,
                    'cv_top': cv_summary
                }
                # Modelin grid arama özetini ekle
                training_info['grid_search_summaries'][name] = {
                    'best_params': grid_search.best_params_,
                    'cv_top': cv_summary
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
        
        # 1) Mevcut dizine kaydet
        joblib.dump(complete_model, model_save_path)
        print(f"✅ En iyi model kaydedildi: {model_save_path}")

        # 2) Model klasörüne 'model2.pkl' adıyla da kaydet
        try:
            model_dir = os.path.join(os.path.dirname(__file__), "..", "Model")
            model_dir = os.path.normpath(model_dir)
            os.makedirs(model_dir, exist_ok=True)  # Klasör yoksa oluştur
            model2_path = os.path.join(model_dir, "model2.pkl")
            joblib.dump(complete_model, model2_path)
            print(f"✅ En iyi model Model klasörüne de kaydedildi: {model2_path}")
        except Exception as save_err:
            print(f"⚠️ Model klasörüne kaydedilirken hata: {save_err}")
        
        return best_model, scaler, metadata, results, X_test, y_test, training_info
        
    except Exception as e:
        print(f"❌ Model eğitimi hatası: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, None

def prepare_multi_label_data(df):
    """Multi-label veriyi hazırlar

    Veri hazırlama sırasında gerçekleştirilen tüm adımların özetini de
    döndürür; böylece raporda ayrıntılı şekilde sunulabilir.
    """
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

    # Veri hazırlama bilgilerini toplamak için sözlük
    prep_info = {
        'num_rows': int(df.shape[0]),
        'num_cols': int(df.shape[1]),
        'num_features': int(len(feature_columns)),
        'num_labels': int(len(label_columns)),
        'feature_columns_head': feature_columns[:20],
        'label_columns': label_columns,
        'removed_single_class_labels': [],
        'categorical_columns': [],
        'missing_summary': {},
        'infinite_detected': False
    }
    
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
        prep_info['removed_single_class_labels'] = single_class_labels
        
        print(f"✅ Geçerli ürün sayısı: {len(crop_names)}")
    else:
        print("✅ Tüm ürünler çok sınıflı")
    
    # Kategorik sütunları sayısal değerlere dönüştür
    categorical_columns = X.select_dtypes(include=['object']).columns
    if len(categorical_columns) > 0:
        print(f"🔄 Kategorik sütunlar işleniyor: {list(categorical_columns)}")
        prep_info['categorical_columns'] = [str(c) for c in list(categorical_columns)]
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
        # Eksik değer özetini (ilk 20 sütun için) kaydet
        prep_info['missing_summary'] = {
            str(col): int(missing_values[col]) for col in missing_values[missing_values > 0].sort_values(ascending=False).head(20).index
        }
        X = X.fillna(X.mean())
    else:
        print("✅ Eksik değer yok")
    
    # Sonsuz değerleri kontrol et
    inf_values = np.isinf(X.select_dtypes(include=[np.number])).sum()
    if inf_values.sum() > 0:
        print("⚠️ Sonsuz değerler bulundu, NaN ile değiştiriliyor...")
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.mean())
        prep_info['infinite_detected'] = True
    
    return X, y_multi_label, crop_names, prep_info

def generate_multi_label_report(results, crop_names, X_test, y_test, prep_info, training_info, metadata):
    """Multi-label analiz raporu oluşturur

    Rapor; veri önişleme adımlarını, eğitim/validasyon ayrıntılarını,
    GridSearch özetlerini, model karşılaştırmasını ve ürün bazlı
    metrikleri ayrıntılı şekilde içerir.
    """
    print("\n📝 Multi-label raporu oluşturuluyor...")
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("BINARY RELEVANCE MULTI-LABEL CLASSIFICATION RAPORU")
    report_lines.append("=" * 80)
    report_lines.append(f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Toplam Ürün Sayısı: {len(crop_names)}")
    report_lines.append("")

    # Veri Hazırlama Özeti
    report_lines.append("VERİ HAZIRLAMA ÖZETİ")
    report_lines.append("-" * 40)
    report_lines.append(f"Satır Sayısı: {prep_info.get('num_rows', 0)}")
    report_lines.append(f"Sütun Sayısı: {prep_info.get('num_cols', 0)}")
    report_lines.append(f"Özellik Sütunu Sayısı: {prep_info.get('num_features', 0)}")
    report_lines.append(f"Label Sütunu Sayısı: {prep_info.get('num_labels', 0)}")
    if prep_info.get('feature_columns_head'):
        report_lines.append("Özellik Sütunları (ilk 20):")
        for c in prep_info['feature_columns_head']:
            report_lines.append(f"  - {c}")
    if prep_info.get('categorical_columns'):
        report_lines.append("Kategorik Sütunlar:")
        for c in prep_info['categorical_columns']:
            report_lines.append(f"  - {c}")
    if prep_info.get('removed_single_class_labels'):
        report_lines.append("Analizden Çıkarılan Tek Sınıflı Ürünler:")
        for c in prep_info['removed_single_class_labels']:
            report_lines.append(f"  - {c}")
    if prep_info.get('missing_summary'):
        report_lines.append("Eksik Değer Özeti (ilk 20 sütun):")
        for col, cnt in prep_info['missing_summary'].items():
            report_lines.append(f"  - {col}: {cnt}")
    report_lines.append(f"Sonsuz Değer Tespit Edildi mi?: {'Evet' if prep_info.get('infinite_detected') else 'Hayır'}")
    report_lines.append("")

    # Eğitim/Doğrulama Özeti
    report_lines.append("EĞİTİM/DOĞRULAMA ÖZETİ")
    report_lines.append("-" * 40)
    report_lines.append(f"Eğitim Örnek Sayısı: {training_info.get('train_size')}")
    report_lines.append(f"Test Örnek Sayısı: {training_info.get('test_size')}")
    report_lines.append(f"Özellik Sayısı: {training_info.get('num_features')}")
    report_lines.append(f"Label Sayısı: {training_info.get('num_labels')}")
    means_head = training_info.get('scaler_means_head') or []
    scales_head = training_info.get('scaler_scales_head') or []
    if means_head and scales_head:
        report_lines.append("StandardScaler İstatistikleri (ilk 10 özellik):")
        for i, (m, s) in enumerate(zip(means_head, scales_head), 1):
            report_lines.append(f"  {i:02d}. mean={m:.6f}, scale={s:.6f}")
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
        if 'best_params' in result and isinstance(result['best_params'], dict):
            report_lines.append(f"   En İyi Parametreler: {result['best_params']}")
        if 'cv_top' in result and result['cv_top']:
            report_lines.append("   GridSearch En İyi 5 Konfigürasyon:")
            for j, row in enumerate(result['cv_top'], 1):
                report_lines.append(f"     {j}. mean_test_score={row['mean_test_score']:.6f}, params={row['params']}")
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
            report_lines.append(f"   False Positives: {false_positives}")
            report_lines.append(f"   False Negatives: {false_negatives}")
            report_lines.append(f"   True Negatives: {true_negatives}")
            report_lines.append("")

    # Genel özet ve meta bilgiler
    report_lines.append("GENEL ÖZET VE META BİLGİLER")
    report_lines.append("-" * 40)
    report_lines.append(f"En İyi Model: {metadata.get('best_model', 'N/A')}")
    report_lines.append(f"En İyi F1-Macro: {metadata.get('best_f1_macro', 0):.4f}")
    report_lines.append(f"Eğitim Tarihi: {metadata.get('training_date', 'N/A')}")
    report_lines.append(f"Ürünler: {', '.join(metadata.get('crop_names', []))}")
    
    report_lines.append("=" * 80)
    report_lines.append("RAPOR SONU")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def generate_visualizations(results, crop_names, y_test, output_dir, best_result):
    """Model ve etiket bazlı performans görsellerini üretir ve kaydeder.

    - Model karşılaştırma grafikleri (F1-Macro, Accuracy)
    - En iyi model için etiket bazlı Precision/Recall/F1 bar grafiği
    Grafikler belirtilen klasöre kaydedilir.
    """
    if not HAS_PLOTTING:
        print("⚠️ matplotlib/seaborn bulunamadı; görseller üretilmedi")
        return

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Grafik klasörü oluşturulamadı: {e}")
        return

    try:
        # 1) Model karşılaştırma (F1-Macro)
        successful = {k: v for k, v in results.items() if 'error' not in v}
        if successful:
            names = list(successful.keys())
            f1_macros = [successful[n]['f1_macro'] for n in names]
            accuracies = [successful[n]['accuracy'] for n in names]

            plt.figure(figsize=(10, 5))
            sns.barplot(x=names, y=f1_macros, palette='viridis')
            plt.xticks(rotation=30, ha='right')
            plt.ylabel('F1-Macro')
            plt.title('Model Karşılaştırması - F1-Macro')
            plt.tight_layout()
            out_path = os.path.join(output_dir, 'model_comparison_f1_macro.png')
            plt.savefig(out_path, dpi=150)
            plt.close()
            print(f"🖼️ Kaydedildi: {out_path}")

            # 2) Model karşılaştırma (Accuracy)
            plt.figure(figsize=(10, 5))
            sns.barplot(x=names, y=accuracies, palette='magma')
            plt.xticks(rotation=30, ha='right')
            plt.ylabel('Accuracy')
            plt.title('Model Karşılaştırması - Accuracy')
            plt.tight_layout()
            out_path = os.path.join(output_dir, 'model_comparison_accuracy.png')
            plt.savefig(out_path, dpi=150)
            plt.close()
            print(f"🖼️ Kaydedildi: {out_path}")

        # 3) En iyi model için etiket bazlı metrikler
        if best_result is not None and 'predictions' in best_result:
            y_pred = best_result['predictions']
            y_true = np.array(y_test)
            per_label_f1 = []
            per_label_prec = []
            per_label_rec = []

            for i in range(min(len(crop_names), y_true.shape[1])):
                tp = np.sum((y_true[:, i] == 1) & (y_pred[:, i] == 1))
                fp = np.sum((y_true[:, i] == 0) & (y_pred[:, i] == 1))
                fn = np.sum((y_true[:, i] == 1) & (y_pred[:, i] == 0))
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                per_label_prec.append(precision)
                per_label_rec.append(recall)
                per_label_f1.append(f1)

            # Çok kalabalık olmaması için ilk 20 etiketi çizelim
            top_k = min(20, len(crop_names))
            labels_plot = crop_names[:top_k]
            f1_plot = per_label_f1[:top_k]
            prec_plot = per_label_prec[:top_k]
            rec_plot = per_label_rec[:top_k]

            # F1 bar
            plt.figure(figsize=(12, 6))
            sns.barplot(x=labels_plot, y=f1_plot, palette='crest')
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('F1-Score')
            plt.title('Etiket Bazlı F1-Score (En İyi Model)')
            plt.tight_layout()
            out_path = os.path.join(output_dir, 'per_label_f1_top20.png')
            plt.savefig(out_path, dpi=150)
            plt.close()
            print(f"🖼️ Kaydedildi: {out_path}")

            # Precision/Recall yan yana
            plt.figure(figsize=(12, 6))
            x = np.arange(len(labels_plot))
            width = 0.4
            plt.bar(x - width/2, prec_plot, width=width, label='Precision')
            plt.bar(x + width/2, rec_plot, width=width, label='Recall')
            plt.xticks(x, labels_plot, rotation=45, ha='right')
            plt.ylim(0, 1.0)
            plt.ylabel('Skor')
            plt.title('Etiket Bazlı Precision/Recall (En İyi Model)')
            plt.legend()
            plt.tight_layout()
            out_path = os.path.join(output_dir, 'per_label_precision_recall_top20.png')
            plt.savefig(out_path, dpi=150)
            plt.close()
            print(f"🖼️ Kaydedildi: {out_path}")
    except Exception as e:
        print(f"⚠️ Görsel üretimi sırasında hata: {e}")


def main():
    """Ana fonksiyon"""
    print("🚀 Multi-Label Makine Öğrenmesi Analizi Başlıyor...")
    print("=" * 60)
    
    try:
        # CSV dosyasını Data klasöründen yükle
        csv_path = os.path.join(os.path.dirname(__file__), "..", "Data", "final5.csv")
        csv_path = os.path.normpath(csv_path)  # Windows path'leri için normalize et
        print(f"📁 CSV dosyası yükleniyor: {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"✅ CSV yüklendi: {df.shape[0]} satır, {df.shape[1]} sütun")
        
        # Multi-label veriyi hazırla
        X, y_multi_label, crop_names, prep_info = prepare_multi_label_data(df)
        
        # Multi-label modelleri eğit
        best_model, scaler, metadata, results, X_test, y_test, training_info = train_multi_label_models(
            X, y_multi_label, crop_names
        )
        
        if best_model is None:
            print("❌ Model eğitilemedi, işlem durduruluyor")
            return
        
        # Rapor oluştur
        report_content = generate_multi_label_report(
            results,
            crop_names,
            X_test,
            y_test,
            prep_info,
            training_info,
            metadata
        )
        
        # Raporu Data klasörüne final_report.txt olarak kaydet
        report_path = os.path.join(os.path.dirname(__file__), "..", "Data", "final_report.txt")
        report_path = os.path.normpath(report_path)  # Windows path'leri için normalize et
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
        
        # Görseller: 'Grafikler' klasörüne yaz
        try:
            best_model_name = metadata.get('best_model')
            best_result = None
            if best_model_name and best_model_name in results:
                best_result = results[best_model_name]
            graphs_dir = os.path.join(os.path.dirname(__file__), "..", "Grafikler")
            graphs_dir = os.path.normpath(graphs_dir)
            generate_visualizations(results, crop_names, y_test, graphs_dir, best_result)
        except Exception as viz_err:
            print(f"⚠️ Görseller üretilirken hata: {viz_err}")

        print("\n🎉 Multi-label analiz tamamlandı!")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
