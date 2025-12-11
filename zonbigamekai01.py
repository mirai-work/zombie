# -*- coding: utf-8 -*-
"""
Tkinter ゾンビゲーム (Thonny などで動く) - 難易度上昇版

修正点:
1.  **ゾンビ生成ロジックの強化**: `reset_stage`内で、現在のステージとグローバル難易度 (ループレベル) に基づいて
    ゾンビの数を計算し、クリアするごとに着実に増加するようにしました。
2.  **旗の配置エリア制限**: HUD (画面上部のスコアやHPなどの文字表示) と旗が重ならないよう、
    上部120ピクセルを避けるロジックを維持しています。
"""

import tkinter as tk
import random
import math
import time

# --- ゲーム設定 ---
WINDOW_W = 640
WINDOW_H = 480
FPS = 30
TICK_MS = int(1000 / FPS)

STAGE_COUNT = 5 # 全ステージ数（これをクリアするとループレベルが上がる）

# --- 演出時間 (フレーム数) ---
TITLE_TIME = 10 * FPS     # 10秒
CLEAR_TIME = 10 * FPS     # 10秒
GAMEOVER_TIME = 3 * FPS   # 3秒
ENDING_TIME = 10 * FPS    # 10秒

# --- 難易度設定 ---
INITIAL_FLAGS = 3   
FLAG_INCREMENT = 2  

# ゾンビの基本数とステージごとの増加率
BASE_ZOMBIES = 15  
ZOMBIE_INCREASE_PER_STAGE = 10 
# ループレベルが上がるごとの乗数ボーナス
ZOMBIE_LOOP_MULTIPLIER = 1.8 

PLAYER_MAX_HP = 3 
INVINCIBILITY_FRAMES = 60 # 衝突後の無敵時間 (2秒)

# --- 速度調整 ---
PLAYER_SPEED = 5.0 
PLAYER_SIZE = 12

ZOMBIE_BASE_SPEED = 1.8 
ZOMBIE_SIZE = 12

# 色
BG_COLORS = ["#081218", "#1a0f1a", "#08121a", "#101814", "#21100e"]
PLAYER_COLOR = "#FF6666"
ZOMBIE_COLOR = "#2E8B57"
FLAG_COLOR = "#FFD54F"
HUD_COLOR = "#BFEFFF"
TEXT_COLOR = "#FFFFFF"

# ----------------------------
# ヘルパー
def clamp(v, a, b): return max(a, min(b, v))
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

# ----------------------------
# Agent 基底
class Agent:
    def __init__(self, x, y, size):
        self.x = float(x)
        self.y = float(y)
        self.size = size

