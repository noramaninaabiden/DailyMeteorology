select
    w.city,
    w.date,
    w.temp_max_c,
    w.temp_min_c,
    w.precipitation_mm,
    a.avg_pm2_5,
    a.avg_pm10,
    a.avg_us_aqi,
    a.max_us_aqi
from {{ ref('silver_weather_daily') }} w
left join {{ ref('silver_air_quality_daily') }} a
    on w.city = a.city and w.date = a.date