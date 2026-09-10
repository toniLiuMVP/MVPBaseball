#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ─────────────────────────────────────────────────────────
#  法律與免責(每一支本站腳本都帶著這一段)
#
#  · 本工具與 Electronic Arts 無任何官方關聯,也未經其授權或背書。
#    MVP Baseball 2005 為 Electronic Arts 之作品與商標。
#  · 本工具為原創程式碼,**不含任何 EA 的程式碼或資產**。
#  · 本工具不提供、不教學、也不包含任何規避技術保護措施的功能。
#  · 使用者應僅對自己合法取得的遊戲副本使用本工具,並自行承擔風險。
#    使用前請自行確認你與遊戲發行商之間的使用者授權合約(EULA)。
#  · 本工具按「現狀」提供,不附任何明示或默示的擔保。
#  · 授權:MIT(見檔尾)。教學文字另採 CC BY 4.0。
#  · 回報與下架:https://toniliumvp.github.io/MVPBaseball/report.html
#    三條管道,其中「直接向 GitHub 提出」不需經過維護者;
#    留言區那條不需要任何帳號。管道有變動只會改那一頁。
# ─────────────────────────────────────────────────────────

"""
mvp_ratings.py —— 把真實成績換算成遊戲裡的能力值。

    python3 mvp_ratings.py --demo                  看公式、誤差、以及配不出來的欄位
    python3 mvp_ratings.py --check "<遊戲資料夾>"   檢查你那份的資料夠不夠用
    python3 mvp_ratings.py --fit "<遊戲資料夾>"     用你自己那份重配一次並印出係數
    python3 mvp_ratings.py --convert stats.csv     把成績表換算成能力值
    python3 mvp_ratings.py --write "<遊戲資料夾>" ratings.csv          ← 預覽
    python3 mvp_ratings.py --write "<遊戲資料夾>" ratings.csv --apply  ← 真的寫
    python3 mvp_ratings.py --restore-write "<遊戲資料夾>"              ← 退回去
    python3 mvp_ratings.py --selftest              自我測試(不碰任何遊戲檔)

【這支跟別的換算工具哪裡不一樣】
公式**不是想出來的,是從這款遊戲自己出貨的資料配出來的**,而且誤差是量過的。

MVP Baseball 2005 出貨時同時附了每一位球員的真實成績與 EA 給他們的能力值,
兩邊用識別碼可以完全對上。所以「成績 → 能力值」有標準答案,不用猜。

【結論是分層的,不是「全部都能算」】

  ✅ 投手續航力 stamina ← 單季 IP/G
        測試 MAE 2.94 · 基準線 16.40 · R² 0.947 · 刻度 40~99
        ⚠️ 單季出賽 G 必須 ≥ 10。原版 1,430 個投手裡 826 人(58%)G = 0,
           對他們這條公式是除以零,不是估不準而是算不出來。

  ✅ 力量 power ← 同邊 SLG(長打率)
        對右投  −2.23 + 149.72 × SLG   MAE 3.34 · 基準 10.56 · R² 0.878
        對左投   9.00 + 127.12 × SLG   MAE 2.87 · 基準 10.84 · R² 0.914
        ⚠️ **同邊打席 TPA 必須 ≥ 100。** 低於 100 時這條公式比亂猜還糟,
           而且錯的方向是固定的:打席少的人碰巧打幾支長打,SLG 虛高,
           公式把替補灌成強打者。
        ⚠️ 左右要用各自的係數。把左側那條套到右側,誤差從 3.34 變 4.32。

  🟡 只有生涯成績時的退路(誤差約兩倍,不得已才用)
        power   25.17 + 464.91 × (HR/AB) + 146.67 × (R/AB)   MAE 7.75 · R² 0.66
        speed   59.52 + 279.60 × (SB/AB) + 91.43 × (R/AB) − 0.13 × √AB
                                                             MAE 7.38 · R² 0.46
        contact 30.90 + 204.96 × (R/AB)                      MAE 8.36 · R² 0.42

  ❌ 配不出來:守備 fielding、選球 platediscipline、守備範圍 range、
     臂力 throwstrength、耐久 durability。
     **這支工具不會給你這些欄位的數字。給了就是編的。**

【⚠️ 你那份遊戲的資料可能不夠】
分項成績(lhbstats / rhbstats / pstats)是配 power 與 stamina 的原料。
**剛安裝好的原版有資料**(rhbstats 非零 18.4%、380 人 TPA ≥ 100),
但**被模組洗過的副本可能整片是空的** —— 本站測試機那份是 0.0%、只剩 1 人。
先跑 --check 看你那份是哪一種。

【輸入是什麼、輸出是什麼】
  · --check / --fit / --write / --restore-write 吃的是**遊戲資料夾**,
    真正讀寫的只有它底下的 data/database/*.dat。那些是純文字名單,
    不是二進位檔:第一行是表頭,之後每一行一位球員,格子的形狀是「欄號 值」。
  · --convert 吃一張 CSV,必須有 id / first_name / last_name 三欄;
    成績欄位有多少給多少(tpa slg g ipg ab hr r sb)。
    輸出另一張 CSV:那三欄再加上六個能力值欄位
    (stamina / power_vs_rhp / power_vs_lhp / power / speed / contact)。
    **空白的格子代表守門沒過,不是算出 0。**
  · --write 吃的就是 --convert 產生的那張 CSV,靠 id 跟遊戲名單配對。
    六欄之中只有四欄寫得回去(見 WRITE_MAP),power 與 contact 只出現在 CSV 裡。

【安全網在哪】
  · 預設不寫:--write 沒加 --apply 就只印預覽,一個位元組都不動。
  · 一個對不上就整批不寫:CSV 裡任何一個 id 在名單裡找不到,整批放棄。
  · 值不是 0~100 的整數也整批不寫:帶逗號的值(Excel 有些地區設定會把
    8.0 存成「8,0」)會把名單的一格拆成兩格,本站實測同一列的 first_name
    從 Default 變成空的。所以這一關擋在寫之前,不是寫完再驗。
  · 自動備份:第一次寫某個檔之前先複製成「原檔名.ratingsbak」,
    而且複製是先寫一顆**名字事先猜不到的暫存檔**(tempfile.mkstemp,
    開在同一個資料夾裡)再 os.replace,不會留下半截備份。
  · 寫檔也是原子的:先寫暫存檔、fsync、把原本的權限抄回來、再 os.replace 換過去。
  · **名單檔或備份檔如果是符號連結,整個停下來不寫。** 跟著連結寫會改到
    遊戲資料夾外面的檔案 —— 而且 os.path.exists() 對「指向不存在目標的
    符號連結」回 False,所以這裡一律用 lexists / islink 判斷。
    要改的每一個檔(名單檔與它的備份檔)都是在**動第一個位元組之前**一次驗完的,
    不是輪到哪個檔才驗那個檔;不然排在最後的那一個是連結時,
    前面幾個早就已經改掉了,「整個停下來不寫」就是一句假話。
  · **--convert 產生的那張 CSV 也一樣**:目的檔是符號連結就不寫,而且是
    先寫暫存檔再原子換名(不是 open(out, 'w') 直接開),**換名之前會再驗一次** ——
    因為第一次驗到真的寫出去中間隔著讀檔與計算,那段時間裡冒出來的連結會被跟著寫。
  · 四個檔之間沒有交易可言,所以寫到一半失敗時會告訴你**哪幾個已經改了**,
    並且叫你跑 --restore-write,不會只丟一段英文錯誤堆疊。
  · 寫完自己把檔案讀回來逐項比對,對不上就叫你還原。
  · --restore-write 把備份蓋回去,而且**還原本身也是原子的**
    (先寫暫存檔、fsync、**整顆 sha256 跟備份對過**,才換名 ——
     既不會在途中把正本截成 0 bytes,也不會換上一顆內容對不起來的檔)。
  · 中途按 Ctrl-C:會照實講「什麼都沒有動到」、「哪幾個已經改了」、
    「哪幾個已經還原了」,還是「中斷的時候正在替換哪一個」,
    結束碼是 130 不是 0。
    ⚠️ 「什麼都沒有動到」只有 --write 那條路講得出口。跑 --restore-write
    卻一個檔都還沒還原時講的是「**這一趟沒有還原到任何檔**,你的遊戲檔
    還停在改過的狀態,再跑一次」—— 會來還原的人正是因為檔案被改過才來的,
    對他說「什麼都沒有動到」會害他不再回頭還原。
    **換名跟「記下已經換過」是綁在一起的一段不可中斷的動作**,
    所以帳本跟磁碟上的狀態不會對不起來(舊版有這個縫:換完名還沒登記時
    按下去,畫面會說「什麼都沒有動到」而檔案其實已經換過去了)。
    還原前先驗備份:0 bytes、表頭讀不出來、最後一列被截斷、
    列數比現在那個檔少或欄數對不上,四種都拒絕;
    備份全部被拒絕時會說「一個都沒還原」,不會反過來說「你還沒寫過」。

【這支不做的事】
  · 不新增球員、不改名字背號、不動 .sav 存檔、不碰任何二進位封裝檔。
  · 守備 / 選球 / 守備範圍 / 臂力 / 耐久這五欄,本站配不出來就不給數字。
  · 不會告訴你改完在遊戲裡的手感如何。本站沒有實機驗過那件事。

法律與免責
    本教學與本腳本與 Electronic Arts 無任何官方關聯,不含 EA 的程式碼或資產,
    也不含任何規避技術保護措施的功能。僅供你對**自己合法取得的副本**使用,
    風險自負。本軟體按現狀提供,不附任何擔保。

—— toni的MVP模組補習班
"""

import argparse
import csv
import hashlib
import io
import math
import os
import shutil
import signal
import statistics
import sys
import tempfile

# ── 本站配出來的係數(2026-08-29)────────────────────────────
# 來源:剛安裝好的原版。誤差全部是**測試集**上的平均絕對誤差
# (依識別碼排序後每 5 筆取 1 筆當測試),不是訓練集。
# ⚠️ 這些數字是跑 --fit 印出來貼進來的,不是手寫的。隨時可以自己重跑對照。
#
# 每一條的欄位怎麼讀:
#   terms    [(自變數名, 係數)]。'const' 是截距,compute() 會把它當成永遠是 1 的自變數,
#            所以整條公式就是把清單裡的每一項相乘再相加,不必為截距寫特例。
#   clamp    (下限, 上限)。**這不是遊戲的合法範圍,是 EA 在這批資料裡實際給過的範圍。**
#            算出來落在外面代表外插了,會夾住並且明白告訴使用者「這個值不可信」。
#   mae      測試集上的平均絕對誤差。baseline 是「一律猜訓練集裡同一個值」的誤差,
#            兩個要並排看:公式沒有明顯贏過 baseline 就等於沒用。
#            ⚠️ **存在這一欄的數字是「猜平均數」那個版本。** 中位數才是讓 MAE
#            最小的常數,所以猜中位數的基準一定比較低(15.83 / 10.09 / 10.73)。
#            --fit 兩個都印,就是為了讓這一欄可以照著重跑對照,而不是二選一。
#   needs    人看的前置條件,--demo 會照著印。真正把關的是下面的 GUARDS。
BEST = {
    'stamina': {
        'terms': [('const', 39.2055), ('ipg', 8.0350)],
        'clamp': (40, 99), 'mae': 2.94, 'baseline': 16.40, 'r2': 0.947,
        'needs': '單季 IP 與 G(pstats.dat)· G 必須 ≥ 10',
    },
    'power_vs_rhp': {
        'terms': [('const', -2.2303), ('slg', 149.7194)],
        'clamp': (41, 96), 'mae': 3.34, 'baseline': 10.56, 'r2': 0.878,
        'needs': '對右投的分項成績(rhbstats.dat)· 同邊 TPA 必須 ≥ 100',
    },
    'power_vs_lhp': {
        'terms': [('const', 9.0026), ('slg', 127.1211)],
        'clamp': (44, 95), 'mae': 2.87, 'baseline': 10.84, 'r2': 0.914,
        'needs': '對左投的分項成績(lhbstats.dat)· 同邊 TPA 必須 ≥ 100',
    },
}

# 退路:只有生涯累積成績、拿不到分項成績時才用。欄位的意義跟 BEST 完全一樣。
# ⚠️ 誤差大約是 BEST 的兩倍,而且 contact 與 speed 的 R² 只有 0.4 上下 ——
#    那代表大部分的變異這條公式解釋不了。當它是「總比亂填好」,不是「算得準」。
#    hr_rate / r_rate / sb_rate 都是**除以生涯 AB** 的比率,sqrt_ab 是生涯 AB 開根號。
#    sqrt_ab 的係數是負的,代表在這批資料裡打數累積愈多的人速度值傾向愈低;
#    那是配出來的趨勢,本站沒有去追它背後的原因。
FALLBACK = {
    'power': {
        'terms': [('const', 25.1696), ('hr_rate', 464.9088), ('r_rate', 146.6668)],
        'clamp': (6, 98), 'mae': 7.75, 'baseline': 14.04, 'r2': 0.66,
        'needs': '生涯 AB / HR / R · AB 必須 ≥ 200',
    },
    'speed': {
        'terms': [('const', 59.5244), ('sb_rate', 279.5962), ('r_rate', 91.4349),
                  ('sqrt_ab', -0.1324)],
        'clamp': (41, 96), 'mae': 7.38, 'baseline': 10.46, 'r2': 0.46,
        'needs': '生涯 AB / SB / R · AB 必須 ≥ 200',
    },
    'contact': {
        'terms': [('const', 30.9020), ('r_rate', 204.9604)],
        'clamp': (6, 89), 'mae': 8.36, 'baseline': 10.67, 'r2': 0.42,
        'needs': '生涯 AB / R · AB 必須 ≥ 200',
    },
}

# 配不出來的五欄,以及各自的理由。
# ⚠️ 這張表不是「還沒做」的待辦,它是**主動拒絕**的清單:compute() 一看到這些欄位
#    就直接丟 Stop,連公式都不會去找。理由要留在程式裡,是因為使用者一定會問
#    「為什麼別的工具給得出來」,而答案是那些數字沒有來源。
CANNOT = {
    'fielding': '所有自變數的 R² 都 ≤ 0.05,而且 EA 給的值(剛安裝好的原版)範圍 2~15、標準差 2.6—— 幾乎每個人一樣,配出來也沒有意義。',
    'platediscipline': '最好的自變數(得分率)R² 只有 0.14。',
    'range': '同守備,原版值域 2~15、標準差 2.6 而且高度集中。',
    'throwstrength': '出貨資料裡沒有任何跟臂力有關的成績。',
    'durability': '出貨資料裡沒有出賽傷停的紀錄。',
}

