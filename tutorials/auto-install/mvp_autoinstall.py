#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_autoinstall.py —— 把一包模組自動放進遊戲裡正確的位置

    先建索引(看你的遊戲長什麼樣)  python3 mvp_autoinstall.py "<遊戲資料夾>" --index
    清點一包模組(完全不動檔案)    python3 mvp_autoinstall.py "<遊戲資料夾>" --scan "<模組資料夾>"
    預覽安裝                      python3 mvp_autoinstall.py "<遊戲資料夾>" --install "<模組資料夾>"
    真的安裝                      (上面那行加 --apply)
    還原                          python3 mvp_autoinstall.py "<遊戲資料夾>" --restore
    自我測試(不碰任何遊戲檔)      python3 mvp_autoinstall.py --selftest

╔══════════════════════════════════════════════════════════════════╗
║ 這支跟 2008 年那個安裝器最大的差別                                ║
║                                                                  ║
║ 那個工具靠模組作者附的設定檔告訴它「這個檔要放哪」。              ║
║ 沒附設定檔的模組,它就沒辦法。                                    ║
║                                                                  ║
║ 這支反過來:**在你自己的遊戲上現場建一份索引**,                   ║
║ 問「這個檔名在這份遊戲裡本來住在哪」。                            ║
║ 不需要模組作者配合,而且你裝過什麼它就照什麼算。                   ║
╚══════════════════════════════════════════════════════════════════╝

⚠️ 不確定就不做。同一個檔名在多個地方出現時,本工具**列出全部選項然後停下來**,
   不會替你挑一個。猜錯會蓋掉別的東西,而你不會知道。

⚠️ 寫**進封裝檔**用的是附加模式:舊資料留在原地,只改目錄表。
   但「整個 .big 替換檔」那種走的是散裝檔那一支,**整個覆蓋**,
   舊內容一個位元組都不會留在檔案裡,只能靠備份救回來。
   第一次動到某個檔之前會自動備份。

輸入 / 輸出
    輸入  兩個資料夾。一個是你的遊戲資料夾(裡面要有 data,沒有就不讓你跑),
          一個是已經解開的模組資料夾。**不需要任何設定檔**,
          模組作者有沒有附說明書都一樣。
    輸出  --index 印這份遊戲的索引摘要;--scan 印一包模組的清點結果;
          --install 不加 --apply 印預覽。這三個全部只往螢幕印字,
          一個位元組都不寫。會動到檔案的是 --install 加上 --apply,以及 --restore。

四個指令一句話說完
    --index    走過整個遊戲資料夾建索引,只告訴你「有多少檔名是唯一的」
    --scan     拿那份索引去對一包模組,把每個檔分成 ✅ / ⏭ / ⚠ / ❓ 四類
               (⏭ 是「算得出去處但本工具不寫那一層」的巢狀壓縮封裝檔)
    --install  同上,再加一段「要怎麼裝」。加 --apply 才真的裝
    --restore  走過整個遊戲資料夾,把本工具做的 .autobak 蓋回去
               (驗不過的那幾份跳過並印出原因,不中斷整趟)
    --selftest 不需要遊戲資料夾,自己造一份最小的假遊戲來測上面那些安全網。
               含反向餌:故意做一件必須失敗的事,失敗不了才是問題

安全網
    · 唯讀是預設,但有一個例外:--install 沒有 --apply 就不寫,而且只有 ✅
      那一類會被寫入;而 --restore 不吃 --apply,打下去就會把找得到的
      .autobak 一個一個蓋回去(本站實測)。驗不過結構的那幾個會被跳過並印出
      原因,不會中斷整趟,最後給一行總計 —— 有任何一個沒還原就回傳非 0。
    · 第一次動到某個檔之前自動備份成 <原檔名>.autobak,備份是原子的
      (寫同資料夾的唯一暫存檔 → fsync → 讀回來比 sha256 → os.replace),
      中途被中斷不會留下半截備份;備份旁邊再留一張收據
      <原檔名>.autobak.receipt(那一刻的大小與 sha256),
      還原時靠它證明備份是完整的;已經有 .autobak 就保留最早那一份。
    · 寫檔一律不原地截斷。散裝檔整包寫進同資料夾的暫存檔、讀回來比對過才
      os.replace;封裝檔先把現況逐位元組複製成暫存檔(**不是**重新打包 ——
      孤兒資料一個位元組不少地留著),在暫存檔上附加 + 改目錄 + 改檔頭,
      讀回來驗過才換上去。Ctrl-C / 磁碟滿 / 外接碟被拔掉都不會留下半套的遊戲檔。
    · 「換上去」跟「記下已經換過」綁成同一段,中間收到 Ctrl-C 會先記著、
      做完才丟出來,所以收尾講的話一定跟磁碟上的狀態一致。萬一連這一段都
      綁不起來,收尾會說「中斷的時候正在替換 X」,而不是說「什麼都沒動到」。
    · 暫存檔一律用系統的 mkstemp 在同一個資料夾裡開(名字猜不到、也不可能
      開到別人先放好的同名符號連結);正本或備份本身是符號連結一律拒絕。
    · 遊戲資料夾或模組資料夾裡只要有一個檔讀不到,--scan 與 --install
      **整批停下來**,不會「略過那一個、其餘照裝」。
    · 寫封裝檔一律附加:新資料接在檔尾,只改目錄那 8 個位元組
      跟檔頭大小欄那 4 個,舊資料一個位元組都不動。
    · --restore 先驗收據(大小 + sha256),再驗備份的結構
      (BIGF 檔頭宣告長度 / LOCH 位移表 / MZ 節區表);**沒有收據的舊備份
      不會自動還原** —— 半截的純文字備份看不出來,不敢賭。
    · 本工具自己做的 .autobak 不進索引,所以第一次裝完之後不會變成
      「同一個名字有兩個去處」把自己卡死,也不會有人不小心往備份裡寫。
    · 只寫遊戲資料夾裡面:去處算出來是符號連結、或路徑跑到資料夾外面,一律不寫。
    · 寫不進去(唯讀 / 遊戲正開著鎖住 / 要系統管理員權限)在**備份之前**就
      擋下來,不會留下一個沒用到的 .autobak,也不會丟一整串 traceback。

做不到的事(先知道,省得白試)
    · **不猜**。同一個檔名有多個去處時列出全部然後停下來。
      ⚠ 那一類永遠不會被自動安裝,即使加了 --apply 也一樣。
    · 只換既有的東西。遊戲裡沒有同名檔案的一律歸到 ❓ 不動,
      因為它無從得知該放哪(新臉皮、新球衣這類新增檔案就是這一種)。
    · 巢狀壓縮封裝檔(封裝檔裡只裝一個壓縮過的封裝檔)那一層,
      索引讀得到,但不寫回去(要重壓一整層,風險比較高)。
    · 散裝檔是整個覆蓋,不做內容層級的合併。
    · 同一趟裡如果既要整個換掉某個封裝檔、又要往那個封裝檔裡塞東西,
      會分成兩趟做:先換掉封裝檔本身,再把那些項目寫進**換上去的那一份**。
      索引是開頭建一次的、對新檔已經失效,所以第二趟重讀一次現場再寫。
    · 安裝時把模組檔**原封不動**接到檔尾,不重新壓縮,
      所以那個檔本來是什麼形式,遊戲拿到的就是什麼形式。
    · 重複裝會讓封裝檔一直變大(舊資料還躺在檔案裡,只是沒人指向它)。
      想收回去就 --restore 回到最初那一份再重來。
    · 備份完不完整靠的是收據(做備份的當下記下來的大小與 sha256),
      所以本工具做的備份驗得出來。但 2026-09-05 以前做的 .autobak 沒有收據,
      那些**一律不自動還原** —— 半截的純文字備份跟一份合法的短檔在結構上
      長得一模一樣,事後看不出來。要用那種舊備份請自己手動複製回去。
    · 「裝完之後遊戲畫面正不正常」本站沒驗過。驗過的是有沒有正確寫進去、
      以及還原之後是不是逐位元組回到原狀。

讀原始碼的人請注意:本檔另外定義了 big_entries / read_entry /
qfs_compress_literal / fsh_first_image / fsh_replace_pixels 與 FSH_FORMATS
那張格式表,**目前這支腳本裡沒有任何地方呼叫它們**,不必去找呼叫點。
底下各自標了一行「目前沒有呼叫點」。

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

import os
import sys
import struct
import shutil
import hashlib
import tempfile
import argparse
import signal

# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

# 本工具做出來的暫存檔一律用這個開頭。
# ⚠️ 2026-09-05 稽核抓到的:舊寫法是 dst + '.part' 這種**猜得到**的名字。
#    那個名字可以被人事先做成一個指向遊戲資料夾外面的符號連結,接下來
#    shutil.copy2 / open(..., 'wb') 會**沿著連結**把外面那個檔截成 0 ——
#    就算後面的 os.replace 只換掉連結本身,傷害在那之前就已經造成了。
#    (Path.exists() 也擋不住:連結指向的檔不存在時它回 False。)
#    改用 tempfile.mkstemp:它以 O_CREAT|O_EXCL 開檔,名字被佔走就換一個,
#    所以永遠不可能開到別人先放好的東西。
TMP_PREFIX = '.mvpai-tmp-'
RECEIPT_TAIL = '.receipt'

# 這一趟裡真的已經被 os.replace 換掉的遊戲檔。
# 按 Ctrl-C 的時候要靠它決定該說「什麼都沒動到」還是「已經改了,去還原」——
# 這兩句話對使用者的意義完全相反,猜錯比不說還糟。
_TOUCHED = []

# 三態的中間那一態:「已經開始換名、還沒登記完」。
# 只有 _commit_replace 會動它,而且進出都在下面那個不可中斷的區段裡面。
_REPLACING = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包成一段:這期間收到 Ctrl-C 先記著,離開才丟出來。

    為什麼需要它 —— 2026-09-06 稽核指出的空窗:
    `os.replace()` 已經把正本換掉了,但程式還沒把「換過了」登記到 _TOUCHED,
    Ctrl-C 剛好落在這兩行中間,收尾就會照舊狀態說「什麼都沒有動到」。
    那句話跟事實相反,而使用者會照它決定要不要去還原。

    非主執行緒之類裝不上處理器的情況就退回原本的行為(不會比以前更糟),
    那時候靠 _REPLACING 那一態兜底。
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
            signal.signal(signal.SIGINT, self._old)
        if self._pending and exc_type is None:
            raise KeyboardInterrupt
        return False


def _commit_replace(tmp, dst, record=False):
    """把暫存檔換上去。record 為真代表 dst 是遊戲檔,換成功就要登記下來。

    「換名」跟「登記」中間不可以被 Ctrl-C 切開,不然收尾講的話會跟磁碟對不上。

    ⚠️ 例外路徑判斷「到底換成了沒有」不看 Python 這邊的旗標,看**檔案系統**:
       os.replace 做成了,暫存檔就不在原地了。設旗標的那一行本身也可能被中斷,
       檔案系統的事實不會。寧可多留一個「正在換」的標記(使用者被叫去比對備份,
       不痛),也不要少留(使用者以為沒事)。
    """
    dst = os.fspath(dst)
    if not record:
        with _NoInterrupt():
            os.replace(tmp, dst)
        return
    _REPLACING.append(dst)
    try:
        with _NoInterrupt():
            os.replace(tmp, dst)
            _TOUCHED.append(dst)
            _REPLACING.remove(dst)
    except BaseException:
        if dst in _REPLACING and os.path.lexists(tmp):
            # 暫存檔還在原地 —— 換名沒有做成,dst 一個位元組都沒被動到。
            _REPLACING.remove(dst)
        raise


def _print_touch_state():
    """收尾時誠實講這一趟到底動了什麼。三態,講錯任何一態都會害人做錯決定:

      還沒動    遊戲資料夾跟你按下去之前一模一樣
      正在換 X  中斷剛好落在換名那一瞬間 —— X 可能換過,也可能還沒
      已經換過  換掉幾個、最後一個是誰,去 --restore
    """
    if _REPLACING:
        print('     中斷的時候正在替換 %s —— 它可能已經換過,也可能還沒。'
              % os.path.basename(_REPLACING[-1]))
        print('     請跑 --restore 還原,或拿它旁邊的 .autobak 比對。')
    if _TOUCHED:
        print('     這一趟已經換掉 %d 個檔(最後一個是 %s)。'
              % (len(_TOUCHED), os.path.basename(_TOUCHED[-1])))
        print('     每一個被換掉的檔旁邊都有備份,要回到動手前的樣子就跑'
              ' --restore。')
    if not _TOUCHED and not _REPLACING:
        print('     還沒有任何一個檔被換掉 —— '
              '遊戲資料夾跟你按下去之前一模一樣。')


def _quiet_remove(path):
    """刪不掉就算了 —— 這是收尾用的,不該把真正的錯誤蓋掉。"""
    try:
        os.remove(path)
    except OSError:
        pass


