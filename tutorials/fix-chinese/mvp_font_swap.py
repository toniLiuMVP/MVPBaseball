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
mvp_font_swap.py —— 一個一個換字型,找出到底是哪一個把記憶體吃爆

    先看現況        python3 mvp_font_swap.py "<遊戲資料夾>"
    預覽要換什麼    python3 mvp_font_swap.py "<遊戲資料夾>" --swap au20b,Tw24
    真的換過去      python3 mvp_font_swap.py "<遊戲資料夾>" --swap au20b,Tw24 --apply
    還原            python3 mvp_font_swap.py "<遊戲資料夾>" --restore
    自我測試        python3 mvp_font_swap.py --selftest

⚠️ 上面第二行**只是預覽**,一個位元組都不會寫。要真的換,同一行最後面
   加上 --apply(第三行)。這兩行只差三個字,所以特地分開寫。

⚠️ 只改 data/fonts/fonts.big,而且一定先備份成 .fontbak,--restore 一行還原。

─────────────────────────────────────────────────────────
 這在解什麼
─────────────────────────────────────────────────────────
2026-08-28 的對照實驗(toni 實機):
**同一個球場檔(清到 8.51 MB,逐位元組相同),英文版進得去,中文版讀取條讀完就當。**

→ 「球場超過 10MB 就當」這條傳了二十年的規矩 **被這一場實驗推翻了**。
   清到 8.51 MB 照樣當,所以問題不在檔案大小。

→ 而中英文的差別被壓縮到 **三個檔**:`FEENG.LOC`、`IGENG.LOC`、`fonts.big`。
   兩個文字檔中文版還比較**小**,只有字型檔變大:

       字型解開後   英文 777,520  →  中文 2,726,912   (多 1.95 MB)

→ 而「讀取條讀完」那一刻,正是球場載入完、要把畫面的字型交出去的時候。

⚠️ **本站沒有證明「字型吃爆記憶體」就是主因。** 量到的是上面那些數字加上
   toni 的對照實驗。機制那一段還是推論 —— 這支腳本就是拿來驗它的。

─────────────────────────────────────────────────────────
 為什麼可以只換一部分
─────────────────────────────────────────────────────────
中文化那份 fonts.big 裡有 12 個字型,但**不是每個都需要中文**:

    字型         中文版字元數    解開後大小     裡面有中文嗎
    au20b            98         526,560       ❌ 沒有(最肥的一個!)
    Tw24             33         132,192       ❌ 沒有
    dflt             95          67,168       ❌ 沒有
    hrdbg           158          72,544       ❌ 沒有(跟英文版逐位元組相同)
    mini1/mini2     267      70,240/135,776   一點點
    frk12 · twc14/16/18 · twcnb · twn14
                   1529         287,072 各    ✅ 這六個才是中文字型

**`au20b` 只有 98 個字元卻佔 526,560** —— 每個字 5,373 bytes,是其他字型的 30 倍。
它不是中文字型,是**做得很大的英文字型**。把它換回英文版的那一份,
一次省 508,560 bytes,而**中文一個字都不會少**。

─────────────────────────────────────────────────────────
 輸入 / 輸出 / 安全網 / 做不到的事
─────────────────────────────────────────────────────────
輸入
  · 一個位置參數:遊戲安裝資料夾(它的下一層才是 data)
  · 會被改到的檔只有一個:<遊戲資料夾>/data/fonts/fonts.big
  · 拿來換過去的「來源字型」自動照這個順序找第一個存在的:
        data/2023英文語系/fonts   data/英文語系/fonts   data/2023英文語系/Fonts
        data/中文語系/Fonts       data/中文語系/fonts
    英文那幾條排在前面,因為英文版是「不會當」的那一邊。
    也可以用 --source 直接指定一個 fonts.big。

輸出
  · 不加旗標           只在畫面上列表(每個字型現在解開後多大、換過去會差多少),
                       一個位元組都不寫
  · --swap / --dedupe  沒加 --apply 就只印預覽,一樣不寫檔
  · --swap --apply     重寫 data/fonts/fonts.big,寫完立刻重讀,逐項逐位元組
                       比對一次,結果印在「複驗」那一行
  · --dedupe --apply   重寫 data/fonts/fonts.big,印「合併的組 / 檔案大小 /
                       解開後總量 / 字型數量」四項,寫完也會重讀複驗
                       (2026-09-05 補的;在那之前這條路沒有這一關)
  · --restore          把 .fontbak 蓋回去,再把備份檔刪掉。**不需要 --apply**,
                       打了就直接寫
  · --selftest         自己造一份最小的 BIGF 來測,不看遊戲資料夾、
                       不碰任何遊戲檔。全過印一行、回 exit code 0。
                       ⚠️ 在 python3 -O 底下會直接拒絕跑、回 exit code 2:
                       -O 會把 assert 全部拿掉,跑下去會印出假的綠燈

安全網
  · --swap 與 --dedupe 預設就是預覽。沒有 --apply 就一個位元組都不會落地。
    (反向對照:--swap au20b 不加 --apply,fonts.big 前後 SHA-256 相同,
     也沒有生出 .fontbak。)
  · ⚠️ --restore 不吃上面那一條,它根本不看 --apply。main() 的判斷順序是
    --restore → --dedupe → --swap,--apply 完全不參與 --restore 那一條路:
    只打 --restore 就會把 .fontbak 蓋回 fonts.big,蓋完還把備份刪掉,
    所以「動之前一定先備份」對它不成立,它是反過來把備份用掉。
    2026-09-03 在暫存複本上實測:正本放中文語系那份 fonts.big(1,279,340 bytes)、
    備份放本機 data/Fonts 那份(397,327 bytes),只打 --restore(沒有 --apply)之後
    正本就變成 397,327 bytes、與備份逐位元組相同,.fontbak 也不見了。
  · 第一次寫入前備份成 fonts.big.fontbak,做法是「先寫一個同資料夾的唯一
    暫存檔(tempfile.mkstemp,名字猜不到也不可能被事先佔位)→ fsync →
    跟原檔對 SHA-256 → os.replace 換名」,中途被中斷不會留下半截備份。
    (2026-09-05 之前用的是 fonts.big.fontbak.part 這種猜得到的名字;
     那個名字要是被人先放上一個指向資料夾外面的符號連結,寫下去會先把
     外面那個檔截斷。現在名字是隨機的,而且動手前會先擋掉符號連結。)
  · **寫遊戲檔本身也是同一套**:--swap / --dedupe 的 --apply 不是直接
    open(fonts.big, 'wb'),而是先寫暫存檔、讀回來逐位元組對過,才 os.replace
    換上去。所以寫到一半斷電、拔碟、按 Ctrl-C,你的 fonts.big 維持原樣,
    不會變成半截檔。(2026-09-05 之前是直接寫的。)
  · 正本或備份的名字如果是符號連結,兩條 --apply 與 --restore 都會停下來,
    什麼都不寫。順著連結寫下去,被改到的會是連結另一頭那個檔。
  · 按 Ctrl-C 時印出來的那句話**不會說謊**:換名與登記被綁成一段不可中斷的
    區間(_NoInterrupt),外加「還沒動 / 正在換 / 已換」三態登記當保險。
    已經換過就承認換過並印還原指令,exit code 一律 130。
    (2026-09-06 之前:Ctrl-C 剛好落在換名與登記中間,會印「跟動手前一模一樣」,
     而正本的 SHA-256 其實已經變了。)
  · 備份已經存在就沿用、不覆蓋,所以重複執行不會把最早那一份原檔洗掉。
  · --swap --apply 寫完會重讀複驗;對不上就**停下來**(印一行中文、exit code 2),
    不會再叫你拿這個檔進遊戲,也不會回 exit code 0 讓包裝腳本誤判成功。
  · --dedupe --apply 從 2026-09-05 起也有這一關:寫完一樣重讀、逐項逐位元組
    比對,對不上就停下來(exit code 2)。在那之前它只印四項統計就結束。
  · --restore 會先驗備份再蓋回去,走的是本檔的 _restore_from_backup:
    0 bytes 的備份、BIGF 檔頭宣告長度跟實際長度對不上的備份(截斷一定對不上),
    都會被擋下來,而且**正本一個位元組都不會動**。蓋完再逐位元組比對一次,
    比對過了才把備份刪掉、才印成功;比對沒過就留著備份、印一行中文、exit code 2
    (備份在第一關就被擋下來的那一種,訊息走 stderr、exit code 1)。
    2026-09-05 在暫存複本上實測(2026-09-03 的舊紀錄寫的是修這一條之前的行為,
    已作廢):本站測試機那份中文版 fonts.big(1,279,340 bytes)跑過一次
    --swap au20b --apply(來源用本機 data/Fonts 那份 397,327 bytes 的 fonts.big,
    正本變 1,232,260 bytes),備份留著原本那 1,279,340;把備份截成八分之一的
    159,917 bytes 再 --restore,印「這份備份是壞的,不敢拿它覆蓋…」、
    exit code 1,正本仍是 1,232,260 且 SHA-256 一個位元組沒變,截斷的備份也還在。
    換成完整的備份再跑一次,正本回到 1,279,340,與動手前逐位元組相同。

做不到的事(先講,免得跑完才發現)
  · 不會生字型。只能在「你電腦上已經有的兩份 fonts.big」之間互搬,
    來源檔裡沒有的字型就換不了。兩邊的名字要一模一樣才換得動:2026-09-05
    實測剛安裝好的原版中文版那份(1,683,513 bytes / 13 項)名字是 _jp 結尾、
    原版英文那份(204,820 bytes / 12 項)是 _en,這兩份互相換不了,
    腳本會停下來說「來源檔裡沒有 au20b_jp.ffn」。
  · 前綴命中兩筆時不會替你猜。同一份原版中文版裡 dflt_en.ffn 與 dflt_jp.ffn
    並存,只打 dflt 會停下來要你把完整名字打出來(完整名字也認)。
  · 只碰 data/fonts/fonts.big。語系檔(FEENG.LOC / IGENG.LOC)、執行檔、
    球場檔一個都不動。
  · 不解 QFS 壓縮。上面那些「解開後大小」是讀 QFS 檔頭自己宣告的數字,
    不是解壓算出來的。
  · 不會直接告訴你兇手是誰。它只讓你一次換一組、每換一組進遊戲試一次,
    答案要你自己二分出來。
  · ⚠️ 「字型吃爆記憶體」這個前提,本站到現在也還沒證明(見上一段)。
  · --dedupe 2026-09-05 之前一執行就 NameError,現在修好了(經過是寫在
    cmd_dedupe 的說明裡)。它做的事跟 --swap 不一樣:不會讓「解開後合計」
    變小,所以它驗的是另一個問題,不是二分測試的替代品。

MIT License · Copyright (c) 2026 toni · 無外部相依,Python 3.7 以上
"""

import argparse
import hashlib
import os
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

def _reject_symlink(path, what):
    """目的檔是符號連結就停下來,不要順著它寫下去。

    2026-09-05 資安稽核抓到的形態:如果 <目標>.part 或 <目標> 本身是一個指向
    資料夾外面的符號連結,`open(..., 'wb')`／`shutil.copy2()` 會**先把連結指到
    的那個檔截斷**,之後的 os.replace 才換掉連結本身 —— 外面那個檔已經被寫壞了。

    ⚠️ 不能用 os.path.exists() 判:符號連結存在、但它指到的檔不存在時
       (dangling symlink),exists() 回 False,等於整道防線失效。
       os.path.islink() 走的是 lstat,不跟著連結,dangling 的也認得出來。

    ⚠️ 只擋**檔案本身**,不擋它上面那幾層資料夾 —— 這是刻意的:
       macOS 的 /tmp 本身就是指向 /private/tmp 的符號連結,外接碟、
       家目錄裡的捷徑也常常是。連資料夾一起擋會把一大票正常的安裝擋在門外。
       真正要防的那一招(有人先在猜得到的暫存名字上放好連結)已經被
       _new_temp 的 O_CREAT|O_EXCL 擋住,不必靠父資料夾檢查。
    """
    path = os.fspath(path)
    if os.path.islink(path):
        try:
            tgt = os.readlink(path)
        except OSError:
            tgt = '(讀不出來)'
        raise DataError(
            '%s 是一個符號連結(指向 %s),本工具不動它。\n'
            '     順著連結寫下去,被改到的會是連結另一頭那個檔。\n'
            '     請先把它換成真正的檔案,或換一個乾淨的遊戲資料夾再跑。'
            % (what, tgt))
    return path


def _new_temp(dst, tag):
    """在 dst 同一個資料夾裡開一個唯一的暫存檔,回傳 (檔案描述子, 路徑)。

    為什麼不用 dst + '.part' 這種猜得到的名字(2026-09-05 改掉的):
      · 猜得到 ⇒ 別人可以先在那個名字上放一個指向別處的符號連結,
        我們一 open 就把外面那個檔截斷了(見 _reject_symlink)
      · mkstemp 用 O_CREAT|O_EXCL 開檔,那個名字要是已經被佔(檔案也好、
        符號連結也好)就換一個,絕不可能寫到別人先放好的東西上

    放在**同一個資料夾**是 os.replace 要原子就必須同一個檔案系統;
    丟到 /tmp 再搬過來,跨磁碟時就退化成「複製 + 刪除」,又回到會留半截檔的老路。
    """
    dst = os.fspath(dst)
    d = os.path.dirname(os.path.abspath(dst))
    return tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(dst), tag))


def _sha256(path):
    """整份檔案的 SHA-256。用來確認「寫出去的」跟「來源」逐位元組相同。

    一次讀 1 MB,不把整份載進記憶體 —— 這個函式也會被拿去對執行檔那種大檔。
    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# 「正本已經被換上新內容了嗎」—— os.replace 真的做過才會記進來。
