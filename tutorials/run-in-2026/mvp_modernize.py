#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_modernize.py — 讓 MVP Baseball 2005 在今天的機器上跑得順

這支腳本處理兩件相容性問題，兩件都是改**你自己那份**遊戲執行檔：

  1. 記憶體上限：這款遊戲是 2005 年的 32 位元程式，預設只能用 2 GB。
     執行檔的 PE 檔頭有一個叫「大位址」的旗標，打開之後在 64 位元的
     Windows 上可以用到 4 GB。

     ⚠️ 社群傳很久的「球場不能超過 20MB」，本站**不**把那 2 GB 的牆
     當成它的根因，因為那條規矩本身就沒站住。本站測試機上剛安裝好、
     從來沒被動過的原版（英文版與繁體中文版各一份，兩份同值），
     frontend 資料夾裡的 stadiums.big 就已經是 30,162,721 bytes
     （28.77 MiB），比 20MB 多 44%，等於 EA 自己出貨就「超標」。
     另一個流傳的數字「10MB」貼的是 stadium 資料夾裡的各別球場檔
     （同一台機器上量到：兩份原版各 87 個檔、最大 4,184,449 bytes；
     站上標「10MB」的那包社群球場 83 個檔、最大 19,333,365 bytes），
     而放多大會當、放多小不會當，沒有人量過。
     另外，中文版配大球場跳出這件事，本站量到卡住的是遊戲自己那塊
     記憶體池（下面的 --pool），不是 2 GB 的位址空間。

  2. 螢幕解析度：遊戲內建的解析度表只到 1280x1024（2005 年的常見上限）。
     那張表就在執行檔裡，一筆 16 個位元組：寬(4) 高(4) 色深(4) 保留(4)，
     全部是 32 位元小端序。把其中一筆換成 1920x1080 之類的現代尺寸就行。

⚠️ **這兩件事都跟光碟檢查、授權驗證完全無關。**
   本站不提供、不教學、也不包含任何規避技術保護措施的功能。
   這支腳本只動上面講的那幾個位元組，其他一個位元組都不碰。

⚠️ **位址不寫死。** 不同版本的執行檔位址不一樣（本站實測:
   英文版原版的解析度表在 0x4C3FD8、中文版原版在 0x52F860）。
   所以腳本是**用內容去找**那張表，不是記位址。

── 這支在做什麼（不讀程式碼也看得懂的版本）─────────────────

輸入：一個參數，你那份遊戲執行檔的完整路徑（mvp2005.exe）。
      除了這個檔，它不讀遊戲裡的任何其他東西，也不連網。

輸出：
  · 什麼開關都不加 = 唯讀體檢，只把讀到的東西印在畫面上。
  · 加了 --4gb / --resolution / --pool / --timestamp 但沒加 --apply
    = 預覽，先講總共會改幾個位元組，再把位置列出來，一樣不寫檔。
      位置只列前 16 個，總數以前面那一句為準（本站在一顆找得到記憶體池、
      而且 CheckSum 原本就有填的 mvp2005.exe 上，四個旋鈕連 --timestamp 一起開
      量到 17 個，畫面就只列得出前 16 個）。
  · 加了 --apply 才真的寫。全部是原地覆寫，檔案大小前後一模一樣。
  · --restore 把備份蓋回去。

四個旋鈕各自動到哪裡（沒有插入也沒有刪除，都是原地換掉幾個位元組）：
  --4gb         PE 檔頭 Characteristics 裡的 1 個位元（0x0020）
  --resolution  解析度表最前面那兩筆的寬與高，各 8 個位元組
  --pool        遊戲自己那塊記憶體池的 imm32，每一處 4 個位元組
  --timestamp   PE 檔頭 TimeDateStamp 的 4 個位元組
原本就有填 CheckSum 的執行檔會再多改那 4 個位元組（原本是 0 就維持 0）。

安全網有三層：
  1. 唯讀是預設，但這一句只涵蓋四個旋鈕（--4gb / --resolution / --pool / --timestamp）：
     它們沒有加 --apply，一個位元組都不會落地。
     --restore 不在這一句裡。它是還原路徑，不看 --apply，覆蓋前那三道把關過了
     就把備份整份蓋回執行檔；那三道寫在這一段的最後一句。
  2. 第一次 --apply 之前先備份成「原檔名 + .modernizebak」，
     而且是先寫一個隨機名字的暫存檔、整份複製完成才改名，中途斷掉不會留下半截備份；
     已經有備份就保留最早那一份，不會被後來的蓋掉 —— 但會先確認那份備份
     確實是**現在這顆執行檔**的備份（大小一樣、兩份不同的位元組全部落在
     這支腳本會動的那幾格裡），對不上就停下來，不在沒有正確備份的情況下
     動你的檔。寫入本身也是先寫一個隨機名字的暫存檔（開在同一個資料夾裡，
     名字事先猜不到，所以不會被人拿一條同名的捷徑騙去寫別的地方），
     寫完才改名，中途出事會把暫存檔收掉，
     而且改名之前把原本那顆的權限抄過去（不然執行檔會掉可執行位元）；
     碰到不讓你設權限的檔案系統（FAT32 隨身碟之類）會印一行告訴你，
     照樣把改好的內容寫下去。
  3. 寫完立刻重新讀回來，比對「實際改動的位元組是不是剛好等於預覽算出的那份完整清單」
     （比的是完整清單，不是畫面上列出來的前 16 個），
     多一個少一個都要你立刻 --restore。
  --restore 也不是無條件覆蓋，覆蓋前三道：開頭要是 MZ；這份備份要對得上
  現在這顆執行檔（大小一樣、不同的位元組全部落在上面那幾格裡 —— 擋掉
  「換過執行檔卻沒刪舊備份」拿另一顆蓋掉現在這顆）；備份的 PE 節區表指到的
  長度不得超出檔案本身，擋掉半截備份把正本吃掉（本站實測過一份被截成八分之一的
  備份，當時的還原把關全過，還印了「內容與備份相同」）。
  三道任何一道沒過都不覆蓋，而且 exit code 不是 0。
  三道都過了才寫，而寫法跟上面一樣：先寫一個隨機名字的暫存檔（同一個資料夾），
  fsync 落地、權限抄過去、再讀回來跟備份比對 sha256，全部相同才原子改名換上去。
  改名之前任何一步不成，就把暫存檔收掉，你那顆執行檔一個位元組都沒被碰過。
  （要寫進去的那兩個檔 —— 遊戲執行檔本身、備份檔 —— 只要有一個是符號連結
  （捷徑），--apply 與 --restore 就直接停下來，不跟著連結寫到資料夾外面去；
  唯讀體檢與預覽只讀不寫，照樣看得下去。）
  （按 Ctrl-C 的時候，畫面上說「動了沒」的那一句是照三態登記寫的：
  改名還沒開始才會說「一個位元組都沒有動到」；改名跑完會說「已經換好了」，
  修改那條路還會附上還原指令，還原那條路則是說「還原那一步已經做完了」；
  剛好卡在中間會說「可能已經被換掉了」。改名與登記那兩行之間不接受 Ctrl-C，
  而且改名沒做成的時候登記會收回去，所以中間那一態幾乎不會出現。）

做不到的事（先講清楚，省得你試）：
  · 不能把 32 位元變成 64 位元。4 GB 是 32 位元指標數得到的上限，
    不是哪裡有個設定值可以調大。
  · 有光碟保護的原版執行檔，程式碼是加密的，--pool 的樣態找不到；
    這支腳本不會、也不打算去碰那一層。
  · 解析度表找不到、或找到不只一處，一律停下來，不拿位址去猜。
    但會因此停下來的只有 --resolution 那一項；--4gb / --pool / --timestamp
    都不看那張表，唯讀體檢也只是少印一段，照樣做得下去。
    本站實測：把剛安裝好的英文版原版（6,972,001 位元組）複製一份，
    故意把後四筆特徵破壞掉再跑，--4gb 與 --timestamp 照樣列出預覽、
    exit code 0，只有 --resolution 停下來、exit code 2
    （--pool 在那顆檔上另有自己的限制，見上一條）。
  · 它只改檔案，不會替你設定顯示卡、視窗模式或畫面比例。
    改完解析度表畫面還是被拉伸，那是遊戲內部投影比例的事，不在這支的範圍。
  · 本站沒有量過遊戲執行時實際吃掉多少記憶體，所以這支不會、也不該
    回答你「開了 4 GB 之後球場可以放多大」。

