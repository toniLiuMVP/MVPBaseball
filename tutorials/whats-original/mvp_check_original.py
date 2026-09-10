#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mvp_check_original.py — 看看你的 MVP Baseball 2005 有哪些檔還沒被動過。

    python3 mvp_check_original.py "遊戲安裝資料夾"

原理只有一句話:遊戲資料夾裡凡是修改時間還停在 2004 或 2005 年的檔案,
多半還是原廠那一份;時間比較新的,代表被某個東西寫過。

判準是「年份是不是 2004 或 2005」(底下的 SHIP_YEARS),不是某一段幾個月的區間。
放寬到整整兩年,是因為不同地區、不同版本的壓片日期不一樣,而且出廠期那一堆檔
本來就散得很開:本站測試機那一份 data 重新掃過,被算成出廠期的檔最早是
2004-05-04、最晚是 2005-02-09,其中 25 個早於 2004 年 12 月。
剛安裝好的原版也一樣,它的 data 底下最早的檔是 2004-05-01。
你自己那一份的數字不一樣是正常的。

這支程式全程唯讀。它不會修改、搬移或刪除任何檔案,也不會連網。
整份只有讀取檔案屬性的呼叫,沒有一處寫入。

⚠️ 時間戳是線索,不是證據。三種情況會讓它說謊:
   1. 有些複製方式不保留原始時間(檔案會變成「今天」)
   2. 模組作者可以刻意把時間改回去
   3. 工具只是讀過檔案卻順手重寫了一次,內容其實沒變
   所以請把它當成「先看哪裡」的地圖,不要當成判決。

── 輸入 ─────────────────────────────────────────────
  一個路徑,指到遊戲的安裝資料夾。
  如果那底下有 data,腳本就只掃 data:安裝程式、說明檔、執行檔本來就不是
  判斷模組的線索,混進來只會把比例稀釋掉。
  以 - 開頭的參數一律當旗標略過,所以 -h 與 --help 不會被誤當成路徑。

── 輸出 ─────────────────────────────────────────────
  只印到畫面,不產生任何檔案:
    【1】總共幾個檔,其中幾個落在出廠期,佔幾成;
         如果有路徑讀不進去(權限不足或掃描當下被鎖住),會在這一段
         底下列出來並講明「沒有算進上面那個比例」。
    【2】每一年各有幾個檔,附一條 # 長條圖
    【3】各個第一層子資料夾:檔數、出廠期檔數、比例,
         以及「最新被動過的那一個檔」(比的是修改時間,不是只比年份)
    【4】怎麼讀這份結果
  結束碼:0 = 跑完了或印出說明,1 = 路徑不存在、資料夾裡沒有檔案,
  或那個資料夾整個讀不進去。
  ⚠️ 開頭那一行「掃描 …」印的是你自己給的完整路徑。如果遊戲裝在
     你的家目錄（帳號名那一層） 這種地方,把整段輸出貼給別人之前記得先遮掉;
     【3】那一欄的檔名是相對路徑,不帶你的帳號名。

── 安全網在哪 ───────────────────────────────────────
  不需要,因為它沒有可以出錯的動作:整份只有 os.walk、os.stat、os.path.*
  這些讀取呼叫,連一個 open() 都沒有,不寫入、不刪除、不搬移,也不連網。
  (另外用 unicodedata 算中文字在終端機佔幾格,那個只看字串,不碰檔案。)

── 做不到的事 ───────────────────────────────────────
  · 證明不了內容有沒有變。時間戳是檔案的屬性,不是內容的雜湊;
    要確定只有逐位元組比對一途(本站的 mvp_fingerprint.py 做那件事)。
  · 分不出是誰改的。它只知道某個檔的時間不在出廠期,不知道是哪個模組寫的。
  · 只分到第一層子資料夾。frontend 底下再分幾層,全部算進 frontend 那一列。
  · 它讀的是「最後修改時間」。有些系統另外還記著建立時間,這支不看那一個。
  · 讀不進去的路徑不會被算進來。它不會安靜地跳過去 —— 有幾個、是哪幾個
    都印在【1】底下,但那些檔的年份確實不在統計裡,比例是「讀得到的那些」
    算出來的。

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
import sys
import time
import unicodedata

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