# 守門條件:欄位 -> (要看 stats 裡的哪一個鍵, 最低值, 給人看的名字)。
# ⚠️ 低於門檻時**不是估不準,是錯的方向固定**:打席少的人碰巧打幾支長打,
#    SLG 就虛高,公式會把替補灌成強打者。所以這裡不是印警告然後照給,
#    是直接拒絕輸出(compute() 丟 Stop)。這是本工具跟其他換算器最大的差別。
GUARDS = {
    'stamina': ('g', 10, '單季出賽 G'),
    'power_vs_rhp': ('tpa', 100, '對右投的打席 TPA'),
    'power_vs_lhp': ('tpa', 100, '對左投的打席 TPA'),
    'power': ('ab', 200, '生涯打數 AB'),
    'speed': ('ab', 200, '生涯打數 AB'),
    'contact': ('ab', 200, '生涯打數 AB'),
}


# 全腳本唯一的例外型別。凡是「本站不敢往下做」的情況都丟它,
# 由 __main__ 統一接住印成一行人話並回傳 exit code 1。
class Stop(Exception):
    pass


# 真的做過 os.replace 的檔案清單。**只有在這裡登記過的檔才算被動過。**
# 用途只有一個:Ctrl-C 之後要能誠實回答「我的遊戲檔現在是什麼狀態」。
# 空的才敢講「什麼都沒有動到」;不空就要講「已經改了,用 --restore-write 退」。
# 2026-09-05 加:在這之前 Ctrl-C 走的是一般失敗那條路,印一行英文然後 exit 1,
# 使用者看不出來自己按下去的那一刻檔案換過去了沒有。
#
# 2026-09-06 加第三態 'replacing'。帳本只有兩態的時候有一個縫:
# os.replace 換完了、還沒把檔名 append 進去之前,Ctrl-C 剛好落在那兩行中間,
# 收尾就會照著空的清單說「什麼都沒有動到」—— 而磁碟上那個檔已經是新的了。
# 本站在拋棄式副本上重現過(換名之後補一個 SIGINT):舊版印「什麼都沒有動到」,
# 同一時間 rhattrib.dat 的 sha256 已經變了。**那是一句假話,而且會害人不去還原。**
# 現在換名跟登記綁成一段不可中斷的動作(見 _NoInterrupt),這個縫幾乎不會發生;
# 'replacing' 是萬一 _NoInterrupt 裝不上(非主執行緒)時的第二層保險。
#   ''         還沒動任何檔
#   '<檔名>'   正在換這一個檔,換過去了沒有不確定
#   write / restore 裡有名字  那些檔確定已經換過去了
#
# 2026-09-11 加 'cmd'(這一趟在做什麼:'write' / 'restore' / '')。理由:
# 「一個檔都還沒換過去」在 --write 那條路上等於「你的遊戲檔什麼都沒有動到」,
# 在 --restore-write 那條路上**卻是相反的意思** —— 會跑還原的人正是因為
# 檔案被改過才來的,一個都還沒還原代表他的檔案還停在改過的狀態。
# 少了這一格,收尾就會對一個正在搶救檔案的人印「什麼都沒有動到」,
# 害他不再回頭還原(跟 cmd_restore_write 裡那段「不可以說『你還沒用 --write 寫過』」
# 是同一個坑,只差一個分支)。
_TOUCHED = {'write': [], 'restore': [], 'gamedir': '', 'replacing': '', 'cmd': ''}


# 把兩張公式表併成一張查詢用的字典。
# 順序有意義:BEST 先放,FALLBACK 後放,所以同名的鍵會以 BEST 為準。
# (目前兩邊沒有同名鍵,這樣寫是為了以後加公式時預設走比較好的那一條。)
def all_formulas():
    d = dict(BEST)
    d.update(FALLBACK)
    return d


def compute(field, **stats):
    """回傳 (值, 警告)。守門不過就丟 Stop —— **不會給你一個看起來合理的數字**。

    這是整支腳本的核心,別的地方(--demo / --convert)都只是餵資料給它。
    五道關卡照順序:配不出來的欄位 → 不認得的欄位 → 沒給守門要看的成績 →
    低於門檻 → 自變數不齊。全部過了才算,算完再夾範圍。
    stats 用關鍵字參數收,鍵名就是 terms 裡的自變數名(tpa / slg / g / ipg …)。
    """
    # 第一關:這一欄本站根本配不出來,連公式都不去找,直接說為什麼。
    if field in CANNOT:
        raise Stop('本站配不出 %s:%s' % (field, CANNOT[field]))
    f = all_formulas().get(field)
    if not f:
        raise Stop('不認得的欄位:%s' % field)
    # 第二關:守門。GUARDS 說要看哪一個成績、最少要多少。
    # 沒給跟給太少分開講,因為使用者要採取的行動不一樣
    # (前者是補資料,後者是這個球員本來就不該用這條公式)。
    key, lo, label = GUARDS[field]
    have = stats.get(key)
    if have is None:
        raise Stop('%s 需要 %s,你沒有給。' % (field, label))
    if have < lo:
        raise Stop('%s:%s 只有 %g,少於 %d。這條公式是用 %s ≥ %d 的球員配的,'
                   '低於門檻時它比亂猜還糟而且會系統性高估,所以本站不給你數字。'
                   % (field, label, have, lo, label, lo))
    # 第三關:自變數到齊了沒有。把截距當成「值永遠是 1 的自變數」塞進同一張表,
    # 這樣底下一行 sum() 就把截距跟其他項一起算完,不必為它寫特例。
    t = dict(stats)
    t['const'] = 1.0
    missing = [k for k, _ in f['terms'] if k not in t]
    if missing:
        raise Stop('%s 還需要:%s' % (field, '、'.join(missing)))
    v = sum(c * t[k] for k, c in f['terms'])
    # 夾範圍。上下限是 EA 在這批資料裡實際給過的值,不是遊戲的合法範圍。
    # 落在外面代表這個球員的成績超出了配公式時看過的區間(外插),
    # 所以除了夾住,還要把「這個值不可信」講出來,交給呼叫端印給使用者。
    a, b = f['clamp']
    warn = ''
    if v < a or v > b:
        warn = '(算出 %.1f,超出 EA 資料裡看過的 %d~%d,已夾住 —— 這個值不可信)' % (v, a, b)
    return int(round(max(a, min(b, v)))), warn


# ── 讀遊戲資料 ──────────────────────────────────────────────
# data/database/*.dat 是純文字,記事本打得開。長相是這樣:
#
#   表頭   0 first_name,1 last_name,2 playerattrib_jerseynum,...;
#   資料   0fff0f559,0 Shohei,1 Ohtani,2 17,...
#          │         └───────┴─ 每一格都是「欄號 空格 值」
#          └─────────────────── 行首多一個 9 碼識別碼,表頭沒有對應的欄
#
# 三件讀者看不出來、但寫錯就會咬人的事:
#   1. **行首那個識別碼比表頭多一格。** 直接照位置切第 N 格會整排錯開一位,
#      所以下面兩個迴圈都靠「格子自己掛的欄號」取值,不靠位置。
#   2. **欄號不可以寫死。** 同一個欄名在不同檔、不同名冊裡的欄號會不一樣
#      (lhattrib.dat 比 rhattrib.dat 少一欄,從第 22 欄起整排位移)。
#   3. 表頭結尾有一個分號,所以先 rstrip(';,') 再切,不然最後一欄會多帶一個符號。
def load(db, name):
    """讀一個名冊檔,回傳 (欄名 -> 欄號, 識別碼 -> {欄號: 值})。"""
    p = os.path.join(db, name)
    if not os.path.isfile(p):
        raise Stop('找不到 %s' % p)
    # 用 latin-1 解碼:這是唯一「每個位元組都對得回去」的單位元組編碼。
    # 名冊裡可能有非 ASCII 的球員名,猜錯編碼會在寫回去時把那些位元組改掉。
    # latin-1 進、latin-1 出,沒動到的部分就保證逐位元組原封不動。
    txt = open(p, 'rb').read().decode('latin-1')
    # 換行字元原檔是什麼就用什麼。整批換成 LF 會讓檔案少掉「行數」個位元組。
    nl = '\r\n' if '\r\n' in txt else '\n'
    lines = txt.split(nl)
    # 表頭:每一格是「欄號 空格 欄名」,建成 欄名 -> 欄號。
    # 要求剛好切成兩段(len(a) == 2),形狀不對的格子直接不收。
    hdr = {}
    for c in lines[0].rstrip(';,').split(','):
        a = c.strip().split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            hdr[a[1]] = int(a[0])
    # 資料列:同樣照「欄號 空格 值」拆,鍵用欄號不用位置。
    # 行首那個識別碼是 9 碼十六進位,含字母就被 isdigit() 濾掉,
    # 不會被誤當成第 0 欄;整列的鑰匙就是它。
    # (真的抽到九碼全是數字的識別碼時,它會變成一個七、八位數的鍵,
    #  跟真正的欄號 0~45 差了好幾個數量級,不會蓋到任何一欄。)
    rows = {}
    for l in lines[1:]:
        if not l.strip():
            continue
        d = {}
        for c in l.split(','):
            a = c.strip().split(None, 1)
            if a and a[0].isdigit():
                d[int(a[0])] = a[1] if len(a) > 1 else ''
        if d:
            rows[l.split(',', 1)[0].strip()] = d
    return hdr, rows


# 取整數。取不到就回 None,**不回 0**:
# 「這一格是空的」跟「這一格真的是 0」在算平均與過門檻時是兩件事。
# lstrip('-') 是為了讓負數也算數字;少了它,任何負值都會被當成「這格是空的」。
def num(d, i):
    v = d.get(i, '')
    return int(v) if v.lstrip('-').isdigit() else None


def cmd_check(gamedir):
    """--check:先問「你那份遊戲的原料夠不夠」,再讓人決定要不要往下做。

    這一步存在的理由:分項成績(rhbstats / lhbstats / pstats)是配 power 與
    stamina 的唯一原料,而**模組常常把它們洗成空的**。本站測試機那份就是
    0.0%、只剩 1 人。沒有這一步,使用者會拿到一堆空白然後以為工具壞了。
    完全唯讀,不動任何檔案。
    """
    db = os.path.join(gamedir, 'data', 'database')
    print('\n  檢查 %s' % db)
    print('  ' + '-' * 60)
    ok = True
    # 三個分項成績檔各數一次「過門檻的人有幾個」。門檻就是 GUARDS 那兩道,
    # 因為過不了門檻的人對配公式跟對換算都一樣沒有用。
    for name, key, lo, what in (('rhbstats.dat', 'lrbatstat_tpa', 100, '對右投的力量'),
                                ('lhbstats.dat', 'lrbatstat_tpa', 100, '對左投的力量'),
                                ('pstats.dat', 'pitchstat_g', 10, '投手續航力')):
        try:
            h, r = load(db, name)
        except Stop as e:
            print('  🔴 %s' % e)
            ok = False
            continue
        # 欄號從表頭查,不寫死(理由見 load() 上面那段)。
        # 50 人是本站訂的下限:再少下去配出來的係數不穩,不如老實說配不出來。
        i = h.get(key)
        cnt = sum(1 for d in r.values() if i and (num(d, i) or 0) >= lo)
        good = cnt >= 50
        print('  %s %-14s 過門檻 %4d 人 → %s'
              % ('✅' if good else '🔴', name, cnt, what if good else what + ' **配不出來**'))
        ok = ok and good
    # 生涯成績是最後的退路,單獨數一次。它壞掉不影響上面三個的結論,
    # 所以這一段的失敗不併進 ok(印出來讓人知道就好)。
    try:
        h, r = load(db, 'career.dat')
        i = h['batcareerstats_ab']
        cnt = sum(1 for d in r.values() if (num(d, i) or 0) >= 200)
        print('  %s %-14s 過門檻 %4d 人 → 生涯成績退路'
              % ('✅' if cnt >= 50 else '🔴', 'career.dat', cnt))
    except Stop as e:
        print('  🔴 %s' % e)
    print('  ' + '-' * 60)
    if ok:
        print('  這份的資料夠用,可以跑 --fit 配出屬於你這份的係數。')
    else:
        print('  ⚠️ 這份的分項成績被洗掉了(模組常常會這樣)。')
        print('     只能用生涯成績那組退路,誤差大約兩倍。')
        print('     想要好公式,請拿一份**剛安裝好、沒裝過模組**的遊戲來 --fit。')
    print()
    return 0 if ok else 1


def _solve(A, b):
    """最小平方法解 A·x ≈ b,回傳係數清單;解不動就回 None。

    自己寫是為了**零相依**:這支腳本要能在只裝了 Python 的電腦上直接跑,
    不能要求使用者先去裝 numpy。

    做法是課本上的常規方程式(normal equations):把 AᵀA 與 Aᵀb 併成一個
    m × (m+1) 的增廣矩陣,再用高斯消去法解。每一步都選當前欄絕對值最大的
    那一列當主元(partial pivoting),否則主元接近 0 時誤差會被放大。
    主元小到 1e-12 以下代表這幾個自變數幾乎共線,解出來沒有意義,回 None。
    """
    m = len(A[0])
    M = [[sum(A[r][i] * A[r][j] for r in range(len(A))) for j in range(m)]
         + [sum(A[r][i] * b[r] for r in range(len(A)))] for i in range(m)]
    for i in range(m):
        p = max(range(i, m), key=lambda r: abs(M[r][i]))
        if abs(M[p][i]) < 1e-12:
            return None
        M[i], M[p] = M[p], M[i]
        for r in range(m):
            if r == i:
                continue
            f = M[r][i] / M[i][i]
            for c in range(i, m + 1):
                M[r][c] -= f * M[i][c]
    return [M[i][m] / M[i][i] for i in range(m)]


