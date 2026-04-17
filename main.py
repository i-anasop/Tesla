import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLORS,
    LANE_WIDTH, NUM_LANES, ROAD_Y_START
)
from environment.map_builder import MapBuilder
from environment.traffic import TrafficManager
from environment.obstacles import ObstacleManager
from environment.pedestrians import PedestrianManager
from environment.pedestrian_crossing import PedestrianCrossingManager
from ai.sensors import SensorSystem
from ai.tesla_brain import TeslaBrain, Action
from ui.dashboard import Dashboard
from ui.animations import TeslaCar, EffectsManager
from ui.start_screen import StartScreen

class TeslaSimulator:
    
    def __init__(self, custom_objects=None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.map_builder = MapBuilder()
        self.traffic_manager = TrafficManager()
        self.obstacle_manager = ObstacleManager()
        
        initial_x = 200
        initial_lane = 1
        initial_y = ROAD_Y_START + (initial_lane * LANE_WIDTH) + (LANE_WIDTH - 35) // 2
        
        self.tesla_car = TeslaCar(initial_x, initial_y)
        self.tesla_car.set_lane(initial_lane)
        
        self.pedestrian_manager = PedestrianManager(self.map_builder.get_zebra_crossings())
        
        self.crossing_manager = PedestrianCrossingManager(self.map_builder.get_zebra_crossings())
        
        self.sensors = SensorSystem()
        self.brain = TeslaBrain()
        self.dashboard = Dashboard()
        self.effects = EffectsManager()
        
        self.current_lane = initial_lane
        self.target_lane = initial_lane
        self.lane_change_cooldown = 0
        
        self.collision_cooldown = 0
        self.total_distance = 0
        self.session_start_x = initial_x
        
        self.paused = False
        self.show_sensors = True
        self.debug_mode = False
        self.simulation_ended = False
        
        self.font = pygame.font.Font(None, 24)

        self.pause_button_rect = pygame.Rect(SCREEN_WIDTH - 120, 10, 100, 40)
        
        if custom_objects:
            self._load_custom_objects(custom_objects)
    
    def handle_events(self):
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.pause_button_rect.collidepoint(event.pos):
                    self.paused = not self.paused

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_s:
                    self.show_sensors = not self.show_sensors
                elif event.key == pygame.K_d:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_r:
                    self.reset_simulation()
    
    def reset_simulation(self):
        # Reset the simulation to initial state
        self.brain.save()
        
        initial_x = 200
        initial_lane = 1
        initial_y = ROAD_Y_START + (initial_lane * LANE_WIDTH) + (LANE_WIDTH - 35) // 2
        
        self.tesla_car = TeslaCar(initial_x, initial_y)
        self.tesla_car.set_lane(initial_lane)
        self.current_lane = initial_lane
        self.target_lane = initial_lane
        
        self.traffic_manager = TrafficManager()
        self.obstacle_manager = ObstacleManager()
        self.pedestrian_manager = PedestrianManager(self.map_builder.get_zebra_crossings())
        
        self.map_builder.camera_x = 0
        self.session_start_x = initial_x
        self.collision_cooldown = 0
        self.simulation_ended = False
    
    def get_obstacle_rects(self) -> list:
        # Get inflated rectangles of obstacles and traffic cars for collision detection
        rects = []
        for obs in self.obstacle_manager.get_obstacles():
            inflated_rect = obs.rect.inflate(10, 10)
            rects.append(inflated_rect)
        for car in self.traffic_manager.get_cars():
            rects.append(car.rect)
        return rects
    
    def check_collisions(self) -> bool:
        # Check for collisions between the Tesla car and obstacles/traffic
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
            return False
        car_rect = self.tesla_car.rect
        for obs in self.obstacle_manager.get_obstacles():
            if car_rect.colliderect(obs.rect):
                return True
        for traffic_car in self.traffic_manager.get_cars():
            if car_rect.colliderect(traffic_car.rect):
                return True
        return False
    
    def handle_collision(self):
        # Handle collision event
        self.collision_cooldown = 60
        self.effects.add_collision_effect(
            self.tesla_car.x + self.tesla_car.length,
            self.tesla_car.y + self.tesla_car.width // 2
        )
        self.brain.record_event('crash', 
                               lane=self.current_lane,
                               location=(self.tesla_car.x, self.tesla_car.y))
        self.tesla_car.emergency_stop()
        
        print("CRASH DETECTED! Resetting position to avoid overlap...")
        self.simulation_ended = True # End simulation on crash for simplicity
    
    def process_ai_action(self, action: Action, sensor_data: dict):
        # Process the action decided by the AI brain
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
        
        if action is None or sensor_data.get('collision_risk', 0) < 0.3:
            self.tesla_car.accelerate()
        elif action == Action.ACCELERATE:
            self.tesla_car.accelerate()
            self.tesla_car.reset_steering()
        elif action == Action.BRAKE:
            self.tesla_car.brake()
            self.tesla_car.reset_steering()
            if self.tesla_car.speed > 2:
                self.effects.add_brake_particles(
                    self.tesla_car.x,
                    self.tesla_car.y + self.tesla_car.width // 2
                )
        elif action == Action.EMERGENCY_STOP:
            self.tesla_car.emergency_stop()
            self.effects.add_brake_particles(
                self.tesla_car.x,
                self.tesla_car.y + self.tesla_car.width // 2
            )
        elif action == Action.STEER_LEFT:
            if self.lane_change_cooldown <= 0 and self.current_lane > 0:
                self.target_lane = self.current_lane - 1
                self.tesla_car.set_lane(self.target_lane)
                self.tesla_car.steer_left()
                self.lane_change_cooldown = 60
                self.brain.record_event('lane_change', success=True)
            else:
                self.tesla_car.accelerate()
        elif action == Action.STEER_RIGHT:
            if self.lane_change_cooldown <= 0 and self.current_lane < NUM_LANES - 1:
                self.target_lane = self.current_lane + 1
                self.tesla_car.set_lane(self.target_lane)
                self.tesla_car.steer_right()
                self.lane_change_cooldown = 60
                self.brain.record_event('lane_change', success=True)
            else:
                self.tesla_car.accelerate()
        else:
            self.tesla_car.accelerate()
        
        if abs(self.tesla_car.y - (ROAD_Y_START + self.target_lane * LANE_WIDTH + 
                                   (LANE_WIDTH - self.tesla_car.width) // 2)) < 5:
            self.current_lane = self.target_lane
            self.tesla_car.reset_steering()
    
    def update(self, dt: float):
        # Main update loop
        if self.paused or self.simulation_ended:
            return
        
        if self.tesla_car.x >= self.map_builder.world_length - 200:
            self.simulation_ended = True
            self.tesla_car.emergency_stop()
            self.brain.save()
            return
        
        self.tesla_car.update(dt)
        self.map_builder.update_camera(self.tesla_car.x)
        camera_x = self.map_builder.camera_x
        
        self.pedestrian_manager.update(dt, camera_x, self.tesla_car.x, self.tesla_car.y)
        pedestrians = self.pedestrian_manager.get_pedestrians()
        self.traffic_manager.update(dt, camera_x, self.tesla_car.x, pedestrians)
        self.obstacle_manager.update(dt, camera_x)
        self.crossing_manager.update(dt, self.pedestrian_manager.get_pedestrians(), camera_x)
        self.effects.update(dt)
        
        obstacle_rects = self.get_obstacle_rects()
        sensor_data = self.sensors.update(
            self.tesla_car.get_front_position(),
            self.tesla_car.angle,
            self.tesla_car.speed,
            obstacle_rects,
            self.traffic_manager.get_cars(),
            self.pedestrian_manager.get_pedestrians(),
            []
        )
        
        sensor_data['speed'] = self.tesla_car.speed
        sensor_data['current_lane'] = self.current_lane
        
        crossing_ahead, crossing_dist = self.crossing_manager.is_pedestrian_crossing_ahead(self.tesla_car.x)
        if crossing_ahead:
            sensor_data['pedestrian_detected'] = True
            sensor_data['pedestrian_distance'] = min(sensor_data.get('pedestrian_distance', 300), crossing_dist)
        
        action = self.brain.update(sensor_data)
        self.process_ai_action(action, sensor_data)
        
        if self.check_collisions():
            self.handle_collision()
        
        distance = self.tesla_car.x - self.session_start_x
        self.brain.record_event('distance', distance=dt * self.tesla_car.speed)
        
        if self.tesla_car.speed > 1 and sensor_data.get('collision_risk', 0) < 0.3:
            self.brain.record_event('smooth_driving')
    
    def draw(self):
        # Main draw loop
        self.map_builder.draw(self.screen)
        camera_x = self.map_builder.camera_x
        
        self.crossing_manager.draw(self.screen, camera_x)
        self.obstacle_manager.draw(self.screen, camera_x)
        self.traffic_manager.draw(self.screen, camera_x)
        self.pedestrian_manager.draw(self.screen, camera_x)
        
        if self.show_sensors:
            self.sensors.draw_sensors(self.screen, 
                                     (self.tesla_car.x - camera_x + self.tesla_car.length // 2,
                                      self.tesla_car.y + self.tesla_car.width // 2),
                                     self.tesla_car.angle)
        
        self.tesla_car.draw(self.screen, camera_x)
        self.effects.draw(self.screen, camera_x)
        
        car_data = {
            'x': self.tesla_car.x,
            'y': self.tesla_car.y,
            'speed': self.tesla_car.speed,
            'speed_mph': self.tesla_car.get_speed_mph(),
            'angle': self.tesla_car.angle,
        }
        
        sensor_data = self.sensors.get_sensor_data()
        ai_status = self.brain.get_status()
        self.dashboard.draw(self.screen, car_data, sensor_data, ai_status)
        
        # --- Draw the Pause Button ---
        btn_color = COLORS['tesla_blue'] if not self.paused else COLORS['neon_cyan']
        pygame.draw.rect(self.screen, btn_color, self.pause_button_rect, border_radius=5)
        btn_text = "PAUSE" if not self.paused else "RESUME"
        text_surf = self.font.render(btn_text, True, COLORS['tesla_white'])
        text_rect = text_surf.get_rect(center=self.pause_button_rect.center)
        self.screen.blit(text_surf, text_rect)

        if self.debug_mode:
            self.draw_debug_info()
        
        if self.paused:
            self.draw_pause_overlay()
        
        if self.simulation_ended:
            self.draw_end_overlay()
        
        pygame.display.flip()
    
    def draw_debug_info(self):
        # Draw debug information on screen
        debug_lines = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"Car X: {self.tesla_car.x:.0f}",
            f"Camera X: {self.map_builder.camera_x:.0f}",
            f"Traffic Cars: {len(self.traffic_manager.get_cars())}",
            f"Obstacles: {len(self.obstacle_manager.get_obstacles())}",
            f"Pedestrians: {len(self.pedestrian_manager.get_pedestrians())}",
            f"Speed: {self.tesla_car.get_speed_mph()} MPH",
        ]
        
        y = 60 # Moved down to avoid overlapping with pause button
        for line in debug_lines:
            text = self.font.render(line, True, COLORS['neon_cyan'])
            self.screen.blit(text, (SCREEN_WIDTH - 150, y))
            y += 20
    
    def draw_pause_overlay(self):
        # 1. Main darkened backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 20, 180))  # Deep midnight blue tint
        self.screen.blit(overlay, (0, 0))
        
        # 2. Glassmorphism Central Panel
        panel_width, panel_height = 400, 300
        panel_rect = pygame.Rect((SCREEN_WIDTH - panel_width) // 2, 
                                 (SCREEN_HEIGHT - panel_height) // 2, 
                                 panel_width, panel_height)
        
        # Panel border and shadow effect
        pygame.draw.rect(self.screen, COLORS['tesla_blue'], panel_rect, border_radius=15, width=2)
        
        # 3. Title with Accent line
        title_font = pygame.font.Font(None, 60)
        title_text = title_font.render("SYSTEM PAUSED", True, COLORS['tesla_white'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, panel_rect.top + 50))
        self.screen.blit(title_text, title_rect)
        
        # Accent Line under title
        pygame.draw.line(self.screen, COLORS['neon_cyan'], 
                         (title_rect.left, title_rect.bottom + 5), 
                         (title_rect.right, title_rect.bottom + 5), 2)

        # 4. Styled Controls List
        hint_font = pygame.font.Font(None, 26)
        controls = [
            ("SPACE", "Resume Autopilot"),
            ("R", "Reset Simulation"),
            ("S", "Toggle Visual Sensors"),
            ("D", "Diagnostics Mode"),
            ("ESC", "Shutdown System")
        ]
        
        start_y = title_rect.bottom + 40
        for key, action in controls:
            # Draw Key box
            key_surf = hint_font.render(key, True, COLORS['neon_cyan'])
            self.screen.blit(key_surf, (panel_rect.left + 50, start_y))
            
            # Draw Action text
            action_surf = hint_font.render(action, True, COLORS['dashboard_text'])
            self.screen.blit(action_surf, (panel_rect.left + 150, start_y))
            start_y += 35

    def draw_end_overlay(self):
        # 1. Full screen dark fade
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 5, 220))
        self.screen.blit(overlay, (0, 0))
        
        # 2. Header
        header_font = pygame.font.Font(None, 70)
        status_text = "SIMULATION COMPLETE" if not self.check_collisions() else "CRITICAL FAILURE"
        status_color = COLORS['tesla_blue'] if not self.check_collisions() else (255, 50, 50)
        
        header_surf = header_font.render(status_text, True, status_color)
        header_rect = header_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(header_surf, header_rect)
        
        # 3. Stats Card
        card_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 160, 400, 100)
        pygame.draw.rect(self.screen, (30, 30, 35), card_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLORS['dashboard_text'], card_rect, border_radius=20, width=1)
        
        # 4. Content Logic
        ai_status = self.brain.get_status()
        stats = [
            ("Distance Covered:", f"{self.tesla_car.x - self.session_start_x:.0f} m"),
        ]
        
        stat_font = pygame.font.Font(None, 32)
        y_offset = 200
        for label, val in stats:
            # Label
            lbl_surf = stat_font.render(label, True, COLORS['dashboard_text'])
            self.screen.blit(lbl_surf, (card_rect.left + 30, y_offset))
            # Value
            val_surf = stat_font.render(val, True, COLORS['tesla_white'])
            val_rect = val_surf.get_rect(right=card_rect.right - 30, top=y_offset)
            self.screen.blit(val_surf, val_rect)
            y_offset += 45

        # 5. Footer Hint
        hint_font = pygame.font.Font(None, 24)
        hint_surf = hint_font.render("PRESS [R] TO RETRY  |  PRESS [ESC] TO EXIT", True, COLORS['neon_cyan'])
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(hint_surf, hint_rect)
    
    def run(self):
        # Main simulation loop
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        
        self.brain.save()
        pygame.quit()


def main():
    # Entry point with start screen
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    start_screen = StartScreen(screen)
    mode = start_screen.run()
    if mode == 'quit':
        pygame.quit()
        return
    simulator = TeslaSimulator(None)
    simulator.run()


if __name__ == "__main__":
    main()