# -*- coding: utf-8 -*-
"""
Machine Learning API (Router Only)
==================================

Bu dosya yalnızca FastAPI router'ını tanımlar ve `Backend/API/main.py` içinde
`app.include_router(...)` ile bağlanır. Kendi başına server başlatmaz; böylece
port çakışması yaşanmaz ve diğer API'lerle (SoilType, Weather) uyumlu çalışır.

Özellikler:
- LLM entegrasyonuna uygun tek endpoint: POST /ml/analyze
- SoilType API ile dayanıklı entegrasyon (yumuşak health-check, kısa timeout, fallback)
- Model yükleme (pickle/joblib) + güvenli kural tabanlı fallback
- Koordinat validasyonu, -9/NA korumaları, kısa ve açıklayıcı loglar
"""

import os
import pickle
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator


# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# FastAPI Router (yalnızca router, server başlatmaz)
router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# ---------- Pydantic Modelleri ----------
class Coordinates(BaseModel):
    """Koordinat verisi modeli (enlem/boylam doğrulaması içerir)."""
    longitude: float
    latitude: float

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return float(v)

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return float(v)


class MLRequest(BaseModel):
    """ML analizi için istek modeli (LLM entegrasyonuyla uyumlu)."""
    method: str = Field(..., description="'Auto' veya 'Manual'")
    coordinates: Optional[Coordinates] = Field(None, description="Manual mod için koordinatlar")

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v.lower() not in ["auto", "manual"]:
            raise ValueError('Method must be "Auto" or "Manual"')
        return v.title()


class PlantRecommendation(BaseModel):
    """Bitki önerisi nesnesi."""
    plant_name: str
    confidence_score: float
    probability: float


class MLAnalysisResponse(BaseModel):
    """ML analizi yanıt modeli."""
    success: bool
    message: str
    timestamp: datetime
    coordinates: Dict[str, float]
    soil_data: Dict[str, Any]
    climate_data: Dict[str, Any]
    recommendations: List[PlantRecommendation]
    model_info: Dict[str, Any]


