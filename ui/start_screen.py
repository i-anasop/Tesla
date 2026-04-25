import pygame
import sys
import os
import asyncio

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, TITLE

class StartScreen:
    def __init__(self, screen: pygame.Surface, logo_path: str = None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if logo_path is None:
            logo_path = os.path.join(base_path, 'assets', 'tesla.png')
        
        self.video_path = os.path.join(base_path, 'assets', 'background.mp4')
        
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        if OPENCV_AVAILABLE and os.path.exists(self.video_path):
            self.video = cv2.VideoCapture(self.video_path)
        else:
            self.video = None
        
        # Load and resize logo
        try:
            self.logo = pygame.image.load(logo_path).convert_alpha()
            self.logo = pygame.transform.smoothscale(self.logo, (600, 500))
        except:
            # Fallback if image fails to load
            self.logo = pygame.Surface((600, 500), pygame.SRCALPHA)
        
        # Fonts
        pygame.font.init()
        self.font_button = pygame.font.Font(None, 40)
        
        # Button Setup
        button_width, button_height = 300, 70
        self.button_start = {
            'rect': pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, 
                                SCREEN_HEIGHT // 2 + 150, 
                                button_width, button_height),
            'text': 'Start Simulation',
            'hover': False
        }

    def _get_video_frame(self):
        """Reads, blurs, and scales video frame if OpenCV is available, else returns static background"""
        if not OPENCV_AVAILABLE or self.video is None:
            # Fallback static background for Web/Pygbag
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            surf.fill((20, 20, 25))
            return surf

        success, frame = self.video.read()
        if not success:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = self.video.read()

        # 1. Apply Blur (Ksize must be odd, higher = more blur)
        # Using (15, 15) for a soft cinematic look
        frame = cv2.GaussianBlur(frame, (35, 35), 0)

        # 2. Convert and Rotate for Pygame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.flip(frame, 1)
        
        surf = pygame.surfarray.make_surface(frame)
        
        # 3. Maintain Aspect Ratio (Cover Screen)
        img_w, img_h = surf.get_size()
        screen_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        img_ratio = img_w / img_h

        if img_ratio > screen_ratio:
            new_h = SCREEN_HEIGHT
            new_w = int(SCREEN_HEIGHT * img_ratio)
        else:
            new_w = SCREEN_WIDTH
            new_h = int(SCREEN_WIDTH / img_ratio)

        return pygame.transform.smoothscale(surf, (new_w, new_h))

    def _draw_overlay(self):
        """Slight dark tint to improve white text contrast"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 60))
        self.screen.blit(overlay, (0, 0))

    def _draw_button(self):
        """All-white button with cursor hand feedback"""
        rect = self.button_start['rect']
        mouse_pos = pygame.mouse.get_pos()
        self.button_start['hover'] = rect.collidepoint(mouse_pos)
        
        try:
            if self.button_start['hover']:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                # Solid White Hover
                pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=12)
                text_color = (0, 0, 0) # Black text
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                # Semi-transparent White Outline
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 255, 255, 30), s.get_rect(), border_radius=12)
                self.screen.blit(s, rect.topleft)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=12)
                text_color = (255, 255, 255)
        except:
            # Fallback for systems where cursor changing fails
            pygame.draw.rect(self.screen, (255, 255, 255) if self.button_start['hover'] else (100, 100, 100), rect, border_radius=12)
            text_color = (0, 0, 0) if self.button_start['hover'] else (255, 255, 255)
            
        text = self.font_button.render(self.button_start['text'], True, text_color)
        self.screen.blit(text, text.get_rect(center=rect.center))

    async def run(self) -> str:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if OPENCV_AVAILABLE and self.video is not None:
                        self.video.release()
                    return 'quit'
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if OPENCV_AVAILABLE and self.video is not None:
                            self.video.release()
                        return 'quit'
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if OPENCV_AVAILABLE and self.video is not None:
                            self.video.release()
                        return 'simulation'
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.button_start['rect'].collidepoint(event.pos):
                        if OPENCV_AVAILABLE and self.video is not None:
                            self.video.release()
                        return 'simulation'

            # Render Layers
            video_surf = self._get_video_frame()
            video_rect = video_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(video_surf, video_rect)
            
            self._draw_overlay()
            
            logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(self.logo, logo_rect)

            self._draw_button()
            
            pygame.display.flip()
            self.clock.tick(30)
            await asyncio.sleep(0)