def _fit_one(label, data, xkey, ykey):
    """配一條單變數直線並印出誤差。**只報測試集,不報訓練集。**

    訓練集上的誤差一定比較好看,拿它當成績等於自己給自己打分數。
    """
    # 少於 60 筆就不配。與其配一條沒人知道準不準的線,不如直說樣本太少。
    if len(data) < 60:
        print('  %-24s 樣本只有 %d 筆,太少,不敢配。' % (label, len(data)))
        return
    # 留出驗證:先照自變數排序,再每 5 筆抽 1 筆當測試集。
    # 排序之後才抽,是為了讓測試集**均勻覆蓋整個值域**;直接照原順序抽,
    # 名冊本身的排列(球隊、位置)會讓某一段值域整片落在同一邊。
    data = sorted(data, key=lambda x: x[xkey])
    tr = [x for i, x in enumerate(data) if i % 5 != 0]
    te = [x for i, x in enumerate(data) if i % 5 == 0]
    co = _solve([[1.0, x[xkey]] for x in tr], [x[ykey] for x in tr])
    if not co:
        print('  %-24s 解不出來' % label)
        return
    # 兩個對照組都只用訓練集算,再拿到測試集上評分:
    #   med  中位數 → 算「一律猜同一個值」的平均絕對誤差。**中位數是讓 MAE
    #                 最小的常數**,所以這是比較嚴的那條基準線;
    #                 公式沒有明顯贏過它,那條公式就是白配的。
    #   mean 平均數 → 算 R² 的分母(總變異),順便算第二條基準線。
    # ⚠️ 兩條基準線都印,是因為 BEST / FALLBACK 裡存的 baseline 那一欄
    #    當初是用**平均數**算的。只印中位數那條的話,照著頁面說的
    #    「隨時可以自己重跑對照」去跑,三個數字全部對不上(15.83 vs 16.40、
    #    10.09 vs 10.56、10.73 vs 10.84),而那一欄其實沒有錯,只是另一把尺。
    mean = statistics.mean(x[ykey] for x in tr)
    med = statistics.median(x[ykey] for x in tr)
    f = lambda x: co[0] + co[1] * x[xkey]
    mae = statistics.mean(abs(f(x) - x[ykey]) for x in te)
    bm = statistics.mean(abs(med - x[ykey]) for x in te)
    bmean = statistics.mean(abs(mean - x[ykey]) for x in te)
    ss = sum((f(x) - x[ykey]) ** 2 for x in te)
    tt = sum((mean - x[ykey]) ** 2 for x in te)
    # 範圍用全部資料算(不只測試集),因為它要拿來當 clamp 的上下限參考。
    vals = [x[ykey] for x in data]
    print('  %-24s n=%d(訓練 %d/測試 %d)· 範圍 %d~%d'
          % (label, len(data), len(tr), len(te), min(vals), max(vals)))
    print('      %.4f + %.4f × %s' % (co[0], co[1], xkey))
    print('      測試 MAE %.2f · 基準(中位數) %.2f · 基準(平均) %.2f · 贏 %.0f%% · R² %.3f'
          % (mae, bm, bmean, (bm - mae) / bm * 100 if bm else 0, 1 - ss / tt if tt else 0))


def cmd_fit(gamedir):
    """--fit:用**你自己那份**遊戲重配一次係數並印出來。完全唯讀。

    為什麼要給使用者這個指令:寫在 BEST 裡的那組係數是本站用剛安裝好的原版
    配的。你手上那份如果是別的名冊(不同年代、不同聯盟),重配一次會更貼。
    印出來的那一行可以直接抄回 BEST。
    """
    db = os.path.join(gamedir, 'data', 'database')
    print('\n  用 %s 重配' % db)
    print('  ⚠️ 只報**測試集**上的誤差(依識別碼排序後每 5 筆取 1 筆)。\n')
    # ── 續航力 ← 單季 IP/G ──
    # 成績在 pstats.dat、能力值在 pitcher.dat,兩邊用行首識別碼配對。
    try:
        hp, rp = load(db, 'pitcher.dat')
        hs, rs = load(db, 'pstats.dat')
        d = []
        for pid, r in rs.items():
            if pid not in rp:
                continue
            g = num(r, hs['pitchstat_g']) or 0
            # G < 10 直接跳過:分母太小的 IP/G 抖得厲害,而 G = 0 是除以零。
            if g < 10:
                continue
            # 投球局數在名冊裡拆成兩欄:pitchstat_ip 是整局數,
            # pitchstat_pip 是**剩下的出局數**,所以要除以 3 再加回去。
            # (本站在剛安裝好的原版 1,430 列上量過:這一欄只出現 0、1、2 三種值,
            #  零例外。一局三個出局數,所以除以 3。)
            # 少了這一步,投了半局零頭的人局數會被系統性低估。
            ip = (num(r, hs['pitchstat_ip']) or 0) + (num(r, hs['pitchstat_pip']) or 0) / 3.0
            s = num(rp[pid], hp['pitchattrib_stamina'])
            if s is not None:
                d.append({'ipg': ip / g, 'st': s})
        _fit_one('stamina ← IP/G', d, 'ipg', 'st')
    except Stop as e:
        print('  stamina:%s' % e)
    # ── 力量 ← 同邊長打率 ──
    # 左右各配一條,**不共用係數**。把左側那條套到右側,誤差從 3.34 變 4.32。
    for side, af, sf in (('對右投', 'rhattrib.dat', 'rhbstats.dat'),
                         ('對左投', 'lhattrib.dat', 'lhbstats.dat')):
        try:
            ha, ra = load(db, af)
            hb, rb = load(db, sf)
            d = []
            for pid, r in rb.items():
                if pid not in ra:
                    continue
                tpa = num(r, hb['lrbatstat_tpa']) or 0
                if tpa < 100:
                    continue
                # 名冊裡沒有直接的長打率,要自己算,而且只給得起分子的原料:
                #   分子 = 壘打數 = 一安 + 二安×2 + 三安×3 + 全壘打×4
                #   分母 = 打數 AB。名冊只有打席 TPA,所以要把不算打數的
                #          四種結果(四壞、觸身、犧牲觸擊、高飛犧牲打)扣掉。
                # ⚠️ 這裡沒有扣「妨礙打擊」之類的稀有項,名冊裡也沒有那些欄位。
                b1, b2, b3, hr = [(num(r, hb['lrbatstat_' + k]) or 0)
                                  for k in ('1b', '2b', '3b', 'hr')]
                ab = tpa - sum((num(r, hb['lrbatstat_' + k]) or 0)
                               for k in ('bb', 'hbp', 'sh', 'sf'))
                p = num(ra[pid], ha['lrattrib_power'])
                # ab > 0 是除以零的防線:全部打席都是四壞的人會讓分母歸零。
                if ab > 0 and p is not None:
                    d.append({'slg': (b1 + 2 * b2 + 3 * b3 + 4 * hr) / ab, 'pow': p})
            _fit_one('power %s ← SLG' % side, d, 'slg', 'pow')
        except Stop as e:
            print('  power %s:%s' % (side, e))
    print('\n  ⚠️ 有哪一條印「樣本太少」,代表你那份的分項成績被洗掉了。跑 --check 看細節。\n')
    return 0


def cmd_demo():
    """--demo(也是不給參數時的預設):不碰任何檔案,把公式、誤差、
    以及**配不出來的那些**一次印給人看。

    最後那一段刻意用兩個一定會被擋下來的例子收尾:守門不是印警告然後照給,
    而是真的不給。看得到它拒絕,才不會有人以為空白是壞掉。
    """
    print('\n' + '=' * 64)
    print(' 成績 → 能力值:本站配出來的公式,以及配不出來的那些')
    print('=' * 64)
    print('\n  資料來源:剛安裝好的原版 MVP Baseball 2005。')
    print('  每一位球員同時有真實成績與 EA 給的能力值,識別碼完全對得上。\n')
    print('  ✅ 可用')
    for k, f in BEST.items():
        parts = ' '.join('%.4f' % c if nm == 'const' else '%+.4f × %s' % (c, nm)
                         for nm, c in f['terms'])
        print('    %-14s = %s' % (k, parts))
        print('        夾在 %d~%d · 測試 MAE %.2f · 基準 %.2f · R² %.3f'
              % (f['clamp'][0], f['clamp'][1], f['mae'], f['baseline'], f['r2']))
        print('        需要:%s' % f['needs'])
    print('\n  🟡 只有生涯成績時的退路(誤差約兩倍)')
    for k, f in FALLBACK.items():
        print('    %-14s MAE %.2f · 基準 %.2f · R² %.2f · %s'
              % (k, f['mae'], f['baseline'], f['r2'], f['needs']))
    print('\n  ❌ 配不出來(本工具不給數字)')
    for k, why in CANNOT.items():
        print('    %-18s %s' % (k, why))
    print('\n  ' + '-' * 60)
    print('  試算:一位 2040 年退休的二刀流(假想數字)')
    print('    打擊 對右投 TPA 3200 · SLG .612')
    v, w = compute('power_vs_rhp', tpa=3200, slg=0.612)
    print('      power(對右投) → %d   ± %.1f %s' % (v, BEST['power_vs_rhp']['mae'], w))
    print('    投球 單季 G 24 · IP 162(IP/G = 6.75)')
    v, w = compute('stamina', g=24, ipg=162 / 24)
    print('      stamina        → %d   ± %.1f %s' % (v, BEST['stamina']['mae'], w))
    print('    守備 → 本站不給。理由見上面。')
    print('  ' + '-' * 60)
    print('  ⚠️ 守門是硬的。下面這些**不會**給數字,只會說為什麼:')
    for f_, kw in (('power_vs_rhp', dict(tpa=60, slg=0.612)),
                   ('stamina', dict(g=3, ipg=6.0))):
        try:
            compute(f_, **kw)
        except Stop as e:
            print('    %s' % str(e).split('。')[0] + '。')
    print('=' * 64 + '\n')
    return 0


# 輸入 CSV 一定要有的三欄。id 是之後 --write 拿去跟遊戲名冊配對的鑰匙,
# 姓名純粹是給人看的(出錯訊息才認得出是誰),不參與任何計算。
CSV_IN = ('id', 'first_name', 'last_name')

# --out 不可以指到的副檔名。--convert 產生的是一張 CSV,而 --out 是使用者
# 自己打的路徑 —— 打成 attrib.dat 就會把一份名單整個蓋成 CSV,而且這條路徑
# 沒有備份也沒有預覽可以救。所以擋在寫之前。
BAD_OUT_EXT = ('.dat', '.big', '.fsh', '.sav', '.loc', '.exe', '.dll', '.ord', '.fel')


def check_out(path):
    """--convert 的輸出路徑守門:不准往遊戲檔上面寫。"""
    name = os.path.basename(path)
    if os.path.splitext(name)[1].lower() in BAD_OUT_EXT:
        raise Stop('--out 指到「%s」—— 那是遊戲檔的副檔名。這一步產生的是一張 CSV,'
                   '寫過去會把那個檔整個蓋掉。換一個 .csv 的檔名。' % name)
    # ⚠️ realpath 不是 abspath:上一層如果是一顆指到 data/database 的符號連結,
    #    abspath 看到的還是那個假名字,只有 realpath 會把它解開。
    if os.path.basename(os.path.realpath(os.path.dirname(os.path.abspath(path)))).lower() == 'database':
        raise Stop('--out 指到 data/database 裡面 —— 那是遊戲名單的資料夾,'
                   '這一步不該往那裡寫。換一個地方放。')
    # 符號連結要單獨擋。上面兩條看的都是「名字」,而一個叫 ratings.csv 的符號連結
    # 可以指到 data/database/attrib.dat —— 副檔名是 .csv、上一層也不是 database,
    # 兩關都過,然後 open(out, 'w') 跟著連結把整份名單蓋成一張 CSV。
    # 這條路沒有備份也沒有預覽可以救,所以擋在寫之前。
    if os.path.islink(path):
        raise Stop('--out 指到的「%s」是一個符號連結(指向 %s)。'
                   '本站不跟著連結寫。換一個一般的檔名。'
                   % (name, os.path.realpath(path)))


def cmd_convert(path, out):
    """--convert:CSV 進、CSV 出。這一步不碰遊戲,只做算術。"""
    # 唯一會寫檔的地方是最後那個 --out,所以守門放在算之前:
    # 算了半天才發現目標不能寫,不如一開始就說。
    check_out(out)
    if not os.path.isfile(path):
        raise Stop('找不到 %s —— 那張成績表的路徑對嗎?' % path)
    # utf-8-sig:Excel 存出來的 CSV 開頭常有 BOM,不吃掉的話第一個欄名
    # 會變成「﻿id」,然後「CSV 少了 id」這種讓人一頭霧水的錯。
    # newline='' 是 csv 模組要求的,少了它在 Windows 上會多出空白列。
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise Stop('%s 是空的。' % path)
    missing = [c for c in CSV_IN if c not in rows[0]]
    if missing:
        raise Stop('CSV 少了:%s' % '、'.join(missing))
    outrows, notes = [], []
    # start=2:第 1 行是欄名,所以資料的第一列在試算表裡是第 2 行。
    # 錯誤訊息要用**使用者在 Excel 裡看到的行號**,不然對不上。
    for i, r in enumerate(rows, start=2):
        # 取一格數字。空白或打錯字一律回 None(不是 0),
        # 交給 compute() 的守門去拒絕,而不是在這裡自作主張補一個值。
        def g(k):
            v = (r.get(k) or '').strip()
            try:
                return float(v) if v else None
            except ValueError:
                return None
        o = {k: r.get(k, '') for k in CSV_IN}
        # 直接照抄的自變數:使用者給什麼就是什麼。
        stats = {}
        for k in ('tpa', 'slg', 'g', 'ipg', 'ab'):
            v = g(k)
            if v is not None:
                stats[k] = v
        # 要算的自變數:退路公式吃的是「每個打數幾支」的比率,不是累積數。
        # 沒有 AB 就整組都算不出來,所以這一段整個包在 ab > 0 底下。
        ab = g('ab')
        if ab and ab > 0:
            for src, dst in (('hr', 'hr_rate'), ('r', 'r_rate'), ('sb', 'sb_rate')):
                if g(src) is not None:
                    stats[dst] = g(src) / ab
            stats['sqrt_ab'] = math.sqrt(ab)
        # 六個欄位各試一次。算不出來就留空白格,**不填 0 也不填猜的值**,
        # 而且不讓一欄的失敗中斷其他欄(所以 Stop 在這裡接住不往上丟)。
        got = 0
        for field in list(BEST) + list(FALLBACK):
            try:
                v, w = compute(field, **stats)
                o[field] = v
                got += 1
                if w:
                    notes.append('第 %d 行 %s:%s' % (i, field, w))
            except Stop:
                o[field] = ''
        # 一欄都算不出來的人要單獨點名。整列空白很容易被當成「程式壞了」,
        # 其實是這個人給的成績不足以算任何一欄。
        if not got:
            notes.append('第 %d 行 %s %s:給的成績不足以算出任何一欄'
                         % (i, r.get('first_name', ''), r.get('last_name', '')))
        outrows.append(o)
    # 輸出的欄位順序寫死成「三欄身分 + BEST 三欄 + FALLBACK 三欄」,
    # 這樣不管哪幾格是空的,每一份輸出的欄位都一樣,下游好處理。
    cols = list(CSV_IN) + list(BEST) + list(FALLBACK)
    # 先在記憶體裡把整張表排好,再一次落地。**不要 open(out, 'w') 直接開** ——
    # 那會跟著符號連結寫,而且會先把目的檔截成 0(理由見 write_export)。
    # 這裡用 io.StringIO 收,csv 模組預設的換行就是 \r\n,跟舊版
    # open(..., newline='') 寫出來的位元組完全一樣(本站逐位元組對過)。
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for o in outrows:
        w.writerow({c: o.get(c, '') for c in cols})
    write_export(out, buf.getvalue().encode('utf-8'))
    print('  換算 %d 列 → %s' % (len(outrows), out))
    print('  ⚠️ 空白的格子代表**守門沒過,本站不給你猜的數字**。')
    print('  ⚠️ 這張表沒有 fielding / 選球 / 臂力 / 耐久 —— 配不出來,不編。')
    if notes:
        print('\n  %d 則說明:' % len(notes))
        for s in notes[:12]:
            print('    %s' % s)
        if len(notes) > 12:
            print('    …還有 %d 則' % (len(notes) - 12))
    return 0



