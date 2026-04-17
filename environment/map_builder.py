# TESLA Map Builder Module

import pygame
import random
import math
from typing import List, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, LANE_WIDTH, NUM_LANES,
    ROAD_Y_START, ROAD_HEIGHT, ROAD_MARGIN
)


class Tree:
    """Tree class for displaying tree PNG images as decorative elements"""

    # Cache loaded tree image
    tree_image = None
    tree_width = 0
    tree_height = 0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.image = self._load_tree_image()

    def _load_tree_image(self):
        """Load tree image from assets folder without scaling"""
        if Tree.tree_image is not None:
            return Tree.tree_image

        try:
            asset_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tree.png')
            if os.path.exists(asset_path):
                image = pygame.image.load(asset_path)
                Tree.tree_image = image
                Tree.tree_width = image.get_width()
                Tree.tree_height = image.get_height()
                return image
        except Exception as e:
            print(f"Warning: Could not load tree.png: {e}")

        return None

    def draw(self, screen: pygame.Surface, offset_x: float = 0):
        """Draw the tree image at original size with shadow"""
        x = self.x - offset_x
        if x < -Tree.tree_width or x > SCREEN_WIDTH:
            return

        # Draw Shadow (UX/UI Improvement: Adds depth)
        shadow_width = Tree.tree_width * 0.6
        shadow_height = Tree.tree_height * 0.2
        shadow_surface = pygame.Surface((int(shadow_width), int(shadow_height)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 60), (0, 0, int(shadow_width), int(shadow_height)))
        
        # Position shadow at the base of the tree
        screen.blit(shadow_surface, (int(x + (Tree.tree_width - shadow_width) / 2), int(self.y + Tree.tree_height - shadow_height / 2)))

        if self.image is not None:
            screen.blit(self.image, (int(x), int(self.y)))


class Building:
    """Building class for displaying house PNG images"""

    # Cache loaded house images
    house_images = {}

    def __init__(self, x: float, y: float, width: int, height: int, house_number: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.house_number = house_number
        self.image = self._load_house_image()

    def _load_house_image(self):
        """Load house image from assets folder"""
        key = (self.house_number, int(self.width), int(self.height))
        if key in Building.house_images:
            return Building.house_images[key]

        try:
            asset_path = os.path.join(os.path.dirname(__file__), '..', 'assets', f'house{self.house_number}.png')
            if os.path.exists(asset_path):
                image = pygame.image.load(asset_path)
                # Use smoothscale for better quality (UI Improvement)
                image = pygame.transform.smoothscale(image, (int(self.width), int(self.height)))
                Building.house_images[key] = image
                return image
        except Exception as e:
            print(f"Warning: Could not load house{self.house_number}.png: {e}")

        return None

    def draw(self, screen: pygame.Surface, offset_x: float = 0):
        """Draw the house image with shadow and improved white border path"""
        x = self.x - offset_x
        if x < -self.width or x > SCREEN_WIDTH:
            return

        # Draw Shadow
        shadow_rect = pygame.Rect(int(x) + 10, int(self.y) + 10, int(self.width), int(self.height))
        s = pygame.Surface((int(self.width), int(self.height)), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 50), s.get_rect(), border_radius=5)
        screen.blit(s, (int(x) + 5, int(self.y) + 5))

        if self.image is not None:
            screen.blit(self.image, (int(x), int(self.y)))
            
            # Draw white bold border as path around house with rounded corners (UI Improvement)
            border_rect = pygame.Rect(int(x) - 5, int(self.y) - 5, int(self.width) + 10, int(self.height) + 10)
            # Use border_radius for softer look
            pygame.draw.rect(screen, (255, 255, 255), border_rect, 3, border_radius=8)


class ZebraCrossing:
    """Zebra crossing element"""

    def __init__(self, x: float):
        self.x = x
        self.width = 60
        self.stripe_width = 8
        self.stripe_gap = 8

    def draw(self, screen: pygame.Surface, offset_x: float = 0):
        """Draw zebra crossing with perspective/depth hints"""
        x = self.x - offset_x
        if x < -self.width or x > SCREEN_WIDTH:
            return

        road_top = ROAD_Y_START
        road_bottom = ROAD_Y_START + ROAD_HEIGHT

        num_stripes = self.width // (self.stripe_width + self.stripe_gap)
        for i in range(num_stripes):
            stripe_x = x + i * (self.stripe_width + self.stripe_gap)
            
            # Draw stripe shadow for depth
            pygame.draw.rect(screen, (50, 50, 50),
                             (stripe_x + 1, road_top + 1, self.stripe_width, road_bottom - road_top))
            
            # Draw main stripe
            pygame.draw.rect(screen, COLORS['zebra_crossing'],
                             (stripe_x, road_top, self.stripe_width, road_bottom - road_top))

    def get_rect(self, offset_x: float = 0) -> pygame.Rect:
        """Get collision rect for zebra crossing"""
        return pygame.Rect(self.x - offset_x, ROAD_Y_START,
                           self.width, ROAD_HEIGHT)


