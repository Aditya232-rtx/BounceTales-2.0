"""Player (ball) logic and physics."""
import pygame
import math
import json
from config import SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY

class PlayerBall:
    def __init__(self, x=SCREEN_WIDTH // 2, y=100):
        # Position and movement
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        
        # Customization defaults
        self.customization = {
            'color': (255, 0, 0),  # Default red
            'size': 20,            # Default radius (10-40)
            'texture': 'solid',    # 'solid', 'striped', 'gradient', 'polka'
            'bounce_factor': 0.7,  # Bounce dampening (0.1-1.0)
            'opacity': 255,        # 0-255
            'glow': False,         # Glow effect
            'glow_color': (255, 255, 200),  # Soft white glow
            'glow_size': 1.5,      # Glow size multiplier
            'pattern_color': (255, 255, 255)  # Secondary color for patterns
        }
        
        # Load saved customization if available
        self.load_customization()
        
        # Physics properties
        self.max_vel_x = 12  # Increased from 8
        self.acceleration = 0.8  # Increased from 0.5
        self.friction = 0.9
    
    def load_customization(self, filename='customization.json'):
        """Load saved customization from file."""
        try:
            with open(filename, 'r') as f:
                saved = json.load(f)
                self.customization.update(saved)
                # Convert color from list to tuple if needed
                if isinstance(self.customization['color'], list):
                    self.customization['color'] = tuple(self.customization['color'])
        except (FileNotFoundError, json.JSONDecodeError):
            # Use defaults if file doesn't exist or is invalid
            pass
    
    def save_customization(self, filename='customization.json'):
        """Save current customization to file."""
        with open(filename, 'w') as f:
            json.dump(self.customization, f)
    
    def update(self, platforms=None, in_water=False):
        """Update player position and handle collisions.
        
        Args:
            platforms: List of platform objects to check for collisions
            in_water: Boolean indicating if player is in water (affects physics)
        """
        if platforms is None:
            platforms = []
            
        # Apply gravity - reduce gravity when in water
        gravity = GRAVITY * 0.5 if in_water else GRAVITY
        self.vel_y += gravity
        
        # Apply friction when on ground
        if self.on_ground:
            self.vel_x *= self.friction
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Check for collisions with platforms
        self.on_ground = False
        for platform in platforms:
            self.check_collision(platform)
        
        # Screen boundaries
        radius = self.customization['size']
        if self.x < radius:
            self.x = radius
            self.vel_x *= -0.5
        elif self.x > SCREEN_WIDTH - radius:
            self.x = SCREEN_WIDTH - radius
            self.vel_x *= -0.5
            
        if self.y < radius:
            self.y = radius
            self.vel_y = 0
        elif self.y > SCREEN_HEIGHT - radius:
            self.y = SCREEN_HEIGHT - radius
            self.vel_y = -self.vel_y * self.customization['bounce_factor']
            self.on_ground = True
    
    def move_left(self):
        """Move the ball left."""
        if abs(self.vel_x) < self.max_vel_x:
            self.vel_x -= self.acceleration
    
    def move_right(self):
        """Move the ball right."""
        if abs(self.vel_x) < self.max_vel_x:
            self.vel_x += self.acceleration
    
    def jump(self):
        """Make the ball jump if on ground."""
        if self.on_ground:
            self.vel_y = -15  # Jump strength
            self.on_ground = False
    
    def check_collision(self, platform):
        """Check and handle collision with a platform."""
        radius = self.customization['size']
        
        # Get closest point on platform to circle
        closest_x = max(platform['x'], min(self.x, platform['x'] + platform['width']))
        closest_y = max(platform['y'], min(self.y, platform['y'] + platform['height']))
        
        # Calculate distance between closest point and circle center
        distance = math.sqrt((self.x - closest_x)**2 + (self.y - closest_y)**2)
        
        if distance <= radius:
            # Collision detected
            if closest_y == platform['y']:  # Top collision
                self.y = platform['y'] - radius
                self.vel_y = -self.vel_y * self.customization['bounce_factor']
                self.on_ground = True
            elif closest_y == platform['y'] + platform['height']:  # Bottom collision
                self.y = platform['y'] + platform['height'] + radius
                self.vel_y = -self.vel_y * 0.5
            elif closest_x == platform['x']:  # Left collision
                self.x = platform['x'] - radius
                self.vel_x *= -0.5
            else:  # Right collision
                self.x = platform['x'] + platform['width'] + radius
                self.vel_x *= -0.5
    
    def move_left(self):
        """Move the ball left."""
        if abs(self.vel_x) < self.max_vel_x:
            self.vel_x -= self.acceleration
    
    def move_right(self):
        """Move the ball right."""
        if abs(self.vel_x) < self.max_vel_x:
            self.vel_x += self.acceleration
    
        """Make the ball jump if on ground."""
        if self.on_ground:
            self.vel_y = -12  # Jump strength
            self.on_ground = False
    
    def render(self, surface, is_preview=False):
        """Draw the player on the given surface.
        
        Args:
            surface: The surface to draw on
            is_preview: If True, renders with preview-specific settings
        """
        radius = self.customization['size']
        x, y = int(self.x), int(self.y)
        
        # Create a surface for the ball to handle transparency
        ball_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # Draw glow effect if enabled
        if self.customization['glow'] and not is_preview:
            glow_radius = int(radius * self.customization['glow_size'])
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            for i in range(3):
                alpha = 100 - (i * 25)
                if alpha > 0:
                    pygame.draw.circle(
                        glow_surface, 
                        (*self.customization['glow_color'], alpha),
                        (glow_radius, glow_radius),
                        glow_radius - (i * 3)
                    )
            surface.blit(glow_surface, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_ADD)
        
        # Draw the ball based on texture type
        if self.customization['texture'] == 'striped':
            # Striped pattern
            pygame.draw.circle(ball_surface, (*self.customization['color'], self.customization['opacity']), 
                             (radius, radius), radius)
            # Add stripes
            stripe_width = max(2, radius // 5)
            for i in range(-radius, radius, stripe_width * 2):
                pygame.draw.line(
                    ball_surface, 
                    (*[min(c + 40, 255) for c in self.customization['color']], self.customization['opacity']),
                    (0, radius + i),
                    (radius * 2, radius + i),
                    stripe_width
                )
        elif self.customization['texture'] == 'gradient':
            # Gradient effect
            for r in range(radius, 0, -1):
                color = [max(0, c - (radius - r) * 2) for c in self.customization['color']]
                alpha = min(255, self.customization['opacity'] * r // radius + 50)
                pygame.draw.circle(ball_surface, (*color, alpha), (radius, radius), r)
        elif self.customization['texture'] == 'polka':
            # Polka dot pattern
            pygame.draw.circle(ball_surface, (*self.customization['color'], self.customization['opacity']), 
                             (radius, radius), radius)
            dot_size = max(2, radius // 5)
            for i in range(0, 360, 45):
                dot_x = radius + int((radius - dot_size) * math.cos(math.radians(i)))
                dot_y = radius + int((radius - dot_size) * math.sin(math.radians(i)))
                pygame.draw.circle(ball_surface, 
                                 (*self.customization['pattern_color'], self.customization['opacity']),
                                 (dot_x, dot_y), dot_size)
        else:  # solid
            pygame.draw.circle(ball_surface, (*self.customization['color'], self.customization['opacity']), 
                             (radius, radius), radius)
        
        # Draw the ball onto the main surface
        surface.blit(ball_surface, (x - radius, y - radius), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def set_color(self, color):
        """Set the ball's primary color."""
        self.customization['color'] = color
        self.save_customization()
    
    def set_pattern_color(self, color):
        """Set the ball's secondary color for patterns."""
        self.customization['pattern_color'] = color
        self.save_customization()
    
    def set_size(self, size):
        """Set the ball's size (radius)."""
        self.customization['size'] = max(10, min(50, int(size)))
        self.save_customization()
    
    def set_bounce(self, factor):
        """Set the ball's bounce factor (0.1 to 1.0)."""
        self.customization['bounce_factor'] = max(0.1, min(1.0, float(factor)))
        self.save_customization()
    
    def set_opacity(self, value):
        """Set the ball's opacity (0-255)."""
        self.customization['opacity'] = max(0, min(255, int(value)))
        self.save_customization()
    
    def set_texture(self, texture):
        """Set the ball's texture type."""
        if texture in ['solid', 'striped', 'gradient', 'polka']:
            self.customization['texture'] = texture
            self.save_customization()
    
    def toggle_glow(self):
        """Toggle the glow effect on/off."""
        self.customization['glow'] = not self.customization['glow']
        self.save_customization()
    
    def set_glow_size(self, size):
        """Set the glow size multiplier (1.0 to 2.5)."""
        self.customization['glow_size'] = max(1.0, min(2.5, float(size)))
        self.save_customization()
    
    def next_texture(self):
        """Cycle to the next texture option."""
        textures = ['solid', 'striped', 'gradient', 'polka']
        current_idx = textures.index(self.customization['texture'])
        next_idx = (current_idx + 1) % len(textures)
        self.set_texture(textures[next_idx])
    
    def get_customization(self):
        """Return a copy of the current customization settings."""
        return self.customization.copy()