# ── 寫回遊戲 ────────────────────────────────────────────────
# ⚠️ 每一次都從表頭讀欄號,絕對不要寫死。
#    lhattrib.dat 少了 lrattrib_chasehardbreak 這一欄,所以從第 22 欄起
#    它的欄號比 rhattrib.dat **整排少 1**。任何假設「左右格式一樣」的程式
#    會靜默寫壞六個欄位(take / miss 那幾個直接影響打擊表現)。
#
# CSV 欄位 -> (要改哪一個檔, 表頭裡的欄名)。
# ⚠️ 這張表只有四項,而 --convert 會輸出六欄:
#    退路的 power 與 contact **刻意不在這裡**。它們的誤差是 BEST 那組的兩倍多
#    (7.75 / 8.36),本站不拿那種等級的估計去覆蓋 EA 原本的值。
#    要用的人自己看 CSV 手動填,那是有意識的決定,跟程式默默寫進去不一樣。
# ⚠️ **speed 是上面那條原則的例外,不能不講。** 它也是退路公式
#    (MAE 7.38 · R² 0.46),跟 power(7.75)、contact(8.36)同一級,
#    可是它在這張表裡 —— 加了 --apply 就會寫進 attrib.dat。
#    不想讓這種等級的估計覆蓋 EA 原本的值,就把 CSV 的 speed 欄清空再 --write:
#    本站實測清空之後另外三個檔照寫 15 格,attrib.dat 逐位元組相同、
#    連備份都不會產生。
WRITE_MAP = {
    'power_vs_rhp': ('rhattrib.dat', 'lrattrib_power'),
    'power_vs_lhp': ('lhattrib.dat', 'lrattrib_power'),
    'stamina': ('pitcher.dat', 'pitchattrib_stamina'),
    'speed': ('attrib.dat', 'playerattrib_speed'),
}
# 備份檔名的後綴。取一個本站專用的名字(不是通用的 .bak),
# 是為了跟其他工具留下的備份分得開,--restore-write 才不會撿到別人的。
WRITE_BAK = '.ratingsbak'

# CSV 那一格寫得進名單的合法範圍。
# ⚠️ 這不是憑感覺訂的:本站在兩份名單(剛安裝好的原版、被模組疊過的測試機)的
#    四個可寫欄位上全部數過一遍,合計 21,552 格,**每一格都是整數,最小 0、最大 100**。
#    所以超出這個範圍的值不是「大膽的設定」,是「這份 CSV 出事了」。
WRITE_RANGE = (0, 100)


def value_ok(v):
    """CSV 那一格能不能寫進名單:必須是十進位整數,而且落在 WRITE_RANGE 裡。

    ⚠️ 這一關擋在寫之前,不是寫完再驗 —— 因為寫壞的方式是**改壞檔案結構**,
    不是寫進一個怪數字:名單的格子長成「欄號 空格 值」,值裡如果有逗號
    (Excel 在某些地區設定會把 8.0 存成「8,0」),那一格就被拆成兩格,
    後面那半格「0」會被當成第 0 欄,把同一列的 first_name 蓋掉。
    本站實測過:寫「8,0」進去之後,那一列的 first_name 從 Default 變成空的,
    整列的格子數從 48 變 49。

    不用 str.isdigit() 判斷,是因為它對全形數字與上標(例如「²」)也回 True,
    而 int() 吃不下那些字元。這裡只認 ASCII 的 0-9。
    """
    s = v.strip()
    if not s or any(c not in '0123456789' for c in s):
        return False
    return WRITE_RANGE[0] <= int(s) <= WRITE_RANGE[1]


def set_field(line, idx, value):
    """只換欄號相符的那一格,其他位元組一個都不動。
    ⚠️ 不可以用 str.replace ——「2 0」在一行裡會出現在很多地方。"""
    cells = line.split(',')
    hit = 0
    for i, cell in enumerate(cells):
        a = cell.strip().split(None, 1)
        if a and a[0].isdigit() and int(a[0]) == idx:
            # 把原本那一格的前置空白原樣留著再接新值。
            # 名冊的格子之間有沒有空白並不統一,重寫時不還原它,
            # 檔案就會出現「只有這一格長得不一樣」的痕跡。
            lead = cell[:len(cell) - len(cell.lstrip())]
            cells[i] = '%s%d %s' % (lead, idx, value)
            hit += 1
    # 剛好一格才動。0 個代表這一列沒有那一欄,2 個以上代表這個檔的欄號有重複
    # (本站在別的檔上見過欄號掛錯的名冊)。兩種都是「停下來問人」,不是猜。
    if hit != 1:
        raise Stop('第 %d 欄找到 %d 個,不敢動。' % (idx, hit))
    return ','.join(cells)


# ── 暫存檔、符號連結、原子換檔 ──────────────────────────────
# ⚠️ 2026-09-05 資安覆驗抓到的洞:在這之前備份與寫入用的都是**事先猜得到的名字**
#    (「原檔名.part」「原檔名.tmp」「原檔名.restoretmp」)。那是一條真的攻擊路徑:
#    先在 data/database 裡放一個叫「attrib.dat.ratingsbak.part」的符號連結指到別處,
#    這支腳本一跑,copyfile / open(..., 'wb') 會**跟著連結**先把外面那個檔截成 0
#    再灌進名單的內容;後面的 os.replace 只換掉連結本身,傷害卻已經造成了。
#    本站在拋棄式資料夾裡照這個方式重現過(--selftest 的餌 1 就是它)。
#    所以現在一律走 tempfile.mkstemp(dir=同一個資料夾):底層是 O_CREAT|O_EXCL,
#    名字事先猜不到,而且**既有的檔(含符號連結)絕對不會被它挑中**。


class _NoInterrupt(object):
    """把「換名 + 登記」包成一段不可中斷的動作:這段期間收到 Ctrl-C 先記著,
    離開這段之後再照常丟出來。

    為什麼要有它(2026-09-06):os.replace 換完之後、還沒把「這個檔已經換過」
    記進 _TOUCHED 之前,只要 Ctrl-C 剛好落在那兩行中間,收尾就會照著空的帳本
    說「什麼都沒有動到」,而磁碟上那個檔其實已經是新的了。有了這一段,
    KeyboardInterrupt 的收尾看到的帳本**一定**跟磁碟上的狀態一致。

    ⚠️ signal.signal 只有主執行緒裝得上。裝不上時就退回原本的行為(不會更糟),
    所以 _TOUCHED['replacing'] 那個旗標是第二層保險,不可以因為有了這個類別就拿掉。
    ⚠️ 這一段裡面只放「換名 + 登記」兩件事,不可以把讀寫整個檔塞進來 ——
    那會變成使用者按了 Ctrl-C 要等很久才停得下來。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):   # 非主執行緒等情況:退回原本行為
            self._old = None
        return self

    def _remember(self, signum, frame):
        # 只記下來,不丟例外。真正丟出去是離開這一段之後的事。
        self._pending = True

    def __exit__(self, exc_type, exc, tb):
        if self._old is not None:
            signal.signal(signal.SIGINT, self._old)
        # 已經有別的例外在往上跑的時候不要再蓋一層 —— 原本那個才是失敗的原因。
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _open_beside(dst, tag):
    """在 dst 所在的那個資料夾裡開一顆猜不到名字的暫存檔,回傳 (已開好的檔物件, 路徑)。

    一定要開在**同一個資料夾**,os.replace 才是原子的(跨磁碟區的改名不是原子的,
    Python 會退化成複製 + 刪除,那就又有半截檔的問題了)。
    名字開頭那個點是為了讓它在 Finder 與 ls 預設看不到,萬一真的留下來也不礙眼。
    """
    d = os.path.dirname(os.path.abspath(dst)) or '.'
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(dst), tag))
    try:
        return os.fdopen(fd, 'wb'), tmp
    except BaseException:
        # fdopen 沒接手成功的話,fd 跟那顆檔都是我們的責任,不可以留著。
        os.close(fd)
        _drop(tmp)
        raise


def _is_leftover_tmp(name):
    """這個檔名是不是本腳本留下來的中間檔(收尾點名用)。

    ⚠️ 這條要跟著 _open_beside 的 prefix 一起改。改了一邊沒改另一邊,
    中間檔會安靜地留在使用者的 database 資料夾裡而沒有人點名它。
    """
    return name.startswith('.') and any(('.%s-' % t) in name
                                        for t in ('part', 'tmp', 'restore'))


def _refuse_symlink(path, what):
    """目的檔是符號連結就整個停下來,不跟著它寫。

    ⚠️ 判斷不可以用 os.path.exists():指向不存在目標的符號連結(dangling)
    它會回 False —— 於是「不存在,那就放心寫吧」這個結論剛好在最危險的
    那一種情況下成立。要用 os.path.islink / os.path.lexists,它們看的是連結本身。
    """
    if os.path.islink(path):
        raise Stop('「%s」是一個符號連結(指向 %s)。本站不跟著連結寫 —— '
                   '那會改到遊戲資料夾外面的檔案。請先把它處理掉再重跑。'
                   % (what, os.path.realpath(path)))


def _sha256(path):
    """整個檔案的 sha256。還原時拿來確認「寫進暫存檔的東西真的跟備份一樣」。"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _finish(w, path):
    """暫存檔收尾:flush → fsync → 關檔。

    fsync 那一步是「逼作業系統真的寫進碟」,少了它,os.replace 之後遇到斷電
    會換上一顆內容還在快取裡的空殼。
    """
    w.flush()
    os.fsync(w.fileno())
    w.close()


def _drop(path):
    """清掉暫存檔。清不掉不可以蓋掉真正的錯誤原因,所以吞掉 OSError。

    用 lexists 不用 exists:留下來的如果是一顆 dangling 符號連結,
    exists() 會說它不存在,然後它就永遠清不掉了。
    """
    if os.path.lexists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def atomic_backup(src, dst):
    """備份要嘛完整、要嘛不存在,中間狀態不會用最終那個檔名。

    為什麼要這樣做(2026-08-29 上線前稽核):直接 copy2 到 .ratingsbak,
    複製途中被中斷(磁碟滿、外接碟拔掉、按 Ctrl-C)會留下**半截的備份**;
    下一次執行看到它「存在」就不再備份,而 --restore-write 之後會拿那個
    半截檔覆蓋掉正本。實測 840,643 bytes 的名單被還原成 105,080。

    做法:先寫一顆 mkstemp 開出來的暫存檔,成功了再 os.replace 換成正式名字。
    os.replace 是原子的,所以 .ratingsbak 這個名字底下不會出現半截檔。
    中途出事就把暫存檔清掉,並且**把原本的例外原封不動往上丟**
    (清理失敗不可以蓋掉真正的錯誤原因)。

    2026-09-05 改了兩件事:
      · 暫存檔名從固定的「dst + '.part'」改成 mkstemp(理由見上面那段)。
      · 來源與備份兩個路徑先過 _refuse_symlink。

    ⚠️ 內容是自己一段一段抄的,不是 shutil.copy2,理由是量出來的:copy2 會
    **連檔案旗標一起複製**,所以來源被鎖住(macOS 的 uchg、Windows 的唯讀屬性)時
    暫存檔自己也變成鎖住的,接著 os.replace 就丟 PermissionError,而且那顆暫存檔
    連清都清不掉,會留在使用者的 database 資料夾裡。本站實測:同一顆來源檔,
    copy2 產生的複本 os.replace 失敗、只抄內容的複本 os.replace 成功。
    備份要的是內容,不是旗標。
    權限(讀寫位元)倒是要抄 —— mkstemp 開出來的檔預設只有自己讀得到(0600),
    不抄的話備份會變成一顆別人打不開的檔。copymode 走的是 chmod,不碰旗標。
    """
    _refuse_symlink(src, '要備份的名單檔 ' + os.path.basename(src))
    _refuse_symlink(dst, '備份檔 ' + os.path.basename(dst))
    w, part = _open_beside(dst, 'part')
    try:
        with open(src, 'rb') as r:
            shutil.copyfileobj(r, w)
        _finish(w, part)
        shutil.copymode(src, part)
        os.replace(part, dst)
    except BaseException:
        w.close()
        _drop(part)
        raise


