import os

FILES_TO_DUMP = [
    './NavierStokesAndEuler/NavierStokes/ActualCandidateAssembly.lean',
    './NavierStokesAndEuler/NavierStokes/R3/ActualCandidate.lean',
    './NavierStokesAndEuler/NavierStokes/MixedPeriodicAssembly.lean',
    './NavierStokesAndEuler/NavierStokes/MixedDiagonalResidual.lean',
    './NavierStokesAndEuler/NavierStokes/WholeDomainPhysicalStageTheorem.lean'
]

with open('actual_candidate_dump.txt', 'w', encoding='utf-8') as out:
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

print("[+] Saved to actual_candidate_dump.txt")