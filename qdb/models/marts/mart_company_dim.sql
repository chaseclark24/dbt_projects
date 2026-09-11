select
  c.symbol,
  c.sector,
  c.industry,
  c.employees,
  c.country,
  c.exchange,
  c.ipo_date, -- null for all at the moment
  c.updated_at as company_metadata_updated_at,
  f.total_revenue,
  f.total_revenue_prev,
  f.revenue_growth_pct,
  f.net_income,
  f.total_cash,
  f.total_debt,
  f.operating_cash_flow,
  f.net_margin_pct,
  f.net_cash,
  f.has_negative_cash_flow,
  f.going_concern,
  f.cash_as_of,
  f.source_updated_at as financials_updated_at,
  f.fiscal_year,
  f.period_end,
  f.operating_cash_flow_as_of,
  f.operating_cash_flow_basis

from {{ ref('stg_company_metadata') }} c
left join {{ ref('mart_latest_financial_health') }} f on c.symbol = f.symbol  --left join in the case of no financials

 