# ----------------------------
# プレイヤー（人間）
class Player(Agent):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_SIZE)
        self.color = PLAYER_COLOR
        self.stamina = 100.0
        self.max_speed = PLAYER_SPEED
        self.collected_flags = 0
        self.hp = PLAYER_MAX_HP
        self.invincible_timer = 0
        self.angle = 0 # 演出用

    def update(self, keys, game_speed=1.0):
        # 1. 無敵タイマーの更新
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # 2. 移動入力
        vx = 0.0; vy = 0.0
        speed = self.max_speed * game_speed
        
        # プレイヤー移動ロジック
        if keys['left']: vx -= speed
        if keys['right']: vx += speed
        if keys['up']: vy -= speed
        if keys['down']: vy += speed

        # 3. 斜め移動の補正
        if abs(vx) > 0.01 and abs(vy) > 0.01:
            f = 1.0/math.sqrt(2); vx *= f; vy *= f

        # 4. スタミナ消費
        if abs(vx) > 0.01 or abs(vy) > 0.01:
            self.stamina = max(0.0, self.stamina - 0.6)
            if self.stamina < 30:
                vx *= 0.6; vy *= 0.6 # 低スタミナで速度を落とす
        else:
            self.stamina = min(100.0, self.stamina + 0.9)

        # 5. 純粋な移動
        half_size = self.size / 2
        
        self.x += vx
        self.y += vy
        
        # 境界チェック
        self.x = clamp(self.x, half_size, WINDOW_W - half_size)
        self.y = clamp(self.y, half_size, WINDOW_H - half_size)

    def draw(self, canvas):
        x = int(self.x); y = int(self.y)
        
        # 無敵時間中は点滅させる (描画をスキップ)
        if self.invincible_timer > 0 and (self.invincible_timer // 6) % 2 == 0:
             return 

        # プレイヤー描画
        # 頭
        canvas.create_oval(x-6, y-12, x+6, y-4, fill=self.color, outline="")
        # 体
        canvas.create_rectangle(x-5, y-4, x+5, y+8, fill="#AA5555", outline="")
        # 足
        canvas.create_line(x-3, y+10, x-3, y+16, fill="#442222", width=2)
        canvas.create_line(x+3, y+10, x+3, y+16, fill="#442222", width=2)
        # HUD circle if low stamina
        if self.stamina < 30:
            canvas.create_oval(x-8, y-14, x+8, y-2, outline="#FFFF88")

# ----------------------------
# ゾンビ
class Zombie(Agent):
    def __init__(self, x, y, kind="walker", difficulty_level=0):
        super().__init__(x, y, ZOMBIE_SIZE)
        self.kind = kind
        self.color = ZOMBIE_COLOR
        
        # 難易度ボーナスを考慮した基本速度
        # ループレベルが高いほどゾンビが速くなる
        base_speed = ZOMBIE_BASE_SPEED * (1.0 + difficulty_level * 0.1)
        
        if kind == "shambler":
            self.base_speed = base_speed * 0.7
        elif kind == "sprinter":
            self.base_speed = base_speed * 1.3
        else: # walker
            self.base_speed = base_speed * 1.0 
        self.phase = random.random()*10

    def update(self, target_x, target_y, game_speed=1.0):
        dx = target_x - self.x
        dy = target_y - self.y
        d = math.hypot(dx, dy) + 1e-6

        speed = self.base_speed * game_speed
        vx = (dx / d) * speed
        vy = (dy / d) * speed

        self.x += vx
        self.y += vy
        
        half_size = self.size / 2
        self.x = clamp(self.x, half_size, WINDOW_W - half_size)
        self.y = clamp(self.y, half_size, WINDOW_H - half_size)

    def draw(self, canvas):
        x = int(self.x); y = int(self.y)
        # head
        canvas.create_oval(x-6, y-12, x+6, y-6, fill="#8B6B44", outline="")
        # torso (ゾンビは少し汚れた色に)
        body_color = self.color if (x // 10 % 2) else "#449966"
        canvas.create_rectangle(x-5, y-6, x+5, y+6, fill=body_color, outline="")
        # legs (ragged)
        canvas.create_line(x-4, y+8, x-2, y+14, fill="#2E5D3E", width=2)
        canvas.create_line(x+4, y+8, x+2, y+14, fill="#2E5D3E", width=2)

# ----------------------------
# 旗（フラッグ）
class Flag:
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.collected = False

    def draw(self, canvas):
        if self.collected: return
        x = int(self.x); y = int(self.y)
        canvas.create_rectangle(x-4, y-8, x-2, y+8, fill="#BBB000", outline="")
        canvas.create_polygon(x-1, y-8, x+10, y-4, x-1, y, fill=FLAG_COLOR, outline="")

# ----------------------------
# ゲームクラス
class Game:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg=BG_COLORS[0], highlightthickness=0)
        self.canvas.pack()
        root.title("Zombie Escape (The Harder Horde) - Difficulty Scaling")

        # 状態
        # title, playing, stage_clear, game_over, ending
        self.state = 'title'  
        self.stage = 1
        self.score = 0
        self.high_score = 0 
        self.start_time = 0
        self.global_difficulty = 0 # ループレベル (0からスタート)
        self.frame_count = 0 # 各演出画面での経過フレーム

        # input (初期化時に全てのキー状態を False に設定)
        self.keys = {'left':False,'right':False,'up':False,'down':False}
        root.bind("<KeyPress>", self.on_key_down)
        root.bind("<KeyRelease>", self.on_key_up)
        root.bind("<space>", self.on_space)

        # world
        self.player = Player(40, WINDOW_H//2)
        self.zombies = []
        self.flags = []
        self.target_flags = 0 
        self.clear_bonus = 0 # ステージクリア時のスコアボーナス

        # 初期化
        self.reset_stage(initial=True)

        # main loop
        self.running = True
        self.frame = 0
        self.loop()

    # --- input ---
    def on_key_down(self, e):
        k = e.keysym.lower() # キーシンボルを小文字に統一
        if k in ('left','a'): self.keys['left'] = True
        if k in ('right','d'): self.keys['right'] = True
        if k in ('up','w'): self.keys['up'] = True
        if k in ('down','s'): self.keys['down'] = True

    def on_key_up(self, e):
        k = e.keysym.lower()
        if k in ('left','a'): self.keys['left'] = False
        if k in ('right','d'): self.keys['right'] = False
        if k in ('up','w'): self.keys['up'] = False
        if k in ('down','s'): self.keys['down'] = False

    def on_space(self, e):
        # 演出中にSPACEキーが押されたら強制スキップ
        if self.state == 'title':
            self.start_game()
        elif self.state == 'stage_clear':
            self.stage_next()
        elif self.state == 'game_over':
            self.reset_game()
        elif self.state == 'ending':
            self.start_new_loop()

    # --- 状態遷移ヘルパー ---
    def start_game(self):
        self.state = 'playing'
        self.start_time = time.time()
        self.frame_count = 0

    def stage_next(self):
        self.stage += 1
        if self.stage > STAGE_COUNT:
            self.state = 'ending'
            self.frame_count = 0
            # エンディング時にもハイスコアを更新
            self.high_score = max(self.high_score, self.score)
        else:
            self.reset_stage(initial=False)
            self.start_game()

    def reset_game(self):
        # ゲームオーバー時にハイスコアを更新
        self.high_score = max(self.high_score, self.score)
        
        self.state = 'title'
        self.stage = 1
        self.score = 0
        self.global_difficulty = 0 
        self.reset_stage(initial=True)
        self.frame_count = 0

    def start_new_loop(self):
        self.global_difficulty += 1
        self.reset_game()

    # --- stage reset ---
    def reset_stage(self, initial=False):
        """ステージの初期化。ゾンビの数をステージクリアごとに増やす"""

        # 1. パラメータの計算 (ゾンビ数の増加ロジック)
        
        # ステージ進行によるゾンビ数の増加 (加算)
        stage_zombies = BASE_ZOMBIES + (self.stage - 1) * ZOMBIE_INCREASE_PER_STAGE
        
        # ループレベルによるゾンビ数の増加 (乗算)
        loop_multiplier = ZOMBIE_LOOP_MULTIPLIER ** self.global_difficulty
        
        # 最終的なゾンビ数
        zcount = int(stage_zombies * loop_multiplier)
        zcount = int(min(zcount, 800)) # 最大ゾンビ数に制限
        
        self.target_flags = INITIAL_FLAGS + (self.stage - 1) * FLAG_INCREMENT
        
        # 2. ワールドのリセット
        self.canvas.configure(bg=BG_COLORS[(self.stage-1) % len(BG_COLORS)])
        self.flags = []
        self.zombies = []

        # 3. プレイヤーの配置と状態リセット
        px = random.randint(40, 120)
        py = random.randint(WINDOW_H//2 - 40, WINDOW_H//2 + 40)
        
        self.player.x = px
        self.player.y = py
        self.player.collected_flags = 0
        # ゲームオーバーからの復帰でない場合、HPは維持
        if initial:
            self.player.hp = PLAYER_MAX_HP
        self.player.invincible_timer = 0
        
        # 4. 旗の配置 (HUDエリアを避けるロジックを維持)
        
        # HUD表示エリアの制限 (上から120px、左右から40pxの領域は避ける)
        HUD_SAFE_MARGIN_Y_TOP = 120 
        HUD_SAFE_MARGIN_X = 40  
        
        placed = 0
        attempts = 0
        while placed < self.target_flags and attempts < 1000:
            attempts += 1
            # Xは画面端を避けてランダム
            fx = random.randint(HUD_SAFE_MARGIN_X, WINDOW_W - HUD_SAFE_MARGIN_X)
            # YはHUDエリアの下からランダム
            fy = random.randint(HUD_SAFE_MARGIN_Y_TOP, WINDOW_H - HUD_SAFE_MARGIN_X)
            
            # 1. プレイヤー初期位置から離す
            if dist((fx, fy), (px, py)) < 150: continue

            self.flags.append(Flag(fx, fy))
            placed += 1

        # 5. ゾンビの生成
        for i in range(zcount):
            zx = random.randint(WINDOW_W - 80, WINDOW_W - 20)
            zy = random.randint(20, WINDOW_H - 20)
            
            r = random.random()
            if r < 0.7: kind = "walker"
            elif r < 0.95: kind = "shambler"
            else: kind = "sprinter"
            
            # Zombie生成時に現在のループレベルを渡す (速度に影響)
            zombie = Zombie(zx, zy, kind, self.global_difficulty)
            self.zombies.append(zombie)
            
        print(f"STAGE {self.stage} (LOOP {self.global_difficulty + 1}): ZOMBIES={zcount}, FLAGS={self.target_flags}")


    # --- main loop ---
    def loop(self):
        if not self.running:
            return
        
        self.frame_count += 1
        self.frame += 1

        self.update()
        self.draw()
        
        self.root.after(TICK_MS, self.loop)

    def update(self):
        # 演出画面のタイマー制御
        if self.state == 'title' and self.frame_count >= TITLE_TIME:
            self.start_game()
        elif self.state == 'stage_clear':
            if self.frame_count < CLEAR_TIME:
                # スコアを徐々に加算するアニメーション
                target_score = self.score + self.clear_bonus
                remaining_frames = CLEAR_TIME - self.frame_count
                
                if remaining_frames > 0:
                    score_to_add = (target_score - self.score) // remaining_frames
                    self.score += max(1, score_to_add) # 最低1点加算
                
            elif self.frame_count >= CLEAR_TIME:
                self.stage_next()

        elif self.state == 'game_over':
            # ゲームオーバー時にハイスコアを更新
            self.high_score = max(self.high_score, self.score)
            if self.frame_count >= GAMEOVER_TIME:
                self.reset_game()
        
        elif self.state == 'ending':
             # エンディング時にハイスコアを更新
            self.high_score = max(self.high_score, self.score)
            if self.frame_count >= ENDING_TIME:
                self.start_new_loop()

        # プレイ中のロジック
        if self.state == 'playing':
            # player update 
            self.player.update(self.keys, game_speed=1.0)

            # zombies update & collision
            for z in self.zombies:
                z.update(self.player.x, self.player.y, game_speed=1.0)
                
                # 衝突判定
                if dist((z.x, z.y), (self.player.x, self.player.y)) < (z.size + self.player.size) / 2:
                    if self.player.invincible_timer == 0:
                        self.player.hp -= 1
                        self.player.invincible_timer = INVINCIBILITY_FRAMES
                        
                        if self.player.hp <= 0:
                            self.state = 'game_over'
                            self.frame_count = 0
                            return

            # flag pickup
            collected = 0
            for f in self.flags:
                if not f.collected:
                    if dist((self.player.x, self.player.y), (f.x, f.y)) < 14:
                        f.collected = True
                        self.player.collected_flags += 1
                        self.score += 500
                if f.collected: collected += 1

            # stage clear?
            if collected >= self.target_flags:
                elapsed = max(1.0, time.time() - self.start_time)
                # タイムボーナス
                self.clear_bonus = int(max(0, (60 - elapsed)) * 1000) 
                self.score += self.clear_bonus # クリア時に即時加算
                self.state = 'stage_clear'
                self.frame_count = 0
                return

    # --- draw ---
    def draw(self):
        self.canvas.delete("all")
        
        # --- TITLE SCREEN (10秒演出) ---
        if self.state == 'title':
            self.canvas.configure(bg="#000000")
            
            t = self.frame_count
            
            # メインタイトルアニメーション
            if t < TITLE_TIME:
                text_color = "#FFD54F" if (t//10)%2 == 0 else "#FFFFFF" 
                
                self.canvas.create_text(WINDOW_W//2, 80 + math.sin(t/15)*5, text="ZOMBIE ESCAPE:", fill=text_color, font=("Helvetica", 36, "bold"))
                self.canvas.create_text(WINDOW_W//2, 140 + math.sin(t/10)*8, text="THE HARDER HORDE", fill="#FF6666", font=("Helvetica", 24, "bold"))
                
                # サブテキスト (後半でフェードイン)
                if t > TITLE_TIME * 0.5:
                    self.canvas.create_text(WINDOW_W//2, 220, text=f"Loop Level: {self.global_difficulty + 1}", fill="#BFEFFF", font=("Helvetica", 14))
                    self.canvas.create_text(WINDOW_W//2, 260, text="Collect Flags, Survive the Swarm.", fill=TEXT_COLOR, font=("Helvetica", 18))
                    
                    # ハイスコア表示
                    self.canvas.create_text(WINDOW_W//2, 320, text=f"HIGH SCORE: {self.high_score}", fill="#FF66FF", font=("Helvetica", 20, "bold"))
                    
                    # クレジット表示 (タイトル演出の最後の部分で表示)
                    self.canvas.create_text(WINDOW_W//2, WINDOW_H - 20, text="(C)M.TAKAHASHI", fill="#999999", font=("Helvetica", 10))

                    # プレイヤーとゾンビのアニメーション
                    px = 120 + math.cos(t/20) * 10
                    py = 350 + math.sin(t/15) * 10
                    self.player.x = px
                    self.player.y = py
                    self.player.draw(self.canvas)
                    
                    for i in range(15):
                        z_x = (t * 2 + i * 40) % (WINDOW_W + 40)
                        z_y = 400 + math.sin((t+i*20)/30) * 5
                        zombie_color = "#2E8B57" if (t//5)%2 == 0 else "#1D5A37"
                        self.canvas.create_oval(z_x-6, z_y-12, z_x+6, z_y-6, fill="#8B6B44", outline="")
                        self.canvas.create_rectangle(z_x-5, z_y-6, z_x+5, z_y+6, fill=zombie_color, outline="")
                    
                    # 最後の点滅
                    if t > TITLE_TIME * 0.8 and (t // 5) % 2 == 0:
                        self.canvas.create_text(WINDOW_W//2, 400, text="PRESS SPACE", fill=FLAG_COLOR, font=("Helvetica", 24, "bold"))

            return

        # --- GAMEOVER SCREEN (3秒演出) ---
        if self.state == 'game_over':
            # 画面全体を赤くフラッシュ
            flash_color = "#FF0000" if (self.frame_count // 3) % 2 == 0 else "#440000"
            self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill=flash_color, outline="")
            
            # 激しく点滅するGAME OVER文字
            text_fill = "#FFFFFF" if (self.frame_count // 2) % 2 == 0 else "#FF3333"
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 - 20, text="GAME OVER", fill=text_fill, font=("Helvetica", 48, "bold"), angle=random.uniform(-1, 1))
            
            # スコアとハイスコアの表示
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 40, text=f"Final Score: {self.score}", fill="#FFD54F", font=("Helvetica", 18))
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 70, text=f"High Score: {self.high_score}", fill="#FF66FF", font=("Helvetica", 14))

            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 120, text=f"Returning to Title in {GAMEOVER_TIME/FPS - self.frame_count/FPS:.1f}s", fill=TEXT_COLOR, font=("Helvetica", 12))
            return
            
        # --- PLAYING / STAGE CLEAR / ENDING (通常描画とHUD) ---
        
        # playing or other - draw world
        bg = BG_COLORS[(self.stage-1) % len(BG_COLORS)]
        self.canvas.configure(bg=bg)

        # flags
        for f in self.flags:
            f.draw(self.canvas)

        # agents (zombies and player)
        all_agents = self.zombies + [self.player]
        all_agents_sorted = sorted(all_agents, key=lambda a: a.y)
        for a in all_agents_sorted:
            a.draw(self.canvas)

        # --- HUD ---
        # この領域には旗が配置されないことが保証されています (reset_stageで制限)
        display_diff = self.global_difficulty + 1
        self.canvas.create_text(WINDOW_W-8, 8, anchor='ne', text=f"HIGH SCORE: {self.high_score}", fill="#FF66FF", font=("Helvetica", 12, "bold"))
        self.canvas.create_text(WINDOW_W-8, 28, anchor='ne', text=f"LOOP LEVEL: {display_diff}", fill=HUD_COLOR, font=("Helvetica", 12))
        self.canvas.create_text(8, 8, anchor='nw', text=f"STAGE: {self.stage}/{STAGE_COUNT}", fill=HUD_COLOR, font=("Helvetica", 12))
        self.canvas.create_text(8, 28, anchor='nw', text=f"FLAGS: {self.player.collected_flags}/{self.target_flags}", fill=HUD_COLOR, font=("Helvetica", 12))
        self.canvas.create_text(8, 48, anchor='nw', text=f"SCORE: {self.score}", fill=HUD_COLOR, font=("Helvetica", 12))
        self.canvas.create_text(WINDOW_W-8, 48, anchor='ne', text=f"HORDE: {len(self.zombies)}", fill=HUD_COLOR, font=("Helvetica", 12))
        
        # HPの描画
        self.canvas.create_text(8, 68, anchor='nw', text="HP:", fill=HUD_COLOR, font=("Helvetica", 12))
        for i in range(PLAYER_MAX_HP):
            fill_color = PLAYER_COLOR if i < self.player.hp else "#333333"
            self.canvas.create_oval(35 + i * 20, 65, 45 + i * 20, 75, fill=fill_color, outline=PLAYER_COLOR, width=1)

        if self.state == 'playing':
            elapsed = int(time.time() - self.start_time)
            self.canvas.create_text(8, 88, anchor='nw', text=f"TIME: {elapsed}s", fill=HUD_COLOR, font=("Helvetica", 12))

        # --- STAGE CLEAR (10秒演出) ---
        if self.state == 'stage_clear':
            t = self.frame_count
            
            # 背景を明るくフラッシュさせる
            flash_intensity = max(0, 200 - t * 4) 
            flash_hex = f"#{flash_intensity:02x}{flash_intensity:02x}{flash_intensity:02x}"
            self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill=flash_hex, stipple="gray50", outline="")
            
            # メインタイトルアニメーション
            angle = t * 5 % 360 # 回転
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 - 50, text=f"STAGE {self.stage} ESCAPED!", fill="#FFD54F", font=("Helvetica", 32, "bold"), angle=angle)
            
            # スコアボーナス表示 (後半でフェードイン)
            if t > CLEAR_TIME * 0.3:
                # すでにスコアは加算されているので、アニメーションせずに表示
                bonus_text = f"TIME BONUS: +{self.clear_bonus}"
                self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 20, text=bonus_text, fill="#FFFFFF", font=("Helvetica", 18))

            # 次のステージ情報
            if t > CLEAR_TIME * 0.6:
                next_flags = INITIAL_FLAGS + self.stage * FLAG_INCREMENT
                
                # 次のゾンビ数計算
                stage_zombies = BASE_ZOMBIES + self.stage * ZOMBIE_INCREASE_PER_STAGE
                loop_multiplier = ZOMBIE_LOOP_MULTIPLIER ** self.global_difficulty
                next_zombies = int(stage_zombies * loop_multiplier)
                
                self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 60, text=f"Next: Stage {self.stage + 1} ({next_flags} Flags)", fill=HUD_COLOR, font=("Helvetica", 12))
                self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 80, text=f"Horde Size: {next_zombies} Zombies", fill="#FF6666", font=("Helvetica", 12))
                
                # スキップボタン
                if (t // 5) % 2 == 0:
                    self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 120, text="PRESS SPACE TO SKIP", fill="#FF6666", font=("Helvetica", 16))

        # --- ENDING SCREEN (10秒演出) ---
        if self.state == 'ending':
            t = self.frame_count
            self.canvas.configure(bg="#000000")
            
            # 巨大なタイトルが回転しながらフェードイン
            angle = t * 2 
            text_size = 48 + math.sin(t/30) * 10
            
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 - 60, text="VICTORY", fill="#FFD54F", font=("Helvetica", int(text_size), "bold"), angle=angle)
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 10, text="SURVIVAL ACHIEVED!", fill="#FFFFFF", font=("Helvetica", 24, "bold"))
            
            # スコア最終表示とハイスコア
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 80, text=f"FINAL SCORE: {self.score}", fill=HUD_COLOR, font=("Helvetica", 20))
            self.canvas.create_text(WINDOW_W//2, WINDOW_H//2 + 120, text=f"HIGH SCORE: {self.high_score}", fill="#FF66FF", font=("Helvetica", 16, "bold"))

            # 次のループへの示唆 (ゆっくり点滅)
            if t > ENDING_TIME * 0.5 and (t // 15) % 2 == 0:
                next_loop_level = self.global_difficulty + 2
                self.canvas.create_text(WINDOW_W//2, WINDOW_H - 40, text=f"PRESS SPACE FOR NEW GAME (LOOP LEVEL {next_loop_level})", fill="#FF6666", font=("Helvetica", 14, "bold"))

            # クレジット表示
            self.canvas.create_text(WINDOW_W//2, WINDOW_H - 20, text="(C)M.TAKAHASHI", fill="#999999", font=("Helvetica", 10))

# ----------------------------
# 実行
if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()