# 只記遊戲正本,不記 .fontbak:備份多一份不會害到任何人,
# 而 Ctrl-C 的訊息要回答的是「我的遊戲檔到底動了沒有」。
# 第二個欄位記的是「換成什麼」,因為「改過了」跟「已經還原了」之後
# 該給的建議剛好相反(前者要 --restore,後者已經在原點了)。
_WRITTEN = []


def _mark_written(path, why):
    _WRITTEN.append((os.fspath(path), why))


# 「正在換 X」這個中間態(2026-09-06 加)。
#
# ⚠️ 為什麼一份 _WRITTEN 不夠:os.replace 把遊戲檔換成新的之後,還要再跑一行
#    _mark_written() 才算登記過。Ctrl-C 剛好落在這兩行中間的話,收尾讀到的
#    _WRITTEN 是空的 —— 它會照舊狀態印「還沒有換過任何檔案」,而磁碟上那個檔
#    其實已經換過了。**那句話是假的**,而看到那句話的人不會去 --restore。
#
# 所以現在是三態:
#    · 不在 _REPLACING 也不在 _WRITTEN → 還沒動
#    · 在 _REPLACING 而不在 _WRITTEN   → 正在換,不知道換完了沒有
#    · 在 _WRITTEN                     → 已換
# 換名之前先進 _REPLACING,換完並登記進 _WRITTEN 之後才退出來。
_REPLACING = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包成一段不會被 Ctrl-C 切開的區間。

    這段期間收到的 SIGINT 先記著不處理,離開這段之後再照常丟出 KeyboardInterrupt。
    所以收尾看到的登記,一定跟磁碟上的狀態一致:要嘛「還沒換、也沒登記」,
    要嘛「換過了、也登記了」,不會卡在中間那個會說謊的窗口。

    ⚠️ 這**不是**「按了沒用」:訊號只是被延後到那兩行結束,離開這個區塊照樣
       丟 KeyboardInterrupt,exit code 一樣是 130。
    ⚠️ signal.signal 只能在主執行緒裝。裝不上去(非主執行緒等情況)就退回
       原本的行為 —— 不會比以前更糟,而且還有上面那個三態登記兜著。
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
            try:
                signal.signal(signal.SIGINT, self._old)
            except (ValueError, OSError):
                pass
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _replace_and_register(tmp, path, why, doing):
    """把暫存檔換成正本,並且登記 —— 這兩件事之間不可以被 Ctrl-C 切開。

    why   進 _WRITTEN 的講法(已經發生的事,例如「換成新的內容」)
    doing 進 _REPLACING 的講法(正在發生的事,例如「把它換成新的內容」)
    """
    path = os.fspath(path)
    key = (path, doing)
    # 「登記進去了沒有」不能用旗標判,要用 _WRITTEN 自己的長度:同一支腳本
    # 一次執行裡可能對同一個檔換好幾次(--selftest 就是),用 in 判會被上一次
    # 留下的同一筆騙到。長度變長 = 這一次真的登記進去了。
    n_before = len(_WRITTEN)
    _REPLACING.append(key)
    try:
        with _NoInterrupt():
            os.replace(tmp, path)      # 這一行是原子的:換上去,或什麼都沒發生
            _mark_written(path, why)
    except OSError:
        # 換名丟 OSError 就是**沒有**換成,狀態是明確的,可以放心撤掉「正在換」。
        _REPLACING.remove(key)
        raise
    finally:
        # ⚠️ 這裡是 finally 不是 else:_NoInterrupt 在區塊**結束時**才補丟那顆
        #    被延後的 KeyboardInterrupt,走 else 的話就永遠跑不到,已經誠實
        #    登記成「已換」的檔會被同時掛在「正在換」上(2026-09-06 餌 15 抓到的)。
        if len(_WRITTEN) > n_before:
            _REPLACING.remove(key)
    # ⚠️ 登記沒進去、又不是 OSError(例如 signal.signal 裝不上去時漏進來的
    #    KeyboardInterrupt)就刻意**不撤**「正在換」:那種時候真的不知道換名
    #    做完了沒有,收尾就該照實說「正在替換」,不可以說「沒動到」。


def _atomic_write(path, data):
    """把 data 變成 path 的新內容 —— 要嘛整份換上,要嘛 path 一個位元組都沒動。

    2026-09-05 之前 write_big / write_big_dedup 是直接 open(遊戲檔, 'wb') 寫下去的:
    那一行執行的瞬間遊戲檔就被截成 0,寫到一半斷電／拔碟／Ctrl-C,玩家拿到的是半截檔。
    現在改成「先寫同資料夾的唯一暫存檔 → fsync → 讀回來逐位元組對過 → os.replace」,
    對不上就把暫存檔刪掉、正本原封不動。

    順序不能換:**複驗排在 os.replace 之前**,所以「寫壞了」的那一份根本沒有機會
    成為玩家的遊戲檔。
    """
    path = os.fspath(path)
    _reject_symlink(path, '%s' % path)
    fd, tmp = _new_temp(path, 'new')
    try:
        with os.fdopen(fd, 'wb') as fo:
            fo.write(data)
            fo.flush()
            os.fsync(fo.fileno())          # 真的落到碟上,不是只到系統快取
        if os.path.exists(path):
            # 保留正本原本的權限。mkstemp 開出來的是 0600,
            # 直接換上去會讓遊戲檔從「大家讀得到」變成「只有我讀得到」。
            shutil.copymode(path, tmp)
        with open(tmp, 'rb') as f:
            back = f.read()
        if back != data:
            raise DataError(
                '剛寫出去的暫存檔讀回來跟記憶體裡的不一樣(%d bytes vs %d bytes)。\n'
                '     磁碟可能滿了或有問題。%s 一個位元組都沒有動,暫存檔已刪掉。'
                % (len(back), len(data), path))
        # 換名 + 登記綁成不可切開的一段:Ctrl-C 不可以卡在這兩件事中間,
        # 不然收尾會照舊狀態說「還沒有換過任何檔案」(理由見 _REPLACING)。
        _replace_and_register(tmp, path, '換成新的內容', '把它換成新的內容')
    except BaseException:
        # 接 BaseException 不是 Exception:Ctrl-C 與 SystemExit 都不是 Exception
        # 的子類,漏掉它們就會在玩家的資料夾裡留下暫存檔垃圾。清完照樣往上丟。
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ⚠️ 2026-09-05 再改一次:暫存檔的名字從**猜得到的** dst + '.part'
       換成 tempfile.mkstemp(dir=備份要放的那個資料夾)。理由與實測見
       _new_temp 與 _reject_symlink 的說明 —— 猜得到的名字可以被事先放上
       一個指向資料夾外面的符號連結,那樣被截斷的會是外面那個檔。
       同一輪也補上「備份寫完先 fsync,再跟來源對一次 SHA-256」:
       對不上就不換名,.fontbak 這個名字上永遠不會出現半截檔。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _reject_symlink(dst, '備份檔 %s' % dst)
    fd, part = _new_temp(dst, 'part')
    try:
        # 先整份複製到一個「別人不可能事先佔位」的暫存名字。
        # 被中斷的話髒掉的是那個暫存檔,不是 .fontbak,
        # 所以「備份已經存在」那個判斷永遠不會被半截檔騙到。
        with os.fdopen(fd, 'wb') as fo:
            with open(src, 'rb') as fi:
                shutil.copyfileobj(fi, fo)
            fo.flush()
            os.fsync(fo.fileno())
        shutil.copymode(src, part)
        # 備份是最後一道退路,所以不只比大小,整份對 SHA-256。
        if _sha256(src) != _sha256(part):
            raise DataError(
                '備份寫出去之後跟原檔對不起來(%s),沒有換上 %s。\n'
                '     磁碟可能滿了或有問題。原檔一個位元組都沒有動。'
                % (src, os.path.basename(dst)))
        # ⚠️ 這一行**沒有**包 _NoInterrupt,是刻意的:備份不進登記表
        #    (理由見 _WRITTEN 那一段),所以這裡沒有「換好了卻還沒登記到」
        #    這個窗口 —— 沒有窗口就沒有謊可以說。要包的是正本那兩處。
        os.replace(part, dst)          # os.replace 是原子的
    except BaseException:
        # 這裡接的是 BaseException 不是 Exception,
        # 因為 Ctrl-C(KeyboardInterrupt)與 SystemExit 都不是 Exception 的子類,
        # 漏掉它們就會在使用者的資料夾裡留下暫存檔垃圾。清完照樣往上丟。
        try:
            os.remove(part)
        except OSError:
            pass
        raise


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

    ⚠️ 2026-09-05 訂正:2026-08-30 那次補說明寫的是「本檔目前沒有任何地方呼叫
       這個函式」—— 那句話已經不成立了。這一支的 cmd_restore 從此走這一條,
       跟同一課的 mvp_fix_loc.py 一樣。在那之前它是直接把備份讀出來蓋回去的,
       實測拿截成八分之一的備份去 --restore,1,232,260 bytes 的正本被 159,917
       bytes 蓋掉、畫面照樣印「✅ 已還原」、備份還被刪掉,exit code 還是 0。
    """
    # 本檔開頭已經 import 過 struct,這裡再寫一次不影響行為;
    # 好處是這一整個函式可以原封不動複製到別支腳本,不必記得補 import。
    import struct
    bak, dst = os.fspath(bak), os.fspath(dst)
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
    # 拿它跟實際長度對。截斷的備份這一關一定過不了。
    # 大小端都收:同一個欄位在不同檔裡兩種寫法都出現過(見上面的實測數字)。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:.LOC 語系檔。它沒有「總長度」欄位可以對,所以改成順著結構走一遍:
    # 檔頭指到的 LOCL 在不在該在的位置、位移表有沒有被切掉、
    # 最後一條字串的位移有沒有超出檔尾。截斷之後最後那一條一定會指到檔案外面。
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
    # 每個節區記著它的內容在檔案裡從哪開始、有多長,最遠的那個不可以超出檔尾。
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
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _do_copy(bak, dst):
    """上面每一道把關都過了,這裡才真的把備份換回去 —— 而且是原子的。

    切成獨立函式是為了「只留一個出口」:每一條檢查路徑最後都得經過它,
    所以以後要加新的把關,只要確定加在 _do_copy 之前,就不可能漏掉哪一條。

    ⚠️ 2026-09-05 改掉的:這裡原本只有一行 shutil.copy2(bak, dst)。
       copy2 是**先把 dst 截成 0 bytes**再一段一段複製,所以複製途中磁碟滿、
       外接碟被拔掉、按了 Ctrl-C,玩家的遊戲檔就停在 0 bytes 或半截狀態 ——
       而前面那五道把關驗的是「備份好不好」,擋不住這一種。
       現在的順序是:同資料夾開唯一暫存檔 → 整份寫進去 → fsync →
       把正本的權限套上去 → 跟備份對 SHA-256 → 過了才 os.replace。
       任何一步失敗就把暫存檔刪掉,**正本維持原樣**,備份也還在。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _reject_symlink(dst, '要還原的 %s' % dst)
    fd, tmp = _new_temp(dst, 'restore')
    try:
        with os.fdopen(fd, 'wb') as fo:
            with open(bak, 'rb') as fi:
                shutil.copyfileobj(fi, fo)
            fo.flush()
            os.fsync(fo.fileno())
        if os.path.exists(dst):
            # 保留正本原本的權限(mkstemp 開出來的是 0600)。
            shutil.copymode(dst, tmp)
        want, got = _sha256(bak), _sha256(tmp)
        if want != got:
            raise DataError(
                '還原用的暫存檔跟備份對不起來,沒有換上去。\n'
                '     備份 %s\n     暫存 %s\n'
                '     磁碟可能滿了或有問題。%s 一個位元組都沒有動,備份也還在。'
                % (want, got, dst))
        _replace_and_register(tmp, dst, '已經還原成備份的內容',
                              '把它還原成備份的內容')     # 理由同 _atomic_write
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise




# 備份檔名 = 原檔名直接接上這個字尾(fonts.big → fonts.big.fontbak)。
# 本站每一支腳本用不同字尾,兩支工具才不會搶同一份備份。
BACKUP = '.fontbak'
# 重建 BIGF 時,目錄之後、每一段資料之間都補 0x00 到 4 的倍數。
# 名字沒改 ⇒ 目錄長度不變 ⇒ 第一筆資料的位移一定算出同一個數字,
# 這是 write_big 敢照原順序整份重寫的前提。
ALIGN = 4


class DataError(Exception):
    """「你的檔案或參數有問題」這一類、使用者看得懂的停止原因。

    main() 只接這一種和 FileNotFoundError,把它印成一行中文、回 exit code 2
    就結束。

    ⚠️ 但「不丟 traceback 就停下來」的路不只這兩條:參數打錯(例如
    --swap 後面漏了值)時 argparse 丟的是 SystemExit,它不經過 main() 那兩個
    except,用法由 Python 自己印到 stderr、回 exit code 2,一樣沒有 traceback。
    第三條是**什麼參數都不給**:2026-09-05 起遊戲資料夾是選填的(--selftest
    不需要它),所以那種情況變成 main() 自己印用法、回 exit code 1
    (2026-09-05 實測;在那之前是 argparse 說「缺 path」、回 2)。
    第四條是 --restore 遇到壞備份:_restore_from_backup 丟的也是 SystemExit,
    訊息印到 stderr、exit code 1,同樣沒有 traceback(2026-09-05 實測)。

    第五條是 Ctrl-C:main() 有接 KeyboardInterrupt,照「還沒動 / 正在換 / 已換」
    三態印一行中文說檔案動了沒有、回 exit code 130。

    正本或備份是符號連結時丟的是 DataError(exit code 2),跟壞備份那條
    (SystemExit / exit code 1)不同,因為它是「你的資料夾長得不對」,
    不是「備份壞了」。

    真正會印出完整 traceback 的,是這幾種以外的例外:那是程式的錯,
    不該包裝成一句好看的中文。
    """
    pass


# ─────────────────────────────────────────────────────────
#  BIGF
# ─────────────────────────────────────────────────────────

def _blob_map(raw, items, what):
    """把 read_big 的 items 壓成 {名字: 內容}。
    ⚠️ 同名項目會讓 dict 靜默覆蓋(後者蓋前者),所以這裡明確擋下來 ——
    正常的 fonts.big 沒有同名項目;會出現同名,是有人先改過名(例如把
    _jp 全改成 _en 之後多出兩個 dflt_en.ffn)。那種檔不該再餵進 --swap/--dedupe。"""
    # items 的每一筆是 [名字, 位移, 長度],位移與長度都是相對於整份 raw 的。
    # 這裡把它切成真正的位元組,之後的換字型與合併都只認名字、不再碰位移。
    seen, out = {}, {}
    for n, o, sz in items:
        if n in seen:
            raise DataError(
                '%s 裡有兩個同名項目 "%s" —— 這個檔改過名(或壞了),'
                '本工具不能對它做這個動作,否則會靜默丟掉其中一份。' % (what, n))
        seen[n] = True
        out[n] = raw[o:o + sz]
    return out


def read_big(path):
    """讀 BIGF 封裝檔的目錄。回傳 (整份位元組, 目錄, 目錄結束的位移)。

    BIGF 的檔頭固定 16 bytes,而且**同一個檔頭裡兩種位元組序都有**:

        位移 0x00   4 bytes   'BIGF' 這四個字
        位移 0x04   4 bytes   整個檔多長      小端序(本站量到手邊 5 份
                                              fonts.big 都是小端;
                                              專案另外量過的 295 個 BIGF 檔
                                              裡有 7 個是大端,所以還原那邊
                                              兩種都收)
        位移 0x08   4 bytes   裡面有幾個項目  大端序
        位移 0x0C   4 bytes   目錄之後的位置  大端序,本函式沒有用到。
                                              ⚠️ 這一格**不是**第一筆資料的位移。
                                              本站在這台開發機上找得到的 1,885 個
                                              BIGF 檔(含歷史資料與各種模組備份)
                                              全掃過一遍:1,885 個都夾在「目錄
                                              結束」與「第一筆資料的位移」之間,
                                              但真的等於第一筆資料的位移只有
                                              133 個。多出來的那一小截是目錄後面
                                              的尾標或補零:1,306 個是 8 個位元組
                                              的 L234 尾標、545 個是 3 個 0x00、
                                              8 個是 2 個 0x00、26 個什麼都沒有。
                                              要知道某一筆資料在哪,請讀那一筆
                                              自己寫在目錄裡的位移。

    目錄接在檔頭後面,一筆一筆排,每一筆長度不一樣:

        4 bytes 大端序   這筆資料在檔案裡的位移
        4 bytes 大端序   這筆資料的長度
        N bytes          名字,以一個 0x00 結尾

    因為名字長度不固定,只能一筆一筆往前走,不能用「第 k 筆 = 16 + k × 固定長」跳。

    名字用 latin-1 解碼而不是 utf-8:latin-1 把 0 到 255 每個位元組都對到
    一個字元、絕不丟例外,而且 encode 回去保證拿回原本那幾個位元組。
    字型名本來就是 ASCII,這樣寫只是讓奇怪的檔也不會卡在這一行。

    回傳的第三個值是目錄結束的位移。本檔所有呼叫端都用 _ 接走沒有在用,
    留著是因為它就是「第一筆資料最早可以放在哪」的下界。
    """
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:4] != b'BIGF':
        raise DataError('%s 開頭不是 BIGF' % os.path.basename(path))
    # 項目數在 +0x08,大端序;目錄從第 16 個位元組開始。
    count = struct.unpack('>I', raw[8:12])[0]
    items, p = [], 16
    for _ in range(count):
        # 先確定還剩得下 8 bytes 才解。壞檔在這裡停,比讀出一堆亂數位移好。
        if p + 8 > len(raw):
            raise DataError('目錄讀到一半就沒了')
        off, size = struct.unpack('>II', raw[p:p + 8])
        p += 8
        # 名字讀到第一個 0x00 為止。找不到 0x00 時 .index 會丟 ValueError,
        # 那代表檔案壞了;總比把後面幾 MB 都當成一個名字好。
        e = raw.index(b'\x00', p)
        items.append([raw[p:e].decode('latin-1'), off, size])
        p = e + 1
    return raw, items, p


def write_big(path, items, blobs):
    """照原順序重建。目錄長度不變(名字沒改),所以第一筆資料的位置也不變。

    流程:算出目錄要多長 → 先用 0x00 把檔頭那一段空出來 → 每一段資料依序
    接在後面(段與段之間補到 4 的倍數)並記下它落在哪 → 最後把檔頭連目錄
    整塊蓋回一開始空出來的那一段。要等資料都放完才知道位移,所以檔頭最後寫。

    ⚠️ 「位置不變」指的是**這支自己重跑幾次都一樣**(名字沒改 ⇒ 目錄長度
       不變 ⇒ 算出同一個 first)。跟 EA 原本打包出來的位置不保證相同:
       本站量到手邊那份中文 fonts.big(1,279,340 bytes、12 個項目)目錄結束
       在 266、第一筆資料放在 272,而這支會算出 268。差幾個位元組沒有影響,
       因為每一筆的位移都明明白白寫在目錄裡,遊戲照目錄找,不是照固定間距找。
       (同一份檔的 +0x0C 寫的是 269,266 與 272 都不是。那一格本來就不是
       「第一筆資料的位移」,見 read_big 的說明。)

    ⚠️ 這是「整份重打包」,不是接在檔尾。目錄指得到的每一段都會原樣寫回去,
       但**目錄指不到的位元組會不見**。本站 2026-08-30 量了手邊 5 份
       fonts.big:中文那 3 份(各 1,279,340 bytes)目錄指不到的只有 103 bytes
       而且全部是 0x00(對齊補的);2009 台灣模組那 2 份英文的
       (各 420,650 bytes)目錄指不到 207,698 bytes,其中 101,872 個不是 0。
       對後者做整份重打包,那 101,872 bytes 會消失。備份就是為了這種事。

    ⚠️ 檔頭 +0x04 的總長度寫**小端序**,而項目數、+0x0C 那一格、每一筆的
       (位移, 長度) 全部是**大端序**。同一個檔頭兩種位元組序不是筆誤,
       是照原檔的寫法。

    ⚠️ 2026-09-05 起最後那一步不是直接寫檔:整份組好之後交給 _atomic_write,
       先寫同資料夾的唯一暫存檔、fsync、讀回來逐位元組對過,才 os.replace
       換上去。中途壞掉的話玩家的 fonts.big 維持原樣,不會變成半截檔。
    """
    # 目錄長度 = 16 bytes 檔頭 + 每筆(8 bytes 的位移與長度 + 名字 + 1 個結尾 0x00)
    dirlen = 16
    for nm, _, _ in items:
        dirlen += 8 + len(nm) + 1
    # 第一筆資料從目錄之後、往上湊到 4 的倍數的地方開始
    first = (dirlen + ALIGN - 1) // ALIGN * ALIGN
    # 先用 0x00 把檔頭那一段佔起來,資料接在它後面長出去
    out = bytearray(first)
    offs = []
    for nm, _, _ in items:
        b = blobs[nm]
        # 接之前先記下「這一段會落在哪」,那就是等一下要寫進目錄的位移
        offs.append(len(out))
        out += b
        while len(out) % ALIGN:
            out += b'\x00'
    head = bytearray()
    head += b'BIGF'
    head += struct.pack('<I', len(out))          # 這個檔用小端序(照原檔)
    head += struct.pack('>I', len(items))        # 項目數:大端序
    # +0x0C 那一格的語意是「目錄區結束之後的位置」,不是「第一筆資料的位移」
    # (為什麼不是,見 read_big 的說明)。這支寫進去的是對齊後的 first:
    # 它不小於這份檔的目錄結束,又剛好等於第一筆資料真正的位移,
    # 兩種讀法都對得上,所以照樣寫得對。
    head += struct.pack('>I', first)             # +0x0C:大端序
    for (nm, _, _), o in zip(items, offs):
        head += struct.pack('>II', o, len(blobs[nm]))
        head += nm.encode('latin-1') + b'\x00'
    # 名字沒改 ⇒ head 的長度必定等於 dirlen ⇒ 一定塞得進前面空出來的 first bytes。
    # 這一行是就地覆蓋,不是插入,所以整份的長度不會因為寫檔頭而改變。
    out[:len(head)] = head
    # 不是 open(path, 'wb') —— 那一行執行的瞬間玩家的 fonts.big 就被截成 0。
    # _atomic_write 先寫同資料夾的暫存檔、讀回來對過,才 os.replace 換上去。
    _atomic_write(path, bytes(out))
    return len(out)


