#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_swap_chant.py — 把某位球員的專屬應援曲指給另一位球員

EA 錄了 57 組球員專屬應援曲。這支腳本可以把其中一首指給你想要的球員，
例如讓陳金鋒用某位大聯盟球員的應援曲。
(57 這個數字是這樣數的:剛安裝好的英文版原版、剛安裝好的中文版原版、
 本站測試機那一份,三份 spch_cht.txt 裡 pchants: 開頭的群組都是 57 組、
 沒有重複,號碼集合完全相同,底下共 58 個音檔條目(0808 那一組有兩首)。
 其中 pchants:0538 在兩份原版的名冊 data/database/attrib.dat 裡都對不到球員,
 所以「有專屬應援曲的球員」是 56 位、「應援曲群組」是 57 組。這一行原本寫
 「56 位球員」,跟本檔下面「這支腳本只動 pchants 那 57 組」那句對不上。)

**只改一個純文字檔**,不動 54 MB 的音檔資料。

應援曲的對應鏈長這樣,除了最後那一層之外全部是純文字:
  data/audio/chants/spch_cht.txt    群組索引(這支腳本只動這個)
    pchants:0004                     群組名,那四位數就是球員的 audioid
      pchant.0004...wav  0           群組裡的音檔,後面是群組內部的位移
  data/audio/chants/chantdat.off    每個群組在音檔資料裡的 起始,長度
  data/audio/cd/chants/chantdat.big 真正的音檔(54 MB,EA 自家格式)

所以「把應援曲指給別人」就是**把群組名的四位數換掉**,一行文字的事。

⚠️ **做不到的事:放進你自己錄的音檔。**
   那需要把聲音編成 EA 自家的音訊格式,本站還沒有做出那個編碼器。
   這支腳本只能在遊戲裡**已經有的**應援曲之間重新指派。

   ⚠️ 2026-08-31 訂正上面那句:編碼器 2026-08-29 做出來了,
      在教學站「換掉遊戲的聲音」那一課。所以「換內容」不再是整條路都不通,
      卡住的只剩「切不出相位的那些段落」。
      但**這一支腳本的範圍沒有變**:它只改一行純文字,不碰那 54 MB 的音檔。
      要換音檔內容請走那一課,不要期待這一支。
      (訂正紀錄留著不刪,是因為「把未解貼在整條路上而不是真正卡住的那一格」
       正是本站踩過的坑,留著提醒下一個人。)

你給它什麼、它產出什麼
--------------------
輸入:**遊戲資料夾**的路徑(裡面看得到 mvp2005.exe 跟 data 那一層)。
      腳本自己往下找 data/audio/chants/spch_cht.txt,不用你指到檔案。
      名冊 data/database/attrib.dat 有就讀、沒有也照跑,差別只是顯示不出球員名字。

輸出:
  · --list:什麼都不寫,只把遊戲裡的球員專屬應援曲印出來給你看。
  · --give 不加 --apply:什麼都不寫,只印出「哪一行會變成什麼樣」。
  · --give 加 --apply:改 spch_cht.txt 裡**一行**的群組名,其餘每一行原封不動;
    動手之前先留一份 spch_cht.txt.chantbak。
  · --restore:把那份備份放回去(備份本身留著不刪)。

安全網在哪
---------
· 預設是預覽。沒加 --apply 一個位元組都不寫。
· 索引檔是**用位元組讀、用位元組寫**的,整份沒有解碼成文字再編碼回去,
  所以沒被你動到的行不可能因為編碼轉換而悄悄改變。行尾是 CRLF 還是 LF 也照原樣沿用。
· 目標球員本來就有專屬應援曲的話直接停手,不製造重複的群組名。
· 寫出去之前先自己算一次:群組數、音檔數要跟改之前一樣,不能有重複群組名,
  檔案總長度也要剛好等於「原長度 + 新舊群組名的長度差」。任何一項對不上就中止。
· 寫檔是先寫一個暫存檔再原子改名,中途斷掉不會留下半截的索引檔。
  暫存檔的名字是隨機的(mkstemp),而且開在同一個資料夾裡 ——
  猜得到的名字(以前是 .tmp / .part)會被人先擺一個指到別處的符號連結,
  寫下去就傷到遊戲資料夾外面的檔。要寫的名字是符號連結時一律停手。
· 備份用 _atomic_copy():要嘛完整、要嘛不存在,不會留下半截的 .chantbak。
· 目標球員的 audioid 超過四位數就停手:群組名在這個檔裡是固定寬度的
  (量到的三份 spch_cht.txt,90 個群組行每一行都剛好 32 bytes),
  寫成五位數會讓那一行多一個位元組,遊戲吃不吃得下本站沒有測過。
· 還原前先把備份**當成索引檔讀一次**(群組數、音檔數、有沒有重複的群組名、
  結尾是不是完整的一行),再交給 _restore_from_backup() 擋一次;
  蓋回去之後還會整份逐位元組跟備份對一次,對不上就不印成功。
  免得拿半截備份去蓋掉本來好好的檔。
· 還原**不是**直接往正本寫。先在同一個資料夾寫一個隨機名字的暫存檔,
  落地、對過位元組,最後才原子改名換上去。所以還原做到一半失敗
  (磁碟滿、外接碟拔掉、按了 Ctrl-C),正本還是還原之前那一份,不會變成半截。
· --restore **不要求索引檔還在**:被刪掉、被別的工具搬走的時候正是最需要
  還原的時候,只要 .chantbak 在就還原得回來。
· 按 Ctrl-C 的時候,「你的檔動了沒」那句話是真的。換名跟登記包成一段
  不可中斷的動作(離開那一段訊號照常丟出,結束碼還是 130),
  所以不會發生「磁碟上已經換好了、螢幕上卻說一個位元組都沒動」。
· 「你的檔動了沒」這句話不是只有 Ctrl-C 會講。換名之後才失敗的那些
  (作業系統擋下來、寫完複驗時讀不回來)也照實講,並且把還原指令印出來;
  換名之前就停手的照舊只說停手的理由,那一句一個字都沒有變。
· 備份已經存在就保留最早那一份,不會被第二次執行覆蓋掉 ——
  但動手之前會先確認那一份還能用(不是 0 bytes、也不是一個資料夾),
  不能用就停手不寫,不會讓你在「沒有還原點」的狀態下改遊戲檔。

做不到的事(除了上面那條音檔)
---------------------------
· 不會幫你新增一組應援曲,只會把既有的那一組改指給別人。
  來源那位球員從此就沒有專屬應援曲了。
· 不驗「遊戲會不會照這個索引播放」。腳本只驗得到「檔案改對了」,
  聲音對不對要靠你的耳朵,本站沒有辦法自動測這件事。
· 不動 chantdat.off,也不動 chantdat.big。群組在音檔資料裡的位置沒有變,
  變的只是「哪個 audioid 對到這一組」。

