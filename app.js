const express = require('express');
const fetch = require('node-fetch');
const app = express();
const port = 3000;

// Base URL for the Flask REST API (Sprint 1)
const API_BASE = 'http://127.0.0.1:5000';

app.set('view engine', 'ejs');
app.set('views', __dirname);
app.use(express.static('public'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ─── API Helper ────────────────────────────────────────────────────────────────────
/**
 * Makes an API call to the Flask backend
 * @param {string} path - API endpoint path
 * @param {object} options - Fetch options (method, body, etc.)
 * @returns {Promise<{status: number, data: any}>} Response status and parsed JSON data
 */
async function apiCall(path, options = {}) {
  try {
    const url = `${API_BASE}${path}`;
    const config = {
      headers: { 'Content-Type': 'application/json' },
      ...options
    };

    const response = await fetch(url, config);
    const data = await response.json();

    return {
      status: response.status,
      data: data
    };
  } catch (error) {
    console.error(`API call failed for ${path}:`, error);
    return {
      status: 500,
      data: { error: 'Network error or API unavailable' }
    };
  }
}

// ─── HOME ──────────────────────────────────────────────────────────────────────
app.get('/', async (req, res) => {
  try {
    const [membersRes, eventsRes, regsRes] = await Promise.all([
      apiCall('/members'),
      apiCall('/events'),
      apiCall('/registrations')
    ]);

    res.render('index', {
      memberCount: Array.isArray(membersRes.data) ? membersRes.data.length : 0,
      eventCount: Array.isArray(eventsRes.data) ? eventsRes.data.length : 0,
      regCount: Array.isArray(regsRes.data) ? regsRes.data.length : 0,
      error: null
    });
  } catch (e) {
    res.render('index', {
      memberCount: 0,
      eventCount: 0,
      regCount: 0,
      error: 'Could not connect to API.'
    });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// MEMBERS
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/members', async (req, res) => {
  const { data } = await apiCall('/members');
  res.render('members', {
    members: Array.isArray(data) ? data : [],
    flash: req.query.flash || null,
    formError: null
  });
});

app.post('/members/create', async (req, res) => {
  const { name, details, title, level } = req.body;
  const { status, data } = await apiCall('/members', {
    method: 'POST',
    body: JSON.stringify({ name, details, title, level })
  });

  if (status === 201) {
    res.redirect('/members?flash=Member+created+successfully');
  } else {
    const membersRes = await apiCall('/members');
    res.render('members', {
      members: Array.isArray(membersRes.data) ? membersRes.data : [],
      flash: null,
      formError: data.error || 'Could not create member'
    });
  }
});

app.post('/members/update', async (req, res) => {
  const { id, name, details, title, level } = req.body;
  const { status, data } = await apiCall(`/members/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ name, details, title, level })
  });

  if (status === 200) {
    res.redirect('/members?flash=Member+updated+successfully');
  } else {
    const membersRes = await apiCall('/members');
    res.render('members', {
      members: Array.isArray(membersRes.data) ? membersRes.data : [],
      flash: null,
      formError: data.error || 'Could not update member'
    });
  }
});

app.post('/members/delete', async (req, res) => {
  const { id } = req.body;
  await apiCall(`/members/${id}`, { method: 'DELETE' });
  res.redirect('/members?flash=Member+deleted');
});

// ═══════════════════════════════════════════════════════════════════════════════
// EVENTS
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/events', async (req, res) => {
  const { data } = await apiCall('/events');
  res.render('events', {
    events: Array.isArray(data) ? data : [],
    flash: req.query.flash || null,
    formError: null
  });
});

app.post('/events/create', async (req, res) => {
  const { name, capacity, level, date } = req.body;
  const { status, data } = await apiCall('/events', {
    method: 'POST',
    body: JSON.stringify({
      name,
      capacity: parseInt(capacity),
      level,
      date
    })
  });

  if (status === 201) {
    res.redirect('/events?flash=Event+created+successfully');
  } else {
    const eventsRes = await apiCall('/events');
    res.render('events', {
      events: Array.isArray(eventsRes.data) ? eventsRes.data : [],
      flash: null,
      formError: data.error || 'Could not create event'
    });
  }
});

app.post('/events/update', async (req, res) => {
  const { id, name, capacity, level, date } = req.body;
  const { status, data } = await apiCall(`/events/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
      name,
      capacity: parseInt(capacity),
      level,
      date
    })
  });

  if (status === 200) {
    res.redirect('/events?flash=Event+updated+successfully');
  } else {
    const eventsRes = await apiCall('/events');
    res.render('events', {
      events: Array.isArray(eventsRes.data) ? eventsRes.data : [],
      flash: null,
      formError: data.error || 'Could not update event'
    });
  }
});