def write_big_dedup(path, items, blobs):
    """跟 write_big 一樣重建,但內容相同的項目只寫一份,多個目錄項指到同一個位移。

    BIGF 的目錄是 (位移, 長度, 名字),沒有任何地方規定兩個項目不能指到同一段資料。
    所以內容一模一樣的字型可以共用,而每個名字都還在、每個字都還在。
    回傳 (新檔長度, 省下的位元組, 共用分組)。

    跟 write_big 唯一的差別在中間那個迴圈:多一張「這段內容已經寫在哪」的表。
    分組直接拿 bytes 當 key,內容一模一樣的自然落到同一組,不必比檔名、
    也不必自己算雜湊(而且 bytes 相等就是逐位元組相等,不會有碰撞問題)。

    ⚠️ 對遊戲來說這是完全合法的檔:目錄怎麼寫,遊戲就怎麼讀。
       但它跟原檔已經不是同一種佈局了,所以一樣要靠備份才回得去。

    ⚠️ 它跟 write_big 一樣是「整份重打包」(out = bytearray(first) 之後,
       只有目錄指得到的段落會被接回去),所以 write_big 那一條
       「目錄指不到的位元組會不見」在這裡一模一樣成立,不是只有「檔案變小」。
       本站 2026-09-03 在同樣那 5 份 fonts.big 上量:中文那 3 份
       (各 1,279,340 bytes)合併後 911,368,少掉 367,972 bytes,其中 367,884
       是合併省下來的,另外 88 bytes 是目錄指不到的 0x00 與對齊的差;
       2009 台灣模組那 2 份英文的(各 420,650 bytes)合併後 198,448,
       少掉 222,202 bytes,其中只有 14,525 是合併省下來的,
       其餘 207,677 bytes 是目錄指不到的那一段跟對齊補的 0x00。

    ⚠️ 跟 write_big 一樣,2026-09-05 起走 _atomic_write:先寫暫存檔、對過,
       才換上去。
    """
    dirlen = 16
    for nm, _, _ in items:
        dirlen += 8 + len(nm) + 1
    first = (dirlen + ALIGN - 1) // ALIGN * ALIGN
    out = bytearray(first)
    where = {}           # 內容 -> 已經寫在哪
    offs = []
    groups = {}          # 內容 -> [名字, ...]
    for nm, _, _ in items:
        b = blobs[nm]
        groups.setdefault(b, []).append(nm)
        # 這段內容寫過了:目錄照樣多一筆,位移指回上一次寫的地方,資料不再寫第二份。
        if b in where:
            offs.append(where[b])
            continue
        where[b] = len(out)
        offs.append(len(out))
        out += b
        while len(out) % ALIGN:
            out += b'\x00'
    head = bytearray()
    head += b'BIGF'
    head += struct.pack('<I', len(out))
    head += struct.pack('>I', len(items))
    head += struct.pack('>I', first)
    for (nm, _, _), o in zip(items, offs):
        head += struct.pack('>II', o, len(blobs[nm]))
        head += nm.encode('latin-1') + b'\x00'
    out[:len(head)] = head
    _atomic_write(path, bytes(out))      # 理由同 write_big
    # 只留「有兩個以上名字共用」的組;省下的量 = 每組的內容長度 × (名字數 - 1),
    # 因為每一組還是要留一份。
    shared = {k: v for k, v in groups.items() if len(v) > 1}
    saved = sum(len(k) * (len(v) - 1) for k, v in shared.items())
    return len(out), saved, shared


def size_field_endian(raw):
    """檔頭 +0x04 的總長度欄位,不同檔可能是大端或小端。回傳 '<' 或 '>'。

    判法是「哪一種讀出來剛好等於檔案實際長度」,兩種都對不上就回小端。
    這種「用量的、不要用猜的」在這裡特別重要:同一個欄位在本站量過的
    BIGF 檔裡兩種寫法都出現過。

    ⚠️ 2026-08-30 補說明時查到:**本檔目前沒有任何地方呼叫它**
       (write_big 直接寫死小端,因為手邊 5 份 fonts.big 量到的都是小端)。
       留著是因為要處理 fonts.big 以外的 BIGF 檔時會需要它。
    """
    for e in ('<', '>'):
        if struct.unpack(e + 'I', raw[4:8])[0] == len(raw):
            return e
    return '<'


# ─────────────────────────────────────────────────────────
#  QFS 只需要解壓來讀字元數
# ─────────────────────────────────────────────────────────

def qfs_size(blob):
    """不解壓,直接讀 QFS 檔頭宣告的解開後大小(3 bytes 大端序)。

    QFS(EA 自家的 RefPack)開頭兩個位元組固定是 0x10 0xFB;
    緊接著第 2、3、4 個位元組是「解開之後有多大」,大端序、只有 3 bytes
    (所以這個欄位表示得了的上限是 16,777,215 bytes)。
    開頭不是 0x10 0xFB 就當成沒有壓縮,直接回傳它本身的長度。

    整支腳本要的只是「這個字型解開後佔多少」,所以**完全不需要解壓**:
    少寫一整套解壓器,也就少一種把資料弄壞的可能。

    ⚠️ 這是「檔案自己宣告的數字」,不是解壓算出來的。宣告值跟真的解出來
       不一樣時(檔案壞了),這裡看不出來。
    """
    if blob[:2] != b'\x10\xfb':
        return len(blob)
    return (blob[2] << 16) | (blob[3] << 8) | blob[4]


# ─────────────────────────────────────────────────────────
#  指令
# ─────────────────────────────────────────────────────────

def paths(root, src=None):
    """算出兩條路徑:要被改的那個檔,以及拿來換過去的來源檔。

    要被改的永遠是 <遊戲資料夾>/data/fonts/fonts.big,沒有第二個選擇。

    來源檔:有 --source 就用它,不再自己找。沒有就照下面那張清單找第一個存在的。
    順序不是隨便排的:
      · 英文語系排在中文語系前面,因為英文版是「不會當」的那一邊,
        換過去才是在減少變數
      · fonts 與 Fonts 兩種大小寫都試。中文化模組是在 Windows(檔名不分
        大小寫)做出來的,搬到 Mac 或 Linux 上大小寫就會咬人

    全部找不到時**不丟例外**,回傳中文語系那條**大寫 Fonts** 的路徑,讓呼叫端自己
    決定要怎麼辦:cmd_show 沒有來源檔照樣能列現況,cmd_swap 才需要停下來。

    ⚠️ 那條回傳值是上面清單的**第 4 條**,不是最後一條。五條還是全部都試過了,
       只是全部落空時挑了中文語系大寫 Fonts 那條當代表,而清單最後試的那條
       是中文語系小寫 fonts。在區分大小寫的檔案系統(Linux,或是格式化成
       區分大小寫的 macOS 磁碟)上,這兩條是不同的路徑。
       本站在 macOS 上拿這一支 mvp_font_swap.py 本身量過:給一個不存在的
       遊戲資料夾,paths() 回傳的來源檔是 data/中文語系/Fonts/fonts.big。
    """
    live = os.path.join(root, 'data', 'fonts', 'fonts.big')
    if src:
        return live, src
    # 來源字型:優先找英文語系那份(那是「不會當」的基準),
    # 找不到才退回中文語系。兩個資料夾大小寫在不同系統上可能不同,都試。
    for parts in (('data', '2023英文語系', 'fonts', 'fonts.big'),
                  ('data', '英文語系', 'fonts', 'fonts.big'),
                  ('data', '2023英文語系', 'Fonts', 'fonts.big'),
                  ('data', '中文語系', 'Fonts', 'fonts.big'),
                  ('data', '中文語系', 'fonts', 'fonts.big')):
        p = os.path.join(root, *parts)
        if os.path.isfile(p):
            return live, p
    return live, os.path.join(root, 'data', '中文語系', 'Fonts', 'fonts.big')


def cmd_show(root, src=None):
    """不加任何旗標時跑的就是這個:只讀、只印,一個位元組都不寫。

    左邊一欄是「現在用的那份 fonts.big 裡,每個字型解開後多大」,
    右邊是「來源檔裡同名字型解開後多大」,最後標出換過去會多還是會少。
    找不到來源檔就只印左邊:沒得比,但至少看得到現況。

    兩邊都用**解開後**的大小來比,不是用檔案裡壓縮後的長度。
    壓縮後的長度會被壓縮率影響,而真正吃記憶體的是解開後那一份。
    """
    live, cn = paths(root, src)
    if not os.path.isfile(live):
        raise DataError('找不到 %s' % live)
    raw, items, _ = read_big(live)
    print('  現在用的  %s' % live)
    print('  大小      %s bytes' % '{:,}'.format(len(raw)))
    print()
    # 這個變數叫 cn 是早期留下來的名字,不代表它一定指到中文語系那一份:
    # paths() 自動找來源時英文語系排在中文語系前面,所以這裡拿到的
    # 通常是英文版。指定了 --source 就是指定的那一份。
    have_cn = os.path.isfile(cn)
    cnitems = {}
    if have_cn:
        craw, citems, _ = read_big(cn)
        cnitems = {n: craw[o:o + s] for n, o, s in citems}
        print('  來源字型  %s' % cn)
        print('  大小      %s bytes' % '{:,}'.format(len(craw)))
    else:
        print('  ⚠️ 找不到來源字型檔（%s）' % cn)
        print('     沒有它就沒得比,只能列出現況。')
    print()
    print('  %-16s %12s %12s %s' % ('字型', '現在(解開後)', '來源(解開後)', ''))
    print('  ' + '-' * 56)
    tot = 0
    for nm, off, size in items:
        # 照目錄記的位移與長度切出這一段,再問 QFS 檔頭它解開後有多大。
        blob = raw[off:off + size]
        a = qfs_size(blob)
        tot += a
        # 來源檔裡沒有同名字型就留白,不要猜、也不要拿別的字型湊。
        b = qfs_size(cnitems[nm]) if nm in cnitems else None
        mark = ''
        if b is not None and b > a:
            mark = '  ← 換過去會大 %s' % '{:,}'.format(b - a)
        elif b is not None and b < a:
            mark = '  ← 換過去會省 %s' % '{:,}'.format(a - b)
        print('  %-16s %12s %12s%s' % (nm, '{:,}'.format(a),
                                       '{:,}'.format(b) if b is not None else '—', mark))
    print('  ' + '-' * 56)
    print('  %-16s %12s' % ('解開後合計', '{:,}'.format(tot)))
    if cnitems:
        ct = sum(qfs_size(v) for v in cnitems.values())
        print('  %-16s %12s  （差 %s）' % ('來源合計', '{:,}'.format(ct),
                                          '{:+,}'.format(ct - tot)))