寫回封裝檔一律用「接到檔尾」的方式:新資料接在檔案最後面,
只改目錄裡那一項的 8 個位元組 + 檔頭的 4 個位元組。
原本的資料一個位元組都不動,所以出錯了也還原得回來。
(上面這一段是本站每一支會動封裝檔的腳本共用的紀律。
 **這一支根本不開封裝檔**:它只改一個純文字檔。寫在這裡是為了讓每一支長得一樣,
 你把兩支擺在一起對照的時候比較好認。)

自包含:整支腳本就是這一個檔,只用 Python 內建模組,不需要安裝任何套件。
**這一支不讀也不寫 PNG**,它只改一個純文字檔。
(2026-09-03 訂正:這一行原本寫「連讀寫 PNG 都是自己做的」,那是從別課的腳本抄過來的
 樣板句,在這一支上不成立,所以把那半句改掉,理由留在這裡。
 在 mvp_swap_chant.py 這個檔上量到:png 只出現在說明文字裡,程式碼一行都沒有。
 它也用不到:要改的 data/audio/chants/spch_cht.txt 是純文字,翻名字用的
 data/database/attrib.dat 也是逗號分隔的純文字,而且是用唯讀模式讀進來的,
 從頭到尾沒有寫回去。
 「不需要安裝任何套件」那半句是對的:本檔 import 的
 argparse / os / re / shutil / signal / struct / sys / tempfile / zlib
 全是 Python 自己就附的模組。
 其中 zlib 在本檔一次都沒有用到(用語法樹數本檔的模組用法:zlib 0 次、os 50 次、
 struct 11 次、sys 6 次、shutil 4 次、signal 4 次、re 2 次、argparse 2 次、tempfile 1 次),
 留著只是為了讓本站每一支腳本的檔頭長得一樣。
 (2026-09-05 訂正這幾個數字:那一輪把備份與還原改成原子的,os 從 35 次變 50 次、
  shutil 2→4、sys 4→6,還多了一個 tempfile。數字寫在說明裡就會過期,
  所以附上量法:用 ast 走一遍本檔,數 <模組>.<屬性> 這種用法出現幾次。
  2026-09-06 那一輪把換名包成不可中斷的一段,多了 signal 4 次,其餘沒變;
  2026-09-10 那一輪只改說明文字與 main() 裡一個判斷,九個數字重數一次全部沒變。)
 真的自己讀寫 PNG 的是「換球員大頭照」「做一張新的球員臉皮」「換掉開機畫面」
 「換球隊隊徽」這四課:site/tutorials/ 底下的 29 支腳本裡,找得到 png_read 與
 png_write 的就只有那四個檔。)

授權:MIT(見檔尾完整條款)。本站教學文字另採 CC BY 4.0。
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
import re
import sys
import zlib
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

# 這一輪到底把遊戲檔換掉了沒有(2026-09-05 加)。
# 按 Ctrl-C 的時候要靠它才講得出「你的檔動了沒」—— 而那句話必須是真的,
# 不可以一律安慰讀者說「什麼都沒有動到」。
#
# 分三段而不是兩段,是因為 Ctrl-C 有可能剛好落在 os.replace() 那一瞬間:
# 那一刻換檔可能已經完成、也可能還沒,程式自己分不出來。與其猜,不如照實說
# 「可能已經換過」並給還原指令 —— 多還原一次沒有代價,說錯「沒動到」有。
#   0 = 還沒碰過正本(這時才可以說「一個位元組都沒有動到」)
#   1 = 換檔那一步已經下去了,結果不明
#   2 = 換檔確定完成
#
# 2026-09-06 再加一層:換檔那一段用 _NoInterrupt 包起來(見下面那個類別),
# 所以「1」這一格幾乎不會被看到了 —— 但它留著,因為 _NoInterrupt 在
# 非主執行緒之類的情況下裝不上處理器,那時就退回原本的行為,還是要有人接住。
_REPLACE_STAGE = 0


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開這段之後再照常丟出。

    為什麼需要它:os.replace() 換完檔、程式還沒把「已經換過」登記下來之前,
    中間隔著一行。Ctrl-C 剛好落在那一行上的話,收尾那句話就會照舊的登記說
    「遊戲檔一個位元組都沒有動到」—— 而磁碟上其實已經換過了。**那句話是假的。**
    這個類別讓那一格縫不存在:登記完才輪得到 KeyboardInterrupt。

    ⚠️ 它**不是**「按了 Ctrl-C 也停不下來」。訊號只是延後幾微秒,
       離開這一段就照常丟出 KeyboardInterrupt,結束碼一樣是 130。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):
            # 非主執行緒等情況裝不上處理器。退回原本的行為,不會比以前更糟
            # (原本就靠 _REPLACE_STAGE 的三段式據實講)。
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


def _state_note(gamedir):
    """回一句「你的遊戲檔到底動了沒」。中斷與作業系統錯誤共用這一句。

    只有一個地方決定怎麼講,兩條路徑就不會有一條說「沒動到」、
    另一條說「已經換過」—— 那種自相矛盾正是本站踩過最多次的坑。
    """
    if _REPLACE_STAGE == 0:
        return '遊戲檔一個位元組都沒有動到。'
    return ('⚠️ 遊戲檔%s。想回到原本的樣子:\n'
            '    python3 %s "%s" --restore'
            % ('已經換過了' if _REPLACE_STAGE == 2
               else '可能已經換過了(中斷點就落在換檔那一步)',
               os.path.basename(sys.argv[0]), gamedir))


