#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MVP Baseball 2005 —— 換打擊姿勢 / 投球姿勢

只改一個欄位:
  打擊姿勢 = data/database/attrib.dat  playerattrib_battingstance 欄
  投球姿勢 = data/database/pitcher.dat pitchattrib_pitcher_delivery 欄

  ⚠️ 不要記欄號。欄號會因名冊而異 —— 本站測試機的 battingstance 在第 28 欄,
     剛安裝好的原版在第 29 欄(原版把 skin_tone 排在第 12,這台移到第 38,
     12 之後全部往前挪一格,46 欄裡有 27 欄編號不同)。
     這支程式是照欄位「名字」從表頭找的,所以兩份都能用。

那個數字是「動作庫的組別編號」。遊戲拿它去 data/anims/anims.big
抓 SIGB<四位數> / SIGP<四位數> 那一組動作。

輸入(三個檔,兩個只讀、一個才寫):
  · 你給的遊戲資料夾路徑,裡面要有 data 這個子資料夾。
  · data/database/attrib.dat 或 pitcher.dat,CRLF 分行的純文字名冊。
    每一格自帶欄號,格式是「欄號 空格 值」,格與格之間用逗號隔開;
    資料列開頭多一個 9 個十六進位字元的紀錄編號,第 0 列是表頭。
    這是唯一會被寫入的檔。
  · data/anims/anims.big,EA 的 BIGF 封裝檔。全程唯讀,只拿來確認
    你要設的編號真的有對應的動作庫,以及 --show 要列的動作檔名。

輸出:
  · --list / --show / --find:只往螢幕印字,一個位元組都不寫。
  · --set 沒加 --apply:印「現在是什麼 / 要改成什麼」的預覽,一樣不寫。
  · --set 加 --apply:改名冊裡的那一格,再把複驗結果印出來。
    複驗只要有一項不符,離開碼就是非 0;備份如果是這一次剛做的,
    當場自動還原回動手之前的樣子(見下面安全網第 5 條)。
  · --selftest:自己造一份名冊在系統暫存資料夾裡跑完整套,不碰遊戲檔。
    (不要加 python -O:-O 會把 assert 整句拿掉,靠 assert 的測試會假綠。
     這一支的檢查不靠 assert,但守門照樣在 —— 加了會直接回 2。)
  · --restore:把 attrib.dat 與 pitcher.dat 兩邊都從 .bak 蓋回去。

安全網(六層,由外而內):
  1. 唯讀是預設,但這一句只涵蓋 --set。--set 沒有加 --apply,這支程式不會碰你的硬碟。
     --restore 不在這一句裡。它是另一條路,不看 --apply,備份通過覆蓋前那幾道把關之後,
     就把 attrib.dat 與 pitcher.dat 兩份整份蓋回去。本站把測試機那份 attrib.dat
     (840,643 bytes)與 pitcher.dat(269,986 bytes)複製到別的資料夾實測,
     只下 --restore、沒有加 --apply,兩份複本的 MD5 當場都變成各自備份的 MD5。
  2. 會動到硬碟的地方只有三處(建備份、寫名冊、把備份蓋回去),三處都是
     「先寫暫存檔、fsync 落地、再 os.replace 換過去」,所以任何一個檔案
     都不會停在半截的狀態:要嘛是舊的那一份、要嘛是新的那一份。
     暫存檔一律用 tempfile.mkstemp 在**同一個資料夾**裡取猜不到的名字
     (2026-09-05 改的;原本叫 .part / .tmp / .restore-part,名字猜得到,
     誰先在那裡放一個指向資料夾外面的符號連結,就會被跟著寫壞)。
     而且「os.replace 換過去」與「登記已經換過了」綁成不可中斷的一段
     (2026-09-06 加):Ctrl-C 沒辦法落在這兩件事中間,所以被中斷時
     程式講的那句話一定跟硬碟上的狀態一致,不會換過去了還說「沒動到」。
     真的卡在那一步的話(極少數環境裝不上訊號處理器),它會說
     「中斷時正在替換 X」,不會說死。
  3. 名冊與備份這兩個位置動手前都先用 os.path.islink 擋一次:是符號連結就停手,
     不跟著它寫到遊戲資料夾外面去。
  4. 第一次寫入前備份成 <檔名>.bak;已經有 .bak 就保留最早那一份,不覆蓋。
  5. 寫完重新讀一次,四個判準:整份要跟寫出去的逐位元組相同、列數要一樣、
     目標那一列要是預期的內容、而且只准有一列不同。
     (把編號改成他本來就是的那一個時,檔案內容不變、0 列不同,那也是對的。)
     任何一項不符就**不會**回 0;而且如果那份備份是這一次剛做的,
     當場自動還原回動手之前的樣子 —— 複驗沒過就不留下半信半疑的檔案。
  6. --restore 把備份寫進暫存檔之後,會整份讀回來算 sha256 跟備份比,
     相等才 os.replace 換過去。對不上就不換,正本維持你下指令之前的樣子。
  還原前另有把關擋掉壞掉的備份(0 bytes、開頭不像欄位表、沒有 CRLF、
  表頭找不到 first_name / last_name、不是以 CRLF 收尾、最後一列格數不對、
  比正本小一半以上);還原本身也是「先寫暫存再改名」,中途被中斷不會留下半截的正本。

做不到的事(先講清楚,免得誤會):
  · 不會替你判斷哪一組姿勢好看。本站沒有進遊戲一組一組看過畫面,
    只證明了「這個數字對到那一組動作庫」。
  · --show 只列得出那一組裡的動作檔名,畫不出動作本身。
  · 沒有任何人在用的編號(打擊 4 個、投球 14 個)設下去會不會正常,
    本站沒試過。
  · 只動姿勢這一欄。能力值、臉皮、大頭照一概不碰。
  · 一次只改一位球員;名字對到兩位以上會停下來要你把名字打完整。
  · 「改完在遊戲畫面上長怎樣」本站沒驗過,驗的是檔案層面。

零相依:只用 Python 標準函式庫。
寫入前一定先備份成 <檔名>.bak,--restore 一行還原。

用法:
  python mvp_edit_stance.py "遊戲資料夾" --list
  python mvp_edit_stance.py "遊戲資料夾" --show 14
  python mvp_edit_stance.py "遊戲資料夾" --find Ohtani
  python mvp_edit_stance.py "遊戲資料夾" --set Ohtani 14
  python mvp_edit_stance.py "遊戲資料夾" --set Ohtani 14 --apply
  python mvp_edit_stance.py "遊戲資料夾" --restore
  python mvp_edit_stance.py --selftest
加 --pitch 就是改投球姿勢(預設是打擊姿勢)。

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
import hashlib
import os
import re
import shutil
import signal
import struct
import sys
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

# 這一輪(2026-09-05,第二輪唯讀稽核)真的動到硬碟的地方只剩三處,
# 三處都走下面這三個 helper,沒有第四條路:
#   _atomic_copy   建備份           (path.bak)
#   _atomic_write  寫名冊           (--set --apply)
#   _do_copy       把備份蓋回正本   (--restore)
# 這一份清單是給稽核的人看的:要確認「這支程式會怎麼動你的檔案」,
# 讀這三個函式就夠了,不必翻完整支。
#
# 被中斷過的話,這裡會留下紀錄,檔尾的 KeyboardInterrupt 靠它決定要講哪一句話。
# 每一項是 (做了什麼, 哪個檔),做了什麼只有三種:'backup' / 'write' / 'restore'。
# 只在 os.replace 真的成功之後才 append —— 這樣「清單是空的」就等於
# 「一個位元組都還沒換過去」,那句「沒有改到任何檔案」才是真的。
_WRITTEN = []

# ── Ctrl-C 不可以說謊(2026-09-06 第三輪稽核加)────────────────────
# 上面那段寫著「清單是空的就等於一個位元組都還沒換過去」。這句話原本有一個
# 兩行寬的破口:os.replace() 已經把新檔扶正了,append 到 _WRITTEN 還沒跑完,
# Ctrl-C 剛好落在這兩行之間 —— 檔案是新的,清單卻是空的,
# 檔尾的收尾就會照舊狀態印「沒有改到任何檔案」。那句話是假的。
#
# 兩道一起補:
#   (a) 把「換名 + 登記」用 _NoInterrupt 包成不可中斷的一段。
#       這段期間收到的 SIGINT 先記著,離開這段之後才照常丟出來,
#       所以 KeyboardInterrupt 看到的登記一定跟磁碟上的狀態一致。
#   (b) 保險:進入那一段之前先把「正在換 X」登記在 _INFLIGHT。
#       (a) 幾乎不會讓 (b) 被用到 —— 唯一漏得掉的是 signal.signal() 自己
#       裝不上去的環境(不是主執行緒會丟 ValueError),那時 (a) 退回原本行為,
#       而 (b) 讓收尾至少講得出「中斷時正在替換 X」,不會講成「沒動到」。
# 三態因此是:_WRITTEN 有 → 已換;_INFLIGHT 有 → 正在換(不確定);
# 兩個都空 → 真的沒動到。
_INFLIGHT = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開之後再照常丟出。

    ⚠️ 這不是「吃掉 Ctrl-C」。使用者按下去的那一次一定會生效,
       只是延到這兩行跑完 —— 而這兩行加起來是一次改名加一次 append,
       不會讓人等。換來的是「程式講的話跟硬碟上的狀態一致」。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):
            # 不是主執行緒(ValueError)之類的環境:退回原本的行為,不會更糟。
            # 這正是 _INFLIGHT 那道保險存在的理由。
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


def _replace_and_record(tmp, dst, what):
    """把暫存檔扶正,並且在同一個不可中斷的區段裡登記「已經換過了」。

    三個寫入點(建備份 / 寫名冊 / 還原)全部走這一行,沒有第二條路 ——
    要稽核「這支程式什麼時候會說自己動過檔案」,看這個函式就夠了。
    """
    _INFLIGHT.append((what, dst))
    try:
        with _NoInterrupt():
            os.replace(tmp, dst)       # os.replace 是原子的
            _WRITTEN.append((what, dst))
    finally:
        try:
            _INFLIGHT.remove((what, dst))
        except ValueError:
            pass


