with arrivals as (

    select *
    from {{ ref('fact_arrivals') }}

),

line_metrics as (

    select
        line_id,
        line_name,

        count(*) as prediction_count,

        count(distinct station_id) as station_count,

        count(distinct vehicle_id) as unique_vehicles,

        round(avg(minutes_to_station), 2) as avg_wait_minutes,

        round(min(minutes_to_station), 2) as min_wait_minutes,

        round(max(minutes_to_station), 2) as max_wait_minutes,

        count(*) filter (
            where time_to_station <= 180
        ) as arrivals_within_3_minutes,

        max(ingested_at) as last_updated

    from arrivals

    group by
        line_id,
        line_name

)

select *
from line_metrics