import pygame, math, random, glob, os, time

screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

#menu and main -----------------------------------------------------------------
def menu():
    pygame.font.init()
    
    title_font = pygame.font.SysFont(None, 72)
    button_font = pygame.font.SysFont(None, 36)

    clock = pygame.time.Clock()

    title_surface = title_font.render("pygame bonk fork", True, "black")
    title_rect = title_surface.get_rect(center=(640, 260))

    button_width, button_height = 200, 50
    button_rect = pygame.Rect(0, 0, button_width, button_height)
    button_rect.center = (640, 360)

    button_text = button_font.render("gae start", True, "black")
    button_text_rect = button_text.get_rect(center = button_rect.center)

    Player.group = []
    Player.id_group = {}
    Player.score = {}

    running = True
    while running:
        screen.fill((100, 100, 100))

        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return("process_ended")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True


        screen.blit(title_surface, title_rect)

        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, "gray", button_rect)
            if mouse_clicked:
                running = False
                if main() == "CLOSED":
                    running = False
                    return("process_ended")

        else:
            pygame.draw.rect(screen, (150,150,150), button_rect)

        screen.blit(button_text, button_text_rect)

        pygame.display.flip()
        clock.tick(60)

def main():
    pygame.font.init()
    font = pygame.font.Font(None, 74)
    
    global round_over, pending_reset, reset_timer, global_movement, player_collision_status

    global_movement = pygame.math.Vector2(0,0)
    player_collision_status = True
    pos_reset()
    round_over = False
    pending_reset = False
    reset_timer = 0
    global dt
    dt = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
        if not running:
            return("CLOSED")

        if Player.death_count >= len(Player.group) - 1 and not pending_reset:
            if len(Player.group) >= 2:
                win_lose()
        # make a drawing surface
        draw_surface = pygame.Surface(screen.get_size())
        draw_surface.fill("white")

        if round_over:
            # Draw all player scores dynamically
            y_offset = 200
            for idx, p in enumerate(Player.group, start=1):
                pid = p.pid
                score = Player.score[pid]
                text_surface = font.render(f"{pid.upper()} : {score}", True, p.col, "grey")
                screen.blit(text_surface, (600, y_offset))
                y_offset += 60  # move down for the next player

            for p in Player.group:
                if Player.score[p.pid] >= 7:
                    win_surface = font.render(f"{p.pid.upper()} win!", True, "white", "black")
                    screen.blit(win_surface, (550, 600))
                    pygame.display.flip()

                    end_time = pygame.time.get_ticks() + 3000
                    while pygame.time.get_ticks() < end_time:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                return
                        clock.tick(60)

                    running = False

            if pending_reset and pygame.time.get_ticks() >= reset_timer:
                pending_reset = False
                round_over = False
                global_movement = pygame.math.Vector2()
                player_collision_status = True
                pos_reset()

        else:

            if dt > 0.1:
                dt = 0
                continue

            draw_surface = pygame.Surface(screen.get_size())
            draw_surface.fill((230, 230, 230))
         
            global map_display_name, map_display_timer
            current_time = pygame.time.get_ticks()

            # Check if we are still showing the intro map title screen
            if current_time < map_display_timer:
                # 1. Just render the objects statically (No updating/moving!)
                for r in Rect.group:
                    r.render(draw_surface)
                for p in Player.group:
                    p.render(draw_surface)

                # Flip the surface so it displays right side up
                flipped_surface = pygame.transform.flip(draw_surface, False, True)
                screen.blit(flipped_surface, (0, 0))

                # 2. Overlay the Map Name in the exact center of the screen (640, 360)
                map_surface = font.render(map_display_name.upper(), True, "black", 'grey')
                map_rect = map_surface.get_rect(center=(640, 360))
                screen.blit(map_surface, map_rect)
            
            else:
                # Title is unloaded -> Run normal game movement and physics updates!
                if global_movement:
                    for r in Rect.group:
                        r.pos += global_movement * dt
                        if r.moving:
                            r.min_pos += global_movement * dt
                            r.max_pos += global_movement * dt
                        if r.rotating:
                            r.orb_center += global_movement * dt
                        
                for r in Rect.group:
                    if r.do_update or global_movement:
                        r.update(dt)
                    r.render(draw_surface)

                for p in Player.group:
                    if global_movement:
                        p.pos += global_movement * dt
                    p.move(dt)
                    p.cycle(draw_surface, dt)

                player_collision(player_collision_status)

                flipped_surface = pygame.transform.flip(draw_surface, False, True)
                screen.blit(flipped_surface, (0, 0))

        dt = clock.tick(240) / 1000
        pygame.display.flip()