def _quiet_remove(path):
    """把還沒扶正的暫存檔清掉。清不掉也不要蓋掉真正的錯誤原因。"""
    try:
        os.remove(path)
    except OSError:
        pass


def _refuse_symlink(path, what):
    """要寫的位置是符號連結就停手,不跟著它寫到資料夾外面去。

    ⚠️ 這一道是 2026-09-05 第二輪稽核補的。原本備份寫在
       `<檔名>.bak.part`、名冊寫在 `<檔名>.tmp`、還原寫在
       `<檔名>.restore-part` —— 三個都是**猜得到的名字**。
       誰先在那個名字上放一個指向別處的符號連結,
       open(..., 'wb') / copy2() 的第一件事就是**跟著連結**把外面那個檔截成 0。
       後面的 os.replace() 確實只換掉連結本身,可是外面的檔早就沒了。

       現在兩件事一起做:暫存檔改用 tempfile.mkstemp(dir=同資料夾) 取
       猜不到也搶不到的名字(mkstemp 內部用 O_CREAT|O_EXCL,
       名字被佔走就換一個,不會沿用),正式的目的檔與備份檔則在動手前
       用 os.path.islink() 擋一次。

    ⚠️ 用 os.path.islink 不用 os.path.exists:符號連結指到不存在的東西時,
       exists() 回的是 False —— 那種「空心的連結」正是最危險的一種,
       因為它會讓「這裡還沒有檔案」看起來成立。
    """
    if os.path.islink(path):
        try:
            tgt = os.readlink(path)
        except OSError:
            tgt = '(讀不出來)'
        raise DataError(
            '%s %s 是一個符號連結(指向 %s),本工具不跟著它寫。\n'
            '  跟著寫下去會改到遊戲資料夾外面的檔案。\n'
            '  請把那個連結刪掉、換成真正的檔案,再跑一次。'
            % (what, path, tgt))


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    ⚠️ 2026-09-05:暫存檔從固定的 dst + '.part' 改成
       tempfile.mkstemp(dir=備份要放的那個資料夾)。理由見 _refuse_symlink()。
       同一個資料夾是必要條件 —— os.replace 跨檔案系統會失敗,
       原子性也只在同一個檔案系統裡才成立。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_symlink(dst, '備份檔')
    d = os.path.dirname(dst) or '.'
    fd, part = tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(dst) + '.part-')
    try:
        with os.fdopen(fd, 'wb') as w:
            with open(src, 'rb') as r:
                shutil.copyfileobj(r, w)
            w.flush()
            os.fsync(w.fileno())       # 先落地,再改名
    except BaseException:
        try:
            os.close(fd)               # fdopen 沒接手時才需要;接手了會是 EBADF
        except OSError:
            pass
        _quiet_remove(part)
        raise
    try:
        shutil.copystat(src, part)     # 時間與權限跟著原檔走,等同 copy2
        # 換名 + 登記是同一步,中間插不進 Ctrl-C(見 _replace_and_record)。
        _replace_and_record(part, dst, 'backup')
    except BaseException:
        _quiet_remove(part)            # 已經扶正的話這裡清不到東西,無妨
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
    # 兩個位置都要在讀第一個位元組之前擋一次:備份被換成連結,
    # 底下每一道結構檢查驗到的都會是連結指向的那個檔,而不是這裡真正躺著的東西;
    # 正本被換成連結,覆蓋就會寫到資料夾外面去。
    _refuse_symlink(bak, '備份')
    _refuse_symlink(dst, '要還原的檔案')
    # lexists 不是 exists:空心的符號連結(指向不存在的東西)在 exists() 下
    # 回 False,會被誤報成「找不到備份」,而真正的狀況是「那裡有東西,但它是壞的」。
    # 上面那道已經把連結擋掉了,這裡用 lexists 是為了不留下第二種說法。
    if not os.path.lexists(bak):
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
# 上面每一道把關都必須先放行,才會走到這裡。
# 把它獨立成一個函式,就是為了「會動到硬碟的地方只有一處」好稽核。
def _do_copy(bak, dst):
    """把備份原封不動蓋回目標:寫暫存 → 落地 → **讀回來對過** → 才改名。

    copy2 會連修改時間一起帶過去。但**不可以**直接 copy2 到正本身上:
    它的第一件事是把正本開成 'wb'(當場清空)再從頭寫,途中被中斷
    (外接碟拔掉、磁碟滿、按 Ctrl-C)正本就停在半截。
    這是整支程式唯一會覆蓋正本的地方,而且會走到這裡的人通常已經出事了,
    不能是三個寫入點裡唯一不原子的那一個。

    實測(2026-09-05):拿一份 419,730,684 bytes 的合法名冊當正本與備份,
    跑 --restore 之後 0.30 秒 kill -9,其中一次量到正本被截成 253,755,392
    bytes(備份完好)。改成「暫存檔 + os.replace」之後同樣的殺法,
    正本要嘛是原本那份、要嘛是完整還原的那份,沒有中間狀態。

    ── 2026-09-05 第二輪稽核又補了三件事 ────────────────────────
    1. 暫存檔名改成 tempfile.mkstemp(dir=正本所在資料夾) —— 理由見
       _refuse_symlink()。原本的 dst + '.restore-part' 是猜得到的名字。
    2. 寫完 fsync,再**整份讀回來算 sha256** 跟備份比。相等才 os.replace。
       這一步不是裝飾:走到 --restore 的人手上通常已經有一個壞掉的檔,
       如果磁碟本身就是出事的原因(壞軌、外接碟接觸不良、空間剛好用完),
       寫出去跟讀回來會不一樣 —— 那種時候寧可不換,讓正本維持現狀。
       任何一步失敗都 os.remove 暫存檔,正本連碰都沒碰過。
    3. 權限跟著**正本**走(shutil.copymode(dst, tmp)),時間跟著備份走。
       mkstemp 造出來的檔是 0600,少了這一行,還原完的名冊權限會突然收緊。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_symlink(bak, '備份')
    _refuse_symlink(dst, '要還原的檔案')
    d = os.path.dirname(dst) or '.'
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(dst) + '.restore-')
    try:
        want = hashlib.sha256()
        with os.fdopen(fd, 'wb') as w:
            with open(bak, 'rb') as r:
                for chunk in iter(lambda: r.read(1 << 20), b''):
                    want.update(chunk)
                    w.write(chunk)
            w.flush()
            os.fsync(w.fileno())
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        _quiet_remove(tmp)
        raise
    try:
        got = hashlib.sha256()
        with open(tmp, 'rb') as r:
            for chunk in iter(lambda: r.read(1 << 20), b''):
                got.update(chunk)
        if got.digest() != want.digest() or os.path.getsize(tmp) != os.path.getsize(bak):
            raise SystemExit(
                '還原寫到一半就對不上了:寫出去的內容跟讀回來的不一樣。\n'
                '  %s 一個位元組都沒有被動到,維持你跑這道指令之前的樣子。\n'
                '  多半是磁碟出問題(壞軌、外接碟接觸不良、空間剛好用完)。\n'
                '  換一顆碟、或先把 %s 複製到別的地方,再試一次。'
                % (dst, os.path.basename(bak)))
        shutil.copystat(bak, tmp)      # 修改時間跟著備份走(等同 copy2)
        if os.path.exists(dst):
            shutil.copymode(dst, tmp)  # 權限跟著正本走,不要被 mkstemp 的 0600 收緊
        _replace_and_record(tmp, dst, 'restore')
    except BaseException:
        _quiet_remove(tmp)
        raise




# ── 輸出編碼(繁體中文 Windows 專用的一道保險)──────────────
# 繁中 Windows 的預設編碼是 cp950,編不出 ✅ ⚠ ✗ 這些符號。
# 直接在主控台跑不會有事(Python 走 Windows 的 Unicode API),
# 但只要把輸出導到檔案或接管線 —— 而那正是新手最常被教的存檔方式:
#     python3 這支腳本.py "你的遊戲資料夾" > 結果.txt
# —— 就會 UnicodeEncodeError,而且是「跑到一半才炸」,
# 前面印出來的東西看起來都好好的,更難判斷發生什麼事。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass   # Python 3.6 以前沒有 reconfigure;那就維持原樣,不要為了保險而炸掉


# (原本這裡有個 FIELD = 28 的常數,但這支腳本自始就用 header_field() 從表頭解析,
#  那個常數沒有被任何地方用到。2026-08-25 拿原版對照時發現原版的
#  playerattrib_battingstance 其實在第 29 欄 —— 幸好程式碼是對的,只有註解會誤導人。)
# 兩種姿勢的規格表。四個欄位一路帶進每一個 cmd_* 函式:
#   (名冊在 data/ 底下的相對路徑, 要找的欄位名, 動作庫檔名前綴, 印給人看的中文名)
# 整支程式沒有第二個地方寫死「打擊」或「投球」,差別全部收斂在這兩行。
BAT = ('database/attrib.dat', 'playerattrib_battingstance', 'SIGB', '打擊姿勢')
PIT = ('database/pitcher.dat', 'pitchattrib_pitcher_delivery', 'SIGP', '投球姿勢')


class DataError(Exception):
    """可以直接講給人聽的錯誤。

    檔尾的進入點會把它印成一行中文,不是 Python traceback。
    凡是「使用者做錯了什麼」都丟這個;
    只有「程式自己壞了」才讓原生例外冒上去,那種才需要看堆疊。
    """
    pass


# ── 名冊 ────────────────────────────────────────────────
def load(path):
    """整個檔案讀進來,保留原始 bytes。名冊是 CRLF 分行的純文字。

    刻意用二進位模式而不是文字模式:名冊裡有非 ASCII 的名字,
    而且換行必須維持 CRLF。文字模式會把 CRLF 讀成單一換行字元,
    寫回去就變成 LF,整份名冊的換行等於被改掉了。
    """
    try:
        raw = open(path, 'rb').read()
    except OSError as e:
        raise DataError('打不開 %s(%s)' % (path, e))
    # 用 CRLF 這兩個位元組去切,不用 splitlines():
    # splitlines() 連單獨的 CR、LF、甚至 U+2028 都當換行,
    # 名字裡混到那類字元就會被切成兩列,寫回去時列數對不上。
    lines = raw.split(b'\r\n')
    if len(lines) < 2:
        raise DataError('%s 看起來不是 CRLF 分行的名冊。' % path)
    return lines


def header_field(header, want):
    """照欄位「名字」去表頭問出它是第幾欄,程式裡沒有寫死的欄號。

    (這個函式不是拿來「確認第 28 欄」的,它就是把欄號查出來的那一步。
     欄號會因名冊而異:本站測試機那份 attrib.dat 的
     playerattrib_battingstance 在第 28 欄、剛安裝好的原版在第 29 欄;
     pitcher.dat 的 pitchattrib_pitcher_delivery 則是兩份都在第 28 欄。
     見檔頭那段警告。)

    表頭長這樣,欄號與欄位名之間只隔一個空格:
        0 first_name,1 last_name,2 playerattrib_jerseynum,...
    找到就回傳那個欄號(整數);找不到回傳 None,
    由呼叫端決定要講什麼話,這裡不自己丟例外。
    """
    for m in re.finditer(rb'(?:^|,)(\d+) ([a-z_0-9]+)', header):
        if m.group(2).decode() == want:
            return int(m.group(1))
    return None


def cell(line, field):
    """取出這一列第 field 欄的值,取不到回傳 None。

    名冊的每一格都自帶欄號,所以「找第 28 欄」就是找
    「行首或逗號」後面緊接著「28 空格」的那一段,一直讀到下一個逗號。
    欄位排列順序因此完全不影響取值,這也是這支程式敢跨名冊用的原因。

    用 latin-1 解碼是刻意的:它把 0 到 255 每個位元組一對一映成字元,
    永遠不會拋解碼錯誤。名冊裡有帶重音符號的外國名字,
    用 utf-8 解會當場炸掉;這裡只需要把值原封不動拿出來比對,
    不需要「正確的文字」。
    """
    m = re.search(rb'(?:^|,)%d ([^,]*)' % field, line)
    return m.group(1).decode('latin-1').strip() if m else None


# 第 0、1 欄固定是 first_name 與 last_name。
# 這不是猜的:looks_like_roster() 就是靠表頭有沒有這兩個名字來認名冊。
# 缺格的列不讓它整支掛掉,用空字串頂著,搜尋時就只是比對不到而已。
def name_of(line):
    """把一列的名與姓接成「名 姓」,只給人看,以及拿來做關鍵字比對。"""
    return '%s %s' % (cell(line, 0) or '', cell(line, 1) or '')


def players(lines):
    """逐列吐出 (列號, 整列 bytes),而且只吐真正的球員資料列。

    從第 1 列起跑,因為第 0 列是表頭;列號用的是「在整份名冊裡的位置」,
    這樣 cmd_set 寫回去時 lines[i] 才對得上,不會差一列。

    認資料列的方法是開頭那 9 個十六進位字元的紀錄編號,後面緊接一個逗號。
    空白列、檔尾殘留、被編輯器加進來的東西因此自動被濾掉。
    """
    for i, ln in enumerate(lines[1:], 1):
        if re.match(rb'\s*[0-9a-f]{9},', ln):
            yield i, ln


# ── 動作庫 ──────────────────────────────────────────────
def banks(gamedir, prefix):
    """讀 anims.big 的目錄,回傳 {編號: (位移, 長度)}。全程唯讀。

    BIGF 封裝檔的檔頭固定 16 bytes:
        +0x00  4 bytes  BIGF 這四個字
        +0x04  4 bytes  檔案總大小
        +0x08  4 bytes  目錄有幾項      big-endian
        +0x0C  4 bytes  目錄區結束位置  big-endian
    目錄從 +0x10 開始,一項是「8 bytes 的位移與長度,兩個都是 big-endian」
    再接一個以 0 結尾的檔名。檔名長度不固定,所以只能從第一項開始
    一項一項往前走,沒辦法直接跳到第 N 項。

    這裡不去讀 +0x04 那個總大小:走得完目錄就夠用了,
    而那一欄的位元組序在不同封裝檔之間並不一致(本站量過 295 個,
    288 個是 little-endian、7 個是 big-endian)。

    找不到檔案、或開頭不是 BIGF,就回傳空的 dict 與 None,不當成錯誤。
    這樣就算 anims.big 不在,--find 與 --set 照樣能跑,只是少了範圍檢查。
    """
    p = os.path.join(gamedir, 'data', 'anims', 'anims.big')
    if not os.path.isfile(p):
        return {}, None
    # 整包一次讀進記憶體:回傳的第二個值就是它,--show 要靠這份原始資料取內容。
    d = open(p, 'rb').read()
    if d[:4] != b'BIGF':
        return {}, None
    # 目錄項目數在 +0x08,big-endian。
    n = struct.unpack('>I', d[8:12])[0]
    off = 16
    out = {}
    for _ in range(n):
        # 每一項的前 8 bytes:資料在檔案裡的位移與長度,兩個都是 big-endian。
        o, s = struct.unpack('>II', d[off:off + 8])
        off += 8
        # 接著是以 0 結尾的檔名,長度不定,所以用掃的找結尾。
        a = off
        while d[off] != 0:
            off += 1
        nm = d[a:off].decode('latin-1')
        off += 1                       # 跳過那個結尾的 0,才是下一項的開頭
        # 只留姿勢動作庫,其餘一律不理。
        # 本站測試機這一份目錄共 730 項,其中 SIGB0000 到 SIGB0065 共 66 組、
        # SIGP0000 到 SIGP0058 共 59 組,合計 125 組,其餘是通用動作。
        m = re.fullmatch(prefix + r'(\d{4})\.axt', nm)
        if m:
            out[int(m.group(1))] = (o, s)
    return out, d


def bank_actions(blob, span):
    """SIGxxxx.axt 是純文字,[Files] 之後每行一個動作名。

    一份 .axt 長這樣:標籤自己一行,值在下一行用 TAB 縮排,區塊之間空一行,
    換行大多是 CRLF,但不是全部(244 個 .axt 裡 44 個只有 LF,SIGB0064 / SIGB0065 / SIGP0044 / SIGP0057 / SIGP0058 也在內;程式用 '\\n' 切、比對不錨行尾,兩種都吃得下)。下面照本站測試機 data/anims/anims.big 裡那份
    SIGB0014.axt(997 個位元組)的開頭抄下來,縮排的 TAB 這裡用空白呈現:

        [Version 0.03]
            1103890703      Dec 24 2004 04:18:23

        [Bank]
            SIGB0014

        [Directory]
            D:/mvp2004/artwork/anims

        [Files] 15
            b_ichirotobpreswing     1103875574      Dec 24 2004 00:06:14
            b_ichirowiggle          1103875574      Dec 24 2004 00:06:14
            ...

    動作名後面那個 10 位數是 Unix 時間戳記(1103875574 換算是 2004 年 12 月 24 日),
    對這支程式沒有用,但它是最好認的錨:要求「縮排 + 名字 + 10 位數」三件事
    同時成立才算數。注意 [Bank] 與 [Directory] 底下那兩行也是縮排的,
    擋掉它們的是後兩件:名字不合 [a-z]_ 開頭的樣式,後面也沒有 10 位數。
    這樣就不必去解析區塊結構。

    解碼用 latin-1,理由跟 cell() 一樣:它把 0 到 255 每個位元組一對一
    映成字元,永遠不會拋解碼錯誤。所以後面那個 'replace' 在這裡一次都不會
    觸發,留著不影響結果,但真正讓這支程式不會炸掉的是 latin-1 本身,
    不是它。
    真正的容錯在另一件事上:span 的長度是從目錄讀來的,萬一那份封裝檔的
    目錄被改壞而指到別的地方,這裡拿到的就是一堆解不出動作名的字元,
    下面的比對撈不到東西,回傳空清單,程式照樣跑完。
    這些 .axt 本身是純 ASCII:本站三處安裝(測試機的 data、歷史資料裡
    剛安裝好的原版、中文版備份的 data)的 anims.big 其實是同一顆檔案
    (sha256 開頭 9afd7728,三份逐位元組相同),量到 125 個 SIGB/SIGP 的
    .axt、合計 46,421 bytes,大於 127 的位元組 0 個。也就是說這是一份
    量測,不是三份互相印證。
    """
    o, s = span
    txt = blob[o:o + s].decode('latin-1', 'replace')
    acts = []
    # 用 '\n' 切就好。.axt 是 CRLF,切完每行尾巴會留一個 CR,
    # 但下面的比對不錨定行尾,留著不影響。
    for ln in txt.split('\n'):
        m = re.match(r'\s+([a-z]_[A-Za-z_0-9]+)\s+\d{10}', ln)
        if m:
            acts.append(m.group(1))
    return acts


# ── 指令 ────────────────────────────────────────────────
def resolve(lines, colname):
    """從表頭找出欄位編號,找不到就講一句人話。

    ⚠️ 這道檢查原本只有 cmd_list 有,cmd_find 與 cmd_set 沒有 ——
       於是表頭一有問題,那兩條路會把 None 丟進 %d,
       吐一整段 Python traceback。對「不會電腦也能跟著改」的讀者來說,
       那是最勸退的一種畫面。抽成共用函式,三條路一起用。

    回傳欄號(整數)。每一次操作都在最前面呼叫它,
    等於「先確認手上這個檔真的是名冊」再往下做任何事。
    """
    # lines[0] 是表頭那一列。欄號從表頭當場問出來,不寫死在程式裡。
    fld = header_field(lines[0], colname)
    if fld is None:
        raise DataError('表頭裡找不到 %s。這個檔可能不是名冊。' % colname)
    return fld


def cmd_list(gamedir, spec):
    """列出所有姿勢編號:哪些有動作庫、哪些有人在用、各幾人。全程唯讀。

    這是預設動作(什麼旗標都不加時跑的就是它),
    因為「先看有哪些可以選」是任何人動手之前的第一步。
    """
    rel, colname, prefix, label = spec
    lines = load(os.path.join(gamedir, 'data', rel))
    fld = resolve(lines, colname)
    # 第一遍:數名冊。每個編號被幾位球員用到,做成 {編號: 人數}。
    # 非數字的格一律跳過,壞掉一列不會讓整份統計垮掉。
    used = {}
    for _, ln in players(lines):
        v = cell(ln, fld)
        if v and v.isdigit():
            used[int(v)] = used.get(int(v), 0) + 1
    # 第二遍:數動作庫。兩份名單合起來才看得出「有庫沒人用」與
    # 「有人用卻沒有庫」兩種狀況,只看其中一邊都會漏。
    bk, _ = banks(gamedir, prefix)
    print('\n%s(第 %d 欄 %s)\n' % (label, fld, colname))
    print('  編號  動作庫        用的人數')
    print('  ' + '-' * 34)
    # 取聯集而不是只列動作庫:名冊裡若有指向不存在動作庫的編號,
    # 也要讓它出現在表上並標成「(沒有這一組)」,不然你永遠不會知道。
    allnum = sorted(set(used) | set(bk))
    for k in allnum:
        tag = '%s%04d' % (prefix, k) if k in bk else '(沒有這一組)'
        cnt = used.get(k, 0)
        mark = '  ← 沒人用' if k in bk and cnt == 0 else ''
        print('  %4d  %-14s %6d%s' % (k, tag, cnt, mark))
    print('\n  動作庫共 %d 組(%s0000–%s%04d)' % (len(bk), prefix, prefix, max(bk)) if bk else '')
    print('  名冊用到 %d 種,沒人用的 %d 種。全程唯讀。'
          % (len(used), len([k for k in bk if used.get(k, 0) == 0])))


def cmd_show(gamedir, spec, num):
    """把某一組動作庫裡的動作檔名列出來。完全不碰名冊,只讀 anims.big。

    這是「設下去之前先看看那是什麼」的唯一辦法。
    注意它列的是檔名不是畫面:本站沒有進遊戲一組一組看過。
    """
    rel, colname, prefix, label = spec
    bk, blob = banks(gamedir, prefix)
    if not bk:
        raise DataError('讀不到 data/anims/anims.big。')
    if num not in bk:
        raise DataError('沒有 %s%04d 這一組。用 --list 看有哪些。' % (prefix, num))
    acts = bank_actions(blob, bk[num])
    print('\n%s 編號 %d = %s%04d\n' % (label, num, prefix, num))
    print('  這一組有 %d 個動作:' % len(acts))
    for a in acts:
        print('    %s' % a)
    # 兩種命名風格要講不同的話。
    # 一種是描述手臂角度的(3q = 四分之三、hi/lo = 高低),那種看檔名就懂;
    # 另一種是 2005 年原版球員的名字,而你手上的名冊早就被重新指派過,
    # 那時候「編號 N 是誰」這個問題本身就不成立,只能問「長什麼樣」。
    if any(re.search(r'[a-z]_(?:st|hi|lo|3q|ov|sub|side)', a) for a in acts):
        print('\n  這一組的動作檔名是手臂角度的描述(例如 3q = 四分之三、hi/lo = 高低)。')
    else:
        print('\n  動作檔名是 2005 年原版球員的名字。這份名冊已經重新指派過,')
        print('  所以「編號 %d 的動作長什麼樣」講得通,「編號 %d 是誰」講不通。' % (num, num))


def cmd_find(gamedir, spec, who):
    """查某位球員現在用第幾號。唯讀,而且是改之前與改之後都該跑的那一步。"""
    rel, colname, prefix, label = spec
    lines = load(os.path.join(gamedir, 'data', rel))
    fld = resolve(lines, colname)
    # 比對用小寫、用「包含」而不是「完全相同」:
    # 使用者記得的通常只有姓,而且大小寫不一定打對。
    hit = [(i, ln) for i, ln in players(lines)
           if who.lower() in name_of(ln).lower()]
    if not hit:
        print('找不到名字含「%s」的球員。' % who)
        return
    print('\n找到 %d 位:\n' % len(hit))
    # 最多印 20 位。名冊有三千多列,只打一個字母會刷掉整個畫面,
    # 而使用者真正需要的是「把名字打完整一點」這句話。
    for i, ln in hit[:20]:
        print('  第 %5d 列  %-26s %s = %s' % (i, name_of(ln).strip(), label, cell(ln, fld)))
    if len(hit) > 20:
        print('  …(還有 %d 位,請把名字打完整一點)' % (len(hit) - 20))


def _atomic_write(path, payload):
    """把 payload 整份寫成 path:先寫暫存檔、落地、換權限,再 os.replace 換過去。

    直接開 path 來寫的話,中途按 Ctrl-C、磁碟滿、或沒有寫入權限,
    原檔會停在被截斷的狀態,而備份雖然還在,使用者不會知道發生了什麼。

    ⚠️ 2026-09-05:暫存檔名從固定的 path + '.tmp' 改成
       tempfile.mkstemp(dir=名冊所在資料夾)。理由見 _refuse_symlink() ——
       固定名字可以被人先放一個指向資料夾外面的符號連結佔走,
       open(..., 'wb') 會跟著它把外面那個檔截成 0。

    os.replace 換過去的是暫存檔的權限(mkstemp 給的是 0600),不是原檔的權限,
    所以要 copymode 把原檔的權限帶過來,不然名冊的權限會突然收緊。
    """
    _refuse_symlink(path, '名冊')
    d = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.' + os.path.basename(path) + '.tmp-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        _quiet_remove(tmp)
        raise
    try:
        shutil.copymode(path, tmp)
        _replace_and_record(tmp, path, 'write')
    except BaseException:
        _quiet_remove(tmp)
        raise


def _rollback_after_bad_write(path, bak, fresh_backup):
    """複驗沒通過之後怎麼收尾。一定回非 0。

    分兩種情況,差別在「那份 .bak 是不是這一次剛做的」:

    · 這一次剛做的 → 它就是動手前那一刻的樣子,當場還原回去最安全,
      而且還原本身還會再走一次備份把關與逐位元組比對。
    · 先前就存在 → 它是**更早**的原始狀態,可能還含著你上幾次改對的東西。
      拿它蓋回去會把那些一起蓋掉,所以這裡不自作主張,只把指令講清楚。
    """
    if fresh_backup:
        try:
            looks_like_roster(bak, os.path.basename(path))
            _restore_from_backup(bak, path)
        except BaseException as e:
            print('  ⚠ 想自動還原,但還原本身也失敗了:%s' % e)
            print('     %s 現在的內容不可信。' % os.path.basename(path))
            print('     請自己把 %s 複製回 %s。'
                  % (os.path.basename(bak), os.path.basename(path)))
            return 1
        print('  ✓ 已自動從剛才那份備份還原,%s 回到動手之前的樣子。'
              % os.path.basename(path))
        print('     這次的修改沒有生效 —— 這是刻意的,複驗沒過就不留下半信半疑的檔案。')
        return 1
    print('  ⚠ 這個檔先前就有備份,那份備份是更早的原始狀態,')
    print('     可能還含著你之前改對的東西,所以這裡不自動還原。')
    print('     確定要整份退回最早那一版再跑:--restore')
    return 1


def cmd_set(gamedir, spec, who, val, apply_it):
    """改一位球員的姿勢編號。apply_it 為假時只印預覽,不碰檔案。

    **回傳離開碼**(2026-09-05 第二輪稽核改的)。原本這個函式一律回 None,
    main() 一律回 0 —— 於是寫完之後的複驗就算整組不符,也只是印一行 ⚠,
    離開碼還是 0。誰把它接在 `&&` 後面、或寫成批次檔,都會以為成功了。
    現在複驗任何一項不符就回 1,而且能安全還原的當場還原。

    整條路的順序是刻意的:
      找欄位 → 檢查編號有沒有動作庫 → 找人(而且只准找到一位)
      → 印預覽 → (要 --apply 才往下) → 備份 → 寫暫存檔 → 換掉 → 重讀複驗。
    每一關都可能停在原地,而停在原地的時候硬碟一個位元組都沒動。
    """
    rel, colname, prefix, label = spec
    path = os.path.join(gamedir, 'data', rel)
    lines = load(path)
    fld = resolve(lines, colname)
    # 先問動作庫:設一個沒有對應動作庫的編號,遊戲進去才會出事,
    # 到那時候你已經不記得改過什麼了。所以在寫入之前就擋掉。
    # anims.big 讀不到時 bk 是空的,這道就自動跳過(少一道檢查,但還是能改)。
    bk, _ = banks(gamedir, prefix)
    if bk and val not in bk:
        raise DataError('編號 %d 沒有對應的動作庫(有的是 0–%d)。'
                        % (val, max(bk)))
    hit = [(i, ln) for i, ln in players(lines)
           if who.lower() in name_of(ln).lower()]
    if not hit:
        raise DataError('找不到名字含「%s」的球員。' % who)
    # 對到兩位以上就停手。這是保護不是錯誤:名冊裡真的有同名的人,
    # 實測連大谷翔平都有兩列。猜錯一位,改的就是別人。
    if len(hit) > 1:
        print('「%s」對到 %d 位球員,請打完整一點:' % (who, len(hit)))
        for i, ln in hit[:10]:
            print('   %s' % name_of(ln).strip())
        return 0
    i, ln = hit[0]
    old = cell(ln, fld)
    # 只換那一格的值,連「欄號 空格」這個前綴都原樣留著(m.group(1))。
    # count=1 是保險:同一列裡不會有第二格符合,但萬一有,也只動第一個。
    # 其他每一格、逗號、列尾都不碰,所以這一列的其餘內容逐位元組不變。
    new = re.sub(rb'((?:^|,)%d )[^,]*' % fld, lambda m: m.group(1) + str(val).encode(), ln, count=1)
    # 5 換成 14 會多一個位元組,這在純文字名冊裡是正常的,
    # 但先講出來,免得使用者看到檔案大小變了以為改壞。
    if len(new) != len(ln):
        print('  (這一行長度從 %d 變成 %d bytes —— 純文字名冊,長度本來就會變)'
              % (len(ln), len(new)))
    print('\n  球員   : %s' % name_of(ln).strip())
    print('  欄位   : 第 %d 欄 %s(%s)' % (fld, colname, label))
    print('  現在   : %s' % old)
    print('  要改成 : %d' % val)
    # 分水嶺就在這裡。上面全部是唯讀,下面才會動硬碟。
    if not apply_it:
        print('\n  這只是預覽,沒有動到檔案。確定要寫入請加 --apply')
        return 0
    # 備份只在「還沒有備份」時建。已經有的一律不覆蓋,
    # 因為那一份才是真正的原始狀態;改第二次時覆蓋掉它,就再也回不去了。
    bak = path + '.bak'
    # 動硬碟之前先把兩個位置都查一遍。名冊本身被換成符號連結,
    # os.replace 只會換掉連結,不會寫壞外面的檔;但那等於「你以為改了遊戲檔,
    # 其實改的是別的東西」,一樣不能放行。
    _refuse_symlink(path, '名冊')
    _refuse_symlink(bak, '備份檔')
    # lexists 不是 exists:空心的符號連結在 exists() 下回 False,
    # 那會走進「還沒有備份」這條路。上面那道已經擋掉了,這裡不留第二種說法。
    fresh_backup = not os.path.lexists(bak)
    if fresh_backup:
        _atomic_copy(path, bak)
        print('\n  ✓ 已備份原始檔:%s' % os.path.basename(bak))
    else:
        print('\n  ✓ 備份已存在,保留最早那一份:%s' % os.path.basename(bak))
    # ⚠️ 複驗要跟「寫入前」比,所以得先留一份。
    #    原本是直接改 lines[i] 再拿 lines 去跟讀回來的檔案比 ——
    #    兩邊當然一樣,diff 恆為 0,於是每一次「成功」的修改
    #    都會跳「⚠ 預期只有 1 行不同」的假警報,
    #    把一個其實已經改對的人叫去 --restore 把正確的修改還原掉。
    #    反過來真的寫壞時它也一樣印 0,什麼都抓不到。
    orig = list(lines)
    lines[i] = new
    # 用同一組 CRLF 接回去。切的時候用什麼,接的時候就用什麼,
    # 所以沒被動到的列連換行都跟原檔一模一樣。
    payload = b'\r\n'.join(lines)
    _atomic_write(path, payload)
    print('  ✓ 已寫入 %s' % os.path.basename(path))

    # 寫完重讀一次確認。從硬碟重新讀一次,不是拿記憶體裡的東西自己跟自己比
    # (上面那段警告就是在講這件事)。
    #
    # ⚠️ 2026-09-05 第二輪稽核:這一段原本只會印 ⚠,不影響離開碼 ——
    #    「宣稱是複驗、卻不參與成敗判定」等於沒有複驗。現在四個判準
    #    任何一個不成立就進 problems,而 problems 非空就不會回 0。
    raw_back = open(path, 'rb').read()
    check = raw_back.split(b'\r\n')
    problems = []
    diff = None
    # (一)最嚴的一道:整份讀回來要跟寫出去的逐位元組相同。
    #      下面三道其實都被這一道涵蓋,但它們講得出「哪裡不對」,留著給人看。
    if raw_back != payload:
        problems.append('讀回來的內容跟寫出去的不一樣(%d bytes vs %d bytes)'
                        % (len(raw_back), len(payload)))
    # (二)列數變了代表換行出事。
    if len(check) != len(lines):
        problems.append('列數不符(寫入 %d 列,讀回 %d 列)' % (len(lines), len(check)))
    else:
        # (三)目標那一列必須就是我們算出來的那一列。
        if check[i] != new:
            problems.append('第 %d 列不是預期的內容' % i)
        # (四)只准有一列不同 —— 不只一列代表寫錯位置。
        #      例外:把編號改成「他本來就是的那一個」時,檔案逐位元組沒變,
        #      diff 是 0,那是對的,不可以叫人去 --restore
        #      (--restore 會把打擊與投球兩邊整份蓋回去,
        #       照做的人會連另一邊先前正確的修改一起還原掉)。
        diff = sum(1 for a_, b_ in zip(orig, check) if a_ != b_)
        if diff == 0:
            if old != str(val):
                problems.append('一列都沒有變,但這次應該要有一列變')
        elif diff != 1:
            problems.append('預期只有 1 列不同,實際有 %d 列' % diff)
    if problems:
        print('\n  ❌ 複驗沒通過:')
        for why in problems:
            print('     · %s' % why)
        return _rollback_after_bad_write(path, bak, fresh_backup)
    print('  ✓ 複驗:%d 列不變,只有 %d 列不同' % (len(check), diff))
    if diff == 0:
        print('  (他本來就是 %s 號,檔案內容沒有變化,這是正常的)' % old)
    print('\n  要還原:--restore(會把打擊與投球兩邊都還原,不用加 --pitch)。')
    return 0


def looks_like_roster(backup, target_name):
    """覆蓋之前先確認這個備份真的是名冊,而且是**完整的**名冊。

    ⚠️ 本站另外三支工具的備份就躺在同一個資料夾,副檔名各不相同但都在旁邊。
       路徑打錯、或有人手動改過副檔名,就會拿別的東西蓋掉名冊。
       這道把關查的是「檔案裡真的有的東西」——
       開頭是數字欄位表、有 CRLF、表頭找得到 first_name 與 last_name,
       再加上兩道「有沒有被截斷」:整份要以 CRLF 收尾,最後一列的格數要對。
       (下面每一道各自寫著它是憑什麼那樣判斷的。)
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
    head_row = raw.split(b'\r\n', 1)[0]
    header = head_row.decode('latin-1', 'replace')
    if 'first_name' not in header or 'last_name' not in header:
        raise DataError('備份 %s 的表頭找不到 first_name / last_name,不像名冊,不敢覆蓋。'
                        % os.path.basename(backup))
    # ── 半截備份的把關(_restore_from_backup 那條通用地板擋不到的那一段)──
    # 通用地板只擋「小於正本的一半」。實測把 840,643 bytes 的名冊備份截成
    # 500,000 bytes(59.5%)去 --restore,三道舊把關全過、印「✓ 已還原」、
    # exit 0,正本從 3,247 列變成 1,931 列,最後一列停在半截。
    # 名冊有格式可以驗,就不該只靠地板:
    #   1. 整份一定以 CRLF 收尾(量過測試機與歷史資料裡 34 份 attrib.dat /
    #      pitcher.dat,34 份都是;這支程式自己也是用 b'\r\n'.join() 接回去的)。
    #   2. 資料列的格數固定是「表頭格數 + 1」(資料列開頭多一個紀錄編號),
    #      那 34 份裡每一份的每一列都成立。截在半路的那一列格數一定變少。
    # ⚠️ 誠實講清楚:剛好斷在某一列結尾 CRLF 上的截斷,這兩道都看不出來
    #    (每一列都完整,只是少了後面幾百列),那種還是只有通用地板擋得住。
    if not raw.endswith(b'\r\n'):
        raise DataError('備份 %s 沒有以 CRLF 收尾,最後一列是半截的 —— '
                        '這份備份被截斷了,不敢拿它覆蓋 %s。'
                        % (os.path.basename(backup), target_name))
    # 用 rfind 取最後一列就好,不要 split 整份檔案(名冊雖然只有幾百 KB,
    # 但這樣就不必為了一道檢查把整份切成幾千個物件)。
    end = raw.rfind(b'\r\n')                    # 收尾那個 CRLF
    prev = raw.rfind(b'\r\n', 0, end)           # 它前面那一個
    last = raw[prev + 2:end] if prev >= 0 else raw[:end]
    if re.match(rb'\s*[0-9a-f]{9},', last):
        want = len(head_row.split(b',')) + 1
        got = len(last.split(b','))
        if got != want:
            raise DataError('備份 %s 的最後一列只有 %d 格,應該有 %d 格 —— '
                            '這份備份被截斷了,不敢拿它覆蓋 %s。'
                            % (os.path.basename(backup), got, want, target_name))


