# -*- coding: utf-8 -*-
"""
Soil Analysis API - FastAPI Implementation
==========================================

Bu API, koordinat bilgilerine göre toprak analizi yapan bir servistir.
HWSD2 (Harmonized World Soil Database) veritabanını kullanarak
toprak özelliklerini analiz eder.

Özellikler:
- Manuel koordinat girişi
- Otomatik IP tabanlı konum tespiti
- Detaylı toprak analizi
- JSON formatında sonuçlar
- Güvenlik korumaları
- Kapsamlı hata yönetimi

Author: Soil Analysis System
Version: 1.0.0
"""

import pyodbc
import rasterio
import os
import geocoder
import re
import random
import math
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import logging
from datetime import datetime

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI uygulaması oluştur
router = APIRouter(prefix="/soiltype", tags=["Soil Analysis"])


# Pydantic modelleri
class ManualRequest(BaseModel):
    """Manuel koordinat girişi için model"""
    method: str = Field(..., description="Method type", example="Manual")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam (-180 ile 180 arası)")
    latitude: float = Field(..., ge=-90, le=90, description="Enlem (-90 ile 90 arası)")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'manual':
            raise ValueError('Method must be "Manual" for manual coordinates')
        return v.title()
    
    @field_validator('longitude', 'latitude')
    @classmethod
    def validate_coordinates(cls, v):
        """Koordinat değerlerini doğrula ve güvenlik kontrolü yap"""
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        
        # SQL injection koruması - sadece sayısal değerlere izin ver
        if re.search(r'[^0-9.\-]', str(v)):
            raise ValueError('Invalid coordinate format - only numbers, dots and minus allowed')
        
        return float(v)

class AutoRequest(BaseModel):
    """Otomatik konum tespiti için model"""
    method: str = Field(..., description="Method type", example="Auto")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v.lower() != 'auto':
            raise ValueError('Method must be "Auto" for automatic location detection')
        return v.title()

class SoilProperty(BaseModel):
    """Toprak özelliği modeli"""
    name: str
    value: Any
    unit: Optional[str] = None

class SoilClassification(BaseModel):
    """Toprak sınıflandırması modeli"""
    wrb4_code: str
    wrb4_description: Optional[str] = None
    wrb2_code: str
    wrb2_description: Optional[str] = None
    fao90_code: str

class SoilAnalysisResponse(BaseModel):
    """Toprak analizi yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    coordinates: Dict[str, float]
    soil_id: int
    classification: SoilClassification
    basic_properties: List[SoilProperty]
    texture_properties: List[SoilProperty]
    physical_properties: List[SoilProperty]
    chemical_properties: List[SoilProperty]
    salinity_properties: List[SoilProperty]

class ErrorResponse(BaseModel):
    """Hata yanıt modeli"""
    success: bool = False
    error: str
    timestamp: datetime
    details: Optional[str] = None

class PointResponse(BaseModel):
    """Koordinat noktası modeli"""
    longitude: float
    latitude: float
    city: Optional[str] = None

class TurkeyPointsResponse(BaseModel):
    """Türkiye noktaları yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    mode: str
    total_points: int
    points: List[PointResponse]
    file_saved: bool
    file_path: Optional[str] = None
    csv_file_path: Optional[str] = None

class SoilAnalysisCSVResponse(BaseModel):
    """Toprak analizi CSV yanıt modeli"""
    success: bool
    message: str
    timestamp: datetime
    total_processed: int
    successful_analyses: int
    failed_analyses: int
    csv_file_path: Optional[str] = None

# WRB sınıflandırması açıklamaları (resmi kaynak)
WRB_DESCRIPTIONS = {
    'HS': 'Histosols - Soils with thick organic layers',
    'AT': 'Anthrosols - Soils with strong human influence (long and intensive agricultural use)',
    'TC': 'Technosols - Soils with strong human influence (containing significant amounts of artefacts)',
    'CR': 'Cryosols - Permafrost-affected soils',
    'LP': 'Leptosols - Thin or with many coarse fragments',
    'SN': 'Solonetz - Soils with high content of exchangeable Na',
    'VR': 'Vertisols - Alternating wet-dry conditions, shrink-swell clay minerals',
    'SC': 'Solonchaks - Soils with high concentration of soluble salts',
    'GL': 'Gleysols - Groundwater-affected, underwater or in tidal areas',
    'AN': 'Andosols - Soils with allophanes and/or Al-humus complexes',
    'PZ': 'Podzols - Soils with subsoil accumulation of humus and/or oxides',
    'PT': 'Plinthosols - Soils with accumulation and redistribution of Fe',
    'PL': 'Planosols - Stagnant water, abrupt textural difference',
    'ST': 'Stagnosols - Stagnant water, structural difference and/or moderate textural difference',
    'NT': 'Nitisols - Low-activity clays, P fixation, many Fe oxides, strongly structured',
    'FR': 'Ferralsols - Soils with dominance of kaolinite and oxides',
    'CH': 'Chernozems - Very dark topsoil, secondary carbonates',
    'KS': 'Kastanozems - Dark topsoil, secondary carbonates',
    'PH': 'Phaeozems - Dark topsoil, no secondary carbonates (unless very deep), high base status',
    'UM': 'Umbrisols - Dark topsoil, low base status',
    'DU': 'Durisols - Accumulation of, and cementation by, secondary silica',
    'GY': 'Gypsisols - Accumulation of secondary gypsum',
    'CL': 'Calcisols - Accumulation of secondary carbonates',
    'RT': 'Retisols - Interfingering of coarser-textured, lighter-coloured material',
    'AC': 'Acrisols - Low-activity clays, low base status',
    'LX': 'Lixisols - Low-activity clays, high base status',
    'AL': 'Alisols - High-activity clays, low base status',
    'LV': 'Luvisols - High-activity clays, high base status',
    'CM': 'Cambisols - Moderately developed soils',
    'FL': 'Fluvisols - Stratified fluviatile, marine or lacustrine sediments',
    'AR': 'Arenosols - Sandy soils',
    'RG': 'Regosols - No significant profile development'
}

