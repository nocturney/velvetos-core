---
name: vf-bom-costing
description: Build and audit engineering BOM and cost models in Excel or compatible tabular workflows. Use for assemblies, part quantities, units, make/buy status, material/process/supplier costs, extended-cost rollups, labor or overhead assumptions, scenario/variance analysis and spreadsheet formula QA. Preserve source prices, currencies, revisions and assumptions; never invent missing prices, rates, exchange rates, quantities or supplier facts. This skill adds BOM/costing craft and validation rather than replacing the source engineering model, accounting authority or existing spreadsheet tooling.
---

# Velvet BOM and Costing

Treat a BOM/cost workbook as a traceable model: source fields, assumptions, formulas and outputs must remain distinguishable. For Velvet Factory, verified material-cost calculations and canonical financial amounts remain under `vfcost`/the existing books authority; this skill may consume those values but never replaces their authority or turns a modeled cost into an approved sale price.

## Workflow

1. Resolve BOM purpose, assembly/revision, quantity basis, units, currencies and authoritative source data.
2. Read references/bom-structure.md to define rows/levels and part identity.
3. Read references/costing.md for cost rollups, scrap/yield, labor/overhead and scenarios.
4. Read references/formula-audit.md before trusting totals or exported summaries.
5. Read references/change-control.md when updating an existing model/revision.
6. Read references/tool-routing.md only for the spreadsheet environment being used.
7. Recalculate and inspect totals, error cells and representative source-to-rollup traces.

## Core rules

- Keep item identity/revision separate from description and row number.
- Keep quantity-per, assembly quantity and extended quantity distinct.
- Keep unit cost, currency, source/date and conversion assumptions visible.
- Separate material, purchased part, process, labor, shipping and overhead components when the decision needs that detail.
- Use explicit scenario/assumption cells rather than burying constants inside formulas.
- Preserve raw/source data separately from derived outputs.

## Hard stops

- Do not invent missing prices, supplier quotes, labor rates, exchange rates or demand quantities.
- Do not silently mix currencies, unit systems or tax/VAT treatment.
- Do not treat a spreadsheet cost estimate as an accounting invoice or committed supplier quote.
- Do not overwrite source values with scenario values.
- Do not publish or send commercial commitments from this skill.

## Completion evidence

Report source_bom_resolved, units_currencies_checked, formula_coverage_checked, rollups_reconciled, assumptions_visible, error_cells_clear and cost_basis_current separately.