# 遊戲出貨的時間範圍。放寬到整個 2004 與 2005 年,
# 因為不同地區、不同版本的壓片日期不一樣。
# 底下是用 `y in SHIP_YEARS` 比對,也就是「是不是這兩個年份之一」,
# 不是「介於兩者之間」;2006 年的檔就不算出廠期了。
# 這兩個數字決定【1】那個百分比,改它等於改掉整份報告的判準。
SHIP_YEARS = (2004, 2005)


def human(n):
    """把位元組數換成人看得懂的單位。1 KB 一律當 1024 bytes 算。

    ⚠️ 目前這支腳本沒有任何地方呼叫它:scan() 確實把每個資料夾的總位元組數
       累加在 d['bytes'] 裡,但【3】那張表最後沒有印出那一欄。
       寫在這裡是為了讓讀原始碼的人不用自己找一遍。
    """
    # 逐級除以 1024,除到數字小於 1024 或者已經升到 GB 為止。
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            # bytes 印整數(位元組再切小數沒有意義),其他單位印一位小數。
            return '%.1f %s' % (n, unit) if unit != 'bytes' else '%d bytes' % n
        n /= 1024.0


def pad(s, width, right=False):
    """把字串補到指定的「顯示寬度」,超出就切掉尾巴。中文字算兩格。

    不能直接用 '%-16s':那個數的是字元數,一個中文字算一格,
    但終端機上它佔兩格 —— 只要資料夾名有中文(台灣模組包很常見,
    像 `fonts - 舊版備份`),整張表就會被推歪。
    east_asian_width 回 'W'(寬)或 'F'(全形)的字算兩格,其餘算一格。
    """
    w = 0
    kept = []
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
        if w + cw > width:
            break        # 切在中文字的前面,不會切出半個字
        kept.append(ch)
        w += cw
    fill = ' ' * (width - w)
    return fill + ''.join(kept) if right else ''.join(kept) + fill


