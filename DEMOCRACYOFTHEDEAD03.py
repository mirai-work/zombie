import pyxel
import random
import math

# --- 定数 ---
WINDOW_W = 160
WINDOW_H = 120

PLAYER_SPEED = 1.7
PLAYER_R = 5
ZOMBIE_R = 4

SANCTUARY_W = 16
MAX_STAGE_PLAY = 5 
ZOMBIE_COUNT_BASE = 6 
TRANSFORM_DURATION = 180
FOLLOW_DISTANCE = 12
TRAIL_MAX_LENGTH = 200
FINAL_SCENE_HOLD_TIME = 180
UI_HEIGHT = 20
CREDITS_SPEED = 0.5 
GAMEOVER_HOLD_TIME = 120 # タイムアップ後の画面保持時間 (2秒)

# ステージ時間設定
BASE_TIME_LIMIT = 45.0 # ステージ1の初期制限時間
BONUS_TIME_AFTER_CLEAR = 10.0 # 追加ボーナス時間 (10秒)
FINAL_STAGE_ZOMBIES = 30 
FINAL_STAGE_TIME_LIMIT_MIN = 20.0 # 最終ステージの最低制限時間

# --- クレジット ---
CREDITS_CONTENT = [
    (16, "DEMOCRACY OF THE DEAD", 8),
    (8, "---", 7),
    (12, "GAME DESIGN & CONCEPT", 11),
    (12, "Y. Kusanagi", 7),
    (8, "", 0),
    (12, "PROGRAMMING & GRAPHICS", 11),
    (12, "M. Takahashi", 7),
    (8, "", 0),
    (12, "SPECIAL THANKS TO:", 11),
    (12, "Team Toda", 7),
    (12, "All Players", 7),
    (8, "", 0),
    (12, "TEST PLAYERS", 11),
    (12, "Team Toda", 7),
    (12, "M.Takahashi", 7),
    (8, "", 0),
    (16, "THANK YOU FOR PLAYING!", 13),
    (8, "---", 7),
    (12, "Presented in MIRAI WORK", 13),
    (8, "---", 7),
    (12, "NEXT GAME AGAIN!", 8), 

    (WINDOW_H, "", 0)
]

# --- ユーティリティ ---
def clamp(v, a, b):
    return max(a, min(b, v))

def dist(ax, ay, bx, by):
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

def center_text_x(text):
    """テキストを中央揃えにするX座標を計算する"""
    return (WINDOW_W - len(text) * 4) // 2

