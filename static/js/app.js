const state = { data: null, role: 'farmer', authMode: 'register' };
const $ = (selector) => document.querySelector(selector);

function money(value) { return `₹${Number(value).toLocaleString('en-IN')}/kg`; }
function showToast(message, target = '#toast') {
  const toast = $(target);
  toast.textContent = message;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 3200);
}
function showAuthError(message) { $('#auth-error').textContent = message; }

function renderDemand(demands) {
  $('#demand-list').innerHTML = demands.slice(0, 3).map((demand) => `<article class="demand-item"><div><h3>${demand.buyer_name}</h3><p>${Number(demand.quantity_kg).toLocaleString()} kg ${demand.crop} <span>•</span> ${demand.location}</p></div><div><strong>${money(demand.price_per_kg)}</strong><small>needed by ${new Date(demand.needed_by).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</small></div><button class="arrow-btn offer-button" data-id="${demand.id}" aria-label="Make offer">→</button></article>`).join('');
  document.querySelectorAll('.offer-button').forEach((button) => button.addEventListener('click', () => makeOffer(button.dataset.id)));
}
function renderRecommendations(recommendations) {
  $('#recommendation-list').innerHTML = recommendations.map((item) => `<article class="recommendation-card"><div class="crop-dot">✦</div><h3>${item.crop}</h3><p>${item.reason}</p><div class="recommendation-meta"><span>Demand <strong>${item.demand}</strong></span><span>${item.price}</span></div></article>`).join('');
}
function renderProduce(listings) {
  $('#produce-list').innerHTML = `<div class="produce-row"><strong>Produce</strong><span>Quantity</span><span>Price</span><span>Status</span><span></span></div>` + listings.map((item) => `<div class="produce-row"><strong>${item.crop} <small>${item.grade}</small></strong><span>${Number(item.quantity_kg).toLocaleString()} kg</span><span>${money(item.price_per_kg)}</span><span class="status">Available</span><button class="arrow-btn" aria-label="Open listing">→</button></div>`).join('');
}
function renderBuyerListings(listings) {
  $('#buyer-listings').innerHTML = listings.map((item) => `<article class="buyer-item"><div class="buyer-crop-icon">✦</div><div><h3>${item.crop} <span class="demand-tag">${item.grade}</span></h3><p>${item.quantity_kg.toLocaleString()} kg · ${item.name} · ${item.village}</p></div><div><strong>${money(item.price_per_kg)}</strong><small>ready ${new Date(item.available_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</small></div><button class="outline-button contact-button" data-crop="${item.crop}">Contact farmer</button></article>`).join('') || '<p class="empty-state">No produce listings are available right now.</p>';
  document.querySelectorAll('.contact-button').forEach((button) => button.addEventListener('click', () => showToast(`Your interest in ${button.dataset.crop} was sent to the farmer.`, '#retailer-toast')));
}
function renderRetailerDemands(demands) {
  $('#retailer-demands').innerHTML = demands.map((item) => `<article class="buyer-item compact"><div class="buyer-crop-icon">↗</div><div><h3>${item.crop}</h3><p>${Number(item.quantity_kg).toLocaleString()} kg · ${item.grade} · ${item.location}</p></div><div><strong>${money(item.price_per_kg)}</strong><small>by ${new Date(item.needed_by).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</small></div><span class="status">Open</span></article>`).join('') || '<p class="empty-state">Post your first requirement to start receiving offers.</p>';
}
function renderOffers(offers) {
  $('#received-offers-list').innerHTML = offers.map((offer) => `<article class="buyer-item compact"><div class="buyer-crop-icon">◇</div><div><h3>${offer.crop}</h3><p>${offer.farmer_name} · ${offer.quantity_kg} kg offered</p></div><div><strong>${money(offer.price_per_kg)}</strong><small>Farmer offer</small></div><button class="primary-button small-button">Review</button></article>`).join('') || '<p class="empty-state">Offers from farmers will appear here.</p>';
}

async function loadFarmerDashboard() {
  const response = await fetch('/api/dashboard');
  if (!response.ok) throw new Error('Farmer dashboard unavailable');
  state.data = await response.json();
  const user = state.data.user;
  $('#farmer-user-name').textContent = user.name;
  document.querySelector('.page-heading h1').innerHTML = `Good morning, ${user.name} <span>✦</span>`;
  renderDemand(state.data.demands); renderRecommendations(state.data.recommendations); renderProduce(state.data.listings);
}
async function loadRetailerDashboard() {
  const response = await fetch('/api/retailer/dashboard');
  if (!response.ok) throw new Error('Retailer dashboard unavailable');
  state.data = await response.json();
  $('#retailer-user-name').textContent = state.data.user.business_name || state.data.user.name;
  $('#available-lots').textContent = state.data.stats.available_lots;
  $('#active-requests').textContent = state.data.stats.active_requests;
  $('#offers-received').textContent = state.data.stats.offers_received;
  renderBuyerListings(state.data.listings); renderRetailerDemands(state.data.demands); renderOffers(state.data.offers);
}
async function makeOffer(demandId) {
  const demand = state.data.demands.find((item) => item.id === Number(demandId));
  const quantity = window.prompt(`How many kg of ${demand.crop} can you supply?`, Math.min(demand.quantity_kg, 500));
  if (!quantity) return;
  const price = window.prompt('Your offer price per kg:', demand.price_per_kg);
  if (!price) return;
  const response = await fetch('/api/offers', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ demand_id: demandId, quantity_kg: quantity, price_per_kg: price }) });
  const result = await response.json(); showToast(response.ok ? 'Offer sent. The buyer will be notified.' : result.error);
}
function openDialog(id) { $(id).showModal(); }

