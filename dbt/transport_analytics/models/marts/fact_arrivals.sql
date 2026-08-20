with arrivals as (

    select *
    from {{ ref('stg_arrivals') }}

),

final as (

    select
        arrival_id,
        vehicle_id,
        line_id,
        line_name,
        station_id,
        station_name,
        destination_name,
        direction,
        mode_name,
        platform_name,

        time_to_station,
        minutes_to_station,

        expected_arrival,
        event_timestamp,
        ingested_at,

        date(expected_arrival) as service_date,
        extract(hour from expected_arrival) as service_hour,

        case
            when time_to_station <= 180 then '0-3 min'
            when time_to_station <= 300 then '3-5 min'
            when time_to_station <= 600 then '5-10 min'
            else '10+ min'
        end as wait_band

    from arrivals

)

select *
from final