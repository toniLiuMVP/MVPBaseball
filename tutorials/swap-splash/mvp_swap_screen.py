#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_swap_screen.py —— 換掉遊戲的開機畫面 / 標題畫面 / 讀取畫面

    看有哪些畫面    python3 mvp_swap_screen.py "<遊戲資料夾>" --info
    匯出成 PNG      python3 mvp_swap_screen.py "<遊戲資料夾>" --export splash out.png
    換成你的圖      python3 mvp_swap_screen.py "<遊戲資料夾>" --import title mine.png
    真的寫入        (上面那行後面加 --apply)
    還原            python3 mvp_swap_screen.py "<遊戲資料夾>" --restore
    自我測試        python3 mvp_swap_screen.py --selftest

會動到遊戲檔的只有兩條路:「--import --apply」與「--restore」。
⚠️ --restore 不吃 --apply,備份過了檢查就會把 .screenbak 換回封裝檔(本站實測)。
--export 沒加 --apply 也會寫檔,但寫的是你指定的那個 PNG,遊戲檔一個位元組都不動。
   ⚠️ 這件事 2026-09-05 起有守門員把關:輸出路徑上已經有一個「不是 PNG」的檔
   就直接拒絕,不覆蓋。在那之前,把輸出檔名打成遊戲檔會當場把它蓋成 PNG。

⚠️ 這三個畫面各自在不同的封裝檔裡,尺寸與格式也不同(--info 會告訴你)。
   匯入的 PNG **尺寸必須完全相同**,不同就拒絕寫入,不會幫你縮放。

⚠️ 上面匯入的例子刻意寫 title 不寫 splash:**splash 這一張匯得出來、匯不回去**,
   連 --export 出來的那張原封不動匯回去也會被擋。實測數字與原因寫在下面
   「做不到的事」。title 與 loading 兩張匯得回去。

⚠️ 寫入採「附加」模式:舊資料留在原地,只改目錄表指到新位置。
   這是本站對 .big 的一貫紀律 —— 你不知道手上這份被前人疊過什麼。

它做什麼(一句話)
    把三張大圖的像素換成你自己的 PNG。不動版面檔、不動遊戲程式,
    只換封裝檔裡那一張圖的像素而已。

輸入
    · 遊戲資料夾(裡面要看得到 data 這個子資料夾)
    · 匯入時再加一張 PNG。8 位元色深的灰階 / RGB / 索引色 / 灰階+透明 / RGBA 都讀得進來;
      交錯式(interlaced)與 16 位元色深會被擋下來,訊息會告訴你原因。

輸出
    --info     把三個畫面的格式與尺寸印出來,不產生任何檔案
    --export   產生一張 32 位元 RGBA 的 PNG
    --import   不加 --apply 只印預覽;加了才會動到封裝檔

安全網在哪
    · 預設唯讀,但有一個例外:--import 沒有 --apply 一個位元組都不會寫進去,
      而 --restore 不吃 --apply,備份過了下面那幾道檢查就會還原
    · 第一次寫入前自動備份成 <封裝檔>.screenbak,而且備份是原子的:
      寫的是一個隨機命名的暫存檔,整份寫完 + fsync + 逐位元組比對過才改名,
      中途被中斷不會留下半截備份
    · **還原也是原子的**(2026-09-05 改):先在同一個資料夾寫一個暫存檔,
      驗完內容跟備份逐位元組相同,才用 os.replace 換上。所以還原途中被中斷時,
      遊戲檔只有兩種樣子 ——「還是改過的樣子」或「完整還原好了」,沒有第三種。
      在這之前是直接複製覆蓋,而複製的第一個動作就是把遊戲檔截成 0
    · 所有暫存檔的名字都是隨機的(tempfile.mkstemp,O_CREAT|O_EXCL),
      而且遊戲檔與備份檔只要是符號連結就直接拒絕 —— 名字猜得到的暫存檔
      會被人先放一條指到別處的連結佔住,寫下去就穿過去改到資料夾外面的檔
    · --restore 之前先驗備份的 BIGF 檔頭長度,對不上就不敢還原
    · --restore 一份壞掉不連累另外兩份:壞的那份跳過並單獨列出來,好的照樣還原。
      只要有任何一份沒還原成功,exit code 就是 1 不是 0
    · **寫入之後把那一項讀回來複驗**(2026-09-05 加):照目錄表重讀一次,
      解出來跟要寫的不一樣就自動用備份還原,而且 exit code 是 1 不是 0
    · --export 不覆蓋既有的非 PNG 檔案 —— 那條路刻意不做備份,覆蓋掉沒東西救得回來
    · 寫入是附加模式,舊資料原地不動,所以就算新資料是壞的,舊的也還在檔案裡
    · 按 Ctrl-C 會告訴你遊戲檔到底有沒有被動到(動到就給你還原指令),
      而且 exit code 是 130 不是 0

做不到的事(先說,免得你白忙)
    · 只處理 DXT1(0x60)與 32 位元 ARGB(0x7D)兩種格式,其他一律拒絕,不亂猜
    · **splash 這一張只匯得出來,匯不回去。** 本站手上六份 data 資料夾全部被擋,
      連 --export 出來的那張原封不動匯回去也一樣:
        splash 是 1024x1024 的兩份(本站測試機那份被前人疊過的安裝,
        以及測試機自己留的那份備份資料夾)
            → 「新像素有 524288 個位元組,原本是 524304」
        splash 是 512x512 的四份(剛安裝好的原版英文版、剛安裝好的原版繁體中文版、
        PK 版、另一份社群繁體中文化版)
            → 「新像素有 131072 個位元組,原本是 131088」
      差的永遠是 16 個位元組:splash.fsh 裡那一筆記錄自己宣告的長度,
      比「16 個位元組的記錄檔頭 + 寬*高/2 的像素」多 16 個位元組,
      而 dxt1_encode 固定只吐 寬*高/2,長度對不起來就被 fsh_replace_pixels 擋掉。
      那多出來的 16 個位元組印出來看全是 0,本站沒查出它們是什麼;
      但宣告的長度確實指到下一筆附加記錄的開頭(緊接著那一筆自己寫著
      EAGL64 metal bin attachment for runtime texture management),
      所以不是本站把邊界算錯。
    · ⚠️ 上面那條**不是**「DXT1 一律寫不回去」:同一套編碼器在 models.big 的臉皮上
      長度是對的 —— 本站測試機那份 models.big,讀得出來的 889 張 DXT1 臉皮,
      889 張都是「宣告長度 = 16 + 寬*高/2」,0 個例外。
      卡住的是 splash.fsh 這一筆記錄的長度欄位,不是 DXT1 這個格式
    · 不縮放、不轉格式、不旋轉。尺寸不同就拒絕寫入
    · 不改圖在畫面上的位置與大小(那寫在版面檔 .fel 裡,不是這一支的事)
    · --selftest 只驗檔案安全那幾道守門員(備份 / 還原 / 符號連結 / 輸出路徑),
      每一道都配一個餌。DXT1、QFS、SHPI 那些格式細節驗不到 ——
      那要有真的遊戲檔才驗得動
    · DXT1 是有損壓縮,匯出成 PNG 再原封不動匯回去,像素不保證逐位元組相同
      (原因見 _endpoint_candidates 的說明)
    · **開機大圖目前根本匯不回去。** 本站量得到的五份安裝(剛安裝好的英文原版、
      剛安裝好的中文原版、本站測試機那份 2023 模組版,以及歷史資料裡的 PK 版與
      NEW TC_PATCH123 版)的 splash.fsh,圖片記錄宣告的長度都比「記錄檔頭 16
      + 像素」多出 16 個位元組,而且那 16 個都是零。fsh_replace_pixels 的長度
      守門員因此一律拒絕,訊息長這樣:
          新像素有 131072 個位元組,原本是 131088
      (512x512 那四份是這個數字;測試機那份 1024x1024 是 524288 對 524304。
       差的都是 16。)--info 與 --export 不受影響。
      真的換得動的是標題頁與讀取畫面那兩張 32 位元的圖,而且那兩張是無損的
    · 換完之後遊戲畫面實際長什麼樣,本站沒有看過

