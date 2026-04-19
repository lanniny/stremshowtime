const POLL_INTERVAL_MS = 1500;

const elements = {
  roomTitle: document.getElementById("roomTitle"),
  roomMeta: document.getElementById("roomMeta"),
  sessionStatus: document.getElementById("sessionStatus"),
  productBadge: document.getElementById("productBadge"),
  hostBadge: document.getElementById("hostBadge"),
  metricBarrage: document.getElementById("metricBarrage"),
  metricReplies: document.getElementById("metricReplies"),
  metricAlerts: document.getElementById("metricAlerts"),
  nextLiveChip: document.getElementById("nextLiveChip"),
  aigcpanelChip: document.getElementById("aigcpanelChip"),
  feishuChip: document.getElementById("feishuChip"),
  voiceChip: document.getElementById("voiceChip"),
  spotlightProduct: document.getElementById("spotlightProduct"),
  spotlightHost: document.getElementById("spotlightHost"),
  stageSpeakingImage: document.getElementById("stageSpeakingImage"),
  stageSubtitle: document.getElementById("stageSubtitle"),
  stageSubtitleSpeaker: document.getElementById("stageSubtitleSpeaker"),
  stageSubtitleText: document.getElementById("stageSubtitleText"),
  currentReplyText: document.getElementById("currentReplyText"),
  currentReplyBubble: document.getElementById("currentReplyBubble"),
  barrageFeed: document.getElementById("barrageFeed"),
  alertFeed: document.getElementById("alertFeed"),
  errorFeed: document.getElementById("errorFeed"),
  replyHistory: document.getElementById("replyHistory"),
  scriptPreview: document.getElementById("scriptPreview"),
  reviewPreview: document.getElementById("reviewPreview"),
  bridgeStatus: document.getElementById("bridgeStatus"),
  barrageStatus: document.getElementById("barrageStatus"),
  feishuStatus: document.getElementById("feishuStatus"),
  aigcStatus: document.getElementById("aigcStatus"),
  aigcResult: document.getElementById("aigcResult"),
  relayResult: document.getElementById("relayResult"),
  stageVideo: document.getElementById("stageVideo"),
  stageFrame: document.getElementById("stageFrame"),
  sessionForm: document.getElementById("sessionForm"),
  barrageForm: document.getElementById("barrageForm"),
  manualBroadcastForm: document.getElementById("manualBroadcastForm"),
  manualReplyForm: document.getElementById("manualReplyForm"),
  loadDemoBtn: document.getElementById("loadDemoBtn"),
  feishuTestBtn: document.getElementById("feishuTestBtn"),
  reviewBtn: document.getElementById("reviewBtn"),
  enableVoiceBtn: document.getElementById("enableVoiceBtn"),
  speakNowBtn: document.getElementById("speakNowBtn"),
  stopVoiceBtn: document.getElementById("stopVoiceBtn"),
  aigcPingBtn: document.getElementById("aigcPingBtn"),
  aigcSubmitBtn: document.getElementById("aigcSubmitBtn"),
  aigcQueryBtn: document.getElementById("aigcQueryBtn"),
  aigcCancelBtn: document.getElementById("aigcCancelBtn")
};

const voiceState = {
  enabled: false,
  available: "speechSynthesis" in window,
  lastSpokenSignature: "",
  speaking: false
};

const stageState = {
  activeReplySignature: "",
  speakingUntil: 0
};

const liveMediaState = {
  defaultStageVideo: "",
  generatedVideoUrl: "",
  lastMediaSignature: "",
  audio: typeof Audio !== "undefined" ? new Audio() : null
};

let latestState = null;

if (liveMediaState.audio) {
  liveMediaState.audio.preload = "auto";
  liveMediaState.audio.addEventListener("play", () => {
    voiceState.speaking = true;
    updateVoiceChip("AIGCPanel 真人音色回放中");
  });
  liveMediaState.audio.addEventListener("ended", () => {
    voiceState.speaking = false;
    if (latestState?.integrations?.aigcpanel?.enabled) {
      updateVoiceChip("AIGCPanel 已接管语音");
    }
  });
  liveMediaState.audio.addEventListener("pause", () => {
    voiceState.speaking = false;
  });
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
}

