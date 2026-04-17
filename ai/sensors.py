"""
TESLA Sensor Simulation Module
Simulates LIDAR-like sensors, lane detection, and collision prediction
Updated with slow/halted car detection for improved lane switching
"""

import math
import pygame
from typing import List, Dict, Tuple, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SENSOR_RANGE, SENSOR_ANGLE_SPREAD, NUM_SENSOR_RAYS,
    LANE_WIDTH, NUM_LANES, ROAD_Y_START, SAFE_DISTANCE, CRITICAL_DISTANCE,
    COLORS
)


class SensorRay:
    """Individual sensor ray for distance detection"""
    
    def __init__(self, angle_offset: float):
        self.angle_offset = angle_offset
        self.distance = SENSOR_RANGE
        self.hit_point: Optional[Tuple[int, int]] = None
        self.detected_object: Optional[str] = None
        self.detected_object_data: Optional[Dict] = None
    
    def cast(self, start_pos: Tuple[float, float], car_angle: float,
             obstacles: List[pygame.Rect], traffic_cars: List,
             pedestrians: List) -> float:
        """Cast ray and detect nearest obstacle"""
        angle = math.radians(car_angle + self.angle_offset)
        self.distance = SENSOR_RANGE
        self.hit_point = None
        self.detected_object = None
        self.detected_object_data = None
        
        for dist in range(10, SENSOR_RANGE, 5):
            check_x = start_pos[0] + math.cos(angle) * dist
            check_y = start_pos[1] - math.sin(angle) * dist
            check_point = (int(check_x), int(check_y))
            
            for obstacle in obstacles:
                if obstacle.collidepoint(check_point):
                    self.distance = dist
                    self.hit_point = check_point
                    self.detected_object = 'obstacle'
                    return self.distance
            
            for car in traffic_cars:
                if hasattr(car, 'rect') and car.rect.collidepoint(check_point):
                    self.distance = dist
                    self.hit_point = check_point
                    self.detected_object = 'car'
                    # Store car data for speed detection
                    self.detected_object_data = {
                        'speed': getattr(car, 'speed', 5.0),
                        'is_halted': getattr(car, 'is_halted', False),
                        'is_slow': getattr(car, 'is_slow', False)
                    }
                    return self.distance
            
            for ped in pedestrians:
                if hasattr(ped, 'rect') and ped.rect.collidepoint(check_point):
                    self.distance = dist
                    self.hit_point = check_point
                    self.detected_object = 'pedestrian'
                    return self.distance
        
        return self.distance


