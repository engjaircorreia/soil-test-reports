# AI Extraction Prompt Contract

This document summarizes the contract between uploaded lab-sheet images/PDFs, the AI extraction step and the fields used by the workbook generator.

## Goal

The AI must extract visible raw data from the sheets and return standardized JSON. It must not calculate variables, complete missing data, create compaction points or synthesize penetration readings from final results.

When a value cannot be read confidently, it must return `null`. The system normalizes, calculates, validates and presents pending fields for human review.

## Proctor

Preferred source: Proctor/compaction sheet, usually with a compaction title and moisture determination table.

Raw/read fields:

- `proctor.higroscopica`: hygroscopic moisture block from the Proctor sheet, with capsule, wet gross weight, dry gross weight and capsule tare, when present.
- `proctor.pontos`: visible points from the compaction table, with weights and capsules when legible.
- `proctor.resultado_lido.umidade_otima_percent`: final value read near `h =`, `w =`, optimum moisture or equivalent.
- `proctor.resultado_lido.densidade_maxima_g_cm3`: final value read near maximum dry density, `gamma max`, `Ymax` or equivalent.

The system calculates or checks the curve by algorithm. The AI must not create missing points.

When the Proctor and CBR sheets refer to the same material, the hygroscopic moisture may be reused between them. The AI should extract whatever is visible in each sheet; reconciliation is handled by the system.

Do not use as final Proctor result:

- wet soil density;
- wet gross weight;
- wet soil weight;
- capsule number;
- water weight;
- mold/equipment weight.

## CBR

Preferred source: CBR sheet, titled `CBR`, `I.S.C.` or `California Bearing Ratio`.

Raw/read fields:

- `cbr.resultado_lido.cbr_percent`: final value highlighted in the `I.S.C.` or pressure-penetration chart, when present.
- `cbr.resultado_lido.expansao_percent`: final value in the soaked expansion block, when present.
- `cbr.higroscopica`: `HIGROSCOPICA` column from the moisture table, with capsule, wet gross weight, dry gross weight and capsule tare.
- `cbr.moldagem`: `MOLDAGEM` column from the moisture table, with capsule, wet gross weight, dry gross weight and capsule tare.
- `cbr.calculo_moldagem`: handwritten values from the molding calculation block, such as soil weight, retained/passing #4 sieve weight and water to add.
- `cbr.penetracao`: visible penetration table readings. Do not synthesize them from the final percentage.
- `cbr.expansao`: visible expansion readings.
- `cbr.verificacao_moldagem`: handwritten values from the molding check block, such as wet specimen gross weight, wet specimen weight and densities.

Do not use as CBR:

- the standard pressure column, usually `70`, `105`, `133`, `161`, `182`;
- manometer reading;
- time;
- penetration;
- pressure/load;
- equipment data.

The system calculates water weight, dry soil weight, moisture, moisture difference, water to add and molding check densities. Molding/check values are not invented; if the AI does not extract them, they remain blank for review.

If `cbr.higroscopica` is empty or inconsistent and `proctor.higroscopica` is valid, the system uses the Proctor hygroscopic moisture as fallback for CBR and `DENS`. If both are valid and divergent, the values are preserved for human review.

## Granulometry

Preferred source: sieve analysis sheet.

Raw/read fields:

- `granulometria.peneiras`: visible sieve rows with sieve number, opening, retained weight and/or passing percentage.
- `granulometria.umidade`: capsule and moisture weights, when legible.
- `granulometria.amostra_total`: total sample weights, when legible.

Do not use as passing percentage:

- partial retained weight;
- accumulated passing weight;
- sieve opening;
- sieve number.

## Atterberg Limits

When the material has no limits, use:

- `LL = NL`
- `LP = NP`
- `IP = NP`

## Consistency Checks

Typical expected ranges:

- optimum moisture: `5%` to `20%`;
- maximum dry density: `1.5` to `2.3 g/cm³`;
- CBR: final percentage, not standard load;
- expansion: `0%` to `10%`;
- passing percentages: `0%` to `100%`.

When the AI cannot distinguish a value confidently, it must return `null` and explain it in `warnings`.

Moisture blocks are inconsistent when they violate:

```text
wet gross weight >= dry gross weight >= capsule tare
```