def atomic_restore(bak, dst, on_replaced=None):
    """把備份放回正本的位置,而且**換過去之前先確認寫對了**。

    on_replaced:換名成功之後、還在不可中斷區間裡要做的登記動作(可以不給)。
    呼叫端不要等這個函式回來才記「已經還原了」—— Ctrl-C 卡在那中間,帳本就說謊了。

    2026-09-05 覆驗:原本這裡是「複製到 <原檔名>.restoretmp 再 os.replace」。
    原子性本身沒問題,但有兩件事沒做:
      · 那個名字猜得到 —— 事先擺一顆同名的符號連結,複製就跟著它寫到資料夾外面去。
      · 寫完沒有讀回來對過 —— 磁碟寫壞、外接碟半路斷線的時候,換過去的會是一顆
        **看起來完整、內容卻不是備份**的檔,而使用者以為自己救回來了。
        還原是出事之後才會跑的救命路徑,它自己騙人的代價最大。

    現在的順序:mkstemp 開暫存檔 → 抄內容 → flush + fsync → 把正本的權限抄過來
    → **整顆 sha256 跟備份對過** → 才 os.replace 換名。
    任何一步失敗都把暫存檔清掉,而正本**一個位元組都不會被動到**
    (--selftest 的餌 5、餌 6 就是在證明這件事)。

    ⚠️ 不可以用 shutil.copy2(bak, dst) 直接蓋正本:copy2 是先把目的檔截成
    0 bytes 再灌回去。本站量過 336 MB 的檔在還原途中大小確實掉到 0 才一路長回來。
    """
    _refuse_symlink(bak, '備份檔 ' + os.path.basename(bak))
    _refuse_symlink(dst, '要還原的名單檔 ' + os.path.basename(dst))
    w, tmp = _open_beside(dst, 'restore')
    try:
        with open(bak, 'rb') as r:
            shutil.copyfileobj(r, w)
        _finish(w, tmp)
        # 權限照正本那顆抄(正本不在了才退而求其次照備份),
        # 否則還原完的名單會變成 mkstemp 的 0600,遊戲那邊未必讀得到。
        shutil.copymode(dst if os.path.exists(dst) else bak, tmp)
        # 讀回來對:比的是**已經落地的暫存檔**,不是記憶體裡那份 buffer。
        if _sha256(tmp) != _sha256(bak):
            raise Stop('寫出來的內容跟備份對不起來(sha256 不同)—— '
                       '沒有換過去,正本原封不動。')
        # 換名 + 登記綁成一段不可中斷的動作(理由見 _NoInterrupt)。
        _TOUCHED['replacing'] = os.path.basename(dst)
        with _NoInterrupt():
            os.replace(tmp, dst)
            if on_replaced is not None:
                on_replaced()
            # 撤旗標在區間裡面(理由同 cmd_write)。
            _TOUCHED['replacing'] = ''
    except BaseException as _e:
        # 旗標只有在確定 os.replace 沒做的時候才可以撤銷(理由同 cmd_write)。
        if not isinstance(_e, KeyboardInterrupt):
            _TOUCHED['replacing'] = ''
        w.close()
        _drop(tmp)
        raise


def _new_file_mode():
    """新開的檔案該有的權限。

    mkstemp 開出來的是 0600(只有自己讀得到),而 --convert 產生的那張 CSV 是要
    給人看、給試算表打開、也可能寄給別人的檔。留 0600 等於偷偷改掉了使用者
    以為自己會拿到的東西(舊版走 open(out, 'w'),拿到的是 0666 扣掉 umask,
    多數機器上就是 0644)。所以這裡把 umask 讀出來自己算一次。

    ⚠️ 標準函式庫只有 os.umask 這一個入口,而它是「設定並回傳舊值」——
    沒有純讀取的版本(本站在手上這台 Python 3.9.6 上確認過 os.getumask 不存在),
    所以只能設一次再設回去。這支腳本是單執行緒的,中間那一瞬間不會有別人在開檔。
    """
    m = os.umask(0o022)
    os.umask(m)
    return 0o666 & ~m


def write_export(path, data):
    """把匯出檔(--convert 產生的那張 CSV)寫出去:**不跟著符號連結,而且是原子的**。

    2026-09-06 補的。在這之前這裡是 open(path, 'w') 直接開,有兩個問題:

      · check_out() 在整條流程的**最前面**就驗過「這不是符號連結」,可是驗完到
        真的開檔中間隔著讀 CSV、算六個欄位。**那段時間裡冒出來的符號連結會被
        跟著寫**。本站用一支變體腳本在那個縫裡塞一顆指向資料夾外面的連結重現過:
        舊寫法把外面那個檔整個蓋成 CSV(exit 還是 0),改成下面這套之後同一支
        變體腳本被擋下來、外面那個檔的 sha256 一個位元都沒變。
      · open(..., 'w') 會先把目的檔截成 0 再寫。寫到一半沒電,使用者原本那張表
        就只剩半截 —— 而那可能是他自己手改過的。

    現在跟寫名單檔同一套:mkstemp 開一顆猜不到名字的暫存檔 → 寫 → flush + fsync
    → 再看一次不是符號連結 → 權限補好 → os.replace 原子換名。
    """
    _refuse_symlink(path, '輸出檔 ' + os.path.basename(path))
    w, tmp = _open_beside(path, 'tmp')
    try:
        w.write(data)
        _finish(w, tmp)
        # 換名之前再看一次。這一道擋的是「第一道驗過之後才擺上去」的連結 ——
        # 窗口很窄,但成本只有一次 lstat。
        # ⚠️ 話要說準:就算兩道都沒擋到,**外面那個檔也不會被寫壞**,
        #    因為 os.replace 換掉的是連結本身,不會順著它寫過去。
        #    兩道守門買到的是「一句看得懂的錯誤訊息」跟「不要默默把使用者的
        #    連結換成一般檔案」,不是唯一的防線。真正的防線是不用 open(path,'w')。
        _refuse_symlink(path, '輸出檔 ' + os.path.basename(path))
        # 目的檔已經在了就照抄它的權限(使用者可能自己調過);
        # 是新檔就用「一般新檔」的權限,不要把 mkstemp 的 0600 留給使用者。
        if os.path.exists(path):
            shutil.copymode(path, tmp)
        else:
            os.chmod(tmp, _new_file_mode())
        os.replace(tmp, path)
    except BaseException:
        w.close()
        _drop(tmp)
        raise