class SoilAnalysisService:
    """Toprak analizi servis sınıfı"""
    
    def __init__(self):
        """Servis başlatıcı - dosya yollarını kontrol et"""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Veri klasörü çözümleme:
        # - Öncelikle 'SOIL_DATA_DIR' ortam değişkeni tanımlıysa onu kullan
        # - Sonra bu dosyanın yanındaki 'Data' klasörünü dene
        # - Ardından mevcut klasörü dene (geriye dönük uyumluluk)
        # - Son olarak üst dizindeki 'Data' klasörünü dene
        env_data_dir = os.getenv('SOIL_DATA_DIR')
        candidate_dirs = [
            os.path.abspath(env_data_dir) if env_data_dir else None,
            os.path.join(self.script_dir, 'Data'),
            self.script_dir,
            os.path.join(os.path.dirname(self.script_dir), 'Data')
        ]
        candidate_dirs = [d for d in candidate_dirs if d and os.path.isdir(d)]

        data_dir = None
        for d in candidate_dirs:
            raster_path = os.path.join(d, 'HWSD2.bil')
            db_path = os.path.join(d, 'HWSD2.mdb')
            if os.path.exists(raster_path) and os.path.exists(db_path):
                data_dir = d
                break

        # Eğer tam eşleşme bulunamazsa, mevcut adaylardan ilkini kullan
        # (aşağıdaki varlık kontrolleri hatayı açıklayıcı şekilde verecek)
        if not data_dir:
            data_dir = candidate_dirs[0] if candidate_dirs else os.path.join(self.script_dir, 'Data')

        self.data_dir = data_dir
        self.raster_file = os.path.join(self.data_dir, 'HWSD2.bil')
        self.db_file = os.path.join(self.data_dir, 'HWSD2.mdb')
        self.country_shapefile = os.path.join(self.data_dir, 'country.shp')
        
        # Dosya varlığını kontrol et
        if not os.path.exists(self.raster_file):
            raise FileNotFoundError(f"Raster file not found: {self.raster_file}")
        if not os.path.exists(self.db_file):
            raise FileNotFoundError(f"Database file not found: {self.db_file}")
        
        # Türkiye sınırlarını yükle
        self.turkey_bounds = None
        self._load_turkey_bounds()
    
    def _load_turkey_bounds(self):
        """Türkiye sınırlarını shapefile'dan yükle (dayanıklı yöntem)"""
        try:
            if not os.path.exists(self.country_shapefile):
                logger.warning("Country shapefile not found, using fallback bounds")
                self._set_fallback_bounds()
                return
            
            # Shapefile'ı yükle
            gdf = gpd.read_file(self.country_shapefile)
            if gdf is None or gdf.empty:
                logger.warning("Country shapefile is empty, using fallback bounds")
                self._set_fallback_bounds()
                return
            
            # CRS'yi WGS84 (EPSG:4326) yap
            try:
                if gdf.crs is None or gdf.crs.to_epsg() != 4326:
                    gdf = gdf.to_crs(epsg=4326)
            except Exception as _:
                # CRS dönüştürülemezse yine de devam et
                pass
            
            # Türkiye'yi bulmak için olası kolonlar ve değerler
            candidate_columns = [
                'NAME', 'NAME_EN', 'COUNTRY', 'NAME_0', 'ADMIN', 'SOVEREIGNT',
                'ADM0_A3', 'ISO_A3', 'ISO3', 'ISO2', 'CNTRY_NAME'
            ]
            name_variants_contains = ['Turkey', 'Türkiye']
            code_equals = ['TUR', 'TR']
            
            turkey_gdf = None
            for col in candidate_columns:
                if col in gdf.columns:
                    # Metin içerik eşleşmesi
                    if gdf[col].dtype == object:
                        mask_contains = gdf[col].astype(str).str.contains('|'.join(name_variants_contains), case=False, na=False)
                    else:
                        mask_contains = None
                    
                    # Kod eşitlik eşleşmesi
                    mask_equals = gdf[col].astype(str).isin(code_equals) if gdf[col].dtype == object else None
                    
                    combined_mask = None
                    if mask_contains is not None and mask_equals is not None:
                        combined_mask = mask_contains | mask_equals
                    elif mask_contains is not None:
                        combined_mask = mask_contains
                    elif mask_equals is not None:
                        combined_mask = mask_equals
                    
                    if combined_mask is not None and combined_mask.any():
                        turkey_gdf = gdf[combined_mask]
                        break
            
            # Hala bulunamadıysa, kabaca Türkiye bbox'una göre mekansal filtre dene
            if (turkey_gdf is None) or turkey_gdf.empty:
                try:
                    approx_min_lon, approx_max_lon = 25.0, 46.0
                    approx_min_lat, approx_max_lat = 35.0, 43.5
                    bbox = gpd.GeoDataFrame(geometry=[gpd.points_from_xy([approx_min_lon, approx_max_lon], [approx_min_lat, approx_max_lat]).unary_union.envelope], crs="EPSG:4326")
                    intersects_mask = gdf.geometry.intersects(bbox.geometry.iloc[0])
                    if intersects_mask.any():
                        # İçinde "Turkey"/"Türkiye" geçenlerden öncelik ver
                        subset = gdf[intersects_mask]
                        for col in candidate_columns:
                            if col in subset.columns and subset[col].dtype == object:
                                sub_mask = subset[col].astype(str).str.contains('|'.join(name_variants_contains), case=False, na=False)
                                if sub_mask.any():
                                    turkey_gdf = subset[sub_mask]
                                    break
                        if (turkey_gdf is None) or turkey_gdf.empty:
                            turkey_gdf = subset
                except Exception as _:
                    pass
            
            if turkey_gdf is not None and not turkey_gdf.empty:
                # Çoklu geometri varsa birleştir
                try:
                    turkey_geom = turkey_gdf.geometry.unary_union
                except Exception:
                    # Son çare: ilk geometriyi al
                    turkey_geom = turkey_gdf.geometry.iloc[0]
                self.turkey_bounds = turkey_geom
                logger.info("Turkey bounds loaded successfully from shapefile")
                return
            
            # Başarısızsa fallback
            logger.warning("Turkey not found in shapefile after all strategies, using fallback bounds")
            self._set_fallback_bounds()
        except Exception as e:
            logger.error(f"Error loading Turkey bounds: {str(e)}")
            self._set_fallback_bounds()
    
    def _set_fallback_bounds(self):
        """Yedek sınırları ayarla (basit dikdörtgen)"""
        self.turkey_bounds = {
            'min_lon': 26.0,
            'max_lon': 45.0,
            'min_lat': 36.0,
            'max_lat': 42.0
        }
        logger.info("Using fallback Turkey bounds")
        print(f"[TurkeyBounds] Fallback rectangle in use: lon=[{self.turkey_bounds['min_lon']}, {self.turkey_bounds['max_lon']}], lat=[{self.turkey_bounds['min_lat']}, {self.turkey_bounds['max_lat']}]")
    
    def _is_point_in_turkey(self, longitude: float, latitude: float) -> bool:
        """Noktanın Türkiye sınırları içinde olup olmadığını kontrol et"""
        try:
            if self.turkey_bounds is None:
                return False
            
            # Eğer bounds bir shapely geometry ise
            if hasattr(self.turkey_bounds, 'contains'):
                point = Point(longitude, latitude)
                return self.turkey_bounds.contains(point)
            
            # Eğer bounds bir dict ise (fallback)
            elif isinstance(self.turkey_bounds, dict):
                return (self.turkey_bounds['min_lon'] <= longitude <= self.turkey_bounds['max_lon'] and
                        self.turkey_bounds['min_lat'] <= latitude <= self.turkey_bounds['max_lat'])
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking point in Turkey: {str(e)}")
            return False
    
    def _get_city_name(self, longitude: float, latitude: float) -> Optional[str]:
        """Koordinat için şehir adını al (geopy ile güvenli istek)"""
        try:
            import time
            
            # İstekler arası bekleme (rate limit koruması)
            time.sleep(0.01)  # 0.2 saniye bekle
            
            # Geopy ile reverse geocoding
            geolocator = Nominatim(user_agent="soil_analysis_api")
            location = geolocator.reverse(f"{latitude}, {longitude}", language='tr')
            
            if location and location.raw:
                # Türkiye kontrolü
                address = location.raw.get('address', {})
                country = address.get('country', '').lower()
                
                if 'turkey' in country or 'türkiye' in country or 'tr' in country:
                    # Şehir ve ilçe bilgilerini al
                    state = address.get('state', '').strip()
                    city = address.get('city', '').strip()
                    town = address.get('town', '').strip()
                    
                    # Şehir/il ve ilçe kombinasyonu oluştur
                    location_parts = []
                    
                    # İl/şehir ekle
                    if state:
                        location_parts.append(state)
                    elif city:
                        location_parts.append(city)
                    
                    # İlçe ekle (varsa ve mahalle/köy değilse)
                    if town and len(town) > 3 and not any(suffix in town.lower() for suffix in ['mahallesi', 'köyü', 'beldesi']):
                        location_parts.append(town)
                    
                    if location_parts:
                        city_name = ', '.join(location_parts)
                        print(f"✅ Şehir bulundu: {city_name} ({longitude}, {latitude})")
                        return city_name
                    else:
                        print(f"❌ Şehir adı bulunamadı: ({longitude}, {latitude})")
                else:
                    print(f"❌ Türkiye dışı: {country} ({longitude}, {latitude})")
            else:
                print(f"❌ Konum bilgisi alınamadı: ({longitude}, {latitude})")
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting city name for ({longitude}, {latitude}): {str(e)}")
            print(f"❌ Hata: {str(e)} ({longitude}, {latitude})")
            return None
    
    def get_soil_id_from_raster(self, longitude: float, latitude: float) -> Optional[int]:
        """
        Raster harita dosyasından koordinata göre toprak ID'sini al
        
        Args:
            longitude: Boylam değeri
            latitude: Enlem değeri
            
        Returns:
            Toprak ID'si veya None
            
        Raises:
            Exception: Raster okuma hatası
        """
        try:
            with rasterio.open(self.raster_file) as src:
                # Koordinat sınırlarını kontrol et
                if not (src.bounds.left <= longitude <= src.bounds.right and 
                        src.bounds.bottom <= latitude <= src.bounds.top):
                    logger.warning(f"Coordinates ({longitude}, {latitude}) outside map bounds")
                    return None

                # Koordinatı piksel koordinatına çevir
                row, col = src.index(longitude, latitude)
                pixel_value = src.read(1, window=((row, row + 1), (col, col + 1)))
                
                if pixel_value.size > 0:
                    soil_id = int(pixel_value[0, 0])
                    logger.info(f"Soil ID found from raster: {soil_id}")
                    return soil_id
                return None
                
        except Exception as e:
            logger.error(f"Error reading raster file: {str(e)}")
            raise Exception(f"Raster file reading error: {str(e)}")
    
    def get_soil_data_from_database(self, soil_id: int) -> Optional[Dict[str, Any]]:
        """
        Veritabanından toprak verilerini al
        
        Args:
            soil_id: Toprak ID'si
            
        Returns:
            Toprak verileri sözlüğü veya None
            
        Raises:
            Exception: Veritabanı bağlantı hatası
        """
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            rf'DBQ={self.db_file};'
        )
        conn = None
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # HWSD2_SMU tablosundan toprak bilgilerini al
            smu_query = "SELECT * FROM [HWSD2_SMU] WHERE [HWSD2_SMU_ID] = ?"
            cursor.execute(smu_query, soil_id)
            smu_row = cursor.fetchone()

            if not smu_row:
                logger.warning(f"No record found in HWSD2_SMU for ID: {soil_id}")
                return None
            
            # SMU verilerini al
            smu_columns = [column[0] for column in cursor.description]
            smu_data = dict(zip(smu_columns, smu_row))
            
            # HWSD2_LAYERS tablosundan detaylı katman bilgilerini al
            layers_query = "SELECT * FROM [HWSD2_LAYERS] WHERE [HWSD2_SMU_ID] = ?"
            cursor.execute(layers_query, soil_id)
            layers_row = cursor.fetchone()

            if layers_row:
                layers_columns = [column[0] for column in cursor.description]
                layers_data = dict(zip(layers_columns, layers_row))
                
                # SMU ve Layers verilerini birleştir
                combined_data = {**smu_data, **layers_data}
                logger.info(f"Soil data retrieved successfully for ID: {soil_id}")
                return combined_data
            else:
                logger.warning(f"No record found in HWSD2_LAYERS for ID: {soil_id}")
                return smu_data

        except pyodbc.Error as ex:
            logger.error(f"Database error: {str(ex)}")
            if 'IM002' in str(ex):
                raise Exception("Microsoft Access Database Engine driver not found")
            else:
                raise Exception(f"Database error: {str(ex)}")
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise Exception(f"Database connection error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
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
                # Koordinatları tam sayıya yuvarla (güvenlik için)
                lat_rounded = round(lat)
                lon_rounded = round(lon)
                logger.info(f"Location detected: Lat={lat_rounded}, Lon={lon_rounded}")
                return lon_rounded, lat_rounded
            else:
                logger.warning("Automatic location detection failed")
                return None, None
                
        except Exception as e:
            logger.error(f"Error in automatic location detection: {str(e)}")
            raise Exception(f"Location detection error: {str(e)}")
    
    def analyze_soil(self, longitude: float, latitude: float) -> SoilAnalysisResponse:
        """
        Toprak analizi yap
        
        Args:
            longitude: Boylam
            latitude: Enlem
            
        Returns:
            Toprak analizi sonucu
            
        Raises:
            HTTPException: Analiz hatası
        """
        try:
            # Koordinatları yuvarla (güvenlik için)
            longitude = round(longitude)
            latitude = round(latitude)
            
            # Toprak ID'sini al
            soil_id = self.get_soil_id_from_raster(longitude, latitude)
            
            if not soil_id or soil_id == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No soil data found for the given coordinates"
                )
            
            # Toprak verilerini al
            soil_data = self.get_soil_data_from_database(soil_id)
            
            if not soil_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Soil data not found in database"
                )
            
            # Sınıflandırma bilgilerini hazırla
            classification = SoilClassification(
                wrb4_code=soil_data.get('WRB4', 'N/A'),
                wrb4_description=WRB_DESCRIPTIONS.get(soil_data.get('WRB4', '')),
                wrb2_code=soil_data.get('WRB2', 'N/A'),
                wrb2_description=WRB_DESCRIPTIONS.get(soil_data.get('WRB2', '')),
                fao90_code=soil_data.get('FAO90', 'N/A')
            )
            
            # Toprak özelliklerini kategorilere ayır
            basic_properties = self._extract_basic_properties(soil_data)
            texture_properties = self._extract_texture_properties(soil_data)
            physical_properties = self._extract_physical_properties(soil_data)
            chemical_properties = self._extract_chemical_properties(soil_data)
            salinity_properties = self._extract_salinity_properties(soil_data)
            
            return SoilAnalysisResponse(
                success=True,
                message="Soil analysis completed successfully",
                timestamp=datetime.now(),
                coordinates={"longitude": longitude, "latitude": latitude},
                soil_id=soil_id,
                classification=classification,
                basic_properties=basic_properties,
                texture_properties=texture_properties,
                physical_properties=physical_properties,
                chemical_properties=chemical_properties,
                salinity_properties=salinity_properties
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Soil analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Soil analysis failed: {str(e)}"
            )
    
    def _extract_basic_properties(self, soil_data: Dict[str, Any]) -> List[SoilProperty]:
        """Temel toprak özelliklerini çıkar"""
        properties = []
        
        if soil_data.get('PH_WATER') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="pH", value=soil_data.get('PH_WATER'), unit="pH units"))
        
        if soil_data.get('ORG_CARBON') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Organic Carbon", value=soil_data.get('ORG_CARBON'), unit="%"))
        
        if soil_data.get('TOTAL_N') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Total Nitrogen", value=soil_data.get('TOTAL_N'), unit="%"))
        
        if soil_data.get('CN_RATIO') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="C/N Ratio", value=soil_data.get('CN_RATIO'), unit="ratio"))
        
        return properties
    
    def _extract_texture_properties(self, soil_data: Dict[str, Any]) -> List[SoilProperty]:
        """Toprak doku özelliklerini çıkar"""
        properties = []
        
        if soil_data.get('CLAY') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Clay", value=soil_data.get('CLAY'), unit="%"))
        
        if soil_data.get('SILT') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Silt", value=soil_data.get('SILT'), unit="%"))
        
        if soil_data.get('SAND') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Sand", value=soil_data.get('SAND'), unit="%"))
        
        if soil_data.get('COARSE') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Coarse Fragments", value=soil_data.get('COARSE'), unit="%"))
        
        return properties
    
    def _extract_physical_properties(self, soil_data: Dict[str, Any]) -> List[SoilProperty]:
        """Fiziksel özellikleri çıkar"""
        properties = []
        
        if soil_data.get('BULK') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Bulk Density", value=soil_data.get('BULK'), unit="g/cm³"))
        
        if soil_data.get('REF_BULK') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Reference Bulk Density", value=soil_data.get('REF_BULK'), unit="g/cm³"))
        
        if soil_data.get('ROOT_DEPTH') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Root Depth", value=soil_data.get('ROOT_DEPTH'), unit="m"))
        
        if soil_data.get('AWC') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Available Water Capacity", value=soil_data.get('AWC'), unit="mm/m"))
        
        return properties
    
    def _extract_chemical_properties(self, soil_data: Dict[str, Any]) -> List[SoilProperty]:
        """Kimyasal özellikleri çıkar"""
        properties = []
        
        if soil_data.get('CEC_SOIL') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Cation Exchange Capacity", value=soil_data.get('CEC_SOIL'), unit="cmol/kg"))
        
        if soil_data.get('CEC_CLAY') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Clay CEC", value=soil_data.get('CEC_CLAY'), unit="cmol/kg"))
        
        if soil_data.get('CEC_EFF') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Effective CEC", value=soil_data.get('CEC_EFF'), unit="cmol/kg"))
        
        if soil_data.get('TEB') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Total Exchangeable Bases", value=soil_data.get('TEB'), unit="cmol/kg"))
        
        if soil_data.get('BSAT') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Base Saturation", value=soil_data.get('BSAT'), unit="%"))
        
        if soil_data.get('ESP') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Exchangeable Sodium Percentage", value=soil_data.get('ESP'), unit="%"))
        
        if soil_data.get('ALUM_SAT') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Aluminum Saturation", value=soil_data.get('ALUM_SAT'), unit="%"))
        
        return properties
    
    def _extract_salinity_properties(self, soil_data: Dict[str, Any]) -> List[SoilProperty]:
        """Tuzluluk özelliklerini çıkar"""
        properties = []
        
        if soil_data.get('ELEC_COND') not in [-9, -9.0, None]:
            properties.append(SoilProperty(name="Electrical Conductivity", value=soil_data.get('ELEC_COND'), unit="dS/m"))
        
        if soil_data.get('TCARBON_EQ') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Total Carbon Equivalent", value=soil_data.get('TCARBON_EQ'), unit="%"))
        
        if soil_data.get('GYPSUM') not in [-9.0, -9, None]:
            properties.append(SoilProperty(name="Gypsum Content", value=soil_data.get('GYPSUM'), unit="%"))
        
        return properties

    def generate_turkey_points(self, mode: str, lon_step: float = 0.5, lat_step: float = 0.5, 
                              count: Optional[int] = None, save_to_file: bool = True) -> TurkeyPointsResponse:
        """
        Türkiye sınırları içinde eşit aralıklı veya rastgele noktalar üretir
        
        Args:
            mode: "grid" (sabit adımlı) veya "stratified" (her hücreden rastgele)
            lon_step: Boylam adımı (grid modu için)
            lat_step: Enlem adımı (grid modu için)
            count: Toplam nokta sayısı (stratified modu için)
            save_to_file: Sonuçları txt dosyasına kaydet
            
        Returns:
            Türkiye noktaları yanıtı
            
        Raises:
            HTTPException: Parametre hatası
        """
        try:
            # Parametre validasyonu
            if mode not in ['grid', 'stratified']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mode must be 'grid' or 'stratified'"
                )
            
            # Türkiye sınırlarını al (shapefile'dan veya fallback)
            if isinstance(self.turkey_bounds, dict):
                # Fallback bounds kullan
                min_lon, max_lon = self.turkey_bounds['min_lon'], self.turkey_bounds['max_lon']
                min_lat, max_lat = self.turkey_bounds['min_lat'], self.turkey_bounds['max_lat']
            else:
                # Shapely geometry kullan - bounding box al
                bounds = self.turkey_bounds.bounds  # (minx, miny, maxx, maxy)
                min_lon, min_lat, max_lon, max_lat = bounds
            
            if mode == 'grid':
                if lon_step <= 0 or lat_step <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Step values must be positive"
                    )
                
                # Çok fazla nokta kontrolü
                lon_count = int((max_lon - min_lon) / lon_step) + 1
                lat_count = int((max_lat - min_lat) / lat_step) + 1
                total_points = lon_count * lat_count
                
                if total_points > 20000:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Too many points ({total_points}). Please increase step values."
                    )
                
                # Grid noktaları üret ve Türkiye sınırları içinde kontrol et
                points = []
                lon = min_lon
                while lon <= max_lon:
                    lat = min_lat
                    while lat <= max_lat:
                        if self._is_point_in_turkey(lon, lat):
                            # Şehir adını al
                            city_name = self._get_city_name(lon, lat)
                            if city_name:  # Sadece şehir adı bulunan noktaları ekle
                                points.append(PointResponse(
                                    longitude=round(lon, 6), 
                                    latitude=round(lat, 6),
                                    city=city_name
                                ))
                        lat += lat_step
                    lon += lon_step
                    
            else:  # stratified mode
                if count is None or count <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Count must be positive for stratified mode"
                    )
                
                if count > 20000:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Maximum 20000 points allowed"
                    )
                
                # Stratified rastgele noktalar üret - sadece Türkiye içindekileri al
                points = []
                attempts = 0
                max_attempts = count * 20  # Maksimum deneme sayısı (şehir kontrolü için artırıldı)
                
                while len(points) < count and attempts < max_attempts:
                    lon = random.uniform(min_lon, max_lon)
                    lat = random.uniform(min_lat, max_lat)
                    
                    if self._is_point_in_turkey(lon, lat):
                        # Şehir adını al
                        city_name = self._get_city_name(lon, lat)
                        if city_name:  # Sadece şehir adı bulunan noktaları ekle
                            points.append(PointResponse(
                                longitude=round(lon, 6), 
                                latitude=round(lat, 6),
                                city=city_name
                            ))
                    
                    attempts += 1
                
                if len(points) < count:
                    logger.warning(f"Could only generate {len(points)} points out of {count} requested")
            
            # Dosyaya kaydet
            file_path = None
            csv_file_path = None
            if save_to_file:
                try:
                    # Dosya adı oluştur
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base = f"turkey_points_{mode}_{timestamp}"
                    filename = f"{base}.txt"
                    csv_filename = f"{base}.csv"
                    file_path = os.path.join(self.script_dir, filename)
                    csv_file_path = os.path.join(self.script_dir, csv_filename)
                    
                    # Koordinatları TXT dosyasına yaz
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Türkiye Koordinat Noktaları - {mode.upper()} Modu\n")
                        f.write(f"# Üretim Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# Toplam Nokta Sayısı: {len(points)}\n")
                        f.write(f"# Format: longitude,latitude\n")
                        
                        # Fallback bilgisi (dikdörtgen sınırlar) varsa yaz
                        if isinstance(self.turkey_bounds, dict):
                            f.write(f"# Fallback bounds in use: lon=[{self.turkey_bounds['min_lon']}, {self.turkey_bounds['max_lon']}], lat=[{self.turkey_bounds['min_lat']}, {self.turkey_bounds['max_lat']}]\n")
                        else:
                            # Shapefile kullanıldıysa bounding box bilgisini bilgi amaçlı yaz
                            minx, miny, maxx, maxy = self.turkey_bounds.bounds
                            f.write(f"# Using shapefile geometry (bbox): lon=[{round(minx,4)}, {round(maxx,4)}], lat=[{round(miny,4)}, {round(maxy,4)}]\n")
                        
                        f.write("#" + "="*50 + "\n")
                        
                        for point in points:
                            f.write(f"{point.longitude},{point.latitude}\n")
                    
                    # Koordinatları CSV dosyasına longitude,latitude,city olarak yaz (başlık yok)
                    try:
                        with open(csv_file_path, 'w', encoding='utf-8') as cf:
                            for point in points:
                                cf.write(f"{point.longitude},{point.latitude},{point.city or ''}\n")
                        logger.info(f"Points saved to CSV file: {csv_file_path}")
                    except Exception as csv_err:
                        logger.error(f"CSV file save error: {str(csv_err)}")
                        csv_file_path = None
                    
                    logger.info(f"Points saved to file: {file_path}")
                    
                except Exception as e:
                    logger.error(f"File save error: {str(e)}")
                    file_path = None
                    csv_file_path = None
            
            return TurkeyPointsResponse(
                success=True,
                message=f"Turkey points generated successfully using {mode} mode",
                timestamp=datetime.now(),
                mode=mode,
                total_points=len(points),
                points=points,
                file_saved=file_path is not None,
                file_path=file_path,
                csv_file_path=csv_file_path
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Turkey points generation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Points generation failed: {str(e)}"
            )

    def analyze_coordinates_from_csv(self, csv_file_path: str) -> SoilAnalysisCSVResponse:
        """
        CSV dosyasındaki koordinatlar için toprak analizi yapar ve sonuçları CSV'ye kaydeder
        
        Args:
            csv_file_path: Analiz edilecek CSV dosyasının yolu
            
        Returns:
            Toprak analizi CSV yanıtı
            
        Raises:
            HTTPException: Dosya okuma veya analiz hatası
        """
        try:
            import pandas as pd
            
            # CSV dosyasını oku
            if not os.path.exists(csv_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"CSV file not found: {csv_file_path}"
                )
            
            # CSV'yi oku - sadece koordinatları al
            df = pd.read_csv(csv_file_path, skiprows=1, header=None, names=['longitude', 'latitude', 'city'])
            
            # Veri tiplerini dönüştür
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            
            # Geçersiz koordinatları filtrele
            df = df.dropna(subset=['longitude', 'latitude'])
            
            if df.empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid coordinates found in CSV file"
                )
            
            logger.info(f"Processing {len(df)} coordinates from CSV file")
            
            # Sonuçları saklamak için liste
            results = []
            successful_count = 0
            failed_count = 0
            
            # Her koordinat için analiz yap
            for index, row in df.iterrows():
                try:
                    longitude = float(row['longitude'])
                    latitude = float(row['latitude'])
                    city = str(row['city']) if pd.notna(row['city']) else ''
                    
                    # Toprak analizi yap
                    soil_analysis = self.analyze_soil(longitude, latitude)
                    
                    # Sonuçları hazırla - sadece koordinatlar ve kütüphane verileri
                    result_row = {
                        'longitude': longitude,
                        'latitude': latitude,
                        'city': city,
                        'soil_id': soil_analysis.soil_id,
                        'wrb4_code': soil_analysis.classification.wrb4_code,
                        'wrb4_description': soil_analysis.classification.wrb4_description,
                        'wrb2_code': soil_analysis.classification.wrb2_code,
                        'wrb2_description': soil_analysis.classification.wrb2_description,
                        'fao90_code': soil_analysis.classification.fao90_code
                    }
                    
                    # Temel özellikleri ekle
                    for prop in soil_analysis.basic_properties:
                        result_row[f'basic_{prop.name.lower().replace(" ", "_")}'] = prop.value
                    
                    # Doku özelliklerini ekle
                    for prop in soil_analysis.texture_properties:
                        result_row[f'texture_{prop.name.lower().replace(" ", "_")}'] = prop.value
                    
                    # Fiziksel özellikleri ekle
                    for prop in soil_analysis.physical_properties:
                        result_row[f'physical_{prop.name.lower().replace(" ", "_")}'] = prop.value
                    
                    # Kimyasal özellikleri ekle
                    for prop in soil_analysis.chemical_properties:
                        result_row[f'chemical_{prop.name.lower().replace(" ", "_")}'] = prop.value
                    
                    # Tuzluluk özelliklerini ekle
                    for prop in soil_analysis.salinity_properties:
                        result_row[f'salinity_{prop.name.lower().replace(" ", "_")}'] = prop.value
                    
                    results.append(result_row)
                    successful_count += 1
                    
                    logger.info(f"Analysis completed for ({longitude}, {latitude}) - {city}")
                    
                except Exception as e:
                    logger.warning(f"Analysis failed for ({row['longitude']}, {row['latitude']}): {str(e)}")
                    failed_count += 1
                    continue
            
            # Sonuçları CSV'ye kaydet
            if results:
                output_df = pd.DataFrame(results)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"soil_analysis_results_{timestamp}.csv"
                output_path = os.path.join(self.script_dir, output_filename)
                output_df.to_csv(output_path, index=False, encoding='utf-8')
                
                logger.info(f"Soil analysis results saved to: {output_path}")
                
                return SoilAnalysisCSVResponse(
                    success=True,
                    message=f"Soil analysis completed for {successful_count} coordinates",
                    timestamp=datetime.now(),
                    total_processed=len(df),
                    successful_analyses=successful_count,
                    failed_analyses=failed_count,
                    csv_file_path=output_path
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No successful analyses completed"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CSV soil analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"CSV soil analysis failed: {str(e)}"
            )

