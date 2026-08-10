select
    city,
    date,
    temp_max_c,
    temp_min_c,
    precipitation_mm
from {{ source('bronze', 'bronze_weather_daily') }}