def _no_symlink(path, what):
    """path 這個名字是符號連結就停手,不要跟著它寫到資料夾外面去。

    ⚠️ 不可以用 os.path.exists() 判斷:它對「指向不存在目標的符號連結」
       回的是 False —— 那個連結明明在那裡,卻完全看不到。
       要看名字本身,就得用 os.path.islink / os.path.lexists。

    為什麼要擋:遊戲資料夾是別人(模組包、解壓工具、共用電腦上的另一個人)
    也放得進東西的地方,有人先在那裡擺一個指到別處的連結。

    ⚠️ 2026-09-10 訂正這一段。原本寫的是「我們照著那個名字寫下去,受害的是
       資料夾外面那個檔」—— 那是**舊版**(用 open(那個名字, 'wb') 直接寫)才會
       發生的事。現在寫入一律是「mkstemp 暫存檔 → os.replace」,而 os.replace
       換掉的是**那個名字本身**,不會跟著連結去動它指到的檔。
       把守門拆掉重跑實測(本檔 --apply,索引檔擺成指向資料夾外一份索引的連結):
       exit 0、資料夾外那份**一個位元組都沒被改**,遊戲資料夾裡那個名字
       從連結變成 6,835 bytes 的實體檔。所以原本那句話講不出證據,改掉。

    量得到的後果是另外兩種,而且兩種都不出聲:
      · **索引檔**的名字被連結佔住:改動落在那個名字上 ——
        連結被換成一個實體檔,你真正在用的那一份(連結指到的)沒有收到修改。
        備份**有**做,但那是連結指到的那份的複本、放在遊戲資料夾裡,
        所以資料夾看起來像是「改好也備份好了」,其實你的索引一個位元組都沒變。
        (實測:守門拆掉後 exit 0,資料夾裡多出 spch_cht.txt 6,835 bytes 實體檔
         與 .chantbak,連結指到的那份 sha 完全沒動。)
      · **備份**的名字被連結佔住:工具會判定「備份已存在,保留最早那一份」
        然後照樣改遊戲檔 —— 你的還原點就變成資料夾外面那個檔。
        (實測:守門拆掉後 exit 0、遊戲檔真的被改,而還原點是一個 29 bytes
         的無關檔案;之後真的 --restore,擋下來的是 cmd_restore() 那一道
         「備份看起來被截斷了(群組 1 個 · 音檔 0 個)」,exit 2 ——
         等於改完了卻沒有還原點。
         ⚠️ 這一句原本寫成被「備份不到一半」那一道擋下來,是我推的沒有量;
            實際跑一次才發現是前面那一道先攔住。留著這行提醒下一個人:
            「哪一道守門先攔」也要量,不要照著自己以為的順序寫。)
    """
    if os.path.islink(path):
        raise SystemExit(
            '%s是一個符號連結:%s\n'
            '  → 它指到 %s\n'
            '  跟著這個名字做下去,動到的不會是它指到的那個檔;\n'
            '  備份的名字被連結佔住時,你的還原點會變成資料夾外面那個檔。\n'
            '  所以這裡停手,什麼都不寫。請把那個連結刪掉或改名,再跑一次。'
            % (what, path, os.path.realpath(path)))


def _mkstemp_beside(path, tag):
    """在 path 所在的那個資料夾裡開一個**別人搶不到的**暫存檔,回傳 (fd, 路徑)。

    ⚠️ 為什麼不用 path + '.part' 這種猜得到的名字(2026-09-05 稽核抓到):
       有人先在那個名字上放一個指到資料夾外面的符號連結,
       shutil.copy2() 或 open(那個名字, 'wb') 會**跟著連結**
       把外面那個檔截成 0 再寫進去 —— 後面的 os.replace() 雖然只換掉連結本身,
       但傷害在那之前就造成了。實測(2026-09-05,本課的舊版):
       先擺 spch_cht.txt.chantbak.part → 外面一個 29 bytes 的檔被寫成 6,835 bytes;
       改擺 spch_cht.txt.tmp → 另一個 15 bytes 的檔一樣被寫成 6,835 bytes。

    mkstemp 是用 O_CREAT|O_EXCL 開檔的:名字已經被佔住(佔住的是符號連結也算)
    就直接失敗,不會跟過去。名字本身也是隨機的,先擺也擺不中。

    暫存檔開在**跟目的檔同一個資料夾**,不是系統的暫存區:
    os.replace() 只有在同一個檔案系統上才是原子的。
    """
    d = os.path.dirname(os.path.abspath(path)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(path), tag))


