import re
import json

def _clean_json_response(text):
    """
    Copy of the improved logic from ai_engine/services.py
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    
    # Find start and end of JSON content
    obj_start = text.find('{')
    list_start = text.find('[')
    
    # Determine if it's likely an object or a list
    if obj_start != -1 and (list_start == -1 or obj_start < list_start):
        start = obj_start
        end = text.rfind('}')
    elif list_start != -1:
        start = list_start
        end = text.rfind(']')
    else:
        return text

    if start != -1 and end != -1:
        text = text[start : end + 1]
        
    # Cleanup common LLM JSON errors
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
        
    return text

def test_cleaning():
    test_cases = [
        {
            "name": "Noisy Object",
            "input": 'Here is the data: {"a": 1, "b": 2} hope it helps!',
            "expected": '{"a": 1, "b": 2}'
        },
        {
            "name": "Noisy List",
            "input": 'Sure, here are the questions: [{"q": "1"}, {"q": "2"}] Let me know if you need more.',
            "expected": '[{"q": "1"}, {"q": "2"}]'
        },
        {
            "name": "Markdown Object",
            "input": '```json\n{"a": 1}\n```',
            "expected": '{"a": 1}'
        },
        {
            "name": "Markdown List",
            "input": '```json\n[{"q": "1"}]\n```',
            "expected": '[{"q": "1"}]'
        },
        {
            "name": "Trailing Comma Object",
            "input": '{"a": 1,}',
            "expected": '{"a": 1}'
        },
        {
            "name": "Trailing Comma List",
            "input": '[{"q": "1"},]',
            "expected": '[{"q": "1"}]'
        }
    ]

    for case in test_cases:
        actual = _clean_json_response(case["input"])
        try:
            json.loads(actual)
            result = "PASS" if actual == case["expected"] else "FAIL (Mismatch)"
        except json.JSONDecodeError:
            result = "FAIL (Invalid JSON)"
        
        print(f"[{result}] {case['name']}")
        if result != "PASS":
            print(f"  Input: {case['input']}")
            print(f"  Expected: {case['expected']}")
            print(f"  Actual: {case['actual']}")

if __name__ == "__main__":
    test_cleaning()