# ------------------------------------------------------------
# プレイヤー (移動入力部分を互換性のある数値に修正)
# ------------------------------------------------------------
class Player:
    def __init__(self, x, y, is_main=True, color_override=None):
        self.x, self.y = x, y
        self.dir = 1
        self.walk_frame = 0
        self.color = color_override if color_override is not None else 11
        self.is_main = is_main
        self.is_zombified = False
        self.temp_color = None
        self.dust_particles = []
        self.transform_particles = []

        if self.is_main:
            self.trail = [(x, y)] * TRAIL_MAX_LENGTH
        else:
            self.trail = None

    def update(self, obstacles, controllable=True):
        # 変異時のパーティクル更新
        for p in self.transform_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
        self.transform_particles = [p for p in self.transform_particles if p[5] > 0]

        if not self.is_main:
            return

        dx, dy = 0, 0
        
        # ゾンビ化しているか、操作不能フラグが立っている場合は移動しない
        if controllable and not self.is_zombified:
            # --- 🎮 ゲームパッド入力の互換性修正 (DPADを数値IDに置き換え) ---
            # 5: RIGHT, 4: LEFT, 3: DOWN, 2: UP
            dx = (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(5)) - \
                 (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(4))
            dy = (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(3)) - \
                 (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(2))
            # ----------------------------------------

        moved = (dx != 0 or dy != 0)
        if moved:
            self.walk_frame = (self.walk_frame + 1) % 16
            sp = PLAYER_SPEED
            nx = self.x + dx * sp
            ny = self.y + dy * sp

            self.x, self.y = nx, ny

            if pyxel.frame_count % 3 == 0:
                self.dust_particles.append([self.x + random.randint(-2, 2), self.y + random.randint(2, 4),
                                             random.uniform(-0.5, 0.5), random.uniform(-0.5, 0), 6, 15])

            if dx > 0:
                self.dir = 1
            if dx < 0:
                self.dir = -1

        self.x = clamp(self.x, PLAYER_R, WINDOW_W - 1 - PLAYER_R)
        self.y = clamp(self.y, UI_HEIGHT + PLAYER_R, WINDOW_H - 1 - PLAYER_R)

        if self.is_main and not self.is_zombified: # ゾンビ化したら軌跡の更新を停止
            self.trail.insert(0, (self.x, self.y))
            self.trail = self.trail[:TRAIL_MAX_LENGTH]

        for p in self.dust_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
        self.dust_particles = [p for p in self.dust_particles if p[5] > 0]

    def draw(self):
        x, y = int(self.x), int(self.y)
        c = self.temp_color if self.temp_color is not None else self.color
        wf = (self.walk_frame // 4)
        foot_offset = [0, 1, -1, 0][wf]

        # パーティクル描画
        for p in self.dust_particles:
            pyxel.pset(int(p[0]), int(p[1]), p[4])
        for p in self.transform_particles:
            pyxel.pset(int(p[0]), int(p[1]), p[4])

        # 影
        pyxel.circ(x, y + 3, 4, 0)
        pyxel.circ(x, y + 3, 3, 1)

        if self.is_zombified:
            # ゾンビ化後の見た目
            z_c = 3
            pyxel.rect(x - 3, y - 3, 6, 6, z_c)
            pyxel.rect(x - 2, y - 2, 4, 4, z_c + 1)
            pyxel.circ(x, y - 5, 2, z_c)
            pyxel.pset(x + self.dir, y - 5, 8)
            pyxel.pset(x - self.dir, y - 5, 8)
            return

        # 胴体
        pyxel.rect(x - 3, y - 3, 6, 6, c)
        pyxel.rect(x - 2, y - 2, 4, 4, c - 1)
        pyxel.rect(x - 1, y - 1, 2, 2, c - 2)

        # 足の動き
        pyxel.rect(x - 3, y + 3 + foot_offset, 6, 2, c)
        pyxel.rect(x - 2, y + 3 + foot_offset, 4, 1, c - 1)

        # 頭部
        pyxel.circ(x, y - 6, 3, 6)
        pyxel.circ(x, y - 6, 2, 7)
        pyxel.pset(x - 1, y - 7, 7)

        # 目
        eye_offset = 0
        if pyxel.frame_count % 120 < 5:
            eye_offset = 1
        pyxel.line(x + self.dir * 1, y - 6 - eye_offset, x + self.dir * 1, y - 6 + eye_offset, 0)

        # 髪の毛
        hair_offset = 0
        if pyxel.frame_count % 16 < 8:
            hair_offset = 1
            
        hair_color = 5
        if c == 7:
            hair_color = 12
        elif c == 8:
            hair_color = 6

        pyxel.pset(x - 2 * self.dir, y - 7 - hair_offset, hair_color)


# ------------------------------------------------------------
# ゾンビ (変更なし)
# ------------------------------------------------------------
class Zombie:
    def __init__(self, x, y, speed_factor=1.0, global_speed_multiplier=1.0):
        self.x, self.y = x, y
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.4, 0.4)
        self.dir = 1
        self.state = "wander"
        self.speed_factor = speed_factor * global_speed_multiplier 
        self.base_color = random.choice([3, 11, 4])
        self.bite_frame = 0
        self.captured_particles = []

    def update(self, player, obstacles, captured_zombies):
        px, py = player.x, player.y
        d = dist(self.x, self.y, px, py)

        if self.state == "captured":
            try:
                index = captured_zombies.index(self)
            except ValueError:
                index = 0
            target_index = min(len(player.trail) - 1, (index + 1) * FOLLOW_DISTANCE)
            target_pos = player.trail[target_index]
            tx, ty = target_pos

            td = dist(self.x, self.y, tx, ty)
            sp = 1.0 * self.speed_factor 

            if td > 1.0:
                self.vx = (tx - self.x) / td * sp
                self.vy = (ty - self.y) / td * sp
            else:
                self.vx = 0
                self.vy = 0

            nx = self.x + self.vx
            ny = self.y + self.vy
            self.x, self.y = nx, ny

            if abs(self.vx) > 0.1:
                if self.vx > 0:
                    self.dir = 1
                if self.vx < 0:
                    self.dir = -1

            for p in self.captured_particles:
                p[0] += p[2]
                p[1] += p[3]
                p[5] -= 1
            self.captured_particles = [p for p in self.captured_particles if p[5] > 0]

            self.x = clamp(self.x, ZOMBIE_R, WINDOW_W - 1 - ZOMBIE_R)
            self.y = clamp(self.y, UI_HEIGHT + ZOMBIE_R, WINDOW_H - 1 - ZOMBIE_R)
            return

        # プレイヤーとの接触判定（捕獲）
        if d < PLAYER_R + ZOMBIE_R and self.state != "captured" and not player.is_zombified:
            self.state = "captured"
            self.vx = 0
            self.vy = 0
            for _ in range(random.randint(5, 10)):
                self.captured_particles.append(
                    [self.x, self.y, random.uniform(-1, 1), random.uniform(-1, -0.5), random.choice([7, 8, 3]), 30])
            return

        # プレイヤー追跡ロジック (プレイヤーがゾンビ化していない場合のみ追跡)
        if not player.is_zombified:
            if d < 45:
                self.state = "follow"
                if d != 0:
                    self.vx += (px - self.x) / d * 0.1
                    self.vy += (py - self.y) / d * 0.1
            else:
                self.state = "wander"
                if random.random() < 0.02:
                    self.vx = random.uniform(-0.5, 0.5)
                    self.vy = random.uniform(-0.5, 0.5)

        v_len = dist(0, 0, self.vx, self.vy)
        max_v = 1.0 * self.speed_factor
        if v_len > max_v and v_len != 0:
            self.vx *= max_v / v_len
            self.vy *= max_v / v_len

        nx = self.x + self.vx
        ny = self.y + self.vy

        # 聖域境界での移動制限
        sanctuary_boundary = WINDOW_W - SANCTUARY_W
        if nx > sanctuary_boundary - ZOMBIE_R:
            if self.x <= sanctuary_boundary - ZOMBIE_R:
                self.vx = 0
            nx = self.x

        self.x, self.y = nx, ny

        if self.vx > 0:
            self.dir = 1
        if self.vx < 0:
            self.dir = -1

        self.x = clamp(self.x, ZOMBIE_R, WINDOW_W - 1 - ZOMBIE_R)
        self.y = clamp(self.y, UI_HEIGHT + ZOMBIE_R, WINDOW_H - 1 - ZOMBIE_R)

    def draw(self):
        x, y = int(self.x), int(self.y)

        for p in self.captured_particles:
            pyxel.pset(int(p[0]), int(p[1]), p[4])

        # 影
        pyxel.circ(x, y + 3, 4, 0)
        pyxel.circ(x, y + 3, 3, 1)

        c = 7 if self.state == "captured" else self.base_color

        # 胴体
        pyxel.rect(x - 3, y - 3, 6, 6, c)
        pyxel.rect(x - 2, y - 2, 4, 4, c + 1)
        pyxel.pset(x + random.randint(-2, 2), y + random.randint(-2, 2), 8)

        # 頭部
        pyxel.circ(x, y - 5, 2, c)
        pyxel.pset(x + self.dir, y - 5, 8)
        if pyxel.frame_count % 30 < 15:
            pyxel.pset(x - self.dir, y - 5, 8)


