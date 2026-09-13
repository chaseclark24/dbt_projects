select
	symbol, 
	cast(date as date) as price_date, 
	open, 
	high, 
	low, 
	close, 
	volume
from {{ source('qdb_source', 'price_history') }}