class MapBuilder:
    """Main map builder class"""

    def __init__(self):
        self.buildings: List[Building] = []
        self.trees: List[Tree] = []
        self.zebra_crossings: List[ZebraCrossing] = []

        self.world_length = 5000
        self.camera_x = 0

        self._generate_decorations()
        self._generate_trees()
        self._generate_zebra_crossings()

    def _generate_decorations(self):
        """Generate buildings with fixed symmetric placement on both sides"""
        house_width = 120
        house_height = 100
        house_gap = 150
        house_counter = 1

        # Top side houses (above road)
        top_y = 25
        x = 50
        while x < self.world_length:
            house_number = ((house_counter - 1) % 8) + 1
            self.buildings.append(Building(x, top_y, house_width, house_height, house_number))
            house_counter += 1
            x += house_width + house_gap

        # Bottom side houses (below road)
        bottom_y = ROAD_Y_START + ROAD_HEIGHT + 125
        x = 50
        while x < self.world_length:
            house_number = ((house_counter - 1) % 8) + 1
            self.buildings.append(Building(x, bottom_y, house_width, house_height, house_number))
            house_counter += 1
            x += house_width + house_gap

    def _generate_trees(self):
        """Generate trees connected as path along both sides of the road"""
        temp_tree = Tree(0, 0)
        tree_width = Tree.tree_width if Tree.tree_width > 0 else 50
        tree_height = Tree.tree_height if Tree.tree_height > 0 else 60
        tree_spacing = tree_width - 10

        # Top side trees
        x = 0
        while x < self.world_length:
            top_y = ROAD_Y_START - ROAD_MARGIN - tree_height // 2
            self.trees.append(Tree(x, top_y))
            x += tree_spacing

        # Bottom side trees
        x = 0
        while x < self.world_length:
            bottom_y = ROAD_Y_START + ROAD_HEIGHT + ROAD_MARGIN - tree_height // 2
            self.trees.append(Tree(x, bottom_y))
            x += tree_spacing

    def _generate_zebra_crossings(self):
        """Generate zebra crossings at intervals"""
        for x in range(400, self.world_length, 400):
            if random.random() > 0.5:
                self.zebra_crossings.append(ZebraCrossing(x))

    def update_camera(self, car_x: float):
        """Update camera position with Linear Interpolation (Lerp) for smoothness"""
        # UX Improvement: Smooth camera follow instead of hard lock
        target_x = car_x - SCREEN_WIDTH // 3
        desired_x = max(0, min(target_x, self.world_length - SCREEN_WIDTH))
        
        # Smoothly interpolate current camera position to desired position
        # 0.1 is the smoothing factor (lower is smoother/slower)
        self.camera_x += (desired_x - self.camera_x) * 0.1

    def draw_background(self, screen: pygame.Surface):
        """Draw background gradient with enhanced dithering/colors"""
        # Drawing in larger chunks for performance, but keeping gradient
        chunk_height = 4
        for y in range(0, SCREEN_HEIGHT, chunk_height):
            ratio = y / SCREEN_HEIGHT
            # Richer gradient: Deep Sky Blue to Soft Horizon White/Cream
            r = int(135 * (1 - ratio) + 240 * ratio)
            g = int(206 * (1 - ratio) + 235 * ratio)
            b = int(235 * (1 - ratio) + 225 * ratio)
            # Clamp values
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
            pygame.draw.rect(screen, (r, g, b), (0, y, SCREEN_WIDTH, chunk_height))

    def draw_grass(self, screen: pygame.Surface):
        """Draw grass areas"""
        # Top Grass
        top_grass = pygame.Rect(0, 0, SCREEN_WIDTH, ROAD_Y_START - ROAD_MARGIN)
        pygame.draw.rect(screen, COLORS['grass'], top_grass)

        # Bottom Grass
        bottom_y = ROAD_Y_START + ROAD_HEIGHT + ROAD_MARGIN
        bottom_grass = pygame.Rect(0, bottom_y, SCREEN_WIDTH, SCREEN_HEIGHT - bottom_y)
        pygame.draw.rect(screen, COLORS['grass'], bottom_grass)

    def draw_road(self, screen: pygame.Surface):
        """Draw the multi-lane road with improved curbs and markings"""
        road_full_y = ROAD_Y_START - ROAD_MARGIN
        road_full_h = ROAD_HEIGHT + ROAD_MARGIN * 2
        
        # Draw "Curb/Shoulder" (Grey concrete color)
        pygame.draw.rect(screen, (160, 160, 160), (0, road_full_y, SCREEN_WIDTH, road_full_h))
        
        # Draw Main Asphalt
        road_rect = pygame.Rect(0, ROAD_Y_START, SCREEN_WIDTH, ROAD_HEIGHT)
        pygame.draw.rect(screen, COLORS['road'], road_rect)

        # Draw Solid Yellow Edge Lines with slight glow/width
        pygame.draw.line(screen, COLORS['road_line_yellow'],
                         (0, ROAD_Y_START + 2), (SCREEN_WIDTH, ROAD_Y_START + 2), 4)
        pygame.draw.line(screen, COLORS['road_line_yellow'],
                         (0, ROAD_Y_START + ROAD_HEIGHT - 2), 
                         (SCREEN_WIDTH, ROAD_Y_START + ROAD_HEIGHT - 2), 4)

        # Draw Lane Markings
        for i in range(1, NUM_LANES):
            y = ROAD_Y_START + i * LANE_WIDTH

            dash_length = 30
            gap_length = 20
            # Offset x based on camera to create moving effect
            x = -int(self.camera_x % (dash_length + gap_length))

            while x < SCREEN_WIDTH:
                # White lane markings
                pygame.draw.line(screen, COLORS['lane_marking'],
                                 (x, y), (x + dash_length, y), 2)
                x += dash_length + gap_length

    def draw_decorations(self, screen: pygame.Surface):
        """Draw all decorative elements"""
        for building in self.buildings:
            building.draw(screen, self.camera_x)

    def draw_trees(self, screen: pygame.Surface):
        """Draw all trees on both sides of road"""
        for tree in self.trees:
            tree.draw(screen, self.camera_x)

    def draw_zebra_crossings(self, screen: pygame.Surface):
        """Draw zebra crossings"""
        for crossing in self.zebra_crossings:
            crossing.draw(screen, self.camera_x)

    def draw_building_to_path_connections(self, screen: pygame.Surface):
        """Draw sandy paths connecting buildings to tree paths"""
        top_tree_y = ROAD_Y_START - ROAD_MARGIN - Tree.tree_height // 2
        bottom_tree_y = ROAD_Y_START + ROAD_HEIGHT + ROAD_MARGIN + Tree.tree_height // 2

        for b in self.buildings:
            center_x = b.x + b.width // 2
            screen_x = center_x - self.camera_x
            if screen_x < -max(b.width, 50) or screen_x > SCREEN_WIDTH + max(b.width, 50):
                continue

            if b.y < ROAD_Y_START:
                start_y = b.y + b.height
                end_y = top_tree_y
            else:
                start_y = b.y
                end_y = bottom_tree_y

            # Draw main path line
            pygame.draw.line(screen, COLORS['path_to_trees'], (screen_x, start_y), (screen_x, end_y), 14)
            # Draw rounded caps for smoother look
            pygame.draw.circle(screen, COLORS['path_to_trees'], (int(screen_x), int(start_y)), 7)
            pygame.draw.circle(screen, COLORS['path_to_trees'], (int(screen_x), int(end_y)), 7)

    def draw_path_to_road(self, screen: pygame.Surface):
        """Draw greyish paths connecting tree paths to road with rounded caps"""
        tree_width = Tree.tree_width if Tree.tree_width > 0 else 50
        tree_spacing = tree_width - 10

        # Helper to draw single path segment
        def draw_segment(sx, sy, ey):
            pygame.draw.line(screen, COLORS['path_to_road'], (sx, sy), (sx, ey), 8)
            # Add subtle rounded end near the road
            pygame.draw.circle(screen, COLORS['path_to_road'], (int(sx), int(ey)), 4)

        # Top path to road
        top_tree_y = ROAD_Y_START - ROAD_MARGIN - Tree.tree_height // 2
        top_road_y = ROAD_Y_START
        x = 0
        while x < SCREEN_WIDTH + self.camera_x:
            screen_x = x - self.camera_x
            if -tree_width < screen_x < SCREEN_WIDTH:
                draw_segment(screen_x, top_tree_y, top_road_y)
            x += tree_spacing

        # Bottom path to road
        bottom_tree_y = ROAD_Y_START + ROAD_HEIGHT + ROAD_MARGIN + Tree.tree_height // 2
        bottom_road_y = ROAD_Y_START + ROAD_HEIGHT
        x = 0
        while x < SCREEN_WIDTH + self.camera_x:
            screen_x = x - self.camera_x
            if -tree_width < screen_x < SCREEN_WIDTH:
                draw_segment(screen_x, bottom_tree_y, bottom_road_y)
            x += tree_spacing

    def draw(self, screen: pygame.Surface):
        """Draw complete map (Painter's Algorithm order)"""
        self.draw_background(screen)
        self.draw_grass(screen)
        self.draw_path_to_road(screen)
        self.draw_road(screen)
        self.draw_building_to_path_connections(screen)
        # Trees and Buildings drawn last to pop over ground elements
        self.draw_trees(screen)
        self.draw_zebra_crossings(screen)
        self.draw_decorations(screen)

    def get_zebra_crossings(self) -> List[ZebraCrossing]:
        """Get list of zebra crossings"""
        return self.zebra_crossings

    def world_to_screen(self, world_x: float) -> float:
        """Convert world X coordinate to screen X"""
        return world_x - self.camera_x

    def screen_to_world(self, screen_x: float) -> float:
        """Convert screen X coordinate to world X"""
        return screen_x + self.camera_x