─────────────────────────────────────────────────────────
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
─────────────────────────────────────────────────────────
"""

import os
import re
import sys
import zlib
import struct
import shutil
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

# ── 被改過的檔案清單(給 Ctrl-C 用)─────────────────────────────────
# 按下 Ctrl-C 的人最想知道的只有一件事:「我的遊戲檔現在是好的還是壞的?」
# 沒有這份清單就只能講模糊話。規則:**真的動到正本之後才登記**
# ——「附加寫入」寫下第一個位元組就算動到(檔案大小一變,檔頭那一欄就對不上了),
# 而還原是等 os.replace 成功之後才算,在那之前正本一個位元組都沒被碰過。
_TOUCHED = []


def _mark_touched(path):
    p = os.fspath(path)
    if p not in _TOUCHED:
        _TOUCHED.append(p)


def _symlink_complaint(path, what):
    """這個路徑是符號連結就回一句話,不是就回 None。

    ⚠️ 一定要用 os.path.islink / os.path.lexists,**不可以**用 os.path.exists:
       exists() 會穿過連結去問「另一頭在不在」,連結指到一個不存在的檔時
       它回 False —— 於是「這個名字沒被佔用」是假的,接著 open(..., 'wb')
       就會穿過連結,在資料夾外面生出一個檔(或蓋掉那裡的檔)。
    """
    if not os.path.islink(path):
        return None
    try:
        tgt = os.readlink(path)
    except OSError:
        tgt = '(讀不出來)'
    return ('%s(%s)是一個符號連結,指向 %s —— 本工具不在符號連結上寫東西。\n'
            '     寫下去會穿過連結去改「另一頭那個檔」,而那個檔不在本工具的\n'
            '     備份範圍內,弄壞了 --restore 也救不回來。\n'
            '     請把它換成真正的檔案,或直接對連結另一頭的那個資料夾跑本工具。'
            % (what, path, tgt))


def _same_bytes(a, b):
    """兩個檔逐位元組相同才回 True。先比大小,再一塊一塊往下讀。

    ⚠️ 不可以用 zip() 把兩邊拉在一起比 —— zip 會在短的那一邊停下來,
       寫到一半的檔反而會被判成「完全相同」。
    """
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        while True:
            x = fa.read(1 << 20)
            y = fb.read(1 << 20)
            if x != y:
                return False
            if not x:
                return True


def _new_temp_beside(dst, tag):
    """在 dst 那個資料夾裡開一個「別人搶不到」的暫存檔,回傳 (fd, 路徑)。

    ── 2026-09-05 改掉可預測的暫存檔名(上線前資安稽核 🔴)────────────────
    原本是 `part = dst + '.part'` 然後 shutil.copy2 過去。名字是**猜得到的**:
    只要有人先在那個資料夾放一個叫 `<目標>.part` 的符號連結指到資料夾外面,
    copy2 就會穿過它,把外面那個檔截成 0 再寫進去 —— 後面的 os.replace 只換掉
    連結本身,但外面那個檔在那之前就已經被蓋掉了。
    tempfile.mkstemp 用的是 O_CREAT|O_EXCL:名字先被佔走就直接失敗,
    而且它產生的名字帶隨機碼,事前放不了餌。權限也只有 0600,寫的過程中
    別人看不到半成品。

    暫存檔一定要跟 dst 在**同一個資料夾**:os.replace 只有在同一個檔案系統
    內才是原子的,丟到 /tmp 再搬回來就不是了。
    """
    d = os.path.dirname(os.path.abspath(os.fspath(dst))) or '.'
    return tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(os.fspath(dst)) + tag)


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    現在寫進去的是 mkstemp 開出來的唯一暫存檔(理由見 _new_temp_beside),
    而且完整寫完 + fsync + 逐位元組比對過,才改名成正式的備份檔名。
    中途被中斷時壞掉的是那個暫存檔,而且會被刪掉;
    正式那個名字要嘛還沒出現、要嘛就是完整的。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    for p, what in ((src, '要備份的那個檔'), (dst, '備份檔')):
        why = _symlink_complaint(p, what)
        if why:
            raise DataError(why)
    fd, part = _new_temp_beside(dst, '.backup-')
    try:
        with os.fdopen(fd, 'wb') as out:
            with open(src, 'rb') as f:
                shutil.copyfileobj(f, out, 1 << 20)
            out.flush()
            os.fsync(out.fileno())
        # 備份是最後一道防線,所以不只比大小,整份讀回來比一次。
        # 幾 MB 的檔案而已,而且一輩子只做第一次。
        if not _same_bytes(src, part):
            raise DataError('備份寫到一半就對不上了(%s)—— 沒有備份成功,'
                            '遊戲檔一個位元組都沒有動。磁碟空間夠嗎?' % dst)
        try:
            shutil.copystat(src, part)     # 修改時間與權限一起抄過去
        except OSError:
            pass                           # 抄不動只是備份的日期不好看,內容是對的
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
    # 符號連結的檢查要排在 exists() 之前:指到不存在的檔的連結,exists() 會說
    # 「找不到備份」,那句話是假的 —— 備份的名字明明被佔住了,只是佔它的是一條
    # 指到別處的連結。講錯原因會讓人往錯的方向找。
    for pth, what in ((bak, '備份檔'), (dst, '要還原的遊戲檔')):
        why = _symlink_complaint(pth, what)
        if why:
            raise SystemExit(why)
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
    # 備份被截斷時這一欄一定對不上。兩種位元組順序都接受,理由見 size_field_order。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道與第 4 道:語系檔與執行檔。
    # ⚠️ 這一支只動 .big,所以這兩段在本檔實際上跑不到。留著是因為
    #    這整段還原防線在本站多支腳本之間是同一份,要改就得一起改;
    #    有人把這一支複製去改別的檔案時,防線也還在。
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


def _do_copy(bak, dst):
    """真正的還原動作。**先寫暫存檔、驗完才換上**,正本不會有中間狀態。

    獨立成一支,是為了讓上面每一道檢查都以 return _do_copy(...) 收尾:
    檢查沒過就永遠走不到這裡,不會有「檢查完忘了 return」那種漏網。

    ── 2026-09-05 改成原子還原(上線前資安稽核 🔴)──────────────────────
    在這之前這裡是一行 `shutil.copy2(bak, dst)`。copy2 是「**先把 dst 截成
    0 bytes**,再一塊一塊寫進去」——「還原」這個動作本身就會先毀掉正本。
    只要複製途中發生 Ctrl-C、磁碟滿、外接碟被拔掉或程式崩潰,玩家的遊戲檔
    就停在 0 或半截,而他跑這一行的時機正是「遊戲已經開不起來」的時候。
    複驗擋得住「已經壞了」,擋不住「正在壞」。

    現在的順序是:
      1. 目標與備份都不可以是符號連結(理由見 _symlink_complaint)
      2. 在**正本那個資料夾**開一個 mkstemp 暫存檔,把備份寫進去
      3. flush + fsync,把權限從正本抄過來
      4. 大小相同 + 逐位元組相同(比完整長度,理由見 _same_bytes)
      5. 全過了才 os.replace 換上 —— 這一步是原子的,不會有中間狀態
    任何一步失敗都刪掉暫存檔,正本原封不動;正本的內容只有兩種可能:
    「還是改過的樣子」或「完整還原好了」。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    for pth, what in ((dst, '要還原的遊戲檔'), (bak, '備份檔')):
        why = _symlink_complaint(pth, what)
        if why:
            raise SystemExit(why)
    fd, tmp = _new_temp_beside(dst, '.restore-')
    try:
        with os.fdopen(fd, 'wb') as out:
            with open(bak, 'rb') as f:
                shutil.copyfileobj(f, out, 1 << 20)
            out.flush()
            os.fsync(out.fileno())
        # mkstemp 開出來的檔是 0600。不把權限抄回去的話,還原完的遊戲檔會變成
        # 只有自己讀得到 —— 遊戲本身跑得動,但這不是玩家原本的樣子。
        try:
            shutil.copymode(dst, tmp)
        except OSError:
            os.chmod(tmp, 0o644)
        if os.path.getsize(tmp) != os.path.getsize(bak):
            raise SystemExit(
                '還原寫到一半就對不上大小了(%d vs %d)—— **沒有動到 %s**,\n'
                '  它還是你跑這行之前的樣子。多半是磁碟空間不夠,清出空間再跑一次。'
                % (os.path.getsize(tmp), os.path.getsize(bak), dst))
        if not _same_bytes(bak, tmp):
            raise SystemExit(
                '還原寫出來的內容跟備份對不上 —— **沒有動到 %s**,'
                '它還是你跑這行之前的樣子。' % dst)
        os.replace(tmp, dst)           # 到這一步才真的換上,而且是原子的
        _mark_touched(dst)
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


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 兩個上限都是防呆:檔案自己宣告的數字不可以無限相信。一個被動過手腳的檔
# 可以宣稱「解壓後有 4 GB」或「目錄有一億項」,照著配置記憶體就當場把機器吃垮。
MAX_UNCOMPRESSED = 64 * 1024 * 1024     # QFS 解壓後的位元組上限
MAX_BIG_ENTRIES = 200000                # 封裝檔目錄項目數上限
# 備份用自己的副檔名,不叫 .bak。別課的腳本也會在同一個資料夾留備份,
# 名字撞在一起會互相覆蓋,而且還原的時候你分不出來是哪一課留的。
BACKUP_SUFFIX = '.screenbak'


# ─────────────────────────────────────────────────────────
#  QFS(EA 的壓縮格式,檔頭是 10 FB)
# ─────────────────────────────────────────────────────────
def qfs_decompress(data):
    """QFS(社群也叫它 RefPack)解壓。傳進來的不是 QFS 就原樣回傳。

    檔頭:第 0 個位元組是旗標,第 1 個固定 0xFB,這就是「10 FB」的由來。
    旗標的 bit0 決定「解壓後有多大」寫在哪裡:
        bit0 = 1   大小在 +0x06 起的 4 個位元組,壓縮資料從 +0x0A 開始
        bit0 = 0   大小在 +0x02 起的 3 個位元組,壓縮資料從 +0x05 開始
    這兩個長度欄位都是 big-endian,跟後面 BIGF 目錄一致,
    但跟 SHPI 內部那些欄位相反(那邊是 little-endian)。看錯就整個解不出來。
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

    def copy_back(offset, length):
        # 這一行擋的是「往回的距離」:至少要往回 1 個位元組,而且不能往回到
        # 還沒解出來的地方。它管的不是輸出總長度,總長度由下面那道擋。
        if not 0 < offset <= len(out):
            raise DataError('QFS 反向參照越界 offset=%d' % offset)
        src = len(out) - offset
        for _ in range(length):
            out.append(out[src]); src += 1
        # ⚠️ 只檢查檔頭宣稱的大小是不夠的:那是「檔案自己說的」。
        #    一個惡意檔可以宣稱很小(通過上面那道),再用反向參照無限吐資料,
        #    把記憶體吃光。實際輸出也必須有上限,而且上限就是它自己宣稱的大小。
        if len(out) > size:
            raise DataError('QFS 解出來的資料超過檔頭宣稱的 %d 位元組' % size)

    # 接下來一路讀「控制位元組」。看第一個位元組落在哪個值域就知道這是哪一種指令:
    #   0x00-0x7F  兩個位元組一組:抄 0-3 個原文,再往回 1-1024 複製 3-10 個
    #   0x80-0xBF  三個位元組一組:抄 0-3 個原文,再往回 1-16384 複製 4-67 個
    #   0xC0-0xDF  四個位元組一組:抄 0-3 個原文,再往回 1-131072 複製 5-1028 個
    #   0xE0-0xFB  只抄原文,一次 4 到 112 個(一定是 4 的倍數)
    #   0xFC-0xFF  結束,順便抄最後 0-3 個原文
    # 「往回複製」的距離是相對於「已經解出來的尾端」,所以邊解邊長,
    # 複製到自己剛剛才寫出去的位元組是正常的,重複的花紋就是這樣壓的。
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

    壓出來比 EA 原本的大(大約等於原始大小),但因為我們是接到檔尾,
    大一點沒有影響。換來的是速度快上千倍,而且不可能壓錯。
    """
    n = len(data)
    # ⚠️ 這個短檔頭只有 3 個位元組寫「解壓後大小」,上限 16,777,215。
    #    超過就會被無聲截成低 24 位元,壓出來的 QFS 會宣告一個錯的長度,
    #    接進封裝檔就是一項壞資料。2026-09-05 下餌實測(不碰任何遊戲檔):
    #      16,777,215 → 宣告 16,777,215,解回來一樣長 ✅
    #      16,777,216 → 宣告 0        ❌
    #      16,777,232 → 宣告 16       ❌
    #    本課三張圖解開後最大 2,097,296 bytes,現況碰不到這一條;
    #    擋在這裡是給「把這一段複製去改別的封裝檔」的人。
    if n > 0xFFFFFF:
        raise DataError('這一段有 %s 個位元組,超過 QFS 短檔頭能表示的 16,777,215 —— '
                        '拒絕壓縮,免得寫出一個長度是錯的封裝檔' % format(n, ','))
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
#  BIGF 封裝檔:讀目錄、接到檔尾
# ─────────────────────────────────────────────────────────
def size_field_order(path):
    """檔頭 +0x04 的「檔案總大小」是 little 還是 big endian。

    ⚠️ 這一欄兩種順序都遇得到,不能寫死,也不能照檔名或檔案大小猜。
       「哪個檔是哪一種」不是這個格式天生的性質,是看你手上這一份被誰重新打包過。
       本站以 BIGF 檔頭(不是副檔名)認過四份 data 資料夾:剛安裝好的原版英文版
       207 個封裝檔、剛安裝好的原版繁體中文版 205 個、PK 版 205 個,這三份全部
       是 little-endian,連它們裡面最大的兩個封裝檔 models.big(172,992,803 個
       位元組)與 frontend/portrait.big(109,291,217 個位元組)也是 little-endian。
       只有本站測試機那份疊過模組的 data 資料夾出現 big-endian:384 個封裝檔裡
       有 10 個是 big-endian,而且只落在 7 個檔名上:models.big、
       frontend/portrait.big、audio 底下的 pnamehdr.big 與 pnamedat.big、
       球場夜間檔 coornite.big、dodgnite.big、wrignite.big(夜間那三個各出現
       兩次,因為測試機留了一份球場備份資料夾)。這 7 個檔名在三份原版裡
       全部是 little-endian。
       所以不要照檔名或檔案大小記,讀出來是哪一種就照哪一種寫回去。
    """
    n = os.path.getsize(path)
    with open(path, 'rb') as f:
        raw = f.read(8)
    if len(raw) < 8:
        raise DataError('%s 太小,不像封裝檔' % os.path.basename(path))
    if struct.unpack('<I', raw[4:8])[0] == n:
        return '<'
    if struct.unpack('>I', raw[4:8])[0] == n:
        return '>'
    raise DataError('%s 的檔頭大小欄位跟實際檔案大小對不上 —— 這個檔可能已經損毀'
                    % os.path.basename(path))


