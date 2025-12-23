# aggregate/operations.py
from typing import List, Dict
from .api_client import AtScaleAPIClient


class AggregateOperations:
    def __init__(self):
        self.api_client = AtScaleAPIClient()
    
    def unblock_aggregates(self, aggregates_data: List[Dict]) -> List[Dict]:
        """Unblock multiple aggregates - makes two API calls per aggregate"""
        results = []
        for agg_data in aggregates_data:
            try:
                definition_id = agg_data.get("id")
                full_data = agg_data.get("full_data", {})
                
                # Check if aggregate is blocked
                is_blocked = full_data.get("blocked", False)
                latest_instance = full_data.get("latest_instance", {})
                instance_id = latest_instance.get("id")
                
                if not definition_id:
                    results.append({
                        "definition_id": "Unknown",
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": "No definition ID found"
                    })
                    continue
                
                if not instance_id:
                    results.append({
                        "definition_id": definition_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": "No instance ID found (aggregate may not be built)"
                    })
                    continue
                
                # Check if aggregate is already unblocked/active
                if not is_blocked:
                    results.append({
                        "definition_id": definition_id,
                        "instance_id": instance_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "success",
                        "already_unblocked": True,
                        "message": "Aggregate is already active"
                    })
                    continue
                
                # Try to unblock - makes TWO API calls
                result = self.api_client.unblock_aggregate(definition_id, instance_id)
                
                # Check the results
                first_call = result.get("first_call", {})
                second_call = result.get("second_call", {})
                overall_success = result.get("overall_success", False)
                
                if overall_success:
                    # Check which call actually updated the aggregate
                    first_updated = first_call.get("updated")
                    second_updated = second_call.get("updated")
                    
                    if first_updated is True:
                        results.append({
                            "definition_id": definition_id,
                            "instance_id": instance_id,
                            "name": agg_data.get("name", "Unknown"),
                            "status": "success", 
                            "result": result,
                            "updated": True,
                            "message": "Successfully unblocked (first call updated)",
                            "details": {
                                "first_call": first_call,
                                "second_call": second_call
                            }
                        })
                    elif second_updated is False:
                        # Even though updated: false, the call succeeded
                        results.append({
                            "definition_id": definition_id,
                            "instance_id": instance_id,
                            "name": agg_data.get("name", "Unknown"),
                            "status": "success",
                            "result": result,
                            "updated": False,
                            "message": "Unblock completed (second call confirmed)",
                            "details": {
                                "first_call": first_call,
                                "second_call": second_call
                            }
                        })
                    else:
                        # Both calls succeeded but no update flag
                        results.append({
                            "definition_id": definition_id,
                            "instance_id": instance_id,
                            "name": agg_data.get("name", "Unknown"),
                            "status": "success",
                            "result": result,
                            "message": "Unblock operation completed",
                            "details": {
                                "first_call": first_call,
                                "second_call": second_call
                            }
                        })
                else:
                    # Check for errors
                    first_error = first_call.get("error")
                    second_error = second_call.get("error")
                    
                    error_msg = ""
                    if first_error and second_error:
                        error_msg = f"Both calls failed: 1) {first_error}, 2) {second_error}"
                    elif first_error:
                        error_msg = f"First call failed: {first_error}"
                    elif second_error:
                        error_msg = f"Second call failed: {second_error}"
                    else:
                        error_msg = "Unknown error in unblock operation"
                    
                    results.append({
                        "definition_id": definition_id,
                        "instance_id": instance_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": error_msg,
                        "details": result
                    })
                        
            except Exception as e:
                results.append({
                    "definition_id": agg_data.get("id", "Unknown"),
                    "name": agg_data.get("name", "Unknown"),
                    "status": "error", 
                    "error": str(e)
                })
        return results
    
    def block_aggregates(self, aggregates_data: List[Dict]) -> List[Dict]:
        """Block multiple aggregates"""
        results = []
        for agg_data in aggregates_data:
            try:
                definition_id = agg_data.get("id")
                full_data = agg_data.get("full_data", {})
                latest_instance = full_data.get("latest_instance", {})
                instance_id = latest_instance.get("id")
                
                # Check if aggregate is already blocked
                is_blocked = full_data.get("blocked", False)
                
                if not definition_id:
                    results.append({
                        "definition_id": "Unknown",
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": "No definition ID found"
                    })
                    continue
                
                if not instance_id:
                    results.append({
                        "definition_id": definition_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": "No instance ID found (aggregate may not be built)"
                    })
                    continue
                
                # Check if aggregate is already blocked
                if is_blocked:
                    results.append({
                        "definition_id": definition_id,
                        "instance_id": instance_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "success",
                        "already_blocked": True,
                        "message": "Aggregate is already blocked"
                    })
                    continue
                
                # Try to block
                result = self.api_client.block_aggregate(definition_id, instance_id)
                
                # Check the result
                if "error" in result:
                    results.append({
                        "definition_id": definition_id,
                        "instance_id": instance_id,
                        "name": agg_data.get("name", "Unknown"),
                        "status": "error", 
                        "error": result["error"]
                    })
                else:
                    deleted = result.get("deleted", False)
                    
                    if deleted:
                        results.append({
                            "definition_id": definition_id,
                            "instance_id": instance_id,
                            "name": agg_data.get("name", "Unknown"),
                            "status": "success", 
                            "result": result,
                            "deleted": True,
                            "message": "Successfully blocked"
                        })
                    else:
                        results.append({
                            "definition_id": definition_id,
                            "instance_id": instance_id,
                            "name": agg_data.get("name", "Unknown"),
                            "status": "success",
                            "result": result,
                            "deleted": False,
                            "message": "Block operation completed"
                        })
                    
            except Exception as e:
                results.append({
                    "definition_id": agg_data.get("id", "Unknown"),
                    "name": agg_data.get("name", "Unknown"),
                    "status": "error", 
                    "error": str(e)
                })
        return results