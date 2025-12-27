import requests
import time
import argparse
import csv
from datetime import datetime

# --- CONFIGURATION ---
# You MUST set a unique User-Agent, or Reddit will block you immediately.
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_account_age_days(created_utc):
    return (time.time() - created_utc) / 86400

def get_user_details(username):
    """Fetches user profile data from the public JSON endpoint."""
    url = f"https://www.reddit.com/user/{username}/about.json"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json().get('data')
            return data
        elif response.status_code == 429:
            print("(!) Too many requests. Sleeping for 10 seconds...")
            time.sleep(10)
            return get_user_details(username) # Retry
    except Exception:
        pass
    return None

def fetch_qualified_users_no_api(subreddit, target_count, min_karma, min_age_days):
    qualified_users = []
    seen_users = set()
    after_token = None # Used for pagination
    
    print(f"--- Scanning r/{subreddit} (No API Mode) ---")

    while len(qualified_users) < target_count:
        # Fetch the latest posts from the subreddit
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
        if after_token:
            url += f"&after={after_token}"
            
        try:
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code != 200:
                print(f"Error fetching subreddit: {resp.status_code}")
                break
                
            data = resp.json()
            posts = data['data']['children']
            after_token = data['data']['after']
            
            if not posts:
                print("No more posts found.")
                break

            for post in posts:
                if len(qualified_users) >= target_count:
                    break
                    
                author_name = post['data']['author']
                
                # Skip [deleted] users or duplicates
                if author_name == '[deleted]' or author_name in seen_users:
                    continue
                    
                seen_users.add(author_name)
                
                # We must sleep slightly between user checks to avoid IP ban
                time.sleep(1.5) 
                
                user_data = get_user_details(author_name)
                
                if user_data:
                    # 1. Karma Check
                    total_karma = user_data.get('total_karma', 0) # total_karma is sum of link + comment
                    
                    # 2. Age Check
                    created_utc = user_data.get('created_utc', time.time())
                    account_age = get_account_age_days(created_utc)

                    if total_karma >= min_karma and account_age >= min_age_days:
                        print(f"[+] Found: {author_name} (Karma: {total_karma}, Age: {int(account_age)}d)")
                        qualified_users.append({
                            'username': author_name,
                            'total_karma': total_karma,
                            'account_age_days': round(account_age, 1),
                            'is_mod': user_data.get('is_mod', False),
                            'verified': user_data.get('has_verified_email', False)
                        })
                    else:
                        # Optional: Print rejected users just to see progress
                        # print(f"[-] Rejected: {author_name} (Low Karma/New)")
                        pass

        except Exception as e:
            print(f"Error: {e}")
            break

    return qualified_users

def save_to_csv(users, filename):
    if not users:
        print("No users found.")
        return
    keys = users[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(users)
    print(f"\nSaved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subreddit", type=str, required=True)
    parser.add_argument("--users-count", type=int, required=True)
    
    args = parser.parse_args()
    
    # Defaults: 500 karma, 180 days age
    users = fetch_qualified_users_no_api(args.subreddit, args.users_count, 500, 180)
    
    filename = f"users_{args.subreddit}_noapi.csv"
    save_to_csv(users, filename)