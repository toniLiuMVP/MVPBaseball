#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_menu_text.py
改 EA MVP Baseball 2005 選單上的文字(預設是主選單)。

    看有哪些字可以改(唯讀)
        python3 mvp_menu_text.py "你的遊戲資料夾" --list

    預覽(不會動到遊戲)
        python3 mvp_menu_text.py "你的遊戲資料夾" --set 12=馬上開打

    真的改
        python3 mvp_menu_text.py "你的遊戲資料夾" --set 12=馬上開打 --apply

    還原
        python3 mvp_menu_text.py "你的遊戲資料夾" --restore

    自我測試(不碰任何遊戲檔)
        python3 mvp_menu_text.py --selftest

原理:版面檔(.fel)裡的 TX 元素帶一個「字串編號」,真正的文字放在
data/ 底下的 .LOC 字串表(UTF-16LE)。所以改選單文字**不必動版面檔**,
只要改字串表裡那一條 —— 這比動版面檔安全得多。

⚠️ 只能改成**同長或更短**的文字。本工具是原地覆寫:
   檔案長度不變、位移表一個位元組都不動、你沒點名的字串保證逐字相同。
   在**原廠英文**的字串表上,每個槽位的可用字數剛好等於原字串長度。
   本站量了兩份:剛安裝好的原版 FEENG.LOC(415,528 位元組)與本站測試機
   那一份(416,753 位元組),兩份都是 6,352 條全部以 2 個 NUL 字元收尾、
   可用字數等於原字數,零例外。中文字少,英文換中文通常綽綽有餘。
   ⚠️ 這個「零例外」只對那兩份原廠英文表成立,不是 .LOC 這個格式的性質。
   本站那份 2009 年台灣模組的中文 FEENG.LOC(219,421 位元組)有 6,436 條,
   其中 145 條不是「剛好」:114 條空間反而更大,30 條的可用字數比原字數
   少一個字(那幾條連原本的字都寫不回去,工具會擋下來、不會寫壞檔),
   還有 1 條算出來的槽位長度是負的。所以預算一律看 --list 印的「可用字數」,
   不要自己拿原字數當預算。

⚠️ 改成中文之前,你的遊戲要先有中文字型,否則畫面上會變成空白或方框。
   看本站「把官方中文版的中文搬進英文版」那一課。

它做什麼(一句話)
    把選單上顯示的那一條字,直接在字串表裡覆寫成你要的字。

輸入
    · 遊戲資料夾(裡面要看得到 data 這個子資料夾)
    · --set 編號=新文字,可以寫很多次。編號用 --list 查
    · 版面檔預設是主選單 fes_mainmenu.fel(在 data/frontend/frontend.big 裡),
      想看別的畫面就用 --fel 與 --big 換掉

輸出
    --list      印出這個版面檔用到哪些字串、現在寫什麼、還能放幾個字
    --set       沒加 --apply 只印預覽;加了才寫,而且寫完立刻讀回來複驗
    --restore   從 .menutextbak 還原
    --selftest  自己造一個最小的字串表來測,不碰任何遊戲檔

安全網在哪
    · 預設唯讀:沒有 --apply 就只印表格
    · 太長的字在寫入之前就擋掉,不會寫到一半才發現。量「太長」用的是
      UTF-16 的編碼單位,跟真正把關的那一關同一把尺;而且加了 --apply 之後
      也還會先把每一個字串表的新內容全部算完,一個都沒出事才開始寫第一個檔
    · 第一次寫入前自動備份,而且備份是原子的(先寫同一個資料夾裡一個
      隨機名字的暫存檔,整份寫完、fsync 落地了才改名成正式的備份檔名)
    · 所有暫存檔都用 tempfile.mkstemp 產生,**不用「正本名字 + .part / .tmp」
      這種猜得到的名字**:那個名字如果已經是一條指向資料夾外面的符號連結,
      寫下去就會把外面那個檔覆蓋掉。正本或備份本身是符號連結時直接拒絕動手
    · 寫入走「先寫暫存檔,fsync 之後再 os.replace」,不會出現半截的字串表
    · 寫完立刻讀回來複驗四件事:檔案大小、字串總數、改的那幾條、
      沒點名的那幾條是不是逐字相同。**四件只要有一件對不上就停**,
      而且會當場自動從剛剛那份備份原子還原,把遊戲檔放回動手前的樣子,
      離開碼是 2 不是 0。四個數字照樣都印出來給你看
    · 一個 --set 同時點到兩個字串表時是**全有或全無**:後面那個檔出了事,
      前面已經換好的會用備份放回動手前的樣子,不會留下一半新一半舊
    · 被 Ctrl-C 中斷時會照實說。換名與「已經換過了」的登記綁成一段不會被
      切開的區間,所以收尾印的「什麼都沒有動到 / 這些檔已經改好了」跟磁碟上
      的狀態一定一致,離開碼 130。已經改好的會把還原指令印給你
    · 還原(--restore 與上面那個自動還原)也是原子的:先寫同資料夾的暫存檔、
      讀回來跟備份比 sha256,相同了才 os.replace 換上去。**不是** copy2 直接
      蓋正本 —— copy2 會先把正本截成 0 再一段一段寫,途中斷掉就沒了
    · --restore 只認 .menutextbak,而且還原之前會先驗備份:開頭要是 LOCH、
      **長度要跟現在那個檔完全相同**(本工具只做同長度覆寫,所以這一條永遠成立;
      半截的備份就是這樣被擋下來的)、內部結構要走得完

做不到的事(先說,免得你白忙)
    · 不能把字串改長,只能同長或更短(理由見下面「改字串」那一段)
    · 不會幫你裝中文字型。沒有字型的話就算改成功,畫面上也是空白或方框
    · 不會改字的位置、大小、顏色(那些在版面檔 .fel 裡,不是這一支的事)
    · 一條字串可能被很多畫面共用,改了就全部一起變。
      本站沒有逐條追過每個編號被哪些畫面用到
    · 本站沒有在遊戲裡看過改完的畫面,驗的是檔案層面

備份副檔名 .menutextbak,只認自己這一個,不會去動別課留下的 .bak。

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

import os
import re
import sys
import shutil
import signal
import struct
import hashlib
import argparse
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

# os.replace 到底做過沒有 —— Ctrl-C 的時候要說真話。
# 「什麼都沒有動到」這句話,只有在這兩個清單都是空的時候才可以印。
_WROTE = []        # --apply 換上去的遊戲檔
_RESTORED = []     # 還原(--restore 或複驗沒過時自動)換回去的遊戲檔
_REPLACING = []    # 「正在換名」的中間態:進去之前登記,登記完成之後拿掉