# ------------------------------------------------------------
# フェード・シェイク (変更なし)
# ------------------------------------------------------------
class Fade:
    def __init__(self):
        self.alpha = 0.0
        self.target = 0.0
        self.speed = 0.06
        self.active = False

    def to(self, target, speed=None):
        self.target = clamp(target, 0.0, 1.0)
        if speed is not None:
            self.speed = speed
        self.active = True

    def update(self):
        if not self.active:
            return
        if self.alpha < self.target:
            self.alpha = clamp(self.alpha + self.speed, 0.0, 1.0)
        elif self.alpha > self.target:
            self.alpha = clamp(self.alpha - self.speed, 0.0, 1.0)
        if abs(self.alpha - self.target) < 0.01:
            self.alpha = self.target
            self.active = False

    def draw(self):
        if self.alpha <= 0.01:
            return
        layers = int(self.alpha * 8) + 1
        # alpha値に基づき、半透明を表現するために黒を複数回重ねて描画する
        for i in range(layers):
            pyxel.rect(0, 0, WINDOW_W, WINDOW_H, 0)


class Shake:
    def __init__(self):
        self.timer = 0
        self.intensity = 0

    def start(self, frames=12, intensity=2):
        self.timer = frames
        self.intensity = intensity

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    def get_offset(self):
        if self.timer <= 0:
            return 0, 0
        return (random.randint(-self.intensity, self.intensity),
                random.randint(-self.intensity, self.intensity))


