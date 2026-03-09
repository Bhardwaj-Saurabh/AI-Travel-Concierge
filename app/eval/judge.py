import csv
import json
import asyncio
import time
from app.main import run_request, create_kernel
from app.eval.llm_judge import LLMJudge
from app.models import TripPlan
from pydantic import ValidationError

# Define test scenarios
TEST_CASES = [
    {
        "name": "Test 1 - Paris Trip",
        "input": {
            "destination": "Paris",
            "travel_dates": "2026-06-01 to 2026-06-08",
            "card": "BankGold"
        },
        "query": "I want to go to Paris from 2026-06-01 to 2026-06-08 with my BankGold card"
    },
    {
        "name": "Test 2 - Tokyo Trip",
        "input": {
            "destination": "Tokyo",
            "travel_dates": "2026-07-10 to 2026-07-17",
            "card": "BankPlatinum"
        },
        "query": "I want to visit Tokyo from July 10-17, 2026 with my BankPlatinum card"
    },
    {
        "name": "Test 3 - Barcelona Trip",
        "input": {
            "destination": "Barcelona",
            "travel_dates": "2026-08-15 to 2026-08-22",
            "card": "BankRewards"
        },
        "query": "Plan a trip to Barcelona from August 15-22, 2026. I have a BankRewards card - what perks can I use?"
    }
]