def cmd_swap(root, names, apply_it, src=None):
    """把指定的字型換成來源檔裡的版本。

    名字用「底線前面那一段」比對,而且不分大小寫:檔案裡叫 au20b_en.ffn,
    你只要打 au20b。這樣指令才能照著上面那張表打,不用去記字尾。
    打完整的名字(au20b_en.ffn)也認,那是同一個前綴命中兩筆時唯一問得清楚的講法。

    沒加 --apply 就只印預覽。加了才會:擋掉符號連結 → 備份(只在第一次)→
    整份重寫(先寫暫存檔、對過才 os.replace 換上去)→ 重讀複驗。
    順序不能換,備份一定要在寫之前。
    """
    live, cn = paths(root, src)
    if not os.path.isfile(cn):
        raise DataError('找不到來源字型檔:%s\n     用 --source 指定' % cn)
    raw, items, _ = read_big(live)
    craw, citems, _ = read_big(cn)
    # 兩份都攤成 {名字: 內容}。_blob_map 會擋掉同名項目(理由見它的說明)。
    # 注意這裡把參數 src 從「來源檔路徑」改指向「來源檔的內容表」,
    # 上面 paths() 已經用完它了。
    src = _blob_map(craw, citems, os.path.basename(cn))
    blobs = _blob_map(raw, items, os.path.basename(live))
    live_names = {n for n, _, _ in items}
    changed = []
    for want in names:
        # 底線前面那一段當作字型名(au20b_en.ffn → au20b),大小寫不計。
        # 一定要排序:live_names 是 set,不排序的話 hit[0] 取到哪一筆會跟著
        # Python 的字串雜湊隨機化跑,同一行指令跑兩次可能換掉不同的字型。
        # 這不是假想:剛安裝好的原版中文版那份 fonts.big(1,683,513 bytes /
        # 13 項)裡 dflt_en.ffn 與 dflt_jp.ffn 並存,前綴「dflt」就命中兩筆。
        # 2026-09-05 在暫存複本上拿它實測修之前的版本,同一行 --swap dflt:
        # PYTHONHASHSEED=2 與 8 印「dflt_en.ffn 兩邊本來就一樣,跳過」,
        # 另外六個 seed 印「來源檔裡沒有 dflt_jp.ffn」。
        # 二分測試靠的就是「同一步重跑結果一樣」,這種不確定性不能留。
        # 完整名字也收(n.lower() == want.lower()),否則下面那句「請把完整名字
        # 打出來」是句做不到的建議 —— 前綴比對認不出 twc14_jp.ffn。
        hit = sorted(n for n in live_names
                     if n.split('_')[0].lower() == want.lower()
                     or n.lower() == want.lower())
        if not hit:
            raise DataError('這個檔裡沒有叫 "%s" 的字型。可用的:%s'
                            % (want, ', '.join(sorted(n.split('_')[0] for n in live_names))))
        if len(hit) > 1:
            # 猜錯就是換掉玩家不想換的那個字型,而且它自己不會知道。
            raise DataError('"%s" 在這個檔裡命中 %d 個字型(%s)——'
                            '不敢替你猜是哪一個,請把完整名字打出來。'
                            % (want, len(hit), ', '.join(hit)))
        nm = hit[0]
        if nm not in src:
            raise DataError('來源檔裡沒有 %s' % nm)
        # 兩邊逐位元組相同就跳過。沒有效果的改動不值得動檔案,
        # 更不值得為它生出一份備份、把「最早那一份原檔」的位置佔掉。
        if blobs[nm] == src[nm]:
            print('  · %s 兩邊本來就一樣,跳過' % nm)
            continue
        before, after = qfs_size(blobs[nm]), qfs_size(src[nm])
        blobs[nm] = src[nm]
        changed.append((nm, before, after))
    if not changed:
        print('\n  沒有東西需要換。\n')
        return
    if not apply_it:
        print()
        for nm, b4, af in changed:
            print('  會換掉 %-16s 解開後 %s → %s  (%s)' %
                  (nm, '{:,}'.format(b4), '{:,}'.format(af), '{:+,}'.format(af - b4)))
        total = sum(qfs_size(v) for v in blobs.values())
        print()
        print('  換完之後解開後合計會是 %s bytes' % '{:,}'.format(total))
        print('     （全英文 777,520 能玩 · 全中文 2,726,912 當機）')
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要換的話,在剛才那一行最後面加上 --apply')
        return
    # 備份只在第一次做。第二次執行時 .fontbak 裡放的仍然是「最原始那一份」,
    # 而不是上一次改完的結果,所以 --restore 一定回得到原點。
    bak = live + BACKUP
    # 兩個都要擋:正本是符號連結的話,寫下去改到的是連結另一頭那個檔;
    # 備份的名字是符號連結的話,備份會落到別的地方,而且下一次 --restore
    # 會從那裡讀。擋在 _atomic_copy 之前,所以擋下來的時候什麼都還沒發生。
    _reject_symlink(live, live)
    _reject_symlink(bak, '備份檔 %s' % bak)
    # 上一行已經把「是符號連結」那一種擋掉了,所以這裡 exists 與 lexists 同義。
    if not os.path.exists(bak):
        _atomic_copy(live, bak)
        print('  已備份 → %s' % os.path.basename(bak))
    newlen = write_big(live, items, blobs)
    print()
    for nm, a, b in changed:
        print('  換掉 %-16s 解開後 %s → %s  (%s)' %
              (nm, '{:,}'.format(a), '{:,}'.format(b), '{:+,}'.format(b - a)))
    print()
    # ⭐ 二分測試要記的是「解開後合計」不是檔案大小:檔案大小被壓縮率影響,
    #    吃記憶體的是解開後那一份。兩個數字都印,是為了讓你看見它們會分家。
    total = sum(qfs_size(v) for v in blobs.values())
    print('  檔案 %s → %s bytes' % ('{:,}'.format(len(raw)), '{:,}'.format(newlen)))
    print('  ⭐ 解開後合計 %s bytes  ← 這個數字是二分測試要記的' % '{:,}'.format(total))
    print('     （全英文 777,520 能玩 · 全中文 2,726,912 當機）')
    # 複驗:把剛寫出去的檔重讀一次,項目數、每個名字的順序、每一段內容
    # 全部逐位元組對一遍。「寫完就當作成功」是這類工具最常見的謊,
    # 而這個檔案是玩家的遊戲資料,不能靠猜的。
    r2, i2, _ = read_big(live)
    ok = len(i2) == len(items)
    for (n1, _, _), (n2, o2, s2) in zip(items, i2):
        if n1 != n2 or r2[o2:o2 + s2] != blobs[n1]:
            ok = False
            break
    if not ok:
        # 複驗沒過就不能往下走:這個檔現在是壞的,不可以叫人拿它進遊戲,
        # 也不可以回 exit code 0 —— .bat / .command / 幫別人代跑的包裝
        # 都是看 exit code 判斷成敗的。
        raise DataError(
            '寫出去的 fonts.big 跟記憶體裡的對不上,這個檔現在是壞的。\n'
            '     不要拿它進遊戲。先還原回原點再回報:\n'
            '     python3 %s "%s" --restore'
            % (os.path.basename(__file__), root))
    print('  複驗:%d 個項目全部逐位元組相同 ✅' % len(i2))
    print()
    print('  進遊戲用那座會當的球場試一次。沒改善就還原:')
    print('    python3 %s "%s" --restore' % (os.path.basename(__file__), root))


def cmd_dedupe(root, apply_it):
    """把 fonts.big 裡內容相同的字型合併成共用一份。目錄裡的字型一個都不會少。

    做這件事的用意不是省硬碟,是做對照實驗:
    它讓「檔案變小」而「解開後的字型資料總量完全不變」。
    如果當機的上限卡在檔案大小,這樣就會好;卡在解開後的資料,就不會好。
    兩種結果都告訴我們答案在哪一層。

    ⚠️ 「檔案變小」不等於「只有重複的那幾份被拿掉」:它走的 write_big_dedup
       跟 write_big 一樣是整份重打包,目錄指不到的位元組會一起不見。
       本站 2026-09-03 量手邊那 2 份 2009 台灣模組英文版 fonts.big
       (各 420,650 bytes):合併後 198,448,少掉 222,202 bytes,
       其中只有 14,525 是合併省下來的。所以備份不是客套話。

    ⚠️ 2026-09-05 修掉的:**這條路在那之前一執行就 NameError。**
       下面第三行原本寫 paths(root, src),而 src 這個名字在這個函式裡不存在
       (只有 cmd_swap 有)。要講清楚的是它**不是「連檔案都還沒讀到」就停**:
       前一行的 read_big(live) 已經把整份 fonts.big 讀進記憶體、目錄也解完了。
       本站當時拿三份不同的 fonts.big 各實跑一次:剛安裝好的原版英文那份
       204,820 bytes / 12 個項目、2009 台灣模組英文那份 420,650 bytes /
       12 個項目、剛安裝好的中文版那份 1,683,513 bytes / 13 個項目,
       三次都停在 blobs = _blob_map(...) 那一行。不過從進函式到那一行只有讀
       沒有寫,備份與寫回都排在更後面,所以三次跑完那個 fonts.big 都跟跑
       之前逐位元組相同、也沒有留下 .fontbak:它確實沒有弄壞任何東西,
       只是做不到。修法是把那一行要的檔名直接用 live(paths() 回傳的第一個
       值就是它)。

    ⚠️ 同一輪補上的另一件事:**這條路的 --apply 以前沒有複驗。**
       cmd_swap 寫完會把檔案重讀一次、逐項逐位元組對一遍,再印「複驗:…」;
       這裡以前寫完只印「合併的組 / 檔案大小 / 解開後總量 / 字型數量」就結束,
       不重讀、不比對,對不上也不會叫你回報。現在兩條 --apply 的保證一樣了:
       合併之後好幾個目錄項會指到同一個位移,複驗順便證明那些位移都指對了。
    """
    live, _ = paths(root)
    raw, items, _ = read_big(live)
    # ⚠️ 2026-09-05 修掉的 NameError 就在這一行:原本寫的是
    #    os.path.basename(paths(root, src)[0]),而這個函式裡根本沒有 src
    #    這個名字(cmd_swap 才有)。要的只是「檔名拿來寫在錯誤訊息裡」,
    #    而 paths() 回傳的第一個值就是 live,直接用它。
    blobs = _blob_map(raw, items, os.path.basename(live))

    # 先看有沒有得省。沒有就不要動檔案。
    # 分組直接拿內容(bytes)當 key:一模一樣的自然落到同一組,
    # 不必比名字、也不必自己算雜湊,而且 bytes 相等就是逐位元組相等。
    groups = {}
    for nm, _, _ in items:
        groups.setdefault(blobs[nm], []).append(nm)
    shared = {k: v for k, v in groups.items() if len(v) > 1}
    if not shared:
        print('\n  這份 fonts.big 裡沒有內容重複的字型,沒有東西可以合併。\n')
        return

    if not apply_it:
        print()
        print('  可以合併的組:')
        for content, names in sorted(shared.items(), key=lambda kv: -len(kv[0])):
            print('    %-52s 各 %s bytes,留一份' %
                  (' = '.join(names), '{:,}'.format(len(content))))
        saved = sum(len(k) * (len(v) - 1) for k, v in shared.items())
        print()
        # ⚠️ 下面印出來的 saved 只算「合併省下來的」,不是檔案實際會少的量。
        #    write_big_dedup 是整份重打包,目錄指不到的位元組會一起不見:
        #    本站 2026-09-03 量 2009 台灣模組那份英文 fonts.big(420,650 bytes),
        #    這裡會印 14,525,而檔案實際少 222,202;中文那份(1,279,340 bytes)
        #    是印 367,884 而實際少 367,972。
        #    這句話原本只講 saved,所以下面把落差當場印出來,
        #    免得玩家拿預覽的數字去對合併後的檔案大小。
        print('  合併重複的字型會少 %s bytes,解開後總量完全不變,字型一個都不少。'
              % '{:,}'.format(saved))
        print('  ⚠️ 但這是整份重打包,目錄指不到的位元組會一起不見,')
        print('     所以檔案實際少掉的可能遠多於上面那個數字。動手前先備份。')
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要合併的話,在剛才那一行最後面加上 --apply')
        return

    # 跟 cmd_swap 同一個規矩:備份只做第一次,沿用的那一份才是最原始的檔。
    bak = live + BACKUP
    _reject_symlink(live, live)                      # 理由同 cmd_swap
    _reject_symlink(bak, '備份檔 %s' % bak)
    if not os.path.exists(bak):
        _atomic_copy(live, bak)
        print('\n  已備份原檔 → %s' % os.path.basename(bak))
    else:
        print('\n  已經有備份了,沿用 → %s' % os.path.basename(bak))

    before = len(raw)
    after, saved, shared = write_big_dedup(live, items, blobs)

    # 複驗(2026-09-05 補的,在這之前這條路寫完就結束):把剛換上去的檔重讀一次,
    # 項目數、每個名字的順序、每一段內容全部逐位元組對一遍。
    # 合併之後好幾個目錄項會指到同一個位移,這一關順便證明那些位移都指對了。
    r2, i2, _ = read_big(live)
    ok = len(i2) == len(items)
    if ok:
        for (n1, _o1, _s1), (n2, o2, s2) in zip(items, i2):
            if n1 != n2 or r2[o2:o2 + s2] != blobs[n1]:
                ok = False
                break
    if not ok:
        raise DataError(
            '合併之後寫出去的 fonts.big 跟記憶體裡的對不上,這個檔現在是壞的。\n'
            '     不要拿它進遊戲。先還原回原點再回報:\n'
            '     python3 %s "%s" --restore'
            % (os.path.basename(__file__), root))

    print('\n  合併的組:')
    for content, names in sorted(shared.items(), key=lambda kv: -len(kv[0])):
        print('    %-52s 各 %s bytes,留一份' %
              (' = '.join(names), '{:,}'.format(len(content))))
    # 三個數字一起印,才看得出這次實驗到底改了什麼:
    # 檔案變小、解開後總量完全沒變、字型數量一個沒少。
    # 注意「檔案大小」那一行印的是 before - after,也就是實際差額:
    # 裡面除了合併省下來的,還含目錄指不到的位元組(整份重打包會一起丟掉)
    # 跟對齊的差,所以它會大於上面預覽那一行印的 saved。
    print()
    print('  檔案大小   %s → %s  (少了 %s,%.1f%%)' %
          ('{:,}'.format(before), '{:,}'.format(after),
           '{:,}'.format(before - after), (before - after) * 100.0 / before))
    dec = sum(qfs_size(b) for b in blobs.values())
    print('  解開後總量 %s → %s  (完全沒變)' %
          ('{:,}'.format(dec), '{:,}'.format(dec)))
    print('  字型數量   %d → %d  (一個都沒少)' % (len(items), len(items)))
    print('  複驗:%d 個項目全部逐位元組相同 ✅' % len(i2))
    print()
    print('  還原:--restore\n')