def cmd_restore(gamedir, _spec=None):
    """還原**兩個**檔案,不管使用者有沒有加 --pitch。

    這裡刻意不看 --pitch:改打擊姿勢動 attrib.dat、改投球姿勢動 pitcher.dat,
    使用者心裡想的是「把這支工具做過的事收回去」,不是「收回其中一半」。
    早期版本讓 --restore 跟著 --pitch 走,結果是:
    改了投球姿勢之後照教學打 --restore,會得到「找不到 attrib.dat 的備份」——
    那句話是假的(備份就在旁邊叫 pitcher.dat.bak),而且改動原封不動留著。
    """
    done, missing = [], []
    # 兩個檔是一個一個做的,做不到「要嘛兩個都還原、要嘛一個都不還原」
    # (第二個檔的備份壞掉時,第一個檔已經扶正了,收不回來)。
    # 做不到全有全無,那就照規矩至少誠實:失敗時逐檔講「已還原 / 沒還原」、
    # 離開碼非 0、把下一步講清楚。這一整份清單先算好,收尾時要用。
    everything = [(os.path.basename(os.path.join(gamedir, 'data', rel)), label)
                  for rel, _c, _p, label in (BAT, PIT)]
    try:
        _restore_both(gamedir, done, missing)
    except BaseException:
        # 接的是 BaseException 不是 Exception —— Ctrl-C 要走同一條誠實路徑。
        # 只接 Exception 的話,按了 Ctrl-C 的人只看得到檔尾那段通用訊息,
        # 不知道兩個檔各自還原了沒有。
        print('\n  ⚠ 還原中途停下來了。逐檔狀況:')
        for n, lab in everything:
            print('     · %s(%s):%s'
                  % (n, lab, '已經還原完成。' if (n, lab) in done else '沒有還原。'))
        print('     把下面那個原因排掉之後再跑一次 --restore,'
              '已經還原好的那一個再做一次也不會有事。')
        raise
    if not done:
        raise DataError('兩個檔都找不到備份(%s)。沒有備份就沒辦法還原。'
                        % '、'.join('%s.bak' % n for n, _ in missing))
    for n, lab in missing:
        print('  %s 沒有備份 —— 代表這支工具沒有改過它的%s,不用還原。' % (n, lab))


