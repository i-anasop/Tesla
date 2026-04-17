"""
TESLA Pedestrians Module
Manages pedestrians that cross at zebra crossings
"""

import pygame
import random
import math
from typing import List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, COLORS, LANE_WIDTH, NUM_LANES, ROAD_Y_START,
    ROAD_HEIGHT, PEDESTRIAN_SPEED, MAX_PEDESTRIANS
)


class Pedestrian:
    """Pedestrian that crosses at zebra crossings"""
    
    CLOTHES_COLORS = [
        (60, 80, 140),
        (140, 60, 80),
        (80, 140, 80),
        (100, 100, 120),
        (140, 120, 80),
        (80, 80, 100),
    ]
    
    def __init__(self, x: float, crossing_y_start: float, crossing_y_end: float,
                 direction: int = 1):
        self.x = x
        self.crossing_y_start = crossing_y_start
        self.crossing_y_end = crossing_y_end
        self.direction = direction
        
        if direction > 0:
            self.y = crossing_y_start - 30
            self.target_y = crossing_y_end + 30
        else:
            self.y = crossing_y_end + 30
            self.target_y = crossing_y_start - 30
        
        self.speed = PEDESTRIAN_SPEED * random.uniform(0.8, 1.2)
        self.walking = True
        self.waiting = False
        self.wait_timer = 0
        
        self.width = 16
        self.height = 28
        
        self.clothes_color = random.choice(self.CLOTHES_COLORS)
        self.skin_color = random.choice([
            (255, 220, 185),
            (240, 200, 160),
            (200, 160, 130),
            (160, 120, 90),
            (120, 80, 60),
        ])
        
        self.walk_cycle = 0
        self.completed = False
        
        self.rect = pygame.Rect(self.x - self.width // 2, self.y,
                               self.width, self.height)
    
    def update(self, dt: float, car_nearby: bool = False):
        """Update pedestrian position and state"""
        if self.completed:
            return
        
        # Pedestrians always move - don't wait for cars
        # The car's AI will handle collision avoidance
        if self.walking:
            self.y += self.speed * self.direction * dt * 60
            self.walk_cycle += 0.2
            
            if self.direction > 0 and self.y >= self.target_y:
                self.completed = True
            elif self.direction < 0 and self.y <= self.target_y:
                self.completed = True
        
        self.rect = pygame.Rect(self.x - self.width // 2, self.y,
                               self.width, self.height)
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the pedestrian"""
        screen_x = self.x - camera_x
        
        if screen_x < -50 or screen_x > SCREEN_WIDTH + 50:
            return
        
        leg_offset = math.sin(self.walk_cycle) * 3 if self.walking else 0
        
        pygame.draw.ellipse(screen, (20, 20, 25),
                           (screen_x - self.width // 2 + 3, self.y + 3,
                            self.width, self.height // 3))
        
        pygame.draw.ellipse(screen, self.skin_color,
                           (screen_x - 6, self.y, 12, 12))
        
        pygame.draw.rect(screen, self.clothes_color,
                        (screen_x - 6, self.y + 10, 12, 14),
                        border_radius=2)
        
        leg_color = (50, 50, 60)
        pygame.draw.rect(screen, leg_color,
                        (screen_x - 5 - leg_offset, self.y + 22, 4, 8))
        pygame.draw.rect(screen, leg_color,
                        (screen_x + 1 + leg_offset, self.y + 22, 4, 8))
        
        arm_color = self.clothes_color
        arm_swing = math.sin(self.walk_cycle) * 2 if self.walking else 0
        pygame.draw.rect(screen, arm_color,
                        (screen_x - 8, self.y + 11 - arm_swing, 3, 8))
        pygame.draw.rect(screen, arm_color,
                        (screen_x + 5, self.y + 11 + arm_swing, 3, 8))
    
    def is_on_road(self) -> bool:
        """Check if pedestrian is currently on the road"""
        road_y_top = ROAD_Y_START
        road_y_bottom = ROAD_Y_START + ROAD_HEIGHT
        return road_y_top <= self.y + self.height // 2 <= road_y_bottom


class PedestrianManager:
    """Manages all pedestrians"""
    
    def __init__(self, zebra_crossings):
        self.pedestrians: List[Pedestrian] = []
        self.zebra_crossings = zebra_crossings
        self.spawn_timer = 0
        self.spawn_interval = 90
        self.random_spawn_timer = 0
        self.random_spawn_interval = 150
    
    def spawn_pedestrian(self, camera_x: float):
        """Spawn a new pedestrian at a zebra crossing"""
        if len(self.pedestrians) >= MAX_PEDESTRIANS:
            return
        
        visible_crossings = []
        for crossing in self.zebra_crossings:
            screen_x = crossing.x - camera_x
            if -100 < screen_x < SCREEN_WIDTH + 500:
                visible_crossings.append(crossing)
        
        if not visible_crossings:
            return
        
        crossing = random.choice(visible_crossings)
        
        for ped in self.pedestrians:
            if abs(ped.x - crossing.x) < 30:
                return
        
        direction = random.choice([1, -1])
        x = crossing.x + crossing.width // 2 + random.randint(-10, 10)
        
        self.pedestrians.append(Pedestrian(
            x=x,
            crossing_y_start=ROAD_Y_START,
            crossing_y_end=ROAD_Y_START + ROAD_HEIGHT,
            direction=direction
        ))
    
    def spawn_random_pedestrian(self, camera_x: float):
        """Spawn a pedestrian at a random location on the road (jaywalking)"""
        if len(self.pedestrians) >= MAX_PEDESTRIANS:
            return
        
        x = camera_x + SCREEN_WIDTH + random.randint(100, 400)
        
        for ped in self.pedestrians:
            if abs(ped.x - x) < 100:
                return
        
        direction = random.choice([1, -1])
        
        self.pedestrians.append(Pedestrian(
            x=x,
            crossing_y_start=ROAD_Y_START,
            crossing_y_end=ROAD_Y_START + ROAD_HEIGHT,
            direction=direction
        ))
    
    def update(self, dt: float, camera_x: float, car_x: float, car_y: float):
        """Update all pedestrians"""
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if random.random() > 0.3:
                self.spawn_pedestrian(camera_x)
        
        self.random_spawn_timer += 1
        if self.random_spawn_timer >= self.random_spawn_interval:
            self.random_spawn_timer = 0
            if random.random() > 0.6:
                self.spawn_random_pedestrian(camera_x)
        
        for ped in self.pedestrians:
            car_nearby = (abs(ped.x - car_x) < 200 and 
                         ROAD_Y_START - 50 < car_y < ROAD_Y_START + ROAD_HEIGHT + 50)
            ped.update(dt, car_nearby)
        
        self.pedestrians = [ped for ped in self.pedestrians 
                           if not ped.completed and abs(ped.x - camera_x) < 1000]
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw all pedestrians"""
        for ped in self.pedestrians:
            ped.draw(screen, camera_x)
    
    def get_pedestrians(self) -> List[Pedestrian]:
        """Get list of all pedestrians"""
        return self.pedestrians
    
    def get_pedestrians_on_road(self) -> List[Pedestrian]:
        """Get pedestrians currently on the road"""
        return [ped for ped in self.pedestrians if ped.is_on_road()]