async function postJson(path, body = {}) {
  return requestJson(path, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

function previewText(text, limit = 900) {
  if (!text) {
    return "暂无数据。";
  }
  return text.length > limit ? `${text.slice(0, limit)}\n\n...` : text;
}

function renderCards(container, items, emptyText, renderItem) {
  if (!items || items.length === 0) {
    container.className = `${container.className.split(" ").filter(Boolean)[0]} empty-state`;
    container.textContent = emptyText;
    return;
  }
  container.className = container.className.replace(" empty-state", "");
  container.innerHTML = items.map(renderItem).join("");
}

function updateVoiceChip(message) {
  elements.voiceChip.textContent = message;
}

function currentReplySignature(reply) {
  if (!reply) {
    return "";
  }
  return `${reply.timestamp || ""}|${reply.user || ""}|${reply.tts_text || reply.reply || ""}`;
}

function estimateSpeechDurationMs(text) {
  const length = String(text || "").trim().length;
  return Math.max(2600, Math.min(9000, 1200 + length * 220));
}

function activateStageSpeech(reply) {
  if (!reply) {
    return;
  }
  const signature = currentReplySignature(reply);
  if (!signature) {
    return;
  }
  stageState.activeReplySignature = signature;
  stageState.speakingUntil = Date.now() + estimateSpeechDurationMs(reply.tts_text || reply.reply || "");
  elements.stageSubtitleSpeaker.textContent = `${reply.user || "数字人"} 正在播报`;
  elements.stageSubtitleText.textContent = reply.tts_text || reply.reply || "";
  elements.stageFrame.classList.add("is-speaking");
}

function setStageVideoSource(src, { loop = true } = {}) {
  if (!src) {
    return;
  }
  if (elements.stageVideo.getAttribute("src") !== src) {
    elements.stageVideo.setAttribute("src", src);
    elements.stageVideo.load();
  }
  elements.stageVideo.loop = loop;
  const playPromise = elements.stageVideo.play();
  if (playPromise && typeof playPromise.catch === "function") {
    playPromise.catch(() => {});
  }
}

function restoreDefaultStageVideo() {
  liveMediaState.generatedVideoUrl = "";
  if (liveMediaState.defaultStageVideo) {
    setStageVideoSource(liveMediaState.defaultStageVideo, { loop: true });
  }
}

function syncStageMode() {
  const speaking = Date.now() < stageState.speakingUntil || voiceState.speaking;
  if (speaking) {
    elements.stageFrame.classList.add("is-speaking");
  } else {
    elements.stageFrame.classList.remove("is-speaking");
  }
}

function speakText(text, options = {}) {
  if (!voiceState.available) {
    updateVoiceChip("当前浏览器不支持语音播报");
    return false;
  }

  const clean = String(text || "").trim();
  if (!clean) {
    updateVoiceChip("当前没有可播报内容");
    return false;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = "zh-CN";
  utterance.rate = 1.02;
  utterance.pitch = 1.0;
  utterance.volume = 1;

  const voices = window.speechSynthesis.getVoices();
  const preferredVoice =
    voices.find((voice) => voice.lang === "zh-CN" && /xiaoxiao|yunxi|xiaoyi|huihui|zh/i.test(voice.name)) ||
    voices.find((voice) => voice.lang === "zh-CN") ||
    voices[0];
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  utterance.onstart = () => {
    voiceState.speaking = true;
    updateVoiceChip(options.label || "正在播报");
  };
  utterance.onend = () => {
    voiceState.speaking = false;
    updateVoiceChip(voiceState.enabled ? "自动播报已开启" : "语音未开启");
  };
  utterance.onerror = () => {
    voiceState.speaking = false;
    updateVoiceChip("语音播报失败");
  };

  window.speechSynthesis.speak(utterance);
  return true;
}

function enableVoicePlayback() {
  if (!voiceState.available) {
    updateVoiceChip("当前浏览器不支持语音播报");
    return;
  }
  voiceState.enabled = true;
  elements.stageVideo.muted = false;
  elements.stageVideo.volume = 1;
  speakText("语音播报已开启，后续新回复会自动朗读。", { label: "语音已开启" });
}

function stopVoicePlayback() {
  if (voiceState.available) {
    window.speechSynthesis.cancel();
  }
  if (liveMediaState.audio) {
    liveMediaState.audio.pause();
    liveMediaState.audio.currentTime = 0;
  }
  voiceState.enabled = false;
  voiceState.speaking = false;
  updateVoiceChip("语音已停止");
}

function maybeSpeakReply(reply) {
  if (!voiceState.enabled || !reply || latestState?.integrations?.aigcpanel?.enabled) {
    return;
  }
  const signature = currentReplySignature(reply);
  if (!signature || signature === voiceState.lastSpokenSignature) {
    return;
  }
  const ok = speakText(reply.tts_text || reply.reply || "", { label: `正在播报 ${reply.user || "当前回复"}` });
  if (ok) {
    voiceState.lastSpokenSignature = signature;
    stageState.speakingUntil = Math.max(
      stageState.speakingUntil,
      Date.now() + estimateSpeechDurationMs(reply.tts_text || reply.reply || "")
    );
  }
}

function currentAigcMediaSignature(aigc) {
  if (!aigc) {
    return "";
  }
  return `${aigc.last_token || ""}|${aigc.last_media_kind || ""}|${aigc.last_media_url || ""}`;
}

function maybePlayAigcMedia(state) {
  const aigc = state.integrations?.aigcpanel || {};
  const mediaUrl = aigc.last_media_url || "";
  const mediaKind = aigc.last_media_kind || "";
  const signature = currentAigcMediaSignature(aigc);

  if (!mediaUrl || !mediaKind || !signature || signature === liveMediaState.lastMediaSignature) {
    return;
  }

  liveMediaState.lastMediaSignature = signature;
  if (mediaKind === "video") {
    liveMediaState.generatedVideoUrl = mediaUrl;
    setStageVideoSource(mediaUrl, { loop: false });
    voiceState.speaking = true;
    updateVoiceChip("AIGCPanel 真人视频回放中");
    return;
  }

  if (mediaKind === "audio" && liveMediaState.audio) {
    if (!liveMediaState.generatedVideoUrl) {
      restoreDefaultStageVideo();
    }
    liveMediaState.audio.pause();
    liveMediaState.audio.src = mediaUrl;
    liveMediaState.audio.currentTime = 0;
    const playPromise = liveMediaState.audio.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {
        updateVoiceChip("AIGCPanel 音频已回传，等待浏览器允许播放");
      });
    }
  }
}

function renderState(state) {
  latestState = state;
  const productName = state.product_name || "未选择商品";
  const hostName = state.host_name || "未设置主播";
  const barrageStatus = state.integrations?.barrage_source?.last_status || "idle";
  const feishu = state.integrations?.feishu || {};
  const aigc = state.integrations?.aigcpanel || {};

  elements.roomTitle.textContent = state.room_title || "数字人直播控制台";
  elements.roomMeta.textContent = `${productName} / ${hostName} / 会话 ${state.session_id || "未开始"}`;
  elements.sessionStatus.textContent = (state.session_status || "idle").toUpperCase();
  elements.productBadge.textContent = productName;
  elements.hostBadge.textContent = `主播：${hostName}`;
  elements.metricBarrage.textContent = String(state.stats?.barrages || 0);
  elements.metricReplies.textContent = String(state.stats?.replies || 0);
  elements.metricAlerts.textContent = String(state.stats?.alerts || 0);
  elements.nextLiveChip.textContent = `下场：${state.next_live_time || "待确认"}`;
  elements.aigcpanelChip.textContent = aigc.ready
    ? `AIGCPanel：${aigc.last_status || "ready"}`
    : aigc.enabled
      ? "AIGCPanel 已启用"
      : "AIGCPanel 未就绪";
  elements.feishuChip.textContent = feishu.configured
    ? `飞书：${feishu.last_alert_status || "ready"}`
    : "飞书未配置";
  if (aigc.last_media_url) {
    updateVoiceChip(
      aigc.last_media_kind === "video" ? "AIGCPanel 真人视频" : "AIGCPanel 真人音色"
    );
  } else if (aigc.enabled) {
    updateVoiceChip(aigc.last_token ? "等待 AIGCPanel 回传" : "AIGCPanel 已接管语音");
  } else if (!voiceState.available) {
    updateVoiceChip("当前浏览器不支持语音");
  } else if (voiceState.speaking) {
    updateVoiceChip("正在播报");
  } else if (voiceState.enabled) {
    updateVoiceChip("自动播报已开启");
  } else {
    updateVoiceChip("语音未开启");
  }
  elements.spotlightProduct.textContent = productName;
  elements.spotlightHost.textContent = `当前主播：${hostName}`;
  if (state.media?.speaking_image) {
    elements.stageSpeakingImage.setAttribute("src", state.media.speaking_image);
  }
  elements.currentReplyText.textContent =
    state.current_reply?.tts_text || "还没有生成回复，先点击“载入完整演示”或手动注入弹幕。";
  elements.stageSubtitleText.textContent =
    state.current_reply?.tts_text || "新回复出现后，这里会显示当前正在播报的内容。";
  elements.stageSubtitleSpeaker.textContent =
    state.current_reply?.user ? `${state.current_reply.user} 正在播报` : "数字人待命中";
  elements.scriptPreview.textContent = previewText(state.script_text, 1400);
  elements.reviewPreview.textContent = previewText(state.review?.markdown, 1400);
  elements.bridgeStatus.textContent = "已连接";
  elements.barrageStatus.textContent = `${barrageStatus} / ${state.integrations?.barrage_source?.last_detail || "等待接入"}`;
  elements.feishuStatus.textContent = feishu.configured
    ? `${feishu.last_test_status || feishu.last_alert_status || "ready"}`
    : "未配置";
  elements.aigcStatus.textContent = aigc.enabled
    ? `${aigc.last_action || "enabled"} / ${aigc.last_status || "ready"}${aigc.last_media_kind ? ` / ${aigc.last_media_kind}` : ""}`
    : "未启用";

  renderCards(
    elements.barrageFeed,
    state.barrage_entries,
    "还没有弹幕进入桥。",
    (entry) => `
      <article class="feed-card category-${entry.category || "E"}">
        <div class="feed-meta">${entry.user || "匿名用户"} · ${entry.category || "E"} · ${entry.timestamp || ""}</div>
        <div class="feed-message">${entry.message || ""}</div>
        <div class="feed-reply">${entry.reply || "静默忽略"}</div>
        <div class="feed-actions">
          <button
            class="mini-button quote-barrage-btn"
            type="button"
            data-user="${encodeURIComponent(entry.user || "")}"
            data-message="${encodeURIComponent(entry.message || "")}"
          >
            引用回复
          </button>
        </div>
      </article>
    `
  );

  renderCards(
    elements.alertFeed,
    state.alerts,
    "当前没有投诉告警。",
    (entry) => `
      <article class="alert-card">
        <div class="card-meta">${entry.timestamp || ""}</div>
        <div><strong>${entry.user || "匿名用户"}</strong>：${entry.message || ""}</div>
        <div class="muted">状态：${entry.status || "unknown"}</div>
      </article>
    `
  );

  renderCards(
    elements.errorFeed,
    state.recent_errors,
    "暂无错误。",
    (entry) => `
      <article class="error-card">
        <div>${entry}</div>
      </article>
    `
  );

  renderCards(
    elements.replyHistory,
    state.reply_history,
    "还没有播报队列。",
    (entry) => `
      <article class="reply-card">
        <div class="card-meta">${entry.timestamp || ""} · ${entry.category || ""}</div>
        <div><strong>${entry.user || "匿名用户"}</strong></div>
        <div class="feed-reply">${entry.tts_text || entry.reply || ""}</div>
      </article>
    `
  );

  const stageVideo = state.media?.stage_video;
  if (stageVideo) {
    liveMediaState.defaultStageVideo = stageVideo;
    if (!liveMediaState.generatedVideoUrl && elements.stageVideo.getAttribute("src") !== stageVideo) {
      elements.stageVideo.setAttribute("poster", state.media?.poster_image || "");
      setStageVideoSource(stageVideo, { loop: true });
    }
  }

  const signature = currentReplySignature(state.current_reply);
  if (signature && signature !== stageState.activeReplySignature) {
    activateStageSpeech(state.current_reply);
  }
  maybePlayAigcMedia(state);
  maybeSpeakReply(state.current_reply);
  syncStageMode();

  if (state.current_reply?.tts_text) {
    elements.currentReplyBubble.style.borderColor = "rgba(255, 167, 118, 0.55)";
  } else {
    elements.currentReplyBubble.style.borderColor = "rgba(255, 167, 118, 0.24)";
  }
}

async function refreshState() {
  try {
    const state = await requestJson("/api/state");
    renderState(state);
  } catch (error) {
    elements.bridgeStatus.textContent = `连接失败：${error.message}`;
  }
}

async function handleAction(run, outputElement) {
  outputElement.textContent = "处理中...";
  try {
    const result = await run();
    outputElement.textContent = JSON.stringify(result, null, 2);
    await refreshState();
  } catch (error) {
    outputElement.textContent = error.message;
  }
}

elements.sessionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.sessionForm);
  await handleAction(
    () =>
      postJson("/api/session/start", {
        room_title: formData.get("room_title"),
        product: formData.get("product"),
        host_name: formData.get("host_name"),
        next_live_time: formData.get("next_live_time")
      }),
    elements.relayResult
  );
});

