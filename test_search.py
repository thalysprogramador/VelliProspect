from ddgs import DDGS

try:
    print("Testing new DDGS")
    results = DDGS().text('site:instagram.com "Estetica" "São Paulo"', max_results=5)
    print(f"Results: {list(results)}")
except Exception as e:
    print(f"Error DDGS: {e}")
