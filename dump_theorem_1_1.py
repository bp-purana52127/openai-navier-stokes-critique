import os

FILES_TO_DUMP = [
    './NavierStokesAndEuler/NavierStokes/R3/Theorem.lean',
    './NavierStokesAndEuler/NavierStokes/R3ActualCandidate.lean',
    './NavierStokesAndEuler/NavierStokes/ComparatorTheorem.lean',
    './NavierStokesAndEuler/NavierStokes/PeriodicPaperTheorem.lean',
    './NavierStokesAndEuler/NavierStokes/MixedCandidateAssembly.lean',
    './NavierStokesAndEuler/NavierStokes/PaperAdditionalResults.lean'
]

with open('theorem_1_1_dump.txt', 'w', encoding='utf-8') as out:
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

print("[+] Saved to theorem_1_1_dump.txt")