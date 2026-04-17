"""
TESLA Brain - AI Decision Engine
Combines Prolog Safety Rules, Minimax, and Memory
Uses hybrid decision pipeline: Prolog validates -> Final action

Decision Pipeline:
  Sensors → State
          ↓
   Prolog Safety Rules (validate)
          ↓
   Final Executed Action
"""

import json
import math
import random
import os
import sys
from typing import Dict, List, Tuple, Optional
from enum import Enum
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MEMORY_FILE, CRASH_PENALTY, SAFE_PASS_REWARD, LANE_CHANGE_REWARD,
    SMOOTH_DRIVING_REWARD, SAFE_DISTANCE, CRITICAL_DISTANCE,
    NUM_LANES, LANE_WIDTH, CAR_MAX_SPEED, PROLOG_RULES_FILE
)
from ai.prolog_engine import PrologEngine


class Action(Enum):
    """Possible actions for the Tesla agent"""
    ACCELERATE = "accelerate"
    BRAKE = "brake"
    STEER_LEFT = "steer_left"
    STEER_RIGHT = "steer_right"
    MAINTAIN = "maintain"
    EMERGENCY_STOP = "emergency_stop"


class PrologReasoner:
    """Prolog-based logical reasoning using rules from prolog_rules.pl"""
    
    def __init__(self):
        self.prolog_engine = PrologEngine(PROLOG_RULES_FILE)
        self.safe_distance = self.prolog_engine.get_constant('safe_distance', SAFE_DISTANCE)
        self.critical_distance = self.prolog_engine.get_constant('critical_distance', CRITICAL_DISTANCE)
        print(f"[PrologReasoner] Initialized with safe_distance={self.safe_distance}, critical_distance={self.critical_distance}")
    
    def query_action(self, sensor_data: Dict, memory: Dict) -> Action:
        """Query the Prolog engine for best action based on sensor data and memory"""
        action_str = self.prolog_engine.evaluate_action(sensor_data, memory)
        
        action_map = {
            'accelerate': Action.ACCELERATE,
            'brake': Action.BRAKE,
            'steer_left': Action.STEER_LEFT,
            'steer_right': Action.STEER_RIGHT,
            'maintain': Action.MAINTAIN,
            'emergency_stop': Action.EMERGENCY_STOP
        }
        
        return action_map.get(action_str, Action.MAINTAIN)
    
    def is_safety_action(self, action: Action) -> bool:
        """Check if action is a safety-critical action that overrides RL"""
        return action in [Action.EMERGENCY_STOP, Action.BRAKE]
    
    def reload_rules(self):
        """Reload rules from Prolog file"""
        self.prolog_engine.reload_rules()
        self.safe_distance = self.prolog_engine.get_constant('safe_distance', SAFE_DISTANCE)
        self.critical_distance = self.prolog_engine.get_constant('critical_distance', CRITICAL_DISTANCE)