def big_entries(path):
    """回傳 [(名稱, 目錄欄位位置, 資料 offset, 資料長度)]。

    目錄欄位位置留著,是為了之後只改那 8 個位元組,不必重寫整個目錄。
    """
    # BIGF 檔頭 16 個位元組:0-4 招牌 BIGF、4-8 檔案總大小、
    # 8-12 目錄項目數、12-16 目錄區大小。除了「檔案總大小」那一欄之外
    # 全部是 big-endian(那一欄兩種順序都遇得到,見 size_field_order)。
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            blob = head + f.read(count * 80 + 8192)
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))

    # 目錄項目沒有固定長度:每一項是 4 個位元組的 offset、4 個位元組的長度
    # (兩個都是 big-endian),接一個以 NUL 結尾的檔名。
    # 所以只能一項一項往前走,不能用乘法直接跳到第 n 項。
    items = []
    pos = 16
    for _ in range(count):
        if pos + 8 > len(blob):
            break                                   # 目錄比預估長,已讀到的就夠用
        field = pos
        off = int.from_bytes(blob[pos:pos + 4], 'big')
        size = int.from_bytes(blob[pos + 4:pos + 8], 'big')
        pos += 8
        end = blob.find(b'\x00', pos)
        if end < 0:
            break
        items.append((blob[pos:end].decode('latin-1', 'replace'), field, off, size))
        pos = end + 1
    return items


def read_entry(path, off, size):
    """照目錄給的 offset 與長度,把那一項的原始位元組讀出來。

    讀不滿就報錯,不回半截資料。半截的 QFS 解出來是垃圾,
    而垃圾一路往下傳只會在很後面才炸,那時候已經看不出問題出在這裡。
    """
    with open(path, 'rb') as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise DataError('目錄說這一項有 %d 個位元組,實際只讀到 %d' % (size, len(data)))
    return data


def append_entry(path, field_pos, blob):
    """把 blob 接到檔尾,只改該項目的目錄 8 bytes 與檔頭的 4 bytes。

    原本的資料一個位元組都不動 —— 所以就算新資料是壞的,舊資料還在檔案裡。
    """
    # 位元組順序一定要在寫入之前量:一旦接了資料上去,檔案大小就跟檔頭那一欄
    # 對不上了,那時候再問「是 little 還是 big」會變成兩邊都不成立。
    order = size_field_order(path)          # 一定要在改檔案之前先量
    why = _symlink_complaint(path, '要寫入的封裝檔')
    if why:
        raise DataError(why)
    # 新資料放在原本的檔尾,所以新的 offset 就是「現在的檔案大小」。
    new_off = os.path.getsize(path)
    with open(path, 'r+b') as f:
        f.seek(0, os.SEEK_END)
        f.write(blob)
        # 寫下第一個位元組就算動到正本了(檔案大小一變,檔頭那一欄就對不上),
        # 所以登記要在這裡,不是等整段做完 —— Ctrl-C 最可能落在這中間。
        _mark_touched(path)
        total = f.tell()
        f.seek(field_pos)
        f.write(struct.pack('>II', new_off, len(blob)))     # 目錄一律 big-endian
        f.seek(4)
        f.write(struct.pack(order + 'I', total))
        # 先確定資料真的落到磁碟,再回報成功。少了這一步,萬一當下斷電,
        # 目錄已經指到新位置而新資料還在快取裡,這個封裝檔就壞了。
        f.flush()
        os.fsync(f.fileno())
    return new_off


# ─────────────────────────────────────────────────────────
#  FSH(SHPI 容器):找到那張圖、換掉像素
# ─────────────────────────────────────────────────────────
# 名字後面那個數字是「一個像素幾個位元組」,全部是本站在剛安裝好的原版上量出來的。
# 2026-08-28 訂正:原本這張表有四格名字跟量到的位元組數對不上(0x6D 寫成 4 位元組、
# 0x7B 寫成 2 位元組、0x7D 寫成 3 位元組、RGB24 這個名字掛錯代號),
# 而且漏了 0x79 與 0x7F 兩個代號 —— 漏掉會讓下面的守門員把真實的圖擋掉。
# 2026-08-28 再訂正:0x79 原本叫 EMPTY_1x1,那是把「用途」寫成了「格式」。
FSH_FORMATS = {
    0x60: 'DXT1',        # 0.5  每 4x4 像素一個 8 位元組區塊
    0x61: 'DXT3',        # 1.0  每 4x4 像素一個 16 位元組區塊,前 8 個是透明度
    0x6D: 'ARGB16_4444', # 2.0  models.big 裡 18,287 張
    0x78: 'RGB16_565',   # 2.0  models.big 裡 10,512 張
    0x79: 'PAL4',        # 0.5  4 位元索引色,調色盤在緊接的 0x2A 區塊裡
                         #      2026-08-28 訂正:原本寫 EMPTY_1x1「永遠 1×1」。
                         #      uniforms.big 的 431 個空槽確實都是 1×1,但那是用途不是格式:
                         #      中文字型的字圖集就是 0x79,1024x512、正好 0.500 bytes/像素,
                         #      而 au20b_en.ffn 後面的 0x2A 調色盤正好 16 個項目(2的4次方)。
    0x7B: 'PAL8',        # 1.0  一個位元組是索引,調色盤在緊接的 0x2A 區塊裡
    0x7D: 'ARGB32',      # 4.0  剛安裝好的原版 portrait.big 2,391 張圖全部是這個
    0x7E: 'ARGB16_1555', # 外部文件說的,本站至今找不到樣本,無從實測
    0x7F: 'RGB24',       # 3.0  models.big 裡 45 張(g001-g045.fsh)
}
# 名字對齊 FSHTOOL 1.22(Denis Auroux, 2002)說明書列的格式表;
# 每像素位元組數是本站在剛安裝好的原版上自己量的,兩邊完全吻合。
# 那份說明書還有一條本站沒用到的規則:代號 +0x80 代表「這張圖本身是壓縮過的」。


def fsh_first_image(data):
    """回傳 (格式代號, 寬, 高, 像素起點, 像素終點)。只看第一筆記錄。

    SHPI 檔頭 16 個位元組:0-4 招牌 SHPI、4-8 檔案長度、8-12 圖片筆數、
    12-16 產生它的工具代號。之後是目錄,每一筆 8 個位元組:
    4 個位元組的標籤(就是 --info 印出來的 firs / lice / memc),
    再 4 個位元組的位移。**這一段全部是 little-endian**,
    跟外面 BIGF 目錄的 big-endian 相反,兩個混著看必錯。

    每張圖自己的記錄開頭也是 16 個位元組:
    第 0 個位元組是格式代號,第 1-3 個是這一塊資料的長度(3 個位元組,
    little-endian),+4 與 +6 各 2 個位元組是寬與高,像素從 +16 開始。
    +8 到 +16 那 8 個位元組這支腳本沒有用到,本站也沒有驗過它們是什麼。
    """
    if len(data) < 16 or data[:4] != b'SHPI':
        raise DataError('不是 SHPI 檔(開頭是 %r)' % data[:4])
    num = struct.unpack_from('<I', data, 8)[0]
    if num < 1:
        raise DataError('這個 SHPI 裡一張圖都沒有')
    off = struct.unpack_from('<I', data, 20)[0]         # 16 + 0*8 + 4
    if off + 16 > len(data):
        raise DataError('圖片記錄的檔頭不完整')
    code = data[off]
    if code not in FSH_FORMATS:
        raise DataError('沒見過的格式代號 0x%02X' % code)
    block_size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
    width = struct.unpack_from('<H', data, off + 4)[0]
    height = struct.unpack_from('<H', data, off + 6)[0]
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise DataError('圖片尺寸異常 %dx%d' % (width, height))
    # 像素從記錄開頭 +16 起。終點有三種判法,由可靠排到不可靠:
    #   1. 記錄自己宣告的長度(block_size 要大於 16 才算是真的有宣告)
    #   2. 沒宣告但後面還有第二張圖,就拿第二張的起點當這一張的終點
    #   3. 兩個都沒有,那就一路到檔尾
    # 這裡抓得準不準,直接決定寫回去時「新舊像素長度一不一樣」;
    # 長度不一樣 fsh_replace_pixels 會擋下來,所以不會默默寫壞,只會拒絕。
    # ⚠️ splash.fsh 就是卡在第 1 種判法:它宣告的長度比「16 + 寬*高/2」多 16。
    #    (本站測試機那份 splash 是 1024x1024,宣告 524320,而 16 + 寬*高/2 是 524304;
    #     剛安裝好的原版英文版與繁體中文版都是 512x512,宣告 131104,
    #     而 16 + 寬*高/2 是 131088。多出來的那 16 個位元組印出來看全是 0。)
    #    於是 end - start 永遠比 dxt1_encode 吐出來的 寬*高/2 多 16,匯入一定被擋。
    #    要讓它匯得回去,得先確定那 16 個位元組是什麼、該不該一起寫回去 ——
    #    沒確定之前不動這一段:寧可擋下來,也不要猜著寫。
    start = off + 16
    if block_size > 16:
        end = min(off + block_size, len(data))
    elif num > 1:
        end = min(struct.unpack_from('<I', data, 16 + 8 + 4)[0], len(data))
    else:
        end = len(data)
    return code, width, height, start, end


