import os

FILES_TO_DUMP = [
    './NavierStokesAndEuler/NavierStokes/ComparatorSolution.lean',
    './NavierStokesAndEuler/NavierStokes/PaperResults.lean',
    './NavierStokesAndEuler/NavierStokes/ComparatorR3Theorem.lean',
    './NavierStokesAndEuler/NavierStokes/ProblemStatement.lean',
    './NavierStokesAndEuler/NavierStokes/ActualCandidateConstruction.lean',
    './NavierStokesAndEuler/Euler/EulerSingularity.lean'
]

with open('final_four_dump.txt', 'w', encoding='utf-8') as out:
    for fpath in FILES_TO_DUMP:
        out.write("=" * 80 + "\n")
        out.write(f"FILE: {fpath}\n")
        out.write("=" * 80 + "\n")
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                out.write(f.read())
        else:
            out.write("[FILE NOT FOUND]\n")
        out.write("\n\n")

print("[+] Saved to final_four_dump.txt")