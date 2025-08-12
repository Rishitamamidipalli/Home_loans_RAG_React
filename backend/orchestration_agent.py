from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import START, END, StateGraph
from agent.document_validator_agent import DocumentValidatorAgent
from agent.credit_score_agent import CreditScoreAgent
from agent.property_valuation_agent import PropertyValuationAgent
from agent.eligibility_agent import EligibilityAgent, eligibility_node
from agent.loan_recommender_agent import loan_recommender_node
from graphviz import Digraph

class WorkflowState(TypedDict):
    applicant_data: Dict[str, Any]
    document_paths: Dict[str, str]
    credit_score_result: Dict[str, Any]
    document_validation_result: Annotated[Dict[str, Any], "doc_validator"]
    property_valuation_result: Annotated[Dict[str, Any], "prop_validator"]
    eligibility_result: Annotated[Dict[str, Any], "eligibility_checker"]
    approval_recommendation: Annotated[Dict[str, Any], "recommender"]
    workflow_status: Annotated[str, "finalizer"]
    doc_errors: Annotated[List[str], "doc_validator"]
    prop_errors: Annotated[List[str], "prop_validator"]
    elig_errors: Annotated[List[str], "eligibility_checker"]
    rec_errors: Annotated[List[str], "recommender"]

class HomeLoanOrchestrator:
    def __init__(self):
        self.graph = self._build_workflow()
        self.app = self.graph.compile()
        self.document_validator = DocumentValidatorAgent()
        self.credit_score_agent = CreditScoreAgent()
        self.property_valuation_agent = PropertyValuationAgent()
        self.eligibility_agent = EligibilityAgent()
        self.progress = {
            "document_validator": False,
            "credit_score_agent": False,
            "property_valuation_agent": False,
            "eligibility_agent": False,
            "approval_recommender": False,
            "finalize_status": False
        }
        self.workflow_callback = None  # Callback for UI updates
        
    def _update_progress(self, node_name: str):
        """Update progress for a specific node"""
        self.progress[node_name] = True
    
    def get_progress(self):
        """Return current progress status"""
        return self.progress
    
    def reset_progress(self):
        """Reset all progress flags"""
        self.progress = {
            "document_validator": False,
            "credit_score_agent": False,
            "property_valuation_agent": False,
            "eligibility_agent": False,
            "approval_recommender": False,
            "finalize_status": False
        }

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)

        workflow.add_node("document_validator", self._run_document_validator)
        workflow.add_node("credit_score_agent", self._run_credit_score_agent)
        workflow.add_node("property_valuation_agent", self._run_property_valuation_agent)
        workflow.add_node("eligibility_agent", self._run_eligibility_agent)
        workflow.add_node("approval_recommender", self._run_approval_recommender)
        workflow.add_node("finalize_status", self._finalize_workflow_status)

        workflow.add_edge(START, "document_validator")
        workflow.add_edge(START, "credit_score_agent")
        workflow.add_edge(START, "property_valuation_agent")
        
        workflow.add_conditional_edges(
            "document_validator",
            self._should_proceed_to_eligibility,
            {"continue": "eligibility_agent", "wait": "document_validator"}
        )

        workflow.add_conditional_edges(
            "credit_score_agent",
            self._should_proceed_to_eligibility,
            {"continue": "eligibility_agent", "wait": "credit_score_agent"}
        )
        
        workflow.add_conditional_edges(
            "property_valuation_agent",
            self._should_proceed_to_eligibility,
            {"continue": "eligibility_agent", "wait": "property_valuation_agent"}
        )
        
        workflow.add_edge("eligibility_agent", "approval_recommender")
        workflow.add_edge("approval_recommender", "finalize_status")
        workflow.add_edge("finalize_status", END)
        
        return workflow

    def _run_document_validator(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            documents = [{"type": t, "path": p} for t, p in state["document_paths"].items()]
            result = self.document_validator.validate_documents(
                {"documents": documents, "details": state["applicant_data"]}
            )
            
            if "applicant_data" in state:
                app_name = state["applicant_data"].get("applicant_name", "").upper()
                doc_name = result.get("data", {}).get("applicant_name", "").upper()
                if app_name and doc_name and app_name != doc_name:
                    result.setdefault("validation_report", {}).setdefault("checks", []).append({
                        "check": "Name Match",
                        "status": "Failure",
                        "reason": f"Document name '{doc_name}' ≠ application name '{app_name}'"
                    })
                    result["validation_report"]["overall_status"] = "Failure"
            
            self._update_progress("document_validator")
            return {
                "document_validation_result": result,
                "doc_errors": []
            }
        except Exception as e:
            self._update_progress("document_validator")
            return {
                "document_validation_result": {"status": "error", "message": str(e)},
                "doc_errors": [f"Document validation error: {str(e)}"]
            }


    def _run_credit_score_agent(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            result = self.credit_score_agent.get_credit_score(state["applicant_data"])
            self._update_progress("credit_score_agent")
            return {
                "credit_score_result": result,
                "credit_errors": []
            }
        except Exception as e:
            self._update_progress("credit_score_agent")
            return {
                "credit_score_result": {"status": "error", "message": str(e)},
                "credit_errors": [f"Credit score error: {str(e)}"]
            }

    def _run_property_valuation_agent(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            if "property_details" not in state["applicant_data"]:
                raise ValueError("Missing property details")
                
            result = self.property_valuation_agent.predict(
                state["applicant_data"]["property_details"]
            )
            self._update_progress("property_valuation_agent")
            return {
                "property_valuation_result": result,
                "prop_errors": []
            }
        except Exception as e:
            self._update_progress("property_valuation_agent")
            return {
                "property_valuation_result": {"status": "error", "message": str(e)},
                "prop_errors": [f"Property valuation error: {str(e)}"]
            }

    def _run_eligibility_agent(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            node_state = {
                "applicant_data": state["applicant_data"],
                "property_valuation_result": state["property_valuation_result"],
                "document_validation_result": state["document_validation_result"],
                "credit_score_result": state["credit_score_result"]
            }
            updated_state = eligibility_node(node_state)
            self._update_progress("eligibility_agent")
            return {
                "eligibility_result": {
                    "is_eligible": updated_state.get("eligibility_result"),
                    "checks": updated_state.get("eligibility_checks"),
                    "applicant_name": updated_state.get("applicant_name")
                },
                "elig_errors": []
            }
        except Exception as e:
            self._update_progress("eligibility_agent")
            return {
                "eligibility_result": {"status": "error", "message": str(e)},
                "elig_errors": [f"Eligibility check error: {str(e)}"]
            }
    def _run_approval_recommender(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            node_state = {
                "applicant_data": state["applicant_data"],
                "eligibility_result": state["eligibility_result"],
                "property_valuation_result": state["property_valuation_result"],
                "credit_score_result": state["credit_score_result"]
            }
            updated_state = loan_recommender_node(node_state)
            self._update_progress("approval_recommender")
            # Return both text and structured table data
            if "loan_recommendation" in updated_state:
                return {
                    "approval_recommendation": {
                        "recommendation": updated_state["loan_recommendation"]["text"],
                        "table": updated_state["loan_recommendation"]["table"],
                        "status": "success"
                    },
                    "rec_errors": []
                }
            elif "loan_recommendation_text" in updated_state:  # Backward compatibility
                return {
                    "approval_recommendation": {
                        "recommendation": updated_state["loan_recommendation_text"],
                        "status": "success"
                    },
                    "rec_errors": []
                }
            
            error_msg = updated_state.get("error", "Unknown recommendation error")
            return {
                "approval_recommendation": {"status": "error", "message": error_msg},
                "rec_errors": [f"Approval recommendation error: {error_msg}"]
            }
        except Exception as e:
            self._update_progress("approval_recommender")
            return {
                "approval_recommendation": {"status": "error", "message": str(e)},
                "rec_errors": [f"Approval recommendation error: {str(e)}"]
            }

    def _finalize_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """Consolidate final status with single writer"""
        all_errors = (
            state.get("doc_errors", []) +
            state.get("credit_errors", []) +
            state.get("prop_errors", []) +
            state.get("elig_errors", []) +
            state.get("rec_errors", [])
        )
        
        status = "success"
        if any([
            state["document_validation_result"].get("status") == "error",
            state["credit_score_result"].get("status") == "error",
            state["property_valuation_result"].get("status") == "error",
            state["eligibility_result"].get("status") == "error",
            state["approval_recommendation"].get("status") == "error"
        ]):
            status = "failed"
        elif all_errors:
            status = "partial_success"
            
        return {
            "workflow_status": status,
            "doc_errors": [],
            "prop_errors": [],
            "elig_errors": [],
            "rec_errors": [],
            "errors": all_errors  # Only finalizer writes to this
        }

    def _should_proceed_to_eligibility(self, state: WorkflowState) -> str:
        """Determine if workflow can proceed to eligibility check"""
        # Check if all prerequisite nodes are complete
        if (state.get("document_validation_result") and 
            state.get("credit_score_result") and 
            state.get("property_valuation_result")):
            return "continue"
        return "wait"
    
    def run_workflow(self, applicant_data: Dict[str, Any], document_paths: Dict[str, str]) -> Dict[str, Any]:
        """Execute the complete workflow with separated inputs"""
        initial_state = WorkflowState(
            applicant_data=applicant_data,
            document_paths=document_paths,
            document_validation_result={},
            credit_score_result={},
            property_valuation_result={},
            eligibility_result={},
            approval_recommendation={},
            workflow_status="started",
            doc_errors=[],
            prop_errors=[],
            elig_errors=[],
            rec_errors=[]
        )
        
        try:
            final_state = self.app.invoke(initial_state)
            
            return {
                "status": final_state["workflow_status"],
                "results": {
                    "document_validation": final_state["document_validation_result"],
                    "credit_score": final_state["credit_score_result"],
                    "property_valuation": final_state["property_valuation_result"],
                    "eligibility": final_state["eligibility_result"],
                    "approval_recommendation": final_state["approval_recommendation"]
                },
                "errors": final_state.get("errors", [])
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "errors": [str(e)]
            }