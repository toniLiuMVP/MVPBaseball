#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_exe_pe.py

把一顆 MVP Baseball 2005 執行檔的 **PE 檔頭修回合乎規格**。
兩件事,兩件都不碰程式碼本身:

  ① 補回 IAT 資料目錄   ② 收緊節區的寫入權限

  看你那顆現在是什麼狀態(唯讀,不會動到檔案)
      python3 mvp_exe_pe.py "你的遊戲資料夾/mvp2005.exe"

  預覽要改什麼(還是不會動到檔案)
      python3 mvp_exe_pe.py "…/mvp2005.exe" --iat --sections

  真的改(會先備份成 .exepebak)
      python3 mvp_exe_pe.py "…/mvp2005.exe" --iat --sections --apply

  還原
      python3 mvp_exe_pe.py "…/mvp2005.exe" --restore

  自我測試(不需要遊戲檔)
      python3 mvp_exe_pe.py --selftest

── 這支在做什麼、為什麼要做 ────────────────────────────────

**① IAT 資料目錄**
PE 規格的第 13 個資料目錄(索引 12)叫 Import Address Table,
它要指出「匯入位址表在哪、多大」。有些執行檔這一欄是 `RVA=0, size=0`,
等於沒填。Windows 載入器不靠它也載得起來(它會走匯入描述子),
但這個欄位是**載入器把那一段暫時改成可寫、填完位址再改回唯讀**的依據。
沒填 = 那一段的保護狀態由節區權限決定,而節區權限那時候常常是可寫的(見②)。
補回去之後,那一段在填完匯入位址之後會回到唯讀。

**② 節區寫入權限**
有些執行檔的 `.text`(程式碼)、`.rdata`(唯讀資料)、`.rsrc`(資源)
三個節區都帶著 **可寫** 旗標。程式碼段可寫又可執行是最寬鬆的組合,
正常的編譯輸出不會這樣。
收緊之後:`.text` 變成 讀+執行,`.rdata` 與 `.rsrc` 變成 唯讀。

**好處是什麼(誠實版)**
· 檔頭合乎規格,分析工具與防毒軟體不會因為「程式碼段可寫」而起疑。
· 程式碼段唯讀之後,執行時如果有東西試圖寫進程式碼,會當場出錯而不是默默改掉。
· ⚠️ **本站沒有量到它讓遊戲變快或變穩**。這兩項是「把檔案修正確」,
  不是效能調整。誰跟你說改這個會變順,請他拿量測出來。

**做不到、也不會做的事**
· 這支**不碰任何保護措施,也不會告訴你怎麼處理保護**。你那顆能不能改,
  是你自己那份遊戲的事。
· 這支不改程式碼、不改解析度、不改記憶體池、**不動任何時間戳**。
  那幾項在「讓它在 2026 年跑起來」那一課的 mvp_modernize.py。
· 改完檔頭會自己重算檢查碼,詳見下面 `_recalc_checksum()`。

備份副檔名 `.exepebak`,只認自己這一個,不會去動別課留下的 .bak。

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
import argparse
import io
import os
import shutil
import signal
import struct
import sys
import tempfile

BAK = '.exepebak'

# PE 規格裡這兩個旗標的值。收緊權限就是把 WRITE 那一位關掉。
SCN_CODE = 0x00000020            # IMAGE_SCN_CNT_CODE
SCN_INITIALIZED = 0x00000040     # IMAGE_SCN_CNT_INITIALIZED_DATA
SCN_EXECUTE = 0x20000000
SCN_READ = 0x40000000
SCN_WRITE = 0x80000000           # ← 要關掉的就是這一位

# 資料目錄的索引。12 = Import Address Table(這支要補的那一個)。
DIR_IMPORT = 1
DIR_IAT = 12


class DataError(Exception):
    """檔案不是預期的樣子。一律用這個丟，好跟程式自己的 bug 分開。"""


# ─────────────────────────────────────────────────────────
#  讀 PE 檔頭
#
#  這一段只做「把檔頭的位置算出來」，不做任何判斷。
#  所有位移都照 PE/COFF 規格：
#    0x3C            → PE 檔頭在哪（e_lfanew）
#    PE+0            → "PE\0\0"
#    PE+6            → 節區數量
#    PE+20           → Optional Header 有多大
#    PE+24           → Optional Header 開始
#    Optional+64     → CheckSum
#    Optional+92     → 資料目錄有幾個
#    Optional+96     → 資料目錄第一筆
#    Optional+size   → 節區表開始，每筆 40 bytes
# ─────────────────────────────────────────────────────────
def parse_pe(d):
    """回傳一個 dict，裝著這支會用到的所有位移。不是 PE 就丟 DataError。"""
    if len(d) < 0x40 or d[:2] != b'MZ':
        raise DataError('這不是 Windows 執行檔（開頭不是 MZ）。')
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    if pe <= 0 or pe + 24 > len(d) or d[pe:pe + 4] != b'PE\0\0':
        raise DataError('找不到 PE 檔頭，這個檔可能壞了或不是 PE 執行檔。')
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    if opt + optsz > len(d):
        raise DataError('Optional Header 宣告的長度超出檔案結尾。')
    ndir = struct.unpack_from('<I', d, opt + 92)[0]
    sect = opt + optsz
    if sect + nsec * 40 > len(d):
        raise DataError('節區表超出檔案結尾，宣告 %d 個節區。' % nsec)
    return {'pe': pe, 'opt': opt, 'nsec': nsec, 'ndir': ndir,
            'dir': opt + 96, 'sect': sect, 'checksum': opt + 64}


def read_dir(d, h, idx):
    """讀第 idx 個資料目錄，回傳 (RVA, size)。超出範圍就回 (0, 0)。"""
    if idx >= h['ndir']:
        return (0, 0)
    return struct.unpack_from('<II', d, h['dir'] + idx * 8)


def read_sections(d, h):
    """把節區表讀成一串 dict。名稱、虛擬位址、大小、旗標，以及旗標欄的位移。"""
    out = []
    for i in range(h['nsec']):
        b = h['sect'] + i * 40
        name = d[b:b + 8].rstrip(b'\0').decode('latin1') or '(無名)'
        vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', d, b + 8)
        flags = struct.unpack_from('<I', d, b + 36)[0]
        out.append({'name': name, 'vaddr': vaddr, 'vsize': vsize,
                    'raddr': raddr, 'rsize': rsize,
                    'flags': flags, 'flags_off': b + 36})
    return out


