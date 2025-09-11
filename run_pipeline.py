"""
Run end-to-end pipeline on example data.
"""

from decoding.peak_decoder import MoccaPeakDecoder
from assignment.assign_compounds import assign_compounds


def main():
    raw_path = "/Users/nathanleung/Documents/Programming/Research Projects/peak_prophet/data_raw/F8.mzML"
    reactants = ["CC(=O)OC(C)=O"]
    solvent = "CCO"

    decoder = MoccaPeakDecoder(
        file_path=raw_path,
        rxn_type="demo",
        reactants=reactants,
        solvents=[solvent],
        wavelength=None,
        method="flatfit",
        time=None,
    )

    result = assign_compounds(
        decoder=decoder,
        mzml_path=raw_path,
        reactants=reactants,
        solvent=solvent,
        weights={"ms": 0.5, "rt": 0.3, "lmax": 0.2},
        mz_tol=0.01,
        ppm=None,
        rt_sigma=0.5,
        lmax_sigma=15.0,
    )

    print("Total score:", result["total_score"])
    print("Num assignments:", len(result["assignments"]))
    for a in result["assignments"]:
        print(a["pred_index"], "->", a["obs_index"], "score=", a["score"])


if __name__ == "__main__":
    main()

