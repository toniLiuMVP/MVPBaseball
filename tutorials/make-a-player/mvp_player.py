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
mvp_player.py —— 把遊戲裡的一位球員改成你想要的球員。

這一支有**兩道門**:

  雙擊(不給參數)  → 一句一句問你,為了不會用電腦的人寫的
  給參數           → 匯出 / 匯入 CSV,一次改幾十個人,為了做整包模組的人寫的

    python3 mvp_player.py "<遊戲資料夾>" --export players.csv
    (用 Excel 或記事本改那張表)
    python3 mvp_player.py "<遊戲資料夾>" --import players.csv          ← 預覽
    python3 mvp_player.py "<遊戲資料夾>" --import players.csv --apply  ← 真的寫
    python3 mvp_player.py "<遊戲資料夾>" --restore
    python3 mvp_player.py --selftest    ← 自我測試(自己造一份名冊,不碰任何遊戲檔)

需要 Python 3.7 以上(本檔用到 str.isascii 與 sys.stdout.reconfigure,
兩個都是 3.7 才有的)。python.org 現在下載到的一定夠新;會不夠的情況是
「這台電腦本來就有一個很舊的 python」,那就把指令裡的 python3 換成新的那一支。

它能改三件事(而且只有這三件):
    名字(英文拼音)· 背號(0-99)· 跑壘速度(0-99)

為什麼只有三件,寫在頁面上,也寫在下面的註解裡。

輸入是什麼、輸出是什麼
---------------------
輸入:**遊戲資料夾**的路徑(不是名冊檔本身)。腳本自己去接
      `data/database/attrib.dat` —— 那個檔就是全遊戲的球員名冊,
      一位球員一行:第一格是**這一列的識別碼**(9 位十六進位字串,沒有欄號),
      第一格之後才是 46 個「欄號 空白 值」的格子,全部用逗號隔開,
      行尾再一個「,;」。整個檔是純文字。
      不給路徑時會自己猜(見 `guess_gamedirs`),猜不到就請你把資料夾拖進視窗。
      批次模式另外吃一張 CSV。

輸出:
  · 雙擊(不給參數)   螢幕上一問一答;確認之後改寫 `attrib.dat`,
                       旁邊留一份 `attrib.dat.playerbak`
  · --export 檔名.csv  匯出一張五欄的 CSV(id / first_name / last_name / jersey / speed),
                       **完全不動遊戲檔** —— 輸出檔名指到名冊本身、或指到任何
                       已經存在而結尾不是 .csv 的檔,都會被擋下來;
                       **輸出檔名是符號連結也會被擋下來**,而且它跟名冊走同一條
                       原子寫入(先寫隨機名字的暫存檔再換名),不是直接開檔覆蓋
  · --import 檔名.csv  預覽這張表會改動什麼,**完全不動遊戲檔**
  · --import … --apply 才真的寫回名冊
  · --restore          拿 `.playerbak` 蓋回名冊

安全網在哪
----------
1. **預覽在前、確認才寫。** 互動模式要打 y,批次模式要加 --apply。沒有「一鍵直接改」。
2. **第一次寫入前自動備份**,而且**已經有備份就保留最早那一份** ——
   第二次執行不會把「動手前的名冊」蓋成「已經改過的名冊」。
   備份用 `atomic_backup`:先寫一個**隨機名字**的暫存檔再換名,
   中斷不會留下半截卻叫得出名字的備份。
3. **整張表一起驗,錯一格就整張擋下。** 批次模式的任何一格不合格就
   一個位元組都不寫(見 `cmd_import` 的 errors),不會出現「改了一半」的名冊。
4. **先寫暫存檔再換名**,fsync、套回原檔權限、**換名之前先把暫存檔讀回來逐位元組比對**,
   全部過了才換名。寫入、還原、匯出 CSV **三個方向都走同一條**(`_atomic_put`)——
   中途斷電只會是「舊的完好」或「新的完整」,不會留下半截的名冊。
   暫存檔的名字是 `tempfile.mkstemp` 給的**隨機名字**,不是猜得到的 `.tmp` / `.part`;
   **任何要寫的目的檔**(名冊、備份、匯出的 CSV)本身是**符號連結**的話直接拒絕寫。
   前兩件是 2026-09-05 補的,匯出那一條是 2026-09-06 補的,
   為什麼補寫在 `atomic_backup` 上面那一段。
5. **寫完讀回來逐項複驗**,對不上就叫你還原,而且結束碼不會是 0。
   中途按 Ctrl-C 也會照實說:**檔案動了沒有是看三態登記,不是寫死一句「什麼都沒有動到」**。
   「換名 + 登記」是**不可中斷的一段**(`_NoInterrupt`):那期間按 Ctrl-C 會先被記下來,
   等登記完才丟出去,所以收尾講的話一定跟磁碟上的狀態一致。中斷一律以結束碼 130 收尾。
   **沒有人預料到的錯**(防毒軟體鎖住檔案、外接碟被拔掉)也走同一套三態:
   先用中文說名冊到底動了沒有、印還原的路,再把英文那一段留給回報用,結束碼 1 ——
   不會只丟一片英文 traceback 就結束(見 `_cli_entry`,2026-09-11 補)。
6. **兩條還原路徑走同一組把關**(`_restore_check`)——「--restore」與互動模式
   「打 r 還原」都要先過這五道才會覆蓋。編號跟程式裡的註解一致,
   所以下面**不是照號碼順序**列的 —— 先列只看備份自己的三道:
     (1) 備份不是 0 bytes
     (3) 表頭讀得懂(擋的是「指錯檔」)
     (4) 每一列的欄數都一樣,而且表頭剛好比資料列少一格
         (本站量過的十一份名冊都是表頭 47 格、資料列 48 格)
   以及兩道**拿現在那份名冊當尺**的(名冊自己壞到讀不出來時整組跳過,
   因為那正是最需要還原的時刻):
     (2) 備份不小於正本的一半(粗篩)
     (5) 列數跟正本一樣(這支工具是原地改,列數不會變)
   過了才寫,寫也是先寫暫存檔再換名,寫完把整份讀回來**逐位元組**比對。
   ⚠️ 第 (5) 道的副作用要知道:你如果在備份之後換了一份**球員人數不同**的
   名冊模組,再來還原會被擋下 —— 那時請自己在檔案總管/Finder 裡
   把 `.playerbak` 複製成 `attrib.dat`。

做不到的事
----------
· **不能加人。** 遊戲的名冊是固定筆數,這一課的做法是「接收」——
  挑一個你不在乎的球員,把他改成你要的那個人。
· **存不了中文。** 名冊 3,247 位球員的名字用到 56 種字元,非 ASCII 是 0 種。
  打中文會被 `check_name` 擋下來,而且檔案不會被動到。
· **改不了球隊。** 46 個欄位裡沒有球隊,換隊要在遊戲裡做。
· **其他能力欄位一律不開。** 理由見下面「為什麼只開這三欄」那一段:
  它們根本不是 0-99 的刻度,本站沒有解開它們。
· **不碰王朝存檔。** 只動 `attrib.dat` 這一個檔。已經開始的王朝會不會吃到這次修改,
  本站沒有測過。

法律與免責
    本教學與本腳本與 Electronic Arts 無任何官方關聯,不含 EA 的程式碼或資產,
    也不含任何規避技術保護措施的功能。僅供你對**自己合法取得的副本**使用,
    風險自負。本軟體按現狀提供,不附任何擔保。
    回報與下架:https://toniliumvp.github.io/MVPBaseball/report.html

