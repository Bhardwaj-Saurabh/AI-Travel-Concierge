"""
LLM-as-Judge Evaluation System
Implements comprehensive evaluation using LLM to judge agent responses.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory

logger = logging.getLogger(__name__)

@dataclass
class EvaluationCriteria:
    """Evaluation criteria for LLM-as-judge"""
    name: str
    description: str
    weight: float
    max_score: float = 5.0

@dataclass
class EvaluationResult:
    """Result of LLM-as-judge evaluation"""
    overall_score: float
    criteria_scores: Dict[str, float]
    reasoning: str
    recommendations: List[str]
    passed: bool

class LLMJudge:
    """LLM-as-Judge evaluation system"""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.criteria = self._setup_evaluation_criteria()
    
    def _setup_evaluation_criteria(self) -> List[EvaluationCriteria]:
        """Set up evaluation criteria"""
        return [
            EvaluationCriteria(
                name="accuracy",
                description="Accuracy of information provided",
                weight=0.25,
                max_score=5.0
            ),
            EvaluationCriteria(
                name="completeness",
                description="Completeness of response to user query",
                weight=0.20,
                max_score=5.0
            ),
            EvaluationCriteria(
                name="relevance",
                description="Relevance of information to user's needs",
                weight=0.20,
                max_score=5.0
            ),
            EvaluationCriteria(
                name="tool_usage",
                description="Appropriate and effective use of tools",
                weight=0.15,
                max_score=5.0
            ),
            EvaluationCriteria(
                name="structure",
                description="Clear structure and organization of response",
                weight=0.10,
                max_score=5.0
            ),
            EvaluationCriteria(
                name="citations",
                description="Proper citations and source attribution",
                weight=0.10,
                max_score=5.0
            )
        ]
    
    async def evaluate_response(
        self,
        user_query: str,
        agent_response: str,
        structured_output: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        citations: List[str],
        reference_facts: Optional[List[str]] = None
    ) -> EvaluationResult:
        """
        Evaluate agent response using LLM-as-judge.
        
        Args:
            user_query: Original user query
            agent_response: Natural language response from agent
            structured_output: Structured output (Pydantic model)
            tool_calls: List of tool calls made
            citations: List of citations provided
            reference_facts: Optional reference facts for accuracy checking
            
        Returns:
            EvaluationResult with scores and feedback
        """
        try:
            logger.info("⚖️ Starting LLM-as-judge evaluation")
            
            # Create evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(
                user_query, agent_response, structured_output, 
                tool_calls, citations, reference_facts
            )
            
            # Get LLM evaluation
            chat_service = self.kernel.get_service(type="ChatCompletionService")
            response = await chat_service.get_chat_message_contents(
                chat_history=ChatHistory.from_messages([("user", evaluation_prompt)]),
                settings={"temperature": 0.1, "max_tokens": 1000}
            )
            
            # Parse evaluation result
            evaluation_text = response[0].content.strip()
            result = self._parse_evaluation_result(evaluation_text)
            
            logger.info(f"⚖️ Evaluation completed. Overall score: {result.overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM-as-judge evaluation failed: {e}")
            return EvaluationResult(
                overall_score=0.0,
                criteria_scores={},
                reasoning=f"Evaluation failed: {e}",
                recommendations=["Fix evaluation system"],
                passed=False
            )
    
    def _create_evaluation_prompt(
        self,
        user_query: str,
        agent_response: str,
        structured_output: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        citations: List[str],
        reference_facts: Optional[List[str]] = None
    ) -> str:
        """Create evaluation prompt for LLM"""
        
        criteria_text = "\n".join([
            f"- {c.name} ({c.weight*100:.0f}%): {c.description} (0-{c.max_score})"
            for c in self.criteria
        ])
        
        tool_calls_text = "\n".join([
            f"- {call.get('name', 'unknown')}: {call.get('arguments', {})}"
            for call in tool_calls
        ]) if tool_calls else "None"
        
        citations_text = "\n".join([f"- {citation}" for citation in citations]) if citations else "None"
        
        reference_facts_text = "\n".join([f"- {fact}" for fact in reference_facts]) if reference_facts else "None"
        
        return f"""
        You are an expert evaluator assessing a Travel Credit Card Concierge agent's response.
        
        USER QUERY:
        {user_query}
        
        AGENT RESPONSE:
        {agent_response}
        
        STRUCTURED OUTPUT:
        {json.dumps(structured_output, indent=2)}
        
        TOOL CALLS MADE:
        {tool_calls_text}
        
        CITATIONS PROVIDED:
        {citations_text}
        
        REFERENCE FACTS (for accuracy checking):
        {reference_facts_text}
        
        EVALUATION CRITERIA:
        {criteria_text}
        
        Please evaluate the agent's response and provide:
        1. A score (0-5) for each criterion
        2. An overall weighted score (0-5)
        3. Detailed reasoning for each score
        4. Specific recommendations for improvement
        5. Whether the response passes (overall score >= 3.0)
        
        Respond in JSON format:
        {{
            "criteria_scores": {{
                "accuracy": 4.5,
                "completeness": 4.0,
                "relevance": 4.5,
                "tool_usage": 3.5,
                "structure": 4.0,
                "citations": 3.0
            }},
            "overall_score": 4.0,
            "reasoning": "Detailed explanation of scores...",
            "recommendations": ["Specific improvement suggestions..."],
            "passed": true
        }}
        """
    
    def _parse_evaluation_result(self, evaluation_text: str) -> EvaluationResult:
        """Parse LLM evaluation result"""
        try:
            # Try to extract JSON from the response
            start_idx = evaluation_text.find('{')
            end_idx = evaluation_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = evaluation_text[start_idx:end_idx]
                result_data = json.loads(json_text)
                
                return EvaluationResult(
                    overall_score=float(result_data.get('overall_score', 0.0)),
                    criteria_scores=result_data.get('criteria_scores', {}),
                    reasoning=result_data.get('reasoning', 'No reasoning provided'),
                    recommendations=result_data.get('recommendations', []),
                    passed=result_data.get('passed', False)
                )
            else:
                # Fallback parsing if JSON not found
                return self._fallback_parse(evaluation_text)
                
        except Exception as e:
            logger.error(f"❌ Failed to parse evaluation result: {e}")
            return self._fallback_parse(evaluation_text)
    
    def _fallback_parse(self, evaluation_text: str) -> EvaluationResult:
        """Fallback parsing when JSON parsing fails"""
        # Simple keyword-based parsing
        overall_score = 3.0  # Default score
        
        if "excellent" in evaluation_text.lower():
            overall_score = 5.0
        elif "good" in evaluation_text.lower():
            overall_score = 4.0
        elif "fair" in evaluation_text.lower():
            overall_score = 3.0
        elif "poor" in evaluation_text.lower():
            overall_score = 2.0
        elif "terrible" in evaluation_text.lower():
            overall_score = 1.0
        
        return EvaluationResult(
            overall_score=overall_score,
            criteria_scores={},
            reasoning="Fallback parsing used - detailed scores not available",
            recommendations=["Improve response format for better evaluation"],
            passed=overall_score >= 3.0
        )
    
    async def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of test cases.
        
        Args:
            test_cases: List of test cases with user_query, agent_response, etc.
            
        Returns:
            Batch evaluation results
        """
        try:
            logger.info(f"⚖️ Starting batch evaluation of {len(test_cases)} test cases")
            
            results = []
            total_score = 0.0
            passed_count = 0
            
            for i, test_case in enumerate(test_cases):
                logger.info(f"⚖️ Evaluating test case {i+1}/{len(test_cases)}")
                
                result = await self.evaluate_response(
                    user_query=test_case.get('user_query', ''),
                    agent_response=test_case.get('agent_response', ''),
                    structured_output=test_case.get('structured_output', {}),
                    tool_calls=test_case.get('tool_calls', []),
                    citations=test_case.get('citations', []),
                    reference_facts=test_case.get('reference_facts')
                )
                
                results.append({
                    "test_case": i + 1,
                    "user_query": test_case.get('user_query', ''),
                    "evaluation": result
                })
                
                total_score += result.overall_score
                if result.passed:
                    passed_count += 1
            
            # Calculate aggregate metrics
            avg_score = total_score / len(test_cases) if test_cases else 0.0
            pass_rate = (passed_count / len(test_cases)) * 100 if test_cases else 0.0
            
            logger.info(f"⚖️ Batch evaluation completed. Avg score: {avg_score:.2f}, Pass rate: {pass_rate:.1f}%")
            
            return {
                "total_cases": len(test_cases),
                "average_score": avg_score,
                "pass_rate": pass_rate,
                "passed_cases": passed_count,
                "failed_cases": len(test_cases) - passed_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Batch evaluation failed: {e}")
            return {
                "error": str(e),
                "total_cases": 0,
                "average_score": 0.0,
                "pass_rate": 0.0
            }
