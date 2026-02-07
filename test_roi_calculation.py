"""
Quick Test Script: Business Impact ROI Calculation Verification
Run this to verify the calculations match Grade A expectations
"""

from app.business_impact_service import BusinessImpactService

# Test inputs from grading rubric
test_inputs = {
    'requests_per_year': 1000,
    'employees': 3,
    'manual_time_mins': 60,  # 1 hour
    'avg_value': 400
}

# Expected results for Grade A
expected = {
    'potential_savings': 18300,
    'revenue_upside': 1500,
    'currency': '$'
}

# Run calculation
result = BusinessImpactService.calculate_roi_simulation(
    requests_per_year=test_inputs['requests_per_year'],
    employees=test_inputs['employees'],
    manual_time_mins=test_inputs['manual_time_mins'],
    avg_value=test_inputs['avg_value']
)

# Display results
print("=" * 60)
print("BUSINESS IMPACT ROI CALCULATION TEST")
print("=" * 60)
print("\nTest Inputs:")
print(f"  Annual Requests: {test_inputs['requests_per_year']:,}")
print(f"  Team Size: {test_inputs['employees']} employees")
print(f"  Manual Time: {test_inputs['manual_time_mins']} minutes per quote")
print(f"  Avg Quote Value: ${test_inputs['avg_value']}")

print("\n" + "-" * 60)
print("RESULTS:")
print("-" * 60)

print(f"\n💰 Potential Savings: {result['currency']}{result['potential_savings']:,.2f}")
print(f"   Expected: ${expected['potential_savings']:,}")
print(f"   Match: {'✅ PASS' if abs(result['potential_savings'] - expected['potential_savings']) < 100 else '❌ FAIL'}")

print(f"\n📈 Revenue Upside: {result['currency']}{result['revenue_upside']:,.2f}")
print(f"   Expected: ${expected['revenue_upside']:,}")
print(f"   Match: {'✅ PASS' if abs(result['revenue_upside'] - expected['revenue_upside']) < 100 else '❌ FAIL'}")

print(f"\n⏱️  Hours Saved Annually: {result['hours_saved_annually']:,.1f} hours")
print(f"💼 Pipeline Value: {result['currency']}{result['pipeline_value']:,.2f}")

print("\n" + "=" * 60)
print("CALCULATION BREAKDOWN:")
print("=" * 60)

time_saved_per_quote = test_inputs['manual_time_mins'] - 2  # 2 min tool time
total_hours_saved = (test_inputs['requests_per_year'] * time_saved_per_quote) / 60
hourly_rate = 18.93

print(f"\n1. Time Savings:")
print(f"   Manual time: {test_inputs['manual_time_mins']} min")
print(f"   Tool time: 2 min")
print(f"   Saved per quote: {time_saved_per_quote} min")
print(f"   Total hours saved: {total_hours_saved:,.2f} hours")

print(f"\n2. Potential Savings:")
print(f"   Hours saved: {total_hours_saved:,.2f}")
print(f"   × Hourly rate: ${hourly_rate}")
print(f"   = ${total_hours_saved * hourly_rate:,.2f}")

pipeline = test_inputs['requests_per_year'] * test_inputs['avg_value']
print(f"\n3. Revenue Upside:")
print(f"   Pipeline value: {test_inputs['requests_per_year']:,} × ${test_inputs['avg_value']} = ${pipeline:,}")
print(f"   × Velocity lift: 0.375%")
print(f"   = ${pipeline * 0.00375:,.2f}")

print("\n" + "=" * 60)

# Grade assessment
savings_match = abs(result['potential_savings'] - expected['potential_savings']) < 100
upside_match = abs(result['revenue_upside'] - expected['revenue_upside']) < 100
currency_match = result['currency'] == expected['currency']

if savings_match and upside_match and currency_match:
    print("GRADE: A ✅")
    print("All calculations match Grade A benchmarks!")
else:
    print("GRADE: Below A ❌")
    print("Calculations do not match expected values.")

print("=" * 60)
