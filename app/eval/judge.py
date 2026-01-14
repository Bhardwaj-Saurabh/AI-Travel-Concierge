import csv
from app.main import run_request
from pydantic import ValidationError

# Define test scenarios
TEST_CASES = [
    {
        "name": "Test 1",
        "input":{
            "destination": "Paris",
            "travel_dates": "2026-06-01 to 2026-06-08",
            "card": "BankGold"
        }
    },
    {
        "name": "Test 2",
        "input":{
            "destination": "Tokyo",
            "travel_dates": "2026-07-10 to 2026-07-17",
            "card": "BankGold"
        }
    },
    {
        "name": "Test 3",
        "input":{
            "destination": "Barcelona",
            "travel_dates": "2026-08-15 to 2026-08-22",
            "card": "BankGold"
        }
    }
]

def evaluate(case):
    """
    Evaluate a test case by running the agent and checking the output.
    
    TODO: Implement this function to:
    1. Run the agent with the test case input
    2. Parse the JSON response
    3. Validate the response structure
    4. Check for required fields and data quality
    5. Return evaluation results
    
    Args:
        case: Test case dictionary with input parameters
        
    Returns:
        Dictionary with evaluation results
        
    Hints:
    - Use run_request() to get agent response
    - Parse JSON and validate with Pydantic
    - Check for citations, card recommendations, etc.
    - Handle errors gracefully
    """
    try:
        # TODO: Implement evaluation logic
        # 1. Run the agent
        # 2. Parse and validate response
        # 3. Check for required fields
        # 4. Return evaluation results
        
        # For now, return mock evaluation
        return {
            "valid_json": True,
            "has_citations": True,
            "card_mentioned": True
        }
    except (ValidationError, Exception) as e:
        print(f"❌ Failed to parse agent output: {e}")
        return {
            "valid_json": False,
            "has_citations": False,
            "card_mentioned": False
        }

def main():
    """
    Main evaluation function that runs all test cases and saves results.
    
    TODO: Implement this function to:
    1. Run all test cases
    2. Collect evaluation results
    3. Save results to CSV file
    4. Print summary statistics
    
    Hints:
    - Iterate through TEST_CASES
    - Call evaluate() for each case
    - Write results to CSV file
    - Print summary statistics
    """
    results = []
    
    # TODO: Implement main evaluation logic
    # 1. Run all test cases
    # 2. Collect results
    # 3. Save to CSV
    # 4. Print summary
    
    for case in TEST_CASES:
        print(f"Running test: {case['name']}")
        outcome = evaluate(case)
        print(f"Test outcome: {outcome}")
        results.append({**case["input"], **outcome})
    
    # Write results to CSV
    with open("app/eval/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print("Evaluation complete. Results saved to eval/results.csv")

if __name__ == "__main__":
    main()