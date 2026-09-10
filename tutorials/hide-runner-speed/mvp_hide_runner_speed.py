#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_hide_runner_speed.py
關掉 EA MVP Baseball 2005 轉播畫面右側的「跑壘者速度數值」。

    預覽(不會改檔)  python3 mvp_hide_runner_speed.py "路徑/ingame.big"
    實際套用        python3 mvp_hide_runner_speed.py "路徑/ingame.big" --apply
    還原            python3 mvp_hide_runner_speed.py "路徑/ingame.big" --restore
    列出項目        python3 mvp_hide_runner_speed.py "路徑/ingame.big" --list
    自我測試        python3 mvp_hide_runner_speed.py --selftest

原理:ingame.big 內的 fes_ingameinfobar.fel 用 QFS/RefPack 壓縮,
解開後是純文字版面腳本。GR:BASES 底下的壘包群組各帶著 TX:RATING,那就是那個數字,
把它的顯示開關由 1 改成 0 即可。
有幾個要看你手上那一份,所以這支程式不寫死數量,掃到幾個就報幾個。
本站測試機這一份 ingame.big(2,665,562 bytes / 47 個項目)是 6 個:
本壘、三壘、二壘的群組各帶一個,而 GR:FIRSTBASE 這個群組被宣告了兩次,
第一次那組帶一個、第二次那組帶兩個(其中一個座標 x=550 y=461)。
本站另一份社群名冊模組的 ingame.big(380,483 bytes / 48 個項目)則是四個壘包各一個。
(這個版面檔的作者就是用同一招關掉 TX:SPEED 與 TX:PLAYERNAME 的。
 注意:這個檔不在 EA 出貨的 ingame.big 裡,所以那不是 EA 的決定。
 EA 在自己出貨的版面檔裡也大量用這個開關,但這一份不是它們其中之一。)

寫回時採 append 模式:新資料接在檔尾,只改 TOC 8 bytes + 檔頭 4 bytes,
原始資料區一個 byte 都不動。切勿用「全部讀出再重新打包」的方式存檔,
這台測試機的 ingame.big 有九成內容是 TOC 不指向的歷史殘留,重新打包會讓檔案從 2.5 MB 掉到 198 KB。
(那是社群模組疊出來的,不是 EA 的格式性質:剛安裝好的原版 TOC 指到 99.1%。
 append 這條紀律照舊 —— 理由是你不知道手上這份被疊過什麼。)

輸入:
  · 一個 data/frontend/ingame.big 的路徑(把檔案拖進終端機就有)。
    這是唯一會被讀的檔。不讀設定檔,不連網路。
    會被寫的只有它自己、放在它旁邊的 <檔名>.bak,以及寫入途中短暫存在
    然後就被改名掉的中繼檔。中繼檔的名字是執行當下才生出來的隨機名
    (.<檔名>.tmp-xxxxxx 這種),用 tempfile.mkstemp 以 O_EXCL 建立 ——
    撞不到你的檔案,也沒有人能事先把那個名字佔起來。

輸出:
  · 不加旗標:把找到的每一個速度數值印成一張表(行號、壘包、座標),
    然後停下來。這條路從頭到尾只讀不寫。
  · --apply:先備份成 <檔名>.bak,再把改好的版面檔壓回去接到 .big 檔尾,
    最後重新讀出來複驗,把結果印給你看。
  · --restore:先把 .bak 寫到目標旁邊的中繼檔、跟備份逐位元組比對,
    全過了才原子換上去;換完再比一次才敢說成功。正本不會被截斷重寫。
  · --list:只把目錄裡每一項的名稱與長度印出來就停,不解壓、不改檔。
    「我這一份到底有沒有那個版面檔」用這個看最準 —— 項目數推不出來。
  · --selftest:自己造一個最小的封裝檔來把整條路跑一遍,完全不碰遊戲檔。
    裡面有 11 個反向餌,先證明「事情錯掉的時候它真的會叫」。
    在 python -O 下會拒絕跑並回傳 2:-O 會把 assert 全部拿掉,測試會假綠。

安全網(八層):
  1. 唯讀是預設,但這一句只涵蓋改檔那條路。沒有 --apply,這支程式不會碰你的硬碟。
     --restore 不在這一句裡。它是另一條路,不看 --apply,第 5 點那三道把關過了,
     就把 .bak 整份蓋回那個封裝檔。本站把測試機那份 ingame.big
     (2,665,562 bytes)複製到別的資料夾實測,只下 --restore、沒有加 --apply,
     那份複本的 MD5 當場變成備份的 MD5。
  2. 備份先寫到一個當下才生成的隨機中繼檔名、fsync、跟原檔逐位元組比對過
     才改名,中途被中斷不會留下半截備份;已經有 .bak 就保留最早那一份,不覆蓋。
     .bak 那個名字如果是符號連結就停下來 —— 不跟著它寫到資料夾外面去。
  3. 寫入先寫中繼檔、fsync、再 os.replace 換掉,不直接截斷原檔重寫。
     中繼檔名一樣是 tempfile.mkstemp 當場生的,沒有人搶得到那個名字。
     換掉之前把原檔的權限複製到新檔上,不然 0700 的遊戲檔會變成 0644。
     目標如果是符號連結,會寫的那兩條路(--apply / --restore)直接停下來,
     不跟著它寫到資料夾外面去;唯讀那條路不受限,跟著連結讀沒有風險。
  4. 寫完重新讀一次,四件事全部要成立:目錄項目數跟改前一樣、殘留未關的是 0 個、
     解壓行數跟改前一樣、讀回來的版面文字跟要寫進去的那一份逐字元相同。
     任一項不符就回傳 1 並叫你 --restore;而且如果那份 .bak 是這一次執行
     自己做的(保證是套用前那一秒的樣子),直接幫你還原回去,不用你自己下指令。
     ⚠️ 2026-09-05 之前「解壓行數」只印不驗:實測故意把行數從 951 弄成 953,
     腳本照樣印「完成」並回傳 0。現在四項全部進判斷式了。
  5. --restore 之前先確認三件事:備份開頭是 BIGF、目標開頭也是 BIGF、
     備份的前 64 KB 裡找得到 fes_ingameinfobar.fel。
     本站好幾課都會留下 .bak,這道是防止拿別課的備份蓋錯檔。
  6. 解壓完會比對長度:解出來的位元組數必須剛好等於 QFS 檔頭宣稱的數字。
     少一個都當成「這一項被截斷了」擋下來,不會拿半截的版面文字去改檔。
     本站對 MVP2026/data/frontend 的 98 個封裝檔共 9,643 個 QFS 項目,
     加上兩份剛安裝好的原版與一份社群名冊模組的 8,711 項,全部解出來的長度
     都剛好等於檔頭宣稱的數字 —— 這一道對健康的檔案不會有動靜。
  7. --restore 不是直接蓋正本:先寫到目標所在資料夾裡的隨機中繼檔、fsync、
     帶上正本原來的權限、跟備份逐位元組比對,全過了才 os.replace 換上去。
     中途任何一步失敗都只是刪掉中繼檔,正本一個位元組都沒被碰過。
     換上去之後再把備份與正本逐位元組比一次(先比長度再比內容),
     兩邊完全一樣才印「已從備份還原」;對不上就說清楚並回傳 1。
  8. Ctrl-C:「換檔那一刻」(os.replace)有沒有發生過會被記下來。沒發生過才敢說
     「一個位元組都沒有被動到」,發生過就叫你 --restore。兩種的離開碼都是 130,
     不會跟「複驗沒過」的 1 混在一起。而且「換名 + 登記」是包成不可中斷的一段:
     Ctrl-C 落在那兩行中間會先被記下來,等登記完才丟出去,收尾看到的狀態
     一定跟磁碟上的一致 —— 還有第三種狀態「正在換」,萬一連這道保險都裝不上,
     它會誠實說「不確定換好了沒有」,而不是猜一個好聽的。

做不到的事(先講清楚):
  · EA 出貨的 ingame.big 裡沒有 fes_ingameinfobar.fel(原版只有 44 個項目)。
    全新安裝跑這支會停下來說明原因,不會動任何東西。
  · 只把顯示開關由 1 改成 0,不刪除那些元素,也不動版面的其他任何部分。
  · 沒有「再打開」的旗標。想打開就 --restore。
  · 「改完在遊戲畫面上長怎樣」本站沒驗過。驗的是檔案層面:
    項目數不變、原始資料區逐位元組相同、還原後與原檔完全一致。

無外部相依,Python 3.7 以上即可。
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

import re
import os
import shutil
import signal
import struct
import sys
import tempfile
from pathlib import Path

