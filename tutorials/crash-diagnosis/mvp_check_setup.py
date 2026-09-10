#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mvp_check_setup.py
檢查 EA MVP Baseball 2005 的安裝狀況,診斷當機原因。

    python3 mvp_check_setup.py "遊戲安裝資料夾"

例如:
    python3 mvp_check_setup.py "C:\\Program Files (x86)\\EA SPORTS\\MVP Baseball 2005"

這支腳本**全程唯讀**,不會修改任何檔案,只是把幾項資訊讀出來給你看:

  1. 執行檔能用多少記憶體(32 位元程式預設上限 2 GB,是當機的候選原因之一;
     另一層是遊戲自己切的記憶體池,本站那顆執行檔上量到的是 64 MB)
  2. 遊戲資料總量,以及最大的幾個檔案
  3. 常見的安裝問題(檔案缺失、資料夾位置不對)

── 輸入 ─────────────────────────────────────────────
  一個路徑,指到遊戲的安裝資料夾(裡面看得到 .exe 與 data 資料夾的那一層)。
  直接把 mvp2005.exe 拖進來也接受,腳本會自己退到它的上一層。
  以 -- 開頭的參數一律當旗標略過,所以路徑排在旗標後面也讀得到。
  唯一認得的旗標是 --selftest:不讀你的遊戲資料夾,只在記憶體裡把
  【4】那條「哪些檔算備份」的規則驗一次(含兩個故意種下的餌)。
  它拒絕在 python3 -O 底下跑,理由寫在 self_test() 的說明裡。

── 輸出 ─────────────────────────────────────────────
  只印到畫面,不產生任何檔案:
    【1】主程式是幾位元、記憶體上限是 2 GB 還是 4 GB
    【2】data 的總量、.big 個數、最大的五個檔;球場檔另外算一次,印個數與最大的那一個,
        超過 10 MB 的最多再列五個(只有這幾項,沒有中位數也沒有分級)
    【3】四個關鍵檔案在不在
    【4】腳本找到的備份檔(總數會印,路徑最多列 8 個;原廠自己附的那一個另外列,不算你的)
  最後把一路收集到的「值得注意」彙整成一張清單。
  結束碼:0 = 跑完了,1 = 沒給路徑或路徑不存在(或 --selftest 有一項紅了),
          2 = 掃描途中讀取出錯,或是在 python3 -O 底下跑 --selftest(它會拒跑),
          130 = 你按了 Ctrl+C。
  「發現 N 項值得注意」不會改變結束碼,那是給人看的,不是給批次檔判斷的。

── 安全網在哪 ───────────────────────────────────────
  這支不需要備份,也沒有還原功能,因為它沒有可以出錯的動作:
  整份只有讀取用的呼叫(read_bytes、stat、exists、is_dir、glob、rglob、iterdir 這一類),
  沒有任何 open(..., 'w')、沒有刪除、沒有搬移,也不連網。
  --selftest 也一樣:它餵給規則的是假的路徑字串,不建暫存檔、不碰磁碟。
  中途按 Ctrl+C 停掉也不會留下半截檔案,因為根本沒有檔案被打開來寫。
  它的定位是「動手之前的體檢」,體檢本身不該動到病人。

── 做不到的事 ───────────────────────────────────────
  · 量不到遊戲跑起來實際吃掉多少記憶體。【1】讀的是執行檔檔頭裡的一個旗標,
    那是「最多准用多少」,不是「現在用了多少」。
  · 判斷不了模組好不好、相不相容。它只量檔案的大小與在不在。
  · 【3】只看檔案在不在,不開內容,所以「檔案還在但已經壞了」這裡驗不出來。
  · 【4】認得的是本站工具留下的那些副檔名(下面 BAK_SUFFIXES 那份清單)。
    你自己手動複製、改名成別的樣子的備份(例如 attrib 複本.dat),這裡看不到。
  · 球場檔那個 10 MB 是社群傳了二十年的說法,不是本站量到的當機邊界。
    超過只代表值得清一下,不代表一定會當(這一點程式碼裡也有寫)。

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

