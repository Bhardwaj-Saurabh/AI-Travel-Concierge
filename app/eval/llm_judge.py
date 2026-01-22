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
    corrections: Optional[Dict[str, Any]] = None
    tool_suggestions: Optional[List[Dict[str, str]]] = None
    debugging_insights: Optional[Dict[str, Any]] = None

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

    async def generate_corrections(
        self,
        user_query: str,
        agent_response: str,
        structured_output: Dict[str, Any],
        evaluation_result: EvaluationResult
    ) -> Dict[str, Any]:
        """
        Generate specific corrections for issues identified in evaluation.

        Args:
            user_query: Original user query
            agent_response: Agent's response that needs correction
            structured_output: Current structured output
            evaluation_result: Results from evaluate_response()

        Returns:
            Dictionary containing corrected versions and explanations
        """
        try:
            logger.info("🔧 Generating corrections for agent response")

            # Create correction prompt
            correction_prompt = f"""
            You are an expert AI debugger helping to correct a Travel Concierge agent's response.

            USER QUERY:
            {user_query}

            AGENT'S CURRENT RESPONSE:
            {agent_response}

            CURRENT STRUCTURED OUTPUT:
            {json.dumps(structured_output, indent=2)}

            EVALUATION SCORES:
            - Overall Score: {evaluation_result.overall_score}/5.0
            - Criteria Scores: {json.dumps(evaluation_result.criteria_scores, indent=2)}

            IDENTIFIED ISSUES:
            {evaluation_result.reasoning}

            RECOMMENDATIONS:
            {json.dumps(evaluation_result.recommendations, indent=2)}

            Please provide specific corrections:
            1. Corrected natural language response
            2. Corrected structured output (JSON)
            3. Explanation of what was wrong and how it was fixed
            4. Line-by-line changes needed

            Respond in JSON format:
            {{
                "corrected_response": "The improved natural language response...",
                "corrected_structured_output": {{...}},
                "issues_fixed": [
                    {{
                        "issue": "Description of what was wrong",
                        "fix": "Description of the correction applied",
                        "impact": "How this improves the response"
                    }}
                ],
                "code_changes": [
                    {{
                        "location": "Where in the code this should be fixed",
                        "current": "Current problematic code/logic",
                        "corrected": "Corrected code/logic"
                    }}
                ]
            }}
            """

            # Get LLM corrections
            chat_service = self.kernel.get_service(type="ChatCompletionService")
            response = await chat_service.get_chat_message_contents(
                chat_history=ChatHistory.from_messages([("user", correction_prompt)]),
                settings={"temperature": 0.2, "max_tokens": 2000}
            )

            # Parse corrections
            corrections_text = response[0].content.strip()
            corrections = self._parse_json_response(corrections_text)

            logger.info("🔧 Corrections generated successfully")
            return corrections

        except Exception as e:
            logger.error(f"❌ Failed to generate corrections: {e}")
            return {
                "error": str(e),
                "corrected_response": agent_response,
                "issues_fixed": []
            }

    async def suggest_tools(
        self,
        user_query: str,
        tool_calls_made: List[Dict[str, Any]],
        evaluation_result: EvaluationResult
    ) -> List[Dict[str, str]]:
        """
        Suggest which tools should have been used or additional tools needed.

        Args:
            user_query: Original user query
            tool_calls_made: List of tools actually called
            evaluation_result: Evaluation results

        Returns:
            List of tool suggestions with rationale
        """
        try:
            logger.info("🔍 Generating tool usage suggestions")

            tools_called = [call.get('name', 'unknown') for call in tool_calls_made]

            suggestion_prompt = f"""
            You are an expert at tool orchestration for a Travel Concierge agent.

            AVAILABLE TOOLS:
            1. get_weather(lat, lon) - Get 7-day weather forecast
            2. convert_fx(amount, base, target) - Convert currency
            3. web_search(query, max_results) - Search for restaurants/attractions
            4. recommend_card(mcc, amount, country) - Recommend credit card
            5. get_card_recommendation(mcc, country) - RAG-based card knowledge
            6. check_availability(start_date, end_date, flexible_days) - Check calendar
            7. schedule_travel_event(title, start_date, end_date, destination, notes) - Schedule trip
            8. translate_text(text, target_language, source_language) - Translate text
            9. get_travel_phrases(target_language, category) - Get phrasebook
            10. detect_language(text) - Detect text language

            USER QUERY:
            {user_query}

            TOOLS ACTUALLY CALLED:
            {json.dumps(tools_called, indent=2)}

            EVALUATION FEEDBACK:
            Tool Usage Score: {evaluation_result.criteria_scores.get('tool_usage', 0)}/5.0
            Reasoning: {evaluation_result.reasoning}

            Analyze the tool usage and provide:
            1. Which tools were appropriately used
            2. Which tools should have been used but weren't
            3. Which tools were used unnecessarily
            4. Optimal tool orchestration order

            Respond in JSON format:
            {{
                "appropriate_tools": ["tool1", "tool2"],
                "missing_tools": [
                    {{
                        "tool": "tool_name",
                        "reason": "Why this tool should be called",
                        "parameters": {{"param": "suggested value"}},
                        "priority": "high/medium/low"
                    }}
                ],
                "unnecessary_tools": ["tool3"],
                "optimal_orchestration": [
                    {{
                        "step": 1,
                        "tool": "tool_name",
                        "rationale": "Why this order"
                    }}
                ]
            }}
            """

            # Get LLM suggestions
            chat_service = self.kernel.get_service(type="ChatCompletionService")
            response = await chat_service.get_chat_message_contents(
                chat_history=ChatHistory.from_messages([("user", suggestion_prompt)]),
                settings={"temperature": 0.3, "max_tokens": 1500}
            )

            # Parse suggestions
            suggestions_text = response[0].content.strip()
            suggestions = self._parse_json_response(suggestions_text)

            logger.info(f"🔍 Tool suggestions generated: {len(suggestions.get('missing_tools', []))} missing tools identified")
            return suggestions

        except Exception as e:
            logger.error(f"❌ Failed to generate tool suggestions: {e}")
            return {"error": str(e), "missing_tools": []}

    async def debug_agent_workflow(
        self,
        user_query: str,
        agent_response: str,
        state_transitions: List[Dict[str, str]],
        tool_calls: List[Dict[str, Any]],
        evaluation_result: EvaluationResult
    ) -> Dict[str, Any]:
        """
        Provide debugging insights about the agent's workflow and decision-making.

        Args:
            user_query: Original user query
            agent_response: Agent's response
            state_transitions: List of state transitions that occurred
            tool_calls: Tools called during execution
            evaluation_result: Evaluation results

        Returns:
            Debugging insights and workflow analysis
        """
        try:
            logger.info("🐛 Generating debugging insights")

            debug_prompt = f"""
            You are an expert AI debugger analyzing a Travel Concierge agent's workflow.

            USER QUERY:
            {user_query}

            AGENT RESPONSE:
            {agent_response}

            STATE TRANSITIONS:
            {json.dumps(state_transitions, indent=2)}

            TOOL CALLS:
            {json.dumps(tool_calls, indent=2)}

            EVALUATION RESULTS:
            Overall Score: {evaluation_result.overall_score}/5.0
            Reasoning: {evaluation_result.reasoning}

            Analyze the agent's execution and provide debugging insights:
            1. Where did the agent go wrong in its workflow?
            2. Which state transition was problematic?
            3. Which tool call failed or was incorrect?
            4. What decision-making errors occurred?
            5. How can the system prompt be improved?
            6. What error handling is missing?

            Respond in JSON format:
            {{
                "workflow_issues": [
                    {{
                        "stage": "State or phase where issue occurred",
                        "issue": "What went wrong",
                        "root_cause": "Why it went wrong",
                        "fix": "How to fix it"
                    }}
                ],
                "tool_execution_problems": [
                    {{
                        "tool": "tool_name",
                        "problem": "What was wrong with this tool call",
                        "expected": "What should have happened",
                        "actual": "What actually happened"
                    }}
                ],
                "prompt_improvements": [
                    {{
                        "section": "Which part of system prompt",
                        "current": "Current problematic instruction",
                        "improved": "Improved instruction",
                        "rationale": "Why this is better"
                    }}
                ],
                "error_handling_gaps": [
                    "Missing error handling for scenario X",
                    "Need validation for parameter Y"
                ],
                "overall_diagnosis": "High-level summary of what needs to be fixed"
            }}
            """

            # Get LLM debugging insights
            chat_service = self.kernel.get_service(type="ChatCompletionService")
            response = await chat_service.get_chat_message_contents(
                chat_history=ChatHistory.from_messages([("user", debug_prompt)]),
                settings={"temperature": 0.2, "max_tokens": 2000}
            )

            # Parse debugging insights
            debug_text = response[0].content.strip()
            debug_insights = self._parse_json_response(debug_text)

            logger.info("🐛 Debugging insights generated successfully")
            return debug_insights

        except Exception as e:
            logger.error(f"❌ Failed to generate debugging insights: {e}")
            return {
                "error": str(e),
                "workflow_issues": [],
                "overall_diagnosis": "Unable to generate debugging insights"
            }

    async def evaluate_with_enhancements(
        self,
        user_query: str,
        agent_response: str,
        structured_output: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        citations: List[str],
        state_transitions: List[Dict[str, str]] = None,
        reference_facts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Complete evaluation with corrections, tool suggestions, and debugging insights.

        This is the enhanced evaluation that provides not just scores,
        but also actionable improvements.

        Args:
            user_query: Original user query
            agent_response: Agent's response
            structured_output: Structured output
            tool_calls: List of tool calls made
            citations: List of citations provided
            state_transitions: List of state transitions
            reference_facts: Optional reference facts

        Returns:
            Comprehensive evaluation with all enhancements
        """
        try:
            logger.info("🚀 Starting enhanced evaluation with corrections and suggestions")

            # Step 1: Basic evaluation
            evaluation_result = await self.evaluate_response(
                user_query, agent_response, structured_output,
                tool_calls, citations, reference_facts
            )

            # Step 2: Generate corrections if score is below threshold
            corrections = None
            if evaluation_result.overall_score < 4.0:
                corrections = await self.generate_corrections(
                    user_query, agent_response, structured_output, evaluation_result
                )

            # Step 3: Suggest tools if tool usage score is low
            tool_suggestions = None
            if evaluation_result.criteria_scores.get('tool_usage', 5.0) < 4.0:
                tool_suggestions = await self.suggest_tools(
                    user_query, tool_calls, evaluation_result
                )

            # Step 4: Generate debugging insights if overall score is low
            debugging_insights = None
            if evaluation_result.overall_score < 3.5 and state_transitions:
                debugging_insights = await self.debug_agent_workflow(
                    user_query, agent_response, state_transitions,
                    tool_calls, evaluation_result
                )

            # Combine all results
            enhanced_result = {
                "evaluation": {
                    "overall_score": evaluation_result.overall_score,
                    "criteria_scores": evaluation_result.criteria_scores,
                    "reasoning": evaluation_result.reasoning,
                    "recommendations": evaluation_result.recommendations,
                    "passed": evaluation_result.passed
                },
                "corrections": corrections,
                "tool_suggestions": tool_suggestions,
                "debugging_insights": debugging_insights,
                "summary": {
                    "needs_correction": corrections is not None,
                    "needs_tool_optimization": tool_suggestions is not None,
                    "needs_debugging": debugging_insights is not None,
                    "ready_for_production": evaluation_result.overall_score >= 4.5
                }
            }

            logger.info(f"🚀 Enhanced evaluation completed. Score: {evaluation_result.overall_score:.2f}/5.0")
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ Enhanced evaluation failed: {e}")
            return {
                "error": str(e),
                "evaluation": {
                    "overall_score": 0.0,
                    "passed": False
                }
            }

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            # Remove markdown code blocks if present
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            # Find JSON object
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_text = text[start_idx:end_idx]
                return json.loads(json_text)
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {}
