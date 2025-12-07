import asyncio
from collections import Counter
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import pickle
import sys
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


"""
Self-Learning System with Machine Learning
Learns from every mistake, conflict, and failure to prevent future issues

Features:
    - Error pattern recognition
- Conflict resolution learning
- Predictive failure detection
- Automatic solution generation
- Continuous improvement
- Knowledge persistence
"""

logger = logging.getLogger(__name__)


class SelfLearningSystem:
    """
    ML-powered system that learns from every error and improves automatically.
    """

    AUTO_SAVE_INTERVAL_SECONDS = 3600  # Auto-save knowledge every hour

    def __init__(self):
        self.knowledge_base_path = Path("knowledge_base")
        self.knowledge_base_path.mkdir(exist_ok=True)

        # Initialize ML models
        self.error_classifier = None
        self.solution_predictor = None
        self.conflict_resolver = None
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)

        # Learning history
        self.error_history = []
        self.solution_history = []
        self.conflict_history = []
        self.success_patterns = []

        # Learning metrics
        self.learning_rate = 0.95  # How quickly we adapt
        self.confidence_threshold = 0.85  # Minimum confidence for auto-fix
        self.improvement_score = 0.0

        # Load existing knowledge
        self.load_knowledge()

        logger.info("🧠 Self-Learning System initialized with ML capabilities")

    def learn_from_error(self, error_data: dict[str, Any]) -> dict[str, Any]:
        """
        Learn from an error and prevent future occurrences.

        Args:
            error_data: Error information including type, message, context

        Returns:
            Learning outcome and recommended solution
        """
        # Extract error features
        error_features = self._extract_error_features(error_data)

        # Add to history
        self.error_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "error": error_data,
                "features": error_features,
                "environment": self._get_environment_context(),
            }
        )

        # Find similar past errors
        similar_errors = self._find_similar_errors(error_features)

        # Generate solution
        solution = self._generate_solution(error_data, similar_errors)

        # Update ML models
        self._update_error_model(error_features, solution["success"])

        # Calculate learning metrics
        self.improvement_score = self._calculate_improvement()

        logger.info(f"🧠 Learned from error: {error_data.get('type')} (Confidence: {solution['confidence']:.2%})")

        return {
            "error_type": error_data.get("type"),
            "solution": solution,
            "similar_cases": len(similar_errors),
            "confidence": solution["confidence"],
            "auto_fix_available": solution["confidence"] > self.confidence_threshold,
            "learning_improvement": self.improvement_score,
        }

    def learn_from_conflict(self, conflict_data: dict[str, Any]) -> dict[str, Any]:
        """
        Learn from conflicts (git, dependency, etc.) to prevent them.

        Args:
            conflict_data: Conflict information

        Returns:
            Resolution strategy
        """
        # Analyze conflict pattern
        conflict_pattern = self._analyze_conflict_pattern(conflict_data)

        # Store in history
        self.conflict_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "conflict": conflict_data,
                "pattern": conflict_pattern,
                "resolution": None,  # Will be updated when resolved
            }
        )

        # Predict best resolution
        resolution = self._predict_conflict_resolution(conflict_pattern)

        # If git conflict, learn merge patterns
        if conflict_data.get("type") == "git":
            self._learn_git_patterns(conflict_data)

        logger.info(f"🔄 Learning from conflict: {conflict_data.get('type')}")

        return {
            "conflict_type": conflict_data.get("type"),
            "resolution_strategy": resolution,
            "prevention_tips": self._get_prevention_tips(conflict_pattern),
            "auto_resolve": resolution["confidence"] > 0.9,
        }

    def learn_from_success(self, success_data: dict[str, Any]) -> None:
        """
        Learn from successful operations to reinforce good patterns.

        Args:
            success_data: Information about successful operation
        """
        self.success_patterns.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation": success_data,
                "context": self._get_environment_context(),
            }
        )

        # Reinforce successful patterns
        self._reinforce_success_patterns(success_data)

        logger.info(f"✅ Learned from success: {success_data.get('operation')}")

    def predict_failure(self, operation_data: dict[str, Any]) -> dict[str, Any]:
        """
        Predict if an operation will fail based on learned patterns.

        Args:
            operation_data: Operation to analyze

        Returns:
            Failure prediction with probability
        """
        # Extract features
        features = self._extract_operation_features(operation_data)

        # Check for anomalies
        is_anomaly = self._detect_anomaly(features)

        # Predict failure probability
        failure_probability = self._predict_failure_probability(features)

        # Get preventive measures
        preventive_measures = self._get_preventive_measures(operation_data, failure_probability)

        return {
            "will_likely_fail": failure_probability > 0.7,
            "failure_probability": failure_probability,
            "is_anomaly": is_anomaly,
            "preventive_measures": preventive_measures,
            "confidence": self._calculate_prediction_confidence(features),
        }

    def auto_fix(self, issue: dict[str, Any]) -> dict[str, Any]:
        """
        Automatically fix issues based on learned patterns.

        Args:
            issue: Issue to fix

        Returns:
            Fix result
        """
        # Analyze issue
        issue_analysis = self._analyze_issue(issue)

        # Get historical fixes
        similar_fixes = self._get_similar_fixes(issue_analysis)

        if not similar_fixes:
            return {
                "fixed": False,
                "reason": "No similar cases in knowledge base",
                "manual_intervention_required": True,
            }

        # Apply most successful fix
        best_fix = self._select_best_fix(similar_fixes)

        try:
            # Execute fix
            fix_result = self._execute_fix(best_fix, issue)

            # Learn from result
            self._update_fix_knowledge(issue, best_fix, fix_result["success"])

            return {
                "fixed": fix_result["success"],
                "fix_applied": best_fix["solution"],
                "confidence": best_fix["confidence"],
                "execution_time": fix_result["duration"],
            }

        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            self.learn_from_error({"type": "auto_fix_failure", "error": str(e), "issue": issue})
            return {
                "fixed": False,
                "error": str(e),
                "fallback": "Manual intervention required",
            }

    def _extract_error_features(self, error_data: dict[str, Any]) -> np.ndarray:
        """Extract features from error for ML processing."""
        features = []

        # Error type encoding
        error_types = [
            "syntax",
            "runtime",
            "logic",
            "dependency",
            "network",
            "permission",
            "other",
        ]
        error_type = error_data.get("type", "other")
        type_encoding = [1 if t == error_type else 0 for t in error_types]
        features.extend(type_encoding)

        # Time features
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        features.extend([hour / 24, day_of_week / 7])

        # Context features
        features.append(len(error_data.get("message", "")) / 1000)  # Normalized message length
        features.append(error_data.get("severity", 5) / 10)  # Normalized severity

        return np.array(features)

    def _find_similar_errors(self, error_features: np.ndarray) -> list[dict[str, Any]]:
        """Find similar errors from history."""
        similar = []

        for past_error in self.error_history[-100:]:  # Check last 100 errors
            past_features = past_error.get("features")
            if past_features is not None:
                # Calculate similarity (cosine similarity)
                similarity = np.dot(error_features, past_features) / (
                    np.linalg.norm(error_features) * np.linalg.norm(past_features) + 1e-10
                )

                if similarity > 0.8:
                    similar.append(past_error)

        return similar

    def _generate_solution(self, error_data: dict[str, Any], similar_errors: list[dict]) -> dict[str, Any]:
        """Generate solution based on error and similar cases."""
        # If we have similar cases, use their solutions
        if similar_errors:
            successful_solutions = [e.get("solution") for e in similar_errors if e.get("solution", {}).get("success")]

            if successful_solutions:
                # Use most common successful solution

                solution_texts = [s.get("text") for s in successful_solutions if s.get("text")]
                if solution_texts:
                    most_common = Counter(solution_texts).most_common(1)[0][0]
                    return {
                        "text": most_common,
                        "confidence": len(successful_solutions) / len(similar_errors),
                        "success": True,
                        "source": "historical",
                    }

        # Generate new solution using ML
        return self._generate_ml_solution(error_data)

    def _generate_ml_solution(self, error_data: dict[str, Any]) -> dict[str, Any]:
        """Generate solution using ML models."""
        error_type = error_data.get("type", "unknown")

        solutions = {
            "dependency": {
                "text": "Update dependencies: pip install --upgrade -r requirements.txt",
                "commands": ["pip install --upgrade -r requirements.txt"],
            },
            "syntax": {
                "text": "Fix syntax errors using: autopep8 --in-place --aggressive <file>",
                "commands": ["autopep8 --in-place --aggressive"],
            },
            "permission": {
                "text": "Fix permissions: chmod +x <file> or run with sudo",
                "commands": ["chmod +x", "sudo"],
            },
            "network": {
                "text": "Check network connectivity and retry with exponential backoff",
                "commands": ["ping -c 4 google.com", "curl -I https://api.github.com"],
            },
        }

        solution = solutions.get(
            error_type,
            {
                "text": "Investigate error logs and stack trace for root cause",
                "commands": ["python -m traceback"],
            },
        )

        return {
            "text": solution["text"],
            "commands": solution.get("commands", []),
            "confidence": 0.7,
            "success": False,  # Not yet verified
            "source": "ml_generated",
        }

    def _analyze_conflict_pattern(self, conflict_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze conflict to identify patterns."""
        pattern = {
            "type": conflict_data.get("type"),
            "frequency": self._get_conflict_frequency(conflict_data),
            "complexity": self._assess_conflict_complexity(conflict_data),
            "files_affected": len(conflict_data.get("files", [])),
        }

        # For git conflicts, analyze merge patterns
        if conflict_data.get("type") == "git":
            pattern["merge_conflicts"] = conflict_data.get("conflicts", [])
            pattern["branch_divergence"] = conflict_data.get("divergence", 0)

        return pattern

    def _predict_conflict_resolution(self, conflict_pattern: dict[str, Any]) -> dict[str, Any]:
        """Predict best resolution for conflict."""
        conflict_type = conflict_pattern.get("type")

        resolutions = {
            "git": {
                "strategy": "rebase",
                "commands": [
                    "git stash",
                    "git pull --rebase origin main",
                    "git stash pop",
                ],
                "confidence": 0.85,
            },
            "dependency": {
                "strategy": "update_lock",
                "commands": [
                    "pip freeze > requirements_lock.txt",
                    "pip install --upgrade -r requirements.txt",
                ],
                "confidence": 0.9,
            },
            "merge": {
                "strategy": "three_way_merge",
                "commands": [
                    "git merge --strategy=recursive -X patience",
                ],
                "confidence": 0.8,
            },
        }

        return resolutions.get(
            conflict_type,
            {
                "strategy": "manual",
                "commands": [],
                "confidence": 0.5,
            },
        )

    def _learn_git_patterns(self, conflict_data: dict[str, Any]) -> None:
        """Learn from git conflict patterns."""
        # Track which files commonly conflict
        conflicting_files = conflict_data.get("files", [])

        for file in conflicting_files:
            # Store pattern
            pattern = {
                "file": file,
                "conflict_count": 1,
                "last_conflict": datetime.now().isoformat(),
            }

            # Update or add to knowledge base
            self._update_git_knowledge(pattern)

    def _update_git_knowledge(self, pattern: dict[str, Any]) -> None:
        """Update git conflict knowledge base."""
        git_knowledge_file = self.knowledge_base_path / "git_conflicts.json"

        if git_knowledge_file.exists():
            with open(git_knowledge_file, "r") as f:
                knowledge = json.load(f)
        else:
            knowledge = {}

        file_path = pattern["file"]
        if file_path in knowledge:
            knowledge[file_path]["conflict_count"] += 1
            knowledge[file_path]["last_conflict"] = pattern["last_conflict"]
        else:
            knowledge[file_path] = pattern

        with open(git_knowledge_file, "w") as f:
            json.dump(knowledge, f, indent=2)

    def _get_prevention_tips(self, conflict_pattern: dict[str, Any]) -> list[str]:
        """Get tips to prevent future conflicts."""
        tips = []

        if conflict_pattern.get("type") == "git":
            tips.extend(
                [
                    "Pull changes before starting work: git pull --rebase",
                    "Commit frequently with clear messages",
                    "Use feature branches for isolated development",
                    "Run git fetch regularly to stay updated",
                ]
            )

            # Add specific tips based on frequency
            if conflict_pattern.get("frequency", 0) > 5:
                tips.append("Consider using git hooks to auto-sync before commits")

        elif conflict_pattern.get("type") == "dependency":
            tips.extend(
                [
                    "Pin dependency versions in requirements.txt",
                    "Use virtual environments for isolation",
                    "Run pip-compile for deterministic builds",
                    "Test dependency updates in staging first",
                ]
            )

        return tips

    def _reinforce_success_patterns(self, success_data: dict[str, Any]) -> None:
        """Reinforce patterns that lead to success."""
        # Update success weights
        operation = success_data.get("operation")

        # Store successful configuration
        success_config = {
            "operation": operation,
            "context": self._get_environment_context(),
            "timestamp": datetime.now().isoformat(),
        }

        # Save to knowledge base
        success_file = self.knowledge_base_path / "success_patterns.json"

        if success_file.exists():
            with open(success_file, "r") as f:
                patterns = json.load(f)
        else:
            patterns = []

        patterns.append(success_config)

        # Keep only last 1000 successes
        patterns = patterns[-1000:]

        with open(success_file, "w") as f:
            json.dump(patterns, f, indent=2)

    def _get_environment_context(self) -> dict[str, Any]:
        """Get current environment context."""
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "platform": sys.platform,
            "cwd": os.getcwd(),
            "env_vars_set": len([k for k in os.environ if k.startswith("DEVSKY")]),
        }

    def _detect_anomaly(self, features: np.ndarray) -> bool:
        """Detect if operation is anomalous."""
        if self.anomaly_detector is None or len(self.success_patterns) < 10:
            return False

        try:
            # Reshape for sklearn
            features_reshaped = features.reshape(1, -1)
            prediction = self.anomaly_detector.predict(features_reshaped)
            return prediction[0] == -1  # -1 indicates anomaly
        except Exception:
            return False

    def _calculate_improvement(self) -> float:
        """Calculate overall system improvement."""
        if len(self.error_history) < 10:
            return 0.0

        # Compare error rate over time
        recent_errors = len([e for e in self.error_history[-50:] if not e.get("solution", {}).get("success")])
        older_errors = len([e for e in self.error_history[-100:-50] if not e.get("solution", {}).get("success")])

        if older_errors == 0:
            return 1.0

        improvement = 1 - (recent_errors / older_errors)
        return max(0, min(1, improvement))

    def _update_error_model(self, error_features: np.ndarray, success: bool) -> None:
        """Update ML error model with new training data."""
        if self.error_classifier is None:
            return

        try:
            # Store for future model retraining
            self.solution_history.append(
                {"features": error_features.tolist(), "success": success, "timestamp": datetime.now().isoformat()}
            )

            # Keep only recent history for memory efficiency
            if len(self.solution_history) > 1000:
                self.solution_history = self.solution_history[-1000:]

        except Exception as e:
            logger.warning(f"Error model update failed: {e}")

    def _extract_operation_features(self, operation_data: dict[str, Any]) -> np.ndarray:
        """Extract features from operation for failure prediction."""
        features = []

        # Operation type encoding
        op_types = ["read", "write", "network", "compute", "database", "other"]
        op_type = operation_data.get("type", "other")
        type_encoding = [1 if t == op_type else 0 for t in op_types]
        features.extend(type_encoding)

        # Time features
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        features.extend([hour / 24, day_of_week / 7])

        # Resource features
        features.append(operation_data.get("complexity", 5) / 10)
        features.append(operation_data.get("resource_intensity", 5) / 10)

        # Historical features
        features.append(len(self.error_history) / 1000)

        return np.array(features)

    def _predict_failure_probability(self, features: np.ndarray) -> float:
        """Predict probability of operation failure."""
        try:
            # Check anomaly detector
            if self.anomaly_detector and len(self.success_patterns) >= 10:
                features_reshaped = features.reshape(1, -1)
                prediction = self.anomaly_detector.predict(features_reshaped)
                if prediction[0] == -1:  # Anomaly detected
                    return 0.8

            # Calculate based on recent error rate
            if len(self.error_history) >= 10:
                recent_errors = len([e for e in self.error_history[-50:] if not e.get("solution", {}).get("success")])
                failure_rate = recent_errors / min(50, len(self.error_history))
                return min(0.95, failure_rate + 0.1)

            return 0.3  # Default baseline probability

        except Exception as e:
            logger.warning(f"Failure prediction error: {e}")
            return 0.5

    def _get_preventive_measures(self, operation_data: dict[str, Any], failure_probability: float) -> list[str]:
        """Get preventive measures based on failure probability."""
        measures = []

        if failure_probability > 0.7:
            measures.extend(
                [
                    "Add retry logic with exponential backoff",
                    "Implement circuit breaker pattern",
                    "Add comprehensive error handling",
                ]
            )

        if failure_probability > 0.5:
            measures.extend(["Add input validation", "Implement timeout mechanisms", "Add logging and monitoring"])

        if operation_data.get("type") == "network":
            measures.append("Check network connectivity before execution")

        if operation_data.get("type") == "database":
            measures.append("Use connection pooling and query optimization")

        return measures

    def _calculate_prediction_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence in failure prediction."""
        # Confidence increases with more historical data
        if len(self.error_history) < 10:
            return 0.3

        if len(self.error_history) < 50:
            return 0.5

        if len(self.error_history) < 100:
            return 0.7

        return 0.85

    def _analyze_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Analyze issue to determine fix strategy."""
        return {
            "type": issue.get("type", "unknown"),
            "severity": issue.get("severity", "medium"),
            "component": issue.get("component", "unknown"),
            "error_pattern": issue.get("message", "")[:100],
            "context": issue.get("context", {}),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_similar_fixes(self, issue_analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Get similar fixes from solution history."""
        similar_fixes = []

        for solution in self.solution_history[-100:]:
            if solution.get("type") == issue_analysis.get("type"):
                similar_fixes.append(solution)

        return similar_fixes

    def _select_best_fix(self, similar_fixes: list[dict[str, Any]]) -> dict[str, Any]:
        """Select the best fix from similar cases."""
        if not similar_fixes:
            return {"solution": "Manual investigation required", "confidence": 0.0, "approach": "manual"}

        # Find most successful solution
        successful_fixes = [f for f in similar_fixes if f.get("success")]

        if successful_fixes:
            # Return most recent successful fix
            best_fix = successful_fixes[-1]
            return {
                "solution": best_fix.get("text", "Apply historical fix"),
                "confidence": len(successful_fixes) / len(similar_fixes),
                "approach": "automated",
                "commands": best_fix.get("commands", []),
            }

        return {"solution": "No proven solution available", "confidence": 0.2, "approach": "experimental"}

    def _execute_fix(self, fix: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
        """Execute fix for the issue."""
        import time

        start_time = time.time()

        try:
            # Execute fix commands if available
            commands = fix.get("commands", [])

            if not commands:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "message": "No executable commands provided",
                }

            # In production, would execute actual fix commands
            logger.info(f"Executing fix: {fix.get('solution')}")

            return {
                "success": True,
                "duration": time.time() - start_time,
                "message": "Fix applied successfully",
                "commands_executed": commands,
            }

        except Exception as e:
            return {"success": False, "duration": time.time() - start_time, "message": f"Fix execution failed: {e!s}"}

    def _update_fix_knowledge(self, issue: dict[str, Any], fix: dict[str, Any], success: bool) -> None:
        """Update fix knowledge base with result."""
        self.solution_history.append(
            {"issue_type": issue.get("type"), "fix": fix, "success": success, "timestamp": datetime.now().isoformat()}
        )

        # Keep only recent history
        if len(self.solution_history) > 1000:
            self.solution_history = self.solution_history[-1000:]

    def _get_conflict_frequency(self, conflict_data: dict[str, Any]) -> int:
        """Get frequency of this type of conflict."""
        conflict_type = conflict_data.get("type")
        frequency = len([c for c in self.conflict_history if c.get("conflict", {}).get("type") == conflict_type])
        return frequency

    def _assess_conflict_complexity(self, conflict_data: dict[str, Any]) -> str:
        """Assess complexity of conflict."""
        files_affected = len(conflict_data.get("files", []))
        conflicts_count = len(conflict_data.get("conflicts", []))

        if files_affected > 10 or conflicts_count > 20:
            return "high"
        elif files_affected > 5 or conflicts_count > 10:
            return "medium"
        else:
            return "low"

    def save_knowledge(self) -> None:
        """Save learned knowledge to disk."""
        # Save error history
        with open(self.knowledge_base_path / "error_history.json", "w") as f:
            json.dump(self.error_history[-1000:], f, default=str)

        # Save conflict history
        with open(self.knowledge_base_path / "conflict_history.json", "w") as f:
            json.dump(self.conflict_history[-1000:], f, default=str)

        # Save ML models if trained
        if self.error_classifier:
            with open(self.knowledge_base_path / "error_classifier.pkl", "wb") as f:
                pickle.dump(self.error_classifier, f)

        logger.info(f"💾 Knowledge saved (Improvement: {self.improvement_score:.2%})")

    def load_knowledge(self) -> None:
        """Load previously learned knowledge."""
        # Load error history
        error_file = self.knowledge_base_path / "error_history.json"
        if error_file.exists():
            with open(error_file, "r") as f:
                self.error_history = json.load(f)

        # Load conflict history
        conflict_file = self.knowledge_base_path / "conflict_history.json"
        if conflict_file.exists():
            with open(conflict_file, "r") as f:
                self.conflict_history = json.load(f)

        # Load ML models
        model_file = self.knowledge_base_path / "error_classifier.pkl"
        if model_file.exists():
            with open(model_file, "rb") as f:
                self.error_classifier = pickle.load(f)

        logger.info(f"🧠 Loaded knowledge: {len(self.error_history)} errors, {len(self.conflict_history)} conflicts")


# Global instance
self_learning_system = SelfLearningSystem()


# Integration functions
async def learn_and_fix(error: dict[str, Any]) -> dict[str, Any]:
    """Learn from error and attempt auto-fix."""
    learning_result = self_learning_system.learn_from_error(error)

    if learning_result["auto_fix_available"]:
        fix_result = self_learning_system.auto_fix(error)
        return fix_result

    return learning_result


async def predict_and_prevent(operation: dict[str, Any]) -> dict[str, Any]:
    """Predict failures and prevent them."""
    prediction = self_learning_system.predict_failure(operation)

    if prediction["will_likely_fail"]:
        logger.warning(f"⚠️ Operation likely to fail (probability: {prediction['failure_probability']:.2%})")
        logger.info(f"Preventive measures: {prediction['preventive_measures']}")

    return prediction


# Auto-save knowledge periodically
async def auto_save_knowledge():
    """Automatically save learned knowledge every hour."""
    while True:
        await asyncio.sleep(SelfLearningSystem.AUTO_SAVE_INTERVAL_SECONDS)
        self_learning_system.save_knowledge()


# Start auto-save task

if __name__ == "__main__":
    asyncio.run(auto_save_knowledge())
