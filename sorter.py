import pandas as pd
import os
import json

def sort_difficulties(csv_file = 'gamebanana_data.csv'):
    diffculties = []
    mod = {}
    if not os.path.exists(csv_file):
        return 'File not found'
    try:
        df = pd.read_csv(csv_file)
        print(f"{len(df)} rows loaded")
    except Exception as e:
        return f"Error loading file: {str(e)}"
    
    diffuculty_categories = {
        'beginner': [],
        'intermediate': [],
        'advanced': [],
        'expert': [],
        'grandmaster': [],
        'no difficulty available': []
    }

    for row in df.iterrows():
        print(row)
        mod = {
            'title': row['title'],
            'url': row['url'],
            'download': int(row['download']),
            'difficulties': row['difficulties'],
            'description': row['description']
        }

        for diff in diffculties:
            if diff in diffuculty_categories:
                diffuculty_categories[diff].append(mod)
    return diffuculty_categories


def get_by_difficulty(difficulty, limit = None):
    sorted_difficulties = sort_difficulties()
    if difficulty not in sorted_difficulties:
        return 'Difficulty not found'
    
    mods = sorted_difficulties[difficulty]

    if limit:
        mods = mods[:limit]
    return mods


def save_sorted_to_json():
    sorted_difficulties = sort_difficulties()
    for mods in sorted_difficulties.items():
        with open('sorted_difficulties.json', 'w') as f:
            json.dump(mods, f, ensure_ascii=False, indent=2)
        return 'Data saved to sorted_difficulties.json'
    

def main():
    print(get_by_difficulty('grandmaster', 5))
    print(save_sorted_to_json())

if __name__ == '__main__':
    main()