def _new_temp_beside(dst):
    """在 dst 所在的**同一個資料夾**裡開一個獨一無二的暫存檔,回 (fd, 路徑)。

    一定要同一個資料夾:os.replace 只有在同一個檔案系統上才是原子的,
    跨磁碟會退化成「複製 + 刪除」,那就沒有原子性可言了。
    """
    d = os.path.dirname(os.path.abspath(os.fspath(dst))) or '.'
    # 檔名有長度上限(多數檔案系統 255 個位元組),名字很長的檔要先截短,
    # 不然 mkstemp 組不出名字會直接失敗。
    base = os.path.basename(os.fspath(dst))[:80]
    return tempfile.mkstemp(dir=d, prefix=TMP_PREFIX + base + '-')


def _sha256_of(path):
    """整個檔案的 sha256。一次讀 1 MB,一百多 MB 的封裝檔也不會吃光記憶體。"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _copy_exact(src, dst):
    """把 src 完整寫進 dst(dst 必須是本工具自己剛開出來的暫存檔)。

    寫完 flush + fsync,再**讀回來**比 sha256 ——
    「寫進去了」跟「寫對了」是兩件事,中間隔著磁碟滿、外接碟斷線、檔案系統出錯。
    """
    h = hashlib.sha256()
    with open(dst, 'wb') as fo, open(src, 'rb') as fi:
        while True:
            chunk = fi.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            fo.write(chunk)
        fo.flush()
        os.fsync(fo.fileno())
    if _sha256_of(dst) != h.hexdigest():
        raise DataError('複製出來的內容跟 %s 對不上(磁碟出問題?)' % src)


def _copy_verified(src, dst, record=False):
    """把 src 完整複製成 dst —— 要嘛完整、要嘛 dst 原封不動,沒有中間狀態。

    步驟寫死成這個順序,每一步都在擋一種真的會發生的事:
      1. dst 是符號連結就拒絕(不然會寫到遊戲資料夾外面去)
      2. 寫到**同資料夾**的唯一暫存檔(mkstemp,名字猜不到也佔不走)
      3. flush + fsync —— 資料真的落到磁碟,不是還躺在作業系統的快取裡
      4. 讀回來比 sha256(在 _copy_exact 裡)
      5. 保留權限
      6. 都對了才 os.replace,而且「換名 + 登記」綁成一段不可中斷的動作
    任何一步失敗都會把暫存檔刪掉,dst 一個位元組都不會變。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 有一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。所以先 os.fspath。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    if os.path.islink(dst):
        raise DataError('%s 是符號連結,不敢往它寫(會寫到別的地方去)' % dst)
    fd, tmp = _new_temp_beside(dst)
    try:
        os.close(fd)
        _copy_exact(src, tmp)
        try:
            shutil.copystat(src, tmp)
            if os.path.exists(dst):
                shutil.copymode(dst, tmp)
        except OSError:
            pass                       # 權限複製不了不該讓整趟失敗
        _commit_replace(tmp, dst, record)   # 原子換名 + 登記,中間不吃 Ctrl-C
    finally:
        # 成功的話 tmp 已經改名了,刪不到很正常;失敗的話這一行負責不留垃圾。
        _quiet_remove(tmp)


def _atomic_write_bytes(dst, data, record=False):
    """把一整包位元組原子地寫成 dst。回 None(成功)或不能寫的原因(字串)。

    ⚠️ 散裝檔那一趟以前是 open(dst, 'wb') 直接寫:開檔那一瞬間正本就被截成
       0 bytes,之後才慢慢寫回去。中途斷電 / Ctrl-C / 磁碟滿,正本就停在半截 ——
       而這一支對散裝檔是**整個覆蓋**,半截的意思就是遊戲檔壞了。
    """
    dst = os.fspath(dst)
    if os.path.islink(dst):
        return '%s 是符號連結,寫下去會寫到遊戲資料夾外面' % os.path.basename(dst)
    fd, tmp = _new_temp_beside(dst)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        try:
            if os.path.exists(dst):
                shutil.copymode(dst, tmp)
        except OSError:
            pass
        with open(tmp, 'rb') as f:
            if f.read() != data:
                return '讀回來跟要寫的不一樣(磁碟出問題?),正本沒有動'
        _commit_replace(tmp, dst, record)
        return None
    finally:
        _quiet_remove(tmp)


def _receipt_path(bak):
    """收據就躺在備份旁邊:<原檔名>.autobak.receipt"""
    return os.fspath(bak) + RECEIPT_TAIL


def _write_receipt(bak):
    """備份做好之後,在它旁邊留一張收據:大小 + sha256。

    為什麼需要收據 —— 這是 2026-09-05 稽核指出的洞:
    半截的**純文字**備份跟一份合法的短檔在結構上長得一模一樣,
    切在換行上的時候連「分隔表格斷在半筆」那一道也看不出來
    (實測:每行等長的表格截成 60% 正好落在行尾,結構檢查與地板全部放行)。
    「這份備份完不完整」沒辦法事後從備份自己身上看出來,
    只能在**做備份的當下**把答案記下來。收據就是那個答案。
    """
    body = ('mvp_autoinstall backup receipt v1\nsize %d\nsha256 %s\n'
            % (os.path.getsize(bak), _sha256_of(bak)))
    why = _atomic_write_bytes(_receipt_path(bak), body.encode('utf-8'))
    if why:
        raise DataError('收據寫不出來:%s' % why)


def _check_receipt(bak):
    """拿收據驗備份。回 None(可以用)或不可以用的原因(字串)。"""
    rp = _receipt_path(bak)
    if os.path.islink(rp) or not os.path.isfile(rp):
        return ('找不到它的收據(%s)。收據是備份完成的那一刻寫下來的,'
                '沒有收據就證明不了這份備份是完整的' % os.path.basename(rp))
    try:
        fields = {}
        with open(rp, 'r', encoding='utf-8') as f:
            for line in f:
                bits = line.split()
                if len(bits) == 2:
                    fields[bits[0]] = bits[1]
        want_size = int(fields['size'])
        want_sha = fields['sha256']
    except (OSError, KeyError, ValueError):
        return '收據本身讀不出來或格式不對(%s)' % os.path.basename(rp)
    n = os.path.getsize(bak)
    if n != want_size:
        return '收據說這份備份應該是 %d bytes,實際只有 %d bytes' % (want_size, n)
    if _sha256_of(bak) != want_sha:
        return '備份的內容跟收據上的 sha256 對不上 —— 它被改過或壞了'
    return None