def fsh_replace_pixels(data, start, end, new_pixels):
    """把 [start, end) 這一段像素換掉,前後的位元組原封不動。

    長度一不一樣是這支腳本最重要的一道防線:SHPI 記錄裡的長度欄位、
    後面每一張圖的位移,全部是照原本的長度算出來的。
    只要差一個位元組,後面那些圖就整批對不上,所以這裡寧可直接拒絕。

    ⚠️ 下面那句「尺寸或格式不一致」對 splash 這一張是會誤導的:
    它的尺寸與格式其實都對,差的是那一筆記錄宣告的長度比像素多 16 個位元組
    (見 fsh_first_image 的說明)。看到 524288 對 524304、
    或 131072 對 131088 這兩組數字,就是那件事,不是你的圖有問題。
    """
    if len(new_pixels) != end - start:
        raise DataError('新像素有 %d 個位元組,原本是 %d —— 尺寸或格式不一致,拒絕寫入'
                        % (len(new_pixels), end - start))
    return data[:start] + new_pixels + data[end:]


# ─────────────────────────────────────────────────────────
#  DXT1:解碼與編碼
#
#  這一段只有**開機大圖那一張**用得到:SCREENS 裡的 splash,也就是
#  data/frontend/splash.big 的 splash.fsh。另外兩張(license.fsh 的 lice、
#  memcard.fsh 的 memc)是 32 位元的 0x7D,走下面另一條路,不經過這裡。
#  (本腳本不碰球員臉皮,models.big 從頭到尾沒有出現在 SCREENS 裡。)
#
#  DXT1 一張圖切成 4x4 的方塊,每塊只有 8 個位元組:
#    兩個底色(各 16 位元)+ 16 個 2 位元的索引
#  兩個底色會再內插出中間色,湊成調色盤,每個像素從裡面挑一個。
#
#  ⚠️ DXT1 有兩種模式,靠兩個底色誰大誰小決定:
#     c0 >  c1  四色模式:底色兩個 + 中間色兩個,全部不透明
#     c0 <= c1  三色模式:底色兩個 + 中間色一個,第四個索引代表**完全透明**
#  這是 DXT1 表達透明度的唯一辦法(它沒有獨立的透明度區塊)。
#  兩種模式在真的 splash.fsh 裡都遇得到,所以兩種都要能產生。
#
#  ⚠️ 尺寸不是固定的,不要把某一台量到的數字當通則。本站量到的 splash.fsh:
#     四份剛安裝好的安裝(英文版、中文版、PK 版、套過官方更新檔的那一份)
#     全部是 512x512;本站測試機那份是 1024x1024。格式兩邊都是 0x60。
#     所以 --import 之前先跑 --info,以它印出來的尺寸為準。
# ─────────────────────────────────────────────────────────
# 下面幾個是 DXT1 的零件。DXT1 的兩個底色是 16 位元的 565 格式:
# 紅 5 個位元、綠 6 個(人眼對綠色最敏感)、藍 5 個。
# 所以 8 位元的色值進出都要換算,而且換算本身就會掉精度。
def _clamp(v):
    """把算出來的色值壓回 0-255。外插出來的候選端點會超出這個範圍。"""
    return 0 if v < 0 else (255 if v > 255 else v)


def _dist(p, q):
    """兩個顏色差多少。用平方和不開根號(只拿來比大小,開根號是白花時間)。"""
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2


def _to565(r, g, b):
    """8 位元三色 → 16 位元 565。用四捨五入,不是直接把低位砍掉。"""
    return (((round(r * 31 / 255) & 0x1F) << 11) |
            ((round(g * 63 / 255) & 0x3F) << 5) |
            (round(b * 31 / 255) & 0x1F))


