def compute_stats(l1_json: dict, ctx_json: dict) -> dict:
    """
    Computes analytics natively in Python from the Level 1 and Context JSONs.
    Handles missing values gracefully.
    """
    stats = {}
    
    current_units = l1_json.get("units_consumed")
    history = ctx_json.get("usage_history") or []
    
    # 1. Parse history units safely
    history_units = []
    for h in history:
        u = h.get("units")
        if isinstance(u, (int, float)):
            history_units.append(u)
            
    # Combine history with current month (if current month is not already in history)
    # For statistical counts, we include current_units if available
    all_units = list(history_units)
    if isinstance(current_units, (int, float)):
        all_units.append(current_units)
        
    # 2. Average, min, max
    stats["average_monthly_units"] = sum(all_units) / len(all_units) if all_units else None
    stats["min_monthly_units"] = min(all_units) if all_units else None
    stats["max_monthly_units"] = max(all_units) if all_units else None
    
    # 3. Counts above thresholds
    def get_counts(u_list):
        return {
            ">100": sum(1 for x in u_list if x > 100),
            ">200": sum(1 for x in u_list if x > 200),
            ">300": sum(1 for x in u_list if x > 300)
        }
        
    stats["months_above_thresholds_with_current"] = get_counts(all_units)
    stats["months_above_thresholds_without_current"] = get_counts(history_units)
    
    # 4. Tax share of current bill
    cb = l1_json.get("current_bill")
    tt = l1_json.get("total_taxes")
    if isinstance(cb, (int, float)) and isinstance(tt, (int, float)) and cb != 0:
        stats["tax_share_of_current_bill"] = tt / cb
    else:
        stats["tax_share_of_current_bill"] = None
        
    # 5. Cost per unit
    if isinstance(cb, (int, float)) and isinstance(current_units, (int, float)) and current_units != 0:
        stats["cost_per_unit"] = cb / current_units
    else:
        stats["cost_per_unit"] = None
        
    # 6. Change vs previous month
    stats["unit_change_vs_prev_month"] = None
    current_month = l1_json.get("bill_month")
    if current_month and isinstance(current_units, (int, float)) and history:
        # Find the latest month strictly before current_month
        valid_hist = [h for h in history if h.get("month") and isinstance(h.get("units"), (int, float))]
        valid_hist.sort(key=lambda x: str(x["month"]))
        
        prev_units = None
        for h in reversed(valid_hist):
            if str(h["month"]) < str(current_month):
                prev_units = h["units"]
                break
                
        if prev_units is not None:
            stats["unit_change_vs_prev_month"] = current_units - prev_units

    # 7. Totals by charge type
    charges = l1_json.get("charges") or []
    charge_totals = {}
    for c in charges:
        ctype = str(c.get("type", "other"))
        amt = c.get("amount")
        if isinstance(amt, (int, float)):
            charge_totals[ctype] = charge_totals.get(ctype, 0.0) + amt
    stats["totals_by_charge_type"] = charge_totals
    
    return stats
