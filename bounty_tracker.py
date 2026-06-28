#!/usr/bin/env python3
"""
GitHub Bounty Tracker
=====================
Scans GitHub repositories for open issues tagged with bounty labels.
Extracts dollar amounts from titles/bodies and displays ranked results.

Usage:
    python bounty_tracker.py                    # Scan configured repos
    python bounty_tracker.py --search           # Search all public GitHub issues
    python bounty_tracker.py --watch            # Run continuously
    python bounty_tracker.py --output csv       # Export as CSV
"""
import os
import re
import json
import time
import argparse
import csv
import logging

import requests
from dotenv import load_dotenv
import colorlog

load_dotenv()

# Logging setup
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
    datefmt="%H:%M:%S"
))
logger = logging.getLogger("BountyTracker")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

GITHUB_API = "https://api.github.com"
AMOUNT_PATTERN = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)


class GitHubBountyTracker:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        else:
            logger.warning("No GITHUB_TOKEN set. Rate limits will be strict (60 req/hour).")

        self.bounty_labels = [
            l.strip() for l in os.getenv(
                "BOUNTY_LABELS", "bounty,Bounty,help wanted"
            ).split(",")
        ]
        self.min_amount = float(os.getenv("MIN_AMOUNT", 0))

    def _get(self, url, params=None):
        """Make a rate-limit-aware GET request."""
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            if resp.status_code == 403:
                reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset_time - int(time.time()), 5)
                logger.warning(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def extract_amount(self, text):
        """Extract the first dollar amount from text."""
        if not text:
            return 0.0
        match = AMOUNT_PATTERN.search(text)
        if match:
            return float(match.group(1).replace(",", ""))
        return 0.0

    def scan_repo(self, owner_repo):
        """Scan a single repo for bounty-labeled open issues."""
        owner, repo = owner_repo.strip().split("/", 1)
        logger.info(f"Scanning {owner}/{repo}...")
        bounties = []

        for label in self.bounty_labels:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
            params = {"state": "open", "labels": label, "per_page": 50}
            data = self._get(url, params)
            if not data:
                continue
            for issue in data:
                if "pull_request" in issue:
                    continue
                amount = self.extract_amount(
                    issue.get("title", "") + " " + (issue.get("body") or "")
                )
                bounties.append({
                    "repo": f"{owner}/{repo}",
                    "issue_number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"],
                    "amount_usd": amount,
                    "labels": [l["name"] for l in issue.get("labels", [])],
                    "created_at": issue["created_at"][:10],
                    "comments": issue.get("comments", 0),
                })

        # Deduplicate by issue number
        seen = set()
        unique = []
        for b in bounties:
            key = (b["repo"], b["issue_number"])
            if key not in seen:
                seen.add(key)
                unique.append(b)
        return unique

    def search_github(self, extra_query=""):
        """Search all public GitHub issues with bounty label."""
        logger.info("Searching public GitHub for bounty issues...")
        bounties = []
        query = f"label:bounty state:open type:issue {extra_query}"
        url = f"{GITHUB_API}/search/issues"
        params = {"q": query, "per_page": 50, "sort": "created", "order": "desc"}
        data = self._get(url, params)
        if data and "items" in data:
            for issue in data["items"]:
                amount = self.extract_amount(
                    issue.get("title", "") + " " + (issue.get("body") or "")
                )
                repo_url = issue["repository_url"]
                repo_name = "/".join(repo_url.split("/")[-2:])
                bounties.append({
                    "repo": repo_name,
                    "issue_number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"],
                    "amount_usd": amount,
                    "labels": [l["name"] for l in issue.get("labels", [])],
                    "created_at": issue["created_at"][:10],
                    "comments": issue.get("comments", 0),
                })
        return bounties

    def filter_and_rank(self, bounties):
        """Filter by min_amount and rank by USD descending."""
        filtered = [b for b in bounties if b["amount_usd"] >= self.min_amount]
        return sorted(filtered, key=lambda x: x["amount_usd"], reverse=True)

    def display_table(self, bounties):
        """Print results as a formatted table."""
        try:
            from tabulate import tabulate
        except ImportError:
            self.display_simple(bounties)
            return

        if not bounties:
            print("\n  No bounties found matching your criteria.\n")
            return

        rows = []
        for b in bounties:
            amount_str = f"${b['amount_usd']:.0f}" if b["amount_usd"] > 0 else "?"
            title = b["title"][:55] + "..." if len(b["title"]) > 55 else b["title"]
            rows.append([
                b["repo"], f"#{b['issue_number']}", title,
                amount_str, b["created_at"], b["comments"], b["url"],
            ])

        headers = ["Repo", "#", "Title", "Amount", "Created", "💬", "URL"]
        print("\n" + tabulate(rows, headers=headers, tablefmt="rounded_outline"))
        print(f"\n  Total: {len(bounties)} bounty issue(s) found\n")

    def display_simple(self, bounties):
        if not bounties:
            print("No bounties found.")
            return
        for b in bounties:
            print(f"  [${b['amount_usd']:>8.0f}]  {b['repo']}#{b['issue_number']} — {b['title'][:60]}")
            print(f"              {b['url']}")

    def export_json(self, bounties, path="output/bounties.json"):
        os.makedirs("output", exist_ok=True)
        with open(path, "w") as f:
            json.dump(bounties, f, indent=2)
        logger.info(f"Saved JSON to {path}")

    def export_csv(self, bounties, path="output/bounties.csv"):
        os.makedirs("output", exist_ok=True)
        if not bounties:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=bounties[0].keys())
            writer.writeheader()
            writer.writerows(bounties)
        logger.info(f"Saved CSV to {path}")


def main():
    parser = argparse.ArgumentParser(description="GitHub Bounty Tracker")
    parser.add_argument("--search", action="store_true", help="Search all public GitHub issues")
    parser.add_argument("--watch", action="store_true", help="Run continuously on a schedule")
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--query", default="", help="Extra GitHub search query terms")
    args = parser.parse_args()

    tracker = GitHubBountyTracker()

    def run_once():
        if args.search:
            bounties = tracker.search_github(args.query)
        else:
            repos_env = os.getenv("REPOS", "")
            if not repos_env.strip():
                logger.info("No REPOS configured. Falling back to public search.")
                bounties = tracker.search_github(args.query)
            else:
                bounties = []
                for repo in repos_env.split(","):
                    if "/" in repo.strip():
                        bounties.extend(tracker.scan_repo(repo.strip()))

        ranked = tracker.filter_and_rank(bounties)

        if args.output == "table":
            tracker.display_table(ranked)
        elif args.output == "json":
            tracker.export_json(ranked)
        elif args.output == "csv":
            tracker.export_csv(ranked)
        return ranked

    if args.watch:
        interval = int(os.getenv("WATCH_INTERVAL", 300))
        logger.info(f"Watch mode: scanning every {interval}s. Press Ctrl+C to stop.")
        while True:
            run_once()
            logger.info(f"Next scan in {interval}s...")
            time.sleep(interval)
    else:
        run_once()


if __name__ == "__main__":
    main()