def _restore_both(gamedir, done, missing):
    """cmd_restore 真正做事的那一半。抽出來只為了讓上面那段收尾看得清楚。

    做完一個就 append 到 done —— 中途停下來的話,上面那段靠它逐檔講話。
    """
    # 兩個檔各走一次。沒有 .bak 的那一個不算失敗,只是「這支工具沒改過它」。
    for rel, colname, prefix, label in (BAT, PIT):
        path = os.path.join(gamedir, 'data', rel)
        bak = path + '.bak'
        # lexists 不是 exists:.bak 如果是一個指向不存在檔案的符號連結,
        # exists() 會回 False,這個檔就會被歸到「沒有備份、不用還原」——
        # 那句話是假的,而且會讓一個明顯不對勁的狀況靜靜地過去。
        # 用 lexists 認出「那裡有東西」,再讓下面的把關去講它哪裡不對。
        if os.path.lexists(bak):
            # 三道把關,順序有意義:
            # 最先擋符號連結 —— 它要排在**讀第一個位元組之前**。
            # 下面那道會把備份整份讀進來驗格式,備份如果是連結,
            # 驗到的是連結指向的那個檔,而不是這裡真正躺著的東西;
            # 正本如果是連結,覆蓋就寫到遊戲資料夾外面去了。
            _refuse_symlink(bak, '備份')
            _refuse_symlink(path, '要還原的檔案')
            # 再問「這份備份是不是名冊、而且整份寫完了」(名冊自己的格式),
            # 最後交給通用的那道(0 bytes、封裝檔/語系檔/執行檔的結構、通用地板)。
            # 三道都過了,_restore_from_backup 裡面才會真的覆蓋,
            # 而那個覆蓋本身也是先寫暫存檔(mkstemp 取的名字)再改名。
            looks_like_roster(bak, os.path.basename(path))
            _restore_from_backup(bak, path)
            # 當場印,不要等兩個檔都做完 —— 第二個檔的備份如果是壞的,
            # 把關會在這一行之後停下整支程式,那時使用者只看得到錯誤訊息,
            # 不會知道第一個檔其實已經還原了。
            print('✓ 已還原 %s(%s)' % (os.path.basename(path), label))
            done.append((os.path.basename(path), label))
        else:
            missing.append((os.path.basename(path), label))


