// Shared helpers for the VSL pages: visitor id, UTM persistence, event tracking and video retention.
(function () {
  const config = window.VSL_CONFIG;
  const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content"];

  function storageGet(store, key) {
    try { return window[store].getItem(key); } catch (e) { return null; }
  }

  function storageSet(store, key, value) {
    try { window[store].setItem(key, value); } catch (e) { /* storage unavailable */ }
  }

  function randomId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 12);
  }

  let visitorId = storageGet("localStorage", "vsl_visitor_id");
  if (!visitorId) {
    visitorId = randomId();
    storageSet("localStorage", "vsl_visitor_id", visitorId);
  }

  // UTMs from the URL win; otherwise reuse the ones captured earlier in this visit.
  const params = new URLSearchParams(location.search);
  const utm = {};
  UTM_KEYS.forEach(function (key) {
    const value = params.get(key) || storageGet("sessionStorage", key);
    if (value) {
      utm[key] = value.slice(0, 255);
      storageSet("sessionStorage", key, utm[key]);
    }
  });

  function apiUrl(path) {
    return config.apiBase + path + "?tenant=" + encodeURIComponent(config.tenant);
  }

  function track(eventType, extra) {
    const body = Object.assign({ visitor_id: visitorId, event_type: eventType }, utm, extra || {});
    fetch(apiUrl("/vsl/events"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      keepalive: true,
    }).catch(function () { /* tracking must never break the page */ });
  }

  // Adds the visit's UTMs to an outbound link (e.g. the VitaClini sign-up page).
  function withUtm(url) {
    try {
      const target = new URL(url, location.href);
      Object.keys(utm).forEach(function (key) { target.searchParams.set(key, utm[key]); });
      return target.toString();
    } catch (e) {
      return url;
    }
  }

  // Embeds the configured video and reports play, 25/50/75/100% milestones and seconds watched.
  // onWatched(seconds) is called as real playback time accumulates (seeking forward does not count).
  function mountVideo(container, onWatched) {
    const video = config.video;
    const reached = {};
    let watched = 0;
    let lastTime = null;

    function onTime(current, duration, playing) {
      if (playing && lastTime !== null) {
        const delta = current - lastTime;
        if (delta > 0 && delta < 2) {
          watched += delta;
          onWatched(watched);
        }
      }
      lastTime = current;
      if (!duration) return;
      [25, 50, 75, 100].forEach(function (pct) {
        const threshold = pct === 100 ? duration - 1 : (duration * pct) / 100;
        if (!reached[pct] && current >= threshold) {
          reached[pct] = true;
          track("progress_" + pct, { video_seconds: Math.round(current) });
        }
      });
    }

    function onPlay() {
      if (!reached.play) {
        reached.play = true;
        track("play");
      }
    }

    if (video.kind === "file") {
      const el = document.createElement("video");
      el.src = video.src;
      el.controls = true;
      el.playsInline = true;
      el.preload = "metadata";
      el.addEventListener("play", onPlay);
      el.addEventListener("timeupdate", function () {
        onTime(el.currentTime, el.duration, !el.paused);
      });
      container.appendChild(el);
      return;
    }

    if (video.kind === "youtube") {
      const holder = document.createElement("div");
      container.appendChild(holder);
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(script);
      window.onYouTubeIframeAPIReady = function () {
        const player = new YT.Player(holder, {
          videoId: video.id,
          playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
          events: {
            onStateChange: function (event) {
              if (event.data === YT.PlayerState.PLAYING) onPlay();
            },
          },
        });
        setInterval(function () {
          if (!player.getCurrentTime) return;
          const playing = player.getPlayerState() === YT.PlayerState.PLAYING;
          onTime(player.getCurrentTime(), player.getDuration(), playing);
        }, 1000);
      };
      return;
    }

    container.classList.add("video-empty");
    container.textContent = "Vídeo não configurado. Defina VSL_VIDEO_URL no .env (arquivo .mp4 ou link do YouTube).";
  }

  window.VSL = {
    config: config,
    visitorId: visitorId,
    utm: utm,
    track: track,
    apiUrl: apiUrl,
    withUtm: withUtm,
    mountVideo: mountVideo,
    storageGet: storageGet,
    storageSet: storageSet,
  };
})();
