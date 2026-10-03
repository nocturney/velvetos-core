# Calibration discipline

For OrcaSlicer, follow the current official calibration workflow rather than old community orderings. The current 2026 guide recommends: temperature -> max volumetric speed -> pressure advance -> flow -> retraction. Treat that as Orca-specific sequencing, not a universal law for every firmware/slicer.

- Calibrate against the exact printer/nozzle/material/profile context that will be used.
- Save accepted results into an explicit material/profile record rather than memory.
- Revisit calibration after meaningful hardware, nozzle, extruder, material or firmware changes.
- Max volumetric speed is material/machine/nozzle/extruder dependent; even filament color can affect it.
- Pressure advance/linear advance capability depends on firmware and extrusion architecture.
- Use tolerance/fit coupons when dimensional mating behavior matters.
- Keep failed/previous calibration results identifiable so regression is detectable.