function setAuthMode(mode) {
  state.authMode = mode;
  const isLogin = mode === 'login';
  $('#auth-title').textContent = isLogin ? 'Welcome back.' : 'Your market, your way.';
  $('#auth-subtitle').textContent = isLogin ? 'Sign in to continue to your KhetSetu workspace.' : 'Choose how you participate in the direct farm marketplace.';
  $('#role-choice').hidden = isLogin;
  document.querySelectorAll('.auth-extra').forEach((item) => { item.hidden = isLogin || !item.classList.contains(`${state.role}-extra`); });
  $('#auth-submit').innerHTML = isLogin ? 'Sign in to KhetSetu <span>→</span>' : `Create ${state.role} account <span>→</span>`;
  document.querySelector('.auth-switch').textContent = isLogin ? 'Create account' : 'Sign in';
  document.querySelector('.auth-switch').dataset.authMode = isLogin ? 'register' : 'login';
  const nameInput = $('#auth-form').querySelector('input[name="name"]');
  nameInput.required = !isLogin;
  $('#auth-form').querySelector('label:first-child').style.display = isLogin ? 'none' : '';
}
function chooseRole(role) {
  state.role = role;
  document.querySelectorAll('.role-card').forEach((card) => card.classList.toggle('selected', card.dataset.role === role));
  setAuthMode(state.authMode);
}
async function submitAuth(event) {
  event.preventDefault(); showAuthError('');
  const formData = Object.fromEntries(new FormData(event.target));
  formData.role = state.role;
  const response = await fetch(state.authMode === 'login' ? '/api/login' : '/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
  const result = await response.json();
  if (!response.ok) { showAuthError(result.error); return; }
  state.role = result.role || state.role; $('#auth-screen').hidden = true;
  if (state.role === 'farmer') { $('#farmer-app').hidden = false; await loadFarmerDashboard(); } else { $('#retailer-app').hidden = false; await loadRetailerDashboard(); }
}
async function logout() { await fetch('/api/logout', { method: 'POST' }); window.location.reload(); }
async function startApp() {
  const response = await fetch('/api/session'); const result = await response.json();
  if (!result.authenticated) { setAuthMode('register'); return; }
  state.role = result.user.role; $('#auth-screen').hidden = true;
  if (state.role === 'farmer') { $('#farmer-app').hidden = false; await loadFarmerDashboard(); } else { $('#retailer-app').hidden = false; await loadRetailerDashboard(); }
}

document.querySelectorAll('.role-card').forEach((card) => card.addEventListener('click', () => chooseRole(card.dataset.role)));
$('.auth-switch').addEventListener('click', (event) => setAuthMode(event.currentTarget.dataset.authMode));
$('#auth-form').addEventListener('submit', submitAuth);
document.querySelectorAll('[data-demo]').forEach((button) => button.addEventListener('click', () => { state.role = button.dataset.demo; setAuthMode('login'); $('#auth-form input[name="email"]').value = `${state.role}@khetsetu.demo`; $('#auth-form input[name="password"]').value = `${state.role}123`; }));
document.querySelectorAll('.logout-button').forEach((button) => button.addEventListener('click', logout));
document.querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.nav-item').forEach((item) => item.classList.remove('active')); if (button.classList.contains('nav-item')) button.classList.add('active'); const target = button.dataset.view === 'demand' ? '#demand-section' : button.dataset.view === 'recommendations' ? '#recommendations-section' : button.dataset.view === 'produce' ? '#produce-section' : '#top'; document.querySelector(target).scrollIntoView({ behavior: 'smooth', block: 'start' }); $('.sidebar').classList.remove('open'); }));
document.querySelectorAll('[data-retailer-view]').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.retailer-sidebar .nav-item').forEach((item) => item.classList.remove('active')); button.classList.add('active'); document.querySelector(`#${button.dataset.retailerView}`).scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
$('#open-listing').addEventListener('click', () => openDialog('#listing-dialog')); $('#open-listing-bottom').addEventListener('click', () => openDialog('#listing-dialog')); $('.mobile-menu').addEventListener('click', () => $('.sidebar').classList.toggle('open'));
$('#open-demand').addEventListener('click', () => openDialog('#demand-dialog')); $('#open-demand-inline').addEventListener('click', () => openDialog('#demand-dialog'));
$('#listing-form').addEventListener('submit', async (event) => { event.preventDefault(); const response = await fetch('/api/listings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); const result = await response.json(); if (!response.ok) { showToast(result.error); return; } $('#listing-dialog').close(); event.target.reset(); await loadFarmerDashboard(); showToast('Your produce listing is now live.'); });
$('#demand-form').addEventListener('submit', async (event) => { event.preventDefault(); const response = await fetch('/api/demands', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); const result = await response.json(); if (!response.ok) { showToast(result.error, '#retailer-toast'); return; } $('#demand-dialog').close(); event.target.reset(); await loadRetailerDashboard(); showToast('Your requirement is now visible to farmers.', '#retailer-toast'); });
startApp().catch(() => showAuthError('The app could not load. Please refresh and try again.'));
