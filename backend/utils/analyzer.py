# backend/utils/analyzer.py
def analyze_portfolio(portfolio_data: list):
    total_invested = 0
    total_current = 0
    asset_type_summary = {}

    for item in portfolio_data:
        invested = float(item['Invested_Amount'])
        current = float(item['Current_Value'])
        asset_type = item['Type']

        total_invested += invested
        total_current += current

        # ROI per asset
        item['ROI (%)'] = round(((current - invested) / invested) * 100, 2)

        # Summarize asset type totals
        if asset_type not in asset_type_summary:
            asset_type_summary[asset_type] = 0
        asset_type_summary[asset_type] += current

    # Calculate asset type diversification %
    diversification = []
    for asset_type, value in asset_type_summary.items():
        diversification.append({
            "Asset_Type": asset_type,
            "Value": value,
            "Percentage": round((value / total_current) * 100, 2)
        })
    print (total_current, total_invested, diversification)
    return {
        "Total_Invested": total_invested,
        "Total_Current": total_current,
        "Total_Profit_Loss": total_current - total_invested,
        "Portfolio_ROI (%)": round(((total_current - total_invested) / total_invested) * 100, 2),
        "Asset_Diversification": diversification,
        "Detailed_Assets": portfolio_data
    }
