#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_audio.py —— 把遊戲的聲音解成 WAV,也把 WAV 編回遊戲的格式

    看檔頭       python3 mvp_audio.py "<聲音檔>" --info
    列出裡面的段  python3 mvp_audio.py "<聲音檔>" --list
    匯出成 WAV    python3 mvp_audio.py "<聲音檔>" --export 0 out.wav
    把 WAV 編回去  python3 mvp_audio.py "<聲音檔>" --import 0 in.wav
    真的寫入      (上面那行加 --apply)
    還原          python3 mvp_audio.py "<聲音檔>" --restore
    自我測試      python3 mvp_audio.py --selftest

會動到遊戲檔的只有兩條路:「--import --apply」與「--restore」。
⚠️ --restore 不吃 --apply,備份通過檢查就把 .audiobak 換回遊戲檔
   (換的方式是原子的:先寫暫存檔、逐位元組比對過才換名,絕不直接蓋正本)
   (本站實測:把正本改壞一個位元組再跑 --restore,md5 回到備份那一份)。
--export 沒加 --apply 也會寫檔,但寫的是你指定的那個 WAV,遊戲檔一個位元組都不動。

╔══════════════════════════════════════════════════════════════════╗
║ 這支怎麼來的                                                      ║
║                                                                  ║
║ EA 的聲音格式本站解了很久,一直卡在「一組 15 個位元組怎麼變回      ║
║ 28 個取樣」。過去試過一千種以上的參數組合,最好只有 0.16 的相關。  ║
║                                                                  ║
║ 2026-08-29 解開了,而關鍵不是想到更聰明的組合,是**找到標準答案**: ║
║ 免費的 ffmpeg 解得開遊戲的選單音樂,那就是一份可以逐取樣比對的     ║
║ 對照組。有了它,把參數空間掃一遍就找到唯一 100% 吻合的那一組。     ║
║                                                                  ║
║ 沒有標準答案的時候,一千次嘗試不會收斂,只會累積。                 ║
╚══════════════════════════════════════════════════════════════════╝

── 它到底在做什麼 ────────────────────────────────────────
遊戲的聲音不是 WAV,是 EA 自己的 4 位元壓縮格式,裝在
SCHl → SCCl → 一連串 SCDl → SCEl 這種「一段接一段」的容器裡。
本工具把那個格式解成一般的 16 位元 WAV,也能把你的 WAV 編回去,
而且是**原地填格子**,不重新打包整個檔。

吃什麼(輸入)
  · 命令列第一個參數:遊戲裡的一個聲音檔
  · --import 時再加一個 **16 位元的 WAV**。聲道數必須跟目標那一段一模一樣,
    不一樣直接拒絕;位元深度不是 16 也直接拒絕。
  · **取樣率那一關,只在那一段的檔頭有寫取樣率時才會擋。** 檔頭沒寫的段這一關
    整個跳過,什麼取樣率都收得下去,因為沒有數字可以拿來比。本站在剛安裝好的
    原版那份 data/audio 上量到:31,034 段裡有 30,824 段檔頭沒寫取樣率(99.3%),
    其中 220 段連相位那一關也過得去(英文版與中文版量到的數字一樣)。那 220 段
    只要聲道數對,丟 8000 Hz 進去也不會被擋(實測
    data/audio/cd/aems/batdit.ast 第 0 段,雙聲道)。本工具還是不幫你重取樣,
    所以取樣率得你自己對:匯出這種段時 WAV 檔頭寫的是預設值 22050 Hz,
    照著做最保險,但那是預設值不是量到的。

吐什麼(輸出)
  · --info / --list:只印在畫面上
  · --export:寫出一個 WAV,遊戲檔一個位元組都不動。輸出檔名要是指到一個
    **已經存在而且不是 WAV** 的檔(手滑打成遊戲檔本身就是這種),直接拒絕,
    不會蓋掉它;是符號連結也拒絕。真正寫出去的方式跟遊戲檔同一套
    (先寫一個猜不到名字的暫存檔,fsync 過才換名),所以不會沿著連結
    把資料夾外面的檔寫壞
  · --import 沒加 --apply:只印預覽,遊戲檔一個位元組都不動
  · --import 加了 --apply:原地覆寫那一段的取樣,並留下 <原檔名>.audiobak
    ⚠️ 2026-09-04 訂正:這一句以前對社群語音包(GSTR 容器)是假的,它一個位元組
    都沒寫,卻照樣印「✅ 寫好了」。原因與量到的範圍見 cmd_import 上面那段。
  · --restore:把 .audiobak 蓋回去

安全網
  1. 預設唯讀。會動遊戲檔的只有「--import --apply」與「--restore」兩條路。
  2. 第一次寫入之前自動備份,而且**備份、寫回去、還原三條路都是原子的**:
     先在同一個資料夾裡開一個**名字猜不到**的暫存檔(tempfile.mkstemp),
     寫完 fsync 到磁碟,再用 os.replace 換上去。中途被中斷只會留下那個暫存檔,
     不會留下半截的遊戲檔。⚠️ 2026-09-05 訂正:以前用的是「<檔名>.part」這個
     **猜得到**的名字,有人先在那裡放一個指向資料夾外面的符號連結,
     就會沿著它把外面的檔案截成 0 bytes。現在暫存檔一律 mkstemp,
     而且**每一個要寫的目的檔**只要是符號連結就直接拒絕:正本、備份、
     還原的目標、--export 的輸出都算(2026-09-06 補上輸出那一個)。
     路徑中間的資料夾是連結沒關係(有人把遊戲裝在別顆碟),只看最後那個檔。
  3. 寫回去之前先試解一次:只要有任何一個區塊切不出相位就**拒絕寫入**。
     因為那代表匯出時少了一塊,取樣會整段錯位(本站實測來回訊噪比 -3.1 dB)。
  4. --restore 之前用格式驗那份備份完不完整:每一段的檔頭寫著取樣總數,
     把那一段每個 SCDl 的取樣數加起來必須等於它 —— 截斷就一定對不上。
     還原完之後再逐位元組複驗一次,對不起來就報錯不印成功。
     還原本身也是「先寫暫存檔 → 比對過 → os.replace」,任何一步失敗正本原封不動。
  5. 格子是定長的:寫回去只填格子,不改長度,所以檔案大小前後一樣。
  6. 寫入迴圈**一組都沒寫進去就拒絕印成功**。2026-09-04 之前沒有這道網,
     位元組序讀錯的那段期間,社群語音包每一個檔都是「什麼都沒做卻印 ✅」。
  7. 寫完之後把檔案**讀回來**跟「本來要寫的那份」逐位元組比對;對不起來就
     自動用備份換回去,並以非 0 的離開碼收場(不會只印一句 ❌ 卻回報成功)。
  8. 按 Ctrl-C 會明說「遊戲檔換掉了沒有」——看的是 os.replace 有沒有真的做過,
     不是用猜的 —— 而且一律以 130 收場,不會是 0。
     ⚠️ 2026-09-06 訂正:以前是「先舉旗、遇到任何例外就把旗子放下」,
     Ctrl-C 剛好落在「換名成功」與「放旗」之間時,旗子會被放下 ——
     畫面就會說「一個位元組都沒有動到」而檔案其實已經換了。現在換名與登記
     綁成一段不可中斷的動作(見 _NoInterrupt),而且狀態有三種:
     沒動過 / 正在換 / 已經換掉。萬一真的停在中間,說的是「正在替換」,
     不會說成「沒動到」。

做不到的事(先說在前面)
  · **不會改長度。** 你的 WAV 比較短會補靜音,比較長會被切掉。
  · **不幫你重取樣、不幫你混音、不幫你轉位元深度。** 聲道數與位元深度對不上
    一定拒絕;取樣率對不上只有在那一段的檔頭有寫取樣率時才擋得住
    (見上面「吃什麼」那一條)。轉檔請自己在音訊軟體裡做完再進來。
  · 編碼是有損的:4 位元格式先天如此。把「本來就是這個格式的聲音」再編一次,
    本站量到 98.1 dB;拿全新錄音進來大約 35 dB,原廠自己編也是那個數字。
    ⚠️ 2026-09-05 訂正:98.1 dB 是**修好立體聲起始狀態之前**量的(見 cmd_import
    寫入迴圈裡那段註解)。修好之後立體聲那一半會好很多:拿剛安裝好的原版
    menu9.asf 的 40 個區塊實測,修之前 156,800 個取樣有 4,365 個不同(最大誤差
    2,129、46.6 dB),修之後 0 個不同、誤差 0 —— 而且是用 ffmpeg 當獨立的
    解碼器去讀「寫回去的那個檔」驗的,不是拿本工具自己驗自己。
    單聲道與 GSTR 那一半不受影響(新舊寫出來的位元組完全相同)。
    98.1 dB 那一整組數字本站還沒有重新量過,先照實說它是舊的。
  · 有些段連對照工具也解不開,那是容器層還有分支。本工具遇到會明說解不出來,
    不會吐出垃圾給你。⚠️ 但「一定會明說」這件事本站自己破過一次:寫回去那一段
    曾經什麼都沒做卻印「✅ 寫好了」(2026-09-04 修,見 cmd_import 上面那段)。
  · **換完之後遊戲裡真的會不會唸出來,本站沒驗。** 驗的是「檔案寫進去了,
    而且寫的內容正確」。⚠️ 2026-09-04 訂正:這句話以前只在 PT 容器上成立,
    GSTR 容器根本沒寫進去,見 cmd_import 上面那段。