def cmd_restore(root):
    """把 .fontbak 蓋回 fonts.big,比對過了才把備份檔刪掉。

    刪備份是刻意的:留著會讓下一次 --swap 誤以為「已經備份過了」而沿用一份
    已經沒有意義的檔。還原完等於回到出發點,下一次改會重新備份一次。
    但**要等比對過了才刪**:比對沒過就代表這次還原失敗,備份是唯一的退路,
    這種時候把它刪掉等於斷了自己的後路。

    順序是三步,不能換:
      1. _restore_from_backup —— 先驗備份再覆寫。0 bytes、BIGF 檔頭宣告長度
         跟實際長度對不上(截斷一定對不上)都會被擋下來,而且**擋下來的時候
         正本一個位元組都不會動**,備份也還留著。
         驗過之後真正的覆寫走 _do_copy,它是原子的:先寫同資料夾的唯一暫存檔、
         fsync、跟備份對 SHA-256,過了才 os.replace。所以覆寫途中被中斷,
         正本停在**舊的完整內容**,不會停在半截(2026-09-05 之前那一行是
         shutil.copy2,copy2 會先把正本截成 0)。
      2. 逐位元組比對 —— 兩邊整份讀出來比,不是比大小、也不是 zip 邊比邊停。
      3. 過了才刪備份、才印成功;比對沒過就留著備份、丟 DataError(exit code 2)。
         (第 1 步就被擋下來的那一種丟的是 SystemExit,訊息走 stderr、exit code 1。)

    ⚠️ 2026-09-05 之前這裡是直接把備份讀出來蓋回去、蓋完立刻刪備份的,
       沒有第 1 步也沒有第 2 步。實測拿截成八分之一的備份去 --restore:
       1,232,260 bytes 的正本被 159,917 bytes 蓋掉,畫面照樣印「✅ 已還原」、
       exit code 0,而且備份也一起沒了 —— 沒有第二次機會。修法是把
       本檔上面早就寫好、卻一個呼叫點都沒有的 _restore_from_backup 接上去。
    """
    live, _ = paths(root)
    bak = live + BACKUP
    # 先擋符號連結再問「在不在」:os.path.exists 對「指到不存在的檔的符號連結」
    # 回 False,只用它的話,那種備份會被說成「找不到備份」而不是被指出來。
    _reject_symlink(bak, '備份檔 %s' % bak)
    _reject_symlink(live, live)
    if not os.path.exists(bak):
        raise DataError('找不到備份 %s' % os.path.basename(bak))
    # 壞備份在這裡就會被擋下來(丟 SystemExit),下面兩行走不到,
    # 所以正本不會被蓋、備份也不會被刪。
    _restore_from_backup(bak, live)
    # 比完整長度,不用 zip:zip 會在短的那一邊停,備份被截斷時它反而看不出來。
    with open(bak, 'rb') as f:
        want = f.read()
    with open(live, 'rb') as f:
        got = f.read()
    if got != want:
        raise DataError(
            '還原之後 fonts.big 跟備份對不上(備份 %s bytes、現在 %s bytes)。\n'
            '     備份沒有刪,還留在 %s —— 請不要再動它,直接回報。'
            % ('{:,}'.format(len(want)), '{:,}'.format(len(got)),
               os.path.basename(bak)))
    os.remove(bak)
    print('\n  ✅ 已還原 fonts.big(%s bytes,與備份逐位元組相同),備份檔已移除。\n'
          % '{:,}'.format(len(got)))


def main():
    """把命令列參數接成一個動作,並且把例外翻成一行中文。

    判斷順序是 --restore → --dedupe → --swap → 什麼都沒加(只看現況)。
    一次只做一件事,所以同時加兩個旗標時,排在前面的贏。
    --apply 不是動作,是「--dedupe / --swap 要不要真的寫檔」的開關;
    單獨加 --apply 會走到「只看現況」那一條,什麼都不會被寫。
    ⚠️ 它管不到 --restore。--restore 排在最前面而且自己就會寫檔,
       不加 --apply 一樣會把 .fontbak 蓋回去、蓋完再把備份刪掉。

    exit code:0 成功、1 是什麼參數都沒給(印用法)、2 是檔案或參數有問題、
    130 是被 Ctrl-C 中斷。壞備份被 _restore_from_backup 擋下來是 1
    (它丟的是 SystemExit,走在 main 的 except 外面)。

    ⚠️ 130 那一條會**先看檔案到底動了沒有**再決定講什麼,而且看的是三態:
    _REPLACING(正在換)與 _WRITTEN(已換)兩張表都空的,才說「什麼都沒有動到」。
    _WRITTEN 只有 os.replace 真的做完才會有東西進去,不是「開始寫了」就記;
    _REPLACING 是「換名做到一半」的中間態,2026-09-06 補的 —— 在那之前,
    Ctrl-C 剛好落在 os.replace 與登記那一行中間的話,這裡會照舊狀態說
    「還沒有換過任何檔案」,而檔案其實已經換過了(實測:對變體檔跑真實的
    --swap --apply,exit code 130、印「跟動手前一模一樣」,正本 SHA-256 卻變了)。
    現在那兩行被 _NoInterrupt 綁成一段,中間態則是連 _NoInterrupt 都裝不上時的保險。
    說錯成沒動而其實動了,玩家就不會去還原。

    只接 DataError 與 FileNotFoundError 兩種例外,它們代表「你的檔案或參數
    有問題」,印一行中文、回 exit code 2。

    ⚠️ 不是「這兩種一行中文 / 其他全部 traceback」的二分法:參數打錯時 argparse
    丟的 SystemExit 走在這兩個 except 外面,用法由 Python 自己印到 stderr、
    回 exit code 2,也不會有 traceback。什麼參數都不給則是 main() 自己印用法、
    回 exit code 1(2026-09-05 起遊戲資料夾是選填的,因為 --selftest 不需要它;
    在那之前是 argparse 說「缺 path」、回 2)。本檔上面那個
    _restore_from_backup() 丟的也是 SystemExit,cmd_restore 從 2026-09-05 起
    會呼叫它,所以壞備份走的是這一條:訊息印到 stderr、exit code 1、
    沒有 traceback(實測)。

    這幾種以外的例外才會丟出完整 traceback:那是程式的錯,不該被包裝成一句
    好看的中文而讓人以為是自己弄錯。
    """
    # 這一段會原封不動印在 --help 最後面(要靠 RawDescriptionHelpFormatter,
    # 預設的格式器會把換行與縮排吃掉)。二分測試的做法寫在腳本自己的說明裡
    # 而不是只寫在網頁上,是為了讓「只拿到這支檔」的人也知道該怎麼用。
    EPILOG = """
二分測試的做法（每一步都可逆）:

  1. 先看現況
     python3 mvp_font_swap.py "<遊戲資料夾>"

  2. 從「沒有中文的那幾個」開始換成來源檔裡的版本,看會不會當
     (沒指定 --source 時,自動找的順序是英文語系排在中文語系前面,
      所以找得到英文語系那一份時,這一步換過去的是英文版。
      本站在測試機那份中文化 fonts.big 上量到這三個都不含中文,
      換掉不會少任何一個中文字)

     先預覽(不會動到任何檔案):
     python3 mvp_font_swap.py "<遊戲資料夾>" --swap au20b,Tw24,dflt

     看過預覽沒問題,同一行最後面加上 --apply 才真的換:
     python3 mvp_font_swap.py "<遊戲資料夾>" --swap au20b,Tw24,dflt --apply

  3. 再把真正的那六個中文字型也換成來源檔裡的版本
     (來源是英文版的話,這一步會讓中文暫時消失。
      它是拿來確認兇手在不在這六個裡面,測完用第 4 步還原)

     先預覽:
     python3 mvp_font_swap.py "<遊戲資料夾>" --swap frk12,twc14,twc16,twc18,twcnb,twn14

     確定了再加 --apply:
     python3 mvp_font_swap.py "<遊戲資料夾>" --swap frk12,twc14,twc16,twc18,twcnb,twn14 --apply

  4. 還原
     python3 mvp_font_swap.py "<遊戲資料夾>" --restore

⚠️ 一次只加一組,加完就進遊戲測。一次全換就分不出是哪一個。
"""
    # Windows 繁體中文(cp950)把輸出導到檔案或管線時,Python 會改用地區編碼,
    # 而 ⭐ ✅ ❌ ⚠️ 這幾個字元 cp950 編不出來。實測(PYTHONIOENCODING=cp950):
    # --swap --apply 在**檔案已經寫完之後、印複驗之前**以 UnicodeEncodeError 收場;
    # --restore 是還原做完了才炸;連 --help 都印不完。訊息殘缺成 ? 可以接受,
    # 已經動過檔的流程崩在最後一行不行 —— 使用者會誤判成敗。
    # 這一段要排在 ArgumentParser 之前,--help 的內容才蓋得到。
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors='replace')   # TextIOWrapper.reconfigure 是 3.7 起有的
        except Exception:
            # 被導到不是 TextIOWrapper 的東西時沒有這個方法。
            # 這裡是「錦上添花」的保護,失敗就照舊,不能反過來害腳本開不起來。
            pass
    ap = argparse.ArgumentParser(
        description='一個一個換字型,找出是哪一個把記憶體吃爆',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)
    # nargs='?' 是為了 --selftest:它不需要遊戲資料夾。
    # 兩個都沒給就印用法、回 exit code 1(跟「檔案有問題」的 2 分開)。
    ap.add_argument('path', nargs='?', help='遊戲安裝資料夾（它的下一層才是 data）')
    ap.add_argument('--swap', metavar='名字,名字',
                    help='把這些字型換成來源檔裡的版本（逗號分隔,不用寫 _en.ffn。'
                         '沒指定 --source 時自動找,英文語系排在中文語系前面）')
    ap.add_argument('--restore', action='store_true', help='還原 fonts.big')
    ap.add_argument('--apply', action='store_true', help='真的寫入（沒加就只是預覽）')
    # ⚠️ 下面那句「只是檔案變小」講的是字型內容:合併之後每個名字、每個字都還在。
    #    但它不代表檔案只少掉重複的那幾份:write_big_dedup 是整份重打包,
    #    目錄指不到的位元組會一起不見,數字寫在 write_big_dedup 的說明裡。
    ap.add_argument('--dedupe', action='store_true',
                    help='內容相同的字型合併成共用一份（字型一個都不會少;但它是整份'
                         '重打包,目錄指不到的位元組會一起不見,檔案少掉的會多於合併'
                         '省下來的）')
    ap.add_argument('--source', metavar='檔案',
                    help='來源 fonts.big（不指定就自動找 2023英文語系 / 中文語系）')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試,不碰任何遊戲檔（自己造一份最小的 BIGF 來測）')
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.path:
        ap.print_help()
        return 1
    try:
        if args.restore:
            cmd_restore(args.path)
        elif args.dedupe:
            cmd_dedupe(args.path, args.apply)
        elif args.swap:
            cmd_swap(args.path, [x.strip() for x in args.swap.split(',') if x.strip()],
                     args.apply, args.source)
        else:
            print()
            cmd_show(args.path, args.source)
            print()
        return 0
    except DataError as e:
        print('\n  停下來了：%s\n' % e)
        return 2
    except FileNotFoundError as e:
        print('\n  找不到檔案：%s\n' % e)
        return 2
    except PermissionError as e:
        # 資料夾唯讀(或檔案被別的程式鎖住)是「你的環境」的問題,不是程式的錯,
        # 所以印一行中文而不是丟 traceback。動了沒有一樣看 _WRITTEN,不用猜的。
        print('\n  沒有權限寫入：%s' % e)
        print('     那個資料夾或檔案是唯讀的,或者被別的程式鎖住了。')
        if _REPLACING:
            # 三態的中間那一態:停下來的時候正在換名,不知道換完了沒有,
            # 只能照實說,不可以說「一個位元組都沒有動」(見 _REPLACING)。
            for p, why in _REPLACING:
                print('     ⚠️ 停下來的時候正在%s,不確定換完了沒有:%s' % (why, p))
        if _WRITTEN:
            for p, why in _WRITTEN:
                print('     ⚠️ 但這個檔已經動過了:%s —— %s' % (p, why))
        elif not _REPLACING:
            print('     你的遊戲檔一個位元組都沒有動。')
        print()
        return 2
    except KeyboardInterrupt:
        # 按 Ctrl-C 之後最需要知道的一件事是「我的遊戲檔到底動了沒有」。
        # 猜不得:說錯成「什麼都沒動」而其實動了,玩家就不會去還原。
        # 所以看的是三態(見 _REPLACING 那一段):_REPLACING 有東西就是
        # 「正在換」,那種時候**不可以**說沒動到;兩張表都空才可以。
        print()
        if _REPLACING:
            # 正常情況這裡永遠是空的(換名與登記被 _NoInterrupt 綁在一起);
            # 它不是空的,代表連 _NoInterrupt 都沒裝上,那就不可以猜。
            print('  ⏹ 中斷了,而且中斷的時候**正在替換**下面這個檔:')
            for p, why in _REPLACING:
                print('     %s —— 正在%s' % (p, why))
            print('     換名本身是原子的,所以它要嘛還是舊的、要嘛已經是新的,')
            print('     不會是半截 —— 但這裡分不出是哪一種。請還原,或自己')
            print('     跟 %s 那份備份比對過再繼續:' % BACKUP)
            print('     python3 %s "%s" --restore'
                  % (os.path.basename(__file__), args.path))
            if _WRITTEN:
                print('     另外下面這些已經換過了:')
                for p, why in _WRITTEN:
                    print('     %s —— %s' % (p, why))
            print()
            return 130
        if _WRITTEN:
            print('  ⏹ 中斷了,但**檔案已經動過了**:')
            for p, why in _WRITTEN:
                print('     %s —— %s' % (p, why))
            if any(w == '換成新的內容' for _p, w in _WRITTEN):
                print('     要回到原點:')
                print('     python3 %s "%s" --restore'
                      % (os.path.basename(__file__), args.path))
            else:
                print('     還原本身已經做完了,檔案就在原點,不必再跑一次。')
                print('     (備份檔還在不在,看上面那個資料夾裡的 %s)' % BACKUP)
        else:
            print('  ⏹ 中斷了。還沒有換過任何檔案,你的遊戲檔跟動手前一模一樣。')
            print('     (寫到一半的暫存檔已經清掉;備份 .fontbak 如果生出來了會留著,')
            print('      它是完整的,下一次執行會沿用。)')
        print()
        return 130