import struct
import sys
from pathlib import Path

# Windows 主控台預設編碼存不下 ✓ ✗ 這類符號,先把輸出轉成 UTF-8。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

# PE Characteristics 旗標
# (前兩個是 Characteristics 裡的位元,後兩個是 Machine 欄位的值,
#  數值都來自 PE 格式本身,不是本站定義的。)
# 0x0020 = 大位址支援。32 位元程式開了它,位址空間上限從 2 GB 變成 4 GB。
# 0x0100 = 這支程式只跑得動 32 位元機器。目前這份程式碼沒有讀這個位元。
# 0x014C / 0x8664 是 Machine 欄位最常見的兩個值:x86 與 x64。
IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020
IMAGE_FILE_32BIT_MACHINE = 0x0100
MACHINE_I386 = 0x014C
MACHINE_AMD64 = 0x8664


def read_pe_info(exe: Path):
    """讀 PE 檔頭,回傳 (machine, characteristics)。不是 PE 就回 None。

    Windows 執行檔的檔頭是一串固定位移的欄位,這裡用到五個(這個數目是照這個函式自己的
    程式碼數的,下面五個欄位各對應一次讀取。其中三個是數字,用小端序讀,也就是低位的
    位元組放前面;另外兩個是 MZ 與 PE 那兩塊招牌,直接比對位元組,不牽涉小端序):

      位移 0x00   2 bytes   'MZ',1980 年代 DOS 留下來的招牌
      位移 0x3C   4 bytes   PE 檔頭從檔案的哪個位移開始
      PE + 0      4 bytes   'PE' 後面接兩個 0x00
      PE + 4      2 bytes   Machine,給哪一種處理器跑的
      PE + 22     2 bytes   Characteristics,一整排開關,
                            大位址支援就是其中一個位元

    只解析開頭 4096 個位元組:上面那些欄位全部落在這個範圍內。
    ⚠️ 2026-09-03 訂正:這裡原本寫「不必為了看兩個數字把整個執行檔搬進
    記憶體」,那句話是錯的。下面那一行是先用 read_bytes() 把整個檔案讀進
    記憶體,再切出前面 4096 個位元組,整個檔案還是進來了。
    本站在那顆剛安裝好的全新英文原版 mvp2005.exe(6,972,001 bytes)上,
    用 Python 內建的 tracemalloc 量(macOS · Python 3.9.6,兩邊的量測腳本除了
    這一行以外一模一樣):這一行的記憶體峰值是 6,979,611 bytes;改寫成
    with open(exe, 'rb') as f: data = f.read(4096) 是 10,549 bytes,
    兩種寫法拿到的 4096 個位元組完全一樣(sha256 相同)。
    ⚠️ 這兩個數字只有在同一支量測腳本裡才可以互相比較。tracemalloc 的峰值
    連量測腳本自己配置的記憶體都算進去,尾數會隨著你怎麼量浮動幾百個位元組;
    而 open() 收到的是 Path 還是字串又會再差一千多個位元組(傳字串量到的是
    8,989)。站得住的是量級:兩者差了約 660 倍。
    體檢腳本只跑一次,這個差別不影響使用,所以程式碼維持原樣,改的是說明。
    """
    try:
        data = exe.read_bytes()[:4096]
    except OSError:
        # 讀不到就當成「格式讀不出來」處理:同名的資料夾、斷掉的捷徑、
        # 沒有讀取權限都走這裡。體檢工具不該把 traceback 丟給讀者。
        return None
    # 沒有 MZ 招牌就不是 Windows 執行檔。硬解下去只會解出一堆假數字。
    if data[:2] != b'MZ':
        return None
    # 檔案短到連 0x3C 那個欄位都放不下,多半是空檔或沒下載完的半截檔。
    if len(data) < 0x40:
        return None
    # '<I' = 小端序、4 個位元組、無號整數。它的值是 PE 檔頭的位移,不是固定的。
    pe_off = struct.unpack('<I', data[0x3C:0x40])[0]
    # 兩種壞法都要擋:指標指到我們沒讀進來的範圍外,或指到的位置不是 'PE' 招牌。
    # 24 是「從 PE 檔頭起算,要讀到 Characteristics 至少需要這麼多位元組」。
    if pe_off + 24 > len(data) or data[pe_off:pe_off + 4] != b'PE\x00\x00':
        return None
    # '<H' = 小端序、2 個位元組、無號整數。兩個欄位都在 PE 檔頭的固定位移上。
    machine = struct.unpack('<H', data[pe_off + 4:pe_off + 6])[0]
    chars = struct.unpack('<H', data[pe_off + 22:pe_off + 24])[0]
    return machine, chars