—— toni的MVP模組補習班
"""

import csv
import io
import os
import re
import shutil
import signal
import sys
import tempfile
import traceback

# ── 畫面編碼的保險(2026-09-05 補)────────────────────────────
# Windows 繁體中文版把畫面**導向檔案或管線**時(`… > log.txt`),
# sys.stdout 的編碼會是 cp950,而本檔的提示文字裡有 ✅ ⚠️ 🔴 ——
# cp950 編不出這幾個字,print 到那一句就丟 UnicodeEncodeError 直接中止。
# 實測 `--export … > log.txt` 會踩到;`--import … --apply` 更麻煩:
# 檔案其實已經寫好、複驗也過了,卻炸在最後那句「✅ 都寫好了」,
# 使用者會以為失敗而跑去還原。
# 這裡**不改編碼**(改了中文會變亂碼),只把「編不出來的字元」換成 ?,
# 訊息照樣看得懂,而且不會中止。回報頁請人附畫面內容,靠的就是這一段。
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None and getattr(_stream, 'encoding', None):
            '✅⚠🔴'.encode(_stream.encoding)
    except (UnicodeEncodeError, LookupError):
        try:
            _stream.reconfigure(errors='replace')   # Python 3.7+
        except (AttributeError, ValueError, OSError):
            pass

# 這個常數**整支腳本沒有任何地方讀到**:只有這一行寫,沒有一行用。
# 留著是當自我說明:這支腳本自己叫什麼名字。改這一行不會有任何效果,
# 因為檔名在文字裡是逐字寫的(檔頭用法那幾行,加上 run_cli() 印給人看的那一句,
# 本檔另有 6 處),真要換檔名要改的是那 6 處。
APP = 'mvp_player.py'
# 備份的副檔名。本站每一課用不同的字尾,是為了讓「哪一支工具改過這個檔」一眼看得出來,
# 也讓打包工具(pack-a-mod 那一課)可以靠字尾認出你改過哪些檔。
BAK_SUFFIX = '.playerbak'

# ── 為什麼只開這三欄 ────────────────────────────────────────
# 2026-08-29 在本站測試機那份 data/database/attrib.dat 上量過,那個檔有 3,247 位球員。
# 這五欄在那一份名冊裡的實際範圍是:
#     speed            0 ~ 97   ← 只有這一欄是 0-99 的刻度
#     fielding         0 ~ 50
#     range            0 ~ 13
#     throwstrength    0 ~ 15
#     starpower        0 ~  4
# 上面那幾個數字跟著名冊走,不是遊戲的規格:剛安裝好的原版(英文版與中文版都量過)
# 有 2,921 位球員,同樣這五欄量到 speed 39 ~ 99、fielding 2 ~ 15、range 2 ~ 15、
# throwstrength 2 ~ 15、starpower 0 ~ 4。
# 其他「能力」欄位**根本不是 0-99 的評分**,刻度各自不同,本站沒有解開它們。
# 讓人往「守備」填 99(實際上限 50)不是危險,是沒有意義 —— 所以不開。
#
# 名字與背號是純顯示欄位,改了不影響任何衍生計算,所以開。
# 球隊不在這個檔裡(46 欄裡沒有球隊),換隊在遊戲裡做就好。
#
# ⚠️ 下面這個 tuple 是上面那段說明的摘要,**不是開關**。
#    跟上面的 APP 一樣,整支腳本沒有任何地方讀到它:只有這一行寫,沒有一行用。
#    真正決定開哪幾欄的是兩個地方:批次匯入 cmd_import() 裡那一組四元組
#    (('first_name', fn, 'name') 開頭的那一行),以及互動模式 main() 裡的四個問句。
#    要增減欄位得改那兩處,改這一行不會有任何效果。
#    (同一種標註見「球場超過 10MB 就當機」那一課:那支腳本裡用不到的
#     QFS 解壓縮與 FSH 圖片容器區塊,程式碼與頁面上都標著這一課沒有用到。)
EDITABLE = ('first_name', 'last_name', 'playerattrib_jerseynum', 'playerattrib_speed')


class Stop(Exception):
    """帶著一句人話中止。

    整支腳本只用這一種例外來表達「停下來,而且我知道為什麼」。
    檔尾統一接住它,印成一句中文再等使用者按 Enter ——
    這一課的讀者不是工程師,丟一整片 traceback 出去只會嚇到人,
    而每一個 Stop 的訊息都已經寫清楚下一步該怎麼辦。
    """


# ── 找遊戲資料夾 ────────────────────────────────────────────
def guess_gamedirs():
    """猜遊戲在哪。先看腳本自己旁邊,再看各平台的常見位置。

    ⚠️ 這裡**不可以**放任何寫死的絕對路徑。
       2026-08-29 第一版放了一條開發用的路徑當方便,結果:
         (一)測試跑起來直接改到真的名冊(還好工具自己的備份是好的)
         (二)那是班主任的私人路徑,而這支腳本會公開 —— 隱私掃描會抓到
       要指定目標請用環境變數 MVP_GAMEDIR,不要寫進程式碼。
    """
    # 環境變數最優先,而且**指定了就只認它**(不會再往下猜)。
    # 測試就是靠這一條把目標鎖在暫時的複本上,不會誤觸真正的遊戲。
    env = os.environ.get('MVP_GAMEDIR')
    if env:
        return [os.path.realpath(env)] if os.path.isfile(
            os.path.join(env, 'data', 'database', 'attrib.dat')) else []
    # 接著找腳本自己的附近。使用者多半是把工具丟進遊戲資料夾再雙擊,
    # 所以「腳本所在的資料夾」與它的上一層、上上層都要看。
    # sys.argv[0] 而不是 __file__:雙擊的情境下這個比較準。
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    cwd = os.getcwd()
    cands = [cwd, here, os.path.dirname(here), os.path.dirname(os.path.dirname(here))]
    # 最後才是各平台的常見安裝位置。這些是**通用**路徑,不是誰的私人路徑。
    home = os.path.expanduser('~')
    cands += [
        r'C:\Program Files (x86)\EA SPORTS\MVP Baseball 2005',
        r'C:\Program Files\EA SPORTS\MVP Baseball 2005',
        r'C:\Games\MVP Baseball 2005',
        os.path.join(home, 'MVP Baseball 2005'),
        os.path.join(home, 'Desktop', 'MVP Baseball 2005'),
    ]
    out = []
    for c in cands:
        try:
            # 判準是「這底下有沒有 data/database/attrib.dat」,不是「資料夾叫什麼名字」——
            # 使用者常常把遊戲資料夾改名,認名字會認不到。
            if c and os.path.isfile(os.path.join(c, 'data', 'database', 'attrib.dat')):
                # realpath 把符號連結與 ../ 攤平,免得同一份遊戲因為兩條不同的路徑
                # 被列成兩個選項,害使用者以為裝了兩套。
                rc = os.path.realpath(c)
                if rc not in out:
                    out.append(rc)
        except OSError:
            pass
    return out


# ── 讀寫名冊 ────────────────────────────────────────────────
# ⚠️ 這個檔是 CRLF(實測 3,248 個)。整份讀成 bytes、只動要動的那幾個位元組,
#    存回去也是 bytes —— 絕對不要用文字模式讀寫,那會把換行改掉。
def read_roster(path):
    """讀名冊,回傳 (原始位元組, 文字, 換行字元, 每一行, 表頭對照表)。

    名冊長這樣:第一行是表頭,46 格「欄號 空白 欄位名」;之後一位球員一行,
    **第一格是這一列的識別碼**(9 位十六進位字串,像 `0f58f3c1b`,這一格沒有欄號),
    第一格之後才是 46 個「欄號 空白 值」的格子,全部用逗號隔開,行尾再一個「,;」。
    這個形狀本站在三份名冊上量過:測試機那份 attrib.dat 3,247 位球員、
    剛安裝好的原版英文版與中文版各 2,921 位。三份都是「識別碼 + 46 格 + ,;」,
    表頭的欄號都是 0 到 45,識別碼都是 9 個十六進位字元。
    所以「跑壘速度」不是固定在第幾格,而是要先從表頭查出它的**欄號**,
    再去每一行裡找那個欄號 —— 這也是 `set_field` 要逐格比對的原因。

    `hdr` 就是那張對照表:{'playerattrib_speed': 22, ...} 這種形狀。
    22 是在本站測試機那份 attrib.dat(上面量到 3,247 位球員的那一份)量到的,
    **不要把欄號記起來**:剛安裝好的原版(英文版與中文版都量過)是第 23 欄,
    而第 33 欄在本站測試機那份其實是 playerattrib_elbowguard(護肘)。
    兩份名冊 46 個欄位裡有 27 個的編號不一樣,對照表見
    https://toniliumvp.github.io/MVPBaseball/reference/player-fields.html
    所以底下一律照欄位「名字」查,不寫死數字。
    回傳裡把 raw / txt / nl / lines 全部一起帶出來,是因為寫回去時
    要用**原來那個換行字元**重組,不能讓 Python 自己決定。
    """
    # 用 bytes 讀進來再以 latin-1 解碼:latin-1 是「一個位元組換一個字元」的雙向對應,
    # 任何位元組都不會丟例外,而且 encode 回去必定一模一樣。
    # 這裡要的不是「看懂編碼」,是「原封不動地搬運」。
    raw = open(path, 'rb').read()
    txt = raw.decode('latin-1')
    # 換行字元自己認,認到什麼就用什麼寫回去。實測這個檔是 CRLF(3,248 行)。
    nl = '\r\n' if '\r\n' in txt else '\n'
    lines = txt.split(nl)
    # 從表頭建欄名 → 欄號的對照表。rstrip(';,') 是為了吃掉行尾多餘的分隔符號。
    hdr = {}
    for cell in lines[0].rstrip(';,').split(','):
        a = cell.strip().split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            hdr[a[1]] = int(a[0])
    # 表頭裡連名字欄都找不到,代表指到的根本不是名冊(或它被別的工具改壞了)。
    # 這種情況要在任何寫入動作之前就停住。
    if 'first_name' not in hdr or 'last_name' not in hdr:
        raise Stop('這個 attrib.dat 的表頭看不懂 —— 第一行找不到 first_name / last_name。\n'
                   '  你指到的可能不是名冊,或者它被別的工具改壞了。')
    return raw, txt, nl, lines, hdr


def parse_row(line):
    """回傳 {欄號: 值}。空值是 '' 不是 None。

    只是把一行拆開來看,**不會拿來寫回去** —— 寫回去走 `set_field`,
    它是在原本那一行上動最少的位元組。這樣分開的用意是:
    讀的時候可以隨便解析,寫的時候絕不重組整行。

    空值統一成 '' 而不是 None,是為了讓下面「新值跟舊值一不一樣」
    那種比較不必到處判斷 None。

    ⚠️ 每一行的**第一格是這一列的識別碼,它沒有欄號**,這裡是靠
    「這一格不是純數字」把它濾掉的。這句話有例外:識別碼是十六進位字串,
    偶爾整串剛好都是數字(本站測試機那份 3,247 位裡有 10 位,剛安裝好的
    原版英文版與中文版 2,921 位裡各有 59 位),那一格就會被當成欄號收進這張表。
    實測這三份名冊裡一個都沒撞到真的欄位:那些整串是數字的識別碼換算成十進位,
    最小的是 50041,而真正的欄號只到 45。就算哪天真的撞到也不會讀錯,
    因為識別碼排在最前面,真正那一格接在後面會把它蓋掉;而 `set_field`
    會數到 2 個命中,直接 raise Stop 不寫。
    但要拿識別碼請走 `line.split(',', 1)[0]`(`cmd_export` 就是這樣拿的),
    不要從這張表裡撈。
    """
    d = {}
    for cell in line.split(','):
        # split(None, 1) 依任意空白切成最多兩段:欄號、值。
        # 值本身含空白時(名字就會)不會被切壞。
        a = cell.strip().split(None, 1)
        if a and a[0].isdigit():
            d[int(a[0])] = a[1] if len(a) > 1 else ''
    return d


def set_field(line, idx, value):
    """把某一行裡「<欄號> <值>」那一格換成新值,其他位元組一個都不動。

    ⚠️ 不可以用 str.replace —— 「2 0」在一行裡會出現在很多地方。
       要逐格走,只換欄號相符的那一格。
    """
    cells = line.split(',')
    hit = 0
    for i, cell in enumerate(cells):
        stripped = cell.strip()
        a = stripped.split(None, 1)
        if a and a[0].isdigit() and int(a[0]) == idx:
            # 把這一格原本的前導空白留著再接回去。名冊是對齊排版的,
            # 空白吃掉不會壞掉,但檔案會跟原版長得不一樣,之後想比對就麻煩了。
            lead = cell[:len(cell) - len(cell.lstrip())]
            cells[i] = '%s%d %s' % (lead, idx, value)
            hit += 1
    # 命中數必須**剛好 1**。0 表示這一行沒有這一欄(行壞了或指錯行),
    # 2 以上表示我對這個格式的理解是錯的 —— 兩種都不可以繼續寫。
    if hit != 1:
        raise Stop('找不到第 %d 欄(或找到 %d 個),不敢動。' % (idx, hit))
    return ','.join(cells)


def find_players(lines, hdr, query):
    """用名字的一部分找球員,回傳 [(行號, 全名, 那一行的欄位)]。

    行號是**在 lines 裡的索引**,不是球員 id —— 之後要改哪一行就靠它,
    所以 enumerate 從 1 開始(第 0 行是表頭)。這個對應關係一旦錯掉,
    就會改到別人身上,是這支腳本最需要小心的一個數字。

    比對一律轉小寫,讓使用者不必管大小寫。
    """
    fn, ln = hdr['first_name'], hdr['last_name']
    q = query.strip().lower()
    out = []
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        d = parse_row(line)
        name = ('%s %s' % (d.get(fn, ''), d.get(ln, ''))).strip()
        # 沒有名字的行(檔尾空白行、或格式不同的行)直接跳過,不要讓它進選單。
        if not name:
            continue
        if q in name.lower():
            out.append((i, name, d))
    return out


# ── 輸入檢查 ────────────────────────────────────────────────
# 這一小張表**不是**拼音系統,只是二十個最常見的姓,用來在使用者打了中文時
# 舉一個他自己的例子(「你打的『陳』,拼音是 Chen」)。
# 舉得出例子的錯誤訊息,比只說「不可以」有用得多。
ROMAN = {
    '陳': 'Chen', '林': 'Lin', '王': 'Wang', '張': 'Chang', '李': 'Lee',
    '黃': 'Huang', '吳': 'Wu', '劉': 'Liu', '蔡': 'Tsai', '楊': 'Yang',
    '許': 'Hsu', '鄭': 'Cheng', '謝': 'Hsieh', '郭': 'Kuo', '洪': 'Hung',
    '曾': 'Tseng', '廖': 'Liao', '賴': 'Lai', '周': 'Chou', '徐': 'Hsu',
}


def check_name(s):
    """名字只能是英文字母、空白、點、連字號、撇號。

    2026-08-29 實測:名冊 3,247 位球員的名字用到 56 種字元,**非 ASCII 0 種**。
    也就是說這個檔存不了中文 —— 打中文進去不是「顯示成問號」,是把檔案弄壞。
    """
    s = s.strip()
    if not s:
        raise Stop('名字不能空白。')
    # 這道門是**分別**套在「名」與「姓」上的(cmd_import 的欄位迴圈與互動模式
    # 都是名、姓各過一次),所以 22 守的是**單一欄位**,不是全名。
    # 而 22 對不上任何一份名冊的單一欄位:本站量過手上九份相異的 attrib.dat,
    # 單一欄位最長只有 15 個字元(tools/Taiwan_20091110 那份的 Martinez-Esteve);
    # 本站測試機那份 MVP2026/data 是 12(Chisholm Jr.),
    # 剛安裝好的原版英文版那份是 14(Van Benschoten)。
    # 22 剛好等於「名接姓」的最長字數(九份都不超過 22;MVP2026/data 那份是
    # Juan Daniel 加 Encarnacion,11 加 11),但那只是數字對得上,
    # 本站沒有證據說當初就是這樣訂的。
    # 留在 22 不收緊:門開得比資料寬只是少擋人,收到 15 以下才會開始擋掉
    # 名冊裡本來就有的名字。遊戲程式真正的上限本站沒有反組譯去確認。
    if len(s) > 22:
        raise Stop('名字太長了(最多 22 個字元,你打了 %d 個)。\n'
                   '  這是「名」或「姓」單獨一格的上限,不是全名的上限。\n'
                   '  本站量過的九份名冊裡,單一欄位最長是 15 個字元。' % len(s))
    # 中文要**單獨挑出來講**,不能跟下面那條「只能用英文字母」合併 ——
    # 打中文的人需要的是「這個檔存不了中文,你要拼音」加一個例子,
    # 不是「格式不符」。這是這一課最常見的第一個錯誤。
    bad = [c for c in s if not c.isascii()]
    if bad:
        hint = ''
        for c in s:
            if c in ROMAN:
                hint = '\n  例如「%s」的拼音是 %s。' % (c, ROMAN[c])
                break
        raise Stop('名冊裡**存不了中文**,只能用英文拼音。\n'
                   '  你打的「%s」裡有 %d 個中文字。%s\n'
                   '  陳金鋒在遊戲裡就叫 Chin-Feng Chen,曹錦輝是 Chin-Hui Tsao ——\n'
                   '  照那個樣子拼就對了。' % (s, len(bad), hint))
    # 白名單而不是黑名單。這五類字元是名冊實際用到的(Chin-Feng、O'Brien、Jr. 這些),
    # 其餘一律擋掉 —— 尤其**逗號會直接把那一行切壞**,而換行會多切出一位球員。
    if not re.fullmatch(r"[A-Za-z .'\-]+", s):
        raise Stop('名字只能用英文字母、空白、點、連字號、撇號。\n'
                   '  你打的是「%s」。' % s)
    return s


def check_num(s, lo, hi, what):
    """數字欄位的守門:必須是純數字,而且在範圍內。回傳正規化後的字串。

    回傳字串而不是整數,是因為要直接填回名冊那一格;
    先 int 再 str 順便把「007」正規化成「7」。
    """
    s = s.strip()
    # 只認 ASCII 的 0-9,**不用 str.isdigit()**:
    #   · 「²」這種上標 isdigit 回 True,而 int() 吃不下 —— 會丟一個
    #     沒有人接得住的 ValueError(不是 Stop),互動模式的人看到英文 traceback,
    #     批次模式則整支中斷(cmd_import 只接得住 Stop)。
    #   · 全形「５」與阿拉伯-印度數字「٣」是 isdigit 與 int() 都吃得下的,
    #     會被悄悄正規化成 5 / 3 才寫進名冊。
    # 一律要求 ASCII 數字,順便擋掉負號、小數點與空字串 ——
    # 名冊這幾欄本來就沒有負數與小數。
    if not re.fullmatch(r'[0-9]+', s):
        raise Stop('%s要填數字,你打的是「%s」。' % (what, s))
    n = int(s)
    if not (lo <= n <= hi):
        raise Stop('%s要在 %d 到 %d 之間,你打的是 %d。' % (what, lo, hi, n))
    return str(n)


# ── 備份與原子寫入 ──────────────────────────────────────────
# 2026-09-05 第二輪:這一整段被重寫過一次,起因是一個真的被重現出來的洞。
#
#   舊版的暫存檔名是**猜得到的**:備份寫成 `attrib.dat.playerbak.part`、
#   寫入寫成 `attrib.dat.tmp`。誰先在名冊旁邊放一個同名的**符號連結**指到別的檔,
#   `shutil.copy2()` / `open(..., 'wb')` 就會**跟著連結**把那個檔截斷再倒資料進去。
#   後面的 `os.replace()` 換掉的只是連結本身,但外面那個檔在那之前就毀了。
#   本站實測(2026-09-05,在複本上):事先放一個 21 bytes 的
#   `attrib.dat.playerbak.part` 連結指到資料夾外的檔,跑一次 `--import … --apply`,
#   外面那個檔變成 840,643 bytes 的名冊內容,而畫面上印的是「✅ 都寫好了」。
#
# 三個改法,底下三個函式各守一段:
#   · 暫存檔一律 `tempfile.mkstemp(dir=目的資料夾)` —— 名字是隨機的,
#     而且它用 O_CREAT|O_EXCL 開檔,先佔位的人佔不到,也不會跟著任何連結。
#   · 目的檔與備份檔寫之前先看 `os.path.islink` —— 是連結就拒絕。
#     ⚠️ 不可以用 `os.path.exists()` 判斷:連結指到的東西不存在時它回 False,
#     那種「斷掉的連結」正是最好用的餌。要用 `lstat` / `lexists` 這一族。
#   · **換名之前**先把暫存檔讀回來逐位元組比對。換名之後才發現不對,正本已經沒了。
#
# 2026-09-06 第三輪再補一件事:**「換名」與「登記換過了」中間不可以有縫。**
# 舊版是「先設旗標、再 os.replace」—— 那是寧可多說一句的權宜寫法,
# 縫還在,只是掉進去的人被多告知一次。現在改成三態 + 不可中斷段,見 `_NoInterrupt`。
class _NoInterrupt(object):
    """把「os.replace + 登記」包成不可中斷的一段。

    這段期間收到的 Ctrl-C 先記下來,離開這一段之後再照常丟出 KeyboardInterrupt。
    這樣收尾看到的登記一定跟磁碟上的狀態一致,不會出現
    「名冊已經換掉了,程式卻還以為沒換」的那一瞬間。

    ⚠️ `signal.signal` 只有主執行緒裝得上,裝不上就退回原本的行為 ——
       不會比以前更糟,而且外面那個 'replacing' 狀態就是留給這種情形的:
       真的落在縫裡,收尾會誠實說「換好了沒有無法確定」,不會說「什麼都沒有動到」。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):    # 非主執行緒等情況:退回原本行為
            self._old = None
        return self

    def _remember(self, signum, frame):
        # 只記著,不做事。真正丟出 KeyboardInterrupt 是 __exit__ 的工作。
        self._pending = True

    def __exit__(self, exc_type, exc, tb):
        if self._old is not None:
            try:
                signal.signal(signal.SIGINT, self._old)
            except (ValueError, OSError):
                pass
        # 區塊裡本來就有例外的話不要蓋掉它(那個例外比較重要);
        # 沒有例外而期間按過 Ctrl-C,現在才照常丟出去。
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _quiet_remove(path):
    """刪掉殘骸,刪不掉也不要蓋掉真正的錯誤。"""
    try:
        os.remove(path)
    except OSError:
        pass


