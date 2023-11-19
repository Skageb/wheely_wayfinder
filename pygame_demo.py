import pygame

import pygame
import math
from shared_queue import shared_aruco_queue, shared_obstacle_queue
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
        CELL_SIZE = 40
        SPEED = 1
        BROWN = (139, 69, 19)
        GREEN = (34, 139, 34)

        if __name__ == "__main__":
            CONTROLLER = 0  # For testing, 1 for aruco, 0 for keyboard
        else:
            CONTROLLER = 1


        def draw_stippled_line(surface, color, start_pos, end_pos, segments=200):
            total_distance = math.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
            segment_length = total_distance / segments
            angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])

            for i in range(segments):
                if i % 2 == 0:
                    start_segment = (start_pos[0] + math.cos(angle) * segment_length * i,
                                    start_pos[1] + math.sin(angle) * segment_length * i)
                    end_segment = (start_pos[0] + math.cos(angle) * segment_length * (i + 1),
                                start_pos[1] + math.sin(angle) * segment_length * (i + 1))
                    pygame.draw.line(surface, color, start_segment, end_segment, 2)

        def draw_stippled_circle(surface, color, center, radius, segments=200):
            for i in range(segments):
                angle = (360 / segments) * i
                x = center[0] + math.cos(math.radians(angle)) * radius
                y = center[1] + math.sin(math.radians(angle)) * radius
                if i % 2 == 0:
                    next_angle = (360 / segments) * (i + 1)
                    next_x = center[0] + math.cos(math.radians(next_angle)) * radius
                    next_y = center[1] + math.sin(math.radians(next_angle)) * radius
                    pygame.draw.line(surface, color, (x, y), (next_x, next_y), 2)

        def draw_stipled_tree(surface, x, y):
            y += 15
            x -= 5
            # Draw the trunk with stippled lines
            trunk_width = 13
            trunk_height = 40
            draw_stippled_line(surface, BROWN, (x, y), (x, y - trunk_height))
            draw_stippled_line(surface, BROWN, (x + trunk_width, y), (x + trunk_width, y - trunk_height))
            draw_stippled_line(surface, BROWN, (x, y - trunk_height), (x + trunk_width, y - trunk_height))

            # Draw the foliage with stippled circles
            leaf_radius = trunk_width
            draw_stippled_circle(surface, GREEN, (x + trunk_width // 2, y - trunk_height*1.12), leaf_radius)
            draw_stippled_circle(surface, GREEN, (x - trunk_width//2, y - trunk_height*1.12 + leaf_radius), leaf_radius)
            draw_stippled_circle(surface, GREEN, (x + trunk_width, y - trunk_height*1.12 + trunk_width), leaf_radius)


        def draw_red_cross(surface, position, size=10, color=(255, 0, 0)):
                pygame.draw.line(surface, color, (position.x - size, position.y - size), (position.x + size, position.y + size), 6)
                pygame.draw.line(surface, color, (position.x + size, position.y - size), (position.x - size, position.y + size), 6)

        
        def draw_tree(surface, x, y):
            y += 15
            x -= 5
            # Draw the trunk
            trunk_width = 13
            trunk_height = 40
            pygame.draw.rect(surface, BROWN, (x, y - trunk_height, trunk_width, trunk_height))

            # Draw the foliage
            leaf_radius = trunk_width
            pygame.draw.circle(surface, GREEN, (x + trunk_width // 2, y - trunk_height*1.12), leaf_radius)
            pygame.draw.circle(surface, GREEN, (x - trunk_width//2, y - trunk_height*1.12 + leaf_radius), leaf_radius)
            pygame.draw.circle(surface, GREEN, (x + trunk_width, y - trunk_height*1.12 + trunk_width), leaf_radius)


        def draw_grid(surface, color):
            """
            Draws a grid on the given surface.
            :param surface: Pygame surface on which to draw the grid.
            :param grid_size: Size of each grid cell.
            :param color: Color of the grid lines.
            """
            width, height = surface.get_size()
            for x in range(0, width, CELL_SIZE):  # Draw vertical lines
                pygame.draw.line(surface, color, (x, 0), (x, height))
            for y in range(0, height, CELL_SIZE):  # Draw horizontal lines
                pygame.draw.line(surface, color, (0, y), (width, y))

        class instructions():
            def __init__(self, type, duration=None):
                self.type = type
                self.duration = duration

        
        class ArucoMarker(pygame.sprite.Sprite):
            def __init__(self, image_path, position):
                super().__init__()
                # Load the image and scale it
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (30, 30))

                # Set the position of the sprite
                self.rect = self.image.get_rect(topleft=position)

        # Arrow Class
        class Arrow(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.original_image = pygame.Surface((50, 20), pygame.SRCALPHA)
                pygame.draw.polygon(self.original_image, (0, 0, 0), [(0, 0), (30, 10), (0, 20), (10, 10)])
                cone_length = 30  # Adjust as needed
                cone_width = 20   # Adjust as needed
                pygame.draw.polygon(self.original_image, (255, 0, 0, 60), [(30, 10), (30 + cone_length, 10 - cone_width // 2), (30 + cone_length, 10 + cone_width // 2)])


                self.image = self.original_image
                self.rect = self.image.get_rect(center=(x, y))
                self.direction = pygame.math.Vector2(SPEED, 0)
                self.position = pygame.math.Vector2(x, y)
                self.angle = 0
                self.trail = []
                self.distance_since_last_trail = 0
                self.moving = False
                self.rotating = False
                self.target_angle = 0
                self.move_timer = 0
                self.rotation_speed = 0
                self.simulated_position = None
                self.scanning = False
                self.pending_instructions = []
                


            def update(self, dt):
                if self.rotating:   #rotation logic
                    rotation_step = 4  # Adjust for smoother or faster rotation

                    # Normalize angles to the range [0, 360)
                    current_angle_normalized = self.angle % 360
                    target_angle_normalized = self.target_angle % 360

                    # Calculate the remaining rotation needed
                    remaining_rotation = target_angle_normalized - current_angle_normalized
                    if remaining_rotation > 180:
                        remaining_rotation -= 360  # Rotate in negative direction
                    elif remaining_rotation < -180:
                        remaining_rotation += 360  # Rotate in positive direction

                    # Determine the actual rotation step to apply
                    actual_rotation_step = min(abs(remaining_rotation), rotation_step) * (1 if remaining_rotation > 0 else -1)

                    # Apply the rotation
                    self.angle += actual_rotation_step
                    self.direction.rotate_ip(actual_rotation_step)

                    # Correct the direction vector for cardinal directions
                    if self.target_angle % 90 == 0:
                        self.direction = self.direction.normalize()

                    # Update the image and rect
                    self.image = pygame.transform.rotate(self.original_image, -self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)

                    # Check if the rotation is complete
                    if current_angle_normalized == target_angle_normalized:
                        self.rotating = False
                        self.instruction_finished()

                else:   #movement logic
                    if not self.scanning:
                        if self.move_timer > 0:
                            self.move_timer -= dt
                            self.position += self.direction
                            self.rect.center = self.position
                            if len(self.trail) == 0 or self.position.distance_to(self.trail[-1]) >= TRAIL_SPACING:
                                self.trail.append(self.position.copy())
                        else:
                            self.moving = False
                            self.instruction_finished()

            
            def jetbot_forward(self, speed, duration):
                self.move_timer = duration*1000
                self.moving = True

            def jetbot_right(self, speed=1):
                self.rotate2(90)
            
            def jetbot_left(self, speed=1):
                self.rotate2(-90)

            def calculate_final_position(self, instructions, duration):
                # Simulate the final position after a series of instructions
                simulated_position = pygame.math.Vector2(self.position)
                simulated_direction = pygame.math.Vector2(self.direction)
                for instruction in instructions:
                    if instruction == "left":
                        simulated_direction.rotate_ip(-90)
                    elif instruction == "right":
                        simulated_direction.rotate_ip(90)
                    elif instruction.startswith("forward"):
                        speed = float(SPEED)
                        duration = float(duration)
                        simulated_position += simulated_direction * speed * duration * 60  # Adjust calculation based on your movement logic
                return simulated_position


            def rotate2(self, angle):
                if not self.rotating:
                    self.target_angle = self.angle + angle
                    self.rotate_speed = 4
                    self.rotating = True

            
            def instructions_2(self):
                if (not self.moving) and (not self.rotating):
                    self.pending_instructions.insert(0, instructions("forward", 4.5))
                    self.simulated_position = self.calculate_final_position(["forward"], 4.5)
                    self.initiate_instruction()
            
            
            def instructions_3(self):
                if (not self.moving) and (not self.rotating):
                    self.pending_instructions.insert(0, instructions("left"))
                    self.pending_instructions.insert(1, instructions("forward", 2.5))
                    self.simulated_position = self.calculate_final_position(["left", "forward"], 2.5)
                    self.initiate_instruction()

            def instructions_4(self):
                if (not self.moving) and (not self.rotating):
                    self.pending_instructions.insert(0, instructions("forward", 2.5))
                    self.simulated_position = self.calculate_final_position(["forward"], 2.5)
                    self.initiate_instruction()
            
            def instructions_5(self):
                if (not self.moving) and (not self.rotating):
                    self.pending_instructions.insert(0, instructions("right"))
                    self.pending_instructions.insert(1, instructions("forward", 2.5))
                    self.simulated_position = self.calculate_final_position(["right", "forward"], 2.5)
                    self.initiate_instruction()

            
            def alternative_route(self):
                self.pending_instructions[0].duration -= 1.5
                remaining_duration = self.pending_instructions[0].duration
                if remaining_duration < 0:
                    self.pending_instructions.pop(0)
                    self.pending_instructions.insert(0, instructions("right"))
                    self.pending_instructions.insert(1, instructions("right"))
                    self.pending_instructions.insert(2, instructions("forward", - remaining_duration))
                    self.pending_instructions.insert(3, instructions("left"))
                    self.pending_instructions.insert(4, instructions("left"))

                self.pending_instructions.insert(0, instructions("left"))
                self.pending_instructions.insert(1, instructions("forward", 1))
                self.pending_instructions.insert(2, instructions("right"))
                self.pending_instructions.insert(3, instructions("forward", 1.5))
                self.pending_instructions.insert(4, instructions("right", 1))
                self.pending_instructions.insert(5, instructions("forward", 1))
                self.pending_instructions.insert(6, instructions("left"))

            def initiate_instruction(self):
                print([instruction.type for instruction in self.pending_instructions])
                if len(self.pending_instructions) > 0:
                    instruction = self.pending_instructions[0]
                    if instruction.type == "left":
                        self.jetbot_left()
                    if instruction.type == "right":
                        self.jetbot_right()
                    if instruction.type == "forward":
                        self.jetbot_forward(SPEED, instruction.duration) 
            
            def instruction_finished(self):
                if len(self.pending_instructions) > 0:
                    self.pending_instructions.pop(0)
                    self.initiate_instruction()
                else:
                    self.simulated_position = None


            def store_remaining_movement(self):
                if len(self.pending_instructions) > 0:
                    self.pending_instructions.pop(0)
                    self.pending_instructions.insert(0, instructions("forward", self.move_timer/1000))

            def rotate(self, angle):
                self.angle += angle

                self.direction.rotate_ip(angle)
                self.image = pygame.transform.rotate(self.original_image, -self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)

            def draw_trail(self, surface):
                for point in self.trail:
                    pygame.draw.circle(surface, (0, 0, 0), (int(point.x), int(point.y)), 3)

        # Setup the screen
        aruco_markers = pygame.sprite.Group()
        obstacles = []
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF, 32)
        pygame.display.set_caption("Wheely Wayfinder simulator")

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
            #Get message from obstacle queue
            try:
                #Place holder for get obstacle_message from QUeueue
                if CONTROLLER == 0:
                    obstacle_message = None
                    if keys[pygame.K_o]:
                        obstacle_message = 1
                    if keys[pygame.K_y]:
                        obstacle_message = 2
                    if keys[pygame.K_n]:
                        obstacle_message = 0
                else:
                    obstacle_message = shared_obstacle_queue.get_nowait()

                #Potential obstacle
                if obstacle_message == 1:
                    arrow.scanning = True
                    obstacle_position = arrow.position + arrow.direction.normalize() * 40
                #Obstacle confirmed
                if obstacle_message == 2:
                    if arrow.scanning:
                        obstacles.append(arrow.position + arrow.direction.normalize() * 40)
                        arrow.scanning = False
                        arrow.store_remaining_movement()
                        arrow.alternative_route()
                        arrow.initiate_instruction()
                #Potential obstacle falsified
                if obstacle_message == 0:
                    arrow.scanning = False
            except queue.Empty:
                pass


            if CONTROLLER == 1:
                #Get message from aruco queue
                try:
                    new_id = shared_aruco_queue.get_nowait()  # Non-blocking get
                    # Execute the corresponding function
                    aruco_markers.add(ArucoMarker("aruco_marker.png", tuple((arrow.position + arrow.direction.normalize() * 40))))
                    if new_id == 2:
                        arrow.instructions_2()
                    if new_id == 3:
                        arrow.instructions_3()
                    if new_id == 4:
                        arrow.instructions_4()
                    if new_id == 5:
                        arrow.instructions_5()
                except queue.Empty:
                    pass  # Do nothing if the queue is empty


            elif CONTROLLER == 0:
                if keys[pygame.K_2]:
                    arrow.instructions_2()
                    aruco_markers.add(ArucoMarker("aruco_marker.png", tuple((arrow.position + arrow.direction.normalize() * 40))))
                if keys[pygame.K_3]:
                    arrow.instructions_3()
                    aruco_markers.add(ArucoMarker("aruco_marker.png", tuple((arrow.position + arrow.direction.normalize() * 40))))
                if keys[pygame.K_4]:
                    arrow.instructions_4()
                    aruco_markers.add(ArucoMarker("aruco_marker.png", tuple((arrow.position + arrow.direction.normalize() * 40))))
                if keys[pygame.K_5]:
                    arrow.instructions_5()
                    aruco_markers.add(ArucoMarker("aruco_marker.png", tuple((arrow.position + arrow.direction.normalize() * 40))))


            # Draw everything
            screen.fill(BG_COLOR)
            draw_grid(screen, pygame.Color((200, 200, 200)))
            arrow.draw_trail(screen)
            screen.blit(arrow.image, arrow.rect)
            aruco_markers.draw(screen)

            # In your main game loop
            if arrow.simulated_position:
                draw_red_cross(screen, arrow.simulated_position)
            if arrow.scanning:
                draw_stipled_tree(screen, obstacle_position[0], obstacle_position[1])
            for obstacle in obstacles:
                draw_tree(screen, obstacle[0], obstacle[1])
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

        pygame.quit()
        print("Pygame thread finished.")
    except Exception as e:
        print(f"Error in Pygame thread: {e}")

if __name__ == "__main__":
    pygame_thread()