def win_lose():
    global pending_reset, reset_timer, round_over
    
    if not pending_reset:  # avoid multiple calls
        if Player.death_count >= len(Player.group) - 1:
            for p in Player.group:
                if p.alive:
                    Player.score[p.pid] += 1

        pending_reset = True
        reset_timer = pygame.time.get_ticks() + 3000
        round_over = True



#player ------------------------------------------------------------------------
class Player:
    group = []
    id_group = {}
    score = {}
    death_count = 0
    def __init__(self, pid, pos_x, pos_y, col,
                 kleft, kright, kjump, kfall, kheavy, karrows,
                 radius = 20):

        self.pid = pid
        self.pos = pygame.Vector2(pos_x,pos_y)
        self.vel = pygame.math.Vector2(0, 0)
        self.accel = pygame.math.Vector2(0, 0)
        self.base_vel = pygame.math.Vector2(0, 0)      #vector force

        self.col = col
        self.radius = radius
        self.mass = self.radius * 3
        self.gravity = -200

        self.onground = False
        self.jumping = False
        self.heavy = False
        self.alive = True

        self.kleft = kleft
        self.kright = kright
        self.kjump = kjump
        self.kfall = kfall
        self.kheavy = kheavy
     
        Player.group.append(self)
        if pid not in Player.score:
            Player.score[pid] = 0
        
    def render(self, surf):
        if self.alive:
            if (self.pos.y - 20 <= screen.get_height()) and (-20 <= self.pos.x <= screen.get_width() + 20):
                pygame.draw.aacircle(surf, self.col , self.pos, 20)
                if self.heavy:
                    pygame.draw.aacircle(surf, "black", self.pos, 20, 2)
            else:
                shadow_x = min(screen.get_width() - 25, max(self.pos.x, 25))
                shadow_y = min(screen.get_height() - 25, self.pos.y)
                shadow_vector = pygame.math.Vector2(shadow_x, shadow_y)
                player_direction = (shadow_vector - self.pos).normalize()
                pygame.draw.line(surf, "black", shadow_vector, shadow_vector - player_direction * 8, 3)
                pygame.draw.circle(surf, self.col, shadow_vector, 10, 2)
            

    def physics(self, dt):
        self.vel.y += self.gravity * dt
        new_pos = self.pos + self.vel * dt

        hit_edge = False
        hit_bounce_edge = False

        #rect collision
        for rect in Rect.group:            
            for A, B in [
                (rect.t_l, rect.t_r),
                (rect.t_r, rect.b_r),
                (rect.b_r, rect.b_l),
                (rect.b_l, rect.t_l)
            ]:
                AB = B - A
                AB_len2 = AB.length_squared()
                if AB_len2 == 0:
                    continue

                t = (new_pos - A).dot(AB) / AB_len2
                t = max(0.0, min(1.0, t))

                closest = A + AB * t
                dist_vec = new_pos - closest
                dist = dist_vec.length()

                if dist <= self.radius:
                    if dist != 0:
                        normal = dist_vec.normalize()
                    else:
                        normal = pygame.math.Vector2(-AB.y, AB.x).normalize()

                    if rect.death:
                        new_pos.y = -500

                    penetration = self.radius - dist
                    new_pos += normal * penetration

                    vel_into = self.vel.dot(normal)
                    if vel_into < 0 and not rect.bouncy:
                        self.vel -= normal * vel_into

                    if rect.bouncy and not hit_bounce_edge:
                        bounce_dir = pygame.math.Vector2(dist_vec).normalize()
                        self.vel += bounce_dir * self.vel.length() * rect.bouncy
                        hit_bounce_edge = True

                    if not rect.bouncy and self.pos.y > closest.y and -10 < self.pos.x - closest.x < 10:
                        hit_edge = True

                    #moving rect callibration
                    if rect.update:
                        if rect.moving:
                            bounce_dir = pygame.math.Vector2(dist_vec).normalize()
                            self.vel += bounce_dir * (rect.speed - self.vel).dot(bounce_dir)
                        if rect.rotating and rect.rot_speed:
                            bounce_dir = pygame.math.Vector2(dist_vec).normalize()
                            bounce_speed = abs((self.pos - rect.orb_center).length() * rect.rot_speed)
                            self.vel += bounce_dir * bounce_speed

        self.onground = hit_edge
        self.pos = new_pos


    def move(self, dt):
        if self.kheavy != None:
            keys = pygame.key.get_pressed()
            if keys[self.kjump]:
                self.jump()
                self.gravity = -100
            else:
                self.gravity = -200
            if keys[self.kfall]:
                self.gravity = -350
               
            if keys[self.kleft]:
                if self.vel.x > -150:
                    self.vel.x -= 300 * dt
                else:
                    self.vel.x -= 200 * dt
            if keys[self.kright]:
                if self.vel.x < 150:
                    self.vel.x += 300 * dt
                else:
                    self.vel.x += 200 * dt

            if keys[self.kheavy]:
                self.heavy = True
            else:
                self.heavy = False


    def jump(self):
        if self.onground:
            self.vel.y = 150
            self.jumping = True


    def are_you_alive(self):
        if not self.alive:
            return
        
        if self.pos.y < -100 or self.pos.y > 6000:
            if self.alive:
                Player.death_count += 1
            self.alive = False


    def cycle(self, surf, dt):
        self.physics(dt)
        self.render(surf)
        self.are_you_alive()