# 這支程式「有沒有真的動到遊戲檔」只有一個開關:os.replace 把新檔換上去的那一刻。
# Ctrl-C 打斷時要照著它講話 —— 沒換過才可以說「一個位元組都沒有被動到」。
# (2026-09-05 補。原本沒有接 KeyboardInterrupt,Ctrl-C 會噴 traceback,
#  離開碼還是 1,跟「複驗沒過」長得一模一樣,使用者分不出檔案有沒有被改。)
#
# ⚠️ 2026-09-06 第三輪訂正:原本只有 replaced 一個布林,而它是在 os.replace
#    「回來之後」才被設起來的。Ctrl-C 剛好落在那兩行中間的話,收尾會照舊的值
#    講話 —— 檔案明明已經換掉了,螢幕上卻寫「一個位元組都沒有被動到」。
#    現在是三態,而且「換名 + 登記」被 _NoInterrupt 包成不可中斷的一段:
#      idle       還沒動過
#      replacing  正在換(_NoInterrupt 裝得上的話幾乎看不到,它是保險)
#      replaced   換過了
_STATE = {'replaced': False, 'phase': 'idle', 'target': None, 'kind': None}


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這段期間不讓 Ctrl-C 插隊。

    收到 SIGINT 先記著,離開這一段之後再照常丟出 KeyboardInterrupt。
    這樣收尾看到的登記一定跟磁碟上的狀態一致,不會出現「檔案換掉了但程式
    還以為沒換」的那一瞬間。

    ⚠️ signal.signal 只有主執行緒裝得上,裝不上就退回原本的行為 ——
       不會比以前更糟,而且外面那個 'replacing' 狀態就是為這種情形留的:
       真的落在縫裡,收尾會誠實說「不確定換好了沒有」,不會說「沒動到」。
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


def _refuse_symlink(path, what):
    """這個名字是符號連結就停下來,不跟著它寫下去。

    ⚠️ 不可以用 os.path.exists 判斷「這個名字有沒有被佔住」:符號連結指到
       一個不存在的檔(dangling)時 exists 回 False —— 名字明明被佔著,
       看起來卻是空的。要用 os.path.islink / os.path.lexists / os.lstat,
       它們看的是連結本身,不是連結指向的東西。
    """
    if os.path.islink(path):
        raise SystemExit(
            '這個名字是一個符號連結,本程式不跟著它寫:%s\n'
            '  (%s)寫過去會動到它指向的那個檔,而那個檔可能根本不在這個資料夾裡。\n'
            '  請先把它移走或換成實體檔,再跑一次。(目前沒有動到任何檔案。)'
            % (path, what))

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ⚠️ 2026-09-05 第二輪訂正:中繼檔名原本寫死成 <dst>.part,而那個名字
       是可以被別人先佔住的。只要事先在同一個資料夾放一個叫 <dst>.part、
       指向資料夾外面的符號連結,shutil.copy2 就會**跟著連結**把外面那個檔
       先截成 0 再寫滿備份內容;後面的 os.replace 只換掉連結本身,
       但外面那個檔早就被吃掉了。第一輪的做法是「這個名字有東西就停下來問你」,
       擋得住普通撞名,擋不住 dangling 連結 —— os.path.exists 對它回 False。
       改用 tempfile.mkstemp:名字執行當下才生、以 O_EXCL 建檔,搶不到也撞不到,
       所以那道「停下來問你」就不需要了。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_symlink(dst, '備份檔')
    fd, part = tempfile.mkstemp(dir=os.path.dirname(dst) or '.',
                                prefix='.' + os.path.basename(dst) + '.part-')
    try:
        with open(fd, 'wb') as fo, open(src, 'rb') as fi:
            shutil.copyfileobj(fi, fo, 1 << 20)
            fo.flush()
            os.fsync(fo.fileno())      # 落到碟上再改名,不然停電會留下空殼
        shutil.copystat(src, part)     # 權限與時間跟著原檔走(等同以前的 copy2)
        # 改名之前先確認寫出來的跟原檔逐位元組相同。這一道在「還沒有人叫它
        # .bak」的時候做,所以擋下來就是全身而退:沒有半截備份留在那個名字上。
        if not _same_bytes(src, part):
            raise SystemExit(
                '備份寫出來跟原檔對不起來(磁碟滿?),已經把半成品刪掉。\n'
                '  原檔沒有被動到,也沒有留下半截的 %s。' % dst)
        os.replace(part, dst)          # os.replace 是原子的
    except BaseException:
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

    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

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