class SensorSystem:
    """Complete sensor system for the Tesla vehicle with enhanced lane detection"""
    
    def __init__(self):
        self.rays: List[SensorRay] = []
        self._create_sensor_rays()
        
        self.front_distance = SENSOR_RANGE
        self.left_distance = SENSOR_RANGE
        self.right_distance = SENSOR_RANGE
        self.rear_distance = SENSOR_RANGE
        
        # Diagonal distances for lane change detection
        self.left_front_distance = SENSOR_RANGE
        self.right_front_distance = SENSOR_RANGE
        self.left_rear_distance = SENSOR_RANGE
        self.right_rear_distance = SENSOR_RANGE
        
        self.current_lane = 1
        self.lane_position = 0.5
        
        self.collision_risk = 0.0
        self.time_to_collision = float('inf')
        
        self.nearest_obstacle_distance = SENSOR_RANGE
        self.nearest_obstacle_type: Optional[str] = None
        
        self.pedestrian_detected = False
        self.pedestrian_distance = SENSOR_RANGE
        
        # Track car ahead speed for lane switching decisions
        self.car_ahead_speed = 10.0
        self.car_ahead_halted = False
        self.car_ahead_slow = False
        
        # Track if a car is directly in front (not just obstacle)
        self.car_directly_ahead = False
        self.car_ahead_distance = SENSOR_RANGE
    
    def _create_sensor_rays(self):
        """Create sensor rays with spread angles including diagonal for lane detection"""
        # Reduced spread for main front sensors to avoid detecting cars in adjacent lanes as "ahead"
        # Using config SENSOR_ANGLE_SPREAD
        angle_step = SENSOR_ANGLE_SPREAD * 2 / (NUM_SENSOR_RAYS - 1) if NUM_SENSOR_RAYS > 1 else 0
        for i in range(NUM_SENSOR_RAYS):
            angle = -SENSOR_ANGLE_SPREAD + (i * angle_step)
            self.rays.append(SensorRay(angle))
        
        # Side sensors (perpendicular)
        self.rays.append(SensorRay(90))   # Left
        self.rays.append(SensorRay(-90))  # Right
        self.rays.append(SensorRay(180))  # Rear
        
        # Diagonal sensors for lane change safety (CRITICAL for detecting cars in adjacent lanes)
        self.rays.append(SensorRay(60))   # Left-front diagonal
        self.rays.append(SensorRay(-60))  # Right-front diagonal
        self.rays.append(SensorRay(120))  # Left-rear diagonal  
        self.rays.append(SensorRay(-120)) # Right-rear diagonal
    
    def update(self, car_pos: Tuple[float, float], car_angle: float,
               car_speed: float, obstacles: List[pygame.Rect],
               traffic_cars: List, pedestrians: List,
               traffic_lights: List = None) -> Dict:
        """Update all sensor readings with enhanced lane detection"""
        
        for ray in self.rays:
            ray.cast(car_pos, car_angle, obstacles, traffic_cars, pedestrians)
        
        front_rays = self.rays[:NUM_SENSOR_RAYS]
        self.front_distance = min(ray.distance for ray in front_rays)
        
        # Perpendicular sensors
        self.left_distance = self.rays[NUM_SENSOR_RAYS].distance
        self.right_distance = self.rays[NUM_SENSOR_RAYS + 1].distance
        self.rear_distance = self.rays[NUM_SENSOR_RAYS + 2].distance
        
        # Diagonal sensors for lane change safety
        self.left_front_distance = self.rays[NUM_SENSOR_RAYS + 3].distance
        self.right_front_distance = self.rays[NUM_SENSOR_RAYS + 4].distance
        self.left_rear_distance = self.rays[NUM_SENSOR_RAYS + 5].distance
        self.right_rear_distance = self.rays[NUM_SENSOR_RAYS + 6].distance
        
        self._detect_lane(car_pos)
        self._calculate_collision_risk(car_speed)
        self._find_nearest_obstacle()
        self._detect_pedestrians(car_pos, pedestrians)
        
        # Enhanced car detection
        self._detect_car_ahead_speed()
        self._detect_car_directly_ahead(traffic_cars, car_pos)
        
        return self.get_sensor_data()
    
    def _detect_lane(self, car_pos: Tuple[float, float]):
        """Detect current lane based on car position"""
        road_y = car_pos[1] - ROAD_Y_START
        if road_y < 0:
            self.current_lane = 0
        elif road_y >= LANE_WIDTH * NUM_LANES:
            self.current_lane = NUM_LANES - 1
        else:
            self.current_lane = int(road_y / LANE_WIDTH)
            self.lane_position = (road_y % LANE_WIDTH) / LANE_WIDTH
    
    def _calculate_collision_risk(self, car_speed: float):
        """Calculate collision risk based on distance and speed"""
        if self.front_distance < CRITICAL_DISTANCE:
            self.collision_risk = 1.0
        elif self.front_distance < SAFE_DISTANCE:
            self.collision_risk = 1.0 - (self.front_distance - CRITICAL_DISTANCE) / (SAFE_DISTANCE - CRITICAL_DISTANCE)
        else:
            self.collision_risk = 0.0
        
        if car_speed > 0:
            self.time_to_collision = self.front_distance / (car_speed * 10)
        else:
            self.time_to_collision = float('inf')
    
    def _find_nearest_obstacle(self):
        """Find the nearest detected obstacle"""
        self.nearest_obstacle_distance = SENSOR_RANGE
        self.nearest_obstacle_type = None
        
        for ray in self.rays:
            if ray.distance < self.nearest_obstacle_distance and ray.detected_object:
                self.nearest_obstacle_distance = ray.distance
                self.nearest_obstacle_type = ray.detected_object
    
    def _detect_pedestrians(self, car_pos: Tuple[float, float], pedestrians: List):
        """Detect pedestrians in the path"""
        self.pedestrian_detected = False
        self.pedestrian_distance = SENSOR_RANGE
        
        for ped in pedestrians:
            if hasattr(ped, 'rect'):
                dx = ped.rect.centerx - car_pos[0]
                dy = abs(ped.rect.centery - car_pos[1])
                
                if dx > 0 and dx < SENSOR_RANGE:
                    in_car_lane = dy < LANE_WIDTH * 1.5
                    
                    if in_car_lane:
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist < self.pedestrian_distance:
                            self.pedestrian_distance = dist
                            if dist < SAFE_DISTANCE * 1.5:
                                self.pedestrian_detected = True
    
    def _detect_car_ahead_speed(self):
        """Detect the speed of the car directly ahead for lane switching decisions"""
        self.car_ahead_speed = 10.0
        self.car_ahead_halted = False
        self.car_ahead_slow = False
        
        front_rays = self.rays[:NUM_SENSOR_RAYS]
        for ray in front_rays:
            if ray.detected_object == 'car' and ray.detected_object_data:
                data = ray.detected_object_data
                self.car_ahead_speed = data.get('speed', 10.0)
                self.car_ahead_halted = data.get('is_halted', False) or self.car_ahead_speed < 0.5
                self.car_ahead_slow = data.get('is_slow', False) or self.car_ahead_speed < 2.5
                break
    
    def _detect_car_directly_ahead(self, traffic_cars: List, car_pos: Tuple[float, float]):
        """Detect if there's a car directly in the same lane ahead"""
        self.car_directly_ahead = False
        self.car_ahead_distance = SENSOR_RANGE
        
        for car in traffic_cars:
            if hasattr(car, 'rect') and hasattr(car, 'lane'):
                # Check if car is ahead
                if car.rect.x > car_pos[0]:
                    dist = car.rect.x - car_pos[0]
                    # Check if in same lane (within tolerance)
                    car_lane_y = ROAD_Y_START + (car.lane * LANE_WIDTH) + LANE_WIDTH // 2
                    if abs(car_pos[1] - car_lane_y) < LANE_WIDTH:
                        if dist < self.car_ahead_distance:
                            self.car_ahead_distance = dist
                            self.car_directly_ahead = True
                            # Also update speed from this car
                            self.car_ahead_speed = getattr(car, 'speed', 5.0)
                            self.car_ahead_halted = self.car_ahead_speed < 0.5
                            self.car_ahead_slow = self.car_ahead_speed < 2.5
    
    def _is_lane_clear_for_change(self, direction: str) -> bool:
        """Check if a lane is clear for a lane change - SAFER MODE"""
        # LOGIC: Check side AND diagonal sensors for better coverage
        # Increased safety buffers and added diagonal checks
        # UPDATED: Significantly increased thresholds to prevent overlapping
        
        # Minimum clear distance needed (approx 2.5 car lengths)
        SIDE_CLEARANCE = 140  
        DIAG_CLEARANCE = 160
        
        if direction == 'left':
            side_clear = self.left_distance > SIDE_CLEARANCE
            front_diag_clear = self.left_front_distance > DIAG_CLEARANCE
            rear_diag_clear = self.left_rear_distance > SIDE_CLEARANCE # Rear check is crucial
            
            # Extra check: If there's an obstacle very close in the target lane type
            # (Simplified check using raw rays if needed, but distances usually suffice)
            
            return side_clear and front_diag_clear and rear_diag_clear
        else:  # right
            side_clear = self.right_distance > SIDE_CLEARANCE
            front_diag_clear = self.right_front_distance > DIAG_CLEARANCE
            rear_diag_clear = self.right_rear_distance > SIDE_CLEARANCE
            return side_clear and front_diag_clear and rear_diag_clear
    
    def get_sensor_data(self) -> Dict:
        """Get all sensor data as dictionary with enhanced lane detection"""
        return {
            'front_distance': self.front_distance,
            'left_distance': self.left_distance,
            'right_distance': self.right_distance,
            'rear_distance': self.rear_distance,
            'left_front_distance': self.left_front_distance,
            'right_front_distance': self.right_front_distance,
            'current_lane': self.current_lane,
            'lane_position': self.lane_position,
            'collision_risk': self.collision_risk,
            'time_to_collision': self.time_to_collision,
            'nearest_obstacle_distance': self.nearest_obstacle_distance,
            'nearest_obstacle_type': self.nearest_obstacle_type,
            'pedestrian_detected': self.pedestrian_detected,
            'pedestrian_distance': self.pedestrian_distance,
            # Enhanced lane clear detection using diagonal sensors
            'left_lane_clear': self._is_lane_clear_for_change('left'),
            'right_lane_clear': self._is_lane_clear_for_change('right'),
            'car_ahead_speed': self.car_ahead_speed,
            'car_ahead_halted': self.car_ahead_halted,
            'car_ahead_slow': self.car_ahead_slow,
            'car_directly_ahead': self.car_directly_ahead,
            'car_ahead_distance': self.car_ahead_distance,
        }
    
    def draw_sensors(self, screen: pygame.Surface, car_pos: Tuple[float, float], car_angle: float):
        """Draw sensor rays for visualization"""
        for ray in self.rays:
            angle = math.radians(car_angle + ray.angle_offset)
            end_x = car_pos[0] + math.cos(angle) * ray.distance
            end_y = car_pos[1] - math.sin(angle) * ray.distance
            
            if ray.detected_object:
                color = COLORS['warning']
            else:
                color = (*COLORS['neon_cyan'][:3], 100)
            
            if ray.distance < SENSOR_RANGE:
                pygame.draw.line(screen, color, car_pos, (end_x, end_y), 1)
                if ray.hit_point:
                    pygame.draw.circle(screen, COLORS['warning'], ray.hit_point, 4)
