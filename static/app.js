/* =============================================
   Media Downloader — Client App
   Synthwave redesign: 2026
   ============================================= */

// DOM refs
const urlInput = document.getElementById('url')
const downloadBtn = document.getElementById('download')
const modeBtns = document.querySelectorAll('#mode_segmented button')
const audioGroup = document.getElementById('audio_group')
const audioSelect = document.getElementById('audio_format')
const videoGroup = document.getElementById('video_group')
const videoSelect = document.getElementById('video_format')
const ytChoice = document.getElementById('youtube_choice')
const ytAudio = document.getElementById('yt_audio')
const ytVideo = document.getElementById('yt_video')
const navBtns = document.querySelectorAll('.nav-btn')

let mode = 'audio'

// ---- Mode toggle ----
modeBtns.forEach(b => b.addEventListener('click', () => {
  modeBtns.forEach(x => x.classList.remove('active'))
  b.classList.add('active')
  mode = b.dataset.mode

  // Show/hide format selectors
  if (mode === 'audio') {
    audioGroup.style.display = 'block'
    videoGroup.style.display = 'none'
  } else {
    audioGroup.style.display = 'none'
    videoGroup.style.display = 'block'
  }

  // YouTube URL detection — hide the legacy youtube_choice block entirely
  const url = urlInput.value.trim()
  ytChoice.style.display = 'none'
}))

// ---- YouTube Audio/Video quick choice ----
if (ytAudio && ytVideo) {
  ytAudio.addEventListener('click', () => {
    mode = 'audio'
    ytAudio.classList.add('active')
    ytVideo.classList.remove('active')
    // Sync the mode segmented too
    document.querySelector('#mode_audio')?.classList.add('active')
    document.querySelector('#mode_video')?.classList.remove('active')
    audioGroup.style.display = 'block'
    videoGroup.style.display = 'none'
  })
  ytVideo.addEventListener('click', () => {
    mode = 'video'
    ytVideo.classList.add('active')
    ytAudio.classList.remove('active')
    document.querySelector('#mode_video')?.classList.add('active')
    document.querySelector('#mode_audio')?.classList.remove('active')
    audioGroup.style.display = 'none'
    videoGroup.style.display = 'block'
  })
}

// Detect YouTube in URL input
urlInput.addEventListener('input', () => {
  // Legacy youtube_choice block is hidden — main mode selector handles everything
})

// ---- Download ----
downloadBtn.addEventListener('click', async () => {
  const url = urlInput.value.trim()
  if (!url) return alert('Enter a URL')
  const audio_format = audioSelect ? audioSelect.value : 'mp3'
  const video_format = videoSelect ? videoSelect.value : 'mp4'
  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ url, mode, audio_format, video_format })
    })
    const data = await res.json()
    showPanel('panel_logs')
    loadLog(data.job_id)
    loadList()
  } catch (e) {
    alert('Error starting job: ' + e)
  }
})

// ---- Bottom Navigation ----
navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    showPanel(btn.dataset.panel)
  })
})

function showPanel(panelId) {
  // Hide all panels
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'))
  // Deactivate all nav buttons
  navBtns.forEach(n => n.classList.remove('active'))
  // Show target panel
  const panel = document.getElementById(panelId)
  if (panel) panel.classList.add('active')
  // Activate matching nav button
  const navBtn = document.querySelector(`.nav-btn[data-panel="${panelId}"]`)
  if (navBtn) navBtn.classList.add('active')
}

// ---- Backward-compat showTab (called from search/download helpers) ----
function showTab(oldId) {
  const map = {
    'tab_recent': 'panel_recent',
    'tab_logs': 'panel_logs',
    'tab_search': 'panel_search'
  }
  showPanel(map[oldId] || 'panel_recent')
}

// ---- Log polling ----
async function loadLog(jobId) {
  const logs = document.getElementById('logs')
  logs.textContent = `Loading log for ${jobId}...`
  const logUrl = `/api/log/${jobId}`
  let last = ''
  const int = setInterval(async () => {
    try {
      const r = await fetch(logUrl)
      if (r.status === 404) {
        logs.textContent = 'Log not found yet...'
        return
      }
      const txt = await r.text()
      if (txt !== last) {
        logs.textContent = txt
        last = txt
        // Auto-scroll to bottom
        logs.scrollTop = logs.scrollHeight
      }
      if (/Exit code:/m.test(txt)) {
        clearInterval(int)
        loadList()
      }
    } catch (e) {
      console.error(e)
    }
  }, 1000)
}

// ---- Downloads list ----
async function loadList() {
  try {
    const r = await fetch('/api/list')
    const data = await r.json()
    const list = document.getElementById('list')
    list.innerHTML = ''
    if (!data.items || data.items.length === 0) {
      list.innerHTML = '<div class="empty-state">No downloads yet.</div>'
      return
    }
    data.items.slice().reverse().forEach(it => {
      const item = document.createElement('div')
      item.className = 'dl-item'

      const info = document.createElement('div')
      info.className = 'dl-item-info'

      const idEl = document.createElement('div')
      idEl.className = 'dl-id'
      idEl.textContent = it.id.substring(0, 8) + '…'
      info.appendChild(idEl)

      it.files.forEach(f => {
        const a = document.createElement('a')
        a.className = 'dl-file'
        a.href = `/api/file/${it.id}/${encodeURIComponent(f)}`
        a.textContent = f
        info.appendChild(a)
      })

      item.appendChild(info)

      const actions = document.createElement('div')
      actions.className = 'dl-item-actions'
      const logBtn = document.createElement('button')
      logBtn.textContent = 'Log'
      logBtn.addEventListener('click', () => {
        showPanel('panel_logs')
        loadLog(it.id)
      })
      actions.appendChild(logBtn)
      item.appendChild(actions)

      list.appendChild(item)
    })
  } catch (_) {
    // Silently retry next render
  }
}

