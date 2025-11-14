# ...existing code...
import pygame
import sys
import random
import math
import os

pygame.init()

# --- CONFIGURACIÓN DE PANTALLA ---
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Mini Final Fight - IA Mejorada")
clock = pygame.time.Clock()

# --- COLORES ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 30, 30)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
GRAY = (60, 60, 60)
GROUND = (100, 100, 100)
DARK_RED = (120, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 150, 0)
LIGHT_GRAY = (180, 180, 180)

# --- FUENTE ---
font = pygame.font.Font(None, 50)
menu_font = pygame.font.Font(None, 80)

# --- ASSETS ---
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

def load_image(name, size=None):
    path = os.path.join(ASSET_DIR, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception as e:
        print(f"No se pudo cargar {path}: {e}")
        surf = pygame.Surface(size if size else (50, 80), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 180))  # magenta visible para debug
        return surf

# Tamaños ajustables (aumentados)
PLAYER_SIZE = (100, 160)
ENEMY_SIZE = (100, 160)
PACK_SIZE = (50, 50)

player_img = load_image("player.png", PLAYER_SIZE)
enemy_img = load_image("enemy.png", ENEMY_SIZE)
pack_img = load_image("pack.png", PACK_SIZE)

# --- BOTONES ---
def draw_button(text, rect, color, text_color=WHITE):
    pygame.draw.rect(screen, color, rect)
    label = menu_font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def menu():
    while True:
        screen.fill(GRAY)
        play_button = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 80, 300, 70)
        exit_button = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 20, 300, 70)
        draw_button("JUGAR", play_button, BLUE)
        draw_button("SALIR", exit_button, RED)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if play_button.collidepoint(mx, my):
                    return
                if exit_button.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