# ------------------------------------------------------------
# メインゲーム (入力判定部分を互換性のある数値に修正)
# ------------------------------------------------------------
class GameApp:
    def __init__(self):
        pyxel.init(WINDOW_W, WINDOW_H, title="DEMOCRACY OF THE DEAD")
        
        # Pyxelパレットのカスタム設定
        try:
            pyxel.pal(1, 4)
            pyxel.pal(3, 8)
            pyxel.pal(4, 5)
            pyxel.pal(7, 6)
            pyxel.pal(8, 8)
            pyxel.pal(10, 12)
            pyxel.pal(11, 2)
            pyxel.pal(12, 9)
            pyxel.pal(13, 15)
        except Exception:
            pass

        self.fade = Fade()
        self.shake = Shake()

        self.state = "TITLE"
        self.stage = -1 
        self.stage_start_frame = 0
        self.stage_time_limit = 0.0
        self.time_remaining_next_stage = BASE_TIME_LIMIT
        self.last_stage_remaining_time = 0.0  
        self.start_time_total = 0.0 
        self.zombie_speed_multiplier = 1.0

        self.player = None
        self.players = []
        self.zombies = []
        self.obstacles = []
        self.dummy_players = []
        self.captured_zombies = []

        self.marching = False
        self.fade_outting = False
        self.next_state_called = False

        self.time_up_zombified = False 
        self.time_up_frame = 0 
        
        self.total_clear_time = 0.0 
        self.ending_timer = 0
        self.credits_y = WINDOW_H
        self.credits_duration = sum(height for height, _, _ in CREDITS_CONTENT)
        self.title_particles = [(random.randint(0, WINDOW_W), random.randint(0, 18), random.random() * 1.4) for _ in
                                 range(28)]
        
        self.show_final_score = False

        pyxel.run(self.update, self.draw)

    def spawn_stage(self):
        self.stage += 1
        
        # Final Stageクリア後の再開 (2週目 Stage 1)
        if self.stage > MAX_STAGE_PLAY + 1:
             self.stage = 1

        if self.stage == 0:
            # 初回起動時のStage 1
            self.stage = 1
            self.stage_time_limit = self.time_remaining_next_stage
            
        elif self.stage <= MAX_STAGE_PLAY:
            # 通常ステージ (2週目 Stage 1 も含む)
            self.stage_time_limit = self.time_remaining_next_stage
        elif self.stage == MAX_STAGE_PLAY + 1:
            # Final Stage
            self.stage_time_limit = max(FINAL_STAGE_TIME_LIMIT_MIN, self.time_remaining_next_stage)

        # タイムアップ状態をリセット
        self.time_up_zombified = False 
        self.time_up_frame = 0
        
        if self.stage == MAX_STAGE_PLAY + 1:
            # Final Stageの初期化
            self.obstacles = []
            spawn_x, spawn_y = WINDOW_W // 4, WINDOW_H // 2
            
            self.players = []
            self.player = Player(spawn_x, spawn_y, is_main=True)
            self.players.append(self.player)

            sanctuary_pos_x = WINDOW_W - SANCTUARY_W + 8
            self.dummy_players = [
                Player(sanctuary_pos_x, WINDOW_H // 2 - 20, is_main=False, color_override=11), 
                Player(sanctuary_pos_x + 5, WINDOW_H // 2, is_main=False, color_override=7), 
                Player(sanctuary_pos_x, WINDOW_H // 2 + 20, is_main=False, color_override=8) 
            ]
            self.players.extend(self.dummy_players)

            self.zombies = []
            self.captured_zombies = []
            zombie_count = FINAL_STAGE_ZOMBIES
                
            for i in range(zombie_count):
                zx = random.randint(0, WINDOW_W - SANCTUARY_W - 6)
                zy = random.randint(UI_HEIGHT, WINDOW_H - 1)
                sf = random.choice([0.8, 1.0, 1.3])
                self.zombies.append(Zombie(zx, zy, speed_factor=sf, global_speed_multiplier=self.zombie_speed_multiplier))
                
            if self.start_time_total == 0.0:
                  self.start_time_total = pyxel.frame_count / 60.0
            
            self.stage_start_frame = pyxel.frame_count
            self.state = "PLAYING"
            self.marching = False
            self.fade.to(0.0, speed=0.08)
            return 

        # 通常ステージ (Stage 1-5, 2週目含む) の初期化
        self.obstacles = []
        spawn_x, spawn_y = WINDOW_W // 4, WINDOW_H // 2
        self.players = []
        self.player = Player(spawn_x, spawn_y, is_main=True)
        self.players.append(self.player)
        self.dummy_players = []

        self.zombies = []
        self.captured_zombies = []
        zombie_count = ZOMBIE_COUNT_BASE + (self.stage - 1) * 2 
            
        for i in range(zombie_count):
            zx = random.randint(0, WINDOW_W - SANCTUARY_W - 6)
            zy = random.randint(UI_HEIGHT, WINDOW_H - 1)
            sf = random.choice([0.8, 1.0, 1.3])
            self.zombies.append(Zombie(zx, zy, speed_factor=sf, global_speed_multiplier=self.zombie_speed_multiplier))

        if self.start_time_total == 0.0:
            self.start_time_total = pyxel.frame_count / 60.0
            
        self.stage_start_frame = pyxel.frame_count
        self.state = "PLAYING"
        self.marching = False
        self.fade.to(0.0, speed=0.08)

    # UPDATE
    def update(self):
        self.fade.update()
        self.shake.update()

        for p in self.players:
            # タイムアップ時は操作不能 (controllable=False)
            can_control = self.state == "PLAYING" and not self.time_up_zombified
            # Player.update()内ですでに修正済み
            p.update(self.obstacles, controllable=can_control) 
            
        for z in self.zombies:
            z.update(self.player, self.obstacles, self.captured_zombies)
            
        # --- 🎮 ゲームパッド入力の互換性修正 (A/STARTボタンを数値IDに置き換え) ---
        # 0: Aボタン, 7: STARTボタン
        is_enter_pressed = pyxel.btnp(pyxel.KEY_RETURN) or \
                           pyxel.btnp(0) or \
                           pyxel.btnp(7)
        # ----------------------------------------

        if self.state == "TITLE":
            if is_enter_pressed:
                self.fade.to(1.0, speed=0.06)
                self.next_state_called = True

            if self.next_state_called and not self.fade.active and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.state = "TUTORIAL"
                self.fade.to(0.0, speed=0.06)

        elif self.state == "TUTORIAL":
            if is_enter_pressed:
                self.fade.to(1.0, speed=0.06)
                self.next_state_called = True

            if self.next_state_called and not self.fade.active and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.stage = 0 
                # ステージ開始時に時間設定
                self.time_remaining_next_stage = BASE_TIME_LIMIT 
                self.start_time_total = 0.0 
                self.spawn_stage()

        elif self.state == "PLAYING":
            # 捕獲処理
            newly_captured = [z for z in self.zombies if z.state == "captured" and z not in self.captured_zombies]
            for z in newly_captured:
                self.captured_zombies.append(z)
                self.shake.start(frames=4, intensity=1)

            # タイムリミットチェック
            elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
            time_left = max(0.0, self.stage_time_limit - elapsed)

            if time_left <= 0.0 and not self.time_up_zombified:
                # --- TIME UP! 処理 ---
                self.time_up_zombified = True
                self.player.is_zombified = True
                self.time_up_frame = pyxel.frame_count
                
            if self.time_up_zombified:
                # ゾンビ化後、一定時間経過したらタイトルへ強制的に戻る
                if pyxel.frame_count - self.time_up_frame > GAMEOVER_HOLD_TIME:
                    self.fade.to(1.0, speed=0.06)
                    self.next_state_called = True

            if self.next_state_called and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.stage = -1 
                self.time_remaining_next_stage = BASE_TIME_LIMIT 
                self.start_time_total = 0.0
                self.state = "TITLE"
                self.fade.to(0.0, speed=0.06)
                return
            # ---------------------

            # 全ゾンビ捕獲チェック
            if len(self.captured_zombies) == len(self.zombies) and len(self.zombies) > 0:
                self.time_remaining_next_stage = time_left
                self.state = "GO_TO_SANCT"
                self.start_march()

        elif self.state == "GO_TO_SANCT":
            self.update_march()

            sanctuary_x_min = WINDOW_W - SANCTUARY_W
            all_in_sanctuary = all(p.x >= sanctuary_x_min for p in self.players if p.is_main) and \
                               all(z.x >= sanctuary_x_min for z in self.captured_zombies)

            if all_in_sanctuary and not self.fade_outting:
                self.marching = False
                self.fade.to(1.0, speed=0.01)
                self.fade_outting = True

            if self.fade_outting and not self.fade.active and self.fade.alpha >= 0.99:
                self.fade_outting = False
                if self.stage == MAX_STAGE_PLAY + 1:
                    # Final Stageクリアの場合
                    self.start_ending()
                else:
                    self.spawn_stage()

        elif self.state == "ENDING":
            if self.ending_timer == 0:
                self.fade.to(0.0, speed=0.08)

            self.ending_timer += 1
            
            # 変異演出
            if self.ending_timer < TRANSFORM_DURATION:
                if self.ending_timer % 10 < 5:
                    self.shake.start(frames=2, intensity=3)
                is_flashing = (self.ending_timer % 3 < 2)
                for p in self.dummy_players:
                    p.temp_color = 3 if is_flashing else (8 if pyxel.frame_count % 6 < 3 else None)
                    p.update(self.obstacles, controllable=False) 

            # 変異完了時
            if self.ending_timer == TRANSFORM_DURATION:
                for p in self.dummy_players:
                    p.is_zombified = True
                    p.temp_color = None
                    for _ in range(random.randint(10, 20)):
                        p.transform_particles.append(
                            [p.x + random.randint(-5, 5), p.y + random.randint(-5, 5), random.uniform(-1.5, 1.5),
                             random.uniform(-1.5, -0.5), random.choice([3, 8, 0]), 60])
                for z in self.zombies:
                    z.x = -100 

            # クレジットロールへ遷移
            if self.ending_timer > TRANSFORM_DURATION + 90:
                self.state = "CREDITS_ROLL"
                self.credits_y = WINDOW_H
                self.fade.to(0.0, speed=0.015)

        elif self.state == "CREDITS_ROLL":
            self.credits_y -= CREDITS_SPEED
            
            # クレジットが完全に画面外に出たことを確認
            if self.credits_y < -(self.credits_duration) + 10: 
                self.show_final_score = True
                
            # スコア表示が完了したらフェードアウト
            if self.credits_y < -(self.credits_duration) - 90: 
                self.fade.to(1.0, speed=0.015)
                
            if self.fade.alpha >= 0.99: 
                # ステージ1に強制的に戻し、持ち越し時間をそのまま引き継ぐ
                self.stage = 0 
                self.start_time_total = pyxel.frame_count / 60.0 
                self.spawn_stage()
                self.fade.to(0.0, speed=0.06)


    def start_ending(self):
        # トータルクリアタイムを計算
        self.total_clear_time = (pyxel.frame_count / 60.0) - self.start_time_total
        
        # 最終ステージクリア時の残り時間を記録
        self.last_stage_remaining_time = self.time_remaining_next_stage

        # 持ち越し時間に10秒ボーナスを加算 
        self.time_remaining_next_stage += BONUS_TIME_AFTER_CLEAR 
        
        self.state = "ENDING"
        self.ending_timer = 0
        self.fade.to(1.0, speed=0.01)
        self.show_final_score = False

    def start_march(self):
        self.marching = True
        for p in self.players:
            p.walk_frame = 0

    def update_march(self):
        if not self.marching:
            return

        tx = WINDOW_W - SANCTUARY_W + 2
        march_speed = PLAYER_SPEED * 1.5

        for e in [self.player] + self.captured_zombies:
            if e.x < tx:
                speed = march_speed
                e.x += min(speed, tx - e.x)
                if isinstance(e, Player):
                    e.walk_frame = (e.walk_frame + 1) % 16
                e.dir = 1

            if isinstance(e, Player) and e.is_main:
                e.trail = [(e.x, e.y)] * TRAIL_MAX_LENGTH

    # DRAW
    def draw(self):
        ox, oy = self.shake.get_offset()

        pyxel.cls(1)

        if self.state == "TITLE":
            self.draw_title()
        elif self.state == "TUTORIAL":
            self.draw_tutorial()
        elif self.state in ("PLAYING", "GO_TO_SANCT"):
            pyxel.clip(0, UI_HEIGHT, WINDOW_W, WINDOW_H - UI_HEIGHT)
            pyxel.camera(ox, oy)

            self.draw_playing()

            pyxel.camera(0, 0)
            pyxel.clip()
            self.draw_ui()
            
            # タイムアップ時、画面中央にメッセージを表示
            if self.time_up_zombified:
                s1 = "TIME UP!"
                s2 = "GAME OVER"
                pyxel.text(center_text_x(s1), WINDOW_H // 2 - 8, s1, 8) 
                pyxel.text(center_text_x(s2), WINDOW_H // 2 + 8, s2, 7) 
                
        elif self.state == "ENDING":
            pyxel.cls(0)
            pyxel.camera(0, 0)
            self.draw_ending_scene()
        elif self.state == "CREDITS_ROLL":
            pyxel.cls(0)
            pyxel.camera(0, 0)
            self.draw_credits_roll()

        self.fade.draw()

    def draw_title_logo(self, cx, cy):
        # ロゴを構成する2行のテキスト
        text1 = "DEMOCRACY"
        text2 = "OF THE DEAD"
        
        # 各行の表示X座標を中央寄せで計算
        x1 = center_text_x(text1)
        x2 = center_text_x(text2)

        pyxel.text(x1, cy - 12, text1, 8)
        pyxel.text(x2, cy + 0, text2, 8)
        
        # 装飾用の点滅
        for i in range(6):
            bx = center_text_x("DEMOCRACY OF THE DEAD") + i * 8 + (pyxel.frame_count % 6) - 10
            by = cy + 18 + (i % 3)
            if pyxel.frame_count % (6 + i) < 4:
                pyxel.pset(bx, by, 8)
                pyxel.pset(bx + 1, by + 1, 8)

    def draw_playing(self):
        sanctuary_x = WINDOW_W - SANCTUARY_W

        # 地面
        for y in range(UI_HEIGHT + 10, WINDOW_H, 12):
            pyxel.line(0, y, WINDOW_W - SANCTUARY_W, y, 9)

        # 聖域エリア
        pyxel.rect(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 10)
        pyxel.rectb(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 12)

        entities = list(self.players) + list(self.zombies)
        entities.sort(key=lambda e: e.y)
        for e in entities:
            e.draw()

        if self.state == "GO_TO_SANCT":
            s = "GO TO SANCTUARY!"
            pyxel.text(center_text_x(s), WINDOW_H - 14, s, 2)

    def draw_ui(self):
        pyxel.rect(0, 0, WINDOW_W, UI_HEIGHT, 0)

        stage_text = f"Stage: {self.stage}/{MAX_STAGE_PLAY}"
        if self.stage == MAX_STAGE_PLAY + 1:
             stage_text = "Stage: FINAL"

        pyxel.text(4, 4, stage_text, 7)
        
        captured_count = len(self.captured_zombies)
        pyxel.text(4, 12, f"Captured: {captured_count}/{len(self.zombies)}", 7)
        
        elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
        time_left = max(0.0, self.stage_time_limit - elapsed)
        
        time_text = f"Time: {time_left:.1f}s"
        t_x = WINDOW_W - len(time_text) * 4 - 4
        
        color = 8 if time_left < 10 or self.time_up_zombified else 7
        
        pyxel.text(t_x, 8, time_text, color)
            
            
    def draw_title(self):
        pyxel.cls(0)
        
        # タイトルロゴ (Y=22)
        self.draw_title_logo(WINDOW_W // 2, 22) 
        
        # --- 🎮 ゲームパッド入力の修正 (テキスト) ---
        begin_text = "- PRESS ENTER / GAMEPAD A/START TO BEGIN -" 
        # ----------------------------------------
        text_x = center_text_x(begin_text)
        text_y = 80 
        
        if pyxel.frame_count % 30 < 15:
             pyxel.text(text_x, text_y, begin_text, 7) 
        
        # パーティクル
        for i, (px, py, spd) in enumerate(self.title_particles):
            ny = (py + (pyxel.frame_count % 40) * spd) % 30 
            pyxel.pset(px, ny + 10, 8 if (pyxel.frame_count + i) % 15 < 7 else 4)
        
        # 初期制限時間表示
        diff_text = f"Initial Time: {BASE_TIME_LIMIT:.1f}s"
        pyxel.text(center_text_x(diff_text), 92, diff_text, 7) 
        
        # クレジット表示を中央寄せ
        credit_y1 = 104
        credit_y2 = 112
        credit_text1 = "(C) Y.Kusanagi"
        credit_text2 = "Game Assembly by (C) M.Takahashi"

        pyxel.text(center_text_x(credit_text1), credit_y1, credit_text1, 13)
        pyxel.text(center_text_x(credit_text2), credit_y2, credit_text2, 13) 

    def draw_tutorial(self):
        pyxel.cls(0)
        cx = WINDOW_W // 2
        
        # --- 🎮 ゲームパッド入力の修正 (テキスト) ---
        begin_text = "- PRESS ENTER / GAMEPAD A/START TO BEGIN -" 
        # ----------------------------------------
        text_x = center_text_x(begin_text)
        text_y = 4
        
        if pyxel.frame_count % 30 < 15:
             pyxel.text(text_x, text_y, begin_text, 8) 
        
        # 中央タイトル
        t_title = "TUTORIAL"
        pyxel.text(center_text_x(t_title), 16, t_title, 8)
        
        # 中央の線をタイトル幅に合わせる
        t_line_start = center_text_x(t_title)
        t_line_end = t_line_start + len(t_title) * 4 - 1
        pyxel.line(t_line_start, 24, t_line_end, 24, 7)
        
        # チュートリアルの項目
        
        # 項目1
        y = 34 
        t1_1 = "1. MOVE:"
        # --- 🎮 ゲームパッド入力の修正 (テキスト) ---
        t1_2 = "Use ARROW keys / GAMEPAD DPAD."
        # ----------------------------------------
        pyxel.text(center_text_x(t1_2), y, t1_1, 7) 
        pyxel.text(center_text_x(t1_2), y + 6, t1_2, 7)
        
        # 項目2
        y = 50 
        t2_1 = "2. CAPTURE:"
        t2_2 = "Touch ZOMBIES to capture them."
        t2_3 = "Captured ZOMBIES follow you."
        pyxel.text(center_text_x(t2_2), y, t2_1, 7)
        pyxel.text(center_text_x(t2_2), y + 6, t2_2, 7)
        pyxel.text(center_text_x(t2_2), y + 12, t2_3, 7)

        # 項目3
        y = 74 
        t3_1 = "3. CLEAR:"
        t3_2 = "Capture ALL ZOMBIES and enter the"
        t3_3 = "SANCTUARY (right side) to clear."
        pyxel.text(center_text_x(t3_2), y, t3_1, 7)
        pyxel.text(center_text_x(t3_2), y + 6, t3_2, 7)
        pyxel.text(center_text_x(t3_3), y + 12, t3_3, 7) 

        # 項目4
        y = 98 
        t4_1 = "4. TIME LIMIT:"
        t4_2 = "Remaining time carries over."
        t4_3 = "Time up means GAME OVER."
        pyxel.text(center_text_x(t4_2), y, t4_1, 8)
        pyxel.text(center_text_x(t4_2), y + 6, t4_2, 8)
        pyxel.text(center_text_x(t4_3), y + 12, t4_3, 8)


    def draw_ending_scene(self):
        pyxel.rect(WINDOW_W - SANCTUARY_W, 0, SANCTUARY_W, WINDOW_H, 10)

        if self.ending_timer < TRANSFORM_DURATION and self.ending_timer % 3 == 0:
            pyxel.rect(WINDOW_W - SANCTUARY_W, 0, SANCTUARY_W, WINDOW_H, random.choice([8, 0, 3]))

        for p in self.players:
            p.draw()
            
        # ゾンビ化進行中
        if self.ending_timer < TRANSFORM_DURATION:
            s = "THE SANCTUARY IS COMPROMISING..."
            pyxel.text(center_text_x(s), 10, s, 8) 
            s2 = "IT HURTS... IT HURTS..."
            pyxel.text(center_text_x(s2), 20, s2, 7) 
        # ゾンビ化完了後
        else:
            s = "THE SANCTUARY WAS COMPROMISED."
            pyxel.text(center_text_x(s), 10, s, 8)
            s2 = "YOU SAVED THEM. BUT WHO SAVED US?"
            pyxel.text(center_text_x(s2), 20, s2, 7)
            

    def draw_credits_roll(self):
        pyxel.cls(0)
        current_y = self.credits_y
        
        # クレジット本文の描画
        for height, text, color in CREDITS_CONTENT:
            if text != "":
                x = center_text_x(text)
                # 画面内にあるクレジット行のみ描画
                if -10 < current_y < WINDOW_H + 10: 
                    pyxel.text(x, current_y, text, color)
            current_y += height
            
        # スコア表示
        if self.show_final_score:
            
            # --- スコア表示エリア ---
            time_text = f"TOTAL CLEAR TIME: {self.total_clear_time:.2f}s"
            remaining_text = f"LAST STAGE REMAINING: {self.last_stage_remaining_time:.1f}s"
            next_time_text = f"NEXT STAGE TIME: {self.time_remaining_next_stage:.1f}s"
            
            y_start = WINDOW_H // 2 - 20
            
            pyxel.text(center_text_x(time_text), y_start, time_text, 7)
            pyxel.text(center_text_x(remaining_text), y_start + 12, remaining_text, 7)
            pyxel.text(center_text_x(next_time_text), y_start + 24, next_time_text, 8)
            

GameApp()