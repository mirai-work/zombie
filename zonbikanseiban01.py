import pyxel
import random
import math

# --- 定数 ---
WINDOW_W = 160
WINDOW_H = 120

PLAYER_SPEED = 1.7 # プレイヤーの基本速度
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

# TIME UP! や GAME OVER の表示時間 (フレーム単位, 3秒 = 180フレーム)
GAME_OVER_HOLD_FRAMES = 180 

# ステージ6の特別設定
FINAL_STAGE_ZOMBIES = 30 
FINAL_STAGE_OBSTACLES = 13
FINAL_STAGE_TIME_LIMIT = 20 

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
    (12, "Presented in MIRAI WORKS", 13),
    (8, "", 0), 
    (12, "Next try hard mode.", 11), 
    (12, "See you again!", 11),      
    (WINDOW_H, "", 0) 
]

# --- ユーティリティ ---
def clamp(v, a, b):
    return max(a, min(b, v))

def dist(ax, ay, bx, by):
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

# ------------------------------------------------------------
# 障害物
# ------------------------------------------------------------
class Obstacle:
    def __init__(self, x, y, w, h, color=5):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color

    def draw(self):
        x, y, w, h = int(self.x), int(self.y), self.w, self.h

        # 遠近法的な影
        for i in range(3):
            pyxel.rect(x + 1 + i, y + 1 + i, w - i * 2, h - i * 2, 0)

        # 本体
        pyxel.rect(x, y, w, h, self.color)

        # ハイライト
        pyxel.line(x, y, x + w - 1, y, self.color + 1)
        pyxel.line(x, y + 1, x + w - 1, y + 1, self.color + 1)
        pyxel.line(x, y, x, y + h - 1, self.color + 1)
        pyxel.line(x + 1, y, x + 1, y + h - 1, self.color + 1)

        # エッジの影
        pyxel.rectb(x, y, w, h, 1)

    def collide(self, x, y, r):
        cx = clamp(x, self.x, self.x + self.w)
        cy = clamp(y, self.y, self.y + self.h)
        return (x - cx) ** 2 + (y - cy) ** 2 < r * r


# ------------------------------------------------------------
# プレイヤー
# ------------------------------------------------------------
class Player:
    def __init__(self, x, y, is_main=True, color_override=None, speed_factor=1.0):
        self.x, self.y = x, y
        self.dir = 1
        self.walk_frame = 0
        self.color = color_override if color_override is not None else 11
        self.is_main = is_main
        self.is_zombified = False
        self.temp_color = None
        self.dust_particles = []
        self.transform_particles = []
        self.speed_factor = speed_factor

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
            # ダミーは移動しない
            return

        # 強制行進中は操作無効（controllable フラグで制御）
        dx, dy = 0, 0
        if controllable:
            dx = (pyxel.btn(pyxel.KEY_RIGHT)) - (pyxel.btn(pyxel.KEY_LEFT))
            dy = (pyxel.btn(pyxel.KEY_DOWN)) - (pyxel.btn(pyxel.KEY_UP))

        moved = (dx != 0 or dy != 0)
        if moved:
            self.walk_frame = (self.walk_frame + 1) % 16
            
            # プレイヤー速度に難易度係数を乗算
            sp = PLAYER_SPEED * self.speed_factor 
            
            nx = self.x + dx * sp
            ny = self.y + dy * sp

            hit = False
            for ob in obstacles:
                if ob.collide(nx, ny, PLAYER_R):
                    if not ob.collide(self.x, ny, PLAYER_R):
                        nx = self.x
                    elif not ob.collide(nx, self.y, PLAYER_R):
                        ny = self.y
                    else:
                        hit = True
                    break
            if not hit:
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

        if self.is_main:
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
        if c == 7: # 女性の色
            hair_color = 12
        elif c == 8: # もう一人の男性の色
            hair_color = 6

        pyxel.pset(x - 2 * self.dir, y - 7 - hair_offset, hair_color)


