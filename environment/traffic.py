"""
TESLA Traffic Module
Manages other vehicles on the road with realistic behavior
- Pre-existing traffic cars at simulation start
- Collision avoidance between bot vehicles
- Pedestrian safety - vehicles stop for pedestrians
"""

import pygame
import random
import math
from typing import List, Optional, Tuple, TYPE_CHECKING
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, LANE_WIDTH, NUM_LANES,
    ROAD_Y_START, ROAD_HEIGHT, CAR_WIDTH, CAR_LENGTH, MAX_TRAFFIC_CARS,
    TRAFFIC_MIN_SPEED, TRAFFIC_MAX_SPEED, SAFE_DISTANCE, CRITICAL_DISTANCE,
    TRAFFIC_MIN_SPAWN_DISTANCE, TRAFFIC_SPAWN_AHEAD_DISTANCE
)

if TYPE_CHECKING:
    from environment.pedestrians import Pedestrian


class TrafficCar:
    """Other vehicles in traffic"""
    
    CAR_COLORS = [
        (180, 50, 50),
        (50, 100, 180),
        (80, 80, 90),
        (200, 200, 200),
        (50, 50, 60),
        (150, 120, 80),
        (100, 150, 100),
    ]
    
    def __init__(self, x: float, lane: int, speed: float):
        self.x = x
        self.lane = lane
        self.speed = speed
        self.base_speed = speed
        
        self.y = ROAD_Y_START + (lane * LANE_WIDTH) + (LANE_WIDTH - CAR_WIDTH) // 2
        
        self.width = CAR_WIDTH
        self.length = CAR_LENGTH - 10
        
        self.color = random.choice(self.CAR_COLORS)
        
        self.braking = False
        self.brake_timer = 0
        self.sudden_brake_chance = 0.001
        
        # Track if this car is halted or slow
        self.is_halted = False
        self.is_slow = False
        
        # Pedestrian avoidance state
        self.stopping_for_pedestrian = False
        
        self.rect = pygame.Rect(self.x, self.y, self.length, self.width)
    
    def _check_pedestrian_ahead(self, pedestrians: List['Pedestrian']) -> bool:
        """Check if there's a pedestrian crossing ahead in this car's path"""
        for ped in pedestrians:
            if not ped.is_on_road():
                continue
            # Check if pedestrian is ahead of this car
            if ped.x > self.x and ped.x < self.x + SAFE_DISTANCE * 1.5:
                # Check if pedestrian is in same lane area (vertically)
                ped_center_y = ped.y + ped.height // 2
                car_top = self.y
                car_bottom = self.y + self.width
                # Add margin for safety
                if car_top - 30 <= ped_center_y <= car_bottom + 30:
                    return True
        return False
    
    def update(self, dt: float, traffic_cars: List['TrafficCar'], pedestrians: List['Pedestrian'] = None):
        """Update traffic car position and behavior with collision avoidance"""
        if pedestrians is None:
            pedestrians = []
        
        # Check for pedestrians first - highest priority
        self.stopping_for_pedestrian = self._check_pedestrian_ahead(pedestrians)
        
        if self.stopping_for_pedestrian:
            # Emergency stop for pedestrian
            self.speed = max(0, self.speed - 0.3)
            self.braking = True
        elif random.random() < self.sudden_brake_chance:
            self.braking = True
            self.brake_timer = random.randint(60, 180)
        
        if self.braking and not self.stopping_for_pedestrian:
            self.brake_timer -= 1
            if self.brake_timer <= 0:
                self.braking = False
            self.speed = max(0.5, self.speed - 0.1)
        elif not self.stopping_for_pedestrian:
            if self.speed < self.base_speed:
                self.speed = min(self.base_speed, self.speed + 0.05)
        
        # Check for cars ahead in the same lane - collision avoidance
        for other in traffic_cars:
            if other is not self and other.lane == self.lane:
                distance = other.x - self.x
                if distance > 0 and distance < CRITICAL_DISTANCE:
                    # Emergency brake - very close
                    self.speed = max(0, self.speed - 0.2)
                    self.braking = True
                elif distance > 0 and distance < SAFE_DISTANCE:
                    # Slow down - moderate distance
                    self.speed = min(self.speed, other.speed * 0.9)
        
        # Update halted/slow status
        self.is_halted = self.speed < 0.3
        self.is_slow = self.speed < self.base_speed * 0.5
        
        self.x += self.speed * dt * 60
        
        self.rect = pygame.Rect(self.x, self.y, self.length, self.width)
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the traffic car"""
        screen_x = self.x - camera_x
        
        if screen_x < -self.length or screen_x > SCREEN_WIDTH + self.length:
            return
        
        shadow_rect = pygame.Rect(screen_x + 3, self.y + 3, self.length, self.width)
        pygame.draw.rect(screen, COLORS['shadow'], shadow_rect, border_radius=4)
        
        car_rect = pygame.Rect(screen_x, self.y, self.length, self.width)
        pygame.draw.rect(screen, self.color, car_rect, border_radius=5)
        
        highlight = (
            min(255, self.color[0] + 40),
            min(255, self.color[1] + 40),
            min(255, self.color[2] + 40)
        )
        pygame.draw.rect(screen, highlight, 
                        pygame.Rect(screen_x + 2, self.y + 2, self.length - 4, 4),
                        border_radius=2)
        
        windshield_color = (80, 120, 160)
        pygame.draw.rect(screen, windshield_color,
                        pygame.Rect(screen_x + self.length - 20, self.y + 5, 
                                   15, self.width - 10),
                        border_radius=3)
        
        pygame.draw.rect(screen, windshield_color,
                        pygame.Rect(screen_x + 5, self.y + 5, 12, self.width - 10),
                        border_radius=3)
        
        wheel_color = (30, 30, 35)
        pygame.draw.ellipse(screen, wheel_color,
                           (screen_x + 8, self.y - 2, 12, 6))
        pygame.draw.ellipse(screen, wheel_color,
                           (screen_x + 8, self.y + self.width - 4, 12, 6))
        pygame.draw.ellipse(screen, wheel_color,
                           (screen_x + self.length - 20, self.y - 2, 12, 6))
        pygame.draw.ellipse(screen, wheel_color,
                           (screen_x + self.length - 20, self.y + self.width - 4, 12, 6))
        
        if self.braking or self.speed < self.base_speed * 0.5:
            pygame.draw.rect(screen, (255, 50, 50),
                           pygame.Rect(screen_x, self.y + 5, 4, self.width - 10),
                           border_radius=2)
    
    def is_off_screen(self, camera_x: float) -> bool:
        """Check if car is too far behind camera"""
        return self.x < camera_x - 200


class TrafficManager:
    """Manages all traffic on the road with pre-existing cars and pedestrian safety"""
    
    def __init__(self):
        self.cars: List[TrafficCar] = []
        self.spawn_timer = 0
        self.spawn_interval = 180  # Slower respawn rate since we have initial cars
        self.initialized = False
    
    def initialize_traffic(self, player_x: float):
        """Spawn initial traffic cars at simulation start"""
        if self.initialized:
            return
        
        self.initialized = True
        
        # Spawn cars distributed across lanes at various distances ahead
        initial_positions = [
            (player_x + 200, 0),   # Close, lane 0
            (player_x + 350, 1),   # Medium, lane 1
            (player_x + 500, 2),   # Far, lane 2
            (player_x + 700, 0),   # Very far, lane 0
            (player_x + 600, 1),   # Far, lane 1
        ]
        
        for x, lane in initial_positions:
            if len(self.cars) < MAX_TRAFFIC_CARS:
                speed = random.uniform(TRAFFIC_MIN_SPEED, TRAFFIC_MAX_SPEED)
                self.cars.append(TrafficCar(x, lane, speed))
    
    def _check_spawn_valid(self, x: float, lane: int) -> bool:
        """Check if spawning at position is valid (no overlaps)"""
        for car in self.cars:
            if car.lane == lane:
                if abs(car.x - x) < TRAFFIC_MIN_SPAWN_DISTANCE:
                    return False
            else:
                if abs(car.x - x) < TRAFFIC_MIN_SPAWN_DISTANCE * 0.5:
                    return False
        return True
    
    def spawn_car(self, camera_x: float, player_x: float):
        """Spawn a new traffic car to maintain traffic density"""
        if len(self.cars) >= MAX_TRAFFIC_CARS:
            return
        
        lane_counts = [0] * NUM_LANES
        for car in self.cars:
            if 0 <= car.lane < NUM_LANES:
                lane_counts[car.lane] += 1
        
        min_count = min(lane_counts)
        available_lanes = [i for i, count in enumerate(lane_counts) if count == min_count]
        lane = random.choice(available_lanes)
        
        min_spawn_x = player_x + TRAFFIC_SPAWN_AHEAD_DISTANCE
        max_spawn_x = camera_x + SCREEN_WIDTH + 400
        
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            x = random.uniform(min_spawn_x, max_spawn_x)
            
            if self._check_spawn_valid(x, lane):
                speed = random.uniform(TRAFFIC_MIN_SPEED, TRAFFIC_MAX_SPEED)
                self.cars.append(TrafficCar(x, lane, speed))
                return
            
            attempts += 1
    
    def update(self, dt: float, camera_x: float, player_x: float, pedestrians: List['Pedestrian'] = None):
        """Update all traffic cars with pedestrian awareness"""
        if pedestrians is None:
            pedestrians = []
        
        # Initialize traffic on first update
        if not self.initialized:
            self.initialize_traffic(player_x)
        
        # Respawn to maintain traffic density
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_car(camera_x, player_x)
        
        # Update each car with pedestrian awareness
        for car in self.cars:
            car.update(dt, self.cars, pedestrians)
        
        # Remove cars that are too far behind or ahead
        self.cars = [car for car in self.cars 
                    if not car.is_off_screen(camera_x) and car.x < camera_x + 3000]
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw all traffic cars"""
        for car in self.cars:
            car.draw(screen, camera_x)
    
    def get_cars(self) -> List[TrafficCar]:
        """Get list of traffic cars"""
        return self.cars
    
    def get_slow_or_halted_cars(self) -> List[TrafficCar]:
        """Get list of slow or halted traffic cars (for lane change decisions)"""
        return [car for car in self.cars if car.is_slow or car.is_halted]
    
    def get_obstacle_rects(self, camera_x: float) -> List[pygame.Rect]:
        """Get collision rectangles for all visible cars"""
        rects = []
        for car in self.cars:
            screen_x = car.x - camera_x
            if -car.length < screen_x < SCREEN_WIDTH + car.length:
                rects.append(pygame.Rect(car.x, car.y, car.length, car.width))
        return rects
