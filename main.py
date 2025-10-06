"""Main game loop and state management."""
import math
import pygame
import sys
from enum import Enum, auto

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from player import PlayerBall
from level_manager import LevelManager

# Game states
class GameState(Enum):
    MENU = auto()
    CUSTOMIZE = auto()
    LEVEL_SELECT = auto()
    GAME_PLAY = auto()
    GAME_OVER = auto()

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bounce Tales Clone")
        
        # Game clock
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = GameState.MENU
        self.running = True
        
        # Game objects
        self.player = None
        self.level_manager = LevelManager()
        self.current_level = 1
        self.max_level = 3
        self.score = 0
        self.lives = 3
        
        # UI state
        self.hovered_level = None
        self.level_buttons = {}
        self.back_button_rect = None
        
        # Initialize player when starting a game
        self.init_game()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle input based on current state
            if self.state == GameState.MENU:
                self.handle_menu_events(event)
            elif self.state == GameState.CUSTOMIZE:
                self.handle_customize_events(event)
            elif self.state == GameState.LEVEL_SELECT:
                self.handle_level_select_events(event)
            elif self.state == GameState.GAME_PLAY:
                self.handle_game_play_events(event)
            elif self.state == GameState.GAME_OVER:
                self.handle_game_over_events(event)
    
    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.init_game()
                self.state = GameState.GAME_PLAY
            elif event.key == pygame.K_2:
                self.state = GameState.LEVEL_SELECT
            elif event.key == pygame.K_3:
                self.state = GameState.CUSTOMIZE
            elif event.key == pygame.K_4:
                self.running = False
    
    def draw_slider(self, surface, x, y, width, height, value, min_val, max_val, color, bg_color=(50, 50, 50), handle_color=(200, 200, 200)):
        """Draw a slider control."""
        # Draw track
        pygame.draw.rect(surface, bg_color, (x, y + height//2 - 2, width, 4), border_radius=2)
        # Draw fill
        fill_width = int((value - min_val) / (max_val - min_val) * width)
        pygame.draw.rect(surface, color, (x, y + height//2 - 2, fill_width, 4), border_radius=2)
        # Draw handle
        handle_x = x + fill_width
        pygame.draw.circle(surface, handle_color, (handle_x, y + height//2), height//2)
        pygame.draw.circle(surface, (100, 100, 100), (handle_x, y + height//2), height//2 - 2, 1)
        
        # Return the slider rect for click detection
        return pygame.Rect(x, y, width, height)
    
    def draw_button(self, surface, rect, text, color, hover_color, text_color=(255, 255, 255), font_size=24):
        """Draw a button with hover effect."""
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Draw button background
        button_color = hover_color if is_hovered else color
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 100), rect, 2, border_radius=5)
        
        # Draw button text
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
        
        return is_hovered and pygame.mouse.get_pressed()[0] == 1
    
    def draw_color_picker(self, surface, x, y, size, colors, selected_color):
        """Draw a color picker with multiple color options."""
        color_size = size // 3
        color_rects = []
        
        for i, color in enumerate(colors):
            row = i // 3
            col = i % 3
            rect = pygame.Rect(x + col * (color_size + 5), y + row * (color_size + 5), color_size, color_size)
            color_rects.append((rect, color))
            
            # Draw color square
            pygame.draw.rect(surface, color, rect)
            
            # Draw selection border if this color is selected
            if color == selected_color:
                pygame.draw.rect(surface, (255, 255, 255), rect, 3)
            else:
                pygame.draw.rect(surface, (100, 100, 100), rect, 1)
        
        return color_rects
    
    def handle_customize_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if any slider was clicked
            if hasattr(self, 'slider_rects'):
                for i, (rect, (min_val, max_val, setter)) in enumerate(self.slider_rects):
                    if rect.collidepoint(mouse_pos):
                        # Calculate value based on click position
                        value = min_val + (max_val - min_val) * ((mouse_pos[0] - rect.x) / rect.width)
                        setter(value)
            
            # Check if any color was clicked
            if hasattr(self, 'color_rects'):
                for rect, color in self.color_rects:
                    if rect.collidepoint(mouse_pos):
                        self.player.set_color(color)
            
            # Check if secondary color was clicked
            if hasattr(self, 'secondary_color_rects'):
                for rect, color in self.secondary_color_rects:
                    if rect.collidepoint(mouse_pos):
                        self.player.set_pattern_color(color)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MENU
            
            # Toggle texture with T key
            elif event.key == pygame.K_t:
                self.player.next_texture()
            
            # Toggle glow with G key
            elif event.key == pygame.K_g:
                self.player.toggle_glow()
            
            # Size adjustment with + and - keys (fine control)
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.player.set_size(self.player.customization['size'] + 1)
            elif event.key == pygame.K_MINUS:
                self.player.set_size(self.player.customization['size'] - 1)
            
            # Bounce adjustment with [ and ] keys
            elif event.key == pygame.K_LEFTBRACKET:
                self.player.set_bounce(max(0.1, self.player.customization['bounce_factor'] - 0.1))
            elif event.key == pygame.K_RIGHTBRACKET:
                self.player.set_bounce(min(1.0, self.player.customization['bounce_factor'] + 0.1))
            
            # Opacity adjustment with , and . keys
            elif event.key == pygame.K_COMMA:
                self.player.set_opacity(self.player.customization['opacity'] - 25)
            elif event.key == pygame.K_PERIOD:
                self.player.set_opacity(self.player.customization['opacity'] + 25)
            
            # Glow size adjustment with ; and ' keys
            elif event.key == pygame.K_SEMICOLON:
                self.player.set_glow_size(self.player.customization['glow_size'] - 0.1)
            elif event.key == pygame.K_QUOTE:
                self.player.set_glow_size(self.player.customization['glow_size'] + 0.1)
            elif event.key == pygame.K_t:
                current = self.player.customization['texture']
                self.player.set_texture('striped' if current == 'solid' else 'solid')
    
    def handle_level_select_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MENU
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                level_num = int(pygame.key.name(event.key))
                if 1 <= level_num <= 3:
                    self.current_level = level_num
                    self.init_game(False)
                    self.state = GameState.GAME_PLAY
        
        # Handle mouse clicks for level selection
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if a level button was clicked
            for level, button_rect in self.level_buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    self.current_level = level
                    self.init_game(False)
                    self.state = GameState.GAME_PLAY
                    return
            
            # Check if back button was clicked
            if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                self.state = GameState.MENU
    
    def handle_game_play_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MENU
            elif event.key == pygame.K_r:  # Reset level
                self.init_game(False)
                
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move_right()
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]):
            self.player.jump()
    
    def handle_game_over_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.state = GameState.MENU
    
    def init_game(self, reset_lives=True):
        """Initialize or reset the game."""
        if reset_lives:
            self.lives = 3
            self.score = 0
            self.current_level = 1
            
        # Initialize player at level start position
        start_pos = self.level_manager.load_level(self.current_level)
        if start_pos:
            self.player = PlayerBall(start_pos[0], start_pos[1])
    
    def next_level(self):
        """Advance to the next level."""
        if self.current_level < self.max_level:
            self.current_level += 1
            self.init_game(False)
            return True
        return False
    
    def update(self):
        # Update game objects based on current state
        if self.state == GameState.GAME_PLAY and self.player:
            # Check for water platforms
            water_platforms = self.level_manager.get_water_platforms()
            in_water = False
            for platform in water_platforms:
                if (platform['x'] <= self.player.x <= platform['x'] + platform['width'] and
                    platform['y'] <= self.player.y + self.player.customization['size'] <= platform['y'] + platform['height']):
                    in_water = True
                    break
            
            # Update player with water physics if needed
            self.player.update(self.level_manager.platforms, in_water)
            
            # Update level and check for win/lose conditions
            result = self.level_manager.update(self.player)
            
            if result == 'level_complete':
                self.score += 100 * self.current_level
                if not self.next_level():
                    self.state = GameState.GAME_OVER
                    
            elif result == 'player_dead' or self.player.y > SCREEN_HEIGHT + 100:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    self.init_game(False)  # Reset current level
    
    def render(self):
        # Clear the screen
        self.screen.fill((0, 0, 0))  # Black background
        
        # Render based on current state
        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.CUSTOMIZE:
            self.render_customize()
        elif self.state == GameState.LEVEL_SELECT:
            self.render_level_select()
        elif self.state == GameState.GAME_PLAY:
            self.render_game_play()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        
        # Update the display
        pygame.display.flip()
    
    def render_menu(self):
        # Modern gradient background
        for y in range(SCREEN_HEIGHT):
            # Subtle gradient from dark blue to darker blue
            color = (15, 22, 40 + y // 30)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Title with subtle shadow
        title_font = pygame.font.Font(None, 80)
        title_text = 'Bounce Tales'
        
        # Title shadow
        title_shadow = title_font.render(title_text, True, (20, 20, 40))
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_shadow.get_width()//2 + 3, 83))
        
        # Main title
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        self.screen.blit(title_surface, (SCREEN_WIDTH//2 - title_surface.get_width()//2, 80))
        
        # Menu items
        menu_items = [
            ('1. Start Game', (76, 209, 55)),
            ('2. Select Level', (52, 152, 219)),
            ('3. Customize', (155, 89, 182)),
            ('4. Quit', (231, 76, 60))
        ]
        
        # Draw menu items with hover effect
        mouse_pos = pygame.mouse.get_pos()
        font = pygame.font.Font(None, 42)
        
        for i, (text, color) in enumerate(menu_items):
            # Button background
            button_rect = pygame.Rect(
                SCREEN_WIDTH//2 - 150,
                220 + i * 70,
                300,
                60
            )
            
            # Hover effect
            is_hovered = button_rect.collidepoint(mouse_pos)
            button_color = (
                min(color[0] + 40, 255),
                min(color[1] + 40, 255),
                min(color[2] + 40, 255)
            ) if is_hovered else color
            
            # Draw button background
            pygame.draw.rect(self.screen, (30, 40, 60), button_rect, border_radius=10)
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10, width=3)
            
            # Draw button text
            text_surface = font.render(text, True, (240, 240, 240))
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)
        
        # High score
        try:
            with open('highscore.txt', 'r') as f:
                high_score = int(f.read())
            score_font = pygame.font.Font(None, 36)
            score_text = f'High Score: {high_score}'
            score_surface = score_font.render(score_text, True, (255, 215, 0))
            
            # Score background
            score_bg = pygame.Rect(
                SCREEN_WIDTH//2 - score_surface.get_width()//2 - 15,
                520,
                score_surface.get_width() + 30,
                40
            )
            pygame.draw.rect(self.screen, (30, 40, 60), score_bg, border_radius=20)
            pygame.draw.rect(self.screen, (255, 215, 0, 50), score_bg, 2, border_radius=20)
            
            self.screen.blit(
                score_surface,
                (SCREEN_WIDTH//2 - score_surface.get_width()//2, 530)
            )
        except (FileNotFoundError, ValueError):
            pass
            
        # Version info
        version_font = pygame.font.Font(None, 20)
        version_text = 'v1.0.0'
        version_surface = version_font.render(version_text, True, (100, 100, 120))
        self.screen.blit(version_surface, (SCREEN_WIDTH - version_surface.get_width() - 10, 
                                         SCREEN_HEIGHT - version_surface.get_height() - 10))
    
    def render_customize(self):
        """Render the customization screen with modern UI elements."""
        # Modern gradient background
        for y in range(SCREEN_HEIGHT):
            # Subtle gradient from dark blue to darker blue
            color = (15, 22, 40 + y // 30)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
            
        # Draw a semi-transparent panel for content
        panel = pygame.Surface((800, 500), pygame.SRCALPHA)
        panel.fill((30, 40, 60, 200))  # Semi-transparent dark blue
        pygame.draw.rect(panel, (255, 255, 255, 20), panel.get_rect(), 2, border_radius=15)
        self.screen.blit(panel, (SCREEN_WIDTH//2 - 400, 100))
        
        # Draw title with shadow
        font_large = pygame.font.Font(None, 64)
        title = font_large.render("CUSTOMIZE BALL", True, (20, 20, 30))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 33))
        title = font_large.render("CUSTOMIZE BALL", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))
        
        # Draw preview area
        preview_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 100, 300, 200)
        pygame.draw.rect(self.screen, (30, 40, 60), preview_rect, border_radius=10)
        pygame.draw.rect(self.screen, (60, 80, 120), preview_rect, 2, border_radius=10)
        
        # Draw preview ball with a subtle animation
        preview_x = SCREEN_WIDTH // 2
        preview_y = 200
        
        # Add a subtle pulse effect to the preview
        pulse = (pygame.time.get_ticks() % 2000) / 1000.0
        pulse_offset = math.sin(pulse * math.pi) * 5
        
        if self.player:
            # Save current state
            original_x, original_y = self.player.x, self.player.y
            original_size = self.player.customization['size']
            
            # Set preview state
            self.player.x, self.player.y = preview_x, preview_y + pulse_offset
            self.player.customization['size'] = 40  # Fixed size for preview
            
            # Render the ball with preview settings
            self.player.render(self.screen, is_preview=True)
            
            # Restore original state
            self.player.x, self.player.y = original_x, original_y
            self.player.customization['size'] = original_size
        
        # Draw controls panel
        panel_rect = pygame.Rect(50, 320, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 370)
        pygame.draw.rect(self.screen, (40, 50, 70, 200), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 120, 180), panel_rect, 2, border_radius=10)
        
        # Draw section headers
        font_medium = pygame.font.Font(None, 28)
        sections = ["COLORS", "APPEARANCE", "PHYSICS"]
        section_x = 70
        section_width = (SCREEN_WIDTH - 140) // 3
        
        # Draw section backgrounds and headers
        for i, section in enumerate(sections):
            section_rect = pygame.Rect(section_x + i * (section_width + 10), 340, section_width, SCREEN_HEIGHT - 400)
            pygame.draw.rect(self.screen, (30, 40, 60), section_rect, border_radius=8)
            pygame.draw.rect(self.screen, (60, 100, 160), section_rect, 1, border_radius=8)
            
            text = font_medium.render(section, True, (200, 220, 255))
            self.screen.blit(text, (section_rect.centerx - text.get_width() // 2, 350))
            
            # Draw section content
            if i == 0:  # COLORS
                # Primary colors
                colors = [
                    (255, 50, 50),   # Red
                    (50, 200, 50),   # Green
                    (50, 150, 255),  # Blue
                    (255, 200, 50),  # Yellow
                    (200, 50, 200),  # Purple
                    (50, 200, 200),  # Cyan
                    (255, 150, 50),  # Orange
                    (200, 50, 100),  # Pink
                    (100, 50, 200)   # Violet
                ]
                self.color_rects = self.draw_color_picker(self.screen, section_rect.x + 20, 380, 40, colors, 
                                                       self.player.customization['color'])
                
                # Secondary colors (for patterns)
                secondary_colors = [
                    (255, 255, 255),  # White
                    (240, 240, 240),  # Light Gray
                    (200, 200, 200),  # Silver
                    (150, 150, 150),  # Gray
                    (100, 100, 100),  # Dark Gray
                    (255, 255, 200),  # Light Yellow
                    (200, 255, 200),  # Light Green
                    (200, 200, 255),  # Light Blue
                    (255, 200, 200)   # Light Red
                ]
                text = font_medium.render("Pattern:", True, (200, 220, 255))
                self.screen.blit(text, (section_rect.x + 20, 500))
                self.secondary_color_rects = self.draw_color_picker(self.screen, section_rect.x + 20, 530, 30, 
                                                                  secondary_colors, self.player.customization['pattern_color'])
                
            elif i == 1:  # APPEARANCE
                # Size slider
                font_small = pygame.font.Font(None, 22)
                text = font_small.render(f"Size: {self.player.customization['size']}", True, (220, 220, 220))
                self.screen.blit(text, (section_rect.x + 20, 380))
                size_slider = self.draw_slider(self.screen, section_rect.x + 20, 410, section_width - 40, 30, 
                                             self.player.customization['size'], 10, 50, (100, 150, 255))
                
                # Opacity slider
                opacity_pct = int((self.player.customization['opacity'] / 255) * 100)
                text = font_small.render(f"Opacity: {opacity_pct}%", True, (220, 220, 220))
                self.screen.blit(text, (section_rect.x + 20, 460))
                opacity_slider = self.draw_slider(self.screen, section_rect.x + 20, 490, section_width - 40, 30, 
                                                self.player.customization['opacity'], 50, 255, (100, 200, 150))
                
                # Glow toggle
                glow_text = "Glow: ON" if self.player.customization['glow'] else "Glow: OFF"
                glow_color = (100, 255, 100) if self.player.customization['glow'] else (200, 100, 100)
                glow_rect = pygame.Rect(section_rect.x + 20, 560, section_width - 40, 40)
                if self.draw_button(self.screen, glow_rect, glow_text, (40, 50, 70), glow_color):
                    self.player.toggle_glow()
                
                # Glow size slider (only show if glow is on)
                if self.player.customization['glow']:
                    text = font_small.render(f"Glow Size: {self.player.customization['glow_size']:.1f}", True, (220, 220, 220))
                    self.screen.blit(text, (section_rect.x + 20, 610))
                    glow_slider = self.draw_slider(self.screen, section_rect.x + 20, 640, section_width - 40, 30, 
                                                 self.player.customization['glow_size'], 1.0, 2.5, (200, 150, 255))
                
                # Store slider rects for click handling
                self.slider_rects = [
                    (pygame.Rect(section_rect.x + 20, 410, section_width - 40, 30), 
                     (10, 50, self.player.set_size)),
                    (pygame.Rect(section_rect.x + 20, 490, section_width - 40, 30), 
                     (50, 255, lambda x: self.player.set_opacity(int(x)))),
                ]
                
                if self.player.customization['glow']:
                    self.slider_rects.append(
                        (pygame.Rect(section_rect.x + 20, 640, section_width - 40, 30), 
                         (1.0, 2.5, self.player.set_glow_size))
                    )
                
            elif i == 2:  # PHYSICS
                # Bounce factor slider
                font_small = pygame.font.Font(None, 22)
                bounce_pct = int(self.player.customization['bounce_factor'] * 100)
                text = font_small.render(f"Bounce: {bounce_pct}%", True, (220, 220, 220))
                self.screen.blit(text, (section_rect.x + 20, 380))
                bounce_slider = self.draw_slider(self.screen, section_rect.x + 20, 410, section_width - 40, 30, 
                                               self.player.customization['bounce_factor'], 0.1, 1.0, (255, 180, 100))
                
                # Texture selection
                text = font_small.render("Texture:", True, (220, 220, 220))
                self.screen.blit(text, (section_rect.x + 20, 460))
                
                texture_names = {
                    'solid': 'Solid',
                    'striped': 'Striped',
                    'gradient': 'Gradient',
                    'polka': 'Polka Dots'
                }
                texture_rect = pygame.Rect(section_rect.x + 20, 490, section_width - 40, 40)
                if self.draw_button(self.screen, texture_rect, 
                                  texture_names[self.player.customization['texture']], 
                                  (60, 70, 100), (100, 150, 255)):
                    self.player.next_texture()
                
                # Add physics slider to slider rects
                if not hasattr(self, 'slider_rects'):
                    self.slider_rects = []
                self.slider_rects.append(
                    (pygame.Rect(section_rect.x + 20, 410, section_width - 40, 30), 
                     (0.1, 1.0, self.player.set_bounce))
                )
        
        # Draw back and play buttons
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 40, 150, 40)
        play_rect = pygame.Rect(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 40, 150, 40)
        
        if self.draw_button(self.screen, back_rect, "BACK", (200, 50, 50), (230, 70, 70)):
            self.state = GameState.MENU
            
        if self.draw_button(self.screen, play_rect, "PLAY NOW!", (50, 200, 50), (70, 230, 70)):
            self.state = GameState.LEVEL_SELECT
        
        # Draw instructions
        font_small = pygame.font.Font(None, 22)
        instructions = [
            "Click and drag sliders to adjust values",
            "Click color swatches to change colors",
            "Press T to cycle through textures",
            "Press G to toggle glow effect"
        ]
        
        for i, text in enumerate(instructions):
            text_surface = font_small.render(text, True, (180, 190, 210))
            self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, SCREEN_HEIGHT - 80 - i * 25))
    
    def render_level_select(self):
        # Modern gradient background
        for y in range(SCREEN_HEIGHT):
            color = (15, 22, 40 + y // 30)  # Same as main menu
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Title with shadow
        title_font = pygame.font.Font(None, 72)
        title_text = 'SELECT LEVEL'
        title_shadow = title_font.render(title_text, True, (20, 20, 40))
        title = title_font.render(title_text, True, (255, 255, 255))
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title.get_width()//2 + 3, 83))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # Level buttons container
        container_width = 500
        container_height = 300
        container_x = (SCREEN_WIDTH - container_width) // 2
        container_y = 150
        
        # Draw container with subtle border
        container_rect = pygame.Rect(container_x, container_y, container_width, container_height)
        pygame.draw.rect(self.screen, (40, 45, 60), container_rect, border_radius=15)
        pygame.draw.rect(self.screen, (80, 90, 120), container_rect, 2, border_radius=15)
        
        # Level colors (vibrant but not too bright)
        level_colors = [
            (255, 100, 100),  # Red
            (100, 200, 100),  # Green
            (100, 150, 255)   # Blue
        ]
        
        # Track hover state
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_level = None
        
        # Draw level buttons
        button_width = 300
        button_height = 60
        button_margin = 20
        start_y = container_y + 40
        
        self.level_buttons = {}  # Reset level buttons
        
        for i in range(1, 4):
            button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - button_width // 2,
                start_y + (i-1) * (button_height + button_margin),
                button_width,
                button_height
            )
            
            # Store button rect for click detection
            self.level_buttons[i] = button_rect
            
            # Check if mouse is hovering over this button
            is_hovered = button_rect.collidepoint(mouse_pos)
            if is_hovered:
                self.hovered_level = i
                # Slight scale effect on hover
                button_rect = button_rect.inflate(10, 4)
            
            # Button shadow
            shadow_rect = button_rect.move(4, 4)
            pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow_rect, border_radius=30)
            
            # Button background with gradient
            color = level_colors[i-1]
            hover_boost = 30 if is_hovered else 0
            base_color = (
                min(255, color[0] + hover_boost),
                min(255, color[1] + hover_boost),
                min(255, color[2] + hover_boost)
            )
            
            # Draw gradient background
            for dy in range(button_rect.height):
                # Darken towards bottom
                r = max(0, base_color[0] - dy // 3)
                g = max(0, base_color[1] - dy // 3)
                b = max(0, base_color[2] - dy // 3)
                pygame.draw.rect(self.screen, (r, g, b), 
                               (button_rect.x, button_rect.y + dy, button_rect.width, 1),
                               border_radius=30)
            
            # Button border
            border_color = (255, 255, 255) if is_hovered else (200, 200, 200, 150)
            pygame.draw.rect(self.screen, border_color, button_rect, 2, border_radius=30)
            
            # Level text with shadow
            font = pygame.font.Font(None, 36)
            level_text = f'LEVEL {i}'
            
            # Text shadow
            text_surface = font.render(level_text, True, (0, 0, 0, 100))
            self.screen.blit(text_surface, 
                           (button_rect.centerx - text_surface.get_width()//2 + 2,
                            button_rect.centery - text_surface.get_height()//2 + 2))
            
            # Main text
            text_surface = font.render(level_text, True, (255, 255, 255))
            self.screen.blit(text_surface, 
                           (button_rect.centerx - text_surface.get_width()//2,
                            button_rect.centery - text_surface.get_height()//2))
        
        # Back button
        back_rect = pygame.Rect(40, 40, 120, 50)
        back_hover = back_rect.collidepoint(mouse_pos)
        
        # Button shadow
        back_shadow = back_rect.move(3, 3)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), back_shadow, border_radius=25)
        
        # Button background
        back_color = (231, 76, 60) if back_hover else (192, 57, 43)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=25)
        pygame.draw.rect(self.screen, (255, 255, 255, 100), back_rect, 2, border_radius=25)
        
        # Back button text
        back_font = pygame.font.Font(None, 32)
        back_text = back_font.render('← Back', True, (255, 255, 255))
        back_text_shadow = back_font.render('← Back', True, (0, 0, 0, 100))
        
        # Text shadow
        self.screen.blit(back_text_shadow, (back_rect.centerx - back_text.get_width()//2 + 2, 
                                          back_rect.centery - back_text.get_height()//2 + 2))
        
        # Main text
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, 
                                   back_rect.centery - back_text.get_height()//2))
        
        # Store back button rect for click detection
        self.back_button_rect = back_rect
        
        # Instructions
        instructions_font = pygame.font.Font(None, 24)
        instructions = instructions_font.render('Select a level to begin', True, (200, 200, 220))
        self.screen.blit(instructions, 
                        (SCREEN_WIDTH//2 - instructions.get_width()//2, 
                         container_y + container_height + 20))
    
    def render_game_play(self):
        # Render the level
        self.level_manager.render(self.screen)
        
        # Render the player
        if self.player:
            self.player.render(self.screen)
        
        # Create a semi-transparent overlay for HUD
        hud_surface = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
        hud_surface.fill((20, 25, 35, 180))  # Semi-transparent dark blue
        
        # Add a subtle gradient to the HUD
        for y in range(hud_surface.get_height()):
            alpha = 180 - y // 2  # Gradient from top to bottom
            pygame.draw.rect(hud_surface, (30, 35, 45, alpha), 
                           (0, y, hud_surface.get_width(), 1))
        
        # Draw the HUD overlay
        self.screen.blit(hud_surface, (0, 0))
        
        # Draw a subtle border at the bottom of the HUD
        pygame.draw.line(self.screen, (80, 90, 120, 100), 
                        (0, 80), (SCREEN_WIDTH, 80), 2)
        
        # Draw level indicator with icon
        level_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(level_icon, (100, 180, 255, 200), (20, 20), 16)  # Blue circle
        font = pygame.font.Font(None, 24)
        level_num = font.render(str(self.current_level), True, (255, 255, 255))
        level_icon.blit(level_num, 
                       (20 - level_num.get_width()//2, 
                        20 - level_num.get_height()//2))
        
        # Position and draw the level indicator
        level_x = 25
        level_y = 20
        self.screen.blit(level_icon, (level_x, level_y))
        
        # Draw lives with heart icons
        heart_icon = '❤️'  # Using text heart for simplicity
        font = pygame.font.SysFont('Arial', 28, bold=True)
        lives_text = font.render(f'×{self.lives}', True, (255, 100, 100))  # Red color for lives
        
        # Draw a heart icon next to lives
        heart_surface = font.render('❤', True, (255, 100, 100))
        self.screen.blit(heart_surface, (level_x + 60, level_y + 5))
        self.screen.blit(lives_text, (level_x + 90, level_y + 8))
        
        # Draw score with a trophy icon
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f'{self.score:06d}', True, (255, 215, 0))  # Gold color for score
        
        # Draw a small trophy icon (using text symbol for simplicity)
        trophy_icon = '🏆'
        trophy_surface = font.render('🏆', True, (255, 255, 255))
        self.screen.blit(trophy_surface, (level_x + 200, level_y + 5))
        self.screen.blit(score_text, (level_x + 235, level_y + 8))
        
        # Draw controls hint at the bottom
        controls_font = pygame.font.Font(None, 20)
        controls_text = [
            '← → : Move',
            '↑ / SPACE: Jump',
            'R: Reset Level',
            'ESC: Menu'
        ]
        
        # Draw each control hint with an icon
        control_x = SCREEN_WIDTH - 200
        control_y = 15
        control_spacing = 30
        
        for i, control in enumerate(controls_text):
            # Draw a subtle background for each control hint
            hint_surface = pygame.Surface((180, 25), pygame.SRCALPHA)
            hint_surface.fill((255, 255, 255, 20))  # Semi-transparent white
            
            # Draw the hint text
            hint_text = controls_font.render(control, True, (220, 220, 240))
            
            # Position and draw the hint
            hint_rect = pygame.Rect(control_x, control_y + i * control_spacing, 180, 25)
            
            # Rounded rectangle background
            pygame.draw.rect(self.screen, (40, 45, 60, 180), hint_rect, border_radius=12)
            pygame.draw.rect(self.screen, (80, 90, 120, 150), hint_rect, 1, border_radius=12)
            
            # Draw the text
            self.screen.blit(hint_text, (hint_rect.x + 12, hint_rect.centery - hint_text.get_height()//2))
        
        # Add a subtle pulse effect to the HUD every few seconds
        pulse = (pygame.time.get_ticks() % 5000) / 5000.0
        pulse_alpha = int(30 * (1 + math.sin(pulse * math.pi * 2)) / 2)  # 0-30 alpha pulse
        
        # Draw a subtle glow at the bottom of the HUD
        glow_height = 10
        for i in range(glow_height):
            alpha = int(30 * (1 - i / glow_height))
            pygame.draw.line(self.screen, (100, 180, 255, alpha), 
                           (0, 80 + i), (SCREEN_WIDTH, 80 + i))
    
    def render_game_over(self):
        # Save high score
        try:
            with open('highscore.txt', 'r') as f:
                high_score = int(f.read())
        except (FileNotFoundError, ValueError):
            high_score = 0
            
        if self.score > high_score:
            high_score = self.score
            with open('highscore.txt', 'w') as f:
                f.write(str(high_score))
        
        # Render game over screen
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, (255, 0, 0))
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 150))
        
        font = pygame.font.Font(None, 48)
        score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
        high_text = font.render(f'High Score: {high_score}', True, (255, 215, 0))
        
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 250))
        self.screen.blit(high_text, (SCREEN_WIDTH//2 - high_text.get_width()//2, 310))
        
        font = pygame.font.Font(None, 36)
        text = font.render('Press ENTER to return to menu', True, (200, 200, 200))
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 400))
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
