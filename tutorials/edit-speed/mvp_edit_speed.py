#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_edit_speed.py — 修改 MVP Baseball 2005 球員的跑壘速度

這支腳本只動 data/database/attrib.dat（800 KB 純文字），
而且只寫 playerattrib_speed 這一欄。
（第幾欄由檔案第一行的表頭決定，不同名冊排法不一樣：
  本站測試機是第 22 欄，剛安裝好的原版是第 23 欄。不要記欄號。）
其他欄位一律「唯讀」，就算你指定也不會寫。

用法（先預覽，確定了再加 --apply）：

    python3 mvp_edit_speed.py "<遊戲資料夾>"
    python3 mvp_edit_speed.py "<遊戲資料夾>" --find Trout
    python3 mvp_edit_speed.py "<遊戲資料夾>" --set Trout 90
    python3 mvp_edit_speed.py "<遊戲資料夾>" --set Trout 90 --apply
    python3 mvp_edit_speed.py "<遊戲資料夾>" --restore

不需要遊戲資料夾、也不碰任何檔案的自我測試：

    python3 mvp_edit_speed.py --selftest

（不要加 python3 -O：-O 會把 assert 整句拿掉，靠 assert 的測試會假綠。
  這一支的檢查不靠 assert，但守門照樣在 —— 加了 -O 會直接回 2 不跑。）

還有一個唯讀的體檢功能，可以看任何一個欄位的實際值長什麼樣：

    python3 mvp_edit_speed.py "<遊戲資料夾>" --audit 28

── 這支在做什麼（不讀程式碼也看得懂的版本）─────────────────

輸入：一個參數，你的遊戲資料夾（裡面要有 data 這一層）。
      它自己往下找 data/database/attrib.dat，不會去翻別的檔案，也不連網。

attrib.dat 長什麼樣：純文字、CRLF 換行、逗號分隔。
  · 第一行是表頭，每一格長得像「22 playerattrib_speed」，也就是
    「欄位編號 + 空白 + 欄位名」。
  · 之後每一行是一位球員。資料列的行首多一格識別碼，
    所以第 N 欄實際上落在第 N+1 格。
  · 每一格自己也帶著欄位編號當前綴。程式每次都會核對那個前綴，
    對不上就當成「這一列我看不懂」直接不動它。

輸出：
  · 什麼開關都不加 = 總覽，把這份名冊的 speed 分佈印出來。
  · --find 名字   = 查那個人現在的 speed。
  · --audit 欄號  = 唯讀體檢，看任何一欄的值長什麼樣（只看，不寫）。
  · --set 人 值   = 預覽要改什麼；加了 --apply 才真的寫。
  · --restore     = 把備份蓋回去。

寫入的範圍小到可以一句話講完：**只改一列、只改那一列的一格、
只改那一格裡的數字**。行數、CRLF 換行、其他欄位、其他球員，一律不動。

安全網有四層：
  1. 唯讀是預設。--set 沒有加 --apply 就只是印給你看。
  2. 第一次 --apply 之前先備份成 attrib.dat.speedbak，
     而且是先寫同一個資料夾裡一個名字隨機的暫存檔、整份寫完才改名，
     中途斷掉不會留下半截備份；備份完會回頭確認它真的是一個大小相符的檔案，
     確認不過就停手、不動名冊；已經有備份就保留最早那一份，不會被後來的蓋掉。
  3. 寫完立刻重新讀回來，確認「改動的行數剛好是 1」而且「那一格真的變成你要的值」，
     任何一項對不上就不算成功（結束代碼 1）；而且只要那份備份是這一次剛做的，
     就直接替你退回動手之前的樣子，不會留一份壞掉的名冊給你。
  4. 名冊與備份這兩個名字只要有一個是符號連結就整個停手 —— 不然寫下去
     改到的會是連結另一頭那個檔，而它可能根本不在遊戲資料夾裡。
  ⚠️ 第 2、3 層裡的「改名」都跟「登記已經換過了」綁成不可中斷的一段
     （2026-09-06 加）：Ctrl-C 插不進這兩件事中間，所以被中斷的時候，
     畫面上那句話一定跟硬碟上的狀態一致，不會換過去了還說「什麼都沒動」。
     真的卡在那一步的話（極少數環境裝不上訊號處理器），它會說
     「中斷時正在替換 X」並要你 --restore 或自己跟備份比對一次，不會說死。
  ⚠️ 出了預料之外的狀況（不是 Ctrl-C、也不是它自己認得的那幾種錯）時，
     它一樣會照上面那三態講一次「你的檔案現在到底怎麼樣」再結束
     （結束代碼 1），不會只丟一段 Python traceback 給你 ——
     traceback 看不出那個檔到底換過去了沒有（2026-09-11 加）。
  --restore 也不是無條件覆蓋。覆蓋之前備份要一路過關：
     · 它自己還是一份看得懂的名冊（開頭是欄位表、有 CRLF、表頭找得到姓名欄）。
     · 整份以 CRLF 收尾 —— 從中間砍斷的檔會停在某一列的中途。
     · 每一列的格數都一樣 —— 半截的那一列格數一定不足。
     · 球員數不少於現在那個檔 —— 剛好砍在換行處的半截備份靠這道擋。
     · 不是 0 bytes，也不小於現在那個檔的一半。
     任何一道不過就停手，不覆蓋、不動你的檔（本站實測過半截備份把正本吃掉，
     而且畫面照樣印「已還原」的情形）。
     過關之後「換上去」這個動作本身也是原子的：先寫進同資料夾的暫存檔，
     讀回來確認雜湊跟備份相同，才一次換名。所以還原到一半斷電或按 Ctrl-C，
     你的名冊也還是原來那一份，不會停在半截。
  ⚠️ 還原退回去的是「第一次 --apply 之前」那一整份名冊。本站另外三支工具
     （make-a-player 的 mvp_player.py、stats-to-ratings 的 mvp_ratings.py、
     edit-stance 的 mvp_edit_stance.py）
     改的是同一個 attrib.dat，你在這支備份之後用它們做的修改，
     會被這一行一起退掉。

做不到的事（先講清楚，省得你試）：
  · 只寫 playerattrib_speed 這一欄。其他欄位就算你用 --audit 看得到，
    這支腳本也不讓你寫。名字看起來像能力值，不代表遊戲把它當分數讀。
  · --audit 的形狀判定只能**排除錯的**（窄範圍一定不是分數），
    不能證明對的。它是統計，不是遊戲怎麼解讀那一欄的答案。
  · 它不會替你判斷「speed 改到多少才合理」，也沒有量過改完之後
    球員在場上實際跑多快。這支驗的是檔案層面。
  · 二刀流球員在名冊裡佔兩列，這支不會替你把兩列一起改。

零相依：只用 Python 3.7+ 內建功能。
自包含：整支腳本就是這一個檔。

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
import hashlib
import argparse
import tempfile
import collections

# ── 這一次有沒有真的換過遊戲檔(2026-09-05 加)────────────────────────
# 只有 os.replace 真的把名冊換掉之後才會變成 True(建備份不算,備份是新檔)。
# 舊版無論如何都印「沒有改到任何檔案」—— 中斷點落在 os.replace 之後的話那是假的。
# ⚠️ 2026-09-06 起這個旗標不是一個人在決定收尾要講什麼,它是三態裡的第三態;
#    另外兩態(正在換 / 這次建過備份)在下面那一段。
_APPLIED = False
# 這一次真的換過去的東西:[(什麼, 路徑)]。收尾要逐檔講,不能只講「有動到」。
_DONE = []

# ── Ctrl-C 不可以說謊(2026-09-06 第三輪稽核加)────────────────────
# 上面那個旗標原本是在 os.replace **之前**設 True 的,理由寫著「寧可多報一次」。
# 方向是對的(寧可多說也不要少說),但那等於承認有一段時間程式講的話跟磁碟上
# 的狀態對不上 —— 而且反過來的破口也還在:換名做完、旗標還沒登記完,
# Ctrl-C 剛好落在中間,收尾就會照舊狀態說「沒有改到任何檔案」,那句話是假的。
#
# 兩道一起補:
#   (a) 把「換名 + 登記」用 _NoInterrupt 包成不可中斷的一段。這段期間收到的
#       SIGINT 先記著,離開之後才照常丟出來,所以 KeyboardInterrupt 看到的
#       登記一定跟磁碟上的狀態一致。
#   (b) 保險:進入那一段之前先把「正在換 X」登記到 _INFLIGHT。(a) 幾乎不會讓
#       (b) 被用到 —— 唯一漏得掉的是 signal.signal() 自己裝不上去的環境
#       (不是主執行緒會丟 ValueError),那時 (a) 退回原本行為,而 (b) 讓收尾
#       至少講得出「中斷時正在替換 X」,不會講成「沒動到」。
# 三態因此是:_APPLIED → 已換;_INFLIGHT 有東西 → 正在換(換沒換不敢說死);
# 兩個都沒有 → 真的沒動到。
_INFLIGHT = []

# 這一次建立過的備份。它不算「改到檔案」(備份是一個新檔,名冊本身沒被碰過),
# 但被中斷的時候還是要講一句 —— 資料夾裡多了一個檔,不講的人會以為是別的東西。
_BACKED_UP = []