def _refuse_symlink(path, what):
    """目的檔是符號連結就拒絕。**不看它指到哪裡,是連結就不寫。**

    `os.path.islink` 走的是 lstat,所以「斷掉的連結」(指到不存在的東西)
    照樣認得出來 —— 那正是 `os.path.exists()` 會回 False 而漏掉的那一種。
    """
    if os.path.islink(path):
        raise Stop('%s 是一個符號連結(捷徑),不敢往它寫 —— 那會改到它指到的那個檔。\n'
                   '  請把 %s 刪掉或改名,再跑一次。'
                   % (what, os.path.basename(path)))


def _read_bytes(path):
    """整份讀回來。

    寫入前後的複驗**都經過這一個口子**,所以 `--selftest` 只要換掉這一個函式,
    就能演出「複驗讀到的東西不對」那一種故障,證明「換名之前真的有比對」。
    """
    with open(path, 'rb') as f:
        return f.read()


# 「正式的替換到底做了沒有」。Ctrl-C 落在寫入之後、複驗之前的時候,
# 檔尾那個 except 就是靠這個登記決定要說「什麼都沒有動到」還是「檔案已經改了」。
# 起手一律「還沒動」;真的動到名冊的只有 atomic_write 那條路。
#
# 2026-09-06 從兩態改成**三態**:
#     idle       還沒動過                → 可以說「什麼都沒有動到」
#     replacing  正在換(登記在換名之前) → 只能說「換好了沒有無法確定」
#     replaced   換過了                  → 要說「已經寫進去了」並印還原的路
# 'replacing' 是**保險**:`_NoInterrupt` 裝得上的話(主執行緒都裝得上)
# 幾乎不可能停在這一格,因為那一段期間的 Ctrl-C 會被押到登記完才丟出來。
# `done` 這個鍵留著沒改名,因為整支腳本與頁面上都用它指「名冊換過了沒有」。
APPLIED = {'done': False, 'phase': 'idle', 'path': None}


def _atomic_put(path, data, mode_src=None, mark_applied=False):
    """把 data 整份放進 path:唯一暫存檔 → fsync → 套權限 → **讀回來比對** → 換名。

    失敗的每一條路都保證兩件事:暫存檔被刪掉、**正本一個位元組都沒有變**。
    正本只在最後那一行 `os.replace` 的瞬間換過去,而那一行在同一個檔案系統上是原子的。

    三條路都走這裡:寫名冊、寫備份、匯出 CSV。

    `mode_src` 是「權限要照誰的」:備份要照名冊的權限,寫入要照原檔自己的;
    匯出的 CSV 第一次寫時沒有原檔可照,那時補成「一般開檔會得到的權限」。
    `mark_applied` **只有寫名冊那條路**會給 True,備份與匯出都不給 ——
    那兩條寫壞了名冊還是原封不動,不該讓 Ctrl-C 的訊息說「檔案已經改了」。
    """
    _refuse_symlink(path, os.path.basename(path))
    d = os.path.dirname(os.path.abspath(path)) or '.'
    prev = dict(APPLIED)                 # 確定沒換成時要把三態收回原狀
    # mkstemp:名字隨機 + O_CREAT|O_EXCL + 權限 0600。先佔位佔不到,也不跟連結。
    # 放在**目的檔同一個資料夾**,os.replace 才會是同一個檔案系統上的原子換名。
    try:
        fd, tmp = tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(path) + '.tmp-')
    except OSError as e:
        # 資料夾唯讀、沒有權限、磁碟滿了都會落在這裡。**這時候一個位元組都還沒動過**,
        # 所以要講的是「什麼都沒發生」加「去看哪裡」,不是丟一片英文 traceback。
        raise Stop('在這個資料夾裡建不出暫存檔:%s\n'
                   '  %s\n'
                   '  %s 一個位元組都沒有被動到。\n'
                   '  常見原因:遊戲裝在需要管理員權限的地方(Program Files)、'
                   '磁碟滿了、或者外接碟是唯讀掛載。'
                   % (e.strerror or e, d, os.path.basename(path)))
    try:
        out = os.fdopen(fd, 'wb')
    except BaseException:
        # fdopen 沒接手成功的話 fd 還在我手上,自己關掉再清殘骸。
        try:
            os.close(fd)
        except OSError:
            pass
        _quiet_remove(tmp)
        raise
    try:
        with out:                       # 這個 with 會關檔,fd 不會漏
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        # 權限:mkstemp 給的是 0600,不補這一行的話原本 0700 的名冊換完會變 0600。
        # 用 copymode 不用 copystat:copystat 連**修改時間**都搬,把新檔的時間往回調
        # 會讓靠 mtime 判斷的同步工具漏掉這次修改。這裡只要權限。
        try:
            shutil.copymode(mode_src if mode_src is not None else path, tmp)
        except OSError:
            # 原檔不在(第一次寫,例如 --export 到一個還不存在的 CSV)。
            # 這時**不可以就這樣算了**:mkstemp 給的是 0600,而使用者預期
            # 匯出的 CSV 跟他自己用其他程式產生的檔一樣看得到、複製得走。
            # 所以補成「一般開檔會得到的權限」= 0666 扣掉這台機器的 umask。
            # (os.umask 只能用「設了再設回去」的方式讀出來;檔案系統不支援
            #  權限位元的話 chmod 會丟 OSError,那種情況才是真的算了。
            #  ⚠️ 那兩行之間 umask 短暫是 0 —— 這支腳本是單執行緒的命令列工具,
            #     那一瞬間不會有別人在建檔;要是哪天有人把它包進多執行緒,
            #     這裡就得改成寫死一個權限,不能再問系統。)
            try:
                _um = os.umask(0)
                os.umask(_um)
                os.chmod(tmp, 0o666 & ~_um)
            except OSError:
                pass
        # ⚠️ **換名之前**讀回來比對。長度先比再比內容 —— 兩個都要,
        #    因為「短了一截」跟「內容不對」是兩種不同的故障。
        back = _read_bytes(tmp)
        if len(back) != len(data) or back != data:
            raise Stop('寫暫存檔的時候出問題(寫了 %d bytes,讀回來 %d bytes)。\n'
                       '  %s 一個位元組都沒有被動到,暫存檔已經刪掉了。\n'
                       '  多半是磁碟滿了或者外接碟出狀況,騰出空間再跑一次。'
                       % (len(data), len(back), os.path.basename(path)))
        # 「正在換」刻意登記在 replace **之前**:Ctrl-C 剛好卡在這兩行之間的時候,
        # 寧可多說一句「檔案可能已經改了,可以還原」,也不要漏說。
        # 說錯的代價是使用者白跑一次還原(還原自己有五道把關,不會弄壞東西),
        # 漏說的代價是他以為沒事就進遊戲。
        #
        # 然後「換名 + 登記換過了」被 `_NoInterrupt` 包成**不可中斷的一段**:
        # 這一段期間按下的 Ctrl-C 會先被記著,等 'replaced' 登記完才丟出去 ——
        # 所以收尾看到的登記跟磁碟上的狀態一定一致,不會有「換掉了卻說沒換」的縫。
        if mark_applied:
            APPLIED.update({'phase': 'replacing', 'path': path})
        with _NoInterrupt():
            os.replace(tmp, path)
            if mark_applied:
                APPLIED.update({'done': True, 'phase': 'replaced', 'path': path})
    except BaseException as e:
        # 用 BaseException 才連 Ctrl-C 都收得到 —— 按 Ctrl-C 一樣要清乾淨殘骸。
        _quiet_remove(tmp)
        if mark_applied and not APPLIED['done'] and isinstance(e, Exception):
            # 一般的例外(磁碟滿了、權限不足…)代表 `os.replace` **沒有**成功
            #('replaced' 是換名之後才登記的,所以 done 還是 False 就等於沒換成),
            # 把三態收回原狀,免得之後的訊息說「檔案可能改了」而其實沒有。
            # ⚠️ Ctrl-C 那一類(BaseException 但不是 Exception)**不收回** ——
            #    `_NoInterrupt` 萬一裝不上(非主執行緒),它可能剛好落在換名的
            #    那一瞬間,那時狀態停在 'replacing',收尾會說「無法確定」,
            #    不會說「什麼都沒有動到」。**確定沒換成才可以撤銷登記。**
            APPLIED.update(prev)
        # 磁碟/權限那一類的錯翻成人話再丟(這一課的讀者看不懂 traceback);
        # **其餘一律原樣丟出去,絕不吞掉**。
        if isinstance(e, OSError):
            raise Stop('寫 %s 的時候出問題:%s\n'
                       '  %s **沒有被動到**(換名之前就失敗了,暫存檔已經刪掉)。\n'
                       '  常見原因:磁碟滿了、外接碟被拔掉、或者沒有寫入權限。'
                       % (os.path.basename(path), e.strerror or e,
                          os.path.basename(path)))
        raise


def atomic_backup(src, dst):
    """備份要嘛完整、要嘛不存在。中斷只會留下一個隨機名字的暫存檔,不會被誤認成備份。

    為什麼要這麼講究:上層是用「`.playerbak` 存不存在」來決定要不要備份的。
    如果複製到一半留下一個叫得出名字的半截檔,下一次執行會認為
    「備份已經有了」而繼續改名冊,之後還原就會拿那個半截檔覆蓋掉正本。
    """
    # 備份檔本身是連結的話,寫下去會改到連結指到的那個檔;而且下一次還原
    # 會從那個檔讀資料蓋回名冊。兩頭都不能接受,所以是連結就直接拒絕。
    _refuse_symlink(dst, '備份檔 %s' % os.path.basename(dst))
    _atomic_put(dst, _read_bytes(src), mode_src=src)


def atomic_write(path, data):
    """把 data 整份寫進 path。**寫入與還原兩個方向都走這一條。**

    2026-09-05 之前只有寫入這樣做,還原是直接 `shutil.copy2(備份, 名冊)` ——
    那是開檔就把正本截成 0 再往裡面倒,中途被打斷(Ctrl-C、當機、外接碟拔掉)
    正本就停在半截。

    真正做事的是 `_atomic_put`。這裡多做的只有一件:標記「名冊已經被替換過了」,
    好讓 Ctrl-C 的訊息說得出實話。
    """
    _atomic_put(path, data, mark_applied=True)


def _print_interrupt_state(interrupted=True):
    """中斷的時候印出「到底有沒有動到檔案」。**這句話不可以是寫死的。**

    2026-09-05 第二輪之前,不管中斷發生在哪裡,這支腳本都印
    「什麼都沒有動到」然後 `sys.exit(0)` —— 而 Ctrl-C 完全可能落在
    `os.replace()` 之後、複驗之前:名冊那時已經是新的了,畫面卻說沒動、
    結束碼還說成功。使用者不會去還原,直接就進遊戲。

    所以改成看 `APPLIED`(那個登記在 `_atomic_put` 裡做,「正在換」刻意登記在
    換名之前 —— 寧可多說一句可以還原,不要漏說)。

    2026-09-06 補上第三種狀態。三句話對三態,**沒有一句是寫死的**:
      replaced   換過了              → 「名冊可能已經寫進去了」+ 兩條還原的路
      replacing  正在換,結果不確定  → 「換好了沒有無法確定」+ 同樣兩條路
                                        (`_NoInterrupt` 裝得上就幾乎到不了這裡)
      idle       還沒動              → 「什麼都沒有動到」

    2026-09-11 多一個 `interrupted` 參數:同樣三態,還有另一種到得了這裡的路 ——
    **不是你按 Ctrl-C,是這支工具自己出了狀況**(防毒軟體鎖住檔案、外接碟被拔掉,
    寫完之後才發作那一種)。那時三態要說的事情一模一樣,只有開頭那半句不能說
    「你中斷了」—— 使用者沒有中斷,講錯會讓他以為是自己弄的。
    `interrupted=True` 是原本的行為,一個字都沒有改。
    """
    if APPLIED['done'] or APPLIED['phase'] == 'replacing':
        if APPLIED['done']:
            print('  ⚠️ 你中斷了,但名冊**可能已經寫進去了**:' if interrupted
                  else '  ⚠️ 名冊**可能已經寫進去了**:')
        else:
            # 只有「換名 + 登記」那一段的保險裝不上時才會走到這裡。
            # 不確定就說不確定,不可以猜一個好聽的。
            print('  ⚠️ 你中斷了,中斷時**正在替換名冊**,換好了沒有無法確定:' if interrupted
                  else '  ⚠️ 出狀況的時候**正在替換名冊**,換好了沒有無法確定:')
        print('     %s' % (APPLIED['path'] or ''))
        print()
        print('  要回到動手前的樣子,兩個方法選一個:')
        print('    · 再跑一次這支工具(雙擊就好),它會問你要不要還原,打 r')
        print('    · 或者打指令:python3 mvp_player.py "〔你的遊戲資料夾〕" --restore')
        print('  備份還在名冊旁邊,檔名是 attrib.dat%s。' % BAK_SUFFIX)
        if not APPLIED['done']:
            print('  不想還原的話,也可以拿備份跟名冊比對,看它到底換過了沒有。')
    else:
        print('  好,先不改。什麼都沒有動到。' if interrupted
              else '  名冊什麼都沒有動到。')


