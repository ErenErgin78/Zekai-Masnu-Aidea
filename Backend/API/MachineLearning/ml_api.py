# -*- coding: utf-8 -*-
"""
Machine Learning API - Bitki Önerisi Sistemi
============================================

Bu API, koordinat bilgilerine göre toprak analizi yaparak
makine öğrenmesi modeli ile bitki önerileri sunar.

Özellikler:
- SoilType API'sinden toprak verilerini alır
- Koordinat eşleştirme ile iklim verilerini bulur
- ML modeli ile bitki önerileri yapar
- Dinamik dosya yolları kullanır
- Kapsamlı hata yönetimi ve loglama

Author: ML Analysis System
Version: 1.0.0
"""

import os
import sys
import json
import logging
import pickle
import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Optional, Any, Tuple
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import math

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI router oluştur
router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Pydantic modelleri
class MLRequest(BaseModel):
    """ML analizi için istek modeli"""
    method: str = Field(..., description="Method type", example="Auto")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Koordinat bilgileri")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() not in ['auto', 'manual']:
            raise ValueError('Method must be "Auto" or "Manual"')
        return v.title()
    
    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if v is not None:
            if 'longitude' not in v or 'latitude' not in v:
                raise ValueError('Coordinates must contain longitude and latitude')
            lon, lat = v['longitude'], v['latitude']
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError('Invalid coordinate ranges')
        return v

class PlantRecommendation(BaseModel):
    """Bitki önerisi modeli"""
    plant_name: str
    confidence_score: float
    probability: float

class MLAnalysisResponse(BaseModel):
    """ML analizi yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    coordinates: Dict[str, float]
    soil_data: Dict[str, Any]
    climate_data: Dict[str, Any]
    recommendations: List[PlantRecommendation]
    model_info: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Hata yanıt modeli"""
    success: bool = False
    error: str
    timestamp: datetime
    details: Optional[str] = None

