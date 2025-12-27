import csv
import subprocess
import argparse
import os
import sys
import time

def extract_subreddit_from_filename(filename):
    """
    Tries to extract 'StockMarket' from 'users_StockMarket_noapi.csv'
    Assumes format starts with 'users_<Subreddit>_'
    """
    base = os.path.basename(filename)
    parts = base.split('_')
    if len(parts) >= 2:
        return parts[1]
    return None

def main():
    parser = argparse.ArgumentParser(description="Batch execute post fetching for a list of users.")
    parser.add_argument("input_file", help="The CSV file containing users (e.g., users_StockMarket_noapi.csv)")
    parser.add_argument("--script-name", default="post_fetch.py", help="Filename of the fetch script (default: post_fetch.py)")
    parser.add_argument("--post-count", type=int, default=20, help="Posts to fetch per user")
    
    args = parser.parse_args()

    # 1. Validation
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    if not os.path.exists(args.script_name):
        print(f"Error: Python script '{args.script_name}' not found. Did you name it correctly?")
        sys.exit(1)

    # 2. Extract Subreddit
    subreddit = extract_subreddit_from_filename(args.input_file)
    if not subreddit:
        print("Error: Could not detect subreddit from filename. Format must be 'users_<Subreddit>_....csv'")
        sys.exit(1)
    
    print(f"--- Batch Processing Started ---")
    print(f"Target Subreddit: r/{subreddit}")
    print(f"Input File: {args.input_file}")
    
    # 3. Read CSV and Execute
    users_processed = 0
    with open(args.input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        total_rows = len(rows)
        
        print(f"Found {total_rows} users to process.\n")

        for i, row in enumerate(rows):
            username = row['username']
            users_processed += 1
            
            print(f"[{users_processed}/{total_rows}] Launching fetch for user: u/{username}")
            
            # Construct the command:
            # python post_fetch.py --username <user> --post-count <count> --subreddit <subname>
            command = [
                sys.executable,       # Uses the current python (python.exe or python3)
                args.script_name,
                "--username", username,
                "--post-count", str(args.post_count),
                "--subreddit", subreddit
            ]
            
            try:
                # Run the script and wait for it to finish
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError:
                print(f"(!) Error executing script for {username}. Moving to next user...")
            except KeyboardInterrupt:
                print("\nStopping batch process...")
                sys.exit(0)
            
            # Small cooldown between users to keep things safe
            time.sleep(5)

    print(f"\n--- Batch Job Complete: Processed {users_processed} users ---")

if __name__ == "__main__":
    main()