def _ensure_backup(target, bak):
    """第一次動到某個檔之前先備份,而且備份完立刻寫一張收據。

    回 None 代表可以往下走,回字串代表**不可以**(原因)。

    ⚠️ 「已經有備份但沒有收據」也回拒絕,而且這一條很要緊:
       那種備份是舊版做的,--restore 不會自動還原它。如果這裡放行繼續改遊戲檔,
       使用者最後會落到「遊戲被改過 + 備份還不了」——
       比一開始就不讓他裝還糟。要繼續請先把那份舊備份移走或改名。
    """
    if os.path.islink(bak):
        return '%s 是符號連結,不敢往它寫' % os.path.basename(bak)
    if os.path.lexists(bak) and not os.path.isfile(bak):
        return '%s 已經存在,而且它不是一個普通檔案' % os.path.basename(bak)
    if os.path.lexists(bak):
        # 備份只做一次:第二次以後保留最早那一份,
        # 因為那一份才是「還沒被本工具動過的」。
        why = _check_receipt(bak)
        if why:
            return ('已經有一份 %s,但%s;'
                    '請先把它(以及它的收據)移走或改名再跑一次'
                    % (os.path.basename(bak), why))
        return None
    try:
        _copy_verified(target, bak)
    except (OSError, DataError) as err:
        return '備份失敗,所以不動這個檔:%s' % err
    try:
        _write_receipt(bak)
    except (OSError, DataError) as err:
        # 收據寫不出來就把剛做好的那份備份收掉。留著它的話,下一次執行會被
        # 「已經有一份沒有收據的舊備份」那一道永遠擋住 —— 等於自己把自己鎖死。
        _quiet_remove(bak)
        return '備份失敗,所以不動這個檔:%s' % err
    print('     已備份 %s' % os.path.basename(bak))
    return None


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

    ── 2026-09-05 再補一道,而且是最強的一道:**收據** ────────────────
    上面那些全部是在「猜」這份備份完不完整,而純文字檔猜不出來:
    切在換行上的半截檔跟一份合法的短檔在結構上長得一模一樣
    (實測:每行等長的表格截成 60% 正好落在行尾,結構那幾道與地板全部放行)。
    完整不完整沒辦法事後從備份自己身上看出來,只能在**做備份的當下**記下來。
    所以現在每一份 .autobak 旁邊都有一張 .autobak.receipt,
    裡面是那一刻的大小與 sha256;還原之前先驗它,對不上就不還原。

    現在檢查四件事,順序就是下面的順序:
      0. **收據**:必須存在,而且大小與 sha256 都對得上。
         沒有收據的舊備份(2026-09-05 以前做的)一律不自動還原。
      1. 備份不是 0 bytes
      2. BIGF:檔頭第 4-8 個位元組宣告的總長度要等於實際長度
         (兩種位元組序都接受;哪些檔是大端、各有幾個,以 reference/bigf.html 量到的為準,這裡不寫會過期的數字)
      3. LOCH(語系檔):檔頭指到的 LOCL 要在檔內,而且最後一條字串的位移
         也要在檔內 —— 截斷之後那個位移一定會超出去
      4. MZ(執行檔):PE 節區表裡 raw offset + raw size 的最大值不得超過檔案長度

    ⚠️ 原本還有第 5 道(分隔表格斷在半筆)與第 6 道(備份不得小於正本一半),
       2026-09-05 這一輪**拿掉了**。它們存在的理由都是「猜完整性」,
       收據既然證得出來,它們就只剩下誤傷的份 —— 第 6 道對這一支尤其危險:
       這一支會**整個覆蓋**散裝檔,模組檔比原檔大一倍以上很常見,
       那時候「備份不到正本一半」會成立,一份完全正確的備份被擋在門外,
       使用者當場還原不了。
    """
    # 這一段在本站多支腳本裡是同一份複本,所以函式內自己再 import 一次 struct,
    # 整段搬到別的腳本就能用,不必連帶檢查那邊有沒有在檔案開頭 import。
    import struct
    bak, dst = os.fspath(bak), os.fspath(dst)
    if not os.path.exists(bak):
        raise SystemExit('找不到備份:%s' % bak)
    n = os.path.getsize(bak)
    # 第 0 道:收據。這是唯一**證得出來**的一道,其餘全是結構上的自我一致性。
    why = _check_receipt(bak)
    if why:
        raise SystemExit(
            '不敢拿這份備份覆蓋 %s。\n'
            '  %s\n'
            '  2026-09-05 以前做的備份沒有收據,本工具不會自動還原它們 ——\n'
            '  半截的純文字備份跟一份合法的短檔長得一模一樣,擋不掉。\n'
            '  你如果確定那份備份是完整的,請自己手動複製回去。' % (dst, why))
    # 目的地是符號連結也不還原:那會寫到遊戲資料夾外面去。
    if os.path.islink(dst):
        raise SystemExit('%s 是符號連結,不敢往它寫(會寫到別的地方去)。' % dst)
    # 第 1 道:0 bytes。這是備份中斷最明顯的樣子。
    # (收據那一道其實已經擋住它了 —— 0 bytes 的備份不可能有對得上的收據。
    #  留著是因為它便宜,而且訊息比較好懂。)
    if n == 0:
        raise SystemExit(
            '備份是 0 bytes(多半是上次備份到一半被中斷),不敢拿它覆蓋 %s。' % dst)
    # 只讀開頭 8 個位元組來認格式,不整個讀進來(備份可能有好幾 MB)。
    with open(bak, 'rb') as _f:
        head = _f.read(8)

    # 每一道檢查失敗都走這個出口:講清楚是哪裡對不上、多半是什麼原因造成的,
    # 而且**不覆蓋任何東西**就結束。寧可還原失敗,也不要拿壞備份蓋掉正本。
    def _stop(why):
        raise SystemExit(
            '這份備份是壞的,不敢拿它覆蓋 %s。\n'
            '  %s\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  請改用你自己另外留的那一份備份。' % (dst, why))

    # 第 2 道:BIGF 封裝檔。檔頭第 4-8 個位元組是「這個檔應該多大」,
    # 兩種位元組順序都遇得到:本站測試機上「剛安裝好的全新 MVP2005 英文版」那份
    # 安裝目錄裡的 207 個 BIGF 檔全部是小端,大端只出現在被模組重新打包過的檔。
    # 跟檔案大不大無關:同一台機器上找到的 1,883 個 BIGF 檔裡有 39 個是大端,
    # 其中最小的只有 191,146 bytes,而最大的小端檔(原版 models.big)是
    # 172,992,803 bytes。所以兩種都算一次,只要有一種等於實際大小就算過。
    # 被截斷的備份兩種都對不上。
    if len(head) == 8 and head[:4] == b'BIGF':
        le = struct.unpack('<I', head[4:8])[0]
        be = struct.unpack('>I', head[4:8])[0]
        if le != n and be != n:
            _stop('檔頭說它應該是 %d bytes(或 %d),實際只有 %d bytes。' % (le, be, n))
        return _do_copy(bak, dst)

    # 第 3 道:LOCH(遊戲的文字表 .LOC)。這種檔沒有「總長度」欄位可以對,
    # 所以改成沿著它自己的指標走一遍:檔頭第 16-20 個位元組(小端)指到字串區,
    # 字串區有一張位移表,拿**最後一條**字串的位移去比檔案長度。
    # 檔案被截掉一半的話,那個位移一定會指到檔案外面。
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

    # 第 4 道:MZ(Windows 執行檔)。同樣沿著它自己的結構走:
    # 位移 0x3C 那 4 個位元組(小端)指到 PE 檔頭,PE 檔頭 +6 是節區數、
    # +20 是選用檔頭長度,節區表就接在後面,每一項 40 個位元組,
    # 其中 +16 是節區在檔案裡的長度、+20 是它的位置(都是小端)。
    # 把所有節區的「位置 + 長度」取最大值,那就是這個執行檔至少該有多大。
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

    # 走到這裡代表:收據對得上(所以備份是完整的),而且格式上也自我一致。
    return _do_copy(bak, dst)


# 真正動手覆蓋正本的只有這一個函式,而且只有通過上面那些檢查的路徑才會走到。
# 「檢查」跟「覆蓋」分成兩個函式,是為了讓人一眼看得出覆蓋只有一個入口。
def _do_copy(bak, dst):
    """把備份蓋回正本 —— 而且是原子的。

    ⚠️ 2026-09-05 稽核抓到的:舊版是一行 shutil.copy2(bak, dst)。
       copy2 做的第一件事是把 dst **截成 0 bytes**,然後才一段一段寫回去。
       複製途中 Ctrl-C / 磁碟滿 / 外接碟被拔掉,遊戲正本就停在 0 或半截 ——
       而這是「還原」指令,使用者按下去的時候通常已經在救火了,
       這時候把他僅剩的那一份正本也弄壞,是本工具能造成的最嚴重的傷害。
       現在改成:寫同資料夾的唯一暫存檔 → fsync → 讀回來比 sha256 →
       都對了才 os.replace。中途失敗的話正本一個位元組都沒被動到。
    """
    _copy_verified(bak, dst, record=True)




# Windows 主控台預設編碼(繁體中文是 cp950)存不下 ✅ ⚠ ❓ 這些符號,
# 輸出被重導向到檔案時會直接 UnicodeEncodeError 中斷,整份清點結果就沒了。
# 先把兩個輸出串流轉成 UTF-8。舊版 Python 沒有 reconfigure,所以包在 try 裡。
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


class DataError(Exception):
    """檔案內容跟預期不符。一律當成「停下來問人」,不要猜。"""


# 三個上限,全部是防呆用的。壞掉或被動過手腳的檔案會宣稱天文數字,
# 沒有上限的話下面那些迴圈會空轉很久,或者把記憶體吃光。
MAX_UNCOMPRESSED = 64 * 1024 * 1024       # 一個項目解開後最多這麼大
MAX_BIG_ENTRIES = 200000                  # 一個封裝檔最多這麼多項
# 備份用專屬字尾,不用通用的 .bak:一個遊戲資料夾裡可能同時躺著
# 好幾課留下來的備份,本工具只認自己這一個,也只還原自己這一個。
BACKUP_SUFFIX = '.autobak'
# 收據跟著備份走,所以它的字尾就是備份字尾再接 .receipt。
# 這兩種檔案都不可以進索引(它們是本工具的產物,不是遊戲內容)。
RECEIPT_SUFFIX = BACKUP_SUFFIX + RECEIPT_TAIL


# ─────────────────────────────────────────────────────────
#  QFS(EA 的壓縮格式,檔頭是 10 FB)
# ─────────────────────────────────────────────────────────
def qfs_decompress(data):
    """把 QFS / RefPack 壓縮過的位元組解開。不是壓縮檔就原樣還你。

    認法是第 2 個位元組固定為 0xFB(第 1 個是旗標,常見的是 0x10)。
    緊接著是「解開來有多大」,大端,長度看旗標的最低位元:
      旗標 bit0 = 1 → 4 個位元組,放在位移 6-10,資料從位移 10 開始
      旗標 bit0 = 0 → 3 個位元組,放在位移 2-5,資料從位移 5 開始
    之後是一串指令,每一種都做兩件事:先原樣抄幾個位元組(literal),
    再從**已經解出來的結果**往回抄一段(反向參照)。

    這支腳本只在一個地方用到它:判斷「封裝檔裡只裝一個壓縮過的封裝檔」
    的時候,把那一層拆開來看裡面有什麼。安裝時不會用到解壓。
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
    # 第一道防呆:檔頭自己宣稱的大小就不合理的話,連解都不要解。
    if not 0 <= size <= MAX_UNCOMPRESSED:
        raise DataError('QFS 宣稱解壓尺寸異常:%d' % size)

    out = bytearray()
    end = len(data)

    def copy_back(offset, length):
        # 從結果尾端往回數 offset 個位元組開始抄 length 個。
        # 來源可以跟目的重疊(offset 比 length 小的時候),那是刻意的:
        # 「往回 1 個位元組抄 20 次」就是把同一個位元組重複 20 遍,
        # 所以只能一個一個抄,不可以改成一次切一段。
        #
        # 上限檢查放在這個函式裡,不放在 literal 那幾條路上:
        # literal 抄多少受輸入檔長度限制,再怎麼樣也吐不出比輸入大很多的東西;
        # 會無中生有把記憶體吃光的只有反向參照。
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

    # 指令迴圈。第一個位元組(b0)決定是哪一種指令,
    # 四段的分界是 0xFC / 0xE0 / 0xC0 / 0x80,由大到小判斷。
    while pos < end:
        b0 = data[pos]
        if b0 >= 0xFC:                    # 結束指令 + 最後 0~3 個 literal
            n = b0 & 0x03; pos += 1
            out += data[pos:pos + n]; break
        # 上限是 112 不是 128:0xFC 以上在上一支已經先被攔掉,能走到這裡的 b0
        # 最大只到 0xFB,(0xFB & 0x1F) = 27,(27 << 2) + 4 = 112。
        if b0 >= 0xE0:                    # 純 literal,一次 4~112 個(必為 4 的倍數)
            n = ((b0 & 0x1F) << 2) + 4; pos += 1
            out += data[pos:pos + n]; pos += n; continue
        # 下面三種都是「抄 n 個 literal,再往回抄 length 個」。
        # 差別只在能表達多長、多遠。位元被拆散在好幾個位元組裡,
        # 是為了讓最常用的短距離參照只花 2 個位元組。
        if b0 >= 0xC0:                    # 4 個位元組:長度 5~1028 · 回頭 1~131072
            b1, b2, b3 = data[pos + 1], data[pos + 2], data[pos + 3]; pos += 4
            n = b0 & 0x03
            length = ((b0 & 0x0C) << 6) + b3 + 5
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 >= 0x80:                  # 3 個位元組:長度 4~67 · 回頭 1~16384
            b1, b2 = data[pos + 1], data[pos + 2]; pos += 3
            n = (b1 >> 6) & 0x03          # 這一種的 literal 個數放在 b1 的高兩位
            length = (b0 & 0x3F) + 4
            offset = ((b1 & 0x3F) << 8) + b2 + 1
        else:                             # 2 個位元組:長度 3~10 · 回頭 1~1024
            b1 = data[pos + 1]; pos += 2
            n = b0 & 0x03
            length = ((b0 & 0x1C) >> 2) + 3
            offset = ((b0 & 0x60) << 3) + b1 + 1
        # 順序不能對調:先把 literal 抄進去,那幾個位元組本身
        # 有可能就是下一句反向參照要回頭抄的來源。
        out += data[pos:pos + n]; pos += n
        copy_back(offset, length)
    # 截到檔頭宣稱的長度為止。結束指令之後就算還有位元組也不算數。
    return bytes(out[:size])