def _drop(tmp):
    """把還沒扶正的暫存檔清掉。用 lexists 不用 exists,理由同 _no_symlink()。"""
    try:
        if os.path.lexists(tmp):
            os.remove(tmp)
    except OSError:
        pass


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ⚠️ 2026-09-05 再改一次:暫存檔的名字從固定的 dst + '.part'
       改成 _mkstemp_beside() 開出來的隨機名字(理由寫在那個函式裡)。
    """
    # 先統一成字串路徑,這樣下面接後綴才不會因為傳進來的是 Path 而爆掉。
    src, dst = os.fspath(src), os.fspath(dst)
    _no_symlink(dst, '備份檔')
    fd, part = _mkstemp_beside(dst, 'part')
    try:
        # 關鍵在「先寫一個別的名字,寫完才改名」。
        # 中途斷掉時,斷在半路的是那個隨機名字的檔,dst 這個名字上還沒有東西,
        # 下一次執行就會判定「還沒備份過」而重新備份,不會誤用半截的。
        with os.fdopen(fd, 'wb') as fo:
            with open(src, 'rb') as fi:
                shutil.copyfileobj(fi, fo)
            fo.flush()
            os.fsync(fo.fileno())   # 真的落到碟上,不是還躺在快取裡
        shutil.copystat(src, part)  # 權限與時間戳照原檔,不要留下 mkstemp 的 0600
        os.replace(part, dst)       # os.replace 是原子的
    # 攔 BaseException 不是攔 Exception:Ctrl-C(KeyboardInterrupt)
    # 跟 SystemExit 都不是 Exception 的子類,而那正是最容易中斷備份的兩種情況。
    except BaseException:
        _drop(part)
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
    # 先看名字本身是不是符號連結,再問「它在不在」。
    # 順序反過來的話,指向不存在目標的死連結會被 exists() 說成「找不到備份」,
    # 讀者就永遠查不出真正的原因(2026-09-05 稽核)。
    _no_symlink(bak, '備份檔')
    if not os.path.lexists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    # 第 1 道:0 bytes。最常見的半截備份就長這樣。
    n = os.path.getsize(bak)
    if n == 0:
        raise SystemExit(
            '備份是 0 bytes(多半是上次備份到一半被中斷),不敢拿它覆蓋 %s。' % dst)
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    def _stop(why):
        """任何一道檢查沒過就走這裡:印出**哪裡不對**,然後停,絕不還原。

        訊息裡一定帶上「why」那一句具體的理由,而不是只說「備份壞了」。
        知道是哪個欄位對不上,你才判斷得出來要不要改用另一份備份。
        """
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 第 2 道:BIGF 封裝檔。檔頭 +0x04 那 4 個位元組是「整個檔案應該有多大」,
    # 拿它跟實際大小對。被截斷過就一定對不上。
    # 兩種位元組順序都接受,因為這個欄位在不同的 .big 裡真的兩種都遇得到。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:語系檔(.LOC)。檔頭 +0x10 指到字串區 LOCL,
    # LOCL 裡面是「幾條字串」加上一張位移表。最後一條字串的位移最大,
    # 所以檔案被截斷時,它一定會指到檔案結尾外面去。這一道就是在抓那個。
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

    # 第 4 道:Windows 執行檔。開頭是 'MZ',+0x3C 那 4 個位元組指到 PE 檔頭,
    # PE 檔頭後面是節區表,每個節區記著「我在檔案裡從哪裡開始、有多長」。
    # 把所有節區的結尾取最大值,那就是這個檔至少要有多大。
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
    """真正把備份放回去。備份先過了它該過的那幾道檢查才會走到這裡。

    哪幾道要看它是什麼類型的檔:BIGF 走檔頭長度那一道,
    語系檔與執行檔各走自己那一道再加通用地板,其餘的只走通用地板。

    抽成一個函式,是為了讓「檢查」跟「覆蓋」只有這一個交會點:
    往後要再加一道檢查,不會有哪一條路徑漏掉。

    ── 2026-09-05 改成原子還原(上線前資安稽核抓到的真漏洞)──────────
    原本這裡是一句 shutil.copy2(bak, dst)。copy2 的做法是
    **先把 dst 開成 'wb'(當場截成 0 bytes)再一段一段寫進去** ——
    中途磁碟滿、外接碟拔掉、按了 Ctrl-C,遊戲正本就停在 0 bytes 或半截。
    而按 --restore 的人手上多半就只剩這一份遊戲檔了,這是最不該賭的一步。

    實測(2026-09-05,本課的舊版):讓覆蓋動作寫了 300 bytes 之後失敗,
    6,835 bytes 的索引檔當場變成 300 bytes。

    現在的順序是:
      1. 目的檔與備份都不可以是符號連結(理由見 _no_symlink():
         動到的不會是它指到的那個檔,而還原點可能變成資料夾外面的檔案)
      2. 在**目的檔那個資料夾裡**開一個隨機名字的暫存檔,寫進去
      3. flush + fsync,真的落到碟上
      4. 權限照正本原本的樣子(正本不在就照備份的)
      5. 把暫存檔**整份讀回來**跟備份逐位元組對一次
      6. 全對了才 os.replace() 換上去 —— 這一步是原子的
    任何一步失敗就把暫存檔刪掉,正本從頭到尾沒有被開過寫入,原封不動。
    """
    global _REPLACE_STAGE
    bak, dst = os.fspath(bak), os.fspath(dst)
    _no_symlink(dst, '要還原的目標檔')
    _no_symlink(bak, '備份檔')
    with open(bak, 'rb') as f:
        want = f.read()
    fd, tmp = _mkstemp_beside(dst, 'restore')
    try:
        with os.fdopen(fd, 'wb') as fo:
            fo.write(want)
            fo.flush()
            os.fsync(fo.fileno())
        # mkstemp 開出來的是 0600。正本原本是什麼權限就照著設回去,
        # 免得還原完之後遊戲(或另一個帳號)反而讀不到它。
        shutil.copymode(dst if os.path.isfile(dst) else bak, tmp)
        # 換上去之前先自己讀回來對一次。這裡對不上就代表根本沒寫成功,
        # 而此時正本還是原本那一份 —— 這正是把比對放在 os.replace **之前**的原因。
        with open(tmp, 'rb') as f:
            got = f.read()
        if got != want:
            raise SystemExit(
                '寫出來的內容跟備份對不起來(備份 %d bytes、寫出 %d bytes),\n'
                '  所以沒有動 %s —— 它還是還原之前那一份。\n'
                '  請確認磁碟空間與這個資料夾的寫入權限。' % (len(want), len(got), dst))
        _REPLACE_STAGE = 1      # 先標記再換,不要在「已經換了但還沒標記」的縫裡被中斷
        # 換名 + 登記包成不可中斷的一段:Ctrl-C 落在這兩行之間時先記著,
        # 等登記做完才丟出來,收尾看到的登記一定跟磁碟上的狀態一致。
        with _NoInterrupt():
            os.replace(tmp, dst)
            _REPLACE_STAGE = 2
    except BaseException:
        _drop(tmp)
        raise




try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 備份用自己的後綴,不跟別課共用。--restore 只認這個後綴,
# 所以不會去碰別課(改能力值、改介面文字那些)留在同一台機器上的備份。
BACKUP_SUFFIX = '.chantbak'
# 索引檔實際是 193 行(90 個群組 + 103 個音檔)。這個上限只是壞檔防護:
# 給你的路徑指到別的東西時,寧可停下來問人,也不要開始猜。
MAX_LINES = 5000


# ─────────────────────────────────────────────────────────
#  應援曲索引 spch_cht.txt
#
#  格式:一行群組名,底下每個音檔一行(檔名 + 群組內部位移)。
#  群組有三種:有名字的(tomahawk 那類)、tchants:NN(球隊隊呼)、
#  pchants:NNNN(某位球員專屬)。這支腳本只動 pchants 那 57 組。
# ─────────────────────────────────────────────────────────
def chant_paths(gamedir):
    """從遊戲資料夾算出索引檔的位置,順便當作「你給的路徑對不對」的檢查。

    要你給資料夾而不是給檔案,是因為指錯檔案很難發現,
    但「這個資料夾底下沒有 data/audio/chants/spch_cht.txt」一句話就講得清楚。
    """
    idx = os.path.join(gamedir, 'data', 'audio', 'chants', 'spch_cht.txt')
    if not os.path.isfile(idx):
        raise DataError('找不到 %s\n'
                        '  請確認你給的是遊戲資料夾(裡面看得到 mvp2005.exe 跟 data)' % idx)
    return idx


def read_index(path):
    """回傳三樣:(原始 bytes, 每行的 bytes 清單, 這個檔用的換行位元組)。

    刻意不解碼整份,寫回時才能保證其他行一個位元組都不動;
    換行也要一起帶出去,因為寫回時得用**原本那一種**接回來。

    為什麼一路用 bytes 不用字串:一解碼就得挑一個編碼,挑錯會把不認得的位元組
    換成問號,再寫回去時那些行就變了。這個檔是遊戲在讀的,不是給人看的,
    只要保證「沒被指定要改的行,位元組完全不動」就好,不需要知道它們是什麼文字。
    """
    try:
        raw = open(path, 'rb').read()
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))
    # 換行照原檔沿用。這個檔是 Windows 遊戲的資料,通常是 CRLF;
    # 統一換成 LF 會讓每一行都少一個位元組,整個檔就變了。
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.split(nl)
    if len(lines) > MAX_LINES:
        raise DataError('%s 有 %d 行,遠多於預期的 193 行 —— 不敢動' % (os.path.basename(path), len(lines)))
    return raw, lines, nl


def parse_groups(lines):
    """回傳 [(行號, 群組名)]。群組行的特徵:不含 .wav,而且不是空行。

    這個檔沒有縮排以外的結構標記,所以判斷方式只能是「排除法」:
    音檔那些行一定帶 .wav,剩下的非空行就是群組名。

    群組名共有三種寫法:
      · 有名字的(tomahawk 那類通用的加油聲)
      · tchants:NN    球隊隊呼
      · pchants:NNNN  某位球員專屬,那四位數就是他的 audioid
    這支腳本只動第三種。

    行號要一起回傳,因為改的時候是「照行號換掉那一行」,
    不是「在整份檔案裡搜尋取代」。後者會誤傷剛好長得一樣的別行。
    """
    out = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s or b'.wav' in l:
            continue
        out.append((i, s.decode('latin-1')))
    return out


def check_index(lines):
    """一致性檢查:群組數、音檔數、有沒有重複的群組名。

    這三個數字是這支腳本的驗算基準。改之前量一次、改之後再量一次,
    群組數與音檔數必須完全一樣(這一課只換名字,不增不減),
    而且不可以出現重複的群組名。

    為什麼盯著重複:索引裡出現兩個一模一樣的群組名時,
    遊戲會用哪一個**本站沒有測過**。與其賭,不如在寫出去之前就停下來。
    """
    groups = parse_groups(lines)
    files = [l for l in lines if b'.wav' in l]
    names = [g[1] for g in groups]
    dup = sorted({n for n in names if names.count(n) > 1})
    return len(groups), len(files), dup


# ─────────────────────────────────────────────────────────
#  名單:audioid ←→ 球員
# ─────────────────────────────────────────────────────────
# attrib.dat 的欄位不是固定順序的,不同名冊會不一樣,所以欄號要**執行時去表頭找**,
# 不可以寫死。這裡寫死的只有「欄位的名字」。
AUDIOID_NAME = 'playerattrib_audioid'   # 應援曲群組名後面那四位數,對的就是這一欄
NAME_FIRST = 0                          # 名
NAME_LAST = 1                           # 姓


def load_players(gamedir):
    """回傳 {audioid: '名 姓'}(只有一邊有字的就只有那一邊)。
    讀不到名冊就回空的,腳本照樣能跑(只是顯示不了名字)。

    名冊只是**方便**用的:有它才能用名字查人、才能在清單上顯示誰在用哪首應援曲。
    真正要改的東西完全不需要它,所以這裡一律「讀不到就回空的」,不拋錯。
    換過名冊、名冊格式不一樣、根本沒有 attrib.dat,都不該讓你連 --list 都跑不了。

    attrib.dat 是逗號分隔的純文字,行尾 CRLF。第一行是表頭,
    每一格長成「<欄號> <欄位名>」;之後每一行是一位球員,每一格長成「<欄號> <值>」。
    每一格自己帶著欄號,是這個格式最好用的地方:可以逐格自我對帳。
    """
    path = os.path.join(gamedir, 'data', 'database', 'attrib.dat')
    if not os.path.isfile(path):
        return {}
    raw = open(path, 'rb').read()
    lines = raw.split(b'\r\n')
    # 先讀表頭,把「欄位名 → 欄號」建起來。欄號不寫死就是靠這一步。
    names = {}
    for c in lines[0].split(b','):
        m = re.match(rb'^\s*(\d+) (\w+)', c)
        if m:
            names[m.group(2).decode('latin-1')] = int(m.group(1))
    # 這份名冊沒有 audioid 這一欄的話,再往下讀也拼不出對照表,直接回空的。
    if AUDIOID_NAME not in names:
        return {}
    fld = names[AUDIOID_NAME]

    def cell(l, f):
        """取出這一行第 f 欄的值;對不上就回 None,不猜。

        兩件事讀者看不出來:
        1. 第 f 欄實際落在切開後的第 f+1 格。
           資料列的第 0 格不是欄位,是一串識別碼(長得像 0f58f3c1b)。
           本站測試機那份是表頭 47 格、資料列 48 格,差的就是它;
           你的名冊欄位數可能不一樣,但「差一格」這件事是一樣的。
        2. 每一格自己帶著欄號,所以取出來之後再對一次
           「你身上寫的欄號是不是 f」。對不上代表這一行的格數跟表頭不一致
           (欄位裡有逗號、行壞掉之類),這時候回 None 比回一個錯的值好。
        """
        cs = l.split(b',')
        i = f + 1
        if i >= len(cs):
            return None
        m = re.match(rb'^(\d+) ?(.*)$', cs[i].strip())
        return m.group(2).decode('latin-1') if m and int(m.group(1)) == f else None

    # audioid 取得到、而且名跟姓**至少有一邊**有字才收。用 setdefault:
    # 同一個 audioid 被多位球員共用時,留先出現的那一位,不讓後面的蓋掉。
    out = {}
    for l in lines[1:]:
        if not l.strip():
            continue
        a = cell(l, fld)
        f_, s_ = cell(l, NAME_FIRST), cell(l, NAME_LAST)
        # 只有名、或只有姓的球員也要收。兩份原版名冊裡的 audioid 1263 就是
        # 「名字欄空白、姓氏欄寫 Ichiro」,而 1263 正是 57 組應援曲的其中一組;
        # 原本要求兩欄都有字,他整列被丟掉,--list 少列一個人、--give Ichiro
        # 還會回「名冊裡找不到」。兩欄都空的那種佔位列才丟掉(本站測試機那份
        # 名冊有 25 列是那樣,audioid 全是 0)。
        if a and a.isdigit() and (f_ or s_):
            out.setdefault(int(a), ('%s %s' % (f_ or '', s_ or '')).strip())
    return out


# ─────────────────────────────────────────────────────────
#  各種動作
# ─────────────────────────────────────────────────────────
def cmd_list(gamedir):
    """把遊戲裡的球員專屬應援曲列出來。**一個位元組都不寫。**

    這是你第一個該下的指令:先看清楚有哪些編號可以拿來當來源,
    再決定要把哪一首指給誰。
    """
    idx = chant_paths(gamedir)
    raw, lines, nl = read_index(idx)
    g, f, dup = check_index(lines)
    players = load_players(gamedir)
    print('  索引 %s' % idx)
    print('  群組 %d 個 · 音檔 %d 個%s' % (g, f, ('  ⚠️ 有重複群組名:%s' % '、'.join(dup)) if dup else ''))
    print()
    # 只挑 pchants: 開頭的。tchants:(隊呼)與有名字的通用加油聲不在這一課的範圍。
    # 四位數就拿去名冊裡查是誰在用;查不到就留空,由下面統一講清楚原因。
    rows = []
    for i, name in parse_groups(lines):
        if not name.startswith('pchants:'):
            continue
        num = name.split(':', 1)[1]
        who = players.get(int(num), '') if num.isdigit() else ''
        rows.append((num, who))
    print('  球員專屬應援曲 %d 首:' % len(rows))
    unknown = 0
    for num, who in rows:
        if who:
            print('    %s  %s' % (num, who))
        else:
            unknown += 1
    if unknown:
        print('    ...另外 %d 個編號在你的名冊裡找不到對應的球員' % unknown)
        print('       （名冊換過就會這樣,不是壞掉。那些應援曲還在,只是沒有人在用）')
    print()
    print('  想把其中一首指給別人:')
    if rows:
        print('    python3 %s "<遊戲資料夾>" --give <球員名字> %s'
              % (os.path.basename(sys.argv[0]), rows[0][0]))


def find_player(gamedir, keyword):
    """用名字的一部分去名冊裡找人,回傳 (audioid, 全名)。

    找到剛好一位才算數。這一點是刻意的:
      · 一個都沒有 → 直接說找不到,不做模糊比對去猜你要誰
      · 找到好幾位 → 把候選印出來叫你打長一點,或者直接給四位數
    在「會改到遊戲檔」的工具裡,猜錯一個人比多問一次糟糕得多。
    """
    players = load_players(gamedir)
    if not players:
        raise DataError('讀不到名冊,沒辦法用名字查。請直接給 audioid 四位數。')
    key = keyword.lower()
    hits = [(a, n) for a, n in players.items() if key in n.lower()]
    if not hits:
        raise DataError('名冊裡找不到名字含「%s」的球員。' % keyword)
    if len(hits) > 1:
        msg = '\n'.join('    %s  audioid %d' % (n, a) for a, n in sorted(hits, key=lambda x: x[1])[:12])
        raise DataError('名字含「%s」的有 %d 位,請打長一點:\n%s' % (keyword, len(hits), msg))
    return hits[0]


def cmd_give(gamedir, who, source_num, apply_it):
    """把某一首既有的應援曲改指給另一位球員。這一支的主戲都在這裡。

    apply_it 為假時整段只印不寫,而且印的就是待會兒真的要做的那一件事,
    不是另外寫一段「大概會像這樣」。

    做的事只有一句:把索引檔裡某一行的群組名,從 pchants:<來源四位數>
    換成 pchants:<目標的 audioid>。其他每一行的位元組完全不動。
    """
    idx = chant_paths(gamedir)
    raw, lines, nl = read_index(idx)
    players = load_players(gamedir)

    # 目標可以直接給四位數,也可以給名字。給名字就走名冊查,查不到或撞名會停下來。
    if who.isdigit():
        target_id, target_name = int(who), players.get(int(who), '(名冊裡查不到)')
    else:
        target_id, target_name = find_player(gamedir, who)

    # 群組名裡的編號固定四位數(不足補 0),所以打 4 跟打 0004 都收。
    src = source_num.zfill(4)
    hit = [(i, n) for i, n in parse_groups(lines) if n == 'pchants:%s' % src]
    if not hit:
        raise DataError('索引裡沒有 pchants:%s。用 --list 看有哪些。' % src)
    line_no, old_name = hit[0]

    # 目標本來就有專屬應援曲的話,改下去索引裡就會有兩個一樣的群組名。
    # 先查出來,下面直接停手。
    already = [(i, n) for i, n in parse_groups(lines) if n == 'pchants:%04d' % target_id]
    print('  來源應援曲  pchants:%s%s' % (src, ('  (原本是 %s 的)' % players[int(src)]) if int(src) in players else ''))
    print('  要指給      %s  audioid %04d' % (target_name, target_id))
    if already:
        print('  ⚠️ %s 本來就有專屬應援曲(pchants:%04d)。' % (target_name, target_id))
        print('     照做的話索引裡會出現兩個一樣的群組名,遊戲會用哪一個本站沒有測過。')
        raise DataError('為了不製造重複的群組名,這裡停下來。\n'
                        '  想換的話請挑一位還沒有專屬應援曲的球員。')
    if int(src) == target_id:
        raise DataError('來源跟目標是同一個編號,不用改。')
    # 群組名在這個檔裡是固定寬度的:本站量到的三份 spch_cht.txt(英文版原版、
    # 中文版原版、測試機那一份),90 個群組行**每一行都剛好 32 bytes**。
    # audioid 超過四位數會寫出 33 bytes 的一行,破壞這個檔唯一看得見的結構,
    # 而遊戲吃不吃得下本站沒有測過 —— 所以停手,不要拿讀者的遊戲檔去賭。
    # (本站測試機那份名冊裡有 149 位球員的 audioid 是五位數,最大 25028;
    #  兩份原版名冊則是 0 位,最大 2665。)
    if target_id > 9999:
        raise DataError('%s 的 audioid 是 %d,超過四位數。\n'
                        '  這個索引檔的群組名固定四位數,寫成五位數會讓那一行多一個位元組,\n'
                        '  遊戲吃不吃得下本站沒有測過,所以這裡停下來。'
                        % (target_name, target_id))

    new_line = b'pchants:%04d' % target_id
    print()
    print('  會改的就是這一行(第 %d 行):' % (line_no + 1))
    print('    %s' % lines[line_no].decode('latin-1'))
    print('    ↓')
    print('    %s' % new_line.decode('latin-1'))
    # 檔案結尾有換行時,raw.split(nl) 會多回一個空字串,那不是一行;
    # 先扣掉它才是真正的行數,再扣掉正在改的這一行,剩下的才是「其他」。
    # (本站測試機的專案資料夾裡六份 spch_cht.txt 位元組完全相同:6,835 bytes、CRLF、
    #  193 行,也就是上面說的 90 個群組 + 103 個音檔,所以這裡會印 192,不是 193。)
    total_lines = len(lines) - 1 if lines and lines[-1] == b'' else len(lines)
    print('  其他 %d 行一個位元組都不會動。' % (total_lines - 1))

    if not apply_it:
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要改的話,在剛才那一行最後面加上 --apply')
        return

    # 只碰 line_no 那一格。其餘每一行都是從原檔切出來的同一串位元組,原樣接回去。
    new_lines = list(lines)
    # 保留原本的縮排與行尾空白,只換群組名本身
    # (在那一行裡取代第 1 次,不是整份檔案搜尋取代;後者會誤傷長得一樣的別行。)
    new_lines[line_no] = lines[line_no].replace(old_name.encode('latin-1'), new_line, 1)
    # 用原檔那一種換行接回去,不用系統預設的。
    out = nl.join(new_lines)

    # 寫之前先自我檢查:群組數、音檔數要跟原本一樣,而且不可以有重複群組名
    # 三道驗算合起來的意思是:「這次改動只換掉一個名字,沒有多出、少掉或錯位任何東西」。
    # 三道都在**記憶體裡**跑完才動磁碟,所以任何一道沒過,遊戲檔連碰都沒被碰到。
    g0, f0, _ = check_index(lines)
    g1, f1, dup = check_index(new_lines)
    if (g0, f0) != (g1, f1):
        raise DataError('改完之後群組或音檔數變了(%d/%d → %d/%d),中止。' % (g0, f0, g1, f1))
    if dup:
        raise DataError('改完之後出現重複的群組名:%s,中止。' % '、'.join(dup))
    if len(out) != len(raw) + (len(new_line) - len(old_name.encode('latin-1'))):
        raise DataError('改完之後檔案長度不符預期,中止。')

    # 備份只做第一次。第二次以後保留最早那一份,
    # 因為那一份才是「你動手之前」的樣子;拿改過的去覆蓋等於把還原點弄丟。
    backup = idx + BACKUP_SUFFIX
    # 要寫的那兩個名字,動手之前先確認都不是「指到別處的符號連結」。
    _no_symlink(idx, '索引檔')
    _no_symlink(backup, '備份檔')
    # 這裡用 lexists 不用 exists:指向不存在目標的死連結,在 exists 眼裡
    # 是「不存在」,會被當成「還沒備份過」而走進去覆蓋它(2026-09-05 稽核)。
    if not os.path.lexists(backup):
        _atomic_copy(idx, backup)
        print()
        print('  已備份 → %s' % os.path.basename(backup))
    else:
        # 已經有備份就保留最早那一份 —— 但先確認它還能用。等到要還原時才發現
        # 備份是 0 bytes 就太晚了:那時遊戲檔已經改過,而那份備份救不回來。
        # 驗備份的力氣不能全放在還原端,寫入才是不可逆的那一步。
        if not os.path.isfile(backup) or os.path.getsize(backup) == 0:
            raise DataError('%s 已經存在,但它不是一份可用的備份'
                            '(不是檔案,或是 0 bytes)。\n'
                            '  請先把它刪掉或改名,再跑一次(腳本會重新備份一份完整的)。'
                            % os.path.basename(backup))
        print()
        print('  備份已存在,保留最早那一份 → %s' % os.path.basename(backup))
    # 先寫一個暫存檔再原子改名。中途斷掉時遊戲看到的還是原本那個完整的索引檔,
    # 不會是一個寫到一半的。
    # ⚠️ 暫存檔的名字不可以是猜得到的 idx + '.tmp'(2026-09-05 稽核):
    #    有人先在那個名字上擺一個指到資料夾外面的符號連結,
    #    open(那個名字, 'wb') 就會跟過去把外面那個檔截掉。實測舊版中招。
    #    _mkstemp_beside() 用 O_CREAT|O_EXCL 開隨機名字,先擺也擺不中。
    global _REPLACE_STAGE
    fd, tmp = _mkstemp_beside(idx, 'tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(out)
            f.flush()
            os.fsync(f.fileno())
        shutil.copymode(idx, tmp)   # 權限照原本的,不要留下 mkstemp 的 0600
        _REPLACE_STAGE = 1      # 先標記再換,理由見 _REPLACE_STAGE 那一段
        # 跟 _do_copy() 同一個寫法:換名與登記之間不留給 Ctrl-C 插隊的縫。
        with _NoInterrupt():
            os.replace(tmp, idx)
            _REPLACE_STAGE = 2
    except BaseException:
        # 寫到一半被中斷(磁碟滿、按 Ctrl-C)時,把那個半截的暫存檔清掉,
        # 跟 _atomic_copy() 是同一個道理:不要在遊戲資料夾裡留垃圾。
        # 遊戲檔本身這時候還是原本那一份完整的,因為改名還沒發生。
        _drop(tmp)
        raise

    # 複驗:重新讀一次
    raw2, lines2, _ = read_index(idx)
    g2, f2, dup2 = check_index(lines2)
    got = [n for _, n in parse_groups(lines2) if n == new_line.decode('latin-1')]
    print('  已寫入。複驗:群組 %d · 音檔 %d · 重複群組名 %d 個 · 新群組名找得到 %s'
          % (g2, f2, len(dup2), '✅' if got else '❌'))
    if (g2, f2) != (g0, f0) or dup2 or not got:
        # 複驗沒過就是**非零結束碼**收場(DataError → 結束碼 2),
        # 絕不會印一個 ❌ 然後當作沒事回 0。順手把還原指令整句寫出來,
        # 讀者不用回頭翻教學頁就照著貼得回去。
        raise DataError('複驗沒過 —— 寫出去的索引檔跟預期對不上。\n'
                        '  請先還原,再回報這個訊息:\n'
                        '    python3 %s "%s" --restore'
                        % (os.path.basename(sys.argv[0]), gamedir))
    print()
    print('  完成。進遊戲,讓 %s 上場打擊,聽聽看應援曲有沒有變。' % target_name)
    print('  ⚠️ 本站只驗到「檔案改對了」。遊戲會不會照這個索引播放,')
    print('     要靠你的耳朵確認 —— 本站沒有辦法自動測這件事。')


def cmd_restore(gamedir):
    """把備份放回去。備份本身留著不刪,所以還原完還可以再還原一次。

    把關分三段:
      1. 這裡先把備份**當成索引檔讀一次**(群組數、音檔數、有沒有重複的群組名、
         結尾是不是完整的一行)。這個檔是純文字,驗得起來就不要退到只看大小。
      2. _restore_from_backup() 再擋一次(0 bytes、通用地板那幾道)。
      3. 蓋回去之後**整份逐位元組**跟備份對一次,對不上就不印成功。
    """
    # 刻意不走 chant_paths():索引檔被刪掉或被別的工具搬走的時候,正是最需要
    # 還原的時候,而 chant_paths() 看到索引檔不在就擋下來、還叫你去檢查路徑 ——
    # 方向是反的。這裡只要求「你給的是遊戲資料夾」,不要求索引檔還在。
    idx = os.path.join(gamedir, 'data', 'audio', 'chants', 'spch_cht.txt')
    backup = idx + BACKUP_SUFFIX
    # 還原是「往正本寫」的動作,所以兩個名字都要先確認不是符號連結。
    # 這裡先擋一次是為了在**讀備份之前**就停:訊息才講得清楚是哪一個檔的問題。
    # (_do_copy() 裡面還會再擋一次 —— 那一道是總開關,不能拿掉。)
    _no_symlink(idx, '要還原的目標檔')
    _no_symlink(backup, '備份檔')
    # 用 lexists:死連結在 exists 眼裡是「不存在」,會被誤報成「找不到備份」。
    if not os.path.lexists(backup):
        if not os.path.isdir(os.path.dirname(idx)):
            raise DataError('找不到 %s\n'
                            '  請確認你給的是遊戲資料夾(裡面看得到 mvp2005.exe 跟 data)'
                            % os.path.dirname(idx))
        raise DataError('找不到備份 %s —— 沒有東西可以還原。' % os.path.basename(backup))

    # 用格式驗備份,不要只靠 _restore_from_backup() 的通用地板。
    # 那一道只擋「不到一半」:本站實測 6,835 bytes 的索引,備份被截成 3,418 bytes
    # (50.007%)照樣印「已還原」、結束碼 0,完整的正本當場被半截檔蓋掉。
    _, bak_lines, _ = read_index(backup)
    bg, bf, bdup = check_index(bak_lines)
    if bdup:
        raise DataError('備份裡有重複的群組名(%s),不敢拿它還原。' % '、'.join(bdup))
    if bg < 1 or bf < 1 or bak_lines[-1] != b'':
        raise DataError('備份看起來被截斷了(群組 %d 個 · 音檔 %d 個 · '
                        '結尾不是完整的一行),不敢拿它還原。\n'
                        '  請改用你自己另外留的那一份備份。' % (bg, bf))
    # 再跟現在那個檔比一次,但**只擋「備份比現在這個檔還少」**。
    # 剛好切在行尾的半截備份會整組整組地少掉,這一道就是在抓它。
    # 反過來(備份比較多)不擋 —— 那正是「正本壞掉、要靠備份救回來」的情況,
    # 擋下去就跟上面那個「索引檔被刪掉反而不給還原」犯同一種錯。
    if os.path.isfile(idx):
        _, live_lines, _ = read_index(idx)
        lg, lf, _ = check_index(live_lines)
        if bg < lg or bf < lf:
            raise DataError('備份只有 %d 組 %d 個音檔,現在那個檔有 %d 組 %d 個 ——\n'
                            '  備份看起來被截斷了,不敢拿它還原。\n'
                            '  請改用你自己另外留的那一份備份。' % (bg, bf, lg, lf))
    _restore_from_backup(backup, idx)
    # 印「已還原」之前先自己看一次:**整份**比完,不是比開頭,也不是兩邊長度
    # 不一樣就在短的那一邊停(用 zip() 兩兩配對就會那樣停,短的比完就結束,
    # 長的那一邊多出來的位元組永遠沒被看過)。
    with open(backup, 'rb') as f:
        want = f.read()
    with open(idx, 'rb') as f:
        got = f.read()
    if want != got:
        raise DataError('還原之後的檔案跟備份對不起來(備份 %d bytes、'
                        '還原後 %d bytes)。\n'
                        '  先不要進遊戲,請確認磁碟空間與這個資料夾的寫入權限。'
                        % (len(want), len(got)))
    print('  已還原 %s ← %s' % (os.path.basename(idx), os.path.basename(backup)))
    print('  備份檔留著沒刪。')


def main():
    """讀參數,分派到 --restore / --give / --list,並把結束碼收成一致的三種。

    沒給任何開關就跑 --list,因為那是唯一絕對不寫檔的動作。
    結束碼:0 正常、2 自己停下來(DataError,或作業系統擋下這個動作)、
    130 你按了 Ctrl-C。備份沒過 _restore_from_backup() 那幾道、
    或是要寫的名字被符號連結佔住時,由 SystemExit 結束,結束碼是 1。
    停下來的理由後面**只有在遊戲檔真的動過的時候**才多一句 _state_note()
    (「已經換過了」加還原指令);還沒動磁碟就停手的那些 —— 也就是你平常
    會看到的那些 —— 輸出一個字都沒有變。
    按 Ctrl-C 的訊息會分兩種寫:遊戲檔還沒換過就說「一個位元組都沒有動到」,
    已經換過就叫你去 --restore —— 那句話得是真的,不能一律安慰。
    換名跟登記之間不留縫(_NoInterrupt),所以這兩句不會講反。
    """
    EPILOG = (
        "\n例子(照順序做):\n\n"
        "  1. 看遊戲裡有哪些球員專屬應援曲\n"
        "     python3 mvp_swap_chant.py \"<遊戲資料夾>\" --list\n\n"
        "  2. 預覽:把 0004 那首指給陳金鋒(不會動到檔案)\n"
        "     python3 mvp_swap_chant.py \"<遊戲資料夾>\" --give Chin-Feng 0004\n\n"
        "  3. 確定了才真的改\n"
        "     python3 mvp_swap_chant.py \"<遊戲資料夾>\" --give Chin-Feng 0004 --apply\n\n"
        "  還原:\n"
        "     python3 mvp_swap_chant.py \"<遊戲資料夾>\" --restore\n"
    )
    ap = argparse.ArgumentParser(
        description='把某位球員的專屬應援曲指給另一位球員',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)
    ap.add_argument('gamedir', help='遊戲資料夾(裡面看得到 mvp2005.exe 跟 data)')
    ap.add_argument('--list', action='store_true', help='列出遊戲裡的球員專屬應援曲')
    ap.add_argument('--give', nargs=2, metavar=('球員', '來源編號'), help='把某首應援曲指給某位球員')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原')
    args = ap.parse_args()

    try:
        if args.restore:
            cmd_restore(args.gamedir)
        elif args.give:
            cmd_give(args.gamedir, args.give[0], args.give[1], args.apply)
        else:
            cmd_list(args.gamedir)
    except DataError as e:
        # 絕大多數的 DataError 是「還沒動磁碟就停手」,那時只印停手的理由 ——
        # 頁面上的範例輸出就是那個樣子,一個字都不動。
        # 但**換名之後**才丟出來的 DataError 不一樣(例如複驗時讀不回來、
        # 讀回來的行數不對):那時遊戲檔已經換過了,只說「停下來了」會讓人
        # 以為什麼都沒發生。跟 Ctrl-C 與 OSError 兩條路走同一個 _state_note(),
        # 三條路就不會有一條說「沒動到」、另一條說「已經換過」。
        #
        # 訊息自己已經把還原指令寫出來的那一種(複驗沒過),就不要再加一次:
        # 同一行指令印兩遍會讓人以為是兩件不同的事。實測過那條路徑會重複,
        # 所以這裡多一個 '--restore' in str(e) 的但書。
        if _REPLACE_STAGE == 0 or '--restore' in str(e):
            print('\n  停下來了:%s\n' % e)
        else:
            print('\n  停下來了:%s\n  %s\n' % (e, _state_note(args.gamedir)))
        return 2
    except KeyboardInterrupt:
        # ⚠️ 不可以一律說「什麼都沒有動到」(2026-09-05 稽核)。
        #    要看 os.replace() 那一刻到底過了沒 —— 那是唯一會換掉遊戲檔的動作,
        #    由 _state_note() 統一講。不管動沒動,結束碼都是 130,
        #    不會因為「反正檔案好好的」就回 0。
        print('\n  已中斷。%s\n' % _state_note(args.gamedir))
        return 130
    except OSError as e:
        # 磁碟滿、檔案被設成唯讀、路徑被別的東西佔住 —— 這些不是「檔案內容不對」,
        # 所以不是 DataError,但也不該讓讀者看到一整串 traceback。
        # 寫檔是「先寫一個隨機名字的暫存檔,全部就緒才原子改名」,
        # 所以改名發生之前出的錯,遊戲檔一個位元組都沒被動到 ——
        # 但改名之後才出的錯(例如複驗時讀不到檔)不算。所以這句話交給
        # _state_note() 照 _REPLACE_STAGE 據實講,不打包票說「一定安全」。
        print('\n  停下來了:作業系統擋下這個動作 —— %s\n'
              '  常見原因:磁碟滿了、檔案被設成唯讀、或那個路徑被別的東西佔住。\n'
              '  %s\n' % (e, _state_note(args.gamedir)))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())

#
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
