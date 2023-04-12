import requests
import json
import os
import re
from pathlib import Path
import sys

base_url = "https://bastilaapi-production.up.railway.app"


def fetch_patterns():
    response = requests.get(f"{base_url}/api/snippets/")
    response.raise_for_status()
    snippets = response.json()

    print(snippets)

    return snippets['results']


def search_files(patterns):
    results = []

    # Loop over every pattern
    for pattern in patterns:
        # Loop over every file
        snippet_instances = 0
        for path in Path('.').glob('**/*'):
            if path.is_dir():
                continue

            with open(path, 'rb') as f:
                content = f.read()

            patterns_in_file = re.findall(pattern['snippet'].encode(), content)
            snippet_instances += len(patterns_in_file)

        pattern_failed = pattern['previous_count'] and (snippet_instances > pattern['previous_count'])
        results.append({
            'id': pattern['id'],
            'previous_count': pattern['previous_count'],
            'count': snippet_instances,
            'is_successful': not pattern_failed
        })

    return results


def post_results(result):
    esponse = requests.post(
        f"{base_url}/api/results/",
        data=json.dumps(result),
        headers={
            'Content-Type': 'application/json'
        }
    )
    response.raise_for_status()
    return response


def create_check():
    response = requests.post(
        f"{base_url}/api/checks/",
        data=json.dumps({}),
        headers={
            'Content-Type': 'application/json'
        }
    )
    response.raise_for_status()
    return response.json()


def main():
    try:
        check = create_check()
    except Exception as e:
        sys.exit(1)

    print('Done Check')

    try:
        patterns = fetch_patterns()
    except Exception as e:
        sys.exit(1)

    print('Patterns fetched')
    print(patterns)

    try:
        results = search_files(patterns)
    except Exception as e:
        sys.exit(1)

    print('Code Searched')

    result = {
        "check": check["id"],
        "results": results
    }
    try:
        post_results(result)
    except Exception as e:
        sys.exit(1)

    print('Results Saved')

    failures = [r for r in results if not r['is_successful']]
    if len(failures) > 1:
        sys.exit(1)


if __name__ == "__main__":
    main()