def qfs_compress_literal(data):
    """純 literal 編碼:不做字串比對,瞬間完成,格式一樣合法。

    壓出來比 EA 原本的大(大約等於原始大小),但因為我們是接到檔尾,
    大一點沒有影響。換來的是速度快上千倍,而且不可能壓錯。

    檔頭是 0x10 0xFB 加 3 個位元組的原始長度(大端),
    所以這個寫法最多只能包 16,777,215 個位元組。

    ⚠️ **目前這支腳本沒有呼叫點。** 安裝是把模組檔原封不動接到檔尾,
       不重新壓縮;這個函式是本站處理 QFS 的同一份實作,留著備用。
    """
    n = len(data)
    out = bytearray([0x10, 0xFB, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])
    tail = n % 4                          # 0~3,交給結束指令帶走
    body = n - tail
    pos = 0
    # literal 指令一次只能帶 4 的倍數個位元組,所以先把不足 4 的尾巴切出去。
    while pos < body:
        chunk = min(112, body - pos)      # 必為 4 的倍數,上限 112
        # 指令位元組 = 0xE0 加上「這一塊有幾個 4 位元組」減 1。
        # chunk 最大 112 時算出 0xFB,剛好停在 0xFC 之前。
        # 再大一格就會被解壓端當成結束標記,檔案當場截斷。
        out.append(0xE0 | ((chunk - 4) // 4))
        out += data[pos:pos + chunk]
        pos += chunk
    out.append(0xFC | tail)               # 結束指令,順便把尾巴幾個帶走
    out += data[pos:]
    return bytes(out)


# ─────────────────────────────────────────────────────────
#  BIGF 封裝檔:讀目錄、接到檔尾
# ─────────────────────────────────────────────────────────
def size_field_order(path):
    """檔頭 +0x04 的「檔案總大小」是 little 還是 big endian。

    ⚠️ 這一欄兩種順序都遇得到,不能寫死,也不能照檔名或檔案大小猜。
       「哪個檔是哪一種」不是這個格式天生的性質,是看你手上這一份被誰重新打包過。
       本站以 BIGF 檔頭(不是副檔名)認過三份剛安裝好的原版 data 資料夾:
       英文版 207 個封裝檔、繁體中文版 205 個、PK 版 205 個,這三份**全部**是
       little-endian,連裡面最大的 models.big(172,992,803 個位元組)與
       frontend/portrait.big(109,291,217 個位元組)也是。
       只有本站測試機那份疊過模組的 data 資料夾(384 個封裝檔)量得到 big-endian,
       共 10 個檔、7 個檔名:models.big、frontend/portrait.big、
       audio/spch_pbp/pnamehdr.big、audio/cd/spch_pbp/pnamedat.big,
       以及球場夜間檔 coornite.big / dodgnite.big / wrignite.big
       (這三個在球場資料夾與它的一份原版備份各有一份,所以檔數比檔名多)。
       這 7 個檔名在三份原版裡全都是 little-endian,
       所以 big-endian 是被別的工具重新打包之後才有的。
       讀出來是哪一種,寫回去就照哪一種。
    """
    # 判法:兩種順序都解一次,哪一種等於**實際檔案大小**就是哪一種。
    # 這是拿檔案自己的長度當標準答案,不必猜也不必查表。
    n = os.path.getsize(path)
    with open(path, 'rb') as f:
        raw = f.read(8)
    if len(raw) < 8:
        raise DataError('%s 太小,不像封裝檔' % os.path.basename(path))
    if struct.unpack('<I', raw[4:8])[0] == n:
        return '<'
    if struct.unpack('>I', raw[4:8])[0] == n:
        return '>'
    # 兩種都對不上 = 這個檔已經被改壞或被截斷。這時候寧可停下來,
    # 因為接下來要做的是「往這個檔裡面寫東西」。
    raise DataError('%s 的檔頭大小欄位跟實際檔案大小對不上 —— 這個檔可能已經損毀'
                    % os.path.basename(path))


def big_entries(path):
    """回傳 [(名稱, 目錄欄位位置, 資料 offset, 資料長度)]。

    目錄欄位位置留著,是為了之後只改那 8 個位元組,不必重寫整個目錄。

    BIGF 的結構:開頭 16 個位元組是檔頭(位移 4-8 是檔案總大小、
    位移 8-12 是項目數,**大端**),目錄從位移 16 開始,
    每一項是資料位移 4 個位元組 + 資料長度 4 個位元組(都是大端),
    接一個以 \0 結尾的名字,長度不固定,
    所以只能從頭一項一項走,沒辦法直接跳到第 N 項。

    ⚠️ **目前這支腳本沒有呼叫點。** 建索引走的是 _entries_of(),
       它吃的是已經讀進記憶體的位元組,不是路徑。
    """
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] != b'BIGF':
                raise DataError('%s 的開頭不是 BIGF,這不是封裝檔' % os.path.basename(path))
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                raise DataError('%s 的目錄項目數異常(%d)' % (os.path.basename(path), count))
            # 目錄有多長取決於名字有多長,事先算不出來。
            # 用「每項抓 80 個位元組再多留 8 KB」當上限一次讀進來,
            # 讀不夠也沒關係:下面的迴圈走到讀完就停,已經拿到的照樣可用。
            blob = head + f.read(count * 80 + 8192)
    except OSError as e:
        raise DataError('讀不到 %s:%s' % (path, e))

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
    """把封裝檔裡某一項的原始位元組讀出來。

    長度對不上就當成壞檔丟例外。Python 切片越界不會出錯,
    只會**默默給你短的資料**,那樣壞檔會被當成好檔一路走下去。

    ⚠️ **目前這支腳本沒有呼叫點。**
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

    代價是檔案會越改越大:被換掉的舊資料還躺在中間,只是沒有人指向它了。
    想收回去只能 --restore 回到最初那一份再重來。
    """
    # 一定要在改檔案之前先量位元組順序:寫完之後檔案大小就變了,
    # 那時候再量,兩種順序都會對不上實際大小,反而判成壞檔。
    order = size_field_order(path)          # 一定要在改檔案之前先量
    # 新資料的位移就是「接上去之前的檔案長度」。
    new_off = os.path.getsize(path)
    # 'r+b' 是就地改,不是重寫;開檔這一步本身不會動到任何既有位元組。
    with open(path, 'r+b') as f:
        f.seek(0, os.SEEK_END)
        f.write(blob)                                       # 一、接到檔尾
        total = f.tell()
        f.seek(field_pos)
        # 二、目錄那一項的 8 個位元組改指向新位置。
        #     目錄裡的數字**一律大端**,跟檔頭那一欄不一樣,不要混。
        f.write(struct.pack('>II', new_off, len(blob)))     # 目錄一律 big-endian
        f.seek(4)
        # 三、檔頭的檔案總大小欄,沿用這個檔原本的位元組順序。
        f.write(struct.pack(order + 'I', total))
        # fsync 之後才回來:確保資料真的落到磁碟,不是還留在作業系統的快取裡。
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
#
# ⚠️ 這一整段(格式表 + 下面兩個函式)**目前這支腳本沒有呼叫點**。
#    安裝時是整個檔換掉或整個檔接到檔尾,不會拆到圖片的像素那一層。
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

    SHPI 的結構:開頭 16 個位元組是檔頭,位移 8-12 是這個容器裡有幾張圖
    (小端);接著是目錄,每一項 8 個位元組(4 個位元組的標籤 + 4 個位元組的位移),
    所以第一張圖的位移就在 16 + 0*8 + 4 = 20 那裡。
    圖片自己的記錄檔頭也是 16 個位元組:第 0 個位元組是格式代號,
    第 1-4 個是這一塊有多長(小端 24 位元),第 4-6 與 6-8 是寬與高(小端 16 位元),
    像素從記錄檔頭之後,也就是 +16 開始。

    ⚠️ **目前這支腳本沒有呼叫點。**
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
    start = off + 16
    # 像素到哪裡結束,三種問法由可靠到勉強:
    #   一、記錄自己說了這一塊有多長(block_size > 16):直接用它
    #   二、沒說,但後面還有下一張圖:用下一張的起點當這一張的終點
    #   三、都沒有:只好當成一路到檔案結尾
    if block_size > 16:
        end = min(off + block_size, len(data))
    elif num > 1:
        end = min(struct.unpack_from('<I', data, 16 + 8 + 4)[0], len(data))
    else:
        end = len(data)
    return code, width, height, start, end


def fsh_replace_pixels(data, start, end, new_pixels):
    """換掉像素區,長度必須**一個位元組都不差**。

    長度一樣不代表格式一樣,但長度不一樣就一定不對(尺寸變了、
    或者每像素的位元組數變了)。所以這是最低標,不是保證。

    ⚠️ **目前這支腳本沒有呼叫點。**
    """
    if len(new_pixels) != end - start:
        raise DataError('新像素有 %d 個位元組,原本是 %d —— 尺寸或格式不一致,拒絕寫入'
                        % (len(new_pixels), end - start))
    return data[:start] + new_pixels + data[end:]

# ─────────────────────────────────────────────────────────
#  認檔案:只看前幾個位元組,不看副檔名
#
#  副檔名會騙人 —— 這個遊戲裡有 17 個叫 .big 的檔根本不是封裝檔
#  (8 個是 SCHl 音訊、1 個是 SHPI 圖集、8 個是索引表)。
#  所以一律看內容。
# ─────────────────────────────────────────────────────────
MAGIC = [
    (b'BIGF', 'BIGF 封裝檔'),
    (b'BIG4', 'BIG4 封裝檔'),
    (b'SHPI', 'FSH 圖集'),
    (b'SCHl', 'EA 音訊'),
    (b'GSTR', 'EA 音訊(串流)'),
    (b'FntF', '字型'),
    (b'FNTF', '字型'),
    (b'LOCH', '文字表 .LOC'),
    (b'MVhd', 'EA 影片'),
    (b'\x10\xfb', 'QFS 壓縮'),
    (b'\x89PNG', 'PNG 圖'),
    (b'BM',   'BMP 圖'),
    (b'PK\x03\x04', 'ZIP 壓縮檔'),
]


def sniff(blob):
    """只看開頭幾個位元組,回一句人看得懂的「它看起來是什麼」。

    這個結果**只拿來顯示**,不參與「該放哪」的判斷,
    去處是靠索引裡的名字算的,跟格式無關。
    所以認錯了頂多是印錯一行字,不會裝錯地方。
    """
    for sig, name in MAGIC:
        if blob.startswith(sig):
            return name
    # 沒有魔術數字的話,再試試看它是不是純文字:
    # 開頭是英數 + 前 400 個位元組能用 UTF-8 解開,就當成文字。
    # 裡面有 tab 或逗號就多講一句「表格」(名冊、索引這類檔長這樣)。
    if blob[:1].isdigit() or blob[:1].isalpha():
        try:
            txt = blob[:400].decode('utf-8')
            if '\t' in txt or ',' in txt:
                return '純文字表格'
            return '純文字'
        except UnicodeDecodeError:
            pass
    # 認不出來就說認不出來。這裡不猜,猜了也沒有好處。
    return '認不出來'


# ─────────────────────────────────────────────────────────
#  索引:這份遊戲裡,每一個名字住在哪
#
#  兩半都要:
#    (一) 封裝檔裡的項目 —— 含巢狀(有些封裝檔裡只裝一個壓縮過的封裝檔)
#    (二) 磁碟上的散裝檔 —— attrib.dat / batdit.ast 這種不在封裝檔裡的
# ─────────────────────────────────────────────────────────
# ⚠️ 名字叫 SKIP,但它**不是跳過**:路徑裡命中這些字樣的檔案照樣進索引,
#    只是被標成 alt(替代)。挑去處時主線優先,主線一個都沒有的時候
#    才會用到它們。這樣一來「你自己留的備份資料夾」不會被當成安裝去處,
#    但也不會因為看不見而讓你以為遊戲裡沒有那個檔。
SKIP_DIR_HINTS = ('- backup', '- 備份', '_snapshots', '.git')


def _entries_of(blob):
    """從**已經讀進記憶體**的位元組裡走一遍封裝檔目錄。

    回 None 代表「這不是封裝檔」,呼叫端就把它當成一個散裝檔記進索引。
    注意這裡回 None 而不是丟例外:走過整個遊戲資料夾時,
    絕大多數檔案本來就不是封裝檔,那是常態不是錯誤。

    目錄格式跟 big_entries() 那邊一樣:位移 8-12 是項目數(大端),
    目錄從 16 開始,每項 4 + 4 個位元組(都是大端)加一個 \0 結尾的名字。
    回傳的第 2 欄 off - 8 就是那 8 個位元組在檔案裡的位置,寫回去要用。
    """
    if blob[:4] not in (b'BIGF', b'BIG4'):
        return None
    n = int.from_bytes(blob[8:12], 'big')
    if not 0 < n < MAX_BIG_ENTRIES:
        return None          # 項目數不合理 = 不當它是封裝檔,不是丟錯誤
    off, out = 16, []
    for _ in range(n):
        if off + 8 > len(blob):
            break
        o = int.from_bytes(blob[off:off + 4], 'big')
        s = int.from_bytes(blob[off + 4:off + 8], 'big')
        off += 8
        e = blob.find(b'\0', off)
        if e < 0:
            break
        out.append((blob[off:e].decode('latin-1', 'replace'), off - 8, o, s))
        off = e + 1
    return out


def build_index(gamedir, verbose=False):
    """回傳 (索引, 統計)。索引:名稱 → [去處]。

    去處是一個 dict:
      kind   'archive'(封裝檔裡)/ 'nested'(封裝檔裡的封裝檔裡)/ 'loose'(磁碟上)
      path   封裝檔或散裝檔的相對路徑
      field  目錄欄位位置(archive 才有,寫回去要用)
      size   原本多大
      alt    True 代表這個去處在備份/替代資料夾裡,不是主線
    """
    idx = {}
    stat = {'archives': 0, 'entries': 0, 'nested': 0, 'loose': 0,
            'unreadable': 0, 'unreadable_paths': []}
    root = os.path.abspath(gamedir)

    # 一個名字可以對到好幾個去處,所以索引的值是一個清單,不是單一筆。
    # 有幾筆就代表有幾個地方叫這個名字,歧義就是這樣算出來的。
    def add(name, rec):
        idx.setdefault(name, []).append(rec)

    # 走過整個遊戲資料夾。每個檔都整個讀進記憶體,
    # 這就是第一次跑很慢的原因,但也是它「認內容不認副檔名」的代價。
    for r, dirs, fs in os.walk(root):
        for f in fs:
            # ⚠️ 本工具自己做的備份**不可以**進索引。
            #    .autobak 是遊戲檔的複本,開頭當然也是 BIGF,不排除的話:
            #    第一次安裝成功之後,同一個名字就有兩個去處(正本 + 剛做的備份),
            #    route() 判成 ambig,從此每一趟都被自己的備份擋下來;
            #    而且 ⚠ 清單會把備份檔列成候選去處 —— 挑到它就是往備份裡寫。
            #    2026-09-05 實測:第二趟起一律「沒有任何檔案能確定去處」,
            #    而 --restore 不刪備份,所以這個狀態不會自己解除。
            #    (SKIP_DIR_HINTS 攔不到它:那是看資料夾名字,備份就躺在正本旁邊。)
            #    收據(.autobak.receipt)與本工具的暫存檔(.mvpai-tmp-…)同理;
            #    .autobak.part 是舊版備份寫到一半的暫時檔,留著一起排除。
            if (f.endswith(BACKUP_SUFFIX) or f.endswith(RECEIPT_SUFFIX)
                    or f.startswith(TMP_PREFIX)
                    or f.endswith(BACKUP_SUFFIX + '.part')):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, root).replace(os.sep, '/')
            # 路徑裡有備份/快照字樣的標成 alt,排在主線後面(不是跳過)。
            alt = any(h in rel.lower() for h in SKIP_DIR_HINTS)
            try:
                blob = open(p, 'rb').read()
            except OSError as e:
                # ⚠️ 2026-09-05 稽核抓到的:以前這裡只把 unreadable 加一,
                #    而那個數字沒有任何一條路會去看它,等於**靜默漏檔**。
                #    漏一個檔就是索引裡少一個去處,而少掉的那個很可能正是
                #    「同一個名字的第二個地方」—— 本來該判成 ambig 停下來問人的檔,
                #    會因此被判成 exact 直接裝下去,而畫面上是一行 ✅。
                #    現在把路徑記起來,由 _unreadable_stop() 中止整批。
                stat['unreadable'] += 1
                stat['unreadable_paths'].append(
                    '%s(%s)' % (rel, e.strerror or e))
                continue
            ents = _entries_of(blob)
            # 不是封裝檔 → 它自己就是一個去處(散裝檔),記完換下一個。
            if ents is None:
                add(os.path.basename(rel), {'kind': 'loose', 'path': rel,
                                            'field': None, 'size': len(blob), 'alt': alt})
                stat['loose'] += 1
                continue
            stat['archives'] += 1
            # ⚠️ 封裝檔自己的名字也要進索引。
            #    只索引「裡面的項目」的話,一包模組如果附的是整個 .big 替換檔
            #    (社群模組最常見的形式),就會被誤報成「遊戲裡沒有同名的」。
            #    這個 bug 是 2026-08-29 用一包測試模組抓到的。
            add(os.path.basename(rel), {'kind': 'loose', 'path': rel,
                                        'field': None, 'size': len(blob), 'alt': alt})
            # 再把封裝檔裡的每一項記進去。field 是那 8 個位元組的位置,
            # 之後真的要安裝時就是靠它,不必重新開檔走一次目錄。
            for nm, field, o, s in ents:
                add(nm, {'kind': 'archive', 'path': rel, 'field': field, 'size': s, 'alt': alt})
                stat['entries'] += 1
                # 只裝一項而且那一項是 QFS 壓縮的封裝檔 → 再拆一層
                # (條件下得這麼窄,是因為這是遊戲裡實際存在的那一種包法;
                #  拆不開就當作沒這回事,不讓一個壞檔害整個索引建不完。)
                if len(ents) == 1 and blob[o:o + 2] == b'\x10\xfb':
                    try:
                        inner = qfs_decompress(blob[o:o + s])
                        ie = _entries_of(inner)
                    except Exception:
                        ie = None
                    if ie:
                        stat['nested'] += 1
                        # 這一層只進索引、不當安裝去處(kind='nested',
                        # 而且 field 是 None)。寫回去要重壓一整層,本工具不做。
                        for inm, ifield, io, isz in ie:
                            add(inm, {'kind': 'nested', 'path': rel + ' → ' + nm,
                                      'field': None, 'size': isz, 'alt': alt})
    return idx, stat