def cmd_write(gamedir, csvpath, apply_it):
    """把 --convert 產生的那張表寫回遊戲。

    流程刻意分成「先全部算完,再一次寫」:
      1. 讀 CSV,對每一個要寫的欄位查出「哪一個檔、第幾列、第幾欄、舊值是什麼」
      2. 中間**任何一筆對不上就整批放棄**,不寫一半
      3. 沒加 --apply 就到這裡為止,只印預覽
      4. 真的寫:每個檔先備份一次(已經有備份就不覆蓋,保留最早那一份),
         再用暫存檔 + fsync + os.replace 換過去
      5. 全部讀回來逐項比對,對不上就叫人還原

    第 2 步是這支腳本最重要的一個決定:寫壞一半的名單比完全沒寫難救得多。
    """
    db = os.path.join(gamedir, 'data', 'database')
    # 路徑打錯是最常見的失手,而這條路徑會去動遊戲檔 ——
    # 所以先把兩個前提講清楚,不要讓使用者收到一段英文堆疊。
    if not os.path.isdir(db):
        raise Stop('找不到 %s —— 遊戲資料夾的路徑對嗎?' % db)
    if not os.path.isfile(csvpath):
        raise Stop('找不到 %s —— 那張表的路徑對嗎?' % csvpath)
    with open(csvpath, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise Stop('%s 是空的。' % csvpath)
    if 'id' not in rows[0]:
        raise Stop('CSV 沒有 id 欄 —— 那是配對用的鑰匙。')

    # ── 第 1 步:算出完整的動作清單,一個位元組都還沒寫 ──
    plans = {}          # 檔名 -> [(行號, 欄號, 新值, id, 欄位名, 舊值)]
    unknown = []
    for field, (fname, col) in WRITE_MAP.items():
        vals = [(r['id'].strip(), r[field].strip())
                for r in rows if r.get(field, '').strip()]
        if not vals:
            continue
        try:
            hdr, data = load(db, fname)
        except Stop as e:
            unknown.append('%s:%s' % (field, e))
            continue
        if col not in hdr:
            unknown.append('%s:%s 的表頭裡沒有 %s' % (field, fname, col))
            continue
        # 欄號永遠現查。lhattrib.dat 少一欄,從第 22 欄起整排跟 rhattrib.dat 差 1,
        # 寫死欄號會靜默寫壞六個欄位(而且是 take / miss 那幾個直接影響打擊的)。
        idx = hdr[col]
        # 這裡重讀一次原始文字(load() 給的是解析結果,不是原文)。
        # 要改的是**這一行的那一格**,其他位元組必須原封不動保留,
        # 所以不能拿解析結果重新組一份檔案出來。
        raw = open(os.path.join(db, fname), 'rb').read().decode('latin-1')
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines = raw.split(nl)
        # 識別碼 -> 行號。start=1 是因為第 0 行是表頭。
        byid = {l.split(',', 1)[0].strip(): i
                for i, l in enumerate(lines[1:], start=1) if l.strip()}
        for pid, v in vals:
            # 值先驗,再找人。理由見 value_ok():不是整數的值會改壞檔案結構,
            # 而這裡跟「id 對不上」走同一個籃子,所以照樣是**整批不寫**。
            if not value_ok(v):
                unknown.append('%s:id %s 的值「%s」不是 %d~%d 的整數'
                               % (field, pid, v, WRITE_RANGE[0], WRITE_RANGE[1]))
                continue
            if pid not in byid:
                unknown.append('%s:名冊裡找不到 id %s' % (field, pid))
                continue
            ln = byid[pid]
            # 把那一行拆成 {欄號: 值} 取舊值,用途有兩個:
            # 預覽時印「原本 → 要改成」,以及下面那一行的「值一樣就不寫」。
            old = num(dict((int(c.strip().split(None, 1)[0]),
                            c.strip().split(None, 1)[1] if len(c.strip().split(None, 1)) > 1 else '')
                           for c in lines[ln].split(',')
                           if c.strip().split(None, 1)[0].isdigit()), idx)
            # 已經是這個值就跳過。少改一格就少一次出錯的機會,
            # 而且預覽列出來的東西才會是「真的會變的那些」。
            if str(old) == v:
                continue
            plans.setdefault(fname, {'nl': nl, 'lines': lines, 'items': []})
            plans[fname]['items'].append((ln, idx, v, pid, field, old))

    # ── 第 2 步:有任何一筆對不上,整批不寫 ──
    # 對不上通常代表 CSV 跟這份遊戲的名冊不是同一批人。這時候寫進去的每一筆
    # 都可疑,所以不是「跳過那幾筆」而是「整批放棄」,並且逐筆說是哪一個。
    if unknown:
        print('  ⚠️ 有 %d 筆對不上,**整批不寫**:' % len(unknown))
        for u in unknown[:10]:
            print('    %s' % u)
        if len(unknown) > 10:
            print('    …還有 %d 筆' % (len(unknown) - 10))
        return 1
    if not plans:
        print('  沒有需要改的 —— 這張表跟遊戲裡的值一樣。')
        return 0

    # ── 第 3 步:預覽。沒加 --apply 就在這裡結束 ──
    total = sum(len(p['items']) for p in plans.values())
    print('  要改 %d 個欄位,分佈在 %d 個檔:' % (total, len(plans)))
    for fname, p in plans.items():
        print('    %-16s %d 個' % (fname, len(p['items'])))
        for ln, idx, v, pid, field, old in p['items'][:5]:
            print('        %s  %-14s %s → %s' % (pid, field, old, v))
        if len(p['items']) > 5:
            print('        …還有 %d 個' % (len(p['items']) - 5))
    if not apply_it:
        print()
        print('  這是預覽,一個位元組都沒有寫。確定再跑一次,最後加上 --apply。')
        return 0

    # ── 第 4 步之前:起飛前檢查,四個檔的八個名字一次驗完 ──
    # ⚠️ 這一段的位置就是它的全部意義。2026-09-11 之前這兩道 _refuse_symlink 是寫在
    #    下面那個迴圈**裡面**的,於是排在最後的那個檔是符號連結時,前面幾個早就
    #    已經換過去了才停下來 —— 而檔頭寫著「名單檔或備份檔如果是符號連結,
    #    整個停下來不寫」。本站在拋棄式副本上量過:把 attrib.dat 換成一顆指到
    #    資料夾外面一份合法名單的符號連結,舊版把 rhattrib.dat、lhattrib.dat、
    #    pitcher.dat 三個都改掉才停,自己的輸出還印著「**已經改掉的檔**」那三個名字。
    #    那句說明當時是假的。現在先把全部的 lstat 做完(每個檔兩次:名單檔與備份檔),
    #    一個都沒問題才動第一個位元組。
    for _fname in plans:
        _path = os.path.join(db, _fname)
        _refuse_symlink(_path, '名單檔 ' + _fname)
        _refuse_symlink(_path + WRITE_BAK,
                        '備份檔 ' + os.path.basename(_path + WRITE_BAK))

    # ── 第 4 步:真的寫 ──
    # ⚠️ 這是一個檔一個檔寫的迴圈。**單一檔案是原子的,四個檔之間不是** ——
    #    第二個檔失敗時,第一個檔已經是改過的狀態了。這種事真的會發生:
    #    檔案被設成唯讀、磁碟滿、外接碟被拔掉。本站實測把 pitcher.dat 鎖起來,
    #    前兩個檔寫進去、後兩個沒有,而畫面上只有一段英文堆疊,
    #    沒有任何一句告訴使用者「跑 --restore-write 可以退回去」。
    #    所以這裡把整段包起來:失敗時先講**哪幾個已經改了**、怎麼退,再結束。
    done = []
    _TOUCHED['gamedir'] = gamedir
    # 收尾那句話在 --write 與 --restore-write 兩條路上意思相反(理由見 _TOUCHED)。
    _TOUCHED['cmd'] = 'write'
    try:
        for fname, p in plans.items():
            path = os.path.join(db, fname)
            bak = path + WRITE_BAK
            # 第二層:起飛前檢查跟這裡之間隔著前面幾個檔的備份與換名,
            # 那段時間裡才擺上去的連結只有這一道擋得住(成本是兩次 lstat)。
            # ⚠️ 不可以因為有這一道就把上面那段起飛前檢查拿掉 —— 只有這裡的話,
            #    前面幾個檔已經改掉了才會停,檔頭那句「整個停下來不寫」就是假的。
            _refuse_symlink(path, '名單檔 ' + fname)
            _refuse_symlink(bak, '備份檔 ' + os.path.basename(bak))
            # 備份只做第一次。第二次再跑時保留最早那一份,
            # 因為那份才是「你動手之前的樣子」;每次覆蓋等於改了兩次就退不回去。
            # ⚠️ 用 lexists 不用 exists:備份那個名字如果是一顆指向不存在目標的
            #    符號連結,exists() 會回 False,於是「還沒有備份」這個結論剛好在
            #    最危險的情況下成立。不過上面那道 _refuse_symlink 已經先擋掉了,
            #    這裡用 lexists 是第二層。
            if not os.path.lexists(bak):
                atomic_backup(path, bak)
                print('  備份 %s' % os.path.basename(bak))
            # 在記憶體裡改完整份,再一次落地。逐行就地改檔會在中途被中斷時
            # 留下半新半舊的名單,那種檔看起來是好的,遊戲卻可能讀出鬼東西。
            out = list(p['lines'])
            for ln, idx, v, _pid, _f, _o in p['items']:
                out[ln] = set_field(out[ln], idx, v)
            # 換行字元用原檔那一種(nl 是讀進來時量的),編碼也用同一個 latin-1,
            # 所以沒動到的行寫回去是逐位元組相同的。
            # 寫暫存檔 → flush → fsync(逼作業系統真的寫進碟)→ os.replace 原子換名。
            # 暫存檔的名字用 mkstemp 開(不是「原檔名.tmp」)。理由見上面那段:
            # 猜得到的名字可以被人事先擺一顆符號連結佔走。
            # 換過去之前把原本的權限抄回來 —— mkstemp 開出來的是 0600,
            # 不抄的話名單會變成只有自己讀得到。
            w, tmp = _open_beside(path, 'tmp')
            try:
                w.write(p['nl'].join(out).encode('latin-1'))
                _finish(w, tmp)
                shutil.copymode(path, tmp)
                # 先把「正在換這一個檔」寫進帳本,再進不可中斷的那一段。
                # 換名跟登記綁在一起(理由見 _NoInterrupt),帳本跟磁碟上的狀態
                # 就不會對不起來;萬一 _NoInterrupt 裝不上,這個旗標會讓收尾
                # 說「中斷時正在替換 X」,不會反過來說「什麼都沒有動到」。
                _TOUCHED['replacing'] = fname
                with _NoInterrupt():
                    os.replace(tmp, path)
                    # 換過去了才登記。這份清單是 Ctrl-C 之後那句「你的檔案現在是
                    # 什麼狀態」的唯一依據,所以只記**真的做過 os.replace 的**。
                    _TOUCHED['write'].append(fname)
                    done.append(fname)
                    # 撤旗標也要在區間**裡面**。放到區間外面的話,離開區間時
                    # 補丟的那個 KeyboardInterrupt 會讓它撤不掉,收尾就同時說
                    # 「已經改掉 X」跟「可能正在換 X」—— 自己跟自己打架。
                    _TOUCHED['replacing'] = ''
            except BaseException as _e:
                # ⚠️ 旗標**只有在確定 os.replace 沒做**的時候才可以撤銷。
                #    這一段裡除了 os.replace 本身沒有別的東西會丟例外,
                #    所以「不是 Ctrl-C 的例外」= 換名失敗 = 可以安心撤銷;
                #    是 Ctrl-C 就留著,讓收尾用比較保守的那句話。
                if not isinstance(_e, KeyboardInterrupt):
                    _TOUCHED['replacing'] = ''
                w.close()
                _drop(tmp)
                raise
    except BaseException as e:
        # Ctrl-C 的狀態說明交給 __main__ 統一講(它才看得到還原那條路走過沒有),
        # 這裡不重複印一次,只留下「中間檔有沒有殘留」那一段。
        kbd = isinstance(e, KeyboardInterrupt)
        if not kbd:
            print('  🔴 寫到一半停下來了:%s' % e)
            if done:
                print('     **已經改掉的檔**:%s' % '、'.join(done))
                print('     其餘的沒動。要全部退回去:--restore-write "%s"' % gamedir)
            else:
                print('     還沒有任何一個檔被改完。')
        # 收尾沒清掉的中間檔要點名,不然它們會安靜地留在遊戲資料夾裡。
        left = [x for x in sorted(os.listdir(db)) if _is_leftover_tmp(x)]
        if left:
            print('     資料夾裡留下了沒清掉的中間檔,可以自己刪掉:%s' % '、'.join(left))
        # Ctrl-C 原封不動往上丟,交給 __main__ 用 130 收尾(不是 1)。
        # 「使用者自己按了中斷」跟「程式失敗了」在指令碼裡是兩件事,
        # 而且上面那份 _TOUCHED 才講得出「換過去了沒有」。
        if kbd:
            raise
        raise Stop('沒有寫完 —— 先照上面那行還原,把原因排掉再重跑。')

    # ── 第 5 步 ──
    # 複驗:全部讀回來逐項比對
    # 「我以為我寫進去了」跟「它真的在檔案裡」是兩件事。這一步不是儀式,
    # 它抓得到欄號查錯、行號對錯、編碼被換掉這一類靜默的失敗。
    bad = []
    for fname, p in plans.items():
        hdr2, _ = load(db, fname)
        raw = open(os.path.join(db, fname), 'rb').read().decode('latin-1')
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines2 = raw.split(nl)
        for ln, idx, v, pid, field, _o in p['items']:
            d = dict((int(c.strip().split(None, 1)[0]),
                      c.strip().split(None, 1)[1] if len(c.strip().split(None, 1)) > 1 else '')
                     for c in lines2[ln].split(',')
                     if c.strip().split(None, 1)[0].isdigit())
            if str(num(d, idx)) != v:
                bad.append((fname, pid, field, v, num(d, idx)))
    if bad:
        print('  🔴 寫進去了但讀回來有 %d 個對不上,跑 --restore-write 還原:' % len(bad))
        for b in bad[:8]:
            print('     %s %s %s 應該 %s 讀回 %s' % b)
        return 1
    print('  ✅ %d 個欄位都寫好了,讀回來逐項相符。' % total)
    print('     要退回去:--restore-write "%s"' % gamedir)
    return 0


def roster_shape(path):
    """把一個名單檔量成 (表頭欄數, 資料列數, 最後一列有沒有收尾)。不像名單就回 None。

    這四個檔都是純文字名單,形狀固定:第一列是表頭(每一格「欄號 空格 欄名」),
    之後每一列一位球員,而且**每一列都以「,;」收尾**。本站在剛安裝好的原版與
    被模組疊過的測試機兩份名單上量過 attrib / rhattrib / lhattrib / pitcher,
    都是這個形狀。有了形狀,就不必只靠檔案大小去猜備份完不完整。
    """
    try:
        raw = open(path, 'rb').read()
    except OSError:
        return None
    if not raw:
        return None
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.split(nl)
    cols = 0
    for c in lines[0].rstrip(b';,').split(b','):
        a = c.strip().split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            cols += 1
    # 表頭連兩欄都湊不出來 = 這不是名單,或者連表頭都被截掉了。
    if cols < 2:
        return None
    body = [l for l in lines[1:] if l.strip()]
    return cols, len(body), bool(body) and body[-1].rstrip().endswith(b';')


def _backup_ok(bak, dst):
    """還原之前確認備份是完整的。回傳「不敢用的理由」,沒問題就回 None。

    2026-08-30 上線前資安稽核加了三道(0 bytes / 最後一行不完整 / 不到正本一半)。
    2026-09-05 覆驗發現那三道**擋不住截掉四成的備份**:把 840,643 bytes 的名單
    截到 504,192 bytes 又剛好停在列界,三道全過,腳本印「✅ 還原了 1 個檔」,
    四成球員就這樣不見了,而使用者以為救回來了。

    所以現在改成用格式驗,四道:
      1. 0 bytes
      2. 備份自己的形狀讀不出來(表頭不成立)
      3. 備份的最後一列沒有以「;」收尾 —— 截在半列
      4. 跟現在那個檔比:欄數不同,或備份的**列數比較少**
         這支腳本只換格子裡的值,不增列、不刪列、不動欄位數,
         所以兩邊的列數與欄數本來就該一模一樣。
         備份列數**比較多**不擋:那代表壞掉的是現在那個檔,而那正是要還原的理由。

    只有現在那個檔連形狀都讀不出來(它自己就是壞的)時,才退回「不得小於一半」
    那條大小地板 —— 那時候已經沒有格式可以比了。
    """
    n = os.path.getsize(bak)
    if n == 0:
        return '備份是 0 bytes'
    shape = roster_shape(bak)
    if shape is None:
        return '備份讀不出名單的形狀(表頭不成立),不像是完整的名單'
    b_cols, b_rows, b_tail = shape
    if not b_tail:
        return '備份的最後一列沒有收尾,它是被截斷的'
    live = roster_shape(dst) if os.path.exists(dst) else None
    if live is not None:
        l_cols, l_rows, _ = live
        if b_cols != l_cols:
            return ('備份的表頭有 %d 欄,現在那個檔有 %d 欄,兩邊不是同一種名單'
                    % (b_cols, l_cols))
        if b_rows < l_rows:
            return ('備份只有 %d 列球員,現在那個檔有 %d 列,備份是被截斷的'
                    % (b_rows, l_rows))
    elif os.path.exists(dst):
        # 現在那個檔連形狀都讀不出來,沒有格式可比,只剩大小地板這條退路。
        live_n = os.path.getsize(dst)
        if live_n > 0 and n * 2 < live_n:
            return ('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes,差太多了(不到一半)'
                    % (n, live_n))
    return None


def cmd_restore_write(gamedir):
    """--restore-write:把這支腳本留下的備份蓋回去。

    掃整個 database 資料夾找 .ratingsbak,一個一個驗過再還原。
    **備份留著不刪** —— 還原完就把救命的那份丟掉,是在賭下一次不會出事。
    """
    db = os.path.join(gamedir, 'data', 'database')
    # 這是救命路徑,而會走到這裡的人多半正在手忙腳亂。路徑打錯時要給一句中文,
    # 不是 os.listdir 丟出來的英文堆疊(全腳本只有這裡漏掉,其他指令都好好地擋著)。
    if not os.path.isdir(db):
        raise Stop('找不到 %s —— 遊戲資料夾的路徑對嗎?' % db)
    _TOUCHED['gamedir'] = gamedir
    # 走到這裡代表使用者是來還原的。收尾那句話要照這條路講(理由見 _TOUCHED)。
    _TOUCHED['cmd'] = 'restore'
    n_ = 0
    refused = []
    failed = []
    for f in sorted(os.listdir(db)):
        if not f.endswith(WRITE_BAK):
            continue
        bak = os.path.join(db, f)
        orig = os.path.join(db, f[:-len(WRITE_BAK)])
        # 還原前先驗備份。壞掉的備份寧可不用:
        # 用它蓋回去等於把正本也弄壞,而且使用者會以為已經救回來了。
        _why = _backup_ok(bak, orig)
        if _why:
            print('  🔴 %s 不敢用:%s' % (f, _why))
            print('     多半是備份途中被中斷。請改用你自己另外留的那一份。')
            refused.append(f)
            continue
        # 還原本身也要是原子的,而且換過去之前要先讀回來對過 —— 細節見 atomic_restore。
        # 「已經還原了」這一筆要在**不可中斷區間裡**跟換名一起記,
        # 所以交給 atomic_restore 在區間內呼叫,不是等它回來才記
        # (理由同 cmd_write:Ctrl-C 卡在中間會讓帳本說謊)。
        try:
            atomic_restore(bak, orig, on_replaced=lambda o=orig:
                           _TOUCHED['restore'].append(os.path.basename(o)))
        except BaseException as e:
            # 一個檔還原失敗**不可以中斷整趟**。本站實測過:把 pitcher.dat 鎖住
            # 之後,原本會在它身上直接結束,排在後面的 rhattrib.dat 明明改過、
            # 備份也是好的,卻連試都沒試 —— 使用者以為救過了,實際上只救了一半。
            # 救援要盡量多救,救不動的最後一起點名。
            # 唯一的例外是 Ctrl-C:那不是「這個檔救不動」,是使用者要停。
            # 講成「還原失敗」會讓人以為備份壞了跑去找別的備份,所以分開講;
            # 而且不可以繼續往下救(那等於無視他按的那一下),往上丟由 __main__ 用 130 收尾。
            if isinstance(e, KeyboardInterrupt):
                # 三態各講各的。**不可以一律說「沒有被動到」** ——
                # 中斷有可能是在換名做完、離開不可中斷區間的時候才補丟出來的,
                # 那時候這個檔其實已經還原好了。本站用變體腳本量過:舊版在這裡
                # 印「attrib.dat 沒有被動到」,而它的 sha256 已經是備份那一顆了。
                nm = os.path.basename(orig)
                print('  ⏹ 在 %s 上被中斷。' % nm)
                if nm in _TOUCHED['restore']:
                    print('     %s **已經還原好了**,是換完之後才停下來的。' % nm)
                elif _TOUCHED['replacing'] == nm:
                    print('     ⚠️ 中斷的時候**正在替換** %s —— 它可能已經換過去了。'
                          '請再跑一次 --restore-write,或自己拿 %s 備份比對。'
                          % (nm, WRITE_BAK))
                else:
                    print('     %s **沒有被動到**,還是還原之前的樣子。' % nm)
                raise
            print('  🔴 %s 還原失敗:%s' % (f, e))
            print('     %s **沒有被動到**,還是還原之前的樣子。' % os.path.basename(orig))
            failed.append(f)
            continue
        # 登記已經在 atomic_restore 的不可中斷區間裡做過了,這裡只數數。
        n_ += 1
    if not n_:
        # ⚠️ 這兩句不可以合成一句。備份被守門擋下來的時候,備份是**存在**的,
        #    而且使用者其實已經寫過了 —— 他的遊戲檔正停在改過的狀態。
        #    在那個情境印「你還沒用 --write 寫過」是一句假話,而且會害一個
        #    正在搶救檔案的人以為自己根本沒改過,不再去找備份。
        if refused or failed:
            raise Stop('找到 %d 份 %s 備份,但**一個都沒還原**(%d 份沒通過檢查、'
                       '%d 份寫不回去)—— 你的遊戲檔還停在改過的狀態。'
                       '請改用你自己另外留的那一份完整備份。'
                       % (len(refused) + len(failed), WRITE_BAK, len(refused), len(failed)))
        raise Stop('找不到任何 %s 備份 —— 你還沒用 --write 寫過。' % WRITE_BAK)
    print('  ✅ 還原了 %d 個檔。備份留著沒刪。' % n_)
    if refused or failed:
        # 一部分還原了、一部分沒有,結果是「半新半舊」。這種狀態要講出來,
        # 而且不可以回 0 —— 回 0 等於告訴呼叫的人「都好了」。
        print('  ⚠️ 還有 %d 個檔**沒有還原**:%s'
              % (len(refused) + len(failed), '、'.join(refused + failed)))
        print('     現在這份名單是半新半舊的。請用你自己另外留的那一份把它們補回去。')
        return 1
    return 0


def _interrupt_report():
    """Ctrl-C 之後印那幾句「我的遊戲檔現在是什麼狀態」。

    ⚠️ 中斷之後最重要的一句話就是這個。_TOUCHED 記的是**真的做過 os.replace
    的那些**,所以「什麼都沒有動到」這句話只有在帳本是空的、**而且這一趟是
    --write**的時候才敢講。

    四種話,對應帳本的四種狀態:
      · 正在換 X          換名做到一半被打斷,帳本還來不及記。不敢說沒動,也不敢說換好了。
      · 已經改掉 A、B     --write 換過去的那些,叫他跑 --restore-write。
      · 已經還原 A、B     --restore-write 換回去的那些,叫他再跑一次接著做完。
      · 一個都還沒換      **這一句在兩條路上意思相反**,所以要看 cmd 分開講。

    最後那一句是 2026-09-11 補的分支。在這之前 --restore-write 一個檔都還沒
    還原就被 Ctrl-C 打斷時,印的是「你的遊戲檔**什麼都沒有動到**」—— 而會跑
    還原的人正是因為檔案被改過才來的。本站用變體腳本量過(中斷落在 atomic_restore
    進入不可中斷區間之前):當下四個名單檔的 sha256 逐一比對**全部**還停在
    --write 改過的狀態,螢幕上卻印著粗體的「什麼都沒有動到」。那是一句假話,
    而且會害一個正在搶救檔案的人不再回頭還原。

    獨立成一個函式是為了下得了餌:`if __name__ == '__main__'` 那一段沒有辦法
    在 --selftest 裡呼叫,包成函式之後餌 9 才驗得到它到底講了什麼話。
    """
    print()
    print('  ✗ 中斷了(你按了 Ctrl-C)。')
    # 三態的第三種先講:換名做到一半被打斷,帳本還來不及記。
    # 這種時候既不可以說「沒動到」,也不敢說「已經改好了」。
    if _TOUCHED['replacing']:
        print('     ⚠️ 中斷的時候**正在替換 %s** —— 它可能已經換過去了。'
              % _TOUCHED['replacing'])
        print('     請跑 --restore-write "%s" 還原,或自己拿 %s 備份比對。'
              % (_TOUCHED['gamedir'] or '<遊戲資料夾>', WRITE_BAK))
    if _TOUCHED['write']:
        print('     **已經改掉的檔**:%s' % '、'.join(_TOUCHED['write']))
        print('     其餘的沒動。要全部退回去:--restore-write "%s"'
              % (_TOUCHED['gamedir'] or '<遊戲資料夾>'))
    elif _TOUCHED['restore']:
        print('     **已經還原的檔**:%s' % '、'.join(_TOUCHED['restore']))
        print('     其餘的還停在改過的狀態,再跑一次 --restore-write 會接著做完。')
    elif not _TOUCHED['replacing']:
        if _TOUCHED['cmd'] == 'restore':
            # ⚠️ 這一句不可以講成「什麼都沒有動到」。這一趟沒有還原到任何檔,
            #    不代表檔案沒被改過 —— 剛好相反,他是因為改過才來還原的。
            print('     這一趟**沒有還原到任何檔** —— 你的遊戲檔還停在你按下 '
                  'Ctrl-C 之前的樣子(先前用 --write 改過的話,那就是改過的狀態)。')
            print('     要接著還原:再跑一次 --restore-write "%s"'
                  % (_TOUCHED['gamedir'] or '<遊戲資料夾>'))
        else:
            print('     還沒有任何一個檔被換過去 —— 你的遊戲檔**什麼都沒有動到**。')
    print()


def selftest():
    """--selftest:不碰任何遊戲檔,在系統暫存資料夾裡把會動檔案的那幾條路走一遍。

    重點不是「跑得完」,是**每一道守門都下了餌** —— 先證明守門壞掉的時候它真的會叫。
    只驗正向的測試會在功能整個壞掉時照樣全綠,那種測試比沒有更危險。

    九個餌(1~7 對應 2026-09-05 那一輪,8、9 是 2026-09-11 補的):
      1. 事先擺一顆叫「<名單>.ratingsbak.part」的符號連結指到資料夾外面 ——
         跑完備份之後,外面那個檔必須**一個位元組都沒變**。
         (舊版會跟著它先截成 0 再灌進名單內容,這就是那個洞。)
      2. 備份檔名本身是符號連結 → 要被擋(Stop),不是跟著它寫。
      3. 名單檔本身是符號連結 → 同上。
      4. 指向不存在目標的符號連結(dangling)也要擋 —— exists() 對它回 False,
         這個餌就是在證明「不可以用 exists() 判斷」。
      5. 還原走到一半失敗(把 os.replace 換成會丟例外的假貨)→
         正本必須逐位元組原封不動,而且暫存檔不可以留下來。
      6. 讀回來跟備份對不起來(把 _sha256 換成會回不同值的假貨)→
         不可以換過去,正本一樣原封不動。
      7. 一個叫 ratings.csv 的符號連結指到名單檔 → 兩層都要擋:
         --out 那道名字守門(check_out),以及真正寫檔的 write_export
         (它在換名之前會再驗一次,擋的是「驗過之後才冒出來」的連結)。
      8. --write 要改的四個檔裡,**排在最後**那一個是符號連結 →
         排在它前面的檔一個位元組都不可以被動到,連備份都不可以做出來。
         (舊版是寫到那個檔才驗,前面三個早就換過去了 —— 而檔頭寫著
          「整個停下來不寫」。這個餌守的就是那句話。)
      9. --restore-write 一個檔都還沒還原就被 Ctrl-C 打斷 → 收尾**不可以**
         說「什麼都沒有動到」(他的檔案還停在改過的狀態);
         同一個情境在 --write 那條路上照舊要說「什麼都沒有動到」。

    跑完會把暫存資料夾刪掉;中途 assert 失敗就留著給人看現場。

    ⚠️ 不可以在 python3 **-O** 底下跑:那個旗標會把 assert 整段拿掉,
    底下每一個餌的判斷句就一條都不執行,螢幕上照樣一路 ✅ ——
    那是一片**假的綠燈**,比沒有測試更危險。所以第一件事就是把它擋掉。
    """
    if not __debug__:
        raise Stop('--selftest 不能在 python3 -O 底下跑:-O 會把 assert 整段拿掉,'
                   '底下那些餌一個都不會執行,你會看到一片假的綠燈。'
                   '請拿掉 -O 再跑一次。')
    print('\n  自我測試(不碰任何遊戲檔)')
    print('  ' + '-' * 60)
    root = tempfile.mkdtemp(prefix='mvp_ratings_selftest_')
    db = os.path.join(root, 'data', 'database')
    os.makedirs(db)

    # 資料夾外面那個「不該被動到」的檔,是餌 1~4 的證人。
    outside = os.path.join(root, 'outside_do_not_touch.txt')
    GUARD = 'このファイルは触ってはいけない / do not touch'.encode('utf-8')
    with open(outside, 'wb') as f:
        f.write(GUARD)

    # 一份最小的假名單。形狀跟真的一樣:表頭一列、資料一列、每列以「,;」收尾。
    live = os.path.join(db, 'attrib.dat')
    body = ('0 first_name,1 last_name,2 playerattrib_speed;\r\n'
            '0abc00001,0 Test,1 Player,2 50,;\r\n')
    with open(live, 'wb') as f:
        f.write(body.encode('latin-1'))
    os.chmod(live, 0o644)
    before = open(live, 'rb').read()
    bak = live + WRITE_BAK

    # ⚠️ Windows 沒開「開發人員模式」時一般帳號建不了符號連結。
    #    那種機器上餌 1~4、餌 7、餌 8 做不出來 —— **要說出來,不可以當成通過**。
    #    (餌 5、6、9 與正例不需要符號連結,照跑。)
    _probe = os.path.join(root, 'symlink_probe')
    try:
        os.symlink(outside, _probe)
        os.remove(_probe)
        can_link = True
    except (OSError, NotImplementedError, AttributeError):
        can_link = False
        print('  ⚠️ 這台機器建不了符號連結(Windows 沒開開發人員模式時就是這樣)。')
        print('     餌 1~4、餌 7、餌 8 這一趟**沒有跑到**,不是通過。'
              '想驗那六個,請在 macOS / Linux 上跑一次。')

    # ── 餌 1:舊版那個猜得到的暫存檔名被人先佔走 ──
    if can_link:
        legacy = bak + '.part'
        os.symlink(outside, legacy)
        atomic_backup(live, bak)
        assert open(outside, 'rb').read() == GUARD, \
            '餌 1 失敗:資料夾外面那個檔被寫壞了 —— 暫存檔名又變回猜得到的了'
        assert os.path.islink(legacy), '餌 1 失敗:那顆符號連結本身不該被動到'
        assert open(bak, 'rb').read() == before, '備份的內容跟來源不一樣'
        assert (os.stat(bak).st_mode & 0o777) == (os.stat(live).st_mode & 0o777), \
            '備份的權限沒有照來源抄(mkstemp 預設 0600,別人會打不開)'
        os.remove(legacy)
        os.remove(bak)
        print('  ✅ 餌 1  猜得到的舊暫存檔名被佔走時,資料夾外面的檔沒被動到')

        # ── 餌 2:備份檔名本身是符號連結 ──
        os.symlink(outside, bak)
        try:
            atomic_backup(live, bak)
        except Stop:
            pass
        else:
            raise AssertionError('餌 2 失敗:備份檔是符號連結竟然照寫')
        assert open(outside, 'rb').read() == GUARD, '餌 2 失敗:外面那個檔被動到了'
        os.remove(bak)
        print('  ✅ 餌 2  備份檔是符號連結 → 擋下來')

        # ── 餌 3:名單檔本身是符號連結 ──
        fake = os.path.join(db, 'pitcher.dat')
        os.symlink(outside, fake)
        try:
            atomic_backup(fake, fake + WRITE_BAK)
        except Stop:
            pass
        else:
            raise AssertionError('餌 3 失敗:名單檔是符號連結竟然照讀照備份')
        os.remove(fake)
        print('  ✅ 餌 3  名單檔是符號連結 → 擋下來')

        # ── 餌 4:dangling 符號連結(exists() 對它回 False)──
        dang = os.path.join(db, 'lhattrib.dat' + WRITE_BAK)
        os.symlink(os.path.join(root, 'no_such_target'), dang)
        assert not os.path.exists(dang) and os.path.lexists(dang), \
            '餌 4 本身沒意義了:這個平台的 exists() 對 dangling 連結不回 False'
        try:
            atomic_backup(live, dang)
        except Stop:
            pass
        else:
            raise AssertionError('餌 4 失敗:dangling 符號連結沒被擋 —— 又用 exists() 判斷了')
        os.remove(dang)
        print('  ✅ 餌 4  dangling 符號連結 → 擋下來(不是用 exists() 判斷的)')

    # 下面兩個餌要一份好的備份跟一顆「已經被改過」的正本。
    atomic_backup(live, bak)
    with open(live, 'wb') as f:
        f.write(b'0 broken;\r\n')
    now = open(live, 'rb').read()

    # ── 餌 5:還原走到一半失敗 ──
    real_replace = os.replace

    def _boom(a, b):
        raise OSError('餌 5:假裝 os.replace 失敗')

    os.replace = _boom
    try:
        try:
            atomic_restore(bak, live)
        except OSError:
            pass
        else:
            raise AssertionError('餌 5 失敗:換名丟例外了還說還原成功')
        # 同一個性質在**匯出**那條路上也要成立:換名失敗時目的檔必須還是原來那個。
        # 這幾行擋的是「偷偷改回 open(path, 'w') 直接開」——
        # 那種寫法會**先把目的檔截成 0** 再寫,os.replace 根本還沒輪到,
        # 使用者原本那張表(可能是他自己手改過的)就已經沒了。
        _exp = os.path.join(root, 'export_must_survive.csv')
        with open(_exp, 'wb') as f:
            f.write(b'old,content\r\n')
        try:
            write_export(_exp, b'new,content\r\n')
        except OSError:
            pass
        else:
            raise AssertionError('餌 5 失敗:匯出檔換名丟例外了還當成寫好了')
        assert open(_exp, 'rb').read() == b'old,content\r\n', \
            '餌 5 失敗:匯出檔換名失敗卻已經把目的檔改掉了 —— 是不是又用 open(path, \'w\') 了?'
        assert not [x for x in os.listdir(root) if _is_leftover_tmp(x)], \
            '餌 5 失敗:匯出檔的暫存檔沒清掉'
    finally:
        os.replace = real_replace
    assert open(live, 'rb').read() == now, '餌 5 失敗:還原半路失敗卻動到了正本'
    _left = [x for x in os.listdir(db) if _is_leftover_tmp(x)]
    assert not _left, '餌 5 失敗:暫存檔沒清掉:%s' % _left
    # 換名失敗那條路要把「正在換」的旗標撤乾淨,不然下一次真的中斷時
    # 會冤枉一個根本沒被動到的檔。
    # ⚠️ 這一句一定要**貼著餌 5**。擺到函式最後面就永遠測不到東西 ——
    #    後面那個成功的正例會把旗標清掉,壞掉的版本照樣一路綠。本站踩過。
    assert not _TOUCHED['replacing'], \
        '餌 5 失敗:換名失敗了卻留著「正在換」的旗標'
    print('  ✅ 餌 5  還原半路失敗 → 正本逐位元組原封不動、暫存檔清乾淨')

    # ── 餌 6:讀回來跟備份對不起來 ──
    real_sha = globals()['_sha256']
    _seq = iter(('aaaaaaaa', 'bbbbbbbb'))
    globals()['_sha256'] = lambda p: next(_seq)
    try:
        try:
            atomic_restore(bak, live)
        except Stop:
            pass
        else:
            raise AssertionError('餌 6 失敗:讀回來對不上竟然照樣換過去')
    finally:
        globals()['_sha256'] = real_sha
    assert open(live, 'rb').read() == now, '餌 6 失敗:對不上還是把正本蓋掉了'
    assert not [x for x in os.listdir(db) if _is_leftover_tmp(x)], \
        '餌 6 失敗:暫存檔沒清掉'
    print('  ✅ 餌 6  寫出來跟備份對不上 → 不換過去,正本原封不動')

    # ── 正例:真的還原一次,要逐位元組等於備份 ──
    atomic_restore(bak, live)
    assert open(live, 'rb').read() == before, '還原之後應該逐位元組等於備份'
    assert (os.stat(live).st_mode & 0o777) == 0o644, \
        '還原之後權限跑掉了(mkstemp 是 0600,要抄回正本原本那個)'
    assert not [x for x in os.listdir(db) if _is_leftover_tmp(x)], '還原完不該留下暫存檔'
    print('  ✅ 正例  還原之後逐位元組等於備份,權限也一樣')

    # ── 餌 7:--out 指到符號連結 ──
    if can_link:
        lnk = os.path.join(root, 'ratings.csv')
        os.symlink(live, lnk)
        try:
            check_out(lnk)
        except Stop:
            pass
        else:
            raise AssertionError('餌 7 失敗:--out 指到符號連結沒被擋 —— '
                                 '副檔名那一關擋不住這種寫法')
        # 第二層:真正寫檔的那一支自己也要擋。check_out 是在流程最前面驗的,
        # 驗完到寫出去中間隔著讀 CSV 跟計算 —— 那段時間裡才擺上去的連結
        # 只有這一層擋得住。餌就是「直接拿一顆連結叫它寫」。
        _lnk_before = open(live, 'rb').read()
        try:
            write_export(lnk, b'x,y,z\r\n')
        except Stop:
            pass
        else:
            raise AssertionError('餌 7 失敗:write_export 跟著符號連結寫了')
        assert open(live, 'rb').read() == _lnk_before, \
            '餌 7 失敗:連結指到的那個檔被寫壞了'
        os.remove(lnk)
        # 正常的路徑要寫得出來,而且權限不可以是 mkstemp 的 0600
        # (沒有這一句,守門「全部擋掉」也會通過 —— 那是壞掉的另一種樣子)。
        _out = os.path.join(root, 'ok.csv')
        write_export(_out, b'a,b\r\n1,2\r\n')
        assert open(_out, 'rb').read() == b'a,b\r\n1,2\r\n', '匯出檔的內容不對'
        assert (os.stat(_out).st_mode & 0o777) == _new_file_mode(), \
            '匯出檔的權限不是「一般新檔」該有的 —— 留在 mkstemp 的 0600 會害人打不開'
        print('  ✅ 餌 7  --out 指到符號連結 → 擋下來')

    # ── 餌 8:寫入的起飛前檢查 —— 排在最後的那個檔是連結時,前面的一個都不可以被動到 ──
    if can_link:
        g8 = os.path.join(root, 'g8')
        db8 = os.path.join(g8, 'data', 'database')
        os.makedirs(db8)
        # ⚠️ 連結要指到一份**合法的名單**。指到隨便一個檔的話,cmd_write 在第 2 步
        #    (整批不寫)就放棄了,根本走不到第 4 步 —— 那樣這個餌等於沒下。
        out_roster = os.path.join(root, 'outside_roster.dat')
        with open(out_roster, 'wb') as f:
            f.write(body.encode('latin-1'))
        out_before = open(out_roster, 'rb').read()
        pit = os.path.join(db8, 'pitcher.dat')
        with open(pit, 'wb') as f:
            f.write(('0 first_name,1 last_name,2 pitchattrib_stamina;\r\n'
                     '0abc00001,0 Test,1 Player,2 50,;\r\n').encode('latin-1'))
        os.chmod(pit, 0o644)
        pit_before = open(pit, 'rb').read()
        # WRITE_MAP 的順序是 rhattrib → lhattrib → pitcher → attrib,所以
        # attrib.dat 是**最後**那一個:舊版會先把 pitcher.dat 改掉才發現連結。
        os.symlink(out_roster, os.path.join(db8, 'attrib.dat'))
        csv8 = os.path.join(root, 'g8.csv')
        with open(csv8, 'wb') as f:
            f.write(b'id,first_name,last_name,stamina,speed\r\n'
                    b'0abc00001,Test,Player,77,77\r\n')
        # 帳本借來用一下就要還回去(這是自我測試,不可以留下「動過遊戲檔」的痕跡)。
        _keep = dict(_TOUCHED)
        _buf = io.StringIO()
        _stdout = sys.stdout
        sys.stdout = _buf
        try:
            try:
                cmd_write(g8, csv8, True)
            except Stop:
                pass
            else:
                raise AssertionError('餌 8 失敗:名單檔是符號連結竟然沒有整個停下來')
        finally:
            sys.stdout = _stdout
            _TOUCHED.clear()
            _TOUCHED.update(_keep)
        assert open(pit, 'rb').read() == pit_before, \
            '餌 8 失敗:排在後面的 attrib.dat 是連結,pitcher.dat 卻已經被改掉了 —— ' \
            '那兩道 _refuse_symlink 是不是又搬回迴圈裡面了?'
        assert not os.path.lexists(pit + WRITE_BAK), \
            '餌 8 失敗:連第一個檔的備份都做出來了,代表是動手之後才發現連結的'
        assert '已經改掉的檔' not in _buf.getvalue(), \
            '餌 8 失敗:輸出自己承認改掉了檔 —— 起飛前檢查沒有擋在動手之前'
        assert open(out_roster, 'rb').read() == out_before, \
            '餌 8 失敗:資料夾外面那份名單被跟著寫了'
        assert not [x for x in os.listdir(db8) if _is_leftover_tmp(x)], \
            '餌 8 失敗:暫存檔沒清掉'
        print('  ✅ 餌 8  最後一個檔是符號連結 → 前面的檔一個位元組都沒動')

    # ── 餌 9:中斷收尾在還原那條路上不可以說「什麼都沒有動到」 ──
    def _report_says(cmd):
        """把帳本擺成「這一趟一個檔都還沒換過去」,看收尾到底講了什麼話。"""
        _keep = dict(_TOUCHED)
        _TOUCHED.update({'write': [], 'restore': [], 'replacing': '',
                         'gamedir': os.path.join(root, 'g'), 'cmd': cmd})
        _buf = io.StringIO()
        _stdout = sys.stdout
        sys.stdout = _buf
        try:
            _interrupt_report()
        finally:
            sys.stdout = _stdout
            _TOUCHED.clear()
            _TOUCHED.update(_keep)
        return _buf.getvalue()

    _r = _report_says('restore')
    assert '什麼都沒有動到' not in _r, \
        '餌 9 失敗:--restore-write 一個檔都還沒還原時竟然說「什麼都沒有動到」 —— ' \
        '會跑還原的人正是因為檔案被改過才來的,這句話會害他不再回頭還原'
    assert '沒有還原到任何檔' in _r and '--restore-write' in _r, \
        '餌 9 失敗:還原那條路沒有講清楚「這一趟沒有還原到任何檔、要再跑一次」'
    _w = _report_says('write')
    assert '什麼都沒有動到' in _w, \
        '餌 9 失敗:--write 一個檔都還沒換過去時應該照舊說「什麼都沒有動到」 —— ' \
        '把兩條路都改成還原那一句話,一樣是說謊'
    print('  ✅ 餌 9  中斷收尾:還原那條路不說「什麼都沒有動到」,寫入那條路照舊說')

    # ── 暫存檔名:兩次不可以撞名,而且收尾要認得出自己開的檔 ──
    w1, t1 = _open_beside(live, 'tmp')
    w2, t2 = _open_beside(live, 'tmp')
    w1.close()
    w2.close()
    assert t1 != t2, '兩顆暫存檔撞名了 —— mkstemp 沒在用?'
    assert _is_leftover_tmp(os.path.basename(t1)), \
        '收尾點名認不出自己開的暫存檔(_open_beside 的 prefix 跟 _is_leftover_tmp 對不上)'
    _drop(t1)
    _drop(t2)
    print('  ✅ 正例  暫存檔名不撞、收尾點名認得出來')

    # ── Ctrl-C 的帳本:自我測試不該登記任何「動過遊戲檔」 ──
    # 四個鍵都要是空的。'replacing' 也要 —— 上面餌 5 的假 os.replace 丟過例外,
    # 那條路必須把「正在換」的旗標撤乾淨,不然真的中斷時會多冤枉一個檔。
    # 'cmd' 也要 —— 餌 8 借了帳本去跑一次 cmd_write,借完沒還回來的話,
    # 這一支之後任何一次真的中斷都會照「還原」那條路講話。
    assert not _TOUCHED['write'] and not _TOUCHED['restore'] \
        and not _TOUCHED['replacing'] and not _TOUCHED['cmd'], \
        '自我測試竟然在帳本上留下痕跡 —— 那 Ctrl-C 那句話就會說謊'
    # 不可中斷區間本身也要驗:訊號在區間裡到達時**不可以**立刻丟出來,
    # 離開區間之後**必須**照常丟出來。少了後半段就變成把 Ctrl-C 吃掉了。
    # 這裡直接呼叫「現在掛著的那個處理器」來假裝訊號到達,不真的送 SIGINT ——
    # 真的送在 Windows 上會直接把行程打掉,測不到東西。
    _order = []
    try:
        with _NoInterrupt() as _ni:
            assert signal.getsignal(signal.SIGINT) == _ni._remember, \
                '不可中斷區間沒有把 SIGINT 接管起來'
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
            _order.append('區間裡沒有立刻丟')
    except KeyboardInterrupt:
        _order.append('離開區間才丟')
    assert _order == ['區間裡沒有立刻丟', '離開區間才丟'], \
        '_NoInterrupt 沒有把 Ctrl-C 延後到區間之後:%s' % _order
    assert signal.getsignal(signal.SIGINT) != _ni._remember, \
        '離開區間之後沒有把原本的訊號處理器裝回去'
    print('  ✅ 正例  Ctrl-C 的帳本是空的(自我測試連遊戲資料夾都沒碰)')

    shutil.rmtree(root, ignore_errors=True)
    print('  ' + '-' * 60)
    # 數字要跟上面真的印出來的 ✅ 行數對得上,不然這一行自己就是一句假話。
    print('  全部通過(%d 個餌 + 3 個正例)。這一趟沒有碰到任何遊戲檔。'
          % (9 if can_link else 3))
    if not can_link:
        print('  ⚠️ 其中 6 個餌因為這台機器建不了符號連結而**沒有跑到**。')
    print('')
    return 0


def main():
    """指令分派。

    add_help=False 加上自己接 -h,是為了讓 --help 直接印檔頭那份說明
    (argparse 產生的清單講不出誤差、守門、配不出來那些事)。
    分派順序不是隨便排的:--selftest 與唯讀的 --check / --fit 排在前面,
    會動檔案的 --write / --restore-write 排在 --convert 前面,
    一次只做一件事。什麼都沒給就走 --demo,不碰任何檔案。
    """
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--fit', metavar='遊戲資料夾')
    ap.add_argument('--check', metavar='遊戲資料夾')
    ap.add_argument('--convert', metavar='stats.csv')
    ap.add_argument('--write', nargs=2, metavar=('遊戲資料夾', 'ratings.csv'))
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--restore-write', dest='restore_write', metavar='遊戲資料夾')
    ap.add_argument('--out', default='ratings.csv')
    ap.add_argument('-h', '--help', action='store_true')
    a = ap.parse_args()
    if a.help:
        print(__doc__)
        return 0
    if a.selftest:
        return selftest()
    if a.check:
        return cmd_check(a.check)
    if a.fit:
        return cmd_fit(a.fit)
    if a.write:
        return cmd_write(a.write[0], a.write[1], a.apply)
    if a.restore_write:
        return cmd_restore_write(a.restore_write)
    if a.convert:
        return cmd_convert(a.convert, a.out)
    return cmd_demo()


# 雙向自我測試:該給的要給,該擋的一個都不能漏
#
# 為什麼放在模組層而不是另外寫測試檔:這樣**每一次執行都會跑**,
# 使用者手上那一份如果被改壞了,第一個指令就會當場失敗,而不是靜靜算出錯的值。
# ⚠️ 唯一的例外是 python3 **-O**:那個旗標會把 assert 整段拿掉,
#    所以下面那些正例與反例一條都不會執行(本站量過:-O 之下 __debug__ 是 False,
#    整段靜靜跳過)。照頁面上的指令跑不會遇到,但這句「每一次執行都會跑」
#    有這個前提,寫出來比較誠實。
# 為什麼要雙向:只測「該給的有給」會漏掉守門失效 —— 守門壞掉時正例照樣通過。
# 所以下面兩組缺一不可:先確認會算,再確認該擋的每一種都真的擋住。
assert compute('power_vs_rhp', tpa=3200, slg=0.612)[0] > 70, '強打者的力量應該高'
assert compute('power_vs_rhp', tpa=500, slg=0.300)[0] < 55, '普通打者不該被評成強打'
assert compute('stamina', g=30, ipg=6.5)[0] > 80, '先發投手續航力應該高'
assert compute('stamina', g=60, ipg=1.1)[0] < 55, '後援投手續航力應該低'
for _f, _kw in (('power_vs_rhp', dict(tpa=60, slg=0.612)),
                ('power_vs_lhp', dict(tpa=99, slg=0.500)),
                ('stamina', dict(g=9, ipg=6.0)),
                ('power', dict(ab=199, hr_rate=0.05, r_rate=0.15)),
                ('fielding', dict(ab=5000))):
    try:
        compute(_f, **_kw)
        raise AssertionError('%s 的守門沒擋住 %s' % (_f, _kw))
    except Stop:
        pass
_v, _w = compute('power_vs_rhp', tpa=200, slg=1.200)
assert _w and _v <= 96, '超出範圍時要夾住而且要講出來'

# 會動檔案的那三道守門也在這裡下餌。這幾個函式都是純算的(不碰硬碟),
# 所以可以放心每次執行都跑一遍。
# 正例:正常的值、正常的輸出檔名要放行。
assert value_ok('80') and value_ok('0') and value_ok('100'), '正常的值要放行'
# ⚠️ 這裡刻意寫成「資料夾/檔名」而不是光一個 ratings.csv:check_out 有一條
#    是看**上一層資料夾叫不叫 database**,而光一個檔名的上一層就是你執行腳本的
#    那個資料夾。把腳本放進 data/database 裡面執行的人(真的會有),
#    光一個檔名會讓這個正例自己被擋下來,整支腳本連 --demo 都跑不起來。
#    本站實測過那一種寫法:在 data/database 底下跑 --demo 直接 Stop。
assert check_out(os.path.join('out', 'ratings.csv')) is None, '正常的 CSV 檔名要放行'
# 反例:每一種寫壞名單的形態都要擋住。
#   '8,0'  Excel 某些地區設定存出來的小數 → 會把名單的一格拆成兩格
#   'ABC'  手填的文字 → 遊戲讀不懂的格子
#   '99999' / '101' 超出兩份名單量到的 0~100
#   '-1'   四個可寫欄位量到的最小值是 0,沒有負的
#   '8.0'  小數點寫不進去(名單那一格只放整數)
#   '²'    全形/上標數字 str.isdigit() 會回 True 但 int() 吃不下
for _bad in ('8,0', 'ABC', '99999', '101', '-1', '8.0', '', ' ', '²'):
    assert not value_ok(_bad), '「%s」不該被當成可以寫的值' % _bad
for _badout in ('attrib.dat', 'x.BIG', 'a/b/mvp2005.exe'):
    try:
        check_out(_badout)
        raise AssertionError('--out 指到 %s 應該被擋下來' % _badout)
    except Stop:
        pass

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Stop as e:
        print('\n  ✗ %s\n' % e)
        sys.exit(1)
    except KeyboardInterrupt:
        # 那幾句話統一在 _interrupt_report() 裡講(包成函式才下得了餌,見那邊的說明)。
        # 結束碼用 130(128 + SIGINT)不是 0 —— 回 0 等於告訴呼叫的人成功了,
        # 而使用者其實是在檔案改到一半的時候把它按停的。
        _interrupt_report()
        sys.exit(130)

# ─────────────────────────────────────────────────────────────
# MIT License · Copyright (c) 2026 toni
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ─────────────────────────────────────────────────────────────
