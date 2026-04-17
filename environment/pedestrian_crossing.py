"""
TESLA Pedestrian Crossing Indicator Module
Displays walking symbol above zebra crossings when pedestrians are crossing
Replaces the old traffic light system
"""

import pygame
import math
from typing import List, Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, COLORS, ROAD_Y_START,
    CROSSING_INDICATOR_SIZE, CROSSING_INDICATOR_MARGIN
)


class PedestrianCrossingIndicator:
    """Walking symbol indicator shown above zebra crossings when pedestrians are present"""
    
    def __init__(self, x: float, width: float):
        self.x = x
        self.width = width
        self.y = ROAD_Y_START - CROSSING_INDICATOR_SIZE - CROSSING_INDICATOR_MARGIN
        self.active = False
        self.pulse_timer = 0
        self.pulse_alpha = 200
        
    def set_active(self, active: bool):
        """Set whether a pedestrian is currently crossing"""
        self.active = active
    
    def update(self, dt: float):
        """Update animation"""
        if self.active:
            self.pulse_timer += dt * 5
            self.pulse_alpha = int(150 + 105 * abs(math.sin(self.pulse_timer)))
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw the pedestrian crossing indicator"""
        screen_x = self.x + self.width // 2 - camera_x
        
        if screen_x < -CROSSING_INDICATOR_SIZE or screen_x > SCREEN_WIDTH + CROSSING_INDICATOR_SIZE:
            return
        
        if not self.active:
            return
        
        # Draw indicator background (circular with glow)
        indicator_size = CROSSING_INDICATOR_SIZE
        center_x = int(screen_x)
        center_y = int(self.y + indicator_size // 2)
        
        # Glow effect
        glow_surface = pygame.Surface((indicator_size * 2, indicator_size * 2), pygame.SRCALPHA)
        glow_color = (*COLORS['pedestrian_crossing_indicator'][:3], int(self.pulse_alpha * 0.4))
        pygame.draw.circle(glow_surface, glow_color, (indicator_size, indicator_size), indicator_size)
        screen.blit(glow_surface, (center_x - indicator_size, center_y - indicator_size))
        
        # Main indicator circle
        pygame.draw.circle(screen, COLORS['tesla_dark'], (center_x, center_y), indicator_size // 2)
        pygame.draw.circle(screen, COLORS['pedestrian_crossing_indicator'], 
                          (center_x, center_y), indicator_size // 2, 2)
        
        # Draw walking person symbol
        self._draw_walking_symbol(screen, center_x, center_y, indicator_size // 2 - 5)
    
    def _draw_walking_symbol(self, screen: pygame.Surface, cx: int, cy: int, size: int):
        """Draw a stylized walking person icon"""
        # Calculate proportions
        head_radius = size // 2
        body_length = size // 1.5
        leg_length = size // 1.5
        arm_length = size // 2
        
        # Colors
        symbol_color = COLORS['pedestrian_crossing_indicator']
        
        # Draw head
        head_y = cy - body_length // 2 - head_radius
        pygame.draw.circle(screen, symbol_color, (cx, head_y), head_radius)
        
        # Draw body (slightly angled for walking pose)
        body_top = (cx, head_y + head_radius)
        body_bottom = (cx + 2, cy + body_length // 4)
        pygame.draw.line(screen, symbol_color, body_top, body_bottom, 3)
        
        # Draw legs (walking pose)
        left_leg_end = (cx - size // 3, cy + leg_length)
        right_leg_end = (cx + size // 3, cy + leg_length // 2)
        pygame.draw.line(screen, symbol_color, body_bottom, left_leg_end, 3)
        pygame.draw.line(screen, symbol_color, body_bottom, right_leg_end, 3)
        
        # Draw arms (walking pose)
        shoulder = (cx, head_y + head_radius + 4)
        left_arm_end = (cx + size // 3, cy - size // 6)
        right_arm_end = (cx - size // 4, cy)
        pygame.draw.line(screen, symbol_color, shoulder, left_arm_end, 2)
        pygame.draw.line(screen, symbol_color, shoulder, right_arm_end, 2)


class PedestrianCrossingManager:
    """Manages all pedestrian crossing indicators"""
    
    def __init__(self, zebra_crossings: List):
        self.indicators: List[PedestrianCrossingIndicator] = []
        
        # Create an indicator for each zebra crossing
        for crossing in zebra_crossings:
            self.indicators.append(
                PedestrianCrossingIndicator(crossing.x, crossing.width)
            )
        
        self.crossings = zebra_crossings
    
    def update(self, dt: float, pedestrians: List, camera_x: float):
        """Update all indicators based on pedestrian positions"""
        for i, indicator in enumerate(self.indicators):
            if i < len(self.crossings):
                crossing = self.crossings[i]
                
                # Check if any pedestrian is crossing at this zebra crossing
                pedestrian_crossing = False
                for ped in pedestrians:
                    if hasattr(ped, 'x') and hasattr(ped, 'is_on_road'):
                        # Check if pedestrian is near this crossing and on the road
                        if abs(ped.x - (crossing.x + crossing.width // 2)) < crossing.width:
                            if ped.is_on_road():
                                pedestrian_crossing = True
                                break
                
                indicator.set_active(pedestrian_crossing)
            
            indicator.update(dt)
    
    def draw(self, screen: pygame.Surface, camera_x: float):
        """Draw all indicators"""
        for indicator in self.indicators:
            indicator.draw(screen, camera_x)
    
    def is_pedestrian_crossing_ahead(self, car_x: float, max_distance: float = 300) -> Tuple[bool, float]:
        """Check if there's an active pedestrian crossing ahead (even slightly behind)"""
        closest_dist = float('inf')
        crossing_found = False
        
        for indicator in self.indicators:
            if indicator.active:
                dist = indicator.x - car_x
                # Extended range: detect pedestrians from further ahead AND slightly behind
                # This prevents the car from getting stuck at crossings
                if -50 < dist < max_distance:
                    crossing_found = True
                    if abs(dist) < abs(closest_dist):
                        closest_dist = dist
        
        return crossing_found, closest_dist if crossing_found else float('inf')
