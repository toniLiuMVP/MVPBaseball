#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_shrink_big.py — 把封裝檔裡「目錄沒指到的位元組」清掉

這是在解決什麼
-------------
社群傳了二十年的一條規矩:**球場檔超過 10 MB,中文版就會跳出**。
大家的理解是「球場做得太精緻、檔案太大」。

本站 2026-08-28 把一包社群球場實際量開,發現不是那樣:

    skydnite.big   檔案 18.44 MB,但目錄指到的內容只有 5.19 MB
                   → 其中 13.25 MB(72%)是**目錄根本沒指到的位元組**

而剛安裝好的原版,87 個球場檔的孤兒比例中位數是 **0.00%**(最高 0.01%)——
所以孤兒不是這個格式的性質,是**編輯過程留下來的殘骸**。

那些位元組是怎麼來的?因為安全的改法是「把新資料接到檔尾、只改目錄」
(本站其他課教的就是這個)。舊的那份資料還躺在原地,只是沒有人再指向它。
改一次留一份,改十次留十份。

這支腳本做的事:**把目錄指到的東西照原順序重新排好,把沒人指的丟掉。**
每一個項目的位元組原封不動,只有它們在檔案裡的位置變了。

⚠️ 這跟本站「不要重新打包」的鐵律衝突嗎?
   那條鐵律的理由是「你不知道孤兒資料有沒有用」。這裡的差別是:
   **剛安裝好的原版孤兒只有 0.00%**(中位數,最高 0.01%),證明這個格式本來就不該有孤兒。
   即使如此,這支腳本一樣會保留原檔,而且寫完會逐項比對位元組。
   最後還是要你進遊戲確認。

輸入是什麼、輸出是什麼
---------------------
輸入:一個 `.big` 封裝檔的路徑,就這樣。球場檔在 `<遊戲資料夾>/data/stadium/` 底下。
      不必先解開、不必準備別的檔案,腳本自己讀它的檔頭與目錄。

輸出分成四種,由參數決定,**預設那一種完全不寫檔**:

    (不加參數)          只印診斷:多大、幾個項目、目錄指到多少、孤兒多少
    --shrink            印「清完會變多小」的預覽,一樣不寫檔
    --shrink --apply    真的寫。旁邊多一份 `<原檔名>.shrinkbak`,原檔換成重排後的版本
    --apply             跟上面同一件事(單獨給 --apply 也會清,不必再加 --shrink)
    --restore           拿 `.shrinkbak` 蓋回原檔

安全網在哪(四層,由外往內)
--------------------------
1. **預設唯讀。** 不給參數就只是量。要動到檔案得自己打 --apply,不會誤觸。
2. **先備份再寫,而且備份是原子的。** 見 `_atomic_copy`:先寫一個**隨機名字**的暫存檔
   (tempfile.mkstemp,建在備份要放的那個資料夾裡)再換名,途中被中斷只會留下那個暫存檔,
   不會留下一個半截卻叫得出名字的 `.shrinkbak`。
   已經有備份就**保留最早那一份** —— 第二次執行不會把「原版的備份」蓋成「已經改過的版本」。
3. **新檔先寫暫存、驗過了才換名。** 內容寫進同一個資料夾裡一個隨機名字的暫存檔,
   flush + fsync,**接著就地把那個暫存檔重讀一次驗過**(2026-09-06 加,見 `_verify_pack`)——
   不過就整份丟掉,壞的那一份根本不會換上去,遊戲檔一個位元組都沒有動。
   驗過了才 os.replace 換過去,而「換名」與「登記已經換過了」是一段
   **不可中斷**的區塊(見 `_NoInterrupt`):Ctrl-C 落不進那條縫裡,
   所以收尾說的話一定跟磁碟上的狀態一致。
4. **換完再複驗一次。** 重新讀一次目錄,逐項比對「長度一樣」與「內容逐位元組相同」,
   再確認檔頭的大小欄跟實際檔案大小相符。**任何一項不過就當場自動從備份還原**,
   然後丟 DataError(結束碼 2)。
   還原那一步也有把關(見 `_restore_from_backup`):半截的備份會被擋下來,不會拿去蓋正本;
   而且還原本身也是原子的(見 `_do_copy`)—— 先寫暫存、比對雜湊,最後才換名,
   中途失敗正本原封不動。

這四層之外,還有三道「乾脆不動」的閘門
--------------------------------------
· **你指的那個名字是符號連結,而這一次會寫檔 → 直接拒絕。**(2026-09-06)
  `--apply` 與 `--restore` 一律停在這裡,結束碼 2。跟著連結寫下去等於替你決定
  去動資料夾**外面**的檔,而你打的那個路徑上看不出來。
  只是量的那兩條路(不加參數、`--shrink`)不受限制,會跟著連結走到本體去量,
  印給你複製的下一行指令也會指到本體。
· **目錄解析不完整就停下來。**(2026-09-05)檔頭宣告 N 筆而只解析得出 M 筆時,`big_entries`
  直接丟 DataError。少解析到的那幾筆會被當成沒人指到的位元組清掉,而複驗是同一個
  函式重讀的、一樣少那幾筆 —— 一個被清壞的檔會拿到「全部逐位元組相同 ✅」的綠燈。
· **重排之後不會變小就不寫。**(2026-09-05)孤兒排在第一筆資料之前的那一段清不掉(見下面
  「做不到的事」),那種檔連備份都不做,直接說「這個檔不用清」。

做不到的事(這一段比上面那一段重要)
-----------------------------------
· **不會讓「內容真的很多」的檔變小。** 孤兒不到 2% 時腳本會直說清了也省不了什麼。
  貼圖換成更大張的(第②種)、或是存回去時沒有重新壓縮(第③種),這兩種它都治不了。
  `cmd_check` 會試著幫你分辨是三種裡的哪一種,但那是線索不是判決。
· **孤兒不等於清得掉。** 目錄沒指到的位元組如果排在**第一筆資料的起點之前**,
  那一段跟檔頭與目錄一起原樣留著,這一課清不掉。實測 `data/frontend/igonly.big`
  孤兒 95.8%,重排之後反而多 1 個位元組;本站測試機 680 個封裝檔裡,
  「孤兒 ≥2% 且 ≥1 KB」的有 331 個,其中 104 個重排後不會變小。
  這種檔腳本會直接說「不用清」,不會白做一次備份與重寫。
· **不重新壓縮、不重新編碼任何東西。** 每一項的位元組原封不動,只有它在檔案裡的位置變了。
· **不判斷孤兒資料「有沒有用」。** 它只認一件事:目錄有沒有指向它。
  如果有哪個模組靠著「目錄沒指到、但位置寫死」的資料運作,這支會把那些位元組清掉。
  (本站在剛安裝好的原版與兩包社群球場上都沒見過這種用法,但沒見過不等於不存在。)
· **不碰遊戲程式,也不碰你的王朝存檔。** 只動你在指令裡指名的那一個 .big。
· **不保證遊戲跑得起來。** 複驗只證明位元組沒變,不證明遊戲讀得動 ——
  所以最後一步永遠是「進遊戲確認那座球場開得起來」。

自包含:整支腳本就是這一個檔,只用 Python 內建模組,不需要安裝任何套件。
⚠️ 2026-09-03 訂正:上面這句原本後面還掛著「連讀寫 PNG 都是自己做的」,那在這一支上不成立。
   這個檔從頭到尾沒有一行 PNG 的程式碼:拿 png 去搜 mvp_shrink_big.py,
   搜得到的只有這一段訂正本身。這一課只搬位置,不解圖也不改圖。
   下面那幾塊 FSH 碰的是 EA 自己的 SHPI/FSH 圖片格式,不是 PNG,
   而且如同 QFS 那一段開頭已經寫的,它們在本支沒有任何地方呼叫;
   檔頭的 import re 與 import zlib 也同樣沒有用到。
   「不需要安裝任何套件」那半句本來就是對的:這個檔 import 的
   argparse / hashlib / os / re / shutil / signal / struct / sys / tempfile / zlib
   全是 Python 自己就附的模組。
   (2026-09-06 補:這一行原本漏列 hashlib 與 tempfile 兩個,那時候它們就已經在
    import 了;signal 是這一輪為了「換名那一段不可中斷」新加的。)
   真的自己讀寫 PNG 的,是「換球員大頭照」「做一張新的球員臉皮」「換掉開機畫面」
   「換球隊隊徽」這四課的腳本。2026-09-03 在 site/tutorials/ 底下 29 支腳本上量,
   找得到 png_read 與 png_write 的就只有那四個檔。

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