def main():
    """解析指令列,派工給某一個 cmd_*。回傳值就是離開碼。

    只有這裡認識 argparse;cmd_* 全部只收普通參數,
    所以那些函式可以單獨拿去測,不必假造一組指令列。
    """
    ap = argparse.ArgumentParser(description='MVP Baseball 2005 換打擊/投球姿勢')
    # nargs='?' 是為了 --selftest 一個參數都不用給。
    # 少了 gamedir 又沒有 --selftest 的話,上面會印說明並回 2 ——
    # 跟原本 argparse 自己報「缺少參數」的離開碼一樣,沒有變。
    ap.add_argument('gamedir', nargs='?',
                    help='遊戲資料夾(裡面要有 data 這個子資料夾)')
    ap.add_argument('--pitch', action='store_true', help='改投球姿勢(預設改打擊姿勢)')
    ap.add_argument('--list', action='store_true', help='列出所有編號、動作庫、用的人數')
    ap.add_argument('--show', type=int, metavar='編號', help='看某一組動作庫裡有哪些動作')
    ap.add_argument('--find', metavar='名字', help='查某位球員現在用第幾號')
    ap.add_argument('--set', nargs=2, metavar=('球員', '編號'), help='改成某個編號')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原')
    ap.add_argument('--selftest', action='store_true',
                    help='自我測試,完全不碰遊戲檔')
    args = ap.parse_args()

    # --selftest 排在最前面,因為它不需要遊戲資料夾,
    # 也不該被下面那道「data 資料夾在不在」擋住。
    if args.selftest:
        return selftest()
    if not args.gamedir:
        ap.print_help()
        return 2

    # --pitch 只在這一行起作用:它決定後面全部用哪一張規格表。
    spec = PIT if args.pitch else BAT
    # 最早、最便宜的一道檢查。第一個參數給錯資料夾是最常見的失誤,
    # 與其讓後面丟「打不開 attrib.dat」,不如在這裡直接講清楚。
    if not os.path.isdir(os.path.join(args.gamedir, 'data')):
        print('❌ %s 底下沒有 data 資料夾。第一個參數要給遊戲資料夾。' % args.gamedir)
        return 2

    # 派工順序不是隨便排的:--restore 排第一,
    # 這樣「我改壞了想救回來」永遠不會被其他旗標卡住。
    if args.restore:
        cmd_restore(args.gamedir)
    elif args.list:
        cmd_list(args.gamedir, spec)
    elif args.show is not None:
        cmd_show(args.gamedir, spec, args.show)
    elif args.find:
        cmd_find(args.gamedir, spec, args.find)
    elif args.set:
        who, val = args.set
        if not val.isdigit():
            print('❌ 第二個參數要是數字編號,你給的是「%s」' % val)
            return 2
        # cmd_set 會回離開碼:複驗沒過就是非 0。這裡不可以吃掉它,
        # 不然「寫壞了」跟「寫好了」在批次檔裡長得一模一樣。
        return cmd_set(args.gamedir, spec, who, int(val), args.apply)
    else:
        # 什麼都沒指定就當成 --list,順便把另外三條路指出來。
        # 對不會電腦的人來說,「跑了但什麼都沒發生」比報錯更難處理。
        cmd_list(args.gamedir, spec)
        print('\n  想看某一組動作:--show <編號>')
        print('  想查某位球員  :--find <名字>')
        print('  想改          :--set <名字> <編號>(加 --apply 才真的寫)')
    return 0


