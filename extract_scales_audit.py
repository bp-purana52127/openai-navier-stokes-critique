import os
import re

# 1. Target filenames likely containing the scale definitions and parameter guards
TARGET_FILE_PATTERNS = [
    'Scale',
    'Guard',
    'Frequency',
    'InfiniteConstruction',
    'InitialSmoothLimit',
    'InductionStage',
    'InitialAmplitude',
    'TailBound',
    'FiniteLifespan'
]

# 2. Specific declarations that bridge the paper's Section 5 parameters to Lean
TARGET_DECLARATIONS = [
    'exists_scales',
    'Scales',
    'StageGuards',
    'constructionScales',
    'scaleSequence',
    'predecessorExponent',
    'frequency',
    'truncation',
    'expansion',
    'delta',
    'smallPower',
    'requiredExponent',
    'commonThreshold',
    'actual_increment_summable',
    'primaryAmplitude',
    'tailBase'
]

def extract_scale_definitions(repo_path, output_filename):
    decl_start_re = re.compile(
        r'^\s*(?:private\s+|protected\s+|noncomputable\s+)*(def|abbrev|structure|class|theorem|lemma|axiom|opaque)\s+([a-zA-Z0-9_.\']+)'
    )
    axiom_sorry_re = re.compile(r'\b(sorry|axiom|opaque|admit|Classical\.choice)\b')

    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write("================================================================================\n")
        out.write("OPENAI NAVIER-STOKES / EULER: PARAMETER SCALES & SUMMABILITY AUDIT\n")
        out.write("================================================================================\n\n")

        matched_files = []
        for root, dirs, files in os.walk(repo_path):
            if '.lake' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith('.lean'):
                    filepath = os.path.join(root, file)
                    if any(pat.lower() in file.lower() for pat in TARGET_FILE_PATTERNS):
                        matched_files.append(filepath)

        out.write(f"Targeted Scale/Parameter Files Found ({len(matched_files)}):\n")
        for mf in sorted(matched_files):
            out.write(f"  - {mf}\n")
        out.write("\n" + "="*80 + "\n\n")

        # Pass 1: Scan ALL project .lean files for exact target declarations or axioms/sorrys
        for root, dirs, files in os.walk(repo_path):
            if '.lake' in root or '.git' in root:
                continue

            for file in sorted(files):
                if not file.endswith('.lean'):
                    continue
                filepath = os.path.join(root, file)
                is_target_file = filepath in matched_files

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    continue

                # Check for any axiom/sorry/Classical.choice in the file
                for idx, line in enumerate(lines):
                    m_ax = axiom_sorry_re.search(line)
                    if m_ax:
                        out.write(f"[CHOICE / AXIOM / SORRY FLAG] {filepath} (Line {idx+1}):\n")
                        start_l = max(0, idx - 2)
                        end_l = min(len(lines), idx + 8)
                        out.writelines(lines[start_l:end_l])
                        out.write("-" * 80 + "\n\n")

                # Extract full blocks of matching declarations
                i = 0
                while i < len(lines):
                    line = lines[i]
                    m_decl = decl_start_re.match(line)
                    if m_decl:
                        decl_kind, decl_name = m_decl.group(1), m_decl.group(2)
                        short_name = decl_name.split('.')[-1]

                        # Capture if it's in our target declaration list OR if it's a structure/def in a target scale file
                        should_capture = (
                            short_name in TARGET_DECLARATIONS or
                            any(td in line for td in TARGET_DECLARATIONS) or
                            (is_target_file and decl_kind in ['def', 'abbrev', 'structure', 'class'])
                        )

                        if should_capture:
                            block = [line]
                            j = i + 1
                            # Read until the next top-level declaration or end of namespace/section (up to 60 lines)
                            while j < len(lines) and (j - i) < 60:
                                if decl_start_re.match(lines[j]) or lines[j].startswith('end ') or lines[j].startswith('namespace '):
                                    break
                                block.append(lines[j])
                                j += 1

                            out.write(f"File: {filepath} (Line {i+1})\n")
                            out.write(f"Declaration: {decl_kind} {decl_name}\n")
                            out.write("-" * 80 + "\n")
                            out.writelines(block)
                            out.write("\n" + "=" * 80 + "\n\n")
                            i = j
                            continue
                    i += 1

if __name__ == "__main__":
    output_file = "scales_and_summability_trace.txt"
    extract_scale_definitions('./NavierStokesAndEuler', output_file)
    print(f"[+] Extraction complete. Upload or inspect '{output_file}'.")