def _refuse_if_symlink(p, what):
    """要寫的位置是符號連結就停下來,絕不跟著它走(2026-09-05 加)。

    ⚠️ **不可以用 os.path.exists() 判斷有沒有這個東西。** 連結還在、但它指向的檔案
       不存在時(dangling symlink),exists() 回的是 False —— 而那一行
       open(那個名字, 'wb') 照樣會沿著連結,在資料夾**外面**建出/蓋掉一個檔。
       這裡用 os.path.islink(走 lstat,不跟著連結),才看得到連結本身。
       (Windows 的 junction / mklink 這一輪還沒實測,不敢說這一行擋得住;
        擋得住的那一半是暫存檔改用 tempfile.mkstemp —— 那個名字別人猜不到,
        也就沒有先放一個連結在那裡等著的機會。)

    為什麼要有這一道:暫存檔與備份檔的名字如果可以被預測,別人(或某個
    模組管理器留下的殘骸)就能先在那個名字上放一個指到別處的連結。
    暫存檔那一半已經改用 tempfile.mkstemp 拿掉可預測性;
    正本與備份這兩個名字是使用者指定的、沒辦法隨機,所以改成「是連結就拒絕」。
    """
    p = os.fspath(p)
    if os.path.islink(p):
        raise DataError(
            '%s 是一個符號連結:%s\n'
            '  它指向:%s\n'
            '  跟著連結寫下去會動到資料夾外面的檔案,所以這裡直接停,一個位元組都不寫。\n'
            '  請把那個連結移走(或直接對真正的那個檔跑一次)之後再試。'
            % (what, p, os.path.realpath(p)))


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ── 2026-09-05 再修(唯讀稽核 🔴「可預測的 .part 會跟著符號連結走」)──────
    原本的暫存檔叫死名字 `<備份名>.part`,而且是用 shutil.copy2 寫的。
    那個名字**別人可以先佔住**:在同一個資料夾先放一個
    `<球場檔>.shrinkbak.part` 符號連結指到資料夾外面的某個檔,
    copy2 會沿著連結把外面那個檔先截成 0 再寫進去 ——
    後面的 os.replace 只換掉連結本身,但外面那個檔早就被蓋掉了。
    現在改成 tempfile.mkstemp(dir=備份要放的那個資料夾):名字是隨機的,
    而且是用 O_CREAT|O_EXCL 建出來的,佔不住也跟不到連結;
    換名之前多做一次 flush + fsync,確定內容真的落到磁碟。
    """
    # os.fspath 把 Path 與字串拉成同一種型別,下面的字串相加才不會爆掉。
    src, dst = os.fspath(src), os.fspath(dst)
    # 備份的名字是算出來的(正本 + 副檔名),沒辦法隨機 —— 所以改成「是連結就拒絕」。
    _refuse_if_symlink(dst, '備份要寫的位置')
    folder = os.path.dirname(os.path.abspath(dst)) or '.'
    # 暫存檔跟備份放同一個資料夾:os.replace 只有在同一個檔案系統上才是原子的。
    # 開頭那個點讓它在 macOS / Linux 的檔案總管裡是隱藏的,不會嚇到讀者。
    fd, part = tempfile.mkstemp(dir=folder, prefix='.' + os.path.basename(dst) + '.part-')
    try:
        with os.fdopen(fd, 'wb') as fdst:
            with open(src, 'rb') as fsrc:
                shutil.copyfileobj(fsrc, fdst)
            # 先把緩衝區推給作業系統,再要求它真的寫到碟上。
            fdst.flush()
            os.fsync(fdst.fileno())
        # copy2 = 複製內容 + 複製權限與時間,這一行補的是後半段。
        # 抄不到不該讓備份失敗(有些網路磁碟機/隨身碟不吃 chmod):
        # 那時候備份會沿用 mkstemp 給的 0600,比原檔更嚴,內容一樣是完整的。
        try:
            shutil.copystat(src, part)
        except OSError:
            pass
        # 換名這一步在同一個檔案系統上是原子的:要嘛整份就位,要嘛完全沒動。
        os.replace(part, dst)          # os.replace 是原子的
    except BaseException:
        # 收拾殘骸。這裡用 BaseException 而不是 Exception,是為了連
        # KeyboardInterrupt / SystemExit 都會走到 —— 按 Ctrl-C 一樣要清乾淨。
        try:
            os.remove(part)
        except OSError:
            pass
        # 清完照樣把原來那個例外丟出去,不可以吞掉:備份失敗必須讓上層知道。
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
    # 第 0 道:備份根本不在,就沒有「還原」這回事,直接說清楚。
    if not os.path.exists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    # 第 1 道:0 bytes。這是「備份到一半被中斷」最常見的樣子。
    n = os.path.getsize(bak)
    if n == 0:
        raise SystemExit(
            '備份是 0 bytes(多半是上次備份到一半被中斷),不敢拿它覆蓋 %s。' % dst)
    # 只讀開頭 8 個位元組就夠認出是哪一種檔:
    #   位移 0-4   四個字元的招牌(BIGF / LOCH / MZ 只有兩個字元)
    #   位移 4-8   BIGF 用來記「整個檔案有多長」的欄位
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    def _stop(why):
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 第 2 道(封裝檔):檔頭 +0x04 的四個位元組寫著「這個檔應該有多長」。
    # 截斷之後那個數字不會跟著變小,所以一比就露餡。
    # ⚠️ 這一欄的位元組順序兩種都遇得到(實測本機 295 個 BIGF:288 小端、7 大端),
    #    所以兩種都算過,任一種對得上就放行。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道(語系檔 .LOC):這種檔的結構是「檔頭 LOCH → 字串區 LOCL → 位移表 → 字串」。
    # 位移表在檔案中段、字串在最後面,所以截斷一定會讓「最後一條字串的位移」指到檔外。
    #   位移 16-20  小端 32 位元:LOCL 區塊從第幾個位元組開始(相對於檔頭那 16 bytes 之後)
    #   L+12~L+16   小端 32 位元:總共幾條字串
    #   L+16 起     每條 4 個位元組的位移,相對於 L
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

    # 第 4 道(Windows 執行檔):PE 的節區表寫著每一段內容在檔案裡的起點與長度。
    # 把「起點 + 長度」取最大值,那就是這個檔至少該有多長 —— 被截斷就一定超出去。
    #   位移 0x3C   小端 32 位元:PE 檔頭在第幾個位元組
    #   pe+6        小端 16 位元:節區數
    #   pe+20       小端 16 位元:選用檔頭有多長(節區表接在它後面)
    #   節區表每筆 40 bytes,其中 +16 是 raw size、+20 是 raw offset
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
    # (第 5 道)上面三道都是「認得出格式才擋得住」,認不出來的格式一樣要有底線。
    # 非 BIGF 的工具都是原地改(大小幾乎不變),所以「備份不到正本的一半」
    # 一定是出事了。BIGF 走接到檔尾的改法會越改越大,刻意不套這一條。
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


# 記「正本到底被換掉了沒有」。按 Ctrl-C 的時候要照實說 ——
# 沒換過才可以說「一個位元組都沒有動到」,換過了就得告訴人家怎麼回去。
# (2026-09-05 加。原本不管有沒有寫過都印同一句「已中斷。」,
#  換到一半被打斷的人會以為自己的球場檔還是原來那一份。)
#
# ⚠️ 2026-09-06 改成**三態**。兩態不夠用:os.replace 做完、還沒登記之前
#    那一瞬間被 Ctrl-C 打斷,收尾看到的還是「沒動過」,就會對著一個
#    **已經被換掉的正本**說「一個位元組都沒有動到」。
#      idle       還沒動過
#      replacing  正在換(下面的 _NoInterrupt 裝得上的話幾乎看不到,它是保險)
#      replaced   換過了
#    'what' 記的是哪一種換名('shrink' 清孤兒 / 'restore' 從備份還原)。
#
# ⚠️ 2026-09-11 再修:**這三個欄位一律用一次 `.update()` 寫完,不可以分成兩行。**
#    三態本身是對的,但登記的動作原本是「先寫 what/path、下一行才寫 phase」——
#    Ctrl-C 落在那兩行之間的話,what 已經是 'shrink' 而 phase 還停在 'idle',
#    收尾就照著 what 說「檔案**已經**換成清過的那一版了」,而 os.replace 根本還沒跑。
#    (實測餌:exit 130、印出那句話,正本 sha256 一個位元組都沒有變 —— 就是 SPEC §1
#     點名要消滅的那種謊。撤銷登記那兩行同樣有縫,落在中間會印「正在替換 None」,
#     還附一行叫人去跑 --restore「None」的指令,照著做也做不出東西來。)
#    `dict.update` 是一個 C 函式呼叫,直譯器只在位元組碼之間才處理訊號,
#    所以三個欄位是一起換掉的,中間沒有可以插進去的那一格。
_REPLACED = {'what': None, 'path': None, 'phase': 'idle'}


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來,這一段期間不讓 Ctrl-C 插隊。

    收到 SIGINT 先記在心裡,離開這一段之後再照常丟出 KeyboardInterrupt。
    這樣收尾看到的登記一定跟磁碟上的狀態一致,不會出現
    「檔案已經換掉了、程式還以為沒換」的那一瞬間。

    ⚠️ signal.signal 只有主執行緒裝得上。裝不上就退回原本的行為 ——
       不會比以前更糟,而且上面那個 'replacing' 狀態就是為這種情形留的:
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


def _do_copy(bak, dst):
    """真正把備份蓋回正本的地方 —— 而且是原子的(2026-09-05 改)。

    刻意獨立成一個函式:上面五道把關每一道都以「呼叫它」作為放行的動作,
    所以「哪裡會覆蓋正本」在這個檔裡只有一個出口,好稽核也好下餌測試。

    ── 為什麼不能只寫 shutil.copy2(bak, dst)(唯讀稽核 🔴 第 1 條)──────────
    copy2 的第一個動作是**把 dst 截成 0 bytes**,然後才一段一段把備份倒進去。
    那五道把關擋得住「備份是壞的」,擋不住「複製到一半停電、磁碟滿、外接碟被拔掉、
    按了 Ctrl-C」—— 那時候玩家的球場檔會停在 0 bytes 或半截,
    而他手上唯一的那份備份還在,卻已經沒有第二次機會了(第二次 --restore 一樣會先截斷)。

    現在的做法:
      1. 在**正本所在的那個資料夾**用 tempfile.mkstemp 開一個隨機名字的暫存檔
         (同一個檔案系統,os.replace 才會是原子的;名字隨機才佔不住、跟不到連結)
      2. 一邊寫一邊算 sha256,寫完 flush + fsync
      3. 把正本的權限抄到暫存檔(沒有這一步,還原完的檔會變成 umask 給的權限)
      4. **把暫存檔整份讀回來再算一次 sha256**,跟備份的雜湊與長度都要相等
      5. 全部對上才 os.replace 換名 —— 而且「換名 + 登記已經換過了」
         綁成一段不可中斷的區塊(見 _NoInterrupt),Ctrl-C 落不進那條縫裡
    任何一步失敗就把暫存檔刪掉,正本**一個位元組都沒被動過**。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    # 這兩個名字都是使用者給的/算出來的,沒辦法隨機化 —— 是連結就拒絕。
    _refuse_if_symlink(dst, '要還原的目標')
    _refuse_if_symlink(bak, '備份')
    folder = os.path.dirname(os.path.abspath(dst)) or '.'
    fd, tmp = tempfile.mkstemp(dir=folder, prefix='.' + os.path.basename(dst) + '.restore-')
    try:
        want = hashlib.sha256()
        with os.fdopen(fd, 'wb') as f_out:
            with open(bak, 'rb') as f_in:
                while True:
                    chunk = f_in.read(1024 * 1024)
                    if not chunk:
                        break
                    want.update(chunk)
                    f_out.write(chunk)
            f_out.flush()
            os.fsync(f_out.fileno())
        # 權限沿用「要被蓋掉的那個正本」。抄不到不該讓整件事失敗(例如正本已經不見了)。
        try:
            shutil.copymode(dst, tmp)
        except OSError:
            pass
        # 讀回來再算一次。拿記憶體裡剛算的那個去比自己,驗不出任何東西。
        got = hashlib.sha256()
        with open(tmp, 'rb') as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                got.update(chunk)
        if os.path.getsize(tmp) != os.path.getsize(bak) or got.digest() != want.digest():
            raise DataError(
                '把備份複製出來的那一份跟備份本身對不起來 —— 沒有換上去,%s 原封不動。'
                % os.path.basename(dst))
        # ⚠️ 2026-09-06:「換名」跟「登記換過了」中間不可以有縫。原本是
        #    os.replace 一行、下一行才登記,Ctrl-C 剛好落在那兩行之間的話,
        #    收尾看到的登記還是「沒動過」—— 而正本已經是備份那一份了。
        #    現在先登記「正在換」,再把換名與登記一起包進 _NoInterrupt。
        # ⚠️ 2026-09-11 再修:登記本身也不可以分成兩行(見上面 _REPLACED 那一段)。
        #    原本 what/path 一行、phase 一行,Ctrl-C 落在中間會讓收尾說
        #    「還原那一步**已經**做完了」而其實還沒還原。改成一次 update。
        _REPLACED.update(what='restore', path=dst, phase='replacing')
        with _NoInterrupt():
            os.replace(tmp, dst)
            _REPLACED['phase'] = 'replaced'
    except BaseException as _e:
        # 失敗就只留下一個沒人看得懂的隱藏暫存檔,正本完好。
        try:
            os.remove(tmp)
        except OSError:
            pass
        # 只有在「確定沒換成」的時候才可以把「正在換」收回「還沒動」。
        # os.replace 自己丟例外就是那種情形:它要嘛整個做完、要嘛完全沒做。
        # 撤銷一樣是一次寫完:分兩行寫的話,Ctrl-C 落在中間會留下
        # what=None 而 phase 還是 'replacing',收尾就印「正在替換 None」。
        if _REPLACED['phase'] == 'replacing' and isinstance(_e, OSError):
            _REPLACED.update(what=None, path=None, phase='idle')
        raise




