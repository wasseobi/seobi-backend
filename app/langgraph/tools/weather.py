from langchain_core.tools import tool
import requests
import os
from flask import g, request
from typing import Optional, Tuple
from datetime import datetime

ACCUWEATHER_API_KEY = os.getenv('ACCUWEATHER_API_KEY')
BASE_URL = "http://dataservice.accuweather.com"

def _normalize_location(location: str) -> str:
    """
    위치 문자열을 정규화합니다.
    예: '제주도' -> '제주', '서울특별시' -> '서울'
    """
    # 행정구역 명칭 제거
    replacements = {
        '특별시': '',
        '광역시': '',
        '특별자치시': '',
        '특별자치도': '',
        '도': '',
        '시': '',
        '군': '',
        '구': ''
    }
    
    result = location.lower()
    for old, new in replacements.items():
        result = result.replace(old.lower(), new)
    
    return result.strip()

def _check_location_similarity(input_loc: str, api_loc: str) -> float:
    """
    입력된 위치와 API 결과 위치의 유사도를 확인합니다.
    """
    # 정규화된 문자열로 비교
    norm_input = _normalize_location(input_loc)
    norm_api = _normalize_location(api_loc)
    
    # 정확히 일치하면 1.0
    if norm_input == norm_api:
        return 1.0
    
    # 한 문자열이 다른 문자열을 포함하면 0.8
    if norm_input in norm_api or norm_api in norm_input:
        return 0.8
    
    return 0.0

def _get_location_key(location: str) -> Tuple[str, str]:
    """
    위치 문자열로부터 AccuWeather Location Key를 가져옵니다.
    정확한 매치가 없을 경우 유사한 위치를 찾아 반환합니다.
    
    Returns:
        Tuple[str, str]: (location_key, found_location_name)
    """
    # 대체 위치 매핑
    alternative_locations = {
        '제주도': ['제주', '제주시'],
        '서울': ['서울특별시', '서울시'],
        '부산': ['부산광역시', '부산시'],
        '대구': ['대구광역시', '대구시'],
        '인천': ['인천광역시', '인천시'],
        '광주': ['광주광역시', '광주시'],
        '대전': ['대전광역시', '대전시'],
        '울산': ['울산광역시', '울산시'],
        '세종': ['세종특별자치시', '세종시'],
        '경기': ['경기도'],
        '강원': ['강원도'],
        '충북': ['충청북도'],
        '충남': ['충청남도'],
        '전북': ['전라북도'],
        '전남': ['전라남도'],
        '경북': ['경상북도'],
        '경남': ['경상남도'],
    }

    def try_location_search(search_location: str) -> Tuple[list, str]:
        """주어진 위치로 API 검색을 시도합니다."""
        url = f"{BASE_URL}/locations/v1/cities/search"
        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': search_location,
            'language': 'ko-kr'
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return [], search_location
        
        return response.json(), search_location

    def find_best_match(locations_list: list, original_loc: str) -> Tuple[dict, float]:
        """주어진 위치 목록에서 가장 적합한 매치를 찾습니다."""
        best_match = None
        best_similarity = -1
        
        for loc in locations_list:
            similarity = _check_location_similarity(original_loc, loc.get('LocalizedName', ''))
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = loc
        
        return best_match, best_similarity

    # 원래 위치로 먼저 시도
    locations, current_location = try_location_search(location)
    
    # 결과가 없으면 정규화된 위치로 시도
    if not locations:
        norm_location = _normalize_location(location)
        locations, current_location = try_location_search(norm_location)
        
        # 여전히 결과가 없으면 대체 위치 시도
        if not locations:
            # 정규화된 입력 위치로 대체 위치 찾기
            for key, values in alternative_locations.items():
                if norm_location in [_normalize_location(v) for v in values] or norm_location == _normalize_location(key):
                    # 원래 키로 시도
                    locations, current_location = try_location_search(key)
                    if locations:
                        break
                    
                    # 키로 찾지 못하면 값들로 시도
                    for alt_loc in values:
                        locations, current_location = try_location_search(alt_loc)
                        if locations:
                            break
                    if locations:
                        break

    # 여전히 결과가 없으면 에러
    if not locations:
        raise Exception(f"'{location}' 위치를 찾을 수 없습니다. 다른 표현으로 다시 시도해보세요.")

    # 가장 적합한 매치 찾기
    best_match, best_similarity = find_best_match(locations, location)
    
    if best_match:
        found_location = best_match['LocalizedName']
        # 찾은 위치가 입력과 다른 경우 메시지 출력
        if current_location != location or best_similarity < 1.0:
            print(f"'{location}' 대신 가장 유사한 위치 '{found_location}'의 날씨 정보를 사용합니다.")
        return best_match['Key'], found_location
    
    # 적절한 매치를 찾지 못한 경우 첫 번째 결과 사용
    selected_location = locations[0]
    found_location = selected_location['LocalizedName']
    print(f"'{location}'의 정확한 위치를 찾을 수 없어 '{found_location}'의 정보를 사용합니다.")
    return selected_location['Key'], found_location