"""
#
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

import os
import sys
import wave
import signal
import struct
import shutil
import tempfile
import argparse

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

# 被 Ctrl-C 打斷的時候,讀者只想知道一件事:遊戲檔到底換掉了沒有。
# 這件事有**三種**狀態,不是兩種:
#     沒動過   _LIVE_REPLACED False 而且 _LIVE_REPLACING 是 None
#     正在換   _LIVE_REPLACING 記著那個檔名(換成功了沒有還不確定)
#     已經換掉 _LIVE_REPLACED True(os.replace 真的做完而且登記過了)
# 只有第一種可以跟讀者說「一個位元組都沒有動到」—— 那句話不可以用猜的。
_LIVE_REPLACED = False
_LIVE_REPLACING = None


# ── 換名與登記要綁成一段不可中斷的動作(2026-09-06 第三輪稽核改)──────────
# 舊版是「先舉旗 → os.replace → 任何例外就把旗子放下」。看起來保守,其實會說謊:
# os.replace **已經成功**之後才收到 Ctrl-C,那個 KeyboardInterrupt 一樣會走進
# 「把旗子放下」那一行,於是畫面印「一個位元組都沒有動到」,而檔案其實已經換了。
# 讀者就不會去還原 —— 這正是不可以發生的那個方向。
#
# 現在的做法:換名與登記兩行包在 _NoInterrupt 裡。這段期間收到的 Ctrl-C 只會被
# 「記著」,等兩行都做完才照常丟出去,所以收尾看到的登記一定跟磁碟上的狀態一致。
# 旗子只有在 os.replace **自己失敗**(確定沒換成)的時候才會保持沒舉起來的樣子。
class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開這段之後再照常丟出。

    非主執行緒之類裝不上處理器的情況,就退回原本的行為(不會比舊版更糟),
    這時候第三態「正在換」就是保險 —— 見 _interrupt_note()。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):
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


def _note_live_replaced(value=True):
    """舉起或放下「正本已經被換掉」這面旗子,回傳它原本的值。"""
    global _LIVE_REPLACED
    was = _LIVE_REPLACED
    _LIVE_REPLACED = value
    return was


def _note_replacing(target):
    """登記「現在正在換這個檔」(target 給 None 代表這件事已經有結論了)。"""
    global _LIVE_REPLACING
    _LIVE_REPLACING = os.fspath(target) if target is not None else None


def _replace_live(tmp, dst):
    """把暫存檔換上正本 —— 換名與登記是不可分的一步。

    進來之前先登記「正在換 dst」,兩種結局各自把它收掉:
      · os.replace 自己丟例外 → 確定沒換成,收掉登記,旗子維持沒舉起來
      · 換名成功 → 舉旗、收掉登記,兩件事都在 _NoInterrupt 裡面做完
    """
    _note_replacing(dst)
    with _NoInterrupt():
        try:
            os.replace(tmp, dst)
        except BaseException:
            # 換名自己失敗才走這裡:這時候「一個位元組都沒有動到」是真的。
            _note_replacing(None)
            raise
        _note_live_replaced(True)
        _note_replacing(None)


# ── 暫存檔的名字不可以是猜得到的(2026-09-05 第二輪稽核加)──────────────
# 原本備份與寫入都用「<目的檔>.part」這個固定名字。名字固定就代表**別人可以
# 先佔位**:在遊戲資料夾裡先放一個叫 <目的檔>.part 的符號連結指到資料夾外面,
# open(那個名字, 'wb') 會沿著連結,把外面那個檔案當場截成 0 bytes。
# 後面的 os.replace 只換掉連結本身,可是傷害在那之前就已經造成了。
#
# 改用 tempfile.mkstemp:它內部是 O_CREAT|O_EXCL,名字已經被佔走就直接失敗,
# 也不會跟著符號連結走。名字開頭加一個點,是為了萬一真的被中斷留在那裡時,
# 讀者一眼看得出那是誰留下的。
def _mkstemp_beside(dst, kind):
    """在 dst 所在的資料夾裡開一個獨一無二的暫存檔,回傳 (fd, 路徑)。

    一定要跟目的檔同一個資料夾:os.replace 只有在同一個檔案系統上才是原子的,
    寫到 /tmp 再搬過來就不是了(跨磁碟會退化成複製)。
    """
    dst = os.fspath(dst)
    d = os.path.dirname(os.path.abspath(dst)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(dst), kind))


# 目的地是符號連結就拒絕,不管它指到哪裡。
# ⚠️ 不可以只用 os.path.exists() 判斷:符號連結指向一個不存在的檔時
#    exists() 回 False,看起來像「這個名字是空的」,可是一寫下去就會沿著它
#    在資料夾外面建檔或覆寫。要看「連結自己在不在」得用 os.path.lexists /
#    os.path.islink —— 這兩個不跟著連結走。
def _reject_symlink(p, what):
    p = os.fspath(p)
    if os.path.islink(p):
        try:
            target = os.readlink(p)
        except OSError:
            target = '(讀不出來)'
        raise DataError(
            '%s(%s)是一個符號連結,指向 %s —— 拒絕。\n'
            '  本工具只寫真正的檔案:寫到連結上,被動到的是它指到的那個檔\n'
            '  (有可能在遊戲資料夾外面);換名字的時候又只換掉連結本身,\n'
            '  真正那個檔反而留著舊內容。兩種結果都不是你要的。\n'
            '  請把路徑直接指向真正的那個檔。' % (what, p, target))


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。
    ⚠️ 2026-09-05:那個固定名字連同「猜得到」這件事一起換掉了,改用
       _mkstemp_beside(理由見上面那一段)。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _reject_symlink(dst, '備份檔')
    # 先寫到一個猜不到的暫時名字,寫完、而且真的落到磁碟了,才換成正式名字。
    fd, tmp = _mkstemp_beside(dst, 'backup')
    try:
        with os.fdopen(fd, 'wb') as fout:
            with open(src, 'rb') as fin:
                shutil.copyfileobj(fin, fout)
            fout.flush()
            os.fsync(fout.fileno())    # 少了這一步,斷電之後留下的可能是空殼
        shutil.copystat(src, tmp)      # 權限與修改時間跟著走(等同 copy2)
        os.replace(tmp, dst)           # os.replace 是原子的
    except BaseException:
        # 失敗就把半截的暫存檔收掉,再把原本的例外原封不動丟出去。
        # 這裡只負責清乾淨,不負責決定「要不要繼續」。
        try:
            os.remove(tmp)
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
    """
    import struct
    bak, dst = os.fspath(bak), os.fspath(dst)
    if not os.path.exists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    # 第 1 道:0 bytes 的備份一定是壞的,不必看內容就能判定。
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

    # 第 2 道:BIGF 封裝檔。檔頭第 4-8 個位元組寫著「整個檔應該多長」,
    # 跟實際長度對不上就是被截斷了。小端與大端兩種都接受:
    # 本機 295 個 BIGF 檔裡 288 個小端、7 個大端,兩種都是真的。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:語系檔。位移 16-20 指向字串區 LOCL,LOCL 裡面又有一張位移表。
    # 檔案被截斷的話,最後一條字串的位移一定會指到檔案結尾外面。
    # 用「指到的地方在不在檔案裡」當判準,比看檔案大小可靠。
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

    # 第 4 道:Windows 執行檔。位移 0x3C 是 PE 檔頭的位置,PE 檔頭後面是節區表,
    # 每個節區 40 bytes,其中位移 16-24 是「這一節在檔案裡的長度與起點」。
    # 所有節區的結尾取最大值,那就是這個執行檔至少該有多長。
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
    # 「不到一半」是門檻,不是證明:它擋得住明顯的半截檔,擋不住只少了幾百
    # 位元組的。真正保得住你的,還是你自己另外留的那一整包備份。
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


# 上面那幾道都沒喊停才會走到這裡:整支腳本真正「把備份換回正本」的動作在這裡。
#
# ── 為什麼不是一行 shutil.copy2(bak, dst)(2026-09-05 第二輪稽核改)────────
# copy2 的第一個動作就是把目的檔開成 'wb' —— **那一行下去正本當場變 0 bytes**,
# 之後才慢慢把備份的內容寫回去。中途按 Ctrl-C、磁碟滿、外接碟被拔掉,
# 留下來的就是一個半截的遊戲檔。而讀者會跑 --restore,正是因為正本已經有問題;
# 這一刀等於連他最後的退路也切斷。本工具處理的檔可以到 24 MB
# (data/audio/cd/aems/crowd4a.ast),那個窗口不是一瞬間。
#
# 現在的順序是:在正本那個資料夾裡開一個猜不到名字的暫存檔 → 寫進去 → fsync →
# 抄正本的權限 → **讀回來跟備份逐位元組比對** → 才 os.replace 換上去。
# 任何一步失敗都只丟掉暫存檔,正本一個位元組都不會被動到。
def _do_copy(bak, dst):
    bak, dst = os.fspath(bak), os.fspath(dst)
    _reject_symlink(bak, '備份檔')
    _reject_symlink(dst, '要還原的那個檔')
    fd, tmp = _mkstemp_beside(dst, 'restore')
    try:
        with os.fdopen(fd, 'wb') as fout:
            with open(bak, 'rb') as fin:
                shutil.copyfileobj(fin, fout)
            fout.flush()
            os.fsync(fout.fileno())
        # 權限要抄**正本**的,不是備份的:換名之後權限跟著新檔走。
        if os.path.exists(dst):
            try:
                shutil.copymode(dst, tmp)
            except OSError:
                pass
        # 換上去之前,先確認「已經落到磁碟上的那一份」真的等於備份。
        # 比的是完整長度加完整內容,不是抽樣。
        if os.path.getsize(tmp) != os.path.getsize(bak):
            raise DataError('還原用的暫存檔跟備份不一樣長,不敢換上去'
                            '(%s 一個位元組都沒有被動到)' % dst)
        with open(bak, 'rb') as f1, open(tmp, 'rb') as f2:
            if f1.read() != f2.read():
                raise DataError('還原用的暫存檔跟備份對不起來,不敢換上去'
                                '(%s 一個位元組都沒有被動到)' % dst)
        _replace_live(tmp, dst)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise




# Windows 的命令提示字元預設用 cp950,直接印中文會炸掉。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 備份的副檔名。本站每一支工具各用各的,免得兩支工具的備份在同一個資料夾裡
# 互相覆蓋,那會讓「還原」變成「拿別的東西蓋掉正本」。
BACKUP_SUFFIX = '.audiobak'
GROUP_SAMPLES = 28          # 一組 15 bytes = 1 表頭 + 14 資料 = 28 個半位元組
GROUP_BYTES = 15

