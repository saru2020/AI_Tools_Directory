(function(){
  var input = document.getElementById('tools-search');
  if (input && input.form) {
    var form = input.form, t;
    input.addEventListener('input', function(){
      if (t) clearTimeout(t);
      t = setTimeout(function(){ form.submit(); }, 300);
    });
    try { input.focus(); var len = input.value.length; input.setSelectionRange(len, len);} catch(e) {}
  }

  window.trackClick = function(slug){
    try {
      var url = '/api/method/ai_tools_dir.api.track.click_tool?slug=' + encodeURIComponent(slug) + '&_t=' + Date.now();
      fetch(url, { method: 'GET', headers: { 'Accept': 'application/json', 'Cache-Control': 'no-cache' } });
    } catch(e) {}
    return true;
  };

  window.upvote = function(slug, btn){
    fetch('/api/method/ai_tools_dir.api.vote.toggle_upvote?slug=' + encodeURIComponent(slug), { method: 'GET' })
      .then(function(r){ return r.json(); })
      .then(function(data){
        if (data && data.message && data.message.login_required){ window.location.href = '/login'; return; }
        var countSpan = btn.parentNode.querySelector('.upvote-count');
        var currentCount = parseInt(countSpan.textContent) || 0;
        countSpan.textContent = currentCount + (data.message.status === 'added' ? 1 : -1);
        btn.textContent = data.message.status === 'added' ? '▼ Remove Upvote' : '▲ Upvote';
        btn.classList.toggle('voted', data.message.status === 'added');
      }).catch(function(){});
    return false;
  };
})();