// ---- Search ----
let searchResults = []
let searchPage = 0
const PER_PAGE = 8

document.getElementById('search_query').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('search_btn').click()
})

document.getElementById('search_btn').addEventListener('click', async () => {
  const q = document.getElementById('search_query').value.trim()
  const engine = document.getElementById('search_engine').value
  if (!q) return alert('Enter search query')
  try {
    const r = await fetch('/api/search', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ engine, query: q, limit: 50 })
    })
    const data = await r.json()
    searchResults = data.results || []
    searchPage = 0
    renderSearchPage()
  } catch (e) {
    console.error('Search failed:', e)
  }
})

function renderSearchPage() {
  const res = document.getElementById('search_results')
  res.innerHTML = ''

  if (!searchResults.length) {
    res.innerHTML = '<div class="empty-state">No results found</div>'
    return
  }

  const totalPages = Math.ceil(searchResults.length / PER_PAGE)
  const start = searchPage * PER_PAGE
  const pageItems = searchResults.slice(start, start + PER_PAGE)

  pageItems.forEach(item => {
    const row = document.createElement('div')
    row.className = 'result-item'

    const thumb = document.createElement('div')
    thumb.className = 'result-thumb'
    if (item.thumbnail) {
      const img = document.createElement('img')
      img.src = item.thumbnail
      img.alt = ''
      img.loading = 'lazy'
      thumb.appendChild(img)
    }
    row.appendChild(thumb)

    const meta = document.createElement('div')
    meta.className = 'result-meta'
    const title = document.createElement('div')
    title.className = 'title'
    title.textContent = item.title
    meta.appendChild(title)
    const sub = document.createElement('div')
    sub.className = 'sub'
    const parts = []
    if (item.uploader) parts.push(item.uploader)
    if (item.duration) parts.push(formatDuration(item.duration))
    sub.textContent = parts.join(' · ')
    meta.appendChild(sub)
    if (item.description) {
      const desc = document.createElement('div')
      desc.className = 'desc'
      desc.textContent = item.description.replace(/<[^>]*>/g, '').substring(0, 80) + (item.description.length > 80 ? '…' : '')
      meta.appendChild(desc)
    }
    row.appendChild(meta)

    const actions = document.createElement('div')
    actions.className = 'result-actions'
    const dlAudio = document.createElement('button')
    dlAudio.textContent = 'Audio'
    dlAudio.addEventListener('click', () => startDownload(item.url, 'audio'))
    actions.appendChild(dlAudio)
    if (document.getElementById('search_engine').value === 'youtube') {
      const dlVideo = document.createElement('button')
      dlVideo.textContent = 'Video'
      dlVideo.addEventListener('click', () => startDownload(item.url, 'video'))
      actions.appendChild(dlVideo)
    }
    row.appendChild(actions)

    res.appendChild(row)
  })

  // Pagination
  if (totalPages > 1) {
    const pag = document.createElement('div')
    pag.className = 'pagination'

    const prevBtn = document.createElement('button')
    prevBtn.className = 'page-btn'
    prevBtn.innerHTML = '&#8592;'
    prevBtn.disabled = searchPage === 0
    prevBtn.addEventListener('click', () => { if (searchPage > 0) { searchPage--; renderSearchPage() } })
    pag.appendChild(prevBtn)

    const info = document.createElement('span')
    info.className = 'page-info'
    info.textContent = `${searchPage + 1} / ${totalPages}`
    pag.appendChild(info)

    const nextBtn = document.createElement('button')
    nextBtn.className = 'page-btn'
    nextBtn.innerHTML = '&#8594;'
    nextBtn.disabled = searchPage >= totalPages - 1
    nextBtn.addEventListener('click', () => { if (searchPage < totalPages - 1) { searchPage++; renderSearchPage() } })
    pag.appendChild(nextBtn)

    res.appendChild(pag)
  }
}

// ---- Helper: start download from search ----
function startDownload(url, dlMode) {
  const audio_format = audioSelect ? audioSelect.value : 'mp3'
  const video_format = videoSelect ? videoSelect.value : 'mp4'
  fetch('/api/download', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url, mode: dlMode, audio_format, video_format })
  })
    .then(r => r.json())
    .then(d => {
      showPanel('panel_logs')
      loadLog(d.job_id)
      loadList()
    })
    .catch(e => alert('Failed: ' + e))
}

// ---- Duration formatter ----
function formatDuration(seconds) {
  if (!seconds) return ''
  const s = Math.floor(Number(seconds))
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}:${String(m % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

// ---- Init ----
loadList()

// ---- ffmpeg status ----
fetch('/api/ffmpeg')
  .then(r => r.json())
  .then(d => {
    const badge = document.getElementById('ffmpeg_badge')
    if (badge) {
      badge.textContent = d.available ? 'ffmpeg ✓' : 'ffmpeg ✗ (will fail)'
      badge.style.color = d.available ? 'rgba(255,255,255,0.5)' : '#ff4444'
    }
  })
  .catch(() => {
    const badge = document.getElementById('ffmpeg_badge')
    if (badge) badge.textContent = 'ffmpeg: unknown'
  })