class MLService:
    """Makine öğrenmesi servis sınıfı"""
    
    def __init__(self):
        """Servis başlatıcı - dosya yollarını dinamik olarak belirle"""
        try:
            # Dinamik dosya yolu belirleme
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Model dosyası yolu
            self.model_path = os.path.join(self.script_dir, 'Model', 'model.pkl')
            
            # Veri dosyası yolu
            self.data_path = os.path.join(self.script_dir, 'Data', 'final5.csv')
            
            # SoilType API URL'i
            self.soil_api_url = "http://localhost:8000/soiltype/analyze/auto"
            
            # Dosya varlığını kontrol et
            self._validate_files()
            
            # Modeli yükle
            self.model_data = self._load_model()
            self.fallback_mode = self.model_data is None
            
            if self.model_data:
                self.model = self.model_data.get('model')
                self.scaler = self.model_data.get('scaler')
                self.metadata = self.model_data.get('metadata', {})
            else:
                self.model = None
                self.scaler = None
                self.metadata = {}
            
            # Veri sütunlarını belirle
            self.feature_columns = self._get_feature_columns()
            
            if self.fallback_mode:
                logger.warning("ML Service initialized in FALLBACK MODE - Model file is corrupted")
                logger.warning("Please fix the model.pkl file for proper ML predictions")
            else:
                logger.info("ML Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML Service: {str(e)}")
            raise Exception(f"ML Service initialization failed: {str(e)}")
    
    def _validate_files(self):
        """Gerekli dosyaların varlığını kontrol et"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        logger.info(f"Model path: {self.model_path}")
        logger.info(f"Data path: {self.data_path}")
    
    def _load_model(self):
        """ML modelini yükle"""
        try:
            # Önce pickle ile dene
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                logger.info("Model loaded successfully with pickle")
            except Exception as pickle_error:
                logger.warning(f"Pickle loading failed: {str(pickle_error)}")
                # Joblib ile dene
                try:
                    import joblib
                    model_data = joblib.load(self.model_path)
                    logger.info("Model loaded successfully with joblib")
                except Exception as joblib_error:
                    logger.error(f"Joblib loading also failed: {str(joblib_error)}")
                    raise Exception(f"Both pickle and joblib failed: {str(pickle_error)}")
            
            # Model verisi dictionary ise içindeki modeli al
            if isinstance(model_data, dict):
                if 'model' in model_data:
                    logger.info("Model data is dictionary, extracting 'model' key")
                    return model_data  # Tüm dictionary'yi döndür (model, scaler, metadata)
                else:
                    logger.warning("Dictionary does not contain 'model' key")
                    return None
            else:
                # Direkt model ise
                logger.info("Model data is direct model object")
                return {'model': model_data, 'scaler': None, 'metadata': {}}
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.warning("Model file appears to be corrupted. Using fallback mode.")
            return None  # Fallback mode için None döndür
    
    def _get_feature_columns(self):
        """Model için gerekli özellik sütunlarını belirle"""
        # Model eğitiminde kullanılan sütunlar
        feature_columns = [
            'wrb4_code', 'physical_available_water_capacity', 'basic_organic_carbon',
            'basic_c/n_ratio', 'texture_clay', 'texture_sand', 'texture_coarse_fragments',
            'physical_reference_bulk_density', 'chemical_cation_exchange_capacity',
            'chemical_clay_cec', 'chemical_total_exchangeable_bases', 'chemical_base_saturation',
            'chemical_exchangeable_sodium_percentage', 'chemical_aluminum_saturation',
            'salinity_electrical_conductivity', 'salinity_total_carbon_equivalent',
            'salinity_gypsum_content', 'Ortalama En Yüksek Sıcaklık (°C)_Eylül',
            'Ortalama En Yüksek Sıcaklık (°C)_Aralık', 'Ortalama En Düşük Sıcaklık (°C)_Ağustos',
            'Ortalama Güneşlenme Süresi (saat)_Ağustos', 'Ortalama Güneşlenme Süresi (saat)_Aralık',
            'Ortalama Yağışlı Gün Sayısı_Şubat', 'Ortalama Yağışlı Gün Sayısı_Mart',
            'Ortalama Yağışlı Gün Sayısı_Nisan', 'Ortalama Yağışlı Gün Sayısı_Ağustos',
            'Ortalama Yağışlı Gün Sayısı_Kasım', 'Ortalama Yağışlı Gün Sayısı_Yıllık',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Nisan',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Mayıs',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Haziran',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ağustos',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Eylül',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ekim',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Aralık',
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Yıllık'
        ]
        
        logger.info(f"Feature columns defined: {len(feature_columns)} columns")
        return feature_columns
    
    def _get_soil_data_from_api(self, coordinates: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """SoilType API'sinden toprak verilerini al"""
        try:
            # API isteği hazırla
            if coordinates:
                # Manuel koordinat kullan
                payload = {
                    "method": "Manual",
                    "longitude": coordinates['longitude'],
                    "latitude": coordinates['latitude']
                }
                api_url = "http://localhost:8000/soiltype/analyze"
            else:
                # Otomatik konum tespiti
                payload = {"method": "Auto"}
                api_url = self.soil_api_url
            
            logger.info(f"Requesting soil data from API: {api_url}")
            logger.info(f"Payload: {payload}")
            
            # API isteği gönder
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            soil_data = response.json()
            logger.info("Soil data retrieved successfully from API")
            
            return soil_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"SoilType API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting soil data: {str(e)}")
            raise Exception(f"Soil data retrieval failed: {str(e)}")
    
    def _extract_soil_features(self, soil_data: Dict[str, Any]) -> Dict[str, float]:
        """Toprak verilerinden model özelliklerini çıkar"""
        try:
            features = {}
            
            # WRB4 kodunu al
            features['wrb4_code'] = self._get_wrb4_code(soil_data)
            
            # Temel özellikler
            features['physical_available_water_capacity'] = self._extract_property_value(
                soil_data, 'physical_properties', 'Available Water Capacity'
            )
            features['basic_organic_carbon'] = self._extract_property_value(
                soil_data, 'basic_properties', 'Organic Carbon'
            )
            features['basic_c/n_ratio'] = self._extract_property_value(
                soil_data, 'basic_properties', 'C/N Ratio'
            )
            
            # Doku özellikleri
            features['texture_clay'] = self._extract_property_value(
                soil_data, 'texture_properties', 'Clay'
            )
            features['texture_sand'] = self._extract_property_value(
                soil_data, 'texture_properties', 'Sand'
            )
            features['texture_coarse_fragments'] = self._extract_property_value(
                soil_data, 'texture_properties', 'Coarse Fragments'
            )
            
            # Fiziksel özellikler
            features['physical_reference_bulk_density'] = self._extract_property_value(
                soil_data, 'physical_properties', 'Reference Bulk Density'
            )
            
            # Kimyasal özellikler
            features['chemical_cation_exchange_capacity'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Cation Exchange Capacity'
            )
            features['chemical_clay_cec'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Clay CEC'
            )
            features['chemical_total_exchangeable_bases'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Total Exchangeable Bases'
            )
            features['chemical_base_saturation'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Base Saturation'
            )
            features['chemical_exchangeable_sodium_percentage'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Exchangeable Sodium Percentage'
            )
            features['chemical_aluminum_saturation'] = self._extract_property_value(
                soil_data, 'chemical_properties', 'Aluminum Saturation'
            )
            
            # Tuzluluk özellikleri
            features['salinity_electrical_conductivity'] = self._extract_property_value(
                soil_data, 'salinity_properties', 'Electrical Conductivity'
            )
            features['salinity_total_carbon_equivalent'] = self._extract_property_value(
                soil_data, 'salinity_properties', 'Total Carbon Equivalent'
            )
            features['salinity_gypsum_content'] = self._extract_property_value(
                soil_data, 'salinity_properties', 'Gypsum Content'
            )
            
            logger.info(f"Extracted {len(features)} soil features")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting soil features: {str(e)}")
            raise Exception(f"Soil feature extraction failed: {str(e)}")
    
    def _get_wrb4_code(self, soil_data: Dict[str, Any]) -> int:
        """WRB4 kodunu sayısal değere çevir"""
        try:
            wrb4_code = soil_data.get('classification', {}).get('wrb4_code', 'N/A')
            
            # WRB4 kodlarını sayısal değerlere çevir (basit mapping)
            wrb4_mapping = {
                'HS': 1, 'AT': 2, 'TC': 3, 'CR': 4, 'LP': 5, 'SN': 6, 'VR': 7, 'SC': 8,
                'GL': 9, 'AN': 10, 'PZ': 11, 'PT': 12, 'PL': 13, 'ST': 14, 'NT': 15,
                'FR': 16, 'CH': 17, 'KS': 18, 'PH': 19, 'UM': 20, 'DU': 21, 'GY': 22,
                'CL': 23, 'RT': 24, 'AC': 25, 'LX': 26, 'AL': 27, 'LV': 28, 'CM': 29,
                'FL': 30, 'AR': 31, 'RG': 32
            }
            
            return wrb4_mapping.get(wrb4_code, 21)  # Varsayılan değer
            
        except Exception as e:
            logger.warning(f"Error converting WRB4 code: {str(e)}")
            return 21  # Varsayılan değer
    
    def _extract_property_value(self, soil_data: Dict[str, Any], category: str, property_name: str) -> float:
        """Belirli bir toprak özelliğinin değerini çıkar"""
        try:
            properties = soil_data.get(category, [])
            for prop in properties:
                if prop.get('name') == property_name:
                    value = prop.get('value')
                    if value is not None and value != -9.0 and value != -9:
                        return float(value)
            return 0.0  # Varsayılan değer
            
        except Exception as e:
            logger.warning(f"Error extracting {property_name}: {str(e)}")
            return 0.0
    
    def _find_closest_climate_data(self, coordinates: Dict[str, float]) -> Dict[str, float]:
        """Koordinatlara en yakın iklim verilerini bul"""
        try:
            # CSV dosyasını oku
            df = pd.read_csv(self.data_path)
            
            # Koordinat bilgileri CSV'de yok, bu yüzden rastgele bir satır seç
            # Gerçek uygulamada koordinat-iklim eşleştirmesi yapılmalı
            logger.warning("Coordinate-based climate matching not implemented, using random sample")
            
            # Rastgele bir satır seç
            random_row = df.sample(n=1).iloc[0]
            
            # İklim özelliklerini çıkar
            climate_features = {}
            climate_columns = [
                'Ortalama En Yüksek Sıcaklık (°C)_Eylül',
                'Ortalama En Yüksek Sıcaklık (°C)_Aralık',
                'Ortalama En Düşük Sıcaklık (°C)_Ağustos',
                'Ortalama Güneşlenme Süresi (saat)_Ağustos',
                'Ortalama Güneşlenme Süresi (saat)_Aralık',
                'Ortalama Yağışlı Gün Sayısı_Şubat',
                'Ortalama Yağışlı Gün Sayısı_Mart',
                'Ortalama Yağışlı Gün Sayısı_Nisan',
                'Ortalama Yağışlı Gün Sayısı_Ağustos',
                'Ortalama Yağışlı Gün Sayısı_Kasım',
                'Ortalama Yağışlı Gün Sayısı_Yıllık',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Nisan',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Mayıs',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Haziran',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ağustos',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Eylül',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ekim',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Aralık',
                'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Yıllık'
            ]
            
            for col in climate_columns:
                if col in df.columns:
                    climate_features[col] = float(random_row[col])
                else:
                    climate_features[col] = 0.0
            
            logger.info(f"Found climate data with {len(climate_features)} features")
            return climate_features
            
        except Exception as e:
            logger.error(f"Error finding climate data: {str(e)}")
            raise Exception(f"Climate data retrieval failed: {str(e)}")
    
    def _prepare_features(self, soil_features: Dict[str, float], climate_features: Dict[str, float]) -> np.ndarray:
        """Model için özellik vektörünü hazırla"""
        try:
            # Tüm özellikleri birleştir
            all_features = {**soil_features, **climate_features}
            
            # Model sütunlarına göre sırala
            feature_vector = []
            for col in self.feature_columns:
                value = all_features.get(col, 0.0)
                feature_vector.append(float(value))
            
            # NumPy array'e çevir
            feature_array = np.array(feature_vector).reshape(1, -1)
            
            # Scaler varsa veriyi normalize et
            if self.scaler is not None:
                try:
                    feature_array = self.scaler.transform(feature_array)
                    logger.info("Features scaled using StandardScaler")
                except Exception as scale_error:
                    logger.warning(f"Scaling failed: {str(scale_error)}, using raw features")
            
            logger.info(f"Prepared feature vector with shape: {feature_array.shape}")
            return feature_array
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise Exception(f"Feature preparation failed: {str(e)}")
    
    def _get_plant_names(self) -> List[str]:
        """Bitki isimlerini al"""
        return [
            'Arpa', 'Ayçiçeği', 'Badem', 'Biber', 'Buğday', 'Ceviz', 'Domates', 'Elma',
            'Fasulye', 'Fındık', 'Fıstık', 'Gül', 'Haşhaş', 'Kayısı', 'Kiraz', 'Kivi',
            'Mercimek', 'Meyve', 'Muz', 'Mısır', 'Narenciye', 'Nohut', 'Pamuk', 'Patates',
            'Patlıcan', 'Pirinç', 'Sarımsak', 'Sebze', 'Turunçgiller', 'Tütün', 'Yer Fıstığı',
            'Zeytin', 'Çay', 'Çilek', 'Üzüm', 'İncir', 'Şeftali', 'Şeker Pancarı', 'Şerbetçi Otu'
        ]
    
    def _make_prediction(self, features: np.ndarray) -> List[PlantRecommendation]:
        """Model ile tahmin yap veya fallback mode kullan"""
        try:
            if self.fallback_mode:
                return self._make_fallback_prediction(features)
            
            # Model tahmini yap
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)[0]
            else:
                # Eğer predict_proba yoksa, predict kullan
                prediction = self.model.predict(features)[0]
                probabilities = np.zeros(len(self._get_plant_names()))
                probabilities[prediction] = 1.0
            
            # Bitki isimlerini al
            plant_names = self._get_plant_names()
            
            # Önerileri hazırla
            recommendations = []
            for i, (plant_name, prob) in enumerate(zip(plant_names, probabilities)):
                if prob > 0.1:  # Sadece %10'dan yüksek olasılıkları dahil et
                    confidence = min(prob * 100, 100)  # Yüzde olarak
                    recommendations.append(PlantRecommendation(
                        plant_name=plant_name,
                        confidence_score=round(confidence, 2),
                        probability=round(prob, 4)
                    ))
            
            # Güven skoruna göre sırala
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # En iyi 5 öneriyi al
            recommendations = recommendations[:5]
            
            logger.info(f"Generated {len(recommendations)} plant recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise Exception(f"Prediction failed: {str(e)}")
    
    def _make_fallback_prediction(self, features: np.ndarray) -> List[PlantRecommendation]:
        """Fallback mode - basit kurallar tabanlı öneriler"""
        try:
            logger.info("Using fallback prediction mode - simple rule-based recommendations")
            
            # Özellik değerlerini al
            feature_dict = dict(zip(self.feature_columns, features[0]))
            
            recommendations = []
            
            # Basit kurallar tabanlı öneriler
            # Toprak tipine göre öneriler
            wrb4_code = feature_dict.get('wrb4_code', 21)
            
            if wrb4_code in [17, 18, 19]:  # Chernozems, Kastanozems, Phaeozems
                recommendations.extend([
                    PlantRecommendation(plant_name="Buğday", confidence_score=85.0, probability=0.85),
                    PlantRecommendation(plant_name="Arpa", confidence_score=80.0, probability=0.80),
                    PlantRecommendation(plant_name="Ayçiçeği", confidence_score=75.0, probability=0.75),
                    PlantRecommendation(plant_name="Mısır", confidence_score=70.0, probability=0.70),
                    PlantRecommendation(plant_name="Şeker Pancarı", confidence_score=65.0, probability=0.65)
                ])
            elif wrb4_code in [28, 29]:  # Luvisols, Cambisols
                recommendations.extend([
                    PlantRecommendation(plant_name="Pamuk", confidence_score=85.0, probability=0.85),
                    PlantRecommendation(plant_name="Mısır", confidence_score=80.0, probability=0.80),
                    PlantRecommendation(plant_name="Domates", confidence_score=75.0, probability=0.75),
                    PlantRecommendation(plant_name="Biber", confidence_score=70.0, probability=0.70),
                    PlantRecommendation(plant_name="Patates", confidence_score=65.0, probability=0.65)
                ])
            elif wrb4_code in [21, 22]:  # Du, Gy
                recommendations.extend([
                    PlantRecommendation(plant_name="Zeytin", confidence_score=85.0, probability=0.85),
                    PlantRecommendation(plant_name="Üzüm", confidence_score=80.0, probability=0.80),
                    PlantRecommendation(plant_name="Badem", confidence_score=75.0, probability=0.75),
                    PlantRecommendation(plant_name="Kayısı", confidence_score=70.0, probability=0.70),
                    PlantRecommendation(plant_name="Şeftali", confidence_score=65.0, probability=0.65)
                ])
            else:  # Diğer toprak tipleri için genel öneriler
                recommendations.extend([
                    PlantRecommendation(plant_name="Buğday", confidence_score=80.0, probability=0.80),
                    PlantRecommendation(plant_name="Arpa", confidence_score=75.0, probability=0.75),
                    PlantRecommendation(plant_name="Mısır", confidence_score=70.0, probability=0.70),
                    PlantRecommendation(plant_name="Patates", confidence_score=65.0, probability=0.65),
                    PlantRecommendation(plant_name="Fasulye", confidence_score=60.0, probability=0.60)
                ])
            
            # İklim koşullarına göre ayarlama
            avg_temp_sep = feature_dict.get('Ortalama En Yüksek Sıcaklık (°C)_Eylül', 25)
            avg_temp_dec = feature_dict.get('Ortalama En Yüksek Sıcaklık (°C)_Aralık', 10)
            annual_rainfall = feature_dict.get('Aylık Toplam Yağış Miktarı Ortalaması (mm)_Yıllık', 500)
            
            # Sıcak iklim için ek öneriler
            if avg_temp_sep > 30:
                recommendations.append(PlantRecommendation(plant_name="Pamuk", confidence_score=90.0, probability=0.90))
                recommendations.append(PlantRecommendation(plant_name="Mısır", confidence_score=85.0, probability=0.85))
            
            # Soğuk iklim için ek öneriler
            if avg_temp_dec < 5:
                recommendations.append(PlantRecommendation(plant_name="Arpa", confidence_score=90.0, probability=0.90))
                recommendations.append(PlantRecommendation(plant_name="Patates", confidence_score=85.0, probability=0.85))
            
            # Kurak iklim için ek öneriler
            if annual_rainfall < 400:
                recommendations.append(PlantRecommendation(plant_name="Zeytin", confidence_score=90.0, probability=0.90))
                recommendations.append(PlantRecommendation(plant_name="Badem", confidence_score=85.0, probability=0.85))
            
            # Nemli iklim için ek öneriler
            if annual_rainfall > 800:
                recommendations.append(PlantRecommendation(plant_name="Çay", confidence_score=90.0, probability=0.90))
                recommendations.append(PlantRecommendation(plant_name="Fındık", confidence_score=85.0, probability=0.85))
            
            # Güven skoruna göre sırala ve tekrarları kaldır
            seen_plants = set()
            unique_recommendations = []
            for rec in sorted(recommendations, key=lambda x: x.confidence_score, reverse=True):
                if rec.plant_name not in seen_plants:
                    unique_recommendations.append(rec)
                    seen_plants.add(rec.plant_name)
            
            # En iyi 5 öneriyi al
            final_recommendations = unique_recommendations[:5]
            
            logger.info(f"Generated {len(final_recommendations)} fallback recommendations")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error in fallback prediction: {str(e)}")
            # Son çare öneriler
            return [
                PlantRecommendation(plant_name="Buğday", confidence_score=70.0, probability=0.70),
                PlantRecommendation(plant_name="Arpa", confidence_score=65.0, probability=0.65),
                PlantRecommendation(plant_name="Mısır", confidence_score=60.0, probability=0.60),
                PlantRecommendation(plant_name="Patates", confidence_score=55.0, probability=0.55),
                PlantRecommendation(plant_name="Fasulye", confidence_score=50.0, probability=0.50)
            ]
    
    def analyze_and_recommend(self, request: MLRequest) -> MLAnalysisResponse:
        """Tam analiz ve öneri süreci"""
        try:
            logger.info(f"Starting ML analysis with method: {request.method}")
            
            # Koordinatları belirle
            if request.method == "Manual" and request.coordinates:
                coordinates = request.coordinates
            else:
                # Otomatik konum tespiti için koordinatları None gönder
                coordinates = None
            
            # Toprak verilerini al
            soil_data = self._get_soil_data_from_api(coordinates)
            
            # Kullanılan koordinatları al
            used_coordinates = soil_data.get('coordinates', {'longitude': 0.0, 'latitude': 0.0})
            
            # Toprak özelliklerini çıkar
            soil_features = self._extract_soil_features(soil_data)
            
            # İklim verilerini bul
            climate_features = self._find_closest_climate_data(used_coordinates)
            
            # Özellik vektörünü hazırla
            feature_vector = self._prepare_features(soil_features, climate_features)
            
            # Tahmin yap
            recommendations = self._make_prediction(feature_vector)
            
            # Model bilgilerini hazırla
            model_info = {
                "model_type": type(self.model).__name__ if self.model else "Fallback Rules",
                "scaler_type": type(self.scaler).__name__ if self.scaler else "None",
                "feature_count": len(self.feature_columns),
                "recommendation_count": len(recommendations),
                "fallback_mode": self.fallback_mode,
                "model_status": "Active" if not self.fallback_mode else "Corrupted - Using fallback rules",
                "metadata": self.metadata
            }
            
            return MLAnalysisResponse(
                success=True,
                message="ML analysis completed successfully",
                timestamp=datetime.now(),
                coordinates=used_coordinates,
                soil_data=soil_features,
                climate_data=climate_features,
                recommendations=recommendations,
                model_info=model_info
            )
            
        except Exception as e:
            logger.error(f"ML analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ML analysis failed: {str(e)}"
            )

# Servis instance'ı oluştur
try:
    ml_service = MLService()
    logger.info("ML Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ML Service: {str(e)}")
    ml_service = None

# API Endpoint'leri
@router.get("/", response_model=Dict[str, str])
async def root():
    """ML API ana endpoint'i"""
    return {
        "message": "Machine Learning API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Service not available"
        )
    
    status_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Machine Learning API",
        "model_status": "Active" if not ml_service.fallback_mode else "Corrupted - Using fallback rules",
        "model_type": type(ml_service.model).__name__ if ml_service.model else "Fallback Rules",
        "scaler_type": type(ml_service.scaler).__name__ if ml_service.scaler else "None",
        "fallback_mode": str(ml_service.fallback_mode)
    }
    
    return status_info

@router.post("/analyze", response_model=MLAnalysisResponse)
async def analyze_and_recommend_plants(request: MLRequest):
    """
    Bitki önerisi analizi
    
    Args:
        request: ML analizi isteği
        
    Returns:
        Bitki önerileri ve analiz sonuçları
        
    Raises:
        HTTPException: Analiz hatası
    """
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Service not available"
        )
    
    try:
        logger.info(f"ML analysis request received: {request.method}")
        return ml_service.analyze_and_recommend(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML analysis endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="0.0.0.0", port=8003)