自包含：整支腳本就是這一個檔，不需要安裝任何套件。

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

import datetime
import os
import sys
import re
import struct
import shutil
import signal
import argparse
import tempfile
import hashlib

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

# ── 暫存檔與符號連結(2026-09-05 唯讀資安稽核加)──────────────────────
# 兩件事一起修:
#   1. 所有暫存檔改用 tempfile.mkstemp(dir=目的檔那個資料夾)。名字是隨機的,
#      而且是 O_CREAT|O_EXCL 開出來的,沒有人能事先把那個名字佔成一條
#      指向資料夾外面的符號連結。
#   2. 目的檔與備份檔在寫入前先用 os.path.islink 擋一次。
#      ⚠️ 不可以用 os.path.exists():連結指到的東西不存在時它回 False,
#         那條連結就會被當成「這裡沒有檔案」放行。要用 islink / lexists(lstat)。
#      ⚠️ 2026-09-06 補上漏掉的那一半:當時 main() 會先把符號連結 realpath 成
#         真檔再往下傳,所以「執行檔本身是連結」那一道其實從來沒亮過 ——
#         跟著連結寫,只是寫到連結指的那個檔而已。現在 main() 不 realpath 了。

# ── Ctrl-C 不可以說謊(2026-09-06 第三輪唯讀稽核加)────────────────────
# 原本只有一個布林值 _TARGET_REPLACED,而且是這樣寫的:
#     os.replace(tmp, path)
#     _TARGET_REPLACED = True
# 這兩行之間有一個很窄、但真的存在的空窗。Ctrl-C 剛好落在裡面的話,
# 磁碟上的遊戲執行檔**已經換掉了**,而收尾訊息讀到的旗標還是 False,
# 於是印「遊戲執行檔一個位元組都沒有動到」—— 那是假話,而且是最糟的一種假話:
# 玩家會因此不去跑 --restore。
#
# 兩道一起修:
#   (a) 把「改名 + 登記」包進 _NoInterrupt。這段期間收到的 SIGINT 先記著,
#       離開這段之後才照常丟出 KeyboardInterrupt,所以登記跟磁碟狀態必定一致。
#   (b) 登記改成三態:'idle'(還沒動)/'replacing'(正在換 X)/'replaced'(已換 X)。
#       進 with 之前先寫 'replacing';收尾看到 'replacing' 就要說
#       「出事的時候正在替換 X,請 --restore 或自己拿備份比對」,不可以說沒動到。
#       (a) 讓 (b) 幾乎不會被觸發,但 (b) 是保險 —— 例如 os.replace 自己噴 OSError。
#   (c) 改名**確定沒做成**的時候(os.replace 自己丟例外、或還沒進 with 就被中斷),
#       收尾把登記收回 'idle'。少了這一步,一次失敗的寫入被中斷會反過來嚇人說
#       「可能已經被換掉了」,而其實一個位元組都沒動。只收 'replacing',
#       已經是 'replaced' 的絕對不收 —— 那才是會害人不去還原的那種謊。
_PROGRESS = {'stage': 'idle', 'target': None, 'action': None}   # idle / replacing / replaced


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開這段之後再照常丟出。

    這樣 KeyboardInterrupt 的收尾看到的登記一定跟磁碟上的狀態一致。
    這段裡面**只放**改名與登記那兩行,不放任何耗時的工作 ——
    不然玩家按了 Ctrl-C 會覺得沒反應。
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
                pass                    # 裝得上就一定收得回,收不回也不該蓋掉正事
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _begin_replace(target, action):
    """要動手改名了。從這一行起,收尾訊息就不可以再說「什麼都沒有動到」。

    action 是 'apply'(把改好的內容換上去)或 'restore'(把備份寫回去)。
    收尾訊息要靠它才講得出對的那一句:同樣是「已經換好了」,
    修改那條路要接還原指令,還原那條路接還原指令就變成叫人再做一次已經做完的事。
    """
    _PROGRESS['stage'] = 'replacing'
    _PROGRESS['target'] = os.fspath(target)
    _PROGRESS['action'] = action


def _mark_replaced():
    """正本已經被換掉了 —— 中斷訊息要改成「已經換好了,要回原樣就 --restore」。"""
    _PROGRESS['stage'] = 'replaced'


def _abandon_replace():
    """這一次改名確定沒有發生 —— 把登記收回「還沒動」。

    ⚠️ 只收 'replacing'。同一個檔案系統上 os.replace 是原子的,它丟例外就代表
       一個位元組都沒換過,所以收回去是誠實的;而已經登記成 'replaced' 的
       **絕對不收** —— 那會讓收尾訊息謊報「沒動到」,玩家就不會去還原。
    """
    if _PROGRESS['stage'] == 'replacing':
        _PROGRESS['stage'] = 'idle'
        _PROGRESS['target'] = None
        _PROGRESS['action'] = None


def _replace_state_note(fallback_path):
    """收尾訊息裡「檔案到底動了沒」那一段,一律照三態登記來寫,不用猜。"""
    who = _PROGRESS['target'] or fallback_path
    stage = _PROGRESS['stage']
    if stage == 'replaced':
        if _PROGRESS['action'] == 'restore':
            # 還原那條路上「已經換好了」的意思是「備份已經寫回去了」。
            # 這裡再印一次 --restore 就是叫人重做一件已經做完的事,所以不印。
            return ('  ⚠️ 還原那一步在這之前就已經做完了(改名那一步跑完了)——\n'
                    '  你那顆執行檔現在已經是備份的內容。')
        return ('  ⚠️ 檔案在這之前就已經換好了(改名那一步跑完了)。\n'
                '  要回到原樣就跑這一行:\n    %s' % _restore_hint(who))
    if stage == 'replacing':
        return ('  ⚠️ 出事的時候正在替換 %s —— 它可能已經被換掉了。\n'
                '  請跑這一行還原,或自己拿備份比對:\n    %s'
                % (os.path.basename(who), _restore_hint(who)))
    return ('  上面印到哪一步就是做到哪一步:沒印出「已寫入」或「已還原」就代表\n'
            '  遊戲執行檔還沒被換掉。')


def _reject_symlink(p, what):
    """p 是符號連結就停下來,而且 exit code 不是 0。"""
    p = os.fspath(p)
    if os.path.islink(p):
        raise SystemExit(
            '\n  停下來了:%s是一條符號連結(捷徑)——\n'
            '    %s\n'
            '  本工具不跟著捷徑走 —— 跟著走的話,真正被動到的檔可能不是你\n'
            '  以為的那一個,而畫面照樣會印成功,那比直接失敗更難發現。\n'
            '  請直接對真正的那個檔跑一次,或先把這條捷徑刪掉 / 改名。\n' % (what, p))


def _mkstemp_beside(dst, tag):
    """在 dst 那個資料夾裡開一個猜不到、也不可能被事先佔住的暫存檔。

    一定要跟 dst 同一個資料夾:os.replace 只有在同一個檔案系統上才是原子改名,
    丟到系統暫存區再搬過來就變成跨檔案系統的複製,原子性就沒了。
    """
    dst = os.fspath(dst)
    d = os.path.dirname(os.path.abspath(dst)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(dst) + '.' + tag + '-')


def _unlink_quiet(p):
    """把暫存檔收掉。收不掉也不要蓋掉正在往上丟的那個例外。"""
    try:
        os.remove(p)
    except OSError:
        pass


