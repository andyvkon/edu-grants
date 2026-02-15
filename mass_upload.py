import requests
import time

API_URL = "http://127.0.0.1:8000/api/v2/grants/"

def upload_points(count=100):
    # Теперь, после правки security.py, этот заголовок точно сработает
    headers = {"x-admin-token": "dev-admin"}
    
    print(f"🚀 Запуск массовой загрузки {count} точек...")
    
    for i in range(1, count + 1):
        data = {
            "title": f"Humanitarian Point #{i}",
            "summary": "Scalability test record for NIW project.",
            "status": "published", 
            "lat": 41.8781 + (i * 0.001), 
            "lng": -87.6298 + (i * 0.001),
            "category": "Emergency",
            "working_hours": "24/7"
        }
        
        try:
            response = requests.post(API_URL, json=data, headers=headers)
            if response.status_code == 200:
                print(f"✅ ПРИНЯТО! Точка {i}")
            else:
                print(f"❌ Отказ ({response.status_code}): {response.text}")
                if i == 1: break 
        except Exception as e:
            print(f"🚨 Ошибка: {e}")
            break
        
        time.sleep(0.5)

if __name__ == "__main__":
    upload_points(100)