@tool
def weather_daily_forecast(location: str, days: int = 1) -> str:
    """
    해당 위치의 일일 날씨 예보를 조회합니다.
    - 날씨 정보 표시 규칙:
        1. 날짜 표시 형식: YYYY년 MM월 DD일 (예: 2025년 6월 9일)
        2. 요일 표시 절대 금지 - 어떤 상황에서도 요일을 언급하지 마세요
        3. 맨 위에 전체적인 날씨 동향에 대한 간단한 요약을 추가하세요.
        4. 모든 기술적 수치(풍속, 습도 등)는 일반인이 이해하기 쉽게 해석하여 설명하세요.
        5. 날짜와 요일을 동시에 표시하는 것을 절대 금지합니다 (예: "6월 9일 (월)" 같은 형식 사용 불가).
        6. 날짜만 단독으로 표시하세요 (예: "2025년 6월 9일").
        이 형식을 엄격하게 따르고, 절대로 요일 정보를 포함하지 마세요.
    
    Args:
        location (str): 날씨를 조회할 위치
        days (int): 예보를 조회할 일 수 (1, 5, 10, 15 중 하나)
    """
    if days not in [1, 5, 10, 15]:
        return "예보 일수는 1, 5, 10, 15일 중 하나여야 합니다."
        
    try:
        location_key, found_location = _get_location_key(location)
        
        url = f"{BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'language': 'ko-kr',
            'metric': True,
            'details': True  # 상세 정보를 포함하도록 설정
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return "날씨 예보를 가져오는데 실패했습니다."
            
        forecast_data = response.json()
        
        # 결과 포맷팅
        forecast_info = f"[{found_location}의 날씨 예보]\n"
        
        # 주요 헤드라인이 있는 경우 표시
        if 'Headline' in forecast_data and forecast_data['Headline'].get('Text'):
            forecast_info += f"\n[주요 날씨 정보]\n"
            forecast_info += f"• {forecast_data['Headline']['Text']}\n"
        
        for daily in forecast_data['DailyForecasts']:
            date = datetime.strptime(daily['Date'], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y년 %m월 %d일")
            forecast_info += f"\n{'='*20} {date} {'='*20}\n"
            
            # 기본 정보
            forecast_info += f"\n[기본 정보]\n"
            forecast_info += f"• 최고기온: {daily['Temperature']['Maximum']['Value']}°C\n"
            forecast_info += f"• 최저기온: {daily['Temperature']['Minimum']['Value']}°C\n"
            forecast_info += f"• 체감 최고온도: {daily['RealFeelTemperature']['Maximum']['Value']}°C\n"
            forecast_info += f"• 체감 최저온도: {daily['RealFeelTemperature']['Minimum']['Value']}°C\n"
            
            # 일출/일몰 정보
            if 'Sun' in daily:
                sun_rise = datetime.strptime(daily['Sun']['Rise'], "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M")
                sun_set = datetime.strptime(daily['Sun']['Set'], "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M")
                forecast_info += f"• 일출: {sun_rise}\n"
                forecast_info += f"• 일몰: {sun_set}\n"
            
            # 낮 시간 정보
            forecast_info += f"\n[낮 시간 날씨]\n"
            forecast_info += f"• 날씨: {daily['Day']['IconPhrase']}\n"
            forecast_info += f"• 상세 설명: {daily['Day']['LongPhrase']}\n"
            forecast_info += f"• 강수 확률: {daily['Day']['PrecipitationProbability']}%\n"
            if daily['Day'].get('HasPrecipitation'):
                forecast_info += f"• 강수 유형: {daily['Day'].get('PrecipitationType', '정보 없음')}\n"
                forecast_info += f"• 강수 강도: {daily['Day'].get('PrecipitationIntensity', '정보 없음')}\n"
            forecast_info += f"• 비 확률: {daily['Day']['RainProbability']}%\n"
            forecast_info += f"• 눈 확률: {daily['Day']['SnowProbability']}%\n"
            forecast_info += f"• 강수 예상 시간: {daily['Day'].get('HoursOfPrecipitation', 0)}시간\n"
            forecast_info += f"• 구름 양: {daily['Day']['CloudCover']}%\n"
            
            # 바람 정보 (낮)
            if 'Wind' in daily['Day']:
                forecast_info += f"• 풍속: {daily['Day']['Wind']['Speed']['Value']} {daily['Day']['Wind']['Speed']['Unit']}\n"
                forecast_info += f"• 풍향: {daily['Day']['Wind']['Direction']['Localized']} ({daily['Day']['Wind']['Direction']['Degrees']}°)\n"
            
            # 밤 시간 정보
            forecast_info += f"\n[밤 시간 날씨]\n"
            forecast_info += f"• 날씨: {daily['Night']['IconPhrase']}\n"
            forecast_info += f"• 상세 설명: {daily['Night']['LongPhrase']}\n"
            forecast_info += f"• 강수 확률: {daily['Night']['PrecipitationProbability']}%\n"
            if daily['Night'].get('HasPrecipitation'):
                forecast_info += f"• 강수 유형: {daily['Night'].get('PrecipitationType', '정보 없음')}\n"
                forecast_info += f"• 강수 강도: {daily['Night'].get('PrecipitationIntensity', '정보 없음')}\n"
            forecast_info += f"• 비 확률: {daily['Night']['RainProbability']}%\n"
            forecast_info += f"• 눈 확률: {daily['Night']['SnowProbability']}%\n"
            forecast_info += f"• 강수 예상 시간: {daily['Night'].get('HoursOfPrecipitation', 0)}시간\n"
            forecast_info += f"• 구름 양: {daily['Night']['CloudCover']}%\n"
            
            # 바람 정보 (밤)
            if 'Wind' in daily['Night']:
                forecast_info += f"• 풍속: {daily['Night']['Wind']['Speed']['Value']} {daily['Night']['Wind']['Speed']['Unit']}\n"
                forecast_info += f"• 풍향: {daily['Night']['Wind']['Direction']['Localized']} ({daily['Night']['Wind']['Direction']['Degrees']}°)\n"
            
            # 대기질과 알레르기 정보
            if 'AirAndPollen' in daily:
                forecast_info += f"\n[대기질 및 알레르기 정보]\n"
                for item in daily['AirAndPollen']:
                    forecast_info += f"• {item['Name']}: {item['Category']} (수치: {item['Value']})\n"
        
        return forecast_info
        
    except Exception as e:
        return f"날씨 예보 조회 중 오류가 발생했습니다: {str(e)}"