def _restore_hint(path):
    """「立刻還原」那一行寫成可以直接複製貼上的指令。"""
    me = os.path.basename(sys.argv[0]) or 'mvp_modernize.py'
    return 'python3 %s "%s" --restore' % (me, path)


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    做法是兩步:先整份複製到「同一個資料夾裡的一個隨機暫存檔」,
    寫完 flush + os.fsync 之後才用 os.replace 把它改名成 dst。
    同一個檔案系統上的改名是原子的,所以「dst 這個名字」在任何一個瞬間
    要嘛還不存在、要嘛就是一份完整的備份,不會有中間狀態。
    途中出任何狀況(含 Ctrl-C)都會把暫存檔收掉再把例外往上丟。

    ── 2026-09-05 拿掉可以事先算出來的暫存檔名(唯讀資安稽核抓到)──────
    原本的暫存檔就叫 dst + '.part',名字任何人都算得出來。只要那個名字
    先被放成一條指向資料夾外面的符號連結,shutil.copy2() 就會**跟著連結**
    把外面那個檔截成 0 再寫進去;後面的 os.replace 只換掉連結本身,
    但外面那個檔在那之前就已經被吃掉了。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _reject_symlink(dst, '備份檔')
    fd, part = _mkstemp_beside(dst, 'part')
    try:
        with open(src, 'rb') as fsrc, os.fdopen(fd, 'wb') as fdst:
            shutil.copyfileobj(fsrc, fdst)
            fdst.flush()
            os.fsync(fdst.fileno())
        try:
            shutil.copystat(src, part)  # copy2 的另一半:時間戳。抄不過去不算失敗
        except OSError:
            pass
        if os.path.getsize(part) != os.path.getsize(src):
            raise OSError('備份只複製了一部分,不敢把它當成一份完整的備份')
        # 這一次改名**沒有**包 _NoInterrupt,是想過才這樣的:換的是備份那個檔名,
        # 不是遊戲執行檔。Ctrl-C 剛好落在這裡的話,備份是完整的一份,
        # 而「遊戲執行檔一個位元組都沒有動到」照樣是真話 —— 沒有訊息會說謊。
        os.replace(part, dst)          # os.replace 是原子的
    except BaseException:
        try:
            os.close(fd)               # 上面那個 with 已經關掉時會丟 EBADF
        except OSError:
            pass
        _unlink_quiet(part)
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

    # 第 2 道:BIGF 封裝檔。檔頭第 4-8 個位元組寫著「我應該有多長」,
    #   跟實際長度一比就知道有沒有被截斷。本站實測本機 295 個 BIGF 檔,
    #   288 個小端序、7 個大端序,所以兩種讀法都接受,任一種對得上就放行。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:LOCH 語系檔。位移 16 起 4 個位元組(小端序)指向 LOCL 區,
    #   LOCL 區再往後 12 個位元組是字串條數,接著是每條 4 個位元組的位移表。
    #   檔案被截斷時,最後一條字串的位移一定會指到檔案結尾外面。
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

    # 第 4 道:MZ 執行檔(這支腳本自己的備份就是走這一道)。
    #   0x3C 起 4 個位元組指向 PE 檔頭;PE+6 是節區數、PE+20 是 Optional Header
    #   的長度,節區表就接在 Optional Header 後面,每個節區 40 個位元組,
    #   其中 +16 是資料長度、+20 是資料在檔案裡的位移(都是小端序)。
    #   把每個節區的「位移 + 長度」取最大值,那就是這個檔至少該有多長。
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
    # 前面那幾道都是格式專屬的,認不出格式的備份就只剩這一道。
    # 用「不到一半」當門檻而不是「大小要相同」:原地改的工具改完大小幾乎不變,
    # 但也可能差幾個位元組,抓太緊會擋掉每一次正常的還原。
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _do_copy(bak, dst):
    """真正覆蓋的那一步,單獨拆成一個函式,是為了讓上面每一道守門都寫成
    「檢查不過就 raise,檢查過才走到這裡」,不會有哪一條路徑漏掉檢查。

    ── 2026-09-05 改成原子還原(唯讀資安稽核抓到的 🔴)────────────────
    原本是 shutil.copy2(bak, dst)。copy2 會**先把 dst 截成 0 bytes**,
    再一段一段把備份寫進去。中途按 Ctrl-C、磁碟滿、外接碟被拔掉,
    玩家的遊戲執行檔就停在 0 或半截 —— 而這一支正是「出事時用來救命」的那條路,
    救命的路自己把檔吃掉是最不能接受的一種。
    (前面那幾道守門擋的是「備份本身壞掉」,擋不到「複製到一半死掉」。)

    現在的順序:
      1. 在 dst 那個資料夾裡開一個隨機暫存檔(mkstemp,而且先擋符號連結)
      2. 把備份的內容整份寫進去,flush + os.fsync 真的落地
      3. 把 dst 原本的權限抄到暫存檔(不然執行檔會掉可執行位元)
      4. 再讀回來,跟備份比 sha256,不一樣就當場失敗
      5. 全部過了才 os.replace(暫存檔, dst) —— 這一步是原子的
    任何一步失敗都把暫存檔收掉,dst 一個位元組都沒被碰過。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _reject_symlink(bak, '備份檔')
    _reject_symlink(dst, '要還原的目標檔')
    with open(bak, 'rb') as f:
        want = f.read()
    fd, tmp = _mkstemp_beside(dst, 'restore')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(want)
            f.flush()
            os.fsync(f.fileno())
        try:
            shutil.copymode(dst, tmp)   # dst 已經被刪掉就沒有權限可抄,跳過
        except OSError:
            pass
        with open(tmp, 'rb') as f:
            got = f.read()
        if hashlib.sha256(got).hexdigest() != hashlib.sha256(want).hexdigest():
            raise OSError('寫出來的暫存檔跟備份對不起來,沒有換上去')
        _begin_replace(dst, 'restore')
        with _NoInterrupt():           # 改名 + 登記中間不接受 Ctrl-C(見 _NoInterrupt)
            os.replace(tmp, dst)
            _mark_replaced()
    except BaseException:
        try:
            os.close(fd)                # 上面那個 with 已經關掉時會丟 EBADF
        except OSError:
            pass
        _unlink_quiet(tmp)
        # 走到這裡如果登記還停在「正在換」,就代表 os.replace 沒做成(它是原子的,
        # 丟例外就是沒換);已經是「已換」的不會被收回去。
        _abandon_replace()
        raise




try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# BACKUP_SUFFIX:備份的檔名就是「原檔名 + 這條尾巴」,所以備份一定跟遊戲執行檔
#   躺在同一個資料夾,不會被丟到暫存區然後被系統清掉。每一支本站腳本的尾巴都不同,
#   這樣四支工具的備份放在一起也不會互相蓋掉。
# LARGE_ADDRESS_AWARE:PE 檔頭 Characteristics 那個 16 位元欄位裡的一個位元。
#   整個 --4gb 做的事就是把這一個位元從 0 變成 1,其他什麼都沒動。
# MACHINE_I386:COFF 檔頭的 Machine 欄位,0x014C 代表 32 位元 x86。
#   這支只把它印出來給你確認,不會去改(改了也不會讓程式變成 64 位元)。
BACKUP_SUFFIX = '.modernizebak'
LARGE_ADDRESS_AWARE = 0x0020          # PE Characteristics 的旗標位元
MACHINE_I386 = 0x014C

# 遊戲內建的解析度表:8 筆,四種尺寸各有 16 與 32 位元色深:
#   640x480 / 800x600 / 1024x768 / 1280x1024,每種各有 16 與 32 位元色深。
#
# ⚠️ 特徵故意用**後四筆**(1024x768 與 1280x1024),不是開頭那兩筆。
#    原因:改解析度時換掉的是最前面那組 640x480,
#    如果拿它當特徵,改完之後腳本就再也找不到自己改過的表了
#    (第一版真的是這樣,執行一次就看到了)。後四筆不會被這支腳本動到。
RECORD = 16
TABLE_ROWS = 8
TAIL_SIGNATURE = (struct.pack('<IIII', 1024, 768, 16, 0) +
                  struct.pack('<IIII', 1024, 768, 32, 0) +
                  struct.pack('<IIII', 1280, 1024, 16, 0) +
                  struct.pack('<IIII', 1280, 1024, 32, 0))
TAIL_OFFSET = 4 * RECORD          # 後四筆從表的第 5 筆開始

# 記憶體池:遊戲開機時 malloc 一大塊自己切,全部資源(球場、字型、.big)都住在裡面。
# 原廠 64 MB 是照 2005 年主機的額度切的。中文字型要在執行時展開成貼圖,
# 光字型就吃掉 13.50 MB,配上大球場就會把池子撐爆 → 配置失敗 → 對 NULL 寫入 → 當機。
# 樣態:push imm32 / call rel32 / pop ecx / ret,imm 是 1 MB 的倍數且落在 64..1024 MB。
POOL_RE = re.compile(rb'\x68(....)\xe8....\x59\xc3', re.S)
POOL_MIN = 64 * 1024 * 1024
POOL_MAX = 1024 * 1024 * 1024


# ─────────────────────────────────────────────────────────
#  PE 檔頭
# ─────────────────────────────────────────────────────────
def pe_offsets(data):
    """回傳 (PE 起點, Characteristics 位置, CheckSum 位置)。不是 PE 就丟錯。

    這三個位置全部用算的,不用搜,因為 PE 檔的排法是固定的:
      · 位移 0x3C 起 4 個位元組(32 位元小端序)寫著 PE 檔頭在哪裡。
      · 那個位置起 4 個位元組是 P、E、0x00、0x00,接著 20 個位元組的 COFF 檔頭。
      · 下面的 +N 一律從「PE 起點」算,不是從 COFF 檔頭起點算,兩者差 4 個位元組。
      · Characteristics 在 PE 起點 +22,佔 2 個位元組,--4gb 動的就是它。
        它在 COFF 檔頭裡自己的位移是 18,而 COFF 檔頭一共只有 20 個位元組,
        本來就裝不下「+22」;照字面推成「COFF 起點 +22」會算到 PE 起點 +26,
        那裡已經是 Optional Header 的連結器版本,寫下去旗標不會生效,還會把
        版本號蓋掉。
      · Optional Header 從 PE 起點 +24 開始,剛好接在 COFF 檔頭後面;
        CheckSum 在 Optional Header 的 +64。
      · PE 起點不是固定值,所以這三個位置一定要算、不能記。本站測試機上量過的
        21 個 mvp2005.exe 裡,英文版那 13 個(5,443,584 / 6,972,001 / 6,976,094
        位元組)PE 起點都在 0x128,Characteristics 落在 0x13E、CheckSum 落在
        0x180;中文版那 8 個(7,525,175 / 7,533,368 位元組)PE 起點在 0x130,
        Characteristics 落在 0x146、CheckSum 落在 0x188。
    這裡故意不接受「看起來差不多像 PE」的檔案:MZ 不對、PE 簽章不在該在的地方、
    或是檔案短到連 PE 檔頭都讀不完,一律當成「這不是我認得的檔」停下來,
    不要在看不懂的檔案上算位址。
    """
    if len(data) < 0x40 or data[:2] != b'MZ':
        raise DataError('這個檔的開頭不是 MZ,不是 Windows 執行檔。')
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    if pe + 24 > len(data) or data[pe:pe + 4] != b'PE\x00\x00':
        raise DataError('找不到 PE 檔頭,這個檔可能已損毀。')
    # 這一行要驗到 CheckSum 的最後一個位元組(PE 起點 +88 +4 = +92,也就是
    # +24 +68)。只驗到 +24 的話,一顆「開頭是 MZ、PE 簽章也在、但檔案被截斷」
    # 的執行檔會過這一關,然後在 describe() 讀 CheckSum 時噴 Python 追蹤訊息。
    if pe + 24 + 68 > len(data):
        raise DataError('PE 檔頭在 0x%X,但整個檔只有 %d 位元組 —— 讀不完檔頭,'
                        '這個檔是半截的。' % (pe, len(data)))
    return pe, pe + 22, pe + 24 + 64      # Optional header 起點 +64 = CheckSum


def pe_checksum(data, ck_off):
    """PE 檔頭的 CheckSum:16 位元加總(進位摺回)+ 檔案大小。

    計算時把 CheckSum 欄位自己當成 0。
    ⚠️ 本站拿一個已經套過修正的執行檔驗過這個算法:算出來跟它檔頭裡寫的
       完全相同。另外兩份剛安裝好的原版檔頭寫的是 0 —— EA 沒有填,
       而 Windows 對一般程式本來就不檢查這一欄。所以這裡算對是為了工整,
       不是因為不算會壞。

    算法本身:整個檔案每 2 個位元組當成一個小端序的 16 位元數字加起來,
    每加一次就把進位摺回低 16 位元(這樣總和永遠不會溢位);跳過 CheckSum
    欄位自己那 4 個位元組(當成 0);檔案長度是奇數時最後那一個位元組單獨加;
    最後再加上檔案總長度。
    """
    s = 0
    n = len(data)
    for i in range(0, n - (n & 1), 2):
        if ck_off <= i < ck_off + 4:
            continue
        s += data[i] | (data[i + 1] << 8)
        s = (s & 0xFFFF) + (s >> 16)
    if n & 1:
        s += data[-1]
        s = (s & 0xFFFF) + (s >> 16)
    s = (s & 0xFFFF) + (s >> 16)
    return (s + n) & 0xFFFFFFFF


def find_table(data):
    """用內容找解析度表。回傳起點位置。找不到就講清楚,不猜。

    找法:把後四筆(1024x768 與 1280x1024,各有 16 與 32 位元色深)接成
    64 個位元組的特徵去搜,搜到之後往回退 TAIL_OFFSET 就是整張表的起點。
    每一筆固定 16 個位元組、四個 32 位元小端序數字,所以特徵是可以直接算出來的。

    找到不只一處也停下來,不用「第一個」湊答案。這種檔案上猜錯位址,
    寫下去就是把別的東西改壞。
    """
    hits = []
    start = 0
    while True:
        i = data.find(TAIL_SIGNATURE, start)
        if i < 0:
            break
        hits.append(i - TAIL_OFFSET)
        start = i + 1
    if not hits:
        raise DataError('在這個執行檔裡找不到解析度表。\n'
                        '  本站是用後四筆(1024x768 與 1280x1024,各有 16 與 32 位元色深)\n'
                        '  連在一起當特徵找的。找不到代表這個版本的表長得不一樣 ——\n'
                        '  腳本不敢亂猜位址。')
    if len(hits) > 1:
        raise DataError('找到 %d 個看起來像解析度表的地方(%s)。\n'
                        '  不確定是哪一個,所以停下來。'
                        % (len(hits), '、'.join('0x%X' % h for h in hits)))
    return hits[0]


def find_pool(data):
    """回傳 [(imm32 的檔案位移, 目前的位元組數), ...]。

    通常會找到兩處。本站在測試機那顆 5,443,584 bytes 的 mvp2005.exe 上量到:
    push 那個位元組在 0x3736F0 與 0x3CDD08(本函式回傳的是它們的立即數位移
    0x3736F1 與 0x3CDD09;64 MB 改成 128 MB 真正動到的是最高位那一格,
    也就是 0x3736F4 與 0x3CDD0C)。兩處的 push 五個位元組完全相同,
    後面 call 的相對位移不同,但算出來的目標是同一個位址 0x3CDCCC。
    把整個 .text 的 E8 相對呼叫掃過一遍,0x3736F0 有 1 個直接呼叫者、
    0x3CDD08 是 0 個,兩個位址也都沒有以 4 位元組常數出現在檔案的任何地方。
    這是純位元組比對的結果,沒有反組譯去確認 0x3CDD08 有沒有間接呼叫
    (例如透過表格或算出來的位址),所以只講到「1 比 0」為止,
    不能斷定它就是編譯器留下的死碼。兩處一起改,反正它們本來就是同一個值。

    找法是找那一段機器碼的形狀(POOL_RE):push 一個 32 位元立即數、
    call 一個相對位址、pop ecx、ret。m.start() 指到 push 那個位元組,
    +1 才是立即數本身的位移,所以回傳的是 m.start() + 1。
    """
    out = []
    for m in POOL_RE.finditer(data):
        v = struct.unpack('<I', m.group(1))[0]
        # 光靠指令形狀會撞到一堆不相干的地方,所以再要求這個數字
        # 「剛好是 1 MB 的整數倍,而且落在 64 MB 到 1024 MB 之間」。
        # 記憶體池的大小本來就是照 MB 開的,一般常數不會剛好長這樣。
        if v % (1024 * 1024) == 0 and POOL_MIN <= v <= POOL_MAX:
            out.append((m.start() + 1, v))
    return out


def read_table(data, base):
    """把整張表的八筆讀出來,每筆回傳 (寬, 高, 色深, 保留欄)。

    一筆 16 個位元組、四個 32 位元小端序數字,所以第 k 筆在 base + k * 16。
    最後那個保留欄本站沒有量出它的用途,所以讀出來但不動它。
    """
    out = []
    for k in range(TABLE_ROWS):
        w, h, dep, pad = struct.unpack_from('<IIII', data, base + k * RECORD)
        out.append((w, h, dep, pad))
    return out


def _mtime(p):
    """檔案的最後修改時間,印成 YYYY-MM-DD HH:MM。

    備份是哪一天留下來的,是玩家判斷「這份是不是我這顆檔的備份」最直覺的線索,
    所以每次提到備份都把它印出來。
    """
    return datetime.datetime.fromtimestamp(
        os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M')


def _utc_date(ts):
    """把 PE 的 TimeDateStamp(1970-01-01 起算的秒數)換成 YYYY-MM-DD。

    ⚠️ 這裡刻意不用 datetime.utcfromtimestamp()。它從 Python 3.12 起被標成
       deprecated:腳本跑到讀時間戳那一行時,畫面中間會插進兩行英文警告
       (把輸出導到檔案或管線的話會跑到最上面)
       (本站在 3.12.13 與 3.14.4 上各實測過一次,3.11.15 上沒有)——
       退休球員看到那兩行會以為腳本壞了。
       更重要的是官方寫明「未來版本會移除」。真的移除那天,這一行會掉進
       呼叫端的 except,把一個好好的日期印成「不是合理的日期」——
       那就從噪音變成假話,而這一課正是靠這個欄位告訴你「這顆檔被動過」。
       (本站的餌:在 3.12 上加 -W error::DeprecationWarning 跑舊寫法,
       同一顆檔的編譯時間戳當場變成「不是合理的日期」。)
       改成自己從 1970-01-01 加秒數:一樣是 UTC、印出來一模一樣,
       本站在 3.9 / 3.11 / 3.12 / 3.14 各跑過一次都沒有警告,
        而這個寫法本身從來沒有被標成 deprecated 過。TimeDateStamp 是無號 32 位元,
       最大 0xFFFFFFFF 也只到 2106 年,timedelta 加得動,不會溢位 ——
       所以呼叫端那個 except 是保險,這個範圍裡叫不出例外來。
    """
    return (datetime.datetime(1970, 1, 1) +
            datetime.timedelta(seconds=ts)).strftime('%Y-%m-%d')


def edit_regions(data):
    """這支腳本會動到的每一段位元組,回傳 [(位移, 長度), ...];認不出結構就回傳 None。

    四個旋鈕加上校驗值,總共就這幾格:
      · Characteristics 2 個位元組(--4gb)
      · CheckSum 4 個位元組(跟著重算的那一次)
      · TimeDateStamp 4 個位元組(--timestamp)
      · 記憶體池每一處的 imm32 各 4 個位元組(--pool)
      · 解析度表第 1、2 筆的寬與高各 8 個位元組(--resolution)

    位置全部從傳進來的那份資料自己算(不是寫死的),所以拿備份算出來的位置
    對得上備份自己那個版本,不會把英文版的位址套到中文版上。
    """
    try:
        pe, ch_off, ck_off = pe_offsets(data)
    except DataError:
        return None
    regions = [(ch_off, 2), (ck_off, 4), (pe + 4 + 4, 4)]
    for off, _v in find_pool(data):
        regions.append((off, 4))
    try:
        base = find_table(data)
    except DataError:
        # 找不到解析度表不影響判斷:那代表這支腳本在這顆檔上本來就改不到那張表,
        # 於是「表的那幾格」也不該被算進允許範圍。
        pass
    else:
        regions.append((base, 8))
        regions.append((base + RECORD, 8))
    return regions


def backup_mismatch(bak, live):
    """備份與現在這顆執行檔對不對得起來?對得起來回傳 None,對不起來回傳一句原因。

    ── 為什麼要有這一關(2026-09-05 加)────────────────────────────
    備份只認檔名(執行檔路徑 + .modernizebak),不記它是哪一顆執行檔的備份。
    玩家把 mvp2005.exe 換成另一顆變體(這一課自己就說「玩久了資料夾裡常常會有
    一排執行檔」)卻沒刪舊備份,再跑一次 --apply,腳本會沿用那份**別顆執行檔**
    的備份;之後 --restore 就把完全不同的二進位蓋上去,而且原本那幾道守門
    一道都不會亮(本站實測:兩顆都是 5,443,584 位元組、都是 MZ、節區表都對得上),
    畫面還會印「已還原 ✅ / 內容與備份相同 ✅」—— 玩家那顆就這樣沒了。

    「對得起來」的定義:大小一樣,而且兩份不同的位元組**全部**落在
    edit_regions() 那幾格裡 —— 也就是「現在這顆看起來就是這份備份被這支腳本
    改過的樣子」。反覆 --apply 幾次都還是落在那幾格裡,所以不會誤擋正常流程;
    中間被別的工具動過(例如改節區旗標)就會落在外面,這一關就會亮。
    """
    if len(bak) != len(live):
        return '大小不一樣:備份 %d 位元組、現在這顆 %d 位元組。' % (len(bak), len(live))
    if bak == live:
        return None
    regions = edit_regions(bak)
    if regions is None:
        return '讀不出備份的 PE 結構,沒辦法確認它是不是這顆檔的備份。'
    allowed = set()
    for off, ln in regions:
        allowed.update(range(off, off + ln))
    stray = [i for i in range(len(bak)) if bak[i] != live[i] and i not in allowed]
    if stray:
        return ('有 %d 個位元組對不上,而且不在這支腳本會動的那幾格裡(前幾個:%s)。'
                % (len(stray), '、'.join('0x%06X' % i for i in stray[:8])))
    return None


# ─────────────────────────────────────────────────────────
#  各種動作
# ─────────────────────────────────────────────────────────
def load(path):
    """整個檔一次讀進記憶體。執行檔只有幾 MB,一次讀完最單純,
    也讓後面的複驗可以直接拿「原本的內容」跟「寫回去之後再讀出來的內容」逐位元組比。
    """
    if not os.path.isfile(path):
        raise DataError('找不到 %s' % path)
    with open(path, 'rb') as f:
        return f.read()


def describe(path):
    """把這個執行檔看得到的東西全部印出來,順便把後面要用的位置回傳出去。

    回傳 (整個檔的內容, PE 起點, Characteristics 位置, CheckSum 位置,
    解析度表起點, 解析度表八筆內容)。找不到解析度表時後兩項是 None,
    這樣 --4gb 這種不需要那張表的動作照樣做得下去,不會被一起擋掉。

    ⚠️ 這個函式只讀不寫。四個旋鈕的寫入都在 apply_changes() 裡,
       而且它也是先呼叫這一支拿到同一份資料,你看到的預覽跟真的會做的事才是同一件。
       但「所有寫入」不只那一處:cmd_restore() 也會寫檔,而且不看 --apply,
       守門過了就把備份寫成一個暫存檔、比對過內容才原子改名蓋回執行檔。
    """
    data = load(path)
    pe, ch_off, ck_off = pe_offsets(data)
    # 三個欄位都是小端序:Machine 2 個位元組、Characteristics 2 個、CheckSum 4 個。
    machine = struct.unpack_from('<H', data, pe + 4)[0]
    chars = struct.unpack_from('<H', data, ch_off)[0]
    stored_ck = struct.unpack_from('<I', data, ck_off)[0]

    print('  檔案 %s(%d 位元組)' % (os.path.basename(path), len(data)))
    print('  架構 0x%04X = %s' % (machine, '32 位元 x86' if machine == MACHINE_I386 else '不是 32 位元 x86'))
    print('  記憶體上限 %s'
          % ('4 GB(大位址旗標已開)✅' if chars & LARGE_ADDRESS_AWARE else '2 GB(大位址旗標沒開)'))
    print('  檔頭校驗值 0x%08X%s' % (stored_ck, '(EA 沒有填,一般程式 Windows 不檢查)' if stored_ck == 0 else ''))
    ts = struct.unpack_from('<I', data, pe + 4 + 4)[0]
    try:
        ts_txt = _utc_date(ts)
    except Exception:
        ts_txt = '不是合理的日期'
    # MVP Baseball 2005 是 2005 年出的。時間戳落在那前後幾年以外,
    # 就代表這個欄位被動過(脫殼工具常把它填成固定的假值)。
    note = ''
    if ts_txt[:4].isdigit() and not (2003 <= int(ts_txt[:4]) <= 2006):
        note = '  ← 這不是真的編譯日期,是被改過的痕跡'
    print('  編譯時間戳 %s%s' % (ts_txt, note))
    # 檢查碼欄位只印十六進位(上面那一行),不把它解成文字 —— 那 4 個位元組是什麼記號不是這一課的事。
    # 記憶體池找不到不算錯:有光碟保護的原版程式碼是加密的,本來就搜不到樣態。
    # 所以這裡只是印一行說明,不丟例外,--4gb 與解析度照樣可以做。
    pool = find_pool(data)
    if pool:
        print('  記憶體池 %d MB(遊戲自己切的那一塊,球場與字型都住在裡面)'
              % (pool[0][1] // (1024 * 1024)))
    else:
        print('  記憶體池:找不到(這個版本的樣態不一樣,或是有光碟保護)')
    # 同理,解析度表找不到也只是少一項功能,不是整支停擺。
    # 把錯誤訊息印出來,回傳的表起點與內容給 None,由呼叫端決定要不要繼續。
    try:
        base = find_table(data)
    except DataError as e:
        print()
        print('  解析度表:%s' % e)
        return data, pe, ch_off, ck_off, None, None
    rows = read_table(data, base)
    print()
    print('  解析度表在 0x%X(用內容找到的,不是寫死的位址):' % base)
    for k, (w, h, dep, _) in enumerate(rows, 1):
        print('    第 %d 筆   %5d x %-5d  %2d 位元色深' % (k, w, h, dep))
    return data, pe, ch_off, ck_off, base, rows


def cmd_check(path):
    """沒帶任何旋鈕時走這裡:只體檢,然後告訴你有哪些旋鈕可以轉。

    這條路徑上完全沒有寫檔的程式碼,所以「不小心改到東西」在這裡是不可能的。
    """
    describe(path)
    print()
    print('  以上全部是唯讀的,沒有動到任何東西。')
    print('  想改的話:')
    print('    --4gb                     把記憶體上限從 2 GB 提到 4 GB')
    print('    --resolution 1920x1080    把解析度表裡最小的那一組換成你要的')
    print('    --pool 128                把遊戲自己那塊記憶體池從 64 MB 調大')


def apply_changes(path, want_4gb, want_res, want_pool, want_stamp, apply_it):
    """算出這一次要改哪些位元組,列出來,apply_it 是真的時才寫下去。

    流程是固定的一條線:先唯讀描述一次 → 在記憶體裡的複本 out 上改
    → 把「改了幾個位元組、在哪幾個位置」列出來(位置只列前 16 個) → 沒有 --apply 就到此為止
    → 有 --apply 才備份、寫檔、重新讀回來複驗。

    orig 留著原始內容整份不動,最後拿它跟「寫完再讀出來的檔」逐位元組比。
    這樣就算中間哪一段算錯位置,也會在複驗那一關被抓出來,
    而不是等你進遊戲才發現。

    每一個旋鈕都先看「現在是不是已經是你要的值」,是的話就印一行說不用做,
    不會白白產生一次寫入。
    """
    if apply_it:
        # 要寫的那一刻才擋(唯讀體檢與預覽只讀不寫,SPEC 明訂讀取不限制),
        # 但要擋在「讀檔」之前:連結指到的東西不是執行檔時,玩家該看到的是
        # 「這是一條捷徑」,不是「開頭不是 MZ」——後者會讓人以為是遊戲檔壞了。
        _reject_symlink(path, '遊戲執行檔')
    data, pe, ch_off, ck_off, base, rows = describe(path)
    orig = bytes(data)
    # out 是可以改的複本,orig 是拿來比對的原件,兩份都在記憶體裡,
    # 檔案本身要到最後面確定要寫的時候才會被碰。
    out = bytearray(data)
    todo = []

    # ── 旋鈕 1:大位址旗標 ──
    # 讀出 Characteristics 這 2 個位元組,把 0x0020 這個位元 or 進去再寫回原位。
    # 檔案長度不變,其他位元也不變。
    if want_4gb:
        chars = struct.unpack_from('<H', out, ch_off)[0]
        if chars & LARGE_ADDRESS_AWARE:
            print()
            print('  ⓘ 大位址旗標本來就已經開了,這一項不用做。')
        else:
            struct.pack_into('<H', out, ch_off, chars | LARGE_ADDRESS_AWARE)
            todo.append('把記憶體上限從 2 GB 提到 4 GB(改 Characteristics 的 1 個位元)')

    # ── 旋鈕 2:編譯時間戳 ──
    # 使用者給的是 YYYY-MM-DD,要換算成 1970-01-01 起算的秒數再寫成 4 個位元組。
    if want_stamp is not None:
        # PE 檔頭的 TimeDateStamp。Windows 載入一般程式時不看它,
        # 但它是這個檔「來歷」的線索之一 —— 改掉之前請先讀下面那段警告。
        try:
            y, mo, dy = [int(x) for x in want_stamp.split('-')]
            epoch = int((datetime.datetime(y, mo, dy) -
                         datetime.datetime(1970, 1, 1)).total_seconds())
        except Exception:
            raise DataError('時間戳要寫成 YYYY-MM-DD,例如 2026-08-29。你給的是「%s」' % want_stamp)
        # TimeDateStamp 是無號 32 位元,只放得下 1970-01-01 到 2106 年之間。
        # 不先擋的話,--timestamp 1960-01-01 的日期字串本身是合法的,
        # 會一路走到 struct.pack_into 才炸成 Python 追蹤訊息。
        if not (0 <= epoch <= 0xFFFFFFFF):
            raise DataError('PE 的時間戳是無號 32 位元,只放得下 1970-01-01 到 '
                            '2106-02-07 之間的日期。你給的是「%s」' % want_stamp)
        ts_off = pe + 4 + 4
        cur_ts = struct.unpack_from('<I', out, ts_off)[0]
        try:
            cur_txt = _utc_date(cur_ts)
        except Exception:
            cur_txt = '0x%08X(不是合理的日期)' % cur_ts
        if cur_ts == epoch:
            print()
            print('  ⓘ 時間戳本來就是 %s,這一項不用做。' % want_stamp)
        else:
            struct.pack_into('<I', out, ts_off, epoch)
            todo.append('把編譯時間戳從 %s 改成 %s(改 4 個位元組)' % (cur_txt, want_stamp))

    # ── 旋鈕 3:記憶體池 ──
    # 找到的每一處都要改成同一個值。本站量到的是「1 比 0」:一處有直接呼叫者、
    # 另一處沒有(細節見 find_pool 的說明),但沒有反組譯就不能斷定沒人呼叫的
    # 那一處是死碼;兩處本來就是同一個值,所以一起改最保險。
    if want_pool is not None:
        sites = find_pool(out)
        if not sites:
            raise DataError('這個執行檔裡找不到記憶體池的樣態,沒辦法改。'
                            '有光碟保護的原版執行檔程式碼是加密的,本工具不適用。')
        if not (64 <= want_pool <= 1024):
            raise DataError('記憶體池只接受 64 到 1024 MB,你給的是 %s。' % want_pool)
        new = want_pool * 1024 * 1024
        cur = sites[0][1]
        if all(v == new for _, v in sites):
            print()
            print('  ⓘ 記憶體池本來就是 %d MB,這一項不用做。' % want_pool)
        else:
            for off, _ in sites:
                struct.pack_into('<I', out, off, new)
            todo.append('把記憶體池從 %d MB 改成 %d MB(%d 處,各改 4 個位元組)'
                        % (cur // (1024 * 1024), want_pool, len(sites)))

    # ── 旋鈕 4:解析度 ──
    # 只換寬與高(每筆前 8 個位元組),色深與保留欄照原樣留著。
    # 表裡本來就有你要的尺寸就不做,免得白改一筆。
    if want_res is not None:
        if base is None:
            raise DataError('這個執行檔裡找不到解析度表,沒辦法改解析度。')
        try:
            w_s, h_s = want_res.lower().split('x')
            w, h = int(w_s), int(h_s)
        except Exception:
            raise DataError('解析度要寫成「寬x高」,例如 1920x1080。你給的是「%s」' % want_res)
        if not (640 <= w <= 7680 and 480 <= h <= 4320):
            raise DataError('%dx%d 超出合理範圍(寬 640-7680、高 480-4320),不敢寫。' % (w, h))
        if any(r[0] == w and r[1] == h for r in rows):
            print()
            print('  ⓘ 表裡本來就有 %dx%d,這一項不用做。' % (w, h))
        else:
            # 換掉最小的那一組(640x480 的 16 與 32 位元兩筆)。
            # 為什麼換最小的:那是今天不會有人選的尺寸,換掉它損失最小。
            for k in (0, 1):
                off = base + k * RECORD
                struct.pack_into('<II', out, off, w, h)
            todo.append('把第 1、2 筆的 %dx%d 換成 %dx%d(各改 8 個位元組)'
                        % (rows[0][0], rows[0][1], w, h))

    if not todo:
        print()
        print('  沒有事情要做。')
        return

    print()
    print('  要做的事:')
    for t in todo:
        print('    · %s' % t)

    # 校驗值:原本是 0 就維持 0(EA 就沒填),原本有值才重算。
    # 這裡刻意用 orig 讀原本的值,不是用已經改過的 out。要判斷的是
    # 「這個檔本來有沒有填」,不是「我剛剛有沒有動到它」。
    stored_ck = struct.unpack_from('<I', orig, ck_off)[0]
    if stored_ck != 0:
        struct.pack_into('<I', out, ck_off, pe_checksum(bytes(out), ck_off))
        print('    · 重算檔頭校驗值(原本有填,所以要跟著更新)')

    # 逐位元組比出「到底哪幾個位置變了」。不用自己記帳,因為記帳會漏。
    # 這樣算出來的清單等一下要拿去跟寫回檔案後的實際結果對,兩邊必須一模一樣。
    changed = [i for i in range(len(orig)) if orig[i] != out[i]]
    print()
    print('  總共會改 %d 個位元組,檔案大小不變(%d)。' % (len(changed), len(out)))
    # 位置只列前 16 個,畫面才不會被洗掉。總數以上面那一行為準。
    # 下面複驗比的是完整的 changed,不是這裡列出來的這幾個。
    print('  位置:%s' % '、'.join('0x%06X' % i for i in changed[:16]))

    if not apply_it:
        print()
        print('  以上是預覽,還沒有動到任何檔案。')
        print('  確定要改的話,在剛才那一行最後面加上 --apply')
        return

    # 到這裡才第一次碰到檔案系統。先備份,而且只在還沒有備份時才建立:
    # 第二次、第三次 --apply 都保留最早那一份,也就是你動手前的原版。
    # 遊戲執行檔的符號連結守門在這個函式最上面(要寫的時候、讀檔之前)。
    # 它以前擋不到:main() 會先把符號連結 realpath 成真檔再傳進來,
    # 等於「跟著連結寫」。2026-09-06 起 main() 不再 realpath,這一道才真的有用。
    backup = path + BACKUP_SUFFIX
    # 備份檔名是算得出來的(執行檔路徑 + 固定尾巴),所以它是最容易被事先佔住的
    # 那個名字。先擋符號連結,而且用 lexists 不用 exists ——
    # 一條指到不存在的東西的連結,exists() 會回 False,那就會被當成「沒有備份」
    # 直接往下走,寫進去就寫到連結指的地方去了。
    _reject_symlink(backup, '備份檔')
    if not os.path.lexists(backup):
        _atomic_copy(path, backup)
        print()
        print('  已備份 → %s' % os.path.basename(backup))
    else:
        print()
        print('  備份已存在,保留最早那一份 → %s(%d 位元組,%s)'
              % (os.path.basename(backup), os.path.getsize(backup), _mtime(backup)))
        # 沿用舊備份之前先確認它真的是「現在這顆執行檔」的備份。對不上就停下來,
        # 不在沒有正確備份的情況下動玩家的檔(理由見 backup_mismatch 的說明)。
        why = backup_mismatch(load(backup), orig)
        if why is not None:
            raise DataError(
                '這份備份跟現在這顆執行檔對不上,所以我不敢在沒有正確備份的情況下動它。\n'
                '  %s\n'
                '  備份:%s(%d 位元組,%s)\n'
                '  現在:%s(%d 位元組,%s)\n'
                '  多半是你換過另一顆執行檔,而舊的備份還留在旁邊。\n'
                '  請先把舊備份改名或搬到別的資料夾,再跑一次這一行 ——\n'
                '  腳本就會替現在這顆重新建一份備份。'
                % (why,
                   os.path.basename(backup), os.path.getsize(backup), _mtime(backup),
                   os.path.basename(path), len(orig), _mtime(path)))
    # 寫入本身也走「先寫暫存檔再改名」:改名是原子的,
    # 所以遊戲執行檔要嘛是舊的、要嘛是完整的新的,不會出現寫到一半的檔。
    # 暫存檔的名字以前是 path + '.tmp' —— 算得出來,就有人可以先把那個名字
    # 放成一條指向資料夾外面的捷徑,open(..., 'wb') 會跟著它去把外面那個檔截斷。
    # 現在用 mkstemp 開在同一個資料夾裡(隨機名字 + O_CREAT|O_EXCL),佔不住也跟不到。
    fd, tmp = _mkstemp_beside(path, 'apply')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(bytes(out))
            f.flush()
            os.fsync(f.fileno())       # 真的落到碟上,不是只到作業系統的快取
        # 新開的暫存檔拿的是系統預設權限(umask),直接改名過去會把執行檔原本的
        # 權限換掉 —— 本站實測 755 變成 644,Wine / Linux 那條路上就少了可執行位元。
        # 所以改名之前先把原本那顆的權限抄過來。只抄權限,不動時間戳:
        # 「這個檔今天被改過」本來就該看得出來。
        try:
            shutil.copymode(path, tmp)
        except OSError:
            # FAT32 隨身碟、某些網路磁碟不讓你設權限。抄不過去就算了 ——
            # 這一步是加分,不是必要,不能因為它讓整次修改失敗。
            print('  ⓘ 這個檔案系統不讓我設定權限,新的執行檔用的是預設權限。')
        _begin_replace(path, 'apply')  # 這一行之後,「什麼都沒動到」就不再保證是真的
        with _NoInterrupt():           # 改名 + 登記中間不接受 Ctrl-C(見 _NoInterrupt)
            os.replace(tmp, path)
            _mark_replaced()           # 這一行之後,「什麼都沒動到」就確定不是真的
    except BaseException:
        # 寫到一半出事(磁碟滿、外接碟被拔掉、按了 Ctrl-C):把半截的暫存檔收掉
        # 再把例外往上丟,不要在玩家的遊戲資料夾裡留一個看起來像執行檔的垃圾。
        # 走到這裡有兩種可能,而分辨它們的是登記本身,不是這個 handler 的猜測:
        #   (1) 改名還沒跑(還沒進不可中斷區,或 os.replace 自己丟例外)——
        #       登記停在「正在換」,_abandon_replace() 把它收回「還沒動」,
        #       收尾就可以誠實地說「一個位元組都沒有動到」;
        #   (2) 改名跑完了,_NoInterrupt 離開那一段之後才把 Ctrl-C 丟出來 ——
        #       那時登記已經是「已換」,_abandon_replace() 不會去動它,
        #       收尾訊息照三態說實話。
        try:
            os.close(fd)               # 上面那個 with 已經關掉時會丟 EBADF
        except OSError:
            pass
        _unlink_quiet(tmp)
        _abandon_replace()
        raise

    # ── 複驗:重新讀回來,而且確認「只有預期的位元組變了」──
    back = load(path)
    if len(back) != len(orig):
        raise DataError('寫入後檔案大小變了,請立刻還原:\n  %s' % _restore_hint(path))
    actual = [i for i in range(len(orig)) if orig[i] != back[i]]
    if actual != changed:
        # 複驗只要有一項對不上就當失敗:訊息裡直接給可以複製的還原指令,
        # 而且往上丟 DataError → main() 回傳 2,exit code 不會是 0。
        raise DataError('實際改動的位元組跟預期不符(預期 %d 個、實際 %d 個),請立刻還原:\n  %s'
                        % (len(changed), len(actual), _restore_hint(path)))
    print('  已寫入。複驗:改動的位元組剛好是預期那 %d 個,其他一個都沒動 ✅' % len(actual))
    print()
    print('  進遊戲看看。沒效果或有問題就 --restore。')


def cmd_restore(path):
    """把備份蓋回去,但覆蓋之前先確認那份備份自己是好的、而且真的是這顆檔的備份。

    三道:
      1. 這裡先看開頭是不是 MZ(拿錯檔就擋下來)。
      2. 這份備份對不對得上現在這顆執行檔(backup_mismatch):大小要一樣,而且
         兩份不同的位元組要全部落在這支腳本會動的那幾格裡。2026-09-05 加 ——
         在這之前,玩家換過執行檔卻沒刪舊備份,--restore 會把一顆完全不同的
         二進位蓋上去,還印「內容與備份相同 ✅」。執行檔不在了(被刪掉)就跳過
         這一道,那種時候「拿備份把它變回來」正是玩家要的。
      3. 交給 _restore_from_backup(),由它去驗 PE 節區表指到的長度有沒有
         超出檔案本身,那一道是擋半截備份的關鍵。
    還原完再讀一次兩邊比對,不同就當成失敗要你手動檢查。
    """
    backup = path + BACKUP_SUFFIX
    _reject_symlink(backup, '備份檔')
    _reject_symlink(path, '要還原的遊戲執行檔')
    if not os.path.lexists(backup):
        raise DataError('找不到備份 %s —— 沒有東西可以還原。' % os.path.basename(backup))
    with open(backup, 'rb') as f:
        if f.read(2) != b'MZ':
            raise DataError('備份檔開頭不是 MZ,不敢拿它覆蓋。')
    if os.path.isfile(path):
        why = backup_mismatch(load(backup), load(path))
        if why is not None:
            raise DataError(
                '這份備份跟現在這顆執行檔對不上,不敢拿它覆蓋。\n'
                '  %s\n'
                '  備份:%s(%d 位元組,%s)\n'
                '  現在:%s(%d 位元組,%s)\n'
                '  多半是你換過另一顆執行檔,而舊的備份還留在旁邊 ——\n'
                '  蓋下去的話,現在這顆就沒了。\n'
                '  真的要用這份備份的話,請自己在檔案總管 / Finder 裡\n'
                '  把 %s 複製成 %s,那樣你至少看得到自己在蓋掉什麼。'
                % (why,
                   os.path.basename(backup), os.path.getsize(backup), _mtime(backup),
                   os.path.basename(path), os.path.getsize(path), _mtime(path),
                   os.path.basename(backup), os.path.basename(path)))
    _restore_from_backup(backup, path)
    same = open(backup, 'rb').read() == open(path, 'rb').read()
    print('  已還原 ← %s' % os.path.basename(backup))
    print('  複驗:內容與備份%s' % ('相同 ✅' if same else '不同 ❌'))
    if not same:
        raise DataError('還原後內容跟備份不一樣,請手動檢查。')


def main():
    """指令列入口:決定這一次走還原、走修改,還是走唯讀體檢。

    三條路互斥,而且順序是有意義的:
    --restore 最優先(出事時那一行一定要能跑),
    接著是「有沒有帶任何一個旋鈕」,都沒有才落到唯讀體檢。

    DataError 與 OSError(權限不足、磁碟滿、外接碟被拔掉)一律在這裡收成
    一句人看得懂的話並回傳 2,不讓 Python 的追蹤訊息噴給玩家。
    Ctrl-C 回傳 130,那是慣例。
    傳進來的路徑如果本身是符號連結(捷徑),要寫的那兩條路(--apply / --restore)
    直接停下來,不跟著連結寫;唯讀體檢與預覽只讀不寫,照樣看得下去。
    """
    EPILOG = (
        "\n例子(照順序做):\n\n"
        "  1. 先看你手上那份是什麼(完全唯讀)\n"
        "     python3 mvp_modernize.py \"<遊戲資料夾>/mvp2005.exe\"\n\n"
        "  2. 預覽要改什麼(還是不會動到檔案)\n"
        "     python3 mvp_modernize.py \"<...>/mvp2005.exe\" --4gb --resolution 1920x1080\n\n"
        "  3. 確定了才真的改\n"
        "     python3 mvp_modernize.py \"<...>/mvp2005.exe\" --4gb --resolution 1920x1080 --apply\n\n"
        "  出問題就還原:\n"
        "     python3 mvp_modernize.py \"<...>/mvp2005.exe\" --restore\n"
    )
    ap = argparse.ArgumentParser(
        description='讓 MVP Baseball 2005 在今天的機器上跑得順(記憶體上限與解析度)',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)
    ap.add_argument('exe', help='遊戲執行檔的完整路徑(mvp2005.exe)')
    ap.add_argument('--4gb', dest='four_gb', action='store_true', help='把記憶體上限從 2 GB 提到 4 GB')
    ap.add_argument('--resolution', metavar='寬x高', help='換一個解析度進去,例如 1920x1080')
    ap.add_argument('--timestamp', metavar='YYYY-MM-DD',
                    help='改 PE 檔頭的編譯時間戳。⚠️ 那是這個檔來歷的線索之一,'
                         '改掉之前先看程式開頭的說明')
    ap.add_argument('--pool', type=int, metavar='MB',
                    help='把遊戲自己那塊記憶體池從 64 MB 調大(64-1024)。'
                         '中文語系配大球場會當,就是被這個卡住')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原')
    args = ap.parse_args()

    # ── 2026-09-06:路徑本身是符號連結時「拒絕」,不是 realpath 之後照寫 ──
    # 這裡以前是 exe = os.path.realpath(exe),理由是「不換的話 os.replace 會把
    # 連結本身換成一般檔案」。那個理由沒錯,但解法選錯邊了:跟著連結寫,等於
    # 讓一條放在遊戲資料夾裡的捷徑,把這支腳本導去改資料夾外面的任何一個檔。
    # 現在改成:**要寫**的路徑是符號連結就停下來(由 apply_changes / cmd_restore
    # 各自的 _reject_symlink 擋),讀取不限制 —— 唯讀體檢與預覽照樣看得下去。
    # 只看最後那一層:上層資料夾是連結不影響(有人把遊戲放在別顆碟)。
    exe = args.exe

    try:
        if args.restore:
            cmd_restore(exe)
        elif (args.four_gb or args.resolution is not None
              or args.pool is not None or args.timestamp is not None):
            # 2026-08-28 修:加 --pool 時忘了加進這個條件,
            # 單獨給 --pool 會安靜地掉到唯讀檢查 —— 使用者會以為改了但其實沒有。
            # (同一種錯 mvp_shrink_big.py 的 --apply 也犯過,toni 實際踩到)
            # 2026-09-05 修完另一半:當時寫成 `or args.pool`,而 --pool 0 的 0
            # 是 falsy,照樣安靜掉到唯讀體檢、exit 0,一個字都不提示
            #(--resolution "" 同理)。要用 `is not None`,「有沒有給這個旗標」
            # 才跟「給的值是不是真的」分得開 —— 值對不對由下面各自的檢查去擋。
            apply_changes(exe, args.four_gb, args.resolution, args.pool, args.timestamp, args.apply)
        else:
            cmd_check(exe)
    except DataError as e:
        print('\n  停下來了:%s\n' % e)
        return 2
    except OSError as e:
        # 作業系統不讓我們讀寫(遊戲裝在 Program Files 這種要管理員權限的位置、
        # 磁碟滿了、外接碟被拔掉)。原本這裡沒收,玩家看到的是 Python 追蹤訊息。
        # 不寫「你的檔沒事」這種保證,寫玩家自己看得到的判準:
        # 「已寫入」那一行是 os.replace 成功之後才印的。
        print('\n  停下來了:作業系統不讓我讀寫檔案 —— %s\n'
              '  常見原因:遊戲裝在 Program Files 這種需要管理員權限的位置、'
              '磁碟滿了、或是外接碟被拔掉。\n'
              '%s\n' % (e, _replace_state_note(exe)))
        return 2
    except KeyboardInterrupt:
        # 「什麼都沒有動到」只有在改名還沒開始的時候才是真的。
        # 已經換過、或中斷時正在換,都要老實說,並且把還原指令給他。
        if _PROGRESS['stage'] == 'idle':
            print('\n  已中斷,遊戲執行檔一個位元組都沒有動到。\n')
        else:
            print('\n  已中斷 ——\n%s\n' % _replace_state_note(exe))
        return 130
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
