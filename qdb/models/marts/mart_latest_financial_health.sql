  with ranked_financials as (

      select
          *,
          row_number() over (
              partition by symbol
              order by period_end desc, updated_at desc
          ) as row_rank
      from {{ ref('stg_financials') }}

  ),

  latest_financials as (

      select *
      from ranked_financials
      where row_rank = 1

  )

  select
    symbol,
    fiscal_year,
    period_end,
    total_revenue,
    total_revenue_prev,
    round(
        100.0 * (total_revenue - total_revenue_prev)
        / nullif(total_revenue_prev, 0),
        2
    ) as revenue_growth_pct,
    net_income,
    total_cash,
    total_debt,
    operating_cash_flow,
    round(
        100.0 * net_income / nullif(total_revenue, 0),
        2
    ) as net_margin_pct,
    total_cash - total_debt as net_cash,
    case
        when operating_cash_flow is null then null
        when operating_cash_flow < 0 then 1
        else 0
    end as has_negative_cash_flow,
    going_concern,
    cash_as_of,
    operating_cash_flow_as_of,
    operating_cash_flow_basis,
    updated_at as source_updated_at
  from latest_financials