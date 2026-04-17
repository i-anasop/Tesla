"""
TESLA Dashboard UI Module
Displays futuristic Tesla-style dashboard overlay
Updated with improved speed display and cleaner UI
"""

import pygame
import pygame.gfxdraw  # Import gfxdraw for smoother anti-aliased rendering
import math
from typing import Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, DASHBOARD_HEIGHT,
    MINI_MAP_SIZE, FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM, FONT_SIZE_SMALL, CAR_MAX_SPEED,
    SAFE_DISTANCE, MAX_SPEED_MPH
)

# Helper function for glowing elements (Local utility)
def draw_glow(surface, color, center, radius, width=2):
    for i in range(3):
        pygame.gfxdraw.aacircle(surface, int(center[0]), int(center[1]), radius + i, (*color[:3], 100 - i*30))

class MiniRadar:
    """Mini radar display showing nearby objects"""
    
    def __init__(self, x: int, y: int, size: int):
        self.x = x
        self.y = y
        self.size = size
        self.center = (x + size // 2, y + size // 2)
        self.scale = size / (SAFE_DISTANCE * 3)
    
    def draw(self, screen: pygame.Surface, sensor_data: Dict):
        """Draw the mini radar"""
        # Create a local surface for the radar with alpha support
        radar_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # 1. Background: Dark glass panel
        bg_rect = pygame.Rect(0, 0, self.size, self.size)
        pygame.draw.rect(radar_surface, (10, 15, 20, 200), bg_rect, border_radius=15)
        pygame.draw.rect(radar_surface, (*COLORS['tesla_blue'], 50), bg_rect, 1, border_radius=15)
        
        cx, cy = self.size // 2, self.size // 2

        # 2. Grid Lines (Concentric circles for distance)
        for r in range(1, 4):
            radius = int(cx * r / 3.5)
            # Use dashed effect or very faint lines
            pygame.draw.circle(radar_surface, (*COLORS['dashboard_text'], 30), (cx, cy), radius, 1)

        # 3. Crosshairs
        pygame.draw.line(radar_surface, (*COLORS['dashboard_text'], 30), (cx, 10), (cx, self.size - 10), 1)
        pygame.draw.line(radar_surface, (*COLORS['dashboard_text'], 30), (10, cy), (self.size - 10, cy), 1)

        # 4. The Ego Car (Triangle/Arrow shape for better directionality)
        car_points = [
            (cx, cy - 6),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6)
        ]
        pygame.draw.polygon(radar_surface, COLORS['tesla_blue'], car_points)
        pygame.draw.polygon(radar_surface, COLORS['neon_blue'], car_points, 1)

        # 5. Obstacles (Blips with Glow)
        def draw_blip(distance, side_offset_factor=0, is_vertical=True):
            if distance < SAFE_DISTANCE * 2.5:
                # Calculate position relative to center
                offset = int(distance * self.scale)
                
                if is_vertical:
                    bx = cx + int(side_offset_factor * 10) # Slight jitter for visual separation
                    by = cy - offset
                else:
                    bx = cx + int(offset * side_offset_factor)
                    by = cy

                # Determine color based on safety
                if distance < SAFE_DISTANCE:
                    blip_color = COLORS['warning']
                elif distance < SAFE_DISTANCE * 1.5:
                    blip_color = COLORS['traffic_yellow']
                else:
                    blip_color = COLORS['neon_cyan']

                # Draw Glow
                pygame.draw.circle(radar_surface, (*blip_color, 50), (bx, by), 6)
                # Draw Core
                pygame.draw.circle(radar_surface, blip_color, (bx, by), 3)

        # Front Sensor
        front_dist = sensor_data.get('front_distance', SAFE_DISTANCE * 3)
        draw_blip(front_dist, 0, is_vertical=True)

        # Left Sensor
        left_dist = sensor_data.get('left_distance', SAFE_DISTANCE * 3)
        draw_blip(left_dist, -1, is_vertical=False)

        # Right Sensor
        right_dist = sensor_data.get('right_distance', SAFE_DISTANCE * 3)
        draw_blip(right_dist, 1, is_vertical=False)
        
        # Label
        font = pygame.font.Font(None, 14)
        label = font.render("RADAR", True, (*COLORS['dashboard_text'][:3], 150))
        radar_surface.blit(label, (cx - label.get_width()//2, self.size - 15))

        screen.blit(radar_surface, (self.x, self.y))


class SpeedGauge:
    """Circular speed gauge display with max speed limit indicator"""
    
    def __init__(self, x: int, y: int, radius: int):
        self.x = x
        self.y = y
        self.radius = radius
        # Center coordinates
        self.center = (x + radius, y + radius)
    
    def draw(self, screen: pygame.Surface, speed: float, speed_mph: int, font: pygame.font.Font):
        """Draw the speed gauge"""
        # Create surface with alpha channel for transparency
        gauge_surface = pygame.Surface((self.radius * 2 + 40, self.radius * 2 + 40), pygame.SRCALPHA)
        cx, cy = self.radius + 20, self.radius + 20
        
        # 1. Background Arc (Dark Grey Track)
        # Using a thick line to simulate an arc track
        # Angles in radians (0 is right, goes clockwise)
        start_angle = math.radians(135)
        end_angle = math.radians(405)
        
        rect = pygame.Rect(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)
        pygame.draw.arc(gauge_surface, (40, 45, 55), rect, -math.radians(45), math.radians(225), 10) # Thicker track

        # 2. Active Speed Arc (Dynamic Fill)
        speed_ratio = min(1.0, speed / CAR_MAX_SPEED)
        
        # Color transition: Blue -> Cyan -> Orange -> Red (Tesla Style)
        if speed_ratio < 0.5: color = COLORS['neon_blue']
        elif speed_ratio < 0.75: color = COLORS['neon_cyan']
        elif speed_ratio < 0.9: color = COLORS['traffic_yellow']
        else: color = COLORS['warning']

        # Calculate arc length
        # Pygame arcs measure counter-clockwise in radians
        arc_start = math.radians(225) # 225 degrees (bottom left)
        arc_span = math.radians(270)  # Total span (270 degrees)
        current_arc_end = arc_start - (arc_span * speed_ratio)

        # Draw the progress bar (thick arc)
        if speed_ratio > 0.01:
            pygame.draw.arc(gauge_surface, color, rect, current_arc_end, arc_start, 10)
            
            # Draw a glowing tip at the end of the arc
            tip_x = cx + math.cos(current_arc_end) * self.radius
            tip_y = cy - math.sin(current_arc_end) * self.radius
            # Glow effect
            pygame.draw.circle(gauge_surface, (*color[:3], 100), (int(tip_x), int(tip_y)), 8)
            pygame.draw.circle(gauge_surface, color, (int(tip_x), int(tip_y)), 4)

        # 3. Digital Speed Readout (Central)
        display_speed = min(MAX_SPEED_MPH, speed_mph)
        
        # Main number (Large)
        # Use a slightly larger font for the number
        number_font = pygame.font.Font(None, 60)
        speed_text = number_font.render(str(display_speed), True, (255, 255, 255))
        text_rect = speed_text.get_rect(center=(cx, cy - 5))
        
        # Subtle glow behind text
        glow_text = number_font.render(str(display_speed), True, (*color[:3], 50))
        gauge_surface.blit(glow_text, (text_rect.x - 1, text_rect.y - 1))
        gauge_surface.blit(speed_text, text_rect)
        
        # "MPH" Label
        unit_font = pygame.font.Font(None, FONT_SIZE_SMALL + 2)
        unit_text = unit_font.render("MPH", True, COLORS['dashboard_text'])
        unit_rect = unit_text.get_rect(center=(cx, cy + 25))
        gauge_surface.blit(unit_text, unit_rect)
        
        # Limit Indicator (Badge style)
        limit_bg_rect = pygame.Rect(cx - 20, cy + 40, 40, 16)
        pygame.draw.rect(gauge_surface, (240, 240, 240), limit_bg_rect, border_radius=4)
        pygame.draw.rect(gauge_surface, (200, 0, 0), limit_bg_rect, 2, border_radius=4)
        
        limit_font = pygame.font.Font(None, 14)
        limit_text = limit_font.render(f"{MAX_SPEED_MPH}", True, (0, 0, 0))
        limit_rect = limit_text.get_rect(center=limit_bg_rect.center)
        gauge_surface.blit(limit_text, limit_rect)
        
        screen.blit(gauge_surface, (self.x - 20, self.y - 20))


class Dashboard:
    """Main dashboard overlay"""
    
    def __init__(self):
        pygame.font.init()
        # Loading fonts (system fonts fallback to ensure clean look)
        self.font_large = pygame.font.Font(None, FONT_SIZE_LARGE + 10) # Slightly larger for modern feel
        self.font_medium = pygame.font.Font(None, FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.Font(None, FONT_SIZE_SMALL)
        
        self.height = DASHBOARD_HEIGHT
        self.y = SCREEN_HEIGHT - self.height
        
        # Adjusted positions for better spacing
        self.radar = MiniRadar(SCREEN_WIDTH - MINI_MAP_SIZE - 25, 
                              self.y + 15, MINI_MAP_SIZE - 30)
        self.speed_gauge = SpeedGauge(30, self.y + 10, 60)
    
    def draw(self, screen: pygame.Surface, car_data: Dict, 
             sensor_data: Dict, ai_status: Dict):
        """Draw the complete dashboard"""
        dashboard_surface = pygame.Surface((SCREEN_WIDTH, self.height), pygame.SRCALPHA)
        
        # 1. Background Panel (Floating Glass Effect)
        # Instead of a full gradient, we use a rounded rect at the bottom
        panel_rect = pygame.Rect(10, 5, SCREEN_WIDTH - 20, self.height - 10)
        
        # Gradient Fill (Simulated)
        pygame.draw.rect(dashboard_surface, (15, 20, 25, 240), panel_rect, border_radius=15)
        
        # Top Accent Line (Tesla Blue Glow)
        pygame.draw.line(dashboard_surface, COLORS['tesla_blue'], 
                        (20, 5), (SCREEN_WIDTH - 20, 5), 2)
        
        screen.blit(dashboard_surface, (0, self.y))
        
        # Draw speed gauge with MPH
        speed_mph = car_data.get('speed_mph', int(car_data.get('speed', 0) * 15))
        self.speed_gauge.draw(screen, car_data.get('speed', 0), speed_mph, self.font_large)
        
        self._draw_info_panel(screen, car_data, sensor_data)
        
        self._draw_ai_panel(screen, ai_status)
        
        self.radar.draw(screen, sensor_data)
        
    
    def _draw_info_panel(self, screen: pygame.Surface, car_data: Dict, sensor_data: Dict):
        """Draw enhanced information panel with lane visualization"""
        base_x = 180
        
        # --- ADJUSTMENT HERE: Vertically Center Content ---
        # content_height is approx 50px. We calculate y to center it.
        content_height = 50 
        base_y = self.y + (self.height - content_height) // 2
        
        # --- Section 1: Lane Assist Visualization (3D Perspective) ---
        lane = sensor_data.get('current_lane', 1)
        
        # Draw perspective lanes (Trapezoids)
        lane_width_bottom = 30
        lane_width_top = 15
        height = 40
        gap = 5
        
        for i in range(3):
            # Calculate perspective offsets
            center_offset = (i - 1) * (lane_width_bottom + gap)
            
            # Points for trapezoid
            p1 = (base_x + 40 + (i-1)*(lane_width_top+2), base_y) # Top Left
            p2 = (base_x + 40 + (i-1)*(lane_width_top+2) + lane_width_top, base_y) # Top Right
            p3 = (base_x + 40 + center_offset + lane_width_bottom, base_y + height) # Bottom Right
            p4 = (base_x + 40 + center_offset, base_y + height) # Bottom Left
            
            # Determine Color
            is_active = (i == lane)
            fill_color = (*COLORS['tesla_blue'][:3], 100) if is_active else (50, 55, 60, 100)
            border_color = COLORS['neon_blue'] if is_active else (80, 85, 90)
            
            # Draw
            pygame.gfxdraw.filled_polygon(screen, [p1, p2, p3, p4], fill_color)
            pygame.draw.polygon(screen, border_color, [p1, p2, p3, p4], 1)

        # Lane Status Indicators (Chevrons instead of circles)
        left_clear = sensor_data.get('left_lane_clear', False)
        right_clear = sensor_data.get('right_lane_clear', False)
        
        # Left Indicator
        l_color = COLORS['success'] if left_clear else (100, 30, 30)
        pygame.draw.line(screen, l_color, (base_x, base_y + 15), (base_x - 10, base_y + 25), 3)
        pygame.draw.line(screen, l_color, (base_x - 10, base_y + 25), (base_x, base_y + 35), 3)
        
        # Right Indicator
        r_color = COLORS['success'] if right_clear else (100, 30, 30)
        pygame.draw.line(screen, r_color, (base_x + 90, base_y + 15), (base_x + 100, base_y + 25), 3)
        pygame.draw.line(screen, r_color, (base_x + 100, base_y + 25), (base_x + 90, base_y + 35), 3)

        # --- Section 2: Objects Ahead ---
        front_dist = sensor_data.get('front_distance', 0)
        
        # Distance Badge
        dist_x = base_x + 130
        dist_bg = pygame.Rect(dist_x, base_y, 80, 40) # Adjusted height to fit center
        
        # Dynamic warning background
        if front_dist < SAFE_DISTANCE:
            bg_color = (*COLORS['warning'][:3], 50)
            text_color = COLORS['warning']
        else:
            bg_color = (30, 35, 40, 150)
            text_color = COLORS['neon_cyan']
            
        pygame.draw.rect(screen, bg_color, dist_bg, border_radius=8)
        pygame.draw.rect(screen, text_color, dist_bg, 1, border_radius=8)
        
        dist_val_text = self.font_medium.render(f"{front_dist:.0f}m", True, text_color)
        screen.blit(dist_val_text, (dist_x + 10, base_y + 5))
        
        dist_lbl_text = self.font_small.render("RANGE", True, COLORS['dashboard_text'])
        screen.blit(dist_lbl_text, (dist_x + 10, base_y + 25))
    
    def _draw_ai_panel(self, screen: pygame.Surface, ai_status: Dict):
        """Draw the AI status panel with RL information"""
        base_x = 420
        
        # --- ADJUSTMENT HERE: Vertically Center Content ---
        # content_height is approx 55px (Badge + Text + Bar)
        content_height = 55
        base_y = self.y + (self.height - content_height) // 2
        
        # 1. Decision Source Badge (Pill Shape)
        source = ai_status.get('decision_source', 'prolog')
        source_colors = {
            'rl': COLORS['success'],
            'prolog': COLORS['neon_blue'],
            'minimax': (200, 0, 200),
            'safety_override': COLORS['warning'],
            'rl_override': COLORS['traffic_yellow']
        }
        s_color = source_colors.get(source, COLORS['dashboard_text'])
        
        # Draw Label "AI CORE:"
        lbl = self.font_small.render("AI CORE", True, COLORS['dashboard_text'])
        screen.blit(lbl, (base_x, base_y - 12)) # Slight adjustment up for the label
        
        # Draw Badge
        badge_rect = pygame.Rect(base_x, base_y, 100, 20)
        pygame.draw.rect(screen, (*s_color[:3], 50), badge_rect, border_radius=4)
        pygame.draw.rect(screen, s_color, badge_rect, 1, border_radius=4)
        
        src_text = self.font_small.render(source.upper(), True, (255, 255, 255))
        text_rect = src_text.get_rect(center=badge_rect.center)
        screen.blit(src_text, text_rect)
        
        # 2. Action Display
        action = ai_status.get('action', 'INITIALIZING')
        action_clean = action.replace('_', ' ').upper()
        
        act_color = COLORS['neon_cyan']
        if 'brake' in action.lower() or 'stop' in action.lower():
            act_color = COLORS['warning']
        
        act_text = self.font_medium.render(action_clean, True, act_color)
        screen.blit(act_text, (base_x + 120, base_y - 2))
        
        # 3. Confidence Bar (Modern thin line)
        confidence = ai_status.get('confidence', 0)
        
        bar_x = base_x
        bar_y = base_y + 35 # Moved closer to the action text
        bar_w = 250
        bar_h = 4
        
        # Track
        pygame.draw.rect(screen, (40, 45, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        
        # Fill
        fill_w = int(bar_w * confidence)
        if fill_w > 0:
            # Gradient color based on confidence
            c_val = int(255 * confidence)
            fill_color = (255 - c_val, c_val, 100) # Red to Green transition
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
            
            # Glow dot at end of bar
            pygame.draw.circle(screen, fill_color, (bar_x + fill_w, bar_y + 2), 4)

        conf_lbl = self.font_small.render(f"CONFIDENCE {int(confidence*100)}%", True, COLORS['dashboard_text'])
        screen.blit(conf_lbl, (bar_x + bar_w + 10, bar_y - 2))
    