app.post('/events/delete', async (req, res) => {
  const { id } = req.body;
  await apiCall(`/events/${id}`, { method: 'DELETE' });
  res.redirect('/events?flash=Event+deleted');
});

// ═══════════════════════════════════════════════════════════════════════════════
// REGISTRATIONS
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/registrations', async (req, res) => {
  const [regsRes, membersRes, eventsRes] = await Promise.all([
    apiCall('/registrations'),
    apiCall('/members'),
    apiCall('/events')
  ]);

  res.render('registrations', {
    registrations: Array.isArray(regsRes.data) ? regsRes.data : [],
    members: Array.isArray(membersRes.data) ? membersRes.data : [],
    events: Array.isArray(eventsRes.data) ? eventsRes.data : [],
    flash: req.query.flash || null,
    formError: null
  });
});

app.post('/registrations/create', async (req, res) => {
  const { event_id, member_id } = req.body;
  const { status, data } = await apiCall('/registrations', {
    method: 'POST',
    body: JSON.stringify({
      event_id: parseInt(event_id),
      member_id: parseInt(member_id)
    })
  });

  if (status === 201) {
    res.redirect('/registrations?flash=Registration+created+successfully');
  } else {
    const [regsRes, membersRes, eventsRes] = await Promise.all([
      apiCall('/registrations'),
      apiCall('/members'),
      apiCall('/events')
    ]);

    res.render('registrations', {
      registrations: Array.isArray(regsRes.data) ? regsRes.data : [],
      members: Array.isArray(membersRes.data) ? membersRes.data : [],
      events: Array.isArray(eventsRes.data) ? eventsRes.data : [],
      flash: null,
      formError: data.error || 'Could not create registration'
    });
  }
});

app.post('/registrations/update', async (req, res) => {
  const { id, event_id, member_id } = req.body;
  const { status, data } = await apiCall(`/registrations/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
      event_id: parseInt(event_id),
      member_id: parseInt(member_id)
    })
  });

  if (status === 200) {
    res.redirect('/registrations?flash=Registration+updated+successfully');
  } else {
    const [regsRes, membersRes, eventsRes] = await Promise.all([
      apiCall('/registrations'),
      apiCall('/members'),
      apiCall('/events')
    ]);

    res.render('registrations', {
      registrations: Array.isArray(regsRes.data) ? regsRes.data : [],
      members: Array.isArray(membersRes.data) ? membersRes.data : [],
      events: Array.isArray(eventsRes.data) ? eventsRes.data : [],
      flash: null,
      formError: data.error || 'Could not update registration'
    });
  }
});

app.post('/registrations/delete', async (req, res) => {
  const { id } = req.body;
  await apiCall(`/registrations/${id}`, { method: 'DELETE' });
  res.redirect('/registrations?flash=Registration+deleted');
});

// ─── Event Members view ────────────────────────────────────────────────────────
app.get('/events/:id/members', async (req, res) => {
  const eventId = req.params.id;
  const [eventRes, membersRes, allEventsRes] = await Promise.all([
    apiCall(`/events/${eventId}`),
    apiCall(`/events/${eventId}/members`),
    apiCall('/events')
  ]);

  res.render('event-members', {
    event: eventRes.data,
    members: Array.isArray(membersRes.data) ? membersRes.data : [],
    allEvents: Array.isArray(allEventsRes.data) ? allEventsRes.data : [],
    selectedEventId: parseInt(eventId)
  });
});

app.listen(port, () => {
  console.log(`Org Portal UI running at http://localhost:${port}`);
});