# -*- coding: utf-8 -*-
"""
Machine Learning API - FastAPI Implementation
=============================================

Bu API, makine öğrenmesi modeli kullanarak tarım ürünü önerisi yapan bir servistir.
Multi-label classification yaklaşımı ile çoklu ürün tahmini yapar.

Özellikler:
- Manuel veri girişi ile tahmin
- Otomatik konum tespiti + entegre analiz
- Multi-label classification
- Detaylı tahmin sonuçları
- JSON formatında sonuçlar
- Güvenlik korumaları
- Kapsamlı hata yönetimi

Author: Machine Learning System
Version: 1.0.0
"""

import joblib
import numpy as np
import pandas as pd
import os
import re
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import requests
import geocoder

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI uygulaması oluştur
router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Pydantic modelleri
class ManualRequest(BaseModel):
    """Manuel veri girişi için model"""
    method: str = Field(..., description="Method type", example="Manual")
    wrb4_code: str = Field(..., description="Toprak türü kodu", example="TC")
    physical_available_water_capacity: float = Field(..., ge=0, description="Su kapasitesi")
    basic_organic_carbon: float = Field(..., ge=0, description="Organik karbon (%)")
    basic_c_n_ratio: float = Field(..., ge=0, description="C/N oranı")
    texture_clay: float = Field(..., ge=0, le=100, description="Kil oranı (%)")
    texture_sand: float = Field(..., ge=0, le=100, description="Kum oranı (%)")
    texture_coarse_fragments: float = Field(..., ge=0, le=100, description="Kaba parçacık oranı (%)")
    physical_reference_bulk_density: float = Field(..., ge=0, description="Referans hacim yoğunluğu")
    chemical_cation_exchange_capacity: float = Field(..., ge=0, description="Katyon değişim kapasitesi")
    chemical_clay_cec: float = Field(..., ge=0, description="Kil CEC")
    chemical_total_exchangeable_bases: float = Field(..., ge=0, description="Toplam değişebilir bazlar")
    chemical_base_saturation: float = Field(..., ge=0, le=100, description="Baz doygunluğu (%)")
    chemical_exchangeable_sodium_percentage: float = Field(..., ge=0, le=100, description="Değişebilir sodyum yüzdesi (%)")
    chemical_aluminum_saturation: float = Field(..., ge=0, le=100, description="Alüminyum doygunluğu (%)")
    salinity_electrical_conductivity: float = Field(..., ge=0, description="Elektriksel iletkenlik")
    salinity_total_carbon_equivalent: float = Field(..., ge=0, description="Toplam karbon eşdeğeri")
    salinity_gypsum_content: float = Field(..., ge=0, description="Jips içeriği")
    ortalama_en_yuksek_sicaklik_eylul: float = Field(..., description="Eylül ortalama en yüksek sıcaklık")
    ortalama_en_yuksek_sicaklik_aralik: float = Field(..., description="Aralık ortalama en yüksek sıcaklık")
    ortalama_en_dusuk_sicaklik_agustos: float = Field(..., description="Ağustos ortalama en düşük sıcaklık")
    ortalama_guneslenme_suresi_agustos: float = Field(..., ge=0, le=24, description="Ağustos güneşlenme süresi")
    ortalama_guneslenme_suresi_aralik: float = Field(..., ge=0, le=24, description="Aralık güneşlenme süresi")
    ortalama_yagisli_gun_sayisi_subat: float = Field(..., ge=0, le=31, description="Şubat yağışlı gün sayısı")
    ortalama_yagisli_gun_sayisi_mart: float = Field(..., ge=0, le=31, description="Mart yağışlı gün sayısı")
    ortalama_yagisli_gun_sayisi_nisan: float = Field(..., ge=0, le=31, description="Nisan yağışlı gün sayısı")
    ortalama_yagisli_gun_sayisi_agustos: float = Field(..., ge=0, le=31, description="Ağustos yağışlı gün sayısı")
    ortalama_yagisli_gun_sayisi_kasim: float = Field(..., ge=0, le=31, description="Kasım yağışlı gün sayısı")
    ortalama_yagisli_gun_sayisi_yillik: float = Field(..., ge=0, le=365, description="Yıllık yağışlı gün sayısı")
    aylik_toplam_yagis_miktari_nisan: float = Field(..., ge=0, description="Nisan aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_mayis: float = Field(..., ge=0, description="Mayıs aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_haziran: float = Field(..., ge=0, description="Haziran aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_agustos: float = Field(..., ge=0, description="Ağustos aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_eylul: float = Field(..., ge=0, description="Eylül aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_ekim: float = Field(..., ge=0, description="Ekim aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_aralik: float = Field(..., ge=0, description="Aralık aylık toplam yağış miktarı")
    aylik_toplam_yagis_miktari_yillik: float = Field(..., ge=0, description="Yıllık toplam yağış miktarı")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'manual':
            raise ValueError('Method must be "Manual" for manual data input')
        return v.title()
    
    @field_validator('wrb4_code')
    @classmethod
    def validate_wrb4_code(cls, v):
        """WRB4 kodunu doğrula"""
        if not isinstance(v, str):
            raise ValueError('WRB4 code must be a string')
        
        # SQL injection koruması - sadece harf ve sayılara izin ver
        if re.search(r'[^a-zA-Z0-9]', str(v)):
            raise ValueError('Invalid WRB4 code format - only letters and numbers allowed')
        
        return str(v).upper()

class AutoRequest(BaseModel):
    """Otomatik analiz için model"""
    method: str = Field(..., description="Method type", example="Auto")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'auto':
            raise ValueError('Method must be "Auto" for automatic analysis')
        return v.title()

class CropPrediction(BaseModel):
    """Ürün tahmini modeli"""
    crop_name: str
    prediction: bool
    probability: float
    confidence: str

class PredictionStatistics(BaseModel):
    """Tahmin istatistikleri modeli"""
    total_crops_analyzed: int
    recommended_crops: int
    recommendation_rate: float
    average_probability: float
    high_confidence_crops: int

class PredictionResponse(BaseModel):
    """Tahmin yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    statistics: PredictionStatistics
    predictions: List[CropPrediction]

class SimplePredictionResponse(BaseModel):
    """Basit tahmin yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    recommended_crops: List[CropPrediction]

class ModelInfoResponse(BaseModel):
    """Model bilgileri yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    best_model: str
    best_f1_macro: float
    feature_count: int
    crop_count: int
    training_date: str
    crop_names: List[str]

class ErrorResponse(BaseModel):
    """Hata yanıt modeli"""
    success: bool = False
    error: str
    timestamp: datetime
    details: Optional[str] = None

class MLService:
    """Makine öğrenmesi servis sınıfı"""
    
    def __init__(self):
        """Servis başlatıcı - model dosyasını yükle"""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_file = os.path.join(self.script_dir, 'Model', 'model.pkl')
        
        # Model dosyasının varlığını kontrol et
        if not os.path.exists(self.model_file):
            raise FileNotFoundError(f"Model file not found: {self.model_file}")
        
        # Modeli yükle
        try:
            self.complete_model = joblib.load(self.model_file)
            self.model = self.complete_model['model']
            self.scaler = self.complete_model['scaler']
            self.metadata = self.complete_model['metadata']
            
            logger.info("Machine Learning model loaded successfully")
            logger.info(f"Model type: {self.metadata.get('best_model', 'Unknown')}")
            logger.info(f"F1-Macro score: {self.metadata.get('best_f1_macro', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise Exception(f"Model loading error: {str(e)}")
    
    def get_automatic_coordinates(self) -> tuple[Optional[float], Optional[float]]:
        """
        IP adresinden otomatik konum tespiti
        
        Returns:
            (longitude, latitude) tuple veya (None, None)
            
        Raises:
            Exception: Konum tespit hatası
        """
        try:
            logger.info("Attempting automatic location detection...")
            g = geocoder.ip('me')
            
            if g.ok:
                lat, lon = g.latlng
                logger.info(f"Location detected: Lat={lat}, Lon={lon}")
                return lon, lat
            else:
                logger.warning("Automatic location detection failed")
                return None, None
                
        except Exception as e:
            logger.error(f"Error in automatic location detection: {str(e)}")
            raise Exception(f"Location detection error: {str(e)}")
    
    def get_soil_data_from_api(self, longitude: float, latitude: float) -> Optional[Dict[str, Any]]:
        """
        Soil API'den toprak verilerini al
        
        Args:
            longitude: Boylam
            latitude: Enlem
            
        Returns:
            Toprak verileri sözlüğü veya None
        """
        try:
            # Soil API'ye istek gönder
            soil_url = "http://localhost:8000/soiltype/analyze"
            soil_data = {
                "method": "Manual",
                "longitude": longitude,
                "latitude": latitude
            }
            
            response = requests.post(soil_url, json=soil_data, timeout=10)
            
            if response.status_code == 200:
                soil_result = response.json()
                logger.info(f"Soil data retrieved for coordinates ({longitude}, {latitude})")
                return soil_result
            else:
                logger.warning(f"Soil API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting soil data: {str(e)}")
            return None
    
    def get_weather_data_from_api(self, longitude: float, latitude: float) -> Optional[Dict[str, Any]]:
        """
        Weather API'den hava durumu verilerini al
        
        Args:
            longitude: Boylam
            latitude: Enlem
            
        Returns:
            Hava durumu verileri sözlüğü veya None
        """
        try:
            # Weather API'ye istek gönder
            weather_url = "http://localhost:8000/weather/dailyweather/manual"
            weather_data = {
                "method": "Manual",
                "longitude": longitude,
                "latitude": latitude
            }
            
            response = requests.post(weather_url, json=weather_data, timeout=10)
            
            if response.status_code == 200:
                weather_result = response.json()
                logger.info(f"Weather data retrieved for coordinates ({longitude}, {latitude})")
                return weather_result
            else:
                logger.warning(f"Weather API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting weather data: {str(e)}")
            return None
    
    def extract_features_from_apis(self, soil_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        API'lerden gelen verilerden özellikleri çıkar
        
        Args:
            soil_data: Toprak analizi verileri
            weather_data: Hava durumu verileri
            
        Returns:
            Özellik sözlüğü veya None
        """
        try:
            features = {}
            
            # Toprak verilerinden özellikleri çıkar
            if soil_data and soil_data.get('success'):
                classification = soil_data.get('classification', {})
                features['wrb4_code'] = classification.get('wrb4_code', 'UNKNOWN')
                
                # Temel özellikler
                basic_props = soil_data.get('basic_properties', [])
                for prop in basic_props:
                    if prop['name'] == 'Organic Carbon':
                        features['basic_organic_carbon'] = prop['value']
                    elif prop['name'] == 'C/N Ratio':
                        features['basic_c_n_ratio'] = prop['value']
                
                # Doku özellikleri
                texture_props = soil_data.get('texture_properties', [])
                for prop in texture_props:
                    if prop['name'] == 'Clay':
                        features['texture_clay'] = prop['value']
                    elif prop['name'] == 'Sand':
                        features['texture_sand'] = prop['value']
                    elif prop['name'] == 'Coarse Fragments':
                        features['texture_coarse_fragments'] = prop['value']
                
                # Fiziksel özellikler
                physical_props = soil_data.get('physical_properties', [])
                for prop in physical_props:
                    if prop['name'] == 'Available Water Capacity':
                        features['physical_available_water_capacity'] = prop['value']
                    elif prop['name'] == 'Reference Bulk Density':
                        features['physical_reference_bulk_density'] = prop['value']
                
                # Kimyasal özellikler
                chemical_props = soil_data.get('chemical_properties', [])
                for prop in chemical_props:
                    if prop['name'] == 'Cation Exchange Capacity':
                        features['chemical_cation_exchange_capacity'] = prop['value']
                    elif prop['name'] == 'Clay CEC':
                        features['chemical_clay_cec'] = prop['value']
                    elif prop['name'] == 'Total Exchangeable Bases':
                        features['chemical_total_exchangeable_bases'] = prop['value']
                    elif prop['name'] == 'Base Saturation':
                        features['chemical_base_saturation'] = prop['value']
                    elif prop['name'] == 'Exchangeable Sodium Percentage':
                        features['chemical_exchangeable_sodium_percentage'] = prop['value']
                    elif prop['name'] == 'Aluminum Saturation':
                        features['chemical_aluminum_saturation'] = prop['value']
                
                # Tuzluluk özellikleri
                salinity_props = soil_data.get('salinity_properties', [])
                for prop in salinity_props:
                    if prop['name'] == 'Electrical Conductivity':
                        features['salinity_electrical_conductivity'] = prop['value']
                    elif prop['name'] == 'Total Carbon Equivalent':
                        features['salinity_total_carbon_equivalent'] = prop['value']
                    elif prop['name'] == 'Gypsum Content':
                        features['salinity_gypsum_content'] = prop['value']
            
            # Hava durumu verilerinden özellikleri çıkar
            if weather_data and isinstance(weather_data, list) and len(weather_data) > 0:
                # İlk günün verilerini al
                daily_data = weather_data[0] if isinstance(weather_data[0], dict) else {}
                
                # Sıcaklık verileri
                features['ortalama_en_yuksek_sicaklik_eylul'] = daily_data.get('apparent_temperature_max', 0)
                features['ortalama_en_yuksek_sicaklik_aralik'] = daily_data.get('apparent_temperature_max', 0)
                features['ortalama_en_dusuk_sicaklik_agustos'] = daily_data.get('apparent_temperature_min', 0)
                
                # Güneşlenme süresi
                features['ortalama_guneslenme_suresi_agustos'] = daily_data.get('sunshine_duration', 0) / 3600  # saniyeden saate
                features['ortalama_guneslenme_suresi_aralik'] = daily_data.get('sunshine_duration', 0) / 3600
                
                # Yağış verileri
                features['ortalama_yagisli_gun_sayisi_subat'] = daily_data.get('precipitation_hours', 0) / 24
                features['ortalama_yagisli_gun_sayisi_mart'] = daily_data.get('precipitation_hours', 0) / 24
                features['ortalama_yagisli_gun_sayisi_nisan'] = daily_data.get('precipitation_hours', 0) / 24
                features['ortalama_yagisli_gun_sayisi_agustos'] = daily_data.get('precipitation_hours', 0) / 24
                features['ortalama_yagisli_gun_sayisi_kasim'] = daily_data.get('precipitation_hours', 0) / 24
                features['ortalama_yagisli_gun_sayisi_yillik'] = daily_data.get('precipitation_hours', 0) / 24 * 12
                
                # Aylık yağış miktarları
                features['aylik_toplam_yagis_miktari_nisan'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_mayis'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_haziran'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_agustos'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_eylul'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_ekim'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_aralik'] = daily_data.get('precipitation_sum', 0)
                features['aylik_toplam_yagis_miktari_yillik'] = daily_data.get('precipitation_sum', 0) * 12
            
            # Eksik değerleri varsayılan değerlerle doldur
            default_values = {
                'physical_available_water_capacity': 0,
                'basic_organic_carbon': 1.0,
                'basic_c_n_ratio': 10.0,
                'texture_clay': 20.0,
                'texture_sand': 40.0,
                'texture_coarse_fragments': 5.0,
                'physical_reference_bulk_density': 1.5,
                'chemical_cation_exchange_capacity': 15.0,
                'chemical_clay_cec': 50.0,
                'chemical_total_exchangeable_bases': 20.0,
                'chemical_base_saturation': 80.0,
                'chemical_exchangeable_sodium_percentage': 2.0,
                'chemical_aluminum_saturation': 0.5,
                'salinity_electrical_conductivity': 1.0,
                'salinity_total_carbon_equivalent': 5.0,
                'salinity_gypsum_content': 0.5,
                'ortalama_en_yuksek_sicaklik_eylul': 25.0,
                'ortalama_en_yuksek_sicaklik_aralik': 10.0,
                'ortalama_en_dusuk_sicaklik_agustos': 20.0,
                'ortalama_guneslenme_suresi_agustos': 10.0,
                'ortalama_guneslenme_suresi_aralik': 5.0,
                'ortalama_yagisli_gun_sayisi_subat': 10.0,
                'ortalama_yagisli_gun_sayisi_mart': 10.0,
                'ortalama_yagisli_gun_sayisi_nisan': 8.0,
                'ortalama_yagisli_gun_sayisi_agustos': 2.0,
                'ortalama_yagisli_gun_sayisi_kasim': 8.0,
                'ortalama_yagisli_gun_sayisi_yillik': 100.0,
                'aylik_toplam_yagis_miktari_nisan': 50.0,
                'aylik_toplam_yagis_miktari_mayis': 40.0,
                'aylik_toplam_yagis_miktari_haziran': 30.0,
                'aylik_toplam_yagis_miktari_agustos': 10.0,
                'aylik_toplam_yagis_miktari_eylul': 30.0,
                'aylik_toplam_yagis_miktari_ekim': 60.0,
                'aylik_toplam_yagis_miktari_aralik': 80.0,
                'aylik_toplam_yagis_miktari_yillik': 600.0
            }
            
            for key, default_value in default_values.items():
                if key not in features:
                    features[key] = default_value
            
            logger.info(f"Features extracted successfully: {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return None
    
    def predict_crops(self, features: Dict[str, Any]) -> PredictionResponse:
        """
        Ürün tahmini yap
        
        Args:
            features: Özellik sözlüğü
            
        Returns:
            Tahmin sonucu
            
        Raises:
            HTTPException: Tahmin hatası
        """
        try:
            # Özellikleri DataFrame'e çevir
            feature_df = pd.DataFrame([features])
            
            # WRB4 kodunu sayısal değere çevir (basit encoding)
            wrb4_mapping = {
                'TC': 1, 'AN': 2, 'CM': 3, 'LV': 4, 'AC': 5, 'LX': 6, 'AL': 7, 'FR': 8,
                'VR': 9, 'SN': 10, 'SC': 11, 'GL': 12, 'HS': 13, 'AT': 14, 'CR': 15,
                'LP': 16, 'PZ': 17, 'PT': 18, 'PL': 19, 'ST': 20, 'NT': 21, 'CH': 22,
                'KS': 23, 'PH': 24, 'UM': 25, 'DU': 26, 'GY': 27, 'CL': 28, 'RT': 29,
                'FL': 30, 'AR': 31, 'RG': 32
            }
            
            if 'wrb4_code' in feature_df.columns:
                feature_df['wrb4_code'] = feature_df['wrb4_code'].map(wrb4_mapping).fillna(0)
            
            # Özellikleri ölçekle
            X_scaled = self.scaler.transform(feature_df)
            
            # Tahmin yap
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            
            # Ürün isimlerini al
            crop_names = self.metadata.get('crop_names', [])
            
            # Sonuçları hazırla
            crop_predictions = []
            recommended_count = 0
            total_probability = 0
            
            for i, crop_name in enumerate(crop_names):
                if i < len(predictions[0]):
                    prediction = bool(predictions[0][i])
                    probability = float(probabilities[0][i][1] if len(probabilities[0][i]) > 1 else probabilities[0][i][0])
                    
                    # Güven seviyesi belirle
                    if probability >= 0.8:
                        confidence = "Yüksek"
                    elif probability >= 0.6:
                        confidence = "Orta"
                    elif probability >= 0.4:
                        confidence = "Düşük"
                    else:
                        confidence = "Çok Düşük"
                    
                    crop_prediction = CropPrediction(
                        crop_name=crop_name,
                        prediction=prediction,
                        probability=probability,
                        confidence=confidence
                    )
                    
                    crop_predictions.append(crop_prediction)
                    
                    if prediction:
                        recommended_count += 1
                        total_probability += probability
            
            # İstatistikleri hesapla
            avg_probability = total_probability / recommended_count if recommended_count > 0 else 0
            recommendation_rate = (recommended_count / len(crop_names)) * 100
            high_confidence_count = sum(1 for cp in crop_predictions if cp.prediction and cp.probability >= 0.8)
            
            statistics = PredictionStatistics(
                total_crops_analyzed=len(crop_names),
                recommended_crops=recommended_count,
                recommendation_rate=round(recommendation_rate, 2),
                average_probability=round(avg_probability, 3),
                high_confidence_crops=high_confidence_count
            )
            
            return PredictionResponse(
                success=True,
                message="Crop prediction completed successfully",
                timestamp=datetime.now(),
                statistics=statistics,
                predictions=crop_predictions
            )
            
        except Exception as e:
            logger.error(f"Crop prediction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Crop prediction failed: {str(e)}"
            )
    
    def predict_crops_simple(self, features: Dict[str, Any]) -> SimplePredictionResponse:
        """
        Basit ürün tahmini yap (sadece önerilen ürünler)
        
        Args:
            features: Özellik sözlüğü
            
        Returns:
            Basit tahmin sonucu
        """
        try:
            # Tam tahmin yap
            full_prediction = self.predict_crops(features)
            
            # Sadece önerilen ürünleri filtrele
            recommended_crops = [
                cp for cp in full_prediction.predictions 
                if cp.prediction and cp.probability >= 0.5
            ]
            
            # Olasılığa göre sırala
            recommended_crops.sort(key=lambda x: x.probability, reverse=True)
            
            return SimplePredictionResponse(
                success=True,
                message=f"Found {len(recommended_crops)} recommended crops",
                timestamp=datetime.now(),
                recommended_crops=recommended_crops
            )
            
        except Exception as e:
            logger.error(f"Simple crop prediction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Simple crop prediction failed: {str(e)}"
            )
    
    def analyze_auto(self, longitude: float, latitude: float) -> PredictionResponse:
        """
        Otomatik analiz yap (konum + toprak + hava durumu + tahmin)
        
        Args:
            longitude: Boylam
            latitude: Enlem
            
        Returns:
            Tahmin sonucu
        """
        try:
            # Toprak verilerini al
            soil_data = self.get_soil_data_from_api(longitude, latitude)
            if not soil_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Soil data not available"
                )
            
            # Hava durumu verilerini al
            weather_data = self.get_weather_data_from_api(longitude, latitude)
            if not weather_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Weather data not available"
                )
            
            # Özellikleri çıkar
            features = self.extract_features_from_apis(soil_data, weather_data)
            if not features:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Feature extraction failed"
                )
            
            # Tahmin yap
            return self.predict_crops(features)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auto analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auto analysis failed: {str(e)}"
            )