# ─────────────────────────────────────────────────────────
#  取樣的數學
#
#  每一組:表頭 1 byte,高半位元組挑係數(0-3),低半位元組決定位移。
#      c1 = EA[h >> 4]        c2 = EA[(h >> 4) + 4]
#      位移 = 20 - (h & 0x0F)
#  接著 14 個 bytes,每個位元組拆成兩個半位元組(**高的先**):
#      s = clip( ((sign4(nib) << 位移) + cur*c1 + prev*c2) >> 8 )
#      prev, cur = cur, s
#
#  ⚠️ 位移是 20 減去低半位元組,也就是**低半位元組越大、位移越小**。
#     本站以前試過的一千種組合裡有一大類寫成相反方向,那是失敗的主因之一。
# ─────────────────────────────────────────────────────────
EA_COEF = [0, 240, 460, 392, 0, 0, -208, -220]
# 前四個是 c1(乘在「上一個取樣」上),後四個是對應的 c2(乘在「再上一個」上),
# 所以 c2 一律取 EA_COEF[idx + 4]。這張表不是猜的:拿 ffmpeg 解出來的同一段
# 音樂當標準答案,1,024 種組合裡只有這一組給出 100.00%,第二名 96.90%,
# 第三名掉到 18.91%。不是勉強領先,是斷崖。


# 半位元組是有號的:0-7 就是 0 到 7,8-15 是 -8 到 -1(四位元的二補數)。
# 少了這一步,所有負的取樣都會變成很大的正數。
def _sx4(v):
    return v - 16 if v >= 8 else v


# 取樣是 16 位元有號整數,算出來超出範圍就夾住。
# (本站沒有單獨驗過「夾住」這一步在真實資料上被觸發過幾次,
#  驗過的是整體解碼跟 ffmpeg 逐取樣相同:21,678,328 個取樣 0 個不同。)
def _clip(v):
    return -32768 if v < -32768 else (32767 if v > 32767 else v)


# 一組的解碼。四個事實讀者從程式碼本身看不出來:
#   · 表頭的高半位元組挑係數,**只可能是 0-3**;超出就代表相位切錯了
#   · 表頭的低半位元組決定位移,而且是 20 減去它(不是加)
#   · 14 個資料位元組,每個拆成兩個半位元組,**高的先**
#   · 每個取樣都要靠前兩個取樣算出來,所以 prev/cur 得一路傳下去:
#     不能從中間任意一組開始解,那是這個格式的性質不是實作偷懶
def decode_group(header, payload, prev, cur):
    """15 bytes → 28 個取樣。payload 是 14 bytes。"""
    idx = header >> 4
    if idx > 3:
        raise DataError('表頭高半位元組是 %d,超過 0-3 —— 相位切錯了' % idx)
    c1, c2 = EA_COEF[idx], EA_COEF[idx + 4]
    sh = 20 - (header & 0x0F)
    out = []
    for k in range(GROUP_SAMPLES):
        b = payload[k >> 1]
        nib = (b >> 4) if not (k & 1) else (b & 0x0F)
        s = _clip(((_sx4(nib) << sh) + cur * c1 + prev * c2) >> 8)
        prev, cur = cur, s
        out.append(s)
    return out, prev, cur


def encode_group(samples, prev, cur):
    """28 個取樣 → 15 bytes。窮舉 4 個係數 × 16 個位移,取誤差平方和最小。

    只有 64 種組合,而且每種只要跑 28 個取樣 —— 全掃比任何啟發式都省事,
    而且結果是這個格式能表達的最好解,不是「夠好就收」。
    """
    # 反過來做:先算「這一步理想上要加多少」(want),除以 2 的位移次方再四捨五入,
    # 就是最接近的那個半位元組。夾到 -8..7 之後**要用夾過的值重新算一次取樣**。
    # 這一步很重要:編碼器接下來用的 prev/cur 必須跟解碼器將來算出來的一模一樣,
    # 不然誤差會一路累積下去。
    best = None
    for ci in range(4):
        c1, c2 = EA_COEF[ci], EA_COEF[ci + 4]
        for lo in range(16):
            sh = 20 - lo
            p, c, err, nibs = prev, cur, 0, []
            for t in samples:
                want = (t << 8) - c * c1 - p * c2
                n = int(round(want / float(1 << sh)))
                n = -8 if n < -8 else (7 if n > 7 else n)
                s = _clip(((n << sh) + c * c1 + p * c2) >> 8)
                err += (s - t) * (s - t)
                p, c = c, s
                nibs.append(n & 0x0F)
            if best is None or err < best[0]:
                best = (err, (ci << 4) | lo, nibs, p, c)
    err, header, nibs, p, c = best
    payload = bytes(((nibs[i * 2] << 4) | nibs[i * 2 + 1]) for i in range(14))
    return header, payload, p, c, err


# ─────────────────────────────────────────────────────────
#  容器:SCHl 檔頭 → SCCl → 一連串 SCDl → SCEl
#
#  檔頭是「標籤, 長度, 值」的串列,值是大端序。已知的標籤:
#      0x80 編碼器(1 = 音樂那種 · 2 = 語音/音效那種 · 3 = 社群語音包用的那種;裝在哪種容器看容器標記,不看編碼器)
#      0x82 聲道數(沒有這一項就是單聲道)
#      0x84 取樣率(沒有就用預設)
#      0x85 取樣總數
#      0xFF 結束
#  ⚠️ 0x80 的意義是本站量出來的。在**剛安裝好的原版**上,值為 1 的段剛好就是
#     menu1 到 menu9 九個選單音樂,一個不多一個不少(英文版與中文版各 31,034
#     段,兩份都是 9 段編碼器 1,而且都是那九個檔)—— 是名字對上名字,
#     不是數量湊巧。
#  ⚠️ 但**裝了模組的機器上不只九個**:本站測試機那份 data/audio 有 464 個
#     編碼器 1 的段,除了那九首之外,還有 61 段在 cd/spch_pa/pnamedat.big、
#     394 段在 cd/spch_pbp/pnamedat.big,那是被換過的球員名字播報語音,
#     而且是單聲道。所以「編碼器 1 = 音樂」在原版成立,在改過的機器上不成立。
#  ⚠️ 另外:「每塊自帶起始狀態」跟編碼器編號無關,是**看聲道數**決定的
#     (見 decode_segment)。連剛安裝好的原版英文版都有 296 段編碼器 2 是立體聲;
#     把「原版英文版 data/audio + 測試機 data/audio + 測試機收藏的社群語音」
#     三棵樹加起來(71,561 段)是編碼器 2 有 487 段立體聲、編碼器 1 有 455 段
#     單聲道。所以不可以拿編號去猜起始狀態怎麼取。
# ─────────────────────────────────────────────────────────
def parse_header(blob, off=0):
    if blob[off:off + 4] != b'SCHl':
        raise DataError('開頭不是 SCHl(是 %r)' % blob[off:off + 4])
    # 區塊本身的長度欄位一律小端(SCHl/SCCl/SCDl/SCEl 都是),
    # **但區塊裡面的數值不一定**,見下面那段位元組序的訂正。
    ln = struct.unpack('<I', blob[off + 4:off + 8])[0]
    p = off + 8
    # 檔頭的前 4 個位元組是平台/容器標記(例如 PT 或 GSTR)。
    # 它決定了底下 SCDl 裡的數字要用哪一種位元組序讀。
    platform = blob[p:p + 4]
    p += 4
    # 接下來是「標籤, 長度, 值」一路串到 0xFF 為止。
    # 0xFC / 0xFD / 0xFE 是單獨一個位元組,沒有長度也沒有值,遇到就跳過
    # (本站只知道它們不帶值,沒有查出它們各自代表什麼)。
    tags, end = {}, off + ln
    while p < end:
        t = blob[p]
        if t == 0xFF:
            break
        if t in (0xFC, 0xFD, 0xFE):
            p += 1
            continue
        if p + 1 >= end:
            break
        L = blob[p + 1]
        tags[t] = int.from_bytes(blob[p + 2:p + 2 + L], 'big')
        p += 2 + L
    # ── 位元組序跟「容器子型別」綁在一起(2026-08-30 量到)──────────────
    # 本工具原本無條件用小端讀 SCDl 的取樣數與聲道起點。
    # 那對原版的 PT 容器是對的,對**社群語音包的 GSTR 容器是錯的** ——
    # 而錯的後果不是報錯,是 n // 28 算出天文數字或 0,整段被 continue 跳過,
    # 最後印一句「這一段解不出取樣」。也就是說:
    # **本工具在社群語音包上從來沒有成功過,而且看起來像是格式沒解開。**
    #
    # 實測(每個容器各抽 50 個以上):
    #   PT   容器 → 小端,26/26 成立
    #   GSTR 容器 → 大端,100/100 成立,零例外
    # 例:許銘傑 8254c.dat 第一段前 4 bytes 是 00 00 25 84 ——
    #   大端讀出 9,604 個取樣(÷28 = 343 組,對得上 body 長度);
    #   小端讀出 2,217,017,344 個,顯然不是取樣數。
    endian = '>' if platform[:4].startswith(b'GSTR') else '<'
    return {'platform': platform.decode('latin-1', 'replace'),
            'endian': endian,
            'header_len': ln,
            'codec': tags.get(0x80),
            'channels': tags.get(0x82, 1),
            'rate': tags.get(0x84),
            'samples': tags.get(0x85),
            'tags': tags}


# 一段的內部是四種區塊接龍:SCHl(檔頭)→ SCCl → 一個或很多個 SCDl(資料)
# → SCEl(結束)。每個區塊前 8 個位元組是「四個字母的標籤 + 長度」,
# 長度含標籤自己,所以下一個區塊的位置就是 p + ln。
# 遇到不認得的標籤就停。寧可少走,也不要把後面的東西當成資料解。
def walk(blob, off=0):
    """回傳這一段的 [(標籤, 起點, 長度)],走到 SCEl 為止。"""
    out, p = [], off
    while p + 8 <= len(blob):
        tag = blob[p:p + 4]
        if tag not in (b'SCHl', b'SCCl', b'SCDl', b'SCEl'):
            break
        ln = struct.unpack('<I', blob[p + 4:p + 8])[0]
        if ln <= 0 or p + ln > len(blob):
            break
        out.append((tag.decode('latin-1'), p, ln))
        p += ln
        if tag == b'SCEl':
            break
    return out


# 一個檔案裡可以串很多段(一個球員的很多句話就是這樣放的)。
# 做法是一路找 SCHl,找到就走完它的接龍,再從那一段的結尾繼續找下一個。
def segments(blob):
    """一個檔裡可能串著很多段。回傳每段的起點。"""
    out, p = [], 0
    while True:
        i = blob.find(b'SCHl', p)
        if i < 0:
            break
        out.append(i)
        chain = walk(blob, i)
        p = (chain[-1][1] + chain[-1][2]) if chain else i + 4
    return out


