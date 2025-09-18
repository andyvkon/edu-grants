async function api(path, opts={}) {
  const res = await fetch(path, {headers: {'Accept': 'application/json'}, ...opts});
  if (!res.ok) {
    const text = await res.text();
    alert('API error '+res.status+': '+text);
    throw new Error('API error '+res.status+': '+text);
  }
  return res.json();
}
function escapeHtml(s){ return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