# Servis instance'ı oluştur
try:
    ml_service = MLService()
    logger.info("Machine Learning Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Machine Learning Service: {str(e)}")
    ml_service = None

@router.get("/", response_model=Dict[str, Any])
async def root():
    """API ana endpoint'i"""
    return {
        "message": "Machine Learning API",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": ml_service is not None,
        "docs": "/docs"
    }

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine Learning Service not available"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Machine Learning API",
        "model_loaded": True,
        "model_name": ml_service.metadata.get('best_model', 'Unknown'),
        "model_score": ml_service.metadata.get('best_f1_macro', 0)
    }

@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Model bilgilerini getir"""
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine Learning Service not available"
        )
    
    try:
        return ModelInfoResponse(
            success=True,
            message="Model information retrieved successfully",
            timestamp=datetime.now(),
            best_model=ml_service.metadata.get('best_model', 'Unknown'),
            best_f1_macro=ml_service.metadata.get('best_f1_macro', 0),
            feature_count=ml_service.metadata.get('feature_count', 0),
            crop_count=ml_service.metadata.get('crop_count', 0),
            training_date=ml_service.metadata.get('training_date', 'Unknown'),
            crop_names=ml_service.metadata.get('crop_names', [])
        )
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model info retrieval failed: {str(e)}"
        )

@router.post("/predict", response_model=PredictionResponse)
async def predict_crops(request: ManualRequest):
    """
    Manuel veri ile ürün tahmini
    
    Args:
        request: Manuel veri isteği
        
    Returns:
        Ürün tahmin sonucu
        
    Raises:
        HTTPException: Tahmin hatası
    """
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine Learning Service not available"
        )
    
    try:
        logger.info("Manual crop prediction request received")
        
        # Request'i dict'e çevir
        features = request.model_dump()
        features.pop('method')  # Method'u çıkar
        
        return ml_service.predict_crops(features)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual prediction failed: {str(e)}"
        )

@router.post("/predict-simple", response_model=SimplePredictionResponse)
async def predict_crops_simple(request: ManualRequest):
    """
    Basit ürün tahmini (sadece önerilen ürünler)
    
    Args:
        request: Manuel veri isteği
        
    Returns:
        Basit ürün tahmin sonucu
        
    Raises:
        HTTPException: Tahmin hatası
    """
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine Learning Service not available"
        )
    
    try:
        logger.info("Simple crop prediction request received")
        
        # Request'i dict'e çevir
        features = request.model_dump()
        features.pop('method')  # Method'u çıkar
        
        return ml_service.predict_crops_simple(features)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simple prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simple prediction failed: {str(e)}"
        )

@router.post("/analyze-auto", response_model=PredictionResponse)
async def analyze_auto(request: AutoRequest):
    """
    Otomatik analiz (konum + toprak + hava durumu + tahmin)
    
    Args:
        request: Otomatik analiz isteği
        
    Returns:
        Otomatik analiz sonucu
        
    Raises:
        HTTPException: Analiz hatası
    """
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine Learning Service not available"
        )
    
    try:
        logger.info("Automatic analysis request received")
        
        # Otomatik koordinat tespiti
        longitude, latitude = ml_service.get_automatic_coordinates()
        
        if longitude is None or latitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Automatic location detection failed"
            )
        
        return ml_service.analyze_auto(longitude, latitude)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Automatic analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automatic analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="0.0.0.0", port=8000)