class _NoInterrupt(object):
    """把「os.replace + 登記」包起來:這段期間收到 Ctrl-C 先記著,離開之後再照常丟出。

    ⚠️ 這不是「吃掉 Ctrl-C」。使用者按下去的那一次一定會生效,只是延到這兩行
       跑完 —— 而這兩行加起來是一次改名加一次登記,不會讓人等。換來的是
       「程式講的話跟硬碟上的狀態一致」。
    """

    def __enter__(self):
        self._pending = False
        self._old = None
        try:
            self._old = signal.signal(signal.SIGINT, self._remember)
        except (ValueError, OSError):
            # 不是主執行緒(ValueError)之類的環境:退回原本的行為,不會更糟。
            # 這正是上面 (b) 那道保險存在的理由。
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

    what='backup' 不算「動到遊戲檔」:備份是一個新檔,名冊本身沒被碰過,
    所以它只登記在 _INFLIGHT 那一態,不會讓收尾叫使用者去 --restore。
    """
    global _APPLIED
    entry = (what, dst)
    _INFLIGHT.append(entry)             # 第二態:正在換
    with _NoInterrupt():
        try:
            os.replace(tmp, dst)        # os.replace 是原子的
        except OSError:
            # OSError = 換名自己失敗,也就是換名沒有發生(同一個檔案系統上的
            # rename 不會換一半),這一態可以放心收掉。
            # ⚠️ 這裡刻意只接 OSError,不接 BaseException。訊號如果剛好落在
            #    改名那個系統呼叫上,浮上來的會是 KeyboardInterrupt ——
            #    那種情形「換過去了沒有」是不知道的,收掉這一態就等於替它
            #    說了「沒動到」。不知道的時候要留著,讓收尾說「不敢說死」。
            #    旗標只有在確定 os.replace 沒做才可以撤銷。
            _drop_inflight(entry)
            raise
        if what != 'backup':
            _APPLIED = True             # 第三態:已換
            _DONE.append(entry)
        else:
            _BACKED_UP.append(dst)
        _drop_inflight(entry)


def _drop_inflight(entry):
    """把「正在換」那一態收掉。收不到就算了,不可以蓋掉真正的錯誤原因。"""
    try:
        _INFLIGHT.remove(entry)
    except ValueError:
        pass


def _interrupt_report():
    """被 Ctrl-C 打斷時把「硬碟上真正發生了什麼」講出來。三態,不可以講錯。

    ⚠️ 2026-09-05:舊版無論如何都印「沒有改到任何檔案」。中斷點如果落在
       os.replace 之後(複驗、印畫面都還要跑一段),那句話就是假的。
    ⚠️ 2026-09-06:改照三態講話,而且抽成函式 —— 這樣 --selftest 驗得到
       它到底講了什麼,不必真的殺自己一次。
    ⚠️ 2026-09-11:三態的內容再往下搬一層到 _state_report(),因為「出了
       預料之外的狀況」那條路要講的是同一件事(見 _unexpected_report)。
       這一層印出來的字句一個都沒有變。
    """
    _state_report('已中斷', '中斷')


def _unexpected_report():
    """DataError 與 Ctrl-C 以外的例外收尾:照同一套三態把硬碟狀態講一次。

    ⚠️ 2026-09-11 補(上線前第三輪覆驗抓到)。在這之前 __main__ 只接
       DataError 與 KeyboardInterrupt,其餘例外會直接吐一整段 Python
       traceback —— 而那時候名冊**可能已經被換過了**,traceback 裡一個字
       都看不出這件事,讀者於是不知道自己該不該 --restore。
       本站實測(scratch 複本,沒有碰任何遊戲正本):把 cmd_restore() 裡
       os.replace 成功之後那一行改成丟 OSError,畫面只有 traceback、
       結束代碼 1,而 attrib.dat 的 sha256 早就變回備份那一份了。
    """
    _state_report('出錯停下來了', '出錯')


def _state_report(stopped, moment):
    """三態的內容本體。stopped 是開頭那個詞,moment 是「那一刻」怎麼稱呼。

    只有這兩個詞會變,狀態的判斷與每一句的內容兩條路完全共用 ——
    不然哪天有人只修了其中一條,另一條就會靜靜地繼續講錯話。
    """
    if _APPLIED:
        print('\n%s —— 但檔案在%s之前已經換過了,不是「什麼都沒動」。'
              % (stopped, moment))
        for what, path in _DONE:
            if what == 'restore':
                print('  · %s 已經從備份還原完成(這一步是原子的,不會是半截)。'
                      % os.path.basename(path))
            else:
                print('  · %s 已經改好了(這一步是原子的,要嘛完整的舊版、'
                      '要嘛完整的新版,不會是半截)。' % os.path.basename(path))
        print('要退回去請跑:')
        print('    python3 %s "<遊戲資料夾>" --restore' % os.path.basename(__file__))
        return
    if _INFLIGHT:
        for what, path in _INFLIGHT:
            if what == 'backup':
                print('\n%s —— %s時正在建立備份 %s,建好了沒有這裡不敢說死;'
                      % (stopped, moment, os.path.basename(path)))
                print('  不過那是一個新檔,你的名冊本身沒有被動到。')
                continue
            print('\n%s —— %s時正在替換 %s,換過去了沒有,這裡不敢說死。'
                  % (stopped, moment, os.path.basename(path)))
            print('  這一步本身是原子的(os.replace),所以那個檔要嘛是完整的舊版、')
            print('  要嘛是完整的新版,不會是半截;但到底是哪一版,請用 --restore')
            print('  還原,或自己拿 .speedbak 比對一次:')
            print('    python3 %s "<遊戲資料夾>" --restore' % os.path.basename(__file__))
        return
    print('\n%s,沒有改到任何檔案。' % stopped)
    for b in _BACKED_UP:
        print('  (這一次建立了備份 %s —— 那是一個新檔,你的名冊本身沒有被動到。)'
              % os.path.basename(b))


# ── 備份的原子性(2026-08-29 上線前稽核加)────────────────────────────
# 原本是直接 shutil.copy2(遊戲檔, .bak)。複製途中被中斷(磁碟滿、外接碟拔掉、
# Windows 上按 Ctrl-C)會留下一個**半截的 .bak**;下一次執行看到它「存在」
# 就印「備份已存在,保留最早那一份」繼續改遊戲檔,之後 --restore
# 會拿那個半截檔覆蓋掉正本。
#
# 實測(2026-08-29):把 2,665,562 bytes 的備份截成 300,000 bytes,
# 本站防護最嚴的那支還原指令三道把關全過、印「✓ 已從備份還原」、exit code 0,
# 2.66 MB 的遊戲檔當場被 300 KB 蓋掉。magic 只看開頭,看不出後面少了多少。

def _refuse_symlink(p, what):
    """這個名字本身是一條符號連結就停手,一個位元組都不寫。

    為什麼要有這一道:寫入是「開檔 → 覆蓋」,而開檔會沿著符號連結走。
    只要遊戲資料夾裡放著一條指向外面的連結,寫下去改到的就是外面那個檔。

    ⚠️ 不可以用 os.path.exists() 判斷。它對「指向不存在目標的符號連結」
       回 False —— 而那正是最危險的一種:open(..., 'wb') 會照著連結
       在外面把那個檔**建出來**。看連結本身要用 os.path.islink /
       os.path.lexists,它們不跟著連結走。

    只檢查最後那一段檔名。把整個遊戲資料夾做成連結是很常見的用法
    (外接碟、雲端同步),那種情形照樣跑得動;擋的是「有人在
    data/database 裡放了一條指出去的連結」。
    """
    if not os.path.islink(p):
        return
    try:
        tgt = os.readlink(p)
    except OSError:
        tgt = '(讀不出來)'
    raise DataError(
        '%s「%s」是一條符號連結,不是真正的檔案。\n'
        '  它指向:%s\n'
        '  寫下去會改到連結另一頭那個檔,而它可能在遊戲資料夾外面,\n'
        '  所以這次什麼都不做。請先把這條連結刪掉或改名,再跑一次。'
        % (what, os.path.basename(p), tgt))


def _sha256(path):
    """整份算一次 SHA-256,回傳十六進位字串。

    拆成獨立函式有兩個理由:還原的複驗一次要算兩份(備份與剛寫好的暫存檔),
    而 --selftest 要能把它換掉,才驗得到「複驗不過就不換上去」那一條路 ——
    沒有反向測試的檢查,分不出「沒問題」跟「根本沒跑」。
    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _new_temp_beside(target, tag):
    """在 target 所在的資料夾裡開一個名字猜不到的暫存檔,回傳 (fd, 路徑)。

    ── 2026-09-05 補:暫存檔的名字不可以猜得到(上線前資安稽核第二輪)──
    舊版寫的是 dst + '.part' 跟 path + '.tmp',兩個名字都猜得到。
    只要事先在那個位置放一條指向資料夾外面的符號連結,copy2 / open(...,'wb')
    就會沿著它把外面那個檔覆蓋掉;後面的 os.replace 只換掉連結本身,
    外面那個檔已經回不來了。
    本站實測(scratch 複本,沒碰任何遊戲正本):先放好
    attrib.dat.speedbak.part → 資料夾外的一個 49 bytes 文字檔,
    跑一次 --set ... --apply,那個檔當場變成 840,643 bytes 的名冊,
    而畫面照樣印「已備份」「✅ 複驗通過」、exit code 0。

    mkstemp 的名字是隨機的,而且用 O_CREAT|O_EXCL 建立 ——
    「先去把那個名字佔起來」這一招從此不成立。
    開在同一個資料夾是為了讓最後的 os.replace 落在同一個檔案系統上,
    跨檔案系統的改名不是原子的。
    """
    target = os.fspath(target)
    d = os.path.dirname(os.path.abspath(target)) or '.'
    return tempfile.mkstemp(dir=d, prefix='.%s.%s-' % (os.path.basename(target), tag))


def _atomic_copy(src, dst):
    """備份要嘛完整、要嘛不存在 —— 中間狀態不會留在 dst 這個名字上。

    ⚠️ 本站有些腳本用 pathlib.Path 存路徑,有些用字串。
       2026-08-29 第一版寫成 dst + '.part',在 Path 上直接 TypeError,
       等於所有備份都失敗 —— 而且「半截備份被擋下來」那個測試照樣是綠的。
       是陰性對照(先證明正常流程真的會產生備份)抓到的。

    做法只有兩步:先整份複製到同一個資料夾裡一個名字猜不到的暫存檔
    (見 _new_temp_beside),寫完 flush + fsync 之後才改名成 dst
    (走 _replace_and_record,換名與登記是同一段不可中斷的動作)。
    同一個檔案系統上的改名是原子的,所以「dst 這個名字」
    在任何一個瞬間要嘛還不存在、要嘛就是一份完整的備份,不會有中間狀態。
    途中出任何狀況(含 Ctrl-C)都會把暫存檔收掉再把例外往上丟。
    """
    src, dst = os.fspath(src), os.fspath(dst)
    _refuse_symlink(dst, '備份檔')
    fd, part = _new_temp_beside(dst, 'part')
    try:
        with open(fd, 'wb') as out:
            fd = None                       # 交給 with 管了,下面不可以再 close
            with open(src, 'rb') as ins:
                shutil.copyfileobj(ins, out, 1 << 20)
            out.flush()
            os.fsync(out.fileno())
        shutil.copystat(src, part)          # 權限與時間戳跟著來源走
        # 換名 + 登記綁成一段,中間插不進 Ctrl-C(見 _replace_and_record)。
        _replace_and_record(part, dst, 'backup')
    except BaseException:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
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

    # 第 4 道:MZ 執行檔。0x3C 起 4 個位元組指向 PE 檔頭;PE+6 是節區數、
    #   PE+20 是 Optional Header 的長度,節區表接在它後面,每個節區 40 個位元組,
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
    # attrib.dat 沒有檔頭可以宣告自己多長,所以它靠的就是這一道。
    # 用「不到一半」當門檻而不是「大小要相同」:改一格數字前後大小幾乎不變,
    # 但也可能差一兩個位元組(83 改成 9),抓太緊會擋掉每一次正常的還原。
    if os.path.exists(dst):
        live = os.path.getsize(dst)
        if live > 0 and n * 2 < live:
            _stop('備份只有 %d bytes,而要被蓋掉的那個檔有 %d bytes ——'
                  '差太多了(不到一半)。' % (n, live))
    return _do_copy(bak, dst)