class _NoInterrupt(object):
    """把「os.replace + 登記」包成一段不會被 Ctrl-C 切開的區間。

    ⚠️ 這是 2026-09-06 補的,補的是一個會讓程式**說謊**的窗口:
       os.replace 已經把遊戲檔換成新的了,但 _WROTE.append 還沒跑,
       Ctrl-C 剛好落在這兩行之間 —— 收尾看到空的清單,就會印
       「什麼都沒有動到」。檔案其實已經換了。時間窗很窄,但它是真的。

    做法是這段期間先把 SIGINT 記下來不處理,離開這段之後再照常丟出
    KeyboardInterrupt。所以收尾看到的登記,跟磁碟上的狀態一定一致。

    ⚠️ signal.signal 只能在主執行緒裝。裝不上(非主執行緒、某些嵌入環境)
       就退回原本的行為 —— 不會更糟,而且還有 _REPLACING 那個中間態兜著。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError, AttributeError):
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


def _refuse_if_symlink(path, what):
    """是符號連結就拒絕動手,不要順著它走到資料夾外面去。

    ⚠️ **不可以**用 os.path.exists() / Path.exists() 判斷:那兩個會跟著連結
       去看目標,目標不存在(dangling)時回 False,整道檢查等於沒有。
       看連結本身要用 os.path.islink / os.path.lexists / os.lstat。
    """
    if os.path.islink(path):
        raise DataError(
            '%s是一條符號連結:%s\n'
            '    順著它寫下去會改到資料夾外面的檔,所以不做。\n'
            '    請把它換成真正的檔案(或先自己把它搬開)再跑一次。' % (what, path))


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ⚠️ 2026-09-05 第二次改:暫存檔的名字**不可以**是「dst + '.part'」。
       那個名字猜得到 —— 它如果已經是一條指向資料夾外面的符號連結,
       shutil.copy2 會**跟著連結**把外面那個檔截成 0 再寫進去;
       後面的 os.replace 只換掉連結本身,外面那個檔早就沒了。
       改用 tempfile.mkstemp:名字是隨機的,而且是用 O_EXCL 開的,佔不住。
    """
    # 先寫進同一個資料夾裡的暫存檔,整份寫完、fsync 落地了才改名成正式的
    # 備份檔名。中途被中斷時壞掉的是那個暫存檔,正式那個名字要嘛還沒出現、
    # 要嘛就是完整的。
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_if_symlink(dst, '備份檔')
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst) or '.',
                               prefix='.' + os.path.basename(dst) + '.part-')
    try:
        with os.fdopen(fd, 'wb') as fo:
            with open(src, 'rb') as fi:
                shutil.copyfileobj(fi, fo)
            fo.flush()
            os.fsync(fo.fileno())
        shutil.copystat(src, tmp)      # 權限與時間戳跟著來源走(等同 copy2)
        os.replace(tmp, dst)           # os.replace 是原子的
    except BaseException:
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
      3. LOCH(語系檔):檔頭指到的 LOCL 要在檔內、位移表要在檔內、
         文字區宣告的長度要在檔內,最後一條字串的位移也要在檔內。
         ⚠️ 這幾道**不足以**認出「只少掉最後那幾百個位元組」的半截備份:
         本站測試機那份 FEENG.LOC 是 416,753 bytes,最後一條字串在 415,762、
         文字區宣告到 415,528,所以截在 415,762 之後都驗得過。
         那個窗口由呼叫端 cmd_restore 的「備份與正本長度必須相同」補上
         (這一支只做同長度的原地覆寫,所以那一條在這裡永遠成立)
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

    # 第 2 道:BIGF 的檔頭第 4-8 個位元組寫著它自己應該有多大。
    # ⚠️ 這一支動的是 .LOC 不是 .big,所以這一段在本檔實際上跑不到;
    #    留著是因為這整段還原防線在本站多支腳本之間是同一份,要改就得一起改。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:語系檔。**這一支真正會走到的就是這一道。**
    # 檢查的邏輯是「順著它自己的位移走一次,看走不走得完」:
    # LOCH 檔頭指到的 LOCL 要在檔案內,文字區宣告的長度與最後一條字串的位移
    # 也都要在檔案內。截得夠多時這幾道就會亮,但截得很少時不會 ——
    # 真正把那個窗口關掉的是 cmd_restore 的長度相同檢查,見上面 docstring。
    if len(head) >= 4 and head[:4] == b'LOCH':
        try:
            d = open(bak, 'rb').read()
            L = struct.unpack('<I', d[16:20])[0]
            if L + 16 > n or d[L:L + 4] != b'LOCL':
                _stop('語系檔的字串區(LOCL)應該在位移 %d,那裡不是 LOCL。' % L)
            lcnt = struct.unpack('<I', d[L + 12:L + 16])[0]
            if lcnt <= 0 or L + 16 + lcnt * 4 > n:
                _stop('語系檔的位移表被截斷了(宣告 %d 條)。' % lcnt)
            # 文字區自己宣告有多長,那一整塊也要在檔案裡。
            # 本站這台機器上找得到的 19 個 .LOC(剛安裝好的英文版與繁中版、
            # 幾個社群模組、本站測試機那一份)全部滿足 L + lsize ≤ 檔案長度:
            # 其中 8 個剛好相等,另外 11 個檔尾多出 50 到 1,225 個位元組,
            # 所以只能比「不超過」,不可以比「相等」。
            lsize = struct.unpack('<I', d[L + 4:L + 8])[0]
            if L + lsize > n:
                _stop('語系檔的文字區宣告到位移 %d,超出檔案結尾(%d bytes)。'
                      % (L + lsize, n))
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

    # 第 5 道:通用地板。這一支是原地覆寫,改完的 .LOC 跟原本一樣大,
    # 所以「備份不到正本的一半」只有一種解釋:備份那次出事了。
    # 通用地板 —— 非 BIGF 走到這裡
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _do_copy(bak, dst):
    """真正的還原動作,而且是原子的。

    獨立成一支,是為了讓上面每一道檢查都以 return _do_copy(...) 收尾:
    檢查沒過就永遠走不到這裡,不會有「檢查完忘了 return」那種漏網。

    ⚠️ 2026-09-05 把 shutil.copy2(bak, dst) 換掉了。copy2 的動作是
       「先把 dst 截成 0 bytes,再一段一段寫進去」:途中按了 Ctrl-C、
       磁碟滿了、外接碟被拔掉、程式崩潰,玩家的遊戲檔就停在半截或 0 ——
       而這支指令的名字叫「還原」。**救火的動作本身不可以是第二把火。**
       上面那五道只驗得出「備份是不是壞的」,驗不到「複製到一半斷掉」。

    現在的順序:
      1. 正本與備份是符號連結就拒絕(不順著它改到資料夾外面的檔)
      2. 寫進**同一個資料夾**裡一個隨機名字的暫存檔(同一個檔案系統,
         os.replace 才是原子的),flush + fsync 落地
      3. 權限沿用「要被換掉的那個正本」,不是備份的
      4. **把暫存檔讀回來跟備份比 sha256**,相同才算數
      5. os.replace 換上去 —— 這一步要嘛整個成功、要嘛沒發生
    任何一步失敗就把暫存檔刪掉,正本一個位元組都沒被碰過。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_if_symlink(bak, '備份檔')
    _refuse_if_symlink(dst, '要還原的那個遊戲檔')
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst) or '.',
                               prefix='.' + os.path.basename(dst) + '.restore-')
    try:
        want = hashlib.sha256()
        with os.fdopen(fd, 'wb') as fo:
            with open(bak, 'rb') as fi:
                while True:
                    chunk = fi.read(1 << 20)
                    if not chunk:
                        break
                    want.update(chunk)
                    fo.write(chunk)
            fo.flush()
            os.fsync(fo.fileno())
        # 權限沿用「要被換掉的那個正本」;正本不在了(整個檔被刪掉才來還原)
        # 就退回用備份的權限 —— 不補這一段的話,還原出來的檔會是 mkstemp 的
        # 0600,遊戲讀不讀得到要看它跑在誰的身分底下。
        try:
            shutil.copymode(dst if os.path.isfile(dst) else bak, tmp)
        except OSError:
            pass
        # 讀回來驗:證明「檔案真的變成那樣」,不是「我算對了」。
        got, n = hashlib.sha256(), 0
        with open(tmp, 'rb') as f2:
            while True:
                chunk = f2.read(1 << 20)
                if not chunk:
                    break
                n += len(chunk)
                got.update(chunk)
        if n != os.path.getsize(bak) or got.digest() != want.digest():
            raise DataError(
                '寫出來的暫存檔跟備份對不上(磁碟可能有問題),所以沒有換上去。\n'
                '    %s 一個位元組都沒有被動到。' % dst)
        # 換名與登記綁在一起:Ctrl-C 不可以卡在這兩行中間,
        # 不然收尾會照舊狀態說「什麼都沒有動到」。
        _REPLACING.append(dst)
        try:
            with _NoInterrupt():
                os.replace(tmp, dst)
                _RESTORED.append(dst)
                _REPLACING.remove(dst)
        except OSError:
            # os.replace 是原子的:它丟例外就是沒換成,中間態要收掉。
            if dst in _REPLACING:
                _REPLACING.remove(dst)
            raise
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise




try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 兩個上限都是防呆:檔案自己宣告的數字不可以無限相信。一個被動過手腳的檔
# 可以宣稱「解壓後有 4 GB」或「目錄有一億項」,照著配置記憶體就當場把機器吃垮。
MAX_UNCOMPRESSED = 64 * 1024 * 1024     # QFS 解壓後的位元組上限
MAX_ENTRIES = 100000                    # 封裝檔目錄項目數上限
VISIBILITY_FIELD = 1          # 元件名稱之後的第 1 個參數 = 顯示開關
# ⚠️ 下面這個 DEFAULT_BIG 在檔案後半段被同名的另一個蓋掉(那個指向 frontend.big),
#    真正生效的是後面那一個。這裡照原樣留著,只加註記,不動程式碼。
DEFAULT_BIG = os.path.join('data', 'frontend', 'ingame.big')

# 可以考慮動的指令。真正決定動不動得了的是 visibility_of:這張表過了,
# 還要那一行的第 1 個參數真的讀得到 0 或 1。本站測試機的 data/frontend/
# (六個封裝檔、332 個版面檔、141,767 行,其中 141,765 行認得出指令)
# 量到:VR / LS / LF / END 冒號後面只有一格,沒有第 1 個參數;
# TS 那一格放空白,SF 放版面檔檔名;
# KA / VS / SC 那一格是 0 或 1,但本站沒有獨立證據證明它就是顯示開關,
# 所以不放行。表裡的 SE 與 TE 同樣沒有那一欄,是這張表列錯了,
# 被 visibility_of 擋著。
# ⚠️ 這張表跟下面的 fel_lines / visibility_of 是從本站「介面萬用工具」沿用過來的
#    共用零件。這一課只換字、不碰顯示開關,所以本檔沒有用到它們。
TOGGLEABLE = {'GR', 'GG', 'SG', 'TX', 'TL', 'TE', 'TB', 'SH', 'RT',
              'SL', 'SE', 'BU', 'FC', 'FR'}


class DataError(Exception):
    """檔案不存在或格式不符預期。訊息是給人看的。"""


# ─────────────────────────────────────────────────────────
#  QFS / RefPack
# ─────────────────────────────────────────────────────────
def size_field_order(raw):
    """看檔頭那一欄用哪一種位元組順序,回傳 '<'(little)或 '>'(big)。

    ⚠️ 這一課只讀版面檔、不寫回封裝檔,所以本檔沒有呼叫這一支。
       它跟下面的 qfs_compress_literal 一樣,是沿用共用零件時一起帶進來的。

    BIGF 檔頭 +0x04 起的四個位元組是「檔案總大小」。哪一種順序不是這個格式
    天生的性質,而是看你手上這一份 data 資料夾被疊過什麼。本站以 BIGF 檔頭
    認過三份 data 資料夾:剛安裝好的原版英文版 207 個封裝檔、剛安裝好的原版
    繁體中文版 205 個,這兩份沒有一個是 big-endian;只有本站測試機那份疊過
    模組的 data 資料夾出現 big-endian,384 個封裝檔裡有 10 個,而且只落在
    這 7 個檔名上(models.big / frontend/portrait.big / pnamedat.big /
    pnamehdr.big / coornite.big / dodgnite.big / wrignite.big;測試機有兩個
    球場資料夾,球場那三個檔名各出現兩次,所以檔名 7 個而檔案 10 個)。

    不可以照檔案大小猜:兩份原版裡最大的封裝檔就是 models.big
    (172,992,803 bytes),它是 little-endian。反過來「被換過就會變 big-endian」
    也不成立:測試機上大小跟原版不同的 little-endian 封裝檔還有 135 個。
    寫回去時必須沿用原檔那一種,不然會寫進跟原檔不同的位元組。
    兩種都對不上時退回 little-endian —— 那代表這個檔的檔頭本來就不一致,
    寫回去之後的複驗會再偵測一次,兩種都對不上就會擋下來。
    """
    n = len(raw)
    if struct.unpack('<I', raw[4:8])[0] == n:
        return '<'
    if struct.unpack('>I', raw[4:8])[0] == n:
        return '>'
    return '<'


def qfs_decompress(data):
    """QFS(社群也叫它 RefPack)解壓。這一課拿它解版面檔 .fel。

    檔頭:第 0 個位元組是旗標,第 1 個固定 0xFB,這就是「10 FB」的由來。
    旗標的 bit0 決定「解壓後有多大」寫在哪裡:
        bit0 = 1   大小在 +0x06 起的 4 個位元組,壓縮資料從 +0x0A 開始
        bit0 = 0   大小在 +0x02 起的 3 個位元組,壓縮資料從 +0x05 開始
    這兩個長度欄位都是 big-endian,跟 BIGF 目錄一致,
    但跟後面 .LOC 裡那些欄位相反(那邊全是 little-endian)。看錯就整個解不出來。

    傳進來的不是 QFS 就原樣回傳。同一個封裝檔裡有壓過的也有沒壓的,
    呼叫端只看開頭兩個位元組是不是 10 FB,其餘交給這裡。
    """
    if len(data) < 2 or data[1] != 0xFB:
        return data
    if data[0] & 0x01:
        if len(data) < 10:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[6:10], 'big'); pos = 10
    else:
        if len(data) < 5:
            raise DataError('QFS 檔頭不完整')
        size = int.from_bytes(data[2:5], 'big'); pos = 5
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise DataError('QFS 宣稱解壓尺寸異常:%d' % size)

    out = bytearray()
    end = len(data)

    def guard():
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的 —— 那是「檔案自己說的」。
        #    一個惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也必須有上限,而且上限就是它自己宣稱的大小。
        if len(out) > size:
            raise DataError('QFS 解出來的資料超過檔頭宣稱的 %d 位元組 —— '
                            '這個檔可能已損毀或被動過手腳' % size)

    def copy_back(offset, length):
        if not 0 < offset <= len(out):
            raise DataError('QFS 反向參照越界 offset=%d' % offset)
        src = len(out) - offset
        for _ in range(length):
            out.append(out[src]); src += 1
        guard()

    # 接下來一路讀「控制位元組」。看第一個位元組落在哪個值域就知道這是哪一種指令:
    #   0x00-0x7F  兩個位元組一組:抄 0-3 個原文,再往回 1-1024 複製 3-10 個
    #   0x80-0xBF  三個位元組一組:抄 0-3 個原文,再往回 1-16384 複製 4-67 個
    #   0xC0-0xDF  四個位元組一組:抄 0-3 個原文,再往回 1-131072 複製 5-1028 個
    #   0xE0-0xFB  只抄原文,一次 4 到 112 個(一定是 4 的倍數)
    #   0xFC-0xFF  結束,順便抄最後 0-3 個原文
    # 「往回複製」的距離是相對於「已經解出來的尾端」,所以邊解邊長,
    # 複製到自己剛剛才寫出去的位元組是正常的:重複的花紋就是這樣壓的。
    while pos < end:
        b0 = data[pos]
        if b0 >= 0xFC:
            n = b0 & 0x03; pos += 1
            out += data[pos:pos + n]; break
        if b0 >= 0xE0:
            n = ((b0 & 0x1F) << 2) + 4; pos += 1
            out += data[pos:pos + n]; pos += n; continue
        if b0 >= 0xC0:
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]; pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 >= 0x80:
            b1, b2 = data[pos + 1], data[pos + 2]; pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        else:
            b1 = data[pos + 1]; pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        out += data[pos:pos + n]; pos += n
        copy_back(offset, length)
    return bytes(out[:size])


def qfs_compress_literal(data):
    """純 literal 編碼:不做字串比對,瞬間完成,格式一樣合法。

    ⚠️ 本檔沒有呼叫這一支(這一課不寫回封裝檔,只改字串表)。
       同樣是沿用共用零件時一起帶進來的。

    代價是檔案略大,但因為我們是「接到檔尾」,大一點沒有影響。
    """
    n = len(data)
    # 檔頭 5 個位元組:0x10 是旗標(bit0 = 0,代表用短的那種長度欄位),
    # 0xFB 是 QFS 的招牌,後面 3 個位元組是解壓後大小,big-endian。
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 0xE0 那一族一次只能抄 4 的倍數、最多 112 個,
    # 所以先把尾巴不足 4 個的那幾個位元組切開,留給最後的結束指令帶走。
    tail = n % 4
    body = n - tail
    pos = 0
    while pos < body:
        chunk = min(112, body - pos)
        out.append(0xE0 | ((chunk - 4) // 4))
        out += data[pos:pos + chunk]
        pos += chunk
    # 0xFC 那一族是結束記號,低 2 個位元順便帶走最後不足 4 個的那幾個位元組。
    out.append(0xFC | tail)
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIG 目錄
# ─────────────────────────────────────────────────────────
def list_entries(data):
    """回傳 [(名稱, TOC 欄位位置, 資料 offset, 資料長度), ...]

    BIGF 檔頭 16 個位元組:0-4 招牌 BIGF、4-8 檔案總大小、
    8-12 目錄項目數、12-16 目錄區大小。除了「檔案總大小」那一欄之外
    全部是 big-endian(那一欄兩種順序都遇得到,見 size_field_order)。

    目錄項目沒有固定長度:每一項是 4 個位元組的 offset、4 個位元組的長度,
    接一個以 NUL 結尾的檔名。所以只能一項一項往前走,不能用乘法跳到第 n 項。
    「TOC 欄位位置」是那 8 個位元組在檔案裡的位置,本檔只讀不寫,
    留著是因為這個回傳格式跟本站其他會寫回去的腳本共用。
    """
    if len(data) < 16 or data[:4] != b'BIGF':
        raise DataError('檔頭前四碼不是 BIGF,這不是 EA 封裝檔')
    count = int.from_bytes(data[8:12], 'big')
    if not 0 < count < MAX_ENTRIES:
        raise DataError('目錄項目數異常(%d),檔案可能已損毀' % count)
    items = []
    pos = 16
    for i in range(count):
        field = pos
        if pos + 8 > len(data):
            raise DataError('目錄在第 %d 項處被截斷' % (i + 1))
        offset, size = struct.unpack('>II', data[pos:pos + 8])
        pos += 8
        end = data.find(b'\x00', pos)
        if end < 0:
            raise DataError('第 %d 項的名稱沒有結束符' % (i + 1))
        if offset + size > len(data):
            raise DataError('第 %d 項的資料範圍超出檔案結尾' % (i + 1))
        items.append((data[pos:end].decode('latin-1', 'replace'), field, offset, size))
        pos = end + 1
    return items


# ─────────────────────────────────────────────────────────
#  FEL 解析(只做我們需要的:指令 / 名稱 / 顯示開關)
# ─────────────────────────────────────────────────────────
def fel_line_count(text):
    """算行數。(共用零件,本檔沒有呼叫它。)

    版面檔的換行是 CRLF,直接 count('\\r\\n')+1 會把結尾那個空字串多算一行。
    但「結尾有沒有換行符」不可以寫死:本站測試機那份 ingame.big(裝過模組)
    是 47 個版面檔,其中 46 個以 CRLF 結尾,例外是 fes_hudleft.fel;剛安裝好的原版
    是 44 個版面檔,44 個全部以 CRLF 結尾(本站三份未改動的安裝量到的都一樣)。
    所以下面用「拆完之後最後一段是不是空字串」動態判斷,兩種都算得對。
    """
    parts = text.split('\r\n')
    if parts and parts[-1] == '':
        parts.pop()
    return len(parts)


def fel_lines(text):
    """產出 (行號從1起, 原始行, 縮排, 指令, 名稱, 參數list)

    版面檔一行長這樣:`指令:名稱,參數,參數,…`,縮排代表群組的層級。
    (共用零件,本檔沒有呼叫它。這一課用的是 menu_entries 裡那條
    自己寫的正規表示式,只挑抓得出字串編號的行。)
    """
    for i, raw in enumerate(text.split('\r\n')):
        stripped = raw.lstrip(' ')
        indent = len(raw) - len(stripped)
        if not stripped or ':' not in stripped:
            yield i + 1, raw, indent, None, None, None
            continue
        cmd, _, rest = stripped.partition(':')
        parts = rest.split(',')
        name = parts[0] if parts else ''
        yield i + 1, raw, indent, cmd, name, parts


def visibility_of(parts):
    """讀「顯示開關」那一欄:1 顯示、0 隱藏,讀不到就回 None。

    (共用零件,本檔沒有呼叫它。這一課只換字,不動任何顯示開關。
    關掉選單元素是另一課的事,而且風險高得多。)
    """
    if parts is None or len(parts) <= VISIBILITY_FIELD:
        return None
    v = parts[VISIBILITY_FIELD].strip()
    return v if v in ('0', '1') else None


# ─────────────────────────────────────────────────────────
#  .LOC 字串表:把版面檔裡的「字串編號」換成真正的文字
#
#  結構(實測 IGENG.LOC / FEENG.LOC 皆同):
#    LOCH  20 bytes 檔頭
#    LOCI  索引:每 4 bytes = (LOCL 索引 << 16) | 字串編號
#    LOCL  文字:count + 位移表 + UTF-16LE 內容
# ─────────────────────────────────────────────────────────
def load_loc(path):
    """回傳 {字串編號: 文字}。讀不到就回空 dict,不中斷主流程。

    位移的算法(全部 little-endian):
      LOCH 檔頭固定 20 個位元組,LOCI 緊接在後面,所以 LOCI 從 20 開始。
      LOCI 的 +4 是它自己的大小、+8 是索引筆數,索引項從檔案位移 32 起,
      每項 4 個位元組:高 16 個位元是「第幾條文字」,低 16 個位元是字串編號
      (版面檔裡寫的就是這個編號)。
      LOCL 從 20 + LOCI 大小 開始,+4 是它自己的大小、+12 是文字條數,
      +16 起是位移表。位移表裡的數字是**相對於 LOCL 開頭**,不是相對於檔案開頭。

    ⚠️ 這一支跟下面的 loc_slots 幾乎一樣,差別是 loc_slots 連「這條字串在
       檔案裡的起迄位置」一起回傳,因為要原地覆寫。本檔只用 loc_slots;
       load_loc / load_all_loc 是沿用共用零件時一起帶進來的,沒有被呼叫。
    """
    try:
        d = open(path, 'rb').read()
    except OSError:
        return {}
    if len(d) < 32 or d[:4] != b'LOCH':
        return {}
    try:
        loci_size = struct.unpack('<I', d[24:28])[0]
        icnt = struct.unpack('<I', d[28:32])[0]
        ents = [struct.unpack('<I', d[32 + i * 4:36 + i * 4])[0] for i in range(icnt)]
        L = 20 + loci_size
        if d[L:L + 4] != b'LOCL':
            return {}
        lsize = struct.unpack('<I', d[L + 4:L + 8])[0]
        lcnt = struct.unpack('<I', d[L + 12:L + 16])[0]
        offs = [struct.unpack('<I', d[L + 16 + i * 4:L + 20 + i * 4])[0] for i in range(lcnt)]

        def text(i):
            a = L + offs[i]
            b = L + offs[i + 1] if i + 1 < lcnt else L + lsize
            return d[a:b].decode('utf-16-le', 'replace').rstrip('\x00')

        out = {}
        for x in ents:
            idx, sid = x >> 16, x & 0xFFFF
            if idx < lcnt:
                out[sid] = text(idx)
        return out
    except (struct.error, IndexError):
        return {}


# 四個候選檔名。FE 是前端(選單),IG 是比賽中,兩張表的編號各自獨立。
# 字串表的檔名跟語言版本綁在一起。
# ⚠️ EA 官方繁體中文版**不是**把中文塞進 ENG 檔,而是另外放一對 JPN 檔
#    (FEJPN.LOC / IGJPN.LOC),ENG 那一對根本不存在。
#    這支工具原本只找 ENG,所以在繁中版上會回傳 0 筆 —— 而且不報錯,
#    只是後面每一個字串都顯示不出來。那正是本站最怕的靜默失敗。
LOC_NAMES = ('FEENG.LOC', 'IGENG.LOC',      # 英文版與大多數社群中文化模組
             'FEJPN.LOC', 'IGJPN.LOC')      # EA 官方繁體中文版


def load_all_loc(gamedir):
    """比賽中與前端兩張表都讀。比賽中的優先。

    四個候選檔名都試,有幾個讀到幾個。回傳空的代表一個都沒找到。
    """
    out = {}
    for name in LOC_NAMES:
        p = os.path.join(gamedir, 'data', name)
        if os.path.isfile(p):
            out.update(load_loc(p))
    return out


def loc_files_present(gamedir):
    """實際找到哪幾個字串表 —— 讀不到的時候要能告訴使用者查過哪些。

    「一個都沒找到」跟「找到了但裡面沒有這個編號」是兩種完全不同的狀況,
    下一步也不一樣(前者是路徑或版本不對,後者是編號打錯),所以要分得開。
    """
    return [n for n in LOC_NAMES
            if os.path.isfile(os.path.join(gamedir, 'data', n))]


def string_id_of(parts):
    """TX 這類指令的參數裡,字型檔後面那個數字就是字串編號。

    做法是掃過每一個參數,遇到結尾是 .ffn 的(那是字型檔),
    就看它後面那一個是不是純數字。是,那就是字串編號。

    為什麼用「找 .ffn」而不是「數到第幾欄」:帶文字的指令有好幾種
    (TX / TB / TL / TE …),每一種前面的欄位數不一樣,數欄位一定會錯。
    字型檔一定緊接在字串編號前面,這個關係比欄位位置穩。
    """
    if not parts:
        return None
    for i, c in enumerate(parts):
        if c.strip().lower().endswith('.ffn') and i + 1 < len(parts):
            v = parts[i + 1].strip()
            if v.isdigit():
                return int(v)
    return None



# ─────────────────────────────────────────────────────────
#  改字串:為什麼只准「同長或更短」
# ─────────────────────────────────────────────────────────
# .LOC 的結構是「位移表 + 一整塊連續文字」。想把某一條字串改長,
# 就得把它後面**每一條**的位移全部往後推,並重算整個 LOCL 區的長度 ——
# 6,352 條裡改錯任何一個位移,遊戲讀到的就是別條字串的中間。
#
# 所以這支工具走另一條路:**原地覆寫,長度不變。**
#   · 檔案總長度不變
#   · 位移表一個位元組都不動
#   · 你沒點名的 6,351 條保證逐位元組相同
# 代價是新文字不能比原本長。在原廠英文的字串表上,每個槽位的可用字數
# **剛好等於原字串長度**:本站量了兩份 FEENG.LOC(剛安裝好的原版
# 415,528 位元組、本站測試機 416,753 位元組),兩份都是 6,352 條全部以
# 2 個 NUL 字元收尾、可用字數等於原字數,零例外。所以規則很單純:
#
#     新文字的字數 ≤ 原文字的字數
#
# ⚠️ 這對「英文改中文」剛好夠用 —— 中文字少。
#    Play Now(8 字)換成「馬上開打」(4 字)綽綽有餘。
#    反過來想把中文改成長英文就會被擋下來,那是刻意的。
#
# ⚠️ 「零例外」只對那兩份原廠英文表成立,不是 .LOC 這個格式的性質。
#    只要字串表被人改過就不一定:本站那份 2009 年台灣模組的**英文**
#    FEENG.LOC(415,840 位元組)有 5 條不是 2 個 NUL,只是那 5 條空間反而更大;
#    同一包裡的**中文** FEENG.LOC(219,421 位元組)有 6,436 條,
#    其中 6,291 條剛好、114 條空間更大、30 條的可用字數比原字數少一個字
#    (「打擊」「捕手」「全壘打」這種),還有 1 條算出來的槽位長度是負的。
#    那 30 條連原本的字都寫不回去,但只會被 write_slots 擋下來,不會寫壞檔。
#    程式不必為此改什麼:budget_chars 本來就是照槽位算的,
#    但你不能拿原字數當預算,要看 --list 印出來的「可用字數」。
# 備份用自己的副檔名,不叫 .bak。別課的腳本也會在 data/ 底下留備份,
# 名字撞在一起會互相覆蓋,而且還原的時候你分不出來是哪一課留的。
BAK_SUFFIX = '.menutextbak'


def loc_slots(path):
    """回傳 (原始位元組, {字串編號: (起, 迄, 文字)})。讀不到回 (None, {})。

    「起、迄」是這條字串在**整個檔案**裡的位元組位置(位移表裡是相對於
    LOCL 開頭的,這裡已經加上 L 換算好了)。原地覆寫要的就是這兩個數字。
    最後一條沒有下一條可以當終點,就用 LOCL 宣告的總長度收尾。

    讀壞了一律回 (None, {}) 而不是丟例外:呼叫端會依序試四個候選檔名,
    其中一個不是字串表(或根本不存在)是正常情況,不該中斷整個流程。
    """
    try:
        d = open(path, 'rb').read()
    except OSError:
        return None, {}
    if len(d) < 32 or d[:4] != b'LOCH':
        return None, {}
    try:
        loci_size = struct.unpack('<I', d[24:28])[0]
        icnt = struct.unpack('<I', d[28:32])[0]
        ents = [struct.unpack('<I', d[32 + i * 4:36 + i * 4])[0] for i in range(icnt)]
        L = 20 + loci_size
        if d[L:L + 4] != b'LOCL':
            return None, {}
        lsize = struct.unpack('<I', d[L + 4:L + 8])[0]
        lcnt = struct.unpack('<I', d[L + 12:L + 16])[0]
        offs = [struct.unpack('<I', d[L + 16 + i * 4:L + 20 + i * 4])[0]
                for i in range(lcnt)]
        out = {}
        for x in ents:
            idx, sid = x >> 16, x & 0xFFFF
            if idx >= lcnt:
                continue
            a = L + offs[idx]
            b = L + offs[idx + 1] if idx + 1 < lcnt else L + lsize
            out[sid] = (a, b, d[a:b].decode('utf-16-le', 'replace').rstrip('\x00'))
        return d, out
    except (struct.error, IndexError):
        return None, {}


def budget_chars(a, b):
    """這個槽位放得下幾個字(扣掉結尾那 2 個 NUL)。

    槽位有 b - a 個位元組,UTF-16LE 一個編碼單位 2 個位元組,
    再扣掉結尾固定的 2 個 NUL 字元(也就是 4 個位元組)。

    ⚠️ 這裡數的是 UTF-16 的**編碼單位**,不是 Python 的字數。
       常用漢字一個字剛好一個單位,兩邊一樣;但 emoji 這類字要兩個單位,
       Python 的 len() 只算一個。真正把關的是 write_slots(它算位元組),
       所以 cmd_set 的預覽也要用同一把尺量(它算 len(text.encode('utf-16-le'))//2),
       不可以用 len(text) —— 2026-09-05 之前用的就是 len(text),於是那種字
       「預覽說放得下、寫入時才被擋」,而 --set 橫跨兩張字串表時
       第一張已經寫進去了才在第二張中止。
    """
    return max(0, (b - a) // 2 - 2)


def write_slots(data, slots, changes):
    """原地覆寫。changes = {字串編號: 新文字}。回傳新的位元組。

    每一條都寫成「新文字 + 補滿 NUL 到原槽位長度」,所以長度一定不變。
    """
    # 逐條在原地覆寫:新文字編成 UTF-16LE,後面用 NUL 補到原本的槽位長度。
    # 補 NUL 不只是為了湊長度,字串本身也要靠 NUL 收尾,
    # 所以上面留了 4 個位元組(2 個 NUL 字元)的餘裕,那是硬性的。
    buf = bytearray(data)
    for sid, text in changes.items():
        a, b, _old = slots[sid]
        enc = text.encode('utf-16-le')
        room = b - a
        if len(enc) + 4 > room:
            raise DataError('編號 %d 放不下:新文字要 %d 個位元組,槽位只有 %d '
                            '(還要留 4 個給結尾)。' % (sid, len(enc), room))
        buf[a:b] = enc + b'\x00' * (room - len(enc))
    # 這一行是這支工具的核心承諾:長度沒變,所以位移表一個位元組都不用動。
    # 承諾一旦破了就是災難級的錯,寧可當場中止,不要寫出去。
    assert len(buf) == len(data), '內部錯誤:長度變了'
    return bytes(buf)


def find_loc_for(gamedir, sid):
    """哪一個 .LOC 檔裡有這個編號。回傳 (路徑, slots) 或 (None, {})。

    照 LOC_NAMES 的順序一個一個試,**先找到的先用**(FEENG 排在 IGENG 前面)。
    同一個編號如果兩張表裡都有,這裡只會回前面那一張,也就是只會改到那一張。
    本站沒有量過「兩張表的編號重疊到什麼程度」,所以改完看不到變化時,
    這是要懷疑的地方之一。
    """
    for name in LOC_NAMES:
        p = os.path.join(gamedir, 'data', name)
        if not os.path.isfile(p):
            continue
        d, slots = loc_slots(p)
        if d is not None and sid in slots:
            return p, slots
    return None, {}


# ⚠️ DataError 在檔案上半段已經定義過一次,這裡是第二次,生效的是這一個。
#    兩個都只是 Exception 的空殼,行為完全一樣,所以留著沒有風險。
#    照本站紀律「看到問題寫下來、不順手改」,這裡只加註記。
class DataError(Exception):
    pass


# ⚠️ 同上:DEFAULT_BIG 也是第二次定義,真正生效的是這一個(frontend.big)。
#    上面那個指向 ingame.big 的沒有作用。主選單的版面檔在 frontend.big 裡,
#    ingame.big 裝的是比賽中的 HUD,不是選單。
DEFAULT_BIG = os.path.join('data', 'frontend', 'frontend.big')
DEFAULT_FEL = 'fes_mainmenu.fel'        # 主選單的版面檔


def menu_entries(gamedir, bigrel, felname):
    """回傳 [(行號, 元素名, 字串編號), ...] —— 這個版面檔用到哪些字串。

    流程:打開封裝檔 → 在目錄裡找出那個版面檔 → 開頭是 10 FB 就解壓 →
    當成文字一行一行掃,把抓得出字串編號的行收起來。
    整段唯讀,連暫存檔都不產生。

    ⚠️ 解出來用 latin-1 解碼,不是 UTF-8。版面檔是純 ASCII 的指令稿,
       latin-1 保證每個位元組都對得到一個字元、不會丟例外,
       行號也才會跟你用文字編輯器打開時看到的一致。
    """
    p = os.path.join(gamedir, bigrel)
    if not os.path.isfile(p):
        raise DataError('找不到 %s\n  你給的是:%s' % (bigrel, gamedir))
    data = open(p, 'rb').read()
    hit = None
    for name, field, off, size in list_entries(data):
        if name.lower() == felname.lower():
            hit = (off, size)
            break
    if hit is None:
        raise DataError('%s 裡沒有 %s' % (bigrel, felname))
    raw = data[hit[0]:hit[0] + hit[1]]
    text = (qfs_decompress(raw) if raw[:2] == b'\x10\xfb' else raw).decode('latin-1')
    # ⚠️ 不要只認 TX。選單上的按鈕是 **TB**(文字按鈕),
    #    主選單裡 31 個 TB 對 10 個 TX —— 第一版只抓 TX,
    #    於是「Play Now」「Game Modes」這些真正想改的字一個都看不到,
    #    而且畫面上還印得很像對(10 行 TITLE 全部列出來)。
    #    改成「任何兩個大寫字母的指令,只要抓得出字串編號就算」,
    #    讓 string_id_of 自己決定 —— 不要靠一份會過期的型別白名單。
    # 版面檔一律 CRLF 換行(本站鐵律之一),所以直接切 \r\n,
    # 行號從 1 起算,對得上你用文字編輯器打開時看到的行號。
    out, seen = [], set()
    for n, line in enumerate(text.split('\r\n'), 1):
        m = re.match(r'\s*([A-Z]{2}):([A-Za-z0-9_]*),(.*)$', line)
        if not m:
            continue
        sid = string_id_of(m.group(3).split(','))
        if sid is None or sid in seen:      # 同一條字串被好幾行引用時只列一次
            continue
        seen.add(sid)
        out.append((n, '%s:%s' % (m.group(1), m.group(2)), sid))
    return out


def cmd_list(gamedir, bigrel, felname):
    """--list:把這個版面檔用到的字串全部列出來。唯讀。

    每一行是:版面檔裡的行號、元素、字串編號、現在的文字、還能放幾個字,
    以及它是在哪一個字串表裡找到的。
    「可用字數」要在這裡就給,不然使用者只能靠 --set 一條一條試才知道放不放得下。

    ⚠️ 開頭印的那個數字是「不同的字串有幾條」,不是「帶文字的元素有幾個」。
       menu_entries() 已經去重,同一條字串被好幾個元素引用時只列一次。
       fes_mainmenu.fel 實測:帶字串編號的元素 41 個(10 個 TX、31 個 TB),
       去重後只剩 9 條(編號 12、13、14、270、280、627、8140、8180、16306),
       所以 --list 印出來是 9 行。三份 data/frontend/frontend.big 上量到的
       都一樣:本站測試機那一份、剛安裝好的全新英文版、剛安裝好的全新中文版。
    """
    rows = menu_entries(gamedir, bigrel, felname)
    present = loc_files_present(gamedir)
    if not present:
        raise DataError('找不到任何字串表。本工具會找這四個:%s' % '、'.join(LOC_NAMES))
    print('  %s → %s' % (bigrel, felname))
    print('  找到的字串表:%s' % '、'.join(present))
    print('  這個版面檔用到 %d 條不同的字串(同一條字串被好幾個元素引用時只列一次)\n' % len(rows))
    print('  %6s  %-22s %7s  %-28s %s' % ('行號', '元素', '編號', '現在的文字', '可用字數'))
    print('  %s' % ('-' * 82))
    for n, nm, sid in rows:
        path, slots = find_loc_for(gamedir, sid)
        if path is None:
            print('  %6d  %-22s %7d  %-28s %s' % (n, nm, sid, '（四個字串表裡都沒有）', '-'))
            continue
        a, b, txt = slots[sid]
        print('  %6d  %-22s %7d  %-28s %d 字（在 %s）'
              % (n, nm, sid, txt, budget_chars(a, b), os.path.basename(path)))
    print('\n  「可用字數」是這條字串**最多**能放幾個字 —— 本工具只做原地覆寫,')
    print('  不會把字串改長(理由見程式開頭)。中文字少,英文換中文通常綽綽有餘。')
    print('\n  要改就這樣:')
    print('    python3 %s "%s" --set 12=馬上開打'
          % (os.path.basename(sys.argv[0]), gamedir))


def _restore_after_failed_verify(path, bak, want_size):
    """複驗沒過就當場還原回去 —— 不要留一個壞掉的檔在那裡等玩家自己發現。

    走的是 --restore 同一條路(同樣那五道把關 + 原子換檔),所以
    「備份自己也是壞的」會被擋下來,不會把壞的蓋在壞的上面。
    還原不成功也不會假裝沒事:回 False,呼叫端照樣用離開碼 2 停掉。
    """
    print('\n  複驗沒過 —— 現在自動從備份還原,把遊戲檔放回動手前的樣子。')
    try:
        n = os.path.getsize(bak)
        if n != want_size:
            raise DataError('備份 %s bytes,動手前那個檔 %s bytes,兩者不同。'
                            % (format(n, ','), format(want_size, ',')))
        _restore_from_backup(bak, path)
    except (Exception, SystemExit) as e:
        print('  ✗ 自動還原沒有做成:%s' % e)
        print('    請立刻自己跑一次 --restore,然後回報。')
        return False
    if path in _WROTE:
        _WROTE.remove(path)            # 已經放回去了,Ctrl-C 的訊息才不會說錯
    print('  ✓ 已自動還原 %s(內容與備份逐位元組相同)' % os.path.basename(path))
    return True


def _rollback_written(done):
    """多檔的時候,後面那個檔出事就把前面已經換好的放回去 —— 全有或全無。

    ⚠️ 2026-09-06 補的。在那之前,--set 同時點到兩個字串表(編號分屬
       FEENG.LOC 與 IGENG.LOC)而第二個檔複驗沒過時,第一個檔會**留在新的狀態**:
       第二個檔自己會自動還原、離開碼 2,但第一個不會 —— 也就是玩家拿到一個
       「一半新一半舊」的遊戲。現在只要有任何一個檔出事,前面換好的都放回去。

    走的是 --restore 同一條路(五道把關 + 原子換檔),所以「備份自己也是壞的」
    會被擋下來。還原不成功不會假裝沒事:逐檔印出來,叫玩家自己跑 --restore。
    """
    if not done:
        return
    print('\n  前面已經改好的 %d 個檔要放回動手前的樣子(要嘛全部改到,要嘛全部回到原樣):'
          % len(done))
    for path, bak, size in reversed(done):
        try:
            n = os.path.getsize(bak)
            if n != size:
                raise DataError('備份 %s bytes,動手前那個檔 %s bytes,兩者不同。'
                                % (format(n, ','), format(size, ',')))
            _restore_from_backup(bak, path)
        except (Exception, SystemExit) as e:
            print('  ✗ %s 沒有放回去:%s' % (os.path.basename(path), e))
            print('    請立刻自己跑一次 --restore,然後回報。')
            continue
        if path in _WROTE:
            _WROTE.remove(path)
        print('  ✓ 已放回 %s(內容與備份逐位元組相同)' % os.path.basename(path))


def cmd_set(gamedir, sets, apply_it):
    """--set:預覽或寫入。沒有 --apply 就只印表格,一個位元組都不寫。

    順序是刻意排的,而且每一步都在寫入之前:
      1. 每一條先歸到它所屬的字串表(不同編號可能在不同檔裡)
      2. 印出「原本 / 改成 / 字數」,太長的標出來
      3. 只要有一條太長就整批停住,不做「能寫幾條算幾條」。
         「太長」用的是 UTF-16 的編碼單位,跟真正把關的 write_slots 同一把尺
      4. 到這裡都還沒碰過檔案。沒加 --apply 就在這裡結束
      5. 加了 --apply 也還會先把**每一個檔**的新內容全部算完,
         一個都沒出事才開始寫第一個檔
      6. 真的開始寫之後還是全有或全無:第二個檔複驗沒過,第一個檔會被
         放回動手前的樣子(見 _rollback_written)
    """
    # 先把每一條歸到它所屬的字串表 —— 不同編號可能在不同檔裡
    by_file = {}
    for sid, text in sets.items():
        path, slots = find_loc_for(gamedir, sid)
        if path is None:
            raise DataError('四個字串表裡都找不到編號 %d。先用 --list 看有哪些。' % sid)
        by_file.setdefault(path, ({}, slots))[0][sid] = text

    print('  %8s  %-26s %-26s %s' % ('編號', '原本', '改成', '字數'))
    print('  %s' % ('-' * 78))
    over = []
    for path, (changes, slots) in by_file.items():
        for sid, text in changes.items():
            a, b, old = slots[sid]
            room = budget_chars(a, b)
            # ⚠️ 預算要數 UTF-16 的編碼單位,不是 Python 的字數。BMP 以外的漢字
            #    (例:𡘙)與 emoji 一個字佔兩個單位,用 len(text) 會少算 ——
            #    預覽放行、write_slots 才擋,多檔時前面那個檔已經寫進去了。
            #    2026-09-05 實測:--set 627=離開 --set 142=𡘙×8 --apply
            #    會先寫完 FEENG.LOC 再在 IGENG.LOC 中止,而檔頭與本課頁面
            #    都寫著「整批停住」。兩把尺換成同一把之後就不會了。
            need = len(text.encode('utf-16-le')) // 2
            flag = '' if need <= room else '  ← 太長'
            if need > room:
                over.append((sid, need, room))
            print('  %8d  %-26s %-26s %d/%d%s' % (sid, old, text, need, room, flag))
    if over:
        print('\n  ✗ 有 %d 條放不下。本工具只做原地覆寫,新文字不能比原本長。' % len(over))
        print('    (為什麼不能改長:.LOC 是「位移表 + 一整塊文字」,改長就要重算')
        print('     後面每一條的位移,6,352 條裡錯一個,遊戲讀到的就是別條的中間。)')
        raise DataError('請把太長的那幾條改短一點。')

    if not apply_it:
        print('\n  這是預覽,沒有改到任何檔案。確定要改請加上 --apply。')
        return

    # 真正寫入。**先把每一個檔的新內容全部算完,一個都沒出事才開始動檔案。**
    # ⚠️ 這一段以前是「算一個寫一個」:上面的預覽跟 write_slots 用不同的尺量
    #    「太長」時,第一個檔已經備份並寫進去了才在第二個檔中止 ——
    #    也就是檔頭與本課頁面同時宣稱不會發生的「能寫幾條算幾條」。
    #    尺已經統一了(見上面 need),這裡再擋一次:write_slots 只要有任何一條
    #    丟例外,就會在還沒碰過任何檔案的時候丟出去。
    prepared = []
    for path, (changes, slots) in by_file.items():
        d = open(path, 'rb').read()
        prepared.append((path, d, write_slots(d, slots, changes), changes, slots))

    # 到這裡為止一個位元組都還沒寫。以下才動檔案:備份 → 寫暫存檔 →
    # fsync 落地 → os.replace 換過去。中途斷電最多留下一個 .tmp,
    # 正本要嘛是舊的、要嘛是新的,不會是半截的。
    # ⚠️ 多檔的時候要嘛全部改到、要嘛全部回到動手前(2026-09-06 補)。
    #    一個 --set 可能同時點到兩個字串表,第二個檔出事時第一個檔已經是新的了。
    #    Ctrl-C 不走這條回滾:那時候玩家要的是「立刻停」,再動檔案反而更嚇人 ——
    #    走的是收尾那條**誠實**路徑(逐檔列出已經改好的哪幾個 + 印還原指令,離開碼 130)。
    done_ok = []
    try:
        for path, d, new, changes, slots in prepared:
            bak = path + BAK_SUFFIX
            # 動手之前先擋符號連結:正本或備份是連結的話,寫下去會改到資料夾外面。
            # ⚠️ 用 islink 不用 exists —— exists 對「指向不存在目標的連結」回 False,
            #    那種連結照樣會把寫入導到外面去。lexists 才看得到連結本身。
            _refuse_if_symlink(path, '要改的那個字串表')
            _refuse_if_symlink(bak, '備份檔')
            if not os.path.lexists(bak):
                _atomic_copy(path, bak)
                print('\n  ✓ 已備份:%s' % os.path.basename(bak))
            else:
                print('\n  · 備份已存在,保留最早那一份:%s' % os.path.basename(bak))
            # 暫存檔用 mkstemp 開在同一個資料夾裡(同一個檔案系統,os.replace 才是原子的)。
            # ⚠️ 不寫死 path + '.tmp':那個名字如果剛好已經存在(上一次被中斷留下的、
            #    或使用者自己的檔),就會被無聲蓋掉。mkstemp 保證拿到一個全新的名字。
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.',
                                       prefix=os.path.basename(path) + '.', suffix='.tmp')
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(new)
                    f.flush()
                    os.fsync(f.fileno())
                # ⚠️ 新建的暫存檔用的是行程 umask(mkstemp 更嚴,是 0600),不是原檔的權限。
                #    不補這一段的話,os.replace 之後遊戲檔的權限會被換掉
                #    (寫死 open() 的舊寫法實測是 0700 → 0644)。
                #    只複製權限位元,不動時間戳 —— 改過的檔本來就該有新的修改時間。
                try:
                    os.chmod(tmp, os.stat(path).st_mode & 0o7777)
                except OSError:
                    pass
                # 換名與登記綁成不可切開的一段(見 _NoInterrupt)。
                # 中間態先登記:萬一連 _NoInterrupt 都裝不上,收尾至少說得出
                # 「中斷的時候正在替換哪一個檔」,而不是「什麼都沒有動到」。
                _REPLACING.append(path)
                try:
                    with _NoInterrupt():
                        os.replace(tmp, path)
                        _WROTE.append(path)   # 換過了 —— Ctrl-C 時不可以說「什麼都沒動」
                        _REPLACING.remove(path)
                except OSError:
                    if path in _REPLACING:
                        _REPLACING.remove(path)
                    raise
            except BaseException:
                # 寫到一半出事(磁碟滿、Ctrl-C):把暫存檔收乾淨,正本一個位元組都沒動。
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass
                raise

            # ── 寫入後複驗 ────────────────────────────────
            # 複驗是重新從磁碟讀回來,不是拿記憶體裡那份來比。
            # 拿記憶體比只證明「我算對了」,讀回來才證明「檔案真的變成那樣」。
            # ⚠️ 四個數字都印,而且**四件只要有一件對不上就停**(2026-09-05 改;
            #    在那之前只擋前兩件,另外兩件只印數字,對不上也照樣印「完成」、
            #    離開碼 0 —— 等於把「這個檔可能已經壞了」交給玩家自己看數字)。
            #    停下來的時候會當場自動從備份還原,離開碼是 2。
            d2, slots2 = loc_slots(path)
            bad = [sid for sid, t in changes.items() if slots2.get(sid, (0, 0, None))[2] != t]
            # ⚠️ 「沒點名的」不能一律拿 len(slots) - len(changes) 當分母:
            #    LOCI 的索引項是 (LOCL 索引 << 16) | 字串編號,**兩個編號可以指到
            #    同一個 LOCL 索引**,那它們就是同一個槽位,改一個另一個一定跟著變。
            #    本站量到的四份原廠字串表(測試機與剛安裝好的原版各兩個檔)都剛好
            #    有一組:編號 0 與編號 8 共用索引 0(內容是佔位用的 <some text>)。
            #    不先把這種扣掉,改到那兩個編號就會被自己的複驗誤判成「檔案壞了」。
            spans = {(slots[sid][0], slots[sid][1]) for sid in changes}
            shared = [sid for sid in slots
                      if sid not in changes and (slots[sid][0], slots[sid][1]) in spans]
            quiet = [sid for sid in slots if sid not in changes and sid not in shared]
            untouched = sum(1 for sid in quiet
                            if slots2.get(sid, (0, 0, None))[2] == slots[sid][2])
            print('  ✓ 已寫入 %s' % os.path.basename(path))
            print('    檔案大小   %s bytes(原本 %s,**必須相同**)'
                  % (format(len(d2), ','), format(len(d), ',')))
            print('    字串總數   %d 條(原本 %d 條)' % (len(slots2), len(slots)))
            print('    改的複驗   %d/%d 正確' % (len(changes) - len(bad), len(changes)))
            print('    沒動到的   %d 條逐字相同(共 %d 條沒點名)' % (untouched, len(quiet)))
            if shared:
                print('    共用槽位   編號 %s 跟你點名的那幾條是同一個槽位,會一起變'
                      '(不是異常)' % '、'.join(str(x) for x in sorted(shared)))
            problems = []
            if len(d2) != len(d):
                problems.append('檔案大小從 %s 變成 %s bytes'
                                % (format(len(d), ','), format(len(d2), ',')))
            if bad:
                problems.append('點名要改的那幾條有 %d 條沒寫成你要的字' % len(bad))
            if len(slots2) != len(slots):
                problems.append('字串總數從 %d 條變成 %d 條' % (len(slots), len(slots2)))
            if untouched != len(quiet):
                problems.append('沒點名的字串有 %d 條跟原本不一樣' % (len(quiet) - untouched))
            if problems:
                _restore_after_failed_verify(path, bak, len(d))
                raise DataError('複驗沒過:%s。請回報。' % '、'.join(problems))
            done_ok.append((path, bak, len(d)))
    except Exception:
        _rollback_written(done_ok)
        raise
    print('\n  完成。要還原:--restore')


def cmd_restore(gamedir):
    """--restore:把四個候選字串表中有備份的那些還原回去。

    四道把關:
      0. 備份或正本是**符號連結**就拒絕。順著它寫下去改到的是資料夾外面
         那個檔,而 os.replace 只會換掉連結本身 —— 外面那個已經沒了。
         ⚠️ 判斷要用 os.path.lexists / islink:exists 對「指向不存在目標的
         連結」回 False,那種連結會被無聲跳過。
      1. 備份的開頭要是 LOCH(拿錯檔、0 bytes 的備份都在這裡擋掉)
      2. **備份與現在那個檔的長度必須完全相同。** 這一支只做同長度的原地覆寫,
         所以它自己留下的備份一定跟正本一樣大;不一樣就只有兩種可能 ——
         備份那次出事了(半截),或者這個 .LOC 後來被別的東西換掉了。
         兩種都不該讓它蓋下去。
         ⚠️ 這一道是 2026-09-05 補的,補的是一個真的會吃掉檔案的窗口:
         把 416,753 bytes 的備份截成 416,336(只少最後 417 個位元組),
         底下 _restore_from_backup 的五道全部驗得過、印「✓ 已還原」、
         exit code 0,正本當場被短掉的檔覆蓋。
      3. 交給 _restore_from_backup 驗它的內部結構完不完整,
         再由 _do_copy 原子地換上去(寫暫存檔 → 比 sha256 → os.replace)。
    只認 .menutextbak,不會去碰別課留下的 .bak。
    """
    done = 0
    for name in LOC_NAMES:
        p = os.path.join(gamedir, 'data', name)
        bak = p + BAK_SUFFIX
        if not os.path.lexists(bak):
            continue
        # lexists 之後緊接著擋連結:順序不能反,不然 dangling 的連結會被跳過。
        _refuse_if_symlink(bak, '備份檔')
        _refuse_if_symlink(p, '要還原的那個遊戲檔')
        with open(bak, 'rb') as f:
            if f.read(4) != b'LOCH':
                raise DataError('備份不是字串表,不敢拿它覆蓋:%s' % os.path.basename(bak))
        if os.path.isfile(p):
            nbak, live = os.path.getsize(bak), os.path.getsize(p)
            if nbak != live:
                raise DataError(
                    '備份跟現在的 %s 長度不一樣,不敢拿它覆蓋。\n'
                    '    備份 %s bytes,現在的檔 %s bytes。\n'
                    '    本工具只做同長度的原地覆寫,自己留下的備份一定跟正本一樣大。\n'
                    '    不一樣代表:備份那次被中斷(半截),或這個檔後來被別的東西換掉了。\n'
                    '    請改用你自己另外留的那一份完整備份。'
                    % (name, format(nbak, ','), format(live, ',')))
        try:
            _restore_from_backup(bak, p)
        except SystemExit as e:
            # 共用零件用 raise SystemExit 報錯,那樣 exit code 會是 1,
            # 跟檔頭寫的「1 = 沒給遊戲資料夾、2 = 檔案內容不如預期」對不上。
            # 轉成 DataError,訊息一字不改,只讓離開碼回到 2。
            raise DataError('%s' % e)
        print('  ✓ 已還原 %s' % name)
        done += 1
    if not done:
        raise DataError('找不到本工具的備份(%s)。\n'
                        '  本工具只認自己這一個,不會去動別課留下的 .bak。' % BAK_SUFFIX)


def main():
    """命令列入口。--selftest 最優先,因為它不需要遊戲資料夾。

    回傳值就是 exit code:0 成功、1 是沒給遊戲資料夾(印說明)、
    2 是檔案內容或參數不如預期(DataError)、130 是被 Ctrl-C 中斷。
    分開是為了讓看輸出的人分得出「我打錯了」跟「這個遊戲資料夾有問題」。
    """
    ap = argparse.ArgumentParser(
        description='改 MVP Baseball 2005 選單上的文字',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
例子(照順序做):

  1. 看主選單有哪些字可以改(唯讀)
     python3 mvp_menu_text.py "<遊戲資料夾>" --list

  2. 預覽(不會動到遊戲)
     python3 mvp_menu_text.py "<遊戲資料夾>" --set 12=馬上開打 --set 627=離開

  3. 確定了才真的改
     python3 mvp_menu_text.py "<遊戲資料夾>" --set 12=馬上開打 --apply

  出問題就還原:
     python3 mvp_menu_text.py "<遊戲資料夾>" --restore

⚠️ 只能改成**同長或更短**的文字。本工具是原地覆寫:檔案長度不變、
   位移表不動、你沒點名的字串保證逐位元組相同。中文字少,英文換中文通常夠用。
⚠️ 改成中文之前,你的遊戲要先有中文字型,否則會變成空白或方框。
''')
    ap.add_argument('gamedir', nargs='?', help='遊戲資料夾(裡面看得到 data)')
    ap.add_argument('--list', action='store_true', help='看有哪些字可以改(唯讀)')
    ap.add_argument('--set', action='append', metavar='編號=新文字', default=[],
                    help='改一條字串,可以寫很多次')
    ap.add_argument('--fel', default=DEFAULT_FEL, help='要看哪個版面檔(預設主選單)')
    ap.add_argument('--big', default=DEFAULT_BIG, help='版面檔在哪個封裝檔裡')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原')
    ap.add_argument('--selftest', action='store_true', help='自我測試,不碰任何遊戲檔')
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.gamedir:
        ap.print_help()
        return 1

    try:
        if args.restore:
            cmd_restore(args.gamedir)
        elif args.set:
            # --set 可以寫很多次,一次收齊再一起處理:
            # 全部先解析、全部先檢查,不會出現「前兩條寫進去了、第三條才發現太長」。
            sets = {}
            for spec in args.set:
                if '=' not in spec:
                    raise DataError('--set 要寫成 編號=新文字,你給的是「%s」' % spec)
                k, v = spec.split('=', 1)
                if not k.strip().isdigit():
                    raise DataError('編號要是數字,你給的是「%s」' % k)
                sets[int(k.strip())] = v
            cmd_set(args.gamedir, sets, args.apply)
        else:
            cmd_list(args.gamedir, args.big, args.fel)
    except DataError as e:
        print('\n  停下來了:%s\n' % e)
        return 2
    except KeyboardInterrupt:
        # ⚠️ 不可以一律印「什麼都沒有動到」:os.replace 如果已經做過了,
        #    遊戲檔就已經是新的那一份。這兩個清單記的就是「換過了沒有」,
        #    沒有它們,這句話有一半的時候是假的。兩種情況都回 130,不是 0。
        # ⚠️ _REPLACING 是「換名做到一半」的中間態。正常情況它永遠是空的
        #    (換名與登記被 _NoInterrupt 綁在一起);它不是空的,代表連
        #    _NoInterrupt 都沒裝上,那就**不可以**猜,只能照實說。
        if _REPLACING:
            print('\n  已中斷,而且中斷的時候正在替換下面這些檔:')
            for q in _REPLACING:
                print('      %s' % q)
            print('  換檔是原子的,所以它要嘛還是舊的、要嘛已經是新的,'
                  '不會是半截 —— 但這裡分不出是哪一種。')
            print('  請跑一次 --restore 還原,或自己跟 %s 比對過再繼續。' % BAK_SUFFIX)
            if _WROTE:
                print('  另外下面這些**已經改好了**:')
                for q in _WROTE:
                    print('      %s' % q)
            print('')
        elif _WROTE:
            print('\n  已中斷。⚠️ 下面這些檔**已經改好了**'
                  '(換檔是原子的,所以是完整的新版,不是半截):')
            for q in _WROTE:
                print('      %s' % q)
            print('  要回到動手前的樣子:--restore\n')
        elif _RESTORED:
            print('\n  已中斷。已經還原回去的是:%s;其餘沒有動到。\n'
                  % '、'.join(os.path.basename(q) for q in _RESTORED))
        else:
            print('\n  已中斷。什麼都沒有動到。\n')
        return 130
    return 0


# ─────────────────────────────────────────────────────────
#  自我測試:不碰任何遊戲檔,自己造一個最小的 .LOC 來做。
# ─────────────────────────────────────────────────────────
def _fake_loc(pairs):
    """造一個能被 loc_slots 讀懂的最小字串表。pairs = [(編號, 文字), ...]

    結構照真檔量到的(FEENG.LOC / IGENG.LOC 皆同):
      0-20   LOCH:magic + 20 + 1 + 1 + LOCL 的位移
      20-32  LOCI:magic + loci_size + icnt
      32-    索引項,每 4 bytes = (LOCL 索引 << 16) | 字串編號
             後面補 4 個位元組 —— **loci_size = 16 + 4*n 不是 12 + 4*n**
             (真檔:icnt 6352、loci_size 25424 = 16 + 4*6352)
      L-     LOCL:magic + lsize + 保留 4 + lcnt + 位移表 + UTF-16LE 內容
    ⚠️ 第一版憑推的寫成 12 + 4*n,少 4 個位元組,LOCL 的 magic 就對不上,
       自我測試自己先掛掉。**先看真檔的位元組再造測試資料。**
    """
    texts = [t.encode('utf-16-le') + b'\x00\x00\x00\x00' for _s, t in pairs]
    offs, cur = [], 16 + 4 * len(texts)
    for t in texts:
        offs.append(cur)
        cur += len(t)
    lsize = cur
    locl = (b'LOCL' + struct.pack('<I', lsize) + b'\x00' * 4
            + struct.pack('<I', len(texts))
            + b''.join(struct.pack('<I', o) for o in offs)
            + b''.join(texts))
    loci_body = b''.join(struct.pack('<I', (i << 16) | sid)
                         for i, (sid, _t) in enumerate(pairs))
    loci_size = 16 + 4 * len(pairs)
    loci = b'LOCI' + struct.pack('<I', loci_size) + struct.pack('<I', len(pairs)) \
        + loci_body + b'\x00' * 4
    L = 20 + loci_size
    loch = (b'LOCH' + struct.pack('<I', 20) + struct.pack('<I', 1)
            + struct.pack('<I', 1) + struct.pack('<I', L))
    return loch + loci + locl


def selftest():
    """--selftest:自己造一個最小的字串表來測,完全不碰遊戲檔。

    測的是這支工具的核心承諾,一條一條驗:
      · 造出來的字串表讀得出來,而且文字跟放進去的一樣
      · 每個槽位算出來的可用字數等於原字串長度
      · 改短之後檔案長度不變,沒點名的字串逐字相同
      · 完整的備份還原得回去,而且逐位元組回到原本的樣子
    上面這四條在程式裡是 7 道檢查(含改完讀回來對、沒點名的逐字相同),都是正向的。
    後面標成「反向餌」的是 6 塊、另外 10 道:改成同長要能過、太長要被擋、
    壞檔與不存在的檔都要回空的(各 1 道)、UTF-16 的兩條編碼假設、
    BMP 以外的字要佔兩個編碼單位(2 道)、
    長度對不上的備份要被 --restore 擋下來而且檔案不可以被動到(2 道)。
    這一段合計 17 道(15 條 assert 加 2 組必須丟出例外的 try)。
    這 6 塊裡真正「故意做一件必須失敗的事」的是「太長要被擋」與
    「長度對不上的備份要被擋」那兩道,其餘是餵壞資料或編碼假設的一般斷言,
    失敗不了才是問題。

    2026-09-05 又加了三組(每一組都是「先讓舊寫法咬得到」才算數的餌):
      · 猜得到的暫存檔名字被人先佔住:在資料夾裡放好 <正本>.part /
        <備份>.part / .tmp 四條指向**資料夾外面**的符號連結,再跑一次
        --apply。舊寫法 shutil.copy2(src, dst + '.part') 會跟著連結
        把外面那個檔覆蓋掉;現在的 mkstemp 拿到的是隨機名字,碰不到它。
        同一趟還做正向對照(備份真的生出來、字真的改到了),
        不然「外面那個檔沒被動到」有可能只是因為整支根本沒跑
      · 備份檔本身、以及字串表本身是符號連結:兩種都必須當場拒絕,
        而且連結指到的那個檔一個位元組都不可以變
      · 複驗四件事的第四件(沒點名的字串被寫壞了):把 write_slots 暫時換成
        一個順便弄髒一條沒點名字串的版本,模擬「檔案真的被寫壞了」。
        必須當場停下來、自動還原、丟 DataError。**這一道是補的**:
        2026-09-05 先寫好「四件全擋」才發現自我測試裡沒有東西咬得到它 ——
        把那一件拿掉,27 道照樣全綠。防線加了沒配餌,等於沒加
      · 還原換檔的那一步失敗(把 os.replace 換成會丟例外的假貨):
        正本必須原封不動,而且不可以留下暫存檔。舊寫法 copy2(bak, dst)
        那一刀下去正本當場被截成 0,根本沒有 os.replace 可以攔
    2026-09-06 又加了一組,並且拒絕在 python -O 下跑:
      · --restore 的**目的地**(要被還原的那個遊戲檔)是一條符號連結:
        要當場拒絕,連結指到的那個檔一個位元組都不可以變。
        寫入的目的位置有三種(遊戲檔、備份檔、還原目標),前兩種本來就有餌,
        這一道補上第三種。外面那個檔刻意做成跟備份一樣長,
        不然「長度必須相同」那一道會先攔下來,餌就咬不到連結那一道
      · python -O 會把 assert 全部拿掉,這一段的正向檢查幾乎都是 assert ——
        真的跑下去會一路印到「全部通過」。所以 -O 直接拒絕,離開碼 2

    符號連結那幾道在建不了連結的系統(Windows 沒開開發者模式)上會跳過,
    而且**會印出來說跳過了**,不會默默當成通過。所以總道數是算出來的,
    不是寫死的 —— 寫死的數字改了程式就會過期。

    餌會失效而沒有人發現(2026-08-29 本站踩過:防線壞了測試照樣全綠),
    所以正向與反向都要有。
    """
    # ⚠️ python -O 會把整支程式裡的 assert **全部拿掉**。這一段的正向檢查
    #    幾乎都是 assert,拿掉之後測試會一路跑到最後印「全部通過」——
    #    綠燈是假的。所以 -O 直接拒絕跑,不留這個假綠的窗口。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    import io
    import contextlib
    total, baits = 17, 10          # 上面 docstring 說的那一段,下面才開始加
    pairs = [(12, 'Play Now'), (627, 'Quit'), (13, 'Game Modes')]
    blob = _fake_loc(pairs)
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'data'))
    p = os.path.join(d, 'data', 'FEENG.LOC')
    open(p, 'wb').write(blob)

    raw, slots = loc_slots(p)
    assert raw is not None, '自造的字串表讀不出來 —— 測試本身壞了'
    assert {s: t for s, (_a, _b, t) in slots.items()} == dict(pairs), '讀出來的文字不對'
    for sid, txt in pairs:
        a, b, _t = slots[sid]
        assert budget_chars(a, b) == len(txt), '預算算錯:%d' % sid

    # 這裡開始是正向:先證明「正常流程真的會做到承諾的事」。
    # 少了正向,反向餌可能是「因為整支都壞了」才過的。
    # 改短:長度不變、別條不動
    new = write_slots(raw, slots, {12: '打'})
    assert len(new) == len(raw), '長度變了 —— 原地覆寫的前提破了'
    open(p, 'wb').write(new)
    _r2, s2 = loc_slots(p)
    assert s2[12][2] == '打', '改完讀回來不對'
    assert s2[627][2] == 'Quit' and s2[13][2] == 'Game Modes', '沒點名的字串被動到了'

    # 反向餌:改成同長要能過
    new2 = write_slots(raw, slots, {627: '離開嗎啊'})
    assert len(new2) == len(raw), '同長度也不該改變長度'
    # 反向餌:太長一定要被擋
    try:
        write_slots(raw, slots, {627: '這句話太長了放不下'})
    except DataError:
        pass
    else:
        raise AssertionError('太長的字串竟然寫得進去 —— 防線失效')
    # 反向餌:壞掉的檔要回 (None, {}) 不可以爆掉
    bad = os.path.join(d, 'data', 'BAD.LOC')
    open(bad, 'wb').write(b'NOTLOC' + b'\x00' * 40)
    assert loc_slots(bad) == (None, {}), '壞檔沒有被擋下來'
    assert loc_slots(os.path.join(d, 'nope.LOC')) == (None, {}), '不存在的檔應該回空的'

    # 反向餌:UTF-16 的中文一個字兩個位元組,預算不可以用位元組數算
    assert len('馬上開打'.encode('utf-16-le')) == 8, 'UTF-16 編碼假設變了'
    assert budget_chars(0, 20) == 8, '預算換算錯(20 bytes 應該是 8 個字)'
    # 反向餌:BMP 以外的字一個字要**兩個**編碼單位,而 Python 的 len() 只算一個。
    #   預覽如果拿 len() 當預算就會少算,那正是 2026-09-05 修掉的那個窗口。
    assert len('\U00021619'.encode('utf-16-le')) // 2 == 2, '非 BMP 的字應該佔兩個編碼單位'
    assert len('\U00021619') == 1, 'Python 的 len() 只算一個 —— 所以不能拿它當預算'

    # 反向餌:--restore 的「備份與正本長度必須相同」那一道(2026-09-05 補的)。
    #   餌故意只讓長度不同、結構完全正常(備份 = 完整檔案再多一個位元組),
    #   這樣結構那幾道都會放行,只有長度比得出來 —— 餌才咬得到那一道。
    live_before = open(p, 'rb').read()
    open(p + BAK_SUFFIX, 'wb').write(blob + b'\x00')
    try:
        cmd_restore(d)
    except DataError:
        pass
    else:
        raise AssertionError('長度對不上的備份竟然還原得下去 —— 防線失效')
    assert open(p, 'rb').read() == live_before, '被擋下來的時候檔案不可以被動到'

    # 正向:長度一樣的完整備份要真的還原得動 ——
    #   少了這一條,上面那個餌可能只是「整支都壞了」才過的。
    open(p + BAK_SUFFIX, 'wb').write(blob)
    with contextlib.redirect_stdout(io.StringIO()):
        cmd_restore(d)
    assert open(p, 'rb').read() == blob, '還原之後應該逐位元組回到原本的樣子'

    # ── 2026-09-05 加的三組。先準備一個「資料夾外面的檔」當受害者。 ──
    outside = tempfile.mkdtemp()
    victim = os.path.join(outside, 'victim.bin')
    KEEP = b'DO NOT TOUCH'
    open(victim, 'wb').write(KEEP)

    def _symlinks_work(where):
        """Windows 沒開開發者模式就建不了符號連結。建不了要**說**,不要裝作過了。"""
        probe = os.path.join(where, '.symlink-probe')
        try:
            os.symlink(os.path.join(where, 'nothing-here'), probe)
        except (OSError, NotImplementedError, AttributeError):
            return False
        os.remove(probe)
        return True

    if _symlinks_work(d):
        # 反向餌 A:舊寫法用得到的那幾個「猜得到的名字」先被連結佔住。
        os.remove(p + BAK_SUFFIX)                  # 讓它需要重新備份
        lures = (p + '.part', p + BAK_SUFFIX + '.part',
                 p + '.tmp', p + BAK_SUFFIX + '.tmp')
        for lure in lures:
            os.symlink(victim, lure)
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_set(d, {627: '掰'}, True)
        assert open(victim, 'rb').read() == KEEP, \
            '資料夾外面的檔被改到了 —— 暫存檔的名字被猜到並劫持'
        total += 1; baits += 1
        # 正向對照:這一趟真的有做事,不然上面那條可能只是因為整支沒跑。
        assert open(p + BAK_SUFFIX, 'rb').read() == blob, '備份沒有正確產生'
        assert loc_slots(p)[1][627][2] == '掰', '字沒有真的改到'
        total += 2
        for lure in lures:
            os.remove(lure)

        # 反向餌 B:備份檔本身是一條連結 —— 要當場拒絕,外面那個檔不可以動。
        os.remove(p + BAK_SUFFIX)
        os.symlink(victim, p + BAK_SUFFIX)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_set(d, {627: 'Bye'}, True)
        except DataError:
            pass
        else:
            raise AssertionError('備份檔是符號連結竟然照寫 —— 防線失效')
        assert open(victim, 'rb').read() == KEEP, '外面那個檔被當成備份寫掉了'
        os.remove(p + BAK_SUFFIX)
        total += 2; baits += 2

        # 反向餌 C:要改的字串表本身是一條連結 —— 同樣拒絕。
        d2 = tempfile.mkdtemp()
        os.makedirs(os.path.join(d2, 'data'))
        real = os.path.join(outside, 'REAL.LOC')
        open(real, 'wb').write(blob)
        os.symlink(real, os.path.join(d2, 'data', 'FEENG.LOC'))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_set(d2, {627: '嗨'}, True)
        except DataError:
            pass
        else:
            raise AssertionError('字串表是符號連結竟然照寫 —— 防線失效')
        assert open(real, 'rb').read() == blob, '順著連結改到資料夾外面的檔了'
        total += 2; baits += 2

        # 反向餌 F:--restore 的**目的地**(要被還原的那個遊戲檔)是一條連結。
        #   寫入的目的位置有三種:遊戲檔、備份檔、還原目標。A/B/C 咬前兩種,
        #   這一道咬第三種。外面那個檔刻意做成**跟備份一樣長**(只有最後一個
        #   位元組不同),不然長度那一道會先攔下來,這個餌就咬不到連結那一道。
        d3 = tempfile.mkdtemp()
        os.makedirs(os.path.join(d3, 'data'))
        real3 = os.path.join(outside, 'REAL3.LOC')
        same_len = bytes(blob[:-1]) + bytes([blob[-1] ^ 0xFF])
        open(real3, 'wb').write(same_len)
        p3 = os.path.join(d3, 'data', 'FEENG.LOC')
        os.symlink(real3, p3)
        open(p3 + BAK_SUFFIX, 'wb').write(blob)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_restore(d3)
        except DataError:
            pass
        else:
            raise AssertionError('要還原的檔是符號連結竟然照還原 —— 防線失效')
        assert open(real3, 'rb').read() == same_len, '順著連結還原到資料夾外面的檔了'
        total += 2; baits += 2
    else:
        print('  (這台機器建不了符號連結,跳過 9 道符號連結的餌)')

    # 反向餌 E:複驗那四件事,任何一件對不上都要停下來、自動還原、離開碼非 0。
    #   挑第四件(沒點名的字串)來咬,因為它最容易被寫成「只印數字不擋」——
    #   2026-09-05 之前正是如此:印完數字照樣印「完成」、離開碼 0。
    open(p, 'wb').write(blob)
    if os.path.lexists(p + BAK_SUFFIX):
        os.remove(p + BAK_SUFFIX)
    real_write = write_slots

    def _dirty(data, slots, changes):
        out = bytearray(real_write(data, slots, changes))
        a, _b, _t = slots[13]              # 13 沒被點名,弄髒它
        out[a:a + 2] = b'ZZ'
        return bytes(out)

    globals()['write_slots'] = _dirty      # cmd_set 是從模組 globals 找它的
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_set(d, {12: '打'}, True)
    except DataError:
        pass
    else:
        raise AssertionError('沒點名的字串被寫壞了竟然還印「完成」 —— 四道複驗沒有全擋')
    finally:
        globals()['write_slots'] = real_write
    assert open(p, 'rb').read() == blob, '複驗沒過的時候應該自動還原成動手前的樣子'
    total += 2; baits += 2

    # 反向餌 D:還原換檔的那一步失敗,正本必須原封不動、不可以留暫存檔。
    #   把 os.replace 換成會丟例外的假貨。舊寫法是 copy2(備份, 正本),
    #   那一刀下去正本當場被截成 0,根本走不到 os.replace ——
    #   所以這道餌測的正是「有沒有先寫暫存檔」。
    open(p, 'wb').write(blob)
    open(p + BAK_SUFFIX, 'wb').write(blob)
    live_before = open(p, 'rb').read()
    real_replace = os.replace

    def _boom(_a, _b):
        raise OSError('假裝換檔失敗(自我測試用)')

    os.replace = _boom
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_restore(d)
    except OSError:
        pass
    else:
        raise AssertionError('換檔失敗竟然沒有反應 —— 還原不是原子的')
    finally:
        os.replace = real_replace
    assert open(p, 'rb').read() == live_before, '還原失敗的時候正本被動到了'
    leftover = [x for x in os.listdir(os.path.join(d, 'data')) if '.restore-' in x]
    assert not leftover, '還原失敗留下了暫存檔:%s' % leftover
    total += 3; baits += 3

    print('自我測試:全部通過(%d 道檢查,其中 %d 道是反向餌)' % (total, baits))
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