def human(n: int) -> str:
    """把位元組數換成人看得懂的單位。1 KB 一律當 1024 bytes 算。"""
    # 逐級除以 1024,除到數字小於 1024 或者已經升到 GB 為止。
    # 不再往上升是因為這個遊戲的資料夾不會到 TB,多一級只是多一個永遠走不到的分支。
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            # bytes 只有在小於 1024 時才會用到,那時印整數就夠,小數點沒有意義;
            # 其他單位印一位小數,「165.0 MB」比「172,992,803 bytes」好讀。
            return f'{n:,.0f} {unit}' if unit == 'bytes' else f'{n:.1f} {unit}'
        n /= 1024
    # 上面那圈跑到 'GB' 時條件一定成立,所以這一行實務上走不到,留著當保險。
    return f'{n:.1f} GB'


# 本站每一支會寫遊戲檔的工具,第一次寫入前都會留一份備份,而且各用各的副檔名
# (.playerbak、.ratingsbak、.portraitbak …),這樣同時跑兩支工具備份不會互相蓋掉。
# 這份清單漏一種,那一支工具留的備份在【4】就完全看不見,而且不會有任何提示 ——
# 讀者會以為自己沒備份。2026-09-05 補齊之前,這裡只有四種,而當時站上已經有 25 種。
# ⚠️ 這份清單要跟「檢查備份夠不夠」那一課的 mvp_check_backup.py 裡那份對得上。
#    兩邊都是逐字寫出的字面字串,所以可以用機器逐條比對,不必用眼睛看。
#    這支腳本要能單獨下載後直接跑(無外部相依),所以是各留一份、靠檢查器對齊,
#    不是 import 對方。多一課會寫檔的教學通常就多一種,所以這裡不寫死「幾種」。
#    順序不影響任何判斷,排成字母序只是給人好找。
BAK_SUFFIXES = (
    '.bak', '.audiobak', '.autobak', '.chantbak', '.datafilebak',
    '.exepebak', '.facebak', '.facetexbak', '.feltoolbak', '.fontbak',
    '.hudcolorbak', '.introbak', '.locbak', '.logobak', '.menutextbak',
    '.modernizebak', '.packbak', '.playerbak', '.portraitbak',
    '.ratingsbak', '.screenbak', '.shrinkbak', '.speedbak', '.unibak',
    '.unpackbak',
)

# ⚠️ EA 自己就在遊戲裡附了一個 .bak。把它算成使用者的備份,
#    等於對一台從沒備份過的全新機器說「這是好習慣」——
#    而這支腳本的用途正是動手前的體檢,方向剛好相反。
# 寫成「斜線 + 小寫」的相對路徑,比對前會把待測路徑也轉成同一種寫法。
SHIPPED_BAKS = {'data/igshapes/igcrsr.fsh.bak'}