# Windows 的主控台預設不是 UTF-8,不轉的話這支腳本印的中文會變亂碼甚至直接丟例外。
# 包在 try 裡是因為舊版 Python 沒有 reconfigure —— 轉不了就照舊跑,不要為了排版而中止。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 三個上限。前兩個是**拿檔案自己宣稱的數字去配置記憶體之前的煞車** ——
# 壞掉的檔會宣稱「我解開有 4 GB」或「我有 20 億個項目」,照著做就是當場吃光記憶體。
# 數值取得比真實資料大很多:本站量過最大的解壓輸出遠低於 64 MB,
# 而封裝檔的目錄項目數實測從數百到一萬多都有(2026-09-05 掃本站測試機 680 個封裝檔,
# 最多的是 audio/cd/spch_pbp/pnamedat.big 的 12,528 筆)。
MAX_UNCOMPRESSED = 64 * 1024 * 1024
MAX_BIG_ENTRIES = 200000
# 備份的副檔名。每一課用不同的字尾,是為了讓「哪一支工具改過這個檔」一眼看得出來。
BACKUP_SUFFIX = '.shrinkbak'


# ─────────────────────────────────────────────────────────
#  QFS(EA 的壓縮格式,檔頭是 10 FB)
# ─────────────────────────────────────────────────────────
# ⚠️ 讀者先知道這件事比較好:**這一整段(QFS 兩支 + 下面的 FSH 三塊)
#    在這支腳本裡沒有任何地方呼叫**。它是本站腳本共用的一塊,
#    站上 30 支腳本裡有 13 支帶著 QFS、8 支帶著 FSH(換球衣、換大頭照、
#    改記分板顏色那幾課真的會用到)。這一課只搬位置、不解壓也不改圖,
#    所以用不到 —— 留著是為了讓每一支都是「一個檔就能跑」,
#    也讓讀者能拿同一份程式碼去改別的東西。
#    同理,檔頭的 `import re` 與 `import zlib` 在這一支也沒有用到。
def qfs_decompress(data):
    """把 EA 的 QFS(又叫 RefPack)壓縮資料解開,回傳原始位元組。

    格式重點(讀者從程式碼上看不出來的部分):
      · 招牌在**第 2 個位元組**是 0xFB,第 1 個位元組是旗標。不是 0xFB 就當它沒壓縮,原樣回傳。
      · 旗標的最低位是 1 → 檔頭 10 bytes,解壓後大小放在位移 6~10;
        是 0 → 檔頭 5 bytes,解壓後大小放在位移 2~5。
      · **那個大小是大端(big-endian)**,而且是 3 或 4 個位元組,不是常見的 4 位元組小端。
      · 之後是一連串控制碼,每一碼帶「先照抄幾個位元組」與
        「再往回幾個位元組、複製幾個」兩件事,四種長度的編碼由第一個位元組的大小決定。

    往回複製的來源可以跟正在寫的位置重疊(這是這類壓縮的重點),
    所以下面是一個位元組一個位元組抄,不能用切片一次搬。
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

    # 主迴圈:一次讀一個控制碼。四個區間各是一種編碼長度,
    # 由控制碼的數值大小決定,所以判斷順序必須由大到小,不能調換。
    while pos < end:
        b0 = data[pos]
        # 0xFC~0xFF:結束碼。只帶「照抄 0~3 個位元組」,抄完整份就到底了。
        if b0 >= 0xFC:
            n = b0 & 0x03; pos += 1
            out += data[pos:pos + n]; break
        # 0xE0~0xFB:純照抄,一次 4~112 個位元組,沒有往回複製。
        if b0 >= 0xE0:
            n = ((b0 & 0x1F) << 2) + 4; pos += 1
            out += data[pos:pos + n]; pos += n; continue
        # 0xC0~0xDF:四位元組碼,能表達最長的往回距離與長度。
        # 位元被拆散在四個位元組裡(這是 RefPack 的省空間手法),所以看起來很亂。
        if b0 >= 0xC0:
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]; pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        # 0x80~0xBF:三位元組碼,中距離。
        elif b0 >= 0x80:
            b1, b2 = data[pos + 1], data[pos + 2]; pos += 3
            n = (b1 >> 6) & 0x03
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        # 0x00~0x7F:兩位元組碼,短距離,最常出現。
        else:
            b1 = data[pos + 1]; pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        # 三種都是同一個順序:先照抄 n 個位元組,再往回 offset 複製 length 個。
        out += data[pos:pos + n]; pos += n
        copy_back(offset, length)
    # 截到檔頭宣稱的長度為止。但是多出來的那幾個位元組不會是「最後一次往回複製」
    # 造成的:往回複製的收尾就在上面 copy_back 裡,一超過宣稱的大小就當成壞檔擋下來,
    # 根本走不到這一行。真正沒被那道檢查看到的只有兩條路:結束碼帶的那 0 到 3 個
    # 照抄位元組,以及純照抄那一段(不過只要後面還有一次往回複製就會被擋下來)。
    # 2026-09-03 實測:餵一份宣稱 6 個位元組的資料流進來,用往回複製多吐 1 個,
    # 拿到的是「QFS 解出來的資料超過檔頭宣稱的 6 位元組」這個錯誤;改成用結束碼的
    # 尾巴多吐 1 個,才真的被這一行切掉,拿回 6 個位元組。至於正常的遊戲檔,
    # 拿本站測試機 MVP2026/data/frontend/ 底下 98 個封裝檔裡的 9,643 個 QFS 項目
    # 各解一次,沒有一項解出來的長度超過檔頭宣稱的大小,所以這一行在實務上
    # 是最後一道保險,不是這支程式的正常路徑。
    return bytes(out[:size])


def qfs_compress_literal(data):
    """純 literal 編碼:不做字串比對,瞬間完成,格式一樣合法。

    壓出來比 EA 原本的大(大約等於原始大小),但因為我們是接到檔尾,
    大一點沒有影響。換來的是速度快上千倍,而且不可能壓錯。
    """
    n = len(data)
    # 5 個位元組的短檔頭:0x10 是旗標(最低位 0 = 短檔頭),0xFB 是招牌,
    # 後面三個位元組是「解開有多長」,**大端**。
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    # 純照抄的控制碼一次只能帶 4 的倍數(4~112),所以先把尾巴那 0~3 個位元組留給結束碼。
    tail = n % 4
    body = n - tail
    pos = 0
    while pos < body:
        chunk = min(112, body - pos)
        # 0xE0 開頭的照抄碼:低 5 位存的是「幾個 4 位元組」減 1,所以要先減 4 再除 4。
        out.append(0xE0 | ((chunk - 4) // 4))
        out += data[pos:pos + chunk]
        pos += chunk
    # 結束碼順便把剩下那 0~3 個位元組帶走。
    out.append(0xFC | tail)
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIGF 封裝檔:讀目錄、接到檔尾
# ─────────────────────────────────────────────────────────
# 這一段開始才是這一課真正在用的東西。封裝檔的長相:
#
#     位移 0x00   'BIGF'      四個字元的招牌
#     位移 0x04   4 bytes     整個檔案有多長(**小端或大端都遇得到**,見 size_field_order)
#     位移 0x08   4 bytes     目錄裡有幾個項目(**大端**)
#     位移 0x0C   4 bytes     跟目錄長度有關的欄位;本課不動目錄長度,所以不碰它
#     位移 0x10   目錄開始    每一筆:4 bytes 起點 + 4 bytes 長度(兩個都是**大端**)
#                             接一個以 \x00 結尾的名字,長度不固定
#     目錄之後    才是各項目的內容
#
# 這一課要做的事,用這張圖講就是一句話:
# **把「內容」那一區照目錄的順序重排、擠掉沒人指的位元組,再把目錄裡的起點改成新位置。**
def size_field_order(path):
    """檔頭 +0x04 的「檔案總大小」是 little 還是 big endian。

    ⚠️ 這一欄兩種順序都遇得到,不能寫死,也不能照檔名或檔案大小猜。
       哪個檔是哪一種不是這個格式天生的性質,而是看你手上這一份被誰重新打包過。

       本站以檔頭的 BIGF 招牌(不是副檔名)認過四份 data 資料夾:
       三份剛安裝好的原版(英文版 207 個封裝檔、繁體中文版 205 個、PK 版 205 個)
       全部是 little-endian,一個 big-endian 都沒有;連那三份裡最大的兩個封裝檔
       models.big(172,992,803 個位元組)與 frontend/portrait.big
       (109,291,217 個位元組)也是 little-endian,所以「大檔就是 big-endian」是假的。
       只有本站測試機那份疊過模組的 data 資料夾(384 個封裝檔)量得到 big-endian,
       共 10 個檔、7 個檔名:models.big、frontend/portrait.big、
       audio 底下的 pnamedat.big 與 pnamehdr.big,以及球場夜間檔
       coornite.big / dodgnite.big / wrignite.big
       (夜間那三個在測試機上另有一份複本放在別的球場資料夾,所以檔數比檔名多 3 個)。
       這 7 個檔名在三份原版裡量到的通通是 little-endian。

       所以不要照檔名或檔案大小記:讀出來是哪一種,就照哪一種寫回去。
    """
    # 判法很土但很可靠:用兩種順序各解一次,哪一種等於實際檔案大小就是哪一種。
    # 不必查表、不必知道是哪個檔,而且兩種都不對時等於順便驗出「這個檔壞了」。
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

    名字的長度不固定(以一個 0x00 位元組結尾),所以**沒辦法直接算出目錄有多長** ——
    只能從第 16 個位元組開始一筆一筆往下走。

    ⚠️ 解析不出宣告的筆數就丟 DataError,不回傳半份目錄(2026-09-05 加)。
       下面那一大塊只讀「檔頭 + count*80 + 8 KB」;名字平均超過約 71 個字元時,
       目錄會超出這一塊,迴圈就會停在中間。原本停下來之後照樣回傳已讀到的那些,
       而少解析到的那幾筆會被 analyse() 當成「沒人指到的位元組」清掉 ——
       複驗又是同一個函式重讀的、一樣少那幾筆,於是一個被清壞的檔會拿到綠燈。
       (實測合成餌:2000 筆、名字 90 字元,只解析出 1557 筆,--apply 之後
        443 筆的內容真的沒了,而腳本印「1557 個項目全部逐位元組相同 ✅」。)
    """
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            # 項目數在位移 8,大端。先用它擋掉離譜的檔,再拿它決定要讀多少。
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            # 一次讀一大塊,不要為了每一筆各讀一次檔(名字長度不固定,反覆 seek 很慢)。
            # 每筆抓 80 bytes 是寬鬆的估計(8 bytes 欄位 + 名字),再加 8 KB 緩衝。
            blob = head + f.read(count * 80 + 8192)
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))

    items = []
    pos = 16
    for _ in range(count):
        if pos + 8 > len(blob):
            break                                   # 目錄比預估長,已讀到的就夠用
        # field 記的是「這一筆的 8 個位元組在檔案裡的位置」。
        # 之後要改起點時只覆寫這 8 個位元組,目錄的長度與名字完全不動。
        field = pos
        off = int.from_bytes(blob[pos:pos + 4], 'big')
        size = int.from_bytes(blob[pos + 4:pos + 8], 'big')
        pos += 8
        # 名字以 \x00 結尾。找不到結尾就是讀到的那一塊不夠長,停在這裡。
        end = blob.find(b'\x00', pos)
        if end < 0:
            break
        # 用 latin-1 解碼:這裡只要「一個位元組換一個字元、不會丟例外」,
        # 名字純粹拿來顯示與配對,不需要真的懂它是什麼編碼。
        items.append((blob[pos:end].decode('latin-1', 'replace'), field, off, size))
        pos = end + 1
    # 上面那兩個 break 的意思是「我讀進來的那一塊不夠長」,不是「目錄到此為止」。
    # 少一筆就不敢動這個檔 —— 見上面 docstring 那段實測。
    if len(items) != count:
        raise DataError(
            '%s 的目錄宣告 %d 筆,只解析得出 %d 筆 —— 名字可能比預估的長,不敢動這個檔。'
            % (os.path.basename(path), count, len(items)))
    return items