# --- JUEGO ---
def game():
    # --- JUGADOR ---
    player = pygame.Rect(0, 0, PLAYER_SIZE[0], PLAYER_SIZE[1])
    player_speed = 10
    player_health = 100
    max_health = 100
    damage_timer = 0

    # --- ATAQUES ---
    punch_damage = 8
    kick_damage = 5
    punching = False
    kicking = False
    blocking = False
    attack_cooldown = 0

    # --- ENEMIGOS ---
    enemies = []
    enemy_speed = 3            # <-- un poco más rápido
    MAX_ENEMIES = 25
    kills = 0
    enemy_spawn_timer = 0
    ENEMY_SPAWN_INTERVAL = 120 # aparecen menos frecuentes
    enemy_max_health = 800

    # --- BOTIQUINES ---
    health_packs = []
    MAX_HEALTH_PACKS = 10
    HEALTH_PACK_SPAWN_CHANCE = 0.004

    # --- CÁMARA ---
    camera_x = 0
    camera_y = 0

    # --- LÍMITES DEL CARRIL ---
    LANE_TOP = -200
    LANE_BOTTOM = 300

    # --- FUNCIONES ---
    def spawn_enemy():
        if len(enemies) < MAX_ENEMIES:
            side = random.choice(["front", "back", "side"])
            offset_x = random.randint(800, 2500)
            offset_y = random.randint(LANE_TOP, LANE_BOTTOM)
            if side == "front":
                ex = player.x + offset_x
            elif side == "back":
                ex = player.x - offset_x
            else:
                ex = player.x + random.choice([-offset_x, offset_x])
            ey = offset_y
            rect = pygame.Rect(ex, ey, ENEMY_SIZE[0], ENEMY_SIZE[1])
            enemies.append({
                "rect": rect,
                "health": enemy_max_health,
                "angle_offset": random.uniform(-0.5, 0.5),
                "stunned": 0
            })

    def spawn_health_pack():
        if len(health_packs) < MAX_HEALTH_PACKS and random.random() < HEALTH_PACK_SPAWN_CHANCE:
            hx = player.x + random.randint(-2500, 2500)
            hy = random.randint(LANE_TOP, LANE_BOTTOM)
            health_packs.append(pygame.Rect(hx, hy, PACK_SIZE[0], PACK_SIZE[1]))

    def enemy_ai(enemy):
        rect = enemy["rect"]
        if enemy["stunned"] > 0:
            enemy["stunned"] -= 1
            return
        dx = player.x - rect.x
        dy = player.y - rect.y
        angle = math.atan2(dy, dx) + enemy["angle_offset"]
        new_x = rect.x + int(math.cos(angle) * enemy_speed)
        new_y = rect.y + int(math.sin(angle) * enemy_speed)
        temp_rect = rect.copy()
        temp_rect.x = new_x
        temp_rect.y = new_y
        collision = False
        for other in enemies:
            if other != enemy and temp_rect.colliderect(other["rect"]):
                collision = True
                break
        if not collision:
            rect.x = new_x
            rect.y = new_y
        if rect.y < LANE_TOP: rect.y = LANE_TOP
        if rect.y > LANE_BOTTOM: rect.y = LANE_BOTTOM

    def separate_enemies():
        for i, e1 in enumerate(enemies):
            for j, e2 in enumerate(enemies):
                if i != j:
                    r1, r2 = e1["rect"], e2["rect"]
                    if r1.colliderect(r2):
                        dx = r1.centerx - r2.centerx
                        dy = r1.centery - r2.centery
                        dist = max(1, math.sqrt(dx**2 + dy**2))
                        push = 2
                        r1.x += int(push * dx / dist)
                        r1.y += int(push * dy / dist)

    # --- BUCLE PRINCIPAL ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if player_health > 0:
                    if event.key == pygame.K_k:
                        blocking = True
                    elif not blocking and attack_cooldown == 0:
                        if event.key == pygame.K_u:
                            punching = True
                            attack_cooldown = 20
                        elif event.key == pygame.K_j:
                            kicking = True
                            attack_cooldown = 20
                        elif event.key == pygame.K_i:
                            for enemy in enemies:
                                if player.colliderect(enemy["rect"]):
                                    enemy["stunned"] = 300
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_k:
                    blocking = False

        keys = pygame.key.get_pressed()
        if player_health > 0:
            if keys[pygame.K_LEFT]: player.x -= player_speed
            if keys[pygame.K_RIGHT]: player.x += player_speed
            if keys[pygame.K_UP]: player.y -= player_speed
            if keys[pygame.K_DOWN]: player.y += player_speed
            if player.y < LANE_TOP: player.y = LANE_TOP
            if player.y > LANE_BOTTOM: player.y = LANE_BOTTOM

        if player_health > 0:
            enemy_spawn_timer += 1
            if enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL:
                spawn_enemy()
                enemy_spawn_timer = 0

        for enemy in enemies[:]:
            if player_health > 0:
                enemy_ai(enemy)
                rect = enemy["rect"]
                if player.colliderect(rect):
                    if damage_timer == 0:
                        player_health -= 2 if blocking else 5
                        damage_timer = 30
                if punching and player.colliderect(rect):
                    enemy["health"] -= punch_damage
                if kicking and player.colliderect(rect):
                    enemy["health"] -= kick_damage
                if enemy["health"] <= 0:
                    enemies.remove(enemy)
                    kills += 1

        separate_enemies()

        if attack_cooldown > 0:
            attack_cooldown -= 1
        else:
            punching = kicking = False
        if damage_timer > 0:
            damage_timer -= 1

        if player_health > 0:
            spawn_health_pack()
            for pack in health_packs[:]:
                if player.colliderect(pack):
                    player_health = min(max_health, player_health + 30)  # <-- botiquines dan 30 de vida
                    health_packs.remove(pack)

        camera_x = player.x - SCREEN_WIDTH // 2
        camera_y = player.y - SCREEN_HEIGHT // 2

        # --- DIBUJADO ---
        screen.fill(GRAY)
        tile_size = 200
        for i in range(-5, 25):
            for j in range(-3, 10):
                tx = i * tile_size - (camera_x % tile_size)
                ty = j * tile_size - (camera_y % tile_size)
                pygame.draw.rect(screen, GROUND, (tx, ty, tile_size - 2, tile_size - 2))

        # Jugador (centrado en pantalla)
        px = SCREEN_WIDTH // 2 - player_img.get_width() // 2
        py = SCREEN_HEIGHT // 2 - player_img.get_height() // 2
        screen.blit(player_img, (px, py))

        # Enemigos
        for enemy in enemies:
            rect = enemy["rect"]
            ex, ey = rect.x - camera_x, rect.y - camera_y
            img = enemy_img.copy()
            if enemy["stunned"] > 0:
                img.fill((180,180,180,180), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(img, (ex, ey))
            ratio = max(enemy["health"], 0) / enemy_max_health
            pygame.draw.rect(screen, DARK_RED, (ex, ey - 10, ENEMY_SIZE[0], 5))
            pygame.draw.rect(screen, YELLOW, (ex, ey - 10, ENEMY_SIZE[0] * ratio, 5))

        # Botiquines
        for pack in health_packs:
            screen.blit(pack_img, (pack.x - camera_x, pack.y - camera_y))

        # HUD
        bar_w = 300
        pygame.draw.rect(screen, DARK_RED, (20, 20, bar_w, 25))
        pygame.draw.rect(screen, GREEN, (20, 20, (player_health / max_health) * bar_w, 25))
        hud = font.render(f"Vida: {player_health} | Kills: {kills} | Enemigos: {len(enemies)}", True, WHITE)
        screen.blit(hud, (20, 60))

        # Game Over
        if player_health <= 0:
            go = font.render("💀 GAME OVER - Presiona ESC para salir", True, RED)
            screen.blit(go, (SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

# --- EJECUCIÓN ---
menu()  # Muestra el menú
game()  # Inicia el juego
pygame.quit()
sys.exit()
# ...existing code...