def describe_flags(f):
    """把節區旗標翻成人看得懂的幾個字。"""
    bits = []
    if f & SCN_CODE:
        bits.append('程式碼')
    if f & SCN_INITIALIZED:
        bits.append('資料')
    perm = ''.join(('讀' if f & SCN_READ else '',
                    '寫' if f & SCN_WRITE else '',
                    '執行' if f & SCN_EXECUTE else ''))
    return '%s · %s' % ('+'.join(bits) or '?', perm or '無權限')


# ─────────────────────────────────────────────────────────
#  ① 補回 IAT 資料目錄
#
#  匯入位址表(IAT)是一串指標,程式啟動時由 Windows 載入器把每個
#  函式的真實位址填進去。它的位置藏在匯入描述子的 FirstThunk 欄位裡,
#  而 PE 規格另外要求把「整段 IAT 的起點與長度」填在第 13 個資料目錄(索引 12)。
#
#  ⚠️ 那個目錄**不是**給載入器找 IAT 用的(它走匯入描述子就找得到)。
#     它的用途是讓載入器知道「這一段要暫時開放寫入,填完再改回去」。
#     沒填的話,那一段的可寫與否就完全由節區權限決定。
#
#  這裡不是憑空造一個範圍出來,而是**從匯入描述子自己算出來的**:
#  掃過每一筆描述子的 FirstThunk,取最小的當起點;
#  再沿著那一串 thunk 走到 0 為止,取最大的結尾。
# ─────────────────────────────────────────────────────────
def rva_to_off(secs, rva):
    """把虛擬位址換成檔案位移。落在任何節區之外就回 None。"""
    for s in secs:
        if s['vaddr'] <= rva < s['vaddr'] + max(s['vsize'], s['rsize']):
            return s['raddr'] + (rva - s['vaddr'])
    return None


def compute_iat_range(d, h, secs):
    """從匯入描述子算出 IAT 應該是 (RVA, size)。算不出來就回 None。"""
    imp_rva, imp_size = read_dir(d, h, DIR_IMPORT)
    if not imp_rva:
        return None
    off = rva_to_off(secs, imp_rva)
    if off is None:
        raise DataError('匯入表的位址 0x%08X 不落在任何節區裡。' % imp_rva)

    lo, hi = None, None
    k = 0
    while True:
        b = off + k * 20
        if b + 20 > len(d):
            break
        fields = struct.unpack_from('<IIIII', d, b)
        if not any(fields):          # 全部是 0 = 描述子表結束
            break
        first_thunk = fields[4]
        if first_thunk:
            t = rva_to_off(secs, first_thunk)
            if t is None:
                raise DataError('第 %d 筆匯入的 FirstThunk 0x%08X 不在任何節區裡。'
                                % (k, first_thunk))
            # 沿著這一串指標走到 0 為止,一筆 4 bytes(32 位元執行檔)
            n = 0
            while t + n * 4 + 4 <= len(d):
                if struct.unpack_from('<I', d, t + n * 4)[0] == 0:
                    break
                n += 1
            n += 1                    # 把結尾那個 0 也算進去,規格是這樣算的
            start, end = first_thunk, first_thunk + n * 4
            lo = start if lo is None else min(lo, start)
            hi = end if hi is None else max(hi, end)
        k += 1
        if k > 4096:                  # 防呆:描述子表壞掉時不要無限跑
            raise DataError('匯入描述子超過 4096 筆,這個檔看起來壞了。')
    if lo is None:
        return None
    return (lo, hi - lo)


# ─────────────────────────────────────────────────────────
#  ② 收緊節區權限
#
#  規則很簡單:**只關掉不該有的寫入權限,絕不打開任何權限。**
#  只動這三種節區,而且只在它們現在真的可寫的時候動:
#    · 帶「程式碼」旗標的      → 程式碼不該可寫
#    · .rdata(唯讀資料)      → 名字就叫唯讀
#    · .rsrc(資源)           → 資源是唯讀資料
#  `.data` 這種本來就該可寫的,一律不碰。
# ─────────────────────────────────────────────────────────
TIGHTEN_NAMES = ('.text', '.rdata', '.rsrc')


def sections_to_tighten(secs):
    """回傳 [(節區, 新旗標)]，只列真的需要動的。

    ⚠️ **只動這三個有名字的節區，不動任何其他節區。**

    這一條是量出來的，不是推理出來的。本站拿來當參考的那顆執行檔
    （班主任 2026 年那顆）除了這三個之外，還有第六個**沒有名字**的節區，
    裡面裝的是被工具重建過的匯入表。那顆的作者把它留成**可寫**，
    只拿掉了「內容是資料」那個旗標。

    這支原本的規則是「凡是帶程式碼旗標又可寫的都收緊」，那會連那個
    無名節區一起關掉寫入 —— **比參考實作更激進**。載入器有沒有需要
    寫進那一段，本站還沒有在 Windows 上實測過這一項。

    在測不到的地方，**參考實作就是真相，不要憑推理改進它**。
    所以規則改成白名單：只認 .text / .rdata / .rsrc 這三個標準名字。
    """
    out = []
    for s in secs:
        if not (s['flags'] & SCN_WRITE):
            continue                  # 已經是唯讀，不用動
        if s['name'] in TIGHTEN_NAMES:
            out.append((s, s['flags'] & ~SCN_WRITE))
    return out


def _recalc_checksum(d, h):
    """PE 檔頭的 CheckSum：16 位元加總（進位摺回）再加上檔案大小。

    計算時把 CheckSum 欄位自己當成 0，這是規格規定的。
    改完檔頭一定要重算，不然那個欄位就變成錯的
    （本站量到的那顆原本就是錯的：檔頭裡存的那個值跟實算的 0x0053C452 對不上）。
    """
    b = bytearray(d)
    struct.pack_into('<I', b, h['checksum'], 0)
    s = 0
    for i in range(0, len(b) & ~1, 2):
        s += struct.unpack_from('<H', b, i)[0]
        s = (s & 0xFFFF) + (s >> 16)
    if len(b) & 1:
        s += b[-1]
        s = (s & 0xFFFF) + (s >> 16)
    return (s + len(b)) & 0xFFFFFFFF