# ─────────────────────────────────────────────────────────
#  路由:一個外來檔案該去哪
# ─────────────────────────────────────────────────────────
def route(idx, relname, basename):
    """回傳 (狀態, 去處清單)。

    狀態:
      'exact'   只有一個去處 → 可以直接裝
      'ambig'   多個去處 → **停下來問人**,不猜
      'unknown' 索引裡沒有 → 只報它是什麼,不動
    找的順序:先用模組附的相對路徑找(那比較精確),再退回只用檔名。
    """
    # 先拿模組裡的相對路徑去找(帶著資料夾結構,比較精確),
    # 找不到才退回只用檔名。兩個都找不到就是 unknown。
    for key in (relname, basename):
        hits = idx.get(key)
        if not hits:
            continue
        # 主線優先:只要主線有,備份/快照資料夾裡那些就不列入考慮,
        # 不然「你自己留了一份備份」就會讓每個檔都變成有歧義。
        main = [h for h in hits if not h['alt']]
        pool = main or hits
        # 同一個封裝檔重複列到的視為同一個去處。
        # ⚠️ 鍵裡一定要帶 field:同一個封裝檔裡**可以有兩個同名項目**。
        #    (本站測試機上走過 380 個封裝檔,16 個是這樣;
        #     frontend/coopteam.big 的 act02.fsh 就有兩筆,目錄位置 16 與 157。)
        #    只用(種類, 路徑)當鍵會把它們壓成一個、判成「只有一個去處」直接裝,
        #    而實際上只有先遇到的那一筆被改,另一筆還指著舊資料 ——
        #    那正是本檔開頭宣稱「不猜」不會發生的事,而且一聲都不吭。
        #    帶了 field 就會判成 ambig 停下來,交給人決定。
        #    loose 與 nested 的 field 都是 None,行為跟以前一樣。
        uniq, seen = [], set()
        for h in pool:
            k = (h['kind'], h['path'], h['field'])
            if k not in seen:
                seen.add(k)
                uniq.append(h)
        # 去重之後只剩一個 → 可以裝;剩兩個以上 → 停下來讓人決定。
        # 這裡**不做**任何加權或猜測,因為猜錯的代價是蓋掉別的東西。
        return ('exact' if len(uniq) == 1 else 'ambig'), uniq
    return 'unknown', []


def collect(moddir):
    """把模組資料夾裡的檔案全部列出來,回 [(完整路徑, 相對路徑, 檔名)]。

    點開頭的檔案與資料夾一律跳過(.DS_Store、.git 這些),
    它們是作業系統或版本控制留下的,不是模組內容。
    最後照相對路徑排序,讓同一包模組每次跑出來的順序都一樣。
    順序穩定,兩次執行的輸出才比得出差別。
    """
    out = []
    root = os.path.abspath(moddir)
    for r, dirs, fs in os.walk(root):
        # 就地改 dirs 才會真的讓 os.walk 不進去那些資料夾(這是 os.walk 的規矩)。
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in fs:
            if f.startswith('.'):
                continue
            p = os.path.join(r, f)
            # 相對路徑一律轉成斜線,Windows 跟 Mac 才對得起來。
            out.append((p, os.path.relpath(p, root).replace(os.sep, '/'), f))
    return sorted(out, key=lambda x: x[1])


def plan(gamedir, moddir):
    """把「建索引」跟「逐檔判去處」串起來,回一份純資料的清單。

    這個函式**不印任何東西、也不動任何檔案**。
    --scan、預覽、真的安裝三條路都先走它,拿到同一份結果,
    所以你看到的預覽跟真的會做的事一定是同一件。
    """
    idx, stat = build_index(gamedir)
    stat['mod_unreadable'] = []
    rows = []
    for full, rel, base in collect(moddir):
        try:
            head = open(full, 'rb').read(512)   # 認格式只需要開頭,不整個讀
        except OSError as e:
            # ⚠️ 以前這裡直接 continue:那個檔就這樣從清單上消失,
            #    「這包模組:N 個檔」少了一個而沒有人會發現,其餘照樣裝下去。
            #    讀不到就是讀不到,整批停下來(見 _unreadable_stop)。
            stat['mod_unreadable'].append('%s(%s)' % (rel, e.strerror or e))
            continue
        state, dests = route(idx, rel, base)
        rows.append({'full': full, 'rel': rel, 'base': base,
                     'kind': sniff(head), 'state': state, 'dests': dests,
                     'size': os.path.getsize(full)})
    return idx, stat, rows


def _unreadable_stop(stat):
    """讀不到的檔一律中止整批。回 None(沒事)或 exit code。

    「略過讀不到的,其餘照裝」看起來體貼,實際上是本工具最危險的一種行為:
    畫面上每一行都是 ✅,而少掉的那一個沒有人會發現 ——
    索引少一個去處,本來該停下來問人的檔就會被判成「只有一個去處」直接裝。
    """
    bad = list(stat.get('unreadable_paths', []))
    mod = list(stat.get('mod_unreadable', []))
    if not bad and not mod:
        return None

    def _list(title, items):
        print('  ❌ %s(%d 個):' % (title, len(items)))
        for line in items[:10]:
            print('       %s' % line)
        if len(items) > 10:
            print('       …另外還有 %d 個' % (len(items) - 10))

    print()
    if bad:
        _list('遊戲資料夾裡有檔案讀不到,索引不完整', bad)
    if mod:
        _list('模組資料夾裡有檔案讀不到', mod)
    print('       索引少一個去處,本來該停下來問人的檔就會被判成'
          '「只有一個去處」直接裝下去,')
    print('       所以整批停在這裡,一個位元組都不寫。')
    print('       請先把上面那些檔的權限修好(或關掉正在用它們的程式)'
          '再跑一次。\n')
    return 1


def show(rows, stat, verbose=True):
    """把 plan() 的結果分成 ✅ / ⏭ / ⚠ / ❓ 四堆印出來,並原樣回傳。

    回傳值是給呼叫端用的:安裝那一條路只會去動 ✅ 那一堆,
    ⏭ ⚠ ❓ 印出來就是印出來,不會有第二段程式碼去碰它們。

    ⚠️ ⏭(巢狀那一堆)本來是混在 ✅ 裡的,那是錯的:它們**算得出去處
       但裝不進去**(寫回去要重壓一整層,本工具不做)。混在 ✅ 裡的話,
       --scan 的人會以為裝得成,要等到真的 --apply 才看得到「不寫這一層」,
       而「裝好 N 個」也會比 ✅ 的個數少,對不起來。所以在這裡就拆開。
    """
    exact = [r for r in rows if r['state'] == 'exact']
    ok = [r for r in exact if r['dests'][0]['kind'] != 'nested']
    nest = [r for r in exact if r['dests'][0]['kind'] == 'nested']
    amb = [r for r in rows if r['state'] == 'ambig']
    unk = [r for r in rows if r['state'] == 'unknown']
    print('\n  這份遊戲的索引:%s 個封裝檔 · %s 個項目 · %s 層巢狀 · %s 個散裝檔'
          % (format(stat['archives'], ','), format(stat['entries'], ','),
             stat['nested'], format(stat['loose'], ',')))
    print('  這包模組:%d 個檔\n' % len(rows))

    if ok:
        print('  ✅ 認得出去處(%d 個)' % len(ok))
        for r in ok:
            d = r['dests'][0]
            where = d['path'] if d['kind'] != 'loose' else d['path'] + '(散裝)'
            print('       %-30s %-14s → %s' % (r['base'][:30], r['kind'], where))
    if nest:
        print('\n  ⏭ 算得出去處,但本工具不寫這一層(%d 個)' % len(nest))
        for r in nest:
            print('       %-30s 在巢狀壓縮封裝檔裡 → %s'
                  % (r['base'][:30], r['dests'][0]['path']))
        print('       (要把整層重新壓回去,風險比較高,本工具不做。'
              '加了 --apply 也一樣不會裝。)')
    if amb:
        print('\n  ⚠ 有多個去處,本工具不猜(%d 個)' % len(amb))
        for r in amb:
            print('       %-30s %s 個去處:' % (r['base'][:30], len(r['dests'])))
            # 同一個封裝檔裡有兩個同名項目時,兩行印出來會長得一模一樣,
            # 讀的人沒辦法分辨。這種情況多印一個目錄位置。
            paths = [d['path'] for d in r['dests']]
            for d in r['dests']:
                if paths.count(d['path']) > 1 and d['field'] is not None:
                    print('            · %s(這個封裝檔裡目錄位置 %d 那一項)'
                          % (d['path'], d['field']))
                else:
                    print('            · %s' % d['path'])
    if unk:
        print('\n  ❓ 這份遊戲裡沒有同名的東西(%d 個)' % len(unk))
        for r in unk:
            print('       %-30s 看起來是:%s' % (r['base'][:30], r['kind']))
        print('       （新增的檔案本來就不會有同名的。'
              '這種要用對應那一課的專用腳本裝,本工具不猜。）')
    print()
    return ok, nest, amb, unk


def cmd_index(gamedir):
    """--index:只建索引,回報這份遊戲有多少檔名是唯一的。

    這一步是整套做法的前提檢查:唯一歸屬的比例夠高,
    「給一個檔就能算出該放哪」才成立。比例是每個人自己的遊戲算出來的,
    裝過什麼模組、留過幾份備份都會影響它,所以不要抄別人的數字。
    """
    idx, stat = build_index(gamedir)
    # 有歧義 = 主線裡有兩個以上**不同的**去處。
    # 去重的鍵要跟 route() 用的**完全一樣**(種類, 路徑, 目錄位置),
    # 不然這裡報「唯一歸屬」的名字,route() 卻會判成有歧義拒絕安裝 ——
    # 同一件事兩個地方算法不同,讀者看到的數字就是假的。
    # alt 那些不算:你自己留的備份資料夾不該讓每個檔都變成有歧義。
    dup = [k for k, v in idx.items()
           if len({(h['kind'], h['path'], h['field'])
                   for h in v if not h['alt']}) > 1]
    print('\n  封裝檔        %s' % format(stat['archives'], ','))
    print('  封裝檔內項目  %s' % format(stat['entries'], ','))
    print('  巢狀再拆一層  %s' % stat['nested'])
    print('  散裝檔        %s' % format(stat['loose'], ','))
    if stat['unreadable']:
        # 這個數字以前算了卻沒有人印,等於白算。索引不完整會讓「唯一歸屬」
        # 的比例算得比實際高,而那正是整套做法的前提。
        print('  讀不到的檔    %s  ← 索引不完整,--scan / --install 會停下來'
              % format(stat['unreadable'], ','))
    print('  ' + '-' * 46)
    print('  不重複名稱    %s' % format(len(idx), ','))
    print('  其中有歧義的  %s  (%.1f%%)'
          % (format(len(dup), ','), len(dup) / max(1, len(idx)) * 100))
    print('\n  也就是說:這份遊戲裡 %.1f%% 的檔名只有唯一一個歸屬,'
          % (100 - len(dup) / max(1, len(idx)) * 100))
    print('  給它一個檔就能算出該放哪。剩下那些會被列出來讓你決定。\n')
    return 0


def cmd_scan(gamedir, moddir):
    """--scan:清點一包模組。從頭到尾唯讀,連備份都不會產生。"""
    _, stat, rows = plan(gamedir, moddir)
    show(rows, stat)
    stop = _unreadable_stop(stat)
    if stop:
        # 唯讀的指令照樣要回非 0:清點結果不完整的時候說「清點完成」是假的。
        return stop
    print('  這一步完全沒有動到任何檔案。要裝的話用 --install。\n')
    return 0


# ⚠️ Windows 上這幾個名字是「裝置」不是檔案,拿去開檔會開到裝置本身。
#    這份遊戲的檔案裡一個都沒有(2026-09-05 走過整個 MVP2026/ 實測 0 命中),
#    列在這裡是因為接下來要做的事是覆蓋檔案 —— 幾乎不花時間,就驗一次。
WIN_RESERVED = ({'con', 'prn', 'aux', 'nul'}
                | {'com%d' % i for i in range(1, 10)}
                | {'lpt%d' % i for i in range(1, 10)})


def _safe_target(gamedir, relpath):
    """把索引裡的相對路徑接成真正要寫的檔案路徑。不安全就回 (None, 原因)。

    去處是本工具自己走過遊戲資料夾建出來的,照理不會有 .. 也不會是絕對路徑;
    這裡照樣驗一遍,因為下一步是**覆蓋檔案**,而「照理不會」不是「不會」。

    最要緊的是符號連結那一條。2026-09-05 實測:把 data/profiles.big 做成
    指向遊戲資料夾外面的連結,--apply 會沿著它把外面那個 4,428 bytes 的檔
    覆蓋成 5 bytes,而 .autobak 卻做在遊戲資料夾裡面 —— 「本工具只動遊戲
    資料夾裡的東西」當場不成立。目錄的符號連結沒事(os.walk 預設不跟),
    所以以前只有檔案層級會中招;現在整條路徑每一層都驗。
    """
    root = os.path.abspath(gamedir)
    parts = relpath.split('/')
    for seg in parts:
        if seg in ('', '.', '..') or ':' in seg or '\\' in seg:
            return None, '路徑裡有 %r 這一段,不安全' % seg
        if seg.split('.')[0].lower() in WIN_RESERVED:
            return None, '%s 在 Windows 上是裝置名,不是檔名' % seg
    probe = root
    for seg in parts:
        probe = os.path.join(probe, seg)
        if os.path.islink(probe):
            return None, ('%s 是符號連結,寫下去會寫到遊戲資料夾外面'
                          % os.path.relpath(probe, root).replace(os.sep, '/'))
    target = os.path.join(root, *parts)
    if not (target + os.sep).startswith(root + os.sep):
        return None, '算出來的位置跑到遊戲資料夾外面了'
    return target, None


