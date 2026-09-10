/* toni的MVP模組補習班 —— 全站共用的互動。
 *
 * 紀律(2026-08-29 訂,違反就不要加功能):
 *   1. 漸進增強。關掉 JavaScript 時每一頁的內容仍然完整可讀,
 *      這支檔案建立的所有東西都不存在,版面一格都不動。
 *   2. 不連任何伺服器。使用者打的字、勾的步驟,只留在他自己的瀏覽器裡。
 *   3. 不用 innerHTML(本站禁用),一律 createElement + textContent。
 *   4. 不用 alert / confirm / prompt(本站禁用)。
 *   5. localStorage 讀寫兩邊都包 try/catch —— 無痕視窗連 getItem 都會丟例外。
 *   6. 不給假的成功。指令裡還有沒換掉的佔位符就要講出來;
 *      比對不到就說「沒有這一條」,絕不推薦「最接近的一條」。
 */
(function () {
  'use strict';

  // ── 小工具 ────────────────────────────────────────────────
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function store(key, val) {          // 寫入;失敗就算了,不影響功能
    try {
      if (val === null) localStorage.removeItem(key);
      else localStorage.setItem(key, val);
    } catch (e) { /* 無痕視窗 / 停用儲存 */ }
  }

  function load(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ── 1. 指令一鍵複製 ───────────────────────────────────────
  // 全站 886 個 <pre>(2026-09-05 重數)。複製前先把 .cm(中文註解)剝掉 ——
  // 25 頁的指令區塊裡有中文,直接複製會把中文貼進終端機。
  function addCopyButtons() {
    var pres = document.querySelectorAll('pre');
    Array.prototype.forEach.call(pres, function (pre) {
      if (pre.getAttribute('data-nocopy') != null) return;
      var txt = pre.textContent || '';
      if (txt.trim().length < 3) return;

      var wrap = el('div', 'prewrap');
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);

      var btn = el('button', 'copybtn', '複製');
      btn.type = 'button';
      btn.setAttribute('aria-label', '複製這段指令');
      wrap.appendChild(btn);

      btn.addEventListener('click', function () {
        // 剝掉中文註解:clone 一份再刪,原本畫面上的不動
        var clone = pre.cloneNode(true);
        Array.prototype.forEach.call(clone.querySelectorAll('.cm'), function (c) {
          c.parentNode.removeChild(c);
        });
        var out = (clone.textContent || '').replace(/[ \t]+$/gm, '').trim();

        // 還沒換掉的佔位符要講出來,不給假的成功
        var ph = null;
        Array.prototype.forEach.call(pre.querySelectorAll('.hl'), function (h) {
          var t = (h.textContent || '').trim();
          if (/[一-鿿]/.test(t) && t.length <= 12) ph = t;
        });

        function done(okText) {
          btn.textContent = okText;
          btn.classList.add('is-done');
          setTimeout(function () {
            btn.textContent = '複製';
            btn.classList.remove('is-done');
          }, 2600);
        }

        function fallback() {
          try {
            var ta = el('textarea');
            ta.value = out;
            ta.setAttribute('readonly', '');
            ta.style.position = 'fixed';
            ta.style.top = '-1000px';
            document.body.appendChild(ta);
            ta.select();
            var ok = document.execCommand('copy');
            document.body.removeChild(ta);
            if (ok) { done(ph ? '已複製(記得換「' + ph + '」)' : '已複製'); return; }
          } catch (e) { /* 落到最後一條 */ }
          btn.textContent = '複製不了,請自己選取';
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(out).then(function () {
            done(ph ? '已複製(記得換「' + ph + '」)' : '已複製');
          }, fallback);
        } else {
          fallback();
        }
      });
    });
  }

  // ── 2. 步驟打勾 ───────────────────────────────────────────
  // 43 頁、195 個 .step-n(2026-09-05 重數)。只加一個勾,**不遮住任何內容**:
  // 全站有 61 個「你會看到」(2026-09-05 重數;原本寫的「44 個沒看到該怎麼辦」量不到,拿掉),
  // 讀者卡住時就是要回頭對照上一步 —— 把做完的步驟弄淡是幫倒忙。
  function addStepChecks() {
    var steps = document.querySelectorAll('.step > .step-n');
    if (!steps.length) return;
    var key = 'mvp:step:' + location.pathname;
    var saved = (load(key) || '').split(',').filter(Boolean);
    var state = {};
    saved.forEach(function (i) { state[i] = 1; });

    var boxes = [];
    Array.prototype.forEach.call(steps, function (n, i) {
      var num = n.textContent;
      var b = el('button', 'step-n step-btn', num);
      b.type = 'button';
      b.setAttribute('aria-pressed', state[i] ? 'true' : 'false');
      b.title = '點一下記錄「這一步我做完了」';
      if (state[i]) b.classList.add('is-done');
      n.parentNode.replaceChild(b, n);
      boxes.push(b);
      b.addEventListener('click', function () {
        if (state[i]) { delete state[i]; b.classList.remove('is-done'); b.setAttribute('aria-pressed', 'false'); }
        else { state[i] = 1; b.classList.add('is-done'); b.setAttribute('aria-pressed', 'true'); }
        save();
      });
    });

    var bar = el('p', 'stepbar');
    var cnt = el('span', 'stepcount');
    var clear = el('button', 'linkbtn', '清除這一頁的紀錄');
    clear.type = 'button';
    var note = el('span', 'small', '這個紀錄只存在你自己的瀏覽器,不會送到任何地方。');
    bar.appendChild(cnt);
    bar.appendChild(document.createTextNode(' '));
    bar.appendChild(clear);
    bar.appendChild(document.createElement('br'));
    bar.appendChild(note);

    var anchor = document.querySelector('.quickfix') || steps[0].closest('.step');
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bar, anchor.nextSibling);

    clear.addEventListener('click', function () {
      state = {};
      boxes.forEach(function (b) { b.classList.remove('is-done'); b.setAttribute('aria-pressed', 'false'); });
      save();
    });

    function save() {
      var on = Object.keys(state);
      store(key, on.length ? on.join(',') : null);
      // 用字紀律:不可以寫「已完成」,更不可以寫「遊戲已經改好了」
      cnt.textContent = '你勾了 ' + on.length + ' / ' + boxes.length +
                        ' 步(只是你自己勾的,本站沒有幫你驗)。';
    }
    save();
  }

  // ── 3. 大表搜尋 ───────────────────────────────────────────
  // 只在速查頁、而且表夠大時才出現。已經自己有搜尋框的頁面(#q)跳過。
  function addTableFilter() {
    if (document.getElementById('q')) return;                 // 該頁已有自己的
    if (location.pathname.indexOf('/reference/') < 0) return;  // 只給速查頁
    var wrap = document.querySelector('.wrap');
    if (!wrap) return;
    var allRows = wrap.querySelectorAll('.tablewrap tbody tr');
    if (allRows.length < 30) return;                           // 小表不需要

    // 以 h2 為分界掃 .wrap 的直接子節點(比 nextElementSibling 穩)
    var blocks = [];
    var cur = null;
    Array.prototype.forEach.call(wrap.children, function (node) {
      if (node.tagName === 'H2') {
        cur = { head: node, nodes: [], rows: [] };
        blocks.push(cur);
        return;
      }
      if (!cur) return;
      cur.nodes.push(node);
      Array.prototype.forEach.call(node.querySelectorAll ? node.querySelectorAll('tbody tr') : [], function (tr) {
        cur.rows.push({ el: tr, text: (tr.textContent || '').toLowerCase() });
      });
    });
    // 重點整理與收尾一律排除 —— 複習的人打字時整段消失是最糟的結果
    blocks = blocks.filter(function (b) {
      return b.head.id !== 'recap' && b.rows.length > 0;
    });
    if (!blocks.length) return;

    var box = el('div', 'tblfind');
    var lab = el('label', null, '在這一頁的對照表裡找(打代號、欄位名、英文名都可以)');
    var inp = el('input');
    inp.type = 'search';
    inp.id = 'tblq';
    inp.spellcheck = false;
    inp.autocomplete = 'off';
    lab.setAttribute('for', 'tblq');
    var msg = el('p', 'small tblmsg');
    msg.setAttribute('role', 'status');
    msg.setAttribute('aria-live', 'polite');
    var priv = el('p', 'small', '打的字只留在你自己的瀏覽器裡,不會送到任何地方;關掉 JavaScript 整張表照常顯示。');
    box.appendChild(lab); box.appendChild(inp); box.appendChild(msg); box.appendChild(priv);

    var first = blocks[0].head;
    first.parentNode.insertBefore(box, first);

    inp.addEventListener('input', function () {
      var v = inp.value.trim().toLowerCase();
      if (!v) {
        blocks.forEach(function (b) {
          b.rows.forEach(function (r) { r.el.hidden = false; });
          b.head.hidden = false;
          b.nodes.forEach(function (n) { n.hidden = false; });
        });
        msg.textContent = '';
        return;
      }
      var hit = 0;
      blocks.forEach(function (b) {
        var any = 0;
        b.rows.forEach(function (r) {
          var on = r.text.indexOf(v) >= 0;
          r.el.hidden = !on;
          if (on) { any++; hit++; }
        });
        b.head.hidden = !any;
        b.nodes.forEach(function (n) { n.hidden = !any; });
      });
      // 計數用字:說「列」不說「個欄位」—— 有些表一列裝四個欄位
      msg.textContent = hit ? ('命中 ' + hit + ' 列,其餘先收起來。')
                            : '這一頁的對照表裡沒有這個。清空搜尋框就會全部回來。';
    });
  }

  // ── 4. 把終端機的紅字貼進來,在本頁的 ❌ 表裡找 ─────────────
  function addErrorFinder() {
    // 找標題含 ❌ 的段落,它後面第一張表的第一欄是 td.mono
    var heads = document.querySelectorAll('h2, h3');
    var target = null;
    Array.prototype.forEach.call(heads, function (h) {
      if (target) return;
      if ((h.textContent || '').indexOf('❌') < 0) return;
      var n = h.nextElementSibling;
      var guard = 0;
      while (n && guard++ < 6) {
        if (n.classList && n.classList.contains('tablewrap')) {
          if (n.querySelector('tbody tr td.mono')) target = { head: h, wrap: n };
          return;
        }
        n = n.nextElementSibling;
      }
    });
    if (!target) return;

    var rows = [];
    Array.prototype.forEach.call(target.wrap.querySelectorAll('tbody tr'), function (tr) {
      var c = tr.querySelector('td');
      if (!c) return;
      var k = norm(c.textContent || '');
      var p = toPattern(k);
      var re = null;
      try { if (p && p.length > 5) re = new RegExp(p); } catch (e) { }
      rows.push({ el: tr, key: k, re: re });
    });
    if (rows.length < 3) return;

    function norm(s) {
      return s.replace(/[‘’]/g, "'").replace(/[“”]/g, '"')
              .replace(/\s+/g, ' ').trim().toLowerCase();
    }

    // 表裡的訊息是省略形,例如 can't open file '…\mvp_*.py',
    // 而使用者貼進來的是完整路徑。… 與 * 是萬用字元不是字面,
    // 所以不能用 indexOf 比 —— 要把那一列變成樣式再比。
    // (2026-08-29 實測:第一版用雙向 indexOf,對這一列完全比不到,
    //  而那一列正是本站自己標註的「最常見的第一個卡點」。)
    function toPattern(key) {
      var parts = key.split(/[…*]+/).filter(function (p) { return p.length; });
      if (!parts.length) return null;
      return parts.map(function (p) {
        return p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('[\\s\\S]*');
    }

    var box = el('div', 'errfind');
    var lab = el('label', null, '把終端機印出來的那一行貼進來,幫你在下面這張表裡找');
    var inp = el('input');
    inp.type = 'search'; inp.id = 'errq'; inp.spellcheck = false; inp.autocomplete = 'off';
    lab.setAttribute('for', 'errq');
    var msg = el('p', 'small errmsg');
    msg.setAttribute('role', 'status'); msg.setAttribute('aria-live', 'polite');
    var priv = el('p', 'small', '打的字只留在你自己的瀏覽器裡,不會送到任何地方。');
    box.appendChild(lab); box.appendChild(inp); box.appendChild(msg); box.appendChild(priv);
    target.wrap.parentNode.insertBefore(box, target.wrap);

    inp.addEventListener('input', function () {
      rows.forEach(function (r) { r.el.classList.remove('errhit'); });
      var v = norm(inp.value);
      if (v.length < 6) { msg.textContent = v ? '再多貼一點(至少六個字)。' : ''; return; }
      var hits = rows.filter(function (r) {
        if (r.key.indexOf(v) >= 0 || v.indexOf(r.key) >= 0) return true;  // 雙向包含
        if (!r.re) return false;
        return r.re.test(v);                                              // 省略形樣式
      });
      if (!hits.length) {
        // 誠實紀律:絕對不推薦「最接近的一條」
        msg.textContent = '這一頁的表裡沒有這一條。照最下面的回報範本貼給班主任,不要亂試。';
        return;
      }
      hits.forEach(function (r) { r.el.classList.add('errhit'); });
      msg.textContent = '找到 ' + hits.length + ' 條,已在下表高亮。';
      if (hits[0].el.scrollIntoView) hits[0].el.scrollIntoView({ block: 'center' });
    });
  }


  /* ── 名詞小教室 ──────────────────────────────────────
     2026-08-29 定案:標英文與科普小教室合二為一,而且不碰原文。
     所以這一整套<u>不存在於任何 HTML 檔裡</u> —— 資料在下面這個物件，
     標記是在讀者的瀏覽器裡掛上去的。關掉 JavaScript 就完全消失，
     正文一個字都沒有被改過(檔頭紀律第 1 條)。
     不需要 JavaScript 的完整清單在 glossary.html。

     規則:每一頁、每一個詞，只標「該頁第一次出現」的那一處。
     全站候選詞出現 5,241 次，全標會讓站台沒辦法讀
     (「位元組」單獨就 920 次)。

     每一筆四個欄位:
       en   英文(讀者在別的軟體/教學上會看到的那個字)
       zh   一句話解釋，講給不會用電腦的人聽
       sci  科普:一個生活比喻，或一個「為什麼要在乎」的理由
  */
  var TERMS = {
    '封裝檔': {
      en: 'BIG archive (.big)',
      zh: '一個檔案裡面裝著很多個檔案，遊戲用它把幾百張圖打包成一包。',
      sci: '像一個沒有夾層的行李箱：東西全部疊在裡面，箱蓋內側貼一張清單寫「第幾公分開始是哪一件」。改東西之前得先看那張清單。'
    },
    '版面檔': {
      en: 'FEL (.fel)',
      zh: '遊戲介面的版面腳本：哪個東西擺在哪、多大、什麼顏色、顯不顯示。',
      sci: '像舞台的走位表。解開壓縮之後它是純文字，一行一個元素，第二欄 1 是顯示、0 是隱藏 —— 關掉畫面上某個東西，改的就是那一格。'
    },
    '檔頭': {
      en: 'header',
      zh: '檔案最前面那一小段，寫著「我是什麼、我有多大、東西在哪」。',
      sci: '像書的目錄頁。程式打開檔案第一件事就是讀它 —— 目錄寫錯了，後面的內容再完整也找不到。'
    },
    '位元組': {
      en: 'byte',
      zh: '電腦檔案的最小計量單位，一個位元組可以存 0 到 255 之間的一個數字。',
      sci: '像記分板上的一格：那一格只放得下一個兩位數。要記 300 就得用兩格。所以「改一個數字」實際上是「改第幾格裡的那個數」。'
    },
    '十六進位': {
      en: 'hex',
      zh: '把每一個位元組寫成固定兩個字的寫法，0 到 9 用完接 A 到 F。',
      sci: '重點是寬度永遠一樣 —— 不管格子裡是 5 還是 255 都佔兩個字，就像記分板每一局固定畫一格，等寬才數得出現在第幾局。所以 42 49 47 46 要兩個字一組地讀，那是四格，換成文字剛好是 BIGF。'
    },
    '偏移': {
      en: 'offset',
      zh: '從檔案開頭算起的第幾個位元組。站上寫的 +0x0C 就是第 12 格。',
      sci: '二進位檔沒有欄位名 —— 某一格叫「檔案總大小」，唯一的理由是它排在那個位置。像一整排沒有門牌的房子，只能從路口數第幾間，數錯一間就敲錯門。而且要從 0 開始數。'
    },
    '區塊': {
      en: 'block',
      zh: '一組固定長度的資料，格式規定「每幾個位元組算一組」。',
      sci: '像一盒雞蛋固定十顆一排。壓縮圖片是每 4×4 個像素算一塊、聲音是每 15 個位元組還原成 28 個取樣 —— 切錯一格，後面整串就全亂了。'
    },
    '孤兒': {
      en: 'orphaned data',
      zh: '還留在檔案裡、但目錄已經不指向它的資料 —— 刪不掉也用不到。',
      sci: '像行李箱裡一件不在清單上的衣服：它佔空間，但你打開清單找不到它。社群模組一層層疊上去之後，這種東西會越積越多。'
    },
    '填充': {
      en: 'padding',
      zh: '為了把長度湊成整數而補進去的空白，本身不是資料。',
      sci: '像貨櫃裡塞的泡棉。它不是貨，但少了它東西會晃。看到一長串重複的位元組先別急著解讀，那多半是泡棉不是貨。'
    },
    '旗標': {
      en: 'flag',
      zh: '只有開跟關兩種狀態的一個設定，通常就是一個 0 或 1。',
      sci: '像電燈開關，沒有中間值。版面檔第二欄那個 1／0 就是旗標 —— 關掉畫面上某個元素，改的是那一格。'
    },
    '雜湊': {
      en: 'hash',
      zh: '把整個檔案算成一串固定長度的字，檔案差一個位元組，那串字就完全不一樣。',
      sci: '像指紋。你不用比對兩個人的每一寸，比指紋就知道是不是同一個。本站用它確認「你下載到的那份跟我做的那份一模一樣」。'
    },
    '貼圖': {
      en: 'texture',
      zh: '貼在 3D 模型表面的那張圖，像是把一張紙包在立體模型外面。',
      sci: '球員的臉是一個沒有五官的立體頭型，五官全部畫在貼圖上。所以「換一張臉」多數時候換的是那張圖，不是那顆頭。'
    },
    '像素': {
      en: 'pixel',
      zh: '圖片裡一格一格的小方塊，每一格記著一個顏色。',
      sci: '像馬賽克磁磚牆：退遠看是一張臉，湊近看是一格一格的色塊。檔案裡並沒有「一張圖」，只有照順序把每格是什麼顏色寫下來的一張長清單 —— 所以換上去的新圖尺寸一定要跟原圖一樣，格數一變後面全部對不上。',
      more: '📐 這件事可以拿計算機驗：清單有多長 ＝ 格數（寬乘高）乘上「每一格花幾個位元組」。256×256 的大頭照，像素資料正好 65,536 個位元組，一格剛好 1.0 個。本站走過兩個倉庫全部 48,885 張圖，沒有一張算出別的數字。這也是為什麼腳本會拒絕尺寸不一樣的新圖 —— 它不是挑剔，是算出來對不上。'
    },
    '調色盤': {
      en: 'palette',
      zh: '一張顏色對照表，圖裡每一格只記「用第幾號顏色」而不記顏色本身。',
      sci: '像著色本旁邊那盒編號的色鉛筆：圖上寫 7，你就拿 7 號筆。省空間，但整張圖最多只能用盒子裡那幾支。'
    },
    '透明度': {
      en: 'alpha',
      zh: '每個像素除了紅綠藍，還可以多記第四個數字：這一格看不看得見。',
      sci: '它是貼紙外面那條裁切線 —— 線以外被裁掉，所以貼上去看到的是底下的桌面。透明不等於白色，把背景塗白交出去，進遊戲就是一塊實心白。JPG 根本沒有這一欄。'
    },
    '編碼器': {
      en: 'encoder / codec',
      zh: '一套「聲音或影像該怎麼寫下來」的規矩。遊戲檔裡放的不是原始數字，是照它的規矩重寫過的版本。',
      sci: '像口譯：要翻得過去，也要翻得回來。所以換聲音一定是一來一回 —— 先解碼成 WAV 你才聽得到，改完再編碼翻成遊戲吃得下去的寫法。而且這個遊戲的規矩不只一種，拿其中一種去讀另一種的資料，怎麼調都不會對。',
      more: '🔍 這個遊戲的規矩不只一種：檔頭 0x80 那一格寫著編號，本站測到值 1 的是九個選單音樂、值 2 的是二十四個語音與音效（剛安裝好的原版；這台裝過社群模組的測試機是二十一個）。免費的 ffmpeg 這五種 EA 音訊格式都解得開，但一個編碼器都沒有 —— 那就是只能聽不能改，也是這一格卡了很久的原因。解開它的不是更聰明的組合，是找到一份標準答案：ffmpeg 解得開選單音樂，於是「你錯了」終於有東西說得出口，對照驗證 21,678,328 個取樣 0 個不同。'
    },
    '解碼': {
      en: 'decode',
      zh: '把照某套規矩寫下來的資料，還原成原本的樣子。',
      sci: '解得開不等於做得出來。免費的 ffmpeg 解得開這個遊戲的五種音訊格式，但一個編碼器都沒有 —— 光靠它就只能聽不能改。本站 2026-08-29 自己寫了一支編碼器，所以現在改得回去（見〈換掉遊戲的聲音〉那一課）。'
    },
    '取樣': {
      en: 'sample',
      zh: '把連續的聲音每隔一小段時間量一次高度，記成一串數字。',
      sci: '像每秒替一顆飛行中的球拍兩萬多張照片。照片夠密，看起來就是連續的動作 —— 聲音也是這樣變成數字的。'
    },
    '聲道': {
      en: 'channel',
      zh: '左邊一條、右邊一條，兩條各自獨立的聲音。',
      sci: '本站量到這個遊戲的兩個聲道是各自連續擺放的，不是左右交錯 —— 照交錯去解，聽起來就是雜訊。這一格是解開整個語音格式的關鍵。'
    },
    '骨架': {
      mark: false,
      en: 'boneprofile（名單欄位）／ skeleton（3D 那副）',
      zh: '兩個意思：名單裡那一欄指的是體型範本編號；3D 那邊指的是撐起模型的骨頭。',
      sci: '本站量到原版 549 個臉部模型共用同一副骨架，每個 66 根骨頭，連開發者留下的玩笑骨名都一起出貨。因為一個詞兩個意思，站上不自動標記它。'
    },
    '關鍵影格': {
      en: 'keyframe',
      zh: '動作裡被記下來的那幾個定格，中間的過程由程式補出來。',
      sci: '像翻頁動畫只畫幾張關鍵的姿勢，中間讓機器補。所以動作檔裡不是每一格畫面，是那幾張定格加上補間的規則。'
    },
    '字型': {
      en: 'font',
      zh: '每個字長什麼樣子的那一包資料。',
      sci: '看檔名就知道你的遊戲能不能顯示中文：全部 _en 結尾、合計約 200 KB 是沒裝中文字型；出現 _jp、超過 1 MB 就是裝過了。'
    },
    '解析度': {
      en: 'resolution',
      zh: '畫面或圖片有多少格 —— 橫的幾格乘直的幾格。',
      sci: '同一張臉，256×256 是 65,536 格，512×512 是 262,144 格，四倍。所以「畫質好一點」的代價從來不是線性的。'
    },
    '模組': {
      en: 'mod',
      zh: '別人做好的一包修改內容，裝進遊戲就會換掉原本的東西。',
      sci: '這個站教的是自己做，但也教怎麼安全地裝別人的 —— 差別在於裝之前你知不知道它會蓋掉哪些檔。'
    },
    '備份': {
      en: 'backup',
      zh: '動任何檔案之前先複製一份原樣留著。',
      sci: '⚠️ 半截的備份比沒有備份更糟：複製到一半斷掉，那份檔還是會留著，檔名對、打得開、開頭也對。像配到一半的備用鑰匙 —— 你要到被鎖在門外那一刻才知道它插不進去。所以本站的腳本一律先寫到同一個資料夾裡的隨機暫存檔，整份複製完、比對過才改成正式的備份檔名。'
    },
    '還原': {
      en: 'restore',
      zh: '把改過的檔案退回備份的那個樣子。',
      sci: '本站每一支會改檔的工具都有一行還原指令，而且還原順序不重要 —— 每支工具只還原自己動過的那個檔，互不干涉。'
    },
    '環境變數': {
      en: 'environment variable',
      zh: '設定給程式看的一個名字對一個值，程式啟動時會去讀它。',
      sci: '像在門口留一張便條寫「鑰匙在花盆下」。本站〈把一位球員改成你想要的球員〉那一課的工具用它（MVP_GAMEDIR）來知道你的遊戲裝在哪，這樣腳本裡就不必寫死任何人的路徑。'
    },
    '相對路徑': {
      en: 'relative path',
      zh: '從你現在所在的資料夾算起的位置。',
      sci: '像「從這裡往前走兩個路口」—— 換一個出發點，同一句話會走到完全不同的地方。這是新手最常卡住的一格。'
    },
    '絕對路徑': {
      en: 'absolute path',
      zh: '從最上層開始寫完整的位置，不管你現在在哪都指到同一個地方。',
      sci: '像完整地址。比較長，但貼給別人一定不會走錯 —— 所以回報問題的時候請貼絕對路徑。'
    },
    '記憶體池': {
      en: 'memory pool',
      zh: '程式一開機就跟系統要走的一整塊記憶體，之後自己切給各種東西用。',
      sci: '像先端一大鍋飯再分裝到每個便當盒。這個遊戲要的是一整塊 64 MB，中文字型光字圖就吃掉 13.5 MB（英文只要 0.37 MB）—— 池子先被吃掉五分之一，再也塞不下一座大球場。改成 128 MB 就好了。'
    },
    '中位數': {
      en: 'median',
      zh: '把所有數字排好之後站在正中間的那一個。',
      sci: '一間辦公室十個人，九個月薪三萬、一個月薪三百萬 —— 平均三十萬，中位數三萬。哪一個比較像「這裡的一般情況」？本站量檔案大小一律用中位數，就是這個理由。'
    },
    '標準差': {
      en: 'standard deviation',
      zh: '一群數字散得多開的一個量法。',
      sci: '兩隊打擊率都是三成，一隊人人三成、一隊有人四成有人兩成 —— 平均一樣，散度差很多。只看平均會把這兩隊當成一樣的隊。'
    },
    '迴歸': {
      en: 'regression',
      zh: '從一堆成對的數字裡，配出一條「用這個推那個」的線。',
      sci: '⚠️ 本站用它抓過一次錯：拿單點相除算出的比值「差 1.5% 應該夠接近」，換成迴歸才看清斜率其實只差 0.16%，那 1.5% 全部來自沒扣掉的固定開銷。單點除法會把固定成本混進每單位成本，要分開就得用迴歸。'
    },
    '相關係數': {
      en: 'correlation coefficient',
      zh: '兩組數字一起變動的程度，1 是完全同步、0 是毫無關係。',
      sci: '⚠️ 它測不到的東西比你以為的多。本站曾經拿一個「答案為真時也不會亮」的指標去驗配對關係，量到 −0.009 差點寫成否定結論 —— 亮不起來的指標測出 0，是它自己的性質，不是資料的性質。'
    },

    // ── 棒球術語(2026-08-30 加)──────────────────────────────
    // 需求:棒球術語一樣附中英文對照與詳細說明。
    // 完整的三欄對照(遊戲英文 / EA 官方繁中 / 台灣講法)在「棒球教練」那一頁，
    // 這裡只放**讀者在正文裡可能卡住**的那些 ——
    // 全壘打、安打、三振這類每個球迷都懂的就不標，標了只是雜訊。
    // 每一條的 sci 欄一律講「這個字在遊戲裡對應哪個欄位」。
    '選球': {
      en: 'plate discipline',
      zh: '打者不揮壞球的本事：等到好球才出棒。',
      sci: '遊戲裡是 playerattrib_platediscipline。EA 官方繁中譯成「本壘板紀律」——照字面翻的，意思沒錯但沒人這樣講。它跟「打得到球」是兩回事：選球好的人保送多、上壘率高，安打不一定多。'
    },
    '續航力': {
      en: 'stamina',
      zh: '投手一場能投多久。',
      sci: '遊戲裡是 pitchattrib_stamina，官方繁中「體力」。⚠️ 別跟打者的 durability(官方也譯「耐力」)搞混 —— 那個是不容易受傷，這個是一場撐多久。體力見底之後控球與球速會一起掉。'
    },
    '控球': {
      en: 'control',
      zh: '投手能不能把球放到想要的位置。',
      sci: '遊戲裡每個球種各有一個 control 值(pitchattrib_*_control)。控球差的投手保送多。它跟球速、尾勁是三個獨立的數字，改一個不會動到另外兩個。'
    },
    '尾勁': {
      en: 'movement',
      zh: '球在飛行途中跑掉多少 —— 打者以為會進來、結果溜掉的那個量。',
      sci: '遊戲裡是 pitchattrib_*_movement。⚠️ EA 官方繁中譯成「動作」，很容易誤會成投球姿勢(那是另一個欄位 pitcher_delivery)。'
    },
    '守備範圍': {
      en: 'range',
      zh: '一個守備員能顧到多大一塊地，往左右追得到多遠。',
      sci: '遊戲裡是 playerattrib_range。⚠️ EA 官方繁中譯成「距離」，讀起來像傳球距離，其實不是。中外野手最吃這一欄。它跟 fielding(接得穩不穩)是兩件事。'
    },
    '防禦率': {
      en: 'earned run average (ERA)',
      zh: '投手每九局平均失掉幾分自責分。數字越小越好。',
      sci: '⚠️ EA 官方繁中把它譯成「得分率」，那是錯的 —— 它算的是自責分不是得分，而且方向相反(越小越好)。這是本站在官方譯法裡抓到最要緊的一個。'
    },
    '自責分': {
      en: 'earned run',
      zh: '算在投手頭上的失分。因為守備失誤而丟的分不算。',
      sci: '防禦率的分子就是它。同樣丟三分，守備爛丟的跟自己被打的，記在投手身上的不一樣多。'
    },
    '上壘率': {
      en: 'on-base percentage (OBP)',
      zh: '打者上壘的比例：安打、保送、觸身球都算。',
      sci: '⚠️ 遊戲裡另有一個 On Base 官方譯成「壘包上」，那是在描述跑者位置，不是這個數字。上壘率的分母是打席不是打數。'
    },
    '打席': {
      en: 'plate appearance',
      zh: '上場打擊的次數，保送與犧牲打都算一次。',
      sci: '跟「打數」不一樣：打數把保送、犧牲打扣掉。所以打擊率的分母是打數，上壘率的分母是打席 —— 兩個率不能直接比。'
    },
    '打數': {
      en: 'at bat (AB)',
      zh: '正式的打擊機會，保送與犧牲打不算。',
      sci: '打擊率的分母。本站解開歷史成績檔時量到的八個打擊欄位，第一個就是它。'
    },
    '長打力': {
      en: 'power',
      zh: '把球打遠的能力。',
      sci: '⚠️ EA 官方繁中譯成「爆發力」，那偏向瞬間力量。棒球講的是能不能把球打出牆。本站的成績換算課量到，它在遊戲裡分成對右投與對左投兩個數字。'
    },
    '觸擊': {
      en: 'bunt',
      zh: '把球輕輕點出去、不揮大棒。',
      sci: '遊戲裡是 playerattrib_bunting。用在推進壘上跑者(犧牲觸擊)或搶一壘安打(觸擊安打)。'
    },
    '牽制': {
      en: 'pickoff',
      zh: '投手把球傳向壘包、逼跑者回壘。',
      sci: '遊戲裡是 pitchattrib_pickoff。這一欄高的投手，電腦控的跑者不太敢盜壘。'
    },
    '牛棚': {
      en: 'bullpen',
      zh: '後援投手熱身的地方，也指全隊的後援投手群。',
      sci: '⚠️ EA 官方繁中譯成「練投區」，只講到那塊地，漏掉「那群人」的意思。'
    },
    '先發輪值': {
      en: 'rotation',
      zh: '先發投手的出場順序，通常五個人輪。',
      sci: '官方繁中「輪替名單」。它跟「打線」(這一場誰第幾棒)、「名冊」(全隊所有球員的資料)是三件不同的事 —— 站上大部分課改的是最後那個。'
    },
    '球種': {
      en: 'pitch type',
      zh: '這一球是直球、變速球還是曲球之類的。',
      sci: '遊戲存了十五種，代號 0 到 14 記在社群編輯器 MVPtools 附的 config.txt 裡那張 EA 代號表。一位投手最多帶五種，每一種各有球速、控球、尾勁三個數字。'
    },
    '盜壘': {
      en: 'stolen base (SB)',
      zh: '投手投球時起跑，安全上到下一個壘。',
      sci: '遊戲把「跑得多快」(speed)跟「多敢跑」(stealing_aggressive)分成兩欄 —— 速度快但積極度低的人，站在壘上不太動。'
    },
    '王朝模式': {
      en: 'Dynasty',
      zh: '接手一支球隊經營很多年：選秀、交易、育成、算薪水。',
      sci: '這個遊戲的主菜，也是站上「王朝存檔」那一頁在拆的東西。每個王朝存檔剛好 2,239,688 個位元組，沒有加密也沒有壓縮。'
    }
  };

  function buildTermPop() {
    var pop = document.createElement('div');
    pop.className = 'termpop';
    pop.setAttribute('role', 'dialog');
    pop.hidden = true;
    var x = document.createElement('button');
    x.className = 'tp-x'; x.type = 'button';
    x.setAttribute('aria-label', '關閉'); x.textContent = '×';
    var h = document.createElement('p'); h.className = 'tp-h';
    var en = document.createElement('span'); en.className = 'tp-en';
    var zh = document.createElement('p');
    var sci = document.createElement('p'); sci.className = 'tp-sci';
    // more 是可選的「再深入一點」——放量到的數字與細節。
    // 2026-08-29 訂正:原本以為彈出框只能放一行,所以把兩格科普寫成
    // 「要插進正文才放得下」。那是我自己發明的限制 —— 框可以變大。
    var more = document.createElement('p'); more.className = 'tp-more';
    h.appendChild(document.createTextNode(''));
    h.appendChild(en);
    pop.appendChild(x); pop.appendChild(h); pop.appendChild(zh);
    pop.appendChild(sci); pop.appendChild(more);
    document.body.appendChild(pop);
    return { pop: pop, h: h, en: en, zh: zh, sci: sci, more: more, x: x };
  }

  function addTermMarks() {
    if (!document.body) return;
    // mark:false 的詞只進 glossary.html，不在正文自動標記。
    // 目前只有「骨架」——它在名單欄位是 boneprofile、在 3D 那邊是 skeleton，
    // 一個詞兩個意思，自動標記一定會有一頁標錯。
    var words = Object.keys(TERMS).filter(function (w) { return TERMS[w].mark !== false; });
    if (!words.length) return;
    // 每頁最多標幾個。52 個詞全放行（2026-09-06 重數）的話，密集的頁面會被記號洗版 ——
    // 對「不會用電腦」的讀者，滿頁虛線比沒有註解更難讀。
    var CAP = 8;
    var marked = 0;
    var seen = {};
    // 只走正文的文字節點。這幾種祖先一律跳過 ——
    // code/pre 裡是可以複製的指令，details 裡是原始碼的逐字鏡像，
    // 動到任何一個都會讓讀者複製到壞掉的東西。
    var SKIP = /^(CODE|PRE|SCRIPT|STYLE|TEXTAREA|BUTTON|A|ABBR|H1|TITLE|NAV|FOOTER)$/;
    // 導覽、麵包屑、徽章、表頭不是正文 —— 標在那裡會把導覽文字切開。
    // 2026-08-29 第一版沒排除 .crumb，於是「教學 › 封裝檔可以拆成散裝嗎」
    // 那行麵包屑被插了一顆按鈕進去。
    // gl-term 是 glossary.html 的條目 —— 那一頁本來就在解釋這些詞，不必再標一次。
    var SKIPCLASS = /(^|\s)(crumb|badge|nav-in|copybtn|swipehint|recap|gl-term)(\s|$)/;
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        for (var p = n.parentNode; p && p !== document.body; p = p.parentNode) {
          if (p.nodeType !== 1) continue;
          if (SKIP.test(p.tagName)) return NodeFilter.FILTER_REJECT;
          if (p.className && typeof p.className === 'string'
              && SKIPCLASS.test(p.className)) return NodeFilter.FILTER_REJECT;
          if (p.tagName === 'TH') return NodeFilter.FILTER_REJECT;
          if (p.tagName === 'DETAILS') return NodeFilter.FILTER_REJECT;
          if (p.classList && p.classList.contains('termpop')) return NodeFilter.FILTER_REJECT;
        }
        return n.nodeValue && n.nodeValue.length > 1
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);

    var ui = null;
    function show(btn, w) {
      if (!ui) {
        ui = buildTermPop();
        ui.x.addEventListener('click', hide);
      }
      var t = TERMS[w];
      ui.h.firstChild.nodeValue = '🔬 ' + w + ' ';
      ui.en.textContent = t.en;
      ui.zh.textContent = t.zh;
      ui.sci.textContent = '💡 ' + t.sci;
      ui.more.textContent = t.more || '';
      ui.more.hidden = !t.more;
      ui.pop.hidden = false;
      if (matchMedia('(min-width:701px)').matches) {
        var r = btn.getBoundingClientRect();
        ui.pop.style.top = (r.bottom + scrollY + 6) + 'px';
        ui.pop.style.left = Math.max(12, Math.min(
          r.left + scrollX, innerWidth - ui.pop.offsetWidth - 12)) + 'px';
      }
      btn.setAttribute('aria-expanded', 'true');
      ui.pop.dataset.owner = w;
    }
    function hide() {
      if (!ui || ui.pop.hidden) return;
      ui.pop.hidden = true;
      var b = document.querySelector('button.term[aria-expanded="true"]');
      if (b) { b.setAttribute('aria-expanded', 'false'); b.focus(); }
    }

    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      for (var j = 0; j < words.length; j++) {
        var w = words[j];
        if (seen[w]) continue;
        if (marked >= CAP) break;
        var at = node.nodeValue.indexOf(w);
        if (at === -1) continue;
        seen[w] = true;
        var after = node.splitText(at);
        after.nodeValue = after.nodeValue.slice(w.length);
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'term';
        btn.textContent = w;
        btn.setAttribute('aria-expanded', 'false');
        btn.title = w + '（' + TERMS[w].en + '）— 點一下看解釋';
        (function (b, word) {
          b.addEventListener('click', function (e) {
            e.stopPropagation();
            if (b.getAttribute('aria-expanded') === 'true') hide(); else show(b, word);
          });
        })(btn, w);
        after.parentNode.insertBefore(btn, after);
        marked++;
        node = after;   // 同一個文字節點後半段繼續找別的詞
      }
    }
    document.addEventListener('click', hide);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') hide();
    });
  }

  function boot() {
    try { addCopyButtons(); } catch (e) { }
    try { addStepChecks(); } catch (e) { }
    try { addTableFilter(); } catch (e) { }
    try { addErrorFinder(); } catch (e) { }
    try { markScrollableTables(); } catch (e) { }
    try { addTermMarks(); } catch (e) { }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  /* ── 表格橫向捲動提示 ──
     站上不少表有四欄以上，在 375px 的手機會被切掉。它們本來就能左右滑，
     但沒有任何跡象說得出來 —— 這段只在「真的捲得動」時掛一行字，捲過就收。
     判斷用 scrollWidth > clientWidth + 2（留 2px 給次像素誤差）。 */
  function markScrollableTables(){
    /* 2026-09-05:SVG 圖的 .figscroll 跟表格同一套提示(手機上 9 張圖捲得動卻看不出來)。 */
    var wraps = document.querySelectorAll('.tablewrap, .figscroll');
    for (var i = 0; i < wraps.length; i++) {
      var w = wraps[i];
      var over = w.scrollWidth - w.clientWidth > 2;
      var hint = w.querySelector('.swipehint');
      if (!over) {
        if (hint) hint.remove();
        w.removeAttribute('tabindex'); w.removeAttribute('role'); w.removeAttribute('aria-label');
        continue;
      }
      /* 捲得動的容器要能用鍵盤捲(WCAG 2.1.1)——
         瀏覽器不會自動把 overflow 容器變成焦點目標,只能鍵盤的人就捲不動。 */
      if (!w.hasAttribute('tabindex')) {
        w.setAttribute('tabindex', '0'); w.setAttribute('role', 'region');
        w.setAttribute('aria-label', w.classList.contains('figscroll') ? '可左右捲動的圖' : '可左右捲動的表格');
      }
      if (!hint) {
        hint = document.createElement('span');
        hint.className = 'swipehint';
        hint.textContent = w.classList.contains('figscroll') ? '← 左右滑動看完整圖 →' : '← 左右滑動看完整表格 →';
        w.insertBefore(hint, w.firstChild);
        (function(el){
          el.addEventListener('scroll', function(){
            if (el.scrollLeft > 4) el.classList.add('scrolled');
          }, { passive: true });
        })(w);
      }
    }
  }
  /* 字型載完之後欄寬會變，所以 load 再量一次；換方向 / 改視窗大小同理。
     這裡不能只在腳本執行當下量 —— 那時版面還沒定，量到的是 0。 */
  addEventListener('load', function(){
    try { markScrollableTables(); } catch (e) { }
  });
  var rz; addEventListener('resize', function(){
    clearTimeout(rz); rz = setTimeout(markScrollableTables, 150);
  });
})();
