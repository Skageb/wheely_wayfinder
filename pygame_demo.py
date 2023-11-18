import pygame

import pygame
import math
from shared_queue import shared_aruco_queue
import queue

def pygame_thread():
    try:
        print("Pygame thread starting...")
        # Initialize Pygame
        pygame.init()

        # Constants
        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        BG_COLOR = (255, 255, 255)  # White background
        TRAIL_LENGTH = 200  # Number of dots in the trail
        TRAIL_SPACING = 20


        # Arrow Class
        class Arrow(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.original_image = pygame.Surface((50, 20), pygame.SRCALPHA)
                pygame.draw.polygon(self.original_image, (0, 0, 0), [(0, 0), (30, 10), (0, 20), (10, 10)])
                self.image = self.original_image
                self.rect = self.image.get_rect(center=(x, y))
                self.direction = pygame.math.Vector2(2, 0)
                self.position = pygame.math.Vector2(x, y)
                self.angle = 0
                self.trail = []
                self.distance_since_last_trail = 0
                self.moving = False
                self.rotating = False
                self.target_angle = 0
                self.move_timer = 0
                self.rotation_speed = 0
                


            def update(self, dt):
                if self.rotating:
                    rotation_step = 4
                    if abs(self.target_angle - self.angle) < abs(rotation_step):
                        self.angle = self.target_angle
                        self.rotating = False
                    else:
                        self.angle += rotation_step
                        self.direction.rotate_ip(rotation_step)
                    self.image = pygame.transform.rotate(self.original_image, -self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)

                if self.move_timer > 0:
                    self.move_timer -= dt
                    self.position += self.direction
                    self.rect.center = self.position
                    if len(self.trail) == 0 or self.position.distance_to(self.trail[-1]) >= TRAIL_SPACING:
                        self.trail.append(self.position.copy())
                else:
                    self.moving == False
                    return

            
            def jetbot_forward(self, speed, duration):
                self.move_timer = duration*1000
                self.moving == True

            def jetbot_right(self, speed=1):
                self.rotate2(90)


            def rotate2(self, angle):
                self.target_angle = self.angle + angle
                self.rotate_speed = 4
                self.rotating = True


            def rotate(self, angle):
                self.angle += angle
                self.direction.rotate_ip(angle)
                self.image = pygame.transform.rotate(self.original_image, -self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)

            def draw_trail(self, surface):
                for point in self.trail:
                    pygame.draw.circle(surface, (0, 0, 0), (int(point.x), int(point.y)), 3)

        # Setup the screen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Arrow Game")

        # Create an arrow
        arrow = Arrow(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Clock to control the frame rate
        clock = pygame.time.Clock()

        # Game loop
        running = True
        while running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update
            arrow.update(dt)
            keys=pygame.key.get_pressed()

            try:
                new_id = shared_aruco_queue.get_nowait()  # Non-blocking get
                # Execute the corresponding function
                if new_id == 3:
                    arrow.jetbot_forward(2, 1)
                if new_id == 4:
                    arrow.jetbot_right()
            except queue.Empty:
                pass  # Do nothing if the queue is empty
            
            
            if keys[pygame.K_m]:
                arrow.jetbot_forward(2, 1)
            # Rotate the arrow with arrow keys

            if keys[pygame.K_LEFT]:
                arrow.rotate(-5)
            if keys[pygame.K_RIGHT]:
                arrow.rotate(5)

            # Draw everything
            screen.fill(BG_COLOR)
            arrow.draw_trail(screen)
            screen.blit(arrow.image, arrow.rect)
            
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

        pygame.quit()
        print("Pygame thread finished.")
    except Exception as e:
        print(f"Error in Pygame thread: {e}")

if __name__ == "__main__":
    pygame_thread()
