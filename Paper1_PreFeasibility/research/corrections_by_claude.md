# Claude's checks against the BNBC 2020 gazette text (local copy)

These override `factcheck.md` where the two disagree.

- **Dhaka seismic zone.** BNBC 2020 Table 6.2.14 places Dhaka in Zone 2 with **Z = 0.20**, and Table 6.2.15 also gives Dhaka Z = 0.20. `factcheck.md` says 0.15, which is **wrong**: 0.15 comes from BNBC 1993.
- **Chittagong.** Z = 0.28 (Zone 3). Gazipur 0.20, Narayanganj 0.20.
- **Zones.** 1 = 0.12 (low), 2 = 0.20 (moderate), 3 = 0.28 (severe), 4 = 0.36 (very severe; Sylhet, Mymensingh, Kurigram).
- **BNBC 2020 Part 6, Sec 6.10.5 (structural integrity of precast), verbatim values:**
  - 6.10.5.1.2: diaphragm-to-supported-member connections ≥ 4.4 kN per linear m.
  - 6.10.5.1.3(a): precast columns, nominal tensile strength ≥ 1.4 Ag (N).
  - 6.10.5.1.3(b): precast wall panels, at least two ties per panel, each ≥ 44 kN.
  - 6.10.5.1.4: "Connection details that rely solely on friction caused by gravity loads shall not be used."
  - 6.10.5.2 applies to precast **bearing wall structures three or more storeys** in height:
    - 6.10.5.2.1: longitudinal and transverse floor/roof ties of 22 kN per m, positioned within 600 mm of the floor plane.
    - 6.10.5.2.2: longitudinal ties at ≤ 3 m centres.
    - 6.10.5.2.3: transverse ties at ≤ the bearing-wall spacing.
    - 6.10.5.2.4: perimeter ties within 1.2 m of the edge, ≥ 71 kN.
    - 6.10.5.2.5: vertical ties continuous over the building height, ≥ 44 kN per horizontal m of wall, at least two per panel.
  - These mirror ACI 318 §16.2.4–16.2.5 (1,500 lb/ft and 3,000 lb/ft, converted to SI).
- **BNBC 6.10.6.1.1:** "The adequacy of connections to transfer forces between members shall be determined by analysis or by test." This is the regulatory hook for the certification gap: the code allows either route but sets out no local test protocol or accreditation pathway.
- **BNBC 2020 dates.** Notified as S.R.O. 55-Law/2020; published in the Bangladesh Gazette (Extraordinary) on 11 Feb 2021.
- **Seismic Design Category.** BNBC Table 6.2.19 is cited in the SSRN text as marking ordinary RC shear walls "Not Permitted" in SDC D. Keep this, but cite it as BNBC Table 6.2.19 rather than restating it as a general rule.