def scan(root):
    """回傳 {子資料夾: {'n':檔數, 'ship':出廠期檔數, 'bytes':總大小,
                        'newest':(修改時間, 年, 相對路徑) 或 None}}

    第二個回傳值是 {年份: 檔數},給【2】那張長條圖用。
    第三個回傳值是「讀不進去而被跳過的路徑」清單(相對於 root)。
    整個函式只呼叫 os.walk 與 os.stat,一個檔案的內容都沒有打開。
    """
    out = {}
    years = {}
    skipped = []

    def note(p):
        # os.walk 預設會把讀不進去的資料夾「整個安靜地跳過」。
        # 對這支腳本特別致命:它的產出就是一個百分比,少算的檔不會留下痕跡,
        # 讀者看到的比例是錯的而他不會知道。所以全部收起來,最後印出來。
        # 存相對路徑而不是絕對路徑:這份輸出很多人會整段貼給別人看。
        try:
            rel = os.path.relpath(p, root)
        except (ValueError, TypeError):
            # ValueError:Windows 跨磁碟機時 relpath 會丟例外。
            # TypeError:例外物件沒有 filename(p 是 None)。
            rel = str(p)
        # relpath 會把 root 自己算成 '.',單獨印一個點沒有人看得懂。
        skipped.append('(你給的那個資料夾本身)' if rel == '.' else rel)

    # onerror 收的是「打不開這個資料夾」;底下 os.stat 的 except 收的是
    # 「這一個檔的屬性讀不到」。兩種都要記,不然比例會靜靜地少算。
    walk = os.walk(root, onerror=lambda e: note(getattr(e, 'filename', None)))
    for dirpath, dirnames, filenames in walk:
        # 就地改寫 dirnames 是 os.walk 的用法:改這個 list 才會讓它不要走進去,
        # 把新的 list 指派給別的名字沒有用。
        # 跳過 . 開頭是為了略過 .git 這類跟遊戲無關的東西,它們會把年份分布拉歪。
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in filenames:
            # 檔案同理,略過 .DS_Store 這種作業系統自己產生的。
            if fn.startswith('.'):
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                # 權限不足、連結斷掉、掃到一半檔案被刪掉:
                # 跳過這一個就好,不要讓整份掃描中斷在別人的一個壞檔上。
                # 但要記下來 —— 跳過幾個檔就是少算幾個檔。
                note(p)
                continue
            # st_mtime 是「最後修改時間」,用本機時區換算成年份。
            # 跨時區看同一份檔案,12/31 與 1/1 的檔可能被分到不同年;
            # 對這個用途無所謂,因為判準是「2004-2005 還是更後面」。
            y = time.localtime(st.st_mtime).tm_year
            years[y] = years.get(y, 0) + 1
            rel = os.path.relpath(dirpath, root)
            # 只取第一層資料夾名當分組。stadium\a\b\c.big 一律算進 stadium 那一列,
            # 因為玩家換模組的單位就是「哪一個資料夾」,不是「第幾層」。
            top = rel.split(os.sep)[0] if rel != '.' else '(根目錄)'
            d = out.setdefault(top, {'n': 0, 'ship': 0, 'bytes': 0, 'newest': None})
            d['n'] += 1
            d['bytes'] += st.st_size
            if y in SHIP_YEARS:
                d['ship'] += 1
            elif d['newest'] is None or st.st_mtime > d['newest'][0]:
                # 注意這是 elif:出廠期的檔永遠不會更新 newest。
                # 所以 newest 記的是「最新的那個被動過的檔」,
                # 不是「這個資料夾裡最新的檔」。前者才是讀者要找的線索起點。
                # 比的是 st_mtime 不是年份:同一年裡也要挑真正最後被寫過的那一個,
                # 只比年份的話會變成「那一年裡剛好第一個被走到的檔」,跟先後無關。
                d['newest'] = (st.st_mtime, y, os.path.relpath(p, root))
    return out, years, skipped