# ── 自我測試 ────────────────────────────────────────────
def _fake_roster(stance=5):
    """造一份最小但格式合法的名冊,只給 --selftest 用,不碰任何遊戲檔。

    格式跟真名冊一樣:表頭是「欄號 空格 欄位名」用逗號隔開,
    資料列開頭多一個 9 個十六進位字元的紀錄編號,整份 CRLF 分行、CRLF 收尾。
    欄號故意用 0 / 1 / 2 / 28 這種不連續的排法 —— 這支程式本來就是
    照欄位名字從表頭問欄號的,測試也該用「欄號不是 0,1,2,3…」的資料餵它。
    """
    head = (b'0 first_name,1 last_name,2 playerattrib_jerseynum,'
            b'28 playerattrib_battingstance')
    rows = [
        b'00000000a,0 Shohei,1 Ohtani,2 17,28 %d' % stance,
        b'00000000b,0 Ichiro,1 Suzuki,2 51,28 3',
        b'00000000c,0 Barry,1 Bonds,2 25,28 7',
    ]
    return b'\r\n'.join([head] + rows) + b'\r\n'


def selftest():
    """--selftest:在系統暫存資料夾自己造一份名冊來測,完全不碰遊戲檔。

    分兩半,兩半都要有:

    · **正向**:預覽真的不寫、--apply 真的改對、備份真的逐位元組相同、
      --restore 真的回得去。少了正向,底下的餌可能只是「整支都壞了」才過的
      (2026-08-29 本站踩過:防線壞掉,測試照樣全綠)。
    · **餌**:每一道守門都先做出它該擋的那個情況,確認它擋得下來,
      而且該保持原狀的東西一個位元組都沒動。

    這一輪(2026-09-05 第二輪唯讀稽核)新增的守門各有一個餌:
      · 猜得到的暫存檔名被人放了指向資料夾外面的符號連結 → 外面的檔不可以被動到
      · 名冊本身是符號連結 → --set --apply 要拒絕
      · 備份是符號連結 → --restore 要拒絕
      · 還原寫到一半失敗(把 os.replace 換成會丟例外的)→ 正本要原封不動,
        而且不可以留下沒扶正的暫存檔
      · 寫出去的內容被動了手腳 → 複驗要抓到、離開碼非 0、而且自動還原回去
      · 還原時讀回來的跟寫出去的對不上(模擬壞軌的碟)→ 不可以換過去
    """
    # ── 不准在 python -O 底下假綠(2026-09-06 第三輪,全站統一)───────
    # -O 會把 assert 整句拿掉。這一支的檢查是 ck() 自己 raise AssertionError,
    # -O 拿不掉它 —— 但這道守門照樣要有:全站每一支的 --selftest 都得在
    # -O 底下講同一句話,而且哪天有人在這裡補一句普通的 assert,
    # 沒有這道守門就會靜靜地變成假綠。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2

    import builtins
    import contextlib
    import io as _io

    state = {'n': 0, 'bait': 0}

    def ck(cond, msg):
        state['n'] += 1
        if not cond:
            raise AssertionError(msg)

    def ck_bait(cond, msg):
        """跟 ck 一樣,只是這一條是餌:它驗的是「該擋的有沒有被擋下來」。"""
        state['bait'] += 1
        ck(cond, msg)

    def must_raise(fn, exc, msg):
        """做一件必須失敗的事。沒失敗就是防線失效。

        被擋下來之前印出來的字(例如 --set 的預覽)一律吞掉,
        不然 --selftest 的輸出會混進半截的操作畫面,看的人分不出那是不是失敗。
        """
        state['n'] += 1
        state['bait'] += 1
        try:
            with quiet():
                fn()
        except exc:
            return
        raise AssertionError(msg)

    def quiet():
        return contextlib.redirect_stdout(_io.StringIO())

    def mkgame(stance=5):
        d = tempfile.mkdtemp(prefix='mvp_edit_stance_selftest_')
        db = os.path.join(d, 'data', 'database')
        os.makedirs(db)
        p = os.path.join(db, 'attrib.dat')
        raw = _fake_roster(stance)
        with open(p, 'wb') as f:
            f.write(raw)
        return d, p, raw

    tmpdirs = []
    try:
        # ── 正向 1:讀得懂自己造的名冊 ────────────────────────
        d, p, raw = mkgame(); tmpdirs.append(d)
        lines = load(p)
        ck(resolve(lines, BAT[1]) == 28, '表頭問不出 battingstance 的欄號')
        ck([name_of(ln).strip() for _, ln in players(lines)]
           == ['Shohei Ohtani', 'Ichiro Suzuki', 'Barry Bonds'],
           '球員列讀出來的名字不對')
        ck(cell(players(lines).__next__()[1], 28) == '5', '取不到姿勢編號')

        # ── 正向 2:沒有 --apply 就是一個位元組都不寫 ──────────
        with quiet():
            rc = cmd_set(d, BAT, 'Ohtani', 14, False)
        ck(rc == 0, '預覽應該回 0')
        ck(open(p, 'rb').read() == raw, '預覽竟然動到了檔案')
        ck(not os.path.lexists(p + '.bak'), '預覽不該產生備份')

        # ── 正向 3:--apply 改對、備份逐位元組相同、複驗過、回 0 ──
        # 順便驗權限。三個寫入點都是「寫暫存檔再改名」,而 mkstemp 造出來的
        # 暫存檔權限是 **0600** —— 所以這裡刻意把名冊設成 0640(跟 0600 不同),
        # 少了 copystat / copymode 的話,權限會在使用者不知情的狀況下被換成 0600。
        # 設 0600 是驗不出來的:它跟 mkstemp 的預設一樣,壞了也看不出來。
        os.chmod(p, 0o640)
        del _WRITTEN[:]
        with quiet():
            rc = cmd_set(d, BAT, 'Ohtani', 14, True)
        ck(rc == 0, '正常寫入應該回 0')
        ck(open(p + '.bak', 'rb').read() == raw, '備份跟原檔不是逐位元組相同')
        after = open(p, 'rb').read()
        ck(cell(load(p)[1], 28) == '14', '姿勢編號沒有改成 14')
        ck(sum(1 for a, b in zip(raw.split(b'\r\n'), after.split(b'\r\n')) if a != b) == 1,
           '只該有一列不同')
        # Ctrl-C 那句話靠這份清單決定講什麼,所以清單本身要驗。
        ck([w for w, _ in _WRITTEN] == ['backup', 'write'],
           '寫入紀錄不對,Ctrl-C 的訊息會講錯話')
        ck(_INFLIGHT == [],
           '跑完了還留著「正在換」的登記,Ctrl-C 的訊息會多講一句不存在的事')
        ck_bait(os.stat(p).st_mode & 0o777 == 0o640,
                '寫入之後名冊的權限被換掉了(%s)' % oct(os.stat(p).st_mode & 0o777))
        ck_bait(os.stat(p + '.bak').st_mode & 0o777 == 0o640,
                '備份的權限沒跟著原檔走(%s)' % oct(os.stat(p + '.bak').st_mode & 0o777))

        # ── 正向 4:--restore 逐位元組回得去 ────────────────────
        # 把備份的權限改成跟正本不一樣,才驗得出「還原之後權限跟著正本走」——
        # 兩邊一樣的話,copymode 那一行拿掉也看不出差別,餌就是啞的。
        os.chmod(p + '.bak', 0o600)
        with quiet():
            cmd_restore(d)
        ck(open(p, 'rb').read() == raw, '還原之後應該逐位元組回到原本的樣子')
        ck_bait(os.stat(p).st_mode & 0o777 == 0o640,
                '還原之後名冊的權限被換掉了(%s)' % oct(os.stat(p).st_mode & 0o777))

        # ── 餌 1:猜得到的暫存檔名被人放了指向外面的符號連結 ──────
        #   舊寫法是 dst+'.part' / path+'.tmp' / dst+'.restore-part',
        #   三個名字都猜得到。這裡先把它們放成指向資料夾外面的連結,
        #   跑完整套備份 → 寫入 → 還原,外面那三個檔必須一個位元組都沒變。
        d2, p2, raw2 = mkgame(); tmpdirs.append(d2)
        outside = tempfile.mkdtemp(prefix='mvp_edit_stance_outside_'); tmpdirs.append(outside)
        victims = {}
        for nm in ('attrib.dat.bak.part', 'attrib.dat.tmp', 'attrib.dat.restore-part'):
            v = os.path.join(outside, nm + '.victim')
            with open(v, 'wb') as f:
                f.write(b'DO NOT TOUCH ME\n' * 64)
            victims[nm] = (v, open(v, 'rb').read())
            os.symlink(v, os.path.join(os.path.dirname(p2), nm))
        del _WRITTEN[:]
        with quiet():
            rc = cmd_set(d2, BAT, 'Bonds', 14, True)
            cmd_restore(d2)
        ck(rc == 0, '有人放了誘餌連結,但正常流程還是該跑完')
        for nm, (v, want) in victims.items():
            ck_bait(open(v, 'rb').read() == want,
                    '資料夾外面的 %s 被寫壞了 —— 暫存檔跟著符號連結走了' % nm)
            ck_bait(os.path.islink(os.path.join(os.path.dirname(p2), nm)),
                    '誘餌連結 %s 不見了,這個餌下次就咬不到人' % nm)
        ck(open(p2, 'rb').read() == raw2, '還原之後應該逐位元組回到原本的樣子')

        # ── 餌 2:名冊本身是符號連結 → --set --apply 要拒絕 ────────
        d3 = tempfile.mkdtemp(prefix='mvp_edit_stance_selftest_'); tmpdirs.append(d3)
        os.makedirs(os.path.join(d3, 'data', 'database'))
        real = os.path.join(outside, 'real_attrib.dat')
        with open(real, 'wb') as f:
            f.write(_fake_roster())
        keep = open(real, 'rb').read()
        os.symlink(real, os.path.join(d3, 'data', 'database', 'attrib.dat'))
        must_raise(lambda: cmd_set(d3, BAT, 'Ohtani', 14, True), DataError,
                   '名冊是符號連結竟然還寫得下去 —— 防線失效')
        ck_bait(open(real, 'rb').read() == keep, '被擋下來的時候外面的檔不可以被動到')

        # ── 餌 2b:.bak 是符號連結 → --set --apply 也要拒絕 ─────────
        #   餌 3 驗的是 --restore 那條路。寫入這條路自己也會碰 .bak
        #   (第一次寫入之前要先建備份),所以它也要有自己的餌 ——
        #   不然「所有要寫的位置都擋符號連結」這句話只有一半是驗過的。
        d3b, p3b, raw3b = mkgame(); tmpdirs.append(d3b)
        outside_bak = os.path.join(outside, 'not_a_backup.dat')
        with open(outside_bak, 'wb') as f:
            f.write(b'I AM NOT A BACKUP\n' * 32)
        keep_bak = open(outside_bak, 'rb').read()
        os.symlink(outside_bak, p3b + '.bak')
        must_raise(lambda: cmd_set(d3b, BAT, 'Ohtani', 14, True), DataError,
                   '.bak 是符號連結,備份竟然還寫得下去 —— 防線失效')
        ck_bait(open(outside_bak, 'rb').read() == keep_bak,
                '被擋下來的時候資料夾外面那個檔不可以被動到')
        ck_bait(open(p3b, 'rb').read() == raw3b,
                '被擋下來的時候名冊不可以被動到')

        # ── 餌 3:備份是符號連結 → --restore 要拒絕 ────────────────
        d4, p4, raw4 = mkgame(); tmpdirs.append(d4)
        os.symlink(real, p4 + '.bak')
        must_raise(lambda: cmd_restore(d4), DataError,
                   '備份是符號連結竟然還原得下去 —— 防線失效')
        ck_bait(open(p4, 'rb').read() == raw4, '被擋下來的時候正本不可以被動到')

        # ── 餌 3b:備份是「空心的」符號連結(指向不存在的東西)────────
        #   這一條專門盯 os.path.lexists:用 exists() 的話它回 False,
        #   這個檔會被歸到「沒有備份、不用還原」—— 話講錯了,而且一個
        #   明顯不對勁的狀況就這樣靜靜地過去。兩種寫法都會丟 DataError,
        #   所以要驗**訊息**,不能只驗有沒有丟例外。
        d4b, p4b, raw4b = mkgame(); tmpdirs.append(d4b)
        os.symlink(os.path.join(outside, 'this_file_does_not_exist'), p4b + '.bak')
        try:
            with quiet():
                cmd_restore(d4b)
        except DataError as e:
            state['n'] += 1
            state['bait'] += 1
            ck_bait('符號連結' in str(e),
                    '空心的符號連結被當成「沒有備份」了,講出來的話是錯的:%s' % e)
        else:
            raise AssertionError('備份是空心的符號連結,竟然沒有被擋下來')
        ck_bait(open(p4b, 'rb').read() == raw4b, '被擋下來的時候正本不可以被動到')

        # ── 餌 4:還原寫到一半失敗 → 正本原封不動、不留半截暫存檔 ────
        d5, p5, raw5 = mkgame(); tmpdirs.append(d5)
        with open(p5 + '.bak', 'wb') as f:
            f.write(_fake_roster(9))
        with open(p5, 'wb') as f:
            f.write(_fake_roster(14))
        live_before = open(p5, 'rb').read()
        real_replace = os.replace
        os.replace = lambda a, b: (_ for _ in ()).throw(OSError('bait: 磁碟在這一刻壞掉'))
        try:
            must_raise(lambda: cmd_restore(d5), OSError,
                       '還原途中失敗竟然沒有把例外丟出來')
        finally:
            os.replace = real_replace
        ck_bait(open(p5, 'rb').read() == live_before,
                '還原失敗之後正本被動到了 —— 這正是最不能發生的事')
        leftovers = [f for f in os.listdir(os.path.dirname(p5)) if '.restore-' in f]
        ck_bait(leftovers == [], '還原失敗留下沒扶正的暫存檔:%s' % leftovers)

        # ── 餌 5:寫出去的內容被動手腳 → 複驗要抓到 + 非 0 + 自動還原 ──
        #   把 _atomic_write 換成「少寫一列」與「多改一列」兩種壞法,
        #   兩種都必須被複驗抓到。這一條驗的是離開碼,不是例外。
        g = globals()
        real_write = g['_atomic_write']

        def drop_a_line(path, payload):
            rows = payload.split(b'\r\n')
            real_write(path, b'\r\n'.join(rows[:-2] + rows[-1:]))

        def touch_another_line(path, payload):
            rows = payload.split(b'\r\n')
            rows[2] = rows[2].replace(b'28 3', b'28 8')
            real_write(path, b'\r\n'.join(rows))

        for bad, tag in ((drop_a_line, '少寫一列'), (touch_another_line, '多改一列')):
            d6, p6, raw6 = mkgame(); tmpdirs.append(d6)
            g['_atomic_write'] = bad
            try:
                with quiet():
                    rc = cmd_set(d6, BAT, 'Ohtani', 14, True)
            finally:
                g['_atomic_write'] = real_write
            ck_bait(rc != 0, '複驗沒抓到「%s」,離開碼還是 %s —— 防線失效' % (tag, rc))
            ck_bait(open(p6, 'rb').read() == raw6,
                    '複驗抓到「%s」之後沒有自動還原,檔案停在壞掉的狀態' % tag)

        # ── 餌 6:還原時「寫出去的」與「讀回來的」對不上 → 不可以換過去 ──
        #   模擬一顆讀寫對不起來的碟(壞軌、外接碟接觸不良):
        #   只攔截還原用的那個暫存檔的讀取,讓它少回一個位元組。
        #   sha256 一比就不同,這時候寧可不換,讓正本維持現狀。
        d8, p8, raw8 = mkgame(); tmpdirs.append(d8)
        with open(p8 + '.bak', 'wb') as f:
            f.write(_fake_roster(9))
        live8 = open(p8, 'rb').read()
        real_open = builtins.open

        def flaky_open(path, mode='r', *a, **k):
            if 'b' in mode and 'r' in mode and \
                    os.path.basename(str(path)).startswith('.attrib.dat.restore-'):
                with real_open(path, 'rb') as f:
                    return _io.BytesIO(f.read()[:-1])
            return real_open(path, mode, *a, **k)

        builtins.open = flaky_open
        try:
            must_raise(lambda: cmd_restore(d8), SystemExit,
                       '讀回來跟寫出去對不上,竟然照樣換過去了 —— 防線失效')
        finally:
            builtins.open = real_open
        ck_bait(open(p8, 'rb').read() == live8,
                '讀回來對不上的時候正本不可以被動到')
        ck_bait([f for f in os.listdir(os.path.dirname(p8)) if '.restore-' in f] == [],
                '對不上之後留下沒扶正的暫存檔')

        # ── 餌 7:半截的備份要被擋下來(2026-08-30 那道的迴歸測試)──────
        d7, p7, raw7 = mkgame(); tmpdirs.append(d7)
        with open(p7 + '.bak', 'wb') as f:
            f.write(raw7[:len(raw7) // 2])
        must_raise(lambda: cmd_restore(d7), DataError,
                   '半截的備份竟然還原得下去 —— 防線失效')
        ck_bait(open(p7, 'rb').read() == raw7, '被擋下來的時候正本不可以被動到')

        # ── 餌 8:Ctrl-C 真的被押到「換名 + 登記」那一段外面 ──────────
        #   這裡不真的殺自己一次(os.kill 在 Windows 上的語義跟 POSIX 不同,
        #   放進讀者會跑的 --selftest 太脆),改成直接驗三件事:
        #   進去之後 SIGINT 的處理器換成我們的、收到訊號時 body 照樣跑完、
        #   離開之後才把 KeyboardInterrupt 丟出來而且原本的處理器裝回去。
        #   真的殺一次的版本在稽核紀錄裡(變體檔 T1 / T2),不放進這支腳本。
        before_handler = signal.getsignal(signal.SIGINT)
        seq = []
        try:
            with _NoInterrupt() as ni:
                # 用 __func__ 比,不要用 `is`:每次取 ni._remember 都會現做一個
                # 新的 bound method 物件,`is` 一定不成立 —— 那是量錯不是防線壞了。
                ck_bait(getattr(signal.getsignal(signal.SIGINT), '__func__', None)
                        is _NoInterrupt._remember,
                        '_NoInterrupt 沒有真的接管 SIGINT,「押後」是假的')
                ni._remember(signal.SIGINT, None)     # 等同「這一刻按了 Ctrl-C」
                seq.append('body 跑完了')
        except KeyboardInterrupt:
            seq.append('離開之後才丟出來')
        ck_bait(seq == ['body 跑完了', '離開之後才丟出來'],
                'Ctrl-C 沒有被押到區段外面:%s' % seq)
        ck_bait(signal.getsignal(signal.SIGINT) is before_handler,
                '離開之後沒有把原本的 SIGINT 處理器裝回去')

        # ── 餌 9:被中斷時講的那三句話要跟硬碟上的狀態對得上 ──────────
        #   三態各驗一次。最要緊的是中間那一態:換名做到一半被打斷,
        #   絕對不可以講成「沒有改到任何檔案」。
        def _say():
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                _interrupt_report()
            return buf.getvalue()

        del _WRITTEN[:]
        del _INFLIGHT[:]
        ck_bait('沒有改到任何檔案' in _say(), '兩份清單都是空的,該說沒動到')
        _INFLIGHT.append(('write', 'attrib.dat'))
        say = _say()
        ck_bait('沒有改到任何檔案' not in say and '正在替換' in say and '--restore' in say,
                '中斷時卡在換名那一步,竟然講成「沒動到」:%s' % say)
        del _INFLIGHT[:]
        _WRITTEN.append(('write', 'attrib.dat'))
        say = _say()
        ck_bait('沒有改到任何檔案' not in say and '已經改好了' in say and '--restore' in say,
                '已經換過去了,竟然講成「沒動到」:%s' % say)
        del _WRITTEN[:]
    finally:
        for d in tmpdirs:
            shutil.rmtree(d, ignore_errors=True)

    print('自我測試:全部通過(%d 道檢查,其中 %d 道是餌)'
          % (state['n'], state['bait']))
    return 0



def _interrupt_report():
    """被 Ctrl-C 打斷時把「硬碟上真正發生了什麼」講出來。三態,不可以講錯。

    ⚠️ 2026-09-05 第二輪稽核:原本無條件說「沒有改到任何檔案」。
       Ctrl-C 如果落在 os.replace **之後**(複驗、印字都還在跑),
       那句話就是假的 —— 而讀者會照著它去做別的事。
    ⚠️ 2026-09-06 第三輪:改照三態講話。
       _WRITTEN 有 → 已經換過去了;_INFLIGHT 有 → 中斷時正卡在換名那一步,
       換沒換過去不確定(見 _replace_and_record 的 (b));兩個都空 → 真的沒動到。
       抽成函式是為了 --selftest 驗得到它講的話,不必真的殺一次自己。
    """
    print('\n已中斷。')
    if not _WRITTEN and not _INFLIGHT:
        print('沒有改到任何檔案。')
        return
    for what, path in _WRITTEN:
        if what == 'backup':
            print('  · 已經建立備份 %s(這是新檔,遊戲檔本身沒被動到)。' % path)
        elif what == 'write':
            print('  · ⚠ %s 已經改好了 —— 這一步是原子的,'
                  '檔案是完整的舊版或完整的新版,不會是半截。' % path)
        elif what == 'restore':
            print('  · %s 已經從備份還原完成(同樣是原子的)。' % path)
    for what, path in _INFLIGHT:
        if what == 'backup':
            print('  · 中斷時正在建立備份 %s —— 建好了沒有這裡不敢說死;'
                  '不過那是新檔,遊戲檔本身沒被動到。' % path)
            continue
        print('  · ⚠ 中斷時正在替換 %s —— 換過去了沒有,這裡不敢說死。' % path)
        print('     這一步本身是原子的(os.replace),所以那個檔要嘛是完整的舊版、'
              '要嘛是完整的新版,不會是半截;')
        print('     但到底是哪一版,請用 --restore 還原,或自己拿 .bak 比對一次。')
    if any(w == 'write' for w, _ in _WRITTEN) or \
            any(w in ('write', 'restore') for w, _ in _INFLIGHT):
        print('  要退回動手之前的樣子:--restore')


# 離開碼:0 成功、1 使用者做錯了什麼(DataError)或環境不讓寫(OSError)、
# 2 參數給錯、130 被 Ctrl-C 中斷。
# DataError 與 OSError 會被收成幾行中文。其他例外故意讓它印出完整 traceback,
# 因為那才代表程式自己有問題,回報時需要那一整段。
if __name__ == '__main__':
    try:
        sys.exit(main())
    except DataError as e:
        print('\n❌ %s' % e)
        sys.exit(1)
    except KeyboardInterrupt:
        _interrupt_report()
        sys.exit(130)
    except OSError as e:
        # 權限不足、磁碟滿、外接碟被拔掉 —— 這些是「你的環境」的問題,
        # 不是這支程式自己壞了,不該讓讀者看到一整段 traceback
        # (上面那段分類就寫著 traceback 代表程式有問題,會把人誤導)。
        print('\n❌ 讀寫檔案失敗:%s' % e)
        print('   常見原因:遊戲資料夾是唯讀的(裝在 Program Files 底下,')
        print('   要用系統管理員身分開命令提示字元)、磁碟空間不足、外接碟被拔掉。')
        sys.exit(1)

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
