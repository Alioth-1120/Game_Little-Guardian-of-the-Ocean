import pygame
import sys
import os
import random
import math
import json
import uuid
import traceback
from datetime import datetime

pygame.init()


WIDTH = 800
HEIGHT = 600
window = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("海洋小卫士")

script_dir = os.path.dirname(os.path.abspath(__file__))

FPS = 60
GAME_TIME = 90  # 90秒，单位：秒
BASE_HOOK_SPEED = 15
HOOK_SPEED = BASE_HOOK_SPEED * 0.42  # 发射速度降低至原速度的60%（原70%基础上再降低至60%）
RETRIEVE_SPEED = HOOK_SPEED * 0.7  # 返回速度设置为发射速度的70%
SCORE_PER_BOTTLE = 500


SAVE_FILE_PATH = os.path.join(script_dir, "gamecache.sav")
HIGH_SCORE_FILE_PATH = os.path.join(script_dir, "highscore.sav")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)  # 深棕色，用于绳索
LIGHT_BLUE = (135, 206, 235)  # 浅蓝色，用于暂停界面按钮
LIGHTER_BLUE = (173, 216, 230)  # 更浅的蓝色，用于按钮悬停效果

MIN_RENDER_SCALE_MULTIPLIER = 1.6
SPAWN_DELAY_MS = 2000  # 回收后延迟 2 秒刷新
SPAWN_MOVE_SPEED_MIN = 1.0
SPAWN_MOVE_SPEED_MAX = 2.5
MIN_CENTER_DISTANCE = 60

def load_high_score():
    if not os.path.exists(HIGH_SCORE_FILE_PATH):
        return 0
    
    try:
        with open(HIGH_SCORE_FILE_PATH, "r") as f:
            data = json.load(f)
        return data.get("high_guardian_value", data.get("high_score", 0))
    except Exception as e:
        print(f"加载最高积分失败: {e}")
        return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE_PATH, "w") as f:
            json.dump({"high_guardian_value": score}, f)
        return True
    except Exception as e:
        print(f"保存最高积分失败: {e}")
        return False


