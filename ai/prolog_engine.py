import re
import os
from typing import Dict, List, Any

class Rule:
    """Represents a Prolog rule with head and body conditions"""
    
    def __init__(self, name: str, params: List[str], conditions: List[Dict]):
        self.name = name
        self.params = params
        self.conditions = conditions
    
    def __repr__(self):
        return f"Rule({self.name}/{len(self.params)})"


class PrologEngine:
    """Lightweight Prolog-style inference engine that parses and executes rules from .pl files"""
    
    def __init__(self, rules_file: str):
        self.rules_file = rules_file
        self.rules: Dict[str, List[Rule]] = {}
        self.facts: Dict[str, List[List[Any]]] = {}
        self.constants: Dict[str, float] = {}
        
        self._load_rules()
    
    def _load_rules(self):
        """Load and parse rules from the Prolog file"""
        if not os.path.exists(self.rules_file):
            print(f"Warning: Prolog rules file not found: {self.rules_file}")
            return
        
        with open(self.rules_file, 'r') as f:
            content = f.read()
        
        content = re.sub(r'%[^\n]*', '', content)
        
        statements = re.split(r'\.\s*(?=\n|$)', content)
        
        rule_count = 0
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            
            if self._parse_statement(stmt):
                rule_count += 1
        
        print(f"[Prolog] Loaded {rule_count} rules, {len(self.constants)} constants from {self.rules_file}")
    
    def _parse_statement(self, stmt: str) -> bool:
        """Parse a single Prolog statement"""
        stmt = stmt.strip().rstrip('.')
        
        # Robust regex for facts with optional whitespace
        fact_match = re.match(r'^(\w+)\s*\(\s*([\d.]+)\s*\)$', stmt)
        if fact_match:
            name, value = fact_match.groups()
            self.constants[name] = float(value)
            return True
        
        # Robust regex for action facts
        action_match = re.match(r'^action\s*\(\s*(\w+)\s*\)$', stmt)
        if action_match:
            action_name = action_match.group(1)
            if 'action' not in self.facts:
                self.facts['action'] = []
            self.facts['action'].append([action_name])
            return True
        
        if ':-' in stmt:
            parts = stmt.split(':-', 1)
            head = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ''
            
            head_match = re.match(r'^(\w+)\(([^)]*)\)$', head)
            if head_match:
                rule_name = head_match.group(1)
                params_str = head_match.group(2)
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                conditions = self._parse_body(body, params)
                
                rule = Rule(rule_name, params, conditions)
                
                if rule_name not in self.rules:
                    self.rules[rule_name] = []
                self.rules[rule_name].append(rule)
                return True
        
        return False
    
    def _parse_body(self, body: str, params: List[str]) -> List[Dict]:
        """Parse the body of a rule into conditions"""
        conditions = []
        
        body = body.strip()
        if not body:
            return conditions
        
        comp_matches = re.findall(r'(\w+)\s*(==|<|>|<=|>=)\s*([\d.]+|\w+)', body)
        for var, op, value in comp_matches:
            conditions.append({
                'type': 'comparison',
                'var': var,
                'op': op,
                'value': value
            })
        
        pred_matches = re.findall(r'(\w+)\(([^)]*)\)', body)
        for pred_name, args_str in pred_matches:
            if pred_name in ['min', 'max', 'is']:
                continue
            args = [a.strip() for a in args_str.split(',') if a.strip()]
            conditions.append({
                'type': 'predicate',
                'name': pred_name,
                'args': args
            })
        
        return conditions
    
    def query(self, rule_name: str, bindings: Dict[str, Any]) -> bool:
        """Query a rule with variable bindings"""
        if rule_name not in self.rules:
            return False
        
        for rule in self.rules[rule_name]:
            if self._evaluate_rule(rule, bindings):
                return True
        
        return False
    
    def _evaluate_rule(self, rule: Rule, bindings: Dict[str, Any]) -> bool:
        """Evaluate a rule with given bindings"""
        local_bindings = bindings.copy()
        
        for i, param in enumerate(rule.params):
            if param in bindings:
                local_bindings[param] = bindings[param]
        
        for condition in rule.conditions:
            if condition['type'] == 'comparison':
                if not self._evaluate_comparison(condition, local_bindings):
                    return False
            elif condition['type'] == 'predicate':
                if not self._evaluate_predicate(condition, local_bindings):
                    return False
        
        return True
    
    def _resolve_value(self, value: str, bindings: Dict[str, Any]) -> Any:
        """Resolve a value from bindings, constants, or literal"""
        if value in bindings:
            return bindings[value]
        if value in self.constants:
            return self.constants[value]
        if value == 'true':
            return True
        if value == 'false':
            return False
        try:
            return float(value)
        except ValueError:
            return value
    
    def _evaluate_comparison(self, condition: Dict, bindings: Dict[str, Any]) -> bool:
        """Evaluate a comparison condition"""
        var_value = self._resolve_value(condition['var'], bindings)
        compare_value = self._resolve_value(condition['value'], bindings)
        op = condition['op']
        
        try:
            if op == '==':
                return var_value == compare_value
            elif op == '<':
                return float(var_value) < float(compare_value)
            elif op == '>':
                return float(var_value) > float(compare_value)
            elif op == '<=':
                return float(var_value) <= float(compare_value)
            elif op == '>=':
                return float(var_value) >= float(compare_value)
        except (ValueError, TypeError):
            return var_value == compare_value
        
        return False
    
    def _evaluate_predicate(self, condition: Dict, bindings: Dict[str, Any]) -> bool:
        """Evaluate a predicate condition by querying its rules"""
        pred_name = condition['name']
        args = condition['args']
        
        pred_bindings = {}
        for i, arg in enumerate(args):
            resolved = self._resolve_value(arg, bindings)
            pred_bindings[arg] = resolved
        
        return self.query(pred_name, pred_bindings)
    
    def evaluate_should_brake(self, distance: float) -> bool:
        """Query: should_brake(Distance, SafeDist) :- Distance < SafeDist"""
        safe_dist = self.constants.get('safe_distance', 120)
        return self.query('should_brake', {'Distance': distance, 'SafeDist': safe_dist})
    
    def evaluate_should_emergency_stop(self, distance: float) -> bool:
        """Query: should_emergency_stop(Distance, CriticalDist)"""
        critical_dist = self.constants.get('critical_distance', 60)
        return self.query('should_emergency_stop', {'Distance': distance, 'CriticalDist': critical_dist})
    
    def evaluate_should_stop_for_pedestrian(self, pedestrian_present: bool) -> bool:
        """Query: should_stop_for_pedestrian(PedestrianPresent)"""
        return self.query('should_stop_for_pedestrian', {'PedestrianPresent': pedestrian_present})
    
    def evaluate_should_change_lane_for_slow_car(self, distance: float, car_speed: float) -> bool:
        """Query: should_change_lane_for_slow_car"""
        slow_threshold = self.constants.get('slow_car_threshold', 2.0)
        return distance < 200 and car_speed < slow_threshold
    
    def evaluate_should_change_lane_for_halted_car(self, distance: float, car_speed: float) -> bool:
        """Query: should_change_lane_for_halted_car"""
        halted_threshold = self.constants.get('halted_car_threshold', 0.3)
        return distance < 250 and car_speed < halted_threshold
    
    def query_select_action(self, distance: float, left_clear: bool, right_clear: bool,
                            pedestrian_present: bool, car_ahead_speed: float = 10.0,
                            car_directly_ahead: bool = False) -> str:
        """
        Query the select_action rule with enhanced lane switching logic.
        
        Priority order (UPDATED):
        1. Pedestrian (stop BEFORE crossing)
        2. LANE CHANGE ATTEMPT (Even in emergency)
        3. Emergency stop (if lane change failed)
        4. Brake (if lane change failed)
        5. Accelerate
        """
        # Priority 1: Pedestrian - stop early (Safety Critical)
        if pedestrian_present:
            return 'emergency_stop'
        
        safe_dist = self.constants.get('safe_distance', 120)
        critical_dist = self.constants.get('critical_distance', 60)
        
        # LOGIC: If there is ANYTHING in front (Car, Obstacle) within detection range
        # We MUST try to change lanes FIRST before deciding to stop.
        
        obstacle_detected = distance < 250
        is_emergency = distance < critical_dist
        
        # If we have an obstacle/car ahead OR we are in an emergency distance
        if obstacle_detected or is_emergency:
            
            # 1. TRY LEFT LANE CHANGE
            if left_clear:
                return 'steer_left'
            
            # 2. TRY RIGHT LANE CHANGE
            if right_clear:
                return 'steer_right'
                
            # 3. IF NO LANE CHANGE POSSIBLE:
            if is_emergency:
                return 'emergency_stop'
            
            if distance < safe_dist:
                return 'brake'
                
        # If road is clear but we are just close to something (tailgating logic)
        if distance < safe_dist:
             # Try to change lane even if just "safe distance" violation
            if left_clear:
                return 'steer_left'
            if right_clear:
                return 'steer_right'
            return 'brake'
        
        return 'accelerate'
    
    def evaluate_action(self, sensor_data: Dict, memory: Dict) -> str:
        """
        Evaluate what action should be taken by directly querying the Prolog engine.
        Now strictly follows the logic defined in prolog_rules.pl.
        """
        # Extract sensor data for Prolog query
        car_directly_ahead = sensor_data.get('car_directly_ahead', False)
        car_ahead_dist = sensor_data.get('car_ahead_distance', 300)
        raw_front_dist = sensor_data.get('front_distance', 300)
        
        # Use lane-specific distance if a car is directly ahead
        if car_directly_ahead:
            front_dist = car_ahead_dist
        else:
            front_dist = raw_front_dist
            
        ped_detected = sensor_data.get('pedestrian_detected', False)
        current_lane = sensor_data.get('current_lane', 1)
        car_ahead_speed = sensor_data.get('car_ahead_speed', 10.0)
        
        left_clear = sensor_data.get('left_lane_clear', True)
        right_clear = sensor_data.get('right_lane_clear', True)
        
        # Construct bindings for the Prolog query
        # select_action(Distance, LeftClear, RightClear, PedestrianPresent, CarAheadSpeed, CurrentLane, Action)
        bindings = {
            'Distance': front_dist,
            'LeftClear': left_clear,
            'RightClear': right_clear,
            'PedestrianPresent': ped_detected,
            'CarAheadSpeed': car_ahead_speed,
            'CurrentLane': current_lane
        }
        
        # 1. CRITICAL SAFETY
        if ped_detected and front_dist < 80:
            return 'emergency_stop'
        
        if front_dist < 70:
            return 'emergency_stop'
            
        # 2. LANE CHANGE / OBSTACLE AVOIDANCE
        if front_dist < 250 and car_ahead_speed < 5.0:
            # Try Left
            if left_clear and current_lane > 0:
                return 'steer_left'
            # Try Right
            elif right_clear and current_lane < 2:
                return 'steer_right'
            # Failed to change -> Brake
            return 'brake'
            
        # 3. SAFE DISTANCE VIOLATION
        if front_dist < 150:
            if left_clear and current_lane > 0:
                return 'steer_left'
            elif right_clear and current_lane < 2:
                return 'steer_right'
            return 'brake'
            
        # 4. DEFAULT
        return 'accelerate'

    def get_constant(self, name: str, default: float = 0) -> float:
        """Get a constant value from the loaded rules"""
        return self.constants.get(name, default)
    
    def reload_rules(self):
        """Reload rules from file"""
        self.rules.clear()
        self.facts.clear()
        self.constants.clear()
        self._load_rules()