def _do_copy(bak, dst):
    """真正把備份換回去的那一步,單獨拆成一個函式,是為了讓上面每一道守門都寫成
    「檢查不過就 raise,檢查過才走到這裡」,不會有哪一條路徑漏掉檢查。

    ── 2026-09-05 改成原子還原(上線前資安稽核第二輪)────────────────
    舊版這裡是一句 shutil.copy2(bak, dst)。copy2 會先把 dst 開成 'wb' ——
    也就是**先把玩家的名冊截成 0 bytes**,再一路寫回去。中途只要斷一次
    (Ctrl-C、磁碟滿、外接碟拔掉、當機),正本就停在半截。
    本站實測(scratch 複本,沒碰任何遊戲正本):讓複製在 200,000 bytes
    的地方丟出 KeyboardInterrupt,840,643 bytes 的名冊當場變成 200,000 bytes。
    上面那五道守門一個都攔不到這件事 —— 因為壞掉的不是備份,
    是「覆蓋」這個動作本身。

    現在的順序是:
      1. 確認 dst 與 bak 都不是符號連結(不然會寫到資料夾外面去)
      2. 在 dst 同一個資料夾裡開一個名字猜不到的暫存檔
      3. 整份寫進去、flush、fsync
      4. 把正本原本的權限套到暫存檔上(正本不在就套備份的)
      5. 重新從碟上讀回來算 SHA-256,跟備份的比 —— 不相等就中止
      6. 都對了才換上去(同一個檔案系統上的改名是原子的);而且「換名」與
         「登記已經換過了」綁成不可中斷的一段(見 _replace_and_record),
         Ctrl-C 插不進中間,收尾講的話一定跟硬碟上的狀態一致
    任何一步失敗都把暫存檔收掉,dst 從頭到尾一個位元組都沒有被碰過。
    """
    bak, dst = os.fspath(bak), os.fspath(dst)
    _refuse_symlink(dst, '要還原的目標')
    _refuse_symlink(bak, '備份檔')
    fd, tmp = _new_temp_beside(dst, 'restore')
    try:
        with open(fd, 'wb') as out:
            fd = None                       # 交給 with 管了,下面不可以再 close
            with open(bak, 'rb') as ins:
                shutil.copyfileobj(ins, out, 1 << 20)
            out.flush()
            os.fsync(out.fileno())
        # 權限:還原之後應該長得跟原本的正本一樣,不是跟暫存檔一樣。
        # mkstemp 開出來的是 0600,直接換上去等於偷偷改了檔案權限。
        try:
            shutil.copymode(dst if os.path.exists(dst) else bak, tmp)
        except OSError:
            pass
        # 複驗:不是相信自己剛才寫對了,是重新從碟上讀回來比。
        # 磁碟寫壞、寫到一半沒滿、檔案系統騙人,都在這裡現形。
        if os.path.getsize(tmp) != os.path.getsize(bak) or _sha256(tmp) != _sha256(bak):
            raise SystemExit(
                '寫出來的內容跟備份對不上(可能是磁碟滿了或寫入出錯),\n'
                '  所以沒有換上去 —— 你的 %s 還是原來那一份,一個位元組都沒有動到。'
                % os.path.basename(dst))
        _replace_and_record(tmp, dst, 'restore')
    except BaseException:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
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

# ⚠️ 2026-08-25:欄位編號**不能寫死**。
#    原本這裡寫 SPEED_FIELD = 22,那是一台裝過台灣模組的名單的值。
#    拿剛安裝好的原版一比,兩份名單的表頭雖然都是 46 個具名欄位(編號 0 到 45)、
#    欄位名稱集合也相同,但**排列順序不一樣**:原版第 22 欄是 playerattrib_baserunning,
#    speed 在第 23 欄。而且每一格的前綴編號也跟著換,所以「檢查前綴等於 22」
#    這道防線在原版上照樣會通過 —— 結果是把速度值靜靜寫進跑壘欄,不會報錯。
#    現在改成執行時從表頭找欄位名,兩種排列都對。
SPEED_NAME = 'playerattrib_speed'
SPEED_FIELD = None       # 由 resolve_field() 在執行時決定
NAME_FIRST = 0
NAME_LAST = 1
# 允許的數值範圍:這一欄的合理上下界,不是「原廠出現過的值」。
#
# ⚠️ 這兩行的註解原本寫「跟著實際讀到的名單走,不寫死」—— 那是假的,
#    下面就是兩個寫死的常數,程式沒有任何一處去讀名單算範圍。
#    連帶錯誤訊息裡的「這個範圍是原廠資料裡實際出現過的值」對兩份名冊都不成立:
#    剛安裝好的原版根本沒有 0,這台測試機根本沒有 98 和 99。
#    0-99 是為了同時容納兩份而取的聯集,那就照實說是聯集。
#    你這一份實際用到多少,總覽會印出來。
SPEED_MIN = 0
SPEED_MAX = 99


class DataError(Exception):
    """檔案不存在或格式不符預期。訊息是給人看的。"""


# ─────────────────────────────────────────────────────────
#  讀 attrib.dat
# ─────────────────────────────────────────────────────────
def read_attrib(path):
    """整份讀進來,順便做三道「這真的是名冊嗎」的檢查,回傳 (原始位元組, 每一行)。

    三道各自在擋一件真實會發生的事:
      1. 開頭第一個字元是數字:表頭第一格就是「0 欄位名」。
         不是的話你多半指到了別的檔。
      2. 檔案裡有 CRLF:這個格式吃 CRLF。用一般文字編輯器存過之後
         換行會被換成 LF,檔案當場就壞了,而且從畫面上看不出來。
      3. 至少三行:表頭加一列球員都湊不出來的檔,不值得往下猜。

    ⚠️ 全程用位元組處理,不解碼成文字。名冊裡有非 ASCII 的名字,
       解碼再編碼回去可能會換掉位元組,那等於在使用者的檔案上動了手腳。
    """
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


def header_names(line_bytes):
    """表頭:{欄位編號: 欄位名}

    表頭每一格長得像「22 playerattrib_speed」,所以用「開頭的數字 + 一個空白
    + 欄位名」去撈。撈不到的格子直接跳過,不當成錯,這一行的第一格
    本來就不是「編號 名稱」那個形狀。
    """
    out = {}
    for c in line_bytes.split(b','):
        m = re.match(rb'^\s*(\d+) (\w+)', c)
        if m:
            out[int(m.group(1))] = m.group(2).decode('latin-1')
    return out


def resolve_field(lines, wanted_name):
    """從表頭找出某個欄位真正的編號。找不到就明白說,不要猜。

    attrib.dat 第一行是表頭,每一格長得像「22 playerattrib_speed」。
    不同來源的名冊會用不同的排列順序,所以編號必須每次讀出來,不能寫死。
    """
    names = header_names(lines[0])
    for num, nm in names.items():
        if nm == wanted_name:
            return num
    raise DataError(
        '這份名冊的表頭裡找不到 %s 這個欄位。\n'
        '  它有 %d 個欄位。這支腳本不敢在看不懂的檔案上動手。'
        % (wanted_name, len(names)))


def cell_value(line_bytes, field):
    """取第 field 欄的值。資料列行首多一個識別碼,所以位置是 field+1。

    取出來之後還要核對「這一格自己帶的編號等不等於 field」。
    這一道很重要:格數不對、或這一列根本不是球員資料時,
    位置算出來會指到別的欄位,而核對前綴就會當場對不上,回 None 而不是回錯的值。
    回 None 的意思一律是「這一格我不認得」,不是「這一格是空的」。
    """
    cells = line_bytes.split(b',')
    idx = field + 1
    if idx >= len(cells):
        return None
    m = re.match(rb'^(\d+) ?(.*)$', cells[idx].strip())
    if not m or int(m.group(1)) != field:
        return None
    return m.group(2).decode('latin-1')


def iter_players(lines):
    """一列一列吐出 (行號, 識別碼, 名, 姓, speed 值)。

    跳過表頭與空行;名或姓有一個讀不出來就跳過這一列,
    因為那代表這一列不是一般的球員資料,寧可漏掉也不要誤判。

    ⚠️ 這裡用到的 SPEED_FIELD 是執行時才由 main() 從表頭決定的,
       所以呼叫順序是固定的:先 resolve_field(),才輪得到這裡。
    """
    for i, l in enumerate(lines):
        if i == 0 or not l.strip():
            continue
        first = cell_value(l, NAME_FIRST)
        last = cell_value(l, NAME_LAST)
        if first is None or last is None:
            continue
        yield i, l.split(b',')[0].decode('latin-1'), first, last, cell_value(l, SPEED_FIELD)


# ─────────────────────────────────────────────────────────
#  欄位體檢:這一欄到底是「分數」還是「編號」
# ─────────────────────────────────────────────────────────
def audit_field(lines, field, names):
    """唯讀:把某一欄的值全部撈出來做統計,幫你判斷它像不像「分數」。

    為什麼需要這個:欄位名寫著能力,值卻可能是「第幾號樣式」。
    battingstance 的範圍看起來像分數,實際上是打擊姿勢的編號,
    照分數去寫只會讓他擺一個不存在的姿勢。

    看的是三件事:
      · 範圍有多寬:窄到只有十幾種值的欄位,一定不是 0 到 99 的分數。
      · 去掉最常見那個值(通常是預設值)之後,剩下的有沒有擠在前幾名。
      · 剩下的有沒有擠在 0 到 7 這種小數字,那是「編號」的長相。

    ⚠️ 這是統計,不是答案。形狀只能排除錯的,不能證明對的:
       背號、體重、身高的形狀跟分數一樣。所以就算你在這裡看到一欄
       「長得很像分數」,這支腳本照樣不讓你寫它。
    """
    vals = []
    for l in lines[1:]:
        if not l.strip():
            continue
        v = cell_value(l, field)
        if v is not None and v.lstrip('-').isdigit():
            vals.append(int(v))
    if not vals:
        print('\n第 %d 欄讀不到數字。它可能是文字欄位(例如姓名),或這個編號不存在。' % field)
        return

    # 最常見的那個值幾乎一定是預設值(沒被個別設定過的球員都用它)。
    # 它會佔掉很大一塊,把整體分佈壓平,所以下面的兩個比例都要先把它拿掉再算,
    # 不然任何一欄看起來都會像「高度集中」。
    name = names.get(field, '(表頭沒有這一欄)')
    c = collections.Counter(vals)
    lo, hi = min(vals), max(vals)
    default, dn = c.most_common(1)[0]
    rest = [v for v in vals if v != default]
    rc = collections.Counter(rest)
    top5 = sum(v for _, v in rc.most_common(5)) / len(rest) * 100 if rest else 0
    small = sum(v for k, v in rc.items() if k <= 7) / len(rest) * 100 if rest else 0

    print('\n【第 %d 欄 %s】' % (field, name))
    print('  資料筆數    : %d' % len(vals))
    print('  值的範圍    : %d – %d' % (lo, hi))
    print('  不重複的值  : %d 種' % len(set(vals)))
    print('  最常見的值  : %d(%d 筆,佔 %.1f%%)—— 這通常是「預設值」' % (default, dn, dn / len(vals) * 100))
    print('  去掉預設值後:')
    print('    前 5 名佔  : %.1f%%' % top5)
    print('    0-7 的小值佔: %.1f%%' % small)
    print('  最常見的 8 個值:', ', '.join('%d×%d' % (k, v) for k, v in c.most_common(8)))

    # 三個判定條件的門檻(20 / 30 / 15 / 30 / 40)都是本站看過幾十欄之後訂的
    # 經驗值,不是從遊戲裡量到的常數。所以四條路裡留了一條「看不出來」,
    # 兩種特徵都不明顯時就照實說不知道,不硬套一個結論。
    print('\n  形狀判定:', end=' ')
    if hi - lo < 20:
        print('窄範圍(只有 %d – %d)' % (lo, hi))
        print('  → 這種欄位只認得少數幾個值。寫 85 進去等於寫了它看不懂的東西,')
        print('     不論它的名字看起來多像能力值。')
    elif top5 < 30 and small < 15:
        print('寬而平均')
        print('  → 值散佈在整個範圍,沒有擠在小數字。「0-99 分數」是這個形狀,')
        print('     但是 ⚠ 背號、體重、身高也是。形狀相同不代表用途相同。')
    elif small > 30 or top5 > 40:
        print('擠在小數字,或高度集中')
        print('  → 這比較像「第幾號樣式」而不是「幾分」。')
        print('     名字寫著能力也一樣 —— 例如打擊姿勢的值是 0-65,')
        print('     但那是姿勢編號,不是打擊有多強。')
    else:
        print('看不出來')
        print('  → 兩種特徵都不明顯,本站不猜。')

    print('\n  ⚠ 這只是「值長什麼樣」的統計,不等於遊戲怎麼解讀它。')
    print('     形狀只能排除錯的(窄範圍一定不是分數),不能證明對的。')
    print('     本腳本只允許寫入第 %d 欄(speed),其他欄位一律唯讀。' % SPEED_FIELD)


