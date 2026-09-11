select
  symbol,
  sector,
  industry,
  employees,
  country,
  exchange,
  cast(ipo_date as date) as ipo_date, -- null for all at the moment
  cast(updated_at as timestamp) as updated_at
from {{ source('qdb_source', 'company_metadata') }}