def _phase_of(body, ngroups):
    """這一塊的資料從第幾個位元組開始。

    判準:唯一能讓**每一個**表頭的高半位元組都落在 0-3 的位置。
    這不是猜 —— 切錯相位的話,53 個表頭裡幾乎一定有人超出 0-3。
    """
    # 判準的來源:每一組的第一個位元組是表頭,而表頭的高半位元組只可能是 0-3。
    # 所以「資料從第幾個位元組開始」可以用這條性質掃出來:
    # 切錯位置的話,幾十個表頭裡幾乎一定會有人超出 0-3。
    cands = [pre for pre in range(0, len(body) - ngroups * GROUP_BYTES + 1)
             if all((body[pre + g * GROUP_BYTES] >> 4) <= 3 for g in range(ngroups))]
    if not cands:
        return None
    # ⚠️ 全靜音的區塊每個位置都通得過(表頭是 0,高半位元組當然 ≤3),
    #    判準在這種資料上失去鑑別力。4 是實測的常態(每塊 4 bytes 前置),
    #    所以 4 在候選裡就用 4,掃描只是備援。
    #    2026-08-29:原本無條件取第一個,在兩個靜音區塊上切到位置 0,
    #    產生 376 個錯誤取樣（整體 0.0017%）—— 少數但確實是錯的。
    return 4 if 4 in cands else cands[0]


# 把一整段解成「每個聲道一串取樣」。兩件事跟直覺不一樣:
#   · 立體聲的兩個聲道在 SCDl 裡是**各自連續**的兩大塊,不是左右交錯。
#     body 的前 12 個位元組給了取樣數與兩塊各自的起點。
#   · 起始狀態:立體聲每一塊開頭 4 個位元組就是這一塊自己的起始狀態
#     (「上一個取樣」與「再上一個」,兩個 16 位元有號小端);
#     單聲道則是狀態跨區塊延續,那 4 個位元組不是種子。
#     本工具用「是不是立體聲」當判準,不是看檔頭那個編碼器編號。
#     這是實作上的選擇,本站沒有另外驗過兩種分法是不是永遠等價。
def decode_segment(blob, start):
    """回傳 (檔頭資訊, 每個聲道的取樣串列)。"""
    info = parse_header(blob, start)
    en = info['endian']
    chain = walk(blob, start)
    chans = max(1, info['channels'])
    outs = [[] for _ in range(chans)]
    state = [(0, 0) for _ in range(chans)]
    skipped = 0
    for tag, off, ln in chain:
        if tag != 'SCDl':
            continue
        body = blob[off + 8:off + ln]
        n = struct.unpack(en + 'I', body[:4])[0]
        ng = n // GROUP_SAMPLES
        if ng == 0:
            continue
        if chans == 2:
            lo, ro = struct.unpack(en + 'II', body[4:12])
            parts = [body[12 + lo:12 + ro], body[12 + ro:]]
        else:
            parts = [body[4:]]
        for ci, part in enumerate(parts):
            pre = _phase_of(part, ng)
            if pre is None:
                skipped += 1
                continue
            if chans == 2 and pre >= 4:
                # 立體聲:每塊開頭 4 bytes 就是這一塊的起始狀態
                cur0, prev0 = struct.unpack('<hh', part[pre - 4:pre])
                prev, cur = prev0, cur0
            else:
                prev, cur = state[ci]
            q = pre
            for _ in range(ng):
                h = part[q]
                seg, prev, cur = decode_group(h, part[q + 1:q + 15], prev, cur)
                q += GROUP_BYTES
                outs[ci].extend(seg)
            state[ci] = (prev, cur)
    info['skipped_blocks'] = skipped
    return info, outs


# ─────────────────────────────────────────────────────────
#  WAV:自己讀自己寫,不需要安裝任何套件
# ─────────────────────────────────────────────────────────
# 寫 WAV 用 Python 內建的 wave 模組,所以零相依。
# WAV 的兩個聲道是**交錯**的(左右左右…),跟遊戲格式的「各自連續」正好相反,
# 所以這裡要一個一個穿插回去。長度取兩個聲道的較短者,免得對不齊。
# ⚠️ 這裡**不可以**直接 wave.open(path, 'wb')(2026-09-06 第三輪稽核改):
#    那一行內部就是 open(path, 'wb'),**會跟著符號連結走**。_check_out_path 已經
#    先擋過一次,但那是「看過一眼」與「真的開檔」之間的兩個時刻,中間那段空窗
#    足夠讓別人把那個名字換成一個指向資料夾外面的連結,外面那個檔就被截成 0。
#    改成跟遊戲檔同一套:mkstemp(O_CREAT|O_EXCL,不跟連結走)→ 寫 → fsync →
#    os.replace。換名只換掉那個名字本身,資料夾外面的檔不會被動到。
#    (匯出的 WAV 不是遊戲檔,所以這裡不登記 _LIVE_REPLACED —— 那面旗子講的是
#     「遊戲檔換掉了沒有」,拿匯出檔去舉它會讓 Ctrl-C 的收尾說錯話。)
def write_wav(path, chans, rate):
    path = os.fspath(path)
    _reject_symlink(path, '輸出檔')
    fd, tmp = _mkstemp_beside(path, 'wav')
    try:
        with os.fdopen(fd, 'wb') as raw:
            with wave.open(raw, 'wb') as w:
                w.setnchannels(len(chans))
                w.setsampwidth(2)
                w.setframerate(rate or 22050)
                n = min(len(c) for c in chans)
                buf = bytearray()
                for i in range(n):
                    for c in chans:
                        buf += struct.pack('<h', c[i])
                w.writeframes(bytes(buf))
            raw.flush()
            os.fsync(raw.fileno())
        # mkstemp 開出來的檔是 0600(只有自己讀得到),而匯出的 WAV 是要拿去用的。
        # 目的檔已經存在就抄它原本的權限,沒有就用 0644 —— 跟一般 umask 022 底下
        # open(..., 'wb') 建出來的一樣,讀者不會發現有什麼不同。
        try:
            if os.path.exists(path):
                shutil.copymode(path, tmp)
            else:
                os.chmod(tmp, 0o644)
        except OSError:
            pass
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