def evaluate(case):
    """
    Evaluate a test case by running the agent and checking the output.

    Args:
        case: Test case dictionary with input parameters

    Returns:
        Dictionary with evaluation results
    """
    print(f"\n{'='*60}")
    print(f"📝 Evaluating: {case['name']}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Step 1: Run the agent with the test case query
        query = case.get("query", f"I want to go to {case['input']['destination']} from {case['input']['travel_dates']} with my {case['input']['card']} card")
        print(f"   Query: {query}")

        agent_response = run_request(query)
        latency = time.time() - start_time
        print(f"   ⏱️  Agent latency: {latency:.2f}s")

        # Step 2: Parse the JSON response
        try:
            plan_data = json.loads(agent_response)
            # Handle wrapper format
            if "plan" in plan_data:
                plan_dict = plan_data["plan"]
            elif "destination" in plan_data:
                plan_dict = plan_data
            else:
                plan_dict = plan_data
            valid_json = True
            print(f"   ✅ Valid JSON response")
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON: {e}")
            valid_json = False
            plan_dict = {}

        # Step 3: Validate with Pydantic TripPlan model
        pydantic_valid = False
        if valid_json and plan_dict:
            try:
                trip_plan = TripPlan(**plan_dict)
                pydantic_valid = True
                print(f"   ✅ Pydantic validation passed")
            except (ValidationError, Exception) as e:
                print(f"   ⚠️  Pydantic validation: {e}")

        # Step 4: Check for required fields
        has_weather = bool(plan_dict.get("weather"))
        has_results = bool(plan_dict.get("results"))
        has_card = bool(plan_dict.get("card_recommendation"))
        has_currency = bool(plan_dict.get("currency_info"))
        has_citations = bool(plan_dict.get("citations"))
        has_next_steps = bool(plan_dict.get("next_steps"))
        card_mentioned = False
        if has_card:
            card_data = plan_dict.get("card_recommendation", {})
            card_mentioned = bool(card_data.get("card", ""))

        print(f"   Weather data: {'✅' if has_weather else '❌'}")
        print(f"   Search results: {'✅' if has_results else '❌'}")
        print(f"   Card recommendation: {'✅' if has_card else '❌'}")
        print(f"   Currency info: {'✅' if has_currency else '❌'}")
        print(f"   Citations: {'✅' if has_citations else '❌'}")
        print(f"   Next steps: {'✅' if has_next_steps else '❌'}")

        # Step 5: Run LLM Judge evaluation
        llm_score = None
        criteria_scores = {}
        try:
            kernel = create_kernel()
            judge = LLMJudge(kernel)

            # Determine tool calls made
            tool_calls = []
            if has_weather:
                tool_calls.append({"name": "get_weather", "arguments": {"destination": case["input"]["destination"]}})
            if has_currency:
                tool_calls.append({"name": "convert_fx", "arguments": {"amount": 100, "base": "USD"}})
            if has_results:
                tool_calls.append({"name": "web_search", "arguments": {"query": f"restaurants in {case['input']['destination']}"}})
            if has_card:
                tool_calls.append({"name": "recommend_card", "arguments": {"card": case["input"]["card"]}})

            citations = plan_dict.get("citations", [])

            eval_result = asyncio.run(judge.evaluate_response(
                user_query=query,
                agent_response=agent_response,
                structured_output=plan_dict,
                tool_calls=tool_calls,
                citations=citations
            ))

            llm_score = eval_result.overall_score
            criteria_scores = eval_result.criteria_scores
            print(f"\n   ⚖️  LLM Judge Score: {llm_score:.2f}/5.0 ({'PASS' if eval_result.passed else 'FAIL'})")
            for criterion, score in criteria_scores.items():
                print(f"      {criterion}: {score}/5.0")

        except Exception as e:
            print(f"   ⚠️  LLM Judge evaluation error: {e}")

        return {
            "valid_json": valid_json,
            "pydantic_valid": pydantic_valid,
            "has_weather": has_weather,
            "has_results": has_results,
            "has_card": has_card,
            "has_currency": has_currency,
            "has_citations": has_citations,
            "has_next_steps": has_next_steps,
            "card_mentioned": card_mentioned,
            "latency_s": round(latency, 2),
            "llm_score": llm_score,
            "criteria_scores": criteria_scores
        }

    except (ValidationError, Exception) as e:
        print(f"   ❌ Failed to evaluate: {e}")
        return {
            "valid_json": False,
            "pydantic_valid": False,
            "has_weather": False,
            "has_results": False,
            "has_card": False,
            "has_currency": False,
            "has_citations": False,
            "has_next_steps": False,
            "card_mentioned": False,
            "latency_s": round(time.time() - start_time, 2),
            "llm_score": None,
            "criteria_scores": {}
        }


def main():
    """
    Main evaluation function that runs all test cases and prints numerical scores.
    """
    print("=" * 60)
    print("🏁 AI Travel Concierge - LLM Judge Evaluation")
    print("=" * 60)

    results = []

    for case in TEST_CASES:
        outcome = evaluate(case)
        results.append({
            "name": case["name"],
            "destination": case["input"]["destination"],
            **outcome
        })

    # Write results to CSV
    if results:
        csv_fields = ["name", "destination", "valid_json", "pydantic_valid",
                       "has_weather", "has_results", "has_card", "has_currency",
                       "has_citations", "has_next_steps", "card_mentioned",
                       "latency_s", "llm_score"]
        with open("app/eval/results.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)

    total_cases = len(results)
    json_pass = sum(1 for r in results if r["valid_json"])
    pydantic_pass = sum(1 for r in results if r["pydantic_valid"])
    weather_pass = sum(1 for r in results if r["has_weather"])
    search_pass = sum(1 for r in results if r["has_results"])
    card_pass = sum(1 for r in results if r["has_card"])
    citation_pass = sum(1 for r in results if r["has_citations"])

    print(f"  Total test cases:      {total_cases}")
    print(f"  Valid JSON:            {json_pass}/{total_cases}")
    print(f"  Pydantic valid:        {pydantic_pass}/{total_cases}")
    print(f"  Has weather data:      {weather_pass}/{total_cases}")
    print(f"  Has search results:    {search_pass}/{total_cases}")
    print(f"  Has card recommendation: {card_pass}/{total_cases}")
    print(f"  Has citations:         {citation_pass}/{total_cases}")

    # LLM Judge scores
    llm_scores = [r["llm_score"] for r in results if r["llm_score"] is not None]
    if llm_scores:
        avg_score = sum(llm_scores) / len(llm_scores)
        min_score = min(llm_scores)
        max_score = max(llm_scores)
        pass_count = sum(1 for s in llm_scores if s >= 3.0)

        print(f"\n  📈 LLM Judge Scores:")
        print(f"    Average score:       {avg_score:.2f}/5.0")
        print(f"    Min score:           {min_score:.2f}/5.0")
        print(f"    Max score:           {max_score:.2f}/5.0")
        print(f"    Pass rate (>=3.0):   {pass_count}/{len(llm_scores)} ({pass_count/len(llm_scores)*100:.0f}%)")

        # Per-criteria averages
        all_criteria = {}
        for r in results:
            for criterion, score in r.get("criteria_scores", {}).items():
                if criterion not in all_criteria:
                    all_criteria[criterion] = []
                all_criteria[criterion].append(float(score))

        if all_criteria:
            print(f"\n  📊 Per-Criterion Averages:")
            for criterion, scores in all_criteria.items():
                avg = sum(scores) / len(scores)
                print(f"    {criterion:20s}: {avg:.2f}/5.0")

    # Latency
    latencies = [r["latency_s"] for r in results]
    avg_latency = sum(latencies) / len(latencies)
    print(f"\n  ⏱️  Average latency:    {avg_latency:.2f}s")

    print("\n" + "=" * 60)
    print("✅ Evaluation complete. Results saved to app/eval/results.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()
