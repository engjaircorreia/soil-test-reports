# Cell Map

This map separates user-entered cells from automatic calculation cells.

The templates were not recolored in this step to avoid rewriting the entire workbook with `openpyxl`, which can remove drawing elements. The distinction is documented here instead.

## Data Sources

User-entered data in the interface:

- General identification: interested party, testing company, project, city, origin/street, location/borehole/station, date, record number and notes.
- Sample identification: layer, side and depth.
- Team: responsible engineer, operator, lab technician and laboratory.
- Configuration: template language, test type and Proctor energy.

Data extracted from PDFs/images and reviewed by the user:

- Proctor: moisture values, capsule weights, compaction curve points, optimum moisture and maximum dry density.
- CBR: molding moisture, expansion readings, penetration readings, final expansion and CBR.
- Granulometry: hygroscopic moisture, sample weights, sieves, passing percentages and classifications.
- Limits: LL, PL and PI. When the material has no limits, use `NL`, `NP` and `NP`.

The generator only replaces administrative data in cells already present in each template. Fields that do not exist in a sheet are not forced into the workbook.

## Proctor / CBR

File: `templates/compactacao_cbr_modelo_limpo.xlsx`

### Sheet `DENS`

User/extracted inputs:

- Identification: `B4` interested party, `F4` project, `K4` Proctor, `M4` record, `B5` location/station, `K6` depth, `M6` date, `B8` origin, `F8` city, `J8` responsible engineer
- Hygroscopic moisture: `G10:G14`
- Compaction points: `C23:D27`, `F23:F27`, `I23:K27`
- Cells without formulas, when needed: `G25:H27`, `L25:N27`

Preserved automatic calculations:

- Moisture and averages: `G15:G17`
- Wet/dry densities for points when formulas exist: `E23:E27`, `L23:N24`
- Main results: `M46`, `M53`
- Auxiliary sheet `Calc`, used by the compaction curve

### Sheet `CBR`

User/extracted inputs:

- Main identification inherited from `DENS`, with `O4` receiving the CBR record
- Capsules and moisture blocks: `O11:P18`
- Optimum moisture when not linked by formula: `F21`
- Penetration data: `F27:G32`, `J29:J32`
- Expansion readings: `N27`, `N29`, `N31`, `N33`
- Molding/check values: `P36`, `P38`, `P40`, `P42`, `P45`, `P47`

Preserved automatic calculations:

- Data imported from `DENS`
- Water to add: `M21:M22`, `O21:O23`, `J23`
- Final CBR and expansion: `F34`, `J34`
- Automatic checks: `P49`, `P51`, `P56`, `P58`, `P62`

## Granulometry

File: `templates/granulometria_modelo_limpo.xlsx`

### Sheet `GRANULOMEDIA `

User/extracted inputs:

- Moisture: `D3:D9`, `D11`
- Total/partial sample: `I3:I9`, `J9`, `K5`, `K9`, `L9`
- Sieving: `D19:F23`, `E19:E23`
- Identification: `A27` project, `D27` origin, `H27` testing company, `B29` layer, `G29` location/station, `J29` side, `L29` depth, `A31` laboratory, `C31` operator, `E31` date, `G31` lab technician, `L31` record

Automatic/documented results:

- TRB/SUCS classification: `M20`, `M21`
- Group index: `M22`
- Auxiliary constants: `M15`, `M18`

### Sheet `LIQUIDEZ`

User/extracted inputs:

- Atterberg limits test data, when applicable
- Identification: `A22` project, `C22` origin, `K22` testing company, `A24` layer, `H24` location/station, `K24` side, `L24` depth, `A26` laboratory, `B26` operator, `F26` date, `J26` lab technician, `L26` record

Results:

- Liquid limit: `M9`
- Plastic limit: `M12`
- Plasticity index: `M14`
