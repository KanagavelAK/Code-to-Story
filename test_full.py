"""Comprehensive E2E Test Suite for Code to Story."""
import sys
import io
import json
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API = "http://127.0.0.1:8000"
passed = 0
failed = 0
total = 0

def test(name, condition, detail=""):
    """Track pass/fail for each test."""
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


def safe_post(payload, timeout=90):
    """POST to /convert with graceful timeout handling."""
    start = time.time()
    try:
        r = requests.post(f"{API}/convert", json=payload, timeout=timeout)
        elapsed = time.time() - start
        return r, elapsed, None
    except requests.exceptions.ReadTimeout:
        elapsed = time.time() - start
        return None, elapsed, "Timed out"
    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, str(e)


# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 1: API Health & Basics")
print("=" * 60)

r = requests.get(f"{API}/health")
test("GET /health returns 200", r.status_code == 200)
test("GET /health returns ok", r.json().get("status") == "ok")

r = requests.get(f"{API}/")
test("GET / returns 200", r.status_code == 200)
test("GET / serves HTML", "text/html" in r.headers.get("content-type", ""))
test("GET / contains page title", "Code to Story" in r.text)

r = requests.get(f"{API}/nonexistent")
test("GET /nonexistent returns 404", r.status_code == 404)

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 2: Edge Cases & Validation")
print("=" * 60)

r, _, _ = safe_post({"code": "", "language": "Python"})
test("Empty code returns 200 (not crash)", r and r.status_code == 200)

r = requests.post(f"{API}/convert", json={"code": "x = 1"})
test("Missing language returns 422", r.status_code == 422)

r = requests.post(f"{API}/convert", json={"language": "Python"})
test("Missing code returns 422", r.status_code == 422)

r = requests.post(f"{API}/convert", json={})
test("Empty body returns 422", r.status_code == 422)

r, elapsed, err = safe_post({"code": "x = 1", "language": "Python"})
test("1-line code returns 200", r and r.status_code == 200, err or "")
if r:
    data = r.json()
    test("1-line code has story field", "story" in data)

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 3: Simple Code (Quick Story Mode)")
print("=" * 60)

simple_tests = [
    {
        "name": "Simple function",
        "code": "def add(a, b):\n    return a + b",
        "language": "Python",
    },
    {
        "name": "Loop with condition",
        "code": "for i in range(5):\n    if i % 2 == 0:\n        print(i)",
        "language": "Python",
    },
    {
        "name": "Class with method",
        "code": 'class Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        return f"{self.name} says woof!"',
        "language": "Python",
    },
]

for t in simple_tests:
    r, elapsed, err = safe_post({"code": t["code"], "language": t["language"]})

    if err:
        test(f"{t['name']} — response received", False, f"{err} ({elapsed:.1f}s)")
        continue

    data = r.json()
    is_fallback = data.get("summary") == "Parse error."

    test(f"{t['name']} — returns 200", r.status_code == 200)
    test(f"{t['name']} — not fallback", not is_fallback, "Got fallback response")
    test(f"{t['name']} — has story", len(data.get("story", "")) > 20)
    test(f"{t['name']} — has summary", len(data.get("summary", "")) > 10)
    test(f"{t['name']} — has key_steps", isinstance(data.get("key_steps"), list) and len(data["key_steps"]) >= 2)
    print(f"     📖 {data['story'][:80]}...")
    print(f"     ⏱️  {elapsed:.1f}s")

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 4: Medium Code (Quick Story)")
print("=" * 60)

medium_code = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1"""

r, elapsed, err = safe_post({"code": medium_code, "language": "Python"})
if err:
    test("Binary search — response received", False, err)
else:
    data = r.json()
    is_fallback = data.get("summary") == "Parse error."
    test("Binary search — returns 200", r.status_code == 200)
    test("Binary search — not fallback", not is_fallback)
    test("Binary search — story > 100 chars", len(data.get("story", "")) > 100)
    test("Binary search — has steps", len(data.get("key_steps", [])) >= 3)
    print(f"     📖 {data['story'][:80]}...")
    print(f"     ⏱️  {elapsed:.1f}s")

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 5: Complex Code (Chapter Mode)")
print("=" * 60)

complex_code = """import functools
import time

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.session_count = 0

    @retry(max_attempts=3, delay=2)
    def fetch_data(self, endpoint):
        self.session_count += 1
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
        response.raise_for_status()
        return response.json()"""

r, elapsed, err = safe_post({"code": complex_code, "language": "Python"})
if err:
    test("Complex code — response received", False, err)
else:
    data = r.json()
    is_fallback = data.get("summary") == "Parse error."
    test("Complex code — returns 200", r.status_code == 200)
    test("Complex code — not fallback", not is_fallback, f"Fallback after {elapsed:.1f}s")
    test("Complex code — story > 200 chars", len(data.get("story", "")) > 200)
    test("Complex code — has Chapter", "Chapter" in data.get("story", "") or "chapter" in data.get("story", ""))
    test("Complex code — has steps", len(data.get("key_steps", [])) >= 3)
    print(f"     📖 {data['story'][:100]}...")
    print(f"     ⏱️  {elapsed:.1f}s")

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 6: Multi-Language Support")
print("=" * 60)

lang_tests = [
    ("JavaScript", "function greet(name) {\n  return `Hello, ${name}!`;\n}"),
    ("Java", "public class Main {\n  public static void main(String[] args) {\n    System.out.println(\"Hello\");\n  }\n}"),
    ("C++", "#include <iostream>\nint main() {\n  std::cout << \"Hello\";\n  return 0;\n}"),
]

for lang, code in lang_tests:
    r, elapsed, err = safe_post({"code": code, "language": lang})
    if err:
        test(f"{lang} — response received", False, err)
        continue

    data = r.json()
    is_fallback = data.get("summary") == "Parse error."
    test(f"{lang} — returns 200", r.status_code == 200)
    test(f"{lang} — not fallback", not is_fallback, f"Fallback after {elapsed:.1f}s")
    print(f"     📖 {data['story'][:70]}...")
    print(f"     ⏱️  {elapsed:.1f}s")

# =====================================================
print("\n" + "=" * 60)
print("  TEST GROUP 7: Response Format Validation")
print("=" * 60)

r, _, _ = safe_post({"code": "print('hi')", "language": "Python"})
if r:
    data = r.json()
    test("Response has 'story' key", "story" in data)
    test("Response has 'summary' key", "summary" in data)
    test("Response has 'key_steps' key", "key_steps" in data)
    test("story is a string", isinstance(data.get("story"), str))
    test("summary is a string", isinstance(data.get("summary"), str))
    test("key_steps is a list", isinstance(data.get("key_steps"), list))
    test("key_steps items are strings", all(isinstance(s, str) for s in data.get("key_steps", [])))
    test("No extra keys", set(data.keys()) == {"story", "summary", "key_steps"}, f"Keys: {set(data.keys())}")

# =====================================================
print("\n" + "=" * 60)
print(f"  FINAL RESULTS: {passed}/{total} passed, {failed}/{total} failed")
print("=" * 60)

if failed == 0:
    print("  🎉 ALL TESTS PASSED! Application is production-ready.")
else:
    print(f"  ⚠️  {failed} test(s) need attention.")
