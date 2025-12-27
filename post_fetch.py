import requests
import argparse
import csv
import json
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def fetch_user_posts(username, target_count, target_subreddit=None):
    collected_posts = []
    after_token = None
    
    print(f"--- Fetching posts for user: u/{username} ---")
    if target_subreddit:
        print(f"Filter: Only posts in r/{target_subreddit}")
    else:
        print("Filter: All subreddits")

    while len(collected_posts) < target_count:
        # Fetch user's submission history
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit=25"
        if after_token:
            url += f"&after={after_token}"
            
        try:
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 429:
                print("(!) Rate limited. Sleeping 6m...")
                time.sleep(600)
                continue
            elif response.status_code != 200:
                print(f"Error {response.status_code}: Could not fetch data.")
                break
                
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            after_token = data.get('data', {}).get('after')
            
            if not posts:
                print("No more posts available.")
                break

            for post in posts:
                if len(collected_posts) >= target_count:
                    break
                    
                p_data = post['data']
                
                # --- FILTER 1: Subreddit (Optional) ---
                # If user specified a subreddit, skip posts not from there
                if target_subreddit:
                    if p_data['subreddit'].lower() != target_subreddit.lower():
                        continue

                # --- FILTER 2: Text Post Only ---
                if not p_data.get('is_self'):
                    continue

                content = p_data.get('selftext', '')
                
                # --- FILTER 3: Removed/Deleted/Empty ---
                if content in ['[removed]', '[deleted]', ''] or content is None:
                    continue
                    
                # --- FILTER 4: Length Check (> 15 words) ---
                word_count = len(content.split())
                if word_count < 15:
                    continue
                
                # Add to collection
                collected_posts.append({
                    'id': p_data['id'],
                    'subreddit': p_data['subreddit'],
                    'title': p_data['title'],
                    'body': content,
                    'score': p_data['score'],
                    'upvote_ratio': p_data['upvote_ratio'],
                    'created_utc': p_data['created_utc'],
                    'date': datetime.utcfromtimestamp(p_data['created_utc']).strftime('%Y-%m-%d'),
                    'url': p_data['url'],
                    'word_count': word_count
                })

            # Sleep to be polite to the API
            time.sleep(3)
            
            if not after_token:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    return collected_posts

def save_to_json(posts, username, label="all"):
    if not posts:
        return
    filename = f"posts_{username}_{label}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)
    print(f"[JSON] Saved {len(posts)} posts to {filename}")

def save_to_csv(posts, username, label="all"):
    if not posts:
        return
    filename = f"posts_{username}_{label}.csv"
    keys = posts[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(posts)
    print(f"[CSV]  Saved {len(posts)} posts to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch public posts from a Reddit user.")
    parser.add_argument("--username", type=str, required=True, help="Reddit username")
    parser.add_argument("--post-count", type=int, default=20, help="Max number of posts to fetch")
    
    # New Optional Flag
    parser.add_argument("--subreddit", type=str, help="Only fetch posts from this subreddit (e.g., 'investing')")
    
    args = parser.parse_args()
    
    # Fetch
    posts = fetch_user_posts(args.username, args.post_count, args.subreddit)
    
    if posts:
        # Generate a label for filenames (e.g., "technology" or "all")
        label = args.subreddit if args.subreddit else "all"
        
        # Save BOTH formats (so you have a backup)
        save_to_json(posts, args.username, label)
        save_to_csv(posts, args.username, label)
    else:
        print("No posts found matching the criteria.")