# ─────────────────────────────────────────────────────────
#  寫檔的共用底座:符號連結守門 + 原子換檔
#
#  ⚠️ 這一段是 2026-09-05 唯讀稽核之後補的。讀者的遊戲檔絕對不能被弄壞,
#     所以「寫入」這件事在這支裡只有一條路徑,而且那條路徑保證:
#     要嘛整份換好,要嘛正本一個位元組都沒動。
# ─────────────────────────────────────────────────────────

# 換檔那一步到底做過沒有。按 Ctrl-C 的時候要靠它才說得出實話。
# **三態,不是兩態** ——
#   'none'       還沒走到換檔那一步     → 可以說「一個位元組都沒有動到」
#   'replacing'  正要換、還沒確定換完    → 只能說「中斷時正在替換,請 --restore 或比對備份」
#   'done'       os.replace() 已經做完   → 要說「已經改了,用 --restore」
# 少了中間那一態,Ctrl-C 剛好落在 os.replace() 與登記之間就會謊報。
_WROTE_TO_TARGET = {'path': None, 'state': 'none'}


def _reset_mark():
    """把三態旗標歸零。只有自我測試會用到 —— 正式流程一次只換一個檔。"""
    _WROTE_TO_TARGET['path'] = None
    _WROTE_TO_TARGET['state'] = 'none'


class _NoInterrupt(object):
    """把「os.replace + 登記」包成一段不會被 Ctrl-C 切開的動作。

    這段期間收到的 SIGINT 先記著,離開這段之後再照常丟出來。
    這樣 KeyboardInterrupt 的收尾看到的登記,一定跟磁碟上的真實狀態一致 ——
    不會出現「檔案其實已經換過去了,而旗標還停在沒換」的那半行空隙。

    ⚠️ 只**延後**,不吞掉:該丟的 KeyboardInterrupt 離開區塊時還是會丟。
    ⚠️ 不是主執行緒的話 signal.signal() 會失敗,那就退回原本的行為 ——
       不會比以前更糟,也不會因為裝不上處理器就讓整件事失敗。
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


def _refuse_symlink(p, what):
    """目的地是符號連結就拒絕,不跟過去。

    ⚠️ 用 os.path.islink() 不是 os.path.exists():後者對「指向不存在的目標」
       的連結會回 False,等於看不見它,然後就一路跟出去寫到資料夾外面。
       備份路徑是這支自己從檔名組出來的(檔名 + .exepebak),
       那個位置剛好躺著一個連結是完全可能的事。
    """
    p = os.fspath(p)
    if os.path.islink(p):
        raise SystemExit(
            '%s 是一個符號連結,指向 %s。\n'
            '  不敢跟著它寫過去(那會動到這個資料夾以外的檔案)。\n'
            '  請把那個連結移走,或直接對真正的檔案操作。'
            % (what, os.path.realpath(p)))


def _copy_times(src, dst):
    """把時間戳等中繼資料帶過去。純粹是為了跟舊版 shutil.copy2 的行為一致 ——
    失敗不影響檔案內容,所以吞掉例外就好,不要為了時間戳讓整件事失敗。"""
    try:
        shutil.copystat(src, dst)
    except OSError:
        pass


def _atomic_write(dst, data, mode_from=None, tmp_tag='tmp', mark_target=False):
    """把 data 寫成 dst,而且**中途失敗絕不留下半截的 dst**。

    順序:同資料夾開一個唯一暫存檔(tempfile.mkstemp —— 名字不可預測,
    也不會跟別人的檔撞名)→ 寫入 → flush → os.fsync(真的落到碟上)→
    把原本的權限帶過去 → **讀回來逐位元組比對** → 最後才 os.replace() 換上。
    os.replace() 在同一個檔案系統內是原子的:要嘛整份換過去,要嘛完全沒換。
    任何一步失敗就把暫存檔刪掉,dst 一個位元組都不會動到。

    ⚠️ 絕對不可以退回 shutil.copy2(來源, dst):copy2 會**先把 dst 截成
       0 bytes** 再慢慢複製,中途 Ctrl-C、磁碟滿、外接碟被拔掉,就留下一顆
       半截的遊戲檔 —— 而站上每一課都寫著「隨時可以 --restore」。
    """
    dst = os.fspath(dst)
    _refuse_symlink(dst, '要寫入的目標(%s)' % os.path.basename(dst))
    folder = os.path.dirname(os.path.abspath(dst)) or '.'
    fd, tmp = tempfile.mkstemp(
        dir=folder, prefix='.%s.%s-' % (os.path.basename(dst), tmp_tag))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if mode_from and os.path.isfile(mode_from):
            # mkstemp 一律 0600,要把原本的權限帶過去,不然還原完檔案權限就變了
            shutil.copymode(mode_from, tmp)
        with open(tmp, 'rb') as f:
            if f.read() != data:
                raise DataError('暫存檔讀回來跟要寫的內容不一樣,不敢拿它換掉正本。')
        if mark_target:
            # ⚠️ 進不可中斷區之前先登記「正在換」。Ctrl-C 剛好落在這裡的話,
            #    收尾會說「中斷時正在替換,請 --restore 或比對備份」——
            #    既不謊報「什麼都沒動到」,也不謊報「已經換好了」。
            _WROTE_TO_TARGET['path'] = dst
            _WROTE_TO_TARGET['state'] = 'replacing'
        # ⚠️ 換名與登記必須綁在一起。中間被 Ctrl-C 切開的話,收尾看到的旗標
        #    就跟磁碟上的真實狀態對不起來 —— 那正是「說謊」的來源。
        with _NoInterrupt():
            os.replace(tmp, dst)
            if mark_target:
                _WROTE_TO_TARGET['state'] = 'done'
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        # 走到這裡代表換名**沒有發生**:要嘛還沒進不可中斷區,要嘛 os.replace()
        # 自己丟了例外(同一個檔案系統內它是原子的,丟例外就是沒換)。
        # **只有這種情形**才可以把旗標收回去;已經 'done' 的絕對不收。
        if mark_target and _WROTE_TO_TARGET['state'] == 'replacing':
            _reset_mark()
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
    # 兩端都不可以是符號連結。備份是連結 = 拿資料夾外的內容蓋遊戲檔;
    # 目標是連結 = 寫穿到資料夾外面。兩種都在這裡擋掉,不跟過去。
    _refuse_symlink(bak, '備份檔(%s)' % os.path.basename(bak))
    _refuse_symlink(dst, '要還原的目標(%s)' % os.path.basename(dst))
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


def _do_copy(bak, dst):
    """真正覆蓋的那一步,單獨拆成一個函式,是為了讓上面每一道守門都寫成
    「檢查不過就 raise,檢查過才走到這裡」,不會有哪一條路徑漏掉檢查。

    ── 2026-09-05 改成原子還原(唯讀稽核抓到的真漏洞)────────────────
    原本這裡是 shutil.copy2(bak, dst)。copy2 **先把 dst 截成 0 bytes**
    再逐步複製 —— 備份就算通過了上面每一道檢查,只要複製途中按了 Ctrl-C、
    磁碟滿了、外接碟被拔掉,遊戲正本就停在 0 bytes 或半截狀態。
    還原後的比對只能發現「已經壞了」,擋不住正本先被截斷。

    現在走 _atomic_write():暫存檔 → fsync → 讀回逐位元組比對 → os.replace。
    失敗時正本原封不動,而且會照實說是哪一步失敗的。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_symlink(bak, '備份檔(%s)' % os.path.basename(bak))
    with open(bak, 'rb') as f:
        data = f.read()
    # 權限來源:正本還在就照正本的;正本被刪掉(最需要還原的那種情境)就照備份的
    _atomic_write(dst, data, mode_from=(dst if os.path.isfile(dst) else bak),
                  tmp_tag='restore', mark_target=True)
    _copy_times(bak, dst)        # 舊版走 copy2,還原後會帶著備份的時間戳,維持一樣


