#!/usr/bin/env python3
"""
Validation service for ML workflow.
Checks if model performance meets deployment thresholds.
"""

import json
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

from config import PERFORMANCE_THRESHOLDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelValidator:
    """Validates model performance against deployment thresholds."""
    
    def __init__(self, thresholds: Optional[Dict] = None):
        self.thresholds = thresholds or PERFORMANCE_THRESHOLDS
        logger.info(f"Initialized validator with thresholds: {self.thresholds}")
    
    def validate_evaluation_results(self, results_path: str) -> Tuple[bool, Dict]:
        """
        Validate evaluation results against performance thresholds.
        
        Args:
            results_path: Path to JSON file containing evaluation results
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
        except FileNotFoundError:
            logger.error(f"Evaluation results file not found: {results_path}")
            return False, {"error": "Results file not found"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in results file: {e}")
            return False, {"error": f"Invalid JSON: {e}"}
        
        validation_details = {
            "results_file": results_path,
            "checks": {},
            "passed": False,
            "summary": ""
        }
        
        # Extract metrics from results
        best_of_n = results.get("Best of N", {})
        full_set = results.get("Full Set", {})
        error_analysis = results.get("Error Analysis", {})
        
        # Check 1: Valid Sample Rate
        best_vsr = best_of_n.get("Valid Sample Rate (%)", 0) / 100.0
        min_vsr = self.thresholds["min_valid_sample_rate"]
        vsr_passed = best_vsr >= min_vsr
        validation_details["checks"]["valid_sample_rate"] = {
            "value": best_vsr,
            "threshold": min_vsr,
            "passed": vsr_passed
        }
        logger.info(f"Valid Sample Rate: {best_vsr:.4f} (threshold: {min_vsr:.4f}) - {'PASS' if vsr_passed else 'FAIL'}")
        
        # Check 2: Mean IOU
        best_mean_iou = best_of_n.get("Mean IOU", 0.0)
        min_mean_iou = self.thresholds["min_mean_iou"]
        mean_iou_passed = best_mean_iou >= min_mean_iou
        validation_details["checks"]["mean_iou"] = {
            "value": best_mean_iou,
            "threshold": min_mean_iou,
            "passed": mean_iou_passed
        }
        logger.info(f"Mean IOU: {best_mean_iou:.4f} (threshold: {min_mean_iou:.4f}) - {'PASS' if mean_iou_passed else 'FAIL'}")
        
        # Check 3: Median IOU
        best_median_iou = best_of_n.get("Median IOU", 0.0)
        min_median_iou = self.thresholds["min_median_iou"]
        median_iou_passed = best_median_iou >= min_median_iou
        validation_details["checks"]["median_iou"] = {
            "value": best_median_iou,
            "threshold": min_median_iou,
            "passed": median_iou_passed
        }
        logger.info(f"Median IOU: {best_median_iou:.4f} (threshold: {min_median_iou:.4f}) - {'PASS' if median_iou_passed else 'FAIL'}")
        
        # Check 4: Failed Generation Rate
        failed_gen_rate = error_analysis.get("Failed Gen (%)", 100.0) / 100.0
        max_failed_gen = self.thresholds["max_failed_generation_rate"]
        failed_gen_passed = failed_gen_rate <= max_failed_gen
        validation_details["checks"]["failed_generation_rate"] = {
            "value": failed_gen_rate,
            "threshold": max_failed_gen,
            "passed": failed_gen_passed
        }
        logger.info(f"Failed Generation Rate: {failed_gen_rate:.4f} (threshold: {max_failed_gen:.4f}) - {'PASS' if failed_gen_passed else 'FAIL'}")
        
        # Overall validation result
        all_passed = all([
            vsr_passed,
            mean_iou_passed,
            median_iou_passed,
            failed_gen_passed
        ])
        
        validation_details["passed"] = all_passed
        
        if all_passed:
            validation_details["summary"] = "✅ All validation checks passed. Model is ready for deployment."
            logger.info("✅ Model validation PASSED - ready for deployment")
        else:
            failed_checks = [k for k, v in validation_details["checks"].items() if not v["passed"]]
            validation_details["summary"] = f"❌ Validation FAILED. Failed checks: {', '.join(failed_checks)}"
            validation_details["failed_checks"] = failed_checks
            logger.warning(f"❌ Model validation FAILED - failed checks: {failed_checks}")
        
        return all_passed, validation_details
    
    def validate_from_dict(self, results: Dict) -> Tuple[bool, Dict]:
        """
        Validate evaluation results from a dictionary (for testing/mocking).
        
        Args:
            results: Dictionary containing evaluation results
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        # Create a temporary file-like validation
        validation_details = {
            "checks": {},
            "passed": False,
            "summary": ""
        }
        
        best_of_n = results.get("Best of N", {})
        error_analysis = results.get("Error Analysis", {})
        
        # Check all thresholds
        best_vsr = best_of_n.get("Valid Sample Rate (%)", 0) / 100.0
        best_mean_iou = best_of_n.get("Mean IOU", 0.0)
        best_median_iou = best_of_n.get("Median IOU", 0.0)
        failed_gen_rate = error_analysis.get("Failed Gen (%)", 100.0) / 100.0
        
        checks = {
            "valid_sample_rate": best_vsr >= self.thresholds["min_valid_sample_rate"],
            "mean_iou": best_mean_iou >= self.thresholds["min_mean_iou"],
            "median_iou": best_median_iou >= self.thresholds["min_median_iou"],
            "failed_generation_rate": failed_gen_rate <= self.thresholds["max_failed_generation_rate"]
        }
        
        validation_details["checks"] = {
            "valid_sample_rate": {
                "value": best_vsr,
                "threshold": self.thresholds["min_valid_sample_rate"],
                "passed": checks["valid_sample_rate"]
            },
            "mean_iou": {
                "value": best_mean_iou,
                "threshold": self.thresholds["min_mean_iou"],
                "passed": checks["mean_iou"]
            },
            "median_iou": {
                "value": best_median_iou,
                "threshold": self.thresholds["min_median_iou"],
                "passed": checks["median_iou"]
            },
            "failed_generation_rate": {
                "value": failed_gen_rate,
                "threshold": self.thresholds["max_failed_generation_rate"],
                "passed": checks["failed_generation_rate"]
            }
        }
        
        all_passed = all(checks.values())
        validation_details["passed"] = all_passed
        
        if all_passed:
            validation_details["summary"] = "✅ All validation checks passed. Model is ready for deployment."
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            validation_details["summary"] = f"❌ Validation FAILED. Failed checks: {', '.join(failed_checks)}"
            validation_details["failed_checks"] = failed_checks
        
        return all_passed, validation_details


if __name__ == "__main__":
    # Test validation with sample results
    validator = ModelValidator()
    
    # Test with passing results
    passing_results = {
        "Best of N": {
            "Valid Sample Rate (%)": 96.97,
            "Mean IOU": 0.563,
            "Median IOU": 0.617,
            "Mean IOU (Adjusted)": 0.546
        },
        "Error Analysis": {
            "Failed Gen (%)": 1.76
        }
    }
    
    is_valid, details = validator.validate_from_dict(passing_results)
    print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
    print(json.dumps(details, indent=2))
    
    # Test with failing results
    failing_results = {
        "Best of N": {
            "Valid Sample Rate (%)": 90.0,  # Below threshold
            "Mean IOU": 0.40,  # Below threshold
            "Median IOU": 0.45,  # Below threshold
            "Mean IOU (Adjusted)": 0.36
        },
        "Error Analysis": {
            "Failed Gen (%)": 10.0  # Above threshold
        }
    }
    
    is_valid, details = validator.validate_from_dict(failing_results)
    print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
    print(json.dumps(details, indent=2))