def classify_baks(rels, suffixes=BAK_SUFFIXES, shipped_set=SHIPPED_BAKS):
    """把相對路徑分成三堆,回傳 (你自己的備份, 遊戲本來就附的, 不是備份檔)。

    只吃路徑字串、不碰檔案系統,所以 --selftest 可以直接餵假路徑進來驗這條規則。
    比對前先統一成「斜線 + 小寫」:Windows 用反斜線分隔,而且檔名不分大小寫,
    不先統一的話同一份清單在三種作業系統上會對不起來。
    """
    mine, shipped, other = [], [], []
    for rel in rels:
        key = str(rel).replace('\\', '/').lower()
        base = key.rsplit('/', 1)[-1]
        # 用最後一個點之後的部分當副檔名,跟 pathlib 的 .suffix 同一種切法
        # (igcrsr.fsh.bak 取到的是 .bak,不是 .fsh.bak)。
        suf = base[base.rfind('.'):] if '.' in base else ''
        if suf not in suffixes:
            other.append(rel)
        elif key in shipped_set:
            shipped.append(rel)
        else:
            mine.append(rel)
    return mine, shipped, other


def self_test():
    """把【4】那條「哪些檔算備份」的規則當場驗一次,全綠回 True。

    全程只在記憶體裡跑假路徑:不建檔、不刪檔、也不讀你的遊戲資料夾。
    四項裡有兩項是餌 —— 沒有餌的話,一個「什麼都算備份」的爛規則也會全綠。

    在 python3 -O 底下不跑,直接以結束碼 2 收工(不回傳 True/False)。
    """
    # ⚠️ python3 -O 會把整份程式裡的 assert 拿掉。本站其他工具的自我測試是用
    #    assert 判斷的,在 -O 底下那些餌一條都不會執行,螢幕上照樣一路 ✅ ——
    #    那是一片假的綠燈,比沒有測試更危險。
    #    這一支目前用的是 if/else 不是 assert,所以 -O 還不會讓它假綠;擋掉是為了
    #    跟全站的自我測試一致,而且哪天這裡改寫成 assert,守門已經在了,
    #    不必指望那時候有人記得補。
    #    這裡直接結束整支程式,不回傳 —— 「測試沒跑」跟「測試沒過」是兩回事,
    #    用 1(有一項紅了)會把它們混在一起。
    if sys.flags.optimize:
        print('--selftest 不能在 python3 -O 底下跑:-O 會把 assert 整段拿掉,'
              '哪天這裡改用 assert 判斷就會變成一片假的綠燈。請拿掉 -O 再跑一次。')
        sys.exit(2)
    print('【0】自我測試(不碰任何檔案)')
    ok = True

    # 一、清單裡的每一種副檔名都要認得出來
    probes = ['data/database/attrib.dat' + s for s in BAK_SUFFIXES]
    mine, _, other = classify_baks(probes)
    if len(mine) == len(BAK_SUFFIXES) and not other:
        print(f'   ✅ 清單裡 {len(BAK_SUFFIXES)} 種副檔名全部認得')
    else:
        ok = False
        print(f'   ❌ 有 {len(other)} 種沒認出來:{other}')

    # 二、陰性對照:沒在清單裡的副檔名不可以被算成備份。
    #     少了這一條,上面那一項用「什麼都算備份」也會過。
    mine, _, other = classify_baks(['data/database/attrib.dat.neverheardofbak',
                                    'data/database/attrib.dat'])
    if not mine and len(other) == 2:
        print('   ✅ 陰性對照:認不得的副檔名沒有被算成備份')
    else:
        ok = False
        print(f'   ❌ 陰性對照失敗,被算成備份的有:{mine}')

    # 三、餌:把清單砍到只剩 .bak,.ratingsbak 就必須從「你的備份」掉出來。
    #     這是 2026-08-29 真的發生過的漏洞形態 —— 清單漏一種,
    #     那一支工具留的備份就完全看不見,而且是靜默的。
    short, _, _ = classify_baks(['data/database/attrib.dat.ratingsbak'],
                                suffixes=('.bak',))
    full, _, _ = classify_baks(['data/database/attrib.dat.ratingsbak'])
    if not short and len(full) == 1:
        print('   ✅ 餌一:清單砍短之後,.ratingsbak 立刻看不見了(規則真的由清單決定)')
    else:
        ok = False
        print(f'   ❌ 餌一沒抓到(砍短={short} / 完整={full})')

    # 四、餌:遊戲本來就附的那一個要被挑出來,連反斜線與大寫的寫法都要挑得出來;
    #     但同名檔放在別的資料夾就是你自己的備份,不可以一起被吃掉。
    mine, shipped, _ = classify_baks(['data/igshapes/igcrsr.fsh.bak',
                                      'DATA\\IGSHAPES\\IGCRSR.FSH.BAK',
                                      'mymods/igcrsr.fsh.bak'])
    if len(shipped) == 2 and len(mine) == 1:
        print('   ✅ 餌二:原廠那一個(含反斜線/大寫寫法)沒被算成你的,同名副本仍算你的')
    else:
        ok = False
        print(f'   ❌ 餌二失敗(原廠={len(shipped)} 個 / 你的={len(mine)} 個)')

    print('   全綠' if ok else '   有項目沒過')
    return ok