def player_collision(test):
    if not test:
        return
    n = len(Player.group)

    soonp1vel = pygame.math.Vector2(0, 0)
    soonp2vel = pygame.math.Vector2(0, 0)
    
    for i in range(n-1):
        p1 = Player.group[i]
        for j in range(i+1, n):
            p2 = Player.group[j]

            diff = p2.pos - p1.pos
            dist = diff.length()
            min_dist = p1.radius + p2.radius

            if 0 < dist < min_dist:
                normal = diff.normalize()
                penetration = min_dist - dist
                correction = normal * (penetration / 2)
                p1.pos -= correction
                p2.pos += correction
                
                speed_diff = (p1.vel - p2.vel).length()
                new_vel_p1 = p1.vel.copy()
                new_vel_p2 = p2.vel.copy()

                force_dir_p1 = (p1.pos - p2.pos).normalize()
                force_dir_p2 = -force_dir_p1

                if not (p1.heavy ^ p2.heavy):   #xor method -> ^
                    new_vel_p1 += force_dir_p1 * speed_diff / 3 * 2
                    new_vel_p2 += force_dir_p2 * speed_diff / 3 * 2
                elif p1.heavy:
                    new_vel_p1 += force_dir_p1 * speed_diff / 3
                    new_vel_p2 += force_dir_p2 * speed_diff
                elif p2.heavy:
                    new_vel_p1 += force_dir_p1 * speed_diff
                    new_vel_p2 += force_dir_p2 * speed_diff / 3

                p1.vel = new_vel_p1
                p2.vel = new_vel_p2

