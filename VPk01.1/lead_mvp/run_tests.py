import json
import requests

BASE_URL = "http://127.0.0.1:8000/lead"

def run_tests():
    with open("test_payloads.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    
    passed = 0
    failed = 0
    
    for case in test_cases:
        if "note" in case:  # пропускаем кейс 10, который требует невалидного JSON
            print(f"[SKIP] {case['id']}: {case.get('description', '')} - {case['note']}")
            continue
        
        payload = case.get("payload")
        expected_status = case["expected_status"]
        
        try:
            response = requests.post(BASE_URL, json=payload)
            status_match = (response.status_code == expected_status)
            
            # Простая проверка наличия ожидаемой фразы в ответе (если указана)
            message_match = True
            if "expected_message" in case and case["expected_message"]:
                message_match = case["expected_message"] in response.text
            
            if status_match and message_match:
                print(f"[PASS] {case['id']}: {case['description']} -> {response.status_code}")
                passed += 1
            else:
                print(f"[FAIL] {case['id']}: {case['description']} -> ожидался {expected_status}, получен {response.status_code}, ответ: {response.text}")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {case['id']}: {case['description']} -> {e}")
            failed += 1
    
    print(f"\nРезультат: {passed} пройдено, {failed} не пройдено")

if __name__ == "__main__":
    run_tests()