def main():
    """依序跑完四段檢查,把結果印出來,最後彙整成一張「值得注意」的清單。"""
    # 只把「不是以 -- 開頭」的參數當成路徑。這樣以後要加旗標,
    # 不會因為旗標排在前面就把路徑吃掉。
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    # --selftest 不需要路徑:它驗的是規則,不是你的遊戲。
    if any(a.lower() == '--selftest' for a in sys.argv[1:]):
        return 0 if self_test() else 1
    if not args:
        # 沒給路徑就把檔頭那份說明當用法提示印出來,並用 1 表示「什麼都沒做」。
        print(__doc__)
        return 1

    # expanduser 是為了讓 ~/... 這種寫法也能用(Mac 與 Linux 常見)。
    root = Path(args[0]).expanduser()
    if not root.exists():
        print(f'✗ 找不到這個資料夾:{root}')
        return 1
    # 有人會直接把 mvp2005.exe 拖進終端機,而不是拖資料夾。
    # 與其怪他打錯,不如退到它的上一層,那本來就是他想指的地方。
    if root.is_file():                                   # 拖到 exe 也接受
        root = root.parent

    print(f'遊戲資料夾  {root}\n')
    # 一路把「值得注意」收在這個清單裡,最後一起印。
    # 邊跑邊印的話,結論會散在四段輸出中間,讀者得自己往回翻。
    problems = []

    # ── 1. 執行檔記憶體上限 ────────────────────────────
    # MVP 2005 是 32 位元程式,沒開大位址支援的話,
    # 不管電腦插了多少記憶體都只准用 2 GB。
    # ⚠️ 「模組疊多了就是會撞到這個天花板」這句話本站沒有量到。量到的是:
    #    在本站那顆執行檔上,只掛大位址旗標沒有感覺 —— 卡住的是遊戲自己切的
    #    那塊記憶體池(量到 64 MB),那是另一層天花板。
    #    所以這一段給的是候選原因,不是結論。
    print('【1】執行檔能用多少記憶體')
    exes = sorted(root.glob('*.exe'))
    # 挑主程式分三層,由準到寬:精確檔名 → 名字裡有 mvp → 第一個 .exe。
    # 分三層是因為改過的懶人包常常多塞幾個 .exe 進來,
    # 挑錯一個,底下整段結論就是在講別的檔案。
    # 優先精確檔名,避免挑到 "mvp2005 - 備份.exe" 這類副本
    main_exe = next((e for e in exes if e.name.lower() == 'mvp2005.exe'), None)
    if not main_exe:
        main_exe = next((e for e in exes if 'mvp' in e.name.lower()), exes[0] if exes else None)
    # 不只一個 .exe 時,要講清楚報告的是哪一個,
    # 否則讀者會拿這一段結論去對照他心裡想的另一個檔。
    if len(exes) > 1:
        others = [e.name for e in exes if e != main_exe]
        print(f'  註    資料夾裡有 {len(exes)} 個 .exe,以下報告的是 {main_exe.name if main_exe else "?"}')
        print(f'        其他:{", ".join(others[:3])}{"…" if len(others) > 3 else ""}')
    if not main_exe:
        print('  ✗ 這個資料夾裡沒有 .exe,可能不是遊戲安裝資料夾')
        problems.append('找不到遊戲執行檔')
    else:
        info = read_pe_info(main_exe)
        # 大小也可能讀不到:斷掉的捷徑就是這樣,stat 會跟著連結走過去然後撲空。
        # 這裡讀不到不該讓整支停下來 —— 後面三段還是有東西可以給讀者看。
        try:
            size_txt = human(main_exe.stat().st_size)
        except OSError:
            size_txt = '大小讀不到'
        print(f'  檔案  {main_exe.name}({size_txt})')
        if not info:
            print('  ✗ 讀不出程式格式(檔案可能損毀,或指到的是資料夾、斷掉的捷徑、沒有讀取權限的檔)')
            problems.append('執行檔格式異常')
        else:
            machine, chars = info
            # Machine 說的是「給哪種處理器跑的」。MVP 2005 是 2005 年的遊戲,
            # 正常情況會是 0x014C(x86);認不得的值就把原始數字印出來,不要亂猜。
            bits = '32 位元' if machine == MACHINE_I386 else '64 位元' if machine == MACHINE_AMD64 else f'未知(0x{machine:04X})'
            # Characteristics 是一整排開關,用 & 取出 0x0020 那一個位元。
            # 它就是大位址支援,開了之後 32 位元程式的位址空間上限從 2 GB 變成 4 GB。
            # 這是相容性旗標,跟任何防拷或授權驗證機制無關。
            large = bool(chars & IMAGE_FILE_LARGE_ADDRESS_AWARE)
            print(f'  類型  {bits} 程式')
            if machine == MACHINE_I386:
                if large:
                    print('  上限  ✅ 最多 4 GB(已開啟大位址支援)')
                    print('        這台的執行檔已經處理過記憶體上限問題。')
                else:
                    print('  上限  ⚠ 只有 2 GB(未開啟大位址支援)')
                    print('        這是當機的候選原因之一。本站在自己那顆執行檔上量到的是:')
                    print('        只掛大位址旗標沒有感覺,卡住的是遊戲自己切的那塊記憶體池。')
                    problems.append('執行檔記憶體上限只有 2 GB')
            else:
                print('  上限  (非 32 位元程式,不受 2 GB 限制)')

    # ── 2. 遊戲資料量 ──────────────────────────────────
    # 這一段量的一律是「磁碟上的位元組數」,不是封裝檔解開之後的內容大小。
    # 兩種算法在大檔上差不多,在小檔上差很多,所以口徑要先講清楚。
    print('\n【2】遊戲資料量')
    data_dir = root / 'data'
    if not data_dir.is_dir():
        print(f'  ✗ 找不到 data 資料夾')
        print('    確認你選的是遊戲安裝資料夾(裡面應該有 data\\ 和 .exe)')
        problems.append('找不到 data 資料夾')
    else:
        # rglob('*') 會一路走進所有子資料夾,包含使用者自己放在 data 底下的備份。
        # 那正是下面要特別點出備份資料夾的原因:總量會被灌水。
        files = [f for f in data_dir.rglob('*') if f.is_file()]
        total = sum(f.stat().st_size for f in files)
        # .big 是這個遊戲的封裝檔,一個 .big 裡面包著很多筆內容。
        # 副檔名先轉小寫再比:有的檔案系統不分大小寫、有的分,
        # 不先統一的話 .BIG 這種寫法會被漏掉。
        bigs = [f for f in files if f.suffix.lower() == '.big']
        print(f'  總量      {human(total)}({len(files):,} 個檔案)')
        print(f'  封裝檔    {len(bigs)} 個 .big')
        # 疑似備份子資料夾會讓數字看起來偏高,提示一下
        # 只看 data 底下的第一層,而且是靠資料夾名字猜的,中英文各列幾個常見寫法。
        # 猜錯的代價很小(多印一行註記),漏掉的代價比較大(讀者會以為自己的遊戲爆掉了)。
        bak_dirs = [d for d in data_dir.iterdir()
                    if d.is_dir() and any(k in d.name for k in ('備份', '原版', 'Backup', 'backup', '副本'))]
        if bak_dirs:
            bak_files = sum(1 for d in bak_dirs for f in d.rglob('*.big'))
            shown = ', '.join(d.name[:22] + ('…' if len(d.name) > 22 else '')
                              for d in bak_dirs[:2])
            if len(bak_dirs) > 2:
                shown += f' 等 {len(bak_dirs)} 個'
            print(f'  註        其中 {bak_files} 個 .big 在疑似備份的子資料夾內'
                  f'({shown})')
            print(f'            未改過的遊戲通常是 224 個 .big')
        big5 = sorted(bigs, key=lambda f: -f.stat().st_size)[:5]
        if big5:
            print('  最大的幾個:')
            for f in big5:
                print(f'    {human(f.stat().st_size):>10}  {f.relative_to(data_dir)}')
        # 球場檔比原版大很多的,值得拿清孤兒那支腳本看一下。
        #
        # ⚠️ 2026-08-28 訂正:這裡原本寫「超過 80 MB」。那個數字沒有依據 ——
        #    本站掃過 692 個球場檔(全部來源合計,不寫死來源數),
        #    最大的一個是 18.44 MB,80 MB 是它的 4.3 倍。
        #    也就是說這個檢查從來沒有亮過,而且不可能亮 ——
        #    它只是讓人以為「檢查過了沒問題」。
        #
        # 現在用的基準是量出來的:剛安裝好的原版 87 個球場檔,最大 3.99 MB。
        # 超過 10 MB 就提醒 —— 10 這個數字是社群傳了二十年的說法,不是本站量到的門檻,
        # 所以措辭是「值得看一下」不是「這會當機」。
        PRISTINE_MAX_MB = 3.99      # 剛安裝好的原版 87 個檔裡最大的那個
        FOLKLORE_MB = 10            # 社群傳的數字,不是實測門檻
        # 球場檔全部放在 data\stadium\ 底下,副檔名是 .big。
        # 沒有這個資料夾也不算錯(有人只裝了部分內容),那就整段跳過。
        stad = data_dir / 'stadium'
        if stad.is_dir():
            bigs_st = sorted(stad.glob('*.big'), key=lambda f: -f.stat().st_size)
            over = [f for f in bigs_st if f.stat().st_size > FOLKLORE_MB * 1024 * 1024]
            if bigs_st:
                top = bigs_st[0]
                print(f'\n  球場檔 {len(bigs_st)} 個,最大的是 '
                      f'{human(top.stat().st_size)}  {top.name}')
                print(f'    (剛安裝好的原版 87 個檔,最大 {PRISTINE_MAX_MB} MB)')
            if over:
                print(f'  ⚠ 有 {len(over)} 個超過 {FOLKLORE_MB} MB:')
                for f in over[:5]:
                    print(f'    {human(f.stat().st_size):>10}  {f.name}')
                print('    這不代表一定會當機 —— 社群傳的「太大會跳出」沒有人量過邊界。')
                print('    但變大的原因多半是改檔留下的舊版本,可以用清孤兒那支腳本清掉,')
                print('    內容一個位元組都不會少。')
                problems.append(f'{len(over)} 個球場檔超過 {FOLKLORE_MB} MB(值得清一下,不一定是問題)')

    # ── 3. 關鍵檔案是否齊全 ────────────────────────────
    # 這四個是「少了就一定不對」的檔:兩個資料庫、兩個介面封裝檔。
    # 缺了通常只有兩種原因,指錯資料夾,或是下載的那一包根本沒下載完。
    # 注意這裡只看檔案在不在,不開內容,所以「在但是壞的」這一段驗不出來。
    print('\n【3】關鍵檔案')
    expect = [
        ('data/database/attrib.dat', '球員屬性'),
        ('data/database/schedule.big', '賽程'),
        ('data/frontend/ingame.big', '比賽中介面'),
        ('data/frontend/frontend.big', '選單介面'),
    ]
    for rel, desc in expect:
        p = root / rel
        mark = '✅' if p.exists() else '✗ '
        print(f'  {mark} {rel:<34}{desc}')
        if not p.exists():
            problems.append(f'缺少 {rel}')

    # ── 4. 備份檔提醒 ──────────────────────────────────
    # 走一次整棵樹,用副檔名比對(副檔名先轉小寫,.BAK 這種寫法也認得)。
    # 只認 .bak 的話,其他二十幾種副檔名的備份會完全看不見,而且不會有任何提示。
    print()
    found = sorted(f for f in root.rglob('*')
                   if f.suffix.lower() in BAK_SUFFIXES and f.is_file())
    baks, shipped, _ = classify_baks([f.relative_to(root) for f in found])
    if baks:
        print(f'【4】找到 {len(baks)} 個你自己的備份檔')
        for b in baks[:8]:
            print(f'  {b}')
        if len(baks) > 8:
            print(f'  …(還有 {len(baks) - 8} 個)')
        print('  這是好習慣。改壞了可以用它們還原。')
    else:
        print('【4】沒有找到任何你自己的備份檔')
        print('  如果你還沒改過任何東西,這是正常的。')
        print('  如果你改過,代表備份不在遊戲資料夾裡,或是你自己取的名字這裡認不得')
        print('  (只認得下面 BAK_SUFFIXES 那份清單裡的副檔名)—— 動手前請先自己複製一份。')
    if shipped:
        names = ', '.join(str(b) for b in shipped)
        print(f'  (另外有 {len(shipped)} 個是遊戲本來就附的,不算你的備份:{names})')

    # ── 結論 ───────────────────────────────────────────
    # 這張清單只印給人看,不影響結束碼:這支是體檢不是測試,
    # 不該讓批次檔因為「有一項值得注意」就中斷。
    print('\n' + '=' * 46)
    if not problems:
        print('沒有發現明顯問題。')
        print('如果還是會當機,可能是模組相容性或顯示設定的問題。')
    else:
        print(f'發現 {len(problems)} 項值得注意:')
        for i, p in enumerate(problems, 1):
            print(f'  {i}. {p}')
    print('\n本次檢查全程唯讀,沒有修改任何檔案。')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 這支從頭到尾沒有打開任何檔案來寫,也沒有搬移或刪除,
        # 所以中途停掉就只是少印幾行,遊戲資料夾裡什麼都沒有動到。
        # 結束碼用 130(=128+SIGINT),跟其他幾種結束方式分得開。
        print('\n\n已中止。本次檢查全程唯讀,沒有動到任何檔案。')
        sys.exit(130)
    except OSError as e:
        # 掃描途中檔案被移走或鎖住會走到這裡:雲端同步資料夾、防毒隔離、
        # 外接碟被拔掉都算。這支全程唯讀,中斷不會留下壞檔;
        # 但要給讀者一句看得懂的話,而不是一整串 traceback。
        # 結束碼用 2,跟「路徑給錯了」的 1 分開,批次檔才判斷得出來。
        print(f'\n✗ 讀取途中出錯:{e}')
        print('  可能的原因:遊戲資料夾正在被別的程式動(雲端同步、防毒掃描),')
        print('  或是外接碟中途斷線。關掉那些程式、確認碟還在,再跑一次。')
        print('  本次檢查全程唯讀,沒有修改任何檔案。')
        sys.exit(2)

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
