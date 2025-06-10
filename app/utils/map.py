import requests
from config import Config

def get_address_from_tmap(latitude, longitude):
    """TMap API를 사용하여 위도/경도로 도로명 주소를 조회합니다."""
    url = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding"
    
    params = {
        "version": "1",
        "lat": str(latitude),
        "lon": str(longitude),
        "coordType": "WGS84GEO",
        "addressType": "A10"  # A10: 행정동 단위까지 표시
    }
    
    headers = {
        "Accept": "application/json",
        "appKey": Config.TMAP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if 'addressInfo' in result:
            address_info = result['addressInfo']
            
            # 도로명 주소 생성
            road_address = address_info.get('city_do', '') + ' ' + \
                          address_info.get('gu_gun', '') + ' ' + \
                          address_info.get('roadName', '') + ' ' + \
                          address_info.get('buildingIndex', '')
            
            # 건물명이 있는 경우 추가
            building_name = address_info.get('buildingName', '')
            if building_name:
                road_address += f' ({building_name})'
                
            return road_address.strip()
        return None
    except Exception as e:
        print(f"TMap API 호출 중 에러 발생: {str(e)}")
        return None