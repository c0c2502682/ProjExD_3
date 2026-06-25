import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (0, 0):   img,
        (+5, 0):  img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5):  pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0):  img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5):  pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(0, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.center = bird.rct.center
        self.vx, self.vy = bird.dire
        self.vx = int(self.vx * 1.5)
        self.vy = int(self.vy * 1.5)

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(500, WIDTH-100), random.randint(100, HEIGHT-100)
        self.vx, self.vy = random.choice([-5, +5]), random.choice([-5, +5])

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


# 🎯 講義資料p39：Explosion（爆発エフェクト）クラス
class Explosion:
    def __init__(self, bomb: Bomb):
        self.img0 = pg.image.load("fig/explosion.gif")
        self.img = self.img0
        self.rct = self.img.get_rect()
        self.rct.center = bomb.rct.center
        self.life = 20  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        self.life -= 1
        # 時間経過で画像を交互に反転させてアニメーションを演出
        self.img = pg.transform.flip(self.img0, True, (self.life % 2 == 0))
        screen.blit(self.img, self.rct)


# 🎯 講義資料p38：Scoreクラス（青字・左下配置）
class Score:
    def __init__(self):
        self.fonto = pg.font.Font(None, 50)               # フォントの設定
        self.color = (0, 0, 255)                          # 文字色の設定：青
        self.score_val = 0                                # スコアの初期値の設定：0
        self.img = self.fonto.render(f"SCORE: {self.score_val}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)              # 画面左下座標

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"SCORE: {self.score_val}", 0, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    
    # 複数の爆弾
    bombs = [Bomb((255, 0, 0), 10) for _ in range(5)]
    
    # 🎯 講義資料p40-41：ビームと爆発群を「リスト」で管理（連射対応）
    beams: list[Beam] = []
    exps: list[Explosion] = []
    
    # 🎯 講義資料p38：Scoreインスタンスの生成
    score = Score()
    
    font_gameover = pg.font.Font(None, 80)
    clock = pg.time.Clock()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            # 🎯 スペースキーでビームをリストに「追加」して連射可能に
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))            
        
        screen.blit(bg_img, [0, 0])

        # 衝突判定（こうかとん vs 爆弾）
        for b_obj in bombs:
            if bird.rct.colliderect(b_obj.rct):
                bird.change_img(8, screen)
                txt_gameover = font_gameover.render("GAME OVER", True, (255, 0, 0))
                rct_gameover = txt_gameover.get_rect()
                rct_gameover.center = (WIDTH // 2, HEIGHT // 2)
                screen.blit(txt_gameover, rct_gameover)
                pg.display.update()
                time.sleep(3)
                return
            
        # 🎯 講義資料p40-41：総当たり衝突判定（ビーム群 vs 爆弾群）
        for i, beam_obj in enumerate(beams):
            hit_bomb = None
            for b_obj in bombs:
                if beam_obj.rct.colliderect(b_obj.rct):
                    hit_bomb = b_obj
                    break
            
            if hit_bomb is not None:
                bombs.remove(hit_bomb)       # 爆弾を消去
                exps.append(Explosion(hit_bomb)) # 🎯 爆発エフェクトを生成
                beams.pop(i)                 # 当たったビームを消去
                score.score_val += 1         # 🎯 倒したらスコアアップ（1点）
                break
                        
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # 🎯 すべてのビームの移動と画面外自動消去
        for i, beam_obj in enumerate(beams):
            beam_obj.update(screen)
            if check_bound(beam_obj.rct) != (True, True):
                beams.pop(i)
            
        for b_obj in bombs:
            b_obj.update(screen)
            
        # 🎯 すべての爆発エフェクトの更新と寿命消去
        for i, exp_obj in enumerate(exps):
            if exp_obj.life > 0:
                exp_obj.update(screen)
            else:
                exps.pop(i)
            
        # 🎯 講義資料p38：スコアの描画（画面左下に青字で表示、右上の古い黒文字は削除）
        score.update(screen)
    
        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()