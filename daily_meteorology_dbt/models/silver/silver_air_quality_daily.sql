select
    city,
    cast(timestamp as date) as date,
    avg(pm2_5) as avg_pm2_5,
    avg(pm10) as avg_pm10,
    avg(us_aqi) as avg_us_aqi,
    max(us_aqi) as max_us_aqi
from {{ source('bronze', 'bronze_air_quality_hourly') }}
group by city, cast(timestamp as date)