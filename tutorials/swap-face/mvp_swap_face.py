#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_swap_face.py — 幫 MVP Baseball 2005 的球員換一張臉

這支腳本只動一個 800 KB 的純文字檔（data/database/attrib.dat），
完全不碰 536 MB 的 models.big。models.big 只會被「讀目錄」，不解壓、不寫入。

用法（先預覽，確定了再加 --apply）：

    python3 mvp_swap_face.py "<遊戲資料夾>"
    python3 mvp_swap_face.py "<遊戲資料夾>" --find Ohtani
    python3 mvp_swap_face.py "<遊戲資料夾>" --set <識別碼> 665
    python3 mvp_swap_face.py "<遊戲資料夾>" --set <識別碼> 665 --apply
    python3 mvp_swap_face.py "<遊戲資料夾>" --restore
    python3 mvp_swap_face.py --selftest        # 自我測試,不碰任何遊戲檔

--set 的第一個參數也可以直接打名字,但名字對到兩位以上就會停手要你改用識別碼:
投打二刀流的球員在名冊裡本來就佔兩列(一列打者、一列投手),Ohtani 就是這種。
識別碼是每一列最左邊那一串,用 --find 查得到。

零相依：只用 Python 3.7+ 內建功能，不必安裝任何東西。
自包含：整支腳本就是這一個檔，可以單獨複製出去用。

── 它到底在做什麼 ────────────────────────────────────────
遊戲怎麼知道某位球員長什麼臉?看名冊裡那一列的 playerattrib_face 欄。
本工具就只做一件事:把那一格的數字換掉,同一列其他的位元組原封不動。

吃什麼(輸入)
  · 命令列第一個參數:遊戲安裝資料夾(它的下一層要有 data 這個子資料夾)
  · data/database/attrib.dat:純文字名冊,CRLF 換行,每一格自己帶著欄位編號
  · data/models.big:**只讀目錄**,拿來知道 c001…c### 這些臉皮哪些真的存在。
    讀不到照樣能跑,總覽跟 --find 照印,只是不能幫你檢查編號存不存在;
    那時候它會說「不知道」,不會把「不知道」報成「不存在」。
    ⚠️ 但「不知道」不等於放行:要換的是 1-900 的專屬臉編號又加了 --apply,
    它會直接停手不寫入(畫面上是「無法確認,所以不寫入」)。
    要寫得進去,得先讓它讀得到 models.big。

吐什麼(輸出)
  · --find,以及沒加 --apply 的 --set:全部只印在畫面上,一個檔案都不動
  · 加了 --apply:改寫 attrib.dat 的那一列,並在旁邊留下 attrib.dat.facebak
  · --restore:把 attrib.dat.facebak 蓋回 attrib.dat

安全網(五層,由外而內)
  1. 預設唯讀,但這一句只涵蓋 --set:不加 --apply 一律只做預覽。
     --restore 不在這一句裡。它是另一條路,不看 --apply,備份通過覆蓋前那幾道把關之後,
     就把 attrib.dat.facebak 整份蓋回 attrib.dat。本站把測試機那份 attrib.dat
     (840,643 bytes)複製到別的資料夾實測,只下 --restore、沒有加 --apply,
     那份複本的 MD5 當場變成備份的 MD5。
  2. 寫之前先確認編號:要換的是 1-900 的專屬臉,而 models.big 裡沒有它、
     或 models.big 根本沒讀到,加了 --apply 一律停手不寫入。預覽不擋,
     讓你看完再決定;真的要動檔案才擋。
     (本站測試機那份 models.big 有 894 張臉皮、c001 到 c900 之間缺 6 個號。
      拿它缺的 c116 加 --apply 實測:attrib.dat 的 md5 前後相同,
      連 attrib.dat.facebak 都不會產生)
  3. 第一次真的寫入之前自動備份成 attrib.dat.facebak。備份是原子的
     (先寫一個名字猜不到的暫存檔、fsync、讀回來逐位元組比對,全過了才 os.replace
     換名),不會留下半截檔;之後再改幾次都不覆蓋
     最早那一份,所以永遠回得去你動手之前的狀態。
     旁邊已經有一份 attrib.dat.facebak 的時候,不是看到「存在」就放行:
     那一份會先跑一次跟 --restore 同一套檢查,壞的話在寫入之前就停手。
     (不然會變成「改得進去、還原不回來」—— 那正好是最糟的組合。)
  4. 寫入也是原子的,而且暫存檔的名字猜不到(tempfile.mkstemp,底層 O_CREAT|O_EXCL):
     事先在旁邊放一個同名的符號連結想騙它去寫別的地方,佔不到位;
     **任何要寫的目的檔本身是符號連結一律停手** —— 名冊、備份、暫存檔都一樣,
     不會跟著連結去改別的檔(路徑中間的資料夾是連結不擋,只看最後那一個檔;
     讀取也不擋)。不會出現寫到一半的名冊。
     換名(os.replace)跟「把換過了記下來」是同一段不可中斷的動作:
     Ctrl-C 落在中間會被壓到那一段結束才丟出來,所以收尾訊息說的
     「有沒有動到你的檔案」跟磁碟上的狀態永遠一致(exit code 130)。
  5. 寫完立刻重讀複驗:行數要一樣、改動行數要剛好 1、那一格要真的是新值。
     任何一項不符,它會**自己**拿剛才那份備份還原回去(退不回去才請你自己
     下 --restore),而且一律以非 0 的 exit code 收場,不會靜靜地回報成功
  另外 --restore 與 --apply 之前都會先驗那份備份,五道:開頭是欄位表、
  檔案裡有 CRLF、表頭找得到 first_name 與 last_name、整份以 CRLF 收尾、
  最後一列的欄數跟第一列一樣。後兩道專門對付截斷 —— 截在一列中間的話,
  那一列的欄數一定湊不齊。(本站這台機器上找得到的 18 份 attrib.dat —— 含三份
  剛安裝好的原版與 2009 年以來的社群名冊 —— 這五道全部通過,沒有一份被誤擋;
  同一批檔各切兩種半截共 36 個,36 個都被擋下。)
  截斷處剛好落在換行邊界上的話,這五道看不出來(那份 840,643 個位元組的名冊裡
  有 3,248 個換行邊界)。所以還有第六道:備份的球員列數比現在這個檔少就停手 ——
  還原不可以讓名冊變短。反過來(備份比較長)照做,因為那是
  「壞掉的是現在這個檔、備份來救它」。
  這六道 --restore 與 --apply 跑的是同一支函式,所以「改得進去」與
  「還原得回來」永遠是同一個答案,不會改完才發現退不回去。

做不到的事(先說在前面)
  · **不會做新的臉皮。** models.big 全程唯讀,連解壓都沒有。想放一張遊戲裡
    本來沒有的臉,那是另一課的事。
  · **不會幫你改 photo 欄。** 本站量到剛安裝好的原版裡 photo=2 的球員,
    臉皮 100% 落在 901-915,那種球員光改 face 不一定看得出差別。
  · 不保證「換完在遊戲裡好看」。本工具只保證那個欄位被改成你指定的數字,
    畫面上長什麼樣本站沒驗。
  · 一次只改一列。這是刻意的:複驗那句「改動行數 = 1」才有意義。
  · 不會替你判斷編號選得好不好。撞到別人只會提醒一句,照樣寫得進去
    (抄別位球員的編號本來就是正常做法)。但「models.big 裡沒有這張」跟
    「models.big 沒讀到」不只是提醒:編號落在 1-900 又加了 --apply,
    一律停手不寫入。

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
import stat
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
#
# ── 2026-09-05 第二輪唯讀稽核抓到的:暫存檔的名字可以被預先佔位 ──────────
# 原本寫的是 part = dst + '.part',名字完全猜得到;而 shutil.copy2() 會
# **跟著符號連結走**。有人(或別的程式)先在旁邊放一個 attrib.dat.facebak.part
# 指向資料夾外面的某個檔,那個檔會在 os.replace() 之前就被開起來截成 0 再寫入 ——
# os.replace() 事後只換掉連結本身,但外面那個檔早就沒了。
# 現在改成 tempfile.mkstemp(dir=目的檔那個資料夾):名字帶隨機字尾,而且底層是
# O_CREAT|O_EXCL 開的 —— 已經存在的名字一律開不起來,佔不到位。
# 目的檔自己也要查:是符號連結就停手不寫(見 _link_guard)。
# ⚠️ Path.exists() / os.path.exists() 對「指向不存在目標的符號連結」會回 False,
#    所以那道要用 os.path.islink / os.lstat,不能用 exists 代替。

# 「換名」做過沒有 —— 每成功一次 os.replace 就往這裡記一筆 (種類, 路徑)。
# 為什麼要記:Ctrl-C 的收尾訊息原本無條件印「沒有改到任何檔案」,可是中斷點
# 如果落在 os.replace 之後(複驗、印字都還在後面),那句話就是假的 ——
# 使用者以為什麼都沒發生,實際上名冊已經被換掉了。
# 種類有三種:'backup'(只產生了 .facebak)、'set'(名冊被改了)、
# 'restore'(名冊已經被備份蓋回去了)。
_REPLACED = []

# ── 2026-09-06 第三輪唯讀稽核抓到的:Ctrl-C 落在「換名」與「登記」之間 ──────
# 上面那份 _REPLACED 是換名之後才記的,而「os.replace 這一行」跟「append 這一行」
# 是兩個獨立的動作。Ctrl-C 剛好落在中間的話,收尾訊息看到的還是舊狀態,
# 於是印出「沒有改到任何檔案」—— 名冊其實已經被換掉了。窗口很窄,但它是真的。
#
# 兩道一起上:
#   (a) _NoInterrupt 把「換名 + 登記」包成一段不可中斷的動作。這段期間收到的
#       SIGINT 先記著,離開這段之後再照常丟出 —— 所以收尾看到的登記
#       一定跟磁碟上的狀態一致。
#   (b) _INFLIGHT 是保險:進入那段之前先登記「正在換 X」。(a) 失效的時候
#       (例如不在主執行緒,signal.signal 裝不上去)還有這一層,
#       收尾會說「中斷時正在替換 X」,不會說「沒動到」。
_INFLIGHT = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開這段之後再丟。

    這樣 KeyboardInterrupt 的收尾看到的 _REPLACED 一定跟磁碟上的狀態一致。
    裝不上處理器的情況(不在主執行緒等)就退回原本行為 —— 不會比以前更糟,
    而且還有 _INFLIGHT 那一層保險。
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


