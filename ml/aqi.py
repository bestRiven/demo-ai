import math

def _linear(aqi_high, aqi_low, conc_high, conc_low, concentration):
    """一个通用的线性插值函数，用于计算AQI值。"""
    return round(((concentration - conc_low) / (conc_high - conc_low)) * (aqi_high - aqi_low) + aqi_low)

def _calculate_pm25_aqi(concentration):
    """
    根据美国环保署(EPA)的标准，计算PM2.5 (24小时)的AQI。
    浓度单位: µg/m³。
    参考: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf (Page 8)
    """
    c = math.floor(concentration * 10) / 10
    if 0.0 <= c <= 12.0:
        return _linear(50, 0, 12.0, 0.0, c)
    elif 12.1 <= c <= 35.4:
        return _linear(100, 51, 35.4, 12.1, c)
    elif 35.5 <= c <= 55.4:
        return _linear(150, 101, 55.4, 35.5, c)
    elif 55.5 <= c <= 150.4:
        return _linear(200, 151, 150.4, 55.5, c)
    elif 150.5 <= c <= 250.4:
        return _linear(300, 201, 250.4, 150.5, c)
    elif 250.5 <= c <= 350.4:
        return _linear(400, 301, 350.4, 250.5, c)
    elif 350.5 <= c <= 500.4:
        return _linear(500, 401, 500.4, 350.5, c)
    else:
        return 501 # 超过500.4的值被视为"危险"并记为501+

def _calculate_o3_aqi(concentration_ppb):
    """
    根据美国环保署(EPA)的标准，计算O3 (8小时)的AQI。
    浓度单位: ppb (parts per billion)。
    参考: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf (Page 7)
    """
    c = math.floor(concentration_ppb)
    if 0 <= c <= 54:
        return _linear(50, 0, 54, 0, c)
    elif 55 <= c <= 70:
        return _linear(100, 51, 70, 55, c)
    elif 71 <= c <= 85:
        return _linear(150, 101, 85, 71, c)
    elif 86 <= c <= 105:
        return _linear(200, 151, 105, 86, c)
    elif 106 <= c <= 200:
        return _linear(300, 201, 200, 106, c)
    # 在此之上，断点是为1小时臭氧水平设定的，通常不用于每日AQI预报。
    else:
        return 301

def get_overall_aqi(pm25_conc, o3_conc_ppb):
    """
    Calculates the overall AQI by taking the maximum of individual pollutant AQIs.
    
    Args:
        pm25_conc (float): PM2.5 concentration in µg/m³.
        o3_conc_ppb (float): Ozone concentration in ppb.

    Returns:
        tuple: A tuple containing the final AQI value (int) and the dominant pollutant (str).
    """
    pm25_aqi = _calculate_pm25_aqi(pm25_conc)
    o3_aqi = _calculate_o3_aqi(o3_conc_ppb)

    if pm25_aqi >= o3_aqi:
        return pm25_aqi, "PM2.5"
    else:
        return o3_aqi, "Ozone"

def get_aqi_category(aqi):
    """
    Returns the AQI category and health recommendations based on the AQI value.
    """
    if 0 <= aqi <= 50:
        return ("Good", "Air quality is considered satisfactory, and air pollution poses little or no risk.", "good")
    elif 51 <= aqi <= 100:
        return ("Moderate", "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.", "moderate")
    elif 101 <= aqi <= 150:
        return ("Unhealthy for Sensitive Groups", "Members of sensitive groups may experience health effects. The general public is not likely to be affected.", "unhealthy")
    elif 151 <= aqi <= 200:
        return ("Unhealthy", "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.", "unhealthy")
    elif 201 <= aqi <= 300:
        return ("Very Unhealthy", "Health alert: everyone may experience more serious health effects.", "unhealthy")
    else: # aqi >= 301
        return ("Hazardous", "Health warnings of emergency conditions. The entire population is more likely to be affected.", "unhealthy")

if __name__ == '__main__':
    # Example usage:
    pm25_value = 40.5  # µg/m³
    o3_value = 65    # ppb

    final_aqi, dominant_pollutant = get_overall_aqi(pm25_value, o3_value)
    category, health_info, level_code = get_aqi_category(final_aqi)

    print(f"--- AQI Calculation Example ---")
    print(f"Input: PM2.5 = {pm25_value} µg/m³, Ozone = {o3_value} ppb")
    print(f"Final AQI: {final_aqi} (Dominant: {dominant_pollutant})")
    print(f"Category: {category}")
    print(f"Health Info: {health_info}")
    print(f"Image Code: {level_code}") 