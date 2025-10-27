# Model dosyasını analiz et
import joblib
import os

model_path = 'Model/model.pkl'
print(f'Dosya boyutu: {os.path.getsize(model_path):,} bytes')

try:
    model_data = joblib.load(model_path)
    print(f'Model tipi: {type(model_data)}')
    
    if isinstance(model_data, dict):
        print('Dictionary icerigi:')
        for key, value in model_data.items():
            print(f'  {key}: {type(value)}')
            if hasattr(value, 'predict'):
                print(f'    predict() metodu var')
            if hasattr(value, 'predict_proba'):
                print(f'    predict_proba() metodu var')
                
except Exception as e:
    print(f'Hata: {str(e)}')
