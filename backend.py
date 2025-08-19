import os
import subprocess
from pathlib import Path
import shutil
import pandas as pd

def translate_fna_to_faa(fna_dir, faa_dir):
    fna_dir = Path(fna_dir)
    faa_dir = Path(faa_dir)
    faa_dir.mkdir(parents=True, exist_ok=True)
    
    fna_files = list(fna_dir.glob("*.fna"))
    if not fna_files:
        print("No FNA files found in directory")
        return
    
    for fna_file in fna_files:
        faa_out = faa_dir / f"{fna_file.stem}.faa"

        try:
            subprocess.run([
                "prodigal", 
                "-i", str(fna_file), 
                "-a", str(faa_out), 
                "-p", "meta", "-q"
            ], check=True, capture_output=True, text=True)
            
            print(f"Translated {fna_file.name} to {faa_out.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"[!] Error translating {fna_file}: {e}")
            print(f"stderr: {e.stderr}")
            continue
        except FileNotFoundError:
            print("[!] Prodigal not found. Please ensure it's installed and in PATH")
            return

    print("Translation of FNA to FAA completed.")

def run_hmmer_search(faa_dir, hmmer_dir, pfam_db):
    faa_dir = Path(faa_dir)
    hmmer_dir = Path(hmmer_dir)
    pfam_db = Path(pfam_db)
    
    hmmer_dir.mkdir(parents=True, exist_ok=True)
    
    if not pfam_db.exists():
        raise FileNotFoundError(f"PFAM database {pfam_db} does not exist.")
    
    faa_files = list(faa_dir.glob("*.faa"))
    if not faa_files:
        print("No FAA files found for HMMER search")
        return
    
    for faa_file in faa_files:
        if not faa_file.exists():
            print(f"[!] Skipping missing file {faa_file}")
            continue
        if faa_file.stat().st_size == 0:
            print(f"[!] Skipping empty file {faa_file}")
            continue

        out_txt = hmmer_dir / f"{faa_file.stem}.hmmscan.tbl"

        try:
            result = subprocess.run([
                "hmmscan",
                "--tblout", str(out_txt),
                str(pfam_db),
                str(faa_file)
            ], 
            check=True, 
            capture_output=True, 
            text=True
            )
            
            print(f"Ran HMMER search for {faa_file.name}, results saved to {out_txt.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"[!] Error running HMMER for {faa_file}: {e}")
            print(f"stderr: {e.stderr}")
            continue
        except FileNotFoundError as e:
            print(f"[!] HMMER not found. Please ensure hmmscan is installed and in PATH: {e}")
            continue

    print("HMMER searches completed.")

def read_results(hmmer_dir):
    hmmer_dir = Path(hmmer_dir)
    results = []

    tbl_files = list(hmmer_dir.glob("*.tbl"))
    if not tbl_files:
        print("No HMMER result files found")
        return None

    for out_file in tbl_files:
        try:
            with open(out_file, 'r') as f:
                for line in f:
                    if line.startswith("#"): 
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 18:
                        # Extract strain name from filename (assumes format: strain_xxx.hmmscan.tbl)
                        strain = out_file.stem.replace('.hmmscan', '')
                        pfam_id = parts[1].split(".")[0] if "." in parts[1] else parts[1]
                        
                        results.append({
                            "Strain": strain,
                            "Pfam": pfam_id,
                            "E-value": float(parts[4]),
                            "Score": float(parts[5]),
                            "Target": parts[2]
                        })
        except Exception as e:
            print(f"Error processing {out_file}: {e}")
            continue
    
    if len(results) > 0:
        df = pd.DataFrame(results)
        output_file = "hmmer_results.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Results saved to {output_file}")
        return df
    else:
        print("No valid results found")
        return None

def count_pfam_hits(tbl_file):
    tbl_file = Path(tbl_file)
    
    if not tbl_file.exists():
        print(f"File {tbl_file} does not exist")
        return None
    
    try:
        with open(tbl_file, 'r') as f:
            lines = [line.strip() for line in f if not line.startswith("#") and line.strip()]
        
        pfam_ids = []
        for line in lines:
            parts = line.split()
            if len(parts) > 1:
                pfam_id = parts[1].split(".")[0] if "." in parts[1] else parts[1]
                pfam_ids.append(pfam_id)
        
        if pfam_ids:
            counts = pd.Series(pfam_ids).value_counts().reset_index()
            counts.columns = ['Pfam', 'Count']
            
            output_file = "pfam_counts.xlsx"
            counts.to_excel(output_file, index=False)
            print(f"PFAM counts saved to {output_file}")
            return counts
        else:
            print("No PFAM hits found")
            return None
            
    except Exception as e:
        print(f"Error counting PFAM hits: {e}")
        return None