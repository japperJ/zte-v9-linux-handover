(function(){
  var path = location.pathname;
  var lang = (document.documentElement.lang === 'en') ? 'en' : 'da';
  var T = (lang === 'en')
    ? { home:'Home', files:'Files', chat:'Chat', cal:'Calendar', grocery:'Grocery', recipes:'Recipes', tasks:'To-dos' }
    : { home:'Hjem', files:'Filer', chat:'Chat', cal:'Kalender', grocery:'Indkøb', recipes:'Opskrifter', tasks:'Gøremål' };

  var I = {
    home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    folder: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    cal: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    cart: '<path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    check: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'
  };

  var items = [
    ['/', T.home, 'home', 'app_hjem', path === '/' || path === '/index.html', false],
    ['/cgi-bin/browse.cgi', T.files, 'folder', 'app_filer', path.indexOf('/cgi-bin/browse.cgi') === 0, false],
    ['/cgi-bin/chat.cgi', T.chat, 'chat', 'app_chat', path.indexOf('/cgi-bin/chat.cgi') === 0, false],
    ['/cgi-bin/calendar.cgi', T.cal, 'cal', 'app_kalender', path.indexOf('/cgi-bin/calendar.cgi') === 0, false],
    ['/cgi-bin/grocery.cgi', T.grocery, 'cart', 'app_indkoeb', path.indexOf('/cgi-bin/grocery.cgi') === 0, true],
    ['/cgi-bin/recipes.cgi', T.recipes, 'book', 'app_opskrifter', path.indexOf('/cgi-bin/recipes.cgi') === 0, false],
    ['/cgi-bin/tasks.cgi', T.tasks, 'check', 'app_opgaveliste', path.indexOf('/cgi-bin/tasks.cgi') === 0, false]
  ];

  var html = '<div class="dock">';
  for(var i = 0; i < items.length; i++){
    var it = items[i];
    html += '<a class="app' + (it[4] ? ' active' : '') + '" href="' + it[0] + '">';
    html += '<span class="tile"><svg viewBox="0 0 24 24" aria-hidden="true">' + I[it[2]] + '</svg>';
    if(it[5]) html += '<span class="badge" id="cartBadge">0</span>';
    html += '</span><span class="lbl" data-i18n="' + it[3] + '">' + it[1] + '</span></a>';
  }
  html += '</div>';
  document.write(html);

  window.setSiteLang = function(l){
    document.cookie = 'lang=' + l + ';path=/;max-age=31536000';
    try { localStorage.setItem('lang', l); } catch(e) {}
    location.reload();
  };

  var hd = document.querySelector('.header');
  if(hd && !hd.querySelector('.lang-toggle')){
    var a = document.createElement('a');
    a.className = 'lang-toggle';
    a.href = '#';
    a.textContent = (lang === 'en') ? 'DA' : 'EN';
    a.onclick = function(){ setSiteLang(lang === 'en' ? 'da' : 'en'); return false; };
    hd.appendChild(a);
  }
})();