#rect --------------------------------------------------------------------------
class Rect:
    group = []
    def __init__(self, col, center, width, height,
                 facing = 0, bouncy = False, rotation = False, movement = False, death = False):
        self.pos = center
        self.width = width
        self.height = height
        self.facing = math.radians(facing)
        self.color = pygame.Color(col)
        self.bouncy = bouncy
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel, rot_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')
        self.death = death
        self.base_image = pygame.Surface((self.width * 8, self.height * 8), pygame.SRCALPHA)
        self.base_image.fill(self.color)
        
        if self.do_update:
            if self.rotating:
                if not rotation[0]:
                    self.orb_center = self.pos
                else:
                    self.orb_center = rotation[0]
                self.orb_speed = rotation[1]
                self.rot_speed = rotation[2]
                self.vel = pygame.math.Vector2(0,0) #orb_vel

            if self.moving:
                self.min_pos = pygame.math.Vector2(self.moving[0])
                self.max_pos = pygame.math.Vector2(self.moving[1])
                self.speed = pygame.math.Vector2(self.moving[2])    #move_vel



        self.c_to_p = pygame.math.Vector2(self.width / 2, self.height / 2).length()
        self.std_f = math.atan2(self.width, self.height)

        self.points_init()

        Rect.group.append(self)

    def points_init(self):
        self.t_r = pygame.math.Vector2(
            self.pos.x + self.c_to_p * math.sin(self.std_f + self.facing),
            self.pos.y + self.c_to_p * math.cos(self.std_f + self.facing)
            )
        self.b_r = pygame.math.Vector2(
            self.pos.x + self.c_to_p * math.sin(math.pi - self.std_f + self.facing),
            self.pos.y + self.c_to_p * math.cos(math.pi - self.std_f + self.facing)
            )
        self.b_l = pygame.math.Vector2(
            self.pos.x + self.c_to_p * math.sin(self.std_f + self.facing + math.pi),
            self.pos.y + self.c_to_p * math.cos(self.std_f + self.facing + math.pi)
            )
        self.t_l = pygame.math.Vector2(
            self.pos.x + self.c_to_p * math.sin(math.pi - self.std_f + self.facing + math.pi),
            self.pos.y + self.c_to_p * math.cos(math.pi - self.std_f + self.facing + math.pi)
            )


    def render(self, screen):
        surf = pygame.transform.smoothscale(self.base_image, (self.width, self.height))
        surf = pygame.transform.rotate(surf, -math.degrees(self.facing))
        rect = surf.get_rect(center = self.pos)
        surf.blit(screen, rect)
        if self.bouncy:
            pygame.draw.aalines(
                screen, "black", True, [self.t_r, self.b_r, self.b_l, self.t_l]
                )
        elif self.death:
            pygame.draw.aalines(
                screen, "red", True, [self.t_r, self.b_r, self.b_l, self.t_l]
                )
        else:
            pygame.draw.aalines(
                screen, self.color, True, [self.t_r, self.b_r, self.b_l, self.t_l]
                )
        
    def rotation(self, dt):
        #orbiting
        pos_vector = self.pos - self.orb_center
        pos_vector.rotate_rad_ip(-self.orb_speed * dt)
        self.vel = self.orb_center + pos_vector - self.pos
        self.pos = self.orb_center + pos_vector

        #rotating
        self.facing -= self.rot_speed * dt

        self.facing %= 2 * math.pi            

    def movement(self, dt):
        #movement
        if self.min_pos.x > self.pos.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.pos.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.pos.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.pos.y:
            self.speed.y = -abs(self.speed.y)

        self.pos += self.speed * dt
        
    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)
        self.points_init()


#circle class ------------------------------------------------------------------
class Circle:
    group = []
    def __init__(self, col, center, radius,
                 bouncy = False, rotation = False, movement = False):
        self.pos = center
        self.radius = radius
        self.color = col
        self.bouncy = bouncy
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')

    def render(self, surf):
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        if self.bouncy:
            pygame.draw.circle(surf, "black", self.pos, self.radius, 2)


#map loading -------------------------------------------------------------------
def pos_reset():
    import shutil
    global players, rects, map_display_name, map_display_timer

    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    players = {}
    rects = {}
    Player.group.clear()
    Rect.group.clear()
    Player.death_count = 0
    
    if not glob.glob("maps/*.txt"):
        if glob.glob("maps/Used/*.txt"):
            for map_file in glob.glob("maps/Used/*.txt"):
                shutil.move(map_file, f"{dir_path}/maps")
        else:
            raise FileNotFoundError("no map or folder existing")

    map_files = glob.glob("maps/*.txt")
    map_c = random.choice(map_files)

    # Extract the map name and set up the 2-second display timer
    map_display_name = os.path.splitext(os.path.basename(map_c))[0]
    map_display_timer = pygame.time.get_ticks() + 2000

    bonk_map = []
    with open(map_c, "r", encoding="utf-8") as f:
        for line in f:
            if "\\" in line:
                break
            bonk_map.append(line)

    exec("".join(bonk_map))

    shutil.move(map_c, f"{dir_path}/maps/Used")

while True:
    if menu():
        pygame.quit()
        break