# ---------- Servis Sınıfı ----------
class MLService:
    """ML servis katmanı: model yükleme, özellik hazırlama ve tahmin."""

    def __init__(self) -> None:
        # Dosya yollarını güvenli biçimde ayarla
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.script_dir, 'Model', 'model.pkl')
        self.data_path = os.path.join(self.script_dir, 'Data', 'final5.csv')
        self.soil_api_base = "http://localhost:8000/soiltype"

        # Modeli yükle (pickle→joblib) ve fallback flag'i belirle
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.metadata: Dict[str, Any] = {}
        self.fallback_mode: bool = False

        self._load_model_safe()
        self.feature_columns = self._define_feature_columns()

    def _load_model_safe(self) -> None:
        """Modeli yükler; başarısızsa kural tabanlı fallback'a geçer."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                logger.info("Model loaded via pickle")
            except Exception as pick_err:
                try:
                    import joblib
                    model_data = joblib.load(self.model_path)
                    logger.info("Model loaded via joblib")
                except Exception as job_err:
                    raise RuntimeError(f"Model load failed: {pick_err} | {job_err}")

            if isinstance(model_data, dict):
                self.model = model_data.get('model')
                self.scaler = model_data.get('scaler')
                self.metadata = model_data.get('metadata', {})
            else:
                self.model = model_data
                self.scaler = None
                self.metadata = {}

            self.fallback_mode = self.model is None
            if self.fallback_mode:
                logger.warning("Model object is None; entering fallback mode")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            self.model = None
            self.scaler = None
            self.metadata = {"status": "load_failed"}
            self.fallback_mode = True

    def _define_feature_columns(self) -> List[str]:
        """Model eğitimi sırasında kullanılan sütun isimleri (sıra korunur)."""
        cols = [
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
        return cols

    @staticmethod
    def _json_safe(value: Any) -> Any:
        """Yanıtta JSON'a serilemeyen türleri güvenli string'e çevirir (rekürsif)."""
        try:
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(k): MLService._json_safe(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [MLService._json_safe(v) for v in value]
            try:
                return str(value)
            except Exception:
                return f"<{type(value).__name__}>"
        except Exception:
            return f"<{type(value).__name__}>"

    # ---------- SoilType Entegrasyonu ----------
    def _soiltype_health_soft(self) -> None:
        """Health kontrolü yumuşak: başarısız olsa bile akış devam eder."""
        try:
            resp = requests.get(f"{self.soil_api_base}/health", timeout=15)
            if resp.status_code != 200:
                logger.warning(f"SoilType health non-200: {resp.status_code}")
        except Exception as e:
            logger.warning(f"SoilType health check failed: {e}")

    def _soiltype_post(self, path: str, payload: Dict[str, Any], timeout: tuple[int, int]) -> Dict[str, Any]:
        url = f"{self.soil_api_base}{path}"
        last_err: Optional[Exception] = None
        for attempt in range(2):
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.Timeout as e:
                last_err = e
                logger.warning(f"SoilType timeout at {url} (attempt {attempt+1}/2)")
            except requests.exceptions.RequestException as e:
                last_err = e
                logger.warning(f"SoilType request error at {url} (attempt {attempt+1}/2): {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"SoilType call failed: {last_err}")

    def _get_soil_data(self, method: str, coords: Optional[Coordinates]) -> Dict[str, Any]:
        """SoilType API'den toprak verisini alır; auto→manual fallback uygular."""
        self._soiltype_health_soft()
        connect_read = (5, 8)

        if method == "Manual" and coords is not None:
            payload = {"method": "Manual", "longitude": coords.longitude, "latitude": coords.latitude}
            return self._soiltype_post("/analyze", payload, connect_read)

        # Auto akış: önce auto, başarısızsa TR merkez fallback
        try:
            return self._soiltype_post("/analyze/auto", {"method": "Auto"}, connect_read)
        except HTTPException:
            fb = {"method": "Manual", "longitude": 35.0, "latitude": 39.0}
            logger.info("Auto failed; using manual fallback coordinates (TR)")
            return self._soiltype_post("/analyze", fb, connect_read)
    
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
            logger.warning(f"Climate CSV read warning: {e}")
        return {}

    def _get_climate_features(self) -> Dict[str, float]:
        """İklim özellikleri: CSV varsa kullan, aksi halde makul defaultlar."""
        defaults: Dict[str, float] = {
            'Ortalama En Yüksek Sıcaklık (°C)_Eylül': 26.0,
            'Ortalama En Yüksek Sıcaklık (°C)_Aralık': 10.0,
            'Ortalama En Düşük Sıcaklık (°C)_Ağustos': 18.0,
            'Ortalama Güneşlenme Süresi (saat)_Ağustos': 10.0,
            'Ortalama Güneşlenme Süresi (saat)_Aralık': 5.0,
            'Ortalama Yağışlı Gün Sayısı_Şubat': 10.0,
            'Ortalama Yağışlı Gün Sayısı_Mart': 9.0,
            'Ortalama Yağışlı Gün Sayısı_Nisan': 8.0,
            'Ortalama Yağışlı Gün Sayısı_Ağustos': 2.0,
            'Ortalama Yağışlı Gün Sayısı_Kasım': 8.0,
            'Ortalama Yağışlı Gün Sayısı_Yıllık': 90.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Nisan': 45.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Mayıs': 40.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Haziran': 25.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ağustos': 10.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Eylül': 20.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Ekim': 35.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Aralık': 60.0,
            'Aylık Toplam Yağış Miktarı Ortalaması (mm)_Yıllık': 550.0
        }
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                if not df.empty:
                    row = df.sample(n=1).iloc[0]
                    for k in list(defaults.keys()):
                        if k in df.columns:
                            try:
                                defaults[k] = float(row[k])
                            except Exception:
                                pass
        except Exception as e:
            logger.warning(f"Climate defaults read warning: {e}")
        return defaults

    def _prepare_vector(self, soil_feats: Dict[str, float], climate_feats: Dict[str, float]) -> np.ndarray:
        merged: Dict[str, float] = {**climate_feats, **soil_feats}
        vec = [float(merged.get(col, 0.0)) for col in self.feature_columns]
        arr = np.array(vec, dtype=float).reshape(1, -1)
        if self.scaler is not None:
            try:
                arr = self.scaler.transform(arr)
            except Exception as e:
                logger.warning(f"Scaler transform failed: {e}")
        return arr

    def _plant_names(self) -> List[str]:
        return [
            'Arpa', 'Ayçiçeği', 'Badem', 'Biber', 'Buğday', 'Ceviz', 'Domates', 'Elma',
            'Fasulye', 'Fındık', 'Fıstık', 'Gül', 'Haşhaş', 'Kayısı', 'Kiraz', 'Kivi',
            'Mercimek', 'Meyve', 'Muz', 'Mısır', 'Narenciye', 'Nohut', 'Pamuk', 'Patates',
            'Patlıcan', 'Pirinç', 'Sarımsak', 'Sebze', 'Turunçgiller', 'Tütün', 'Yer Fıstığı',
            'Zeytin', 'Çay', 'Çilek', 'Üzüm', 'İncir', 'Şeftali', 'Şeker Pancarı', 'Şerbetçi Otu'
        ]

    def _predict(self, X: np.ndarray) -> List[PlantRecommendation]:
        if self.fallback_mode or self.model is None:
            return self._fallback_recommendations(X)
        try:
            if hasattr(self.model, 'predict_proba'):
                probs = self.model.predict_proba(X)[0]
            else:
                pred = int(self.model.predict(X)[0])
                probs = np.zeros(len(self._plant_names()), dtype=float)
                probs[pred] = 1.0
            names = self._plant_names()
            recs: List[PlantRecommendation] = []
            for name, p in zip(names, probs):
                if p > 0.1:
                    recs.append(PlantRecommendation(plant_name=name, confidence_score=round(float(p) * 100, 2), probability=round(float(p), 4)))
            recs.sort(key=lambda r: r.confidence_score, reverse=True)
            return recs[:5]
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return self._fallback_recommendations(X)

    def _fallback_recommendations(self, X: np.ndarray) -> List[PlantRecommendation]:
        feats = dict(zip(self.feature_columns, X[0]))
        wrb = int(round(float(feats.get('wrb4_code', 21))))
        annual_rain = float(feats.get('Aylık Toplam Yağış Miktarı Ortalaması (mm)_Yıllık', 550))
        sep_max = float(feats.get('Ortalama En Yüksek Sıcaklık (°C)_Eylül', 26))
        dec_max = float(feats.get('Ortalama En Yüksek Sıcaklık (°C)_Aralık', 10))

        recs: List[PlantRecommendation] = []
        if wrb in [17, 18, 19]:
            recs += [
                PlantRecommendation(plant_name="Buğday", confidence_score=85.0, probability=0.85),
                PlantRecommendation(plant_name="Arpa", confidence_score=80.0, probability=0.80),
                PlantRecommendation(plant_name="Ayçiçeği", confidence_score=75.0, probability=0.75),
                PlantRecommendation(plant_name="Mısır", confidence_score=70.0, probability=0.70),
                PlantRecommendation(plant_name="Şeker Pancarı", confidence_score=65.0, probability=0.65)
            ]
        elif wrb in [28, 29]:
            recs += [
                PlantRecommendation(plant_name="Pamuk", confidence_score=85.0, probability=0.85),
                PlantRecommendation(plant_name="Mısır", confidence_score=80.0, probability=0.80),
                PlantRecommendation(plant_name="Domates", confidence_score=75.0, probability=0.75),
                PlantRecommendation(plant_name="Biber", confidence_score=70.0, probability=0.70),
                PlantRecommendation(plant_name="Patates", confidence_score=65.0, probability=0.65)
            ]
        elif wrb in [21, 22]:
            recs += [
                PlantRecommendation(plant_name="Zeytin", confidence_score=85.0, probability=0.85),
                PlantRecommendation(plant_name="Üzüm", confidence_score=80.0, probability=0.80),
                PlantRecommendation(plant_name="Badem", confidence_score=75.0, probability=0.75),
                PlantRecommendation(plant_name="Kayısı", confidence_score=70.0, probability=0.70),
                PlantRecommendation(plant_name="Şeftali", confidence_score=65.0, probability=0.65)
            ]
        else:
            recs += [
                PlantRecommendation(plant_name="Buğday", confidence_score=80.0, probability=0.80),
                PlantRecommendation(plant_name="Arpa", confidence_score=75.0, probability=0.75),
                PlantRecommendation(plant_name="Mısır", confidence_score=70.0, probability=0.70),
                PlantRecommendation(plant_name="Patates", confidence_score=65.0, probability=0.65),
                PlantRecommendation(plant_name="Fasulye", confidence_score=60.0, probability=0.60)
            ]
        if sep_max > 30:
            recs.append(PlantRecommendation(plant_name="Pamuk", confidence_score=90.0, probability=0.90))
            recs.append(PlantRecommendation(plant_name="Mısır", confidence_score=85.0, probability=0.85))
        if dec_max < 5:
            recs.append(PlantRecommendation(plant_name="Arpa", confidence_score=90.0, probability=0.90))
            recs.append(PlantRecommendation(plant_name="Patates", confidence_score=85.0, probability=0.85))
        if annual_rain < 400:
            recs.append(PlantRecommendation(plant_name="Zeytin", confidence_score=90.0, probability=0.90))
            recs.append(PlantRecommendation(plant_name="Badem", confidence_score=85.0, probability=0.85))
        if annual_rain > 800:
            recs.append(PlantRecommendation(plant_name="Çay", confidence_score=90.0, probability=0.90))
            recs.append(PlantRecommendation(plant_name="Fındık", confidence_score=85.0, probability=0.85))
        uniq: Dict[str, PlantRecommendation] = {}
        for r in sorted(recs, key=lambda x: x.confidence_score, reverse=True):
            if r.plant_name not in uniq:
                uniq[r.plant_name] = r
        return list(uniq.values())[:5]

    # ---------- Ana Akış ----------
    def analyze(self, req: MLRequest) -> MLAnalysisResponse:
        soil_raw = self._get_soil_data(req.method, req.coordinates)
        used_coords = soil_raw.get('coordinates', {'longitude': 0.0, 'latitude': 0.0})
        soil_feats = self._extract_soil_features(soil_raw)
        climate_feats = self._get_climate_features()
        vector = self._prepare_vector(soil_feats, climate_feats)
        recs = self._predict(vector)
        model_info = {
            "model_type": type(self.model).__name__ if self.model else "Fallback Rules",
            "scaler_type": type(self.scaler).__name__ if self.scaler else "None",
            "feature_count": len(self.feature_columns),
            "recommendation_count": len(recs),
            "fallback_mode": self.fallback_mode,
            "metadata": self._json_safe(self.metadata),
        }
        return MLAnalysisResponse(
            success=True,
            message="ML analysis completed successfully",
            timestamp=datetime.now(),
            coordinates={"longitude": float(used_coords.get('longitude', 0.0)), "latitude": float(used_coords.get('latitude', 0.0))},
            soil_data=soil_feats,
            climate_data=climate_feats,
            recommendations=recs,
            model_info=model_info,
        )


