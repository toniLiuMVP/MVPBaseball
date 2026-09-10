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
mvp_fix_loc.py —— 把中文語系檔裡「會讓遊戲當掉的格式符」拿掉

    先看有幾條      python3 mvp_fix_loc.py "<遊戲資料夾>"
    預覽修法        python3 mvp_fix_loc.py "<遊戲資料夾>" --fix
    真的修          python3 mvp_fix_loc.py "<遊戲資料夾>" --fix --apply
    還原            python3 mvp_fix_loc.py "<遊戲資料夾>" --restore
    自我測試        python3 mvp_fix_loc.py --selftest

⚠️ 只改 data/FEENG.LOC 與 data/IGENG.LOC,一定先備份成 .locbak,一行還原。
⚠️ **中文字一個都不會動**,只拿掉多出來的格式符。

─────────────────────────────────────────────────────────
 這在解什麼
─────────────────────────────────────────────────────────
2026-08-28,toni 的交叉實驗把範圍縮到只剩兩個檔:

  · 球場檔清到 8.51 MB(逐位元組相同)→ 英文能玩、中文照樣當
    ⇒ **「球場超過 10MB 就當」這條傳了二十年的規矩是錯的**
  · 字型瘦身 689 KB → 還是當  ⇒ 不是字型吃爆記憶體
  · 剩下的變數只有 `FEENG.LOC` 與 `IGENG.LOC`

把兩份逐條比對之後找到這個:

  ┌──────────────────────────────────────────────────────┐
  │  同一個字串編號,中英文放的是**完全不同的東西**            │
  │                                                       │
  │  編號 23484   英「Right Field Camera」      不要參數     │
  │               中「   -  %s得分。%c」        要 2 個參數  │
  │                                                       │
  │  編號 23505   英「Argument Intensity」      不要參數     │
  │               中「 - %s盜%d%s壘成功。%c」    要 4 個參數  │
  └──────────────────────────────────────────────────────┘

C 語言的 `printf` 遇到 `%s` 卻沒有對應的參數,會把**堆疊上的隨機值當成指標**
去讀記憶體 —— 那就是當機。

全掃的結果:
    IGENG.LOC(比賽中)  25 條
    FEENG.LOC(選單)   143 條
    合計 **168 條**「程式不會傳參數、字串卻要參數」

而反方向(中文的參數比英文**少**)有 247 條 —— **那不會當**,只會少印東西。
**這個不對稱正是「當機」而不是「顯示怪怪的」的原因。**
⚠️ 那 247 條裡有 79 條是量法造成的:CFMT 的旗標裡含一個半形空白,
   英文那邊的 'Checking %3 for %8 Saves.' 會被多算成兩個格式符,中文那邊
   沒有這種命中,於是英文顯得比較多。把空白從旗標裡拿掉重跑同一對檔,
   反方向剩 168 條(2026-09-03 量的);要修的那 168 條則一條不差,
   完全不受影響。細節見 CFMT 那一段。

⭐ 最關鍵的一群:IG 那 25 條裡有 11 條擠在編號 23482–23741,
   而那一段的英文是「中間三壘攝影機 / 右外野攝影機 / 抗議判決 / 投打小遊戲 /
   可變好球帶 / 打者視野 / 犯規球頻率」—— **全部是進比賽時一定會讀的比賽設定**。
   這正好對上 toni 描述的症狀:**讀取條讀完、進比賽的那一瞬間跳出**。

⚠️ 本站**沒有**實機證明「這 168 條就是主因」。上面是量到的結構事實加上症狀吻合。
   這支腳本就是拿來驗它的 —— 修掉之後如果還是當,那這條也不對。

─────────────────────────────────────────────────────────
 修法:只拿掉多出來的格式符,不動中文
─────────────────────────────────────────────────────────
以編號 23484 為例:

    修之前   「   -  %s得分。%c」     要 2 個參數
    修之後   「   -  得分。」          要 0 個參數 ← 跟英文版一樣

字面上那句話會變得不完整(少了球員名字),但**那句話本來就不該出現在那裡** ——
遊戲在那個編號要的是「右外野攝影機」,根本不是播報句。
所以拿掉之後不會有人看到殘缺的句子,只會看到一段沒有意義但**不會當**的文字。

─────────────────────────────────────────────────────────
 輸入 / 輸出 / 安全網 / 做不到的事
─────────────────────────────────────────────────────────
輸入
  · 一個位置參數:遊戲安裝資料夾(它的下一層才是 data)。
    給的資料夾底下沒有 data 就直接說「底下沒有 data 資料夾」,
    不會拐個彎去講英文語系資料夾。
  · 會被改到的檔只有兩個:<遊戲資料夾>/data/IGENG.LOC 與 data/FEENG.LOC
  · 比對用的基準:data/2023英文語系/ 或 data/英文語系/ 底下同名的那兩個檔。
    **沒有英文語系資料夾就跑不了。** 沒有基準就沒辦法判斷哪些格式符是多的,
    這時候它會停下來把話講清楚,不會用猜的去改你的檔。

輸出
  · 不加旗標        印每個檔有幾條對不上、前 8 條長什麼樣,一個位元組都不寫
  · --fix           沒加 --apply 就只印預覽(每個檔列前 3 條的修前修後)
  · --fix --apply   備份 → 重寫那兩個 .LOC → 重讀複驗(字串條數、每一條編號、
                    每一條內容都要對得上)。**對不上就自動用備份還原**,
                    備份留著不刪,而且回非 0 的 exit code
  · --restore       把 .locbak 蓋回去(**會先驗備份完不完整**),蓋完再跟備份
                    **逐位元組比一次**,比過了才刪掉備份檔。
                    **不需要 --apply**,打了就直接寫

安全網
  · --fix 預設就是預覽。沒有 --apply 就一個位元組都不會落地。
  · ⚠️ --restore 不吃上面那一條,它根本不看 --apply。main() 的判斷順序是
    --restore → --fix,--apply 完全不參與 --restore 那一條路:只打 --restore
    就會把 .locbak 蓋回 IGENG.LOC / FEENG.LOC,蓋完還把備份刪掉,
    所以「動之前一定先備份」對它不成立,它是反過來把備份用掉。
    2026-09-03 在暫存複本上實測:拿本機 data/ 底下那兩個語系檔當備份
    (IGENG.LOC 60,023 bytes、FEENG.LOC 416,753 bytes),正本各多接 5,000 個
    0x00 冒充「已經改過」,只打 --restore(沒有 --apply)之後兩個正本都被蓋回
    60,023 / 416,753 bytes、與備份逐位元組相同,兩個 .locbak 也都不見了。
    (下面那一條的把關仍然有效:備份自己被截斷的話會先被擋下來。)
  · 備份成 IGENG.LOC.locbak / FEENG.LOC.locbak,做法是「先寫一個**名字帶亂數**的
    暫存檔(tempfile.mkstemp,跟備份放同一個資料夾)、fsync、讀回來逐位元組
    比對過,再用 os.replace 換名」,中途被中斷不會留下半截備份。
    ⚠️ 名字帶亂數是刻意的。以前叫 `<備份檔>.part`,那是**可以事先預測的名字**:
    有人先在那裡擺一個指向資料夾外面的符號連結,複製就會沿著它去覆寫外面
    那個檔。mkstemp 用 O_CREAT|O_EXCL,連結先佔著也建不起來。
  · 動筆之前會先看正本與備份**是不是符號連結**,是的話整支停下來、
    一個位元組都不寫。判斷用 os.path.islink 而不是 os.path.exists ——
    指向不存在目標的連結在 exists() 眼中是 False,而 open(..., 'wb')
    照樣會沿著它去建立、覆寫外面那個檔。
  · 備份已經存在就沿用、不覆蓋,所以重複執行不會把最早那一份原檔洗掉。
    ⚠️ 沿用之前會**先驗那份備份完不完整**,而且兩個語系檔的舊備份是在
    動筆之前一起驗完的。壞掉的備份等於沒有備份,驗不過就整支停下來,
    一個位元組都不寫(以前只看「檔案存不存在」,半截備份會被照樣沿用)。
  · --restore 走 _restore_from_backup,會順著 LOCH 的結構走一遍
    (LOCL 在不在該在的位置、位移表有沒有被切掉、最後一條字串的位移有沒有
    超出檔尾),截斷的備份會被擋下來,不會蓋掉正本。
  · --restore 是**原子**的:先把備份寫進同資料夾一個名字帶亂數的暫存檔,
    fsync、權限比照正本、讀回來跟備份比長度與 sha256 都過了,才用 os.replace
    換上正本。中途出任何事(磁碟滿、外接碟被拔掉、按 Ctrl-C)都只丟掉暫存檔,
    **正本原封不動**。以前這裡是一行 shutil.copy2(備份, 正本) ——
    copy2 會先把正本截成 0 bytes 再一路寫,前面那五道把關全部在驗
    「備份好不好」,沒有一道擋得住「複製到一半斷掉」。
    換上去之後再跟備份**逐位元組比一次**(先比長度再比內容),
    比過了才刪備份;沒過就把備份留著並回非 0 的 exit code。
  · --restore 兩個語系檔各走各的:其中一份備份壞掉不會把另一份一起帶走,
    好的那份照樣還原,最後才用非 0 的 exit code 收尾並說清楚哪個沒還原。
  · 讀檔時位移只要指到檔案外面、或字串走不到結尾標記,就當成半截檔停下來,
    不會把它讀成一串空字串再寫回去。
  · 重寫語系檔本身也是原子的:先寫同資料夾的亂數暫存檔,再 os.replace 換上。
    正本永遠不會停在半截狀態。
  · 寫完立刻重讀複驗;**對不上就自動拿備份還原**(備份留著不刪),
    並且回非 0 的 exit code。以前只印一個 ❌ 就照樣回 0 ——
    看輸出的人以為成功了,壞掉的檔卻留在遊戲資料夾裡。
  · 中途按 Ctrl-C:程式記著 os.replace 到底做過幾次,所以它會明確告訴你
    「遊戲檔有沒有被動到」,而不是含糊地說沒事。exit code 一律 130。
    以前是安靜地回 0。
    ⚠️ 2026-09-06 補上這一條的另一半。光是「記著」還不夠:換名做完之後,
    還要再跑一行才算登記過,Ctrl-C 剛好落在那兩行**中間**的話,收尾讀到的
    紀錄是空的 —— 它會說「什麼都沒有動到」,而磁碟上那個檔已經換過了。
    現在那兩行被包成**不可中斷的一段**:這段期間收到的 Ctrl-C 先記著,
    等登記做完才照常丟出來(exit code 還是 130,按了不會沒用,只是晚兩行)。
    另外加一個「正在換 X」的中間態當保險:萬一連那道也失效(例如不是在
    主執行緒,裝不上訊號處理常式),收尾會照實說「中斷時正在替換 X,
    請用 --restore 還原或跟備份比對一次」,**不會**說「沒動到」。
    在複本上實測過:把 Ctrl-C 精準塞進那個窗口,修好前印「一個位元組都
    沒有動到」而檔案的 SHA-256 已經變了;修好後印「已經被改過」並附還原指令。
  · 兩個語系檔是**依序**處理的,所以第二個檔中途出事(磁碟滿、外接碟被拔掉、
    按了 Ctrl-C)的時候第一個已經改好了。這時候會先逐檔印「已改 / 沒改」
    再印還原指令,判斷方式是**當場拿每個檔跟它自己的 .locbak 比一次**,
    不是靠記帳(記帳會漏:複驗沒過那條路會先改檔、再自動還原回去)。
  · `--selftest` 不需要遊戲資料夾:它自己造一份最小的語系檔,把上面每一道
    把關**正反各測一次**(反向的那些是「故意做一件必須失敗的事」)。
    ⚠️ 它在 `python3 -O` 底下會**拒跑**並回 exit code 2:-O 會把 assert
    整句拿掉,測試工具寧可拒跑,也不要印一行沒有根據的「全部通過」。

