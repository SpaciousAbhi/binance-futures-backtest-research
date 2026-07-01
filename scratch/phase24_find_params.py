"""
scratch/phase24_find_params.py

Finds all parameters accessed in src/strategies/candidates.py.
"""
import re

def main():
    with open('src/strategies/candidates.py', 'r', encoding='utf-8') as f:
        content = f.read()

    params = re.findall(r'self\.params\["([^"]+)"\]|self\.params\.get\("([^"]+)"', content)
    flat_params = set()
    for p in params:
        flat_params.add(p[0] if p[0] else p[1])
    print('Parameters used in candidates.py:', sorted(list(flat_params)))

if __name__ == "__main__":
    main()