def _fake_big(entries):
    """造一份最小的 BIGF 給 --selftest 用。entries = [(名字, 內容), ...]

    佈局跟 write_big 算出來的一模一樣(目錄長度 → 對齊到 4 的倍數 → 資料接在
    後面,段與段之間補 0x00),所以 read_big 讀得出來。
    自己造是刻意的:自我測試一個遊戲檔都不碰。
    """
    dirlen = 16
    for nm, _b in entries:
        dirlen += 8 + len(nm) + 1
    first = (dirlen + ALIGN - 1) // ALIGN * ALIGN
    out = bytearray(first)
    offs = []
    for _nm, b in entries:
        offs.append(len(out))
        out += b
        while len(out) % ALIGN:
            out += b'\x00'
    head = bytearray()
    head += b'BIGF'
    head += struct.pack('<I', len(out))
    head += struct.pack('>I', len(entries))
    head += struct.pack('>I', first)
    for (nm, b), o in zip(entries, offs):
        head += struct.pack('>II', o, len(b))
        head += nm.encode('latin-1') + b'\x00'
    out[:len(head)] = head
    return bytes(out)


def _junk(d):
    """那個資料夾裡有沒有本工具留下來的暫存檔。成功或失敗都不該留下任何一個。"""
    return sorted(n for n in os.listdir(d)
                  if '.part-' in n or '.new-' in n or '.restore-' in n)


