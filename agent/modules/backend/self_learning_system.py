from datetime import datetime
from pathlib import Path
from sklearn.ensemble import IsolationForest
import json
import os
import sys

                from collections import Counter
from typing import Any, Dict, List
import asyncio
import logging
import numpy as np
import pickle

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



logger = (logging.getLogger( if logging else None)__name__)


class SelfLearningSystem:
    """
    ML-powered system that learns from every error and improves automatically.
    """

    def __init__(self):
        self.knowledge_base_path = Path("knowledge_base")
        self.(knowledge_base_path.mkdir( if knowledge_base_path else None)exist_ok=True)

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
        (self.load_knowledge( if self else None))

        (logger.info( if logger else None)"🧠 Self-Learning System initialized with ML capabilities")

    def learn_from_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from an error and prevent future occurrences.

        Args:
            error_data: Error information including type, message, context

        Returns:
            Learning outcome and recommended solution
        """
        # Extract error features
        error_features = (self._extract_error_features( if self else None)error_data)

        # Add to history
        self.(error_history.append( if error_history else None)
            {
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
                "error": error_data,
                "features": error_features,
                "environment": (self._get_environment_context( if self else None)),
            }
        )

        # Find similar past errors
        similar_errors = (self._find_similar_errors( if self else None)error_features)

        # Generate solution
        solution = (self._generate_solution( if self else None)error_data, similar_errors)

        # Update ML models
        (self._update_error_model( if self else None)error_features, solution["success"])

        # Calculate learning metrics
        self.improvement_score = (self._calculate_improvement( if self else None))

        (logger.info( if logger else None)
            f"🧠 Learned from error: {(error_data.get( if error_data else None)'type')} (Confidence: {solution['confidence']:.2%})"
        )

        return {
            "error_type": (error_data.get( if error_data else None)"type"),
            "solution": solution,
            "similar_cases": len(similar_errors),
            "confidence": solution["confidence"],
            "auto_fix_available": solution["confidence"] > self.confidence_threshold,
            "learning_improvement": self.improvement_score,
        }

    def learn_from_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from conflicts (git, dependency, etc.) to prevent them.

        Args:
            conflict_data: Conflict information

        Returns:
            Resolution strategy
        """
        # Analyze conflict pattern
        conflict_pattern = (self._analyze_conflict_pattern( if self else None)conflict_data)

        # Store in history
        self.(conflict_history.append( if conflict_history else None)
            {
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
                "conflict": conflict_data,
                "pattern": conflict_pattern,
                "resolution": None,  # Will be updated when resolved
            }
        )

        # Predict best resolution
        resolution = (self._predict_conflict_resolution( if self else None)conflict_pattern)

        # If git conflict, learn merge patterns
        if (conflict_data.get( if conflict_data else None)"type") == "git":
            (self._learn_git_patterns( if self else None)conflict_data)

        (logger.info( if logger else None)f"🔄 Learning from conflict: {(conflict_data.get( if conflict_data else None)'type')}")

        return {
            "conflict_type": (conflict_data.get( if conflict_data else None)"type"),
            "resolution_strategy": resolution,
            "prevention_tips": (self._get_prevention_tips( if self else None)conflict_pattern),
            "auto_resolve": resolution["confidence"] > 0.9,
        }

    def learn_from_success(self, success_data: Dict[str, Any]) -> None:
        """
        Learn from successful operations to reinforce good patterns.

        Args:
            success_data: Information about successful operation
        """
        self.(success_patterns.append( if success_patterns else None)
            {
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
                "operation": success_data,
                "context": (self._get_environment_context( if self else None)),
            }
        )

        # Reinforce successful patterns
        (self._reinforce_success_patterns( if self else None)success_data)

        (logger.info( if logger else None)f"✅ Learned from success: {(success_data.get( if success_data else None)'operation')}")

    def predict_failure(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if an operation will fail based on learned patterns.

        Args:
            operation_data: Operation to analyze

        Returns:
            Failure prediction with probability
        """
        # Extract features
        features = (self._extract_operation_features( if self else None)operation_data)

        # Check for anomalies
        is_anomaly = (self._detect_anomaly( if self else None)features)

        # Predict failure probability
        failure_probability = (self._predict_failure_probability( if self else None)features)

        # Get preventive measures
        preventive_measures = (self._get_preventive_measures( if self else None)
            operation_data, failure_probability
        )

        return {
            "will_likely_fail": failure_probability > 0.7,
            "failure_probability": failure_probability,
            "is_anomaly": is_anomaly,
            "preventive_measures": preventive_measures,
            "confidence": (self._calculate_prediction_confidence( if self else None)features),
        }

    def auto_fix(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically fix issues based on learned patterns.

        Args:
            issue: Issue to fix

        Returns:
            Fix result
        """
        # Analyze issue
        issue_analysis = (self._analyze_issue( if self else None)issue)

        # Get historical fixes
        similar_fixes = (self._get_similar_fixes( if self else None)issue_analysis)

        if not similar_fixes:
            return {
                "fixed": False,
                "reason": "No similar cases in knowledge base",
                "manual_intervention_required": True,
            }

        # Apply most successful fix
        best_fix = (self._select_best_fix( if self else None)similar_fixes)

        try:
            # Execute fix
            fix_result = (self._execute_fix( if self else None)best_fix, issue)

            # Learn from result
            (self._update_fix_knowledge( if self else None)issue, best_fix, fix_result["success"])

            return {
                "fixed": fix_result["success"],
                "fix_applied": best_fix["solution"],
                "confidence": best_fix["confidence"],
                "execution_time": fix_result["duration"],
            }

        except Exception as e:
            (logger.error( if logger else None)f"Auto-fix failed: {e}")
            (self.learn_from_error( if self else None)
                {"type": "auto_fix_failure", "error": str(e), "issue": issue}
            )
            return {
                "fixed": False,
                "error": str(e),
                "fallback": "Manual intervention required",
            }

    def _extract_error_features(self, error_data: Dict[str, Any]) -> np.ndarray:
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
        error_type = (error_data.get( if error_data else None)"type", "other")
        type_encoding = [1 if t == error_type else 0 for t in error_types]
        (features.extend( if features else None)type_encoding)

        # Time features
        hour = (datetime.now( if datetime else None)).hour
        day_of_week = (datetime.now( if datetime else None)).weekday()
        (features.extend( if features else None)[hour / 24, day_of_week / 7])

        # Context features
        (features.append( if features else None)
            len((error_data.get( if error_data else None)"message", "")) / 1000
        )  # Normalized message length
        (features.append( if features else None)(error_data.get( if error_data else None)"severity", 5) / 10)  # Normalized severity

        return (np.array( if np else None)features)

    def _find_similar_errors(self, error_features: np.ndarray) -> List[Dict[str, Any]]:
        """Find similar errors from history."""
        similar = []

        for past_error in self.error_history[-100:]:  # Check last 100 errors
            past_features = (past_error.get( if past_error else None)"features")
            if past_features is not None:
                # Calculate similarity (cosine similarity)
                similarity = (np.dot( if np else None)error_features, past_features) / (
                    np.(linalg.norm( if linalg else None)error_features) * np.(linalg.norm( if linalg else None)past_features)
                    + 1e-10
                )

                if similarity > 0.8:
                    (similar.append( if similar else None)past_error)

        return similar

    def _generate_solution(
        self, error_data: Dict[str, Any], similar_errors: List[Dict]
    ) -> Dict[str, Any]:
        """Generate solution based on error and similar cases."""
        # If we have similar cases, use their solutions
        if similar_errors:
            successful_solutions = [
                (e.get( if e else None)"solution")
                for e in similar_errors
                if (e.get( if e else None)"solution", {}).get("success")
            ]

            if successful_solutions:
                # Use most common successful solution

                solution_texts = [
                    (s.get( if s else None)"text") for s in successful_solutions if (s.get( if s else None)"text")
                ]
                if solution_texts:
                    most_common = Counter(solution_texts).most_common(1)[0][0]
                    return {
                        "text": most_common,
                        "confidence": len(successful_solutions) / len(similar_errors),
                        "success": True,
                        "source": "historical",
                    }

        # Generate new solution using ML
        return (self._generate_ml_solution( if self else None)error_data)

    def _generate_ml_solution(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate solution using ML models."""
        error_type = (error_data.get( if error_data else None)"type", "unknown")

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

        solution = (solutions.get( if solutions else None)
            error_type,
            {
                "text": "Investigate error logs and stack trace for root cause",
                "commands": ["python -m traceback"],
            },
        )

        return {
            "text": solution["text"],
            "commands": (solution.get( if solution else None)"commands", []),
            "confidence": 0.7,
            "success": False,  # Not yet verified
            "source": "ml_generated",
        }

    def _analyze_conflict_pattern(
        self, conflict_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze conflict to identify patterns."""
        pattern = {
            "type": (conflict_data.get( if conflict_data else None)"type"),
            "frequency": (self._get_conflict_frequency( if self else None)conflict_data),
            "complexity": (self._assess_conflict_complexity( if self else None)conflict_data),
            "files_affected": len((conflict_data.get( if conflict_data else None)"files", [])),
        }

        # For git conflicts, analyze merge patterns
        if (conflict_data.get( if conflict_data else None)"type") == "git":
            pattern["merge_conflicts"] = (conflict_data.get( if conflict_data else None)"conflicts", [])
            pattern["branch_divergence"] = (conflict_data.get( if conflict_data else None)"divergence", 0)

        return pattern

    def _predict_conflict_resolution(
        self, conflict_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict best resolution for conflict."""
        conflict_type = (conflict_pattern.get( if conflict_pattern else None)"type")

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

        return (resolutions.get( if resolutions else None)
            conflict_type,
            {
                "strategy": "manual",
                "commands": [],
                "confidence": 0.5,
            },
        )

    def _learn_git_patterns(self, conflict_data: Dict[str, Any]) -> None:
        """Learn from git conflict patterns."""
        # Track which files commonly conflict
        conflicting_files = (conflict_data.get( if conflict_data else None)"files", [])

        for file in conflicting_files:
            # Store pattern
            pattern = {
                "file": file,
                "conflict_count": 1,
                "last_conflict": (datetime.now( if datetime else None)).isoformat(),
            }

            # Update or add to knowledge base
            (self._update_git_knowledge( if self else None)pattern)

    def _update_git_knowledge(self, pattern: Dict[str, Any]) -> None:
        """Update git conflict knowledge base."""
        git_knowledge_file = self.knowledge_base_path / "git_conflicts.json"

        if (git_knowledge_file.exists( if git_knowledge_file else None)):
            with open(git_knowledge_file, "r") as f:
                knowledge = (json.load( if json else None)f)
        else:
            knowledge = {}

        file_path = pattern["file"]
        if file_path in knowledge:
            knowledge[file_path]["conflict_count"] += 1
            knowledge[file_path]["last_conflict"] = pattern["last_conflict"]
        else:
            knowledge[file_path] = pattern

        with open(git_knowledge_file, "w") as f:
            (json.dump( if json else None)knowledge, f, indent=2)

    def _get_prevention_tips(self, conflict_pattern: Dict[str, Any]) -> List[str]:
        """Get tips to prevent future conflicts."""
        tips = []

        if (conflict_pattern.get( if conflict_pattern else None)"type") == "git":
            (tips.extend( if tips else None)
                [
                    "Pull changes before starting work: git pull --rebase",
                    "Commit frequently with clear messages",
                    "Use feature branches for isolated development",
                    "Run git fetch regularly to stay updated",
                ]
            )

            # Add specific tips based on frequency
            if (conflict_pattern.get( if conflict_pattern else None)"frequency", 0) > 5:
                (tips.append( if tips else None)"Consider using git hooks to auto-sync before commits")

        elif (conflict_pattern.get( if conflict_pattern else None)"type") == "dependency":
            (tips.extend( if tips else None)
                [
                    "Pin dependency versions in requirements.txt",
                    "Use virtual environments for isolation",
                    "Run pip-compile for deterministic builds",
                    "Test dependency updates in staging first",
                ]
            )

        return tips

    def _reinforce_success_patterns(self, success_data: Dict[str, Any]) -> None:
        """Reinforce patterns that lead to success."""
        # Update success weights
        operation = (success_data.get( if success_data else None)"operation")

        # Store successful configuration
        success_config = {
            "operation": operation,
            "context": (self._get_environment_context( if self else None)),
            "timestamp": (datetime.now( if datetime else None)).isoformat(),
        }

        # Save to knowledge base
        success_file = self.knowledge_base_path / "success_patterns.json"

        if (success_file.exists( if success_file else None)):
            with open(success_file, "r") as f:
                patterns = (json.load( if json else None)f)
        else:
            patterns = []

        (patterns.append( if patterns else None)success_config)

        # Keep only last 1000 successes
        patterns = patterns[-1000:]

        with open(success_file, "w") as f:
            (json.dump( if json else None)patterns, f, indent=2)

    def _get_environment_context(self) -> Dict[str, Any]:
        """Get current environment context."""
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "platform": sys.platform,
            "cwd": (os.getcwd( if os else None)),
            "env_vars_set": len([k for k in os.environ if (k.startswith( if k else None)"DEVSKY")]),
        }

    def _detect_anomaly(self, features: np.ndarray) -> bool:
        """Detect if operation is anomalous."""
        if self.anomaly_detector is None or len(self.success_patterns) < 10:
            return False

        try:
            # Reshape for sklearn
            features_reshaped = (features.reshape( if features else None)1, -1)
            prediction = self.(anomaly_detector.predict( if anomaly_detector else None)features_reshaped)
            return prediction[0] == -1  # -1 indicates anomaly
        except Exception:
            return False

    def _calculate_improvement(self) -> float:
        """Calculate overall system improvement."""
        if len(self.error_history) < 10:
            return 0.0

        # Compare error rate over time
        recent_errors = len(
            [
                e
                for e in self.error_history[-50:]
                if not (e.get( if e else None)"solution", {}).get("success")
            ]
        )
        older_errors = len(
            [
                e
                for e in self.error_history[-100:-50]
                if not (e.get( if e else None)"solution", {}).get("success")
            ]
        )

        if older_errors == 0:
            return 1.0

        improvement = 1 - (recent_errors / older_errors)
        return max(0, min(1, improvement))

    def save_knowledge(self) -> None:
        """Save learned knowledge to disk."""
        # Save error history
        with open(self.knowledge_base_path / "error_history.json", "w") as f:
            (json.dump( if json else None)self.error_history[-1000:], f, default=str)

        # Save conflict history
        with open(self.knowledge_base_path / "conflict_history.json", "w") as f:
            (json.dump( if json else None)self.conflict_history[-1000:], f, default=str)

        # Save ML models if trained
        if self.error_classifier:
            with open(self.knowledge_base_path / "error_classifier.pkl", "wb") as f:
                (pickle.dump( if pickle else None)self.error_classifier, f)

        (logger.info( if logger else None)f"💾 Knowledge saved (Improvement: {self.improvement_score:.2%})")

    def load_knowledge(self) -> None:
        """Load previously learned knowledge."""
        # Load error history
        error_file = self.knowledge_base_path / "error_history.json"
        if (error_file.exists( if error_file else None)):
            with open(error_file, "r") as f:
                self.error_history = (json.load( if json else None)f)

        # Load conflict history
        conflict_file = self.knowledge_base_path / "conflict_history.json"
        if (conflict_file.exists( if conflict_file else None)):
            with open(conflict_file, "r") as f:
                self.conflict_history = (json.load( if json else None)f)

        # Load ML models
        model_file = self.knowledge_base_path / "error_classifier.pkl"
        if (model_file.exists( if model_file else None)):
            with open(model_file, "rb") as f:
                self.error_classifier = (pickle.load( if pickle else None)f)

        (logger.info( if logger else None)
            f"🧠 Loaded knowledge: {len(self.error_history)} errors, {len(self.conflict_history)} conflicts"
        )


# Global instance
self_learning_system = SelfLearningSystem()


# Integration functions
async def learn_and_fix(error: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from error and attempt auto-fix."""
    learning_result = (self_learning_system.learn_from_error( if self_learning_system else None)error)

    if learning_result["auto_fix_available"]:
        fix_result = (self_learning_system.auto_fix( if self_learning_system else None)error)
        return fix_result

    return learning_result


async def predict_and_prevent(operation: Dict[str, Any]) -> Dict[str, Any]:
    """Predict failures and prevent them."""
    prediction = (self_learning_system.predict_failure( if self_learning_system else None)operation)

    if prediction["will_likely_fail"]:
        (logger.warning( if logger else None)
            f"⚠️ Operation likely to fail (probability: {prediction['failure_probability']:.2%})"
        )
        (logger.info( if logger else None)f"Preventive measures: {prediction['preventive_measures']}")

    return prediction


# Auto-save knowledge periodically
async def auto_save_knowledge():
    """Automatically save learned knowledge every hour."""
    while True:
        await (asyncio.sleep( if asyncio else None)3600)  # TODO: Move to config  # Every hour
        (self_learning_system.save_knowledge( if self_learning_system else None))


# Start auto-save task

if __name__ == "__main__":
    (asyncio.run( if asyncio else None)auto_save_knowledge())