class ExperienceMemory:
    """Memory system for learning from past experiences"""
    
    def __init__(self):
        self.memory = self._load_memory()
        self.session_rewards = 0
        self.session_distance = 0
    
    def _load_memory(self) -> Dict:
        """Load memory from file"""
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._create_default_memory()
    
    def _create_default_memory(self) -> Dict:
        """Create default memory structure"""
        return {
            "crashes": [],
            "successful_overpasses": 0,
            "safe_lanes": [0, 1, 2],
            "danger_zones": [],
            "traffic_patterns": {},
            "total_distance": 0,
            "total_sessions": 0,
            "lane_change_successes": 0,
            "lane_change_failures": 0,
            "obstacles_avoided": 0,
            "pedestrians_yielded": 0,
            "slow_cars_passed": 0,
            "rewards_accumulated": 0,
            "rl_episodes": 0
        }
    
    def save_memory(self):
        """Save memory to file"""
        self.memory['rewards_accumulated'] += self.session_rewards
        self.memory['total_distance'] += self.session_distance
        self.memory['total_sessions'] += 1
        
        try:
            os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
            with open(MEMORY_FILE, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")
    
    def record_crash(self, lane: int, location: Tuple[float, float]):
        """Record a crash event"""
        self.memory['crashes'].append({
            'lane': lane,
            'location': [location[0], location[1]]
        })
        self.session_rewards += CRASH_PENALTY
        
        if lane in self.memory['safe_lanes']:
            self.memory['safe_lanes'].remove(lane)
        
        zone_exists = False
        for zone in self.memory['danger_zones']:
            if abs(zone['x'] - location[0]) < 100 and zone.get('lane') == lane:
                zone_exists = True
                zone['count'] = zone.get('count', 1) + 1
                break
        
        if not zone_exists:
            self.memory['danger_zones'].append({
                'x': location[0],
                'y': location[1],
                'lane': lane,
                'count': 1
            })
    
    def record_successful_pass(self):
        """Record successful obstacle avoidance"""
        self.memory['successful_overpasses'] += 1
        self.memory['obstacles_avoided'] += 1
        self.session_rewards += SAFE_PASS_REWARD
    
    def record_lane_change(self, success: bool):
        """Record lane change attempt"""
        if success:
            self.memory['lane_change_successes'] += 1
            self.session_rewards += LANE_CHANGE_REWARD
        else:
            self.memory['lane_change_failures'] += 1
            self.session_rewards -= LANE_CHANGE_REWARD // 2
    
    def record_slow_car_passed(self):
        """Record successfully passing a slow car"""
        self.memory['slow_cars_passed'] = self.memory.get('slow_cars_passed', 0) + 1
        self.session_rewards += SAFE_PASS_REWARD
    
    def record_pedestrian_yield(self):
        """Record yielding to pedestrian"""
        self.memory['pedestrians_yielded'] += 1
        self.session_rewards += SAFE_PASS_REWARD
    
    def add_smooth_driving_reward(self):
        """Reward for smooth driving"""
        self.session_rewards += SMOOTH_DRIVING_REWARD
    
    def update_distance(self, distance: float):
        """Update session distance"""
        self.session_distance += distance
    
    def increment_rl_episodes(self):
        """Increment RL episode counter"""
        self.memory['rl_episodes'] = self.memory.get('rl_episodes', 0) + 1


class MinimaxEvaluator:
    """Minimax-style evaluation for path selection with slow car handling"""
    
    def __init__(self):
        self.depth = 3
    
    def evaluate_state(self, sensor_data: Dict, current_speed: float) -> float:
        """Evaluate current state score"""
        score = 0.0
        
        front_dist = sensor_data.get('front_distance', SAFE_DISTANCE)
        if front_dist > SAFE_DISTANCE:
            score += 25  # Increased reward for safe distance
        elif front_dist > CRITICAL_DISTANCE:
            score += 10
        else:
            score -= 40  # Increased penalty for being too close
        
        left_dist = sensor_data.get('left_distance', SAFE_DISTANCE)
        right_dist = sensor_data.get('right_distance', SAFE_DISTANCE)
        score += min(left_dist, right_dist) / SAFE_DISTANCE * 15  # Increased weight for side clearance
        
        collision_risk = sensor_data.get('collision_risk', 0)
        score -= collision_risk * 300  # Tripled collision risk penalty (was 100)
        
        speed_ratio = current_speed / CAR_MAX_SPEED
        if sensor_data.get('front_distance', 0) > SAFE_DISTANCE:
            score += speed_ratio * 15
        
        if sensor_data.get('pedestrian_detected') and current_speed > 1:
            score -= 200  # Severe penalty for pedestrian risk (Increased)
        
        car_ahead_speed = sensor_data.get('car_ahead_speed', 10.0)
        if car_ahead_speed < 2.0 and front_dist < 200:
            score -= 25
        
        return score
    
    def evaluate_action(self, action: Action, sensor_data: Dict, 
                       current_lane: int, memory: Dict) -> float:
        """Evaluate a specific action with slow car consideration"""
        score = 0.0
        
        car_ahead_speed = sensor_data.get('car_ahead_speed', 10.0)
        front_dist = sensor_data.get('front_distance', SAFE_DISTANCE)
        
        if action == Action.ACCELERATE:
            if sensor_data.get('front_distance', 0) > SAFE_DISTANCE:
                score += 15
            else:
                score -= 20
        
        elif action == Action.BRAKE:
            if sensor_data.get('front_distance', 0) < SAFE_DISTANCE:
                score += 20
            else:
                score -= 5
        
        elif action == Action.STEER_LEFT:
            if current_lane > 0 and sensor_data.get('left_lane_clear', False):
                score += 15
                
                if car_ahead_speed < 2.0 and front_dist < 200:
                    score += 25
                
                danger_zones = memory.get('danger_zones', [])
                for zone in danger_zones:
                    if zone.get('lane') == current_lane - 1:
                        score -= 10
            else:
                score -= 25
        
        elif action == Action.STEER_RIGHT:
            if current_lane < NUM_LANES - 1 and sensor_data.get('right_lane_clear', False):
                score += 15
                
                if car_ahead_speed < 2.0 and front_dist < 200:
                    score += 25
                
                danger_zones = memory.get('danger_zones', [])
                for zone in danger_zones:
                    if zone.get('lane') == current_lane + 1:
                        score -= 10
            else:
                score -= 25
        
        elif action == Action.EMERGENCY_STOP:
            if sensor_data.get('collision_risk', 0) > 0.7:
                score += 30
            else:
                score -= 10
        
        return score
    
    def get_best_action(self, sensor_data: Dict, current_lane: int, 
                        memory: Dict) -> Tuple[Action, float]:
        """Get best action using minimax evaluation"""
        best_action = Action.MAINTAIN
        best_score = float('-inf')
        
        for action in Action:
            score = self.evaluate_action(action, sensor_data, current_lane, memory)
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action, best_score


class TeslaBrain:
    """
    Main AI brain combining all decision systems.
    
    Decision Pipeline:
    1. Sensors collect data → Discretized State
    2. Prolog Safety Rules validate/override
    3. Final action is executed
    """
    
    def __init__(self):
        self.reasoner = PrologReasoner()
        self.memory = ExperienceMemory()
        self.minimax = MinimaxEvaluator()
        
        self.current_action = Action.MAINTAIN
        self.last_action = Action.MAINTAIN
        self.action_confidence = 0.0
        
        self.decision_explanation = ""
        self.learning_status = "Initializing..."
        self.decision_source = "prolog"  # 'prolog', 'minimax', 'safety_override'
        
        self.frames_since_update = 0
        self.update_interval = 2
        
        # Track for rewards
        self.last_sensor_data: Optional[Dict] = None
        self.passed_slow_car = False
        self.lane_change_success = False
    
    def update(self, sensor_data: Dict) -> Action:
        """
        Main update function with safety override.
        
        Pipeline:
        1. Prolog evaluates safety
        2. If Prolog says brake/emergency_stop → override
        3. Otherwise use Prolog/Minimax
        """
        self.frames_since_update += 1
        
        if self.frames_since_update < self.update_interval:
            return self.current_action
        
        self.frames_since_update = 0
        self.last_action = self.current_action
        
        # ==============================
        # STEP 1: Get Prolog Safety Action
        # ==============================
        prolog_action = self.reasoner.query_action(sensor_data, self.memory.memory)
        prolog_is_safety = self.reasoner.is_safety_action(prolog_action)
        
        # ==============================
        # STEP 2: Decision Pipeline
        # ==============================
        current_lane = sensor_data.get('current_lane', 1)
        car_ahead_speed = sensor_data.get('car_ahead_speed', 10.0)
        car_ahead_halted = sensor_data.get('car_ahead_halted', False)
        car_ahead_slow = sensor_data.get('car_ahead_slow', False)
        front_dist = sensor_data.get('front_distance', 300)
        
        # Priority 1: Pedestrian detection (highest priority)
        if sensor_data.get('pedestrian_detected', False):
            ped_dist = sensor_data.get('pedestrian_distance', 300)
            if ped_dist < CRITICAL_DISTANCE:
                self.current_action = Action.EMERGENCY_STOP
                self.action_confidence = 1.0
                self.decision_explanation = "Emergency: Pedestrian detected!"
                self.decision_source = "safety_override"
            elif ped_dist < SAFE_DISTANCE:
                self.current_action = Action.BRAKE
                self.action_confidence = 0.95
                self.decision_explanation = "Slowing: Pedestrian ahead"
                self.decision_source = "safety_override"
            else:
                self.current_action = prolog_action
                self.action_confidence = 0.8
                self.decision_explanation = f"Logic: {prolog_action.value}"
                self.decision_source = "prolog"
        
        # Priority 2: Prolog safety override (CRITICAL)
        elif prolog_is_safety:
            self.current_action = prolog_action
            self.action_confidence = 1.0
            self.decision_explanation = f"Safety override: {prolog_action.value}"
            self.decision_source = "safety_override"
        
        # Priority 3: Handle slow/halted car with lane change (Prolog-guided)
        elif car_ahead_halted and front_dist < 250:  # Increased lookahead from 200
            left_clear = sensor_data.get('left_lane_clear', False)
            right_clear = sensor_data.get('right_lane_clear', False)
            
            if left_clear and current_lane > 0:
                self.current_action = Action.STEER_LEFT
                self.action_confidence = 0.98
                self.decision_explanation = "Passing halted car: left lane (Early)"
                self.decision_source = "prolog"
            elif right_clear and current_lane < NUM_LANES - 1:
                self.current_action = Action.STEER_RIGHT
                self.action_confidence = 0.98
                self.decision_explanation = "Passing halted car: right lane (Early)"
                self.decision_source = "prolog"
            else:
                self.current_action = Action.BRAKE
                self.action_confidence = 0.95
                self.decision_explanation = "Halted car ahead: no lane available"
                self.decision_source = "prolog"
        
        elif car_ahead_slow and front_dist < 220:  # Increased lookahead from 180
            left_clear = sensor_data.get('left_lane_clear', False)
            right_clear = sensor_data.get('right_lane_clear', False)
            
            if left_clear and current_lane > 0:
                self.current_action = Action.STEER_LEFT
                self.action_confidence = 0.95
                self.decision_explanation = "Passing slow car: left lane"
                self.decision_source = "prolog"
            elif right_clear and current_lane < NUM_LANES - 1:
                self.current_action = Action.STEER_RIGHT
                self.action_confidence = 0.95
                self.decision_explanation = "Passing slow car: right lane"
                self.decision_source = "prolog"
            else:
                self.current_action = Action.BRAKE
                self.action_confidence = 0.9
                self.decision_explanation = "Slow car ahead: matching speed"
                self.decision_source = "prolog"
        
        # Priority 4: Use Prolog/Minimax for remaining cases
        elif prolog_action in [Action.STEER_LEFT, Action.STEER_RIGHT]:
            self.current_action = prolog_action
            self.action_confidence = 0.9
            self.decision_explanation = f"Lane change: {prolog_action.value}"
            self.decision_source = "prolog"
        
        else:
            minimax_action, minimax_score = self.minimax.get_best_action(
                sensor_data, current_lane, self.memory.memory
            )
            state_score = self.minimax.evaluate_state(
                sensor_data, sensor_data.get('speed', 0)
            )
            
            if minimax_score > state_score * 0.5:
                self.current_action = minimax_action
                self.action_confidence = min(1.0, minimax_score / 50)
                self.decision_explanation = f"Optimizing: {minimax_action.value}"
                self.decision_source = "minimax"
            else:
                self.current_action = prolog_action
                self.action_confidence = 0.8
                self.decision_explanation = f"Logic: {prolog_action.value}"
                self.decision_source = "prolog"
        
        # Store for next update
        self.last_sensor_data = sensor_data.copy()
        
        self._update_learning_status()
        
        return self.current_action
    
    def _update_learning_status(self):
        """Update learning status message"""
        sessions = self.memory.memory.get('total_sessions', 0)
        avoided = self.memory.memory.get('obstacles_avoided', 0)
        crashes = len(self.memory.memory.get('crashes', []))
        slow_passed = self.memory.memory.get('slow_cars_passed', 0)
        
        if sessions == 0:
            self.learning_status = f"First session - Learning..."
        elif crashes == 0:
            self.learning_status = f"Perfect! {avoided} obstacles, {slow_passed} slow cars"
        else:
            ratio = avoided / max(1, crashes)
            if ratio > 10:
                self.learning_status = f"Expert driver ({ratio:.1f}x)"
            elif ratio > 5:
                self.learning_status = f"Skilled ({ratio:.1f}x)"
            elif ratio > 2:
                self.learning_status = f"Improving ({ratio:.1f}x)"
            else:
                self.learning_status = f"Learning... ({ratio:.1f}x)"
    
    def record_event(self, event_type: str, **kwargs):
        """Record various events for learning (memory only)"""
        if event_type == 'crash':
            self.memory.record_crash(
                kwargs.get('lane', 1),
                kwargs.get('location', (0, 0))
            )
        
        elif event_type == 'obstacle_avoided':
            self.memory.record_successful_pass()
        
        elif event_type == 'lane_change':
            success = kwargs.get('success', True)
            self.memory.record_lane_change(success)
            self.lane_change_success = success
        
        elif event_type == 'slow_car_passed':
            self.memory.record_slow_car_passed()
            self.passed_slow_car = True
        
        elif event_type == 'pedestrian_yield':
            self.memory.record_pedestrian_yield()
        
        elif event_type == 'smooth_driving':
            self.memory.add_smooth_driving_reward()
        
        elif event_type == 'distance':
            self.memory.update_distance(kwargs.get('distance', 0))
    
    def save(self):
        """Save all learning data (memory only)"""
        self.memory.save_memory()
    
    def get_status(self) -> Dict:
        """Get current AI status for display"""
        status = {
            'action': self.current_action.value,
            'confidence': self.action_confidence,
            'explanation': self.decision_explanation,
            'learning_status': self.learning_status,
            'decision_source': self.decision_source,
            'total_sessions': self.memory.memory.get('total_sessions', 0),
            'obstacles_avoided': self.memory.memory.get('obstacles_avoided', 0),
            'crashes': len(self.memory.memory.get('crashes', [])),
            'session_rewards': self.memory.session_rewards,
            'slow_cars_passed': self.memory.memory.get('slow_cars_passed', 0)
        }
        
        return status