def selftest():
    """--selftest:自己造一份最小的 BIGF 來測,完全不碰遊戲檔。

    正向(先證明「正常流程真的做得到承諾的事」;少了正向,反向餌可能只是
    「整支都壞了」才過的):
      · 造出來的 BIGF 讀得出來,名字與內容都對
      · --swap --apply 換得動、備份是原檔、複驗那一關真的跑過
      · --restore 之後逐位元組回到原本的樣子,備份檔被刪掉
      · --dedupe --apply 合併得動,字型數量與解開後總量都沒變
        (這條同時是 2026-09-05 修掉的那個 NameError 的回歸測試)
      · 每一次成功的操作之後,資料夾裡不可以留下任何暫存檔

    反向餌(故意做一件必須失敗的事,或故意佈一個陷阱看防線咬不咬得住):
      1. 事先在**舊版猜得到的暫存名字** <備份>.part 上放一個指向資料夾外面的
         符號連結 —— 跑完 --swap --apply,外面那個檔必須一個位元組都沒變
         (2026-09-05 改用 tempfile.mkstemp 之前,這裡會把外面那個檔截斷)
      2. 同樣的陷阱放在 <正本>.part 上,一樣不可以被寫到
      3. 正本本身是符號連結 → 必須停下來,而且連結指到的檔不可以被動
      4. 備份的名字是**指到不存在的檔**的符號連結(os.path.exists 會回 False)
         → 必須說它是符號連結,不可以說「找不到備份」
      5. 截成八分之一的備份 → --restore 必須擋下來,正本逐位元組不變、備份還在
      6. 還原做到一半 os.replace 丟例外 → 正本必須維持**舊的完整內容**,
         不可以是 0 bytes 或半截,而且不留暫存檔
      7. --swap --apply 寫到一半 os.replace 丟例外 → 同上
      8. --dedupe --apply 寫到一半 os.replace 丟例外 → 同上
      9. 同名項目的 BIGF → _blob_map 必須擋下來(不然會靜默丟掉其中一份)
     10. 前綴命中兩個字型 → 必須要求打完整名字,不可以替使用者猜
     11. --swap --apply 寫出去的內容跟記憶體裡不一樣 → 複驗要咬住,
         而且訊息裡要有還原指令
     12. --dedupe --apply 同上
     13. 資料夾唯讀 → 寫不進去要停,正本不可以被動、不可以留下暫存檔
         (用 root 跑的話 chmod 擋不住,那種情況會跳過這一道而不是假裝測過)
     14. 在 _NoInterrupt 區塊裡送一個真的 SIGINT → 區塊裡不可以被打斷,
         離開區塊之後才可以丟出 KeyboardInterrupt
     15. 真的跑一次 --swap --apply,SIGINT 在 os.replace 做完之後才打進來 →
         exit code 130、輸出要**承認檔案已經動過**並印還原指令,正本真的變了
     16. 同一條路,SIGINT 打在還沒開始換名的時候 → exit code 130、輸出說
         「還沒有換過任何檔案」、正本逐位元組不變、不留「正在換」的登記
         (14/15/16 在送不出 SIGINT 的環境會跳過,而且會印出來說跳過,
          不會默默當成通過;所以最後那一行的餌數是算出來的,不是寫死的)

    ⚠️ 這一段在 python3 -O 底下**直接拒絕跑**:-O 會把 assert 全部拿掉,
       而下面的檢查幾乎都是 assert,跑下去會一路印到「全部通過」——
       那是假的綠燈。(2026-09-06 補這一道之前實測:python3 -O 跑 --selftest
       印的跟一般模式一模一樣、exit code 也是 0。)

    餌會失效而沒有人發現(2026-08-29 本站踩過:防線壞了測試照樣全綠),
    所以上面每一道都做過陰性對照:把對應的那道防線改回舊寫法,--selftest
    必須變紅。2026-09-05 這一輪就是這樣抓到餌 7 原本下錯地方的
    (它直接呼叫 _atomic_write,所以把 write_big 改回直接寫檔時它照樣全綠)。
    """
    # ⚠️ python -O 會把整支程式裡的 assert **全部拿掉**,而下面的檢查
    #    幾乎都是 assert(ck() 就是包了一層的 assert)。拿掉之後這一段會
    #    一路跑到最後印「全部通過」—— 那個綠燈是假的,比沒有測試更糟。
    #    所以 -O 直接拒絕跑,不留這個假綠的窗口。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    import contextlib
    import io
    import shutil as _shutil

    n_checks = 0

    def ck(cond, why):
        nonlocal n_checks
        n_checks += 1
        assert cond, why

    quiet = lambda: contextlib.redirect_stdout(io.StringIO())

    root = tempfile.mkdtemp(prefix='mvp_font_swap_selftest-')
    try:
        fonts = os.path.join(root, 'data', 'fonts')
        srcdir = os.path.join(root, 'data', '2023英文語系', 'fonts')
        outside = os.path.join(root, '外面')
        for d in (fonts, srcdir, outside):
            os.makedirs(d)
        live = os.path.join(fonts, 'fonts.big')
        srcp = os.path.join(srcdir, 'fonts.big')
        bak = live + BACKUP

        # twc14 與 twc16 內容一模一樣 —— --dedupe 要合併的就是這兩個。
        # dflt_en 與 dflt_jp 並存 —— 前綴 "dflt" 會命中兩筆,那是第 9 道餌。
        live_entries = [('au20b_en.ffn', b'A' * 100),
                        ('dflt_en.ffn', b'B' * 60),
                        ('dflt_jp.ffn', b'D' * 44),
                        ('twc14_en.ffn', b'C' * 80),
                        ('twc16_en.ffn', b'C' * 80)]
        src_entries = [('au20b_en.ffn', b'a' * 20),
                       ('dflt_en.ffn', b'B' * 60),
                       ('dflt_jp.ffn', b'd' * 12),
                       ('twc14_en.ffn', b'c' * 24),
                       ('twc16_en.ffn', b'c' * 24)]
        origin = _fake_big(live_entries)
        open(live, 'wb').write(origin)
        open(srcp, 'wb').write(_fake_big(src_entries))

        # ── 正向:讀得出來 ──────────────────────────────────────
        raw, items, _ = read_big(live)
        ck([n for n, _o, _s in items] == [n for n, _b in live_entries],
           '造出來的 BIGF 名字讀不對 —— 測試本身壞了')
        blobs = _blob_map(raw, items, 'selftest')
        ck(blobs == dict(live_entries), '讀出來的內容跟放進去的不一樣')

        # ── 餌 1 / 餌 2:舊版猜得到的暫存名字上放符號連結 ────────
        out1 = os.path.join(outside, '別人的檔1')
        out2 = os.path.join(outside, '別人的檔2')
        open(out1, 'wb').write(b'X' * 500)
        open(out2, 'wb').write(b'Y' * 500)
        os.symlink(out1, bak + '.part')       # 舊版備份用的名字
        os.symlink(out2, live + '.part')      # 舊版寫檔用過的名字
        with quiet():
            cmd_swap(root, ['au20b'], True)
        ck(open(out1, 'rb').read() == b'X' * 500,
           '餌 1 沒咬到:<備份>.part 那個符號連結指到的檔被寫壞了')
        ck(open(out2, 'rb').read() == b'Y' * 500,
           '餌 2 沒咬到:<正本>.part 那個符號連結指到的檔被寫壞了')
        ck(os.path.islink(bak + '.part') and os.path.islink(live + '.part'),
           '那兩個符號連結不該被本工具動到')
        os.remove(bak + '.part')
        os.remove(live + '.part')

        # ── 正向:換得動、備份是原檔、暫存檔沒有留下 ────────────
        ck(open(bak, 'rb').read() == origin, '備份的內容應該是動手前那一份')
        raw2, items2, _ = read_big(live)
        b2 = _blob_map(raw2, items2, 'selftest')
        ck(b2['au20b_en.ffn'] == b'a' * 20, 'au20b 沒有被換過去')
        ck(b2['dflt_en.ffn'] == b'B' * 60, '沒點名的字型被動到了')
        ck(len(items2) == len(live_entries), '換完之後字型數量變了')
        ck(_junk(fonts) == [], '成功之後不該留下暫存檔:%s' % _junk(fonts))

        # ── 餌 7 / 餌 8:寫到一半 os.replace 炸掉,正本要維持舊的完整內容 ──
        # ⚠️ 這兩道一定要走**真正的那條指令**(cmd_swap / cmd_dedupe),
        #    不可以直接呼叫 _atomic_write:2026-09-05 第一版就是直接呼叫,
        #    結果把 write_big 改回 open(遊戲檔, 'wb') 之後測試照樣全綠 ——
        #    餌下錯了地方,量到的是自己。
        #    這裡的前提是「備份已經在了」,所以 cmd_swap 會跳過備份那一步、
        #    直接進到寫檔;不然炸的會是備份那一步,寫檔那一段根本沒跑到。
        before = open(live, 'rb').read()
        real_replace = os.replace

        def _boom(a, b):
            raise OSError(28, '磁碟滿了(測試用的假故障)')

        ck(os.path.exists(bak), '餌 7 佈置錯了:備份要先在,才會跳過備份那一步')
        for tag, act in (('餌 7 --swap --apply',
                          lambda: cmd_swap(root, ['twc14'], True)),
                         ('餌 8 --dedupe --apply',
                          lambda: cmd_dedupe(root, True))):
            os.replace = _boom
            try:
                with quiet():
                    act()
            except OSError:
                pass
            else:
                raise AssertionError('%s 沒咬到:os.replace 炸了卻沒有丟例外' % tag)
            finally:
                os.replace = real_replace
            n_checks += 1
            ck(open(live, 'rb').read() == before,
               '%s 沒咬到:寫到一半炸掉,正本竟然被動了' % tag)
            ck(_junk(fonts) == [], '%s:失敗之後不該留下暫存檔:%s' % (tag, _junk(fonts)))

        # ── 餌 11 / 餌 12:寫出去的內容跟記憶體裡不一樣 ─────────────
        # 這兩道證明「寫完重讀、逐項逐位元組對一遍」那一關真的在運作:
        # 把 write_big / write_big_dedup 暫時換成「故意寫錯一段」的版本,
        # 兩條 --apply 都必須停下來、而且訊息裡要有還原指令。
        # (沒有這兩道的話,把複驗整段拿掉,--selftest 照樣全綠 ——
        #  2026-09-05 的陰性對照就是這樣抓到的。)
        g = globals()
        for tag, key, act in (
                ('餌 11 --swap --apply', 'write_big',
                 lambda: cmd_swap(root, ['twc14'], True)),
                ('餌 12 --dedupe --apply', 'write_big_dedup',
                 lambda: cmd_dedupe(root, True))):
            real_fn = g[key]

            def _wrong(path, items, blobs, _real=real_fn):
                bad = dict(blobs)
                bad[items[0][0]] = b'Z' * 7      # 只弄壞一段,其餘照寫
                return _real(path, items, bad)

            g[key] = _wrong
            try:
                with quiet():
                    act()
            except DataError as e:
                ck('--restore' in str(e), '%s:停下來的訊息裡要有還原指令' % tag)
            else:
                raise AssertionError('%s 沒咬到:寫錯了竟然沒有被複驗抓到' % tag)
            finally:
                g[key] = real_fn
            n_checks += 1
            # 這兩道是「已經寫下去才發現不對」,所以正本現在是壞的 ——
            # 那正是真實情況下要 --restore 的理由。這裡直接把場景放回上一步。
            open(live, 'wb').write(before)
        ck(_junk(fonts) == [], '餌 11/12:不該留下暫存檔:%s' % _junk(fonts))

        # ── 餌 13:資料夾唯讀 → 正本不可以被動,也不可以留下暫存檔 ────
        # 用 root 跑的話 chmod 擋不住,所以先確認「這台機器上它真的擋得住」;
        # 擋不住就跳過,不要假裝測過。
        os.chmod(fonts, 0o500)
        try:
            can_write = True
            try:
                probe_fd, probe = tempfile.mkstemp(dir=fonts)
                os.close(probe_fd)
                os.remove(probe)
            except OSError:
                can_write = False
            if not can_write:
                # 走 main() 而不是直接呼叫 cmd_swap:要驗的除了「正本沒被動」,
                # 還有「exit code 不是 0」—— 印個 ❌ 卻回 0 會讓包裝腳本誤判成功。
                old_argv = sys.argv
                sys.argv = ['mvp_font_swap.py', root, '--swap', 'twc16', '--apply']
                try:
                    with quiet():
                        rc = main()
                finally:
                    sys.argv = old_argv
                ck(rc == 2, '餌 13 沒咬到:寫不進去卻回 exit code %r' % rc)
                ck(open(live, 'rb').read() == before,
                   '餌 13 沒咬到:唯讀資料夾裡正本竟然被動了')
                ck(_junk(fonts) == [], '餌 13:不該留下暫存檔:%s' % _junk(fonts))
        finally:
            os.chmod(fonts, 0o700)

        # ── 餌 5:截成八分之一的備份,--restore 必須擋下來 ────────
        full_bak = open(bak, 'rb').read()
        open(bak, 'wb').write(full_bak[:len(full_bak) // 8])
        try:
            with quiet():
                cmd_restore(root)
        except SystemExit:
            pass
        else:
            raise AssertionError('餌 5 沒咬到:截斷的備份竟然還原得下去')
        n_checks += 1
        ck(open(live, 'rb').read() == before, '餌 5:被擋下來時正本不可以被動')
        ck(os.path.exists(bak), '餌 5:被擋下來時備份不可以被刪掉')

        # ── 餌 6:還原到一半 os.replace 炸掉 ─────────────────────
        open(bak, 'wb').write(full_bak)
        os.replace = _boom
        try:
            with quiet():
                cmd_restore(root)
        except OSError:
            pass
        else:
            raise AssertionError('餌 6 沒咬到:os.replace 炸了卻沒有丟例外')
        finally:
            os.replace = real_replace
        n_checks += 1
        ck(open(live, 'rb').read() == before,
           '餌 6 沒咬到:還原到一半炸掉,正本竟然變成半截')
        ck(_junk(fonts) == [], '餌 6:失敗之後不該留下暫存檔:%s' % _junk(fonts))
        ck(os.path.exists(bak), '餌 6:失敗的還原不可以把備份刪掉')

        # ── 正向:完整的備份還原得回去,而且備份會被刪掉 ─────────
        with quiet():
            cmd_restore(root)
        ck(open(live, 'rb').read() == origin, '還原之後應該逐位元組回到原本的樣子')
        ck(not os.path.exists(bak), '還原成功之後備份檔應該被刪掉')
        ck(_junk(fonts) == [], '還原成功之後不該留下暫存檔:%s' % _junk(fonts))

        # ── 餌 4:備份的名字是指到不存在的檔的符號連結 ───────────
        os.symlink(os.path.join(outside, '根本沒有這個檔'), bak)
        ck(not os.path.exists(bak) and os.path.islink(bak),
           '餌 4 佈置錯了:它應該是一個指到不存在的檔的符號連結')
        try:
            with quiet():
                cmd_restore(root)
        except DataError as e:
            ck('符號連結' in str(e),
               '餌 4 沒咬到:它被當成「找不到備份」而不是符號連結')
        else:
            raise AssertionError('餌 4 沒咬到:符號連結的備份竟然走得下去')
        n_checks += 1
        os.remove(bak)

        # ── 餌 3:正本本身是符號連結 ─────────────────────────────
        real_live = os.path.join(outside, '真正的 fonts.big')
        _shutil.copyfile(live, real_live)
        os.remove(live)
        os.symlink(real_live, live)
        try:
            with quiet():
                cmd_swap(root, ['au20b'], True)
        except DataError:
            pass
        else:
            raise AssertionError('餌 3 沒咬到:正本是符號連結竟然照寫')
        n_checks += 1
        ck(open(real_live, 'rb').read() == origin,
           '餌 3 沒咬到:連結另一頭那個檔被寫到了')
        ck(not os.path.exists(bak), '餌 3:被擋下來的時候不該生出備份')
        os.remove(live)
        open(live, 'wb').write(origin)

        # ── 正向:--dedupe --apply(順便是那個 NameError 的回歸測試)──
        with quiet():
            cmd_dedupe(root, True)
        raw3, items3, _ = read_big(live)
        b3 = _blob_map(raw3, items3, 'selftest')
        ck(len(items3) == len(live_entries), '合併之後字型數量不可以變')
        ck(b3 == dict(live_entries), '合併之後每一段內容都要跟原本一樣')
        ck(sum(qfs_size(v) for v in b3.values())
           == sum(qfs_size(v) for _n, v in live_entries),
           '合併之後解開後總量不可以變')
        ck(len(raw3) < len(origin), '合併之後檔案應該變小')
        ck(_junk(fonts) == [], '合併成功之後不該留下暫存檔:%s' % _junk(fonts))
        with quiet():
            cmd_restore(root)
        ck(open(live, 'rb').read() == origin, '合併之後也要還原得回去')

        # ── 餌 9:同名項目一定要擋下來 ───────────────────────────
        dup = _fake_big([('x.ffn', b'1'), ('x.ffn', b'2')])
        draw, ditems, _ = read_big(io_write(root, 'dup.big', dup))
        try:
            _blob_map(draw, ditems, 'dup.big')
        except DataError:
            pass
        else:
            raise AssertionError('餌 9 沒咬到:同名項目竟然過了')
        n_checks += 1

        # ── 餌 10:前綴命中兩個一定要停 ──────────────────────────
        try:
            with quiet():
                cmd_swap(root, ['dflt'], False)
        except DataError as e:
            ck('命中' in str(e), '餌 10 咬到的不是「命中兩個」那一條')
        else:
            raise AssertionError('餌 10 沒咬到:前綴命中兩個竟然還替人猜')
        n_checks += 1
        ck(open(live, 'rb').read() == origin, '預覽不可以動到檔案')

        # ── 餌 14 / 15 / 16:Ctrl-C 不可以說謊 ───────────────────
        # 測的是 2026-09-06 補的那一段:換名與登記綁成一段不可中斷的區間
        # (_NoInterrupt),外加「還沒動 / 正在換 / 已換」三態登記當保險。
        # 陰性對照:把 _replace_and_register 改回「os.replace 完才登記、
        # 中間不擋訊號」,餌 15 就會變紅 —— 它會印「還沒有換過任何檔案」,
        # 而正本的 SHA-256 已經變了。
        baits = 13
        fire = None
        if hasattr(signal, 'raise_signal'):          # Python 3.8 起才有
            fire = lambda: signal.raise_signal(signal.SIGINT)
        elif os.name != 'nt':
            # Windows 的 os.kill 不接 SIGINT(它會直接終結行程),
            # 所以那條只在非 Windows 上走。
            fire = lambda: os.kill(os.getpid(), signal.SIGINT)
        if fire is not None:
            # 裝得回原本的處理器,才代表這個環境裝得上(非主執行緒裝不上)。
            cur = signal.getsignal(signal.SIGINT)
            try:
                if cur is None:
                    fire = None
                else:
                    signal.signal(signal.SIGINT, cur)
            except (ValueError, OSError):
                fire = None
        if fire is None:
            print('  (這台機器送不出 SIGINT,餌 14/15/16 跳過,不當成通過)')
        else:
            # ── 餌 14:區塊裡不可以被打斷,離開才可以丟 ──────────
            seq = []
            try:
                with _NoInterrupt():
                    fire()
                    seq.append('區塊裡沒有被打斷')
            except KeyboardInterrupt:
                seq.append('離開區塊之後才丟出來')
            ck(seq == ['區塊裡沒有被打斷', '離開區塊之後才丟出來'],
               '餌 14 沒咬到:_NoInterrupt 沒有把 Ctrl-C 延後到區塊結束(%r)' % seq)
            baits += 1

            # ── 餌 15:換名做完之後才被 Ctrl-C → 必須承認換過了 ──
            # 備份先放好,cmd_swap 才會跳過備份那一步,直接進到寫正本;
            # 不然 SIGINT 會打在備份那一次換名上,正本那一段根本沒跑到。
            def _run_apply():
                buf = io.StringIO()
                old_argv = sys.argv
                sys.argv = ['mvp_font_swap.py', root, '--swap', 'au20b', '--apply']
                try:
                    with contextlib.redirect_stdout(buf):
                        rc = main()
                finally:
                    sys.argv = old_argv
                return rc, buf.getvalue()

            def _reset():
                del _WRITTEN[:]
                del _REPLACING[:]
                open(live, 'wb').write(origin)
                open(bak, 'wb').write(origin)

            def _replace_then_sigint(a, b, _real=real_replace):
                _real(a, b)
                fire()

            _reset()
            sha_before = _sha256(live)
            os.replace = _replace_then_sigint
            try:
                rc, said = _run_apply()
            finally:
                os.replace = real_replace
            ck(rc == 130, '餌 15 沒咬到:Ctrl-C 之後 exit code 應該是 130,'
                          '結果是 %r' % rc)
            ck(_sha256(live) != sha_before,
               '餌 15 佈置錯了:正本應該真的被換過,不然量到的不是這一道')
            ck('已經動過' in said,
               '餌 15 沒咬到:檔案換過了卻沒有承認(%r)' % said[-200:])
            ck('--restore' in said, '餌 15 沒咬到:換過了卻沒有印還原指令')
            ck(_REPLACING == [], '餌 15:登記完成之後不該留下「正在換」')
            ck(_junk(fonts) == [], '餌 15:不該留下暫存檔:%s' % _junk(fonts))
            baits += 1

            # ── 餌 16:還沒換名就被 Ctrl-C → 必須說沒動到 ─────────
            # 打在 fsync 之後、換名之前:那時候暫存檔寫好了,正本還沒動。
            real_fsync = os.fsync

            def _fsync_then_sigint(fd, _real=real_fsync):
                _real(fd)
                fire()

            _reset()
            os.fsync = _fsync_then_sigint
            try:
                rc, said = _run_apply()
            finally:
                os.fsync = real_fsync
            ck(rc == 130, '餌 16 沒咬到:exit code 應該是 130,結果是 %r' % rc)
            ck(open(live, 'rb').read() == origin,
               '餌 16 沒咬到:還沒換名就被中斷,正本竟然被動了')
            ck('還沒有換過任何檔案' in said,
               '餌 16 沒咬到:什麼都沒動卻沒有這樣說(%r)' % said[-200:])
            ck(_REPLACING == [], '餌 16:沒換成就不可以留下「正在換」的登記')
            ck(_junk(fonts) == [], '餌 16:失敗之後不該留下暫存檔:%s' % _junk(fonts))
            baits += 1
            del _WRITTEN[:]
            del _REPLACING[:]

        print('自我測試:全部通過(%d 道檢查,涵蓋 %d 組反向餌)' % (n_checks, baits))
        return 0
    finally:
        _shutil.rmtree(root, ignore_errors=True)


def io_write(root, name, data):
    """--selftest 用的小工具:把一段位元組寫成檔案,回傳路徑。"""
    p = os.path.join(root, name)
    with open(p, 'wb') as f:
        f.write(data)
    return p


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
