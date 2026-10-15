import os
import re

def extract_ns_root_and_theorems(repo_path, output_filename):
    decl_re = re.compile(
        r'^\s*(?:private\s+|protected\s+|noncomputable\s+)*(def|abbrev|structure|class|theorem|lemma|axiom|opaque)\s+([a-zA-Z0-9_.\']+)'
    )
    import_re = re.compile(r'^\s*import\s+([a-zA-Z0-9_.]+)')
    
    # Keywords that indicate final/top-level Navier-Stokes or Comparator theorems
    top_keywords = [
        'NavierStokes', 'Existence', 'Smoothness', 'Breakdown', 'Singularity',
        'Lifespan', 'Blowup', 'ForceCondition', 'InitialVelocity', 'Comparator',
        'main', 'final', 'submission', 'clay', 'millennium', 'viscous', 'forcing'
    ]
    
    all_lean_files = {}
    imported_modules = set()

    # Pass 1: Collect all .lean files and track which modules are imported by others
    for root, dirs, files in os.walk(repo_path):
        if '.lake' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.lean'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, repo_path)
                mod_name = rel_path[:-5].replace(os.sep, '.')
                all_lean_files[mod_name] = filepath
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            m = import_re.match(line)
                            if m:
                                imported_modules.add(m.group(1))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    # Leaf modules are files that NO other file imports (i.e., top-level entry points!)
    leaf_modules = sorted(set(all_lean_files.keys()) - imported_modules)

    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write("=" * 80 + "\n")
        out.write("OPENAI NAVIER-STOKES & EULER: TOP-LEVEL ENTRY POINTS & FINAL THEOREMS\n")
        out.write("=" * 80 + "\n\n")

        out.write(f"1. IDENTIFIED LEAF / ROOT MODULES (Not imported by any other file) [{len(leaf_modules)}]:\n")
        for mod in leaf_modules:
            out.write(f"   * {mod} -> {all_lean_files[mod]}\n")
        out.write("\n" + "=" * 80 + "\n\n")

        # Pass 2: Dump the FULL contents of all Leaf/Root modules (up to 300 lines each)
        out.write("2. FULL DUMP OF LEAF / ROOT ENTRY-POINT FILES:\n")
        out.write("=" * 80 + "\n\n")
        for mod in leaf_modules:
            filepath = all_lean_files[mod]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                out.write(f"FILE: {filepath} (Total Lines: {len(lines)})\n")
                out.write("-" * 80 + "\n")
                if len(lines) <= 350:
                    out.writelines(lines)
                else:
                    out.write("--- [First 100 lines] ---\n")
                    out.writelines(lines[:100])
                    out.write("\n--- [Last 200 lines] ---\n")
                    out.writelines(lines[-200:])
                out.write("\n" + "=" * 80 + "\n\n")
            except Exception as e:
                print(f"Error dumping {filepath}: {e}")

        # Pass 3: Search all files in NavierStokes/ for top-level keywords & final theorems
        out.write("3. TARGETED THEOREMS & DEFINITIONS IN ./NavierStokes/:\n")
        out.write("=" * 80 + "\n\n")
        for mod, filepath in sorted(all_lean_files.items()):
            if not ('NavierStokes' in filepath and 'ComparatorChallenges' not in filepath):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception:
                continue

            i = 0
            while i < len(lines):
                line = lines[i]
                m_decl = decl_re.match(line)
                if m_decl:
                    decl_kind, decl_name = m_decl.group(1), m_decl.group(2)
                    if any(kw.lower() in line.lower() for kw in top_keywords):
                        block = [line]
                        j = i + 1
                        while j < len(lines) and (j - i) < 50:
                            if decl_re.match(lines[j]) or lines[j].startswith('end '):
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
    output_file = "ns_toplevel_trace.txt"
    extract_ns_root_and_theorems('./NavierStokesAndEuler', output_file)
    print(f"[+] Extraction complete. Upload or inspect '{output_file}'.")