# Formula and model QA

1. Check for hardcoded numbers inside formulas that should be named inputs.
2. Check units on both sides of each major calculation.
3. Check missing/blank/error values and make them visible rather than silently coercing to zero.
4. Check duplicates and double counting across BOM levels.
5. Reconcile component rollups to assembly/grand totals through an independent sum/check where practical.
6. Test at least one simple known case and one quantity change to expose broken absolute/relative references.
7. Flag circular references and volatile/manual overrides.
8. Keep rounding at presentation boundaries unless business rules require line-level rounding.