def roster_row_count(lines, what):
    """驗名冊的形狀,順便回傳資料列的列數。形狀不對就 raise Stop。

    這是 `_restore_check` 用來分辨「完整的名冊」與「被截斷的半截檔」的尺。
    量的是本站手上十一份相異的 attrib.dat(測試機那份、剛安裝好的原版英文版
    與中文版、以及八份社群模組名冊),十一份的形狀完全一致:

        表頭   47 格(46 個欄位 + 行尾那個「;」)
        資料列 48 格(識別碼 + 46 個欄位 + 行尾那個「;」)

    所以判準有兩條,都不假設欄位叫什麼名字:
      · 每一列的欄數要一樣
      · 表頭要剛好比資料列少一格(少的就是最前面那個識別碼)

    截斷會被抓到,是因為**截斷只會讓逗號變少**:斷在半行中間的那一列
    一定湊不滿 48 格。斷得剛好落在換行邊界的那種,這裡看不出來 ——
    那一種靠 `_restore_check` 的「列數要跟正本一樣」抓。
    """
    ncell = len(lines[0].split(','))
    rows = 0
    for i, l in enumerate(lines[1:], start=2):
        if not l.strip():
            continue
        rows += 1
        if len(l.split(',')) != ncell + 1:
            raise Stop('%s 第 %d 行的格式不對(那一行有 %d 格,表頭有 %d 格,\n'
                       '  正常的資料列應該是 %d 格)。這個檔是半截的,或者根本不是名冊。'
                       % (what, i, len(l.split(',')), ncell, ncell + 1))
    if rows == 0:
        raise Stop('%s 裡面一位球員都沒有。' % what)
    return rows


# ── 畫面 ────────────────────────────────────────────────────
def line(ch='─', n=54):
    """畫一條分隔線。54 是配合下面那些提示文字寬度挑的,沒有別的意思。"""
    print(ch * n)


def ask(prompt, default=None):
    """問一句話,回傳去掉頭尾空白的答案。

    **Ctrl-C 與 Ctrl-D 在這裡就直接乾淨離開**,不往上丟例外 ——
    因為這支腳本是給雙擊的人用的,任何一個問句都應該可以隨時退出。
    退出時印的那句話由 `_print_interrupt_state()` 決定:**它會先看檔案動了沒有**,
    不是無條件說「什麼都沒有動到」。結束碼一律 130(中斷的慣例),不是 0 ——
    0 的意思是「做完了而且成功」,中斷不是那件事。
    """
    try:
        v = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print()
        _print_interrupt_state()
        sys.exit(130)
    return v if v else (default or '')


# ── 批次模式(給做整包模組的人)────────────────────────────
# 為什麼要有這個(2026-08-29,一位 43 歲的老玩家來試聽時指出的):
#   他要做「台灣之光」模組,得接收二三十個位置。
#   互動問答一次一位 = 回答兩百多次提問。他五分鐘就能編好一張表。
#   所以同一支工具開第二道門,互動那道完全不動。
# CSV 只有五欄:一把配對用的鑰匙 + 四個可以改的欄位。
# 刻意不把 46 欄全倒出去 —— 表越寬,使用者不小心動到不該動的那一格的機會就越大。
CSV_COLS = ('id', 'first_name', 'last_name', 'jersey', 'speed')


def cmd_export(path, out):
    """--export:把名冊裡的五欄倒成一張 CSV。**完全不寫遊戲檔。**

    這是批次那道門的第一步。id 是每一行的第一格,也是等一下 --import
    用來對回同一位球員的唯一憑據 —— 所以匯出時要原樣帶出去。
    """
    # 輸出檔名的守門。這條路沒有備份可以救 —— 沒跑過 --apply 的人
    # 連 .playerbak 都沒有,寫錯地方就是直接把遊戲檔蓋掉。
    # 實測(2026-09-05):`--export <遊戲>/data/database/attrib.dat` 會把
    # 840,643 bytes 的名冊變成一張 98,784 bytes 的 CSV,還印四行成功訊息。
    if os.path.realpath(out) == os.path.realpath(path):
        raise Stop('--export 後面那個檔名不能是名冊本身,那會把名冊蓋掉。\n'
                   '  換一個名字,例如 players.csv。')
    # 已經存在、而且結尾不是 .csv 的檔一律不覆蓋(`.playerbak` 也在這一條裡)。
    # 只擋「已經存在」的,所以重複匯出到同一張 players.csv 照樣可以。
    if os.path.exists(out) and not out.lower().endswith('.csv'):
        raise Stop('%s 已經存在,而且它不是 .csv —— 不敢覆蓋。\n'
                   '  --export 只往 .csv 寫。換一個名字,例如 players.csv。' % out)
    # 匯出的目的檔也是「要寫的檔」,一樣不跟著符號連結走(2026-09-06 補)。
    # ⚠️ 上面那一道用的是 `os.path.exists`,對**斷掉的**連結會回 False ——
    #    所以它擋不住連結,必須另外用 `os.path.islink` 看一次。
    #    實測(2026-09-06,在暫存複本上):補這一道之前,把 players.csv 先做成
    #    指向資料夾外某個檔的連結,`--export` 會把那個檔整個蓋成 CSV,
    #    畫面上照樣印「匯出 N 位球員」。這一條跟名冊、備份是同一種洞。
    _refuse_symlink(out, '匯出的檔案 %s' % os.path.basename(out))
    _raw, _txt, nl, lines, hdr = read_roster(path)
    # 先把四個欄位的欄號查出來。名冊的欄位順序不保證每個版本都一樣,
    # 所以一律從表頭查,不寫死數字。
    fn, ln = hdr['first_name'], hdr['last_name']
    jn, sp = hdr['playerattrib_jerseynum'], hdr['playerattrib_speed']
    n = 0
    # 先在記憶體裡把整張表排好,再一次原子寫出去(2026-09-06 改)。
    #
    # 舊版是 `open(out, 'w')` 直接開檔 —— 那有兩個問題:
    #   (一)`open(..., 'w')` 會**跟著符號連結**,而且是「先把那個檔截成 0
    #        再往裡面倒」。上面新加的那道 islink 已經擋掉這一種。
    #   (二)就算不是連結,寫到一半斷掉會留下半截的 CSV,而它看起來跟
    #        完整的一樣(CSV 沒有檔尾標記),使用者拿它去 --import 只會匯到一半。
    # 現在改走名冊那條同一條路(`_atomic_put`):隨機名字的暫存檔 → fsync →
    # 讀回來逐位元組比對 → 換名。斷在中途只會留下一個暫存檔,`out` 還是舊那份。
    #
    # newline='' 是 csv 模組的規定,少了它在 Windows 上會多出空白行 ——
    # 寫進 StringIO 時同樣要照規矩來,csv 自己會用 \r\n 當行尾。
    # 用 UTF-8 編出去,Excel 與記事本都讀得動。
    _buf = io.StringIO(newline='')
    w = csv.writer(_buf)
    w.writerow(CSV_COLS)
    for line_ in lines[1:]:
        if not line_.strip():
            continue
        d = parse_row(line_)
        # id 是這一行的第一格,原樣抄出去。它是 --import 的鑰匙,
        # 不做任何正規化 —— 改動它就等於改動配對關係。
        pid = line_.split(',', 1)[0].strip()
        w.writerow([pid, d.get(fn, ''), d.get(ln, ''), d.get(jn, ''), d.get(sp, '')])
        n += 1
    # 資料夾不存在是這條路最常見的錯(檔名打錯、路徑打錯)。先自己看一眼,
    # 才講得出「檢查一下那個資料夾在不在」這句話 —— `_atomic_put` 只知道
    # 「建不出暫存檔」,講不出這麼具體的下一步。
    _outdir = os.path.dirname(os.path.abspath(out)) or '.'
    if not os.path.isdir(_outdir):
        raise Stop('寫不出 %s:找不到資料夾 %s\n'
                   '  檢查一下那個資料夾在不在、檔名有沒有打錯。' % (out, _outdir))
    # mark_applied 不給:這條路一個位元組都不會動到遊戲檔,
    # 匯出失敗不該讓 Ctrl-C 的訊息說「名冊可能改了」。
    _atomic_put(out, _buf.getvalue().encode('utf-8'))
    print('  匯出 %d 位球員 → %s' % (n, out))
    print('  用 Excel 或記事本改那張表,只改 first_name / last_name / jersey / speed 四欄。')
    print('  ⚠️ id 那一欄是配對用的鑰匙,**絕對不要動**。')
    print('  ⚠️ 名字只能用英文拼音(名冊存不了中文)。')
    return 0


