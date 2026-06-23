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
    引数：こうかとんや爆弾，ビームなどのRect
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
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (0, 0):   img,  # 停止時
        (+5, 0):  img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5):  pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0):  img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5):  pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(0, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # 🎯 最後に移動した方向（デフォルトは右）を保持

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
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
            self.dire = tuple(sum_mv)  # 🎯 動いている方向を記録
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.center = bird.rct.center  # ビームの初期位置をこうかとんの中心にする
        
        # 🎯 こうかとんの移動方向（8方向）に合わせて速度ベクトルを設定
        self.vx, self.vy = bird.dire
        
        # 🎯 斜め移動のとき速度が速くなりすぎないよう調整（必要に応じて調整）
        # ビームの進行方向をわかりやすくするため、少し速度を速く（1.5倍）します
        self.vx = int(self.vx * 1.5)
        self.vy = int(self.vy * 1.5)

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        # こうかとんの初期位置(300, 200)と被らない位置に生成
        self.rct.center = random.randint(500, WIDTH-100), random.randint(100, HEIGHT-100)
        self.vx, self.vy = random.choice([-5, +5]), random.choice([-5, +5])

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    
    # 複数の爆弾（5個）を作成
    bombs = [Bomb((255, 0, 0), 10) for _ in range(5)]
    
    beam = None  # 初期状態ではビームは存在しない
    
    # 爆発エフェクト用の変数
    exp_tmr = 0
    exp_rct = None
    
    # スコア管理用
    score = 0
    font_score = pg.font.Font(None, 40)  # スコア用のフォント（サイズ40）
    
    # ゲームオーバー画面用
    font_gameover = pg.font.Font(None, 80)  # 「GAME OVER」用の大きいフォント（サイズ80）
    clock = pg.time.Clock()
    
    while True:
        # イベント処理ループ
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            # スペースキー押下でビームを新しく生成
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beam = Beam(bird)            
        
        screen.blit(bg_img, [0, 0])

        # すべての衝突判定を一元管理する安全な処理
        # すべての衝突判定を一元管理する安全な処理
        hit_bomb = None
        for b_obj in bombs:
            # 1. こうかとんと爆弾の衝突（ゲームオーバー）
            if bird.rct.colliderect(b_obj.rct):
                bird.change_img(8, screen)  # 泣いているこうかとんに切り替え
                

                # 「GAME OVER」の文字画像を生成
                txt_gameover = font_gameover.render("GAME OVER", True, (255, 0, 0))  # 赤色
                rct_gameover = txt_gameover.get_rect()
                rct_gameover.center = (WIDTH // 2, HEIGHT // 2)  # 画面のど真ん中に位置合わせ
                
                screen.blit(txt_gameover, rct_gameover)  # 画面中央に貼り付け
                pg.display.update()                     # 文字を表示するために画面を即時更新
                time.sleep(3)                           # 3秒間そのまま待つ
                
                return
            
            # 2. ビームと爆弾の衝突（ビームが存在するときのみ判定）
            if beam is not None and beam.rct.colliderect(b_obj.rct):
                hit_bomb = b_obj
                break
        
        # もしビームが爆弾に当たっていたら、安全にリストから消去してエフェクトを出す
        if hit_bomb is not None:
            exp_rct = hit_bomb.rct.copy()
            exp_tmr = 20            # 爆発タイマーセット
            bombs.remove(hit_bomb)  # リストから爆弾を消す
            beam = None             # ビームを消す
            score += 10             # スコアを10点加算
        # 各種アップデートと描画
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # ビームの移動と画面外判定
        if beam is not None:
            beam.update(screen)
            # 画面外に出たらビームを消滅させる
            if check_bound(beam.rct) != (True, True):
                beam = None
            
        # 爆弾の移動と描画
        for b_obj in bombs:
            b_obj.update(screen)
        
        # 爆発エフェクトの描画
        if exp_tmr > 0 and exp_rct is not None:
            pg.draw.circle(screen, (255, 165, 0), exp_rct.center, (21 - exp_tmr) * 3)
            exp_tmr -= 1

# スコアの文字画像を生成（文字列, 滑らかにするか, 色）
        txt_score = font_score.render(f"SCORE: {score}", True, (0, 0, 0))  # 黒色で描画
        screen.blit(txt_score, [WIDTH - 200, 30])  # 画面の右上（端から少し内側）に貼り付け
        
        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()