# ─────────────────────────────────────────────────────────
#  查詢與修改
# ─────────────────────────────────────────────────────────
def cmd_overview(lines):
    """沒帶任何開關時走這裡:把這一份名冊的 speed 分佈印出來。

    這件事本身就是一道防呆:你會先看到「這份檔案讀得懂、有幾位球員、
    值的範圍長怎樣」,再決定要不要動手。最常見的那個值就是預設值,
    佔比通常很高,代表很多球員從來沒有被個別設定過速度。

    直方圖每 10 分一格,最後一格把 90 以上全部收進去。
    """
    vals = []
    for _, _, _, _, sp in iter_players(lines):
        if sp is not None and sp.isdigit():
            vals.append(int(sp))
    if not vals:
        raise DataError('讀不到任何 speed 值,檔案格式可能不對')
    c = collections.Counter(vals)
    default, dn = c.most_common(1)[0]
    print('\n【總覽】共 %d 位球員有 speed 值' % len(vals))
    print('  範圍       : %d – %d' % (min(vals), max(vals)))
    print('  最常見的值 : %d(%d 位,佔 %.1f%%)' % (default, dn, dn / len(vals) * 100))
    print('  平均       : %.1f' % (sum(vals) / len(vals)))
    print('\n  分佈:')
    buckets = collections.Counter(min(v // 10 * 10, 90) for v in vals)
    top = max(buckets.values())
    for b in range(0, 100, 10):
        n = buckets.get(b, 0)
        bar = '█' * max(1, round(n / top * 40)) if n else ''
        print('    %2d-%2d  %5d  %s' % (b, b + 9, n, bar))


def cmd_find(lines, keyword):
    """查名字。不分大小寫,名或姓其中一個含到就算。

    最多列 40 位,不是為了省事,是因為列太長你反而找不到人;
    超過就告訴你還有幾位,請你把關鍵字打長一點。
    同名的時候用識別碼指定最保險,所以識別碼放在第一欄。
    """
    kw = keyword.lower()
    hits = [(i, rid, f, l, sp) for i, rid, f, l, sp in iter_players(lines)
            if kw in f.lower() or kw in l.lower()]
    if not hits:
        print('\n找不到名字含「%s」的球員。' % keyword)
        print('提示:名字要用檔案裡的英文拼法。')
        return
    print('\n找到 %d 位:' % len(hits))
    print('  %-10s %-14s %-14s %s' % ('識別碼', '名', '姓', 'speed'))
    for i, rid, f, l, sp in hits[:40]:
        print('  %-10s %-14s %-14s %s' % (rid, f, l, sp if sp is not None else '?'))
    if len(hits) > 40:
        print('  …另外還有 %d 位' % (len(hits) - 40))
    if len(hits) > 1:
        print('\n  同名的話,用識別碼指定比較保險。')


def find_target(lines, who):
    """把使用者打的那個字對到唯一一位球員,對不到就停下來要他講清楚。

    順序是「由嚴到寬」,而且每一關都要求唯一:
      1. 完全等於識別碼(最沒有歧義的指定方式)。
      2. 完全等於名、姓,或「名 姓」,一律小寫比對。
    對到不只一位就把候選人連同他們目前的 speed 印出來,請你改用識別碼。

    ⚠️ 這裡刻意不做「部分符合」。--set 是要寫檔的,寫錯人不會有任何錯誤訊息,
       只會有一位你沒想改的球員被改掉。想模糊搜尋請用 --find。
    """
    exact = [x for x in iter_players(lines) if x[1] == who]
    if len(exact) == 1:
        return exact[0]
    kw = who.lower()
    hits = [x for x in iter_players(lines)
            if kw == x[2].lower() or kw == x[3].lower() or kw == ('%s %s' % (x[2], x[3])).lower()]
    if not hits:
        raise DataError('找不到「%s」。先用 --find %s 查查看正確拼法。' % (who, who))
    if len(hits) > 1:
        msg = ['「%s」對到 %d 位球員,請改用識別碼指定:' % (who, len(hits))]
        for i, rid, f, l, sp in hits[:10]:
            msg.append('    %s  %s %s  (目前 speed=%s)' % (rid, f, l, sp))
        raise DataError('\n'.join(msg))
    return hits[0]


def build_new_line(line_bytes, new_val):
    """把一列裡的 speed 那一格換成新值,回傳整列的新位元組。其他格原封不動。

    換之前先核對那一格帶的編號等不等於 SPEED_FIELD,對不上就寧可停下來也不寫。
    重組時保留原本那一格前面的空白(m.group(1)),因為那是這個檔案格式的一部分,
    順手「整理」掉就是在改一個沒有人要求你改的東西。

    ⚠️ 這裡只碰 cells 裡的一格,然後用逗號接回去,
       所以逗號的數量、其他欄位的內容、整列以外的東西,全部不可能被動到。
    """
    cells = line_bytes.split(b',')
    idx = SPEED_FIELD + 1
    if idx >= len(cells):
        raise DataError('這一列沒有第 %d 欄,不敢動' % SPEED_FIELD)
    m = re.match(rb'^(\s*)(\d+) ?(.*)$', cells[idx])
    if not m or int(m.group(2)) != SPEED_FIELD:
        raise DataError('第 %d 欄的內容是 %r,不是預期格式,不敢動' % (SPEED_FIELD, cells[idx]))
    cells[idx] = b'%s%d %d' % (m.group(1), SPEED_FIELD, new_val)
    return b','.join(cells)


def cmd_set(path, lines, who, new_val, apply_it):
    """--set 的主流程:找人 → 算出新的那一列 → 印預覽 → 有 --apply 才寫 → 複驗。

    順序是刻意的:預覽跟真的會寫下去的內容是同一個 new_line,
    所以你在預覽看到的,就是等一下真的會發生的事。

    新舊兩列一模一樣時直接說「已經是這個值了」,不會白備份也不會白寫一次。
    """
    global _APPLIED
    i, rid, first, last, old = find_target(lines, who)
    old_line = lines[i]
    new_line = build_new_line(old_line, new_val)

    print('\n【預覽】%s %s  (識別碼 %s)' % (first, last, rid))
    print('  第 %d 欄 playerattrib_speed' % SPEED_FIELD)
    print('    原本:%s' % old)
    print('    改成:%d' % new_val)

    if old_line == new_line:
        print('\n  這一列已經是這個值了,不需要改動。')
        return

    if not apply_it:
        print('\n  以上只是預覽,沒有改到任何檔案。')
        print('  確定要改的話,在同一行指令最後加上 --apply')
        return

    backup = path + '.speedbak'
    # ── 2026-09-05 補:寫之前先確認這兩個名字都不是符號連結 ────────────
    # 下面那個 os.path.isfile(backup) 對「指向資料夾外面某個檔的符號連結」
    # 會回 True,舊版於是印「備份已存在,保留最早那一份」然後照樣改名冊 ——
    # 使用者其實沒有備份,而連結指到哪裡,備份就等於寫到哪裡。
    _refuse_symlink(path, '名冊')
    _refuse_symlink(backup, '備份')
    # ⚠️ 這裡看的是 isfile 不是 exists。2026-09-05 實測:如果
    #    attrib.dat.speedbak 那個位置擺的是一個資料夾(同步軟體、或手滑建出來的),
    #    只看 exists 就會判成「備份已存在,保留最早那一份」然後照樣改名冊,
    #    使用者一直以為自己有備份,直到 --restore 那天才發現沒有。
    #    (當初這一段是「.part 剛好是資料夾」的情形抓出來的;暫存檔改用
    #     mkstemp 之後那個名字別人佔不到了,但目標名字本身還是要分清楚。)
    #    所以備份這一段現在做三件事:分清楚檔案與非檔案、備份失敗要講人話、
    #    備份完回頭確認它真的落地而且大小跟來源一樣。
    # fresh_backup:這一份備份是不是「這一次」才做的。
    # 只有這種備份才等於「動手之前的原狀」,複驗不過時才敢替使用者自動退回去;
    # 更早以前留下的那一份退回去會連帶退掉他後來用別的工具做的修改。
    fresh_backup = False
    if os.path.isfile(backup):
        print('\n  備份已存在,保留最早那一份 → %s' % os.path.basename(backup))
    elif os.path.exists(backup):
        raise DataError(
            '%s 已經存在,但它不是一個檔案(是資料夾之類的東西)。\n'
            '  這樣就備份不了,所以不動你的名冊 —— 這次什麼都沒改。\n'
            '  請先把它移走或改名,再跑一次。'
            % os.path.basename(backup))
    else:
        try:
            _atomic_copy(path, backup)
        except OSError as e:
            raise DataError(
                '備份失敗:%s\n'
                '  沒有備份就不動你的名冊,所以這次什麼都沒改。\n'
                '  常見原因:磁碟滿了、那個資料夾是唯讀的、防毒軟體擋住。' % e)
        if not os.path.isfile(backup) or os.path.getsize(backup) != os.path.getsize(path):
            raise DataError(
                '備份沒有成功(%s 不是一個大小相符的檔案),所以不動你的名冊。\n'
                '  請確認那個資料夾可以寫入,而且沒有同名的資料夾擋在那裡。'
                % os.path.basename(backup))
        fresh_backup = True
        print('\n  已備份 → %s' % os.path.basename(backup))

    # 只換掉第 i 列,其餘照原樣,再用 CRLF 接回去。
    # 這個格式吃 CRLF,用平台預設的換行寫出去在 Mac / Linux 上就會把檔案改壞。
    new_lines = list(lines)
    new_lines[i] = new_line
    # 寫入走「先寫暫存檔 → flush → fsync → 改名」:改名是原子的,
    # 所以 attrib.dat 要嘛是舊的、要嘛是完整的新的,不會出現寫到一半的名冊。
    # fsync 是逼作業系統真的把資料寫進碟再換名(跟本站 mvp_ratings.py 同一套);
    # 少了它,換名可能先落地、內容還在快取裡,斷電就會留下一個空殼。
    # copymode 是因為新檔是暫存檔生的,原本 attrib.dat 的權限不會自己跟過來:
    # 本站實測 -rwx------ 的名冊改完會變成 -rw-r--r--,等於順手放寬了權限。
    # 暫存檔的名字不可以猜得到:舊版寫的是 path + '.tmp',先在那個位置放一條
    # 指向資料夾外面的符號連結,open(..., 'wb') 就會沿著它把外面那個檔覆蓋掉。
    # 改用 mkstemp(見 _new_temp_beside),隨機名 + O_CREAT|O_EXCL。
    fd, tmp = _new_temp_beside(path, 'tmp')
    try:
        with open(fd, 'wb') as f:
            fd = None                      # 交給 with 管了,下面不可以再 close
            f.write(b'\r\n'.join(new_lines))
            f.flush()
            os.fsync(f.fileno())
        try:
            shutil.copymode(path, tmp)
        except OSError:
            pass
        # 換名 + 登記綁成不可中斷的一段(見 _replace_and_record):
        # Ctrl-C 插不進這兩件事中間,所以收尾講的那句話一定跟磁碟上的狀態一致。
        # 舊版是在 os.replace **之前**就把旗標設起來,方向雖然保守,
        # 但那等於承認有一段時間程式講的話是猜的。
        _replace_and_record(tmp, path, 'write')
    except OSError as e:
        # 這條路在 Windows 上很實際:遊戲開著、防毒鎖檔、磁碟滿,
        # open 跟 os.replace 都會丟 OSError。原本這裡沒有人接,
        # 畫面會吐一整段 Python traceback,而且那顆 .tmp 會留在遊戲資料夾裡。
        # attrib.dat 本身沒有被動到 —— 新內容從頭到尾都只寫在暫存檔上。
        # ⚠️ 這裡**不可以**寫 _APPLIED = False。旗標現在只在 os.replace 真的
        #    做完之後才會被設起來(見 _replace_and_record),走到這裡就代表
        #    它根本沒被設過,沒有東西需要撤銷;硬撤一次反而會把同一次執行裡
        #    先前真的換過的檔說成「沒動到」。
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise DataError(
            '寫不進去:%s\n'
            '  你的 %s 沒有被改到(新內容全程只寫在暫存檔上),備份也還在。\n'
            '  常見原因:遊戲還開著、防毒軟體鎖住那個檔、磁碟滿了、\n'
            '  或那個資料夾是唯讀的。關掉遊戲再跑一次。\n'
            '  如果 %s 還留在資料夾裡,那是這次沒收乾淨的暫存檔,可以直接刪掉。'
            % (e, os.path.basename(path), os.path.basename(tmp)))
    except BaseException:
        # Ctrl-C 之類的:暫存檔要收掉,不然它會留在遊戲資料夾裡。
        # 這裡不動 _APPLIED —— 中斷點可能落在 os.replace 之前也可能之後,
        # 分不出來的時候要往「可能已經換過了」那邊講,不可以說成什麼都沒動。
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise

    # 複驗:不是相信自己剛才寫對了,而是重新從磁碟讀一次來檢查三件事:
    # 行數沒變、只有一列不一樣、那一列的那一格真的等於你要的值。
    # 三件事只要有一件不成立就不會走到「✅ 複驗通過」,而是丟例外(exit code 1),
    # 而且**這一次的備份如果是剛做的,就直接替你退回去**,不留一份壞掉的名冊。
    fail = None
    lines2 = None
    try:
        raw2, lines2 = read_attrib(path)
    except DataError as e:
        fail = '寫入後的檔案讀不回來了(%s)' % e
    if lines2 is not None:
        if len(lines2) != len(lines):
            fail = '寫入後行數變了(%d → %d)' % (len(lines), len(lines2))
        else:
            diff = sum(1 for a, b in zip(lines, lines2) if a != b)
            got = cell_value(lines2[i], SPEED_FIELD)
            print('  已寫入。改動行數 = %d(應該是 1),%s(第 %d 欄)現在是 %s'
                  % (diff, SPEED_NAME, SPEED_FIELD, got))
            if diff != 1 or got != str(new_val):
                fail = ('改動行數是 %d(應該是 1),那一格是 %s(應該是 %s)'
                        % (diff, got, new_val))
    if fail is not None:
        msg = ['複驗不通過:%s' % fail]
        if fresh_backup:
            # 這一份備份就是這一次動手之前的名冊,退回去剛好是原狀,
            # 不會連帶退掉你用別的工具做的修改 —— 所以直接替你還原。
            try:
                _restore_from_backup(backup, path)
                _APPLIED = False
                msg.append('  已自動退回這次動手之前的樣子(來源:%s)。'
                           % os.path.basename(backup))
                msg.append('  你的名冊現在跟你跑這一行之前一樣,備份也還留著。')
            except BaseException as e2:
                msg.append('  想替你自動退回去,但那一步也失敗了(%s)。' % e2)
                msg.append('  請立刻自己跑一次還原:')
                msg.append('    python3 %s "<遊戲資料夾>" --restore'
                           % os.path.basename(__file__))
        else:
            # 備份是更早以前留下的,退回去會連帶把你後來做的修改一起退掉,
            # 這種事不可以自作主張,只把指令給你。
            msg.append('  這個資料夾裡的備份是更早以前留下的,自動退回去會連帶')
            msg.append('  退掉你後來用別的工具做的修改,所以這裡不替你決定。')
            msg.append('  要退回去請自己跑:')
            msg.append('    python3 %s "<遊戲資料夾>" --restore'
                       % os.path.basename(__file__))
        raise DataError('\n'.join(msg))
    print('  ✅ 複驗通過')


def cmd_restore(path):
    """把備份蓋回去,但覆蓋之前要先確定那份備份自己是好的。

    這一支的還原有四段:先確認備份還是一份看得懂的名冊;再驗名冊自己的形狀
    (以 CRLF 收尾、每一列格數一致、球員數不少於現在那個檔);然後交給
    _restore_from_backup() 擋 0 bytes 與明顯過短的備份,由它底下的 _do_copy
    原子地換上去(寫暫存檔 → fsync → 比雜湊 → os.replace,不直接覆蓋正本);
    最後跟「還原前的內容」比對,告訴你這次到底有沒有東西被換回去。

    ⚠️ 它退回去的是整份名冊,不是只有 speed 那一欄。本站的 mvp_player.py、
       mvp_ratings.py 與 mvp_edit_stance.py 改的是同一個 attrib.dat,你在這支備份之後用它們做的修改,
       會被這一次還原一起退掉。
    """
    backup = path + '.speedbak'
    # 連結先擋:_do_copy 底下也有同一道,但那要走到最後才會亮。
    # 在這裡先擋是為了給一句看得懂的話,而不是讓它一路讀到最後才停。
    # ⚠️ 順序不可以顛倒 —— 下一行的 os.path.exists() 對「指向不存在目標的
    #    符號連結」回 False,會把它說成「找不到備份」,那是錯的診斷。
    _refuse_symlink(backup, '備份')
    _refuse_symlink(path, '名冊')
    if not os.path.exists(backup):
        raise DataError('找不到備份 %s。這支腳本只在第一次 --apply 時建立備份。'
                        % os.path.basename(backup))
    # ⚠️ 覆蓋之前先確認這個備份真的是名冊。
    #    另外三支工具的備份就躺在同一個資料夾,副檔名各不相同但都在旁邊;
    #    路徑打錯、或手動改過副檔名,就會拿別的東西蓋掉名冊。
    #    read_attrib 已經有三道格式檢查(開頭是欄位表、有 CRLF、行數夠不夠),直接拿來用。
    #
    #    ⚠️ read_attrib 回傳的是「整份位元組」跟「每一行」兩樣東西,一定要拆成兩個名字接。
    #       這一行原本寫成 lines = read_attrib(backup),lines[0] 拿到的就是整份檔案,
    #       不是表頭那一行,下面那道等於在全檔搜尋 first_name / last_name,比要的鬆。
    #       在本站測試機那份 attrib.dat 上,整份是 840,643 bytes、表頭只有 1,182 bytes。
    #       本站實測:拿測試機那份照抄,只把表頭換成「0 zzz,1 yyy,2 www」、檔尾多接一行
    #       first_name,last_name,得到一份 839,500 bytes 的假備份。地板擋的是「備份不到
    #       正本的一半」(840,643 的一半是 420,321),839,500 遠在門檻之上所以過得去;
    #       沒拆開之前 --restore 一句警告都沒有,直接把名冊換成那份垃圾,拆開之後才擋得下來。
    #       合法的還原不受影響:本站測試機那份與剛安裝好的原版那份,first_name 與
    #       last_name 都各只出現 1 次而且就在表頭;實測改一位球員的 speed 再 --restore,
    #       還原後與動手之前位元組相同,半截備份也照樣被大小那道擋住。
    try:
        raw_bak, lines = read_attrib(backup)
    except DataError as e:
        raise DataError('這個備份看起來不是名冊(%s),不敢拿它覆蓋 %s。'
                        % (e, os.path.basename(path)))
    header = lines[0].decode('latin-1', 'replace')
    if 'first_name' not in header or 'last_name' not in header:
        raise DataError('這個備份的表頭找不到 first_name / last_name,不像名冊,不敢覆蓋。')

    # ── 2026-09-05 補:半截備份靠「不到一半」那道地板擋不住 ────────────────
    # 本站實測(scratch 複本,沒碰任何遊戲正本):把 840,643 bytes 的名冊砍成
    # 600,000 bytes(71%,遠在地板之上),舊版五道守門全過,正本當場被蓋掉、
    # 930 位球員從名冊裡消失,而畫面印「已從備份還原」「跟還原前有 1 行不同」、
    # exit code 0。「不到一半」只擋得住砍得很兇的那一種。
    #
    # 名冊自己有形狀可以驗,不必只靠地板:
    #   · 整份要以 CRLF 收尾 —— 從中間砍斷的檔幾乎一定停在某一列的中途。
    #   · 每一列的逗號數都要一樣 —— 半截的那一列格數一定不足。
    #     本站量過兩份相異的名冊(測試機 3,247 位、剛安裝好的原版 2,921 位),
    #     兩份的資料列都是每列 47 個逗號,一列都沒有例外。
    # 這兩道合起來,只有「剛好砍在換行處」的備份還能通過。
    if not raw_bak.endswith(b'\r\n'):
        raise DataError(
            '這個備份的最後一列是半截的(檔案沒有以 CRLF 收尾),\n'
            '  多半是備份途中被中斷(磁碟滿、外接碟拔掉、按了 Ctrl-C)。\n'
            '  不敢拿它覆蓋 %s,請改用你自己另外留的那一份備份。'
            % os.path.basename(path))
    widths = set(l.count(b',') for l in lines[1:] if l.strip())
    if len(widths) != 1:
        raise DataError(
            '這個備份的每一列格數不一致(%s),名冊不該長這樣 ——\n'
            '  最可能的原因是它被截斷了,或被文字編輯器改壞了。\n'
            '  不敢拿它覆蓋 %s,請改用你自己另外留的那一份備份。'
            % (', '.join('%d 格' % (w + 1) for w in sorted(widths)) or '一列都讀不到',
               os.path.basename(path)))

    # 剩下的那一種:剛好砍在換行處。形狀是完好的,只是後面少了好幾百位球員,
    # 只能拿「現在那個檔」的列數來比才看得出來。本站三支會改 attrib.dat 的工具
    # (這一支、換球員、數據換算)都是就地改既有的列,不增不減,
    # 所以正常情況下備份與正本的球員數一定相同。
    # 現在那個檔已經讀不出來(真的壞了)就不比 —— 那正是 --restore 要救的情形。
    if os.path.exists(path):
        try:
            _live_raw, live_lines = read_attrib(path)
        except DataError:
            live_lines = None
        if live_lines is not None:
            bak_rows = sum(1 for l in lines[1:] if l.strip())
            live_rows = sum(1 for l in live_lines[1:] if l.strip())
            if bak_rows < live_rows:
                raise DataError(
                    '這個備份裡只有 %d 位球員,現在的 %s 有 %d 位 —— 備份少了 %d 位。\n'
                    '  還原下去那些人會從名冊裡消失,所以停在這裡不動。\n'
                    '  常見原因有兩個:\n'
                    '    1. 這份備份是半截的(備份途中被中斷)—— 請改用你另外留的那一份。\n'
                    '    2. 你在備份之後用別的工具加過球員 —— 那份備份本來就比較舊,\n'
                    '       真要退回去的話,請自己把 %s 複製成 %s。'
                    % (bak_rows, os.path.basename(path), live_rows, live_rows - bak_rows,
                       os.path.basename(backup), os.path.basename(path)))

    # ⚠️ 這裡原本印「位元組完全一致」,拿的是剛複製過去的檔跟來源比 ——
    #    複製成功就一定相等,那句話只是在報告自己剛複製成功,不代表任何事。
    #    改成跟「還原前的檔案」比,這樣才看得出來到底有沒有變。
    before = open(path, 'rb').read() if os.path.exists(path) else None
    # 「換上去」與「登記換過了」綁在 _replace_and_record 裡面,是同一段不可中斷
    # 的動作 —— 舊版是在這一行**之後**才補登記,Ctrl-C 落在中間就會說成
    # 「什麼都沒動」,而檔案其實已經被換掉了。
    _restore_from_backup(backup, path)
    after = open(path, 'rb').read()
    print('\n  已從備份還原 → %s' % os.path.basename(path))
    if before is None:
        print('  (還原前那個檔不在,所以沒有可比對的對象)')
    elif before == after:
        print('  跟還原前一模一樣 —— 你的檔案本來就跟備份相同,這次沒有任何改變。')
    else:
        # ⚠️ zip 會在較短的那一邊停住,所以「行數變了」一定要另外講。
        #    只用 zip 數的話,一份被截掉 930 行的備份會印成「1 行不同」——
        #    2026-09-05 實測就是這個數字在替那次覆蓋掩護。
        bl, al = before.split(b'\r\n'), after.split(b'\r\n')
        n = sum(1 for a_, b_ in zip(bl, al) if a_ != b_)
        if len(bl) != len(al):
            print('  ⚠ 行數從 %d 變成 %d(差 %d 行)。' % (len(bl), len(al), abs(len(bl) - len(al))))
        print('  已還原,前 %d 行裡有 %d 行不同。' % (min(len(bl), len(al)), n))
        # 退回去的是整份名冊,不是只有 speed 那一欄 —— 這件事在畫面上也要講一次,
        # 不能只寫在檔頭,因為會來按 --restore 的人多半正在急。
        print('  ⚠ 這一次退回去的是「第一次 --apply 之前」那一整份名冊。')
        print('    如果你在那之後還用過本站的「把一位球員改成你想要的球員」或')
        print('    「把真實成績換算成遊戲裡的能力值」改同一個 attrib.dat,')
        print('    那些修改也一起被退掉了。')


# ─────────────────────────────────────────────────────────
def main():
    """指令列入口:找檔、決定欄號,然後分派到五條路的其中一條。

    順序有意義:--restore 排在讀檔之前,因為出事的時候那一行一定要能跑,
    不能被「現在這個檔壞掉讀不出來」卡住。
    其餘四條(--audit / --find / --set / 總覽)都要先把名冊讀進來。

    SPEED_FIELD 是 global,在這裡才填上。欄號每一次都從表頭現找,
    不同來源的名冊排列順序不一樣,寫死就會靜靜地寫錯欄位。
    """
    ap = argparse.ArgumentParser(
        description='修改 MVP Baseball 2005 球員的跑壘速度'
                    '(只寫 attrib.dat 的 playerattrib_speed 欄,欄號由表頭決定)')
    ap.add_argument('gamedir', help='遊戲資料夾(裡面要有 data 這個子資料夾)')
    ap.add_argument('--find', metavar='名字', help='查球員目前的 speed')
    ap.add_argument('--set', nargs=2, metavar=('球員', 'speed'), help='修改某位球員的 speed')
    ap.add_argument('--audit', metavar='欄位編號', help='唯讀:看某一欄的值長什麼樣')
    ap.add_argument('--apply', action='store_true', help='真的寫入(沒加就只是預覽)')
    ap.add_argument('--restore', action='store_true', help='從備份還原 attrib.dat')
    args = ap.parse_args()

    # 使用者給的是遊戲資料夾,名冊固定在 data/database/attrib.dat。
    # 找不到就把完整路徑印出來,讓他一眼看出自己指到哪一層去了。
    attrib = os.path.join(args.gamedir, 'data', 'database', 'attrib.dat')
    if not os.path.isfile(attrib):
        print('❌ 找不到 %s' % attrib)
        print('   請確認第一個參數是遊戲資料夾(裡面應該要有 data 這個子資料夾)。')
        return 2

    if args.restore:
        cmd_restore(attrib)
        return 0

    raw, lines = read_attrib(attrib)

    # 欄位編號每次從表頭讀出來 —— 不同來源的名冊排列順序不一樣。
    global SPEED_FIELD
    SPEED_FIELD = resolve_field(lines, SPEED_NAME)
    if SPEED_FIELD != 22:
        print('  註:這份名冊的 %s 在第 %d 欄(常見的台灣模組名冊是第 22 欄)。'
              % (SPEED_NAME, SPEED_FIELD))

    # --audit 一律唯讀。它接受任何欄號,但也僅止於看。
    # 會寫檔的路有兩條,不是一條:
    #   cmd_set()     要加 --apply 才寫,而且只寫 speed 那一欄。
    #   cmd_restore() 不看 --apply,覆蓋前那幾道守門過了就把備份整份換回
    #                 attrib.dat(先寫暫存檔、比對雜湊、再原子改名)。
    # 所以「沒有 --apply 就不會動到檔案」這句話只對 --set 那一條成立。
    if args.audit is not None:
        if not args.audit.isdigit():
            print('❌ 欄位編號要是數字,你給的是「%s」' % args.audit)
            return 2
        audit_field(lines, int(args.audit), header_names(lines[0]))
    elif args.find:
        cmd_find(lines, args.find)
    elif args.set:
        who, val = args.set
        if not val.lstrip('-').isdigit():
            print('❌ speed 要是數字,你給的是「%s」' % val)
            return 2
        v = int(val)
        if v < SPEED_MIN or v > SPEED_MAX:
            print('❌ speed 請填 %d 到 %d 之間,你給的是 %d' % (SPEED_MIN, SPEED_MAX, v))
            print('   (%d-%d 是這一欄的合理上下界,涵蓋兩種名冊;'
                  '你這一份實際用到的範圍,執行不加參數就會印出來)' % (SPEED_MIN, SPEED_MAX))
            return 2
        cmd_set(attrib, lines, who, v, args.apply)
    else:
        cmd_overview(lines)
    return 0


# ─────────────────────────────────────────────────────────
#  自我測試(--selftest):不碰任何遊戲檔,全部在一個丟棄式資料夾裡做
#
#  每一道新守門都配一個「餌」—— 先製造出那個守門要擋的情況,再確認它真的擋了,
#  而且該保住的東西一個位元組都沒少。沒有反向測試的檢查,分不出
#  「沒問題」跟「根本沒跑」(本站 2026-08-29 就吃過這個虧:一整批檢查器
#  看起來全綠,實際上是通過時不出聲)。
# ─────────────────────────────────────────────────────────
def _fake_roster(rows=6, speed=50):
    """造一份最小的名冊:表頭三欄 + 幾列球員,格式跟真的 attrib.dat 一樣。

    刻意用第 2 欄放 speed(真檔是 22 或 23),這樣「欄號從表頭現找」
    那條路也順便驗到了 —— 寫死欄號的話這個測試會當場紅。
    """
    head = b'0 first_name,1 last_name,2 playerattrib_speed'
    body = [b'id%03d,0 First%03d,1 Last%03d,2 %d' % (i, i, i, speed)
            for i in range(rows)]
    return b'\r\n'.join([head] + body) + b'\r\n'


def selftest():
    """跑一次全部的守門,回傳 0 代表全綠。不需要遊戲資料夾,也不碰任何遊戲檔。

    測試過程本身會呼叫 cmd_set / cmd_restore,它們會印一大堆東西,
    所以整段的輸出先收起來 —— 只有在有一條紅的時候才把它倒出來,
    那時候那些畫面正好是現場。

    餌的數目不寫死,由 bait() 自己數(2026-09-06 改)——
    寫死的數字會在下一個人加餌的那一天變成假話。
    """
    # ── 不准在 python -O 底下假綠(2026-09-06 第三輪,全站統一)───────
    # -O 會把 assert 整句拿掉。這一支的檢查是 check() 自己 raise AssertionError,
    # -O 拿不掉它 —— 但這道守門照樣要有:全站每一支的 --selftest 都得在 -O
    # 底下講同一句話,而且哪天有人在這裡補一句普通的 assert,
    # 沒有這道守門就會靜靜地變成假綠。
    if sys.flags.optimize:
        print('--selftest 不能在 python -O 下跑:-O 會把 assert 全部拿掉,測試會假綠')
        return 2

    global SPEED_FIELD, _APPLIED
    import io as _io
    import contextlib
    noise = _io.StringIO()
    ok = []
    baits = []

    def check(cond, why):
        if not cond:
            raise AssertionError(why)
        ok.append(why)

    def bait(what):
        """標記一個反向餌開始了:先製造出守門要擋的情況,再確認它真的擋了。"""
        baits.append(what)

    try:
        with contextlib.redirect_stdout(noise):
            _selftest_body(check, bait)
    except BaseException:
        sys.stdout.write(noise.getvalue())
        print('\n自我測試:有一條沒過(前面 %d 條是過的)' % len(ok))
        raise
    print('自我測試:全部通過(%d 項,含 %d 個反向餌)' % (len(ok), len(baits)))
    return 0


def _selftest_body(check, bait):
    """實際的測試內容。拆出來是為了讓上面那層可以把輸出收乾淨。"""
    global SPEED_FIELD, _APPLIED
    import io as _io
    import contextlib
    with tempfile.TemporaryDirectory() as box:
        outside = os.path.join(box, 'outside.txt')
        with open(outside, 'wb') as f:
            f.write(b'DO-NOT-TOUCH')
        gamedir = os.path.join(box, 'game', 'data', 'database')
        os.makedirs(gamedir)
        dat = os.path.join(gamedir, 'attrib.dat')
        bak = dat + '.speedbak'
        original = _fake_roster()

        def fresh():
            """把丟棄式資料夾恢復成「只有一份名冊」的乾淨狀態。"""
            for n in os.listdir(gamedir):
                q = os.path.join(gamedir, n)
                if os.path.islink(q) or os.path.isfile(q):
                    os.remove(q)
            with open(dat, 'wb') as f:
                f.write(original)

        def leftovers():
            return sorted(n for n in os.listdir(gamedir)
                          if n not in ('attrib.dat', 'attrib.dat.speedbak'))

        # ── 一、陰性對照:正常流程真的會寫、真的會產生備份 ───────────────
        #    這一條沒先站住的話,底下每一個「有沒有被動到」的餌都可能是
        #    「因為根本沒跑到那裡」而綠的。
        fresh()
        _APPLIED = False
        raw, lines = read_attrib(dat)
        SPEED_FIELD = resolve_field(lines, SPEED_NAME)
        check(SPEED_FIELD == 2, '欄號沒有從表頭讀出來')
        cmd_set(dat, lines, 'First001', 77, True)
        after = open(dat, 'rb').read()
        check(after != original, '陰性對照失敗:--apply 竟然沒有改到檔案')
        check(os.path.isfile(bak) and open(bak, 'rb').read() == original,
              '陰性對照失敗:備份沒有產生,或內容不是動手之前那一份')
        check(after.count(b'\r\n') == original.count(b'\r\n'), '行數變了')
        check(_APPLIED is True, 'os.replace 做過了,_APPLIED 卻還是 False')
        check(leftovers() == [], '寫完之後還有暫存檔留在資料夾裡:%s' % leftovers())

        # 餌:沒有 --apply 就一個位元組都不可以動
        before = open(dat, 'rb').read()
        _raw, l2 = read_attrib(dat)
        cmd_set(dat, l2, 'First002', 11, False)
        check(open(dat, 'rb').read() == before, '沒加 --apply 竟然改到了檔案')

        # ── 二、還原:換回去要是原子的,而且真的換回來了 ────────────────
        _APPLIED = False
        cmd_restore(dat)
        check(open(dat, 'rb').read() == original, '還原之後內容不等於備份')
        check(_APPLIED is True, '還原換過檔了,_APPLIED 卻還是 False')
        check(leftovers() == [], '還原之後還有暫存檔留在資料夾裡:%s' % leftovers())

        # 餌 1:換上去那一步失敗 —— 正本必須原封不動,不可以停在半截。
        #      舊版是 shutil.copy2(bak, dst),先把正本截成 0 再寫,
        #      實測 840,643 bytes 的名冊會停在 200,000 bytes。
        bait('換上去那一步失敗,正本卻被動到')
        fresh()
        with open(bak, 'wb') as f:
            f.write(_fake_roster(speed=99))
        keep = open(dat, 'rb').read()
        real_replace = os.replace

        def boom(a, b):
            raise OSError(28, '模擬:換名的時候磁碟滿了')
        os.replace = boom
        try:
            cmd_restore(dat)
        except BaseException:
            pass
        finally:
            os.replace = real_replace
        check(open(dat, 'rb').read() == keep,
              '換名失敗時正本被動到了(舊版會被截斷)')
        check(leftovers() == [], '換名失敗之後暫存檔沒收乾淨:%s' % leftovers())

        # 餌 2:讀回來的內容跟備份對不上 —— 不可以換上去。
        #      把 _sha256 換掉來製造這個情況,不然正常路徑上碰不到。
        bait('讀回來跟備份對不上,卻還是換上去了')
        real_sha = globals()['_sha256']
        seen = []

        def liar(p):
            seen.append(p)
            return 'a' * 64 if len(seen) == 1 else 'b' * 64
        globals()['_sha256'] = liar
        try:
            cmd_restore(dat)
        except BaseException:
            pass
        finally:
            globals()['_sha256'] = real_sha
        check(open(dat, 'rb').read() == keep, '雜湊對不上卻還是換上去了')
        check(leftovers() == [], '雜湊對不上之後暫存檔沒收乾淨:%s' % leftovers())

        # 餌 3:半截的備份要被擋下來(這是上一輪就有的守門,一起回歸測試)
        bait('半截的備份被拿去覆蓋正本')
        fresh()
        with open(bak, 'wb') as f:
            f.write(_fake_roster()[:40])
        keep = open(dat, 'rb').read()
        try:
            cmd_restore(dat)
            raise AssertionError('半截的備份竟然通過了')
        except (DataError, SystemExit):
            pass
        check(open(dat, 'rb').read() == keep, '半截備份被擋下來了,正本卻被動到')

        # ── 三、符號連結:資料夾外面的檔一個位元組都不可以被碰到 ──────────
        # 餌 4:事先佔住舊版那個猜得到的備份暫存檔名。
        #      舊版走 copy2 會沿著它把 outside.txt 覆蓋成整份名冊。
        bait('備份的暫存檔名被連結佔住,寫到資料夾外面去')
        fresh()
        os.symlink(outside, bak + '.part')
        raw, lines = read_attrib(dat)
        keep = open(dat, 'rb').read()
        cmd_set(dat, lines, 'First003', 66, True)
        check(open(outside, 'rb').read() == b'DO-NOT-TOUCH',
              '資料夾外面那個檔被 .part 連結帶著改掉了')
        check(open(bak, 'rb').read() == keep, '備份的內容不是動手之前那一份')

        # 餌 5:事先佔住舊版那個猜得到的寫入暫存檔名。
        bait('寫入的暫存檔名被連結佔住,寫到資料夾外面去')
        fresh()
        os.symlink(outside, dat + '.tmp')
        raw, lines = read_attrib(dat)
        cmd_set(dat, lines, 'First004', 55, True)
        check(open(outside, 'rb').read() == b'DO-NOT-TOUCH',
              '資料夾外面那個檔被 .tmp 連結帶著改掉了')

        # 餌 6:備份這個名字本身就是一條指出去的連結 —— 必須整個停手。
        #      舊版 os.path.isfile(連結) 回 True,會印「備份已存在」然後照樣改名冊。
        bait('備份是符號連結,卻照樣往下改名冊')
        fresh()
        os.symlink(outside, bak)
        raw, lines = read_attrib(dat)
        keep = open(dat, 'rb').read()
        try:
            cmd_set(dat, lines, 'First005', 44, True)
            raise AssertionError('備份是符號連結,竟然還是往下寫了')
        except DataError as e:
            check('符號連結' in str(e),
                  '停手的理由不是符號連結,可能是別的錯先擋下來了:%s' % e)
        check(open(dat, 'rb').read() == keep, '備份是連結時名冊仍被改到')
        check(open(outside, 'rb').read() == b'DO-NOT-TOUCH', '外面那個檔被寫到了')
        # 同一個位置有兩道:cmd_set 外層先擋,_atomic_copy 自己也擋一次。
        # 上面那幾條只驗得到外層 —— 把外層拆掉照樣是綠的(實測過),
        # 所以內層要自己被叫一次才算驗過。
        try:
            _atomic_copy(dat, bak)
            raise AssertionError('_atomic_copy 對著符號連結竟然照樣備份下去')
        except DataError as e:
            check('符號連結' in str(e), '_atomic_copy 停手的理由不是符號連結:%s' % e)
        check(open(outside, 'rb').read() == b'DO-NOT-TOUCH',
              '_atomic_copy 被擋下來時外面那個檔仍被寫到')
        # 還原那條路的內層(_do_copy 自己擋)同理。這裡用「指向真檔」的連結,
        # 守門拆掉的話它會把名冊換成外面那個 12 bytes 的檔,紅得看得懂;
        # 用懸空連結的話會紅在 FileNotFoundError,看不出是哪一道倒了。
        try:
            _do_copy(bak, dat)
            raise AssertionError('_do_copy 對著符號連結竟然照樣換上去')
        except DataError as e:
            check('符號連結' in str(e), '_do_copy 停手的理由不是符號連結:%s' % e)
        check(open(dat, 'rb').read() == keep, '_do_copy 被擋下來時名冊仍被動到')

        # 餌 7:名冊本身是一條指出去的連結 —— 也必須整個停手。
        #      ⚠️ lines 要先從「還是真檔」的時候讀出來再換成連結。
        #         隨便傳一個空 lines 的話,find_target 會先丟 DataError,
        #         這個測試就會在「根本沒走到守門」的情況下綠掉(第一版就是這樣)。
        bait('名冊是符號連結,卻照樣往下寫')
        fresh()
        _raw7, lines7 = read_attrib(dat)
        os.remove(dat)
        os.symlink(outside, dat)
        try:
            cmd_set(dat, lines7, 'First000', 44, True)
            raise AssertionError('名冊是符號連結,竟然還是往下寫了')
        except DataError as e:
            check('符號連結' in str(e),
                  '停手的理由不是符號連結,可能是別的錯先擋下來了:%s' % e)
        check(open(outside, 'rb').read() == b'DO-NOT-TOUCH',
              '名冊是連結時外面那個檔被寫到了')
        os.remove(dat)

        # 餌 8:--restore 的備份是一條「指向不存在的檔」的連結。
        #      os.path.exists() 對這種連結回 False,只看它會把停手的理由
        #      說成「找不到備份」—— 診斷是錯的,而且連結另一頭那個檔
        #      會被 open(..., 'wb') 憑空建出來。這裡確認兩件事都沒發生。
        bait('備份是懸空連結,診斷說成「找不到備份」而且把外面那個檔建出來')
        fresh()
        ghost = os.path.join(box, 'ghost.dat')
        os.symlink(ghost, bak)
        keep = open(dat, 'rb').read()
        try:
            cmd_restore(dat)
            raise AssertionError('備份是空連結,竟然還是往下走了')
        except DataError as e:
            check('符號連結' in str(e), '停手的理由被說成別的:%s' % e)
        check(not os.path.lexists(ghost), '連結另一頭那個檔被憑空建出來了')
        check(open(dat, 'rb').read() == keep, '名冊被動到了')

        # ── 四、複驗不過要退回去,不可以留一份壞掉的名冊 ─────────────────
        # 餌 9:讓寫出去的內容故意不對(把重組那一步換掉),
        #      複驗必須抓到、必須丟例外、而且必須把名冊退回原狀。
        bait('寫出去的內容不對,複驗竟然通過')
        fresh()
        _APPLIED = False
        raw, lines = read_attrib(dat)
        real_build = globals()['build_new_line']

        def sabotage(line_bytes, new_val):
            return real_build(line_bytes, new_val + 1)   # 寫進去的值差 1
        globals()['build_new_line'] = sabotage
        try:
            cmd_set(dat, lines, 'First001', 33, True)
            raise AssertionError('寫進去的值不對,複驗竟然通過了')
        except DataError as e:
            check('複驗不通過' in str(e), '複驗失敗的訊息沒有講清楚:%s' % e)
            check('已自動退回' in str(e), '備份是這次剛做的,卻沒有自動退回去')
        finally:
            globals()['build_new_line'] = real_build
        check(open(dat, 'rb').read() == original, '複驗不過之後名冊沒有退回原狀')
        check(_APPLIED is False, '已經退回原狀了,_APPLIED 卻還是 True')

        # 餌 10:備份是更早以前留下的(不是這次做的)—— 不可以自作主張退回去,
        #      只能把 --restore 指令告訴使用者。
        bait('舊備份被自作主張拿去還原')
        fresh()
        with open(bak, 'wb') as f:
            f.write(_fake_roster(speed=1))
        raw, lines = read_attrib(dat)
        globals()['build_new_line'] = sabotage
        try:
            cmd_set(dat, lines, 'First001', 33, True)
            raise AssertionError('寫進去的值不對,複驗竟然通過了')
        except DataError as e:
            check('--restore' in str(e), '沒有把還原指令印出來')
            check('已自動退回' not in str(e), '舊備份竟然被拿去自動還原了')
        finally:
            globals()['build_new_line'] = real_build
        check(open(bak, 'rb').read() == _fake_roster(speed=1), '舊備份被蓋掉了')

        # ── 五、Ctrl-C 不可以說謊(2026-09-06 第三輪稽核加)──────────────
        # 餌 11:Ctrl-C 真的被押到「換名 + 登記」那一段外面。
        #      這裡不真的殺自己一次(os.kill 在 Windows 上的語義跟 POSIX 不同,
        #      放進讀者會跑的 --selftest 太脆),改成驗三件事:進去之後 SIGINT
        #      的處理器換成我們的、收到訊號的時候區段裡的程式照樣跑完、
        #      離開之後才把 KeyboardInterrupt 丟出來而且原本的處理器裝回去。
        #      真的送一次訊號的版本在本輪的稽核紀錄裡(變體檔 T1 / T2)。
        bait('_NoInterrupt 沒有真的把 Ctrl-C 押到區段外面')
        before_handler = signal.getsignal(signal.SIGINT)
        seq = []
        try:
            with _NoInterrupt() as ni:
                # 用 __func__ 比,不要用 is:每次取 ni._remember 都會現做一個新的
                # bound method 物件,is 一定不成立 —— 那是量錯,不是防線壞了。
                check(getattr(signal.getsignal(signal.SIGINT), '__func__', None)
                      is _NoInterrupt._remember,
                      '_NoInterrupt 沒有真的接管 SIGINT,「押後」是假的')
                ni._remember(signal.SIGINT, None)     # 等同「這一刻按了 Ctrl-C」
                seq.append('區段裡跑完了')
        except KeyboardInterrupt:
            seq.append('離開之後才丟出來')
        check(seq == ['區段裡跑完了', '離開之後才丟出來'],
              'Ctrl-C 沒有被押到區段外面:%s' % seq)
        check(signal.getsignal(signal.SIGINT) is before_handler,
              '離開之後沒有把原本的 SIGINT 處理器裝回去')

        # 餌 12:被中斷時講的那幾句話要跟硬碟上的狀態對得上。三態各驗一次,
        #      最要緊的是中間那一態:換名那一步被打斷,不可以講成「沒動到」。
        bait('三態的收尾訊息講錯話')

        def _say():
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                _interrupt_report()
            return buf.getvalue()

        _APPLIED = False
        del _INFLIGHT[:]
        del _BACKED_UP[:]
        del _DONE[:]
        check('沒有改到任何檔案' in _say(), '兩態都是空的,那就該說沒動到')
        _BACKED_UP.append(bak)
        say = _say()
        check('沒有改到任何檔案' in say and os.path.basename(bak) in say,
              '這一次建立過備份,收尾卻一個字都沒提:%s' % say)
        del _BACKED_UP[:]
        _INFLIGHT.append(('write', dat))
        say = _say()
        check('沒有改到任何檔案' not in say and '正在替換' in say and '--restore' in say,
              '中斷時卡在換名那一步,竟然講成「沒動到」:%s' % say)
        del _INFLIGHT[:]
        _APPLIED = True
        _DONE.append(('write', dat))
        say = _say()
        check('沒有改到任何檔案' not in say and '已經換過了' in say and '--restore' in say,
              '已經換過去了,竟然講成「沒動到」:%s' % say)
        check(os.path.basename(dat) in say, '已經換過去了,卻沒有講是哪一個檔:%s' % say)
        _APPLIED = False
        del _DONE[:]

        # 餌 13:換名那一步丟出來的如果不是 OSError,「正在換」這一態就不可以
        #      被收掉。訊號如果剛好落在改名那個系統呼叫上,浮上來的是
        #      KeyboardInterrupt,而那種情形「換過去了沒有」是不知道的 ——
        #      收掉這一態等於替它說了「沒動到」,而檔案其實已經換過去了。
        bait('換名被訊號打斷,收尾卻說成「沒動到」')
        fresh()
        _APPLIED = False
        del _INFLIGHT[:]
        _raw13, lines13 = read_attrib(dat)
        real_replace13 = os.replace

        def replace_then_interrupt(a, b):
            # 只在換名冊那一次動手 —— 備份那一次也丟的話,中斷點會落在
            # 建備份那一步,這個餌就驗不到它要驗的東西了。
            real_replace13(a, b)                     # 真的換過去了
            if os.fspath(b) == dat:
                raise KeyboardInterrupt              # 訊號剛好落在這一步
        os.replace = replace_then_interrupt
        try:
            cmd_set(dat, lines13, 'First001', 88, True)
            raise AssertionError('這個餌應該要把 KeyboardInterrupt 丟出來')
        except KeyboardInterrupt:
            pass
        finally:
            os.replace = real_replace13
        check(open(dat, 'rb').read() != original,
              '陰性對照:這個餌本來就該真的把檔案換過去,沒換的話分不出擋沒擋')
        say = _say()
        check('沒有改到任何檔案' not in say,
              '換名被訊號打斷、檔案其實已經換過去了,收尾卻說「沒有改到任何檔案」:%s' % say)
        check('正在替換' in say and '--restore' in say,
              '不敢說死的那一態沒有把下一步講清楚:%s' % say)
        del _INFLIGHT[:]
        del _DONE[:]
        del _BACKED_UP[:]
        _APPLIED = False

        # 餌 14:不是 Ctrl-C、也不是它自己認得的錯,收尾一樣不可以說謊
        #      (2026-09-11 加)。修這一條之前,__main__ 只接 DataError 與
        #      KeyboardInterrupt,其餘例外直接吐 traceback —— 而檔案可能
        #      已經換過去了。本站實測(scratch 複本,沒碰任何遊戲正本):
        #      把 cmd_restore() 裡 os.replace 之後那一行改成丟 OSError,
        #      畫面只有 traceback、結束代碼 1,而名冊的 sha256 早就變回
        #      備份那一份。這個餌驗兩件事,缺一件那道守門就是啞的:
        #        (1) _unexpected_report() 三態各講對話;
        #        (2) __main__ 真的把它接起來了 —— 函式寫得再對,
        #            沒有接起來的話那條路照樣只有 traceback。
        bait('出了預料之外的狀況,收尾卻沒有講硬碟上的狀態')

        def _say_err():
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                _unexpected_report()
            return buf.getvalue()

        _APPLIED = False
        del _INFLIGHT[:]
        del _DONE[:]
        say = _say_err()
        check('沒有改到任何檔案' in say and '出錯' in say,
              '兩態都是空的,那就該說沒動到,而且要講明是出錯不是中斷:%s' % say)
        _INFLIGHT.append(('write', dat))
        say = _say_err()
        check('沒有改到任何檔案' not in say and '正在替換' in say and '--restore' in say,
              '出錯時卡在換名那一步,竟然講成「沒動到」:%s' % say)
        del _INFLIGHT[:]
        _APPLIED = True
        _DONE.append(('write', dat))
        say = _say_err()
        check('沒有改到任何檔案' not in say and '已經換過了' in say and '--restore' in say,
              '出錯之前就已經換過去了,竟然講成「沒動到」:%s' % say)
        check(os.path.basename(dat) in say, '已經換過去了,卻沒有講是哪一個檔:%s' % say)
        _APPLIED = False
        del _DONE[:]
        # Ctrl-C 那一條的字句不可以被這次的共用改掉 —— 兩條共用 _state_report,
        # 只有開頭那兩個詞不一樣,所以順手把它也對一次。
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            _interrupt_report()
        check('已中斷,沒有改到任何檔案。' in buf.getvalue(),
              'Ctrl-C 那一條的字句被改掉了:%s' % buf.getvalue())
        # (2):驗「有沒有真的接起來」。少了 __main__ 那一條 except,
        #     上面三條照樣全綠,而讀者看到的還是 traceback。
        try:
            _src = open(os.path.abspath(__file__), 'rb').read().decode('utf-8')
        except (OSError, UnicodeDecodeError) as e:
            _src = ''
            check(False, '讀不回自己的原始碼,驗不到收尾有沒有接起來(%s)' % e)
        _tail = _src.split("if __name__ == '__main__':")[-1]
        check('except Exception' in _tail and '_unexpected_report()' in _tail,
              '__main__ 沒有把「預料之外的例外」接起來,那條路還是只會吐 traceback')
        check('except BaseException' not in _tail,
              '__main__ 接了 BaseException —— SystemExit 與 Ctrl-C 會被它吃掉')


if __name__ == '__main__':
    # --selftest 要排在最前面判斷:它不需要遊戲資料夾,
    # 走進 main() 反而會因為「沒給路徑」被 argparse 擋下來。
    # 這一條是額外加的,原本那幾行指令的用法一個字都沒有變。
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    try:
        sys.exit(main())
    except DataError as e:
        print('\n❌ %s' % e)
        sys.exit(1)
    except KeyboardInterrupt:
        # ⚠️ 2026-09-05 訂正:舊版無論如何都印「沒有改到任何檔案」。
        #    中斷點如果落在 os.replace 之後(複驗、印畫面都還要跑一段),
        #    那句話就是假的 —— 而它會讓人以為不必還原。
        #    2026-09-06:改成三態(沒動到 / 正在換 / 已換),由 _interrupt_report
        #    負責講話,--selftest 驗得到它講了什麼。三種情形都 exit 130。
        _interrupt_report()
        sys.exit(130)
    except Exception as e:
        # ⚠️ 2026-09-11 補:這一條原本沒有人接。DataError 以外的例外
        #    (例如換名成功之後才發生的讀檔失敗)會直接吐一整段 Python
        #    traceback —— 而那時候名冊**可能已經被換過了**,traceback 裡
        #    一個字都看不出這件事,讀者於是不知道自己該不該 --restore。
        #    現在照跟 Ctrl-C 同一套三態把硬碟上的狀態講一次再結束(代碼 1)。
        #    ⚠️ 只接 Exception,不接 BaseException:SystemExit 要照原樣往上走
        #       (--restore 那幾道守門就是用它把話講完再結束的),
        #       KeyboardInterrupt 由上面那一條負責,兩條都不可以被這裡吃掉。
        print('\n❌ 出了預料之外的狀況:%s: %s' % (type(e).__name__, e))
        print('   這不是你打錯,是這支腳本沒有預料到的情形。')
        print('   下面這段講的是「你的檔案現在到底怎麼樣」,連同上面那行一起回報:')
        print('   https://toniliumvp.github.io/MVPBaseball/report.html')
        _unexpected_report()
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