# Windows 主控台預設編碼(繁中是 cp950)存不下 ⚠️ ✅ 這類符號,
# 輸出被重導向到檔案時會直接 UnicodeEncodeError 中斷。先把輸出轉成 UTF-8。
# ⚠️ 這一段非補不可:--apply 是「先寫檔、再印成功訊息」,印到一半炸掉的話
#    檔案其實已經改好了,讀者卻只看到 traceback,會以為失敗而重跑。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):                # Python 3.6 以下沒有 reconfigure
    pass


# ─────────────────────────────────────────────────────────
#  報告：唯讀，什麼都不會動到
# ─────────────────────────────────────────────────────────
def report(path):
    d = io.open(path, 'rb').read()
    h = parse_pe(d)
    secs = read_sections(d, h)
    print('檔案:%s' % os.path.basename(path))
    print('大小:%s bytes' % format(len(d), ','))

    iat_rva, iat_size = read_dir(d, h, DIR_IAT)
    print('\n① IAT 資料目錄')
    if iat_rva:
        print('   已經填好了:RVA=0x%08X size=%d' % (iat_rva, iat_size))
    else:
        print('   ⚠️ 沒有填(RVA=0 size=0)')
        want = compute_iat_range(d, h, secs)
        if want:
            print('   從匯入描述子算出來應該是:RVA=0x%08X size=%d' % want)
        else:
            print('   這個檔沒有匯入表,算不出來。')

    print('\n② 節區權限')
    for s in secs:
        mark = ''
        if (s['flags'] & SCN_WRITE) and ((s['flags'] & SCN_CODE)
                                         or s['name'] in TIGHTEN_NAMES):
            mark = ('  ⚠️ 可寫' if s['name'] in TIGHTEN_NAMES
                    else '  ⚠️ 可寫（不在白名單，這支不動它）')
        print('   %-9s 0x%08X  %s%s'
              % (s['name'], s['flags'], describe_flags(s['flags']), mark))
    todo = sections_to_tighten(secs)
    print('   %s' % ('要收緊的有 %d 個:%s'
                     % (len(todo), '、'.join(s['name'] for s, _ in todo))
                     if todo else '沒有需要收緊的 ✅'))

    stored = struct.unpack_from('<I', d, h['checksum'])[0]
    calc = _recalc_checksum(d, h)
    print('\n③ 檔頭檢查碼')
    print('   檔內寫的 0x%08X · 實算 0x%08X  %s'
          % (stored, calc, '相符 ✅' if stored == calc else '⚠️ 不符'))
    print('\n（以上全部是讀出來的，這一步不會動到你的檔案。）')