def _from565(c):
    """565 → 8 位元三色。乘 255 再除以該色的最大值,讓 0x1F 還原成 255。"""
    return (((c >> 11) & 0x1F) * 255 // 31,
            ((c >> 5) & 0x3F) * 255 // 63,
            (c & 0x1F) * 255 // 31)


def _palette(c0, c1, four):
    """把兩個底色展開成四格調色盤。

    四色模式的中間兩格是 1/3 與 2/3 的內插;三色模式只內插出中間那一格,
    第四格保留給「完全透明」,顏色寫什麼都不會被畫出來,所以填黑。
    """
    r0, g0, b0 = _from565(c0)
    r1, g1, b1 = _from565(c1)
    if four:
        return [(r0, g0, b0), (r1, g1, b1),
                ((2 * r0 + r1) // 3, (2 * g0 + g1) // 3, (2 * b0 + b1) // 3),
                ((r0 + 2 * r1) // 3, (g0 + 2 * g1) // 3, (b0 + 2 * b1) // 3)]
    return [(r0, g0, b0), (r1, g1, b1),
            ((r0 + r1) // 2, (g0 + g1) // 2, (b0 + b1) // 2), (0, 0, 0)]


def dxt1_decode(raw, w, h):
    """DXT1 → RGBA bytes

    一塊 8 個位元組:前 2 個是底色 c0、接著 2 個是 c1(都是 little-endian 的 565),
    後 4 個是 16 個像素各 2 個位元的調色盤索引,由低位往高位排,
    對應的像素順序是由左到右、由上到下。
    圖的寬高不是 4 的倍數時,最後一塊會有一部分落在圖外,那些位置直接跳過。
    """
    out = bytearray(w * h * 4)
    pos = 0
    for by in range((h + 3) // 4):
        for bx in range((w + 3) // 4):
            if pos + 8 > len(raw):
                break
            c0 = raw[pos] | (raw[pos + 1] << 8)
            c1 = raw[pos + 2] | (raw[pos + 3] << 8)
            lookup = (raw[pos + 4] | (raw[pos + 5] << 8) |
                      (raw[pos + 6] << 16) | (raw[pos + 7] << 24))
            pos += 8
            # 兩個底色誰大誰小,就決定了這一塊是四色還是三色模式。
            # 這是 DXT1 唯一的透明度開關,它沒有獨立的透明度區塊。
            four = c0 > c1
            pal = _palette(c0, c1, four)
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px; y = by * 4 + py
                    if x >= w or y >= h:
                        continue
                    i = py * 4 + px
                    idx = (lookup >> (2 * i)) & 0x03
                    r, g, b = pal[idx]
                    a = 0 if (not four and idx == 3) else 255
                    di = (y * w + x) * 4
                    out[di] = r; out[di + 1] = g; out[di + 2] = b; out[di + 3] = a
    return bytes(out)


def _endpoint_candidates(cols):
    """端點候選。

    DXT 解出來的方塊最多只有四種相異色,所以直接試遍所有配對就行(最多十組)。
    但端點不一定出現在像素裡 —— 方塊可能只用到中間的內插色。那種情況可以
    解回來:若 a、b 是 1/3 與 2/3 內插點,則 c0 = 2a - b、c1 = 2b - a。
    這幾個外插候選有沒有用,本站拿這一課自己的開機大圖量過(解出來、重編碼、
    再解一次,比對三個色通道完全相同的像素比例):
      剛安裝好的原版 512x512(英文版與中文版數字相同,歷史資料裡的
      PK 版與 NEW TC_PATCH123 版也是同一張)      66.4% → 89.2%
      本站測試機那份 2023 模組版 1024x1024        96.1% → 99.8%
    差多少要看那張圖長什麼樣,不是一個固定的數字。
    ⚠️ 這裡量的是「重編碼」,不是「寫回遊戲檔」:開機大圖目前會被長度
    守門員擋下來,見檔頭「做不到的事」那一條。
    """
    if len(cols) > 8:
        best = -1; pair = (cols[0], cols[0])
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                d = _dist(cols[i], cols[j])
                if d > best:
                    best, pair = d, (cols[i], cols[j])
        return [pair, (tuple(min(c[k] for c in cols) for k in range(3)),
                       tuple(max(c[k] for c in cols) for k in range(3)))]
    out = [(cols[i], cols[j]) for i in range(len(cols)) for j in range(i, len(cols))]
    for a, b in list(out):
        if a == b:
            continue
        for m, n, p, q in ((2, -1, a, b), (2, -1, b, a), (3, -2, b, a), (3, -2, a, b)):
            cand = tuple(_clamp(m * p[k] + n * q[k]) for k in range(3))
            out.append((p, cand)); out.append((q, cand))
    seen = set(); uniq = []
    for p in out:
        if p not in seen:
            seen.add(p); uniq.append(p)
    return uniq


def dxt1_encode(rgba, w, h):
    """RGBA bytes → DXT1。透明的像素用三色模式的索引 3 表達。

    一次處理 4x4 一塊,塊與塊之間互不相干,所以編碼順序跟解碼時完全一樣。
    圖的寬高不是 4 的倍數時,超出去的位置拿邊緣像素補(min(..., w - 1))。
    補邊緣比補黑色好:那些位置不會被畫出來,但會參與這一塊的取色。
    """
    out = bytearray()
    for by in range((h + 3) // 4):
        for bx in range((w + 3) // 4):
            px = []; al = []
            for py in range(4):
                for pxi in range(4):
                    x = min(bx * 4 + pxi, w - 1)
                    y = min(by * 4 + py, h - 1)
                    di = (y * w + x) * 4
                    px.append((rgba[di], rgba[di + 1], rgba[di + 2]))
                    al.append(rgba[di + 3])
            out += _encode_block(px, al)
    return bytes(out)


def _encode_block(px, alphas):
    """把一塊 4x4 編成 8 個位元組。

    做法是窮舉:可能的端點配對通通試一遍,算出每一組的誤差,取最小的。
    一塊只有 16 個像素、候選最多十幾組,窮舉比任何近似法都省事,而且不會猜錯。
    誤差為 0 時直接跳出,那代表這一塊本來就是 DXT1 解出來的,原封不動編回去。
    """
    # 透明度只有「有」跟「沒有」兩種,門檻取 128。DXT1 表達不了半透明。
    vis = [i for i in range(16) if alphas[i] >= 128]
    need3 = len(vis) < 16                       # 有透明像素就只能用三色模式
    if not vis:
        # 整塊都透明。照樣把顏色編進去,因為遊戲做雙線性過濾會採樣到透明像素的
        # 顏色,填黑會在邊緣暈出黑邊。
        vis = list(range(16)); need3 = True
    cols = sorted({px[i] for i in vis})

    # 兩個端點換算成 565 之後可能會撞成同一個值,那時候調色盤退化成單色,
    # 沒有模式可選(modes = [None]),整塊就填那一個顏色。
    best_err = None; best = None
    for a, b in _endpoint_candidates(cols):
        ca, cb = _to565(*a), _to565(*b)
        if ca == cb:
            modes = [None]
        elif need3:
            modes = [False]
        else:
            modes = [True, False]
        for four in modes:
            if four is None:
                c0 = c1 = ca
                lookup = 0
                if need3:
                    for k in range(16):
                        if alphas[k] < 128:
                            lookup |= 3 << (2 * k)
                err = sum(_dist(px[i], _from565(c0)) for i in vis)
            else:
                c0, c1 = (max(ca, cb), min(ca, cb)) if four else (min(ca, cb), max(ca, cb))
                pal = _palette(c0, c1, four)
                hi = 3 if four else 2            # 三色模式的索引 3 是透明,不能拿來配色
                lookup = 0; err = 0
                for k in range(16):
                    if need3 and alphas[k] < 128:
                        lookup |= 3 << (2 * k)
                        continue
                    bi = 0; bd = None
                    for pi in range(hi + 1):
                        d = _dist(px[k], pal[pi])
                        if bd is None or d < bd:
                            bd, bi = d, pi
                    if alphas[k] >= 128:
                        err += bd
                    lookup |= bi << (2 * k)
            if best_err is None or err < best_err:
                best_err, best = err, (c0, c1, lookup)
                if err == 0:
                    break
        if best_err == 0:
            break
    c0, c1, lookup = best
    return bytes((c0 & 0xFF, c0 >> 8, c1 & 0xFF, c1 >> 8,
                  lookup & 0xFF, (lookup >> 8) & 0xFF,
                  (lookup >> 16) & 0xFF, (lookup >> 24) & 0xFF))


# ─────────────────────────────────────────────────────────
#  PNG:自己讀、自己寫(只用內建的 zlib,不需要安裝任何套件)
# ─────────────────────────────────────────────────────────
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def png_write(path, rgba, w, h):
    """寫一張 8 位元 RGBA 的 PNG。只用內建的 zlib,不需要裝 Pillow。

    PNG 的每個區塊都是「4 個位元組長度 + 4 個位元組標籤 + 內容 + 4 個位元組 CRC」,
    長度與 CRC 都是 big-endian。這裡只寫最少的三塊:IHDR、IDAT、IEND。
    IHDR 那串 8, 6, 0, 0, 0 的意思是:每色 8 位元、色彩型別 6(RGBA)、
    標準壓縮、標準濾波、不交錯。
    """
    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload +
                struct.pack('>I', zlib.crc32(tag + payload) & 0xFFFFFFFF))
    # 每一列前面都要有一個「濾波型別」位元組。這裡固定選 0(不做預測),
    # 因為這張圖是要拿給人編輯的:壓得小不重要,寫得單純、不會出錯才重要。
    rows = bytearray()
    for y in range(h):
        rows.append(0)                                  # 每一列前面加一個 0 = 不做預測濾波
        rows += rgba[y * w * 4:(y + 1) * w * 4]
    data = (PNG_MAGIC
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(rows), 9))
            + chunk(b'IEND', b''))
    # 2026-09-05:原本是 open(path, 'wb') 直接寫。那有兩個問題 ——
    # 檔名是使用者打的、可預測,而且 'wb' 會先把既有的那個檔截成 0;
    # 寫到一半失敗(磁碟滿)就留下一張半截 PNG 佔著那個名字。
    # 改成寫在同資料夾的 mkstemp 暫存檔,fsync 完才 os.replace 換上。
    fd, tmp = _new_temp_beside(path, '.png-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)           # mkstemp 給的是 0600,PNG 是要拿去給人看的
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def png_read(path):
    """回傳 (rgba bytes, w, h)。支援 8 位元的灰階/RGB/索引/灰階+透明/RGBA,不支援交錯。"""
    # 2026-09-05:這兩個是這一課最常見的兩種輸入錯誤,原本會吐 Python
    # traceback(FileNotFoundError / zlib.error)。讀者是「會用修圖軟體」的人,
    # 不是會讀 traceback 的人。兩者都發生在任何寫入之前,檔案不會被弄壞。
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as e:
        raise DataError('讀不到 %s(%s)—— 檔名打對了嗎?'
                        '路徑裡有空白或中文的話,整個路徑要用引號包起來'
                        % (path, e.strerror or e))
    if data[:8] != PNG_MAGIC:
        raise DataError('%s 不是 PNG 檔' % os.path.basename(path))
    pos = 8
    w = h = depth = ctype = None
    idat = bytearray(); plte = None; trns = None
    while pos + 8 <= len(data):
        ln = struct.unpack_from('>I', data, pos)[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b'IHDR':
            w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', body)
            if depth != 8:
                raise DataError('只支援每色 8 位元的 PNG,這張是 %d 位元' % depth)
            if inter:
                raise DataError('不支援交錯式(interlaced)PNG,請另存成一般的 PNG')
        elif tag == b'PLTE':
            plte = body
        elif tag == b'tRNS':
            trns = body
        elif tag == b'IDAT':
            idat += body
        elif tag == b'IEND':
            break
    if w is None:
        raise DataError('這個 PNG 沒有 IHDR')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None:
        raise DataError('沒見過的 PNG 色彩型別 %d' % ctype)

    # IDAT 可能被切成好幾塊,要全部接起來再一次解壓。
    # 解出來不是純像素,而是「每列一個濾波型別位元組 + 一整列像素」。
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as e:
        raise DataError('%s 的影像資料解不開(%s)—— 這張 PNG 多半是半截的'
                        '(下載沒完成、或複製到一半被中斷)。請用修圖軟體重新存一次'
                        % (os.path.basename(path), e))
    stride = w * channels
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        # PNG 的五種預測濾波,每一列自己選一種
        if ft == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa = abs(b - c); pb = abs(a - c); pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise DataError('沒見過的 PNG 濾波型別 %d' % ft)
        out[y * stride:(y + 1) * stride] = line
        prev = line

    # 不管來源是哪一種色彩型別,一律攤平成「一個像素 4 個位元組」的 RGBA,
    # 後面的編碼器就只要認得這一種排法。
    rgba = bytearray(w * h * 4)
    for i in range(w * h):
        s = i * channels; d = i * 4
        if ctype == 6:
            rgba[d:d + 4] = out[s:s + 4]
        elif ctype == 2:
            rgba[d:d + 3] = out[s:s + 3]; rgba[d + 3] = 255
        elif ctype == 0:
            v = out[s]; rgba[d] = rgba[d + 1] = rgba[d + 2] = v; rgba[d + 3] = 255
        elif ctype == 4:
            v = out[s]; rgba[d] = rgba[d + 1] = rgba[d + 2] = v; rgba[d + 3] = out[s + 1]
        else:                                            # 索引色
            if plte is None:
                raise DataError('索引色 PNG 卻沒有調色盤')
            idx = out[s]
            rgba[d:d + 3] = plte[idx * 3:idx * 3 + 3]
            rgba[d + 3] = trns[idx] if (trns and idx < len(trns)) else 255
    return bytes(rgba), w, h

# ─────────────────────────────────────────────────────────
#  三個畫面各自住在哪
#
#  ⚠️ 這張表是量出來的,不是抄別人的說明書。
#     2007 年有一份社群工具的說明寫「開機畫面是遊戲根目錄的
#     00000000.256」—— 在本站測的這台機器上,整個遊戲目錄
#     一個 .256 都沒有,執行檔裡也找不到那個字串。
#     真正的線索在執行檔的符號表(FSPLASH / LEGAL / LOADING)
#     跟版面檔 fes_title.fel 裡:它寫 SH:CLICKME,...,lice,lice,
#     而 license.fsh 裡那張圖的名字就叫 lice。名字對上名字,
#     不是數量對上數量。
# ─────────────────────────────────────────────────────────
# 每一項是 (封裝檔的相對路徑, 封裝檔裡那一項的名字, 給人看的說明)。
# 路徑寫成斜線,用的時候才 split 出來交給 os.path.join,Windows 上一樣走得到。
SCREENS = {
    'splash':  ('data/frontend/splash.big',   'splash.fsh',
                '開機大圖(遊戲啟動時第一張)'),
    'title':   ('data/frontend/sushared.big', 'license.fsh',
                '標題頁 / 授權畫面用的圖'),
    'loading': ('data/frontend/suonly.big',   'memcard.fsh',
                '讀取中顯示的圖'),
}


def locate(gamedir, key):
    """回傳 (big 路徑, 這一項在目錄裡的欄位位置, 名稱, 資料 offset, 長度)。

    ⚠️ big_entries 回的是四元組 (名稱, 目錄欄位位置, offset, 長度)。
       欄位位置要留著,append_entry 只改那 8 個位元組。
    """
    rel, member, _ = SCREENS[key]
    path = os.path.join(gamedir, *rel.split('/'))
    if not os.path.isfile(path):
        raise DataError('找不到 %s —— 這個遊戲資料夾對嗎?' % rel)
    for name, field, off, size in big_entries(path):
        if name == member:
            return path, field, name, off, size
    raise DataError('%s 裡面沒有 %s' % (rel, member))


def decode_screen(gamedir, key):
    """回傳 (big 路徑, field_pos, 名稱, 解開後的 SHPI, 格式, 寬, 高, 像素起, 像素迄)

    --info、--export、--import 三個動作共用這一段:找到位置、把那一項讀出來、
    開頭兩個位元組是 10 FB 才解壓(不是就當它本來就沒壓),
    再從 SHPI 裡把第一張圖的規格量出來。
    三條路走同一段,所以你在預覽看到的規格,就是真的寫入時用的那一份。
    """
    path, field_pos, name, off, size = locate(gamedir, key)
    blob = read_entry(path, off, size)
    raw = qfs_decompress(blob) if blob[:2] == b'\x10\xfb' else blob
    code, w, h, s, e = fsh_first_image(raw)
    return path, field_pos, name, raw, code, w, h, s, e


def to_rgba(code, w, h, px):
    """把檔案裡的像素轉成統一的 RGBA,好交給 png_write。

    0x7D 這種未壓縮的圖,檔案裡的順序是 BGRA 不是 RGBA。
    這件事看錯的話畫面不會壞掉,只會紅藍對調,
    而且你多半會以為是自己那張圖有問題。
    """
    if code == 0x60:
        return dxt1_decode(px, w, h)
    if code == 0x7D:                       # 未壓縮 32 位元,檔案裡是 BGRA
        out = bytearray(w * h * 4)
        for i in range(w * h):
            b, g, r, a = px[i * 4:i * 4 + 4]
            out[i * 4:i * 4 + 4] = bytes((r, g, b, a))
        return bytes(out)
    raise DataError('這個畫面是 %s 格式,本工具目前只處理 DXT1 與 32 位元'
                    % FSH_FORMATS.get(code, '0x%02X' % code))


def from_rgba(code, w, h, rgba):
    """to_rgba 的反向。寫回去一定要用原本那一種格式,不能順便換格式。

    格式代號是從檔案裡讀出來的,不是使用者選的:換格式會連動到記錄裡的
    長度欄位與後面每一張圖的位移,那已經不是「換一張圖」的範圍了。
    """
    if code == 0x60:
        return dxt1_encode(rgba, w, h)
    if code == 0x7D:
        out = bytearray(w * h * 4)
        for i in range(w * h):
            r, g, b, a = rgba[i * 4:i * 4 + 4]
            out[i * 4:i * 4 + 4] = bytes((b, g, r, a))
        return bytes(out)
    raise DataError('不支援寫入 0x%02X' % code)


def cmd_info(gamedir):
    """--info:三個畫面各印一行。唯讀,連暫存檔都不會產生。

    某一個畫面讀不出來不影響另外兩個:每一個各自 try,壞掉的那個印警告。
    社群模組常常只換其中一張,一張壞掉不該讓另外兩張也看不到。
    """
    print('\n  代號       格式        尺寸          封裝檔')
    print('  ' + '-' * 66)
    for key in SCREENS:
        rel, member, desc = SCREENS[key]
        try:
            _, _, _, _, code, w, h, s, e = decode_screen(gamedir, key)
            fmt = FSH_FORMATS.get(code, '0x%02X' % code)
            print('  %-9s %-11s %5d x %-5d %s' % (key, fmt, w, h, member))
            print('  %-9s %s' % ('', desc))
        except DataError as err:
            print('  %-9s ⚠ %s' % (key, err))
    print('\n  匯出:--export <代號> <輸出.png>')
    print('  匯入:--import <代號> <你的.png>   (加 --apply 才真的寫)\n')
    return 0


def _refuse_to_clobber(out):
    """--export 的輸出路徑守門員。

    ⚠️ --export 這條路刻意不做備份(它本來就不該碰遊戲檔),所以它絕對不可以
       蓋掉一個「不是 PNG」的既有檔案 —— 蓋掉了沒有任何東西救得回來,
       連 --restore 都不行,因為這條路根本沒留 .screenbak。
    2026-09-05 實測(在複本上):把輸出檔名打成遊戲檔,
    4,194,592 bytes 的 sushared.big 當場變成 594,955 bytes 的 PNG,
    而且印「成功」、exit code 0、資料夾裡一個備份都沒有。
    判斷用**內容**不用副檔名:副檔名是使用者自己打的,騙得了人;
    開頭那 8 個位元組是檔案自己的,騙不了。
    """
    if os.path.isdir(out):
        raise DataError('%s 是一個資料夾,不是檔名 —— 請給一個 .png 結尾的檔名' % out)
    parent = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(parent):
        raise DataError('%s 這個資料夾不存在 —— 請先把它建好,或換一個路徑' % parent)
    # ⚠️ 2026-09-05 補:下面那個 os.path.exists 對「指到不存在的檔」的符號連結
    #    會回 False,於是這一整道守門員直接被繞過,而 open(out, 'wb') 會穿過
    #    連結,在資料夾外面把那個檔生出來/蓋掉。所以符號連結一律先擋。
    why = _symlink_complaint(out, '匯出的輸出路徑')
    if why:
        raise DataError(why)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        with open(out, 'rb') as f:
            head = f.read(8)
        if head != PNG_MAGIC:
            raise DataError(
                '%s 已經存在,而且它不是 PNG(開頭是 %r)—— 本工具不覆蓋它。\n'
                '     匯出請另外取一個 .png 的檔名。這一道是為了擋'
                '「不小心把輸出檔名打成遊戲檔」:--export 不做備份,蓋掉就沒了'
                % (out, head[:4]))


def cmd_export(gamedir, key, out):
    """--export:把畫面存成 PNG。遊戲檔唯讀,只會產生你指定的那一個 PNG。

    改圖請一律從這張匯出的圖開始改,不要自己開新檔:
    尺寸與格式都是從遊戲檔量出來的,自己開的很容易差幾個像素,匯入時就被擋。

    ⚠️「唯讀」是對**遊戲檔**說的,不是對你給的那個輸出路徑說的 —— 那個路徑
       本來就是要被寫出去的。所以寫之前先過 _refuse_to_clobber 這一道。
    """
    _, _, name, raw, code, w, h, s, e = decode_screen(gamedir, key)
    _refuse_to_clobber(out)
    rgba = to_rgba(code, w, h, raw[s:e])
    try:
        png_write(out, rgba, w, h)
    except OSError as err:
        raise DataError('寫不出 %s(%s)—— 那個位置可能是唯讀的,或磁碟滿了'
                        % (out, err.strerror or err))
    print('  %s(%s %dx%d)→ %s' % (name, FSH_FORMATS.get(code), w, h, out))
    print('  改完之後用 --import %s "%s" 放回去。尺寸不能變。' % (key, out))
    return 0


def cmd_import(gamedir, key, src, apply_it):
    """--import:把你的 PNG 換進去。沒有 --apply 就只印預覽。

    順序是刻意排的:先把原本那張解出來(拿到格式、尺寸、像素範圍),
    再讀你的 PNG,尺寸不合就在這裡停住。
    所有會失敗的檢查全部排在備份與寫入之前,所以失敗的時候檔案還沒被碰過。

    ⚠️ 2026-09-05 訂正:上面那句話原本是假的。「封裝檔頭大小欄位對不上」
       那一道埋在 append_entry 裡面,排在備份**後面** —— 於是一個已經寫壞的
       封裝檔會先被備份成 .screenbak(而備份只做第一次,那份壞的就固定下來了),
       才在下一行被擋掉。現在那一道搬到備份之前,這句話才是真的。
    """
    path, field_pos, name, raw, code, w, h, s, e = decode_screen(gamedir, key)
    rgba, nw, nh = png_read(src)
    if (nw, nh) != (w, h):
        raise DataError('你的圖是 %dx%d,這個畫面要 %dx%d —— 拒絕寫入,本工具不幫你縮放'
                        % (nw, nh, w, h))
    px = from_rgba(code, w, h, rgba)
    new_raw = fsh_replace_pixels(raw, s, e, px)
    packed = qfs_compress_literal(new_raw)
    print('  目標   %s → %s(%s %dx%d)' % (os.path.basename(path), name,
                                          FSH_FORMATS.get(code), w, h))
    print('  來源   %s' % src)
    print('  寫入後 %s 這一項會變成 %s bytes' % (name, format(len(packed), ',')))
    if not apply_it:
        print('\n  這是預覽,沒有動到任何檔案。確定要寫就加 --apply\n')
        return 0
    # 這一道要在備份之前跑:封裝檔本身已經壞掉的話,備份它只會把壞的那份定住。
    # 順便給一句指路 —— 原本的訊息只說「這個檔可能已經損毀」,沒說下一步。
    try:
        size_field_order(path)
    except DataError as err:
        raise DataError(
            '%s\n'
            '     這個封裝檔已經被動過或寫壞了,本工具不敢在上面接東西。\n'
            '     如果你之前用本工具改過它,現在跑 --restore 就能還原;\n'
            '     沒有本工具的備份就從你自己那份完整備份複製一個回來。' % err)
    # 備份只做第一次。第二次以後要保留最早那一份,
    # 不然改第二次就會拿「已經改過的檔」當備份,--restore 就還原不回原版了。
    bak = path + BACKUP_SUFFIX
    # ⚠️ 這裡要用 lexists 不是 exists(2026-09-05 補):備份檔的名字是猜得到的,
    #    有人先在那裡放一個指到別處的符號連結時,exists() 會說「不存在」
    #    (連結的另一頭不存在就回 False),於是備份會穿過連結寫到資料夾外面去。
    #    _atomic_copy 自己也擋一次,這裡先擋是為了讓訊息出現在動任何東西之前。
    why = _symlink_complaint(bak, '備份檔')
    if why:
        raise DataError(why)
    try:
        if not os.path.lexists(bak):
            _atomic_copy(path, bak)
            print('  已備份 → %s' % os.path.basename(bak))
        append_entry(path, field_pos, packed)
    except OSError as err:
        # 遊戲裝在 Program Files、或整包從光碟複製過來的,常常整個資料夾是唯讀的。
        # 原本這裡會吐 PermissionError 的 traceback,而且留下一個孤兒備份
        # 沒人告訴使用者它是好的還是壞的。
        raise DataError(
            '寫不進去(%s)。\n'
            '     %s 或它所在的資料夾是唯讀的。\n'
            '     遊戲檔一個位元組都沒有動;備份%s。\n'
            '     改成可以寫再跑一次:Windows 右鍵→內容→取消「唯讀」;'
            'macOS / Linux 用 chmod u+w'
            % (err.strerror or err, os.path.basename(path),
               ('已經做好了,而且是完整的(%s)' % os.path.basename(bak))
               if os.path.exists(bak) else '也還沒做成'))
    _verify_after_write(gamedir, key, new_raw, path, bak)
    print('  ✅ 寫好了。要還原就跑 --restore\n')
    return 0


def _verify_after_write(gamedir, key, expect_raw, path, bak):
    """寫完之後照著目錄表把那一項讀回來,對不上就自動還原,而且不會說成功。

    ── 2026-09-05 加(上線前資安稽核)──────────────────────────────────
    在這之前,append_entry 沒丟例外就直接印「✅ 寫好了」,沒有任何一行去確認
    「目錄現在指到的那段資料,解出來真的是我要寫的東西」。而這一支改的是**目錄
    指標**:寫錯的話舊資料其實還在檔案裡,只是沒人指得到它 —— 這種壞法從檔案
    大小、從 exit code 都看不出來,只有讀回來比對才看得到。

    這一趟是真的從磁碟重讀(locate → big_entries → read_entry → 解壓),
    走的跟遊戲讀它的路徑一樣,不是拿記憶體裡的變數自己比自己。

    對不上就用備份自動還原(這一步是安全的:備份是完整的,還原是原子的),
    然後 raise 讓 exit code 變 1。**絕對不可以只印一個 ❌ 然後 return 0** ——
    照著指令做的人不會去讀輸出,他只知道跑完了。
    """
    try:
        raw = decode_screen(gamedir, key)[3]
        bad = (raw != expect_raw)
        why = '讀回來的內容跟要寫進去的不一樣'
    except DataError as err:
        bad, why = True, str(err)
    if not bad:
        return
    msg = '寫完之後讀回來複驗沒過:%s —— 這一次寫入不算成功。' % why
    if os.path.lexists(bak):
        try:
            _restore_from_backup(bak, path)
            msg += ('\n     已經用備份把 %s 還原回原本的樣子了,遊戲可以照常開;'
                    '請把問題連同這段訊息回報。' % os.path.basename(path))
        except (SystemExit, OSError) as err:
            msg += ('\n     自動還原也沒成功(%s)。\n'
                    '     請手動跑:--restore;它沒救回來的話,'
                    '從你自己那份完整備份把 %s 複製回來。'
                    % (err, os.path.basename(path)))
    else:
        msg += ('\n     而且找不到備份 %s —— 請從你自己那份完整備份把 %s 複製回來。'
                % (os.path.basename(bak), os.path.basename(path)))
    raise DataError(msg)


def cmd_restore(gamedir):
    """--restore:三個封裝檔,只要有本工具留下的備份就還原。

    只認 .screenbak 這一個副檔名,不會去碰別課或別人留下的 .bak。
    每一份都要先過 _restore_from_backup 那幾道檢查,半截的備份不敢拿來用。

    ⚠️ 一份壞掉不可以連累另外兩份(2026-09-05 修)。
       _restore_from_backup 的守門是 raise SystemExit,而這個迴圈原本沒有接,
       SCREENS 的走訪順序又是 splash → title → loading —— 排在前面那份
       .screenbak 壞掉,後面兩份好的備份就永遠用不到。實測:三份備份只有
       splash 那份是半截的,結果三個封裝檔一個都沒還原。
       而人會跑 --restore 的時機,正是遊戲已經開不起來的時候:
       這時候能救幾個就救幾個,救不動的最後單獨列出來並說下一步。

    回傳值:全部還原成功是 0;只要有任何一份沒成功就是 1,
    好讓「有沒有全部救回來」在 exit code 上看得出來,不必去讀輸出。
    """
    n = 0
    bad = []
    for key in SCREENS:
        rel = SCREENS[key][0]
        path = os.path.join(gamedir, *rel.split('/'))
        bak = path + BACKUP_SUFFIX
        # lexists 不是 exists:備份檔的名字被一條指到別處的符號連結佔住時,
        # exists() 回 False 會讓這一份被靜靜跳過,使用者只看到「沒有找到備份」。
        # 用 lexists 走進去,由 _restore_from_backup 把真正的原因說出來。
        if not os.path.lexists(bak):
            continue
        try:
            _restore_from_backup(bak, path)
        except SystemExit as err:
            # 備份沒過檢查(半截、0 bytes、檔頭對不上),或還原後複驗對不上。
            bad.append((os.path.basename(path), str(err)))
            continue
        except OSError as err:
            # 目標檔或資料夾是唯讀的。原本這裡會吐 PermissionError 的 traceback。
            bad.append((os.path.basename(path),
                        '寫不進去(%s)。這個檔或它所在的資料夾是唯讀的 —— '
                        'Windows 右鍵→內容→取消「唯讀」,'
                        'macOS / Linux 用 chmod u+w,再跑一次。'
                        % (err.strerror or err)))
            continue
        print('  還原 %s' % os.path.basename(path))
        n += 1
    # ⚠️ 「一個都沒還原」有兩種完全不同的意思,不可以印同一句話:
    #    真的沒有備份 vs 備份找到了但全部沒過檢查。後者印「沒有找到備份」
    #    會讓人以為自己沒備份過,那是假的。
    if n:
        print('  共還原 %d 個檔' % n)
    elif bad:
        print('  一個都沒還原成功')
    else:
        print('  沒有找到本工具做的備份')
    for name, why in bad:
        print('\n  ❌ %s 沒有還原成功:\n     %s' % (name, why.replace('\n', '\n     ')))
    if bad:
        # ⚠️ 這一句不可以寫死成「請改用你自己的備份」—— 上面兩種失敗的下一步不一樣:
        #    備份壞掉才需要換一份備份,唯讀寫不進去要做的是把檔案改成可寫。
        #    所以這裡只說「照它自己那一行做」,細節由上面各自那一行負責。
        print('\n  ⚠ 上面這 %d 個沒有還原成功,請照它各自那一行寫的處理;'
              '能還原的已經還原好了。\n'
              '    備份是壞的那幾個,把那個 %s 移開再跑一次,本工具就不會再碰它。\n'
              % (len(bad), BACKUP_SUFFIX))
        return 1
    print('')
    return 0


# ─────────────────────────────────────────────────────────
#  --selftest:不需要遊戲檔,只驗那幾道會決定「玩家的檔會不會壞」的守門員
# ─────────────────────────────────────────────────────────
def selftest():
    """每一道守門員都配一個**餌**:先製造出它應該擋下來的那個情況,再看它有沒有擋。

    ⚠️ 為什麼一定要下餌:一個永遠不會亮的檢查,跟一個好的檢查,在測試報告上
       長得一模一樣(全綠)。所以每一項都成對出現 —— 先一個「正常流程真的做得成」
       的陰性對照,再一個「該擋的真的被擋住,而且旁邊那個檔一個位元組都沒被動到」。

    這裡驗的都是**檔案安全**那幾道,不驗 DXT1/QFS 那些格式細節 ——
    那些要有真的遊戲檔才驗得動(見檔頭「做不到的事」)。
    """
    import random
    fails = []
    passes = [0]

    def check(name, ok, detail=''):
        if ok:
            passes[0] += 1
            print('  ✓ %s' % name)
        else:
            fails.append(name)
            print('  ✗ %s  %s' % (name, detail))

    def blob(n, seed):
        r = random.Random(seed)
        return bytes(r.getrandbits(8) for _ in range(n))

    root = tempfile.mkdtemp(prefix='mvp_swap_screen_selftest_')
    outside_dir = os.path.join(root, 'outside')
    work = os.path.join(root, 'work')
    os.makedirs(outside_dir)
    os.makedirs(work)
    OUT_SENTINEL = b'OUTSIDE-FILE-MUST-NOT-BE-TOUCHED\n' * 64

    def fresh_outside(name):
        pth = os.path.join(outside_dir, name)
        with open(pth, 'wb') as f:
            f.write(OUT_SENTINEL)
        return pth

    def outside_intact(pth):
        with open(pth, 'rb') as f:
            return f.read() == OUT_SENTINEL

    def leftovers(d, keep):
        return sorted(x for x in os.listdir(d) if x not in keep)

    def write(pth, data):
        with open(pth, 'wb') as f:
            f.write(data)
        return pth

    try:
        # ── 1. _atomic_copy:陰性對照(先證明正常流程真的做得成)────────────
        d1 = os.path.join(work, 'a1'); os.makedirs(d1)
        src = write(os.path.join(d1, 'x.big'), blob(200000, 1))
        bak = src + BACKUP_SUFFIX
        _atomic_copy(src, bak)
        check('備份:正常流程做得出一份逐位元組相同的備份',
              os.path.exists(bak) and _same_bytes(src, bak))
        check('備份:做完之後資料夾裡沒有留下暫存檔',
              leftovers(d1, {'x.big', os.path.basename(bak)}) == [],
              leftovers(d1, {'x.big', os.path.basename(bak)}))

        # ── 2. 餌:有人先佔住「猜得到的暫存檔名」,而且它指到資料夾外面 ──────
        d2 = os.path.join(work, 'a2'); os.makedirs(d2)
        src = write(os.path.join(d2, 'x.big'), blob(120000, 2))
        bak = src + BACKUP_SUFFIX
        victim = fresh_outside('victim_backup_part')
        os.symlink(victim, bak + '.part')           # 舊版寫的就是這個名字
        _atomic_copy(src, bak)
        check('備份餌①:被預先放了 <備份檔>.part 符號連結,資料夾外那個檔沒被動到',
              outside_intact(victim))
        check('備份餌①:備份本身照樣做得成而且是完整的',
              os.path.exists(bak) and _same_bytes(src, bak))

        # ── 3. 餌:備份檔那個名字本身就是一條指到外面的符號連結 ──────────────
        d3 = os.path.join(work, 'a3'); os.makedirs(d3)
        src = write(os.path.join(d3, 'x.big'), blob(50000, 3))
        bak = src + BACKUP_SUFFIX
        victim = fresh_outside('victim_backup_itself')
        os.symlink(victim, bak)
        try:
            _atomic_copy(src, bak)
            check('備份餌②:備份檔是符號連結時要拒絕', False, '沒有拒絕')
        except DataError:
            check('備份餌②:備份檔是符號連結時拒絕,而且外面那個檔沒被動到',
                  outside_intact(victim))

        # ── 4. 餌:dangling 符號連結會騙過 os.path.exists ─────────────────
        dang = os.path.join(work, 'dangling')
        os.symlink(os.path.join(outside_dir, 'no_such_file'), dang)
        check('符號連結:exists() 說「不存在」,但守門員抓得到(這正是舊版被繞過的那一格)',
              (not os.path.exists(dang)) and os.path.lexists(dang)
              and _symlink_complaint(dang, '測試') is not None)

        # ── 5. _do_copy:陰性對照(還原真的做得成、權限有保住)──────────────
        d5 = os.path.join(work, 'r1'); os.makedirs(d5)
        original = blob(300000, 5)
        bak = write(os.path.join(d5, 'x.big' + BACKUP_SUFFIX), original)
        dst = write(os.path.join(d5, 'x.big'), original + blob(4096, 55))
        os.chmod(dst, 0o640)
        del _TOUCHED[:]
        _do_copy(bak, dst)
        check('還原:正常流程真的把正本還原成備份的樣子', _same_bytes(bak, dst))
        check('還原:權限有從正本抄回去(0640)', (os.stat(dst).st_mode & 0o777) == 0o640,
              oct(os.stat(dst).st_mode & 0o777))
        check('還原:做完之後資料夾裡沒有留下暫存檔',
              leftovers(d5, {'x.big', os.path.basename(bak)}) == [],
              leftovers(d5, {'x.big', os.path.basename(bak)}))
        check('還原:成功之後有登記「這個檔動過了」(Ctrl-C 才講得出實話)',
              dst in _TOUCHED)

        # ── 6. 餌:還原寫到一半就斷掉(磁碟滿 / 拔碟 / Ctrl-C 都是這一格)────
        d6 = os.path.join(work, 'r2'); os.makedirs(d6)
        bak = write(os.path.join(d6, 'x.big' + BACKUP_SUFFIX), blob(200000, 6))
        before = blob(200000, 66)
        dst = write(os.path.join(d6, 'x.big'), before)
        real_copyfileobj = shutil.copyfileobj

        def half_then_die(fsrc, fdst, length=0):
            fdst.write(fsrc.read(4096))
            raise OSError(28, 'No space left on device')

        del _TOUCHED[:]
        shutil.copyfileobj = half_then_die
        try:
            _do_copy(bak, dst)
            broke = False
        except (OSError, SystemExit):
            broke = True
        finally:
            shutil.copyfileobj = real_copyfileobj
        with open(dst, 'rb') as f:
            after = f.read()
        check('還原餌①:寫到一半斷掉時會失敗收場', broke)
        check('還原餌①:正本一個位元組都沒被動到(舊版這裡會被截成半截)',
              after == before, '%d bytes' % len(after))
        check('還原餌①:沒有留下暫存檔',
              leftovers(d6, {'x.big', os.path.basename(bak)}) == [],
              leftovers(d6, {'x.big', os.path.basename(bak)}))
        check('還原餌①:失敗就不可以登記成「動過了」', dst not in _TOUCHED)

        # ── 7. 餌:最後那一步 os.replace 自己失敗 ────────────────────────
        d7 = os.path.join(work, 'r3'); os.makedirs(d7)
        bak = write(os.path.join(d7, 'x.big' + BACKUP_SUFFIX), blob(80000, 7))
        before = blob(80000, 77)
        dst = write(os.path.join(d7, 'x.big'), before)
        real_replace = os.replace

        def boom(a, b):
            raise OSError(13, 'Permission denied')

        del _TOUCHED[:]
        os.replace = boom
        try:
            _do_copy(bak, dst)
            broke = False
        except (OSError, SystemExit):
            broke = True
        finally:
            os.replace = real_replace
        with open(dst, 'rb') as f:
            after = f.read()
        check('還原餌②:換檔那一步失敗時會失敗收場', broke)
        check('還原餌②:正本原封不動', after == before)
        check('還原餌②:沒有留下暫存檔',
              leftovers(d7, {'x.big', os.path.basename(bak)}) == [],
              leftovers(d7, {'x.big', os.path.basename(bak)}))
        check('還原餌②:失敗就不可以登記成「動過了」', dst not in _TOUCHED)

        # ── 8. 餌:寫出來的東西跟備份不一樣(複驗那一道)────────────────────
        d8 = os.path.join(work, 'r4'); os.makedirs(d8)
        bak = write(os.path.join(d8, 'x.big' + BACKUP_SUFFIX), blob(90000, 8))
        before = blob(90000, 88)
        dst = write(os.path.join(d8, 'x.big'), before)

        def wrong_bytes(fsrc, fdst, length=0):
            fdst.write(b'\x00' * 90000)

        shutil.copyfileobj = wrong_bytes
        try:
            _do_copy(bak, dst)
            blocked = False
        except SystemExit:
            blocked = True
        finally:
            shutil.copyfileobj = real_copyfileobj
        with open(dst, 'rb') as f:
            after = f.read()
        check('還原餌③:寫出來的內容跟備份對不上時要擋下來', blocked)
        check('還原餌③:擋下來之後正本原封不動', after == before)

        # ── 9. 餌:還原的目標是一條指到資料夾外面的符號連結 ──────────────────
        d9 = os.path.join(work, 'r5'); os.makedirs(d9)
        bak = write(os.path.join(d9, 'x.big' + BACKUP_SUFFIX), blob(1000, 9))
        victim = fresh_outside('victim_restore_target')
        os.symlink(victim, os.path.join(d9, 'x.big'))
        try:
            _do_copy(bak, os.path.join(d9, 'x.big'))
            blocked = False
        except SystemExit:
            blocked = True
        check('還原餌④:目標是符號連結時要拒絕', blocked)
        check('還原餌④:資料夾外那個檔沒被動到', outside_intact(victim))
        # 餌:備份檔的名字被一條「指到不存在的檔」的符號連結佔住。
        # 這一格驗的是**訊息有沒有講對原因** —— exists() 會說「找不到備份」,
        # 那是假的:名字明明被佔住了。講錯原因會讓人往錯的方向找。
        d9b = os.path.join(work, 'r6'); os.makedirs(d9b)
        dst = write(os.path.join(d9b, 'x.big'), blob(1000, 96))
        os.symlink(os.path.join(outside_dir, 'never_created'),
                   os.path.join(d9b, 'x.big' + BACKUP_SUFFIX))
        try:
            _restore_from_backup(os.path.join(d9b, 'x.big' + BACKUP_SUFFIX), dst)
            said = '(沒有拒絕)'
        except SystemExit as err:
            said = str(err)
        check('還原餌⑤:備份檔是 dangling 符號連結時,說的是「符號連結」不是「找不到備份」',
              '符號連結' in said, said.split('\n')[0])

        # ── 10. 半截備份:陰性對照 + 餌(這一道 2026-08-30 就有,一起回歸驗)──
        d10 = os.path.join(work, 'b1'); os.makedirs(d10)
        payload = blob(40000, 10)
        good = b'BIGF' + struct.pack('<I', 8 + len(payload)) + payload
        bak = write(os.path.join(d10, 'x.big' + BACKUP_SUFFIX), good)
        dst = write(os.path.join(d10, 'x.big'), good + b'appended')
        _restore_from_backup(bak, dst)
        check('半截備份:完整的 BIGF 備份還原得動(陰性對照)', _same_bytes(bak, dst))
        write(bak, good[:len(good) // 8])           # 砍成前 1/8
        dst = write(os.path.join(d10, 'x.big'), good + b'appended')
        before = good + b'appended'
        try:
            _restore_from_backup(bak, dst)
            blocked = False
        except SystemExit:
            blocked = True
        with open(dst, 'rb') as f:
            after = f.read()
        check('半截備份餌:被砍成 1/8 的備份要擋下來', blocked)
        check('半截備份餌:擋下來之後正本原封不動', after == before)

        # ── 11. --export 的輸出路徑守門員 ───────────────────────────────
        d11 = os.path.join(work, 'e1'); os.makedirs(d11)
        _refuse_to_clobber(os.path.join(d11, 'new.png'))       # 不存在 → 放行
        png_ok = write(os.path.join(d11, 'old.png'), PNG_MAGIC + b'whatever')
        _refuse_to_clobber(png_ok)                             # 既有 PNG → 放行
        check('匯出:不存在的路徑與既有 PNG 都放行(陰性對照)', True)
        notpng = write(os.path.join(d11, 'game.big'), b'BIGF' + b'\x00' * 100)
        try:
            _refuse_to_clobber(notpng)
            check('匯出餌①:輸出檔名打成遊戲檔要拒絕', False, '沒有拒絕')
        except DataError:
            check('匯出餌①:輸出檔名打成遊戲檔會被拒絕', True)
        dang_out = os.path.join(d11, 'trap.png')
        os.symlink(os.path.join(outside_dir, 'not_created_yet'), dang_out)
        try:
            _refuse_to_clobber(dang_out)
            check('匯出餌②:指到外面的 dangling 符號連結要拒絕(舊版 exists() 會放行)',
                  False, '沒有拒絕')
        except DataError:
            check('匯出餌②:指到外面的 dangling 符號連結會被拒絕', True)

        # ── 12. png_write:原子寫出 + 兩個餌 ────────────────────────────
        d12 = os.path.join(work, 'p1'); os.makedirs(d12)
        rgba = bytes((x * 7 + y * 3) & 0xFF for y in range(4) for x in range(4 * 4))
        out = os.path.join(d12, 'a.png')
        victim = fresh_outside('victim_png_part')
        os.symlink(victim, out + '.part')
        png_write(out, rgba, 4, 4)
        back, bw, bh = png_read(out)
        check('匯出:寫出來的 PNG 讀得回來,而且像素一樣', (back, bw, bh) == (rgba, 4, 4))
        check('匯出餌③:被預先放了 <輸出>.part 符號連結,外面那個檔沒被動到',
              outside_intact(victim))
        out2 = os.path.join(d12, 'b.png')
        victim2 = fresh_outside('victim_png_target')
        os.symlink(victim2, out2)
        png_write(out2, rgba, 4, 4)
        check('匯出餌④:輸出路徑本身是符號連結時,寫的是連結那個名字,不是穿過去寫外面',
              outside_intact(victim2) and not os.path.islink(out2))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print('')
    if fails:
        print('  ❌ %d 項沒過:%s' % (len(fails), '、'.join(fails)))
        return 1
    print('  ✅ 全部 %d 項通過' % passes[0])
    return 0


def main():
    """命令列入口。先擋掉明顯給錯的路徑與代號,再分派到四個動作去。

    回傳值就是 exit code:0 成功、1 是檔案內容不如預期(DataError,
    以及 --restore 有任何一份沒還原成功)、2 是參數給錯了。
    分開是為了讓看輸出的人分得出「我打錯了」
    跟「這個遊戲資料夾有問題」,這兩件事的下一步完全不同。
    """
    ap = argparse.ArgumentParser(description='MVP Baseball 2005 開機/標題/讀取畫面替換工具')
    # gamedir 改成可省略,只是為了讓 --selftest 不必硬塞一個假路徑進來。
    # 其他四個動作照舊一定要給,沒給就在下面擋掉並回 2,指令用法一個字都沒變。
    ap.add_argument('gamedir', nargs='?', help='遊戲資料夾(裡面要有 data 這個子資料夾)')
    ap.add_argument('--info', action='store_true', help='看有哪些畫面、各是什麼規格')
    ap.add_argument('--export', nargs=2, metavar=('代號', '輸出.png'))
    ap.add_argument('--import', nargs=2, metavar=('代號', '來源.png'), dest='imp')
    ap.add_argument('--apply', action='store_true', help='真的寫入(不加只做預覽)')
    ap.add_argument('--restore', action='store_true',
                    help='還原本工具做的備份(壞掉的那份會跳過,其它照樣還原)')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試(不需要遊戲檔,只驗那幾道安全守門員)')
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.gamedir:
        print('  ❌ 要給遊戲資料夾。例:python3 %s "<遊戲資料夾>" --info'
              % os.path.basename(__file__))
        return 2
    # 先確認這真的是遊戲資料夾。路徑給錯是最常見的錯,
    # 在這裡擋下來,比後面丟一句「找不到 splash.big」好懂得多。
    if not os.path.isdir(os.path.join(a.gamedir, 'data')):
        print('  ❌ %s 底下沒有 data 資料夾,這不像是遊戲資料夾' % a.gamedir)
        return 2
    # 代號打錯也在這裡擋,而且把可用的三個印出來。
    for key in (a.export[0] if a.export else None, a.imp[0] if a.imp else None):
        if key is not None and key not in SCREENS:
            print('  ❌ 沒有「%s」這個畫面。可用的是:%s' % (key, '、'.join(SCREENS)))
            return 2
    try:
        if a.restore:
            return cmd_restore(a.gamedir)
        if a.export:
            return cmd_export(a.gamedir, a.export[0], a.export[1])
        if a.imp:
            return cmd_import(a.gamedir, a.imp[0], a.imp[1], a.apply)
        return cmd_info(a.gamedir)
    except DataError as err:
        print('  ❌ %s' % err)
        return 1
    except KeyboardInterrupt:
        # ⚠️ 按 Ctrl-C 的人只想知道一件事:「我的遊戲檔現在是好的還是壞的?」
        #    所以這裡分兩句話講,依據是 _TOUCHED —— 真的動到正本才會登記。
        #    兩種都 exit 130(被訊號中止的慣例),**不可以 exit 0**:
        #    照著教學跑批次的人只看 exit code,0 會被當成「做完了」。
        print('')
        if _TOUCHED:
            print('  ⚠ 你按了 Ctrl-C,而這些檔已經動過了:')
            for pth in _TOUCHED:
                print('      %s' % pth)
            print('    要回到原狀就跑:python3 %s "%s" --restore'
                  % (os.path.basename(__file__), a.gamedir))
        else:
            print('  ⚠ 你按了 Ctrl-C。遊戲檔一個位元組都沒有動到,直接再跑一次就好。')
        return 130


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
    sys.exit(main())
