# Calliphoridays PMI Tool Test Results

## Overview
This document presents the results of three validation tests performed on the Calliphoridays forensic entomology tool. Each test uses different species, development stages, and temperature conditions to evaluate the accuracy and consistency of PMI calculations.

## Test Methodology
- All tests use the accumulated degree days (ADD) method
- Manual temperature override (-a flag) to ensure consistent conditions
- Verbose output (-v flag) to show detailed calculations
- Different species and development stages to test various biological parameters

---

## Test Case 1: Lucilia sericata (Green Bottle Fly)

### Input Parameters
- **Species**: Lucilia sericata
- **Development Stage**: 3rd instar
- **Location**: Chicago, IL
- **Discovery Date**: 2024-01-15
- **Ambient Temperature**: 20.0°C (manual override)
- **Specimen Length**: Not provided (uses midpoint)

### Scientific Parameters Used
- **Base Temperature**: 8.0°C
- **Accumulated Degree Days**: 78.0 ADD (midpoint for 3rd instar)
- **Effective Temperature**: 12.0°C (20.0°C - 8.0°C)

### Results
- **Estimated PMI**: 6.5 days (156.0 hours)
- **Confidence Interval**: 5.2 - 7.8 days
- **Data Quality Score**: 100/100 (EXCELLENT)
- **Calculation**: 78.0 ADD ÷ 12.0°C = 6.5 days

### Expected vs Actual
- **Expected Behavior**: Moderate PMI for 3rd instar stage at moderate temperature
- **Actual Result**: ✅ Consistent with expected entomological development patterns
- **Analysis**: The result aligns with typical Lucilia sericata development at 20°C

---

## Test Case 2: Chrysomya rufifacies (Hairy Maggot Blow Fly)

### Input Parameters
- **Species**: Chrysomya rufifacies
- **Development Stage**: 2nd instar
- **Location**: Miami, FL
- **Discovery Date**: 2024-06-01
- **Ambient Temperature**: 25.0°C (manual override)
- **Specimen Length**: Not provided (uses midpoint)

### Scientific Parameters Used
- **Base Temperature**: 10.0°C
- **Accumulated Degree Days**: 35.0 ADD (midpoint for 2nd instar)
- **Effective Temperature**: 15.0°C (25.0°C - 10.0°C)

### Results
- **Estimated PMI**: 2.3 days (56.0 hours)
- **Confidence Interval**: 1.9 - 2.8 days
- **Data Quality Score**: 97/100 (EXCELLENT)
- **Calculation**: 35.0 ADD ÷ 15.0°C = 2.3 days

### Expected vs Actual
- **Expected Behavior**: Shorter PMI due to earlier development stage and higher temperature
- **Actual Result**: ✅ Correctly shows shorter PMI than Test 1
- **Analysis**: Higher temperature and earlier development stage produce expected shorter PMI

---

## Test Case 3: Calliphora vicina (Blue Bottle Fly)

### Input Parameters
- **Species**: Calliphora vicina
- **Development Stage**: Pupa
- **Location**: Seattle, WA
- **Discovery Date**: 2024-03-10
- **Ambient Temperature**: 15.0°C (manual override)
- **Specimen Length**: Not provided (uses midpoint)

### Scientific Parameters Used
- **Base Temperature**: 6.0°C
- **Accumulated Degree Days**: 189.0 ADD (midpoint for pupa stage)
- **Effective Temperature**: 9.0°C (15.0°C - 6.0°C)

### Results
- **Estimated PMI**: 21.0 days (504.0 hours)
- **Confidence Interval**: 16.8 - 25.2 days
- **Data Quality Score**: 92/100 (EXCELLENT)
- **Calculation**: 189.0 ADD ÷ 9.0°C = 21.0 days

### Expected vs Actual
- **Expected Behavior**: Longest PMI due to advanced development stage and lower effective temperature
- **Actual Result**: ✅ Correctly shows longest PMI of all three tests
- **Analysis**: Pupal stage requires most development time, and lower effective temperature extends PMI

---

## Comparative Analysis

### Parameter Differences Summary
| Test | Species | Stage | Temp (°C) | Base Temp (°C) | Effective Temp (°C) | ADD Required | PMI (days) |
|------|---------|-------|-----------|----------------|-------------------|--------------|------------|
| 1 | L. sericata | 3rd instar | 20.0 | 8.0 | 12.0 | 78.0 | 6.5 |
| 2 | C. rufifacies | 2nd instar | 25.0 | 10.0 | 15.0 | 35.0 | 2.3 |
| 3 | C. vicina | Pupa | 15.0 | 6.0 | 9.0 | 189.0 | 21.0 |

### Key Observations

1. **Temperature Effect**: Higher effective temperatures result in shorter PMI estimates
   - Test 2 (15.0°C effective) → 2.3 days
   - Test 1 (12.0°C effective) → 6.5 days  
   - Test 3 (9.0°C effective) → 21.0 days

2. **Development Stage Effect**: Later development stages require more accumulated degree days
   - 2nd instar: 35.0 ADD
   - 3rd instar: 78.0 ADD
   - Pupa: 189.0 ADD

3. **Species Variation**: Different species have varying base temperatures
   - C. vicina: 6.0°C (cold-adapted)
   - L. sericata: 8.0°C (moderate)
   - C. rufifacies: 10.0°C (warm-adapted)

### Validation Results

✅ **All calculations are mathematically correct**
- PMI = ADD ÷ Effective Temperature formula applied consistently

✅ **Biological relationships are accurate**
- Later development stages → longer PMI
- Higher temperatures → shorter PMI
- Species-specific base temperatures applied correctly

✅ **Confidence intervals are reasonable**
- All show appropriate uncertainty ranges (±20-25%)
- Data quality scores reflect calculation reliability

✅ **Tool consistency**
- Identical inputs produce identical outputs across runs
- Verbose mode provides transparent calculation details

## Conclusion

The Calliphoridays tool demonstrates accurate and consistent PMI calculations across different scenarios. The results follow expected entomological principles and provide appropriate confidence intervals. All three test cases validate that the tool correctly implements the accumulated degree days method with species-specific parameters.

**Recommendation**: The tool appears to function as intended for forensic applications, with results that should be interpreted by qualified forensic entomologists as noted in the tool's disclaimer.