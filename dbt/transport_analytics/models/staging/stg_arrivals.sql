with source as (

    select *
    from {{ source('transport', 'arrivals') }}

),

cleaned as (

    select
        id as arrival_id,
        vehicle_id,
        lower(line_id) as line_id,
        line_name,
        station_id,
        station_name,
        destination_name,
        direction,
        time_to_station,
        expected_arrival,
        event_timestamp,
        mode_name,
        platform_name,
        ingested_at,

        round(time_to_station / 60.0, 2) as minutes_to_station

    from source

    where
        station_name is not null
        and time_to_station >= 0

)

select *
from cleaned