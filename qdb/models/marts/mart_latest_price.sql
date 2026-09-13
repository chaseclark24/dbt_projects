with latest_price as (
    select price_date,
    symbol,
    open, 
	high, 
	low, 
	close, 
	volume,
    row_number() over (partition by symbol order by price_date desc) as row_rank
    from {{ ref('stg_price_history') }}
)




select
    price_date,
    symbol,
    open, 
	high, 
	low, 
	close, 
	volume
from latest_price
where row_rank = 1
    