def main():
    """讀參數、掃一次資料夾,然後把四段報告印出來。"""
    # 這裡濾的是單一個 '-' 開頭(姊妹腳本 mvp_check_setup.py 濾的是 '--'),
    # 所以 -h 與 --help 都不會被誤當成路徑。
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if '--help' in sys.argv or '-h' in sys.argv or not args:
        # 沒給路徑,跟明講要看說明,都印檔頭那份文件。
        # 這裡回 0 不是 1:使用者問用法而他得到了用法,那不是錯誤。
        print(__doc__)
        return 0

    root = args[0]
    # 給的是安裝資料夾的話就自動縮到 data:遊戲的內容都在那裡,
    # 外面那層是安裝程式與說明檔,混進來只會把出廠期的比例稀釋掉。
    data = os.path.join(root, 'data')
    if os.path.isdir(data):
        root = data
        print('  找到 data 資料夾,只掃它。')
    elif not os.path.isdir(root):
        print('  找不到這個資料夾:%s' % root)
        print('  請把遊戲安裝資料夾的完整路徑放在後面,例如:')
        print('    python3 mvp_check_original.py "C:\\Program Files (x86)\\EA SPORTS\\MVP Baseball 2005"')
        return 1

    print('  掃描 %s' % root)
    print()
    # 只走一次資料夾,四段報告全部從這一次的結果算出來。
    # 走兩次的話,萬一中間有東西變了,兩段報告會互相打架而且沒人看得出來。
    out, years, skipped = scan(root)
    total = sum(d['n'] for d in out.values())
    ship = sum(d['ship'] for d in out.values())
    if not total:
        if skipped:
            # 一個檔都沒讀到、而且掃描過程有東西讀不進去 —— 那是權限問題,
            # 不是路徑問題。講成「路徑可能給錯了」會害讀者去改一個沒有錯的路徑。
            print('  這裡一個檔都讀不到,但不是空的:有 %d 個路徑因為權限不足'
                  % len(skipped))
            print('  或掃描當下被鎖住而跳過:')
            for rel in sorted(skipped)[:5]:
                print('       · %s' % rel)
            if len(skipped) > 5:
                print('       · …還有 %d 個沒列出來。' % (len(skipped) - 5))
            print('  先確認你對它有讀取權限,路徑不必改')
            print('  (Windows 可以改用「以系統管理員身分執行」再跑一次)。')
        else:
            print('  這個資料夾裡沒有檔案。路徑可能給錯了。')
        return 1

    print('  【1】整體')
    print('    共 %d 個檔,其中 %d 個的時間落在 %d-%d 年(%.1f%%)。'
          % (total, ship, SHIP_YEARS[0], SHIP_YEARS[1], ship * 100.0 / total))
    if skipped:
        # 少算的檔一定要講出來,不然上面那個百分比是錯的而沒有人看得出來。
        print('    ⚠️ 另有 %d 個路徑讀不進去(權限不足或掃描當下被鎖住),'
              % len(skipped))
        print('       沒有算進上面這個比例:')
        for rel in sorted(skipped)[:5]:   # 排序過,同一台機器重跑列出來的是同幾個
            print('       · %s' % rel)
        if len(skipped) > 5:
            print('       · …還有 %d 個沒列出來。' % (len(skipped) - 5))
    print()

    print('  【2】各年份有幾個檔')
    # 長條圖以「檔數最多的那一年」當滿格 40 個 #,其他年份照比例縮。
    top = max(years.values())
    for y in sorted(years):
        mark = ' ← 出廠期' if y in SHIP_YEARS else ''
        # max(1, ...) 保證只有一兩個檔的年份也看得到一格。
        # 少了這個保護,那些年會變成空白,看起來像沒有資料而不是「很少」。
        bar = '#' * max(1, int(round(years[y] * 40.0 / top)))
        print('    %d  %5d  %s%s' % (y, years[y], bar, mark))
    print()

    print('  【3】各資料夾')
    # 整份輸出裡最有用的一段。依檔數由多到少排,量體大的資料夾先看到。
    print('    %s %s %s %s   %s'
          % (pad('資料夾', 16), pad('檔數', 6, True), pad('出廠期', 8, True),
             pad('比例', 7, True), '最新被動過的一個'))
    for k, d in sorted(out.items(), key=lambda x: -x[1]['n']):
        pct = d['ship'] * 100.0 / d['n']
        # newest 只有在出現過「非出廠期」的檔時才有值(否則是 None),
        # 所以沒值就代表這個資料夾整個沒被動過。
        newest = '%d 年 %s' % (d['newest'][1], d['newest'][2]) if d['newest'] else '(全是出廠期)'
        # 資料夾欄用 pad() 依「顯示寬度」切到 16 格 —— 中文字佔兩格,
        # 用 %-16s 只要名字有中文就會歪掉。最後一欄在行尾,不影響對齊,
        # 所以照舊用字元數硬切 44。切掉的都是尾巴,前面那段通常就夠認人。
        print('    %s %6d %8d %6.0f%%   %s' % (pad(k, 16), d['n'], d['ship'], pct, newest[:44]))
    print()

    # 最後這一段是固定文字,不是算出來的。放進輸出而不是只寫在網頁上,
    # 是因為很多人只會把終端機的結果複製給別人看,那時候網頁不在旁邊。
    print('  【4】怎麼讀這份結果')
    print('    比例接近 100% 的資料夾:大概沒被動過,可以當成比對的基準。')
    print('    比例很低的資料夾:裝過模組。要還原就從這裡找。')
    print('    ⚠️ 時間戳會說謊 —— 有些複製方式不保留時間,也有人會刻意改。')
    print('       這是「先看哪裡」的地圖,不是判決。')
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
