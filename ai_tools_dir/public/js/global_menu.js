(function(){
  if (window.__aitools_menu || window.aitools_menu) return;

  try { document.documentElement.classList.add('hide-frappe-chrome'); } catch(e) {}

  function isGuest(){
    try { 
      // Handle cases where frappe.session.user might be undefined during initialization
      var user = frappe.session?.user;
      var result = !window.frappe || !frappe.session || !user || user === 'Guest' || user === undefined;
      console.log('isGuest check:', { frappe: !!window.frappe, session: !!frappe.session, user: user, result: result });
      return result;
    } catch(e){ 
      console.log('isGuest error:', e);
      return true; 
    }
  }

  function buildMenuHTML(){
    var overlay = document.createElement('div');
    overlay.className = 'side-menu-overlay';

    var menu = document.createElement('aside');
    menu.className = 'side-menu';
    menu.innerHTML = ''+
      '<div class="brand">AI Tools</div>'+
      '<div class="links">'
        + '<a href="/">Home</a>'
        + '<a href="/categories">Categories</a>'
        + (isGuest() ? '<a href="/login">Login</a>' : '<a href="/logout?cmd=web_logout&redirect-to=/">Logout</a>')
      + '</div>';

    function close(){ menu.classList.remove('open'); overlay.classList.remove('open'); }
    function open(){ menu.classList.add('open'); overlay.classList.add('open'); }

    overlay.addEventListener('click', close);

    document.body.appendChild(overlay);
    document.body.appendChild(menu);

    return { overlay: overlay, menu: menu, open: open, close: close, toggle: function(){ (menu.classList.contains('open') ? close : open)(); } };
  }

  // Wait for Frappe to be fully ready before building menu
  function waitForFrappe(callback) {
    if (window.frappe && frappe.session && frappe.session.user !== undefined) {
      callback();
    } else {
      // Wait a bit more for Frappe to initialize
      setTimeout(function() {
        if (window.frappe && frappe.session && frappe.session.user !== undefined) {
          callback();
        } else {
          // Fallback: build menu anyway but mark as guest
          console.log('Frappe not fully ready, building menu as guest');
          callback();
        }
      }, 500);
    }
  }

  waitForFrappe(function() {
    var menuInstance = buildMenuHTML();
    window.__aitools_menu = menuInstance;
    window.aitools_menu = menuInstance;
    window.ait_menu_toggle = function(){ var m = window.aitools_menu || window.__aitools_menu; if (m) m.toggle(); };

    // Rebuild menu content when opened to always show current login state
    var originalOpen = menuInstance.open;
    menuInstance.open = function(){
      console.log('Menu opening, rebuilding content...');
      // Rebuild the menu content dynamically
      var linksContainer = menuInstance.menu.querySelector('.links');
      if (linksContainer) {
        linksContainer.innerHTML = ''+
          '<a href="/">Home</a>'+
          '<a href="/categories">Categories</a>'+
          (isGuest() ? '<a href="/login">Login</a>' : '<a href="/logout?cmd=web_logout&redirect-to=/">Logout</a>');
        console.log('Menu content rebuilt, isGuest:', isGuest());
      }
      originalOpen();
    };

    // Force refresh function for debugging
    window.aitools_refresh_menu = function() {
      console.log('Force refreshing menu...');
      var linksContainer = menuInstance.menu.querySelector('.links');
      if (linksContainer) {
        linksContainer.innerHTML = ''+
          '<a href="/">Home</a>'+
          '<a href="/categories">Categories</a>'+
          (isGuest() ? '<a href="/login">Login</a>' : '<a href="/logout?cmd=web_logout&redirect-to=/">Logout</a>');
        console.log('Menu content refreshed, isGuest:', isGuest());
      }
    };
  });
})();