做不到的事
  · **不會翻譯,也不會補字。** 它只拿掉多出來的格式符,中文字一個都不動。
  · 只看「數量」不看「型別」:中文有 4 個、英文有 2 個,就把中文砍到剩前 2 個。
    至於留下來那 2 個是不是 %s 對 %s、%d 對 %d,這支不管,本站也沒有驗過。
  · 反方向完全不碰:中文的格式符比英文**少**的那 247 條原樣留著。
    少印東西不會當,而每動一條就多一分風險。
  · 不主動處理 %1 %2 %6 這種 EA 自己的替換符。但 CFMT 的旗標裡含一個半形空白,
    「%數字 + 空白 + 英文字母」會被連成一段當成格式符(見 CFMT 那一段的說明)。
  · 只改 data/ 底下那兩個 .LOC。字型檔、執行檔、球場檔一個都不動。
  · ⚠️ 本站**沒有**實機證明「這 168 條就是主因」(見上一段)。

MIT License · Copyright (c) 2026 toni · 無外部相依,Python 3.7 以上
"""

import argparse
import hashlib
import os
import re
import shutil
import signal
import struct
import sys
import tempfile

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

# 每做完一次 os.replace 就把目的檔記在這裡。只有這一份紀錄能回答
# 「被 Ctrl-C 打斷的時候,使用者的遊戲檔到底有沒有被動到」——
# 沒有它就只能含糊地說「應該沒事」,而那句話有一半的機率是假的。
_WRITTEN = []

# 「正在換 X」這個中間態(2026-09-06 加)。
#
# ⚠️ 為什麼一份 _WRITTEN 不夠:os.replace 做完之後,還要再跑一行
#    _WRITTEN.append(dst) 才算「登記過」。Ctrl-C 剛好落在這兩行中間的話,
#    收尾的 _interrupted() 讀到的 _WRITTEN 是空的 —— 它會照舊狀態說
#    「什麼都沒有動到」,而磁碟上那個檔其實已經換過了。**那句話是假的。**
#
# 所以現在有三態:
#    · 不在 _REPLACING 也不在 _WRITTEN → 還沒動
#    · 在 _REPLACING 而不在 _WRITTEN   → 正在換,不知道換完了沒有
#    · 在 _WRITTEN                     → 已換
# 換名之前先進 _REPLACING,換完並登記進 _WRITTEN 之後才退出來。
_REPLACING = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這一段期間 Ctrl-C 先記著,離開再照常丟出。

    這樣 KeyboardInterrupt 的收尾看到的登記,一定跟磁碟上的狀態一致 ——
    要嘛「還沒換、也沒登記」,要嘛「換過了、也登記了」,不會卡在中間。

    ⚠️ 這**不是**「按了沒用」:訊號只是被延後到這一小段(兩行)結束,
       離開這個區塊之後照樣丟 KeyboardInterrupt,exit code 一樣是 130。
    ⚠️ signal.signal 只能在主執行緒裝。裝不上去(ValueError / OSError)就
       退回原本的行為 —— 不會比以前更糟,而且上面那個三態的登記仍然擋著。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):   # 非主執行緒等情況:退回原本行為,不會更糟
            self._old = None
        return self

    def _remember(self, signum, frame):
        self._pending = True

    def __exit__(self, exc_type, exc, tb):
        if self._old is not None:
            signal.signal(signal.SIGINT, self._old)
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _reject_symlink(path, what):
    """正本或備份是符號連結就停下來,一個位元組都不寫。

    ⚠️ **不可以用 os.path.exists() 判斷。** 指向不存在目標的符號連結
       (dangling symlink)在 exists() 眼中是 False,而 open(..., 'wb')
       與 shutil.copy2() 照樣會沿著它去建立、覆寫連結指到的那個檔 ——
       那個檔可能在遊戲資料夾外面。要看連結**本身**就得用
       os.path.islink / os.lstat / os.path.lexists。
       (os.path.islink 在 Windows 上也認得 reparse point。)

    ⚠️ **只看這個檔本身,不往上檢查每一層父資料夾。** 稽核建議連父資料夾
       一起擋,本檔沒有照做,理由是那會擋掉合法的用法:玩家的遊戲資料夾
       路徑本來就可能經過符號連結(macOS 的 /Volumes、Linux 的家目錄
       搬過家、Windows 的 junction 都很常見),而那條路徑是玩家自己給的。
       這裡防的是「別人事先在遊戲資料夾裡擺一個連結」,不是玩家自己的路徑。
    """
    if os.path.islink(os.fspath(path)):
        raise SystemExit(
            '%s 是一個符號連結(symlink),不是真正的檔案:\n'
            '  %s\n'
            '  沿著它寫下去會改到資料夾外面的檔案,所以停在這裡,'
            '一個位元組都沒有動。\n'
            '  請把它移走或換成真正的檔案,再跑一次。' % (what, os.fspath(path)))


def _new_tmp(dst, tag):
    """在 dst 所在的資料夾開一個**名字帶亂數**的暫存檔,回傳 (fd, 路徑)。

    · 同一個資料夾 → 等一下的 os.replace 一定在同一個檔案系統上,換名才是原子的
    · 名字不可預測 → 沒有人能事先在 `<目的檔>.part` 擺一個符號連結,
      讓我們沿著它去覆寫資料夾外面的檔。mkstemp 內部是 O_CREAT|O_EXCL,
      那個名字已經存在(連結也算)就直接換下一個亂數,不會沿用。
    """
    dst = os.fspath(dst)
    d = os.path.dirname(os.path.abspath(dst)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(dst), tag))


def _atomic_replace(src, dst, tag):
    """把 src 的內容原子地換上 dst:要嘛還是原本那份,要嘛已經是完整的新內容。

    ⚠️ **為什麼不能 shutil.copy2(src, dst)**:copy2 是「先把 dst 截成 0 bytes,
       再一路寫過去」。中途按 Ctrl-C、磁碟滿、外接碟被拔掉,dst 就停在 0 或
       半截 —— 而 dst 是使用者的遊戲檔。2026-09-05 上線前資安稽核點名的
       就是這一條路:還原前面那五道把關全部在驗「備份好不好」,
       沒有一道擋得住「複製到一半斷掉」。

    順序:寫進同資料夾的亂數暫存檔 → flush → os.fsync(真的落到碟上)
          → 權限比照目的檔 → 讀回來跟來源比長度與 sha256 → os.replace。
    任何一步失敗都只丟掉暫存檔,dst 原封不動。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串,所以兩邊先 os.fspath。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的,
       是陰性對照(先證明正常流程真的會產生備份)抓到的。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _reject_symlink(dst, '要寫入的檔')
    fd, tmp = _new_tmp(dst, tag)
    try:
        h = hashlib.sha256()
        n = 0
        with os.fdopen(fd, 'wb') as w, open(src, 'rb') as r:
            # 一次一 MB,不要整份讀進記憶體 —— 這個 helper 在本站是共用的,
            # 別的課拿它去搬 5 MB 的執行檔。
            for chunk in iter(lambda: r.read(1 << 20), b''):
                h.update(chunk)
                n += len(chunk)
                w.write(chunk)
            w.flush()
            os.fsync(w.fileno())      # 不 fsync 的話「寫完了」只是作業系統說的
        # 權限比照目的檔:還原之後不該把唯讀變成可寫,或反過來。
        # 目的檔還不存在(第一次備份)時就比照來源。
        shutil.copymode(dst if os.path.isfile(dst) else src, tmp)
        h2 = hashlib.sha256()
        n2 = 0
        with open(tmp, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h2.update(chunk)
                n2 += len(chunk)
        if (n2, h2.digest()) != (n, h.digest()):
            raise SystemExit(
                '寫出去的內容跟來源對不上(%d bytes vs %d bytes),'
                '已經把暫存檔丟掉。\n'
                '  %s 原封不動,沒有被改到。' % (n2, n, dst))
        # 換名 + 登記是不可分割的一段,理由見 _REPLACING 那一段的說明。
        _REPLACING.append(dst)
        try:
            with _NoInterrupt():
                os.replace(tmp, dst)  # os.replace 是原子的
                _WRITTEN.append(dst)
                tmp = None
        except OSError:
            # 換名是原子的:丟 OSError 就是**沒有**換成,狀態是明確的,
            # 所以可以放心把「正在換」撤掉。撤不掉的是下面那一種。
            _REPLACING.remove(dst)
            raise
        else:
            _REPLACING.remove(dst)
        # ⚠️ 其他的 BaseException(例如 signal.signal 裝不上去時漏進來的
        #    KeyboardInterrupt)刻意**不撤**「正在換」的登記:那時候真的不知道
        #    換名做完了沒有,收尾就該照實說「正在替換」,不可以說「沒動到」。
    finally:
        # 這裡不寫 except BaseException:finally 連 Ctrl-C(KeyboardInterrupt)
        # 與 SystemExit 都會走到,不會在使用者的資料夾裡留下暫存檔垃圾。
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass
    return n


def _atomic_write_bytes(dst, data, tag):
    """跟 _atomic_replace 同一套規矩,只是來源是記憶體裡的位元組。

    重寫語系檔走的是這一條。以前是 open(path, 'wb') 直接寫正本 ——
    那一行的第一件事就是把使用者的遊戲檔截成 0 bytes。
    """
    dst = os.fspath(dst)
    _reject_symlink(dst, '要寫入的檔')
    fd, tmp = _new_tmp(dst, tag)
    try:
        with os.fdopen(fd, 'wb') as w:
            w.write(data)
            w.flush()
            os.fsync(w.fileno())
        if os.path.isfile(dst):
            shutil.copymode(dst, tmp)
        with open(tmp, 'rb') as f:
            back = f.read()
        if back != data:
            raise SystemExit(
                '寫出去的內容跟打算寫的不一樣,已經把暫存檔丟掉。\n'
                '  %s 原封不動,沒有被改到。' % dst)
        # 換名 + 登記包成不可中斷的一段,理由同 _atomic_replace。
        _REPLACING.append(dst)
        try:
            with _NoInterrupt():
                os.replace(tmp, dst)
                _WRITTEN.append(dst)
                tmp = None
        except OSError:
            _REPLACING.remove(dst)
            raise
        else:
            _REPLACING.remove(dst)
    finally:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass
    return len(data)


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。"""
    return _atomic_replace(src, dst, 'part')


def _restore_from_backup(bak, dst):
    """還原之前先擋掉明顯壞掉的備份。

    ⚠️ 這裡**不能**比對「備份與目標大小相同」—— 本站多數腳本是把資料接到
    檔尾來改檔(專案鐵律:封裝檔不可重新打包),改完之後正本本來就比備份大,
    那樣比會擋掉每一次合法的還原。

    ── 2026-08-30 補上三道(上線前資安稽核抓到的真漏洞)────────────────
    原本只有「不是 0 bytes」+「BIGF 檔頭宣告長度」兩道。**BIGF 以外全破。**
    實測拿「前 1/8 的半截備份」去還原,六支腳本把正本吃掉而且都印成功:
        mvp_fix_loc / mvp_menu_text   .LOC        416,753 →  52,094
        mvp_edit_speed / mvp_ratings
        / mvp_player                  attrib.dat  840,643 → 105,080
        mvp_modernize                 mvp2005.exe 5,443,584 → 680,448
                                      (它還印「複驗:內容與備份相同 ✅」)
    最後那個會讓遊戲**完全開不起來**,而站上每一課都寫著「隨時可以 --restore」。

    現在檢查五件事:
      1. 備份不是 0 bytes
      2. BIGF:檔頭第 4-8 個位元組宣告的總長度要等於實際長度
         (兩種位元組序都接受;哪些檔是大端、各有幾個,以 reference/bigf.html 量到的為準,這裡不寫會過期的數字)
      3. LOCH(語系檔):檔頭指到的 LOCL 要在檔內,而且最後一條字串的位移
         也要在檔內 —— 截斷之後那個位移一定會超出去
      4. MZ(執行檔):PE 節區表裡 raw offset + raw size 的最大值不得超過檔案長度
      5. **通用地板**:非 BIGF 的備份不得小於「要被蓋掉的那個檔」的一半。
         非 BIGF 的工具都是原地改(大小幾乎不變),所以這條很安全;
         BIGF 走 append 會越改越大,所以刻意**不套**這條,由第 2 道負責。

    本檔真正會走到的是第 1、3、5 道(語系檔是 LOCH 開頭)。
    BIGF 與 MZ 那兩段留著,是因為這個函式在本站是整段共用的。
    """
    # 本檔開頭已經 import 過 struct,這裡再寫一次不影響行為;
    # 好處是這一整個函式可以原封不動複製到別支腳本,不必記得補 import。
    import struct
    bak, dst = os.fspath(bak), os.fspath(dst)
    # 第 0 道(2026-09-05 加):兩邊都不可以是符號連結。這一道要排在最前面 ——
    # 下面那些檢查都是在讀,擋不住「沿著連結寫到資料夾外面」。
    _reject_symlink(bak, '備份檔')
    _reject_symlink(dst, '要還原的遊戲檔')
    if not os.path.exists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    n = os.path.getsize(bak)
    if n == 0:
        raise SystemExit(
            '備份是 0 bytes(多半是上次備份到一半被中斷),不敢拿它覆蓋 %s。' % dst)
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    def _stop(why):
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 第 2 道:BIGF 封裝檔。檔頭 +0x04 那 4 個位元組是「整個檔應該多長」,
    # 拿它跟實際長度對。大小端都收,因為同一個欄位兩種寫法都出現過。
    # (本檔處理的是 .LOC,走不到這一段。)
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:.LOC 語系檔,也就是本檔真正會走的那一條。
    # .LOC 沒有「總長度」欄位可以對,所以改成順著結構走一遍:
    # 位移 0x10 那 4 bytes(小端序)說文字段 LOCL 在哪 → 那裡要真的是 'LOCL'
    #   → LOCL + 0x0C 是字串條數 → LOCL + 0x10 起是每條 4 bytes 的位移表
    #   → 最後一條的位移不可以指到檔案外面。
    # 檔案被截斷時,最後那一條一定會超出去,所以這一關擋得住半截備份。
    if len(head) >= 4 and head[:4] == b'LOCH':
        try:
            d = open(bak, 'rb').read()
            L = struct.unpack('<I', d[16:20])[0]
            if L + 16 > n or d[L:L + 4] != b'LOCL':
                _stop('語系檔的字串區(LOCL)應該在位移 %d,那裡不是 LOCL。' % L)
            lcnt = struct.unpack('<I', d[L + 12:L + 16])[0]
            if lcnt <= 0 or L + 16 + lcnt * 4 > n:
                _stop('語系檔的位移表被截斷了(宣告 %d 條)。' % lcnt)
            last = struct.unpack('<I', d[L + 16 + (lcnt - 1) * 4:L + 20 + (lcnt - 1) * 4])[0]
            if L + last >= n:
                _stop('語系檔最後一條字串在位移 %d,超出檔案結尾(%d bytes)。'
                      % (L + last, n))
        except SystemExit:
            raise
        except (struct.error, IndexError):
            _stop('讀不出語系檔的結構,它壞了。')

    # 第 4 道:Windows 執行檔。MZ 之後 +0x3C 是 PE 檔頭的位移,
    # PE 檔頭 +0x06 是節區數、+0x14 是選用檔頭長度,節區表接在後面、一個 40 bytes。
    # 每個節區記著內容從檔案哪裡開始、有多長,最遠的那個不可以超出檔尾。
    # (本檔處理的是 .LOC,走不到這一段。)
    if len(head) >= 2 and head[:2] == b'MZ':
        try:
            d = open(bak, 'rb').read()
            pe = struct.unpack('<I', d[0x3C:0x40])[0]
            if pe + 24 > n or d[pe:pe + 4] != b'PE\x00\x00':
                _stop('執行檔的 PE 檔頭不在它該在的地方,檔案不完整。')
            nsec = struct.unpack('<H', d[pe + 6:pe + 8])[0]
            optsz = struct.unpack('<H', d[pe + 20:pe + 22])[0]
            sec = pe + 24 + optsz
            end = 0
            for i in range(nsec):
                o = sec + i * 40
                if o + 40 > n:
                    _stop('執行檔的節區表被截斷了(宣告 %d 個節區)。' % nsec)
                raw_sz, raw_off = struct.unpack('<II', d[o + 16:o + 24])
                end = max(end, raw_off + raw_sz)
            if end > n:
                _stop('執行檔的節區指到 %d bytes,實際只有 %d bytes。' % (end, n))
        except SystemExit:
            raise
        except (struct.error, IndexError):
            _stop('讀不出執行檔的結構,它壞了。')

    # 通用地板 —— 非 BIGF 走到這裡
    # 語系檔是原地改(拿掉幾個格式符,檔案只會小一點點),
    # 所以「備份不到正本的一半」一定是備份出了事,不是正常的改動。
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _check_reusable_backup(bak):
    """沿用一份已經存在的 .locbak 之前,先驗它完不完整。備份不存在就什麼都不做。

    ⚠️ 為什麼要有這一關:--fix --apply 以前只看「.locbak 存不存在」就決定沿用,
       完全不驗它。而把關全部集中在 --restore 那一邊 —— 也就是**事後**。
       2026-09-05 在暫存複本上實測:先放兩份 head -c 5000 截出來的假 .locbak,
       再跑 --fix --apply,腳本印「修了 25 條 / 143 條」「備份 → IGENG.LOC.locbak」
       「複驗:… ✅」、exit code 0,兩個正本都被改寫;等到要救的時候 --restore
       才說「這份備份是壞的」exit 1 —— 那時候正本已經回不去了。
       壞掉的備份等於沒有備份,所以要在**動筆之前**就擋。

    判準跟 _restore_from_backup 的第 1、3 道同一條:不是 0 bytes,而且
    LOCH → LOCI → LOCL → 位移表 → 每一條字串都走得完(parse 現在自己會擋半截檔)。
    """
    _reject_symlink(bak, '備份檔')
    if not os.path.exists(bak):
        return
    why = None
    if os.path.getsize(bak) == 0:
        why = '它是 0 bytes(多半是上次備份到一半被中斷)。'
    else:
        try:
            parse(bak)
        except DataError as e:
            why = '%s' % e
    if why:
        raise DataError(
            '%s 已經存在,但它不是一份完整的語系檔。\n'
            '     %s\n'
            '     沿用壞掉的備份等於沒有備份 —— 改完之後 --restore 會拒絕它,\n'
            '     那時候正本就回不去了。所以停在這裡,一個位元組都沒有改。\n'
            '     請把它移走或改名(或改用你自己另外留的那一份),再跑一次。'
            % (os.path.basename(bak), why))


def _verify_restored(bak, dst):
    """還原之後、刪掉備份之前,拿還原出來的檔跟備份逐位元組比一次。

    ⚠️ 不可以用 zip(a, b) 逐位元組比 —— zip 在短的那一邊就停,兩個長度不同、
       前面又一樣的檔會被判成「相同」。所以這裡先比長度,再整份比。
    ⚠️ 比對沒過就**不刪備份**:那是使用者唯一的副本。
    """
    nb, nd = os.path.getsize(bak), os.path.getsize(dst)
    if nb != nd:
        raise SystemExit(
            '還原之後大小對不上(備份 %d bytes、還原出來的 %d bytes)。\n'
            '備份保留著沒有刪,請自己把 %s 複製成 %s。'
            % (nb, nd, os.path.basename(bak), os.path.basename(dst)))
    with open(bak, 'rb') as f1, open(dst, 'rb') as f2:
        if f1.read() != f2.read():
            raise SystemExit(
                '還原之後內容跟備份不一樣(長度相同但位元組不同)。\n'
                '備份保留著沒有刪,請自己把 %s 複製成 %s。'
                % (os.path.basename(bak), os.path.basename(dst)))


def _do_copy(bak, dst):
    """上面每一道把關都過了,真正的覆寫只有這裡。

    切成獨立函式是為了「只留一個出口」:每一條檢查路徑最後都得經過它,
    所以以後要加新的把關,只要確定加在 _do_copy 之前,就不可能漏掉哪一條。

    ⚠️ 2026-09-05 改成原子的。以前這裡是一行 shutil.copy2(bak, dst),
       而 copy2 的第一件事是**把 dst 截成 0 bytes**。前面那五道把關驗的
       全部是「備份好不好」,一道都擋不住「複製到一半斷掉」——
       斷在那裡,使用者的遊戲檔就停在 0 或半截。
    """
    return _atomic_replace(bak, dst, 'restore')




# 備份檔名 = 原檔名直接接上這個字尾(IGENG.LOC → IGENG.LOC.locbak)。
# 兩個語系檔各自有各自的備份,互不影響,所以可以只還原其中一個。
BACKUP = '.locbak'
# 真正會從堆疊取參數的格式符。%1 %2 %NX 這種是 EA 自己的替換,由遊戲的字串引擎
# 處理,不會直接餵給 printf,所以不碰。
# 拆開看這條式子:% 之後可以先有旗標與寬度精度(- + 空格 # 數字 小數點),
# 最後一個字元一定要是 printf 認得的轉換字元(d i u f F e E g G x X o s c p S C)。
# ⚠️ 旗標那一類裡**含一個半形空白**(還有小數點),所以「%數字 + 空白 +
# 一個剛好是轉換字元的英文字母」會被連成一段吃掉:'%1 in %2' 命中 '%1 i'。
# (這裡以前寫「EA 的 %2 %6 不會中,整支腳本碰不到它們」,那句話是錯的。)
# 2026-09-03 分別在兩份檔上量:
#   · 剛安裝好的英文原版 data/:FEENG.LOC 354 個命中裡 90 個含空白,
#     IGENG.LOC 29 個裡 9 個。例如 'Checking %3 for %8 Saves.' 中 '%3 f'
#     與 '%8 S',以及 '... on %3.  Continue?' 中 '%3.  C'。analyse 的 ne 是
#     拿英文那一條算的,所以英文那邊會被多算,方向是**少報**,不是多改。
#   · 手邊那份中文語系檔(FEENG 6,436 條 / IGENG 1,663 條):含空白的命中 0 個。
#     FEENG 只有 7 個 %數字 開頭的命中,全是合法的 %02d / %4d;IGENG 一個都沒有。
#     原本說的「FEENG 有 5 條含 %%、這條式子一個都沒命中」仍然成立。
#   · 把旗標裡的空白拿掉重跑同一對檔:要修的 168 條(FEENG 143 / IGENG 25)
#     一條不差,keep 一樣,strip_fmt 輸出逐字相同。所以這是說明寫錯,
#     不是這對檔上的行為錯了。差別只出現在反方向那 247 條(見檔頭):
#     拿掉空白後剩 168 條,其中 79 條是英文被多算才變成「少」的。
CFMT = re.compile(r'%[-+ #0-9.]*[diufFeEgGxXoscpSC]')


class DataError(Exception):
    """「你的檔案或參數有問題」這一類、使用者看得懂的停止原因。

    main() 只接這一種,把它印成一行中文、回 exit code 2 就結束。

    ⚠️ 但「不丟 traceback 就停下來」的路不只這一條。--restore 走的
    _restore_from_backup() 擋下壞掉的備份時丟的是 SystemExit,那段中文由
    Python 自己印到 stderr、回 exit code 1;參數打錯時 argparse 丟的也是
    SystemExit(印用法、回 exit code 2)。兩種都不會有 traceback,所以這裡
    不是「DataError 一行中文 / 其他全部 traceback」的二分法。

    真正會印出完整 traceback 的,是 DataError 與 SystemExit 以外的例外:
    那是程式的錯,不該包裝成一句好看的中文。
    """
    pass


def parse(path):
    """讀 .LOC 語系檔。回傳 (整份位元組, 一包解出來的欄位)。

    .LOC 是三段接在一起,**每個數字欄位都是小端序**:

        LOCH  檔頭      +0x04  這個檔頭多長。照它往後跳就是下一段的開頭
        LOCI  索引段    +0x04  文字段大概在哪(idxoff)
                        +0x08  總共有幾條字串(count)
                        +0x10  起,每 4 bytes 一筆。前 2 bytes 是**字串編號**
                               (遊戲程式拿這個號碼跟語系檔要字串),
                               後 2 bytes 本函式沒有用到
        LOCL  文字段    +0x10  起,每 4 bytes 一筆位移。這個位移是**相對於
                               'LOCL' 那四個字的開頭**,不是相對於檔案開頭
                               位移指過去就是字串本體:UTF-16LE,兩個 0x00 結尾,
                               長度沒有另外記在別的地方

    ⚠️ 文字段是用 b.find(b'LOCL', idxoff) 找的,不是照 idxoff 直接跳。
       也就是說 idxoff 在這裡只被當成「從這裡開始往後找」的起點,
       中間就算多幾個位元組也還是找得到。

    ⚠️ 解碼用 errors='replace'。讀進來只是為了數格式符,一條壞字元不該讓
       整支停掉。但 rebuild 是把**每一條**都重新編碼寫回去的,所以萬一原檔
       真有解不出來的位元組,它會被換成 U+FFFD 寫回去,而 cmd_fix 的複驗
       比的是「解出來的字串」,比不出這種差別。
       2026-08-30 拿手邊的中文語系檔實測:IGENG.LOC 1,663 條、FEENG.LOC
       6,436 條,U+FFFD 是 0 個,而且每一條重新編碼回去都跟原本的位元組
       逐位元組相同(8,099 條零例外)。手上那兩個檔沒有這個問題,
       但這不代表所有中文化版本都沒有。
    """
    with open(path, 'rb') as f:
        b = f.read()
    if b[:4] != b'LOCH':
        raise DataError('%s 開頭不是 LOCH' % os.path.basename(path))
    # 檔頭長度自己記在 +0x04,照它跳到下一段,不要寫死 16 或 32。
    hdrlen = struct.unpack('<I', b[4:8])[0]
    i = hdrlen
    if b[i:i + 4] != b'LOCI':
        raise DataError('找不到 LOCI 索引段')
    idxoff, count = struct.unpack('<II', b[i + 4:i + 12])
    # 索引表要真的整份在檔案裡。少了這一關,截斷得比較狠的檔會在下面那個
    # list comprehension 撞出 struct.error 的完整 traceback —— 那看起來像
    # 程式的錯,實際上是使用者的檔壞了。2026-09-05 實測:把 42,983 bytes 的
    # IGENG.LOC 截成 8,000 bytes,原本會丟 struct.error traceback。
    if count <= 0 or i + 16 + count * 4 > len(b):
        raise DataError('%s 的索引表宣告 %d 條,檔案只有 %d bytes —— 這個檔是半截的。'
                        % (os.path.basename(path), count, len(b)))
    # 每筆索引 4 bytes,只取前 2 bytes 的字串編號。後 2 bytes 本工具用不到,
    # 而**整個索引段等一下會被原樣搬回去**,所以不需要知道它是什麼。
    ids = [struct.unpack('<HH', b[i + 16 + k * 4:i + 20 + k * 4])[0] for k in range(count)]
    L = b.find(b'LOCL', idxoff)
    if L < 0:
        raise DataError('找不到 LOCL 文字段')
    # 位移表也一樣要整份在檔案裡,理由同上。
    if L + 16 + count * 4 > len(b):
        raise DataError('%s 的位移表宣告 %d 條,檔案只有 %d bytes —— 這個檔是半截的。'
                        % (os.path.basename(path), count, len(b)))
    # 位移表:第 k 筆放在 LOCL + 16 + k*4,小端序 4 bytes。
    offs = [struct.unpack('<I', b[L + 16 + k * 4:L + 20 + k * 4])[0] for k in range(count)]
    strs = []
    for o in offs:
        # 位移是相對於 LOCL 的,所以真正的檔案位置要加上 L。
        s = L + o
        # 位移指到檔案外面 = 這個檔是半截的。不擋的話 b[s:e] 是空切片,
        # 那一條就安靜地變成空字串 —— 而 cmd_fix 的複驗比的是「打算寫進去的
        # 內容」,拿同一份被讀壞的資料自比一定相同,比不出這種空。
        # 2026-09-05 實測:把 IGENG.LOC 截成 20,000 bytes,1,663 條裡有 1,197 條
        # 被讀成空字串,--fix --apply 照樣印「1663 條字串全部讀得回來 ✅」exit 0。
        if s >= len(b):
            raise DataError('%s 的第 %d 條字串位移指到檔案外面(%d ≥ %d),這個檔是半截的。'
                            % (os.path.basename(path), len(strs) + 1, s, len(b)))
        e = s
        # UTF-16 一個字元 2 bytes,所以一次走 2 bytes,不是 1 bytes。
        # 結尾是「連續兩個 0x00」;只看一個 0x00 會把中文字砍成半個。
        while e + 1 < len(b) and b[e:e + 2] != b'\x00\x00':
            e += 2
        # 走到檔尾都沒遇到那兩個 0x00 = 最後一條被切掉了。
        # (本站手邊四份語系檔 —— 中文 IGENG/FEENG 與剛安裝好的英文原版兩份 ——
        #  合計 16,035 條,沒有一條走不到結尾,所以這一關不會誤傷正常的檔。)
        if b[e:e + 2] != b'\x00\x00':
            raise DataError('%s 的第 %d 條字串沒有結尾標記,這個檔是半截的。'
                            % (os.path.basename(path), len(strs) + 1))
        strs.append(b[s:e].decode('utf-16-le', errors='replace'))
    return b, dict(hdrlen=hdrlen, idxoff=idxoff, count=count, LOCL=L,
                   ids=ids, offs=offs, strs=strs)


def strip_fmt(s, keep):
    """把 CFMT 格式符拿掉,只留前 keep 個。中文字一律不動。

    做法是照 CFMT 從左掃到右:格式符**之間**的文字原封不動接回去,
    第 keep + 1 個之後的格式符就不接。所以:
      · 留下來的是**最前面**那幾個,不是挑型別最像英文版的那幾個
      · 中文字一個都碰不到(中文不在 CFMT 任何一個字元類裡);但被拿掉的
        不一定只有 % 開頭那幾個字元:旗標裡含半形空白與小數點,'%1 i' 這種
        「%數字 + 空白 + 英文字母」會被整段當成格式符(見 CFMT 那一段)
      · keep = 0 就是整條的格式符全部拿掉
      · 中文原本比英文少的情況不會走到這裡(analyse 只挑「多」的那個方向)
    """
    out = []
    n = 0
    pos = 0
    for m in CFMT.finditer(s):
        # 先把上一個格式符結束到這個格式符開始之間的原文接回去。
        out.append(s[pos:m.start()])
        if n < keep:
            out.append(m.group(0))
        n += 1
        pos = m.end()
    # 最後一個格式符之後還有一段原文,不要漏掉。
    out.append(s[pos:])
    return ''.join(out)


def analyse(root):
    """回傳 [(檔名, 路徑, [(索引, 編號, 英文, 中文, 英要, 中要)])]

    把中文那兩個 .LOC 跟英文版逐條對帳,挑出「中文要的參數比英文多」的條目。
    整支腳本只有這裡在做判斷,cmd_show 與 cmd_fix 都只是拿它的結果去印或去改。

    ⚠️ 對帳是照**字串編號**配對,不是照順序。兩邊的條數與排列可以不同,
       照順序比會整排錯位,而錯位之後每一條看起來都「對不上」。
       編號在英文版裡找不到的直接跳過:沒有基準就不判,不猜。

    ⚠️ 只挑 nc > ne 這一個方向。反過來(中文比英文少)不會當,只會少印東西,
       所以完全不碰,理由見檔頭那一段。

    ⚠️ 只比數量,不比型別。中文 4 個、英文 2 個 → 砍到剩前 2 個;
       至於剩下那 2 個是不是 %s 對 %s,這裡沒有驗,本站也沒有驗過。
    """
    data = os.path.join(root, 'data')
    # 先確認給的真的是「遊戲安裝資料夾」。少了這一關,路徑打錯或把 data 本身
    # 當成遊戲資料夾,兩種最常見的手誤都會掉到下面那句「找不到英文語系資料夾」,
    # 把人引去翻一個根本不是問題的東西。
    if not os.path.isdir(data):
        raise DataError('%s 底下沒有 data 資料夾。\n'
                        '     要給的是遊戲安裝資料夾(它的下一層才是 data)。' % root)
    # 英文語系資料夾有兩種常見名字(2023 版與更早的版本),兩個都試。
    en_dir = None
    for cand in ('2023英文語系', '英文語系'):
        p = os.path.join(data, cand)
        if os.path.isdir(p):
            en_dir = p
            break
    # 沒有基準就整支停掉。「猜哪些格式符是多的」然後去改玩家的遊戲檔,
    # 是這支腳本唯一不可以做的事。
    if not en_dir:
        raise DataError('找不到英文語系資料夾（試過 data/2023英文語系、data/英文語系）\n'
                        '     沒有它就沒有基準可比,無法判斷哪些格式符是多的。')
    out = []
    for name in ('IGENG.LOC', 'FEENG.LOC'):
        live = os.path.join(data, name)
        base = os.path.join(en_dir, name)
        # 兩邊少了任何一邊就跳過這個檔(例如只蓋了其中一半的中文化)。
        # 那不是錯誤,只是這個檔沒得比。
        if not (os.path.isfile(live) and os.path.isfile(base)):
            continue
        _, C = parse(live)
        _, E = parse(base)
        # 把英文那份攤成 {字串編號: 字串},配對才不會受兩邊排列順序影響。
        emap = dict(zip(E['ids'], E['strs']))
        bad = []
        for k, (sid, s) in enumerate(zip(C['ids'], C['strs'])):
            if sid not in emap:
                continue
            # ne = 英文那一條要幾個參數(遊戲程式實際會傳幾個,以英文版為準)
            # nc = 中文那一條開口要幾個
            ne = len(CFMT.findall(emap[sid]))
            nc = len(CFMT.findall(s))
            # 中文開口比英文多 = 會去堆疊上撈不存在的參數 = 當機的那一種。
            # k(在字串表裡的第幾條)要一起記,因為 cmd_fix 是照 k 回去改的。
            if nc > ne:
                bad.append((k, sid, emap[sid], s, ne, nc))
        out.append((name, live, bad))
    return out


def rebuild(path, C, newstrs):
    """照原結構寫回。字串段重排,索引段的偏移跟著更新。

    只有「位移表之後的字串本體」會被重寫。前面那一整塊(LOCH 檔頭、
    LOCI 索引段、LOCL 的表頭與位移表)是整段原樣搬過去的,所以字串編號、
    條數、每一條的順序都不會變,遊戲照編號要字串一定還要得到。

    位移表本身長度不變(條數沒變),所以是**就地改裡面的數字**,不是重寫它。

    ⚠️ 位移是「相對於 'LOCL' 那四個字的開頭」算的,不是相對於檔案開頭。
       所以下面那一行寫的是 len(head) - L + len(body),先扣掉 L。
    ⚠️ 字串長度沒有記在任何地方,結尾就是那兩個 0x00。所以字串變短之後
       只要位移表跟著改,整個檔就會自然變小,不需要補空白對齊。
    ⚠️ newstrs 是**整份**字串表,不是只有要改的那幾條;沒改到的那些會照原樣
       重新編碼一次寫回去(見 parse 說明裡關於 U+FFFD 的那一段)。
    """
    with open(path, 'rb') as f:
        b = bytearray(f.read())
    L = C['LOCL']
    # head = 從檔案開頭一路到位移表的最後一筆為止,原樣不動。
    # 位移表就在這一塊的尾巴,等一下用 pack_into 就地改。
    head = bytes(b[:L + 16 + C['count'] * 4])
    body = bytearray()
    offs = []
    for s in newstrs:
        # 接之前先算出「這一條會落在哪」,而且要換算成相對於 LOCL 的位移。
        offs.append(len(head) - L + len(body))
        body += s.encode('utf-16-le') + b'\x00\x00'
    out = bytearray(head) + body
    # 位移表就地更新:第 k 筆寫在 LOCL + 16 + k*4,小端序 4 bytes。
    for k, o in enumerate(offs):
        struct.pack_into('<I', out, L + 16 + k * 4, o)
    # ⚠️ 以前這裡是 open(path, 'wb') 直接寫正本 —— 那一行的第一件事就是把
    #    使用者的遊戲檔截成 0 bytes,寫到一半斷掉就回不去了。改成先寫
    #    同資料夾的亂數暫存檔、fsync、讀回來比對,再 os.replace 換上。
    return _atomic_write_bytes(path, bytes(out), 'new')


def _selfcmd():
    """印「下一步該打什麼」時用的腳本名稱。

    ⚠️ 這裡以前是 os.path.basename(__file__),不管人從哪裡呼叫都印
       mvp_fix_loc.py。腳本不在目前資料夾時(還放在「下載」裡、或用完整路徑
       呼叫),把印出來那一行複製貼上會得到 can't open file —— 而這一課的速解
       正好把 can't open file 列為要避開的陷阱。
       sys.argv[0] 就是他剛才實際打的那個字,照抄一定跑得動。
    """
    p = sys.argv[0]
    # argv[0] 不一定是一個真的檔案:空字串、或用 python3 - 從標準輸入餵進來時
    # 它會是 '-'。印那個沒有意義,退回檔名。
    if not p or not os.path.isfile(p):
        p = os.path.basename(__file__)
    # 路徑含空白時要加引號,不然複製過去會被 shell 拆成兩個參數。
    return '"%s"' % p if ' ' in p else p


def cmd_show(root):
    """不加旗標時跑的就是這個:只讀、只印,一個位元組都不寫。

    每個檔先印有幾條對不上,再列前 8 條:上面一行是英文版長什麼樣、要幾個參數,
    下面一行是中文版長什麼樣、要幾個參數。兩行對齊擺,差別一眼就看得出來。

    只截前 34 個字是為了讓兩行對得齊,**不是完整內容**。
    要看完整的,把那個編號拿去 reference/loc-strings 那一頁查。
    """
    res = analyse(root)
    total = 0
    for name, live, bad in res:
        print('  %s  %s 條會讓遊戲拿到不存在的參數' % (name, len(bad)))
        total += len(bad)
        # 只列前 8 條。全部列出來會洗版(本站量到合計 168 條),
        # 而看 8 條就足以判斷「這確實是同一種毛病」。
        for k, sid, e, c, ne, nc in bad[:8]:
            print('     編號 %-6d 英「%s」要 %d 個' % (sid, e[:34], ne))
            print('     %-11s 中「%s」要 %d 個' % ('', c[:34], nc))
        if len(bad) > 8:
            print('     …還有 %d 條' % (len(bad) - 8))
        print()
    print('  合計 %d 條。' % total)
    if total:
        print('  要修的話（中文字一個都不會動,只拿掉多出來的格式符）:')
        print('    python3 %s "%s" --fix' % (_selfcmd(), root))


def _report_partial(root):
    """中途出事的時候,逐檔講清楚「已改 / 沒改」,並且印還原指令。

    ⚠️ 這裡**不靠記帳,直接量檔案**:拿每個 .LOC 跟它自己的 .locbak 比一次。
       記帳會說謊 —— 複驗沒過那條路會先改檔、再自動還原回去,_WRITTEN 裡
       兩次都在,可是磁碟上其實已經回到原點了。量的話就不會弄錯。
       (沒有備份可比的檔就不列:那代表這一輪根本沒輪到它。)

    什麼時候會走到這裡:兩個語系檔是**依序**處理的,第二個檔中途出事
    (磁碟滿、外接碟被拔掉、按了 Ctrl-C)的時候,第一個檔已經改好了。
    原本的訊息只講得到出事的那一個,看的人不會知道另一個已經被動過。
    """
    # ⚠️ 光靠量也會說謊,所以要兩個條件一起看。
    #    只量的話:使用者資料夾裡本來就擺著一份**不相干或半截的** .locbak
    #    (那正是 _check_reusable_backup 擋下來的情況),量出來一定「不一樣」,
    #    這裡就會誣賴自己改過檔 —— 而那一條路是一個位元組都沒有寫的。
    #    所以先問記帳「這一輪到底有沒有換過任何一個遊戲檔」,有才往下量。
    touched = [p for p in list(_WRITTEN) + list(_REPLACING)
               if not p.endswith(BACKUP)]
    if not touched:
        return
    data = os.path.join(root, 'data')
    changed, same = [], []
    for name in ('IGENG.LOC', 'FEENG.LOC'):
        live = os.path.join(data, name)
        bak = live + BACKUP
        if not os.path.isfile(live):
            continue
        if not os.path.isfile(bak):
            # 沒有備份 = 這一輪一定沒輪到它。備份一律在 rebuild **之前**才做,
            # 所以「連備份都還沒有」等於「一個位元組都還沒寫過」。
            same.append(name)
            continue
        try:
            with open(live, 'rb') as f1, open(bak, 'rb') as f2:
                # 先比長度再比內容:zip 逐位元組比會在短的那一邊就停。
                if os.path.getsize(live) != os.path.getsize(bak) or f1.read() != f2.read():
                    changed.append(name)
                else:
                    same.append(name)
        except OSError:
            # 連讀都讀不到就不要猜。少講一行,好過講錯一行。
            continue
    if not changed:
        return
    print()
    print('  ⚠️ 中途出事了。剛才實地跟備份比對過,到目前為止:')
    for nm in changed:
        print('       已改 %s(跟 %s%s 不一樣了)' % (nm, nm, BACKUP))
    for nm in same:
        print('       沒改 %s' % nm)
    print('  要回到原本的樣子:')
    print('    python3 %s "%s" --restore' % (_selfcmd(), root))


def cmd_fix(root, apply_it):
    """真正的內容在 _cmd_fix_inner,這一層只負責「中途出事要把話講完」。

    ⚠️ 接的是 BaseException 不是 Exception:Ctrl-C(KeyboardInterrupt)與
       SystemExit 都不是 Exception 的子類。只接 Exception 的話,最常見的那一種
       中斷(使用者按 Ctrl-C)反而走不到誠實路徑。
       接完一律 raise 回去,exit code 與原本的訊息一個字都沒有變 ——
       這一層只是在原本的訊息**之前**多印一段逐檔的「已改 / 沒改」。
       (Ctrl-C 另外還會走 main() 的 _interrupted():那一段講的是
        os.replace 做過幾次,跟這裡的逐檔比對互補,不衝突。)
    """
    try:
        return _cmd_fix_inner(root, apply_it)
    except BaseException:
        try:
            _report_partial(root)
        except Exception:
            # 報告自己出事,絕對不可以蓋掉原本那個錯 —— 那才是使用者要看的。
            # 少一段補充說明,好過把真正的原因換成「報告程式壞了」。
            pass
        raise


def _cmd_fix_inner(root, apply_it):
    """預覽或真的修。沒加 --apply 就只印,加了才會備份 → 重寫 → 複驗。

    兩個語系檔各自處理,而且是各自備份、各自複驗,所以其中一個沒東西要修
    也不影響另一個。

    順序不能換:備份一定在寫之前,複驗一定在寫之後。
    備份只做第一次(.locbak 已經存在就沿用),所以重複執行 --fix --apply
    也還是回得到最原始那一份。

    ⚠️ 但「沿用」之前要先驗那份舊備份完不完整,而且是**兩個檔一起先驗完**
       才開始寫第一個檔(見 _check_reusable_backup)。壞掉的備份等於沒有備份,
       驗不過就丟 DataError 整支停下來,一個位元組都不會落地。
    ⚠️ 同一輪先驗的還有「正本與備份是不是符號連結」(_reject_symlink)。
       這一道也要排在動筆之前:沿著連結寫下去會改到遊戲資料夾外面的檔案。
    ⚠️ 複驗沒過**不是印一個 ❌ 就算了**。2026-09-05 之前 ok 只決定印 ✅ 還是 ❌,
       main() 照樣回 0 —— 看輸出的人會以為成功了,而壞掉的檔就留在遊戲資料夾裡。
       現在改成:立刻拿(剛剛才驗過的)備份自動還原,備份留著不刪,
       最後用 SystemExit 收尾,exit code 非 0。
    """
    res = analyse(root)
    # 要真的寫檔的話,先把「已經存在的備份」兩個一起驗過,再開始寫第一個檔。
    # 分成兩段是刻意的:兩個語系檔是依序處理的,邊驗邊寫的話,第二個檔的備份
    # 壞掉時第一個檔已經被改掉了,訊息就只能說一半。先驗完才寫,
    # 「停在這裡,一個位元組都沒有改」這句話才是真的。
    if apply_it:
        for name, live, bad in res:
            if bad:
                # 順序不能換:符號連結那一道要在讀備份之前,因為連結指到的
                # 東西可能根本不是這個資料夾裡的檔。
                _reject_symlink(live, '遊戲檔')
                _reject_symlink(live + BACKUP, '備份檔')
                _check_reusable_backup(live + BACKUP)
    changed_any = False
    preview_any = False
    verify_failed = []
    for name, live, bad in res:
        if not bad:
            print('  %s  沒有要修的' % name)
            continue
        # analyse 只回報「哪幾條有問題」,不回傳整份結構,所以這裡重讀一次,
        # 拿完整的 C(字串表、位移表、LOCL 在哪)給 rebuild 用。
        _, C = parse(live)
        # 先整份複製一份,再只改要改的那幾條。沒問題的那些原樣留著。
        newstrs = list(C['strs'])
        for k, sid, e, c, ne, nc in bad:
            # ne 是英文那一條要幾個參數,砍到跟它一樣多為止。
            # k 是「在字串表裡的第幾條」,由 analyse 一路帶過來。
            newstrs[k] = strip_fmt(c, ne)
        if not apply_it:
            # 預覽:兩個語系檔都要列出來,所以是 continue 不是 return
            print('  %s  會修 %d 條(預覽,沒有動到檔案)' % (name, len(bad)))
            for k, sid, e, c, ne, nc in bad[:3]:
                print('        編號 %-6d 「%s」→「%s」' % (sid, c[:26], newstrs[k][:26]))
            preview_any = True
            continue
        # 備份只做第一次。第二次執行時 .locbak 裡放的仍然是最原始那一份,
        # 而不是上一次改完的結果,所以 --restore 一定回得到原點。
        bak = live + BACKUP
        if not os.path.exists(bak):
            _atomic_copy(live, bak)          # 備份原檔
        size = rebuild(live, C, newstrs)
        changed_any = True
        # 複驗:重讀剛寫出去的檔,三件事都要對得上:
        # 條數一樣、每一條的字串編號一個沒變(遊戲是照編號要字串的)、
        # 每一條內容跟我們打算寫進去的完全相同。
        # 「寫完就當作成功」是這類工具最常見的謊。
        _, C2 = parse(live)
        # 三件事都要對得上,而且**三件都要參與判斷** ——
        # 只拿來印一個符號的檢查,等於沒有檢查。
        why = []
        if C2['count'] != C['count']:
            why.append('條數 %d → %d' % (C['count'], C2['count']))
        if C2['ids'] != C['ids']:
            why.append('字串編號變了')
        if C2['strs'] != newstrs:
            why.append('內容跟打算寫的不一樣')
        ok = not why
        print('  %s  修了 %d 條 → %s bytes' % (name, len(bad), '{:,}'.format(size)))
        print('     備份 → %s' % os.path.basename(bak))
        if ok:
            print('     複驗:%d 條字串全部讀得回來、編號一個沒變 ✅' % C2['count'])
            for k, sid, e, c, ne, nc in bad[:3]:
                print('        編號 %-6d 「%s」→「%s」' % (sid, c[:26], newstrs[k][:26]))
            continue
        # 複驗沒過 = 寫出去的東西不是我們打算寫的。備份是這一輪動筆之前
        # 才驗過的完整檔,所以直接拿它還原,不留一個壞掉的正本給玩家。
        # 備份**不刪**:自動還原也可能失敗,那時候它是唯一的副本。
        print('     複驗:❌ 對不上(%s)' % '、'.join(why))
        print('     正在拿備份自動還原……')
        try:
            _restore_from_backup(bak, live)
            _verify_restored(bak, live)
        except SystemExit as e2:
            print('     ❌ 自動還原也失敗了:')
            for ln in str(e2).splitlines():
                print('        %s' % ln.lstrip())
            print('     備份留著沒有刪:%s' % bak)
        else:
            print('     ✅ 已經還原回原本的樣子(備份留著沒有刪)')
        verify_failed.append(name)
    if verify_failed:
        # 這裡一定要用非 0 的 exit code 結束。以前印完 ❌ 就往下走,
        # main() 照樣回 0 —— 對於用腳本串起來的人來說,那等於沒有失敗。
        raise SystemExit(
            '  %s 的複驗沒過,已經照上面說的處理過了。\n'
            '  請把上面整段貼到回報頁,並且先不要進遊戲。'
            % '、'.join(verify_failed))
    if preview_any:
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要修的話,在剛才那一行最後面加上 --apply')
    if changed_any:
        print()
        print('  進遊戲,用那座會當的球場試一次。沒改善就還原:')
        print('    python3 %s "%s" --restore' % (_selfcmd(), root))


def cmd_restore(root):
    """把兩個 .LOC 的備份蓋回去,還原成功一個就刪掉一個備份。

    只還原「找得到備份」的那些。只修過其中一個檔的話,另一個本來就沒有備份
    可以還原,那不是錯誤;兩個都沒有才印「沒有東西要還原」。

    兩個檔各走各的:IGENG 的備份壞掉不會把 FEENG 一起帶走,FEENG 的備份
    如果是好的照樣會被還原。最後才用 SystemExit 收尾(exit code 1),
    訊息裡會寫哪個沒還原、哪個已經還原好了。

    刪備份是刻意的:留著會讓下一次 --fix 誤以為「已經備份過了」而沿用一份
    已經沒有意義的檔。還原完等於回到出發點,下一次改會重新備份一次。
    ⚠️ 但刪之前一定要先 _verify_restored 逐位元組比過 —— 那是使用者唯一的副本,
       比不過就留著不刪。
    """
    data = os.path.join(root, 'data')
    n = 0
    failed = []
    for name in ('IGENG.LOC', 'FEENG.LOC'):
        live = os.path.join(data, name)
        bak = live + BACKUP
        if os.path.exists(bak):
            # ⚠️ 2026-08-30 上線前資安稽核修:這裡原本是 raw read/write,
            #    **完全繞過本檔的 _restore_from_backup**,等於一道防線都沒有。
            #    實測拿前 1/8 的半截備份還原,416,753 bytes 的語系檔變成 52,094,
            #    而且印「✅ 已還原」—— 更糟的是下一行就把備份刪掉,
            #    唯一的副本也沒了。改成走那個函式(它會擋掉截斷的備份)。
            try:
                _restore_from_backup(bak, live)
                # 還原成功才算成功:蓋回去之後跟備份逐位元組比一次,
                # 比過了才刪備份。「寫完就當作成功」是這類工具最常見的謊。
                _verify_restored(bak, live)
            except SystemExit as e:
                # ⚠️ 一個檔的備份壞掉,不可以把另一個檔一起帶走。
                #    這裡以前是讓 SystemExit 直接往上飛,而迴圈是先 IGENG 後 FEENG,
                #    所以 IGENG 的備份壞掉時整支就結束了 —— FEENG 就算備份是好的
                #    也永遠不會被還原,畫面上連 FEENG 這三個字都不會出現。
                #    2026-09-05 實測過:FEENG 那份 219,421 bytes 的完好備份原封不動,
                #    正本停在被改過的狀態。改成記下來、繼續處理下一個檔。
                print('  ❌ %s 沒有還原:' % name)
                # 訊息本身是多行的,每一行都對齊到同一個縮排再印,
                # 不然第二行以後會比第一行還靠左,看起來像另一段話。
                for ln in str(e).splitlines():
                    print('     %s' % ln.lstrip())
                failed.append(name)
                continue
            os.remove(bak)
            print('  ✅ 已還原 %s' % name)
            n += 1
    if failed:
        # 還是要用非 0 的 exit code 結束,但話要講完整:哪些還原了、哪些沒有。
        raise SystemExit(
            '  %s 沒有還原,%s。\n'
            '  沒還原的那些,備份都還留著沒有刪 —— 原因與該怎麼辦寫在上面那幾行。'
            % ('、'.join(failed),
               ('另外 %d 個檔已經還原好了' % n) if n else '沒有任何檔被還原'))
    if not n:
        print('  找不到備份,沒有東西要還原。')


def _interrupted(restoring):
    """被 Ctrl-C 打斷時,照登記說清楚遊戲檔有沒有被動到。

    ⚠️ 「什麼都沒有動到」這句話只有在 os.replace 一次都沒做過的時候才能說。
       猜的不算 —— 所以每一次 os.replace 成功之後都會把目的檔記進 _WRITTEN,
       這裡讀的就是那份紀錄。

    四種說法對應四種真實狀態,exit code 都是 130(shell 慣例:128 + SIGINT):
      · **正在換某個檔** → 不知道換完了沒有,請 --restore 或自己跟備份比對
      · 一次都沒換過   → 什麼都沒有動到
      · 只換過備份檔   → 遊戲檔沒動,只是多了一份備份
      · 換過遊戲檔     → 遊戲檔已經改了,要回到原點就 --restore

    第一種是 2026-09-06 補的保險。_NoInterrupt 已經讓「換完了但還沒登記」
    幾乎不可能發生(那兩行中間收到的 Ctrl-C 會被延後),但「幾乎」不是「不會」:
    signal.signal 在非主執行緒裝不上去,那時候窗口還開著。窗口開著的時候
    這支腳本要說「我不確定」,不可以說「沒動到」。
    """
    live = [p for p in _WRITTEN if not p.endswith(BACKUP)]
    # 「正在換」而且還沒登記成「已換」的,才是不確定的那些。
    busy = [p for p in _REPLACING if p not in _WRITTEN]
    if busy:
        print()
        print('  ⚠️ 被 Ctrl-C 中斷,而中斷的時候**正在替換**下面這些檔:')
        for p in busy:
            print('       %s' % p)
        print('  換名本身是原子的,所以它要嘛還是原本那份、要嘛已經是新的完整檔,')
        print('  不會有半截檔 —— 但這支腳本無法確定是哪一種。請用 --restore 還原,')
        print('  或自己拿 .locbak 跟它比對一次:')
        print('    python3 %s "<遊戲資料夾>" --restore' % _selfcmd())
        if live:
            print('  另外,下面這些遊戲檔可以確定已經換過了:')
            for p in live:
                print('       %s' % p)
        print()
        return 130
    print()
    if live and restoring:
        # 還原途中被打斷。os.replace 是原子的,所以每個檔要嘛還是被改過的那份、
        # 要嘛已經是還原好的完整檔,不會有半截檔。再跑一次 --restore 是安全的。
        print('  被 Ctrl-C 中斷。下面這些檔已經還原完成(換名是原子的,沒有半截檔):')
        for p in live:
            print('       %s' % p)
        print('  其餘的檔還沒還原,再跑一次 --restore 就好。')
    elif live:
        print('  ⚠️ 被 Ctrl-C 中斷,而且**遊戲檔已經被改過**了:')
        for p in live:
            print('       %s' % p)
        print('  要回到原本的樣子:')
        print('    python3 %s "<遊戲資料夾>" --restore' % _selfcmd())
    elif _WRITTEN:
        print('  被 Ctrl-C 中斷。遊戲檔一個位元組都沒有動到,只是多了備份檔:')
        for p in _WRITTEN:
            print('       %s' % p)
    else:
        print('  被 Ctrl-C 中斷。什麼都沒有動到。')
    print()
    return 130


def main():
    """把命令列參數接成一個動作,並且把例外翻成一行中文。

    判斷順序是 --restore → --fix → 什麼都沒加(只看)。
    --apply 不是動作,是「--fix 要不要真的寫檔」的開關;
    單獨加 --apply 會走到「只看」那一條,什麼都不會被寫。
    ⚠️ 它管不到 --restore。--restore 排在最前面而且自己就會寫檔,
       不加 --apply 一樣會把 .locbak 蓋回去、蓋完再把備份刪掉。

    只接 DataError,它代表「你的檔案或參數有問題」,印一行中文、回 exit code 2。

    ⚠️ 這裡不是「DataError 一行中文 / 其他全部 traceback」的二分法,SystemExit
    走的是第三條路:--restore 的 _restore_from_backup() 擋下壞掉的備份時丟它,
    參數打錯時 argparse 也丟它。兩種都不經過下面這個 except,訊息由 Python
    自己印到 stderr,也都不會有 traceback。

    2026-09-03 在本站測試機那份 data/FEENG.LOC 上實測(416,753 bytes,
    與同資料夾那份舊備份逐位元組相同;
    備份刻意截成前 1/8 的 52,094 bytes):
      · --restore 印「這份備份是壞的,不敢拿它覆蓋 …」,echo $? = 1
        (2026-09-05 起訊息前面多一行「❌ IGENG.LOC 沒有還原:」,而且會**繼續**
         處理 FEENG.LOC,最後才由 cmd_restore 自己丟 SystemExit 收尾,
         exit code 一樣是 1)
      · 路徑指到不存在的資料夾走 DataError,印「停下來了：…」,echo $? = 2
      · 不給任何參數,argparse 印用法,echo $? = 2

    DataError 與 SystemExit 以外的例外才會丟出完整 traceback:那是程式的錯,
    不該被包裝成一句好看的中文而讓人以為是自己弄錯。

    第四條路是 Ctrl-C:接住 KeyboardInterrupt、照登記說清楚
    「遊戲檔到底有沒有被動到」,回 exit code 130(shell 的慣例:128 + SIGINT)。
    2026-09-05 之前這裡沒有接,Python 會印 KeyboardInterrupt 的 traceback;
    而更早的版本在某些路徑上是安靜地回 0 —— 那等於告訴使用者「沒事」,
    但那句話有一半的機率是假的。
    ⚠️ 2026-09-06:登記從兩態變三態(還沒動 / 正在換 X / 已換 X),而且
    「換名 + 登記」被包進 _NoInterrupt。細節與實測見檔頭「安全網」那一段。
    """
    ap = argparse.ArgumentParser(
        description='把中文語系檔裡會讓遊戲當掉的格式符拿掉（中文字不動）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
照順序做:

  1. 先看有幾條(唯讀,一個位元組都不寫)
     python3 mvp_fix_loc.py "<遊戲資料夾>"

  2. 預覽修法(還是不寫)
     python3 mvp_fix_loc.py "<遊戲資料夾>" --fix

  3. 確定了才真的修
     python3 mvp_fix_loc.py "<遊戲資料夾>" --fix --apply

  沒改善就還原:
     python3 mvp_fix_loc.py "<遊戲資料夾>" --restore

⚠️ --fix 沒有加 --apply 就只是預覽,一個位元組都不會落地。
⚠️ --restore 不看 --apply,打了就直接寫回去,而且會把備份用掉。
''')
    ap.add_argument('path', help='遊戲安裝資料夾（它的下一層才是 data）')
    ap.add_argument('--fix', action='store_true', help='修（不加 --apply 只是預覽）')
    ap.add_argument('--apply', action='store_true', help='真的寫入（沒加就只是預覽）')
    ap.add_argument('--restore', action='store_true', help='還原')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試(不需要遊戲資料夾,也不碰任何遊戲檔)')
    # ⚠️ --selftest 要走在 parse_args() **之前**:path 是必填的位置參數,
    #    讓 argparse 先看到就會因為缺 path 而印用法。上面還是把它加進 parser,
    #    那是為了讓 --help 列得到它;真正接住它的是下面這兩行。
    #    這樣「不給遊戲資料夾 → argparse 印用法、exit code 2」那個行為
    #    一個字都沒有變。
    if '--selftest' in sys.argv[1:]:
        return selftest()
    args = ap.parse_args()
    try:
        print()
        if args.restore:
            cmd_restore(args.path)
        elif args.fix:
            cmd_fix(args.path, args.apply)
        else:
            cmd_show(args.path)
        print()
        return 0
    except DataError as e:
        print('  停下來了：%s\n' % e)
        return 2
    except KeyboardInterrupt:
        return _interrupted(args.restore)


def _fake_loc(pairs):
    """造一份最小但結構完整的 .LOC,只給 --selftest 用,完全不碰遊戲檔。

    版面照本站測試機那份 data/IGENG.LOC 量出來的抄(xxd 前 64 bytes):

        00000000  4c4f 4348 1400 0000 0100 0000 0100 0000   LOCH,檔頭長 20
        00000010  e418 0000 4c4f 4349 d018 0000 3006 0000   +0x10 是 LOCL 的位移
                                                            接著 LOCI、idxoff、條數

    所以 +0x10 那 4 bytes 一定要放 LOCL 的**絕對**位移 ——
    _restore_from_backup 的第 3 道就是照它走的,放錯的話連完好的備份都會被擋。
    """
    count = len(pairs)
    hdrlen = 20
    locl_off = hdrlen + 16 + count * 4          # LOCI 佔 16 + 索引表
    idxoff = locl_off - hdrlen                  # 只當「從這裡往後找 LOCL」的起點
    head = b'LOCH' + struct.pack('<IIII', hdrlen, 1, 1, locl_off)
    idx = b''.join(struct.pack('<HH', sid, 0) for sid, _t in pairs)
    loci = b'LOCI' + struct.pack('<II', idxoff, count) + b'\x00' * 4 + idx
    body = b''
    offs = []
    base = 16 + count * 4                       # 位移是相對於 'LOCL' 的開頭算的
    for _sid, txt in pairs:
        offs.append(base + len(body))
        body += txt.encode('utf-16-le') + b'\x00\x00'
    locl = (b'LOCL' + b'\x00' * 8 + struct.pack('<I', count)
            + b''.join(struct.pack('<I', o) for o in offs) + body)
    return head + loci + locl


def selftest():
    """--selftest:自己造一份最小的語系檔來測,完全不碰任何遊戲檔。

    ⚠️ 為什麼每一道把關都要配一個「餌」:2026-08-29 本站踩過 ——
       防線壞掉了,測試照樣全綠。只有正向測試的話,通過只能證明
       「正常流程沒壞」,證明不了「不正常的東西真的被擋下來」。
       所以下面標成【餌】的每一塊,都是**故意做一件必須失敗的事**;
       它沒有失敗,才是出事了。

    測到的東西:
      正向 —— 自造的語系檔讀得出來、strip_fmt 砍對地方、analyse 挑對條數、
              --fix --apply 真的改對而且編號一個沒變、--restore 逐位元組回到原點、
              檔案權限沒有被還原動作改掉、os.replace 有被記進 _WRITTEN
      餌   —— 複驗對不上要自動還原並回非 0、半截舊備份在動筆之前就被擋、
              半截備份不可以還原得下去、還原途中 os.replace 出錯正本要原封不動
              而且不留暫存檔、`<備份檔>.part` 符號連結不可以被沿用、
              指向不存在目標的符號連結(exists() 看不到的那種)要被擋、
              正本本身是符號連結也要被擋、
              **Ctrl-C 落在「換名之後、登記之前」不可以說「什麼都沒有動到」**、
              **狀態真的不明的時候要照實說「正在替換」**、
              **兩個檔只改到一半要逐檔講「已改 / 沒改」**,
              而且一個位元組都沒寫的時候**不可以誣賴自己改過檔**

    ⚠️ 這個函式在 `python3 -O` 底下會拒跑並回 exit code 2(見開頭第一段)。
    """
    # ⚠️ 第一件事:python -O 會把 assert 整句拿掉。這支目前是自己 raise
    #    AssertionError(不是 assert 句),所以 -O 底下**這一版**其實還是真的在測;
    #    但只要以後有人補一行 assert 進來,-O 就會讓它變成假綠而沒有人發現。
    #    測試工具寧可拒跑,也不要印一行沒有根據的「全部通過」。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:'
              '-O 會把 assert 全部拿掉,測試會假綠。請拿掉 -O 再跑一次。')
        return 2

    import contextlib
    import io as _io

    tally = {'n': 0, 'bait': 0}

    def ck(cond, msg, is_bait=False):
        tally['n'] += 1
        if is_bait:
            tally['bait'] += 1
        if not cond:
            raise AssertionError(msg)

    def quiet(fn, *a):
        with contextlib.redirect_stdout(_io.StringIO()):
            return fn(*a)

    # 英文基準不帶格式符,中文那兩條分別多要 2 個與 4 個參數 ——
    # 就是檔頭講的 23484 / 23505 那兩條的縮影。
    EN = [(23484, 'Right Field Camera'), (23505, 'Argument Intensity')]
    CN = [(23484, '   -  %s得分。%c'), (23505, ' - %s盜%d%s壘成功。%c')]
    FIXED = ['   -  得分。', ' - 盜壘成功。']

    root = tempfile.mkdtemp(prefix='mvp_fix_loc_selftest_')

    def make_game(both=False):
        """每一塊測試都用全新的一份,免得上一塊的殘留影響下一塊。

        both=True 會連 FEENG.LOC 也造出來 —— 「兩個檔只改到一半」那一道餌
        需要真的有兩個檔可以改,只有一個的話它根本咬不到。
        """
        d = tempfile.mkdtemp(dir=root)
        en = os.path.join(d, 'data', '2023英文語系')
        os.makedirs(en)
        names = ('IGENG.LOC', 'FEENG.LOC') if both else ('IGENG.LOC',)
        for nm in names:
            with open(os.path.join(d, 'data', nm), 'wb') as f:
                f.write(_fake_loc(CN))
            with open(os.path.join(en, nm), 'wb') as f:
                f.write(_fake_loc(EN))
        return d, os.path.join(d, 'data', 'IGENG.LOC')

    def read(p):
        with open(p, 'rb') as f:
            return f.read()

    def junk(live):
        """資料夾裡有沒有留下我們自己的暫存檔(名字都是 .<檔名>.<標籤>-亂數)。"""
        pre = '.' + os.path.basename(live)
        return [x for x in os.listdir(os.path.dirname(live)) if x.startswith(pre)
                and not x.endswith(BACKUP)]

    # ── 正向:先證明正常流程真的會做到承諾的事 ──────────────────────
    # 少了這一段,下面的餌可能只是「因為整支都壞了」才過的。
    d, live = make_game()
    orig = read(live)
    _b, C = parse(live)
    ck(C['ids'] == [23484, 23505], '自造的語系檔讀不出正確的字串編號')
    ck(C['strs'] == [t for _s, t in CN], '讀出來的文字不對')
    ck(strip_fmt(CN[0][1], 0) == FIXED[0], 'strip_fmt 砍錯了(keep=0)')
    ck(strip_fmt(CN[1][1], 2) == ' - %s盜%d壘成功。', 'strip_fmt 沒有留下最前面 2 個')
    ck(len(analyse(d)[0][2]) == 2, 'analyse 應該挑出 2 條')

    os.chmod(live, 0o644)
    mode_before = os.stat(live).st_mode & 0o777
    del _WRITTEN[:]
    quiet(cmd_fix, d, True)
    ck(os.path.isfile(live + BACKUP), '--fix --apply 之後應該要有備份')
    ck(read(live + BACKUP) == orig, '備份放的不是原檔')
    _b2, C2 = parse(live)
    ck(C2['strs'] == FIXED, '修完的內容不對')
    ck(C2['ids'] == C['ids'], '字串編號被動到了')
    ck(live in _WRITTEN, 'os.replace 做過卻沒有記進 _WRITTEN —— Ctrl-C 就會說錯話')
    ck(not junk(live), '寫完不可以留下暫存檔:%r' % junk(live))

    quiet(cmd_restore, d)
    ck(read(live) == orig, '還原之後應該逐位元組回到原本的樣子')
    ck(not os.path.exists(live + BACKUP), '還原成功之後備份應該被刪掉')
    ck(os.stat(live).st_mode & 0o777 == mode_before, '還原不該改掉檔案權限')

    # ── 【餌】複驗對不上:要自動還原,而且不可以成功結束 ────────────────
    d, live = make_game()
    orig = read(live)
    real_rebuild = globals()['rebuild']

    def wrong_rebuild(path, C_, newstrs):
        # 故意只讓「內容」那一項對不上:結構、條數、編號全部正常,
        # 這樣前兩項都會放行,只有第三項抓得到 —— 餌才咬得到那一道。
        return real_rebuild(path, C_, ['我不是你要的東西'] + list(newstrs[1:]))

    globals()['rebuild'] = wrong_rebuild
    try:
        blocked = False
        try:
            quiet(cmd_fix, d, True)
        except SystemExit:
            blocked = True
    finally:
        globals()['rebuild'] = real_rebuild
    ck(blocked, '複驗對不上竟然還是成功結束 —— 防線失效', True)
    ck(read(live) == orig, '複驗沒過就要自動還原回原本的樣子', True)
    ck(os.path.isfile(live + BACKUP), '自動還原之後備份要留著不刪', True)

    # ── 【餌】半截的舊備份:要在動筆之前就被擋下來 ──────────────────
    d, live = make_game()
    orig = read(live)
    with open(live + BACKUP, 'wb') as f:
        f.write(orig[:40])
    del _WRITTEN[:]
    blocked = False
    try:
        quiet(cmd_fix, d, True)
    except DataError:
        blocked = True
    ck(blocked, '半截的舊備份竟然被沿用了 —— 防線失效', True)
    ck(read(live) == orig, '被擋下來的時候正本一個位元組都不可以動', True)
    ck(not _WRITTEN, '一個位元組都沒寫,_WRITTEN 就不該有東西', True)

    # ── 【餌】--restore 拿半截備份:要被擋,正本不可以被動到 ──────────
    d, live = make_game()
    orig = read(live)
    quiet(cmd_fix, d, True)
    fixed = read(live)
    ck(fixed != orig, '測試本身壞了:--apply 之後檔案應該不一樣')
    with open(live + BACKUP, 'wb') as f:
        f.write(orig[:40])
    blocked = False
    try:
        quiet(cmd_restore, d)
    except SystemExit:
        blocked = True
    ck(blocked, '半截的備份竟然還原得下去 —— 防線失效', True)
    ck(read(live) == fixed, '備份被擋下來的時候正本一個位元組都不可以動', True)

    # ── 【餌】還原途中 os.replace 出錯:正本要原封不動,不留暫存檔 ────
    # 這一道就是 shutil.copy2 的那個窗口:copy2 會先把正本截成 0 再寫,
    # 斷在中間就回不去了。原子版是「暫存檔寫壞了就丟掉」,正本沒被碰過。
    d, live = make_game()
    quiet(cmd_fix, d, True)
    fixed = read(live)
    real_replace = os.replace

    def boom(_a, _b):
        raise OSError(28, '磁碟滿了(自我測試故意丟的假錯誤)')

    os.replace = boom
    try:
        blocked = False
        try:
            quiet(cmd_restore, d)
        except (OSError, SystemExit):
            blocked = True
    finally:
        os.replace = real_replace
    ck(blocked, '還原途中出錯竟然沒有反應 —— 防線失效', True)
    ck(read(live) == fixed, '還原途中出錯,正本必須原封不動(不可以是 0 或半截)', True)
    ck(os.path.isfile(live + BACKUP), '還原沒成功就不可以把備份刪掉', True)
    ck(not junk(live), '失敗之後不可以留下暫存檔:%r' % junk(live), True)

    # ── 【餌】Ctrl-C 落在「換名之後、登記之前」:不可以說「什麼都沒動到」──
    # 這是 2026-09-06 補的那道。做法是把 os.replace 換成「先做真正的換名,
    # 再對自己送一個 SIGINT」—— 也就是把 Ctrl-C 精準地塞進那個窗口裡。
    # _NoInterrupt 會把它記著、等登記做完才丟出來,所以 _WRITTEN 一定有東西。
    # 沒有 _NoInterrupt 的話這裡會是空的,收尾就會說「什麼都沒有動到」——
    # 而磁碟上那個檔其實已經被換掉了。**那句話就是這道餌要抓的謊。**
    def _self_sigint():
        # raise_signal 是 3.8 才有的,而且跨平台(Windows 上 os.kill 送 SIGINT
        # 的語意跟 POSIX 不一樣)。沒有它就不假裝測過。
        signal.raise_signal(signal.SIGINT)
        # 送出去只是設一個旗標,Python 層的處理常式要等下一個檢查點才跑。
        # 燒掉一些位元組碼確保它真的跑到,不然這道餌會變成看運氣。
        for _ in range(200000):
            pass

    ctrlc_skipped = 0
    if hasattr(signal, 'raise_signal'):
        d, live = make_game()
        orig = read(live)
        real_replace = os.replace

        def replace_then_sigint(a, b):
            r = real_replace(a, b)
            if os.fspath(b) == live:      # 只在換「正本」的那一次咬,備份那次放行
                _self_sigint()
            return r

        del _WRITTEN[:]
        del _REPLACING[:]
        os.replace = replace_then_sigint
        try:
            bit = False
            try:
                quiet(cmd_fix, d, True)
            except KeyboardInterrupt:
                bit = True
        finally:
            os.replace = real_replace
        ck(bit, 'Ctrl-C 被吞掉了 —— _NoInterrupt 應該在離開那一段之後照常丟出來', True)
        ck(read(live) != orig, '測試本身壞了:換名應該已經真的做完了', True)
        ck(live in _WRITTEN,
           '換名做完了卻沒登記 —— 收尾會說「什麼都沒有動到」,那是假話', True)
        ck(not [p for p in _REPLACING if p not in _WRITTEN],
           '「正在換」的登記沒有收乾淨', True)
        # 收尾真的會承認嗎?把 _interrupted 的輸出接下來看。
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _interrupted(False)
        ck(rc == 130, 'Ctrl-C 的 exit code 一定是 130', True)
        ck('已經被改過' in buf.getvalue(),
           '遊戲檔已經換過了,收尾卻沒有承認', True)
        ck('--restore' in buf.getvalue(), '換過檔就要印還原指令', True)

        # 反過來:Ctrl-C 落在**進入那一段之前**,就必須說「沒動到」。
        # 這裡用「換名時直接丟 KeyboardInterrupt、而且不做換名」來模擬
        # 最壞的情況(signal.signal 裝不上去、窗口還開著)。那時候誰也不知道
        # 換名做完了沒有,所以正確答案不是「沒動到」也不是「已改」,
        # 而是**照實說「正在替換」**。說「沒動到」才是說謊。
        d, live = make_game()
        orig = read(live)
        real_replace = os.replace

        def replace_is_ctrlc(a, b):
            if os.fspath(b) == live:
                raise KeyboardInterrupt
            return real_replace(a, b)

        del _WRITTEN[:]
        del _REPLACING[:]
        os.replace = replace_is_ctrlc
        try:
            bit = False
            try:
                quiet(cmd_fix, d, True)
            except KeyboardInterrupt:
                bit = True
        finally:
            os.replace = real_replace
        ck(bit, '測試本身壞了:應該要飛出 KeyboardInterrupt', True)
        ck(read(live) == orig, '這一種模擬裡正本不該被換掉', True)
        ck(live not in _WRITTEN, '沒換成就不可以登記成「已換」', True)
        ck(live in _REPLACING,
           '不知道換完了沒有的時候,「正在換」的登記不可以被撤掉', True)
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _interrupted(False)
        ck(rc == 130, 'Ctrl-C 的 exit code 一定是 130', True)
        ck('正在替換' in buf.getvalue(),
           '狀態不明的時候要照實說「正在替換」,不可以說「什麼都沒有動到」', True)
        ck('什麼都沒有動到' not in buf.getvalue(),
           '狀態不明卻說「什麼都沒有動到」—— 這就是那句謊話', True)
        del _REPLACING[:]
    else:
        ctrlc_skipped = 2

    # ── 【餌】兩個檔只改到一半:要逐檔講「已改 / 沒改」並印還原指令 ────
    # 兩個語系檔是依序處理的,第二個檔中途出事的時候第一個已經改好了。
    # 原本的訊息只講得到出事的那一個 —— 看的人不會知道另一個已經被動過。
    d, live = make_game(both=True)
    feeng = os.path.join(d, 'data', 'FEENG.LOC')
    real_rebuild = globals()['rebuild']

    def rebuild_second_blows_up(path, C_, newstrs):
        if os.fspath(path) == feeng:
            raise OSError(28, '磁碟滿了(自我測試故意丟的假錯誤)')
        return real_rebuild(path, C_, newstrs)

    del _WRITTEN[:]
    del _REPLACING[:]
    globals()['rebuild'] = rebuild_second_blows_up
    buf = _io.StringIO()
    try:
        bit = False
        try:
            with contextlib.redirect_stdout(buf):
                cmd_fix(d, True)
        except OSError:
            bit = True
    finally:
        globals()['rebuild'] = real_rebuild
    said = buf.getvalue()
    ck(bit, '第二個檔寫壞了竟然沒有反應 —— 防線失效', True)
    ck('已改 IGENG.LOC' in said, '第一個檔已經改掉了,卻沒有逐檔講出來', True)
    ck('沒改 FEENG.LOC' in said, '沒改到的那個也要講,不然看的人得自己猜', True)
    ck('--restore' in said, '改到一半就要印還原指令', True)

    # 陰性對照:一個位元組都沒寫的那條路(舊備份是半截的,動筆之前就被擋),
    # **不可以**印「已改」。只靠「跟備份比對」會在這裡誣賴自己改過檔 ——
    # 因為那份備份本來就跟正本不一樣。
    d, live = make_game(both=True)
    orig = read(live)
    with open(live + BACKUP, 'wb') as f:
        f.write(orig[:40])
    del _WRITTEN[:]
    del _REPLACING[:]
    buf = _io.StringIO()
    blocked = False
    try:
        with contextlib.redirect_stdout(buf):
            cmd_fix(d, True)
    except DataError:
        blocked = True
    ck(blocked, '半截的舊備份竟然被沿用了 —— 防線失效', True)
    ck('已改' not in buf.getvalue(),
       '一個位元組都沒寫,卻說自己改過檔 —— 誣賴自己也是說謊', True)
    ck(read(live) == orig, '被擋下來的時候正本一個位元組都不可以動', True)

    # ── 【餌】符號連結三塊 ───────────────────────────────────────
    # Windows 沒開開發者模式時建不了符號連結,那三塊就跳過(並且說出來),
    # 不假裝測過。
    skipped = 0
    try:
        probe = os.path.join(root, '_probe')
        os.symlink(os.path.join(root, '_nowhere'), probe)
        os.remove(probe)
        can_link = True
    except (OSError, NotImplementedError, AttributeError):
        can_link = False

    if can_link:
        # (a) 可以預測的舊名字 `<備份檔>.part`:先擺一個指向資料夾外面的連結。
        #     舊版會沿著它把外面那個檔覆寫掉;現在的名字帶亂數,根本不會用到它。
        d, live = make_game()
        orig = read(live)
        outside = os.path.join(root, 'outside_a.txt')
        with open(outside, 'wb') as f:
            f.write(b'this file lives outside the game folder')
        keep = read(outside)
        os.symlink(outside, live + BACKUP + '.part')
        quiet(cmd_fix, d, True)
        ck(read(outside) == keep, '資料夾外面的檔被 <備份檔>.part 連結帶著改掉了', True)
        ck(read(live + BACKUP) == orig, '備份還是要正常做出來(陰性對照)', True)

        # (b) 備份檔本身是**指向不存在目標**的符號連結 ——
        #     os.path.exists() 對它回 False,這正是舊寫法看不到的那一種。
        d, live = make_game()
        orig = read(live)
        ghost = os.path.join(root, 'outside_b_does_not_exist.txt')
        os.symlink(ghost, live + BACKUP)
        ck(not os.path.exists(live + BACKUP),
           '測試本身壞了:dangling symlink 在 exists() 眼中應該是 False', True)
        blocked = False
        try:
            quiet(cmd_fix, d, True)
        except SystemExit:
            blocked = True
        ck(blocked, '備份檔是符號連結竟然照樣寫下去 —— 防線失效', True)
        ck(not os.path.exists(ghost), '沿著連結在資料夾外面生出了新檔案', True)
        ck(read(live) == orig, '被擋下來的時候正本一個位元組都不可以動', True)

        # (c) 正本自己是符號連結,指到資料夾外面。
        d, live = make_game()
        real = os.path.join(root, 'outside_c.LOC')
        os.replace(live, real)
        os.symlink(real, live)
        keep = read(real)
        blocked = False
        try:
            quiet(cmd_fix, d, True)
        except SystemExit:
            blocked = True
        ck(blocked, '正本是符號連結竟然照樣寫下去 —— 防線失效', True)
        ck(read(real) == keep, '沿著連結改到了遊戲資料夾外面的檔案', True)
    else:
        skipped = 3

    shutil.rmtree(root, ignore_errors=True)
    print('自我測試:全部通過(%d 道檢查,其中 %d 道是反向餌)'
          % (tally['n'], tally['bait']))
    if skipped:
        print('           這台機器建不了符號連結,%d 塊符號連結的餌跳過了 —— '
              '沒有測到,不算通過。' % skipped)
    if ctrlc_skipped:
        # 跳過就要說出來。不說的話,這一行「全部通過」會把「沒測到」
        # 混進「測過了」裡面 —— 那正是這一輪在修的那種謊。
        print('           這個 Python 沒有 signal.raise_signal(3.8 以前),'
              '%d 塊 Ctrl-C 的餌跳過了 —— 沒有測到,不算通過。' % ctrlc_skipped)
    return 0


if __name__ == '__main__':
    sys.exit(main())


# ─────────────────────────────────────────────────────────
#  MIT License
#
#  Copyright (c) 2026 toni
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
# ─────────────────────────────────────────────────────────