# ─────────────────────────────────────────────────────────
#  真的改：先備份，寫到暫存檔再換過去，最後逐位元組複驗
# ─────────────────────────────────────────────────────────
def apply_changes(path, do_iat, do_sections, apply_it):
    d = io.open(path, 'rb').read()
    h = parse_pe(d)
    secs = read_sections(d, h)
    out = bytearray(d)
    plan = []

    if do_iat:
        rva, size = read_dir(d, h, DIR_IAT)
        if rva:
            print('  ⓘ IAT 目錄本來就填好了，這一項不用做。')
        else:
            want = compute_iat_range(d, h, secs)
            if not want:
                print('  ⓘ 這個檔沒有匯入表，IAT 目錄這一項跳過。')
            else:
                struct.pack_into('<II', out, h['dir'] + DIR_IAT * 8, *want)
                plan.append('補回 IAT 資料目錄（RVA=0x%08X size=%d，8 個位元組）' % want)

    if do_sections:
        # ⚠️ 這兩項有先後關係,不是各自獨立的。
        #
        #    載入器要把匯入位址填進 .rdata,而 .rdata 一旦變成唯讀,
        #    它就必須先把那幾頁暫時改回可寫 —— **而它是照 IAT 資料目錄
        #    給的範圍去改的**。目錄是空的,它就沒有任何範圍可以解鎖,
        #    填不進去,遊戲直接開不起來。
        #
        #    也就是說:**IAT 目錄是空的時候,.rdata 只能留著可寫。**
        #    二十年來社群那顆執行檔就是這樣繞過去的。
        #    要收緊權限,必須同一次把目錄補回去。
        #
        #    所以這裡擋下來,而不是寫完才發現遊戲開不起來。
        iat_rva, _iat_sz = read_dir(out, h, DIR_IAT)
        if not iat_rva:
            raise DataError(
                '這顆的 IAT 資料目錄是空的,現在把節區改成唯讀,遊戲會開不起來。\n'
                '        載入器要靠那個目錄才知道哪一段可以暫時解鎖來填匯入位址。\n'
                '        請把 --iat 一起加上去(兩個一起做才安全)。')
        todo = sections_to_tighten(secs)
        if not todo:
            print('  ⓘ 沒有節區需要收緊，這一項不用做。')
        for s, new in todo:
            struct.pack_into('<I', out, s['flags_off'], new)
            plan.append('%s 拿掉可寫（0x%08X → 0x%08X，4 個位元組）'
                        % (s['name'], s['flags'], new))

    if not plan:
        print('\n沒有要改的東西。')
        return

    # 檔頭動過就一定要重算檢查碼，不然那個欄位會變成錯的
    before_ck = struct.unpack_from('<I', out, h['checksum'])[0]
    struct.pack_into('<I', out, h['checksum'], 0)
    new_ck = _recalc_checksum(bytes(out), h)
    struct.pack_into('<I', out, h['checksum'], new_ck)
    if new_ck != before_ck:
        plan.append('重算檔頭檢查碼（0x%08X → 0x%08X，4 個位元組）' % (before_ck, new_ck))

    print('\n要做的事:')
    for x in plan:
        print('  · %s' % x)
    changed = sum(1 for i in range(len(d)) if d[i] != out[i])
    print('\n總共會動到 %d 個位元組（檔案長度不變:%s bytes）'
          % (changed, format(len(d), ',')))

    if not apply_it:
        print('\n這是預覽，沒有寫入。確定了就加 --apply。')
        return

    bak = path + BAK
    # ⚠️ 寫之前先擋符號連結。備份路徑是這支自己用「檔名 + .exepebak」組出來的,
    #    那個位置躺著一個指向資料夾外面的連結是完全可能的事,跟過去就寫穿了。
    _refuse_symlink(path, '要修改的執行檔(%s)' % os.path.basename(path))
    _refuse_symlink(bak, '備份檔(%s)' % os.path.basename(bak))

    # os.path.lexists() 而不是 exists():後者對「指向不存在目標」的連結會回
    # False,那樣就會把一個連結當成「還沒有備份」而覆蓋掉它。
    if not os.path.lexists(bak):
        # 先寫同資料夾的唯一暫存檔,fsync + 讀回比對都過了才改名成備份。
        # 中途斷掉留下的是暫存檔,不會有人把半截的東西當成完整備份。
        _atomic_write(bak, d, mode_from=path, tmp_tag='part')
        _copy_times(path, bak)   # 舊版走 copy2,備份會帶著原檔的時間戳,維持一樣
        print('\n已備份:%s' % os.path.basename(bak))
    else:
        print('\n備份已經存在，沿用:%s' % os.path.basename(bak))

    _atomic_write(path, bytes(out), mode_from=path, tmp_tag='new', mark_target=True)

    # 複驗：讀回來逐位元組比對，動到的一定要剛好是計畫裡那些
    back = io.open(path, 'rb').read()
    diff = ([i for i in range(len(d)) if d[i] != back[i]]
            if len(back) == len(d) else [])
    if len(back) != len(d) or len(diff) != changed:
        # ⚠️ 複驗不過就一定要非零結束,不可以只印一行 ❌ 然後照樣回 0。
        #    手上還有剛剛逐位元組驗過的完整備份,所以先自動還原,再把指令印出來。
        print('\n❌ 複驗失敗:寫回去的內容跟預期不同。')
        try:
            _restore_from_backup(bak, path)
            print('   已經自動用備份還原回原狀:%s' % os.path.basename(path))
        except BaseException as e:            # SystemExit 也要接住,不能讓它靜靜跳出去
            print('   自動還原沒有成功(%s)。' % e)
            print('   請手動還原:python3 mvp_exe_pe.py "%s" --restore' % path)
        raise DataError('複驗失敗:寫回去的內容跟預期不同(上面已說明處理結果)。')
    print('已寫入。複驗:改動的位元組剛好是預期那 %d 個，其他一個都沒動 ✅' % changed)
    print('\n進遊戲看看。沒效果或有問題就 --restore。')


# ─────────────────────────────────────────────────────────
#  自我測試：自己造一顆最小的 PE 出來測，不需要遊戲檔
#
#  ⚠️ 測試要**兩個方向都測**：該改的有沒有改到，不該改的有沒有被動到。
#     只測「改得動」的測試，遇到「什麼都改」的 bug 一樣會過。
# ─────────────────────────────────────────────────────────
def _fake_pe():
    """造一顆結構正確的 32 位元 PE：兩個節區、一筆匯入、IAT 目錄留空。"""
    SECT_ALIGN = 0x1000
    d = bytearray(0x4000)
    d[0:2] = b'MZ'
    struct.pack_into('<I', d, 0x3C, 0x80)          # e_lfanew
    pe = 0x80
    d[pe:pe + 4] = b'PE\0\0'
    struct.pack_into('<H', d, pe + 4, 0x014C)      # Machine = i386
    struct.pack_into('<H', d, pe + 6, 2)           # 兩個節區
    struct.pack_into('<H', d, pe + 20, 224)        # Optional Header 大小
    opt = pe + 24
    struct.pack_into('<H', d, opt, 0x010B)         # PE32
    struct.pack_into('<I', d, opt + 92, 16)        # 16 個資料目錄
    sect = opt + 224

    text = {'name': b'.text', 'va': SECT_ALIGN, 'raw': SECT_ALIGN,
            'size': SECT_ALIGN, 'flags': SCN_CODE | SCN_EXECUTE | SCN_READ | SCN_WRITE}
    rdata = {'name': b'.rdata', 'va': SECT_ALIGN * 2, 'raw': SECT_ALIGN * 2,
             'size': SECT_ALIGN * 2, 'flags': SCN_INITIALIZED | SCN_READ | SCN_WRITE}
    for i, s in enumerate((text, rdata)):
        b = sect + i * 40
        d[b:b + len(s['name'])] = s['name']
        struct.pack_into('<IIII', d, b + 8, s['size'], s['va'], s['size'], s['raw'])
        struct.pack_into('<I', d, b + 36, s['flags'])

    # .rdata 裡放一筆匯入描述子，FirstThunk 指到同一節區稍後的位置
    imp_rva = rdata['va']
    thunk_rva = rdata['va'] + 0x100
    struct.pack_into('<IIIII', d, rdata['raw'], 0, 0, 0, 0, thunk_rva)
    struct.pack_into('<IIIII', d, rdata['raw'] + 20, 0, 0, 0, 0, 0)   # 結束
    t = rdata['raw'] + 0x100
    struct.pack_into('<III', d, t, 0x80001111, 0x80002222, 0)         # 兩筆 + 結尾 0
    struct.pack_into('<II', d, opt + 96 + DIR_IMPORT * 8, imp_rva, 40)
    struct.pack_into('<II', d, opt + 96 + DIR_IAT * 8, 0, 0)          # 故意留空
    return bytes(d), thunk_rva