def read_entry(path, off, size):
    """照目錄給的起點與長度,把某一個項目的原始位元組讀出來。

    讀完一定要驗長度:目錄說有 N 個位元組而只讀到 M 個,代表這個檔被截斷過。
    這種情況要當場停下來,不可以拿短少的資料繼續做事。

    (共用區塊。這一課整份讀進記憶體再切,所以沒有呼叫它。)
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

    **這正是孤兒資料的來源**,也就是這一課要清的東西:
    舊的那一份還躺在原地,只是沒有人再指向它。這裡把它寫成程式碼,
    是為了讓讀者看清楚「安全的改法」跟「檔案越變越大」其實是同一件事的兩面。

    (共用區塊。這一課是重排整個檔,不走接到檔尾這條路,所以沒有呼叫它。)
    """
    order = size_field_order(path)          # 一定要在改檔案之前先量
    # 新資料的起點就是現在的檔尾。先問大小,再開檔寫。
    new_off = os.path.getsize(path)
    with open(path, 'r+b') as f:
        f.seek(0, os.SEEK_END)
        f.write(blob)
        total = f.tell()
        # 只覆寫這一項目錄的那 8 個位元組:前 4 是新起點,後 4 是新長度。
        f.seek(field_pos)
        f.write(struct.pack('>II', new_off, len(blob)))     # 目錄一律 big-endian
        # 再更新檔頭 +0x04 的「整個檔案有多長」。位元組順序沿用原檔那一種。
        f.seek(4)
        f.write(struct.pack(order + 'I', total))
        # fsync 把資料真的推到磁碟。少了這一步,寫完到斷電之間那段時間,
        # 檔案可能停在「目錄已經指到新位置、但新資料還沒落地」的狀態。
        f.flush()
        os.fsync(f.fileno())
    return new_off