def _open_target(gamedir, d):
    """安裝前的兩道:路徑安全、而且真的寫得進去。回 (路徑, None) 或 (None, 原因)。"""
    target, why = _safe_target(gamedir, d['path'])
    if target is None:
        return None, why
    # 寫不進去要在**備份之前**就發現。不然備份做好了、寫入才失敗,
    # 遊戲資料夾裡會留下一個沒用到的 .autobak。
    # (os.access 在 Windows 上看不出「檔案正被遊戲鎖住」——
    #  那是共用模式不是權限,由 main() 的 OSError 出口接住。)
    if not os.access(target, os.W_OK):
        return None, ('寫不進去(遊戲正開著把它鎖住?檔案被設成唯讀?'
                      '這個資料夾要系統管理員權限?)')
    return target, None


def _field_in_current_file(target, names):
    """封裝檔剛被整個換掉,拿**磁碟上現在這一份**重新找目錄位置。

    (安裝時傳進來的是「即將換上去的那份暫存複本」,內容跟磁碟上那一份
     逐位元組相同,所以算出來的目錄位置是同一個。)

    索引是整趟開頭建一次的。封裝檔一被整個換掉,索引裡屬於它的每一個
    目錄位置就全部失效 —— 拿舊位置去寫,改到的是新檔裡不相干的欄位。
    所以這種情況一律重讀一次現場,而不是相信索引。
    回 (目錄位置, None) 或 (None, 原因)。
    """
    try:
        blob = open(target, 'rb').read()
    except OSError as e:
        return None, '讀不回剛換上去的封裝檔:%s' % e
    ents = _entries_of(blob)
    if ents is None:
        return None, '剛換上去的那個檔不是封裝檔,沒辦法往它裡面寫'
    for name in names:
        hits = [e for e in ents if e[0] == name]
        if len(hits) == 1:
            return hits[0][1], None
        if len(hits) > 1:
            return None, ('剛換上去的封裝檔裡有 %d 個項目都叫 %s,本工具不猜'
                          % (len(hits), name))
    return None, '剛換上去的封裝檔裡沒有叫這個名字的項目'


def _verify_archive(path, pairs):
    """封裝檔寫完之後、換上去之前讀回來驗一遍。回 None(過)或不合的原因。

    驗三件事,三件都是「檔案自己說得出來」的:
      · 檔頭宣告的總長度等於實際長度(順序沿用這個檔原本那一種)
      · **整張目錄從頭走得完**:宣告幾項就要走得出幾項,每一項的
        位移 + 長度都要落在檔案裡面。走不完代表目錄被寫壞了
      · 每一個剛寫進去的項目,目錄指到的那一段位元組**逐位元組**等於
        我們要寫的內容 —— 「寫進去了」跟「寫對了」是兩件事
    這一步刻意放在 os.replace 之前:驗不過的時候遊戲正本還沒被碰過,
    使用者不需要還原,只要看訊息就好。
    """
    try:
        n = os.path.getsize(path)
        with open(path, 'rb') as f:
            head = f.read(16)
            if len(head) < 16 or head[:4] not in (b'BIGF', b'BIG4'):
                return '寫出來的檔開頭不是封裝檔標記'
            le = struct.unpack('<I', head[4:8])[0]
            be = struct.unpack('>I', head[4:8])[0]
            if le != n and be != n:
                return ('檔頭宣告的總長度(%d 或 %d)跟實際長度 %d 對不上'
                        % (le, be, n))
            # 整張目錄走一遍。目錄長度事先算不出來(名字長度不固定),
            # 用「每項 80 個位元組再多留 8 KB」當上限一次讀進來就夠 ——
            # 這是 big_entries() 同一套算法,不必把整個檔讀進記憶體。
            count = int.from_bytes(head[8:12], 'big')
            if not 0 < count < MAX_BIG_ENTRIES:
                return '檔頭說有 %d 個項目,這個數字不合理' % count
            toc = head + f.read(count * 80 + 8192)
            pos, seen = 16, 0
            for _ in range(count):
                if pos + 8 > len(toc):
                    return ('目錄只走得出 %d 項,檔頭卻說有 %d 項' % (seen, count))
                o = int.from_bytes(toc[pos:pos + 4], 'big')
                z = int.from_bytes(toc[pos + 4:pos + 8], 'big')
                if o + z > n:
                    return ('目錄第 %d 項指到 %d bytes,超出檔案結尾(%d bytes)'
                            % (seen + 1, o + z, n))
                pos += 8
                e = toc.find(b'\0', pos)
                if e < 0:
                    return '目錄第 %d 項的名字沒有結尾' % (seen + 1)
                pos = e + 1
                seen += 1
            for field, blob in pairs:
                f.seek(field)
                rec = f.read(8)
                if len(rec) != 8:
                    return '目錄位置 %d 讀不到' % field
                off, size = struct.unpack('>II', rec)
                if size != len(blob):
                    return ('目錄說這一項有 %d 個位元組,應該是 %d'
                            % (size, len(blob)))
                f.seek(off)
                if f.read(size) != blob:
                    return '讀回來的內容跟要寫進去的不一樣'
    except (OSError, struct.error) as err:
        return '讀不回剛寫好的暫存檔:%s' % err
    return None


def cmd_install(gamedir, moddir, apply_it):
    """--install:預覽或真的安裝。apply_it 為假時走到一半就收工。

    ⚠️ 迴圈只跑 ok(✅ 那一堆)。⏭ 與 ⚠ 與 ❓ 從來不會進到這個迴圈裡。
       這不是「還沒做完」,是刻意的:猜錯會蓋掉你沒要求改的東西,
       而且你不會知道。
    """
    _, stat, rows = plan(gamedir, moddir)
    ok, nest, amb, unk = show(rows, stat)
    # 讀不到的檔在**任何寫入之前**就中止整批(預覽也一樣,
    # 不然預覽跟真的會做的事就不是同一件了)。
    stop = _unreadable_stop(stat)
    if stop:
        return stop
    # 一個都認不出去處就直接收工,而且回傳 1。
    # 這種情況多半是那包模組全是新增檔案,要用對應那一課的專用腳本。
    if not ok:
        if nest:
            print('  能裝的一個都沒有 —— 上面那些都在巢狀壓縮封裝檔裡,'
                  '本工具不寫那一層。\n')
        else:
            print('  沒有任何檔案能確定去處,不做任何事。\n')
        return 1

    # ⚠️ 索引是整趟開始的時候建一次的,之後不再更新。
    #    如果這包模組同時附了「整個 X.big 的替換檔」與「本來住在 X.big 裡面的
    #    某一項」(社群模組很常見),替換檔一寫下去,索引裡 X.big 那些目錄位置
    #    就全部失效 —— 拿舊位置去寫,改到的是新檔裡不相干的欄位。
    #    2026-09-05 實測(修之前):profiles.big(整檔替換)+ profiles.csv 一起裝,
    #    結果 profiles.csv 根本沒進去,反而把新檔裡的 baserun.csv 改成指向
    #    profiles.csv 的內容 —— 而兩行都印 ✅、exit code 是 0。
    #    修法是分兩趟做,而且第二趟重讀現場:
    #      第一趟 先把要整個換掉的封裝檔換完
    #      第二趟 再寫封裝檔裡面的項目;去處是剛換掉的那些檔的話,
    #             目錄位置改成從磁碟上現在那一份重新找,不看索引。
    #    (不可以叫使用者「裝完再跑一次」—— 模組資料夾裡那個替換檔還在,
    #     下一趟一樣會先把封裝檔換掉,同一個撞車永遠解不開。這是本輪
    #     第一版修法犯的錯,實測跑兩趟兩次都印一樣的話。)
    replaced = {r['dests'][0]['path'] for r in ok
                if r['dests'][0]['kind'] == 'loose'}
    clash = [r for r in ok if r['dests'][0]['kind'] == 'archive'
             and r['dests'][0]['path'] in replaced]
    if clash:
        print('  ⓘ 這包模組同時附了整個封裝檔的替換檔,'
              '以及本來住在它裡面的項目(%d 個):' % len(clash))
        for r in clash:
            print('       %-30s 要進 %s(而這個檔本身也要被整個換掉)'
                  % (r['base'][:30], r['dests'][0]['path']))
        print('       所以會分兩趟做:先換掉封裝檔本身,'
              '再把上面那些寫進**換上去的那一份**裡面。')
        print('       (索引是開頭建一次的,對新檔已經失效,'
              '所以第二趟會重讀一次現場。)\n')

    # 唯讀是預設:沒有 --apply 就停在這裡,前面印的東西全部只是預覽。
    if not apply_it:
        print('  以上是預覽,一個位元組都沒有動。確定要裝就加 --apply\n')
        return 0

    # 以下才是真的會動檔的部分。
    done, skipped = 0, 0
    loose_rows = [r for r in ok if r['dests'][0]['kind'] == 'loose']
    arch_rows = [r for r in ok if r['dests'][0]['kind'] == 'archive']
    other_rows = [r for r in ok if r['dests'][0]['kind'] not in ('loose', 'archive')]

    # 第一趟:散裝檔,整個覆蓋。不做內容層級的合併,也不看格式對不對,
    #         去處是靠名字算的,格式那一欄只是印出來給人看。
    # ⚠️ 「整個覆蓋」以前是 open(target, 'wb') 直接寫 —— 開檔那一瞬間正本就被
    #    截成 0 bytes,之後才慢慢寫回去。中途 Ctrl-C / 磁碟滿 / 外接碟被拔掉,
    #    遊戲檔就停在半截。現在整包寫進同資料夾的暫存檔、讀回來比對過,
    #    才 os.replace 換上去(見 _atomic_write_bytes)。
    for r in loose_rows:
        d = r['dests'][0]
        target, why = _open_target(gamedir, d)
        if target is None:
            print('  ❌ %s 不裝:%s' % (r['base'], why))
            skipped += 1
            continue
        # 備份只做一次:第二次以後保留最早那一份,
        # 因為那一份才是「還沒被本工具動過的」。
        # 兩趟都印備份訊息 —— 以前只有封裝檔那一趟印,而「整個 .big 替換檔」
        # 是社群模組最常見的形態、走的正是這一趟,結果最常見的情況反而
        # 一行備份訊息都看不到,照著頁面判準檢查的人會判成失敗。
        why = _ensure_backup(target, target + BACKUP_SUFFIX)
        if why is not None:
            print('  ❌ %s 不裝:%s' % (r['base'], why))
            skipped += 1
            continue
        why = _atomic_write_bytes(target, open(r['full'], 'rb').read(),
                                  record=True)
        if why is not None:
            print('  ❌ %s 不裝:%s' % (r['base'], why))
            print('     (正本沒有動。要回到最初那一份就跑 --restore)')
            skipped += 1
            continue
        print('  ✅ %s → %s(散裝,整個換掉)' % (r['base'], d['path']))
        done += 1

    # 第二趟:封裝檔裡的項目,附加到檔尾,只改目錄。
    #         blob 是模組檔的原始內容,原封不動接上去,不重新壓縮。
    # ⚠️ 以前是直接在遊戲檔上做「接到檔尾 → 改目錄 8 bytes → 改檔頭 4 bytes」。
    #    這三步之間被中斷(Ctrl-C / 磁碟滿 / 外接碟被拔掉),留下來的就是一個
    #    資料、目錄、總長度互相對不上的封裝檔 —— 遊戲讀它會怎麼樣沒有人知道。
    #    現在改成:先把現況**逐位元組**複製成同資料夾的暫存檔
    #    (這不是重新打包 —— 孤兒資料一個位元組不少地跟著複製過去,
    #     專案鐵律「封裝檔不可重新打包」沒有被違反),
    #    三步全部做在暫存檔上,讀回來驗過(目錄指到的位元組真的等於要寫的內容、
    #    檔頭總長度等於實際長度)才 os.replace 換上去。
    #    同一個封裝檔的多個項目合成一趟做,不必把大檔複製很多次。
    groups = []
    for r in arch_rows:
        p = r['dests'][0]['path']
        for g in groups:
            if g[0] == p:
                g[1].append(r)
                break
        else:
            groups.append((p, [r]))
    for path, members in groups:
        target, why = _open_target(gamedir, members[0]['dests'][0])
        if target is None:
            for r in members:
                print('  ❌ %s 不裝:%s' % (r['base'], why))
                skipped += 1
            continue
        why = _ensure_backup(target, target + BACKUP_SUFFIX)
        if why is not None:
            for r in members:
                print('  ❌ %s 不裝:%s' % (r['base'], why))
                skipped += 1
            continue
        fd, tmp = _new_temp_beside(target)
        try:
            os.close(fd)
            _copy_exact(target, tmp)          # 逐位元組複製現況(含孤兒資料)
            written = []
            for r in members:
                field = r['dests'][0]['field']
                if path in replaced:
                    # 這個封裝檔剛剛被整個換掉了,索引裡的目錄位置已經失效,
                    # 改從現場(也就是這份暫存複本)重新找。
                    field, why = _field_in_current_file(tmp, (r['rel'], r['base']))
                    if field is None:
                        print('  ❌ %s 不裝:%s' % (r['base'], why))
                        skipped += 1
                        continue
                blob = open(r['full'], 'rb').read()
                append_entry(tmp, field, blob)
                written.append((r, field, blob))
            if not written:
                continue                       # finally 會把暫存檔收掉
            why = _verify_archive(tmp, [(f, b) for _r, f, b in written])
            if why is not None:
                for r, _f, _b in written:
                    print('  ❌ %s 不裝:%s' % (r['base'], why))
                    skipped += 1
                print('     (正本沒有動。要回到最初那一份就跑 --restore)')
                continue
            try:
                shutil.copymode(target, tmp)
            except OSError:
                pass
            _commit_replace(tmp, target, record=True)
            for r, _f, _b in written:
                print('  ✅ %s → %s(附加寫入)' % (r['base'], path))
                done += 1
        except DataError as err:
            # 這個封裝檔本身有問題(檔頭大小欄對不上之類)。
            # 正本沒有被碰過 —— 所有動作都做在暫存檔上。
            print('  ❌ %s 這個封裝檔不裝:%s' % (path, err))
            print('     (正本沒有動。)')
            skipped += len(members)
        finally:
            _quiet_remove(tmp)

    # 防守用的出口。show() 已經把巢狀那一類從 ✅ 拆出去了,照理這裡是空的;
    # 萬一哪天有人改了分類方式,寧可印一行,也不要靜靜地少裝一個檔。
    for r in other_rows:
        print('  ⏭ %s 在巢狀壓縮封裝檔裡,本工具目前不寫這一層' % r['base'])
        skipped += 1

    # 有東西沒裝就不要回 0。回 0 會讓「跑完沒事」這個直覺變成假的。
    if skipped:
        print('\n  裝好 %d 個,另外 %d 個沒裝(上面每一個都印了原因)。'
              % (done, skipped))
        print('  要還原就跑 --restore\n')
        return 1
    print('\n  裝好 %d 個。要還原就跑 --restore\n' % done)
    return 0