# Servis instance'ı oluştur
try:
    soil_service = SoilAnalysisService()
    logger.info("Soil Analysis Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Soil Analysis Service: {str(e)}")
    soil_service = None

@router.get("/", response_model=Dict[str, str])
async def root():
    """API ana endpoint'i"""
    return {
        "message": "Soil Analysis API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    if soil_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil Analysis Service not available"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Soil Analysis API"
    }

@router.post("/analyze", response_model=SoilAnalysisResponse)
async def analyze_soil(request: ManualRequest):
    """
    Manuel koordinat ile toprak analizi
    
    Args:
        request: Manuel koordinat isteği
        
    Returns:
        Toprak analizi sonucu
        
    Raises:
        HTTPException: Analiz hatası
    """
    if soil_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil Analysis Service not available"
        )
    
    try:
        logger.info(f"Manual soil analysis request: {request.longitude}, {request.latitude}")
        return soil_service.analyze_soil(request.longitude, request.latitude)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/analyze/auto", response_model=SoilAnalysisResponse)
async def analyze_soil_auto(request: AutoRequest):
    """
    Otomatik konum tespiti ile toprak analizi
    
    Args:
        request: Otomatik konum isteği
        
    Returns:
        Toprak analizi sonucu
        
    Raises:
        HTTPException: Analiz hatası
    """
    if soil_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil Analysis Service not available"
        )
    
    try:
        logger.info("Automatic soil analysis request")
        
        # Otomatik koordinat tespiti
        longitude, latitude = soil_service.get_automatic_coordinates()
        
        if longitude is None or latitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Automatic location detection failed"
            )
        
        return soil_service.analyze_soil(longitude, latitude)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Automatic analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automatic analysis failed: {str(e)}"
        )