# ─────────────────────────────────────────────────────────
#  FSH(SHPI 容器):找到那張圖、換掉像素
# ─────────────────────────────────────────────────────────
# ⚠️ 同上,**這一整塊在這支腳本裡沒有任何地方呼叫**(這一課不碰圖片)。
#    留著是因為它是本站共用的一塊,站上 8 支腳本帶著它;
#    也讓讀者可以拿這一份程式碼直接去改「換球衣」「換大頭照」那幾課的東西。
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

    SHPI 容器的長相(**這裡全部是小端**,跟上面 BIGF 的目錄相反):
      位移 0x00   'SHPI'
      位移 0x08   4 bytes   裡面有幾張圖
      位移 0x10   起  目錄:每筆 8 bytes = 4 bytes 標籤 + 4 bytes 該圖的起點
                      所以第一張圖的起點在位移 16 + 0*8 + 4 = 20
      圖片記錄     +0    1 byte    格式代號(查 FSH_FORMATS)
                   +1    3 bytes   這個區塊有多長(**三個位元組**,小端,不是四個)
                   +4    2 bytes   寬
                   +6    2 bytes   高
                   +16   像素資料開始

    (共用區塊。這一課不碰圖片,所以沒有呼叫它。)
    """
    if len(data) < 16 or data[:4] != b'SHPI':
        raise DataError('不是 SHPI 檔(開頭是 %r)' % data[:4])
    num = struct.unpack_from('<I', data, 8)[0]
    if num < 1:
        raise DataError('這個 SHPI 裡一張圖都沒有')
    off = struct.unpack_from('<I', data, 20)[0]         # 16 + 0*8 + 4
    if off + 16 > len(data):
        raise DataError('圖片記錄的檔頭不完整')
    # 格式代號不在表裡就停下來。**不要猜**:猜錯會算出錯的每像素位元組數,
    # 接著就是把別人的圖片資料當成自己的覆蓋掉。
    code = data[off]
    if code not in FSH_FORMATS:
        raise DataError('沒見過的格式代號 0x%02X' % code)
    block_size = data[off + 1] | (data[off + 2] << 8) | (data[off + 3] << 16)
    width = struct.unpack_from('<H', data, off + 4)[0]
    height = struct.unpack_from('<H', data, off + 6)[0]
    # 4096 是寬鬆的上限,用來擋掉「讀到的根本不是尺寸」的情況。
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise DataError('圖片尺寸異常 %dx%d' % (width, height))
    start = off + 16
    # 像素資料到哪裡結束,三種來源由可靠到不可靠:
    #   ① 區塊自己寫了長度(> 16 才算數,16 是檔頭本身的長度)
    #   ② 沒寫的話,用下一張圖的起點當作結束點
    #   ③ 只有一張圖又沒寫長度,那就到檔尾
    if block_size > 16:
        end = min(off + block_size, len(data))
    elif num > 1:
        end = min(struct.unpack_from('<I', data, 16 + 8 + 4)[0], len(data))
    else:
        end = len(data)
    return code, width, height, start, end


def fsh_replace_pixels(data, start, end, new_pixels):
    """把 start~end 這一段像素換成 new_pixels,長度必須完全一樣。

    **長度一樣是唯一的放行條件,而且不可以放寬。** 這個容器裡每一張圖的
    起點都寫在前面的目錄裡;像素區長度一變,後面每一張圖的起點就全錯了,
    而錯掉的檔案在遊戲裡不是報錯,是花掉或直接跳出。

    (共用區塊。這一課不碰圖片,所以沒有呼叫它。)
    """
    if len(new_pixels) != end - start:
        raise DataError('新像素有 %d 個位元組,原本是 %d —— 尺寸或格式不一致,拒絕寫入'
                        % (len(new_pixels), end - start))
    return data[:start] + new_pixels + data[end:]




# ─────────────────────────────────────────────────────────
#  量:目錄指到多少、孤兒有多少
# ─────────────────────────────────────────────────────────
ALIGN = 4          # 實測:原版與社群包的每一個項目位置都是 4 的倍數


def analyse(path):
    """回傳 (檔案大小, 目錄項目, 目錄指到的位元組數, 第一筆資料的位置)。

    整支腳本的量法就這三行:**把目錄裡每一項的長度加起來,拿去跟檔案大小比。**
    差額就是「沒有人指到的位元組」。這個量法對任何一個封裝檔都成立,不只球場。

    `first`(最小的那個起點)之所以要一起回傳,是因為重排時要把
    檔頭與目錄那一整段原樣留著 —— 新的內容從原本第一筆資料的位置開始排。
    """
    items = big_entries(path)
    if not items:
        raise DataError('%s 的目錄是空的。' % os.path.basename(path))
    total = os.path.getsize(path)
    used = sum(it[3] for it in items)
    first = min(it[2] for it in items)
    # 動手之前先確認目錄自己是自洽的:有任何一項指到檔案外面,
    # 就代表這個檔已經壞了(或不是我們以為的格式)。這種檔一個位元組都不要碰。
    for name, field, off, size in items:
        if off + size > total:
            raise DataError('目錄裡「%s」指到 %d~%d,超出檔案大小 %d —— 這個檔可能已損毀,不敢動。'
                            % (name, off, off + size, total))
    return total, items, used, first


def planned_size(items, first):
    """重排之後這個檔會有多長。

    **刻意跟 `cmd_shrink` 的重排迴圈算同一件事**:從 first 開始,每一項先補 0
    對齊到 4 的倍數再放進去。兩邊算法一致,診斷印的數字才會等於 --apply 真的做出來的
    大小,「不用清」的判斷也才不會一邊說要清、一邊說不用清(2026-09-05 加)。
    """
    pos = first
    for _, _, _, size in sorted(items, key=lambda it: it[2]):
        pos += (-pos) % ALIGN
        pos += size
    return pos


def cmd_check(path):
    """不加參數時走這裡:**純唯讀的診斷**,印出這個檔的體檢報告。

    這是每一位讀者的第一個動作,也是這一課的重點 ——
    先弄清楚「檔案大」的原因是三種裡的哪一種,再決定要不要清。
    這個函式從頭到尾沒有任何寫檔的動作。
    """
    total, items, used, first = analyse(path)
    orphan = total - used
    # 整份讀進來,是為了下面判斷「大項目是不是壓縮過的」時可以直接看那兩個位元組。
    with open(path, 'rb') as _f:
        raw0 = _f.read()
    print('  檔案 %s' % os.path.basename(path))
    print('  大小            %12d 位元組（%.2f MB）' % (total, total / 1048576.0))
    print('  目錄項目數      %12d' % len(items))
    print('  目錄指到的內容  %12d 位元組（%.2f MB）' % (used, used / 1048576.0))
    print('  沒人指到的      %12d 位元組（%.2f MB，佔 %.1f%%）'
          % (orphan, orphan / 1048576.0, 100.0 * orphan / total))
    print()
    # 封裝檔變大有**三個**完全不同的原因，這裡直接判給使用者看:
    #   ① 孤兒堆積     —— 清得掉，畫面完全不變
    #   ② 貼圖真的變大 —— 一個位元組都清不掉
    #   ③ 壓縮被丟掉   —— 也清不掉，要重新壓縮才會小回去
    # 實測:rfksnite.big 14.95 MB 的孤兒是 0%，那 15 MB 全是真內容(②);
    # 而某個護具模組的 initstaz.big 是 2.94 MB、原版同一個檔只有 1.16 MB，
    # 孤兒同樣接近 0 —— 差別在原版的內層是壓縮的，那個模組沒壓(③)。
    # 只講①會誤導人，只講①②一樣會。
    # 先算「清完會變多小」:檔頭與目錄那一段照留(first),之後每一項的**起點**
    # 對齊到 4 的倍數再一項一項排下去 —— 跟 cmd_shrink 的重排迴圈同一套算法
    # (見 planned_size),所以這裡印的數字就是 --apply 真的會做出來的大小。
    newsize = planned_size(items, first)
    # 2% 這條線是拿來分岔用的,不是物理常數:低於它就算清了也看不出差別,
    # 那時該講的是「你的問題不是孤兒」,而不是「來清吧」。
    #
    # 另外兩個條件是 2026-09-05 補的,為的是讓這裡跟 cmd_shrink 說同一句話:
    #   · orphan < 1024:cmd_shrink 用的就是這條線。少了它,894 bytes 的
    #     data/frontend/misc.big(孤兒 128 bytes、14.3%)會在這裡被叫去清,
    #     而 --shrink 回他「幾乎沒有孤兒資料,不用清」——讀者查不到自己看到的字。
    #   · newsize >= total:孤兒排在第一筆資料之前,清不掉(見下面那一段)。
    # 這三個條件是 cmd_shrink 拒絕情況的**超集合**,所以「這裡叫你清、那裡不清」
    # 不會再發生。
    if orphan < 1024 or orphan < total * 0.02 or newsize >= total:
        # 判斷的順序照「哪一句對讀者最有用」排,不是照條件寫的順序:
        # 孤兒本來就少的檔,該講的還是「這個檔很乾淨」(原本就是這一句,沒動),
        # 另外兩句是 2026-09-05 新增的兩種情況才會看到。
        if orphan < total * 0.02:
            print('  這個檔很乾淨（孤兒不到 2%），清了也省不了什麼。')
        elif orphan < 1024:
            print('  沒人指到的只有 %d 個位元組，清了也省不了什麼。' % orphan)
        else:
            print('  重排之後不會變小 —— 那些沒人指到的位元組排在第一筆資料之前，')
            print('  跟檔頭與目錄一起被原樣留著，這一課清不掉。這個檔不用清。')
        # ③ 的線索:大項目的開頭不是 QFS 的 10 FB
        uncomp = [n for n, _, o, sz in items
                  if sz > 65536 and raw0[o:o + 2] != b'\x10\xfb']
        if uncomp:
            print()
            print('  ⚠️ 有 %d 個大項目**不是**壓縮格式開頭（不是 10 FB）。' % len(uncomp))
            print('     如果原版的同一個檔明顯比較小，那多半是存回去時沒有重新壓縮 ——')
            print('     那種情況這一課也幫不上忙，要重新壓縮才會小回去。')
            print('     例:%s' % '、'.join(uncomp[:3]))
        # 這句話只有在「孤兒真的很少」時才成立。孤兒很多但清不掉(newsize >= total)
        # 的檔也會走到這個分支,對那種檔說「做這個模組的人好好重新打包過」是錯的,
        # 所以這裡多綁一個 orphan 的條件(2026-09-05 加)。
        if total > 10 * 1048576 and not uncomp and orphan < total * 0.02:
            print()
            print('  ⚠️ 但它有 %.2f MB —— 這是「內容真的有那麼多」，不是垃圾。' % (total / 1048576.0))
            print('     做這個模組的人好好重新打包過，只是換上了更大的貼圖。')
            print('     這一課幫不了你。要縮小只能換回原版的那一份。')
    else:
        print('  清掉之後大約會變成 %.2f MB（現在 %.2f MB，省 %.0f%%）'
              % (newsize / 1048576.0, total / 1048576.0, 100.0 * (1 - newsize / float(total))))
        if newsize > 10 * 1048576:
            print('  ⚠️ 注意:清完還是有 %.2f MB —— 剩下的是真內容，清不掉了。'
                  % (newsize / 1048576.0))
        # 2026-08-28 修:這裡原本寫「把 --check 換成 --shrink」,
        # 但 --check 這個參數根本不存在(不加參數就是診斷),
        # 使用者照著做會打出一個無效的指令。改成印出可以直接複製的整行。
        print()
        print('  要看清完會變怎樣（不會動到檔案）:')
        print('    python3 %s "%s" --shrink' % (os.path.basename(__file__), path))
        print('  確定要清:')
        print('    python3 %s "%s" --apply' % (os.path.basename(__file__), path))


def _verify_pack(check_path, items, raw):
    """重讀 check_path 的目錄,逐項跟「動手前的原始位元組」比對,回傳問題清單。

    回傳空的清單 = 全部對得上。**刻意回傳字串而不是直接印**:
    這個函式會被呼叫兩次,兩次要做的事不一樣 ——
      · 換名**之前**驗暫存檔:發現問題就整個放棄,一個字都不必印給讀者看,
        因為那時候遊戲檔一個位元組都還沒被動到
      · 換名**之後**驗正本:每一條都要印出來,然後自動從備份還原
    (2026-09-06 抽出來。原本只有換名之後那一次 —— 重排如果算錯,
     讀者的球場檔會先被換成壞的,再靠還原救回來;現在壞的那一份根本不會換上去。)

    複驗刻意**重新從磁碟讀一次目錄**,不拿記憶體裡的 out 來比 ——
    拿自己剛算出來的東西驗自己,驗不出任何東西。
    """
    probs = []
    items2 = big_entries(check_path)
    if len(items2) != len(items):
        probs.append('  ❌ 項目數變了（%d → %d）' % (len(items), len(items2)))
        return probs
    # 用「這一筆在目錄裡的位置」配對,不要用名字。
    # ⚠️ 名字在真實的封裝檔裡會重複:2026-09-05 掃本站測試機 680 個封裝檔,
    #    34 個有重複名字(frontend 底下的 coopteam.big、stadiums.big、
    #    coopunis.big …)。用名字當鍵的話,重複的那幾筆只有最後一筆留在字典裡,
    #    複驗就會拿另一筆的舊內容去比第一筆,把一個**寫得完全正確**的檔判成失敗、
    #    印 ❌ 叫人立刻 --restore —— 等於叫人把好檔換回肥檔。
    #    (合成餌實測:dup.fsh=AAA / other.fsh=BBB / dup.fsh=CCC,新檔三筆確實是
    #     AAA/BBB/CCC 位置與內容全對,舊版照樣印「dup.fsh 的內容跟原本不同」。)
    # 目錄的位置是唯一的,而且這一課從頭到尾沒動過目錄的長度與名字,
    # 所以新舊兩邊的 field 一定對得起來;名字有沒有被動到則另外驗一次。
    old_by_field = {it[1]: (it[0], it[2], it[3]) for it in items}
    with open(check_path, 'rb') as f:
        for name, field, off, size in items2:
            if field not in old_by_field:
                probs.append('  ❌ 新檔的目錄裡多出一筆（第 %d 個位元組那一筆，%s）'
                             % (field, name)); continue
            o_name, o_off, o_size = old_by_field[field]
            if name != o_name:
                probs.append('  ❌ 目錄第 %d 個位元組那一筆的名字變了（%s → %s）'
                             % (field, o_name, name)); continue
            if size != o_size:
                probs.append('  ❌ %s 的長度變了（%d → %d）' % (name, o_size, size)); continue
            # 逐位元組比對:這一項的內容,必須等於**動手前**同一項的內容。
            f.seek(off)
            if f.read(size) != bytes(raw[o_off:o_off + o_size]):
                probs.append('  ❌ %s 的內容跟原本不同' % name)
    # 最後補驗檔頭的大小欄。它跟實際檔案大小對不上的話,遊戲讀這個檔就會出事。
    n = os.path.getsize(check_path)
    with open(check_path, 'rb') as f:
        h = f.read(8)
    if struct.unpack('<I', h[4:8])[0] != n and struct.unpack('>I', h[4:8])[0] != n:
        probs.append('  ❌ 檔頭的大小欄跟實際檔案大小對不上')
    return probs


def cmd_shrink(path, apply_it):
    """--shrink / --apply 走這裡。

    `apply_it` 是 False 就只算給你看,一個位元組都不寫;
    是 True 才依序做:備份 → 寫暫存 → **複驗暫存** → 換名 → 再複驗一次。
    (2026-09-06 補上中間那一次:換名之前就發現重排算錯的話,
     壞的那一份根本不會換上去,遊戲檔一個位元組都沒有動。)
    兩條路走的是**同一段重排程式碼**,所以你預覽看到的數字就是實際會發生的事。
    """
    total, items, used, first = analyse(path)
    orphan = total - used
    print('  檔案 %s：%.2f MB，其中沒人指到的 %.2f MB（%.1f%%）'
          % (os.path.basename(path), total / 1048576.0, orphan / 1048576.0, 100.0 * orphan / total))
    # 1 KB 以下不值得動。動一個檔的風險是固定的,省下來的好處卻趨近於零。
    if orphan < 1024:
        print('  幾乎沒有孤兒資料，不用清。')
        return

    # 整份讀進記憶體。球場檔最大也就十幾 MB,這樣做最單純,
    # 而且待會複驗要拿「動手前的原始位元組」來比對,本來就得留著。
    with open(path, 'rb') as f:
        raw = bytearray(f.read())

    # ── 重排 ────────────────────────────────────────────
    # 原則:**只改每一項在檔案裡的位置**。
    #   · 項目順序照原本的先後（依原 offset 排序），不重新命名也不排序
    #   · 目錄的位元組長度完全不變（名稱與數量都沒動），所以檔頭的
    #     +0x0C 那一欄不必碰 —— 它跟目錄長度有關，而目錄長度沒變
    #   · 資料起點沿用原本第一筆的位置，把檔頭與目錄那一段整個留著
    #   · 每一項對齊到 4 的倍數（實測原版與社群包都是這樣）
    # 依原本的起點排序 = 維持原來的先後。**不重新命名、不按名字排序** ——
    # 順序換掉就等於在做「重新打包」,那是本站鐵律不准的事。
    order = sorted(items, key=lambda it: it[2])
    # 先把檔頭與整份目錄原樣搬過來(raw[:first]),新的內容從原本第一筆的位置開始排。
    out = bytearray(raw[:first])
    newpos = {}
    for name, field, off, size in order:
        # 補 0 補到 4 的倍數。這是實測原版與社群包都遵守的排列方式,
        # 補的是位置不是內容 —— 項目本身的位元組一個都沒動。
        while len(out) % ALIGN:
            out.append(0)
        newpos[field] = len(out)
        out += raw[off:off + size]

    # 內容排好之後才回頭改目錄。每一筆只覆寫它自己的 8 個位元組(新起點 + 原長度),
    # 目錄的總長度完全不變,所以檔頭 +0x0C 那一欄不必碰。
    for name, field, off, size in order:
        struct.pack_into('>II', out, field, newpos[field], size)

    # 最後更新檔頭 +0x04 的「整個檔案有多長」,位元組順序沿用原檔那一種。
    order_char = size_field_order(path)          # 這一欄兩種位元組順序都遇得到
    struct.pack_into(order_char + 'I', out, 4, len(out))

    # ⚠️ 孤兒不等於清得掉。上面 out 是從 raw[:first] 開始接的 ——
    #    排在第一筆資料起點之前的那一段(檔頭、目錄,以及夾在中間沒人指的位元組)
    #    原樣留著。孤兒全在那一段的話,重排完只會一樣大甚至更大。
    #    實測 data/frontend/igonly.big:孤兒 95.8%,--apply 之後
    #    5,456,802 → 5,456,803 個位元組(多 1 個),而且照樣做了一份 5.2 MB 的備份、
    #    照樣印「複驗 ✅」。這種檔連備份都不該做,所以在這裡就停(2026-09-05 加)。
    if len(out) >= total:
        print('  重排後 %.2f MB —— 不會變小。' % (len(out) / 1048576.0))
        print('  那些沒人指到的位元組排在第一筆資料之前，跟檔頭與目錄一起被原樣留著，')
        print('  這一課清不掉它們。這個檔不用清，什麼都沒有動到。')
        return

    print('  重排後 %.2f MB（省 %.2f MB，%.1f%%）'
          % (len(out) / 1048576.0, (total - len(out)) / 1048576.0,
             100.0 * (1 - len(out) / float(total))))
    print('  項目數不變 %d，每一項的位元組原封不動，只有位置變了。' % len(items))

    if not apply_it:
        print()
        print('  以上是預覽，還沒有動到任何檔案。')
        print('  確定要清的話，在剛才那一行最後面加上 --apply')
        return

    # 動手之前先擋掉符號連結(2026-09-05 改)。
    # 這一段原本檢查的是「<原檔名>.tmp 是不是已經被佔用」—— 那是因為暫存檔叫死名字。
    # 現在暫存檔改用 tempfile.mkstemp 產生隨機名字(O_CREAT|O_EXCL),
    # 佔不住也就不必檢查了;真正擋不住的是**正本或備份本身是一個符號連結**:
    #   · 正本是連結 → os.replace 換掉的是連結,真正的球場檔一個位元組都沒清
    #     (main() 在 --apply 這條路上已經先擋掉了,這裡是第二道 ——
    #      2026-09-06 訂正:那裡原本是「先解開再照樣寫」,現在是「直接拒絕」)
    #   · 備份的名字是連結 → 備份會寫到資料夾外面去,而且 os.path.exists()
    #     對「指向不存在的檔」的連結回 False,會被誤判成「還沒有備份」
    backup = path + BACKUP_SUFFIX
    _refuse_if_symlink(path, '要清的封裝檔')
    _refuse_if_symlink(backup, '備份')

    # 備份。**已經有了就不覆蓋** —— 第二次執行時原檔已經是改過的,
    # 蓋上去等於把「動手前的樣子」永遠弄丟。最早那一份才是有價值的那一份。
    if not os.path.exists(backup):
        _atomic_copy(path, backup)
        print()
        print('  已備份 → %s' % os.path.basename(backup))
    else:
        print()
        print('  備份已存在，保留最早那一份 → %s' % os.path.basename(backup))

    # 先寫暫存檔再換名。直接對原檔開 'wb' 的話,寫到一半被中斷就留下一個半截的球場檔;
    # 這樣寫則是「舊的完好」或「新的完整」二選一,沒有中間狀態。
    # 暫存檔用 tempfile.mkstemp 建在**同一個資料夾**裡(換個資料夾 os.replace 就不是
    # 原子的了),名字隨機 + O_CREAT|O_EXCL —— 沒有人能先用一個符號連結佔住那個名字,
    # 把這一次的寫入導到資料夾外面去(2026-09-05 改;原本叫死名字 <原檔名>.tmp)。
    # ⚠️ 2026-09-05 一起補上 flush + fsync:原本沒有這一步,換名之後新內容有沒有
    #    真的落到磁碟,作業系統沒有給保證(同一支腳本的 append_entry 一直都有做)。
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)) or '.',
                               prefix='.' + os.path.basename(path) + '.tmp-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(bytes(out))
            f.flush()
            os.fsync(f.fileno())
        # 暫存檔是新建的,權限由 mkstemp 決定(0600)—— 直接換名會把原檔的權限一起換掉。
        # 實測本站測試機的封裝檔是 0700(rwx------),先把原檔的權限抄過去再換名。
        try:
            shutil.copymode(path, tmp)
        except OSError:
            pass                            # 抄不到權限不該讓整件事失敗
        # ── 複驗(第一次):**還沒換名之前**先用本檔自己的解析器重讀暫存檔 ──
        # 2026-09-06 加。原本只有換名之後那一次:重排如果算錯,讀者的球場檔會
        # **先被換成壞的**,再靠自動還原救回來 —— 那時候「一個位元組都沒動」
        # 這句話已經不能說了。現在壞的那一份根本不會換上去。
        probs = _verify_pack(tmp, items, raw)
        if probs:
            for _msg in probs:
                print(_msg)
            raise DataError(
                '重排出來的那一份沒有通過複驗（%d 項）—— 它沒有被換上去,'
                '你的遊戲檔一個位元組都沒有動。請把這件事回報給本站。' % len(probs))
        # ⚠️ 「換名」跟「登記換過了」中間不可以有縫(2026-09-06 改)。原本是
        #    os.replace 一行、下一行才登記,Ctrl-C 剛好落在那兩行之間的話,
        #    收尾看到的登記還是「沒動過」,會對著一個**已經被換掉的球場檔**
        #    說「一個位元組都沒有動到」。現在先登記「正在換」,再把換名與登記
        #    一起包進 _NoInterrupt(這段期間的 Ctrl-C 先記著,離開之後才丟出來)。
        # ⚠️ 2026-09-11 再修:登記本身也不可以分成兩行(見上面 _REPLACED 那一段)。
        #    原本 what/path 一行、phase 一行,Ctrl-C 落在中間會讓收尾說
        #    「檔案**已經**換成清過的那一版了」而其實一個位元組都沒換。改成一次 update。
        _REPLACED.update(what='shrink', path=path, phase='replacing')
        with _NoInterrupt():
            os.replace(tmp, path)
            # 換過去了。從這一秒起,被打斷就不可以再說「什麼都沒有動到」。
            _REPLACED['phase'] = 'replaced'
    except BaseException as _e:
        # 沒換成就把暫存檔收掉,原檔完好。
        try:
            os.remove(tmp)
        except OSError:
            pass
        # 只有在「確定沒換成」的時候才可以把「正在換」收回「還沒動」。
        # os.replace 自己丟例外就是那種情形:它要嘛整個做完、要嘛完全沒做。
        # 撤銷一樣是一次寫完(理由同 _do_copy 那一處)。
        if _REPLACED['phase'] == 'replacing' and isinstance(_e, OSError):
            _REPLACED.update(what=None, path=None, phase='idle')
        raise

    # ── 複驗(第二次):每一項都要逐位元組相同 ──────────────────────
    # 換名之前已經對暫存檔驗過一次了(見上面那一段),這一次驗的是**換上去之後的正本**。
    # 兩次不是同一件事重跑:第一次擋的是「重排算錯」(那時候還來得及不換),
    # 第二次擋的是「換名之後磁碟上的東西跟我剛寫出去的不一樣」。
    probs = _verify_pack(path, items, raw)
    for _msg in probs:
        print(_msg)
    bad = len(probs)
    if bad:
        # 複驗沒過就是「寫出去的東西跟原本不一樣」。這時候**不要只印一句叫人自己去還原** ——
        # 備份就在旁邊、而且剛才才驗過,直接換回去比較安全(2026-09-05 加)。
        # 還原走的是 _restore_from_backup:五道把關 + 原子換名,失敗的話正本原封不動。
        print()
        print('  複驗沒過 —— 現在立刻把備份換回去。')
        restored, why = False, ''
        try:
            _restore_from_backup(backup, path)
            restored = True
        except (Exception, SystemExit) as e:   # KeyboardInterrupt 故意不接,讓它照常走 130
            why = str(e) or e.__class__.__name__
        if restored:
            print('  ✓ 已自動還原 ← %s（檔案回到動手前的樣子）' % os.path.basename(backup))
            raise DataError('複驗有 %d 項沒過。已經自動從備份還原了，請把這件事回報給本站。' % bad)
        print('  ⚠️ 自動還原沒有成功:%s' % why)
        print('  請自己跑一次:')
        print('    python3 %s "%s" --restore' % (os.path.basename(__file__), path))
        raise DataError('複驗有 %d 項沒過，而且自動還原也失敗了 —— 見上面那一行。' % bad)
    # 兩次複驗都零問題才走到這裡。項目數用 items —— 數量對不上的話
    # _verify_pack 第一件事就是回報「項目數變了」,根本走不到這一行。
    print('  複驗：%d 個項目全部逐位元組相同，檔頭大小欄正確 ✅' % len(items))
    print()
    print('  進遊戲確認那座球場開得起來。有問題就 --restore。')


def cmd_restore(path):
    """--restore 走這裡:把 `.shrinkbak` 蓋回原檔。

    三層把關,一層比一層深:
      ① 備份存不存在
      ② 備份的開頭是不是 BIGF(不是就代表指錯檔了)
      ③ `_restore_from_backup` 裡那五道(擋半截的備份)
    五道都過之後才走 `_do_copy`,而那一步是**原子的**(2026-09-05 改):
    先寫一個隨機名字的暫存檔、比對 sha256 與長度,最後才 os.replace 換名 ——
    複製途中斷電、磁碟滿、外接碟被拔掉,正本都是原封不動的那一份。
    蓋完再把兩個檔整份讀出來比一次,確定真的一樣才說還原成功。

    ⚠️ 第 ③ 組那五道丟的是 SystemExit,會**繞過** main() 的統一出口:
       訊息跑到 stderr、結束碼變成 1,而檔頭寫著結束碼只有 0 / 2 / 130。
       批次腳本照那份說明去判斷「2 = 自己認出來的問題」,就會漏掉最重要的一種 ——
       備份是壞的、拒絕還原。所以這裡把它轉成 DataError(2026-09-05 加),
       讓它跟其他錯誤走同一個出口。擋人的邏輯完全沒動,只換了怎麼回報。
    """
    backup = path + BACKUP_SUFFIX
    if not os.path.exists(backup):
        raise DataError('找不到備份 %s —— 沒有東西可以還原。' % os.path.basename(backup))
    with open(backup, 'rb') as f:
        if f.read(4) != b'BIGF':
            raise DataError('備份檔開頭不是 BIGF，不敢拿它覆蓋。')
    try:
        _restore_from_backup(backup, path)
    except SystemExit as e:
        # _restore_from_backup 是本站多支腳本共用的一塊,不去改它裡面丟什麼;
        # 在這裡接住,轉成這支腳本自己的錯誤型別。
        raise DataError(str(e))
    # 「印了成功」跟「真的還原了」是兩件事,所以讀回來實際比一次。
    same = open(backup, 'rb').read() == open(path, 'rb').read()
    print('  已還原 ← %s' % os.path.basename(backup))
    print('  複驗：內容與備份%s' % ('相同 ✅' if same else '不同 ❌'))
    if not same:
        raise DataError('還原後內容跟備份不一樣，請手動檢查。')


def main():
    """看參數決定走哪一條路,並且把所有錯誤收在同一個地方。

    回傳值就是行程的結束碼:0 成功、2 是自己認出來的問題,130 是使用者按 Ctrl-C。
    分開的用意是讓批次腳本能判斷發生了什麼事。**2 這一種涵蓋四類**:
    DataError、「備份是壞的所以拒絕還原」(cmd_restore 轉成 DataError)、
    「你指的那個名字是符號連結,而這一次會寫檔」(2026-09-06 加,一樣是 DataError),
    以及作業系統不讓讀寫這個檔(OSError)。

    DataError 一律印成一句人話而不是丟 traceback —— 這一課的讀者不是工程師,
    看到一整片紅字只會嚇到,而每一個 DataError 的訊息都已經寫清楚該怎麼辦。
    """
    EPILOG = (
        "\n順序（每一步都可逆）:\n\n"
        "  1. 先量:這個檔裡有多少是沒人指到的\n"
        "     python3 mvp_shrink_big.py \"<遊戲資料夾>/data/stadium/skydnite.big\"\n\n"
        "  2. 預覽會變多小（不會動到檔案）\n"
        "     python3 mvp_shrink_big.py \"<...>/skydnite.big\" --shrink\n\n"
        "  3. 確定了才真的清\n"
        "     python3 mvp_shrink_big.py \"<...>/skydnite.big\" --shrink --apply\n\n"
        "  4. 出問題就還原\n"
        "     python3 mvp_shrink_big.py \"<...>/skydnite.big\" --restore\n"
    )
    ap = argparse.ArgumentParser(
        description='把封裝檔裡目錄沒指到的位元組清掉（內容一個位元組都不少）',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EPILOG)
    ap.add_argument('bigfile', help='要處理的 .big')
    ap.add_argument('--shrink', action='store_true', help='清掉孤兒資料（沒加 --apply 就只是預覽）')
    ap.add_argument('--apply', action='store_true',
                    help='真的寫入（單獨用就會清,不必再加 --shrink）')
    ap.add_argument('--restore', action='store_true', help='從備份還原')
    args = ap.parse_args()

    # 符號連結:**會寫檔的那兩條路一律拒絕,唯讀那兩條照樣跟著走。**
    #
    # os.replace 換掉的是**連結本身**:對一個指向真正球場檔的連結跑 --apply,
    # 連結會變成一般檔案,真正那個檔一個位元組都沒清,而腳本照樣印「複驗 ✅」
    # 與「進遊戲確認」(實測就是這樣),備份也寫在連結旁邊而不是本體旁邊。
    # 用 Wine 玩、或用模組管理器把球場檔連過去的裝法都會踩到。
    #
    # ⚠️ 2026-09-06 改。2026-09-05 那一版是「先 realpath 再照樣寫下去」——
    #    比起「寫壞連結本身」是好一點(至少動到的是同一個實體檔),但那仍然是
    #    替使用者決定去改資料夾**外面**的東西,而他打的那個路徑上看不出來。
    #    要改哪一個檔應該由他自己講明白,所以現在直接拒絕(結束碼 2)。
    #    唯讀那兩條路不受限:只是量,跟著連結走沒有風險 —— 而且照著解開之後,
    #    畫面上印給他複製的那兩行 --shrink / --apply 才會指到真正的那個檔。
    target = args.bigfile

    # 三條路的順序有意義:--restore 最優先(那是逃生口,任何時候都該通),
    # 其次才是會寫檔的 --shrink / --apply,都沒給就落到唯讀診斷。
    try:
        if os.path.islink(target):
            if args.restore or args.apply:
                _refuse_if_symlink(target, '要處理的封裝檔')     # 一定會丟 DataError
            target = os.path.realpath(target)
            print('  %s 是一個符號連結，實際處理的是：' % args.bigfile)
            print('    %s' % target)
            print()
        if args.restore:
            cmd_restore(target)
        elif args.shrink or args.apply:
            # 2026-08-28 修:原本 --apply 只是 --shrink 的修飾詞,
            # 單獨給 --apply 會安靜地掉到唯讀診斷 —— 使用者會以為清了但其實沒有。
            # 一個「什麼都沒做卻看起來像做了」的指令,比直接報錯更糟。
            cmd_shrink(target, args.apply)
        else:
            cmd_check(target)
    except DataError as e:
        print('\n  停下來了：%s\n' % e)
        return 2
    except OSError as e:
        # 遊戲裝在 C:\Program Files\ 之類寫不進去的地方、磁碟滿了、外接碟被拔掉、
        # 或那個檔正被遊戲開著 —— 這些走這裡。原本會噴一整片英文 traceback
        # (實測:唯讀資料夾 + --apply,六層 traceback、結束碼 1),
        # 而這一課的讀者不是工程師,正好是上面那句「一律印成一句人話」保證不會發生的事。
        print('\n  停下來了：作業系統不讓我讀寫這個檔 —— %s\n'
              '  常見原因:遊戲資料夾沒有寫入權限、磁碟滿了、外接碟被拔掉,\n'
              '  或那個檔正被遊戲開著。' % e)
        # 照實說有沒有換過(2026-09-05 加)。這種錯誤**多半**發生在還沒開始寫的階段,
        # 但「多半」不是「一定」—— 換名之後的複驗也會讀檔,那時候外接碟被拔一樣走這裡。
        if _REPLACED['phase'] == 'replacing':
            # 換名那一段被包成不可中斷的區塊之後,這一格幾乎不可能亮 ——
            # 它是保險,而保險亮的時候要說不確定,不可以猜一個好聽的。
            print('  ⚠️ 出事的時候**正在換名**,換好了沒有沒辦法確定。\n'
                  '  請拿旁邊那份 .shrinkbak 跟它比對,或直接還原(還原一定回得去):\n'
                  '    python3 %s "%s" --restore\n'
                  % (os.path.basename(__file__), _REPLACED['path']))
        elif _REPLACED['what'] == 'shrink':
            print('  ⚠️ 不過換名那一步**已經**做完了,檔案現在是清過的那一版。\n'
                  '  要回到動手前的樣子:\n'
                  '    python3 %s "%s" --restore\n'
                  % (os.path.basename(__file__), _REPLACED['path']))
        elif _REPLACED['what'] == 'restore':
            print('  ⚠️ 不過還原那一步**已經**做完了,檔案現在就是備份的那一份。\n')
        else:
            print('  發生在這個階段的話,你的遊戲檔一個位元組都沒動。\n'
                  '  旁邊如果已經有 .shrinkbak,加 --restore 可以確定回到動手前的樣子。\n')
        return 2
    except KeyboardInterrupt:
        # 照實說。「什麼都沒有動到」這句話只有在**還沒 os.replace** 的時候才是真的
        # (2026-09-05 改;原本不管有沒有寫過都印同一句)。
        what, p = _REPLACED['what'], _REPLACED['path']
        if _REPLACED['phase'] == 'replacing':
            # 「換名 + 登記」那一段的保險(_NoInterrupt)裝不上時才會走到這裡
            # (signal.signal 只有主執行緒裝得上)。不確定就要說不確定 ——
            # 這一格的存在就是為了不要在這種時候說「一個位元組都沒有動到」。
            print('\n  已中斷 —— 中斷的時候**正在替換** %s,\n'
                  '  換好了沒有,這邊沒辦法確定。\n'
                  '  請拿旁邊那份 .shrinkbak 跟它比對,或直接還原(還原一定回得去):\n'
                  '    python3 %s "%s" --restore\n'
                  % (p, os.path.basename(__file__), p))
        elif what == 'shrink':
            print('\n  已中斷 —— 但檔案**已經**換成清過的那一版了(換名那一步已經做完)。\n'
                  '  要回到動手前的樣子:\n'
                  '    python3 %s "%s" --restore\n'
                  % (os.path.basename(__file__), p))
        elif what == 'restore':
            print('\n  已中斷 —— 但還原那一步**已經**做完了,檔案現在就是備份的那一份。\n')
        else:
            print('\n  已中斷。你的遊戲檔一個位元組都沒有動到\n'
                  '  (旁邊可能留下一個看不太懂的隱藏暫存檔,刪掉就好)。\n')
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