def _replace_and_record(tmp, dst, kind):
    """換名,然後登記 —— 兩件事之間不接受中斷。

    三態:進來之前是「還沒動」,_INFLIGHT 有東西是「正在換」,
    _REPLACED 有東西是「已經換過」。收尾訊息就照這三態說話。
    """
    _INFLIGHT.append((kind, dst))
    try:
        with _NoInterrupt():
            os.replace(tmp, dst)        # os.replace 是原子的
            _REPLACED.append((kind, dst))
    except Exception:
        # os.replace 自己失敗(磁碟滿、跨裝置、權限):它要嘛整個成功要嘛完全沒動,
        # 所以走到這裡可以確定沒換成,「正在換」撤掉是安全的。
        # ⚠️ 這裡刻意只接 Exception 不接 BaseException:KeyboardInterrupt 走到這裡
        #    的時候「換成了沒有」是不確定的,那一筆就要留在 _INFLIGHT 裡讓收尾說實話。
        _INFLIGHT.pop()
        raise
    _INFLIGHT.pop()


def _link_guard(p, what):
    """目的檔是符號連結(或 Windows 的 reparse point)就停手,不寫。

    換名用的 os.replace 只會換掉連結本身,看起來很安全;但**寫之前**那個開檔
    動作會跟著連結走,先把連結指到的那個檔截斷。所以要擋在開檔之前。
    (父資料夾是連結不擋 —— 外接碟、mod 管理器做的目錄連結都很正常。
     暫存檔一律開在目的檔解析過後的真實資料夾裡,所以照樣落在同一個位置。)
    """
    p = os.fspath(p)
    try:
        st = os.lstat(p)               # lstat 不跟著連結走,dangling 也看得到
    except OSError:
        return                          # 不存在就沒有連結問題
    is_link = os.path.islink(p)
    # Windows 的 junction / reparse point:os.path.islink() 不見得認得。
    if not is_link and hasattr(st, 'st_file_attributes'):
        is_link = bool(st.st_file_attributes
                       & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
    if is_link:
        raise DataError(
            '%s 是一個符號連結:\n'
            '    %s\n'
            '  寫進去會動到連結指向的那個檔,不是你以為的那個 —— 所以停手,\n'
            '  一個位元組都沒有動。請先把那個連結刪掉(或改個名字)再跑一次。'
            % (what, p))


def _open_tmp_beside(dst, tag):
    """在 dst 真正所在的那個資料夾裡開一個獨佔的暫存檔,回傳 (fd, 路徑)。

    名字猜不到(mkstemp 會加隨機字尾),而且底層用 O_CREAT|O_EXCL ——
    事先放一個同名的連結在那裡也佔不到位,開檔會直接失敗。
    跟目的檔同一個資料夾是 os.replace 換名要能原子完成的前提。
    """
    dst = os.fspath(dst)
    d = os.path.dirname(os.path.realpath(dst)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(dst) + '.' + tag + '-')


def _sha256(p):
    """整個檔的 SHA-256(分段讀,不把整份塞進記憶體)。"""
    h = hashlib.sha256()
    with open(os.fspath(p), 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _atomic_copy(src, dst, tag='part', kind='backup'):
    """把 src 的內容原子地放到 dst —— 要嘛完整、要嘛 dst 原封不動。

    五步,少一步都不算原子:
      1. 開一個**猜不到名字**的獨佔暫存檔(同一個資料夾)
      2. 寫完 flush + os.fsync,確定內容真的落到磁碟才往下走
      3. 把權限帶過去(目的檔本來就在的話以它為準)
      4. 讀回來算 SHA-256,跟來源逐位元組對過
      5. 都通過才 os.replace 換名 —— 而且換名與登記綁在一起(_replace_and_record),
         中間不接受 Ctrl-C,收尾訊息才不會說「沒動到」。
    任何一步失敗就把暫存檔收掉,dst 這個名字上不會出現半截的檔。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _link_guard(dst, '要寫入的 %s' % os.path.basename(dst))
    fd, tmp = _open_tmp_beside(dst, tag)
    try:
        h = hashlib.sha256()
        # fdopen 寫在前面:萬一 open(src) 失敗,fd 也會被關掉,不會漏。
        with os.fdopen(fd, 'wb') as fout, open(src, 'rb') as fin:
            for chunk in iter(lambda: fin.read(1 << 20), b''):
                h.update(chunk)
                fout.write(chunk)
            fout.flush()
            os.fsync(fout.fileno())     # 換名之前先確定內容真的落到磁碟
        # 權限與時間:先照來源那一份(還原時 = 備份,備份時 = 遊戲檔),
        # 目的檔本來就在的話再以它為準 —— 使用者刻意設成唯讀(444)保護的檔
        # 不該因為被還原過一次就把那道鎖弄丟。
        try:
            shutil.copystat(src, tmp)
        except OSError:
            pass
        if os.path.exists(dst):
            try:
                shutil.copymode(dst, tmp)
            except OSError:
                pass
        # 複驗:寫下去的東西要跟來源逐位元組相同,對不上就不換名。
        # (2026-08-29 那次 300 KB 蓋掉 2.66 MB,就是因為沒有人回頭讀一次。)
        if _sha256(tmp) != h.hexdigest():
            raise DataError(
                '寫出來的內容跟來源對不上,所以不換名 —— %s 一個位元組都沒被動到。'
                % os.path.basename(dst))
        # 換名 + 登記是同一段不可中斷的動作(理由見檔案上面 _replace_and_record)。
        _replace_and_record(tmp, dst, kind)
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
    # ⚠️ 這裡不能用 os.path.exists:備份如果是一個指向不存在目標的符號連結,
    #    exists() 會回 False,錯誤訊息就會變成「找不到備份」,把真正的問題
    #    (那是一個壞掉的連結)藏起來。lexists 看得到連結本身。
    if not os.path.lexists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    if not os.path.exists(bak):
        raise SystemExit('備份 %s 是一個連結,而它指向的檔案不存在 —— 不敢拿它還原。' % bak)
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
    # (用 exists 是對的:這一道比的是「要被蓋掉的那個檔有多大」,
    #  檔案不在就沒有東西要比。dst 是不是連結由 _atomic_copy 的 _link_guard 擋。)
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


# 上面那幾道都沒喊停才會走到這裡。整支腳本真正「用備份蓋掉正本」的動作只有這裡。
# ⚠️ 這裡原本是直接 shutil.copy2(bak, dst)。複製途中被中斷(磁碟滿、外接碟拔掉、
#    按了 Ctrl-C)會在 attrib.dat 這個名字上留下一個半截的名冊 —— 備份寫得那麼小心,
#    還原卻不是原子的,等於前面那幾道白做。改成走 _atomic_copy:
#    先寫一個名字猜不到的暫存檔(同一個資料夾)、fsync、逐位元組複驗,
#    全過了才 os.replace 換名。中斷只會留下那個暫存檔,attrib.dat 完好。
#    (_atomic_copy 會把備份的權限與修改時間帶回去。)
def _do_copy(bak, dst):
    # 登記('restore')由 _replace_and_record 在換名的同一段裡做掉,這裡不另外記 ——
    # 分開記就會又長出一個「換完了還沒記」的窗口,那正是這一輪要關掉的東西。
    _atomic_copy(bak, dst, tag='restore', kind='restore')




# Windows 的命令提示字元預設用 cp950，直接印中文會炸掉。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ⚠️ 2026-08-25:欄位編號不寫死。
#    不同來源的名冊,欄位排列順序不一樣 —— 拿剛安裝好的原版跟裝過台灣模組的
#    那台比,兩份的表頭都是 46 個具名欄位(編號 0 到 45)、名稱集合也相同,
#    但順序不同:playerattrib_skin_tone 在原版是第 12 欄、在這台是第 38 欄,
#    中間那 26 欄整批往前挪一格,46 欄裡有 27 欄的編號對不上。
#    (拿逗號去切表頭會切出 47 格,最後一格是收尾的 ';',不是欄位。)
#    playerattrib_face 剛好兩邊都在第 10 欄,但那是運氣不是設計,
#    所以改成執行時從表頭找。(同一個問題在 mvp_edit_speed.py 上真的踩到了。)
FACE_NAME = 'playerattrib_face'
FACE_FIELD = None        # 由 resolve_field() 在執行時決定
# 名與姓的欄位編號。這兩格只拿來「找人」跟「印給你看」,寫入時碰都不碰,
# 所以不像 face 那樣需要每次從表頭反查。
NAME_FIRST = 0
NAME_LAST = 1
GENERIC_MIN = 901        # 901 以上是通用臉，不對應 models.big 的 c###
# 目錄項目數的理智上限。BIGF 檔頭那個數字若被改壞(或那根本不是 BIGF),
# 拿它去乘就會要求配置天文數字的記憶體。這是「明顯不合理就停手」的門檻,
# 不是格式規定的最大值。
MAX_BIG_ENTRIES = 100000


class DataError(Exception):
    """檔案不存在或格式不符預期。訊息是給人看的。"""


# ─────────────────────────────────────────────────────────
#  BIG 封裝檔:只讀目錄,不解壓
# ─────────────────────────────────────────────────────────
def big_entry_names(path):
    """回傳 .big 目錄裡的所有項目名稱。只讀檔頭與目錄,外加目錄後面一小段餘量,不解壓也不寫入。"""
    # BIGF 的檔頭固定 16 個位元組:
    #   0-4    magic,就是 'BIGF' 四個字母
    #   4-8    整個檔案的長度
    #   8-12   目錄裡有幾個項目(**大端序**,EA 在這個欄位不用小端)
    #   12-16  資料區的起點
    # 底下只讀檔頭與目錄,不解壓也不寫入 models.big。
    # 但目錄長度不固定,所以會多讀一小段當餘量,這一小段會蓋到資料區的最前面。
    # 本站測試機那份 models.big(561,891,312 位元組,目錄 4,211 項)總共讀進記憶體
    # 273,616 位元組,而檔頭宣告資料區從 73,322 起算,等於有 200,294 位元組的資料區
    # 也進了記憶體;剛安裝好的原版那份(172,992,803 位元組,目錄 2,671 項)是讀 175,056、
    # 資料區起點 46,780,多讀 128,276。
    # 多讀的那一段不會被當成目錄項目解析:兩份都在資料區起點之前就走完 count 項。
    # 所以「不解壓、不會改到它」成立,但「一個位元組都不碰」照字面講是誇大的。
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            # 目錄長度不固定(名稱是變長字串),保守多讀一些再逐項解析
            blob = head + f.read(count * 64 + 4096)
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))

    # 目錄的每一項 = 4 bytes 位移 + 4 bytes 長度 + 一個 0x00 收尾的名字。
    # 名字是變長的,所以「第 N 項在哪裡」沒辦法直接算,只能從頭一項一項走。
    names = []
    pos = 16
    for i in range(count):
        if pos + 8 > len(blob):
            break                                  # 目錄比預估長,已讀到的就夠用
        pos += 8                                   # 跳過 offset 與 size
        end = blob.find(b'\x00', pos)
        if end < 0:
            break
        names.append(blob[pos:end].decode('latin-1', 'replace'))
        pos = end + 1
    return names


# 只認「c + 剛好三位數字 + .fsh」這種名字。models.big 裡還有球衣、球棒之類的
# 東西,不長這樣的一律不算臉皮。寧可少認,不要把不是臉的東西算進來。
def available_faces(models_big):
    """models.big 裡實際存在的臉皮編號集合(c001.fsh → 1)。"""
    faces = set()
    for n in big_entry_names(models_big):
        m = re.fullmatch(r'c(\d{3})\.fsh', n)
        if m:
            faces.add(int(m.group(1)))
    return faces


# ─────────────────────────────────────────────────────────
#  attrib.dat:純文字,但每一格都帶欄位編號
# ─────────────────────────────────────────────────────────
# 這個函式會擋下四種狀況,但第一種跟後面三種不是同一回事:讀不到這個檔
# (路徑拖錯、檔名打錯)走的是下面那個 OSError 分支;剩下三道才是格式檢查,
# 依序是開頭像不像欄位表(不像多半是拿到了別的檔)、有沒有 CRLF(這個檔被
# 一般文字編輯器存過,換行被換成 LF)、行數夠不夠(連表頭加一列球員都湊不齊
# 的檔,不值得再往下猜)。CRLF 那一道本站沒驗遊戲會怎麼反應,但檔案已經跟
# 原本不同了,所以一律擋下來不動它。
def read_attrib(path):
    """回傳 (原始 bytes, [每列的 bytes])。刻意不解碼整份,寫回時才能保證 byte 一致。"""
    try:
        raw = open(path, 'rb').read()
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))
    if not raw[:1].isdigit():
        raise DataError('%s 的開頭不像欄位表,可能不是 attrib.dat' % os.path.basename(path))
    if b'\r\n' not in raw:
        raise DataError('%s 沒有 CRLF 換行,可能已被編輯器改壞' % os.path.basename(path))
    lines = raw.split(b'\r\n')
    if len(lines) < 3:
        raise DataError('%s 只有 %d 行,內容不完整' % (os.path.basename(path), len(lines)))
    return raw, lines


# 名冊的第一行是表頭,長成「0 first_name,1 last_name,…」這樣:
# 每一格自己帶著欄位編號。所以欄位順序可以不一樣,編號才是身分。
def header_names(line_bytes):
    """表頭:{欄位編號: 欄位名}"""
    out = {}
    for c in line_bytes.split(b','):
        m = re.match(rb'^\s*(\d+) (\w+)', c)
        if m:
            out[int(m.group(1))] = m.group(2).decode('latin-1')
    return out


# 從表頭反查欄位編號,而不是寫死。理由見檔案上面那段 ⚠️:
# 兩份名冊的表頭都是 46 個具名欄位、欄位名稱的集合也相同,順序卻不一樣。
# (下面錯誤訊息印的「它有 %d 個欄位」數的就是這 46 個具名欄位。)
def resolve_field(lines, wanted_name):
    """從表頭找出某個欄位真正的編號。找不到就明白說,不要猜。"""
    names = header_names(lines[0])
    for num, nm in names.items():
        if nm == wanted_name:
            return num
    raise DataError(
        '這份名冊的表頭裡找不到 %s 這個欄位。\n'
        '  它有 %d 個欄位。這支腳本不敢在看不懂的檔案上動手。'
        % (wanted_name, len(names)))


# 取一格的值。回傳 None 有兩種意思:這一列沒有那麼多格、或那一格開頭的欄位
# 編號跟預期對不上。兩種都當成「讀不出來」:寧可少報,也不要猜。
def cell_value(line_bytes, field):
    """取第 field 欄的值。資料列行首多一個識別碼,所以位置是 field+1。"""
    cells = line_bytes.split(b',')
    idx = field + 1
    if idx >= len(cells):
        return None
    m = re.match(rb'^(\d+) ?(.*)$', cells[idx].strip())
    if not m or int(m.group(1)) != field:
        return None                                # 欄位編號對不上就不猜
    return m.group(2).decode('latin-1')


# 每一列開頭那一格就是識別碼,是這份名冊裡的唯一身分。
# 同名球員只能靠它區分,所以 --set 建議一律用它而不是名字。
def row_id(line_bytes):
    return line_bytes.split(b',')[0].decode('latin-1')


# 逐列走整份名冊。名或姓讀不出來就跳過:那不是一列正常的球員資料,
# 硬解只會把統計數字弄髒。
def iter_players(lines):
    """逐列產出 (行號, row-id, 名, 姓, face)。跳過表頭與空行。"""
    for i, l in enumerate(lines):
        if i == 0 or not l.strip():
            continue
        first = cell_value(l, NAME_FIRST)
        last = cell_value(l, NAME_LAST)
        face = cell_value(l, FACE_FIELD)
        if first is None or last is None:
            continue
        yield i, row_id(l), first, last, face


# ─────────────────────────────────────────────────────────
#  各種動作
# ─────────────────────────────────────────────────────────
# 沒給 --find 也沒給 --set 時的預設動作:整份名冊點一次名,回答
# 「幾位有專屬臉、幾位用通用臉、有沒有人指向不存在的臉」。全程唯讀。
def cmd_overview(lines, faces):
    custom = generic = zero = broken = 0
    dangling = []
    for _, rid, first, last, face in iter_players(lines):
        if face is None or not face.isdigit():
            broken += 1
            continue
        v = int(face)
        if v == 0:
            zero += 1
        elif v >= GENERIC_MIN:
            generic += 1
        else:
            custom += 1
            if faces is not None and v not in faces:
                dangling.append((first, last, v))

    # 四個桶子互斥,所以總數直接相加就好,不另外數一次,
    # 免得兩個數字對不起來的時候不知道該信哪一個。
    total = custom + generic + zero + broken
    print('\n【總覽】共 %d 位球員' % total)
    print('  有專屬臉皮 (1-%d)  : %5d 位  (%.1f%%)' % (GENERIC_MIN - 1, custom, pct(custom, total)))
    print('  用通用臉  (%d 以上) : %5d 位  (%.1f%%)' % (GENERIC_MIN, generic, pct(generic, total)))
    print('  沒有指定  (0)       : %5d 位' % zero)
    if broken:
        print('  讀不出 face 欄     : %5d 位' % broken)
    # ⚠️ 「讀不到 models.big」跟「讀到了、但裡面沒有這張臉」是兩件事。
    #    這裡原本混在一起:讀不到時 faces 是空集合,於是每一位有專屬臉的
    #    球員都被算成「指向不存在的臉皮」,還附一句「你的 models.big 被換過」。
    #    拿剛安裝好的原版跑,會被告知 465 位球員的臉全壞了 —— 而它其實好好的。
    if faces is None:
        print('\n  models.big 沒讀到,所以「不知道」裡面有幾張臉。')
        print('  下面只報名冊自己的統計,不判斷臉皮存不存在。')
        return
    print('\n  models.big 裡實際有 %d 張臉皮' % len(faces))

    if dangling:
        print('\n  ⚠ 有 %d 位球員指向不存在的臉皮:' % len(dangling))
        for first, last, v in dangling[:10]:
            print('      %s %s → c%03d(models.big 裡沒有這張)' % (first, last, v))
        if len(dangling) > 10:
            print('      …另外還有 %d 位' % (len(dangling) - 10))
        print('  這通常代表你的 models.big 被換過,而球員資料沒跟著更新。')
    else:
        print('\n  ✅ 沒有球員指向不存在的臉皮')


# --find:查名字。名跟姓都比對,一律轉小寫再比。最多印 40 位,
# 印不完時提示「名字打完整一點」,比一次噴一千行有用。
def cmd_find(lines, faces, keyword):
    kw = keyword.lower()
    hits = [(i, rid, f, l, face) for i, rid, f, l, face in iter_players(lines)
            if kw in f.lower() or kw in l.lower()]
    if not hits:
        print('\n找不到名字含「%s」的球員。' % keyword)
        print('提示:名字要用檔案裡的英文拼法,例如 Ohtani 而不是「大谷」。')
        return
    print('\n找到 %d 位:' % len(hits))
    print('  %-10s %-14s %-14s %-8s %s' % ('識別碼', '名', '姓', 'face', '狀態'))
    for i, rid, first, last, face in hits[:40]:
        print('  %-10s %-14s %-14s %-8s %s' % (rid, first, last, face or '?', face_status(face, faces)))
    if len(hits) > 40:
        print('  …另外還有 %d 位(名字打完整一點可以縮小範圍)' % (len(hits) - 40))
    if len(hits) > 1:
        print('\n  同名的話,用識別碼指定比較保險:--set <識別碼> <編號>')


# 把一個 face 值翻成人看得懂的一句話。faces 是 None 的時候只說「無法確認」,
# 絕不說「不存在」。這兩件事在這支腳本裡從頭到尾都分得很開。
def face_status(face, faces):
    if face is None or not face.isdigit():
        return '讀不出來'
    v = int(face)
    if v == 0:
        return '沒有指定'
    if v >= GENERIC_MIN:
        return '通用臉'
    if faces is None:
        return '專屬臉 c%03d(沒讀到 models.big,無法確認)' % v
    return '專屬臉 c%03d' % v if v in faces else '⚠ 指向不存在的 c%03d' % v


# 百分比。分母是 0 的時候回 0,不讓一份空名冊變成除以零的錯誤訊息。
def pct(a, b):
    return a / b * 100 if b else 0.0


# 先用識別碼精準比對,對不到才退回用名字。名字對到兩位以上一律停手:
# 投打二刀流的球員在名冊裡本來就佔兩列(一列打者、一列投手),
# 也真的有不同球員剛好同名,猜錯就是改到另一個人。
def find_target(lines, who):
    """who 可以是識別碼或名字。回傳唯一那一列,不唯一就報錯。"""
    exact = [(i, rid, f, l, face) for i, rid, f, l, face in iter_players(lines) if rid == who]
    if len(exact) == 1:
        return exact[0]
    kw = who.lower()
    hits = [(i, rid, f, l, face) for i, rid, f, l, face in iter_players(lines)
            if kw == f.lower() or kw == l.lower() or kw == ('%s %s' % (f, l)).lower()]
    if not hits:
        raise DataError('找不到「%s」。先用 --find %s 查查看正確拼法。' % (who, who))
    if len(hits) > 1:
        msg = ['「%s」對到 %d 位球員,請改用識別碼指定:' % (who, len(hits))]
        for i, rid, f, l, face in hits[:10]:
            msg.append('    %s  %s %s  (目前 face=%s)' % (rid, f, l, face))
        raise DataError('\n'.join(msg))
    return hits[0]


# 整支腳本唯一會產生新內容的地方。做法是把整列切成一格一格,只換其中一格,
# 再用逗號接回去,其餘的空白、大小寫、位元組全部原封不動。
# 換之前先確認那一格真的以「<欄位編號> 」開頭,對不上就寧可不動。
def build_new_line(line_bytes, new_face):
    """把 face 欄(FACE_FIELD,執行時從表頭決定)換成新值,其餘 byte 原封不動。"""
    cells = line_bytes.split(b',')
    idx = FACE_FIELD + 1
    if idx >= len(cells):
        raise DataError('這一列沒有第 %d 欄,不敢動' % FACE_FIELD)
    old = cells[idx]
    m = re.match(rb'^(\s*)(\d+) ?(.*)$', old)
    if not m or int(m.group(2)) != FACE_FIELD:
        raise DataError('第 %d 欄的內容是 %r,不是預期的「%d <值>」格式,不敢動'
                        % (FACE_FIELD, old, FACE_FIELD))
    cells[idx] = b'%s%d %d' % (m.group(1), FACE_FIELD, new_face)
    return b','.join(cells)


# --set:換臉的主流程。順序是刻意排的:
#   找人 → 檢查編號在不在 models.big 裡 → 提醒撞號 → 印預覽
#   →(要 --apply 才)備份 → 原子寫入 → 重讀複驗。
# 前面每一道都可能喊停,而喊停的時候檔案一個位元組都還沒被動過。
def cmd_set(path, raw, lines, faces, who, new_face, apply_it):
    i, rid, first, last, face = find_target(lines, who)

    # 第一道:你給的這個編號到底存不存在?三種情況分開處理:
    # 讀不到 models.big(不知道)、讀到了但裡面沒有這張(不存在)、有這張(放行)。
    # 前兩種都會先警告;只有加了 --apply 才真的擋下來,預覽一律讓你看完。
    if faces is None and new_face != 0 and new_face < GENERIC_MIN:
        print('\n⚠ models.big 沒讀到,所以無法確認 c%03d 這張臉在不在。' % new_face)
        if apply_it:
            raise DataError('無法確認,所以不寫入。先確認遊戲資料夾路徑對不對。')
    elif faces is not None and new_face != 0 and new_face < GENERIC_MIN and new_face not in faces:
        print('\n⚠ models.big 裡沒有 c%03d 這張臉。' % new_face)
        print('  換下去遊戲可能顯示成通用臉或出問題。')
        print('  可用的編號範圍:c%03d – c%03d(共 %d 張)'
              % (min(faces), max(faces), len(faces)) if faces else '  (讀不到可用編號)')
        if apply_it:
            raise DataError('為安全起見不寫入。確定要用這個編號的話,先確認 models.big 有它。')

    # ── 撞號提醒 ────────────────────────────────────────────
    # 臉皮編號在 EA 原版只用到 c606:兩份剛安裝好的原版(英文版與中文版,models.big
    # 都是 172,992,803 bytes)量到的 504 張臉全部落在 c001-c606,c607-c900 是 0 張。
    # 所以那一段的意思是「沒人占用」,不是「有臉可以換」。上面第一道檢查會擋下
    # models.big 裡沒有的編號,所以在剛安裝好的原版上拿 c700 去 --apply 會直接被拒絕。
    # 裝過模組的就不一定:本站測試機那份 models.big 有 894 張,c607-c900 占了 294 張。
    # 拿一個「已經有別人在用」的編號來換,不會出錯,但那個人的臉就跟你一樣了。
    # 2009 年那份台灣之光模組用了 15 個 EA 範圍內的編號,其中 14 個撞號 ——
    # 他們的做法是把被撞到的現役球員改成通用臉,退休球員直接不放進名冊。
    # 那是有人一個一個決定的。這裡只負責讓你知道有這回事。
    if new_face != 0 and new_face < GENERIC_MIN:
        others = []
        for j, ln in enumerate(lines[1:], start=1):
            if j == i or not ln.strip():
                continue
            v = cell_value(ln, FACE_FIELD)
            if v and v.strip().isdigit() and int(v) == new_face:
                others.append('%s %s' % (cell_value(ln, NAME_FIRST) or '?', cell_value(ln, NAME_LAST) or '?'))
        if others:
            print('\n⚠ c%03d 目前已經有 %d 位球員在用:' % (new_face, len(others)))
            for o in others[:5]:
                print('     %s' % o.strip())
            if len(others) > 5:
                print('     …另外還有 %d 位' % (len(others) - 5))
            print('  換下去不會出錯,但他們會跟你改的這位長同一張臉。')
            print('  想避開的話,挑一個 models.big 裡有、名冊裡卻沒人用的編號。')
            print('  c607 以上 EA 原版沒有指派給任何人,但剛安裝好的原版那一段')
            print('  一張臉也沒有,指過去會被上面第一道檢查擋下,不能 --apply。')

    # 到這一行為止,檔案一個位元組都還沒動。下面先把新的那一列做出來,
    # 目的只是印預覽給你看,沒有 --apply 就到此為止。
    old_line = lines[i]
    new_line = build_new_line(old_line, new_face)

    print('\n【預覽】%s %s  (識別碼 %s)' % (first, last, rid))
    print('  第 %d 欄 playerattrib_face' % FACE_FIELD)
    print('    原本:%s   %s' % (face, face_status(face, faces)))
    print('    改成:%-5d %s' % (new_face, face_status(str(new_face), faces)))

    if old_line == new_line:
        print('\n  這一列已經是這個值了,不需要改動。')
        return

    print('\n  這一列的位元組:%d → %d' % (len(old_line), len(new_line)))

    if not apply_it:
        print('\n  以上只是預覽,沒有改到任何檔案。')
        print('  確定要改的話,在同一行指令最後加上 --apply')
        return

    # 這一道要擋在**備份之前**:名冊本身是符號連結的話,連備份都不該產生 ——
    # 產生了只會讓人以為「有備份、應該有動到什麼」。
    _link_guard(path, '要寫入的 %s' % os.path.basename(path))

    # 只有第一次 --apply 會建立備份,之後再改幾次都保留最早那一份。
    # 「回得去的」要是你動手之前的原始狀態,不是上一次改完的狀態。
    backup = path + '.facebak'
    if not os.path.lexists(backup):
        # 登記('backup')在 _replace_and_record 裡跟換名綁在一起,這裡不另外記。
        _atomic_copy(path, backup, kind='backup')
        print('\n  已備份 → %s' % os.path.basename(backup))
    else:
        # ⚠️ 既有的備份也要驗過才能信。只看「存不存在」的話,旁邊躺著一份
        #    0 bytes 或半截的 .facebak 會讓這裡直接放行 —— 遊戲檔改下去了,
        #    之後 --restore 又拒收那份備份,使用者沒有退路。
        #    這裡跑的就是 --restore 那一支把關函式,所以「改得進去」與
        #    「還原得回來」永遠是同一個答案。
        check_backup_usable(backup, path, '這次不寫入')
        print('\n  備份已存在,保留最早那一份 → %s' % os.path.basename(backup))

    new_lines = list(lines)
    new_lines[i] = new_line
    out = b'\r\n'.join(new_lines)

    # 先整份寫到一個暫存檔,再用 os.replace 換名。擋得住的是「腳本中途被打斷」
    # (按 Ctrl-C、磁碟滿、外接碟被拔):那時候留下來的是那個暫存檔,attrib.dat 完好。
    # ⚠️ 暫存檔的名字**不可以**是 path + '.tmp' 這種猜得到的:事先在旁邊放一個
    #    同名的符號連結指向資料夾外面,open(..., 'wb') 會跟著它走,把外面那個檔
    #    截成 0 —— 而 os.replace 之後只換掉連結,外面那個檔已經回不來了。
    #    mkstemp 的名字帶隨機字尾又是 O_CREAT|O_EXCL 開的,佔不到位。
    #    目的檔自己是連結的話一樣停手(上面建備份之前就查過了)。
    # 換名之前 fsync:內容確定落到磁碟才換名。(換名這個動作本身在斷電下的
    # 持久性仍由檔案系統決定,本站沒有辦法對「拔電源」給保證。)
    fd, tmp = _open_tmp_beside(path, 'tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(out)
            f.flush()
            os.fsync(f.fileno())
        # 換名之前先把原本那個檔的權限套到新檔上。新建的檔套的是行程的 umask,
        # 不補這一步的話,600 會變成 644、使用者刻意設成唯讀(444)保護的名冊
        # 會在改完之後連那道鎖都被拿掉。備份那邊也有帶,這樣兩邊才一致。
        # (Windows 上只有唯讀那一位有意義,套過去不會出事。)
        try:
            shutil.copymode(path, tmp)
        except OSError:
            pass                # 權限套不回去不該讓整次寫入失敗,內容才是重點
        # 換名之前讀回來對一次:磁碟寫滿、外接碟出狀況的時候,write() 不見得會叫。
        # 對不上就不換名,attrib.dat 一個位元組都不會被動到。
        # (跟備份那邊走同一個 _sha256,兩處的「讀回來比對」是同一個出口。)
        if _sha256(tmp) != hashlib.sha256(out).hexdigest():
            raise DataError(
                '寫出來的內容跟預期對不上,所以不換名 —— %s 一個位元組都沒被動到。'
                % os.path.basename(path))
        # ⚠️ 換名與登記中間不可以留縫。原本是 os.replace 一行、_REPLACED.append
        #    另一行,Ctrl-C 落在中間的話收尾會照舊狀態印「沒有改到任何檔案」,
        #    而名冊已經被換掉了。現在兩件事包在同一段不可中斷的動作裡。
        _replace_and_record(tmp, path, 'set')
    except BaseException:
        try:
            os.remove(tmp)      # 失敗就把半截的暫存檔收掉,不留垃圾
        except OSError:
            pass
        raise

    # 複驗:重讀一次,確認真的改成功而且沒動到別的地方。
    # 三件事一起查:讀得回來、行數沒變、改動行數剛好 1 而且那一格真的是新值。
    # ⚠️ 三道以前是三個各自 raise 的 if,只印紅字叫使用者自己去 --restore。
    #    現在改成先收成一個 problem,再由同一段收尾處理 —— 因為「該還原」的
    #    判斷三道是一樣的,分開寫就會像 2026-09-05 之前那樣:行數那一道漏掉了
    #    自動還原,只有欄位那一道有。
    problem = None
    lines2 = None
    try:
        _raw2, lines2 = read_attrib(path)
    except DataError as e:
        problem = '寫入後的名冊讀不回來(%s)' % e
    if problem is None and len(lines2) != len(lines):
        problem = '寫入後行數變了(%d → %d)' % (len(lines), len(lines2))
    if problem is None:
        diff = sum(1 for a, b in zip(lines, lines2) if a != b)
        got = cell_value(lines2[i], FACE_FIELD)
        print('  已寫入。改動行數 = %d(應該是 1),第 %d 欄現在是 %s'
              % (diff, FACE_FIELD, got))
        if diff != 1 or got != str(new_face):
            problem = '改動行數 %d(應該是 1)、第 %d 欄是 %s' % (diff, FACE_FIELD, got)
    if problem is not None:
        # ⚠️ 複驗不過不可以只印一行紅字就算了。這時候名冊已經被換過名,
        #    而旁邊那份備份是**進來之前就驗過**的(上面 check_backup_usable 那一段),
        #    所以直接拿它退回去是安全的,不必等使用者自己想到要下 --restore。
        #    退不回去才把指令印出來請他自己來。無論哪一種都是非 0 離開。
        print('  ❌ 複驗不通過(%s),正在用剛才那份備份自動還原……' % problem)
        try:
            # ⚠️ 這裡**不能**呼叫 check_backup_usable:它比的是「備份 vs 現在這個檔」,
            #    而現在這個檔正是剛剛寫壞的那一份 —— 寫壞的方式如果是多長出幾列,
            #    那道就會判「還原會少掉幾列」而拒絕,把使用者鎖在壞掉的名冊上。
            #    要比的對象是**動手之前**那一份(raw),所以這裡自己比一次。
            looks_like_roster(backup, os.path.basename(path))
            n_bak, n_before = _roster_rows(open(backup, 'rb').read()), _roster_rows(raw)
            if n_bak < n_before:
                raise DataError('備份只有 %d 列,動手之前的名冊有 %d 列,不敢拿它蓋回去。'
                                % (n_bak, n_before))
            _restore_from_backup(backup, path)
            print('  ✅ 已自動還原,名冊回到你動手之前的樣子。')
        except (DataError, SystemExit, OSError) as e:
            print('  ⚠ 自動還原沒有成功:%s' % e)
            print('     請自己執行下面這一行(把路徑換成你的遊戲資料夾):')
            print('       python3 %s "<遊戲資料夾>" --restore'
                  % os.path.basename(sys.argv[0] or 'mvp_swap_face.py'))
        raise DataError('複驗不通過(%s),已如上處理。' % problem)
    print('  ✅ 複驗通過')



# 數名冊裡有幾列球員資料(表頭與空行不算)。這個數字拿來比對「備份」與
# 「現在這個檔」—— 截斷剛好落在換行邊界上的時候,列數是唯一還看得出來的痕跡。
def _roster_rows(raw):
    return sum(1 for l in raw.split(b'\r\n')[1:] if l.strip())


# 備份的把關。--restore 與 --apply 兩條路都會先跑這一支,
# 再交給 _restore_from_backup 做通用的那幾道(0 bytes、大小地板)。
# 這一支查的是「名冊自己的格式」,那一支查的是「所有檔案都適用的常識」。
def looks_like_roster(backup, target_name):
    """覆蓋之前先確認這個備份真的是名冊,而且沒有被截斷。

    ⚠️ 本站另外三支工具的備份就躺在同一個資料夾,副檔名各不相同但都在旁邊。
       路徑打錯、或有人手動改過副檔名,就會拿別的東西蓋掉名冊。
       這道把關查的是「檔案裡真的有的東西」,五件:
         開頭是數字欄位表、檔案裡有 CRLF、表頭找得到 first_name 與 last_name、
         整份以 CRLF 收尾、最後一列的欄數跟第一列一樣。
       前三件在問「這是不是名冊」,後兩件在問「它完不完整」。
    """
    try:
        raw = open(backup, 'rb').read()
    except OSError as e:
        raise DataError('讀不到備份 %s:%s' % (os.path.basename(backup), e))
    if not raw[:1].isdigit():
        raise DataError('備份 %s 的開頭不像欄位表,不敢拿它覆蓋 %s。'
                        % (os.path.basename(backup), target_name))
    if b'\r\n' not in raw:
        raise DataError('備份 %s 沒有 CRLF 換行,可能已被編輯器改壞,不敢覆蓋。'
                        % os.path.basename(backup))
    header = raw.split(b'\r\n', 1)[0].decode('latin-1', 'replace')
    if 'first_name' not in header or 'last_name' not in header:
        raise DataError('備份 %s 的表頭找不到 first_name / last_name,不像名冊,不敢覆蓋。'
                        % os.path.basename(backup))

    # ── 下面兩道專門對付「被截斷」──────────────────────────────
    # 上面三道只看開頭,開頭再漂亮也看不出後面少了多少 —— 2026-08-29 那份
    # 300 KB 蓋掉 2.66 MB 的實測就是這樣過關的。這兩道改看檔案的結尾:
    #   (a) 完整的名冊一定以 CRLF 收尾
    #   (b) 每一列的欄數都一樣,截在列中間的話最後一列一定湊不齊
    # 本站這台機器上找得到的 18 份 attrib.dat(含三份剛安裝好的原版與 2009 年
    # 以來的社群名冊)全部符合這兩條:都以 CRLF 收尾、資料列一律 48 格。
    # ⚠️ 擋不住的那一種:截斷處剛好落在換行邊界上。那份 840,643 個位元組的名冊裡
    #    有 3,248 個換行邊界,所以「剛好切在邊界」不是不可能,只是少見。
    #    那一種交給 check_backup_usable 那一道(備份的列數比現在這個檔少就停手)。
    lines = raw.split(b'\r\n')
    if lines[-1] != b'':
        raise DataError('備份 %s 沒有以換行收尾,它被截斷了,不敢拿它覆蓋 %s。\n'
                        '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
                        '  請改用你自己另外留的那一份備份。'
                        % (os.path.basename(backup), target_name))
    rows = [l for l in lines[1:] if l.strip()]
    if len(rows) < 2:
        raise DataError('備份 %s 只有 %d 列球員資料,內容不完整,不敢覆蓋 %s。'
                        % (os.path.basename(backup), len(rows), target_name))
    first_cells, last_cells = len(rows[0].split(b',')), len(rows[-1].split(b','))
    if first_cells != last_cells:
        raise DataError('備份 %s 的最後一列只有 %d 格,前面每一列都是 %d 格 ——\n'
                        '  它被截斷在一列的中間,不敢拿它覆蓋 %s。\n'
                        '  請改用你自己另外留的那一份備份。'
                        % (os.path.basename(backup), last_cells, first_cells, target_name))


# --apply 與 --restore 共用的備份把關。
# ⚠️ 兩邊查的必須是同一套,不然就會出現「改得進去、還原不回來」——
#    那是最糟的組合:遊戲檔已經被改了,而唯一的退路被自己的檢查拒收。
#    (2026-09-05 覆驗時真的踩到:先只在 --restore 那一邊加了列數這一道,
#     於是一份剛好截在換行邊界上的備份,--apply 放行、--restore 拒收。)
# 回傳 (備份的列數, 現在這個檔的列數);現在這個檔不在就回 (備份的列數, None)。
def check_backup_usable(backup, path, action):
    looks_like_roster(backup, os.path.basename(path))
    n_bak = _roster_rows(open(backup, 'rb').read())
    if not os.path.exists(path):
        return n_bak, None
    n_now = _roster_rows(open(path, 'rb').read())
    # 列數是「剛好截在換行邊界上」唯一還看得出來的痕跡。方向不對稱,只擋一邊:
    #   · 備份比較短 → 拿它還原會讓名冊變短,停。
    #   · 備份比較長 → 那是壞掉的是現在這個檔、備份來救它,放行。
    # (備份之後用別的工具加過球員也會落在第一種。那時候還原本來就會把那些
    #  球員一起收回去,所以停下來問一聲是對的 —— 訊息裡有手動做的指令。)
    if n_bak < n_now:
        raise DataError(
            '備份 %s 只有 %d 列球員資料,而現在的 %s 有 %d 列 ——\n'
            '  用它還原會少掉 %d 列,所以%s。\n'
            '  兩種可能:這份備份被截斷過,或者你在備份之後用別的工具加過球員。\n'
            '  真的確定要回到備份那個狀態的話,自己複製一次就好:\n'
            '    Windows:  copy /Y "%s" "%s"\n'
            '    Mac:      cp "%s" "%s"'
            % (os.path.basename(backup), n_bak, os.path.basename(path), n_now,
               n_now - n_bak, action, backup, path, backup, path))
    return n_bak, n_now


# --restore:把關都過了才覆蓋(是不是名冊、有沒有被截斷、列數會不會變少、
# 是不是 0 bytes、有沒有小到不到正本的一半)。覆蓋完再把「還原前」跟「還原後」比一次,
# 告訴你到底變了幾行,這樣你才知道剛剛那次還原有沒有意義。
def cmd_restore(path):
    backup = path + '.facebak'
    if not os.path.exists(backup):
        raise DataError('找不到備份 %s。這支腳本只在第一次 --apply 時建立備份。'
                        % os.path.basename(backup))
    n_bak, n_now = check_backup_usable(backup, path, '停手不做')
    if n_now is not None and n_bak > n_now:
        print('\n  註:備份有 %d 列球員資料,現在這個檔只有 %d 列。' % (n_bak, n_now))
        print('      現在這個檔比備份短,還原會把少掉的那些列補回來。')
    # ⚠️ 這裡原本印「位元組完全一致」,拿的是剛複製過去的檔跟來源比 ——
    #    複製成功就一定相等,那句話只是在報告自己剛複製成功。
    before = open(path, 'rb').read() if os.path.exists(path) else None
    _restore_from_backup(backup, path)
    after = open(path, 'rb').read()
    print('\n  已從備份還原 → %s' % os.path.basename(path))
    if before is None:
        print('  (還原前那個檔不在,所以沒有可比對的對象)')
    elif before == after:
        print('  跟還原前一模一樣 —— 你的檔案本來就跟備份相同,這次沒有任何改變。')
    else:
        lb, la = before.split(b'\r\n'), after.split(b'\r\n')
        # ⚠️ zip() 只比到短的那一邊為止。行數不一樣的時候多出來的那幾千列
        #    一列都不會被算進去 —— 「備份少了 1300 列」會被報成「只差 1 行」,
        #    而那正好是最需要被看見的那一種。所以行數差要另外加回去。
        n = sum(1 for x, y in zip(lb, la) if x != y) + abs(len(lb) - len(la))
        print('  已還原,跟還原前有 %d 行不同。' % n)
        if len(lb) != len(la):
            print('  ⚠ 名冊的總行數從 %d 變成 %d。' % (len(lb), len(la)))
            print('    上面那個「有幾行不同」已經把行數差算進去了。')
            print('    走到這裡代表備份比還原前那個檔長 —— 短的那個方向')
            print('    在覆蓋之前就被擋掉了,所以你沒有掉任何一列。')


# ─────────────────────────────────────────────────────────
# 進入點。這裡只做四件事:認參數、算出兩個檔案的位置、決定 face 是第幾欄,
# 然後把工作交給上面那幾個 cmd_*。真正會寫檔的只有 cmd_set 與 cmd_restore。
def main():
    ap = argparse.ArgumentParser(
        description='幫 MVP Baseball 2005 的球員換一張臉(只動 attrib.dat 純文字檔)')
    ap.add_argument('gamedir', nargs='?',
                    help='遊戲資料夾(裡面要有 data 這個子資料夾)')
    ap.add_argument('--find', metavar='名字', help='查球員目前用哪張臉')
    ap.add_argument('--set', nargs=2, metavar=('球員', '臉皮編號'),
                    help='把某位球員的臉換成指定編號')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原 attrib.dat')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試,不碰任何遊戲檔')
    args = ap.parse_args()

    # --selftest 排在最前面,因為它自己造測試資料,不需要遊戲資料夾。
    if args.selftest:
        return selftest()
    if not args.gamedir:
        ap.print_help()
        return 2

    # 使用者給的是「遊戲安裝資料夾」,這兩個檔案在它底下的相對位置是固定的。
    attrib = os.path.join(args.gamedir, 'data', 'database', 'attrib.dat')
    models = os.path.join(args.gamedir, 'data', 'models.big')

    # attrib.dat 有可能是一個符號連結(有人把名冊放在別處,或用模組管理器
    # 做連結共用)。
    # ⚠️ 2026-09-06 訂正:這裡原本是「解成真實路徑再照常寫」。那樣做的問題是
    #    你以為在改 A,實際被改的是 B —— 而畫面上只有一行小字提過。本站的規矩
    #    改成:要「寫」的那個檔本身是連結,一律停手,由你自己決定要動哪一個。
    #    (路徑中間的**資料夾**是連結不擋 —— 遊戲裝在別顆碟很正常,
    #     只看最後那一個檔。讀取也不擋。)
    if os.path.islink(attrib):
        print('❌ %s 是一個符號連結:' % os.path.basename(attrib))
        print('      %s' % attrib)
        print('   本工具不跟著連結寫 —— 會被改到的是連結指向的那個檔,不是你以為的那個。')
        print('   請把那個連結換成真正的檔案(或直接把遊戲資料夾指到連結的目的地)再跑一次。')
        return 2

    # --restore 要排在「找不到 attrib.dat」之前:名冊被刪掉或改名的時候,
    # 還原正是你現在要做的事,不該被「找不到」擋在門外 —— 備份就躺在旁邊。
    # (排在讀名冊之前也是同一個理由:名冊壞到讀不動時,還原不該被「讀不動」擋住。)
    if args.restore:
        bakpath = attrib + '.facebak'
        # ⚠️ 這兩種要分開講。os.path.isfile / exists 對「指向不存在目標的符號連結」
        #    都會回 False,一律報成「找不到備份」的話,使用者會照著去找一個
        #    其實就躺在那裡的檔 —— 真正的問題是那個連結斷了。
        if os.path.lexists(bakpath) and not os.path.exists(bakpath):
            print('❌ %s 是一個連結,而它指向的檔案不存在。' % bakpath)
            print('   先確認那個連結指到哪裡(Mac:ls -l / Windows:dir),')
            print('   或改用你自己另外留的那一份備份。')
            return 2
        if not os.path.isfile(bakpath):
            print('❌ 找不到 %s' % bakpath)
            print('   請確認第一個參數是遊戲資料夾(裡面應該要有 data 這個子資料夾)。')
            print('   這支腳本只在第一次 --apply 時建立備份。')
            return 2
        cmd_restore(attrib)
        return 0

    if not os.path.isfile(attrib):
        print('❌ 找不到 %s' % attrib)
        print('   請確認第一個參數是遊戲資料夾(裡面應該要有 data 這個子資料夾)。')
        return 2

    raw, lines = read_attrib(attrib)

    # face 是第幾欄要執行時才知道(見檔案上面那段 ⚠️),決定不了就 DataError 停下來:
    # 看不懂的名冊寧可不動。不是第 10 欄時會印一行出來,讓你知道這份名冊不一樣。
    global FACE_FIELD
    FACE_FIELD = resolve_field(lines, FACE_NAME)
    if FACE_FIELD != 10:
        print('  註:這份名冊的 %s 在第 %d 欄。' % (FACE_NAME, FACE_FIELD))

    # 讀 models.big 只是為了「能不能幫你檢查編號」,不是必要條件。
    # 讀不到就繼續跑,但要把這件事說出來。
    # None = 沒讀到(不知道);set() = 讀到了而且真的是空的。
    # 兩者不可以混用 —— 混用就會把「不知道」報成「不存在」。
    faces = None
    if os.path.isfile(models):
        try:
            faces = available_faces(models)
        except DataError as e:
            print('⚠ 讀 models.big 時出狀況:%s' % e)
            print('  仍可繼續,但無法檢查臉皮編號是否存在。')
    else:
        print('⚠ 找不到 models.big,無法檢查臉皮編號是否存在。')

    # 三種動作互斥,都沒給就印總覽。總覽與 --find 全程唯讀,只有 --set 會寫檔。
    if args.find:
        cmd_find(lines, faces, args.find)
    elif args.set:
        who, num = args.set
        if not num.lstrip('-').isdigit():
            print('❌ 臉皮編號要是數字,你給的是「%s」' % num)
            return 2
        # 範圍檢查放在這裡而不是 cmd_set:參數打錯屬於「使用者輸入錯誤」,
        # 回傳 exit code 2;檔案內容不對才是 DataError(exit code 1)。
        # 0-999 是因為臉皮編號是 c### 三位數,0 代表「不指定」。
        n = int(num)
        if n < 0 or n > 999:
            print('❌ 臉皮編號要在 0 到 999 之間,你給的是 %d' % n)
            return 2
        cmd_set(attrib, raw, lines, faces, who, n, args.apply)
    else:
        cmd_overview(lines, faces)
    return 0


def _fake_roster(rows=3, face='665'):
    """造一份最小但格式正確的名冊(46 個具名欄位 + 收尾的 ';',CRLF 換行)。

    完全不碰遊戲檔:--selftest 只在系統暫存區工作。
    """
    names = {0: 'first_name', 1: 'last_name', 10: 'playerattrib_face'}
    hdr = ','.join('%d %s' % (n, names.get(n, 'playerattrib_x%d' % n))
                   for n in range(46)) + ',;'
    out = [hdr]
    for k in range(rows):
        cells = []
        for n in range(46):
            if n == 0:
                v = 'Test%d' % k
            elif n == 1:
                v = 'Player%d' % k
            elif n == 10:
                v = face if k == 0 else '901'
            else:
                v = str(n)
            cells.append('%d %s' % (n, v))
        out.append('id%08d,' % k + ','.join(cells) + ',;')
    return ('\r\n'.join(out) + '\r\n').encode('latin-1')


def selftest():
    """--selftest:自己造一份最小的名冊來測,完全不碰遊戲檔。

    測的是這支工具對讀者的承諾,一條一條驗。**正向與反向都要有** ——
    2026-08-29 本站踩過「防線壞了測試照樣全綠」,所以每一道守門都先證明
    「正常流程真的做得到」,再放一個餌證明「答案錯的時候它真的會叫」。

    正向 9 道:
      · 造出來的名冊讀得出來、face 欄是第 10 欄
      · 沒加 --apply 一個位元組都不動、不產生備份、不記到任何一次換名
      · --apply 之後那一格真的是新值
      · 沒點名的那幾列逐位元組相同
      · 備份逐位元組等於動手之前的名冊
      · 換名有被記下來(Ctrl-C 的收尾訊息靠它)
      · --restore 之後逐位元組回到動手之前

    (--selftest 不接受 python -O:-O 會把下面每一個 assert 拿掉,
     整份測試會在什麼都沒驗的情況下印「全部通過」。進來第一行就擋掉。)

    反向餌 13 組(2026-09-05 第二輪、2026-09-06 第三輪稽核補的守門,每一道各配一組):
      A 事先把「備份名 + .part」放成指向資料夾外面的符號連結 → 跑 --apply,
        外面那個檔必須一個位元組都沒變(暫存檔的名字已經猜不到了)
      B 事先把「名冊名 + .tmp」放成同樣的連結 → 同上
      C 寫入的目的地本身是符號連結 → 停手,連結沒被換掉、外面那個檔沒被動到
      C2 旁邊躺著一份指向垃圾內容的既有 .facebak → 停手,名冊不可以被改
      D 名冊本身是符號連結 → 停手,而且連結指到的那份名冊沒被動到
      E 還原做到一半失敗(把 os.replace 換成一定丟例外的版本)→
        正本原封不動,而且不留下暫存檔
      F 複驗的「改動行數 = 1」那一道 → 自己還原回去、丟出例外
      F2 複驗的「行數沒變」那一道(只在列尾多一個換行,內容全都一樣)→ 同上
      G 備份是一個指向不存在目標的符號連結 → 不可以被報成「找不到備份」
      G2 同一件事在命令列那條路(main() 的 --restore)上也要成立
      H 「換名之前讀回來比一次」那一道 → 備份與寫入兩條路都要停手,不留暫存檔
      I _NoInterrupt 真的把 Ctrl-C 壓到區塊結束才丟(而且處理器有還回去)
      J 換名剛做完就中斷 → 登記一定已經在了,收尾不可以說「沒動到」;
        連 (a) 失效時由 _INFLIGHT 接手的「正在替換」那一句也一起驗
      K 名冊本身是符號連結 → 命令列那條路(main())一律停手、exit code 2,
        連結沒被換掉、它指到的那份名冊沒被動到、不產生備份

    每一組都拿「把對應的那道守門改壞」驗過會亮 —— 餌會自己失效而沒有人發現,
    所以餌本身也要驗。(2026-09-05 那 10 組是 14 個突變體;2026-09-06 補的
    I / J / K 三組另外驗過:拆掉 _NoInterrupt、把登記搬回換名之後、
    把 main() 改回「解成真實路徑再照常寫」,三個變體各自被對應的餌咬到。)
    """
    # ⚠️ 這一道要排在最前面。python -O 會把 assert 整個拿掉,下面幾十道守門
    #    一句都不會執行,而畫面照樣印「全部通過」—— 那是最糟的一種綠燈。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2

    import io as _io
    import contextlib
    global FACE_FIELD

    def _raise_sigint():
        """對自己發一次 SIGINT(等於使用者按了 Ctrl-C)。"""
        if hasattr(signal, 'raise_signal'):     # 3.8+
            signal.raise_signal(signal.SIGINT)
        else:
            os.kill(os.getpid(), signal.SIGINT)

    d = tempfile.mkdtemp(prefix='mvp_swap_face_selftest-')
    db = os.path.join(d, 'data', 'database')
    os.makedirs(db)
    p = os.path.join(db, 'attrib.dat')
    bak = p + '.facebak'
    blob = _fake_roster()
    open(p, 'wb').write(blob)
    outside = os.path.join(d, 'OUTSIDE.txt')      # 「資料夾外面那個檔」的替身
    guard_bytes = b'do not touch me\r\n' * 100
    faces = {665, 700}

    def _reload():
        return read_attrib(p)

    def _quiet(fn, *a, **kw):
        with contextlib.redirect_stdout(_io.StringIO()):
            return fn(*a, **kw)

    raw, lines = _reload()
    FACE_FIELD = resolve_field(lines, FACE_NAME)
    assert FACE_FIELD == 10, '自造名冊的 face 欄應該是第 10 欄,測試本身壞了'

    # 正向:沒加 --apply 一個位元組都不動
    _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, False)
    assert open(p, 'rb').read() == blob, '預覽竟然動到檔案'
    assert not os.path.lexists(bak), '預覽不該產生備份'
    assert not _REPLACED, '預覽不該記到任何一次換名'

    # ── 餌 A/B:事先佔位的可預測暫存檔名 ────────────────────────────
    # 舊寫法是 dst + '.part' 與 path + '.tmp',名字完全猜得到,而開檔會跟著
    # 符號連結走。這裡先把兩個名字都佔掉,指向資料夾外面那個檔。
    open(outside, 'wb').write(guard_bytes)
    for lure in (bak + '.part', p + '.tmp'):
        os.symlink(outside, lure)
    raw, lines = _reload()
    _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, True)
    assert open(outside, 'rb').read() == guard_bytes, \
        '餌 A/B:資料夾外面那個檔被寫到了 —— 暫存檔還是走可預測的名字'
    for lure in (bak + '.part', p + '.tmp'):
        assert os.path.islink(lure), '餌 A/B:那兩個連結不該被換掉'
        os.remove(lure)

    # 正向:--apply 真的改到那一格,而且只改那一列;備份逐位元組等於動手之前
    _raw3, lines3 = _reload()
    assert cell_value(lines3[1], FACE_FIELD) == '700', '--apply 之後那一格不是新值'
    assert lines3[2:] == lines[2:], '沒點名的那幾列被動到了'
    assert open(bak, 'rb').read() == blob, '備份跟動手之前不是逐位元組相同'
    assert ('set', p) in _REPLACED, 'os.replace 做過了卻沒記下來 —— Ctrl-C 會說錯話'

    # 正向:--restore 逐位元組回到動手之前
    _quiet(cmd_restore, p)
    assert open(p, 'rb').read() == blob, '還原之後應該逐位元組回到原本的樣子'

    # ── 餌 C:寫入的目的地本身是符號連結 ────────────────────────
    #    直接叫 _atomic_copy —— 這是整支腳本所有「產生檔案」的共同出口。
    #    (旁邊已經有一個 .facebak 連結的情況走不到這裡:那時候腳本只會**讀**
    #     那份備份、由名冊那幾道決定收不收,不會往它身上寫。所以要驗守門本身,
    #     就得對著出口驗。)
    os.remove(bak)
    open(outside, 'wb').write(guard_bytes)
    link_dst = os.path.join(db, 'link-target.dat')
    os.symlink(outside, link_dst)
    try:
        _atomic_copy(p, link_dst)
    except DataError:
        pass
    else:
        raise AssertionError('餌 C:目的地是符號連結竟然照寫 —— 防線失效')
    assert os.path.islink(link_dst), '餌 C:那個連結被換成一般檔案了'
    assert open(outside, 'rb').read() == guard_bytes, '餌 C:連結指到的那個檔被動到了'
    assert open(p, 'rb').read() == blob, '餌 C:被擋下來的時候名冊不可以被改'
    os.remove(link_dst)

    # ── 餌 C2:旁邊躺著一份指向垃圾內容的 .facebak 連結 ──────────────
    #    這一路不寫備份,只讀它 —— 讀出來不是名冊就要停手,而且名冊不可以被改。
    os.symlink(outside, bak)
    raw, lines = _reload()
    try:
        _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, True)
    except DataError:
        pass
    else:
        raise AssertionError('餌 C2:壞掉的既有備份竟然放行 —— 改得進去、還原不回來')
    assert open(p, 'rb').read() == blob, '餌 C2:被擋下來的時候名冊不可以被改'
    os.remove(bak)

    # ── 餌 G:備份是一個指向不存在目標的符號連結 ──────────────────
    #    os.path.exists() 對這種會回 False,錯誤訊息就會變成「找不到備份」,
    #    把「那是一個壞掉的連結」這件事藏起來。
    os.symlink(os.path.join(d, 'nope-does-not-exist'), bak)
    assert not os.path.exists(bak) and os.path.lexists(bak), '餌 G 的前提不成立'
    try:
        _restore_from_backup(bak, p)
    except SystemExit as e:
        assert '找不到備份' not in str(e), \
            '餌 G:壞掉的連結被報成「找不到備份」—— 使用者會去找不存在的問題'
    else:
        raise AssertionError('餌 G:壞掉的連結竟然還原得下去 —— 防線失效')
    # 餌 G2:同一件事在使用者真正會走的那條路(main() 的 --restore)上也要成立。
    real_argv = sys.argv
    sys.argv = ['mvp_swap_face.py', d, '--restore']
    buf = _io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = main()
    finally:
        sys.argv = real_argv
    assert rc == 2, '餌 G2:壞掉的連結竟然不是以 exit code 2 收場(是 %r)' % rc
    assert '找不到' not in buf.getvalue(), \
        '餌 G2:命令列那條路把壞掉的連結報成「找不到」—— 使用者會去找不存在的問題'
    os.remove(bak)

    # ── 餌 D:名冊本身是符號連結 ────────────────────────────────
    #    (main() 會先把連結解成真實路徑,所以正常路徑碰不到;
    #     這裡直接叫 cmd_set,測的是最後那道守門本身。)
    link_dir = os.path.join(d, 'linkdir')   # 跟餌 C 的 link-target.dat 不同,別搞混
    os.makedirs(link_dir)
    lp = os.path.join(link_dir, 'attrib.dat')
    os.symlink(p, lp)
    before = open(p, 'rb').read()
    raw, lines = _reload()
    try:
        _quiet(cmd_set, lp, raw, lines, faces, 'id00000000', 700, True)
    except DataError:
        pass
    else:
        raise AssertionError('餌 D:名冊是符號連結竟然照寫 —— 防線失效')
    assert open(p, 'rb').read() == before, '餌 D:連結指到的那份名冊被動到了'
    assert not os.path.lexists(lp + '.facebak'), '餌 D:不該產生備份'
    os.remove(lp)

    # ── 餌 E:還原做到一半失敗,正本必須原封不動 ────────────────────
    raw, lines = _reload()
    _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, True)
    live_before = open(p, 'rb').read()
    assert live_before != blob, '餌 E 的前提不成立(名冊應該已經被改過)'
    real_replace = os.replace

    def _boom(*a, **kw):
        raise OSError(28, '磁碟滿了(餌)')

    os.replace = _boom
    try:
        _quiet(cmd_restore, p)
    except OSError:
        pass
    else:
        raise AssertionError('餌 E:換名失敗竟然還報成功 —— 防線失效')
    finally:
        os.replace = real_replace
    assert open(p, 'rb').read() == live_before, '餌 E:換名失敗時正本不可以被動到'
    leftovers = [f for f in os.listdir(db) if f.startswith('.attrib.dat.')]
    assert not leftovers, '餌 E:失敗之後留下了暫存檔 %r' % leftovers

    # ── 餌 F:複驗不過要自己還原回去,而且一定要丟出例外 ──────────────
    #    把 build_new_line 換成一個「寫進去的值跟你要的不一樣」的版本
    #    (700 → 701,長度一樣、行數一樣)。這咬的是複驗「那一格要真的是新值」
    #    那一道 —— 用多塞一行的方式咬不到它,那種會先被行數那一道接走(見餌 F2)。
    _quiet(cmd_restore, p)
    assert open(p, 'rb').read() == blob, '餌 F 的前提不成立'
    real_build = globals()['build_new_line']   # 餌 F2 會再用一次

    def _sabotage(line_bytes, new_face):
        return real_build(line_bytes, new_face + 1)

    raw, lines = _reload()
    globals()['build_new_line'] = _sabotage
    try:
        _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, True)
    except DataError:
        pass
    else:
        raise AssertionError('餌 F:複驗不過竟然沒有丟出例外 —— 會被當成成功')
    finally:
        globals()['build_new_line'] = real_build
    assert open(p, 'rb').read() == blob, '餌 F:複驗不過之後應該已經自動還原回去'

    # ── 餌 F2:複驗的「行數」那一道 ────────────────────────────
    #    餌 F 咬到的是「改動行數 = 1」那一道。行數那一道要另外咬:
    #    對**最後一列**動手、只在列尾多加一個換行 —— 每一列的內容都還一樣,
    #    只有總行數多了一行。少了這個餌,行數那一道拿掉也不會有人發現。
    real_build = globals()['build_new_line']

    def _extra_newline(line_bytes, new_face):
        return real_build(line_bytes, new_face) + b'\r\n'

    raw, lines = _reload()
    globals()['build_new_line'] = _extra_newline
    try:
        _quiet(cmd_set, p, raw, lines, faces, 'id00000002', 700, True)
    except DataError:
        pass
    else:
        raise AssertionError('餌 F2:寫完多出一行竟然算複驗通過 —— 防線失效')
    finally:
        globals()['build_new_line'] = real_build
    assert open(p, 'rb').read() == blob, '餌 F2:複驗不過之後應該已經自動還原回去'

    # ── 餌 H:「換名之前讀回來比一次」那一道 ────────────────────────
    #    把 _sha256 換成永遠回同一個假答案,等於模擬「寫下去的跟手上的不一樣」。
    #    備份與寫入兩條路都走它,所以兩條都要停手,而且名冊不可以被動到。
    real_sha = globals()['_sha256']
    globals()['_sha256'] = lambda _p: 'deadbeef'
    try:
        try:
            _atomic_copy(p, os.path.join(db, 'should-not-appear.dat'))
        except DataError:
            pass
        else:
            raise AssertionError('餌 H:內容對不上竟然還換名(備份那條路)—— 防線失效')
        assert not os.path.lexists(os.path.join(db, 'should-not-appear.dat')), \
            '餌 H:對不上就不該產生那個檔'
        raw, lines = _reload()
        try:
            _quiet(cmd_set, p, raw, lines, faces, 'id00000000', 700, True)
        except DataError:
            pass
        else:
            raise AssertionError('餌 H:內容對不上竟然還換名(寫入那條路)—— 防線失效')
    finally:
        globals()['_sha256'] = real_sha
    assert open(p, 'rb').read() == blob, '餌 H:被擋下來的時候名冊不可以被改'
    leftovers = [f for f in os.listdir(db) if f.startswith('.attrib.dat.')]
    assert not leftovers, '餌 H:失敗之後留下了暫存檔 %r' % leftovers

    # ── 餌 I:_NoInterrupt 真的把 Ctrl-C 壓到區塊結束才丟 ──────────────
    #    這是「換名 + 登記」不可中斷的地基。它壞掉的話,下面餌 J 那個
    #    「換完才中斷」的情境會退回舊行為:收尾照舊狀態說「沒動到」。
    seq = []
    old_h = signal.getsignal(signal.SIGINT)
    try:
        with _NoInterrupt():
            assert signal.getsignal(signal.SIGINT) is not old_h, \
                '餌 I:_NoInterrupt 根本沒把處理器裝上去'
            _raise_sigint()             # 這一下要被壓住
            seq.append('inside')        # 壓住了才跑得到這一行
    except KeyboardInterrupt:
        seq.append('after')
    assert seq == ['inside', 'after'], \
        '餌 I:Ctrl-C 沒有被壓到區塊結束才丟(%r)' % seq
    assert signal.getsignal(signal.SIGINT) is old_h, \
        '餌 I:離開之後沒有把原本的處理器還回去'

    # ── 餌 J:換名剛做完就中斷 —— 登記一定要已經在了 ────────────────
    #    這咬的正是這一輪要關掉的那個窗口:os.replace 成功、_REPLACED 還沒記,
    #    Ctrl-C 落在中間。舊寫法會讓收尾印「沒有改到任何檔案」。
    j_src, j_dst = os.path.join(db, 'J-src.dat'), os.path.join(db, 'J-dst.dat')
    open(j_src, 'wb').write(b'J')
    marker = len(_REPLACED)
    real_replace2 = os.replace

    def _replace_then_sigint(a, b):
        real_replace2(a, b)
        _raise_sigint()                 # 換名剛做完,這時候中斷
    os.replace = _replace_then_sigint
    try:
        _replace_and_record(j_src, j_dst, 'set')
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError('餌 J:被壓住的 Ctrl-C 應該在區塊結束時丟出來')
    finally:
        os.replace = real_replace2
    assert os.path.exists(j_dst), '餌 J 的前提不成立(換名應該已經做完了)'
    assert ('set', j_dst) in _REPLACED[marker:], \
        '餌 J:換名做完了卻沒登記 —— Ctrl-C 的收尾會說「沒動到」'
    # 三態的第三態:(a) 那道失效的時候(裝不上處理器)由 _INFLIGHT 接手,
    # 收尾一樣不可以說「沒動到」。
    saved_replaced, saved_pending = list(_REPLACED), list(_INFLIGHT)
    _REPLACED[:], _INFLIGHT[:] = [], [('set', p)]
    buf3 = _io.StringIO()
    with contextlib.redirect_stdout(buf3):
        _interrupt_note()
    _REPLACED[:], _INFLIGHT[:] = saved_replaced[:marker], saved_pending
    assert '沒有改到任何檔案' not in buf3.getvalue(), \
        '餌 J:「正在替換」的狀態被收尾報成「沒動到」'
    assert '正在替換' in buf3.getvalue(), \
        '餌 J:「正在替換」的狀態沒有被說出來(%r)' % buf3.getvalue()

    # ── 餌 K:名冊是符號連結 → 命令列那條路一律停手,不跟著連結寫 ──────
    #    (餌 D 咬的是 cmd_set 裡那道守門;這裡咬的是使用者真正會走的 main()。
    #     2026-09-06 之前 main() 是「解成真實路徑再照常寫」,守門根本走不到。)
    link_game = os.path.join(d, 'linkgame')
    os.makedirs(os.path.join(link_game, 'data', 'database'))
    lp2 = os.path.join(link_game, 'data', 'database', 'attrib.dat')
    os.symlink(p, lp2)
    before2 = open(p, 'rb').read()
    sys.argv = ['mvp_swap_face.py', link_game, '--set', 'id00000000', '700', '--apply']
    buf4 = _io.StringIO()
    slipped = None
    try:
        with contextlib.redirect_stdout(buf4):
            rc2 = main()
    except (DataError, SystemExit, OSError) as e:
        # 走到這裡代表這道守門沒攔住,是後面別的守門把它接下來的。
        # 那不算這一道有效 —— 換一台 models.big 讀得到的機器就會真的寫下去。
        rc2, slipped = None, e
    finally:
        sys.argv = real_argv
    assert slipped is None, \
        '餌 K:名冊是連結竟然一路走到寫入邏輯,才被別的守門攔下(%s)' % slipped
    assert rc2 == 2, '餌 K:名冊是連結竟然不是以 exit code 2 收場(是 %r)' % rc2
    assert '符號連結' in buf4.getvalue(), '餌 K:沒有說清楚為什麼停手(%r)' % buf4.getvalue()
    assert os.path.islink(lp2), '餌 K:那個連結不該被換掉'
    assert open(p, 'rb').read() == before2, '餌 K:連結指到的那份名冊被動到了'
    assert not os.path.lexists(lp2 + '.facebak'), '餌 K:不該產生備份'

    print('自我測試:全部通過(53 道檢查:9 道正向,44 道分在 13 組反向餌裡)')
    print('  測試資料在 %s(跑完不刪,想自己看的話可以進去翻)' % d)
    return 0


# DataError 是「檔案跟預期不符」,一律印一行人看得懂的話然後 exit 1,
# 不丟 traceback,因為讀者多半不是工程師,traceback 幫不上忙。
# OSError 是「作業系統不讓你讀寫」,同樣不該噴 traceback:最常見的那一種
# (遊戲裝在 C:\Program Files (x86)\ 底下、命令提示字元不是用系統管理員身分開的)
# 讀者自己修得好,前提是有人告訴他發生什麼事。
# Ctrl-C 另外報。⚠️ 這裡原本無條件印「沒有改到任何檔案」——
# 寫入確實是先寫暫存檔再換名,但**中斷點可能落在換名之後**(複驗、印字都在後面),
# 那句話那時候就是假的:使用者以為什麼都沒發生,名冊其實已經被換掉了。
# 現在看 _REPLACED 裡有沒有記到換名,分四種情況說實話。兩種都是 exit 130。
def _interrupt_note():
    kinds = [k for k, _p in _REPLACED]
    # 三態的第三態:換名已經開始、而「換成了沒有」還不確定。這一筆只有在
    # _NoInterrupt 沒裝上處理器(例如不在主執行緒)的時候才留得下來,
    # 但留下來的時候絕對不可以說「沒動到」。
    pendings = [(k, p) for k, p in _INFLIGHT if (k, p) not in _REPLACED]
    if pendings and 'set' not in kinds and 'restore' not in kinds:
        k, pth = pendings[-1]
        print('  ⚠ 中斷的時候正在替換 %s —— 換成了沒有無法確定。' % os.path.basename(pth))
        print('    請用 --restore 還原,或自己拿旁邊那份 .facebak 比對一次。')
        return
    if 'set' in kinds:
        print('  ⚠ 名冊**已經被改過了** —— 換名在你按下 Ctrl-C 之前就完成了。')
        print('    要退回動手之前的樣子,執行:')
        print('      python3 %s "<遊戲資料夾>" --restore'
              % os.path.basename(sys.argv[0] or 'mvp_swap_face.py'))
    elif 'restore' in kinds:
        print('  註:還原在你按下 Ctrl-C 之前就完成了,名冊已經是備份那一份。')
    elif 'backup' in kinds:
        print('  只產生了備份(.facebak),名冊本身沒有被改到。')
    else:
        print('  沒有改到任何檔案。')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except DataError as e:
        print('\n❌ %s' % e)
        sys.exit(1)
    except OSError as e:
        print('\n❌ 讀寫檔案時被作業系統擋下來了:%s' % e)
        print('   最常見的兩種:')
        print('   · 遊戲裝在 C:\\Program Files (x86)\\ 底下,而命令提示字元')
        print('     不是用系統管理員身分開的 —— 對著它按右鍵選「以系統管理員身分執行」。')
        print('   · 那個檔正被遊戲或編輯器開著 —— 先把遊戲關掉。')
        # 同一個理由:這句「名冊沒有被改到」也不能無條件印。
        _interrupt_note()
        sys.exit(1)
    except KeyboardInterrupt:
        print('\n已中斷。')
        _interrupt_note()
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
