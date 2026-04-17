import pygame
import random
from typing import List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, COLORS, LANE_WIDTH, NUM_LANES, ROAD_Y_START,
    MAX_STATIC_OBSTACLES
)

class Obstacle:
    """Base obstacle class"""

    def __init__(self, x: float, y: float, width: int, height: int, 
                 obstacle_type: str = 'generic'):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.obstacle_type = obstacle_type
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the obstacle"""
        screen_x = self.x - camera_x
        if screen_x < -self.width or screen_x > SCREEN_WIDTH:
            return
        
        pygame.draw.rect(screen, COLORS['shadow'],
                        (screen_x + 3, self.y + 3, self.width, self.height))
        pygame.draw.rect(screen, COLORS['obstacle'],
                        (screen_x, self.y, self.width, self.height),
                        border_radius=3)
    
    def update_rect(self):
        """Update collision rectangle"""
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class Cone(Obstacle):
    """Traffic cone obstacle"""
    
    def __init__(self, x: float, lane: int):
        y = ROAD_Y_START + (lane * LANE_WIDTH) + LANE_WIDTH // 2 - 10
        super().__init__(x, y, 15, 20, 'cone')
        self.lane = lane
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw traffic cone"""
        screen_x = self.x - camera_x
        if screen_x < -self.width or screen_x > SCREEN_WIDTH:
            return
        
        cone_color = (255, 140, 0)
        points = [
            (screen_x + self.width // 2, self.y),
            (screen_x, self.y + self.height),
            (screen_x + self.width, self.y + self.height)
        ]
        pygame.draw.polygon(screen, cone_color, points)
        
        stripe_color = (255, 255, 255)
        pygame.draw.line(screen, stripe_color,
                        (screen_x + 3, self.y + 8),
                        (screen_x + self.width - 3, self.y + 8), 2)
        pygame.draw.line(screen, stripe_color,
                        (screen_x + 2, self.y + 14),
                        (screen_x + self.width - 2, self.y + 14), 2)


class Barrier(Obstacle):
    """Road barrier obstacle"""
    
    def __init__(self, x: float, lane: int):
        y = ROAD_Y_START + (lane * LANE_WIDTH) + LANE_WIDTH // 2 - 15
        super().__init__(x, y, 60, 30, 'barrier')
        self.lane = lane
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw road barrier"""
        screen_x = self.x - camera_x
        if screen_x < -self.width or screen_x > SCREEN_WIDTH:
            return
        
        pygame.draw.rect(screen, COLORS['shadow'],
                        (screen_x + 3, self.y + 3, self.width, self.height),
                        border_radius=3)
        
        base_color = (200, 200, 200)
        pygame.draw.rect(screen, base_color,
                        (screen_x, self.y, self.width, self.height),
                        border_radius=3)
        
        stripe_color = (255, 100, 0)
        for i in range(0, self.width, 15):
            pygame.draw.polygon(screen, stripe_color, [
                (screen_x + i, self.y),
                (screen_x + i + 10, self.y),
                (screen_x + i + 15, self.y + self.height),
                (screen_x + i + 5, self.y + self.height)
            ])


class BrokenDownCar(Obstacle):
    """Broken down car obstacle"""
    
    def __init__(self, x: float, lane: int):
        y = ROAD_Y_START + (lane * LANE_WIDTH) + (LANE_WIDTH - 35) // 2
        super().__init__(x, y, 65, 35, 'broken_car')
        self.lane = lane
        self.hazard_timer = 0
        self.hazard_on = True
    
    def update(self, dt: float):
        """Update hazard lights"""
        self.hazard_timer += 1
        if self.hazard_timer >= 30:
            self.hazard_timer = 0
            self.hazard_on = not self.hazard_on
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw broken down car"""
        screen_x = self.x - camera_x
        if screen_x < -self.width or screen_x > SCREEN_WIDTH:
            return
        
        pygame.draw.rect(screen, COLORS['shadow'],
                        (screen_x + 4, self.y + 4, self.width, self.height),
                        border_radius=5)
        
        car_color = (100, 100, 110)
        pygame.draw.rect(screen, car_color,
                        (screen_x, self.y, self.width, self.height),
                        border_radius=5)
        
        pygame.draw.rect(screen, (60, 80, 100),
                        (screen_x + self.width - 18, self.y + 6, 14, self.height - 12),
                        border_radius=3)
        
        pygame.draw.ellipse(screen, (30, 30, 35),
                           (screen_x + 8, self.y - 2, 12, 6))
        pygame.draw.ellipse(screen, (30, 30, 35),
                           (screen_x + 8, self.y + self.height - 4, 12, 6))
        pygame.draw.ellipse(screen, (30, 30, 35),
                           (screen_x + self.width - 18, self.y - 2, 12, 6))
        pygame.draw.ellipse(screen, (30, 30, 35),
                           (screen_x + self.width - 18, self.y + self.height - 4, 12, 6))
        
        if self.hazard_on:
            hazard_color = (255, 180, 0)
            pygame.draw.rect(screen, hazard_color,
                           (screen_x + self.width - 3, self.y + 4, 4, 6))
            pygame.draw.rect(screen, hazard_color,
                           (screen_x + self.width - 3, self.y + self.height - 10, 4, 6))
            pygame.draw.rect(screen, hazard_color,
                           (screen_x - 1, self.y + 4, 4, 6))
            pygame.draw.rect(screen, hazard_color,
                           (screen_x - 1, self.y + self.height - 10, 4, 6))


class ObstacleManager:
    """Manages all obstacles on the road"""
    
    def __init__(self):
        self.obstacles: List[Obstacle] = []
        self.spawn_timer = 0
        self.spawn_interval = 300
        self.world_length = 5000
        
        self._spawn_initial_obstacles()
    
    def _spawn_initial_obstacles(self):
        """Spawn some initial obstacles"""
        for x in range(500, self.world_length, 600):
            if random.random() > 0.6:
                self._spawn_obstacle_at(x)
    
    def _spawn_obstacle_at(self, x: float):
        """Spawn an obstacle at specific x position"""
        if len(self.obstacles) >= MAX_STATIC_OBSTACLES * 3:
            return
        
        lane = random.randint(0, NUM_LANES - 1)
        
        for obs in self.obstacles:
            if hasattr(obs, 'lane') and obs.lane == lane:
                if abs(obs.x - x) < 200:
                    return
        
        obstacle_type = random.choice(['cone', 'barrier', 'broken_car'])
        
        if obstacle_type == 'cone':
            self.obstacles.append(Cone(x, lane))
            if random.random() > 0.5:
                self.obstacles.append(Cone(x + 20, lane))
        elif obstacle_type == 'barrier':
            self.obstacles.append(Barrier(x, lane))
        else:
            self.obstacles.append(BrokenDownCar(x, lane))
    
    def update(self, dt: float, camera_x: float):
        """Update all obstacles"""
        for obs in self.obstacles:
            if hasattr(obs, 'update'):
                obs.update(dt)
        
        self.obstacles = [obs for obs in self.obstacles 
                         if obs.x > camera_x - 200]
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw all obstacles"""
        for obs in self.obstacles:
            obs.draw(screen, camera_x)
    
    def get_obstacles(self) -> List[Obstacle]:
        """Get list of all obstacles"""
        return self.obstacles
    
    def get_obstacle_rects(self) -> List[pygame.Rect]:
        """Get collision rectangles for all obstacles"""
        return [obs.rect for obs in self.obstacles]
