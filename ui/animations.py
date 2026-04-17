"""
TESLA Animations Module
Handles smooth animations for car, effects, and transitions
Updated with smoother acceleration/deceleration curves
"""

import pygame
import math
from typing import Tuple, List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    COLORS, CAR_WIDTH, CAR_LENGTH, LANE_WIDTH, ROAD_Y_START,
    CAR_MAX_SPEED, CAR_ACCELERATION, CAR_DECELERATION, MAX_SPEED_MPH
)


class TeslaCar:
    """Tesla Model 3 style car with animations and smooth speed control"""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.target_y = y
        
        self.angle = 0
        self.target_angle = 0
        
        self.speed = 0
        self.target_speed = 0
        
        self.width = CAR_WIDTH
        self.length = CAR_LENGTH
        
        self.braking = False
        self.brake_light_intensity = 0
        
        self.indicator_left = False
        self.indicator_right = False
        self.indicator_timer = 0
        self.indicator_on = True
        
        self.wheel_rotation = 0
        
        # Smooth acceleration parameters
        self.acceleration_curve = 0.0  # For smooth acceleration ramp
        self.deceleration_curve = 0.0  # For smooth deceleration ramp
        
        self.rect = pygame.Rect(x, y, self.length, self.width)
    
    def update(self, dt: float):
        """Update car animations with smoother speed control"""
        # Smooth angle transition
        self.angle += (self.target_angle - self.angle) * 0.15
        
        # Smooth y position transition for lane changes
        self.y += (self.target_y - self.y) * 0.1
        
        # Smoother speed transition with acceleration curves
        speed_diff = self.target_speed - self.speed
        
        if abs(speed_diff) > 0.01:
            if speed_diff > 0:
                # Accelerating - use smooth curve
                self.acceleration_curve = min(1.0, self.acceleration_curve + CAR_ACCELERATION * 0.5)
                accel_factor = self._ease_in_out(self.acceleration_curve)
                self.speed += speed_diff * CAR_ACCELERATION * accel_factor
                self.deceleration_curve = 0.0
            else:
                # Decelerating - use smooth curve
                self.deceleration_curve = min(1.0, self.deceleration_curve + CAR_DECELERATION * 0.5)
                decel_factor = self._ease_in_out(self.deceleration_curve)
                self.speed += speed_diff * CAR_DECELERATION * decel_factor
                self.acceleration_curve = 0.0
        else:
            self.acceleration_curve = 0.0
            self.deceleration_curve = 0.0
        
        # Clamp speed to max
        self.speed = max(0, min(CAR_MAX_SPEED, self.speed))
        
        # Update position
        self.x += self.speed * dt * 60
        
        # Update brake lights
        if self.braking:
            self.brake_light_intensity = min(1.0, self.brake_light_intensity + 0.2)
        else:
            self.brake_light_intensity = max(0.0, self.brake_light_intensity - 0.1)
        
        # Update indicators
        self.indicator_timer += 1
        if self.indicator_timer >= 15:
            self.indicator_timer = 0
            self.indicator_on = not self.indicator_on
        
        # Update wheel rotation
        self.wheel_rotation += self.speed * 10
        
        # Update collision rect
        self.rect = pygame.Rect(self.x, self.y, self.length, self.width)
    
    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out function for smooth acceleration curves"""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2
    
    def set_lane(self, lane: int):
        """Set target lane for smooth transition"""
        self.target_y = ROAD_Y_START + (lane * LANE_WIDTH) + (LANE_WIDTH - self.width) // 2
    
    def steer_left(self):
        """Steer left"""
        self.target_angle = min(15, self.target_angle + 3)
        self.indicator_left = True
        self.indicator_right = False
    
    def steer_right(self):
        """Steer right"""
        self.target_angle = max(-15, self.target_angle - 3)
        self.indicator_right = True
        self.indicator_left = False
    
    def reset_steering(self):
        """Reset steering angle"""
        self.target_angle = 0
        self.indicator_left = False
        self.indicator_right = False
    
    def accelerate(self, amount: float = None):
        """Accelerate the car with smoother curve"""
        if amount is None:
            amount = CAR_ACCELERATION
        self.target_speed = min(CAR_MAX_SPEED, self.target_speed + amount)
        self.braking = False
    
    def brake(self, amount: float = None):
        """Apply brakes with smoother curve"""
        if amount is None:
            amount = CAR_DECELERATION
        self.target_speed = max(0, self.target_speed - amount)
        self.braking = True
    
    def emergency_stop(self):
        """Emergency stop"""
        self.target_speed = 0
        self.braking = True
    
    def get_speed_mph(self) -> int:
        """Get current speed in MPH"""
        return min(MAX_SPEED_MPH, int(self.speed * 15))
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the Tesla car with all visual details"""
        screen_x = self.x - camera_x
        
        car_surface = pygame.Surface((self.length + 20, self.width + 20), pygame.SRCALPHA)
        center = (self.length // 2 + 10, self.width // 2 + 10)
        
        shadow_rect = pygame.Rect(13, 13, self.length, self.width)
        pygame.draw.rect(car_surface, (*COLORS['shadow'], 150), shadow_rect, border_radius=8)
        
        car_rect = pygame.Rect(10, 10, self.length, self.width)
        pygame.draw.rect(car_surface, COLORS['tesla_white'], car_rect, border_radius=8)
        
        highlight_rect = pygame.Rect(12, 12, self.length - 4, 8)
        pygame.draw.rect(car_surface, (240, 245, 250), highlight_rect, border_radius=4)
        
        roof_color = (30, 35, 45)
        roof_rect = pygame.Rect(25, 14, 35, self.width - 8)
        pygame.draw.rect(car_surface, roof_color, roof_rect, border_radius=4)
        
        windshield_color = (60, 90, 130)
        front_windshield = pygame.Rect(58, 14, 14, self.width - 8)
        pygame.draw.rect(car_surface, windshield_color, front_windshield, border_radius=3)
        
        rear_windshield = pygame.Rect(12, 14, 10, self.width - 8)
        pygame.draw.rect(car_surface, windshield_color, rear_windshield, border_radius=3)
        
        wheel_color = (25, 25, 30)
        wheel_rim = (80, 85, 95)
        
        wheel_positions = [
            (18, 6), (18, self.width + 4),
            (self.length - 8, 6), (self.length - 8, self.width + 4)
        ]
        
        for wx, wy in wheel_positions:
            pygame.draw.ellipse(car_surface, wheel_color, 
                               (wx, wy, 14, 8))
            pygame.draw.ellipse(car_surface, wheel_rim, 
                               (wx + 3, wy + 2, 8, 4))
        
        headlight_color = (255, 250, 240)
        pygame.draw.rect(car_surface, headlight_color, 
                        (self.length + 5, 14, 4, 6), border_radius=2)
        pygame.draw.rect(car_surface, headlight_color, 
                        (self.length + 5, self.width, 4, 6), border_radius=2)
        
        if self.braking or self.brake_light_intensity > 0:
            intensity = int(255 * self.brake_light_intensity)
            brake_color = (intensity, 30, 30)
            pygame.draw.rect(car_surface, brake_color, 
                            (6, 14, 4, self.width - 8), border_radius=2)
        else:
            pygame.draw.rect(car_surface, (100, 30, 30), 
                            (6, 14, 4, self.width - 8), border_radius=2)
        
        if self.indicator_left and self.indicator_on:
            pygame.draw.rect(car_surface, COLORS['traffic_yellow'], 
                            (self.length + 4, 8, 4, 5), border_radius=1)
            pygame.draw.rect(car_surface, COLORS['traffic_yellow'], 
                            (6, 8, 4, 5), border_radius=1)
        
        if self.indicator_right and self.indicator_on:
            pygame.draw.rect(car_surface, COLORS['traffic_yellow'], 
                            (self.length + 4, self.width + 7, 4, 5), border_radius=1)
            pygame.draw.rect(car_surface, COLORS['traffic_yellow'], 
                            (6, self.width + 7, 4, 5), border_radius=1)
        
        tesla_blue = COLORS['tesla_blue']
        pygame.draw.line(car_surface, tesla_blue, 
                        (30, 10 + self.width // 2), (55, 10 + self.width // 2), 2)
        
        rotated_surface = pygame.transform.rotate(car_surface, self.angle)
        rotated_rect = rotated_surface.get_rect(center=(screen_x + self.length // 2, 
                                                        self.y + self.width // 2))
        screen.blit(rotated_surface, rotated_rect)
    
    def get_front_position(self) -> Tuple[float, float]:
        """Get position of front of car"""
        angle_rad = math.radians(self.angle)
        front_x = self.x + self.length + math.cos(angle_rad) * 10
        front_y = self.y + self.width // 2 - math.sin(angle_rad) * 10
        return (front_x, front_y)
    
    def get_center_position(self) -> Tuple[float, float]:
        """Get center position of car"""
        return (self.x + self.length // 2, self.y + self.width // 2)


class ParticleEffect:
    """Particle effect for various animations"""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 velocity: Tuple[float, float], lifetime: int = 60):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 3
    
    def update(self, dt: float) -> bool:
        """Update particle, returns False if dead"""
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= 1
        
        self.size = max(1, int(3 * (self.lifetime / self.max_lifetime)))
        
        return self.lifetime > 0
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the particle"""
        screen_x = self.x - camera_x
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        if 0 < screen_x < screen.get_width():
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*self.color, alpha),
                              (self.size, self.size), self.size)
            screen.blit(particle_surface, (screen_x - self.size, self.y - self.size))


class EffectsManager:
    """Manages visual effects"""
    
    def __init__(self):
        self.particles: List[ParticleEffect] = []
        self.screen_shake = 0
        self.flash_alpha = 0
    
    def add_brake_particles(self, x: float, y: float):
        """Add brake/skid particles"""
        import random
        for _ in range(3):
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(-0.5, 0.5)
            self.particles.append(ParticleEffect(
                x, y, (150, 150, 160), (vx, vy), 30
            ))
    
    def add_collision_effect(self, x: float, y: float):
        """Add collision effect"""
        import random
        self.screen_shake = 10
        self.flash_alpha = 150
        
        for _ in range(15):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)
            color = random.choice([
                COLORS['warning'],
                COLORS['traffic_red'],
                (255, 200, 100)
            ])
            self.particles.append(ParticleEffect(x, y, color, (vx, vy), 45))
    
    def update(self, dt: float):
        """Update all effects"""
        self.particles = [p for p in self.particles if p.update(dt)]
        
        if self.screen_shake > 0:
            self.screen_shake -= 1
        
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 10)
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw all effects"""
        for particle in self.particles:
            particle.draw(screen, camera_x)
        
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 100, 100, self.flash_alpha))
            screen.blit(flash_surface, (0, 0))
    
    def get_screen_offset(self) -> Tuple[int, int]:
        """Get screen shake offset"""
        if self.screen_shake > 0:
            import random
            return (random.randint(-3, 3), random.randint(-3, 3))
        return (0, 0)
