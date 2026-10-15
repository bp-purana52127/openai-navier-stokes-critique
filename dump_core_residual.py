import os

FILES_TO_DUMP = [
    './NavierStokesAndEuler/NavierStokes/GluedStageEstimates.lean',
    './NavierStokesAndEuler/NavierStokes/WholeDomainPrefixBounds.lean',
    './NavierStokesAndEuler/NavierStokes/ActualCycleResidualBounds.lean',
    './NavierStokesAndEuler/NavierStokes/PeriodicResidualLimits.lean',
    './NavierStokesAndEuler/NavierStokes/MixedAxisPreservation.lean',
    './NavierStokesAndEuler/NavierStokes/ActualIterationLedger.lean'
]

with open('core_residual_dump.txt', 'w', encoding='utf-8') as out:
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

print("[+] Saved to core_residual_dump.txt")