# 真正覆蓋正本的動作,全程只有這一行。
# 上面每一道把關都必須先放行才會走到這裡。
# 獨立成一個函式,是為了「會動到硬碟的地方只有一處」好稽核。
def _do_copy(bak, dst):
    """把備份原封不動蓋回目標 —— 而且是原子的。

    ⚠️ 2026-09-05 第二輪訂正:原本這裡就是一行 shutil.copy2(bak, dst)。
       copy2 的做法是「先把 dst 截成 0 bytes,再一段一段寫進去」。
       備份再怎麼驗過都沒用:只要複製途中磁碟滿、外接碟被拔掉、按了 Ctrl-C、
       程式崩掉,遊戲正本就停在 0 bytes 或半截狀態 —— 而它是正本,
       不是備份,沒有第二份可以救。後面那道「還原完再比一次」只能告訴你
       「已經壞了」,擋不住它先被截斷。
       現在改成:寫到同一個資料夾裡的隨機中繼檔 → fsync → 帶上正本原來的權限
       → 跟備份逐位元組比對 → 全過了才 os.replace 換上去。
       中途任何一步失敗都只是刪掉那個中繼檔,正本一個位元組都沒被碰過。

    為什麼中繼檔一定要放在「目的檔所在的那個資料夾」:os.replace 只有在
    同一個檔案系統上才是原子的。放系統暫存區再搬過來就退化成複製,
    等於又回到會截斷正本的老路。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_symlink(dst, '要被還原的目標')
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst) or '.',
                               prefix='.' + os.path.basename(dst) + '.restore-')
    _swapped = False
    try:
        with open(fd, 'wb') as fo, open(bak, 'rb') as fi:
            shutil.copyfileobj(fi, fo, 1 << 20)
            fo.flush()
            os.fsync(fo.fileno())
        # 權限跟著「要被蓋掉的那個檔」走 —— 它才是遊戲在讀的那一個,
        # 0700 的遊戲檔不該還原成 0644。修改時間跟著備份走,
        # 跟以前 copy2 的行為一樣(還原本來就是回到備份那一刻)。
        try:
            shutil.copymode(dst, tmp)
        except OSError:
            pass
        try:
            _st = os.stat(bak)
            os.utime(tmp, ns=(_st.st_atime_ns, _st.st_mtime_ns))
        except OSError:
            pass
        if not _same_bytes(bak, tmp):
            raise SystemExit(
                '還原用的中繼檔寫出來跟備份對不起來(磁碟滿?),已經把它刪掉。\n'
                '  %s 沒有被動到,還是原來那一份。' % dst)
        # 換名與登記中間不可以有縫(2026-09-06)。備份蓋上去之後 Ctrl-C 才到,
        # 收尾要說「現在是備份那一份」,不可以說「一個位元組都沒有被動到」。
        _STATE['target'], _STATE['phase'] = dst, 'replacing'
        with _NoInterrupt():
            os.replace(tmp, dst)
            _swapped = True
            _STATE.update(replaced=True, phase='replaced', kind='restore')
    except BaseException as _e:
        if not _swapped:
            try:
                os.remove(tmp)
            except OSError:
                pass
            if isinstance(_e, OSError):
                # os.replace 自己失敗:換名確定沒有發生,狀態收回「還沒動」
                _STATE['phase'], _STATE['target'] = 'idle', None
        raise


def _same_bytes(a, b):
    """兩個檔逐位元組相同才回 True。

    ⚠️ 不可以用 zip() 把兩份資料配對著比 —— zip 走到短的那一邊就停,
       一份被截斷的檔會「每一對都相同」而通過。所以先比長度,再比內容。
    分段讀是為了不要把兩份封裝檔同時整份放進記憶體。
    """
    a, b = os.fspath(a), os.fspath(b)
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        while True:
            ca, cb = fa.read(1 << 20), fb.read(1 << 20)
            if ca != cb:
                return False
            if not ca:
                return True




# Windows 主控台預設編碼(繁中是 cp950)存不下 ✓ ✗ 這類符號,
# 輸出被重導向到檔案時會直接 UnicodeEncodeError 中斷。先把輸出轉成 UTF-8。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):                # Python 3.6 以下沒有 reconfigure
    pass

# 這一課只認這一個版面檔。它是社群模組加進去的,EA 原版沒有,
# 所以「找不到」是常見且正常的結果,main() 裡有一整段在解釋這件事。
TARGET_FEL = b'fes_ingameinfobar.fel'
MAX_UNCOMPRESSED = 256 * 1024 * 1024      # 防壞檔宣稱超大尺寸而吃光記憶體


# ─────────────────────────────────────────────────────────
#  QFS / RefPack 解壓
# ─────────────────────────────────────────────────────────
def qfs_decompress(data: bytes) -> bytes:
    """把一塊 QFS / RefPack 資料解成原本的內容。沒壓縮的原樣退回。

    檔頭:
        byte[0]  旗標,& 0x01 決定檔頭多長
        byte[1]  0xFB,這是辨識碼
        旗標 & 0x01 == 0  →  檔頭 5 bytes,byte[2..4] 是解壓後大小(big-endian)
        旗標 & 0x01 == 1  →  檔頭 10 bytes,byte[6..9] 是解壓後大小(big-endian)
    遊戲裡絕大多數是前者,所以最常看到的開頭就是 10 FB 再接三個位元組。

    檔頭之後是一連串指令,用第一個位元組的值域分辨:
        < 0x80        2 bytes  短距離複製  複製 3-10    回看 1-0x400
        0x80 - 0xBF   3 bytes  中距離複製  複製 4-67    回看 1-0x4000
        0xC0 - 0xDF   4 bytes  長距離複製  複製 5-1028  回看 1-0x20000
        0xE0 - 0xFB   1 byte   純資料      帶出 4-112(每 4 遞增)
        >= 0xFC       1 byte   結束        帶出 0-3 個尾巴位元組
    三種複製指令都可以順便帶 0 到 3 個「直接寫出去」的位元組,
    就是下面那個 n。

    ⚠️ 為什麼不是壓縮的也要接受:同一個封裝檔裡壓縮與未壓縮會混在一起。
       本站量過剛安裝好的原版 207 個封裝檔,有 106 個是混的;
       ingame.big 的 44 項裡有 1 項(alib_ingamelogos.fel)是純文字。
       所以不能假設「這個 .big 裡全都壓縮」,要逐項看第 2 個位元組。
    """
    if len(data) < 2 or data[1] != 0xFB:
        return data                                    # 未壓縮,原樣返回

    if data[0] & 0x01:                                 # 4-byte 尺寸欄位
        if len(data) < 10:
            raise ValueError('QFS 檔頭不完整')
        size = int.from_bytes(data[6:10], 'big')
        pos = 10
    else:                                              # 3-byte 尺寸欄位
        if len(data) < 5:
            raise ValueError('QFS 檔頭不完整')
        size = int.from_bytes(data[2:5], 'big')
        pos = 5

    # 第一道:檔頭自己宣稱的大小不可以離譜。壞掉的檔常常在這裡就露餡。
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise ValueError(f'QFS 宣稱解壓尺寸異常:{size}')

    out = bytearray()
    end = len(data)

    def guard():
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的 —— 那是「檔案自己說的」。
        #    惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也要有上限,而上限就是它自己宣稱的大小。
        if len(out) > size:
            raise ValueError(f'QFS 解出來的資料超過檔頭宣稱的 {size} 位元組 —— '
                     f'這個檔可能已損毀或被動過手腳')

    def copy_back(offset, length):
        """往已經解出來的資料倒退 offset 個位元組,從那裡抄 length 個過來。

        ⚠️ 一定要一個位元組一個位元組抄,不可以用切片一次抄完。
           offset 小於 length 是合法的,而且很常見:那代表「邊寫邊抄自己
           剛寫出去的東西」,格式就是用這招來表達重複的字串。
           用切片會抄到「還沒被寫出來」的那一段,結果完全不同。

        offset 必須落在 1 到目前已解長度之間。倒退超過開頭 = 這個檔壞了。
        """
        if not 0 < offset <= len(out):
            raise ValueError(f'QFS 反向參照越界 offset={offset}')
        src = len(out) - offset
        for _ in range(length):
            out.append(out[src])
            src += 1
        guard()

    # 解壓只能從頭循序做,不能跳著解:每個複製指令都要看
    # 「到目前為止已經解出來的東西」。
    while pos < end:
        b0 = data[pos]

        if b0 >= 0xFC:                                 # 結束標記 + 0~3 個 literal
            n = b0 & 0x03
            pos += 1
            out += data[pos:pos + n]
            guard()
            break

        if b0 >= 0xE0:                                 # 純 literal
            n = ((b0 & 0x1F) << 2) + 4
            pos += 1
            out += data[pos:pos + n]
            guard()
            pos += n
            continue

        if b0 >= 0xC0:                                 # 4-byte 指令:長距離參照
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]
            pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 >= 0x80:                               # 3-byte 指令:中距離參照
            b1, b2 = data[pos + 1], data[pos + 2]
            pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        else:                                          # 2-byte 指令:短距離參照
            b1 = data[pos + 1]
            pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1

        # 三種複製指令共用的收尾:先把順便帶的 n 個位元組寫出去,
        # 再做反向複製。順序不能顛倒,因為複製要看的是「含這 n 個」之後的結果。
        out += data[pos:pos + n]

        guard()
        pos += n
        copy_back(offset, length)

    # guard() 只守上界(不准超過檔頭宣稱的大小),下界要在這裡守。
    # 2026-09-05 抓到的漏洞:壓縮流被截斷時,切片 data[pos:pos+n] 只會拿到
    # 比較短的資料,迴圈就自然結束 —— 沒有人喊停,函式安靜回傳一份
    # 「比檔頭宣稱短」的版面文字。--apply 會拿那份殘缺文字改一改壓回去寫進
    # 遊戲檔,而寫後複驗的兩個判斷式(項目數不變、殘留未關 = 0)兩項都會過,
    # 螢幕照樣印「完成」。實測把目錄裡的長度從 11,617 改成 10,817,
    # 寫出去的版面檔只剩 79,476 bytes / 887 行,結尾連 END: 都沒有。
    # 所以解完一定要比長度:少一個位元組都當成這一項被截斷了。
    #
    # 這一道對健康的檔案是 no-op:本站把 MVP2026/data/frontend 的 98 個封裝檔
    # 共 9,643 個 QFS 項目,加上兩份剛安裝好的原版與一份社群名冊模組的
    # 8,711 項,各解一次量長度 —— 每一項都剛好等於檔頭宣稱的數字。
    if len(out) != size:
        raise ValueError(f'QFS 只解出 {len(out)} 個位元組,檔頭說應該有 {size} 個 —— '
                         f'這個項目被截斷了')
    # 走到這裡 len(out) 一定等於 size,所以這個切片切不到東西,留著當最後保險。
    return bytes(out[:size])


# ─────────────────────────────────────────────────────────
#  QFS / RefPack 壓縮(純 literal 編碼)
#
#  RefPack 允許整份資料都用 literal 指令表達。不做字串匹配搜尋,
#  所以是瞬間完成,而且不必依賴壓縮器的正確性,格式一樣合法。
#  代價是檔案較大(本例 84 KB 對上原檔的 11.6 KB —— 那份原檔是社群做的,不是 EA 出貨的),
#  對 2.5 MB 的 ingame.big 而言只多 3%。
# ─────────────────────────────────────────────────────────
def qfs_compress_literal(data: bytes) -> bytes:
    """把資料包成合法的 QFS,全部用純資料指令,不做任何字串比對。

    輸出的檔頭固定是 10 FB 再接三個位元組的解壓後大小(big-endian),
    也就是上面解壓那邊的「5 bytes 檔頭」那一種。

    為什麼敢這樣做:純資料指令(0xE0 系列)可以表達任意內容,
    整份資料都用它輸出,格式一樣合法,遊戲照樣讀得懂。
    好處是瞬間完成,而且不必依賴壓縮器寫得對不對:
    解壓端只會走純資料那一條路,沒有機會踩到複製指令的邊界錯誤。

    代價只有檔案變大。本站測試機實測:84,183 bytes 的版面文字
    包成 84,941 bytes,而整個 ingame.big 從 2,665,562 變成 2,750,503,
    多了 3.2%。
    """
    n = len(data)
    # 檔頭的尺寸欄位只有三個位元組。超過就會被無聲截掉高位,
    # 包出來的東西解回來會少一大截 —— 那是會寫壞遊戲檔的路,寧可停下來。
    # (實際的版面檔是幾十 KB 等級,正常情況碰不到這條;它擋的是
    #  「餵進來的封裝檔本身有問題,解出一份超大文字」那種情形。)
    if n > 0xFFFFFF:
        raise ValueError('要壓回去的內容有 %d bytes,超過 QFS 檔頭三個位元組'
                         '能表達的 16,777,215 bytes' % n)
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 純資料指令一次只能帶 4 的倍數,所以尾巴不足 4 個的那幾個位元組
    # 交給結束指令帶走(結束指令剛好可以帶 0 到 3 個)。
    tail = n % 4                                       # 0~3,交給結束指令帶走
    body = n - tail
    pos = 0
    while pos < body:
        chunk = min(112, body - pos)                   # 必為 4 的倍數,上限 112
        out.append(0xE0 | ((chunk - 4) // 4))          # 0xE0~0xFB,不會撞到 0xFC
        out += data[pos:pos + chunk]
        pos += chunk
    out.append(0xFC | tail)                            # 結束標記
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIG 檔目錄
# ─────────────────────────────────────────────────────────
class BigFormatError(Exception):
    """.big 檔頭或目錄不合格式。

    只在「這個檔不是我們認得的封裝檔」時丟。
    main() 會把它收成一句中文加一句「請確認選到的是 ingame.big」,
    不讓使用者看到 Python traceback。
    """


def list_entries(data: bytes):
    """走一次目錄,回傳 [(名稱, TOC 欄位位置, 資料 offset, 資料長度), ...]。

    BIGF 的檔頭固定 16 bytes:
        +0x00  4 bytes  BIGF 這四個字
        +0x04  4 bytes  檔案總大小      多數是 little-endian
        +0x08  4 bytes  目錄有幾項      big-endian
        +0x0C  4 bytes  目錄區結束位置  big-endian
    目錄從 +0x10 開始,一項是「8 bytes 的位移與長度,兩個都是 big-endian」
    再接一個以 0 結尾的檔名。檔名長度不固定,所以只能從第一項開始
    一項一項往前走,沒辦法直接跳到第 N 項。

    ⚠️ 回傳值裡的「TOC 欄位位置」是本支腳本的關鍵:
       它記下那 8 bytes 本身在檔案裡的位置。之後要把這一項指到別的地方,
       只要覆寫那 8 個位元組,不必重寫整個目錄,更不必重新打包整個檔。
    """
    if len(data) < 16 or data[:4] != b'BIGF':
        raise BigFormatError('檔頭前四碼不是 BIGF,這不是 EA BIG 封裝檔')
    # 項目數在 +0x08,big-endian。上限只是常識性的防呆:
    # 壞掉的檔會宣稱幾十億項,那會讓下面的迴圈跑到天荒地老。
    count = int.from_bytes(data[8:12], 'big')
    if not 0 < count < 100000:
        raise BigFormatError(f'目錄項目數異常({count}),檔案可能已損毀')

    items = []
    pos = 16
    for i in range(count):
        # 先把「這一項的 8 bytes 在哪裡」記下來,之後要改的就是這 8 個位元組。
        field = pos
        if pos + 8 > len(data):
            raise BigFormatError(f'目錄在第 {i + 1} 項處被截斷,檔案不完整')
        # 位移與長度都是 big-endian。這一點跟檔頭的「總大小」不一樣,
        # 同一個檔頭裡混著兩種位元組序,是這個格式最容易寫錯的地方。
        offset, size = struct.unpack('>II', data[pos:pos + 8])
        pos += 8
        end = data.find(b'\x00', pos)                  # find 不會丟例外
        if end < 0:
            raise BigFormatError(f'第 {i + 1} 項的名稱沒有結束符,檔案已損毀')
        # 每一項都要落在檔案裡面。這道擋的是「目錄看起來正常但指到檔案外面」,
        # 那種檔如果放行,後面切片會安靜地拿到空資料而不是報錯。
        if offset + size > len(data):
            raise BigFormatError(f'第 {i + 1} 項的資料範圍超出檔案結尾')
        items.append((data[pos:end].decode('latin-1', 'replace'), field, offset, size))
        pos = end + 1
    return items


def find_entry(items, name: bytes):
    """回傳 (TOC 欄位位置, 資料 offset, 資料長度)。找不到回傳 None。

    找不到不是例外而是 None:對這一課來說「原版沒有這個檔」是正常結果,
    main() 要為它印一整段說明,不是印一句錯誤。
    """
    # 目錄裡的檔名是用 latin-1 解出來的,這裡也用同一套解,兩邊才比得起來。
    want = name.decode('latin-1')
    for entry_name, field, offset, size in items:
        if entry_name == want:
            return field, offset, size
    return None


# ─────────────────────────────────────────────────────────
#  找出目標:GR:BASES 底下的 TX:RATING
# ─────────────────────────────────────────────────────────
def patch_script(text: str):
    """回傳 (改過的內容, [(行號, 壘包群組名, x, y), ...])。

    版面腳本用縮排表示層級,所以群組範圍以縮排判定:
    進入 GR:BASES 之後,任何縮排回到同層或更外層的行就代表群組結束。
    不用「下一個群組叫什麼名字」當邊界,別人的檔案結構不同也不會誤判。

    版面腳本的每一行長這樣,用逗號隔開:
        指令:名稱,顯示開關,保留,X,Y,寬,高,...
    所以 p[1] 是顯示開關(1 顯示 / 0 隱藏),p[3] 與 p[4] 是座標。
    座標是 640x480 畫面的絕對值,不是相對於上層群組。

    ⚠️ 只把 1 改成 0,不刪任何一行,也不動其他欄位。
       1 跟 0 都是一個字元,所以解壓後的版面文字長度一個位元組都沒變,
       改的就只有那幾個字元。所以複驗的「解壓行數」一定要跟改前一模一樣 ——
       2026-09-05 起這一項有寫進判斷式了(以前只印不驗),不一樣就算複驗沒過。

    ⚠️ 換行必須維持原樣。這裡用 '\n' 切、用 '\n' 接,
       CRLF 的 CR 會留在每一行的尾巴跟著回去。
       版面檔全是 CRLF,被編輯器統一成 LF 就會少掉一行數的位元組,檔案就壞了。

    已經是 0 的行不會被挑中,所以重跑第二次會回報「沒有需要改的地方」,
    不會愈改愈多。
    """
    lines = text.split('\n')
    base = '?'                                         # 目前在哪個壘包底下,只拿來給人看
    hits = []
    bases_indent = None                                # None 表示尚未進入 GR:BASES
    # 逐行掃。要記住的狀態只有兩個:GR:BASES 的縮排深度,以及最近讀到的壘包名。
    for i, line in enumerate(lines):
        body = line.lstrip()
        if not body:                                   # 空行不影響層級判斷
            continue
        indent = len(line) - len(body)

        if bases_indent is None:                       # 還在群組外,只找入口
            if re.match(r'GR:BASES\b', body):
                bases_indent = indent
                base = '?'
            continue

        if indent <= bases_indent:                     # 縮排回頭 = 群組結束
            bases_indent = indent if re.match(r'GR:BASES\b', body) else None
            if bases_indent is not None:
                base = '?'
            continue

        # 記住現在走到哪個壘包底下。這只影響印給人看的那一欄,
        # 不影響要不要改:只要在 GR:BASES 範圍內的 TX:RATING 都算數。
        # (所以如果有哪一個不是直接掛在壘包群組底下,它會沿用上一次讀到的壘包名;
        #  本站測試機那一份沒有這種情形,6 個全部在壘包群組裡。)
        m = re.match(r'GR:(HOMEPLATE|THIRDBASE|SECONDBASE|FIRSTBASE)\b', body)
        if m:
            base = m.group(1)
        elif re.match(r'TX:RATING\b', body):
            p = line.split(',')
            # 兩個條件缺一不可:欄位要夠(不夠代表這行不是我們認得的格式,
            # 硬改會寫壞),而且現在是開著的(已經關掉的不用再動)。
            if len(p) >= 5 and p[1] == '1':            # 欄位不足的畸形行直接跳過
                p[1] = '0'
                lines[i] = ','.join(p)
                # 行號 +1 是因為要印給人看,人從第 1 行數起。
                hits.append((i + 1, base, p[3], p[4]))
    return '\n'.join(lines), hits


# 只用在畫面輸出。查不到就原樣印英文,不讓翻譯表缺一筆就變成當機。
BASE_ZH = {'HOMEPLATE': '本壘', 'THIRDBASE': '三壘',
           'SECONDBASE': '二壘', 'FIRSTBASE': '一壘', '?': '未知'}


def _verify_failed(big, backup, made_backup, why):
    """寫進去了但複驗沒過 —— 一定要回傳非 0,而且能安全自動還原的就直接還原。

    ⚠️ 為什麼只有 made_backup 為真才自動還原:那一份 .bak 是這一次執行、
       在動任何東西之前才做的,保證等於「套用前那一秒」的樣子,蓋回去只會
       回到使用者按下 --apply 之前。而「本來就存在的 .bak」是上一次執行
       (甚至上一課)留下的舊快照,自動拿它蓋掉會把使用者更早的狀態一起弄丟。
       那種情形只把指令印出來,由使用者自己決定 —— 這件事不該由程式代決。
    """
    print(f'\n✗ {why}')
    if not made_backup:
        print('  這個 .bak 是之前就存在的那一份(不是這次做的),不敢自動拿它蓋掉。')
        print('  確認過那份備份就是你要的之後,自己下這一行還原:')
        print(f'  python3 {Path(sys.argv[0]).name} "{big}" --restore')
        return 1
    print('  這一份備份是剛剛套用之前才做的,直接幫你還原回去⋯')
    try:
        _do_copy(backup, big)
    except BaseException as e:
        print(f'  ✗ 自動還原沒有成功:{e}')
        print('  遊戲檔可能還停在改過的狀態,請自己再跑一次:')
        print(f'  python3 {Path(sys.argv[0]).name} "{big}" --restore')
        return 1
    if not _same_bytes(backup, big):
        print('  ✗ 還原之後跟備份對不起來,請自己再跑一次:')
        print(f'  python3 {Path(sys.argv[0]).name} "{big}" --restore')
        return 1
    # 已經回到原樣,Ctrl-C 的訊息也要跟著改口(三態一起收回 idle)
    _STATE.update(replaced=False, phase='idle', target=None, kind=None)
    print(f'  ✓ 已還原成套用前的樣子:{big.name}(遊戲檔等同沒有被改過)')
    print('  請把上面那一段訊息回報給本站。')
    return 1


def main():
    """從頭走一遍:找檔 → 讀目錄 → 取出版面檔 → 解壓 → 掃 → 印,
    加了 --apply 才往下備份、壓回去、寫入、複驗。回傳值就是離開碼。
    --list 在讀完目錄之後就停,--restore 走另一條路,兩個都不會解壓。

    自己解析參數而不用 argparse:這支只有三個旗標,而第一個參數
    是一個會被拖進終端機的路徑,拖出來的東西不會以 -- 開頭,
    用「不以 -- 開頭的就是路徑」這條規則反而不會誤判。
    """
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    # --selftest 排在最前面,因為它不需要任何路徑,也不碰遊戲檔。
    if '--selftest' in flags:
        return selftest()
    # 什麼都沒給就把檔頭那段說明印出來當說明書。
    if not args:
        print(__doc__)
        return 1

    big = Path(args[0]).expanduser()
    # ⚠️ 2026-09-06 第三輪訂正:會寫的那兩條路(--apply / --restore),
    #    目標是符號連結就停下來,不跟著它寫。
    #    第一輪的做法是「先解到真正的那個檔再動手」—— 那比「把連結本身換成
    #    實體檔」好(至少動到的是同一個檔),但仍然是替使用者決定去改資料夾
    #    外面的東西。要改哪一個檔應該由他自己講明白。
    #    唯讀那條路不受限:只是讀,跟著連結走沒有風險。
    if big.is_symlink():
        if '--apply' in flags or '--restore' in flags:
            print(f'✗ 這個名字是一個符號連結:{big}')
            print('  本程式不跟著它寫 —— 它指到的那個檔可能根本不在這個資料夾裡。')
            print('  請把真正的那個檔的路徑直接餵給它,或換成實體檔再跑一次。')
            print('  (目前沒有動到任何檔案。)')
            return 1
        _real = Path(os.path.realpath(big))
        print(f'· 這是符號連結,跟著它走到:{_real}')
        big = _real
    # 備份是「原檔名再接 .bak」,不是把 .big 換成 .bak。
    # 換掉副檔名的話,同一個資料夾裡不同的 .big 會共用同一個備份名。
    backup = big.with_suffix(big.suffix + '.bak')

    if not big.is_file():
        print(f'✗ 找不到檔案:{big}')
        return 1

    # ── 還原 ──────────────────────────────────────────
    if '--restore' in flags:
        # ⚠️ 2026-09-05 補:先看連結、再看存不存在。順序不能反 ——
        #    is_file() 會跟著連結走,dangling 連結會被說成「找不到備份」,
        #    使用者會以為那個名字是空的,其實它被佔著。
        if os.path.islink(backup):
            print(f'✗ 備份是一個符號連結:{backup.name}')
            print('  本程式不跟著它讀 —— 它可能指到資料夾外面完全無關的檔。')
            print('  請換成實體檔再跑一次。(目前沒有動到任何檔案。)')
            return 1
        if not backup.is_file():
            print(f'✗ 找不到備份:{backup}')
            return 1
        # ⚠️ 還原前一定要確認這兩個檔真的是封裝檔。
        #    本站好幾課都會留下 .bak,如果使用者拖錯檔案,
        #    這裡會拿別課的舊快照蓋掉現在這個檔,而且完全看不出來。
        #    2026-08-25 上線前稽核抓到的,補上這道把關。
        if backup.read_bytes()[:4] != b'BIGF':
            print(f'✗ 這個備份不是本工具建立的:{backup.name}')
            print('  它的開頭不是 BIGF,不敢拿它覆蓋任何東西。')
            return 1
        if big.read_bytes()[:4] != b'BIGF':
            print(f'✗ 要還原的目標不是封裝檔:{big.name}')
            print('  路徑可能指錯了。')
            return 1
        if b'fes_ingameinfobar.fel' not in backup.read_bytes()[:65536]:
            print(f'✗ 這個備份裡沒有這一課要的項目:{backup.name}')
            print('  它可能是別的教學留下來的備份。')
            return 1
        _restore_from_backup(backup, big)
        # 蓋回去之後再比一次。copy2 中途出錯會丟例外,但「磁碟寫到一半滿了」
        # 這種情形值得再確認一次:比長度,再比內容,不用 zip()。
        if not _same_bytes(backup, big):
            print(f'✗ 還原之後 {big.name} 的內容跟備份對不起來,它現在可能是半截的。')
            print(f'  備份 {backup.name} 本身沒有被動過,請再跑一次 --restore。')
            return 1
        print(f'✓ 已從備份還原:{backup.name} → {big.name}')
        return 0

    # 整包讀進記憶體。ingame.big 這台機器上是 2.5 MB 左右,
    # 一次讀完最單純,後面 append 也只是往這個 bytearray 後面接。
    data = bytearray(big.read_bytes())
    print(f'檔案    {big}')
    print(f'大小    {len(data):,} bytes')

    try:
        entries = list_entries(bytes(data))
    except BigFormatError as e:
        print(f'\n✗ {e}')
        print('  請確認選到的是遊戲 data/frontend 資料夾裡的 ingame.big')
        return 1
    print(f'內含    {len(entries)} 個項目\n')

    # --list 只把目錄印出來就停。放在這裡是因為它不需要解壓,
    # 而使用者會來按它,多半正是因為前一次跑出來說「沒有那個項目」。
    if '--list' in flags:
        print('目錄裡的項目:\n')
        for entry_name, _field, _off, _size in entries:
            print(f'  {entry_name:<40} {_size:>10,} bytes')
        print(f'\n共 {len(entries)} 項。這一課要的是 {TARGET_FEL.decode()}。')
        print('這是唯讀的,沒有改到任何檔案。')
        return 0

    found = find_entry(entries, TARGET_FEL)
    if not found:
        print(f'✗ 這個 .big 裡沒有 {TARGET_FEL.decode()}')
        # ⚠️ 2026-08-25:拿到剛安裝好的原版之後才發現,EA 出貨的 ingame.big
        #    只有 44 個項目,而且不含 fes_ingameinfobar.fel —— 那個檔是
        #    台灣模組之類的社群模組加進去的。原本這裡叫使用者「確認有沒有選錯檔」,
        #    但他其實選對了,訊息會把人帶去錯的方向。
        if len(entries) == 44:
            print()
            print('  你這一份是 EA 原版:44 個項目,而原版就沒有這個版面檔。')
            print('  這一課要改的東西,是社群模組(例如台灣名冊模組)加進去的。')
            print('  裝過那類模組之後這個檔才會出現(但不是每個模組都會加它)。')
        else:
            print(f'  你這一份有 {len(entries)} 個項目。')
            print('  參考:EA 原版是 44 個,而且不含這個檔。')
            # ⚠️ 不要再給「46 到 48」這種範圍。那是從一台機器的一個數字推出來的,
            #    而手邊樣本就有反例:兩個 46 項的模組包都沒有這個檔
            #    (其中一個還是中職 2008 的轉播畫面模組),45 項的也沒有。
            #    對這些人來說,「你有 46 個;通常是 46 到 48」等於在暗示
            #    「你應該要有這個檔」——方向剛好是錯的。
            print('  但項目數推不出有沒有這個檔 —— 實測有 46 個項目卻不含它的模組包。')
            print('  用 --list 把檔名列出來看才準:')
            print(f'  python3 {Path(sys.argv[0]).name} "{big}" --list')
            print('  也請順便確認選到的是 frontend 資料夾裡的 ingame.big,而不是其他 .big。')
        return 1
    field, offset, size = found
    print(f'目標    {TARGET_FEL.decode()}')
    print(f'        位置 0x{offset:X}  長度 {size:,} bytes')

    # 取出那一項的原始位元組,解壓,再用 latin-1 當成文字看待。
    # latin-1 把 0 到 255 一對一映成字元,所以解不出來也不會拋例外,
    # 而且待會 encode 回去時可以逐位元組還原,不會被編碼偷改內容。
    try:
        script = qfs_decompress(bytes(data[offset:offset + size])).decode('latin-1')
    # ⚠️ 2026-09-05 訂正:這裡原本只接 ValueError,但壓縮流被截在複製指令
    #    中間時丟的是 IndexError(data[pos + 3] 讀不到),接不到就變成一整段
    #    Python traceback 噴到使用者臉上。實測把目標項目最後一個位元組改成
    #    0xC0 就會發生。三種都接:ValueError 是我們自己丟的、
    #    IndexError 是切片與索引越界、struct.error 是欄位讀不完整。
    except (ValueError, IndexError, struct.error) as e:
        print(f'\n✗ 解壓失敗:{e}')
        print('  這個 .fel 可能已被其他工具改成本腳本不認得的形式,')
        print('  也可能是這個封裝檔本身已經被寫壞了。')
        print('  沒有動到任何檔案。')
        return 1
    print(f'        解壓後 {len(script):,} bytes / {len(script.splitlines())} 行\n')

    # 掃描與修改是同一個函式做的,所以「預覽看到的」與「--apply 會做的」
    # 是同一件事,不是兩段各自實作的程式碼。
    new_script, hits = patch_script(script)
    # 一個都沒找到有兩種可能:已經關過了,或這個檔本來就沒開著。
    # 兩種都不是錯誤,離開碼 0。
    if not hits:
        print('已經是關掉的狀態,沒有需要改的地方。')
        return 0

    print(f'找到 {len(hits)} 個跑壘者速度數值:\n')
    print(f"  {'行號':>6}  {'壘包':<6} {'座標':<12} 動作")
    print(f"  {'-' * 44}")
    for line_no, base, x, y in hits:
        print(f'  {line_no:>6}  {BASE_ZH.get(base, base):<6} x={x:<4} y={y:<5} 顯示 1 → 0')

    if '--apply' not in flags:
        print(f'\n這是預覽,沒有改到任何檔案。')
        print(f'確定要套用請加上 --apply：')
        print(f'\n  python3 {Path(sys.argv[0]).name} "{big}" --apply\n')
        return 0

    # ── 實際套用 ──────────────────────────────────────
    # 動硬碟之前先看備份那個名字。目標本身在上面已經解到實體檔了,
    # 但 <檔名>.bak 如果是符號連結,備份的內容會被寫到它指向的地方去 ——
    # 那可能是資料夾外面完全無關的檔。停下來問人,不自己決定。
    # (寫入與備份用的中繼檔名改用 tempfile.mkstemp 當場生成,
    #  沒有固定名字可以被佔住,所以第一輪那兩道「這個名字已經有東西」不需要了。)
    if os.path.islink(backup):
        print(f'\n✗ 備份的名字是一個符號連結:{backup.name}')
        print('  本程式不跟著它寫 —— 它可能指到資料夾外面完全無關的檔。')
        print('  請先把它移走或換成實體檔,再跑一次。(目前沒有動到任何檔案。)')
        return 1

    # ⚠️ 用 lexists 不用 exists:dangling 連結對 exists 回 False,
    #    那會讓我們以為那個名字是空的而去建備份。(上面已經擋掉連結,
    #    這裡是第二道 —— 規則寫在程式裡才不會下次又忘記。)
    if not os.path.lexists(backup):
        _atomic_copy(big, backup)
        print(f'\n✓ 已備份原始檔:{backup.name}')
        _made_backup = True            # 這一份保證是「套用前那一秒」的樣子
    else:
        print(f'\n· 備份已存在,保留不覆蓋:{backup.name}')
        _made_backup = False           # 上一次(甚至上一課)留下的,不敢自動拿它蓋

    # ── 這四行就是 append 模式的全部 ──
    # 舊資料原封不動留在原地(只是沒有人再指向它),新資料接在檔尾,
    # 然後只覆寫兩個地方:目錄那一項的 8 bytes,加上檔頭大小欄的 4 bytes。
    # 合計最多 12 個位元組被覆蓋,原始資料區一個位元組都沒動。
    # 為什麼不能「全部讀出再重新打包」,見檔頭那段警告。
    try:
        payload = qfs_compress_literal(new_script.encode('latin-1'))
    except ValueError as e:
        print(f'\n✗ 壓不回去:{e}')
        print('  遊戲檔沒有被改到(備份已經建立,確認過就可以自己刪掉)。')
        return 1
    new_offset = len(data)
    data += payload                                            # 接到檔尾
    # 目錄裡的位移與長度是 big-endian('>II')。
    data[field:field + 8] = struct.pack('>II', new_offset, len(payload))  # 更新目錄
    # 檔頭的總大小是 little-endian('<I'),跟上面那一行不同:
    # 同一個檔頭裡混著兩種位元組序。本站量過 295 個封裝檔,
    # 288 個的這一欄是 little-endian,ingame.big 是其中之一。
    data[4:8] = struct.pack('<I', len(data))                   # 更新檔頭總長
    # 先寫暫存檔再換掉,不要直接截斷原檔重寫。
    # 中途被中斷的話,原檔會停在半殘狀態;雖然 .bak 還在,
    # 但使用者不會知道發生了什麼。2026-08-25 上線前稽核統一。
    # 開檔前再看一次(上面那道是在讀檔之前做的;這中間如果有人把它換成連結,
    # 就會在這裡被擋下來)。
    _refuse_symlink(str(big), '要被寫入的遊戲檔')
    _fd, _tmp = tempfile.mkstemp(dir=str(big.parent) or '.',
                                 prefix='.' + big.name + '.tmp-')
    _swapped = False
    try:
        with open(_fd, 'wb') as _f:
            _f.write(bytes(data))
            _f.flush()
            os.fsync(_f.fileno())
        # ⚠️ 2026-09-05 補:暫存檔的權限是照當下 umask 現生的,原檔的模式不會
        #    自己跟過來。實測 0700 的遊戲檔換完變成 0644 —— 少了擁有者的執行位元,
        #    多了同群組與其他人的讀取權,而且螢幕上一個字都不提。
        #    只帶模式、不帶時間:改過的檔就應該有新的修改時間。
        #    (Windows 上 copymode 幾乎沒有作用,那邊本來就沒有這個問題。)
        try:
            shutil.copymode(big, _tmp)
        except OSError:
            pass                               # 帶不過去就算了,不值得為它中斷
        # ⚠️ 2026-09-06:換名與登記中間不可以有縫。原本是 os.replace 一行、
        #    離開 try 之後才 _STATE['replaced'] = True,Ctrl-C 落在那兩行中間
        #    的話收尾會說「一個位元組都沒有被動到」—— 而檔案已經換掉了。
        _STATE['target'], _STATE['phase'] = str(big), 'replacing'
        with _NoInterrupt():
            os.replace(_tmp, big)
            _swapped = True
            _STATE.update(replaced=True, phase='replaced', kind='apply')
    except BaseException as _e:
        # Ctrl-C 也走這裡(BaseException 才收得到 KeyboardInterrupt)。
        if not _swapped:
            # 換檔還沒發生,所以只要把中繼檔刪掉,遊戲檔就完全沒被動到。
            try:
                os.remove(_tmp)
            except OSError:
                pass
            if isinstance(_e, OSError):
                # 寫入或換名自己失敗:確定沒換成,狀態收回「還沒動」
                _STATE['phase'], _STATE['target'] = 'idle', None
        raise

    # ── 寫入後複驗 ────────────────────────────────────
    # 複驗是從硬碟重新讀一次,整條鏈再走一遍(讀目錄 → 找項目 → 解壓),
    # 不是拿記憶體裡那份自己跟自己比。這樣才驗得到「有沒有真的寫進去」。
    # ⚠️ 這一段跑的時候,檔案已經被 os.replace 換掉了。所以這裡丟例外
    #    不能變成 traceback —— 使用者需要看到的是「請用 --restore 還原」。
    check = big.read_bytes()
    try:
        ok_entries = list_entries(check)
        f2, o2, s2 = find_entry(ok_entries, TARGET_FEL)
        text2 = qfs_decompress(check[o2:o2 + s2]).decode('latin-1')
    except (BigFormatError, ValueError, IndexError, struct.error, TypeError) as e:
        return _verify_failed(big, backup, _made_backup, f'寫完之後讀不回來:{e}')
    # ⚠️ 2026-09-05 第二輪訂正:判斷式原本只有兩項(殘留未關、項目數),
    #    「解壓行數」印在旁邊卻沒有進判斷 —— 資安稽核抓到的形態是
    #    「聲稱是複驗的欄位沒有參與判定」。實測把行數從 951 弄成 953,
    #    腳本照樣印「完成」並回傳 0。現在四項全部要成立,而第四項
    #    (讀回來的文字 == 要寫進去的那一份)其實把前三項都包住了,
    #    前三項留著是為了「哪裡不對」講得出人話。
    # ⚠️ 2026-09-05 訂正:這裡原本是 re.findall(r'TX:RATING,1', text2) ——
    #    對「整份文字」數,但 patch_script 只改 GR:BASES 底下那些。
    #    手上這份剛好每一個 TX:RATING 都在壘包群組裡,所以一直都是 0,
    #    看不出兩邊口徑不同;別人的檔案只要有一個 TX:RATING 掛在 GR:BASES
    #    外面,--apply 就會永遠複驗不過。而且那個字面比對還會把
    #    TX:RATING,10 這種也算進去。改成「再跑一次同一個掃描函式,
    #    看它還找不找得到要改的」—— 跟改的時候用同一把尺,不會對不起來。
    left = len(patch_script(text2)[1])
    lines_before = len(script.splitlines())
    lines_after = len(text2.splitlines())

    print(f'\n✓ 已寫入 {big.name}')
    print(f'  項目數     {len(ok_entries)} 個(原本 {len(entries)} 個)')
    print(f'  檔案大小   {len(check):,} bytes')
    print(f'  殘留未關   {left} 個(應為 0)')
    print(f'  解壓行數   {lines_after} 行(改前 {lines_before} 行,應相同)')
    problems = []
    if len(ok_entries) != len(entries):
        problems.append('目錄項目數從 %d 變成 %d' % (len(entries), len(ok_entries)))
    if left != 0:
        problems.append('還有 %d 個沒有被關掉' % left)
    if lines_after != lines_before:
        problems.append('解壓行數從 %d 變成 %d' % (lines_before, lines_after))
    if text2 != new_script:
        problems.append('讀回來的版面文字跟要寫進去的那一份不一樣')
    if not problems:
        print('\n完成。開遊戲打到有人上壘就能確認。')
        print(f'要還原:python3 {Path(sys.argv[0]).name} "{big}" --restore')
        return 0
    return _verify_failed(big, backup, _made_backup,
                          '複驗未通過:' + '、'.join(problems))



# ─────────────────────────────────────────────────────────
#  自我測試(--selftest):不碰任何遊戲檔
# ─────────────────────────────────────────────────────────
# 這一段用的版面文字是本檔自己造的,不是從遊戲裡抄來的。
# 最後那三行 GR:OTHER / TX:RATING 是**陰性對照**:它在 GR:BASES 外面,
# 所以不管跑幾次都不可以被改到。少了這一段,「有沒有真的只改壘包底下那些」
# 就沒有被測到 —— 一個把全部 TX:RATING 都關掉的錯誤版本照樣會全綠。
_SELFTEST_FEL = (
    'SC:INGAMEINFOBAR,1,0,0,0,640,480\r\n'
    ' GR:BASES,1,0,0,0,640,480\r\n'
    '  GR:HOMEPLATE,1,0,100,400,50,20\r\n'
    '   TX:RATING,1,0,110,410,30,12\r\n'
    '  GR:FIRSTBASE,1,0,540,450,50,20\r\n'
    '   TX:RATING,1,0,550,461,30,12\r\n'
    ' GR:OTHER,1,0,0,0,10,10\r\n'
    '  TX:RATING,1,0,5,5,10,10\r\n'
    'END:\r\n')


def _selftest_big(fel_text):
    """組一個最小但合法的 BIGF,裡面第二項就是這一課要找的版面檔。

    刻意放三項:前後各一項不相干的,中間才是目標 —— 這樣「目錄有沒有走對」
    才測得到。位移與長度是 big-endian、檔頭總長是 little-endian,
    這兩種位元組序混在同一個檔頭裡是這個格式最容易寫錯的地方。
    """
    names = [b'aaa_other.fel', TARGET_FEL, b'zzz_other.fel']
    blobs = [qfs_compress_literal(b'SC:A,1,0,0,0,1,1\r\n'),
             qfs_compress_literal(fel_text.encode('latin-1')),
             qfs_compress_literal(b'SC:Z,1,0,0,0,1,1\r\n')]
    dir_end = 16 + sum(8 + len(n) + 1 for n in names)
    off, offsets = dir_end, []
    for b in blobs:
        offsets.append(off)
        off += len(b)
    out = bytearray(b'BIGF')
    out += struct.pack('<I', off)                  # 總長:little-endian
    out += struct.pack('>I', len(names))           # 項目數:big-endian
    out += struct.pack('>I', dir_end)              # 目錄結束位置:big-endian
    for n, o, b in zip(names, offsets, blobs):
        out += struct.pack('>II', o, len(b)) + n + b'\x00'
    assert len(out) == dir_end, '目錄長度算錯了'
    for b in blobs:
        out += b
    return bytes(out)


def _selftest_run(argv):
    """把 main() 當成使用者那樣跑一遍,把它印的東西收起來不要洗版。"""
    import contextlib
    import io as _io
    old_argv, buf = sys.argv, _io.StringIO()
    sys.argv = ['mvp_hide_runner_speed.py'] + list(argv)
    try:
        with contextlib.redirect_stdout(buf):
            rc = main()
    finally:
        sys.argv = old_argv
    return rc, buf.getvalue()


def selftest():
    """不碰任何遊戲檔的自我測試:自己造一個最小的封裝檔,把整條路跑一遍。

    重點不是「有沒有通過」,是**裡面有 11 個反向餌** —— 先證明「事情錯掉的時候
    它真的會叫」。只驗正向的測試會一路綠燈,卻在功能整個壞掉時照樣綠燈,
    那種測試比沒有更危險。

    11 個反向餌:
      1. 被截斷的 QFS 資料流不可以安靜地解出半截(要丟例外)
      2. 半截的檔不可以被 _same_bytes 判成「相同」(那是 zip() 的陷阱)
      3. 目的檔是符號連結 → _refuse_symlink 要擋下來
      4. 事先把「以前那個固定中繼檔名」<備份>.part 佔成一個指向資料夾外面的
         符號連結 → 備份照樣要成功,而且**外面那個檔一個位元組都不可以被動到**
      5. 還原途中失敗(把 os.replace 換成會丟例外的)→ 正本必須原封不動,
         而且不可以留下中繼檔
      6. .bak 是符號連結 → --apply 要停下來,不跟著它寫出去
      7. .bak 是 dangling 符號連結(os.path.exists 對它回 False)→ 一樣要停下來
      8. GR:BASES 以外的 TX:RATING 不可以被改到
      9. 寫出去的內容跟預期不符(把壓縮函式換成會掉一行的)→ --apply 必須回傳
         非 0,而且要自動還原成套用前的樣子
     10. 遊戲檔本身是符號連結 → --apply 要停,被指向的那個檔一個位元組都不可以動,
         而且不可以先去做備份
     11. 同一個連結下 --restore 也要停(備份故意放一份內容不同的,
         真的跟著連結蓋下去的話被指向的檔一定會變)

    跑完會在系統暫存區留下幾個資料夾(不刪,方便出事時自己去看)。
    """
    # python -O 會把 assert 整個拿掉 —— 上面那些餌有一半是靠 assert 站著的,
    # 在 -O 下會一路走到「全部通過」而其實什麼都沒驗。寧可不跑也不要假綠。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    ok = 0

    # ── 反向餌 1:截斷的 QFS 要丟例外 ─────────────────────────
    raw = _SELFTEST_FEL.encode('latin-1')
    packed = qfs_compress_literal(raw)
    assert qfs_decompress(packed) == raw, 'QFS 來回一趟就對不上了'
    try:
        qfs_decompress(packed[:len(packed) // 2])
    except (ValueError, IndexError, struct.error):
        ok += 1
    else:
        raise AssertionError('截斷的 QFS 竟然安靜地解出了半截')

    # ── 反向餌 2:半截的檔不可以被判成「相同」 ─────────────────
    d = tempfile.mkdtemp(prefix='mvp_hrs_st1_')
    whole, half = os.path.join(d, 'a.bin'), os.path.join(d, 'b.bin')
    open(whole, 'wb').write(b'A' * 2000)
    open(half, 'wb').write(b'A' * 1000)
    assert _same_bytes(whole, whole), '同一個檔應該相同'
    if not _same_bytes(whole, half):
        ok += 1
    else:
        raise AssertionError('半截的檔竟然被判成跟完整的相同')

    # ── 反向餌 3:目的檔是符號連結 → 要擋 ──────────────────────
    link = os.path.join(d, 'link.bin')
    os.symlink(whole, link)
    try:
        _refuse_symlink(link, '測試')
    except SystemExit:
        ok += 1
    else:
        raise AssertionError('符號連結竟然被放行')
    _refuse_symlink(os.path.join(d, 'nothing-here'), '測試')   # 正向:不存在就放行

    # ── 反向餌 4:.part 被佔成指向資料夾外面的連結 ─────────────
    outside_dir = tempfile.mkdtemp(prefix='mvp_hrs_out_')
    outside = os.path.join(outside_dir, '我的心血.bin')
    open(outside, 'wb').write('絕對不可以被動到'.encode('utf-8'))
    d2 = tempfile.mkdtemp(prefix='mvp_hrs_st2_')
    src2 = os.path.join(d2, 'x.big')
    dst2 = os.path.join(d2, 'x.big.bak')
    open(src2, 'wb').write(b'BIGF' + b'\x01' * 4096)
    os.symlink(outside, dst2 + '.part')          # 佔住第一輪那個固定名字
    _atomic_copy(src2, dst2)
    assert _same_bytes(src2, dst2), '備份沒有做成功'
    if open(outside, 'rb').read() == '絕對不可以被動到'.encode('utf-8'):
        ok += 1
    else:
        raise AssertionError('備份跟著 .part 這個連結把資料夾外面的檔吃掉了')

    # ── 反向餌 5:還原途中失敗 → 正本原封不動 ──────────────────
    d3 = tempfile.mkdtemp(prefix='mvp_hrs_st3_')
    live3, bak3 = os.path.join(d3, 'live.big'), os.path.join(d3, 'live.big.bak')
    open(live3, 'wb').write(b'BIGF' + b'N' * 100000)     # 正本(比較大)
    open(bak3, 'wb').write(b'BIGF' + b'O' * 4096)        # 備份(比較小)
    before3 = open(live3, 'rb').read()
    real_replace = os.replace

    def _boom(*a, **k):
        raise OSError(28, '自我測試假裝磁碟滿了')

    os.replace = _boom
    try:
        _do_copy(bak3, live3)
    except OSError:
        pass
    else:
        raise AssertionError('還原途中失敗竟然沒有反映出來')
    finally:
        os.replace = real_replace
    leftovers = [f for f in os.listdir(d3) if f.startswith('.live.big.restore-')]
    assert not leftovers, '還原失敗後留下了中繼檔:%r' % leftovers
    if open(live3, 'rb').read() == before3:
        ok += 1
    else:
        raise AssertionError('還原失敗,正本卻被動到了 —— 這正是 copy2 的老毛病')
    _do_copy(bak3, live3)                                # 正向:這次要成功
    assert _same_bytes(bak3, live3), '正常的還原竟然沒有做成'

    # ── 端到端:造一個最小封裝檔,--apply → --apply → --restore ──
    d4 = tempfile.mkdtemp(prefix='mvp_hrs_st4_')
    big4 = os.path.join(d4, 'ingame.big')
    original = _selftest_big(_SELFTEST_FEL)
    open(big4, 'wb').write(original)

    rc, out = _selftest_run([big4])                      # 預覽
    assert rc == 0 and '找到 2 個' in out, '預覽沒有找到 2 個:\n%s' % out
    assert open(big4, 'rb').read() == original, '預覽竟然改到檔案了'

    rc, out = _selftest_run([big4, '--apply'])
    assert rc == 0, '--apply 沒有成功:\n%s' % out
    assert os.path.isfile(big4 + '.bak'), '沒有留下備份'
    assert open(big4 + '.bak', 'rb').read() == original, '備份不等於原檔'

    ents = list_entries(open(big4, 'rb').read())
    assert len(ents) == 3, '項目數變了:%d' % len(ents)
    _f, _o, _sz = find_entry(ents, TARGET_FEL)
    got = qfs_decompress(open(big4, 'rb').read()[_o:_o + _sz]).decode('latin-1')
    # ── 反向餌 8:GR:BASES 外面那一個不可以被改到 ──────────────
    if got.count('TX:RATING,1') == 1 and got.count('TX:RATING,0') == 2:
        ok += 1
    else:
        raise AssertionError('改到的數量不對(應該只關掉 GR:BASES 底下那兩個):\n%s' % got)
    assert got.count('\r\n') == _SELFTEST_FEL.count('\r\n'), 'CRLF 被吃掉了'

    rc, out = _selftest_run([big4, '--apply'])           # 正向:重跑不會愈改愈多
    assert rc == 0 and '已經是關掉的狀態' in out, '第二次 --apply 的訊息不對:\n%s' % out

    rc, out = _selftest_run([big4, '--restore'])
    assert rc == 0, '--restore 沒有成功:\n%s' % out
    assert open(big4, 'rb').read() == original, '還原之後跟原檔不一樣'

    # ── 反向餌 6:.bak 是符號連結 → --apply 要停 ───────────────
    d5 = tempfile.mkdtemp(prefix='mvp_hrs_st5_')
    big5 = os.path.join(d5, 'ingame.big')
    open(big5, 'wb').write(original)
    os.symlink(outside, big5 + '.bak')
    rc, out = _selftest_run([big5, '--apply'])
    if rc != 0 and '符號連結' in out:
        ok += 1
    else:
        raise AssertionError('.bak 是符號連結竟然照樣寫下去了:\n%s' % out)
    assert open(big5, 'rb').read() == original, '擋下來了卻還是改到遊戲檔'
    assert open(outside, 'rb').read() == '絕對不可以被動到'.encode('utf-8'), \
        '備份把資料夾外面的檔吃掉了'

    # ── 反向餌 7:.bak 是 dangling 連結(exists 回 False)→ 一樣要停 ──
    os.remove(big5 + '.bak')
    os.symlink(os.path.join(outside_dir, '根本不存在的檔'), big5 + '.bak')
    assert not os.path.exists(big5 + '.bak'), 'dangling 連結對 exists 應該回 False'
    assert os.path.lexists(big5 + '.bak'), 'lexists 應該看得到連結本身'
    rc, out = _selftest_run([big5, '--apply'])
    if rc != 0 and '符號連結' in out:
        ok += 1
    else:
        raise AssertionError('dangling 的 .bak 竟然照樣寫下去了:\n%s' % out)
    assert open(big5, 'rb').read() == original, '擋下來了卻還是改到遊戲檔'

    # ── 反向餌 10:遊戲檔本身是符號連結 → --apply 要停,不跟著它寫 ──
    d7 = tempfile.mkdtemp(prefix='mvp_hrs_st7_')
    real7 = os.path.join(d7, 'real_ingame.big')
    open(real7, 'wb').write(original)
    link7 = os.path.join(d7, 'ingame.big')
    os.symlink(real7, link7)
    rc, out = _selftest_run([link7, '--apply'])
    if rc != 0 and '符號連結' in out:
        ok += 1
    else:
        raise AssertionError('遊戲檔是符號連結竟然照樣寫下去了:\n%s' % out)
    assert open(real7, 'rb').read() == original, '擋下來了卻還是改到被指向的那個檔'
    assert not os.path.lexists(link7 + '.bak'), '擋下來了卻還是先做了備份'

    # ── 反向餌 11:同一個連結,--restore 也要停 ────────────────
    # 備份故意放一份「內容不同但格式合法」的,這樣萬一它真的跟著連結蓋下去,
    # 被指向的那個檔一定會變 —— 拿同一份原檔當備份是驗不出來的。
    other = _selftest_big(_SELFTEST_FEL.replace('TX:RATING,1,0,110,410',
                                                'TX:RATING,0,0,110,410'))
    assert other != original, '陰性對照的備份跟原檔一樣,這個餌就白下了'
    open(link7 + '.bak', 'wb').write(other)
    rc, out = _selftest_run([link7, '--restore'])
    if rc != 0 and '符號連結' in out:
        ok += 1
    else:
        raise AssertionError('遊戲檔是符號連結時 --restore 竟然照樣蓋下去:\n%s' % out)
    assert open(real7, 'rb').read() == original, '擋下來了卻還是還原到被指向的那個檔'

    # ── 反向餌 9:寫出去的內容不對 → 必須回非 0 而且自動還原 ────
    d6 = tempfile.mkdtemp(prefix='mvp_hrs_st6_')
    big6 = os.path.join(d6, 'ingame.big')
    open(big6, 'wb').write(original)
    g = globals()
    real_pack = g['qfs_compress_literal']

    def _lossy(data):
        # 故意掉一行 —— 這正是第一輪「解壓行數只印不驗」放過去的那種壞法
        return real_pack(data.replace(b'END:\r\n', b''))

    g['qfs_compress_literal'] = _lossy
    try:
        rc, out = _selftest_run([big6, '--apply'])
    finally:
        g['qfs_compress_literal'] = real_pack
    if rc != 0 and '複驗未通過' in out and '解壓行數從' in out:
        ok += 1
    else:
        raise AssertionError('寫壞了竟然還是回報成功:rc=%s\n%s' % (rc, out))
    if open(big6, 'rb').read() == original:
        pass
    else:
        raise AssertionError('複驗沒過卻沒有自動還原成套用前的樣子')
    assert _STATE['replaced'] is False, '自動還原之後 Ctrl-C 的訊息會講錯話'

    print('自我測試:全部通過(%d 個反向餌都如預期地叫了)' % ok)
    assert ok == 11, '反向餌只跑到 %d 個' % ok
    return 0


# 離開碼:0 成功(含「本來就已經關掉」),1 任何一種沒做成的狀況,130 是 Ctrl-C。
if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # ⚠️ 2026-09-05 補:原本沒有接。Ctrl-C 會噴一整段 traceback,
        #    離開碼還是 1 —— 跟「複驗沒過」長得一模一樣,使用者分不出
        #    遊戲檔到底有沒有被改。現在照 _STATE 講實話,離開碼一律 130。
        _paths = [a for a in sys.argv[1:] if not a.startswith('--')]
        _who = _paths[0] if _paths else '<那個 .big>'
        _tgt = _STATE['target'] or _who
        print()
        if _STATE['phase'] == 'replaced':
            if _STATE['kind'] == 'restore':
                print('✗ 被中斷了 —— 但備份已經蓋回去了。')
                print(f'  {_tgt} 現在是備份那一份(還原本身已經做完)。')
            else:
                print('✗ 被中斷了 —— 但遊戲檔已經換成改過的那一份了。')
                print('  要回到原樣:')
                print(f'  python3 {Path(sys.argv[0]).name} "{_who}" --restore')
        elif _STATE['phase'] == 'replacing':
            # 只有「換名 + 登記」那一段的保險裝不上時才會走到這裡。
            # 不確定就要說不確定,不可以猜一個好聽的。
            print(f'✗ 被中斷了 —— 中斷時正在替換 {_tgt},換好了沒有無法確定。')
            print('  請拿 .bak 跟它比對,或直接還原:')
            print(f'  python3 {Path(sys.argv[0]).name} "{_who}" --restore')
        else:
            print('✗ 被中斷了。遊戲檔一個位元組都沒有被動到。')
        sys.exit(130)

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
