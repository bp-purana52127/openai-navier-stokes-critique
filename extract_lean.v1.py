import os
import re

def extract_lean_parameters(repo_path, output_filename):
    # Regex to find Lean definitions related to the physical setup
    keywords = ['force', 'forcing', 'initial', 'velocity', 'energy']
    pattern = re.compile(r'^\s*(def|structure|noncomputable def|theorem|lemma)\s+.*(' + '|'.join(keywords) + r')', re.IGNORECASE)
    
    # Number of lines to pull after finding a match to capture the full block
    lines_to_capture = 15 
    
    with open(output_filename, 'w', encoding='utf-8') as out:
        out.write("OpenAI Lean Code Extraction: Physical Parameters\n")
        out.write("="*60 + "\n\n")
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.lean'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for i, line in enumerate(lines):
                            if pattern.search(line):
                                out.write(f"Location: {filepath} (Line {i+1})\n")
                                out.write("-" * 40 + "\n")
                                # Extract the definition block
                                block = lines[i : min(i + lines_to_capture, len(lines))]
                                out.writelines(block)
                                out.write("\n" + "="*60 + "\n\n")
                    except Exception as e:
                        print(f"Could not read {filepath}: {e}")

if __name__ == "__main__":
    # Point this to the directory where you cloned the repository
    repo_directory = './NavierStokesAndEuler'
    output_txt = 'openai_extracted_parameters.txt'
    
    if os.path.exists(repo_directory):
        extract_lean_parameters(repo_directory, output_txt)
        print(f"Extraction complete. Open '{output_txt}' to view the definitions.")
    else:
        print(f"Error: Directory '{repo_directory}' not found. Run this script in the parent folder.")