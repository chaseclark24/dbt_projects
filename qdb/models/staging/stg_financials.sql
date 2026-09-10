  select
      symbol,
      fiscal_year,
      cast(period_end as date) as period_end,
      total_revenue,
      total_revenue_prev,
      net_income,
      total_cash,
      total_debt,
      operating_cash_flow,
      going_concern,
      cast(updated_at as timestamp) as updated_at,
    cast(cash_as_of as date) as cash_as_of,
    cast(operating_cash_flow_as_of as date) as operating_cash_flow_as_of,
    operating_cash_flow_basis
  from {{ source('qdb_source', 'financials') }}