def write_log(msg: str):
    try:
        log_path = os.path.join(script_dir, "save_load.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
    except Exception:
        pass

try:
    background_image = pygame.image.load(os.path.join(script_dir, "art_resources/game_backdround.png"))
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
    
    plastic_bottle_image = pygame.image.load(os.path.join(script_dir, "art_resources/plastic_bottle.png"))
    plastic_bottle_image = pygame.transform.scale(plastic_bottle_image, (40, 60))
    
    battery_image = pygame.image.load(os.path.join(script_dir, "art_resources/battery.png"))
    battery_image = pygame.transform.scale(battery_image, (35, 55))
    
    medicine_bottle_image = pygame.image.load(os.path.join(script_dir, "art_resources/medicine_bottle.png"))
    medicine_bottle_image = pygame.transform.scale(medicine_bottle_image, (30, 50))
    
    can_images = {}
    can_image_names = ["can_green.png", "can_red.png", "can_orange.png"]
    for can_name in can_image_names:
        can_img = pygame.image.load(os.path.join(script_dir, f"art_resources/{can_name}"))
        can_img = pygame.transform.scale(can_img, (25, 45))
        can_images[can_name] = can_img
    
    launcher_image = pygame.Surface((40, 60), pygame.SRCALPHA)
    launcher_image.fill((0, 0, 0, 0))  # 完全透明
    
    hook_image = pygame.Surface((20, 20))
    hook_image.fill((150, 150, 150))
except pygame.error as e:
    print(f"图像加载错误: {e}")
    pygame.quit()
    sys.exit()


try:
    glass_blue_image = pygame.image.load(os.path.join(script_dir, "art_resources/glass_blue.png"))
    glass_blue_image = pygame.transform.scale(glass_blue_image, (30, 30))
    glass_green_image = pygame.image.load(os.path.join(script_dir, "art_resources/glass_green.png"))
    glass_green_image = pygame.transform.scale(glass_green_image, (30, 30))
except Exception:
    glass_blue_image = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(glass_blue_image, (50, 150, 255), (15, 15), 15)
    glass_green_image = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(glass_green_image, (50, 200, 100), (15, 15), 15)

def _load_fish_image(name_variants, target_size=(40, 24)):
    for name in name_variants:
        path = os.path.join(script_dir, "art_resources", name)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                return pygame.transform.scale(img, target_size)
            except Exception:
                continue
    return None

fish_blue_left = _load_fish_image(["fish_blue_left.png", "fish_blue-left.png", "fish blue left.png"]) 
fish_orange_left = _load_fish_image(["fish_orange_left.png", "fish_orange-left.png", "fish orange left.png"]) 
fish_blue_right = _load_fish_image(["fish_blue_right.png", "fish_blue-right.png", "fish blue right.png", "fish_blue _right.png"]) 
fish_orange_right = _load_fish_image(["fish_orange_right.png", "fish_orange-right.png", "fish orange right.png"]) 

if fish_blue_left is None:
    fish_blue_left = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.polygon(fish_blue_left, (50, 150, 255), [(0,12),(30,4),(36,12),(30,20)])
if fish_orange_left is None:
    fish_orange_left = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.polygon(fish_orange_left, (255,160,60), [(0,12),(30,4),(36,12),(30,20)])
if fish_blue_right is None:
    fish_blue_right = pygame.transform.flip(fish_blue_left, True, False)
if fish_orange_right is None:
    fish_orange_right = pygame.transform.flip(fish_orange_left, True, False)

class OceanTrash:

    def __init__(self, image, score_value, width_scale=1.0, height_scale=1.0):
        self.original_image = image
        self.image = image
        self.score_value = score_value
        self.uid = str(uuid.uuid4())

        scale_x = random.uniform(0.9, 1.2) * MIN_RENDER_SCALE_MULTIPLIER * width_scale
        scale_y = random.uniform(0.9, 1.2) * MIN_RENDER_SCALE_MULTIPLIER * height_scale
        self.image = pygame.transform.scale(
            self.image,
            (int(self.image.get_width() * scale_x), int(self.image.get_height() * scale_y))
        )

        self.original_width = self.image.get_width()
        self.original_height = self.image.get_height()

        self.rect = self.image.get_rect()

        self.fx = float(self.rect.x)
        self.fy = float(self.rect.y)

        self.in_transit = False
        self.spawn_target = None
        self.spawn_speed = 0.0
        self.can_be_captured = True

        self.rect.x = random.randint(50, WIDTH - self.rect.width - 50)
        self.rect.y = random.randint(HEIGHT // 2, HEIGHT - self.rect.height - 50)

        self.initial_x = self.rect.x
        self.initial_y = self.rect.y

        self.speed_x = random.uniform(-1, 1)

        self.collected = False
        self.target_x = 0
        self.target_y = 0

        self.rotation_angle = random.randint(0, 360)

        self.sway_offset_x = 0
        self.sway_offset_y = 0

        self.max_sway_x = 10
        self.max_sway_y = 10

        self.sway_phase_x = random.uniform(0, 2 * math.pi)
        self.sway_phase_y = random.uniform(0, 2 * math.pi)
        self.sway_amplitude_x = random.uniform(3, self.max_sway_x)  # 晃动幅度3-10像素
        self.sway_amplitude_y = random.uniform(3, self.max_sway_y)
        self.sway_speed_x = random.uniform(0.008, 0.02)  # 原0.02-0.05的40%
        self.sway_speed_y = random.uniform(0.01, 0.024)  # 原0.025-0.06的40%

        self.collision_offset_x = 0  # 碰撞点相对于初始中心的偏移
        self.collision_offset_y = 0

    def get_collision_point(self):
        if self.collected:
            return (self.rect.centerx, self.rect.centery)
        elif getattr(self, 'in_transit', False):
            cx = getattr(self, 'fx', float(self.rect.x)) + self.rect.width / 2
            cy = getattr(self, 'fy', float(self.rect.y)) + self.rect.height / 2
            return (cx, cy)
        else:
            initial_center_x = self.initial_x + self.rect.width / 2
            initial_center_y = self.initial_y + self.rect.height / 2
            return (initial_center_x + self.sway_offset_x,
                    initial_center_y + self.sway_offset_y)

    def update(self):
        if not self.collected and not self.in_transit:
            current_time = pygame.time.get_ticks() / 1000.0  # 转换为秒

            new_sway_x = math.sin(current_time * self.sway_speed_x * 60 + self.sway_phase_x) * self.sway_amplitude_x
            new_sway_y = math.cos(current_time * self.sway_speed_y * 40 + self.sway_phase_y) * self.sway_amplitude_y

            self.sway_offset_x = max(-self.max_sway_x, min(self.max_sway_x, new_sway_x))
            self.sway_offset_y = max(-self.max_sway_y, min(self.max_sway_y, new_sway_y))

            self.collision_offset_x = self.sway_offset_x
            self.collision_offset_y = self.sway_offset_y
        elif self.in_transit:
            if self.spawn_target is not None:
                dx = self.spawn_target[0] - self.fx
                dy = self.spawn_target[1] - self.fy
                distance = math.hypot(dx, dy)
                if distance <= self.spawn_speed or distance == 0:
                    self.fx = float(self.spawn_target[0])
                    self.fy = float(self.spawn_target[1])
                    self.rect.x = int(round(self.fx))
                    self.rect.y = int(round(self.fy))
                    self.in_transit = False
                    self.spawn_target = None
                    self.spawn_speed = 0.0
                    self.can_be_captured = True
                    self.initial_x = self.rect.x
                    self.initial_y = self.rect.y
                else:
                    if distance != 0:
                        move_x = (dx / distance) * self.spawn_speed
                        move_y = (dy / distance) * self.spawn_speed
                    else:
                        move_x = move_y = 0.0
                    self.fx += move_x
                    self.fy += move_y
                    self.rect.x = int(round(self.fx))
                    self.rect.y = int(round(self.fy))
                    self.collision_offset_x = self.rect.centerx - (self.initial_x + self.rect.width / 2)
                    self.collision_offset_y = self.rect.centery - (self.initial_y + self.rect.height / 2)
        else:
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 5:
                move_speed = RETRIEVE_SPEED
                new_cx = self.rect.centerx + (dx / distance) * move_speed
                new_cy = self.rect.centery + (dy / distance) * move_speed
                self.rect.centerx = int(round(new_cx))
                self.rect.centery = int(round(new_cy))

            self.collision_offset_x = self.rect.centerx - (self.initial_x + self.rect.width / 2)
            self.collision_offset_y = self.rect.centery - (self.initial_y + self.rect.height / 2)

    def draw(self, surface):
        rotated_image = pygame.transform.rotate(self.image, self.rotation_angle)
        rotated_rect = rotated_image.get_rect(center=self.image.get_rect().center)

        if self.collected:
            draw_x = self.rect.x
            draw_y = self.rect.y
        elif getattr(self, 'in_transit', False):
            draw_x = getattr(self, 'fx', float(self.rect.x))
            draw_y = getattr(self, 'fy', float(self.rect.y))
        else:
            draw_x = self.initial_x + self.sway_offset_x
            draw_y = self.initial_y + self.sway_offset_y

        surface.blit(rotated_image, (draw_x, draw_y))

class PlasticBottle(OceanTrash):
    def __init__(self):
        super().__init__(plastic_bottle_image, SCORE_PER_BOTTLE)

class Battery(OceanTrash):
    def __init__(self):
        super().__init__(battery_image, 800, 0.9, 0.9)  # 800分奖励积分

class MedicineBottle(OceanTrash):
    def __init__(self):
        super().__init__(medicine_bottle_image, 750, 0.8, 0.85)  # 750分奖励积分

class Can(OceanTrash):
    def __init__(self):
        can_name = random.choice(can_image_names)
        super().__init__(can_images[can_name], 600, 0.7, 0.8)  # 600分奖励积分


class SeaGlass:

    DURATION_MS = 12000

    def __init__(self, image, score_value, start_pos, end_pos):
        self.image = image
        self.score_value = score_value
        self.rect = self.image.get_rect()
        self.uid = str(uuid.uuid4())
        self.start_x, self.start_y = start_pos
        self.end_x, self.end_y = end_pos
        self.fx = float(self.start_x)
        self.fy = float(self.start_y)
        self.rect.x = int(round(self.fx))
        self.rect.y = int(round(self.fy))
        self.spawn_time = pygame.time.get_ticks()
        self.collected = False
        self.can_be_captured = True
        mid_x = (self.start_x + self.end_x) / 2
        mid_y = (self.start_y + self.end_y) / 2
        jitter_x = random.uniform(-WIDTH * 0.15, WIDTH * 0.15)
        jitter_y = random.uniform(-HEIGHT * 0.08, HEIGHT * 0.08)
        self.control_x = mid_x + jitter_x
        self.control_y = mid_y + jitter_y
        self.target_x = 0
        self.target_y = 0
        self.alive = True

    def get_collision_point(self):
        return (self.fx + self.rect.width / 2, self.fy + self.rect.height / 2)

    def update(self):
        now = pygame.time.get_ticks()
        if self.collected:
            dx = self.target_x - (self.fx + self.rect.width / 2)
            dy = self.target_y - (self.fy + self.rect.height / 2)
            dist = math.hypot(dx, dy)
            if dist > 1:
                move = RETRIEVE_SPEED
                self.fx += (dx / dist) * move
                self.fy += (dy / dist) * move
                self.rect.x = int(round(self.fx))
                self.rect.y = int(round(self.fy))
            else:
                self.alive = False
        else:
            t = (now - self.spawn_time) / float(self.DURATION_MS)
            if t >= 1.0:
                self.alive = False
                return

            u = 1.0 - t
            bx = u * u * self.start_x + 2 * u * t * self.control_x + t * t * self.end_x
            by = u * u * self.start_y + 2 * u * t * self.control_y + t * t * self.end_y
            self.fx = float(bx)
            self.fy = float(by)
            self.rect.x = int(round(self.fx))
            self.rect.y = int(round(self.fy))

    def draw(self, surface):
        surface.blit(self.image, (self.fx, self.fy))


class Fish:
    def __init__(self, image, direction: str, speed_px_per_frame: float):
        self.image = image
        self.rect = self.image.get_rect()
        self.uid = str(uuid.uuid4())
        self.direction = direction  # 'left' or 'right'
        self.fx = 0.0
        self.fy = 0.0
        self.speed = speed_px_per_frame
        self.collected = False
        self.can_be_captured = True
        self.alive = True
        self.target_x = 0
        self.target_y = 0

    def get_collision_point(self):
        return (self.fx + self.rect.width / 2, self.fy + self.rect.height / 2)

    def update(self):
        if self.collected:
            dx = self.target_x - (self.fx + self.rect.width / 2)
            dy = self.target_y - (self.fy + self.rect.height / 2)
            dist = math.hypot(dx, dy)
            if dist > 1:
                move = RETRIEVE_SPEED
                self.fx += (dx / dist) * move
                self.fy += (dy / dist) * move
                self.rect.x = int(round(self.fx))
                self.rect.y = int(round(self.fy))
            else:
                self.alive = False
        else:
            if self.direction == 'left':
                self.fx -= self.speed
            else:
                self.fx += self.speed
            self.rect.x = int(round(self.fx))
            self.rect.y = int(round(self.fy))
            if self.fx + self.rect.width < -50 or self.fx > WIDTH + 50:
                self.alive = False

    def draw(self, surface):
        surface.blit(self.image, (self.fx, self.fy))

class Hook:
    def __init__(self, launcher_x, launcher_y):
        self.launcher_x = launcher_x
        self.launcher_y = launcher_y
        self.x = launcher_x
        self.y = launcher_y
        self.angle = 0
        self.length = 0
        self.max_length = 0
        self.speed = HOOK_SPEED
        self.state = "ready"  # ready, launching, retrieving, returning
        self.target = None
        self.stuck_counter = 0  # 静止帧计数
        self.last_position = (launcher_x, launcher_y)
        self.max_stuck_frames = 60  # 最大静止帧数（约1秒）
    
    def launch(self, angle):
        if self.state == "ready":
            self.angle = angle
            self.state = "launching"
            self.x = self.launcher_x
            self.y = self.launcher_y
            self.length = 0
            self.stuck_counter = 0
            self.last_position = (self.x, self.y)
    
    def update(self):
        if self.state == "launching":
            self.x += math.cos(math.radians(self.angle)) * self.speed
            self.y += math.sin(math.radians(self.angle)) * self.speed
            self.length += self.speed

            current_pos = (self.x, self.y)
            if current_pos == self.last_position:
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
                self.last_position = current_pos

            if self.stuck_counter > self.max_stuck_frames:
                self.state = "returning"
                self.stuck_counter = 0

            if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
                self.state = "returning"
        
        elif self.state == "returning":
            self.x -= math.cos(math.radians(self.angle)) * self.speed
            self.y -= math.sin(math.radians(self.angle)) * self.speed
            self.length -= self.speed

            current_pos = (self.x, self.y)
            if current_pos == self.last_position:
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
                self.last_position = current_pos

            if self.stuck_counter > self.max_stuck_frames:
                self.x = self.launcher_x
                self.y = self.launcher_y
                self.length = 0
                self.state = "ready"
                self.stuck_counter = 0
                return False

            dx = self.x - self.launcher_x
            dy = self.y - self.launcher_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < self.speed:
                self.x = self.launcher_x
                self.y = self.launcher_y
                self.length = 0
                self.state = "ready"
                self.stuck_counter = 0
        
        elif self.state == "retrieving":
            if self.target:
                try:
                    collision_point = self.target.get_collision_point()
                    self.x = collision_point[0]
                    self.y = collision_point[1]

                    dx = self.x - self.launcher_x
                    dy = self.y - self.launcher_y
                    self.length = math.sqrt(dx * dx + dy * dy)

                    if self.length < 10:
                        return True  # 回收完成
                except (AttributeError, TypeError, ValueError):
                    self.target = None
                    self.state = "returning"
                    self.stuck_counter = 0
            else:
                self.state = "returning"
                self.stuck_counter = 0
        
        return False
    
    def check_collision(self, items):
        if self.state == "launching":
            for obj in items:
                if getattr(obj, 'collected', False):
                    continue
                if not getattr(obj, 'can_be_captured', True):
                    continue

                try:
                    collision_point = obj.get_collision_point()
                except Exception:
                    continue

                dx = self.x - collision_point[0]
                dy = self.y - collision_point[1]
                distance = math.sqrt(dx * dx + dy * dy)

                avg_size = (getattr(obj, 'rect', pygame.Rect(0,0,30,30)).width + getattr(obj, 'rect', pygame.Rect(0,0,30,30)).height) / 2
                radius = max(24, int(round(avg_size * 0.5)))
                if distance < radius:
                    self.state = "retrieving"
                    try:
                        obj.collected = True
                        obj.target_x = self.launcher_x
                        obj.target_y = self.launcher_y
                    except Exception:
                        pass
                    self.target = obj
                    return obj

        return None
    
    def draw(self, surface):
        if self.state != "ready":
            if self.state == "retrieving" and self.target:
                num_segments = 5  # 分段数量，越多越平滑
                
                start_x, start_y = self.launcher_x, self.launcher_y
                end_x, end_y = self.x, self.y
                
                mid_x = start_x + (end_x - start_x) * 0.5
                mid_y = start_y + (end_y - start_y) * 0.5
                
                dx = end_x - start_x
                dy = end_y - start_y
                sag_factor = 0.05  # 下垂程度系数
                sag = math.sqrt(dx * dx + dy * dy) * sag_factor
                
                perp_length = math.sqrt(dx * dx + dy * dy)
                if perp_length > 0:
                    perp_x = -dy / perp_length
                    perp_y = dx / perp_length
                else:
                    perp_x, perp_y = 0, 1
                
                sag_mid_x = mid_x + perp_x * sag
                sag_mid_y = mid_y + perp_y * sag
                
                points = []
                for i in range(num_segments + 1):
                    t = i / num_segments
                    
                    if t < 0.5:
                        sub_t = t * 2
                        x = (1 - sub_t) ** 2 * start_x + 2 * (1 - sub_t) * sub_t * sag_mid_x + sub_t ** 2 * mid_x
                        y = (1 - sub_t) ** 2 * start_y + 2 * (1 - sub_t) * sub_t * sag_mid_y + sub_t ** 2 * mid_y
                    else:
                        sub_t = (t - 0.5) * 2
                        x = (1 - sub_t) ** 2 * mid_x + 2 * (1 - sub_t) * sub_t * sag_mid_x + sub_t ** 2 * end_x
                        y = (1 - sub_t) ** 2 * mid_y + 2 * (1 - sub_t) * sub_t * sag_mid_y + sub_t ** 2 * end_y
                    
                    points.append((x, y))
                
                for i in range(len(points) - 1):
                    pygame.draw.line(surface, BROWN, points[i], points[i+1], 3)
            else:
                pygame.draw.line(surface, BROWN, (self.launcher_x, self.launcher_y), (self.x, self.y), 3)
            
            surface.blit(hook_image, (self.x - 10, self.y - 10))

class Game:
    def __init__(self):
        self.score = 0
        self.time_left = GAME_TIME
        self.start_time = None
        self.running = True
        self.game_over = False
        self.paused = False
        
        self.launcher_x = WIDTH // 2
        self.launcher_y = HEIGHT // 4
        self.launcher_angle = 90.0  # 初始角度设为90°（正右方），精确到0.1°
        self.launcher_rotation_speed = 1.4  # 降低旋转速度至原速度的70%，精确控制
        self.rotation_direction = 1  # 1为顺时针，-1为逆时针
        self.launcher_visible = True  # 发射装置可见性
        
        self.hook = Hook(self.launcher_x, self.launcher_y)
        
        self.bottles = []
        self.startup_in_progress = True
        initial_classes = [PlasticBottle, Battery, MedicineBottle, Can]
        for _ in range(8 - len(initial_classes)):
            initial_classes.append(random.choice(initial_classes))
        random.shuffle(initial_classes)
        for cls in initial_classes:
            bottle = cls()
            target_x = random.randint(50, WIDTH - bottle.rect.width - 50)
            target_y = random.randint(HEIGHT // 2, HEIGHT - bottle.rect.height - 50)
            side = random.choice(['left', 'right'])
            if side == 'left':
                start_x = -bottle.rect.width - 10
            else:
                start_x = WIDTH + 10
            start_y = random.randint(HEIGHT // 2, HEIGHT - bottle.rect.height - 50)
            bottle.rect.x = start_x
            bottle.rect.y = start_y
            bottle.fx = float(start_x)
            bottle.fy = float(start_y)
            bottle.in_transit = True
            bottle.spawn_target = (target_x, target_y)
            distance = math.hypot(target_x - start_x, target_y - start_y)
            duration_ms = random.randint(900, 1600)
            frames = max(1, duration_ms * FPS / 1000.0)
            bottle.spawn_speed = distance / frames
            bottle.can_be_captured = False
            bottle.initial_x = target_x
            bottle.initial_y = target_y
            self.bottles.append(bottle)
        self.pending_spawns = []  # 列表元素: {'when': millis, 'class': TrashClass}
        self.sea_glasses = []
        self.seaglass_triggers = {75: False, 45: False, 15: False}
        self.fishes = []
        self.last_fish_check = None
        self.trash_classes = [PlasticBottle, Battery, MedicineBottle, Can]
        
        self.font = pygame.font.SysFont("Microsoft YaHei", 24)
        self.large_font = pygame.font.SysFont("Microsoft YaHei", 48)
        
        self.pause_button_rect = pygame.Rect(10, 10, 80, 80)  # 80x80像素的暂停按钮
        
        self.resume_button_rect = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2, 150, 60)
        self.quit_button_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2, 150, 60)
        
        self.restart_button_rect = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 50, 150, 60)
        self.return_home_button_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 50, 150, 60)
        self.just_loaded = False
    
    def save_game(self):
        write_log("开始保存游戏")
        trash_type_map = {
            PlasticBottle: "plastic_bottle",
            Battery: "battery",
            MedicineBottle: "medicine_bottle",
            Can: "can"
        }
        
        pending_removal_bottle_uid = ""
        pending_removal_guardian_value = 0
        
        for bottle in self.bottles:
            if bottle.collected:
                dx = bottle.rect.centerx - self.launcher_x
                dy = bottle.rect.centery - self.launcher_y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < 15:  # 即将到达发射器
                    pending_removal_bottle_uid = getattr(bottle, 'uid', '')
                    pending_removal_guardian_value = bottle.score_value
                    break
                    break
        
        game_state = {
            "version": "1.2",  # 版本号用于数据兼容性检查
            "timestamp": pygame.time.get_ticks(),  # 保存时间戳
            "guardian_value": self.score,
            "time_left": self.time_left,
            "launcher_x": self.launcher_x,
            "launcher_y": self.launcher_y,
            "launcher_angle": self.launcher_angle,
            "launcher_visible": self.launcher_visible,
            "rotation_direction": self.rotation_direction,
                "bottles": [
                {
                    "type": trash_type_map.get(type(bottle), "plastic_bottle"),
                    "x": bottle.rect.x,
                    "y": bottle.rect.y,
                    "initial_x": bottle.initial_x,
                    "initial_y": bottle.initial_y,
                    "speed_x": bottle.speed_x,
                    "speed_y": getattr(bottle, 'speed_y', 0),
                    "collected": bottle.collected,
                    "target_x": getattr(bottle, 'target_x', 0),
                    "target_y": getattr(bottle, 'target_y', 0),
                    "uid": getattr(bottle, 'uid', ''),
                    "sway_offset_x": bottle.sway_offset_x,
                    "sway_offset_y": bottle.sway_offset_y,
                    "sway_phase_x": bottle.sway_phase_x,
                    "sway_phase_y": bottle.sway_phase_y,
                    "sway_amplitude_x": bottle.sway_amplitude_x,
                    "sway_amplitude_y": bottle.sway_amplitude_y,
                    "sway_speed_x": bottle.sway_speed_x,
                    "sway_speed_y": bottle.sway_speed_y,
                    "rotation_angle": bottle.rotation_angle
                }
                for bottle in self.bottles
            ],
            "sea_glasses": [
                {
                    "score_value": sg.score_value,
                    "start_x": sg.start_x,
                    "start_y": sg.start_y,
                    "end_x": sg.end_x,
                    "end_y": sg.end_y,
                    "fx": sg.fx,
                    "fy": sg.fy,
                    "img_w": getattr(sg, 'rect').width if getattr(sg, 'rect', None) is not None else getattr(sg, 'image').get_width(),
                    "img_h": getattr(sg, 'rect').height if getattr(sg, 'rect', None) is not None else getattr(sg, 'image').get_height(),
                    "elapsed_ms": (pygame.time.get_ticks() - getattr(sg, 'spawn_time', pygame.time.get_ticks())),
                    "collected": getattr(sg, 'collected', False),
                    "target_x": getattr(sg, 'target_x', 0),
                    "target_y": getattr(sg, 'target_y', 0),
                    "alive": getattr(sg, 'alive', True),
                    "uid": getattr(sg, 'uid', '')
                }
                for sg in self.sea_glasses
            ],
            "fishes": [
                {
                    "direction": getattr(f, 'direction', 'left'),
                    "fx": getattr(f, 'fx', f.rect.x),
                    "fy": getattr(f, 'fy', f.rect.y),
                    "speed": getattr(f, 'speed', 0),
                    "collected": getattr(f, 'collected', False),
                    "target_x": getattr(f, 'target_x', 0),
                    "target_y": getattr(f, 'target_y', 0),
                    "alive": getattr(f, 'alive', True),
                    "uid": getattr(f, 'uid', ''),
                    "img_w": getattr(f, 'rect').width if getattr(f, 'rect', None) is not None else getattr(f, 'image').get_width(),
                    "img_h": getattr(f, 'rect').height if getattr(f, 'rect', None) is not None else getattr(f, 'image').get_height()
                }
                for f in self.fishes
            ],
            "hook": {
                "x": self.hook.x,
                "y": self.hook.y,
                "state": self.hook.state,
                "angle": self.hook.angle,
                "length": self.hook.length,
                "target_uid": getattr(self.hook.target, 'uid', ''),  # 使用稳定 UID 关联目标
                "pending_removal_bottle_uid": pending_removal_bottle_uid,
                "pending_removal_guardian_value": pending_removal_guardian_value
            }
        }
        
        try:
            with open(SAVE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(game_state, f, indent=4, ensure_ascii=False)
            write_log("保存游戏成功")
            return True
        except Exception as e:
            err = f"保存游戏失败: {e}"
            print(err)
            write_log(err + "\n" + traceback.format_exc())
            return False
    
    def spawn_bottles(self, count):
        for _ in range(count):
            attempts = 0
            max_attempts = 10
            bottle = None
            
            while attempts < max_attempts:
                trash_class = self.choose_spawn_class()
                bottle = trash_class()
                overlap = False
                
                for existing_bottle in self.bottles:
                    if bottle.rect.colliderect(existing_bottle.rect):
                        overlap = True
                        break
                
                if not overlap:
                    break
                
                attempts += 1
            
            if bottle and not overlap:
                try_x, try_y = self.choose_spawn_point(bottle.rect.width, bottle.rect.height)
                bottle.rect.x = try_x
                bottle.rect.y = try_y
                bottle.fx = float(try_x)
                bottle.fy = float(try_y)
                self.bottles.append(bottle)

    def spawn_seaglass(self):
        if random.random() < 0.5:
            base_img = glass_blue_image
            score = 1000
        else:
            base_img = glass_green_image
            score = 1200
        scale = random.uniform(1.7, 3.0)
        sw = max(1, int(round(base_img.get_width() * scale)))
        sh = max(1, int(round(base_img.get_height() * scale)))
        img = pygame.transform.scale(base_img, (sw, sh))

        start_side = random.choice(['left', 'right', 'bottom'])
        possible_ends = [s for s in ['left', 'right', 'bottom'] if s != start_side]
        end_side = random.choice(possible_ends)

        def safe_rand_in(a, b, allowed_min, allowed_max):
            lo = max(a, allowed_min)
            hi = min(b, allowed_max)
            if lo <= hi:
                return random.randint(lo, hi)
            if allowed_min > allowed_max:
                return allowed_min
            return (allowed_min + allowed_max) // 2

        img_w = img.get_width()
        img_h = img.get_height()
        allowed_x_min = 50
        allowed_x_max = max(50, WIDTH - img_w - 50)
        allowed_y_min = HEIGHT // 2
        allowed_y_max = max(allowed_y_min, HEIGHT - img_h - 30)

        if start_side == 'left':
            sx = -img_w - 10
            sy = safe_rand_in(HEIGHT // 2, HEIGHT - img_h - 30, allowed_y_min, allowed_y_max)
        elif start_side == 'right':
            sx = WIDTH + 10
            sy = safe_rand_in(HEIGHT // 2, HEIGHT - img_h - 30, allowed_y_min, allowed_y_max)
        else:  # bottom
            sy = HEIGHT + 10
            sx = safe_rand_in(50, WIDTH - img_w - 50, allowed_x_min, allowed_x_max)

        if end_side == 'left':
            ex = safe_rand_in(50, 120, allowed_x_min, allowed_x_max)
            ey = safe_rand_in(HEIGHT // 2, HEIGHT - img_h - 30, allowed_y_min, allowed_y_max)
        elif end_side == 'right':
            ex = safe_rand_in(WIDTH - 120, WIDTH - img_w - 50, allowed_x_min, allowed_x_max)
            ey = safe_rand_in(HEIGHT // 2, HEIGHT - img_h - 30, allowed_y_min, allowed_y_max)
        else:  # bottom
            ey = safe_rand_in(HEIGHT - 90, HEIGHT - img_h - 10, allowed_y_min, allowed_y_max)
            ex = safe_rand_in(50, WIDTH - img_w - 50, allowed_x_min, allowed_x_max)

        sg = SeaGlass(img, score, (sx, sy), (ex, ey))
        self.sea_glasses.append(sg)
        write_log(f"生成海玻璃: start={start_side} end={end_side} 蔚蓝守护值={score}")

    def spawn_fish(self):
        direction = random.choice(['left', 'right'])
        if direction == 'left':
            base_img = random.choice([fish_blue_left, fish_orange_left])
        else:
            base_img = random.choice([fish_blue_right, fish_orange_right])

        if base_img is None:
            base_img = pygame.Surface((40, 24), pygame.SRCALPHA)
            pygame.draw.polygon(base_img, (150, 150, 200), [(0,12),(30,4),(36,12),(30,20)])

        scale = random.uniform(2.5, 4.5)
        sw = max(1, int(round(base_img.get_width() * scale)))
        sh = max(1, int(round(base_img.get_height() * scale)))
        img = pygame.transform.scale(base_img, (sw, sh))

        img_h = img.get_height()
        img_w = img.get_width()
        y = random.randint(HEIGHT // 2, max(HEIGHT // 2, HEIGHT - img_h - 30))

        if direction == 'left':
            sx = WIDTH + 10
            ex = -img_w - 10
        else:
            sx = -img_w - 10
            ex = WIDTH + 10

        distance = abs(ex - sx)
        duration_ms = random.randint(6000, 12000)
        frames = max(1, duration_ms * FPS / 1000.0)
        base_speed = distance / frames
        speed_px_per_frame = base_speed * random.uniform(0.35, 0.65)

        fish = Fish(img, direction, speed_px_per_frame)
        fish.fx = float(sx)
        fish.fy = float(y)
        fish.rect.x = int(round(fish.fx))
        fish.rect.y = int(round(fish.fy))
        self.fishes.append(fish)
        write_log(f"生成鱼: dir={direction} y={y} speed={speed_px_per_frame:.2f}")
    
    def update(self):

        if self.game_over or self.paused:
            return
        
        self.launcher_angle = round(self.launcher_angle + self.launcher_rotation_speed * self.rotation_direction, 1)
        if self.launcher_angle >= 150.0:
            self.launcher_angle = 150.0
            self.rotation_direction = -1
            print("已达到右边界 (150°)")
        elif self.launcher_angle <= 30.0:
            self.launcher_angle = 30.0
            self.rotation_direction = 1
            print("已达到左边界 (30°)")
        
        if self.hook.state != "ready" and self.launcher_visible:
            self.launcher_visible = False
        elif self.hook.state == "ready" and not self.launcher_visible:
            self.launcher_visible = True
        
        retrieved = self.hook.update()
        if retrieved and self.hook.target:
            target_bottle = self.hook.target
            if target_bottle in self.bottles:
                self.score += target_bottle.score_value
                self.bottles.remove(target_bottle)
            elif target_bottle in self.sea_glasses:
                self.score += target_bottle.score_value
                try:
                    self.sea_glasses.remove(target_bottle)
                except ValueError:
                    pass
            elif target_bottle in self.fishes:
                penalty = 750
                self.score = max(0, self.score - penalty)
                try:
                    self.fishes.remove(target_bottle)
                except ValueError:
                    pass
            
            self.hook.target = None
            self.hook.state = "ready"
            
            if not self.just_loaded:
                cls = self.choose_spawn_class()
                spawn_time = pygame.time.get_ticks() + SPAWN_DELAY_MS
                self.pending_spawns.append({'when': spawn_time, 'class': cls})
        
        for sg in list(self.sea_glasses):
            sg.update()
        for f in list(self.fishes):
            f.update()

        collided_obj = self.hook.check_collision(self.bottles + self.sea_glasses + self.fishes)

        now = pygame.time.get_ticks()
        if self.pending_spawns:
            to_add = []
            remaining = []
            for entry in self.pending_spawns:
                if now >= entry['when']:
                    to_add.append(entry['class'])
                else:
                    remaining.append(entry)
            self.pending_spawns = remaining
            for cls in to_add:
                bottle = cls()
                target_x, target_y = self.choose_spawn_point(bottle.rect.width, bottle.rect.height)
                side = random.choice(['left', 'right'])
                if side == 'left':
                    start_x = -bottle.rect.width - 10
                else:
                    start_x = WIDTH + 10
                start_y = random.randint(HEIGHT // 2, HEIGHT - bottle.rect.height - 50)
                bottle.rect.x = start_x
                bottle.rect.y = start_y
                bottle.fx = float(start_x)
                bottle.fy = float(start_y)
                bottle.in_transit = True
                bottle.spawn_target = (target_x, target_y)
                distance = math.hypot(target_x - start_x, target_y - start_y)
                duration_ms = random.randint(900, 1600)
                frames = max(1, duration_ms * FPS / 1000.0)
                bottle.spawn_speed = distance / frames
                bottle.can_be_captured = False
                bottle.initial_x = target_x
                bottle.initial_y = target_y
                self.bottles.append(bottle)
        
        if getattr(self, 'startup_in_progress', False):
            all_arrived = all(not getattr(b, 'in_transit', False) for b in self.bottles)
            if all_arrived:
                self.start_time = pygame.time.get_ticks()
                self.startup_in_progress = False
                write_log("启动动画完成，开始倒计时")
                for _ in range(2):
                    self.spawn_fish()
                self.last_fish_check = pygame.time.get_ticks()

        for bottle in self.bottles:
            bottle.update()

        if getattr(self, 'just_loaded', False):
            any_collected = any(getattr(b, 'collected', False) for b in self.bottles)
            if not any_collected and self.hook.state != 'retrieving':
                self.just_loaded = False
                write_log("已解除加载保护：允许正常刷新")

        current_time = pygame.time.get_ticks()
        if self.start_time is None:
            elapsed_time = 0
        else:
            elapsed_time = (current_time - self.start_time) // 1000
        self.time_left = max(0, GAME_TIME - elapsed_time)

        remaining_sea = []
        for sg in list(self.sea_glasses):
            if getattr(sg, 'alive', True):
                remaining_sea.append(sg)
            else:
                pass
        self.sea_glasses = remaining_sea

        remaining_fish = []
        for f in list(self.fishes):
            if getattr(f, 'alive', True):
                remaining_fish.append(f)
            else:
                pass
        self.fishes = remaining_fish

        if not getattr(self, 'startup_in_progress', False):
            if len(self.fishes) == 0:
                self.spawn_fish()

        if not getattr(self, 'startup_in_progress', False):
            for thr in (75, 45, 15):
                if self.time_left <= thr and not self.seaglass_triggers.get(thr, False):
                    self.spawn_seaglass()
                    self.seaglass_triggers[thr] = True

            now_ms = pygame.time.get_ticks()
            if self.last_fish_check is None:
                self.last_fish_check = now_ms
            if now_ms - self.last_fish_check >= 20000:
                if len(self.fishes) <= 1:
                    self.spawn_fish()
                self.last_fish_check = now_ms

        if self.time_left <= 0 and not self.game_over:
            self.game_over = True
            current_high_score = load_high_score()
            if self.score > current_high_score:
                save_high_score(self.score)

    def choose_spawn_class(self):
        present = set(type(b) for b in self.bottles)
        missing = [cls for cls in self.trash_classes if cls not in present]
        if missing:
            return random.choice(missing)
        return random.choice(self.trash_classes)

    def choose_spawn_point(self, item_width: int, item_height: int) -> tuple[int, int]:
        attempts = 50
        last_candidate = (random.randint(50, max(50, WIDTH - item_width - 50)),
                          random.randint(HEIGHT // 2, max(HEIGHT // 2, HEIGHT - item_height - 50)))
        for _ in range(attempts):
            cx = random.randint(50, max(50, WIDTH - item_width - 50))
            cy = random.randint(HEIGHT // 2, max(HEIGHT // 2, HEIGHT - item_height - 50))
            candidate_center = (cx + item_width / 2, cy + item_height / 2)

            ok = True
            for existing in self.bottles:
                if getattr(existing, 'in_transit', False) and getattr(existing, 'spawn_target', None) is not None:
                    ex_cx = existing.spawn_target[0] + existing.rect.width / 2
                    ex_cy = existing.spawn_target[1] + existing.rect.height / 2
                else:
                    ex_cx = existing.rect.x + existing.rect.width / 2
                    ex_cy = existing.rect.y + existing.rect.height / 2
                dist = math.hypot(candidate_center[0] - ex_cx, candidate_center[1] - ex_cy)
                if dist < MIN_CENTER_DISTANCE:
                    ok = False
                    break

            if ok:
                return (cx, cy)
            last_candidate = (cx, cy)

        return last_candidate
    
    def load_game(self):
        write_log("开始加载存档")
        if not os.path.exists(SAVE_FILE_PATH):
            return False
        
        trash_type_map = {
            "plastic_bottle": PlasticBottle,
            "battery": Battery,
            "medicine_bottle": MedicineBottle,
            "can": Can
        }
        
        try:
            with open(SAVE_FILE_PATH, "r", encoding="utf-8") as f:
                game_state = json.load(f)
            
            required_fields = ["version", "time_left", "bottles", "hook"]
            for field in required_fields:
                if field not in game_state:
                    print(f"存档数据不完整：缺少必要字段 {field}")
                    return False
            
            version = game_state.get("version", "1.0")
            if version != "1.2":
                print(f"存档版本不兼容：当前版本 {version}，期望版本 1.2")
            
            self.score = game_state.get("guardian_value", game_state.get("score", 0))
            self.time_left = game_state["time_left"]
            self.launcher_x = game_state["launcher_x"]
            self.launcher_y = game_state["launcher_y"]
            self.launcher_angle = game_state["launcher_angle"]
            self.launcher_visible = game_state["launcher_visible"]
            self.rotation_direction = game_state.get("rotation_direction", 1)
            
            self.bottles.clear()
            
            hook_data = game_state["hook"]
            self.hook.x = hook_data["x"]
            self.hook.y = hook_data["y"]
            self.hook.state = hook_data["state"]
            self.hook.angle = hook_data["angle"]
            self.hook.length = hook_data["length"] if "length" in hook_data else 0
            
            pending_removal_bottle_uid = hook_data.get("pending_removal_bottle_uid", "")
            if not pending_removal_bottle_uid:
                old_id = hook_data.get("pending_removal_bottle_id", -1)
                pending_removal_bottle_uid = ""
            pending_removal_guardian_value = hook_data.get("pending_removal_guardian_value",
                                                          hook_data.get("pending_removal_score", 0))

            need_migrate = False
            
            for bottle_data in game_state["bottles"]:
                trash_type = bottle_data.get("type", "plastic_bottle")
                trash_class = trash_type_map.get(trash_type, PlasticBottle)
                bottle = trash_class()
                bottle.rect.x = bottle_data["x"]
                bottle.rect.y = bottle_data["y"]
                bottle.speed_x = bottle_data["speed_x"]
                bottle.uid = bottle_data.get("uid", getattr(bottle, 'uid', ''))
                
                if "collected" in bottle_data:
                    bottle.collected = bottle_data["collected"]
                    if "target_x" in bottle_data and "target_y" in bottle_data:
                        bottle.target_x = bottle_data["target_x"]
                        bottle.target_y = bottle_data["target_y"]
                    if bottle.collected and not (hasattr(bottle, 'target_x') and hasattr(bottle, 'target_y')):
                        bottle.target_x = self.launcher_x
                        bottle.target_y = self.launcher_y
                
                bottle.initial_x = bottle_data.get("initial_x", bottle.rect.x)
                bottle.initial_y = bottle_data.get("initial_y", bottle.rect.y)
                
                if bottle.collected:
                    bottle.target_x = bottle_data.get("target_x", getattr(bottle, 'target_x', self.launcher_x))
                    bottle.target_y = bottle_data.get("target_y", getattr(bottle, 'target_y', self.launcher_y))
                
                if not bottle_data.get("uid"):
                    need_migrate = True

                bottle.sway_offset_x = bottle_data.get("sway_offset_x", 0)
                bottle.sway_offset_y = bottle_data.get("sway_offset_y", 0)
                bottle.sway_phase_x = bottle_data.get("sway_phase_x", random.uniform(0, 2 * math.pi))
                bottle.sway_phase_y = bottle_data.get("sway_phase_y", random.uniform(0, 2 * math.pi))
                bottle.sway_amplitude_x = bottle_data.get("sway_amplitude_x", random.uniform(3, 10))
                bottle.sway_amplitude_y = bottle_data.get("sway_amplitude_y", random.uniform(3, 10))
                bottle.sway_speed_x = bottle_data.get("sway_speed_x", random.uniform(0.008, 0.02))
                bottle.sway_speed_y = bottle_data.get("sway_speed_y", random.uniform(0.01, 0.024))
                bottle.rotation_angle = bottle_data.get("rotation_angle", 0)
                bottle_uid = getattr(bottle, 'uid', '')
                if bottle_uid == pending_removal_bottle_uid and pending_removal_bottle_uid != "":
                    self.score += pending_removal_guardian_value
                    continue

                self.bottles.append(bottle)
            
            self.sea_glasses = []
            for sg_data in game_state.get("sea_glasses", []):
                try:
                    score = sg_data.get("score_value", 1000)
                    base_img = glass_green_image if score >= 1200 else glass_blue_image
                    if base_img is None:
                        img = pygame.Surface((32, 32), pygame.SRCALPHA)
                        pygame.draw.circle(img, (200, 200, 255), (16, 16), 16)
                    else:
                        img_w = int(sg_data.get("img_w", base_img.get_width()))
                        img_h = int(sg_data.get("img_h", base_img.get_height()))
                        try:
                            img = pygame.transform.scale(base_img, (max(1, img_w), max(1, img_h)))
                        except Exception:
                            img = base_img.copy()

                    sg = SeaGlass(img, score, (sg_data.get("start_x", 0), sg_data.get("start_y", 0)),
                                  (sg_data.get("end_x", 0), sg_data.get("end_y", 0)))
                    sg.fx = float(sg_data.get("fx", sg.start_x))
                    sg.fy = float(sg_data.get("fy", sg.start_y))
                    sg.rect.x = int(round(sg.fx))
                    sg.rect.y = int(round(sg.fy))
                    elapsed = sg_data.get("elapsed_ms", 0)
                    sg.spawn_time = pygame.time.get_ticks() - int(elapsed)
                    sg.collected = sg_data.get("collected", False)
                    sg.target_x = sg_data.get("target_x", 0)
                    sg.target_y = sg_data.get("target_y", 0)
                    sg.alive = sg_data.get("alive", True)
                    sg.uid = sg_data.get("uid", getattr(sg, 'uid', ''))
                    self.sea_glasses.append(sg)
                except Exception:
                    write_log("恢复海玻璃时出错:\n" + traceback.format_exc())

            self.fishes = []
            for f_data in game_state.get("fishes", []):
                try:
                    direction = f_data.get("direction", "left")
                    if direction == 'left':
                        base_img = fish_blue_left or fish_orange_left
                    else:
                        base_img = fish_blue_right or fish_orange_right

                    if base_img is None:
                        base_img = pygame.Surface((40, 24), pygame.SRCALPHA)
                        pygame.draw.polygon(base_img, (150, 150, 200), [(0, 12), (30, 4), (36, 12), (30, 20)])

                    img_w = int(f_data.get("img_w", base_img.get_width()))
                    img_h = int(f_data.get("img_h", base_img.get_height()))
                    try:
                        img = pygame.transform.scale(base_img, (max(1, img_w), max(1, img_h)))
                    except Exception:
                        img = base_img.copy()
                    fish = Fish(img, direction, f_data.get("speed", 0))
                    fish.fx = float(f_data.get("fx", fish.fx))
                    fish.fy = float(f_data.get("fy", fish.fy))
                    fish.rect.x = int(round(fish.fx))
                    fish.rect.y = int(round(fish.fy))
                    fish.collected = f_data.get("collected", False)
                    fish.target_x = f_data.get("target_x", 0)
                    fish.target_y = f_data.get("target_y", 0)
                    fish.alive = f_data.get("alive", True)
                    fish.uid = f_data.get("uid", getattr(fish, 'uid', ''))
                    self.fishes.append(fish)
                except Exception:
                    write_log("恢复鱼类时出错:\n" + traceback.format_exc())

            target_uid = hook_data.get("target_uid", "")
            target_id = hook_data.get("target_id", -1)
            target_index = hook_data.get("target_index", -1)

            if target_uid:
                for bottle in self.bottles:
                    if getattr(bottle, 'uid', '') == target_uid:
                        self.hook.target = bottle
                        break
                else:
                    warn = f"警告：无法找到钩索目标 (UID: {target_uid})，重置钩索状态"
                    print(warn)
                    write_log(warn)
                    self.hook.state = "ready"
                    self.hook.target = None
            elif target_id != -1:
                for bottle in self.bottles:
                    if id(bottle) == target_id:
                        self.hook.target = bottle
                        break
                else:
                    warn = f"警告：无法找到钩索目标 (ID: {target_id})，重置钩索状态"
                    print(warn)
                    write_log(warn)
                    self.hook.state = "ready"
                    self.hook.target = None
            elif target_index != -1 and 0 <= target_index < len(self.bottles):
                self.hook.target = self.bottles[target_index]
            else:
                self.hook.target = None
            
            self.hook.stuck_counter = 0
            self.hook.last_position = (self.hook.x, self.hook.y)
            if self.hook.state == 'retrieving' and self.hook.target is not None:
                dx = self.hook.x - self.launcher_x
                dy = self.hook.y - self.launcher_y
                self.hook.length = math.sqrt(dx * dx + dy * dy)
                self.hook.stuck_counter = 0
                self.hook.last_position = (self.hook.x, self.hook.y)

                try:
                    self.hook.target.collected = True
                    self.hook.target.target_x = self.launcher_x
                    self.hook.target.target_y = self.launcher_y
                    self.hook.target.rect.centerx = int(round(self.hook.x))
                    self.hook.target.rect.centery = int(round(self.hook.y))
                except Exception:
                    write_log("恢复钩索目标时出错\n" + traceback.format_exc())
            
            self.start_time = pygame.time.get_ticks() - (GAME_TIME - self.time_left) * 1000
            
            self.just_loaded = True

            self.startup_in_progress = False
            if need_migrate:
                write_log("检测到旧存档格式，正在迁移并写回新存档（UID 格式）")
                try:
                    self.save_game()
                    write_log("迁移并保存新存档成功")
                except Exception:
                    write_log("迁移保存失败\n" + traceback.format_exc())

            write_log("加载存档成功")
            return True
            
        except json.JSONDecodeError as e:
            print(f"存档文件格式错误：{e}")
            return False
        except Exception as e:
            print(f"加载游戏失败: {e}")
            return False
    
    def handle_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.game_over:
                if self.restart_button_rect.collidepoint(event.pos):
                    self.__init__()
                elif self.return_home_button_rect.collidepoint(event.pos):
                    self.running = False
            elif self.paused:
                if self.resume_button_rect.collidepoint(event.pos):
                    self.paused = False
                elif self.quit_button_rect.collidepoint(event.pos):
                    self.save_game()
                    self.running = False
            else:
                if self.pause_button_rect.collidepoint(event.pos):
                    self.paused = True
                else:
                    self.hook.launch(self.launcher_angle)
    
    def draw(self, surface):

        surface.blit(background_image, (0, 0))
        
        pygame.draw.rect(surface, DARK_RED, self.pause_button_rect)
        pause_text = self.font.render("暂停", True, WHITE)
        pause_text_rect = pause_text.get_rect(center=self.pause_button_rect.center)
        surface.blit(pause_text, pause_text_rect)
        
        score_text = self.font.render(f"蔚蓝守护值: {self.score}", True, WHITE)
        score_rect = pygame.Rect(100, 10, 260, 50)  # 调整位置和宽度以容纳新文字
        pygame.draw.rect(surface, DARK_RED, score_rect)
        surface.blit(score_text, (score_rect.x + 10, score_rect.y + 10))
        
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_text = self.font.render(f"时间: {minutes:02d}:{seconds:02d}", True, WHITE)
        time_rect = pygame.Rect(WIDTH - 210, 10, 200, 50)
        pygame.draw.rect(surface, DARK_RED, time_rect)
        surface.blit(time_text, (time_rect.x + 10, time_rect.y + 10))
        
        if self.launcher_visible:
            indicator_length = 50
            indicator_x = self.launcher_x + math.cos(math.radians(self.launcher_angle)) * indicator_length
            indicator_y = self.launcher_y + math.sin(math.radians(self.launcher_angle)) * indicator_length
            pygame.draw.line(surface, RED, (self.launcher_x, self.launcher_y), (indicator_x, indicator_y), 3)
        
        for bottle in self.bottles:
            bottle.draw(surface)

        for f in self.fishes:
            f.draw(surface)

        for sg in self.sea_glasses:
            sg.draw(surface)
        
        self.hook.draw(surface)
        
        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)  # 60%透明度
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            pause_text = self.large_font.render("游戏暂停", True, WHITE)
            pause_text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            surface.blit(pause_text, pause_text_rect)
            
            mouse_pos = pygame.mouse.get_pos()
            if self.resume_button_rect.collidepoint(mouse_pos):
                resume_color = (173, 216, 230)  # 悬停颜色
            else:
                resume_color = LIGHT_BLUE
            pygame.draw.rect(surface, resume_color, self.resume_button_rect, border_radius=10)
            resume_text = self.font.render("继续游戏", True, WHITE)
            resume_text_rect = resume_text.get_rect(center=self.resume_button_rect.center)
            surface.blit(resume_text, resume_text_rect)
            
            if self.quit_button_rect.collidepoint(mouse_pos):
                quit_color = (173, 216, 230)  # 悬停颜色
            else:
                quit_color = LIGHT_BLUE
            pygame.draw.rect(surface, quit_color, self.quit_button_rect, border_radius=10)
            quit_text = self.font.render("结束游戏", True, WHITE)
            quit_text_rect = quit_text.get_rect(center=self.quit_button_rect.center)
            surface.blit(quit_text, quit_text_rect)
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            congratulation_text = "挑战完成！"
            score_text = f"您的蔚蓝守护值是{self.score}！"
            
            for text, y_offset in [(congratulation_text, -80), (score_text, -20)]:
                for dx, dy in [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]:
                    text_surface = self.large_font.render(text, True, WHITE)
                    text_rect = text_surface.get_rect(center=(WIDTH // 2 + dx, HEIGHT // 2 + y_offset + dy))
                    surface.blit(text_surface, text_rect)
                text_surface = self.large_font.render(text, True, RED)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
                surface.blit(text_surface, text_rect)
            
            mouse_pos = pygame.mouse.get_pos()
            is_restart_clicked = False
            is_return_clicked = False
            
            if pygame.mouse.get_pressed()[0]:
                if self.restart_button_rect.collidepoint(mouse_pos):
                    is_restart_clicked = True
                elif self.return_home_button_rect.collidepoint(mouse_pos):
                    is_return_clicked = True
            
            restart_scale = 0.95 if is_restart_clicked else 1.0
            restart_color = LIGHT_BLUE if not self.restart_button_rect.collidepoint(mouse_pos) else (100, 180, 210)
            restart_width = int(self.restart_button_rect.width * restart_scale)
            restart_height = int(self.restart_button_rect.height * restart_scale)
            restart_x = self.restart_button_rect.x + (self.restart_button_rect.width - restart_width) // 2
            restart_y = self.restart_button_rect.y + (self.restart_button_rect.height - restart_height) // 2
            pygame.draw.rect(surface, restart_color, (restart_x, restart_y, restart_width, restart_height), border_radius=10)
            restart_button_text = self.font.render("再来一次", True, WHITE)
            restart_text_rect = restart_button_text.get_rect(center=(self.restart_button_rect.centerx, self.restart_button_rect.centery))
            surface.blit(restart_button_text, restart_text_rect)
            
            return_scale = 0.95 if is_return_clicked else 1.0
            return_color = LIGHT_BLUE if not self.return_home_button_rect.collidepoint(mouse_pos) else (100, 180, 210)
            return_width = int(self.return_home_button_rect.width * return_scale)
            return_height = int(self.return_home_button_rect.height * return_scale)
            return_x = self.return_home_button_rect.x + (self.return_home_button_rect.width - return_width) // 2
            return_y = self.return_home_button_rect.y + (self.return_home_button_rect.height - return_height) // 2
            pygame.draw.rect(surface, return_color, (return_x, return_y, return_width, return_height), border_radius=10)
            return_button_text = self.font.render("返回主页", True, WHITE)
            return_text_rect = return_button_text.get_rect(center=(self.return_home_button_rect.centerx, self.return_home_button_rect.centery))
            surface.blit(return_button_text, return_text_rect)

def main():
    class Button:
        def __init__(self, x, y, width, height, text, color, hover_color, text_color):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.color = color
            self.hover_color = hover_color
            self.text_color = text_color
            self.font = pygame.font.SysFont("Microsoft YaHei", 36)
            
        def draw(self, surface):
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, self.hover_color, self.rect, border_radius=10)
            else:
                pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
            
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
            
        def is_clicked(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    return self.rect.collidepoint(event.pos)
            return False
    
    while True:
        clock = pygame.time.Clock()
        login_background = pygame.image.load(os.path.join(script_dir, "art_resources/login_background.png"))
        login_background = pygame.transform.scale(login_background, (WIDTH, HEIGHT))
        
        button_width = 200
        button_height = 60
        button_x = WIDTH - button_width - 50
        button_y = HEIGHT // 2 - button_height // 2
        
        start_button = Button(
            button_x, button_y, button_width, button_height,
            "开始游戏", 
            (0, 128, 255),
            (0, 191, 255),
            (255, 255, 255)
        )
        
        continue_button_y = HEIGHT // 2 + button_height // 2 + 20
        continue_button = Button(
            button_x, continue_button_y, button_width, button_height,
            "继续游玩",
            (0, 128, 0),
            (0, 191, 0),
            (255, 255, 255)
        )
        
        has_save_file = os.path.exists(SAVE_FILE_PATH)
        
        login_running = True
        while login_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    login_running = False
                    pygame.quit()
                    sys.exit()
                
                if start_button.is_clicked(event):
                    login_running = False
                    continue_game = False
                elif has_save_file and continue_button.is_clicked(event):
                    login_running = False
                    continue_game = True
            
            window.blit(login_background, (0, 0))
            start_button.draw(window)
            
            if has_save_file:
                continue_button.draw(window)
            
            pygame.display.flip()
            clock.tick(FPS)
        
        def render_wrapped_text(surface, text, font_name, color, area_rect, max_font_size=48, min_font_size=12, line_spacing=4, align='center'):
            paragraphs = text.split("\n")
            for size in range(max_font_size, min_font_size - 1, -1):
                font = pygame.font.SysFont(font_name, size)
                lines = []
                for para in paragraphs:
                    if para == "":
                        lines.append("")
                        continue

                    if " " in para:
                        words = para.split()
                        cur = ""
                        for w in words:
                            test = cur + (" " if cur else "") + w
                            if font.size(test)[0] <= area_rect.width:
                                cur = test
                            else:
                                if cur:
                                    lines.append(cur)
                                if font.size(w)[0] > area_rect.width:
                                    sub = ""
                                    for ch in w:
                                        if font.size(sub + ch)[0] <= area_rect.width:
                                            sub += ch
                                        else:
                                            if sub:
                                                lines.append(sub)
                                            sub = ch
                                    if sub:
                                        cur = sub
                                    else:
                                        cur = ""
                                else:
                                    cur = w
                        if cur:
                            lines.append(cur)
                    else:
                        cur = ""
                        for ch in para:
                            if font.size(cur + ch)[0] <= area_rect.width:
                                cur += ch
                            else:
                                if cur:
                                    lines.append(cur)
                                cur = ch
                        if cur:
                            lines.append(cur)

                total_h = sum(font.size(line)[1] for line in lines) + line_spacing * (len(lines) - 1)
                if total_h <= area_rect.height:
                    y = area_rect.y
                    for line in lines:
                        surf = font.render(line, True, color)
                        if align == 'left':
                            x = area_rect.x
                        else:
                            x = area_rect.x + (area_rect.width - surf.get_width()) // 2
                        surface.blit(surf, (x, y))
                        y += surf.get_height() + line_spacing
                    return True

            font = pygame.font.SysFont(font_name, min_font_size)
            y = area_rect.y
            for para in paragraphs:
                cur = ""
                for ch in para:
                    if font.size(cur + ch)[0] <= area_rect.width:
                        cur += ch
                    else:
                        if cur:
                            surf = font.render(cur, True, color)
                            if align == 'left':
                                x = area_rect.x
                            else:
                                x = area_rect.x + (area_rect.width - surf.get_width()) // 2
                            surface.blit(surf, (x, y))
                            y += surf.get_height() + line_spacing
                        cur = ch
                if cur:
                    surf = font.render(cur, True, color)
                    if align == 'left':
                        x = area_rect.x
                    else:
                        x = area_rect.x + (area_rect.width - surf.get_width()) // 2
                    surface.blit(surf, (x, y))
                    y += surf.get_height() + line_spacing
            return False

        def show_background_intro():
            try:
                bg = pygame.image.load(os.path.join(script_dir, "art_resources/blank_background.png"))
                bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
            except Exception:
                bg = pygame.Surface((WIDTH, HEIGHT))
                bg.fill(WHITE)

            text = (
                "蔚蓝深海本是生命的摇篮，如今却被塑料瓶、废电池等垃圾层层裹挟——珊瑚褪色、鱼群迁徙，曾经热闹的海洋家园正逐渐失去生机。\n"
                "作为一名志愿加入“海洋守护者计划”的清理员，你将搭乘专业清理船，潜入近海海域，用精准的打捞设备清除海洋垃圾，为小鱼、小虾等海洋原住民重建干净的家园。\n"
                "每一次成功打捞，都是对海洋生态的一次救赎；每一分努力，都在为蓝色星球注入希望。现在，就让我们即刻启航，守护这片蔚蓝！"
            )

            text_area = pygame.Rect(40, 20, WIDTH - 80, int(HEIGHT * 3 / 4) - 40)
            btn_w = int(WIDTH * 0.4)
            btn_h = int(HEIGHT * 0.12)
            btn_x = (WIDTH - btn_w) // 2
            btn_y = int(HEIGHT * 3 / 4) + ((HEIGHT // 4) - btn_h) // 2

            intro_btn = Button(btn_x, btn_y, btn_w, btn_h, "即刻出发！", (200, 30, 30), (230, 60, 60), WHITE)
            intro_font_name = "Microsoft YaHei"

            running = True
            while running:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if intro_btn.is_clicked(ev):
                        return True

                window.blit(bg, (0, 0))
                render_wrapped_text(window, text, intro_font_name, (0, 0, 0), text_area, max_font_size=36, min_font_size=14)

                intro_btn.draw(window)

                pygame.display.flip()
                clock.tick(FPS)

        def show_play_intro():
            text = (
                "【玩法介绍】\n\n"
                "1.  核心目标：操控打捞设备，精准捕获海洋中的各类垃圾，积累蔚蓝守护值的同时，避开海洋原住民，守护海洋生态平衡。\n\n"
                "2.  打捞规则：点击启动打捞设备，设备会沿当前方向发射，命中目标后会自动回收，成功捕获目标即可获得对应蔚蓝守护值；若误捕海洋原住民，将扣除蔚蓝守护值。\n\n"
                "3.  蔚蓝守护值明细：\n"
                "- 塑料瓶：500蔚蓝守护值 -- 常见垃圾，清理优先级高\n"
                "- 易拉罐：600蔚蓝守护值 -- 不易降解，及时清理可减少海洋污染\n"
                "- 废药瓶：750蔚蓝守护值 -- 含有害成分，对海洋生物危害极大，优先清理\n"
                "- 废电池：800蔚蓝守护值 -- 高污染垃圾，严重破坏海洋生态，重中之重\n"
                "- 海玻璃：1000-1200蔚蓝守护值 -- 海洋垃圾经自然打磨形成的“幸运彩蛋”，是清理途中的意外惊喜\n"
                "- 误捕小鱼：倒扣750蔚蓝守护值！-- 海洋原住民不可伤害，守护它们就是守护海洋生态"
            )

            text_area = pygame.Rect(40, 20, WIDTH - 80, int(HEIGHT * 3 / 4) - 40)
            btn_w = int(WIDTH * 0.4)
            btn_h = int(HEIGHT * 0.12)
            btn_x = (WIDTH - btn_w) // 2
            btn_y = int(HEIGHT * 3 / 4) + ((HEIGHT // 4) - btn_h) // 2

            go_btn = Button(btn_x, btn_y, btn_w, btn_h, "为了海洋！", (200, 30, 30), (230, 60, 60), WHITE)
            intro_font_name = "Microsoft YaHei"

            running = True
            while running:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if go_btn.is_clicked(ev):
                        return True

                    try:
                        play_bg = pygame.image.load(os.path.join(script_dir, "art_resources/blank_background.png"))
                        play_bg = pygame.transform.scale(play_bg, (WIDTH, HEIGHT))
                        window.blit(play_bg, (0, 0))
                    except Exception:
                        window.fill(WHITE)

                    render_wrapped_text(window, text, intro_font_name, (0, 0, 0), text_area, max_font_size=30, min_font_size=12, align='left')
                go_btn.draw(window)
                pygame.display.flip()
                clock.tick(FPS)

        game = None
        if not continue_game:
            proceed = show_background_intro()
            if not proceed:
                pygame.quit()
                sys.exit()
            proceed2 = show_play_intro()
            if not proceed2:
                pygame.quit()
                sys.exit()
            game = Game()
        else:
            game = Game()
            game.load_game()
        
        while game.running:
            for event in pygame.event.get():
                game.handle_events(event)
            
            if game.running:
                game.update()
                game.draw(window)
                
                pygame.display.flip()
                clock.tick(FPS)

if __name__ == "__main__":
    main()
    