# ---------- Router Endpoint'leri ----------
try:
    _ml_service = MLService()
    logger.info("ML Service ready")
except Exception as e:
    logger.error(f"ML Service initialization failed: {e}")
    _ml_service = None


@router.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    return {
        "message": "Machine Learning API",
        "version": "2.0.0",
        "status": "running" if _ml_service else "unavailable",
        "docs": "/docs",
    }


@router.get("/health", response_model=Dict[str, str])
async def health() -> Dict[str, str]:
    if _ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ML Service not available")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Machine Learning API",
        "model_status": "Active" if not _ml_service.fallback_mode else "Fallback",
        "model_type": type(_ml_service.model).__name__ if _ml_service.model else "Fallback Rules",
        "scaler_type": type(_ml_service.scaler).__name__ if _ml_service.scaler else "None",
        "fallback_mode": str(_ml_service.fallback_mode),
    }


@router.post("/analyze", response_model=MLAnalysisResponse)
async def analyze(request: MLRequest) -> MLAnalysisResponse:
    if _ml_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ML Service not available")
    try:
        return _ml_service.analyze(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML analysis error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ML analysis failed: {e}")


# ------------------------------------------------------------
# Opsiyonel Standalone Sunucu (yalnızca doğrudan çalıştırıldığında)
# Bu, port çakışmasını önlemek için 8003'te yalnızca ML router'ını ayağa kaldırır.
# `Backend/API/main.py` içinde include edildiğinde etkisi yoktur.
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        import uvicorn
        from fastapi import FastAPI

        app = FastAPI(title="Machine Learning API (Standalone)", version="2.0.0")
        app.include_router(router)

        uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start standalone ML server: {e}")