elements.barrageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.barrageForm);
  await handleAction(
    () =>
      postJson("/api/barrage", {
        user: formData.get("user"),
        message: formData.get("message")
      }),
    elements.relayResult
  );
  elements.barrageForm.reset();
});

elements.manualBroadcastForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.manualBroadcastForm);
  await handleAction(
    () =>
      postJson("/api/broadcast/manual", {
        speaker: formData.get("speaker"),
        text: formData.get("text")
      }),
    elements.relayResult
  );
});

elements.manualReplyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.manualReplyForm);
  await handleAction(
    () =>
      postJson("/api/barrage/reply", {
        user: formData.get("user"),
        message: formData.get("message"),
        reply: formData.get("reply"),
        category: formData.get("category")
      }),
    elements.relayResult
  );
});

elements.barrageFeed.addEventListener("click", (event) => {
  const target = event.target.closest(".quote-barrage-btn");
  if (!target || !elements.manualReplyForm) {
    return;
  }
  const user = decodeURIComponent(target.dataset.user || "");
  const message = decodeURIComponent(target.dataset.message || "");
  elements.manualReplyForm.elements.user.value = user;
  elements.manualReplyForm.elements.message.value = message;
  elements.manualReplyForm.elements.reply.focus();
});

elements.loadDemoBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/demo/load"), elements.relayResult)
);
elements.feishuTestBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/integrations/feishu/test"), elements.relayResult)
);
elements.reviewBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/review"), elements.relayResult)
);
elements.enableVoiceBtn.addEventListener("click", enableVoicePlayback);
elements.speakNowBtn.addEventListener("click", () => {
  const text = elements.currentReplyText.textContent;
  if (latestState?.integrations?.aigcpanel?.enabled) {
    handleAction(
      () => postJson("/api/integrations/aigcpanel/submit", { text }),
      elements.aigcResult
    );
    return;
  }
  if (speakText(text, { label: "正在试听当前播报" })) {
    voiceState.lastSpokenSignature = currentReplySignature({
      timestamp: Date.now(),
      user: "manual-preview",
      tts_text: text
    });
  }
});
elements.stopVoiceBtn.addEventListener("click", stopVoicePlayback);
elements.stageVideo.addEventListener("ended", () => {
  if (liveMediaState.generatedVideoUrl) {
    voiceState.speaking = false;
    restoreDefaultStageVideo();
    if (latestState?.integrations?.aigcpanel?.enabled) {
      updateVoiceChip("AIGCPanel 已接管语音");
    }
  }
});
elements.aigcPingBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/integrations/aigcpanel/ping"), elements.aigcResult)
);
elements.aigcSubmitBtn.addEventListener("click", () => {
  const text = latestState?.current_reply?.tts_text || latestState?.current_reply?.reply || "";
  handleAction(
    () => postJson("/api/integrations/aigcpanel/submit", text ? { text } : {}),
    elements.aigcResult
  );
});
elements.aigcQueryBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/integrations/aigcpanel/query"), elements.aigcResult)
);
elements.aigcCancelBtn.addEventListener("click", () =>
  handleAction(() => postJson("/api/integrations/aigcpanel/cancel"), elements.aigcResult)
);

refreshState();
if (voiceState.available) {
  window.speechSynthesis.onvoiceschanged = () => {
    if (voiceState.enabled) {
      updateVoiceChip("自动播报已开启");
    }
  };
}
window.setInterval(syncStageMode, 300);
window.setInterval(refreshState, POLL_INTERVAL_MS);