def cmd_restore(gamedir):
    """--restore:走過整個遊戲資料夾,把本工具做的備份全部還原。

    只認 .autobak 這個字尾,所以不會去碰別課留下的 .bak。
    還原之後**備份留著不刪**,所以這個指令可以重複跑,
    每一次都會回到「本工具第一次動它之前」的狀態。

    ⚠️ 一個檔還原失敗**不會中斷整趟**。
       以前是直接讓 _restore_from_backup 的 SystemExit 往外丟,結果第一個
       壞備份就把整趟打斷:後面還沒輪到的檔一個都不還原,而畫面上只有一行
       錯誤訊息 —— 讀的人會合理地以為「只有那一個沒救、其他都回去了」,
       實際上遊戲還停在被改過的狀態。而「有壞備份」正好就是上一趟被中斷的
       情境,也就是最需要還原的時候。
       2026-09-05 實測:一份壞的 bad.big.autobak 就讓另一個資料夾裡完好的
       good.big 完全沒被還原,而且沒有任何收尾統計。
       現在改成:壞的那一個印出原因、跳過,其餘照樣還原,最後給一行總計,
       只要有任何一個沒還原成功就回傳非 0。
    """
    n, bad = 0, 0
    for r, _, fs in os.walk(gamedir):
        for f in fs:
            if not f.endswith(BACKUP_SUFFIX):
                continue
            bak = os.path.join(r, f)
            # 原檔名就是把字尾拿掉;備份跟正本永遠躺在同一個資料夾裡,
            # 所以不需要另外記一份「誰對應誰」的清單。
            orig = bak[:-len(BACKUP_SUFFIX)]
            # 這一步會先驗備份的結構,壞的備份不會被拿來覆蓋正本。
            # 擋下來的時候它丟的是 SystemExit,在這裡接住,當成「這一個不還原」。
            try:
                _restore_from_backup(bak, orig)
            except SystemExit as err:
                print('  ❌ %s 沒有還原:' % os.path.relpath(orig, gamedir))
                for line in str(err).splitlines():
                    print('       %s' % line.strip())
                bad += 1
                continue
            except OSError as err:
                print('  ❌ %s 沒有還原:%s'
                      % (os.path.relpath(orig, gamedir), err))
                bad += 1
                continue
            print('  還原 %s' % os.path.relpath(orig, gamedir))
            n += 1
    if bad:
        # 有東西沒還原就明講「那幾個還停在被改過的狀態」,而且不可以回 0 ——
        # 回 0 會讓人(跟自動化流程)以為全部都回去了。
        print('\n  共還原 %d 個檔,另外 %d 個沒有還原(上面每一個都印了原因)。'
              % (n, bad))
        print('  那 %d 個檔還停在被改過的狀態,'
              '請改用你自己另外留的那一份備份。\n' % bad)
        return 1
    print('  %s\n' % ('共還原 %d 個檔' % n if n else '沒有找到本工具做的備份'))
    return 0

def _fake_big(items):
    """造一個最小的 BIGF 封裝檔給自我測試用。完全不碰任何遊戲檔。

    格式跟 _entries_of() 讀的一樣:檔頭 16 個位元組(位移 4-8 是檔案總大小、
    8-12 是項目數、12-16 是目錄長度),目錄從 16 開始,
    每一項是 4 個位元組的資料位移 + 4 個位元組的長度(都是大端)
    再接一個以 \0 結尾的名字。
    """
    toc = b''
    for name, _data in items:
        toc += b'\0' * 8 + name.encode('ascii') + b'\0'
    hdr = 16 + len(toc)
    body, offs = b'', []
    for _name, data in items:
        offs.append(hdr + len(body))
        body += data
    out = bytearray(b'BIGF' + b'\0' * 4 + struct.pack('>I', len(items))
                    + struct.pack('>I', hdr) + toc + body)
    pos = 16
    for i, (name, data) in enumerate(items):
        struct.pack_into('>II', out, pos, offs[i], len(data))
        pos += 8 + len(name) + 1
    struct.pack_into('<I', out, 4, len(out))      # 總大小欄用小端(原版的做法)
    return bytes(out)