# ------------------------------------------------------------
# ゾンビ
# ------------------------------------------------------------
class Zombie:
    def __init__(self, x, y, speed_factor=1.0):
        self.x, self.y = x, y
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.4, 0.4)
        self.dir = 1
        self.state = "wander"
        self.speed_factor = speed_factor
        self.base_color = random.choice([3, 11, 4])
        self.bite_frame = 0
        self.captured_particles = []

    def update(self, player, obstacles, captured_zombies):
        px, py = player.x, player.y
        d = dist(self.x, self.y, px, py)

        if self.state == "captured":
            # 追従先はプレイヤーのtrail上の一定間隔
            try:
                index = captured_zombies.index(self)
            except ValueError:
                index = 0
            # 隊列のターゲット位置を計算
            target_index = min(len(player.trail) - 1, (index + 1) * FOLLOW_DISTANCE)
            target_pos = player.trail[target_index]
            tx, ty = target_pos

            td = dist(self.x, self.y, tx, ty)
            # 追従速度にも speed_factor を適用
            sp = 1.0 * self.speed_factor 

            if td > 1.0:
                self.vx = (tx - self.x) / td * sp
            
                # ゾンビがプレイヤーに追いつきすぎないように Y 軸方向の追従を調整
                if index == 0:
                   self.vy = (ty - self.y) / td * sp
                else:
                   # 追従距離に応じて緩やかに
                   self.vy = (ty - self.y) / td * sp * 0.8
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
        if d < PLAYER_R + ZOMBIE_R and self.state != "captured":
            self.state = "captured"
            self.vx = 0
            self.vy = 0
            for _ in range(random.randint(5, 10)):
                self.captured_particles.append(
                    [self.x, self.y, random.uniform(-1, 1), random.uniform(-1, -0.5), random.choice([7, 8, 3]), 30])
            return

        # プレイヤー追跡ロジック
        if d < 45:
            self.state = "follow"
            # 速度を更新する際の増分に self.speed_factor を適用
            self.vx += (px - self.x) / d * 0.1 * self.speed_factor
            self.vy += (py - self.y) / d * 0.1 * self.speed_factor
        else:
            self.state = "wander"
            if random.random() < 0.02:
                # 徘徊速度にも self.speed_factor を適用
                self.vx = random.uniform(-0.5, 0.5) * self.speed_factor
                self.vy = random.uniform(-0.5, 0.5) * self.speed_factor

        v_len = dist(0, 0, self.vx, self.vy)
        max_v = 1.0 * self.speed_factor # 最大速度にも speed_factor を適用
        if v_len > max_v and v_len != 0:
            self.vx *= max_v / v_len
            self.vy *= max_v / v_len

        nx = self.x + self.vx
        ny = self.y + self.vy

        blocked = any(ob.collide(nx, ny, ZOMBIE_R) for ob in obstacles)

        # 聖域境界での移動制限
        sanctuary_boundary = WINDOW_W - SANCTUARY_W
        if nx > sanctuary_boundary - ZOMBIE_R:
            if self.x <= sanctuary_boundary - ZOMBIE_R:
                self.vx = 0
            nx = self.x
            blocked = True

        if not blocked:
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
# フェード・シェイク
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
            # 修正: GAME_OVER ステートでフェードが停止した場合も update を実行しないことで
            # alphaが変化しないようにする。
            return
        
        if self.alpha < self.target:
            self.alpha = clamp(self.alpha + self.speed, 0.0, 1.0)
        elif self.alpha > self.target:
            self.alpha = clamp(self.alpha - self.speed, 0.0, 1.0)
            
        if abs(self.alpha - self.target) < 0.01:
            self.alpha = self.target
            self.active = False
            # 修正: alpha がターゲットに到達した場合、アクティブフラグを解除。

    def draw(self):
        if self.alpha <= 0.01:
            return
        
        # アルファ値に応じて黒い矩形を重ねて描画する
        layers = int(self.alpha * 8) + 1
        
        # 画面全体に半透明の黒を重ねることで、ゲーム画面を暗く見せる効果
        # この効果は、TIME UP/GAME OVER表示中に画面を少し暗く保つために使用します。
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
# メインゲーム
# ------------------------------------------------------------
class GameApp:
    def __init__(self):
        pyxel.init(WINDOW_W, WINDOW_H, title="DEMOCRACY OF THE DEAD")
        # パレット（簡易）
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
        self.stage = 0
        self.stage_start_frame = 0
        self.stage_time_limit = 0
        self.start_time_total = 0.0 
        self.cleared_count = 0  

        self.player = None
        self.players = []
        self.zombies = []
        self.obstacles = []
        self.dummy_players = []

        self.captured_zombies = []

        self.marching = False
        self.fade_outting = False
        self.next_stage_called = False

        self.final_scene_step = 0
        self.step_start_frame = 0
        self.ending_timer = 0
        self.credits_y = WINDOW_H
        self.credits_duration = 0
        for height, _, _ in CREDITS_CONTENT:
            self.credits_duration += height

        self.title_particles = [(random.randint(0, WINDOW_W), random.randint(0, 18), random.random() * 1.4) for _ in
                                     range(28)]

        # flags for end-flow and time-up
        self.final_gameover_started = False
        self.final_gameover_timer = 0
        self.total_clear_time = 0.0 
        # gameover_step: 0: 待機, 1: Time Up表示, 2: Game Over表示, 3: タイトルへフェードアウト
        self.gameover_step = 0 

        pyxel.run(self.update, self.draw)

    # ステージ生成 (Stage 1-5 および Stage 6(FINAL) の初期化を兼ねる)
    def spawn_stage(self):
        # 難易度係数を決定 (ゾンビ速度、プレイヤー速度、追従速度に使用)
        zombie_base_speed_factor = 1.0 + (self.cleared_count * 0.2)
        
        # タイムリミット設定 (クリア回数に応じた時間の短縮)
        # 0, St1, St2, St3, St4, St5, St6
        if self.cleared_count == 0:
            # 1周目
            tt = [0, 40, 35, 25, 25, 25, 20]
        elif self.cleared_count == 1:
            # 2周目: 全ステージ 20秒
            tt = [0, 20, 20, 20, 20, 20, 20]
        elif self.cleared_count == 2:
            # 3周目: 全ステージ 15秒
            tt = [0, 15, 15, 15, 15, 15, 15]
        else:
            # 4周目以降: 全ステージ 10秒 (最難関)
            tt = [0, 10, 10, 10, 10, 10, 10]
        
        # ステージ数をインクリメント
        self.stage += 1
        
        # --- Stage 6 (FINAL) の初期化ロジック (無限再帰を解消) ---
        if self.stage > MAX_STAGE_PLAY:
            self.stage = MAX_STAGE_PLAY + 1 # 確実に Stage 6 に設定
            # Stage 6 のタイムリミットを適用
            self.stage_time_limit = tt[self.stage] if self.stage < len(tt) else 0 
            
            self.obstacles = []
            
            # 障害物の生成 (13個)
            obstacle_count = FINAL_STAGE_OBSTACLES
            for _ in range(obstacle_count):
                w = random.randint(8, 22)
                h = random.randint(6, 14)
                x = random.randint(6, WINDOW_W - SANCTUARY_W - w - 6)
                y = random.randint(UI_HEIGHT + 6, WINDOW_H - h - 6)
                self.obstacles.append(Obstacle(x, y, w, h, color=4))

            # プレイヤー初期位置
            spawn_x, spawn_y = WINDOW_W // 4, WINDOW_H // 2
            # 障害物と重ならないように調整
            for _ in range(40): 
                if not any(o.collide(spawn_x, spawn_y, PLAYER_R + 2) for o in self.obstacles):
                    break
                spawn_x = random.randint(PLAYER_R + 4, WINDOW_W - SANCTUARY_W - PLAYER_R - 4)
                spawn_y = random.randint(UI_HEIGHT + PLAYER_R + 4, WINDOW_H - PLAYER_R - 4)

            self.players = []
            # メインプレイヤーに速度係数を渡す
            self.player = Player(spawn_x, spawn_y, is_main=True, speed_factor=zombie_base_speed_factor)
            self.players.append(self.player)

            self.dummy_players = []
            sanctuary_pos_x = WINDOW_W - SANCTUARY_W + 8
            # ダミープレイヤー（色で識別）を配置
            # ダミープレイヤーには速度係数を渡す必要はない（移動しないため）
            self.dummy_players = [
                Player(sanctuary_pos_x, WINDOW_H // 2 - 20, is_main=False, color_override=11), 
                Player(sanctuary_pos_x + 5, WINDOW_H // 2, is_main=False, color_override=7),  
                Player(sanctuary_pos_x, WINDOW_H // 2 + 20, is_main=False, color_override=8)  
            ]
            self.players.extend(self.dummy_players)

            self.zombies = []
            self.captured_zombies = []
            zombie_count = FINAL_STAGE_ZOMBIES # 30匹に設定
                
            for i in range(zombie_count):
                while True:
                    zx = random.randint(0, WINDOW_W - SANCTUARY_W - 6)
                    zy = random.randint(UI_HEIGHT, WINDOW_H - 1)
                    # プレイヤー初期位置から離れ、障害物と重ならない位置を探す
                    if dist(zx, zy, spawn_x, spawn_y) > 32 and not any(o.collide(zx, zy, ZOMBIE_R) for o in self.obstacles):
                        break
                    # ゾンビに難易度係数を渡す
                    sf = random.choice([0.8, 1.0, 1.3]) * zombie_base_speed_factor
                    self.zombies.append(Zombie(zx, zy, speed_factor=sf))
                    
            self.stage_start_frame = pyxel.frame_count
            self.state = "PLAYING" # Stage 6 はゾンビ捕獲から開始
            self.marching = False
            self.fade.to(0.0, speed=0.08)
            return 

        # --- 通常のステージ (Stage 1-5) のロジック ---
        # プレイ可能ステージのタイムリミット設定
        self.stage_time_limit = tt[self.stage]
        
        self.obstacles = []
        # 障害物の数を増やす
        obstacle_count = 3 + self.stage
        for _ in range(obstacle_count):
            w = random.randint(8, 22)
            h = random.randint(6, 14)
            # 聖域エリア（右端）には障害物を置かない
            x = random.randint(6, WINDOW_W - SANCTUARY_W - w - 6)
            y = random.randint(UI_HEIGHT + 6, WINDOW_H - h - 6)
            self.obstacles.append(Obstacle(x, y, w, h, color=4))

        # プレイヤー初期位置
        spawn_x, spawn_y = WINDOW_W // 4, WINDOW_H // 2
        for _ in range(40): 
            if not any(o.collide(spawn_x, spawn_y, PLAYER_R + 2) for o in self.obstacles):
                break
            spawn_x = random.randint(PLAYER_R + 4, WINDOW_W - SANCTUARY_W - PLAYER_R - 4)
            spawn_y = random.randint(UI_HEIGHT + PLAYER_R + 4, WINDOW_H - PLAYER_R - 4)

        self.players = []
        # メインプレイヤーに速度係数を渡す
        self.player = Player(spawn_x, spawn_y, is_main=True, speed_factor=zombie_base_speed_factor)
        self.players.append(self.player)
        self.dummy_players = [] # Stage 1-5 ではダミープレイヤーはいない

        self.zombies = []
        self.captured_zombies = []
        # ステージに応じてゾンビ数を増やす
        zombie_count = ZOMBIE_COUNT_BASE + (self.stage - 1) * 2 
            
        for i in range(zombie_count):
            while True:
                zx = random.randint(0, WINDOW_W - SANCTUARY_W - 6)
                zy = random.randint(UI_HEIGHT, WINDOW_H - 1)
                # プレイヤー初期位置から離れ、障害物と重ならない位置を探す
                if dist(zx, zy, spawn_x, spawn_y) > 32 and not any(o.collide(zx, zy, ZOMBIE_R) for o in self.obstacles):
                    break
            # ゾンビに難易度係数を渡す
            sf = random.choice([0.8, 1.0, 1.3]) * zombie_base_speed_factor
            self.zombies.append(Zombie(zx, zy, speed_factor=sf))

        # ステージが 1 の時だけ総プレイ時間をリセット
        if self.stage == 1:
            self.start_time_total = pyxel.frame_count / 60.0
            
        self.stage_start_frame = pyxel.frame_count
        self.state = "PLAYING"
        self.marching = False
        self.fade.to(0.0, speed=0.08)

    # エンディング演出開始
    def start_ending(self):
        # クリアタイムを計算
        self.total_clear_time = (pyxel.frame_count / 60.0) - self.start_time_total
        # 最終ステージクリア時のみ、クリア回数をインクリメント
        if self.stage == MAX_STAGE_PLAY + 1:
            self.cleared_count += 1 
            
        self.state = "ENDING"
        self.ending_timer = 0
        self.fade.to(1.0, speed=0.01)

    # UPDATE
    def update(self):
        # GAME_OVER ステートのステップ 1, 2 の間は、フェードを停止
        if self.state != "GAME_OVER" or self.gameover_step == 0 or self.gameover_step == 3:
             self.fade.update()
             
        self.shake.update()

        # ゾンビとプレイヤーの更新
        # GAME_OVER ステートのステップ 1, 2 の間は操作不可だが、背景の動きは継続させる
        controllable = (self.state == "PLAYING") 
        
        if self.state not in ["TITLE", "CREDITS_ROLL"]:
            for p in self.players:
                # 修正: GAME_OVER ステートのステップ 1, 2 の間は、プレイヤーは操作不可
                p_controllable = controllable and (self.state != "GAME_OVER")
                p.update(self.obstacles, controllable=p_controllable)
                
            for z in self.zombies:
                z.update(self.player, self.obstacles, self.captured_zombies)

        if self.state == "TITLE":
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.fade.to(1.0, speed=0.06)
                self.next_stage_called = True

            if self.next_stage_called and not self.fade.active and self.fade.alpha >= 0.99:
                self.next_stage_called = False
                self.stage = 0
                self.spawn_stage()

        elif self.state == "PLAYING":
            newly_captured = []
            for z in self.zombies:
                if z.state == "captured" and z not in self.captured_zombies:
                    newly_captured.append(z)

            for z in newly_captured:
                self.captured_zombies.append(z)
                self.shake.start(frames=4, intensity=1)

            # 全ゾンビ捕獲チェック
            if len(self.captured_zombies) == len(self.zombies) and len(self.zombies) > 0:
                self.state = "GO_TO_SANCT"
                self.start_march()

            # タイムリミットチェック (Stage 1-6 共通)
            elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
            if elapsed >= self.stage_time_limit and self.stage_time_limit > 0:
                # タイムアップでゲームオーバー処理へ移行
                self.state = "GAME_OVER"
                self.gameover_step = 1 # 1: Time Up表示へ直行
                self.final_gameover_timer = GAME_OVER_HOLD_FRAMES
                # 画面を少し暗くするフェードを開始 (半透明の黒)
                self.fade.to(0.5, speed=0.03) 

        elif self.state == "GO_TO_SANCT":
            self.update_march()

            sanctuary_x_min = WINDOW_W - SANCTUARY_W

            # プレイヤーと捕獲ゾンビが聖域に到達したか
            all_in_sanctuary = all(p.x >= sanctuary_x_min for p in self.players if p.is_main) and \
                               all(z.x >= sanctuary_x_min for z in self.captured_zombies)

            if all_in_sanctuary and not self.fade_outting:
                self.marching = False
                self.fade.to(1.0, speed=0.01)
                self.fade_outting = True

            if self.fade_outting and not self.fade.active and self.fade.alpha >= 0.99:
                self.fade_outting = False
                # 最終ステージ行進完了時はエンディングへ
                if self.stage == MAX_STAGE_PLAY + 1:
                    self.start_ending()
                else:
                    self.spawn_stage() # 次のステージへ

        elif self.state == "ENDING":
            if self.ending_timer == 0:
                self.fade.to(0.0, speed=0.08)

            self.ending_timer += 1

            # 変異演出（ダミーキャラがフラッシュ → ゾンビ化）
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
                    z.x = -100 # 捕獲ゾンビは画面外へ

            # 変異演出後、クレジットロールへ自動遷移
            if self.ending_timer > TRANSFORM_DURATION + 90:
                self.state = "CREDITS_ROLL"
                self.credits_y = WINDOW_H
                self.step_start_frame = pyxel.frame_count
                self.fade.to(0.0, speed=0.015)

        elif self.state == "CREDITS_ROLL":
            # クレジットをスクロール
            self.credits_y -= CREDITS_SPEED

            # すべてのクレジットが表示され、画面外へ出たらフェードアウト開始
            if self.credits_y < -(self.credits_duration):
                self.fade.to(1.0, speed=0.015) # 画面を黒くする
                
                # 画面が完全に黒くなったらタイトルへ戻る
                if self.fade.alpha >= 0.99: 
                    self.stage = 0
                    self.state = "TITLE"
                    self.fade.to(0.0, speed=0.06) # タイトル画面へフェードイン

        elif self.state == "GAME_OVER":
            # gameover_step: 1: Time Up表示, 2: Game Over表示, 3: タイトルへフェードアウト
            
            if self.gameover_step == 1:
                # Time Up表示 (タイマーを減らす)
                self.final_gameover_timer -= 1
                if self.final_gameover_timer <= 0:
                    self.gameover_step = 2  # Game Over表示へ
                    self.final_gameover_timer = GAME_OVER_HOLD_FRAMES

            elif self.gameover_step == 2:
                # Game Over表示 (タイマーを減らす)
                self.final_gameover_timer -= 1
                if self.final_gameover_timer <= 0:
                    self.gameover_step = 3 # タイトルへフェードアウト開始
                    # 修正: ここで画面全体を覆う黒へのフェードアウトを開始
                    self.fade.to(1.0, speed=0.03) 

            elif self.gameover_step == 3:
                # フェードアウト完了を待つ
                if not self.fade.active and self.fade.alpha >= 0.99:
                    # タイトルへ自動遷移
                    self.stage = 0
                    self.state = "TITLE"
                    self.fade.to(0.0, speed=0.06) # タイトル画面へフェードイン開始


    def start_march(self):
        self.marching = True
        for p in self.players:
            p.walk_frame = 0

    def update_march(self):
        if not self.marching:
            return

        tx = WINDOW_W - SANCTUARY_W + 2

        # 行進速度にもプレイヤーの速度係数を適用
        march_speed = PLAYER_SPEED * 1.5 * self.player.speed_factor 

        # プレイヤーとゾンビを行進させる
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
        elif self.state in ("PLAYING", "GO_TO_SANCT", "GAME_OVER"): # GAME_OVER時もゲーム画面を描画
            pyxel.clip(0, UI_HEIGHT, WINDOW_W, WINDOW_H - UI_HEIGHT)
            pyxel.camera(ox, oy)

            self.draw_playing()

            pyxel.camera(0, 0)
            pyxel.clip()
            self.draw_ui()
            
            # GAME_OVER ステートなら、ゲーム画面とUIの上に文字を表示
            if self.state == "GAME_OVER":
                 # 修正: GAME_OVER ステート時も fade.draw() を呼び出し、その後に文字を描画
                 # これにより、ゲーム画面を暗くした状態（半透明の黒）の上に文字を重ねて表示します。
                 self.fade.draw()
                 self.draw_game_over() 
            
        elif self.state == "ENDING":
            pyxel.cls(0)
            pyxel.camera(0, 0)
            self.draw_ending_scene()
        elif self.state == "CREDITS_ROLL":
            pyxel.cls(0)
            pyxel.camera(0, 0)
            self.draw_credits_roll()
            
        # 最終的な黒フェード（タイトル遷移時など）は、他の描画が終わった後に実行
        # ただし、GAME_OVER ステートのステップ 1, 2 では既に draw_game_over 内で draw() を呼び出しているので、
        # 重複を避けるためにここでの呼び出しは、タイトルへ戻るフェーズに限定する
        if self.state != "GAME_OVER" and self.state != "TITLE" and self.fade.alpha > 0.01:
             self.fade.draw()


    def draw_title_logo(self, cx, cy):
        pyxel.text(cx - 34, cy - 12, "DEMOCRACY", 8)
        pyxel.text(cx - 6, cy + 0, "OF THE DEAD", 8)
        for i in range(6):
            bx = cx - 34 + i * 12 + (pyxel.frame_count % 6)
            by = cy + 18 + (i % 3)
            if pyxel.frame_count % (6 + i) < 4:
                pyxel.pset(bx, by, 8)
                pyxel.pset(bx + 1, by + 1, 8)
                
        # 周回モード表示
        if self.cleared_count > 0 and self.state == "TITLE":
            s = f"CLEARED: {self.cleared_count} TIMES"
            pyxel.text(WINDOW_W // 2 - len(s) * 2, 45, s, 8)
            # 速度係数を取得して表示
            speed_factor_display = 1.0 + self.cleared_count * 0.2
            s_hard = f"SPEED: x{speed_factor_display:.1f}"
            pyxel.text(WINDOW_W // 2 - len(s_hard) * 2, 55, s_hard, 7)


    def draw_playing(self):
        sanctuary_x = WINDOW_W - SANCTUARY_W

        # 地面
        for y in range(UI_HEIGHT + 10, WINDOW_H, 12):
            pyxel.line(0, y, WINDOW_W - SANCTUARY_W, y, 9)

        # 聖域エリア
        pyxel.rect(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 10)
        pyxel.rectb(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 12)

        for ob in self.obstacles:
            ob.draw()

        # エンティティをY座標順に描画
        entities = list(self.players) + list(self.zombies)
        entities.sort(key=lambda e: e.y)
        for e in entities:
            e.draw()

        if self.state == "GO_TO_SANCT":
            s = "GO TO SANCTUARY!"
            pyxel.text((WINDOW_W - len(s) * 4) // 2, WINDOW_H - 14, s, 2)
            
    def draw_ending_scene(self):
        # 変異前の捕獲ゾンビは非表示
        entities = [p for p in self.players if p.is_main or p in self.dummy_players] 
        entities.sort(key=lambda e: e.y)

        # 聖域エリア
        sanctuary_x = WINDOW_W - SANCTUARY_W
        pyxel.rect(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 10)
        pyxel.rectb(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 12)

        for e in entities:
            e.draw()
            
        # 演出完了後
        if self.ending_timer > TRANSFORM_DURATION:
            s = "DEMOCRACY ELECTION ENDED"
            pyxel.text((WINDOW_W - len(s) * 4) // 2, WINDOW_H // 2 + 10, s, 7)
            
            # クリアタイム表示
            s_time = f"TOTAL TIME: {self.total_clear_time:.2f}s"
            pyxel.text((WINDOW_W - len(s_time) * 4) // 2, WINDOW_H // 2 + 20, s_time, 10)

    def draw_credits_roll(self):
        y = self.credits_y
        for height, text, color in CREDITS_CONTENT:
            if text:
                pyxel.text((WINDOW_W - len(text) * 4) // 2, y, text, color)
            y += height
            
    def draw_ui(self):
        pyxel.rect(0, 0, WINDOW_W, UI_HEIGHT, 0)

        # 最終ステージは「Stage: FINAL」と表示
        stage_text = f"Stage: {self.stage}/{MAX_STAGE_PLAY}"
        if self.stage == MAX_STAGE_PLAY + 1:
              stage_text = "Stage: FINAL"

        pyxel.text(4, 4, stage_text, 7)
        
        captured_count = len(self.captured_zombies)
        pyxel.text(4, 12, f"Captured: {captured_count}/{len(self.zombies)}", 7)

        # 時間表示ロジック (Stage 1-6 共通)
        elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
        time_left = max(0.0, self.stage_time_limit - elapsed)
        
        time_text = f"Time: {time_left:.1f}s"
        t_x = WINDOW_W - len(time_text) * 4 - 4
        
        # タイムリミットが近い場合 (10秒未満) は赤く表示
        color = 8 if time_left < 10 else 7
        
        pyxel.text(t_x, 8, time_text, color)
            
            
    def draw_title(self):
        pyxel.cls(0)
        self.draw_title_logo(WINDOW_W // 2 - 8, 22)
        for i, (px, py, spd) in enumerate(self.title_particles):
            ny = (py + (pyxel.frame_count % 40) * spd) % 30
            pyxel.pset(px, ny + 10, 8 if (pyxel.frame_count + i) % 15 < 7 else 4)
        pyxel.text(WINDOW_W // 2 - 46, 86, "- PRESS ENTER TO START -", 7)
        pyxel.text(10, 102, "(C) Y.Kusanagi", 13)
        pyxel.text(10, 112, "Game Assembly by (C) M.Takahashi", 13)

    def draw_game_over(self):
        # 画面中央にテキストを描画
        text_y = WINDOW_H // 2 - 8
        
        if self.gameover_step == 1:
            s = "TIME UP!"
            # 画面中央に赤色のテキストを描画 (影付き)
            pyxel.text((WINDOW_W - len(s) * 4) // 2 - 1, text_y - 1, s, 0) # 影
            pyxel.text((WINDOW_W - len(s) * 4) // 2, text_y, s, 8)
        
        elif self.gameover_step == 2:
            s = "GAME OVER"
            # 画面中央に点滅する赤色のテキストを描画 (影付き)
            color = 8 if pyxel.frame_count % 30 < 15 else 9 # 赤とオレンジで点滅
            
            pyxel.text((WINDOW_W - len(s) * 4) // 2 - 1, text_y - 1, s, 0) # 影
            pyxel.text((WINDOW_W - len(s) * 4) // 2, text_y, s, color)
        
# ------------------------------------------------------------
# アプリケーションの実行
# ------------------------------------------------------------
if __name__ == "__main__":
    GameApp()