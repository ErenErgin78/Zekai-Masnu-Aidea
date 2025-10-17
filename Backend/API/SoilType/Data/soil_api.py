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
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
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
app = FastAPI(
    title="Soil Analysis API",
    description="HWSD2 veritabanı kullanarak toprak analizi yapan API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domainler belirtilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        self.raster_file = os.path.join(self.script_dir, 'HWSD2.bil')
        self.db_file = os.path.join(self.script_dir, 'HWSD2.mdb')
        
        # Dosya varlığını kontrol et
        if not os.path.exists(self.raster_file):
            raise FileNotFoundError(f"Raster file not found: {self.raster_file}")
        if not os.path.exists(self.db_file):
            raise FileNotFoundError(f"Database file not found: {self.db_file}")
    
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

# Servis instance'ı oluştur
try:
    soil_service = SoilAnalysisService()
    logger.info("Soil Analysis Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Soil Analysis Service: {str(e)}")
    soil_service = None

@app.get("/", response_model=Dict[str, str])
async def root():
    """API ana endpoint'i"""
    return {
        "message": "Soil Analysis API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=Dict[str, str])
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

@app.post("/analyze", response_model=SoilAnalysisResponse)
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

@app.post("/analyze/auto", response_model=SoilAnalysisResponse)
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

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