def selftest():
    """--selftest:自己造一份最小的假遊戲來測,完全不碰任何真的遊戲檔。

    正向(先證明正常流程真的做得到承諾的事 —— 少了它,底下的反向餌
    有可能只是「整支都壞了」才過的):
      散裝檔真的被換掉 · 封裝檔裡的項目真的接得進去也讀得回來 ·
      附加寫入之後舊資料一個位元組都還在(專案鐵律)·
      備份與收據都做出來了而且對得上 · --restore 之後逐位元組回到原狀。

    反向餌 12 塊,每一塊都是「故意做一件必須失敗的事」,失敗不了就是防線壞了:
      1 事先把 <目標>.autobak.part 做成指向資料夾外面的符號連結 ——
        外面那個檔不可以被動到(舊版那個猜得到的暫存名就是死在這裡)
      2 <目標>.autobak 本身是符號連結 —— 要拒絕,外面那個檔不可以被動到
      3 已經有一份沒有收據的舊備份 —— 不可以讓你繼續改那個檔
      4 去處本身是符號連結 —— _safe_target 與寫入層都要擋
      5 收據不見了 —— --restore 要拒絕,而且正本不可以被動到
      6 收據還在但備份被截短 —— 一樣要拒絕、正本不可以被動到
      7 還原到一半 os.replace 失敗 —— 正本必須原封不動,而且不留暫存檔
      8 散裝檔寫到一半 os.replace 失敗 —— 同上
      9 封裝檔的複驗餵一段對不上的內容 —— 一定要抓出來
     10 模組裡有讀不到的檔 —— 整批中止,一個檔都不可以被裝
     11 還原的目的地是符號連結 —— 要拒絕,資料夾外面那個檔不可以被動到
     12 收據的位置是符號連結 —— 要拒絕,而且不可以留下一份沒有收據的備份
    """
    # -O 會把 assert 整個拿掉。本檔的 ck() 是自己 raise AssertionError,
    # 所以不吃這一刀;守門加在這裡是為了跟本站其他腳本口徑一致 ——
    # 不該讀者換一支跑,有的擋、有的不擋。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,'
              '測試會假綠')
        return 2

    import io as _io
    import contextlib

    tally = [0]

    def ck(cond, msg):
        tally[0] += 1
        if not cond:
            raise AssertionError(msg)

    def quiet(fn, *a):
        """跑一個指令但把它印的東西吃掉,只留回傳值。"""
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fn(*a)
        return rc, buf.getvalue()

    def leftovers(path):
        d = os.path.dirname(path)
        return [x for x in os.listdir(d) if x.startswith(TMP_PREFIX)]

    root = tempfile.mkdtemp(prefix='mvpai-selftest-')
    try:
        game = os.path.join(root, 'game')
        mod = os.path.join(root, 'mod')
        os.makedirs(os.path.join(game, 'data'))
        os.makedirs(mod)
        outside = os.path.join(root, 'outside.txt')
        OUTSIDE = b'OUTSIDE-MUST-NOT-CHANGE\n'
        open(outside, 'wb').write(OUTSIDE)

        big0 = _fake_big([('a.txt', b'OLD-A-DATA'), ('b.txt', b'OLD-B-DATA')])
        notes0 = b'line1\nline2\nline3\n'
        bigp = os.path.join(game, 'data', 'test.big')
        notesp = os.path.join(game, 'data', 'notes.txt')
        open(bigp, 'wb').write(big0)
        open(notesp, 'wb').write(notes0)
        open(os.path.join(mod, 'a.txt'), 'wb').write(b'NEW-A-DATA-LONGER')
        open(os.path.join(mod, 'notes.txt'), 'wb').write(b'brand new notes\n')

        # 餌 1:先把舊版那個猜得到的暫存名做成指向資料夾外面的符號連結。
        os.symlink(outside, notesp + BACKUP_SUFFIX + '.part')

        rc, out = quiet(cmd_install, game, mod, True)
        ck(rc == 0, '正常安裝應該回 0,實際 %d\n%s' % (rc, out))
        ck(open(outside, 'rb').read() == OUTSIDE,
           '餌 1:資料夾外面那個檔被動到了 —— 暫存檔跟著符號連結走了')

        # 餌 1b:散裝檔寫入用的暫存檔名也不可以猜得到。
        #       事先把舊寫法會用到的 <目標>.part 做成指向資料夾外面的連結,
        #       外面那個檔一個位元組都不可以變。
        probe = os.path.join(game, 'data', 'probe.bin')
        open(probe, 'wb').write(b'live')
        os.symlink(outside, probe + '.part')
        ck(_atomic_write_bytes(probe, b'NEWDATA') is None, '正常寫入應該成功')
        ck(open(probe, 'rb').read() == b'NEWDATA', '正常寫入沒有生效')
        ck(open(outside, 'rb').read() == OUTSIDE,
           '餌 1b:外面那個檔被暫存檔寫穿了')
        os.remove(probe + '.part')
        os.remove(probe)

        # 正向:散裝檔換掉了
        ck(open(notesp, 'rb').read() == b'brand new notes\n', '散裝檔沒有被換掉')
        # 正向:封裝檔裡的項目接進去了,而且讀得回來
        live = open(bigp, 'rb').read()
        ents = dict((e[0], (e[2], e[3])) for e in _entries_of(live))
        off, sz = ents['a.txt']
        ck(live[off:off + sz] == b'NEW-A-DATA-LONGER', '封裝檔項目沒有接進去')
        # 正向:附加寫入 —— 舊資料一個位元組都還在(專案鐵律)
        old_off, old_sz = [(e[2], e[3]) for e in _entries_of(big0)
                           if e[0] == 'a.txt'][0]
        ck(live[old_off:old_off + old_sz] == b'OLD-A-DATA',
           '舊資料應該還躺在檔案裡 —— 附加寫入的鐵律破了')
        b_off, b_sz = ents['b.txt']
        ck(live[b_off:b_off + b_sz] == b'OLD-B-DATA', '沒點名的項目被動到了')
        # 正向:備份 + 收據
        for p, want in ((notesp, notes0), (bigp, big0)):
            ck(open(p + BACKUP_SUFFIX, 'rb').read() == want,
               '備份的內容不對:%s' % os.path.basename(p))
            ck(_check_receipt(p + BACKUP_SUFFIX) is None,
               '收據對不上:%s' % os.path.basename(p))

        # 餌 9:複驗餵一段對不上的內容,一定要抓出來
        field = [e[1] for e in _entries_of(live) if e[0] == 'a.txt'][0]
        ck(_verify_archive(bigp, [(field, b'NEW-A-DATA-LONGER')]) is None,
           '複驗把對的說成錯的')
        ck(_verify_archive(bigp, [(field, b'XXX-A-DATA-LONGER')]) is not None,
           '餌 9:複驗沒抓到對不上的內容(長度一樣、內容不一樣)')
        ck(_verify_archive(bigp, [(field, b'short')]) is not None,
           '餌 9:複驗沒抓到長度對不上')
        broken = os.path.join(root, 'broken.big')
        raw = bytearray(big0)
        struct.pack_into('<I', raw, 4, len(raw) + 7)   # 檔頭說謊
        open(broken, 'wb').write(bytes(raw))
        ck(_verify_archive(broken, []) is not None, '餌 9:檔頭總長度對不上竟然說過')
        broken2 = os.path.join(root, 'broken2.big')
        raw2 = bytearray(big0)
        struct.pack_into('>I', raw2, 8, 9)            # 目錄說有 9 項,實際 2 項
        struct.pack_into('<I', raw2, 4, len(raw2))    # 總長度仍然對得上
        open(broken2, 'wb').write(bytes(raw2))
        ck(_verify_archive(broken2, []) is not None,
           '餌 9:目錄走不完(說 9 項只有 2 項)竟然說過')
        ck(_verify_archive(bigp, []) is None, '整張目錄走得完的檔不該被判成壞的')

        real_replace = os.replace

        def boom(*_a, **_k):
            raise OSError(5, '餌:故意讓 os.replace 失敗')

        # 餌 8:散裝檔寫到一半 os.replace 失敗
        before = open(notesp, 'rb').read()
        os.replace = boom
        try:
            try:
                _atomic_write_bytes(notesp, b'X' * 999)
                ck(False, '餌 8:os.replace 都壞了竟然還回報成功')
            except OSError:
                ck(True, '')
        finally:
            os.replace = real_replace
        ck(open(notesp, 'rb').read() == before, '餌 8:寫入失敗的時候正本被動到了')
        ck(not leftovers(notesp), '餌 8:失敗之後留下暫存檔')

        # 餌 7:還原到一半 os.replace 失敗
        open(notesp, 'wb').write(b'MODIFIED')
        os.replace = boom
        try:
            try:
                _do_copy(notesp + BACKUP_SUFFIX, notesp)
                ck(False, '餌 7:還原到一半失敗竟然沒有報錯')
            except OSError:
                ck(True, '')
        finally:
            os.replace = real_replace
        ck(open(notesp, 'rb').read() == b'MODIFIED',
           '餌 7:還原失敗的時候正本被動到了')
        ck(not leftovers(notesp), '餌 7:失敗之後留下暫存檔')

        # 餌 5:收據不見了 —— 不可以自動還原
        rp = _receipt_path(notesp + BACKUP_SUFFIX)
        saved = open(rp, 'rb').read()
        os.remove(rp)
        rc, out = quiet(cmd_restore, game)
        ck(rc != 0, '餌 5:沒有收據竟然還原成功了')
        ck(open(notesp, 'rb').read() == b'MODIFIED',
           '餌 5:被擋下來的時候正本不可以被動到')
        open(rp, 'wb').write(saved)

        # 餌 6:收據還在,但備份被截短
        bakp = notesp + BACKUP_SUFFIX
        full = open(bakp, 'rb').read()
        open(bakp, 'wb').write(full[:len(full) // 2])
        rc, out = quiet(cmd_restore, game)
        ck(rc != 0, '餌 6:收據對不上竟然還原成功了')
        ck(open(notesp, 'rb').read() == b'MODIFIED',
           '餌 6:被擋下來的時候正本不可以被動到')
        open(bakp, 'wb').write(full)

        # 餌 2:備份路徑本身是符號連結
        p2 = os.path.join(game, 'data', 'notes2.txt')
        open(p2, 'wb').write(b'hello\n')
        os.symlink(outside, p2 + BACKUP_SUFFIX)
        why2 = _ensure_backup(p2, p2 + BACKUP_SUFFIX)
        ck(why2 is not None and '符號連結' in why2,
           '餌 2:備份路徑是符號連結,擋下來的理由要講明是符號連結,'
           '實際講的是:%r' % why2)
        ck(open(outside, 'rb').read() == OUTSIDE, '餌 2:外面那個檔被動到了')
        os.remove(p2 + BACKUP_SUFFIX)
        os.remove(p2)

        # 餌 3:已經有一份沒有收據的舊備份 —— 不可以讓你繼續改那個檔
        p3 = os.path.join(game, 'data', 'old.txt')
        open(p3, 'wb').write(b'hi\n')
        open(p3 + BACKUP_SUFFIX, 'wb').write(b'hi\n')
        ck(_ensure_backup(p3, p3 + BACKUP_SUFFIX) is not None,
           '餌 3:沒有收據的舊備份旁邊竟然還讓你繼續改')
        os.remove(p3 + BACKUP_SUFFIX)
        os.remove(p3)

        # 餌 4:去處本身是符號連結
        linkp = os.path.join(game, 'data', 'linked.big')
        os.symlink(outside, linkp)
        t, why = _safe_target(game, 'data/linked.big')
        ck(t is None and why, '餌 4:去處是符號連結竟然沒被擋')
        ck(_atomic_write_bytes(linkp, b'zzz') is not None,
           '餌 4:寫入層也要擋符號連結')
        ck(open(outside, 'rb').read() == OUTSIDE, '餌 4:外面那個檔被動到了')
        os.remove(linkp)

        # 餌 11:還原的目的地被換成指向資料夾外面的符號連結。
        #       還原是使用者救火時按的那一鍵,這裡沿著連結寫下去,
        #       被毀的會是遊戲資料夾**外面**那個檔 —— 他連想都不會想到。
        p11 = os.path.join(game, 'data', 'note11.txt')
        open(p11, 'wb').write(b'eleven\n')
        buf11 = _io.StringIO()
        with contextlib.redirect_stdout(buf11):
            why11 = _ensure_backup(p11, p11 + BACKUP_SUFFIX)
        ck(why11 is None, '餌 11 的前置:正常的備份應該做得出來,實際:%r' % why11)
        os.remove(p11)
        os.symlink(outside, p11)
        try:
            _restore_from_backup(p11 + BACKUP_SUFFIX, p11)
            ck(False, '餌 11:還原的目的地是符號連結竟然照樣還原')
        except SystemExit:
            ck(True, '')
        ck(open(outside, 'rb').read() == OUTSIDE, '餌 11:外面那個檔被還原寫穿了')
        os.remove(p11)
        os.remove(_receipt_path(p11 + BACKUP_SUFFIX))
        os.remove(p11 + BACKUP_SUFFIX)

        # 餌 12:收據要放的位置被人先擺了一個指向資料夾外面的符號連結。
        #       兩件事都要成立:外面那個檔不可以被寫穿,而且不可以留下
        #       一份沒有收據的備份 —— 那種備份會把這個檔永遠鎖住(見餌 3)。
        p12 = os.path.join(game, 'data', 'note12.txt')
        open(p12, 'wb').write(b'twelve\n')
        os.symlink(outside, _receipt_path(p12 + BACKUP_SUFFIX))
        buf12 = _io.StringIO()
        with contextlib.redirect_stdout(buf12):
            why12 = _ensure_backup(p12, p12 + BACKUP_SUFFIX)
        ck(why12 is not None, '餌 12:收據寫不出來竟然還讓你繼續改那個檔')
        ck(open(outside, 'rb').read() == OUTSIDE, '餌 12:外面那個檔被收據寫穿了')
        ck(not os.path.lexists(p12 + BACKUP_SUFFIX),
           '餌 12:收據失敗之後留下一份沒有收據的備份 —— 那會把這個檔永遠鎖住')
        os.remove(_receipt_path(p12 + BACKUP_SUFFIX))
        os.remove(p12)

        # 餌 10:模組裡有讀不到的檔 —— 整批中止,一個檔都不可以被裝
        mod2 = os.path.join(root, 'mod2')
        os.makedirs(mod2)
        open(os.path.join(mod2, 'notes.txt'), 'wb').write(b'MUST-NOT-INSTALL\n')
        locked = os.path.join(mod2, 'b.txt')
        open(locked, 'wb').write(b'x')
        os.chmod(locked, 0)
        if not os.access(locked, os.R_OK):   # 用 root 跑的話 chmod 擋不住,跳過
            before = open(notesp, 'rb').read()
            rc, out = quiet(cmd_install, game, mod2, True)
            ck(rc != 0, '餌 10:模組裡有讀不到的檔竟然照裝')
            ck(open(notesp, 'rb').read() == before, '餌 10:中止了卻還是寫了東西')
        os.chmod(locked, 0o600)

        # 正向收尾:完整的備份 + 對得上的收據,要真的還原得動,而且逐位元組回去
        rc, out = quiet(cmd_restore, game)
        ck(rc == 0, '正常還原應該回 0:\n%s' % out)
        ck(open(notesp, 'rb').read() == notes0, '還原之後應該逐位元組回到原狀')
        ck(open(bigp, 'rb').read() == big0, '還原之後應該逐位元組回到原狀')
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print('自我測試:全部通過(%d 道檢查,其中 12 塊是反向餌)' % tally[0])
    return 0


def main():
    """指令列入口。回傳值就是 exit code:
    0 全部做完、1 有東西沒裝成/沒還原成/資料有問題、2 路徑不對、
    130 你按了 Ctrl-C。"""
    ap = argparse.ArgumentParser(
        description='MVP Baseball 2005 模組自動安裝器 —— 認內容不認設定檔')
    # --selftest 不需要遊戲資料夾,所以位置參數改成可有可無;
    # 沒給又不是 --selftest 的話,下面自己補一句錯誤訊息(exit code 還是 2)。
    ap.add_argument('gamedir', nargs='?',
                    help='遊戲資料夾(裡面要有 data 這個子資料夾)')
    ap.add_argument('--index', action='store_true', help='看這份遊戲的索引摘要')
    ap.add_argument('--scan', metavar='模組資料夾', help='清點,完全不動檔案')
    ap.add_argument('--install', metavar='模組資料夾', help='安裝(不加 --apply 只預覽)')
    ap.add_argument('--apply', action='store_true', help='真的寫入')
    ap.add_argument('--restore', action='store_true', help='還原本工具做的備份')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試,完全不碰遊戲檔(不需要遊戲資料夾)')
    a = ap.parse_args()

    # --selftest 最優先:它自己造一份假遊戲,不需要也不會碰真的遊戲資料夾。
    if a.selftest:
        return selftest()
    if not a.gamedir:
        ap.error('要給遊戲資料夾(或者用 --selftest)')

    # 先擋一次「路徑給錯」。建索引要走過整個資料夾,
    # 給錯路徑的話會安安靜靜地掃很久,最後告訴你什麼都沒找到。
    if not os.path.isdir(os.path.join(a.gamedir, 'data')):
        print('  ❌ %s 底下沒有 data 資料夾,這不像是遊戲資料夾' % a.gamedir)
        return 2
    # 模組資料夾也要擋,而且理由一樣重要:os.walk 走一個不存在的路徑
    # **不會出錯**,只會給你一份空清單。所以路徑打錯的人會看到
    # 「這包模組:0 個檔」然後 --scan 印「這一步完全沒有動到任何檔案」、
    # exit code 0,整段看起來像跑成功;而排錯表會把「什麼都認不出來」
    # 導向「這包模組全是新增檔案」,方向完全錯。
    moddir = a.scan or a.install
    if moddir is not None and not os.path.isdir(moddir):
        print('  ❌ 找不到模組資料夾:%s' % moddir)
        print('       請確認路徑沒有打錯,而且那是**已經解壓縮出來的資料夾**,'
              '不是壓縮檔本身。')
        return 2
    # 順序有意義:還原排第一(檔案已經壞掉時你會來按這個),
    # 再來是唯讀的清點,最後才是會動檔的安裝。
    # 什麼都沒指定就跑 --index,那是唯讀的,當預設最安全。
    try:
        if a.restore:
            return cmd_restore(a.gamedir)
        if a.scan:
            return cmd_scan(a.gamedir, a.scan)
        if a.install:
            return cmd_install(a.gamedir, a.install, a.apply)
        return cmd_index(a.gamedir)
    # DataError 是「檔案內容跟預期不符」。這裡接住它印成一行人話,
    # 而不是丟一整串 traceback 給不寫程式的人看。
    except DataError as err:
        print('  ❌ %s' % err)
        # 已經動過檔才多講一段 —— 一個檔都還沒碰的失敗不必再說一次「沒動到」。
        if _REPLACING or _TOUCHED:
            _print_touch_state()
        return 1
    # 讀寫失敗同理。--apply 之前已經先用 os.access 驗過一次能不能寫,
    # 但那個驗法在 Windows 上看不出「檔案正被遊戲鎖住」(那是共用模式的問題,
    # 不是權限),所以這裡還要再接一層,不然讀者會拿到一整串 traceback。
    except OSError as err:
        print('  ❌ 讀寫失敗:%s' % err)
        print('       常見原因:遊戲正開著、檔案被設成唯讀、'
              '這個資料夾要系統管理員權限、磁碟滿了。')
        if _REPLACING or _TOUCHED:
            _print_touch_state()
        return 1
    # Ctrl-C。這裡**一定**要分清楚「已經換掉幾個檔」——
    # 「什麼都沒動到」跟「檔案已經改了,去還原」對使用者的意義完全相反,
    # 猜錯比不說還糟;而且不可以回 0,回 0 會讓自動化流程以為跑完了。
    except KeyboardInterrupt:
        print('\n  ⛔ 你按了 Ctrl-C。')
        _print_touch_state()
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
