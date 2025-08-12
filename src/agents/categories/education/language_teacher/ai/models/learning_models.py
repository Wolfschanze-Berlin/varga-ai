"""
Learning Models - IRT and BKT implementations for adaptive learning.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import scipy.optimize as opt
from datetime import datetime, timedelta

from src.log_service import get_logger


@dataclass
class ItemParameters:
    """Parameters for an item in IRT model."""
    difficulty: float  # Item difficulty (b parameter)
    discrimination: float = 1.0  # Item discrimination (a parameter) 
    guessing: float = 0.0  # Guessing parameter (c parameter)
    item_id: str = ""
    topic: str = ""


@dataclass
class StudentAbility:
    """Student ability parameters."""
    theta: float  # Ability level
    standard_error: float = 1.0
    confidence_interval: Tuple[float, float] = (-2.0, 2.0)


class LearningModel(ABC):
    """Abstract base class for learning models."""
    
    @abstractmethod
    def update_student_state(self, student_id: str, item_id: str, 
                           correct: bool, **kwargs) -> None:
        """Update student state based on response."""
        pass
    
    @abstractmethod
    def predict_success_probability(self, student_id: str, item_id: str) -> float:
        """Predict probability of correct response."""
        pass
    
    @abstractmethod
    def get_optimal_next_item(self, student_id: str, 
                            available_items: List[str]) -> str:
        """Select optimal next item for student."""
        pass


class IRT_Model(LearningModel):
    """
    Item Response Theory (IRT) Model for adaptive testing and learning.
    
    Uses 3-parameter logistic model:
    P(correct) = c + (1-c) * 1/(1 + exp(-a*(theta - b)))
    
    Where:
    - theta: Student ability
    - a: Item discrimination  
    - b: Item difficulty
    - c: Guessing parameter
    """
    
    def __init__(self):
        """Initialize IRT model."""
        self.logger = get_logger("irt_model")
        
        # Student abilities
        self.student_abilities: Dict[str, StudentAbility] = {}
        
        # Item parameters
        self.item_parameters: Dict[str, ItemParameters] = {}
        
        # Response history for calibration
        self.response_history: List[Dict[str, Any]] = []
        
        # Model settings
        self.max_ability = 4.0
        self.min_ability = -4.0
        self.initial_ability = 0.0
        self.initial_se = 1.0
        
        self.logger.info("Initialized IRT model")
    
    def add_item(self, item_id: str, difficulty: float, 
                discrimination: float = 1.0, guessing: float = 0.0,
                topic: str = "") -> None:
        """
        Add item with parameters to the model.
        
        Args:
            item_id: Unique item identifier
            difficulty: Item difficulty (-4 to 4)
            discrimination: Item discrimination (0.5 to 3)
            guessing: Guessing parameter (0 to 0.3)
            topic: Topic/category for the item
        """
        try:
            self.item_parameters[item_id] = ItemParameters(
                difficulty=max(-4, min(4, difficulty)),
                discrimination=max(0.1, min(3.0, discrimination)),
                guessing=max(0.0, min(0.3, guessing)),
                item_id=item_id,
                topic=topic
            )
            
            self.logger.debug(f"Added item {item_id} with difficulty {difficulty}")
            
        except Exception as e:
            self.logger.error(f"Error adding item {item_id}: {e}")
    
    def get_student_ability(self, student_id: str) -> StudentAbility:
        """Get or create student ability."""
        if student_id not in self.student_abilities:
            self.student_abilities[student_id] = StudentAbility(
                theta=self.initial_ability,
                standard_error=self.initial_se
            )
        return self.student_abilities[student_id]
    
    def predict_success_probability(self, student_id: str, item_id: str) -> float:
        """
        Predict probability of correct response using 3PL model.
        
        Args:
            student_id: Student identifier
            item_id: Item identifier
            
        Returns:
            Probability of correct response (0-1)
        """
        try:
            if item_id not in self.item_parameters:
                self.logger.warning(f"Item {item_id} not found, using default parameters")
                return 0.5
            
            ability = self.get_student_ability(student_id)
            item = self.item_parameters[item_id]
            
            # 3PL model
            theta = ability.theta
            a = item.discrimination
            b = item.difficulty
            c = item.guessing
            
            # Prevent overflow in exponential
            exponent = -a * (theta - b)
            exponent = max(-10, min(10, exponent))
            
            probability = c + (1 - c) / (1 + np.exp(exponent))
            
            return max(0.01, min(0.99, probability))
            
        except Exception as e:
            self.logger.error(f"Error predicting probability: {e}")
            return 0.5
    
    def update_student_state(self, student_id: str, item_id: str, 
                           correct: bool, **kwargs) -> None:
        """
        Update student ability using Maximum Likelihood Estimation.
        
        Args:
            student_id: Student identifier
            item_id: Item identifier  
            correct: Whether response was correct
        """
        try:
            if item_id not in self.item_parameters:
                self.logger.warning(f"Cannot update for unknown item {item_id}")
                return
            
            ability = self.get_student_ability(student_id)
            item = self.item_parameters[item_id]
            
            # Record response
            response_data = {
                'student_id': student_id,
                'item_id': item_id,
                'correct': correct,
                'timestamp': datetime.now(),
                'previous_ability': ability.theta
            }
            self.response_history.append(response_data)
            
            # Update ability using Newton-Raphson method
            new_theta = self._update_ability_mle(
                student_id, ability.theta, item, correct
            )
            
            # Update standard error
            new_se = self._calculate_standard_error(student_id, new_theta)
            
            # Update student ability
            ability.theta = max(self.min_ability, min(self.max_ability, new_theta))
            ability.standard_error = new_se
            ability.confidence_interval = (
                new_theta - 1.96 * new_se,
                new_theta + 1.96 * new_se
            )
            
            self.logger.debug(
                f"Updated ability for {student_id}: {new_theta:.3f} (SE: {new_se:.3f})"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating student state: {e}")
    
    def _update_ability_mle(self, student_id: str, current_theta: float,
                           item: ItemParameters, correct: bool) -> float:
        """Update ability using Maximum Likelihood Estimation."""
        try:
            # Get all responses for this student
            student_responses = [
                r for r in self.response_history 
                if r['student_id'] == student_id
            ]
            
            # Add current response
            student_responses.append({
                'item_id': item.item_id,
                'correct': correct,
                'item_params': item
            })
            
            # Define likelihood function
            def log_likelihood(theta):
                ll = 0.0
                for response in student_responses:
                    if 'item_params' in response:
                        params = response['item_params']
                    else:
                        params = self.item_parameters.get(response['item_id'])
                        if not params:
                            continue
                    
                    # Calculate probability
                    prob = self._calculate_3pl_probability(theta, params)
                    
                    # Add to log likelihood
                    if response['correct']:
                        ll += np.log(max(0.001, prob))
                    else:
                        ll += np.log(max(0.001, 1 - prob))
                
                return -ll  # Minimize negative log likelihood
            
            # Optimize
            result = opt.minimize_scalar(
                log_likelihood,
                bounds=(self.min_ability, self.max_ability),
                method='bounded'
            )
            
            if result.success:
                return result.x
            else:
                # Fallback to simple update
                return self._simple_ability_update(current_theta, item, correct)
                
        except Exception as e:
            self.logger.error(f"Error in MLE update: {e}")
            return self._simple_ability_update(current_theta, item, correct)
    
    def _simple_ability_update(self, theta: float, item: ItemParameters, 
                              correct: bool) -> float:
        """Simple ability update as fallback."""
        try:
            prob = self._calculate_3pl_probability(theta, item)
            
            # Learning rate based on prediction confidence
            learning_rate = 0.3 * (0.5 - abs(prob - 0.5))
            
            if correct:
                return theta + learning_rate * (1 - prob)
            else:
                return theta - learning_rate * prob
                
        except Exception as e:
            self.logger.error(f"Error in simple update: {e}")
            return theta
    
    def _calculate_3pl_probability(self, theta: float, 
                                  item: ItemParameters) -> float:
        """Calculate 3PL probability."""
        try:
            exponent = -item.discrimination * (theta - item.difficulty)
            exponent = max(-10, min(10, exponent))
            
            return item.guessing + (1 - item.guessing) / (1 + np.exp(exponent))
            
        except Exception as e:
            self.logger.error(f"Error calculating 3PL probability: {e}")
            return 0.5
    
    def _calculate_standard_error(self, student_id: str, theta: float) -> float:
        """Calculate standard error of ability estimate."""
        try:
            # Get all items attempted by student
            student_responses = [
                r for r in self.response_history 
                if r['student_id'] == student_id
            ]
            
            if not student_responses:
                return self.initial_se
            
            # Calculate Fisher information
            information = 0.0
            for response in student_responses:
                item_id = response['item_id']
                if item_id in self.item_parameters:
                    item = self.item_parameters[item_id]
                    prob = self._calculate_3pl_probability(theta, item)
                    
                    # Information function
                    a = item.discrimination
                    c = item.guessing
                    
                    numerator = a**2 * (prob - c)**2 * (1 - prob)
                    denominator = prob * (1 - c)**2
                    
                    if denominator > 0:
                        information += numerator / denominator
            
            # Standard error is inverse square root of information
            if information > 0:
                return 1.0 / np.sqrt(information)
            else:
                return self.initial_se
                
        except Exception as e:
            self.logger.error(f"Error calculating standard error: {e}")
            return self.initial_se
    
    def get_optimal_next_item(self, student_id: str, 
                            available_items: List[str]) -> str:
        """
        Select optimal next item using maximum information criterion.
        
        Args:
            student_id: Student identifier
            available_items: List of available item IDs
            
        Returns:
            Optimal item ID
        """
        try:
            if not available_items:
                return ""
            
            ability = self.get_student_ability(student_id)
            theta = ability.theta
            
            max_information = -1
            best_item = available_items[0]
            
            for item_id in available_items:
                if item_id not in self.item_parameters:
                    continue
                
                item = self.item_parameters[item_id]
                
                # Calculate Fisher information for this item
                prob = self._calculate_3pl_probability(theta, item)
                
                # Information function
                a = item.discrimination
                c = item.guessing
                
                if prob > 0 and prob < 1:
                    numerator = a**2 * (prob - c)**2 * (1 - prob)
                    denominator = prob * (1 - c)**2
                    
                    if denominator > 0:
                        information = numerator / denominator
                        
                        if information > max_information:
                            max_information = information
                            best_item = item_id
            
            self.logger.debug(f"Selected item {best_item} for student {student_id}")
            return best_item
            
        except Exception as e:
            self.logger.error(f"Error selecting optimal item: {e}")
            return available_items[0] if available_items else ""


@dataclass  
class KnowledgeComponent:
    """Knowledge component for BKT model."""
    name: str
    prior_knowledge: float = 0.1  # P(L0)
    learn_rate: float = 0.3  # P(T)
    guess_rate: float = 0.2  # P(G)
    slip_rate: float = 0.1  # P(S)


class BKT_Model(LearningModel):
    """
    Bayesian Knowledge Tracing (BKT) Model.
    
    Tracks knowledge state for individual knowledge components.
    Uses four parameters:
    - P(L0): Prior probability of knowing
    - P(T): Probability of learning (transition)
    - P(G): Probability of correct guess
    - P(S): Probability of slip (know but incorrect)
    """
    
    def __init__(self):
        """Initialize BKT model."""
        self.logger = get_logger("bkt_model")
        
        # Knowledge components
        self.knowledge_components: Dict[str, KnowledgeComponent] = {}
        
        # Student knowledge states P(L_n)
        self.student_knowledge: Dict[str, Dict[str, float]] = {}
        
        # Performance history
        self.performance_history: List[Dict[str, Any]] = []
        
        self.logger.info("Initialized BKT model")
    
    def add_knowledge_component(self, kc_name: str, prior_knowledge: float = 0.1,
                               learn_rate: float = 0.3, guess_rate: float = 0.2,
                               slip_rate: float = 0.1) -> None:
        """
        Add knowledge component to the model.
        
        Args:
            kc_name: Knowledge component name
            prior_knowledge: Prior probability of knowing (P(L0))
            learn_rate: Learning rate (P(T))
            guess_rate: Guess rate (P(G))  
            slip_rate: Slip rate (P(S))
        """
        try:
            self.knowledge_components[kc_name] = KnowledgeComponent(
                name=kc_name,
                prior_knowledge=max(0.01, min(0.99, prior_knowledge)),
                learn_rate=max(0.01, min(0.99, learn_rate)),
                guess_rate=max(0.01, min(0.99, guess_rate)),
                slip_rate=max(0.01, min(0.99, slip_rate))
            )
            
            self.logger.debug(f"Added knowledge component: {kc_name}")
            
        except Exception as e:
            self.logger.error(f"Error adding knowledge component: {e}")
    
    def get_student_knowledge_state(self, student_id: str, kc_name: str) -> float:
        """Get current knowledge state for student and KC."""
        if student_id not in self.student_knowledge:
            self.student_knowledge[student_id] = {}
        
        if kc_name not in self.student_knowledge[student_id]:
            if kc_name in self.knowledge_components:
                prior = self.knowledge_components[kc_name].prior_knowledge
            else:
                prior = 0.1
            self.student_knowledge[student_id][kc_name] = prior
        
        return self.student_knowledge[student_id][kc_name]
    
    def predict_success_probability(self, student_id: str, item_id: str,
                                  knowledge_components: List[str] = None) -> float:
        """
        Predict probability of correct response.
        
        Args:
            student_id: Student identifier
            item_id: Item identifier
            knowledge_components: List of KCs for this item
            
        Returns:
            Probability of correct response
        """
        try:
            if not knowledge_components:
                # If no KCs specified, use item_id as KC name
                knowledge_components = [item_id]
            
            # For multiple KCs, use conjunctive model (need all)
            total_prob = 1.0
            
            for kc_name in knowledge_components:
                if kc_name not in self.knowledge_components:
                    self.add_knowledge_component(kc_name)
                
                kc = self.knowledge_components[kc_name]
                p_knowledge = self.get_student_knowledge_state(student_id, kc_name)
                
                # P(correct) = P(K)*P(correct|K) + P(not K)*P(correct|not K)
                # P(correct|K) = 1 - P(S), P(correct|not K) = P(G)
                prob_correct = (
                    p_knowledge * (1 - kc.slip_rate) +
                    (1 - p_knowledge) * kc.guess_rate
                )
                
                total_prob *= prob_correct
            
            return max(0.01, min(0.99, total_prob))
            
        except Exception as e:
            self.logger.error(f"Error predicting success probability: {e}")
            return 0.5
    
    def update_student_state(self, student_id: str, item_id: str, 
                           correct: bool, knowledge_components: List[str] = None,
                           **kwargs) -> None:
        """
        Update student knowledge state using Bayesian updating.
        
        Args:
            student_id: Student identifier
            item_id: Item identifier
            correct: Whether response was correct
            knowledge_components: List of KCs for this item
        """
        try:
            if not knowledge_components:
                knowledge_components = [item_id]
            
            # Record performance
            performance_data = {
                'student_id': student_id,
                'item_id': item_id,
                'correct': correct,
                'knowledge_components': knowledge_components,
                'timestamp': datetime.now()
            }
            self.performance_history.append(performance_data)
            
            # Update each knowledge component
            for kc_name in knowledge_components:
                if kc_name not in self.knowledge_components:
                    self.add_knowledge_component(kc_name)
                
                self._update_knowledge_component(
                    student_id, kc_name, correct
                )
            
        except Exception as e:
            self.logger.error(f"Error updating student state: {e}")
    
    def _update_knowledge_component(self, student_id: str, kc_name: str, 
                                   correct: bool) -> None:
        """Update knowledge state for a specific KC."""
        try:
            kc = self.knowledge_components[kc_name]
            p_knowledge_before = self.get_student_knowledge_state(student_id, kc_name)
            
            # Bayesian update
            # P(K_n | evidence) = P(evidence | K_n) * P(K_n-1) / P(evidence)
            
            if correct:
                # P(correct | K) and P(correct | not K)
                p_correct_given_k = 1 - kc.slip_rate
                p_correct_given_not_k = kc.guess_rate
            else:
                # P(incorrect | K) and P(incorrect | not K)  
                p_correct_given_k = kc.slip_rate
                p_correct_given_not_k = 1 - kc.guess_rate
            
            # Calculate posterior
            numerator = p_correct_given_k * p_knowledge_before
            denominator = (
                p_correct_given_k * p_knowledge_before +
                p_correct_given_not_k * (1 - p_knowledge_before)
            )
            
            if denominator > 0:
                p_knowledge_after_evidence = numerator / denominator
            else:
                p_knowledge_after_evidence = p_knowledge_before
            
            # Apply learning (opportunity to transition from not-known to known)
            if p_knowledge_after_evidence < 1.0:
                p_knowledge_final = (
                    p_knowledge_after_evidence + 
                    (1 - p_knowledge_after_evidence) * kc.learn_rate
                )
            else:
                p_knowledge_final = p_knowledge_after_evidence
            
            # Update knowledge state
            self.student_knowledge[student_id][kc_name] = max(
                0.01, min(0.99, p_knowledge_final)
            )
            
            self.logger.debug(
                f"Updated KC {kc_name} for {student_id}: "
                f"{p_knowledge_before:.3f} -> {p_knowledge_final:.3f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating KC {kc_name}: {e}")
    
    def get_optimal_next_item(self, student_id: str, 
                            available_items: List[str],
                            item_kcs: Dict[str, List[str]] = None) -> str:
        """
        Select optimal next item based on knowledge state.
        
        Args:
            student_id: Student identifier
            available_items: List of available item IDs
            item_kcs: Mapping of item IDs to their knowledge components
            
        Returns:
            Optimal item ID
        """
        try:
            if not available_items:
                return ""
            
            if not item_kcs:
                item_kcs = {item: [item] for item in available_items}
            
            best_item = available_items[0]
            best_score = -1
            
            for item_id in available_items:
                kcs = item_kcs.get(item_id, [item_id])
                
                # Calculate learning opportunity score
                score = 0.0
                for kc_name in kcs:
                    p_knowledge = self.get_student_knowledge_state(student_id, kc_name)
                    
                    # Prefer items where student has moderate knowledge
                    # (not too easy, not too hard)
                    optimal_knowledge = 0.5
                    distance_from_optimal = abs(p_knowledge - optimal_knowledge)
                    kc_score = 1.0 - distance_from_optimal
                    
                    score += kc_score
                
                # Average score across KCs
                if kcs:
                    score /= len(kcs)
                
                if score > best_score:
                    best_score = score
                    best_item = item_id
            
            self.logger.debug(f"Selected item {best_item} for student {student_id}")
            return best_item
            
        except Exception as e:
            self.logger.error(f"Error selecting optimal item: {e}")
            return available_items[0] if available_items else ""
    
    def get_mastery_status(self, student_id: str, 
                          mastery_threshold: float = 0.95) -> Dict[str, bool]:
        """
        Get mastery status for all knowledge components.
        
        Args:
            student_id: Student identifier
            mastery_threshold: Minimum probability for mastery
            
        Returns:
            Dictionary mapping KC names to mastery status
        """
        try:
            mastery_status = {}
            
            if student_id in self.student_knowledge:
                for kc_name, p_knowledge in self.student_knowledge[student_id].items():
                    mastery_status[kc_name] = p_knowledge >= mastery_threshold
            
            return mastery_status
            
        except Exception as e:
            self.logger.error(f"Error getting mastery status: {e}")
            return {}
    
    def get_learning_curve(self, student_id: str, kc_name: str) -> List[Dict[str, Any]]:
        """Get learning curve for a knowledge component."""
        try:
            curve_data = []
            
            # Filter performance history for this student and KC
            relevant_history = [
                perf for perf in self.performance_history
                if (perf['student_id'] == student_id and 
                    kc_name in perf['knowledge_components'])
            ]
            
            # Sort by timestamp
            relevant_history.sort(key=lambda x: x['timestamp'])
            
            # Simulate knowledge state evolution
            if kc_name in self.knowledge_components:
                kc = self.knowledge_components[kc_name]
                p_knowledge = kc.prior_knowledge
                
                curve_data.append({
                    'opportunity': 0,
                    'knowledge_probability': p_knowledge,
                    'timestamp': None,
                    'correct': None
                })
                
                for i, perf in enumerate(relevant_history):
                    # This is simplified - in practice, we'd need to replay
                    # the full Bayesian update sequence
                    curve_data.append({
                        'opportunity': i + 1,
                        'knowledge_probability': self.get_student_knowledge_state(
                            student_id, kc_name
                        ),
                        'timestamp': perf['timestamp'],
                        'correct': perf['correct']
                    })
            
            return curve_data
            
        except Exception as e:
            self.logger.error(f"Error getting learning curve: {e}")
            return []