@router.get("/points/turkey", response_model=TurkeyPointsResponse)
async def generate_turkey_points(
    mode: str = "grid",
    lon_step: float = 0.5,
    lat_step: float = 0.5,
    count: Optional[int] = None,
    save_to_file: bool = True
):
    """
    Türkiye sınırları içinde eşit aralıklı veya rastgele noktalar üretir
    
    Args:
        mode: "grid" (sabit adımlı) veya "stratified" (rastgele)
        lon_step: Boylam adımı (grid modu için, varsayılan: 0.5)
        lat_step: Enlem adımı (grid modu için, varsayılan: 0.5)
        count: Toplam nokta sayısı (stratified modu için)
        save_to_file: Sonuçları txt dosyasına kaydet (varsayılan: True)
        
    Returns:
        Türkiye noktaları listesi ve dosya bilgisi
        
    Raises:
        HTTPException: Parametre hatası
    """
    if soil_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil Analysis Service not available"
        )
    
    try:
        logger.info(f"Turkey points generation request: mode={mode}, lon_step={lon_step}, lat_step={lat_step}, count={count}")
        return soil_service.generate_turkey_points(mode, lon_step, lat_step, count, save_to_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Turkey points generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Points generation failed: {str(e)}"
        )

@router.post("/analyze/csv", response_model=SoilAnalysisCSVResponse)
async def analyze_coordinates_from_csv_endpoint(csv_file_path: str):
    """
    CSV dosyasındaki koordinatlar için toplu toprak analizi
    
    Args:
        csv_file_path: Analiz edilecek CSV dosyasının yolu
        
    Returns:
        Toprak analizi CSV yanıtı
        
    Raises:
        HTTPException: Dosya okuma veya analiz hatası
    """
    if soil_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil Analysis Service not available"
        )
    
    try:
        logger.info(f"CSV soil analysis request for file: {csv_file_path}")
        return soil_service.analyze_coordinates_from_csv(csv_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV soil analysis endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV soil analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
