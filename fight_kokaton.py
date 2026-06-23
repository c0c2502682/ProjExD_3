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
        self.dire = (+5, 0)  # 最後に移動した方向（デフォルトは右）を保持

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
            self.dire = tuple(sum_mv)  # 動いている方向を記録
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
        
        # こうかとんの移動方向（8方向）に合わせて速度ベクトルを設定
        self.vx, self.vy = bird.dire
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


# 🎯 講義資料p39-41「Explosion（爆発）」クラスの実装
class Explosion:
    """
    爆弾が爆発したときのエフェクトに関するクラス
    """
    def __init__(self, bomb: Bomb):
        """
        爆弾の位置を基に爆発ビジュアルを初期化する
        """
        self.img0 = pg.image.load("fig/explosion.gif")
        self.img = self.img0
        self.rct = self.img.get_rect()
        self.rct.center = bomb.rct.center
        self.life = 20  # 爆発の表示時間（時間経過で消滅させるためのタイマー）

    def update(self, screen: pg.Surface):
        """
        爆発タイマーを減算し、時間を追うごとに画像を上下反転（交互変化）させて描画する
        """
        self.life -= 1
        # 1コマごとに上下反転させて爆発のダイナミックさを演出（資料の標準演出）
        self.img = pg.transform.flip(self.img0, True, (self.life % 2 == 0))
        screen.blit(self.img, self.rct)


# 🎯 講義資料p38「Scoreクラス」の完全実装
class Score:
    def __init__(self):
        """
        イニシャライザ：フォント、色、スコアの初期値、初期Surfaceと中心座標を設定する
        """
        self.fonto = pg.font.Font(None, 50)               # フォントの設定
        self.color = (0, 0, 255)                          # 文字色の設定：青
        self.score_val = 0                                # スコアの初期値の設定：0
        # 文字列Surfaceの生成
        self.img = self.fonto.render(f"SCORE: {self.score_val}", 0, self.color)
        self.rct = self.img.get_rect()
        # 文字列の中心座標：画面左下（横座標：100，縦座標：画面下部から50）
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示させる文字列Surfaceを生成し、スクリーンにblitする
        """
        self.img = self.fonto.render(f"SCORE: {self.score_val}", 0, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    
    # 複数の爆弾（5個）を作成
    bombs = [Bomb((255, 0, 0), 10) for _ in range(5)]
    
    # 🎯 講義資料p40-41：複数のビーム、爆発エフェクトを管理する「リスト」の初期化
    beams: list[Beam] = []
    exps: list[Explosion] = []
    
    # (初期化)Scoreインスタンスの生成
    score = Score()
    
    # ゲームオーバー用の大きなフォント
    font_gameover = pg.font.Font(None, 80)
    
    clock = pg.time.Clock()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            # 🎯 講義資料p40-41：スペースキーでビームを「リストに追加（連射対応）」
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))            
        
        screen.blit(bg_img, [0, 0])

        # 衝突判定（こうかとん vs 爆弾）
        for b_obj in bombs:
            if bird.rct.colliderect(b_obj.rct):
                bird.change_img(8, screen)
                
                # 「GAME OVER」の文字を画面中央に描画
                txt_gameover = font_gameover.render("GAME OVER", True, (255, 0, 0))
                rct_gameover = txt_gameover.get_rect()
                rct_gameover.center = (WIDTH // 2, HEIGHT // 2)
                screen.blit(txt_gameover, rct_gameover)
                
                pg.display.update()
                time.sleep(3)
                return
            
        # 🎯 講義資料p40-41：リスト化されたビーム群と爆弾群の「総当たり衝突判定」
        for i, beam_obj in enumerate(beams):
            hit_bomb = None
            for b_obj in bombs:
                if beam_obj.rct.colliderect(b_obj.rct):
                    hit_bomb = b_obj
                    break
            
            if hit_bomb is not None:
                bombs.remove(hit_bomb)       # 爆弾を消す
                # 🎯 講義資料p39：爆発インスタンスを生成してリストに追加
                exps.append(Explosion(hit_bomb))
                beams.pop(i)                 # 当たったビームを消す
                score.score_val += 1         # 爆弾を打ち落としたらスコアアップ（1点）
                break                        # ループのズレを防ぐため一度抜ける
                        
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # 🎯 講義資料p40-41：すべてのビームをアップデートし、画面外のものは自動削除
        for i, beam_obj in enumerate(beams):
            beam_obj.update(screen)
            if check_bound(beam_obj.rct) != (True, True):
                beams.pop(i)
            
        for b_obj in bombs:
            b_obj.update(screen)
            
        # 🎯 講義資料p39：すべての爆発エフェクトをアップデートし、寿命（life）が尽きたら削除
        for i, exp_obj in enumerate(exps):
            if exp_obj.life > 0:
                exp_obj.update(screen)
            else:
                exps.pop(i)
            
        # updateメソッドを呼び出してスコアを描画
        score.update(screen)
    
        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()