# 讀 WAV。只吃 16 位元,8 位元或 32 位元浮點一律拒絕,
# 因為本工具不做格式轉換,那件事應該由你在音訊軟體裡做完再進來。
# 最後一行 all_s[c::nch] 是把交錯的取樣拆回「一個聲道一串」。
def read_wav(path):
    # 讀者最常打錯的兩件事在這裡先擋成一句中文:WAV 檔名打錯、丟了一個
    # 根本不是 WAV 的檔。不擋的話 wave 模組會分別丟 FileNotFoundError 與
    # EOFError 的 traceback,而這一課的讀者是「不能要求開 terminal」的那群人。
    if not os.path.isfile(path):
        raise DataError('找不到這個 WAV 檔:%s' % path)
    try:
        with wave.open(path, 'rb') as w:
            if w.getsampwidth() != 2:
                raise DataError('只吃 16 位元的 WAV(這個是 %d 位元)'
                                % (w.getsampwidth() * 8))
            nch, rate, n = w.getnchannels(), w.getframerate(), w.getnframes()
            raw = w.readframes(n)
    except (wave.Error, EOFError):
        # DataError 不會被這裡吃掉(它不是 wave.Error 也不是 EOFError),
        # 所以上面那句「只吃 16 位元」照樣送得出去。
        raise DataError('讀不出 %s 的 WAV 結構 —— 它可能不是 WAV,或是壞的' % path)
    all_s = struct.unpack('<%dh' % (len(raw) // 2), raw)
    return [list(all_s[c::nch]) for c in range(nch)], rate


# ─────────────────────────────────────────────────────────
#  指令
# ─────────────────────────────────────────────────────────
# 檔頭標籤 0x80 的值。意義是本站量出來的:在剛安裝好的原版上,值為 1 的段
# 剛好就是 menu1 到 menu9 九個選單音樂,一個不多一個不少(名字對上名字,
# 不是數量湊巧);3 是裝在 GSTR 容器裡的那種(2026-08-30 之前一直被誤會成
# 「格式沒解開」)。
# ⚠️ 這裡**刻意不寫「起始狀態怎麼取」**:那件事看的是聲道數不是編碼器編號
#    (見 decode_segment)。本站在 parse_header 上面那段講的三棵樹(71,561 段)
#    量到編碼器 1 有 455 段是單聲道、編碼器 2 有 487 段是立體聲,拿編號去猜會猜錯。
# ⚠️ 也刻意不寫「編碼器 1 就是音樂」:那只在原版成立,裝了模組的機器上
#    球員名字的播報語音也有 455 段是編碼器 1(見 parse_header 上面那段)。
CODEC_NAME = {1: '1(原版只有九首選單音樂用它)',
              2: '2(語音/音效那種)',
              3: '3(社群語音包用的那種)'}


# --info:只看第一段的檔頭。最便宜的一步,先確認「這確實是 EA 的聲音檔」,
# 再決定要不要往下做。
def cmd_info(path):
    blob = open(path, 'rb').read()
    segs = segments(blob)
    print('\n  檔案 %s bytes · 裡面有 %d 段' % (format(len(blob), ','), len(segs)))
    if not segs:
        print('  找不到 SCHl —— 這不是 EA 的聲音檔\n')
        return 1
    info = parse_header(blob, segs[0])
    print('  平台標記   %s' % info['platform'])
    print('  編碼器     %s' % CODEC_NAME.get(info['codec'], info['codec']))
    print('  聲道       %s' % info['channels'])
    print('  取樣率     %s' % (info['rate'] or '(檔頭沒寫)'))
    print('  取樣總數   %s' % (format(info['samples'], ',') if info['samples'] else '?'))
    print('  其餘標籤   %s\n' % {hex(k): v for k, v in info['tags'].items()
                                if k not in (0x80, 0x82, 0x84, 0x85)})
    return 0


# --list:一個檔裡每一段各印一行。最多印 200 段,再多就只報還有幾段:
# 一個檔裡常常串著上萬段,全印出來沒有人看得完。
def cmd_list(path):
    blob = open(path, 'rb').read()
    segs = segments(blob)
    print('\n  編號   起點        區塊數  編碼器  聲道  取樣率   取樣數')
    print('  ' + '-' * 60)
    for i, s in enumerate(segs[:200]):
        info = parse_header(blob, s)
        nblk = sum(1 for t, _, _ in walk(blob, s) if t == 'SCDl')
        print('  %-5d %-11s %-7d %-7s %-5s %-8s %s'
              % (i, format(s, ','), nblk, info['codec'], info['channels'],
                 info['rate'] or '-',
                 format(info['samples'], ',') if info['samples'] else '?'))
    if len(segs) > 200:
        print('  …還有 %d 段' % (len(segs) - 200))
    print()
    return 0


# 輸出檔名的守門。--export 是唯一一條「不用 --apply 也會寫檔」的路,
# 而它以前完全不看輸出檔名就覆寫:讀者只要手滑把輸出打成遊戲資料夾裡既有的
# 檔名(.ast / .exe / .sav 都可以),那個檔會被 WAV 內容整個蓋掉,而且 exit 0
# 什麼都不說(2026-09-05 實測:14 bytes 的 precious.txt 變成 74,188 bytes 的 WAV)。
# 現在四件事都擋:
#   0. 輸出不可以是符號連結。⚠️ 這一道不能靠下面那個 os.path.exists():
#      連結指到一個不存在的檔時 exists() 回 False,整段檢查會被跳過,
#      而 wave 模組照樣會沿著連結在資料夾外面建出一個檔。要用 islink 看連結自己。
#   1. 輸出不可以就是輸入那個遊戲檔(用 os.path.samefile 比,不是比字串,
#      這樣 ./x.dat 跟 x.dat 也認得出來是同一個)
#   2. 輸出的資料夾要存在(不存在的話 wave 模組會丟一句
#      「'Wave_write' object has no attribute '_file'」,沒有人看得出那是路徑問題)
#   3. 輸出檔要是**已經存在而且不是 WAV**,拒絕。已經是 WAV 就讓它蓋 ——
#      重跑一次 --export 覆蓋上一次的輸出是正常用法,擋掉反而礙事。
def _check_out_path(src_path, out):
    _reject_symlink(out, '輸出檔')
    if os.path.exists(out):
        try:
            if os.path.samefile(src_path, out):
                raise DataError('輸出檔名就是那個遊戲檔本身(%s)—— 拒絕,'
                                '這會把它整個蓋掉' % out)
        except OSError:
            pass
        if not os.path.isfile(out):
            raise DataError('%s 已經存在而且不是一般檔案 —— 拒絕寫入' % out)
        with open(out, 'rb') as f:
            head = f.read(12)
        if not (head[:4] == b'RIFF' and head[8:12] == b'WAVE'):
            raise DataError('%s 已經存在,而且它不是 WAV 檔 —— 拒絕蓋掉它。'
                            '請換一個輸出檔名' % out)
    d = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(d):
        raise DataError('輸出的資料夾不存在:%s' % d)


# --export:把一段解成 WAV。完全不動遊戲檔。
# 「有 N 個區塊切不出相位,已跳過」那一句很重要:它代表匯出的長度短了一截,
# 而那正是 cmd_import 拒絕寫回去的理由。
def cmd_export(path, idx, out):
    _check_out_path(path, out)
    blob = open(path, 'rb').read()
    segs = segments(blob)
    if idx >= len(segs):
        raise DataError('只有 %d 段,沒有第 %d 段' % (len(segs), idx))
    info, chans = decode_segment(blob, segs[idx])
    if not any(chans):
        raise DataError('這一段解不出取樣(可能是本工具還沒處理的排列方式)')
    write_wav(out, chans, info['rate'])
    n = min(len(c) for c in chans)
    print('  第 %d 段 → %s' % (idx, out))
    print('  編碼器 %s · %d 聲道 · %s Hz · %s 取樣 · %.2f 秒'
          % (info['codec'], len(chans), info['rate'] or 22050,
             format(n, ','), n / float(info['rate'] or 22050)))
    if info['skipped_blocks']:
        print('  ⚠ 有 %d 個區塊本工具切不出相位,已跳過（匯出的長度會短一些）'
              % info['skipped_blocks'])
    return 0


# --import:把 WAV 編回某一段。它是檢查最多的一條:聲道數、取樣率、相位對不對齊,
# 三關都過才准寫;而且還要再加 --apply。
# ⚠️ 但取樣率那一關是**有條件**的:下面寫的是 if info['rate'] and ...,
#    那一段的檔頭沒寫取樣率時,這一關會整個跳過。本站在剛安裝好的原版那份
#    data/audio 上量到 31,034 段裡有 30,824 段沒寫(99.3%),其中 220 段連
#    相位那一關也過得去,只要聲道數對,丟任何取樣率進去都不會被擋(實測
#    cd/aems/batdit.ast 第 0 段吃一個 8000 Hz 的立體聲 WAV,直接放行)。
#    精確講是「聲道數與位元深度一定擋,取樣率看那一段的檔頭有沒有寫」。
# ⚠️ 但**會動遊戲檔的不只它一條**,還有 --restore。檔頭「安全網」第 1 條就是
#    這樣寫的:cmd_restore() 不做上面那三關,直接把 .audiobak 整份蓋回正本。
#    本站拿 8254c.dat 的複本實測(67,324 bytes,歷史資料裡許銘傑那一份語音檔):
#    把正本改壞一個位元組再跑 --restore,md5 回到備份那一份的值。
def cmd_import(path, idx, src, apply_it):
    blob = open(path, 'rb').read()
    segs = segments(blob)
    if idx >= len(segs):
        raise DataError('只有 %d 段,沒有第 %d 段' % (len(segs), idx))
    info = parse_header(blob, segs[idx])
    chans_in, rate = read_wav(src)
    if len(chans_in) != max(1, info['channels']):
        raise DataError('這一段是 %d 聲道,你的 WAV 是 %d 聲道 —— 拒絕寫入'
                        % (info['channels'], len(chans_in)))
    if info['rate'] and rate != info['rate']:
        raise DataError('這一段是 %d Hz,你的 WAV 是 %d Hz —— 拒絕寫入,本工具不幫你重取樣'
                        % (info['rate'], rate))

    # 對齊守門:寫之前先整段試解一次,只要有任何一塊切不出相位就停手。
    # ⚠️ 2026-08-29:匯出時若有區塊切不出相位會被跳過,那會讓 WAV 的第 0 個取樣
    #    其實對應到第 1 個區塊 —— 再寫回去就整段錯位(實測來回訊噪比 -3.1 dB)。
    #    對不齊就不寫。這比「盡量對」安全:錯位的聲音聽起來像壞掉,而且無從追查。
    probe, _chans = decode_segment(blob, segs[idx])
    if probe.get('skipped_blocks'):
        raise DataError('這一段有 %d 個區塊本工具切不出相位 —— 無法保證寫回去的位置對齊,'
                        '拒絕寫入' % probe['skipped_blocks'])
    # 這一段能裝多少取樣是**固定的**:每個 SCDl 的前 4 個位元組寫著它的取樣數,
    # 全部加起來就是「格子總長」。格子不能變大,所以你的錄音只會被補靜音或被切掉。
    #
    # ── 2026-09-04 訂正:寫回去這一段以前無條件用小端讀取樣數 ──────────
    # 解碼那邊(parse_header 的 endian)早就改成看容器決定位元組序,寫入沒跟著改。
    # 舊註解寫的「本站尚未逐檔驗證影響範圍」已經作廢:影響範圍是每一個 GSTR 檔。
    # 小端讀出來是天文數字 → n // 28 大到 _phase_of 連候選都排不出來 →
    # 每一塊都被跳過 → 檔案一個位元組都沒改,而畫面照樣印「✅ 寫好了」。
    #
    # 量法:本站測試機上收藏的模組與語音檔裡,開頭是 SCHl 的檔共 1,129 個,
    # 每一個都先 --export 第 0 段成 WAV,再把那個 WAV 原封不動 --import --apply
    # 回去(所以聲道數與取樣率一定相符),比對前後 md5。用修之前的程式碼:
    #   GSTR 967 個 → 沒有一個檔被改到位元組。191 個一路印到「✅ 寫好了」
    #                 而 md5 前後相同,772 個在相位守門被明說拒絕,
    #                 另外 4 個連匯出都明說解不出來,沒有進到匯入
    #   PT   取 2 MB 以下的 47 個當對照組 → 過得了守門的 4 個都真的改到位元組
    # 例:張誌家 8433a.dat 印「格子總長 5,591,793,664 取樣」「✅ 寫好了
    #     (5,591,793,592 取樣)」,而寫入前後 md5 都是 268cefc3 開頭那一個。
    en = info['endian']
    chain = walk(blob, segs[idx])
    scdl = [(o, l) for t, o, l in chain if t == 'SCDl']
    total = 0
    for o, l in scdl:
        total += struct.unpack(en + 'I', blob[o + 8:o + 12])[0]
    have = min(len(c) for c in chans_in)
    # ⚠️ 那一段的檔頭沒寫取樣率時,這裡印的 Hz 是**你來源 WAV 的取樣率**
    #    (info['rate'] or rate),不是從那一段量到的。看到的數字剛好跟你丟
    #    進來的一樣時就是這個原因,不要把它當成那一段的規格。
    print('  目標   第 %d 段(編碼器 %s · %d 聲道 · %s Hz)'
          % (idx, info['codec'], len(chans_in), info['rate'] or rate))
    print('  來源   %s(%s 取樣)' % (src, format(have, ',')))
    print('  這一段的格子總長 %s 取樣' % format(total, ','))
    if have < total:
        print('  ⚠ 你的比較短,不足的部分會補靜音')
    elif have > total:
        print('  ⚠ 你的比較長,超出的會被切掉(格子是定長的,不能變大)')
    if not apply_it:
        print('\n  這是預覽,沒有動到任何檔案。確定要寫就加 --apply\n')
        return 0

    bak = path + BACKUP_SUFFIX
    # 兩個都要看,理由不一樣:
    #   · 正本是符號連結 → os.replace 只會把連結本身換成一個真的檔,
    #     連結原本指到的那個遊戲檔反而留著舊內容,讀者會以為換好了。
    #   · 備份是符號連結 → --restore 會從資料夾外面讀東西回來蓋正本。
    _reject_symlink(path, '要寫入的那個遊戲檔')
    _reject_symlink(bak, '備份檔')
    if not os.path.exists(bak):
        _atomic_copy(path, bak)
        print('  已備份 → %s' % os.path.basename(bak))

    # 原地填格子:整個檔先讀進記憶體,只覆寫每個 SCDl 裡面那些 15 個位元組的組,
    # 區塊長度、容器結構、後面所有段的位移全部不動。
    # (專案鐵律:封裝檔不重新打包,重打包會把你不知道的東西弄丟。)
    buf = bytearray(blob)
    pos = 0
    state = [(0, 0) for _ in chans_in]
    worst = 0
    wrote = 0                   # 真的被覆寫掉的「15 個位元組一組」有幾組
    for o, l in scdl:
        body = bytearray(buf[o + 8:o + l])
        # 取樣數與兩個聲道的起點,跟解碼讀的是同一批欄位,位元組序當然要同一個。
        n = struct.unpack(en + 'I', bytes(body[:4]))[0]
        ng = n // GROUP_SAMPLES
        if ng == 0:
            continue
        if len(chans_in) == 2:
            lo, ro = struct.unpack(en + 'II', bytes(body[4:12]))
            spans = [(12 + lo, 12 + ro), (12 + ro, len(body))]
        else:
            spans = [(4, len(body))]
        for ci, (a, b) in enumerate(spans):
            part = bytes(body[a:b])
            pre = _phase_of(part, ng)
            if pre is None:
                continue
            # ⚠️ 起始狀態要跟**解碼端將來會用的那一個**一模一樣,否則每個區塊
            #    的開頭都會對不上。decode_segment 對立體聲且 pre>=4 的區塊,
            #    是從這一塊開頭那 4 個位元組讀出它自己的起始狀態;寫入端本來
            #    卻一律用跨區塊延續的 state[ci],而且從來不重寫那 4 個位元組。
            #    實測(2026-09-05,menu9.asf 的第 1000~1004 個 SCDl 組成的
            #    5 區塊測試檔):--export → --import --apply → --export 之後,
            #    29,400 個取樣有 486 個不同、最大誤差 11,436(訊號峰值 32,052),
            #    而且誤差全部集中在區塊開頭再往後衰減。改用同一個種子之後
            #    29,400 個取樣 0 個不同。
            #    那 4 個位元組在 q 前面,寫入迴圈從 q 開始,所以不會被蓋掉。
            if len(chans_in) == 2 and pre >= 4:
                cur0, prev0 = struct.unpack('<hh', part[pre - 4:pre])
                prev, cur = prev0, cur0
            else:
                prev, cur = state[ci]
            q = a + pre
            for g in range(ng):
                seg = []
                for k in range(GROUP_SAMPLES):
                    j = pos + g * GROUP_SAMPLES + k
                    seg.append(chans_in[ci][j] if j < len(chans_in[ci]) else 0)
                h, pay, prev, cur, err = encode_group(seg, prev, cur)
                body[q] = h
                body[q + 1:q + 15] = pay
                q += GROUP_BYTES
                worst = max(worst, err)
                wrote += 1
            state[ci] = (prev, cur)
        buf[o + 8:o + l] = bytes(body)
        pos += ng * GROUP_SAMPLES

    # ⚠️ 一組都沒有寫進去就不准印成功(2026-09-04 加的網)。
    #    上面那個位元組序 bug 的長相就是這樣:每一塊都被跳過、檔案一個位元組都沒變,
    #    畫面卻印「✅ 寫好了」。以後再有哪一種容器分支讓寫入整段落空,
    #    這裡會擋下來,而不是讓你以為換好了。
    if wrote == 0:
        raise DataError('這一段一個位元組都沒有被寫進去,拒絕印成功。'
                        '請把這個檔回報給本站,不要當成已經換好了')

    # 先寫一個暫存檔,寫完了才用 os.replace 換成正式名字 —— 跟 _atomic_copy
    # 同一套。直接 open(path, 'wb') 的話,**那一行呼叫下去檔案當場就變 0 bytes**,
    # 之後才慢慢寫回去;中途被中斷(按 Ctrl-C、磁碟滿、外接碟拔掉)就會留下
    # 一個半截的遊戲檔。這支工具處理的檔可以到 24 MB
    # (data/audio/cd/aems/crowd4a.ast),那個窗口不是瞬間。
    # 備份還是排在寫入之前,兩道是互補的:.audiobak 保住舊內容,
    # 這一段保住「正本要嘛是舊的、要嘛是新的,不會是半截的」。
    # ⚠️ 2026-09-05:暫存檔的名字以前是 path + '.part',**猜得到**;
    #    有人先在那裡放一個指向資料夾外面的符號連結,open(...,'wb') 就會沿著它
    #    把外面的檔截成 0。現在改用 mkstemp(O_CREAT|O_EXCL,不跟連結走)。
    new_bytes = bytes(buf)
    fd, tmp_path = _mkstemp_beside(path, 'write')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(new_bytes)
            f.flush()
            os.fsync(f.fileno())   # 少了這一步,斷電之後換上去的可能是空殼
        try:
            # 換名之後權限跟著新檔走,所以先把正本的權限抄過去。
            shutil.copymode(path, tmp_path)
        except OSError:
            pass
        _replace_live(tmp_path, path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    # 寫完之後把檔案讀回來,跟「本來要寫的那一份」逐位元組比對。
    # 對不起來就用備份換回去,並以非 0 的離開碼收場 —— 不可以只印一句 ❌
    # 然後照樣回報成功,那會讓批次腳本以為這一步過了,繼續往下做。
    _verify_written(path, new_bytes, bak)
    print('  ✅ 寫好了(%s 取樣)。要還原就跑 --restore\n' % format(pos, ','))
    return 0


def _verify_written(path, expect, bak):
    """寫完之後的複驗。對不起來就自動還原,並讓整支以非 0 收場。

    為什麼要有這一道:os.replace 成功不等於磁碟上的內容就是你要的
    (檔案系統滿了、外接碟中途掉線、防毒軟體攔截改寫,都做得出這種事)。
    複驗讀的是磁碟,不是記憶體裡那份 buf。
    """
    try:
        with open(path, 'rb') as f:
            got = f.read()
    except OSError as err:
        why = '讀不回來(%s)' % err
    else:
        if got == expect:
            return
        if len(got) != len(expect):
            why = ('磁碟上是 %s bytes,本來要寫的是 %s bytes'
                   % (format(len(got), ','), format(len(expect), ',')))
        else:
            # 長度一樣的時候要說出「第幾個位元組開始不一樣」,
            # 不然畫面會印出兩個一模一樣的數字,讀者看不懂到底哪裡不對。
            bad = next(k for k in range(len(got)) if got[k] != expect[k])
            why = ('長度一樣都是 %s bytes,但從第 %s 個位元組起就跟本來要寫的不同'
                   % (format(len(got), ','), format(bad, ',')))
    try:
        _restore_from_backup(bak, path)
        undone = '  已經自動用 %s 把它換回去了。\n' % os.path.basename(bak)
    except BaseException as err:
        undone = ('  ⚠️ 自動還原也失敗了(%s),請自己跑:\n'
                  '     python3 mvp_audio.py "%s" --restore\n' % (err, path))
    raise SystemExit(
        '寫完之後複驗對不起來:%s。\n%s'
        '  請不要繼續用這個檔,改用 --restore 或你自己另外留的那一份備份。'
        % (why, undone))


def _audio_container_error(path):
    """用格式驗這個檔完不完整。

    回傳 None  = 裡面找不到 SCHl,沒有格式可以驗(這種檔本工具本來也處理不了)
    回傳 ''    = 驗過而且完整
    回傳一句話 = 驗過而且壞了,那句話說它壞在哪

    判準:每一段的檔頭有一個標籤 0x85 寫著「這一段有幾個取樣」,
    而那一段每個 SCDl 的前 4 個位元組各自寫著自己那一塊有幾個取樣。
    後者加起來必須等於前者 —— 檔案被截斷就會少掉尾巴那幾塊,兩個數字對不上。

    ⚠️ 為什麼不用「最後一塊是不是 SCEl」當判準:本站收藏的社群語音裡有兩個檔
       (邱子愷 3499a.dat / 3499d.dat)本來就沒有 SCEl 收尾,拿那個當判準會把
       它們的合法備份也擋掉。
    ⚠️ 這個判準量過三棵樹:剛安裝好的原版英文版 data/audio(31,034 段)、
       測試機的 data/audio(40,458 段)、測試機收藏的社群語音(69 段),
       合計 71,561 段,每一段的「宣告值」與「加總值」都相等。
    ⚠️ 它擋得住「尾巴被切掉」,擋不住「中間被改壞但長度沒變」——
       真正保得住你的,還是你自己另外留的那一整包備份。
    """
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as err:
        return '讀不到 %s(%s)。' % (path, err)
    if b'SCHl' not in data:
        return None
    starts = segments(data)
    if not starts:
        return None
    for st in starts:
        try:
            info = parse_header(data, st)
        except (DataError, struct.error, IndexError):
            return '位移 %d 的那一段檔頭讀不出來。' % st
        chain = walk(data, st)
        if not chain or chain[0][0] != 'SCHl':
            return '位移 %d 的那一段區塊接龍讀不出來。' % st
        decl = info.get('samples')
        if not decl:
            # 檔頭沒寫取樣總數就沒有東西可以比。本站量到的三棵樹裡沒有這種段,
            # 真遇到就跳過這一段,不要假裝驗過。
            continue
        total = 0
        for tag, off, ln in chain:
            if tag != 'SCDl':
                continue
            try:
                total += struct.unpack(info['endian'] + 'I', data[off + 8:off + 12])[0]
            except struct.error:
                return '位移 %d 的那一段有一塊 SCDl 讀不出取樣數。' % st
        if total != decl:
            return ('位移 %d 的那一段檔頭宣告 %s 個取樣,實際只湊得出 %s 個'
                    '(尾巴被切掉了)。'
                    % (st, format(decl, ','), format(total, ',')))
    return ''


# --restore:只認本工具自己做的 .audiobak。找不到就明說「沒有找到本工具做的備份」,
# 不去猜資料夾裡別的檔案。猜錯就是拿別的東西蓋掉你的遊戲檔。
def cmd_restore(path):
    bak = path + BACKUP_SUFFIX
    # 先擋符號連結,再問「在不在」。順序不能反:指向不存在的檔的連結,
    # os.path.exists() 會說「不在」,那樣就會被當成「還沒備份過」而放行。
    _reject_symlink(bak, '備份檔')
    _reject_symlink(path, '要還原的那個檔')
    if not os.path.lexists(bak):
        print('  沒有找到本工具做的備份\n')
        return 1

    # ── 用格式驗備份完不完整(2026-09-05 加)────────────────────────
    # _restore_from_backup 的通用地板(「不得小於正本一半」)對這一支擋不住:
    # 實測把 20,352 bytes 的 4631a.dat 的備份截成 60%(12,211 bytes)再 --restore,
    # 三道結構檢查(BIGF / LOCH / MZ)都走不到,地板也過得去,
    # 於是印「已還原」、exit 0,而遊戲檔當場從 20,352 變成 12,211 bytes。
    # 這一支有格式可以驗,所以不該退到那條地板 —— 見 _audio_container_error。
    why = _audio_container_error(bak)
    if why:
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (path, why))

    # 這支工具是純原地填格子,寫回去不改長度(檔頭「安全網」第 5 條),
    # 所以備份跟正本的大小本來就該一樣,不一樣就代表有一邊被動過手腳。
    # ⚠️ 但這一條**只在正本自己結構也完整的時候**才拿來擋:
    #    正本被寫到一半正是最需要還原的時候,那時候大小一定對不上,
    #    要是照樣攔下來,就變成「讀者最需要救援的時候把救援關掉」。
    if why == '' and os.path.exists(path) and _audio_container_error(path) == '':
        nb, nd = os.path.getsize(bak), os.path.getsize(path)
        if nb != nd:
            raise SystemExit(
                '備份是 %d bytes,要被蓋掉的那個檔是 %d bytes —— 兩邊結構都完整\n'
                '  卻不一樣大。這支工具不改長度,所以這種情形代表那個檔不是本工具\n'
                '  改出來的(可能被別的工具動過)。不敢拿備份覆蓋 %s。' % (nb, nd, path))

    _restore_from_backup(bak, path)

    # 複驗:還原完之後正本必須跟備份**逐位元組**相同,而且比的是完整長度。
    # (不可以用 zip() 那種「兩邊一起走、短的那邊先停」的比法 ——
    #  少掉的尾巴永遠比不到,截斷會從頭到尾都是綠的。)
    with open(bak, 'rb') as f1, open(path, 'rb') as f2:
        same = (os.path.getsize(bak) == os.path.getsize(path)
                and f1.read() == f2.read())
    if not same:
        raise SystemExit(
            '還原之後 %s 跟備份對不起來 —— 請不要繼續用這個檔,\n'
            '  改用你自己另外留的那一份備份。' % path)
    print('  已還原 %s(逐位元組複驗過,跟備份相同)\n' % os.path.basename(path))
    return 0


def _seg_no(text):
    """段號一定是非負整數。打錯的話給一句中文,不要讓 int() 丟 ValueError 的
    traceback —— 這一課的讀者看不懂那個。"""
    try:
        n = int(text)
    except ValueError:
        raise DataError('段號要填數字,你填的是「%s」' % text)
    if n < 0:
        raise DataError('段號不能是負數(你填的是 %d)' % n)
    return n


# 進入點。動作是互斥的,判斷的順序就是優先權:
# --restore > --list > --export > --import,什麼都不給就印檔頭。
# DataError 一律變成一行人看得懂的話 + exit code 1,不丟 traceback 給讀者看。
# (最常打錯的幾種情形 —— WAV 檔名打錯、丟了不是 WAV 的檔、段號打成非數字、
#  輸出資料夾不存在 —— 已經在 read_wav / _seg_no / _check_out_path 裡先變成
#  DataError,所以走到這裡就都是一句中文,不會是 traceback。)
def main():
    ap = argparse.ArgumentParser(description='MVP Baseball 2005 聲音解碼／編碼工具')
    ap.add_argument('path', help='遊戲裡的聲音檔')
    ap.add_argument('--info', action='store_true', help='看檔頭')
    ap.add_argument('--list', action='store_true', help='列出裡面每一段')
    ap.add_argument('--export', nargs=2, metavar=('段號', '輸出.wav'))
    ap.add_argument('--import', nargs=2, metavar=('段號', '來源.wav'), dest='imp')
    ap.add_argument('--apply', action='store_true', help='真的寫入(不加只做預覽)')
    ap.add_argument('--restore', action='store_true', help='還原本工具做的備份')
    a = ap.parse_args()

    if not os.path.isfile(a.path):
        print('  ❌ 找不到 %s' % a.path)
        return 2
    try:
        if a.restore:
            return cmd_restore(a.path)
        if a.list:
            return cmd_list(a.path)
        if a.export:
            return cmd_export(a.path, _seg_no(a.export[0]), a.export[1])
        if a.imp:
            return cmd_import(a.path, _seg_no(a.imp[0]), a.imp[1], a.apply)
        return cmd_info(a.path)
    except DataError as err:
        print('  ❌ %s' % err)
        return 1


# Ctrl-C 之後要跟讀者說的那句話。看的是 _LIVE_REPLACED 這個旗標
# (os.replace 真的做過才會是 True),不是用猜的 —— 猜錯的兩個方向都很貴:
# 說「沒動到」而其實動到了,他就不會去還原;說「動到了」而其實沒有,
# 他會白跑一次 --restore(而那一次會因為找不到備份而失敗,更嚇人)。
def _interrupt_note():
    if _LIVE_REPLACED:
        return ('  ⚠️ 已中斷,而且遊戲檔**已經被換成新的內容了**。\n'
                '     要回到原樣就跑:--restore')
    # 第三態:換名已經開始、還沒有結論。正常情況走不到這裡(_NoInterrupt 會把
    # Ctrl-C 押到登記之後),但裝不上處理器的時候它就是保險 —— 這種時候寧可說
    # 「不確定」也不可以說「沒動到」。
    if _LIVE_REPLACING:
        return ('  ⚠️ 已中斷,而中斷的時候正在替換 %s ——\n'
                '     換成功了沒有,本工具不敢保證。請跑 --restore 還原,\n'
                '     或自己拿 %s 比對。' % (_LIVE_REPLACING, BACKUP_SUFFIX))
    return '  已中斷。遊戲檔一個位元組都沒有動到。'


# ─────────────────────────────────────────────────────────
#  自我測試(--selftest):不碰任何遊戲檔,全部在系統暫存資料夾裡做
#  每一道守門都下一個餌 —— 沒有反向測試的檢查,分不出「沒問題」跟「根本沒跑」。
# ─────────────────────────────────────────────────────────
def selftest():
    global _LIVE_REPLACED
    # ⚠️ 這一關要排在最前面:python -O 會把整支程式裡的 assert 全部拿掉,
    #    下面每一個餌都是靠 assert 判定的,少了它們這支測試會一路印「全部通過」
    #    卻什麼都沒有驗到 —— 那比沒有測試更危險。寧可拒跑。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    baits = 0
    dirs = []

    def _new_dir():
        d = tempfile.mkdtemp(prefix='mvp_audio_selftest-')
        dirs.append(d)
        return d

    def _put(path, data):
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def _get(path):
        with open(path, 'rb') as f:
            return f.read()

    def _expect(exc, fn, what):
        try:
            fn()
        except exc:
            return
        except Exception as err:
            raise AssertionError('%s:丟出來的是 %r,不是 %s'
                                 % (what, err, exc.__name__))
        raise AssertionError('%s:竟然沒有被擋下來' % what)

    try:
        # ── 一、目的地是符號連結就拒絕 ───────────────────────
        # 餌:備份檔那個名字先被換成一個指向資料夾外面的連結。
        # 沒有這一道的話,備份會沿著它把外面那個檔覆蓋掉。
        d = _new_dir()
        outside = _put(os.path.join(d, 'OUTSIDE.bin'), b'DO NOT TOUCH')
        box = os.path.join(d, 'box')
        os.mkdir(box)
        live = _put(os.path.join(box, 'g.dat'), b'LIVE' * 64)
        bak = os.path.join(box, 'g.dat' + BACKUP_SUFFIX)
        os.symlink(outside, bak)
        _expect(DataError, lambda: _atomic_copy(live, bak), '備份檔是符號連結')
        baits += 1
        assert _get(outside) == b'DO NOT TOUCH', '資料夾外面那個檔被動到了'

        # ── 二、暫存檔的名字不可以是猜得到的 ─────────────────
        # 餌:把三個「以前用過的」固定名字全部先佔成指向外面的連結。
        # 舊版是 open('<目的檔>.part', 'wb'),那一行會沿著連結把外面截成 0。
        os.remove(bak)
        planted = ['g.dat.part', 'g.dat' + BACKUP_SUFFIX + '.part', 'g.dat.tmp']
        for name in planted:
            os.symlink(outside, os.path.join(box, name))
        _atomic_copy(live, bak)                       # 陰性對照:正常流程要成功
        baits += len(planted)
        assert _get(bak) == _get(live), '備份的內容不對(陰性對照沒過)'
        assert _get(outside) == b'DO NOT TOUCH', '猜得到的暫存名字把外面的檔寫壞了'
        for name in planted:
            assert os.path.islink(os.path.join(box, name)), '%s 被當成一般檔用掉了' % name
        left = sorted(os.listdir(box))
        assert left == sorted(['g.dat', 'g.dat' + BACKUP_SUFFIX] + planted), \
            '資料夾裡留下了不該有的東西:%s' % left

        # ── 三、還原是原子的:換名失敗,正本要原封不動 ────────
        # 餌:把 os.replace 換成一個一定會爆的函式。
        # 舊版是 shutil.copy2(備份, 正本),正本在那一刻就已經被截成 0 了。
        d2 = _new_dir()
        live2 = _put(os.path.join(d2, 'g.dat'), b'NEW' * 100)
        bak2 = _put(os.path.join(d2, 'g.dat' + BACKUP_SUFFIX), b'OLD' * 100)

        def _boom(*a, **k):
            raise RuntimeError('餌:故意讓換名失敗')

        _LIVE_REPLACED = False
        real_replace = os.replace
        os.replace = _boom
        try:
            _expect(RuntimeError, lambda: _do_copy(bak2, live2), '換名失敗')
        finally:
            os.replace = real_replace
        baits += 1
        assert _get(live2) == b'NEW' * 100, '換名失敗,正本卻已經被動過了'
        assert _LIVE_REPLACED is False, '換名失敗,旗子卻沒有放下來'
        assert sorted(os.listdir(d2)) == sorted(['g.dat', 'g.dat' + BACKUP_SUFFIX]), \
            '失敗之後留下了暫存檔沒收掉'

        # ── 四、還原前的逐位元組比對 ─────────────────────────
        # 餌:讓複製只寫進去三個位元組。長度對不上就必須拒絕換上去。
        def _short(fin, fout, length=0):
            fout.write(fin.read()[:3])

        real_cfo = shutil.copyfileobj
        shutil.copyfileobj = _short
        try:
            _expect(DataError, lambda: _do_copy(bak2, live2), '還原的內容對不起來')
        finally:
            shutil.copyfileobj = real_cfo
        baits += 1
        assert _get(live2) == b'NEW' * 100, '比對沒過,正本卻已經被換掉了'

        # 陰性對照:上面兩個餌拿掉之後,還原本身要真的會動作
        _LIVE_REPLACED = False
        _do_copy(bak2, live2)
        assert _get(live2) == b'OLD' * 100, '正常的還原沒有把備份換上去'
        assert _LIVE_REPLACED is True, '換過正本卻沒記下來(Ctrl-C 會說錯話)'

        # ── 五、寫完之後的複驗 ───────────────────────────────
        d3 = _new_dir()
        live3 = _put(os.path.join(d3, 'g.dat'), b'BAD!' * 50)
        bak3 = _put(os.path.join(d3, 'g.dat' + BACKUP_SUFFIX), b'GOOD' * 50)
        _verify_written(live3, b'BAD!' * 50, bak3)     # 陰性對照:相符就安靜通過
        # 餌:磁碟上的內容跟「本來要寫的」不一樣 —— 必須非 0 收場而且自動還原
        _expect(SystemExit,
                lambda: _verify_written(live3, b'WANT' * 50, bak3), '複驗對不起來')
        baits += 1
        assert _get(live3) == b'GOOD' * 50, '複驗沒過卻沒有自動還原'

        # ── 六、備份本身壞掉的那兩道(既有守門,一起下餌)──────
        d4 = _new_dir()
        live4 = _put(os.path.join(d4, 'g.dat'), b'x' * 1000)
        bak4 = _put(os.path.join(d4, 'g.dat' + BACKUP_SUFFIX), b'')
        _expect(SystemExit,
                lambda: _restore_from_backup(bak4, live4), '0 bytes 的備份')
        baits += 1
        _put(bak4, b'x' * 100)                          # 不到正本的一半
        _expect(SystemExit,
                lambda: _restore_from_backup(bak4, live4), '只有正本一成的備份')
        baits += 1
        assert _get(live4) == b'x' * 1000, '壞掉的備份還是把正本蓋掉了'

        # ── 七、--export 的輸出檔名守門 ──────────────────────
        d5 = _new_dir()
        prec = _put(os.path.join(d5, 'precious.txt'), b'14 bytes here!')
        src5 = _put(os.path.join(d5, 'g.dat'), b'SCHl')
        link5 = os.path.join(d5, 'out.wav')
        os.symlink(prec, link5)
        _expect(DataError, lambda: _check_out_path(src5, link5), '輸出檔是符號連結')
        baits += 1
        assert _get(prec) == b'14 bytes here!', '輸出沿著連結把外面那個檔寫壞了'
        # 餌:指向不存在的檔的連結。os.path.exists() 對它回 False,
        # 只看 exists 的話這一關會整個被跳過。
        dang = os.path.join(d5, 'dangling.wav')
        os.symlink(os.path.join(d5, 'nope'), dang)
        assert os.path.exists(dang) is False, '這個餌的前提不成立'
        _expect(DataError,
                lambda: _check_out_path(src5, dang), '指向不存在的檔的符號連結')
        baits += 1
        # 既有那道:已經存在而且不是 WAV
        _expect(DataError, lambda: _check_out_path(src5, prec), '已經存在的非 WAV 檔')
        baits += 1
        _check_out_path(src5, os.path.join(d5, 'ok.wav'))   # 陰性對照:新檔名要放行

        # ── 八、Ctrl-C 說的話要跟旗標走 ──────────────────────
        _LIVE_REPLACED = False
        assert '一個位元組都沒有動到' in _interrupt_note(), '沒換過卻沒說沒動到'
        _note_live_replaced()
        assert '已經被換成新的內容' in _interrupt_note(), '換過了卻說什麼都沒動到'
        baits += 1
        _LIVE_REPLACED = False
        # 第三態:停在「正在換」的中間 —— 這種時候只能說不確定,不可以說沒動到。
        _note_replacing(os.path.join('someplace', 'g.dat'))
        assert '正在替換' in _interrupt_note(), '停在換名中間卻說成一個位元組都沒動'
        baits += 1
        _note_replacing(None)
        assert '一個位元組都沒有動到' in _interrupt_note(), \
            '登記收掉之後應該回到「沒動到」'

        # ── 九、編碼／解碼本身沒有被上面那些改動碰到 ──────────
        import random
        rnd = random.Random(20260905)
        want = [rnd.randint(-8000, 8000) for _ in range(GROUP_SAMPLES)]
        h, pay, p1, c1 = encode_group(want, 0, 0)[:4]
        back, p2, c2 = decode_group(h, pay, 0, 0)
        assert len(back) == GROUP_SAMPLES, '一組解出來的取樣數不對'
        assert (p1, c1) == (p2, c2), '編碼與解碼收尾的狀態對不上'
        assert (h >> 4) <= 3, '編碼吐出來的表頭高半位元組超出 0-3'

        # ── 十、匯出的 WAV 也是「寫」,一樣不跟著符號連結走 ────
        # _check_out_path 已經先看過一次,但「看過」跟「真的開檔」是兩個時刻。
        # 餌:直接叫 write_wav 去寫一個指向資料夾外面的連結 —— 舊版的
        # wave.open(path, 'wb') 會沿著它,把外面那個檔整個蓋成一個 WAV。
        d6 = _new_dir()
        keep6 = _put(os.path.join(d6, 'OUTSIDE.bin'), b'DO NOT TOUCH')
        sub6 = os.path.join(d6, 'box')
        os.mkdir(sub6)
        link6 = os.path.join(sub6, 'out.wav')
        os.symlink(keep6, link6)
        _expect(DataError, lambda: write_wav(link6, [[0, 1, 2]], 22050),
                '匯出的目的檔是符號連結')
        baits += 1
        assert _get(keep6) == b'DO NOT TOUCH', '匯出沿著連結把外面那個檔寫壞了'
        assert os.path.islink(link6), '連結被當成一般檔用掉了'
        # 陰性對照:正常的檔名要真的寫得出 WAV,而且不可以留下暫存檔
        ok6 = os.path.join(sub6, 'ok.wav')
        write_wav(ok6, [[0, 1, 2]], 22050)
        assert _get(ok6)[:4] == b'RIFF', '正常的匯出沒有寫出 WAV(陰性對照沒過)'
        assert sorted(os.listdir(sub6)) == ['ok.wav', 'out.wav'], \
            '匯出之後留下了暫存檔:%s' % sorted(os.listdir(sub6))

        # ── 十一、Ctrl-C 落在「換名成功」與「登記」中間 ────────
        # 這正是本輪要修的那個窗口。餌:把 os.replace 換成「先真的換名,
        # 再把當下裝著的 SIGINT 處理器叫起來」。有 _NoInterrupt 守著的話,
        # 那一下只會被記著,登記照樣做得完;守門被拆掉的話,叫到的就是
        # Python 預設的處理器,當場丟 KeyboardInterrupt,登記那一行永遠跑不到,
        # 於是 Ctrl-C 的收尾會說「一個位元組都沒有動到」——而檔案已經換了。
        d7 = _new_dir()
        live7 = _put(os.path.join(d7, 'g.dat'), b'OLD' * 100)
        fd7, tmp7 = _mkstemp_beside(live7, 'write')
        with os.fdopen(fd7, 'wb') as f7:
            f7.write(b'NEW' * 100)

        def _replace_then_sigint(a, b):
            real_replace(a, b)
            h2 = signal.getsignal(signal.SIGINT)
            if callable(h2):
                h2(signal.SIGINT, None)
            else:
                raise KeyboardInterrupt

        _LIVE_REPLACED = False
        _note_replacing(None)
        os.replace = _replace_then_sigint
        try:
            _expect(KeyboardInterrupt,
                    lambda: _replace_live(tmp7, live7), '換名成功之後才收到 Ctrl-C')
        finally:
            os.replace = real_replace
        baits += 1
        assert _get(live7) == b'NEW' * 100, '這個餌的前提不成立(檔案根本沒被換)'
        assert _LIVE_REPLACED is True, \
            '換名已經做完卻沒有登記 —— 收尾會說「一個位元組都沒有動到」'
        assert _LIVE_REPLACING is None, '登記沒有收乾淨'
        assert '已經被換成新的內容' in _interrupt_note(), '換過了收尾卻說錯話'

        # 餌:換名**自己**失敗 —— 這時候「沒動到」才是真的,旗子不可以舉起來。
        fd8, tmp8 = _mkstemp_beside(live7, 'write')
        os.close(fd8)
        _LIVE_REPLACED = False
        os.replace = _boom
        try:
            _expect(RuntimeError, lambda: _replace_live(tmp8, live7), '換名自己失敗')
        finally:
            os.replace = real_replace
        baits += 1
        assert _LIVE_REPLACED is False, '換名失敗,旗子卻舉了起來'
        assert _LIVE_REPLACING is None, '換名失敗,「正在換」的登記卻沒收掉'
        assert '一個位元組都沒有動到' in _interrupt_note(), '換名失敗卻不敢說沒動到'
        assert _get(live7) == b'NEW' * 100, '換名失敗,檔案卻被動過了'
        os.remove(tmp8)
        _LIVE_REPLACED = False
    finally:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)

    print('自我測試:全部通過(含 %d 個反向餌)' % baits)
    return 0


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

if __name__ == '__main__':
    # --selftest 要排在最前面判斷:它不需要遊戲檔,
    # 走進 main() 反而會因為「沒給路徑」被 argparse 擋下來。
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 離開碼一律 130(128 + SIGINT),**不可以是 0**:
        # 0 會讓批次腳本、.bat、或包在外面的懶人包以為這一步做完了,繼續往下做。
        print()
        print(_interrupt_note())
        print()
        sys.exit(130)
