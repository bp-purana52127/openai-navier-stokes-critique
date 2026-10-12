import os
import re

REPO_PATH = './NavierStokesAndEuler'
OUTPUT_FILE = 'audit_results.txt'

TARGET_DEFS = {
    'velocity_evolution': 'MeanVelocityPressure.lean',
    'momentumForcing': 'TransverseMomentumRegularity.lean',
    'forcing_bound': 'ContinuousAccelerationForcing.lean'
}

def analyze_lean_definition(filepath, def_name):
    """Extract a Lean definition block and analyze its type signature."""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    pattern = re.compile(r'(?:noncomputable\s+)?(?:def|theorem|lemma)\s+' + re.escape(def_name) + r'[\s\S]*?:=')
    match = pattern.search(content)
    
    if not match:
        return None
    
    block = match.group(0)
    
    has_bochner = any(k in block for k in ['TimeLp', 'L2', 'Bochner'])
    has_smooth = ('ContDiff' in block) or ('C^∞' in block)
    has_frame = any(k in block for k in ['timeMultiplier', 'extendPath', 'adjoint'])
    
    return {
        'block': block,
        'has_bochner': has_bochner,
        'has_smooth': has_smooth,
        'has_frame': has_frame
    }

def run_audit():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        def log(text=""):
            print(text)
            out.write(text + "\n")

        log("=" * 70)
        log("OPENAI NAVIER-STOKES LEAN 4 TYPE-MISMATCH AUDIT")
        log("=" * 70 + "\n")
        
        mismatches_found = 0

        if not os.path.exists(REPO_PATH):
            log(f"Error: Repository directory '{REPO_PATH}' not found.")
            log("Please ensure you are running this script in the directory containing 'NavierStokesAndEuler'.")
            return

        for root, dirs, files in os.walk(REPO_PATH):
            for def_name, target_file in TARGET_DEFS.items():
                if target_file in files:
                    filepath = os.path.join(root, target_file)
                    res = analyze_lean_definition(filepath, def_name)
                    
                    if res:
                        log(f"[MATCH] Definition '{def_name}' found in {target_file}")
                        log("-" * 50)
                        log(res['block'][:300] + "...\n")
                        log("Type Inspection Analysis:")
                        log(f"  - Uses Weak Bochner Space (TimeLp/L2): {res['has_bochner']}")
                        log(f"  - Uses Classical Smoothness (ContDiff): {res['has_smooth']}")
                        log(f"  - Uses Frame Transformation Matrix Q(t): {res['has_frame']}")
                        
                        if res['has_bochner'] and not res['has_smooth']:
                            log("  => SPECIFICATION DRIFT CONFIRMED: Operates on weak Lp space, not C^∞ Eulerian space.")
                            mismatches_found += 1
                        log("\n" + "=" * 70 + "\n")

        log(f"Audit Complete. Total Specification Mismatches Isolated: {mismatches_found}")
        log(f"\n[+] Audit log successfully saved to '{OUTPUT_FILE}'")

if __name__ == '__main__':
    run_audit()