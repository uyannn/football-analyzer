"""
天气数据抓取 (Open-Meteo, 免费无需API Key)
"""
import urllib.request
import json
from typing import Optional
from ..models import WeatherInfo
from ..config import OPEN_METEO_API, REQUEST_TIMEOUT


def log(msg):
    print(msg, flush=True)


class WeatherFetcher:
    """天气数据抓取器"""
    
    def __init__(self):
        self.city_coords = {
            "Oslo": (59.91, 10.75),
            "Bergen": (60.39, 5.32),
            "Stavanger": (58.97, 5.73),
            "Trondheim": (63.43, 10.39),
            "Molde": (62.73, 7.16),
            "Helsinki": (60.17, 24.94),
            "Tampere": (61.50, 23.79),
            "Turku": (60.45, 22.27),
            "Stockholm": (59.33, 18.07),
            "Gothenburg": (57.71, 11.97),
            "Malmo": (55.61, 13.00),
            "Seoul": (37.57, 126.98),
            "Busan": (35.18, 129.08),
        }
    
    def fetch_weather(self, city: str) -> Optional[WeatherInfo]:
        """获取指定城市的天气"""
        if city not in self.city_coords:
            log(f"[WARN] 未找到城市 {city} 的坐标信息")
            return None
        
        lat, lon = self.city_coords[city]
        
        try:
            url = (
                f"{OPEN_METEO_API}?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,wind_speed_10m,precipitation,weather_code"
                f"&timezone=auto"
            )
            
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
            data = json.loads(resp.read().decode("utf-8"))
            
            current = data.get("current", {})
            temp = current.get("temperature_2m", 20)
            wind = current.get("wind_speed_10m", 0)
            precip = current.get("precipitation", 0)
            code = current.get("weather_code", 0)
            
            condition = self._code_to_condition(code)
            impact = self._assess_impact(temp, wind, precip, condition)
            
            return WeatherInfo(
                city=city, temperature=temp, wind_speed=wind,
                precipitation=precip, condition=condition, impact=impact,
            )
        except Exception as e:
            log(f"[WARN] 获取 {city} 天气失败: {e}")
            return None
    
    def _code_to_condition(self, code: int) -> str:
        if code == 0: return "晴朗"
        elif code in [1, 2, 3]: return "多云"
        elif code in [45, 48]: return "雾"
        elif code in [51, 53, 55, 56, 57]: return "毛毛雨"
        elif code in [61, 63, 65, 66, 67]: return "雨"
        elif code in [71, 73, 75, 77]: return "雪"
        elif code in [80, 81, 82]: return "阵雨"
        elif code in [85, 86]: return "阵雪"
        elif code in [95, 96, 99]: return "雷暴"
        return "未知"
    
    def _assess_impact(self, temp, wind, precip, condition):
        impacts = []
        if temp > 30: impacts.append("高温可能导致球员疲劳")
        elif temp < 5: impacts.append("低温可能影响球员发挥")
        if wind > 40: impacts.append("大风严重影响传球和射门")
        elif wind > 25: impacts.append("较强风力可能影响长传")
        if precip > 10: impacts.append("大雨导致场地湿滑，利好防守")
        elif precip > 2: impacts.append("小雨可能影响控球")
        if "雷暴" in condition: impacts.append("雷暴可能导致比赛中断")
        if "雪" in condition: impacts.append("雪天影响视线和控球")
        return "; ".join(impacts) if impacts else "天气良好，无明显影响"
    
    def fetch_for_league(self, league: str) -> Optional[WeatherInfo]:
        from ..config import LEAGUE_CITIES
        cities = LEAGUE_CITIES.get(league, [])
        if not cities: return None
        return self.fetch_weather(cities[0])