def cmd_import(path, src, apply_it):
    """--import:把 CSV 的內容寫回名冊。`apply_it` 是 False 就只預覽。

    這個函式的順序是刻意的,而且**順序本身就是安全網**:

        讀名冊 → 讀 CSV → 驗欄位 → 逐格算出「要改什麼」→
        有任何一格不合格就整張擋下(一個位元組都不寫)→
        沒有 --apply 就印預覽結束 → 有 --apply 才備份、寫暫存、換名、複驗

    「整張擋下」是重點:一張二十幾個位置的表如果邊驗邊寫,
    寫到第十五個才發現第十六格打錯,名冊就停在改了一半的狀態。
    這裡是全部算完、全部通過,才開始動檔案。
    """
    raw, _txt, nl, lines, hdr = read_roster(path)
    fn, ln = hdr['first_name'], hdr['last_name']
    jn, sp = hdr['playerattrib_jerseynum'], hdr['playerattrib_speed']
    # 先建「id → 行號」的索引。配對靠 id 不靠行號順序,
    # 所以使用者在 Excel 裡把列排序過、或刪掉不相干的列,都不影響配對。
    byid = {}
    for i, line_ in enumerate(lines[1:], start=1):
        if line_.strip():
            byid[line_.split(',', 1)[0].strip()] = i

    # utf-8-sig:Excel 存 CSV 會在最前面加 BOM,不吃掉的話第一個欄名會變成
    # 「﻿id」而對不上,然後報一個看不懂的「少了 id 欄」。
    # 檔名打錯是批次模式最常見的錯。不接住的話讀者看到的是一整片
    # 英文 traceback,而不是 Stop 那段承諾的一句中文。
    try:
        with open(src, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        raise Stop('讀不到 %s:%s\n'
                   '  檢查一下檔名有沒有打錯、那張表是不是在你現在的資料夾裡。'
                   % (src, e.strerror or e))
    if not rows:
        raise Stop('%s 是空的,或第一行不是欄位名。' % src)
    # 欄位缺一個就先停,而且把缺的全部列出來 —— 不要讓使用者改一次跑一次。
    missing = [c for c in CSV_COLS if c not in rows[0]]
    if missing:
        raise Stop('CSV 少了這幾欄:%s\n  需要的欄位:%s'
                   % ('、'.join(missing), '、'.join(CSV_COLS)))

    # 一趟走完整張表,把「要改什麼」跟「哪裡有問題」分別收集起來。
    # 這一趟**完全不寫任何東西**,只是在算。
    changes, errors = [], []
    for i, r in enumerate(rows, start=2):     # 第 1 行是欄名
        pid = (r.get('id') or '').strip()
        # id 空白的列直接略過,不算錯 —— 使用者常在表尾留空行。
        if not pid:
            continue
        if pid not in byid:
            errors.append('第 %d 行:找不到 id %s' % (i, pid))
            continue
        cur = parse_row(lines[byid[pid]])
        for col, idx, checker in (('first_name', fn, 'name'), ('last_name', ln, 'name'),
                                  ('jersey', jn, 'num'), ('speed', sp, 'num')):
            new = (r.get(col) or '').strip()
            # 空白 = 不改這一格(不是「改成空白」);跟現值一樣也不算改動。
            # 少了這一條,預覽會塞滿「Chen → Chen」這種沒有意義的列。
            if new == '' or new == cur.get(idx, ''):
                continue
            try:
                val = check_name(new) if checker == 'name' else check_num(
                    new, 0, 99, '背號' if col == 'jersey' else '跑壘速度')
            except Stop as e:
                # 這裡把 Stop **接住當成一筆錯誤**而不是讓它中止整支程式,
                # 是為了一次把整張表的問題全部列給使用者,而不是修一格跑一次。
                # 只取第一行:那些訊息後面還有給互動模式看的多行說明,列表裡會太長。
                errors.append('第 %d 行 %s:%s' % (i, col, str(e).split(chr(10))[0]))
                continue
            # (行號, 欄號, 新值, id, 欄名, 舊值)—— 前三個給寫入用,後三個給預覽與複驗用。
            changes.append((byid[pid], idx, val, pid, col, cur.get(idx, '')))

    # 有錯就到此為止。**一個位元組都不寫**,回傳 1 讓呼叫者知道失敗了。
    if errors:
        print('  🔴 這張表有 %d 個問題,一個位元組都不會寫:' % len(errors))
        for e in errors[:20]:
            print('     %s' % e)
        if len(errors) > 20:
            print('     …還有 %d 個' % (len(errors) - 20))
        return 1

    if not changes:
        print('  這張表跟名冊完全一樣,沒有要改的。')
        return 0

    who = len({c[3] for c in changes})
    print('  要改 %d 位球員、%d 個欄位:' % (who, len(changes)))
    for lineno, idx, val, pid, col, old in changes[:40]:
        print('    %s  %-11s %-14s → %s' % (pid, col, old or '(空的)', val))
    if len(changes) > 40:
        print('    …還有 %d 個' % (len(changes) - 40))

    if not apply_it:
        print()
        print('  這是預覽,一個位元組都沒有寫。確定的話再跑一次,最後加上 --apply。')
        return 0

    backup = path + BAK_SUFFIX
    # 動任何一根手指之前先擋掉符號連結。放在備份**之前**是刻意的:
    # 名冊是連結的話,連備份都不該做 —— 那份備份會是連結指到的那個檔的內容,
    # 之後還原就會把它蓋回一個不相干的地方。
    _refuse_symlink(path, os.path.basename(path))
    _refuse_symlink(backup, '備份檔 %s' % os.path.basename(backup))
    if not os.path.exists(backup):
        atomic_backup(path, backup)
        print('  已先備份成 %s' % os.path.basename(backup))
    else:
        print('  備份已經有了,保留最早那一份。')

    # 在**行的副本**上動手。同一位球員可能有好幾格要改,
    # 所以是把上一次的結果再丟進 set_field,一格一格疊上去。
    out = list(lines)
    for lineno, idx, val, _pid, _col, _old in changes:
        out[lineno] = set_field(out[lineno], idx, val)
    # 用原本那個換行字元重組,再以 latin-1 編回位元組 ——
    # 跟讀進來時完全對稱,沒有被改到的行連一個位元組都不會變。
    # 先寫暫存檔、fsync、套回原檔權限、再換名(見 atomic_write)。
    atomic_write(path, nl.join(out).encode('latin-1'))

    # 複驗:讀回來逐項確認
    # 刻意**重新從磁碟讀一次**,不拿記憶體裡的 out 來比 ——
    # 拿自己剛算出來的東西驗自己,驗不出任何東西。
    _r, _t, _n, lines2, _h = read_roster(path)
    bad = []
    for lineno, idx, val, pid, col, _old in changes:
        if parse_row(lines2[lineno]).get(idx, '') != val:
            bad.append((pid, col, val))
    if bad:
        print('  🔴 寫進去了,但讀回來有 %d 個對不上:' % len(bad))
        for b in bad[:10]:
            print('     %s %s 應該是 %s' % b)
        print('  跑 --restore 還原,然後回報給班主任。')
        return 1
    print('  ✅ %d 位球員、%d 個欄位都寫好了,讀回來逐項相符。' % (who, len(changes)))
    return 0


def cmd_restore_cli(path):
    """--restore:把 `.playerbak` 蓋回名冊。備份留著不刪。

    備份不刪是刻意的 —— 還原之後使用者常常想再改一次,
    刪掉的話下一輪就會拿「已經改過的名冊」當成新的備份基準。
    """
    backup = path + BAK_SUFFIX
    if not os.path.exists(backup):
        raise Stop('找不到備份 %s —— 你還沒用這支工具改過這份名冊。'
                   % os.path.basename(backup))
    _restore_check(backup, path)
    print('  ✅ 已從 %s 還原。備份留著沒刪。' % os.path.basename(backup))
    return 0


def _restore_check(bak, dst):
    """還原前擋掉壞掉的備份,過了才由這個函式自己把備份寫回去。

    **這是唯一的還原入口。** `--restore` 與互動模式「打 r 還原」都走這裡 ——
    2026-09-05 之前互動那條是自己呼叫 `shutil.copy2`,一道把關都沒走:
    同一份截成前 1/8 的備份,`--restore` 擋得下來,雙擊那條卻直接蓋上去,
    840,643 bytes 的名冊當場變成 105,080,畫面上還印
    「✅ 已經還原成第一次改之前的樣子」。而雙擊那條正是這一課
    **唯一教給不會打指令的讀者**的路。

    五道把關,分成兩組:

      只看備份自己(正本壞了也照驗)
        1. 不是 0 bytes
        3. 表頭讀得懂(`read_roster`,擋的是「指錯檔」)
        4. 形狀:每一列欄數一致、表頭剛好少一格(`roster_row_count`)

      拿正本當尺(**正本自己讀不出來就整組跳過**)
        2. 不到正本的一半(粗篩,給最常見的那種中斷一句好懂的話)
        5. 列數跟正本一樣 —— 這支工具是原地改,列數不會變

    第 5 道不能省:截在**換行邊界**的備份形狀是完好的,第 1、3、4 道全過。
    實測截到 60% 且對齊 CRLF 的備份,舊版四道全放行、印 ✅,
    名冊從 3,247 位球員變成 1,947 位。

    ⚠️ 第 5 道的代價寫在檔頭安全網第 6 條:備份之後換了一份球員人數不同的
    名冊模組,再來還原會被擋。那時請自己在檔案總管/Finder 裡複製。
    ⚠️ 反過來,正本已經壞到讀不出來時**不可以擋** —— 那正是最需要還原的時刻。
    """
    # ── 把關之前先擋符號連結 ────────────────────────────────
    # 備份是連結 → 讀到的是別人的內容;名冊是連結 → 寫下去會改到別的檔。
    # 兩頭都是「不看它指到哪裡,是連結就不做」。
    _refuse_symlink(bak, '備份檔 %s' % os.path.basename(bak))
    _refuse_symlink(dst, os.path.basename(dst))

    # ── 只驗備份自己的三道(1 / 3 / 4)──────────────────────
    # 第 1 道:0 bytes。備份到一半被中斷最常見的樣子。
    n = os.path.getsize(bak)
    if n == 0:
        raise Stop('備份是 0 bytes,不敢拿它覆蓋 %s。' % dst)
    # 第 3 道:表頭解得開嗎。這一道擋的是「指錯檔」,不是截斷。
    _braw, _btxt, _bnl, blines, _bhdr = read_roster(bak)   # 表頭看不懂就會丟 Stop
    # 第 4 道:形狀。每一列的欄數要一致,表頭要剛好少一格。
    #          斷在半行中間的備份湊不滿一列,這裡就會亮。
    brows = roster_row_count(blines, '備份 %s' % os.path.basename(bak))

    # ── 拿正本當尺的兩道(2 / 5)────────────────────────────
    # ⚠️ **正本自己讀不出來的時候這兩道一律跳過,不可以擋。**
    #    正本被別的工具改壞了、或上一次還原到一半斷電 —— 那正是最需要還原的時刻,
    #    而且壞掉的尺量出來的數字沒有意義。備份已經自己過了上面三道,是可信的那一份。
    lrows = None
    if os.path.exists(dst):
        try:
            _lraw, _ltxt, _lnl, llines, _lhdr = read_roster(dst)
            lrows = roster_row_count(llines, os.path.basename(dst))
        except (Stop, OSError):
            lrows = None
            print('  ⓘ 現在這份 %s 讀不出來(壞了),那就不拿它當尺了 ——'
                  % os.path.basename(dst))
            print('    備份自己已經過了前面三道把關,直接拿它蓋回去。')
    if lrows is not None:
        # 第 2 道:大小地板。這支腳本是原地改(改幾個字,大小幾乎不變),
        # 所以備份不到正本的一半就一定出事了。
        # ⚠️ 它排在第 4 道**後面**,所以「被截斷的備份」實際上是先被第 4 道
        #    (形狀)接走的,不會走到這裡 —— 實測前 1/8 的半截備份印的是
        #    「第 406 行的格式不對」。這一道現在守的是「形狀完好但小得離譜」
        #    的那種(例如只有一百位球員的名冊),那種第 5 道也擋得下,
        #    留著是因為它講得出「差太多了」這句最好懂的話。
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            raise Stop('這份備份只有 %d bytes,而 %s 有 %d bytes —— 差太多了'
                       '(不到一半),不敢拿它覆蓋。多半是備份途中被中斷。'
                       % (n, os.path.basename(dst), live))
        # 第 5 道:列數要跟正本一樣。斷在換行邊界的備份形狀是完好的,只有列數會少。
        if brows != lrows:
            raise Stop('這份備份有 %d 位球員,而 %s 有 %d 位 —— 對不上,不敢拿它覆蓋。\n'
                       '  兩種可能:(一)備份是半截的;(二)你在備份之後換過一份\n'
                       '  球員人數不同的名冊模組。如果是第二種而你確定要還原,\n'
                       '  請自己在檔案總管/Finder 裡把 %s 複製成 %s。'
                       % (brows, os.path.basename(dst), lrows,
                          os.path.basename(bak), os.path.basename(dst)))
    # 五道全過才真的覆蓋,而且覆蓋也是先寫暫存檔再換名(見 atomic_write)——
    # 直接 copy2 是「開檔就把正本截成 0 再往裡面倒」,中途被打斷正本就停在半截。
    atomic_write(dst, _braw)
    # 寫完把整份讀回來逐位元組比對。**不可以用 zip()** —— 它會在短的那一邊停,
    # 而「短了一截」正是這裡要抓的東西。長度先比,再比內容。
    back = open(dst, 'rb').read()
    if len(back) != len(_braw) or back != _braw:
        raise Stop('還原寫進去了,但讀回來跟備份不一樣(備份 %d bytes,讀回來 %d bytes)。\n'
                   '  先不要進遊戲。備份 %s 還在,請回報給班主任。'
                   % (len(_braw), len(back), os.path.basename(bak)))


# ── 自我測試 ────────────────────────────────────────────────
def _fake_roster(names, nl='\r\n'):
    """造一份最小的名冊,形狀跟真的一樣:表頭 47 格、資料列 48 格、CRLF、行尾「,;」。

    測試一律在這種自己造的名冊上跑,**絕對不碰任何真的遊戲檔**。
    形狀是照 `roster_row_count` 那一段量到的十一份 attrib.dat 抄的。
    """
    cols = ['first_name', 'last_name', 'playerattrib_jerseynum'] + \
           ['playerattrib_f%d' % i for i in range(3, 45)] + ['playerattrib_speed']
    assert len(cols) == 46, '表頭要剛好 46 欄'
    head = ','.join('%d %s' % (i, c) for i, c in enumerate(cols)) + ',;'
    rows = []
    for k, (fn, ln) in enumerate(names):
        cells = ['%09x' % (0xf58f3c1b + k)]
        for i, _c in enumerate(cols):
            v = fn if i == 0 else (ln if i == 1 else ('%d' % (i + k)))
            cells.append('%d %s' % (i, v))
        rows.append(','.join(cells) + ',;')
    return (nl.join([head] + rows) + nl).encode('latin-1')


def selftest():
    """--selftest:自己造一份最小的名冊來測,**完全不碰任何遊戲檔**。

    測的是這支工具對讀者的承諾,而且**正向與反向都要有**:
    只有反向餌的話,「整支壞掉」也會讓每個餌都「成功地失敗」;
    只有正向的話,防線壞掉了測試照樣全綠(2026-08-29 本站踩過)。

    正向(證明正常流程真的做到承諾的事):
      1. 造出來的名冊讀得出來,表頭四個欄位查得到
      2. `--export` 一個位元組都不動名冊,而且匯出的列數等於球員數
      3. `--import` 沒加 --apply 時名冊逐位元組不變
      4. `--import --apply` 真的改到、備份出現、**沒點名的行逐位元組不變**
      5. `--restore` 之後逐位元組回到原狀
      6. `set_field` 只換那一格,同一行其他格不動

    反向餌(每一道新守門各一個,失敗不了才是問題):
      A. `<備份>.part` 先被放成指向資料夾外的符號連結 → 外面那個檔不可以被動到
         (這一條是 2026-09-05 真的重現出來的洞,舊版會把外面那個檔寫成整份名冊)
      B. 名冊本身是符號連結 → 兩道門都要被擋下,連結指到的檔不可以被動到,
         而且批次那道門**連備份都不可以做**(備份會是連結指到的那個檔的內容)
      C. 備份檔是**斷掉的**符號連結 → 要被擋下(`os.path.exists()` 對它回 False,
         所以這一條同時證明了「不能用 exists 判斷」)
      D. 換名之前的複驗讀到不對的東西 → 要被擋下,正本逐位元組不變、不留殘骸
      E. `os.replace` 當場丟例外(還原做到一半失敗)→ 正本逐位元組不變、不留殘骸,
         而且錯誤訊息要是人話、要說得出「正本沒有被動到」
      E2. 資料夾唯讀,連暫存檔都建不出來 → 同上(Windows 與 root 底下測不出來,跳過)
      F. 中斷登記:寫成功之前是「還沒動」,寫成功之後是「換過了」;
         而且「正在換」要**登記在換名之前**、三態各自講的那句話都不可以講錯
         (檔尾那句「什麼都沒有動到」就是靠它,說錯了會害人不去還原)
      G. 截斷的備份 → `_restore_check` 要擋下,正本不變
      H. 中文名字、超出範圍的數字 → `check_name` / `check_num` 要擋下
      I. `--export` 的目的檔是指向資料夾外的符號連結 → 要被擋下,
         外面那個檔一個位元組都不可以變(2026-09-06 補這道門之前它會被寫穿)
      J. `_NoInterrupt` 真的接管了 SIGINT、期間的中斷會被押到離開才丟、
         離開之後把原本的處理器裝回去(「不可中斷的一段」不可以是空話)
      K. **沒有人預料到的例外**(不是 Stop、也不是 Ctrl-C)不可以只丟一片英文
         traceback:名冊換過了就要說換過了、要印還原的路,原本那個例外也不可以
         被吞掉;一個位元組都沒寫的時候則要說「什麼都沒有動到」。結束碼都是 1

    ⚠️ 這支測試靠 `assert` 站著,所以 `python -O` 底下**拒跑**(見第一行)——
       -O 會把 assert 整個拿掉,每一道餌都會安靜地「通過」。
    """
    # -O 會把 assert 全部拿掉,上面那些餌有一半是靠 assert 站著的,
    # 在 -O 下會一路走到「全部通過」而其實什麼都沒驗。寧可不跑也不要假綠。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    # 兩個數字分開數(正向 / 反向餌),不要寫死在最後那句話裡 ——
    # 寫死的數字加了一道測試就過期,而沒有人會發現。
    n = {'fwd': 0, 'rev': 0}

    def eq(a, b, msg):
        assert a == b, '%s(得到 %r,應該是 %r)' % (msg, a, b)

    d = tempfile.mkdtemp(prefix='mvp_player_selftest_')
    gd = os.path.join(d, 'game')
    dbdir = os.path.join(gd, 'data', 'database')
    os.makedirs(dbdir)
    path = os.path.join(dbdir, 'attrib.dat')
    backup = path + BAK_SUFFIX
    origin = _fake_roster([('Cory', 'Abbott'), ('Chin-Feng', 'Chen'), ('Dai-Kang', 'Yang')])
    open(path, 'wb').write(origin)
    outside = os.path.join(d, 'precious.txt')
    open(outside, 'wb').write(b'PRECIOUS-DO-NOT-TOUCH\n')

    def leftovers():
        """資料夾裡有沒有留下暫存殘骸。每一條失敗的路走完都要是 0。"""
        return [f for f in os.listdir(dbdir) if '.tmp-' in f or '.part' in f]

    # ── 正向 1:讀得出來 ────────────────────────────────────
    raw, _txt, nl, lines, hdr = read_roster(path)
    eq(raw, origin, '讀進來的位元組跟寫下去的不一樣')
    eq(nl, '\r\n', '換行字元認錯了')
    for c in ('first_name', 'last_name', 'playerattrib_jerseynum', 'playerattrib_speed'):
        assert c in hdr, '表頭查不到 %s' % c
    eq(roster_row_count(lines, 'test'), 3, '球員數不對')
    n['fwd'] += 4

    # ── 正向 6:set_field 只動那一格 ────────────────────────
    one = set_field(lines[1], hdr['playerattrib_speed'], '88')
    eq(len(one.split(',')), len(lines[1].split(',')), 'set_field 把格數改掉了')
    eq(parse_row(one)[hdr['playerattrib_speed']], '88', 'set_field 沒改到那一格')
    eq(parse_row(one)[hdr['first_name']], 'Cory', 'set_field 動到別格了')
    n['fwd'] += 3

    # ── 正向 2:--export 不動名冊 ───────────────────────────
    csvp = os.path.join(d, 'players.csv')
    import io as _io
    import contextlib as _ctx
    with _ctx.redirect_stdout(_io.StringIO()):
        eq(cmd_export(path, csvp), 0, '--export 應該回 0')
    eq(open(path, 'rb').read(), origin, '--export 動到名冊了')
    with open(csvp, encoding='utf-8-sig', newline='') as f:
        exported = list(csv.DictReader(f))
    eq(len(exported), 3, '匯出的列數不對')
    # 匯出的 CSV 權限要跟「一般開檔寫出來的檔」一樣。暫存檔是 0600,
    # 忘了補權限的話匯出的表會變成只有自己看得到 —— 而使用者要拿它去 Excel,
    # 也常常複製給別人。拿一個真的用 open() 建出來的檔當尺,不自己算數字。
    #(Windows 的權限位元不是這一套,那邊跳過 —— 測不出來就別假裝測過了。)
    if os.name != 'nt':
        moderef = os.path.join(d, 'mode_ref.csv')
        open(moderef, 'w').close()
        eq(os.stat(csvp).st_mode & 0o777, os.stat(moderef).st_mode & 0o777,
           '匯出的 CSV 權限跟一般開檔建出來的不一樣(暫存檔的 0600 漏出去了)')
        n['fwd'] += 1
    n['fwd'] += 3

    # ── 反向餌 I:--export 的目的檔是符號連結 ────────────────
    #    2026-09-06 補這道門之前,`open(out, 'w')` 會**跟著連結**把資料夾外
    #    那個檔整個蓋成 CSV,而畫面上照樣印「匯出 N 位球員」——
    #    本站在暫存複本上重現過。跟名冊、備份是同一種洞,只是它沒有備份可以救。
    baitcsv = os.path.join(d, 'exported.csv')
    os.symlink(outside, baitcsv)
    try:
        with _ctx.redirect_stdout(_io.StringIO()):
            cmd_export(path, baitcsv)
    except Stop:
        pass
    else:
        raise AssertionError('餌 I 失效:--export 對著符號連結竟然照樣寫')
    eq(open(outside, 'rb').read(), b'PRECIOUS-DO-NOT-TOUCH\n',
       '餌 I 失效:資料夾外那個檔被寫穿了')
    assert os.path.islink(baitcsv), '餌 I 失效:那個連結被動過'
    os.remove(baitcsv)
    # 斷掉的連結也是連結。這一半同時證明「上面那道 os.path.exists 擋不住它」:
    # 對斷掉的連結 exists 回 False,所以非得另外用 islink 看一次不可。
    dangcsv = os.path.join(d, 'dangling.csv')
    os.symlink(os.path.join(d, 'no-such-file'), dangcsv)
    assert not os.path.exists(dangcsv), 'exists() 對斷掉的連結應該回 False'
    try:
        with _ctx.redirect_stdout(_io.StringIO()):
            cmd_export(path, dangcsv)
    except Stop:
        pass
    else:
        raise AssertionError('餌 I 失效:--export 對著斷掉的連結竟然照樣寫')
    assert not os.path.exists(os.path.join(d, 'no-such-file')), \
        '餌 I 失效:連結指到的位置被建出來了'
    os.remove(dangcsv)
    eq(open(path, 'rb').read(), origin, '餌 I 失效:被擋下了還是動到名冊')
    n['rev'] += 5

    # ── 正向 3:--import 預覽不寫 ───────────────────────────
    editp = os.path.join(d, 'edit.csv')
    with open(editp, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        w.writerow([exported[1]['id'], 'Chieh-Hsien', 'Wang', '77', '88'])
    with _ctx.redirect_stdout(_io.StringIO()):
        eq(cmd_import(path, editp, False), 0, '預覽應該回 0')
    eq(open(path, 'rb').read(), origin, '預覽動到名冊了')
    assert not os.path.lexists(backup), '預覽不該產生備份'
    n['fwd'] += 3

    # ── 反向餌 A:`<備份>.part` 是指向資料夾外的符號連結 ────
    #    舊版會 shutil.copy2(src, part) 跟著連結,把外面那個檔寫成整份名冊。
    bait = backup + '.part'
    os.symlink(outside, bait)
    with _ctx.redirect_stdout(_io.StringIO()):
        eq(cmd_import(path, editp, True), 0, '--apply 應該回 0')
    eq(open(outside, 'rb').read(), b'PRECIOUS-DO-NOT-TOUCH\n',
       '餌 A 失效:資料夾外那個檔被寫穿了')
    assert os.path.islink(bait), '餌 A 失效:那個連結被動過'
    os.remove(bait)
    n['rev'] += 2

    # ── 正向 4:真的改到、備份出現、沒點名的行不動 ──────────
    assert os.path.isfile(backup) and not os.path.islink(backup), '備份沒出現'
    eq(open(backup, 'rb').read(), origin, '備份的內容不是動手前那一份')
    _r2, _t2, _n2, lines2, _h2 = read_roster(path)
    eq(parse_row(lines2[2])[hdr['first_name']], 'Chieh-Hsien', '名字沒寫進去')
    eq(parse_row(lines2[2])[hdr['playerattrib_speed']], '88', '速度沒寫進去')
    eq(lines2[1], lines[1], '沒點名的第 1 行被動到了')
    eq(lines2[3], lines[3], '沒點名的第 3 行被動到了')
    eq(len(open(path, 'rb').read().split(b'\r\n')), len(origin.split(b'\r\n')),
       'CRLF 的數量變了')
    n['fwd'] += 6

    # ── 反向餌 F:三態登記,以及它講的那三句話 ───────────────
    assert APPLIED['done'] is True, '餌 F 失效:寫過名冊了,登記卻還是「還沒動」'
    eq(APPLIED['phase'], 'replaced', '餌 F 失效:寫過名冊了,三態卻不是 replaced')
    eq(APPLIED['path'], path, '餌 F 失效:登記記錯檔案')

    # 「正在換」必須登記在**換名之前**。登記在後面的話那道縫還在,
    # 而這一格正是為那道縫留的保險。把 os.replace 換成一個會回頭看登記的版本,
    # 就量得出兩者的先後 —— 只讀狀態、不改行為,原本那個照樣呼叫。
    seen = {}
    real_replace0 = os.replace

    def _watch_replace(a, b):
        seen['phase'] = APPLIED['phase']
        return real_replace0(a, b)
    os.replace = _watch_replace
    try:
        atomic_write(path, open(path, 'rb').read())    # 內容原封不動地再寫一次
    finally:
        os.replace = real_replace0
    eq(seen.get('phase'), 'replacing', '餌 F 失效:換名的當下還沒登記「正在換」')

    # 三態各自要說對話。登記對了而話說錯,對使用者是一樣的傷害 ——
    # 他看到的只有這三句,不是那個字典。
    def _said(phase, done):
        keep_ = dict(APPLIED)
        APPLIED.update({'phase': phase, 'done': done, 'path': path})
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf):
            _print_interrupt_state()
        APPLIED.update(keep_)
        return buf.getvalue()

    said = _said('idle', False)
    assert '什麼都沒有動到' in said, '餌 F 失效:還沒動卻沒說「什麼都沒有動到」'
    said = _said('replacing', False)
    assert '什麼都沒有動到' not in said, \
        '餌 F 失效:正在換的時候竟然說「什麼都沒有動到」'
    assert '無法確定' in said and '--restore' in said, \
        '餌 F 失效:正在換的時候沒說「無法確定」,或沒印還原的路'
    said = _said('replaced', True)
    assert '什麼都沒有動到' not in said and '--restore' in said, \
        '餌 F 失效:換過了卻沒印還原的路'
    n['rev'] += 8

    # ── 正向 5:--restore 逐位元組回到原狀 ──────────────────
    with _ctx.redirect_stdout(_io.StringIO()):
        eq(cmd_restore_cli(path), 0, '--restore 應該回 0')
    eq(open(path, 'rb').read(), origin, '--restore 沒有逐位元組還原')
    eq(leftovers(), [], '--restore 留下殘骸')
    n['fwd'] += 3

    # ── 反向餌 D:換名之前的複驗讀到不對的東西 ──────────────
    #    _read_bytes 是複驗唯一的口子,換掉它就等於演出「寫下去的跟讀回來的不一樣」。
    before = open(path, 'rb').read()
    real_read = globals()['_read_bytes']
    globals()['_read_bytes'] = lambda p: b'WRONG'
    try:
        atomic_write(path, origin.replace(b'Cory', b'Kory'))
    except Stop:
        pass
    else:
        raise AssertionError('餌 D 失效:複驗讀到不對的東西竟然照樣換名')
    finally:
        globals()['_read_bytes'] = real_read
    eq(open(path, 'rb').read(), before, '餌 D 失效:正本被動到了')
    eq(leftovers(), [], '餌 D 失效:留下殘骸')
    n['rev'] += 3

    # ── 反向餌 E:os.replace 當場失敗(還原做到一半)────────
    real_replace = os.replace

    def boom(*_a, **_k):
        raise OSError(5, 'Input/output error')
    os.replace = boom
    # 換名**失敗**的時候登記不可以留在「換過了」—— 不然下一次 Ctrl-C 會謊報
    # 「檔案可能改了」,害人白跑一趟還原。這裡先把三態歸零才測得出來
    #(前面幾道正向測試已經把它推到 replaced 了)。
    keep = dict(APPLIED)
    APPLIED.update({'done': False, 'phase': 'idle', 'path': None})
    try:
        _restore_check(backup, path)
    except Stop as e:
        # 磁碟那一類的錯要翻成人話(這一課的讀者看不懂 traceback),
        # 而且那句話必須說「沒有被動到」—— 說錯了他會跑去做不必要的還原。
        assert '沒有被動到' in str(e), '餌 E 失效:訊息沒說清楚正本沒事:%s' % e
    else:
        raise AssertionError('餌 E 失效:換名失敗了卻沒有丟出來')
    finally:
        os.replace = real_replace
    assert APPLIED['done'] is False, '餌 E 失效:換名失敗了,登記卻停在「換過了」'
    # 三態也要跟著收回「還沒動」。停在 'replacing' 的話,收尾會說
    # 「換好了沒有無法確定」—— 而這裡是**確定**沒換成的,說不確定就是說謊。
    eq(APPLIED['phase'], 'idle', '餌 E 失效:確定沒換成,三態卻沒收回「還沒動」')
    APPLIED.update(keep)
    eq(open(path, 'rb').read(), before, '餌 E 失效:換名失敗卻動到正本')
    eq(leftovers(), [], '餌 E 失效:留下殘骸')
    n['rev'] += 5

    # ── 反向餌 E2:資料夾唯讀,連暫存檔都建不出來 ────────────
    #    (Windows 上 chmod 不擋寫入、root 也擋不住,那兩種情況跳過這一塊 ——
    #     測不出來就別假裝測過了。)
    if os.name != 'nt' and getattr(os, 'geteuid', lambda: 1)() != 0:
        os.chmod(dbdir, 0o500)
        try:
            atomic_write(path, origin)
        except Stop as e:
            assert '沒有被動到' in str(e), '餌 E2 失效:訊息沒說清楚正本沒事:%s' % e
        else:
            raise AssertionError('餌 E2 失效:資料夾唯讀竟然還寫得進去')
        finally:
            os.chmod(dbdir, 0o700)
        eq(open(path, 'rb').read(), before, '餌 E2 失效:資料夾唯讀卻動到正本')
        eq(leftovers(), [], '餌 E2 失效:留下殘骸')
        n['rev'] += 3

    # ── 反向餌 B:名冊本身是符號連結 ────────────────────────
    d2 = os.path.join(d, 'linked')
    os.makedirs(d2)
    linkdst = os.path.join(d2, 'attrib.dat')
    os.symlink(outside, linkdst)
    try:
        atomic_write(linkdst, origin)
    except Stop:
        pass
    else:
        raise AssertionError('餌 B 失效:目的檔是符號連結竟然照樣寫')
    eq(open(outside, 'rb').read(), b'PRECIOUS-DO-NOT-TOUCH\n',
       '餌 B 失效:連結指到的檔被寫穿了')
    # 同一件事走批次那道門,而且**這個餌要下對**:連結必須指向一份
    # **讀得懂的名冊**。指向垃圾的話,`read_roster` 會先擋下來,
    # 那時測到的是「垃圾檔擋得住」,不是「符號連結擋得住」——
    # 2026-09-05 第一版的餌就下錯在這裡,反向測試(把守門拿掉)照樣全綠。
    real2 = os.path.join(d2, 'other_roster.dat')
    open(real2, 'wb').write(origin)
    linkdst2 = os.path.join(d2, 'attrib2.dat')
    os.symlink(real2, linkdst2)
    linkbak = linkdst2 + BAK_SUFFIX
    try:
        with _ctx.redirect_stdout(_io.StringIO()):
            cmd_import(linkdst2, editp, True)
    except Stop:
        pass
    else:
        raise AssertionError('餌 B 失效:--apply 對著符號連結名冊竟然照樣寫')
    assert not os.path.lexists(linkbak), \
        '餌 B 失效:名冊是連結卻做了備份(那份備份是別人的內容)'
    eq(open(real2, 'rb').read(), origin, '餌 B 失效:批次那道門把連結指到的名冊改掉了')
    n['rev'] += 5

    # ── 反向餌 C:備份檔是斷掉的符號連結 ────────────────────
    #    這一條同時證明「不能用 os.path.exists() 判斷」:對斷掉的連結它回 False。
    dangling = os.path.join(d2, 'attrib.dat' + BAK_SUFFIX)
    os.symlink(os.path.join(d, 'nothing-here'), dangling)
    assert not os.path.exists(dangling), 'exists() 對斷掉的連結應該回 False'
    assert os.path.lexists(dangling), 'lexists() 對斷掉的連結應該回 True'
    try:
        atomic_backup(path, dangling)
    except Stop:
        pass
    else:
        raise AssertionError('餌 C 失效:備份檔是斷掉的連結竟然照樣寫')
    assert not os.path.exists(os.path.join(d, 'nothing-here')), \
        '餌 C 失效:連結指到的位置被建出來了'
    n['rev'] += 4

    # ── 反向餌 G:截斷的備份要被 _restore_check 擋下 ─────────
    open(backup, 'wb').write(origin[:len(origin) // 3])
    try:
        _restore_check(backup, path)
    except Stop:
        pass
    else:
        raise AssertionError('餌 G 失效:截斷的備份竟然蓋得上去')
    eq(open(path, 'rb').read(), before, '餌 G 失效:被擋下了還是動到正本')
    eq(leftovers(), [], '餌 G 失效:留下殘骸')
    n['rev'] += 3

    # ── 反向餌 J:「不可中斷的一段」不可以是空話 ──────────────
    #    這裡**不真的殺自己一次**:os.kill 在 Windows 上的語義跟 POSIX 不同,
    #    而且真的丟一個 SIGINT 進來會弄亂後面幾道測試。改成驗三件看得見的事 ——
    #    進去之後 SIGINT 的處理器換成 `_NoInterrupt` 自己的、期間「收到訊號」
    #    不會當場打斷 body、離開之後把原本的處理器裝回去並且補丟出來。
    #    (真的按下 Ctrl-C 的那一種另外用變體檔對真實的 --apply 測過,
    #     結果寫在這一輪的回報裡;那種測試會殺掉整個行程,放不進這裡。)
    before_handler = signal.getsignal(signal.SIGINT)
    ran = []
    try:
        with _NoInterrupt() as _ni:
            assert signal.getsignal(signal.SIGINT) is not before_handler, \
                '餌 J 失效:_NoInterrupt 沒有真的接管 SIGINT,「押後」是假的'
            _ni._remember(signal.SIGINT, None)     # 等同「這一刻按了 Ctrl-C」
            ran.append('body 跑完了')              # 沒被打斷才到得了這一行
    except KeyboardInterrupt:
        ran.append('離開之後才丟出來')
    eq(ran, ['body 跑完了', '離開之後才丟出來'], '餌 J 失效:押後中斷沒有照約定發生')
    assert signal.getsignal(signal.SIGINT) is before_handler, \
        '餌 J 失效:離開之後沒有把原本的 SIGINT 處理器裝回去'
    n['rev'] += 3

    # ── 反向餌 H:輸入的兩道門 ──────────────────────────────
    for bad_name in ('陳金鋒', 'Wang,Chien-Ming', 'A' * 23):
        try:
            check_name(bad_name)
        except Stop:
            pass
        else:
            raise AssertionError('餌 H 失效:check_name 放行了「%s」' % bad_name)
    for bad_num in ('100', '-1', '５', '7.5', ''):
        try:
            check_num(bad_num, 0, 99, '測試')
        except Stop:
            pass
        else:
            raise AssertionError('餌 H 失效:check_num 放行了「%s」' % bad_num)
    eq(check_num('007', 0, 99, '測試'), '7', 'check_num 沒有正規化 007')
    n['rev'] += 9

    # ── 反向餌 K:沒人接住的例外不可以只丟一片英文 ────────────
    #    守的是**收尾**那一段。寫進去之後才出狀況(防毒軟體鎖住檔案、外接碟被拔掉)
    #    的時候,畫面第一句必須說得出名冊動了沒有、還要印還原的路;
    #    原本那個例外也不可以被吞掉,不然班主任查不出原因。
    #    做法:把 `run_cli` 換成一個「就是要爆炸」的版本,讓 `_cli_entry` 真的
    #    走一次那條收尾 —— 測的是正式那一段程式,不是另外抄一份來測。
    #    順便把 `input` 換掉:Stop 那條路會停下來等按鍵,測試不可以卡在那裡。
    import builtins as _bi

    def _crashed(phase, done, err_):
        """讓 `_cli_entry` 在指定的三態下吃到 err_,回傳 (結束碼, 螢幕, 英文那段)。"""
        keep_ = dict(APPLIED)
        APPLIED.update({'phase': phase, 'done': done, 'path': path})
        real_run_cli, real_input = run_cli, _bi.input

        def _boom(_argv):
            raise err_
        globals()['run_cli'] = _boom
        _bi.input = lambda *a, **k: ''
        buf, errbuf = _io.StringIO(), _io.StringIO()
        try:
            with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(errbuf):
                code_ = _cli_entry(['mvp_player.py', 'x', '--restore'])
        except Exception as _e:      # 收尾自己沒接住 = 這一格就是壞的
            raise AssertionError('餌 K 失效:例外一路衝出收尾沒人接住(%r)' % (_e,))
        finally:
            globals()['run_cli'] = real_run_cli
            _bi.input = real_input
            APPLIED.update(keep_)
        return code_, buf.getvalue(), errbuf.getvalue()

    # (一)名冊已經換過了才出狀況 —— 最危險的那一種,漏說他就直接進遊戲了
    code_, said, errtxt = _crashed('replaced', True, PermissionError(13, 'Permission denied'))
    eq(code_, 1, '餌 K 失效:沒人接住的例外結束碼不是 1')
    assert '什麼都沒有動到' not in said, '餌 K 失效:名冊換過了卻說「什麼都沒有動到」'
    assert '可能已經寫進去了' in said and '--restore' in said, \
        '餌 K 失效:名冊換過了卻沒說,也沒印還原的路'
    assert '你中斷了' not in said, '餌 K 失效:使用者沒有中斷,不可以說是他中斷的'
    assert 'PermissionError' in errtxt, '餌 K 失效:原本的例外被吞掉了,班主任查不到原因'
    # (二)一個位元組都還沒寫 —— 這時要說清楚沒動到,不要害他白跑一次還原
    code_, said, errtxt = _crashed('idle', False, RuntimeError('boom'))
    eq(code_, 1, '餌 K 失效:沒人接住的例外結束碼不是 1')
    assert '什麼都沒有動到' in said, '餌 K 失效:一個位元組都沒寫卻沒說「什麼都沒有動到」'
    assert 'RuntimeError' in errtxt, '餌 K 失效:原本的例外被吞掉了'
    # (三)Stop 也一樣:名冊換過之後才丟的 Stop,不可以只印那一句就算了
    code_, said, errtxt = _crashed('replaced', True, Stop('假裝寫完之後才發現的問題'))
    eq(code_, 1, 'Stop 的結束碼不是 1')
    assert '假裝寫完之後才發現的問題' in said, '餌 K 失效:Stop 那句話不見了'
    assert '可能已經寫進去了' in said and '--restore' in said, \
        '餌 K 失效:名冊換過之後才丟的 Stop 沒有把還原的路一起講出來'
    # (四)`--selftest` 自己不可以把「名冊換過了」的登記留給收尾 —— 它只動假名冊,
    #      留下去會讓一道測試沒過長得像「你的遊戲檔可能被改了」。
    #      拿一個「弄髒登記之後就爆炸」的假 selftest 去跑真的 `run_cli`。
    #      ⚠️ 進去之前要先把登記**壓成 idle**:跑到這裡時它本來就是 'replaced'
    #         (前面那些正向測試真的寫過假名冊),不壓的話「進去前 == 出來後」
    #         會自動成立,這個餌就永遠不會紅 —— 種餌種在對照組上等於沒種。
    keep_applied = dict(APPLIED)
    APPLIED.update({'done': False, 'phase': 'idle', 'path': None})
    real_selftest = selftest

    def _dirty_selftest():
        APPLIED.update({'done': True, 'phase': 'replaced', 'path': 'X'})
        raise RuntimeError('假裝測試沒過')
    globals()['selftest'] = _dirty_selftest
    try:
        run_cli(['mvp_player.py', '--selftest'])
    except RuntimeError:
        pass
    finally:
        globals()['selftest'] = real_selftest
    eq(APPLIED['phase'], 'idle', '餌 K 失效:--selftest 把三態登記留給了收尾')
    eq(APPLIED['done'], False, '餌 K 失效:--selftest 把「換過了」留給了收尾')
    APPLIED.update(keep_applied)
    n['rev'] += 13

    shutil.rmtree(d, ignore_errors=True)
    print('  ✅ --selftest 全過:%d 道(正向 %d 道、反向餌 %d 道)。'
          % (n['fwd'] + n['rev'], n['fwd'], n['rev']))
    print('     全程只用自己造的名冊,一個遊戲檔都沒有碰。')
    return 0


def run_cli(argv):
    """有參數就走這裡。回傳 None 表示「不是批次模式」,讓它掉回互動模式。

    這是「兩道門」的分岔點,而且**回傳 None 這件事就是那道岔**:
    只給一個資料夾路徑而沒給 --export / --import / --restore 的話,
    它會回 None,檔尾就改去跑互動模式 —— 使用者把資料夾拖到腳本上也能用。

    手寫參數解析而不用 argparse:這一課的雙擊入口(.command / .bat)
    要的是「沒有參數時完全不像命令列工具」,argparse 會在
    參數不對時自己印出英文用法並直接結束,那對這一課的讀者是反效果。
    """
    args = [a for a in argv[1:] if a.strip()]
    if not args:
        return None
    gamedir = None
    mode = None
    target = None
    apply_it = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--export' or a == '--import':
            mode = a[2:]
            i += 1
            if i >= len(args):
                raise Stop('%s 後面要接一個 CSV 檔名。' % a)
            target = args[i]
        elif a == '--apply':
            apply_it = True
        elif a == '--restore':
            mode = 'restore'
        elif a == '--selftest':
            # 自我測試。不需要遊戲資料夾,也不碰任何遊戲檔 ——
            # 所以下面「猜遊戲資料夾」那一段之前就會先分岔出去。
            mode = 'selftest'
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        elif a.startswith('-'):
            raise Stop('不認得的參數:%s\n  用 --help 看用法。' % a)
        else:
            gamedir = a
        i += 1
    # 沒有任何一個模式旗標 = 不是批次模式,交還給互動模式。
    if mode is None:
        return None
    # --selftest 在「找遊戲資料夾」之前就分岔出去:它自己造一份名冊,
    # 不需要遊戲,也**不可以**碰到任何遊戲檔。
    if mode == 'selftest':
        # 跑完(或跑壞)之後把三態登記收回原狀。selftest 全程只動自己造的假名冊,
        # 那個「換過了」不可以留給收尾看 —— 不然一道測試沒過會長得像
        #「你的遊戲檔可能被改了,快去還原」,而它指的其實是暫存資料夾裡的假名冊。
        # (2026-09-11 補;沒有這一段的樣子由反向餌 K 的第四小段擋著)
        _keep = dict(APPLIED)
        try:
            return selftest()
        finally:
            APPLIED.update(_keep)
    # 批次模式**只接受「剛好猜到一份」**。猜到零份或多份都要使用者明講 ——
    # 這條路沒有人在旁邊看,猜錯就是改到別份遊戲。
    if not gamedir:
        dirs = guess_gamedirs()
        if len(dirs) != 1:
            raise Stop('批次模式要明確指定遊戲資料夾:\n'
                       '  python3 mvp_player.py "<遊戲資料夾>" %s' % ('--' + mode))
        gamedir = dirs[0]
    path = os.path.join(gamedir, 'data', 'database', 'attrib.dat')
    if not os.path.isfile(path):
        raise Stop('%s 底下找不到 data/database/attrib.dat。' % gamedir)
    if mode == 'export':
        return cmd_export(path, target)
    if mode == 'import':
        return cmd_import(path, target, apply_it)
    return cmd_restore_cli(path)


def main():
    """互動模式:雙擊之後一句一句問。七個步驟,寫死的順序。

        1. 找遊戲       2. 問要不要還原   3. 找球員   4. 問要改什麼
        5. 印預覽並確認  6. 備份 + 寫入    7. 讀回來複驗

    ⚠️ **改球員這條路**在第 5 步之前一個位元組都沒有寫過。這一課的讀者不會打指令,
       所以「不小心按到就改掉了」是這支腳本最需要防的事,
       而防法就是把「改球員」那個寫入動作關在「打 y」後面。

    ⚠️ 例外是**第 2 步那條還原分支,它會寫**。打 r 再按 Enter 就把備份寫回
       名冊然後 return,第 3 步以後不會跑到。蓋回去的是「第一次改之前」那份名冊
       (第 6 步已經有備份就保留最早那一份)。
       這一步**跟 --restore 走同一個 _restore_check**(五道把關 + 原子寫入 +
       寫完逐位元組比對),備份要是壞的會被擋下來,不會蓋掉正本。
       2026-09-05 之前這裡是自己呼叫 shutil.copy2,一道都沒走 —— 那個洞已經補掉。
    """
    print()
    line('=')
    print(' ⚾  把一位球員改成你想要的球員')
    line('=')
    print('  這支工具會一句一句問你,不用打指令。')
    print('  隨時按 Ctrl + C 就離開,還沒確認之前什麼都不會改。')
    print()

    # 1. 找遊戲
    # 三條分支:猜不到就請人把資料夾拖進來、剛好一份就直接用、
    # 多份就列出來讓人選。互動模式**可以**問,所以不像批次模式那樣直接拒絕。
    dirs = guess_gamedirs()
    if not dirs:
        print('  找不到遊戲資料夾。')
        print('  請把**遊戲資料夾**拖進這個視窗,再按 Enter:')
        print('  (那個資料夾裡面要有一個叫 data 的資料夾)')
        # 把路徑左右的引號剝掉:終端機在拖曳含空白的資料夾時會自動加上引號,
        # 不剝的話 os.path.isfile 一定找不到,而使用者完全看不出自己哪裡做錯。
        g = ask('  > ').strip().strip('"').strip("'")
        if not os.path.isfile(os.path.join(g, 'data', 'database', 'attrib.dat')):
            raise Stop('那個資料夾裡找不到 data\\database\\attrib.dat。\n'
                       '  你可能拖錯資料夾了。')
        gamedir = g
    elif len(dirs) == 1:
        gamedir = dirs[0]
        print('  找到遊戲了:%s' % gamedir)
    else:
        print('  找到不只一份遊戲,你要改哪一份?')
        for i, d in enumerate(dirs, 1):
            print('    %d. %s' % (i, d))
        c = check_num(ask('  打數字再按 Enter > '), 1, len(dirs), '選項')
        gamedir = dirs[int(c) - 1]

    path = os.path.join(gamedir, 'data', 'database', 'attrib.dat')
    backup = path + BAK_SUFFIX
    # 符號連結的檢查放在**問問題之前**:不能寫的話,不該讓人先回答一輪問題。
    _refuse_symlink(path, os.path.basename(path))
    _refuse_symlink(backup, '備份檔 %s' % os.path.basename(backup))
    raw, txt, nl, lines, hdr = read_roster(path)
    print('  名冊讀好了,裡面有 %d 位球員。' % (len([l for l in lines[1:] if l.strip()])))
    print()

    # 2. 還原?
    # 備份存在 = 這個人以前改過。**還原要排在「找球員」之前**,
    # 因為想還原的人不該被逼著先挑一位球員才看得到出口。
    if os.path.exists(backup):
        line()
        print('  ⓘ 這份名冊你以前改過,備份還在。')
        print('    要「還原成沒改過的樣子」的話,打 r 再按 Enter。')
        print('    要繼續改別的球員,直接按 Enter。')
        if ask('  > ').lower() == 'r':
            # 兩條還原路徑走同一組把關:_restore_check 五道全過了,
            # 才由它自己用 atomic_write 寫回去,並逐位元組比對。
            # 任何一道不過都會丟 Stop,底下這兩行印不出來。
            _restore_check(backup, path)
            print('\n  ✅ 已經還原成第一次改之前的樣子。')
            print('     備份留著沒刪(%s)。' % os.path.basename(backup))
            return 0
        print()

    # 3. 找球員
    line()
    print('  你想改哪一位球員?')
    print('  打他名字的一部分就好,要用**英文**。')
    print('  (名冊裡沒有中文。陳金鋒在遊戲裡叫 Chin-Feng Chen)')
    # 問到問出一個「不多不少」的結果為止。
    # 上限 12 是刻意的:一次列超過十幾個選項,人反而挑不到,
    # 而挑錯就是改到別人身上。與其列一長串,不如請他多打兩個字母。
    while True:
        q = ask('  > ')
        if not q:
            continue
        hits = find_players(lines, hdr, q)
        if not hits:
            print('    找不到名字含「%s」的球員。換個拼法,或只打兩三個字母。' % q)
            continue
        if len(hits) > 12:
            print('    找到 %d 位,太多了。多打幾個字母縮小範圍。' % len(hits))
            continue
        break

    fn, ln, jn = hdr['first_name'], hdr['last_name'], hdr['playerattrib_jerseynum']
    sp = hdr['playerattrib_speed']
    print()
    for i, (li, name, d) in enumerate(hits, 1):
        print('    %d. %-24s 背號 %-3s 跑壘速度 %s'
              % (i, name, d.get(jn, '?'), d.get(sp, '?')))
    print()
    idx = int(check_num(ask('  要改哪一個?打數字再按 Enter > '), 1, len(hits), '選項'))
    lineno, oldname, row = hits[idx - 1]

    # 4. 要改什麼
    line()
    print('  你選的是:%s(背號 %s,跑壘速度 %s)'
          % (oldname, row.get(jn, '?'), row.get(sp, '?')))
    print()
    print('  要改什麼?可以一次改好幾個,不改的直接按 Enter 跳過。')
    print()
    # 四個問句,每一句都可以直接按 Enter 跳過。
    # 值一填進來就當場檢查(check_name / check_num),不合格立刻丟 Stop ——
    # 互動模式下當場講比較有用,不必像批次模式那樣攢到最後一起報。
    changes = []

    v = ask('  新的名(first name,例如 Chieh-Hsien)> ')
    if v:
        changes.append((fn, check_name(v), '名'))
    v = ask('  新的姓(last name,例如 Chen)> ')
    if v:
        changes.append((ln, check_name(v), '姓'))
    v = ask('  新的背號(0-99)> ')
    if v:
        changes.append((jn, check_num(v, 0, 99, '背號'), '背號'))
    v = ask('  新的跑壘速度(0-99,現在是 %s)> ' % row.get(sp, '?'))
    if v:
        changes.append((sp, check_num(v, 0, 99, '跑壘速度'), '跑壘速度'))

    # 填了但跟原本一樣的,不算改動 —— 預覽裡不該出現「Chen → Chen」
    same = [(i, v, lab) for i, v, lab in changes if row.get(i, '') == v]
    changes = [c for c in changes if c not in same]
    for _i, _v, lab in same:
        print('  (%s 本來就是 %s,不用改)' % (lab, _v))

    if not changes:
        print('\n  沒有任何一項需要改。什麼都沒有動到。')
        return 0

    # 5. 預覽
    print()
    line()
    print('  這是**預覽**,還沒有動到任何檔案:')
    print()
    for i, val, label in changes:
        print('    %-10s %s  →  %s' % (label, row.get(i, '(空的)') or '(空的)', val))
    print()
    print('  改完之後他會變成:')
    newfn = next((v for i, v, _ in changes if i == fn), row.get(fn, ''))
    newln = next((v for i, v, _ in changes if i == ln), row.get(ln, ''))
    newjn = next((v for i, v, _ in changes if i == jn), row.get(jn, ''))
    print('    %s  背號 %s' % (('%s %s' % (newfn, newln)).strip(), newjn))
    print()
    # **只有 y 算同意**,其他任何輸入(含直接按 Enter)都當取消。
    # 這是整支互動流程唯一的閘門,所以判準要嚴,不可以做成「按 Enter 等於 yes」。
    print('  確定要改嗎?打 y 再按 Enter。打別的都算取消。')
    if ask('  > ').lower() != 'y':
        print('\n  取消了,什麼都沒有動到。')
        return 0

    # 6. 備份 + 寫入
    # 備份已經有了就保留最早那一份 —— 那才是「動手前的名冊」。
    if not os.path.exists(backup):
        atomic_backup(path, backup)
        print('\n  已經先備份成 %s' % os.path.basename(backup))
    else:
        print('\n  備份已經有了,保留最早那一份(%s)' % os.path.basename(backup))

    # 只重寫**那一行**。名冊裡其餘每一行連碰都沒碰過,
    # 用原本的換行字元接回去、以 latin-1 編回位元組,整份檔案的其餘部分逐位元組不變。
    newline = lines[lineno]
    for i, val, _ in changes:
        newline = set_field(newline, i, val)
    lines2 = list(lines)
    lines2[lineno] = newline
    out = nl.join(lines2).encode('latin-1')

    # 一樣走 atomic_write:先寫暫存、fsync、套回原檔權限、再換名。
    atomic_write(path, out)

    # 7. 複驗:讀回來確認真的改到了
    # 從磁碟重新讀一次,不看記憶體裡的 out。
    # 「印了成功」跟「真的寫進去了」是兩件事,這一段就是在分辨那兩件事。
    _r2, _t2, _nl2, lines3, hdr3 = read_roster(path)
    check = parse_row(lines3[lineno])
    bad = [(lab, val, check.get(i, '')) for i, val, lab in changes if check.get(i, '') != val]
    print()
    line('=')
    if bad:
        print('  🔴 寫進去了,但讀回來對不上:')
        for lab, want, got in bad:
            print('     %s 應該是 %s,讀回來是 %s' % (lab, want, got))
        print('  請跑一次這支工具選 r 還原,然後回報給班主任。')
        return 1
    print('  ✅ 改好了!')
    print('     %s  背號 %s' % (('%s %s' % (newfn, newln)).strip(), newjn))
    print()
    print('  進遊戲看看吧。想改回來的話,再跑一次這支工具,')
    print('  它會問你要不要還原。')
    line('=')
    print()
    return 0


def _cli_entry(argv):
    """整支腳本的收尾:分兩道門進去,四種方式出來。回傳行程的結束碼。

    2026-09-11 從 `if __name__ == '__main__':` 底下抽成函式,**為了讓它測得到**。
    寫在 `if __name__` 底下的程式沒有任何辦法在 `--selftest` 裡跑到,
    而「出狀況的時候有沒有說實話」正是這支腳本最需要被測到的一段
    (反向餌 K 就是拿這個函式真的走一次那條收尾)。抽出來的過程沒有改行為:
    原本 `sys.exit(X)` 的地方現在 `return X`,由底下那一行 `sys.exit` 送出去。

    四種出口:
      正常          run_cli 給的結束碼;它回 None 就是「沒給模式旗標」,改跑互動模式
      Stop          自己丟的、講人話的錯 → 印一句中文,結束碼 1
      沒人接住的例外 這支工具自己出狀況 → **先講檔案動了沒有**,再把英文丟給班主任,結束碼 1
      Ctrl-C        照三態講實話,結束碼 130
    """
    # 兩道門的分岔就在這一行:run_cli 回 None 代表「沒有給模式旗標」,
    # 那就跑互動模式;回了數字就是批次模式的結束碼,直接拿去當行程結束碼。
    #
    # Stop 統一在這裡接住,印成一句中文,再**等使用者按 Enter** ——
    # Windows 上雙擊執行時視窗會在程式結束的瞬間關掉,
    # 沒有這一行的話錯誤訊息只會閃一下,使用者什麼都看不到。
    try:
        _r = run_cli(argv)
        return main() if _r is None else _r
    except Stop as e:
        print()
        print('  ✗ %s' % e)
        # 這個 Stop 要是在名冊換過之後才丟出來的(寫進去了才發現讀不回來那一種),
        # 光印那句話會讓人以為什麼都沒發生。**動了就要說**,而且要把還原的路一起給他。
        # 沒動到的時候這一段不會印任何東西,所以平常看到的畫面一個字都沒有變。
        if APPLIED['done'] or APPLIED['phase'] == 'replacing':
            print()
            _print_interrupt_state(interrupted=False)
        print()
        try:
            input('  按 Enter 關閉這個視窗。')
        except (EOFError, KeyboardInterrupt):
            pass
        return 1
    except Exception:
        # ⚠️ 這一段守的是「**沒有人預料到**的例外」。2026-09-11 之前這裡沒有東西接,
        #    所以任何一個沒被翻成 Stop 的錯(最現實的是防毒軟體或同步工具在
        #    `os.replace()` 之後那一瞬間鎖住名冊,複驗那一次 open 就丟 PermissionError)
        #    會直接噴一片英文 traceback 出去 —— 而那時**名冊已經換過了**,
        #    畫面上卻一個字都沒提「你可以還原」。這一課的讀者看不懂 traceback,
        #    他會以為只是壞掉了,然後就進遊戲。
        #    本站實測(2026-09-11,在測試複本上):在複驗那一行種一個 PermissionError,
        #    修補前印的是三行英文 traceback、結束碼 1,而名冊的 sha256 真的變了。
        #    順序刻意是「先講檔案、再給英文」:讀者要的是第一句,班主任要的是後面那段。
        #    這裡**不再多等一次按鍵** —— 雙擊的兩個入口(.bat 的 pause 與 .command 的
        #    read)自己會把視窗停住,而多一個等待會讓自動跑的檢查器卡在這裡。
        print()
        print('  ✗ 這支工具自己出狀況了 —— 不是你打錯什麼。')
        print()
        _print_interrupt_state(interrupted=False)
        print()
        print('  下面這段英文是給班主任看的,請整段複製起來回報:')
        print('  https://toniliumvp.github.io/MVPBaseball/report.html')
        print()
        # 英文那一段是寫到 stderr 的,中文這幾行是 stdout。畫面上兩邊是同一個地方,
        # 但**把輸出導進檔案**的時候 stdout 會先被存起來、離開才吐出去 ——
        # 不先 flush 的話存下來的檔案裡英文會跑到中文前面,回報的人看了會錯亂。
        try:
            sys.stdout.flush()
        except (OSError, ValueError):
            pass
        traceback.print_exc()
        return 1
    except KeyboardInterrupt:
        # ⚠️ 這裡**不可以**無條件說「什麼都沒有動到」。Ctrl-C 可能落在
        #    os.replace() 之後、複驗之前 —— 那時名冊已經是新的了。
        #    _print_interrupt_state() 會看 APPLIED 旗標決定要說哪一句。
        #    結束碼一律 130:中斷不是成功,不可以回 0。
        print()
        print()
        _print_interrupt_state()
        return 130


if __name__ == '__main__':
    sys.exit(_cli_entry(sys.argv))

# ─────────────────────────────────────────────────────────────
# MIT License
#
# Copyright (c) 2026 toni
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
