# reddit-public-api-scripts
scripts using reddit public api without any credential:

- Fetch users from a subreddit:

```sh
python users_select.py --subreddit wallstreetbets --users-count 10 
```

- Fetch posts from an user in a subreddit:

```sh
python ./post_fetch.py --username <username> --post-count 20 --subreddit <subreddit name>
```