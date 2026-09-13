select 	
    symbol, 
	price_date, 
	open, 
	high, 
	low, 
	close, 
	volume,
	lag(close, 7) over (partition by symbol order by symbol, price_date) as close_7_days_ago,
	lag(close, 30) over (partition by symbol order by symbol, price_date) as close_30_days_ago,
	    (close - lag(close, 1) over (partition by symbol order by symbol, price_date)) 
            / nullif(lag(close, 1) over (partition by symbol order by symbol, price_date), 0) as return_daily,
	    (close - lag(close, 7) over (partition by symbol order by symbol, price_date)) 
            / nullif(lag(close, 7) over (partition by symbol order by symbol, price_date), 0) as return_7_days,
	    (close - lag(close, 30) over (partition by symbol order by symbol, price_date)) 
            / nullif(lag(close, 30) over (partition by symbol order by symbol, price_date), 0) as return_30_days,
	sum(volume) over (partition by symbol order by price_date range between interval 29 days preceding and current row) as volume_30_day
from {{ ref('stg_price_history') }}