def selftest():
    # ⚠️ -O 會把 assert 整個拿掉。這一支的自我測試雖然走 chk() 不走 assert,
    #    但全站十幾支腳本共用同一條規矩:selftest 一律不在 -O 下跑,免得哪一天
    #    有人加了 assert 就變成假綠而沒人看得出來。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2
    ok = True

    def chk(cond, msg):
        nonlocal ok
        print('   %s %s' % ('✅' if cond else '🔴', msg))
        if not cond:
            ok = False

    print('=== 自我測試 ===\n')
    raw, thunk_rva = _fake_pe()
    d = tempfile.mkdtemp(prefix='exepe_')
    p = os.path.join(d, 'fake.exe')
    io.open(p, 'wb').write(raw)
    # 另外開一個「這個資料夾以外」的地方,專門給【8】符號連結那一項當靶。
    outside_dir = tempfile.mkdtemp(prefix='exepe_outside_')
    outside = os.path.join(outside_dir, 'do_not_touch.bin')
    io.open(outside, 'wb').write(b'DO NOT TOUCH')
    try:
        h = parse_pe(raw)
        secs = read_sections(raw, h)

        print('【1】算得出 IAT 範圍嗎')
        got = compute_iat_range(raw, h, secs)
        chk(got == (thunk_rva, 12),
            '算出 RVA=0x%08X size=%d（預期 0x%08X / 12）'
            % (got[0], got[1], thunk_rva) if got else '算不出來')

        print('\n【2】該收緊的收緊，不該動的不動')
        todo = dict((s['name'], new) for s, new in sections_to_tighten(secs))
        chk(set(todo) == {'.text', '.rdata'}, '挑出 .text 與 .rdata（實際:%s）'
            % '、'.join(sorted(todo)) if todo else '一個都沒挑到')
        chk(all(not (v & SCN_WRITE) for v in todo.values()), '新旗標都不帶可寫')
        chk(all((v & SCN_READ) for v in todo.values()), '讀取權限都留著（沒有多關）')

        print('\n【3】真的改一次，然後複驗')
        apply_changes(p, True, True, True)
        d2 = io.open(p, 'rb').read()
        h2 = parse_pe(d2)
        chk(len(d2) == len(raw), '檔案長度沒變')
        chk(read_dir(d2, h2, DIR_IAT) == (thunk_rva, 12), 'IAT 目錄填好了')
        s2 = dict((s['name'], s['flags']) for s in read_sections(d2, h2))
        chk(not (s2['.text'] & SCN_WRITE), '.text 不再可寫')
        chk(s2['.text'] & SCN_EXECUTE, '.text 還是可執行')
        chk(struct.unpack_from('<I', d2, h2['checksum'])[0] == _recalc_checksum(d2, h2),
            '檢查碼跟著重算了')

        print('\n【4】陰性對照：改過的檔再跑一次，不該再動它')
        before = io.open(p, 'rb').read()
        apply_changes(p, True, True, True)
        chk(io.open(p, 'rb').read() == before, '第二次執行沒有再動任何位元組')

        print('\n【5】還原守衛：半截備份不可以蓋掉正本')
        bak = p + BAK
        io.open(bak, 'wb').write(io.open(bak, 'rb').read()[:200])
        live_before = io.open(p, 'rb').read()
        try:
            _restore_from_backup(bak, p)
        except SystemExit:
            pass
        except Exception:
            pass
        chk(io.open(p, 'rb').read() == live_before, '正本沒有被半截備份蓋掉')

        print('\n【6】還原的正常路徑:備份是好的就要真的蓋回去')
        # ⚠️ 這一項不能省。【5】只證明「壞備份會被擋下」,而那條路在 raise 的
        #    時候就結束了,永遠走不到真正覆蓋的那一行。也就是說,少了這一項的話
        #    「合法還原每一次都崩潰」這種缺陷會躲過整套測試,總判定照樣印 ✅。
        io.open(bak, 'wb').write(raw)                   # 放一份完好的備份回去
        io.open(p, 'wb').write(b'\0' * len(raw))        # 把正本弄成不一樣的內容
        _restore_from_backup(bak, p)
        chk(io.open(p, 'rb').read() == raw, '備份完好時真的還原回來了(逐位元組相同)')

        print('\n【7】還原是原子的:換檔那一步失敗,正本必須原封不動')
        # ⚠️ 這一項是【6】的反面。【6】證明「備份好就還原得回來」,
        #    但那條路徑就算是 shutil.copy2(先截斷再複製)也照樣會過。
        #    真正要證的是**失敗的時候**正本沒有被截成半截。
        io.open(bak, 'wb').write(raw)
        io.open(p, 'wb').write(b'\xEE' * len(raw))
        live7 = io.open(p, 'rb').read()
        real_replace = os.replace

        def _boom(_src, _dst):
            raise OSError(28, '假裝磁碟滿了')

        os.replace = _boom
        try:
            _restore_from_backup(bak, p)
        except BaseException:
            pass
        finally:
            os.replace = real_replace
        chk(io.open(p, 'rb').read() == live7, '換檔失敗時正本一個位元組都沒動')
        chk(len(io.open(p, 'rb').read()) == len(raw), '正本沒有被截短')
        junk7 = [x for x in os.listdir(d) if x.startswith('.fake.exe.')]
        chk(not junk7, '失敗之後沒有留下暫存檔(實際 %d 個)' % len(junk7))

        print('\n【8】符號連結守衛:連結指到資料夾外面就拒絕,不跟過去')
        os.remove(bak)
        os.symlink(outside, bak)                       # 備份的位置放一個連結
        live8 = io.open(p, 'rb').read()
        refused = False
        try:
            _restore_from_backup(bak, p)
        except SystemExit:
            refused = True
        except Exception:
            pass
        chk(refused, '--restore 拒絕了指向外面的備份連結')
        chk(io.open(outside, 'rb').read() == b'DO NOT TOUCH', '資料夾外那個檔沒被動到')
        chk(io.open(p, 'rb').read() == live8, '正本沒有被連結後面的內容蓋掉')

        # 斷掉的連結(指向不存在的檔)也要認得出來。os.path.exists() 對它回 False,
        # 少了 _restore_from_backup 開頭那一道,就會被當成「找不到備份」——
        # 訊息指錯方向,讀者會去找一個其實躺在那裡的連結。
        os.remove(bak)
        os.symlink(os.path.join(outside_dir, 'nope.bin'), bak)
        msg8 = ''
        try:
            _restore_from_backup(bak, p)
        except BaseException as e:
            msg8 = str(e)
        chk('符號連結' in msg8,
            '斷掉的連結也被認出是連結(訊息開頭:%s)' % msg8.split('\n')[0][:34])


        p2 = os.path.join(d, 'fake2.exe')
        io.open(p2, 'wb').write(raw)
        os.symlink(outside, p2 + BAK)                  # --apply 也要擋
        refused2 = False
        try:
            apply_changes(p2, True, True, True)
        except SystemExit:
            refused2 = True
        except Exception:
            pass
        chk(refused2, '--apply 遇到連結備份也拒絕')
        chk(io.open(outside, 'rb').read() == b'DO NOT TOUCH', '外面那個檔還是沒被動到')
        chk(io.open(p2, 'rb').read() == raw, 'fake2.exe 一個位元組都沒被改')

        print('\n【9】寫入是原子的:換檔失敗時不留半截的正本、也不留假備份')
        p3 = os.path.join(d, 'fake3.exe')
        io.open(p3, 'wb').write(raw)
        os.replace = _boom                             # 連備份都換不上去
        try:
            apply_changes(p3, True, True, True)
        except BaseException:
            pass
        finally:
            os.replace = real_replace
        chk(io.open(p3, 'rb').read() == raw, '備份就失敗時,正本原封不動')
        chk(not os.path.lexists(p3 + BAK), '沒有留下一份半截的備份')
        chk(not [x for x in os.listdir(d) if x.startswith('.fake3.exe.')],
            '沒有留下暫存檔')

        p4 = os.path.join(d, 'fake4.exe')
        io.open(p4, 'wb').write(raw)

        def _boom_on_exe(src, dstp):                   # 只讓「換正本」那一步失敗
            if os.path.abspath(dstp) == os.path.abspath(p4):
                raise OSError(28, '假裝磁碟滿了')
            return real_replace(src, dstp)

        os.replace = _boom_on_exe
        try:
            apply_changes(p4, True, True, True)
        except BaseException:
            pass
        finally:
            os.replace = real_replace
        chk(io.open(p4, 'rb').read() == raw, '備份成功、換正本失敗時,正本仍是原樣')
        chk(os.path.isfile(p4 + BAK) and io.open(p4 + BAK, 'rb').read() == raw,
            '備份留下來而且是完整的(還原得回去)')
        chk(not [x for x in os.listdir(d) if x.startswith('.fake4.exe.')],
            '沒有留下暫存檔')

        print('\n【10】Ctrl-C 要說得出實話:換檔做過沒做過分得出來')
        # ⚠️ 兩個方向都要測。只測「做過會記錄」的話,「永遠記錄」的 bug 一樣會過,
        #    那會讓預覽被中斷時謊報「檔案已經改了」。
        p5 = os.path.join(d, 'fake5.exe')
        io.open(p5, 'wb').write(raw)
        _reset_mark()
        apply_changes(p5, True, True, False)           # 只是預覽
        chk(_WROTE_TO_TARGET['path'] is None
            and _WROTE_TO_TARGET['state'] == 'none',
            '預覽沒有記錄(被中斷時才說得出「什麼都沒動到」)')
        apply_changes(p5, True, True, True)            # 真的寫
        chk(_WROTE_TO_TARGET['path'] == p5
            and _WROTE_TO_TARGET['state'] == 'done',
            '真的換過檔就記錄下來(被中斷時才不會謊報沒動到)')
        _reset_mark()

        _atomic_write(os.path.join(d, 'plain.bin'), b'x', tmp_tag='probe')
        chk(_WROTE_TO_TARGET['path'] is None,
            '不是換正本的寫入(例如做備份)不會被記成「已改」')

        print('\n【11】符號連結守衛:正本自己是連結、還原目標是連結,都要拒絕')
        # ⚠️【8】測的是「備份的位置放了一個連結」。這一項補另外兩個寫入目的地:
        #    ① --apply 的正本自己就是連結 ② --restore 要寫回去的目標是連結。
        #    餌指向的是資料夾外面一顆**合法的 PE**,所以不會在解析階段就被擋掉 ——
        #    真正要證的是「守衛擋下來」,不是「檔案看起來不對」。
        outside_exe = os.path.join(outside_dir, 'real_outside.exe')
        io.open(outside_exe, 'wb').write(raw)
        p6 = os.path.join(d, 'fake6.exe')
        os.symlink(outside_exe, p6)
        refused6 = False
        try:
            apply_changes(p6, True, True, True)
        except SystemExit:
            refused6 = True
        except Exception:
            pass
        chk(refused6, '--apply 遇到「正本自己是連結」就拒絕(不跟過去改外面那顆)')
        chk(io.open(outside_exe, 'rb').read() == raw, '連結後面那顆檔一個位元組都沒被改')
        chk(not os.path.lexists(p6 + BAK), '也沒有在連結旁邊留下備份')

        p7 = os.path.join(d, 'fake7.exe')
        os.symlink(outside_exe, p7)
        io.open(p7 + BAK, 'wb').write(raw)             # 備份是好的,問題出在目標
        refused7 = False
        try:
            _restore_from_backup(p7 + BAK, p7)
        except SystemExit:
            refused7 = True
        except Exception:
            pass
        chk(refused7, '--restore 遇到「要寫回去的目標是連結」也拒絕')
        chk(io.open(outside_exe, 'rb').read() == raw, '外面那顆檔還是沒被還原蓋過去')

        print('\n【12】Ctrl-C 不可以說謊:不可中斷區與三態旗標')
        # ⚠️ 這裡**不送真的訊號**。Windows 的 os.kill() 不是送訊號而是直接砍行程,
        #    測試自己會死在那一行。改成直接呼叫「當下裝著的那個處理器」——
        #    測到的是同一段邏輯:_NoInterrupt 有沒有把處理器換上去、有沒有收回來、
        #    有沒有把該丟的 KeyboardInterrupt 留到離開區塊才丟。
        old_sigint = signal.getsignal(signal.SIGINT)
        trail = []
        late = False
        try:
            with _NoInterrupt():
                signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
                trail.append('區塊跑完了')
        except KeyboardInterrupt:
            late = True
        chk(trail == ['區塊跑完了'], '區塊裡的動作沒有被中斷切開(它要先做完)')
        chk(late, '離開區塊之後 KeyboardInterrupt 照樣丟出來(只延後,沒吞掉)')
        chk(signal.getsignal(signal.SIGINT) is old_sigint, '原本的 Ctrl-C 處理器有還回去')

        # 換檔失敗時旗標要收回「沒動到」,不可以卡在「正在換」——
        # 卡住的話,一次失敗的預覽被 Ctrl-C 就會嚇讀者說「可能已經換過去了」。
        p8 = os.path.join(d, 'fake8.exe')
        io.open(p8, 'wb').write(raw)
        _reset_mark()
        os.replace = _boom
        try:
            _atomic_write(p8, b'x' * 32, mark_target=True)
        except BaseException:
            pass
        finally:
            os.replace = real_replace
        chk(_WROTE_TO_TARGET['state'] == 'none',
            '換檔失敗時旗標收回「沒動到」(不會卡在「正在換」嚇人)')
        chk(io.open(p8, 'rb').read() == raw, '換檔失敗,正本仍是原樣')
        _atomic_write(p8, b'x' * 32, mark_target=True)
        chk(_WROTE_TO_TARGET['state'] == 'done' and _WROTE_TO_TARGET['path'] == p8,
            '換檔成功時旗標是「已換」(被中斷才說得出實話)')
        _reset_mark()

    finally:
        shutil.rmtree(d, ignore_errors=True)
        shutil.rmtree(outside_dir, ignore_errors=True)

    print('\n' + '=' * 46)
    print('總判定: %s' % ('✅ 全部通過' if ok else '❌ 有問題'))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(
        description='把改過的 MVP Baseball 2005 執行檔的 PE 檔頭修回合乎規格。')
    ap.add_argument('exe', nargs='?', help='遊戲執行檔的完整路徑（mvp2005.exe）')
    ap.add_argument('--iat', action='store_true', help='補回 IAT 資料目錄')
    ap.add_argument('--sections', action='store_true', help='收緊節區的寫入權限')
    ap.add_argument('--apply', action='store_true', help='真的寫入（沒加就只是預覽）')
    ap.add_argument('--restore', action='store_true', help='從 %s 還原' % BAK)
    ap.add_argument('--selftest', action='store_true', help='自我測試，不需要遊戲檔')
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.exe:
        ap.print_help()
        return 2

    # 目標本身是符號連結的話:**要寫的時候一律拒絕,不跟過去**。
    # ⚠️ 舊版是 realpath() 解開之後照樣寫。那等於「你指著 A,我去改 B」——
    #    B 可能根本不在遊戲資料夾裡,而備份(.exepebak)又是照你打的 A 組出來的,
    #    出事的時候還原會找不到對的東西。所以現在改成拒絕,請直接對真正的檔操作。
    # 只讀的模式不受限制(不加參數的檢查、加了 --iat/--sections 但沒 --apply
    # 的預覽)—— 讀不會弄壞任何人的檔案。
    # 只看最後那一個檔;路徑中間的資料夾是連結沒關係(有人把遊戲放在別顆碟)。
    if (a.apply or a.restore) and os.path.islink(a.exe):
        _refuse_symlink(a.exe, '要修改的執行檔(%s)' % os.path.basename(a.exe))

    # ⚠️ 「檔案不存在」不可以擋掉 --restore。最需要還原的情境正是
    #    「執行檔被刪掉 / 被別的東西蓋掉」,那時候備份就躺在旁邊。
    if not a.restore and not os.path.isfile(a.exe):
        print('找不到這個檔:%s' % a.exe)
        return 2
    try:
        if a.restore:
            bak = a.exe + BAK
            # 還原前:備份自己得是一顆執行檔(拿錯檔就擋下來)。
            # 半截備份那一道更關鍵,由 _restore_from_backup() 驗 PE 節區表;
            # 「不存在」與「0 bytes」也留給它講,它的訊息說得更清楚。
            if (os.path.exists(bak) and os.path.getsize(bak) > 0
                    and io.open(bak, 'rb').read(2) != b'MZ'):
                print('這份備份的開頭不是 MZ（不是執行檔），不敢拿它覆蓋 %s。' % a.exe)
                return 1
            _restore_from_backup(bak, a.exe)
            # 還原後:整份逐位元組比對,不是只比開頭也不是只比長度。
            same = (io.open(bak, 'rb').read() == io.open(a.exe, 'rb').read())
            print('已還原:%s' % os.path.basename(a.exe))
            print('複驗:內容與備份%s' % ('相同 ✅' if same else '不同 ❌'))
            if not same:
                print('還原後的內容跟備份對不起來,請手動檢查那兩個檔。')
                return 1
            return 0
        if not (a.iat or a.sections):
            report(a.exe)
            return 0
        apply_changes(a.exe, a.iat, a.sections, a.apply)
        return 0
    except DataError as e:
        print('\n停下來了:%s' % e)
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # ⚠️ 「什麼都沒動到」這句話只有在換檔那一步還沒發生的時候才可以說。
        #    三態各講各的實話,一律以 130 結束(128 + SIGINT),**不可以回 0**。
        _state = _WROTE_TO_TARGET['state']
        _done = _WROTE_TO_TARGET['path']
        if _state == 'none':
            print('\n你按了 Ctrl-C。換檔那一步還沒發生,你的檔案一個位元組都沒有動到。')
        elif _state == 'replacing':
            print('\n你按了 Ctrl-C,而中斷的時候正在替換:%s' % _done)
            print('這個檔可能已經換過去,也可能還沒有。請跟備份比對,或直接還原:')
            print('  python3 mvp_exe_pe.py "%s" --restore' % _done)
        else:
            print('\n你按了 Ctrl-C,但檔案已經換過去了:%s' % _done)
            print('要回到原狀請跑:python3 mvp_exe_pe.py "%s" --restore' % _done)
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
