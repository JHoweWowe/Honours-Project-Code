(function () {
  'use strict';

  const btn = document.getElementById('find-stores-btn');
  if (!btn) return;

  const postcodeForm = document.getElementById('postcode-form');
  const postcodeInput = document.getElementById('postcode-input');
  const postcodeCountry = document.getElementById('postcode-country');
  const postcodeSubmitBtn = document.getElementById('postcode-submit-btn');
  const resultsDiv = document.getElementById('stores-results');
  const disclaimer = document.getElementById('stores-disclaimer');

  // Pre-fill postcode from saved profile value
  const savedPostcode = btn.dataset.postcode || '';
  if (postcodeInput && savedPostcode) postcodeInput.value = savedPostcode;

  // Pre-select country dropdown from profile location (e.g. "singapore" → sg)
  const profileLocation = (btn.dataset.location || '').toLowerCase();
  if (postcodeCountry) {
    if (profileLocation.indexOf('singapore') !== -1 || profileLocation === 'sg') {
      postcodeCountry.value = 'sg';
    } else if (
      profileLocation.indexOf('united kingdom') !== -1 ||
      profileLocation.indexOf('england') !== -1 ||
      profileLocation.indexOf('scotland') !== -1 ||
      profileLocation.indexOf('wales') !== -1 ||
      profileLocation === 'uk' ||
      profileLocation === 'gb'
    ) {
      postcodeCountry.value = 'gb';
    }
  }

  btn.addEventListener('click', function () {
    setLoading(true);
    if (!navigator.geolocation) {
      setLoading(false);
      showPostcodeForm();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        callApi({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      },
      function () {
        setLoading(false);
        showPostcodeForm();
      },
      { timeout: 8000 }
    );
  });

  if (postcodeSubmitBtn) {
    postcodeSubmitBtn.addEventListener('click', submitPostcode);
  }

  if (postcodeInput) {
    postcodeInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') submitPostcode();
    });
  }

  function submitPostcode() {
    const pc = (postcodeInput ? postcodeInput.value : '').trim();
    if (!pc) return;
    setLoading(true);
    postcodeForm.style.display = 'none';
    const country = postcodeCountry ? postcodeCountry.value : '';
    callApi({ postcode: pc, country: country });
  }

  function showPostcodeForm() {
    if (postcodeForm) postcodeForm.style.display = '';
  }

  function setLoading(on) {
    btn.disabled = on;
    btn.textContent = on ? 'Searching…' : 'Find Stores Near Me';
  }

  function getIngredients() {
    try {
      const raw = btn.dataset.ingredients || '[]';
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function callApi(params) {
    const ingredients = getIngredients();
    const url = new URL('/api/stores/nearby', window.location.origin);
    if (params.lat !== undefined) {
      url.searchParams.set('lat', params.lat);
      url.searchParams.set('lng', params.lng);
    } else {
      url.searchParams.set('postcode', params.postcode);
      if (params.country) url.searchParams.set('country', params.country);
    }
    url.searchParams.set('ingredients', JSON.stringify(ingredients));

    fetch(url.toString())
      .then(function (res) {
        return res.json().then(function (data) { return { ok: res.ok, data: data }; });
      })
      .then(function (res) {
        setLoading(false);
        handleResponse(res.data);
      })
      .catch(function () {
        setLoading(false);
        showAlert('Unable to find stores right now. Please try again.', 'danger');
      });
  }

  function handleResponse(data) {
    resultsDiv.innerHTML = '';

    if (data.error === 'limit_reached') {
      showAlert('⏱ ' + (data.message || 'Search limit reached. Please try again later.'), 'warning');
      return;
    }
    if (data.error) {
      showAlert(data.message || 'Something went wrong. Please try again.', 'danger');
      return;
    }
    if (!data.stores || data.stores.length === 0) {
      showAlert('No supermarkets found within 5km. Try entering a postcode instead.', 'info');
      return;
    }

    const tierLabel = { budget: 'budget-friendly', mid: 'mid-range', premium: 'premium' };
    const heading = document.createElement('p');
    heading.className = 'text-muted small mb-2';
    heading.textContent = 'Stores near you — ranked for your '
      + (tierLabel[data.user_tier] || data.user_tier) + ' budget:';
    resultsDiv.appendChild(heading);

    const row = document.createElement('div');
    row.className = 'row g-2';
    data.stores.forEach(function (store) {
      const col = document.createElement('div');
      col.className = 'col-12 col-md-6';
      col.appendChild(buildStoreCard(store));
      row.appendChild(col);
    });
    resultsDiv.appendChild(row);

    if (disclaimer) disclaimer.style.display = '';
  }

  function buildStoreCard(store) {
    const card = document.createElement('div');
    card.className = 'card h-100';

    const body = document.createElement('div');
    body.className = 'card-body py-2 px-3';

    // Header: name + tier badge + distance
    const header = document.createElement('div');
    header.className = 'd-flex align-items-center flex-wrap gap-2 mb-1';

    const name = document.createElement('strong');
    name.textContent = store.name;

    const badge = document.createElement('span');
    badge.className = 'badge ' + tierBadgeClass(store.tier);
    badge.textContent = store.tier;

    const dist = document.createElement('span');
    dist.className = 'text-muted small ms-auto';
    dist.textContent = store.distance_m < 1000
      ? store.distance_m + 'm away'
      : (store.distance_m / 1000).toFixed(1) + 'km away';

    header.append(name, badge, dist);

    // Address
    const addr = document.createElement('p');
    addr.className = 'text-muted small mb-2';
    addr.textContent = store.address || '';

    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'd-flex flex-wrap gap-2';

    // Google Maps link
    if (store.maps_url && store.maps_url.startsWith('https://www.google.com/maps/')) {
      const mapsLink = document.createElement('a');
      mapsLink.className = 'btn btn-outline-secondary btn-sm';
      mapsLink.textContent = 'View on Google Maps';
      mapsLink.href = store.maps_url;
      mapsLink.target = '_blank';
      mapsLink.rel = 'noopener noreferrer';
      actions.appendChild(mapsLink);
    }

    // Ingredient shop links toggle
    const searchUrls = store.search_urls || {};
    const ingredients = Object.keys(searchUrls);
    if (ingredients.length > 0) {
      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'btn btn-success btn-sm';
      toggleBtn.textContent = 'Shop ingredients here';

      const linksDiv = document.createElement('div');
      linksDiv.className = 'mt-2';
      linksDiv.style.display = 'none';

      ingredients.forEach(function (ing) {
        const a = document.createElement('a');
        a.className = 'btn btn-outline-success btn-sm me-1 mb-1';
        a.textContent = ing.length > 35 ? ing.substring(0, 32) + '…' : ing;
        a.title = ing;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        const url = searchUrls[ing];
        if (url && url.startsWith('https://')) a.href = url;
        linksDiv.appendChild(a);
      });

      toggleBtn.addEventListener('click', function () {
        const hidden = linksDiv.style.display === 'none';
        linksDiv.style.display = hidden ? '' : 'none';
        toggleBtn.textContent = hidden ? 'Hide ingredient links' : 'Shop ingredients here';
      });

      actions.appendChild(toggleBtn);
      body.append(header, addr, actions, linksDiv);
    } else {
      body.append(header, addr, actions);
    }

    card.appendChild(body);
    return card;
  }

  function tierBadgeClass(tier) {
    if (tier === 'budget') return 'bg-success';
    if (tier === 'mid') return 'bg-warning text-dark';
    if (tier === 'premium') return 'stores-badge-premium';
    return 'bg-secondary';
  }

  function showAlert(msg, type) {
    resultsDiv.innerHTML = '';
    const div = document.createElement('div');
    div.className = 'alert alert-' + type + ' py-2';
    div.textContent = msg;
    resultsDiv.appendChild(div);
  }
})();
