(() => {
  'use strict';

  const PROVIDERS = ['gemini', 'openai', 'perplexity'];

  const state = {
    defaultDemoMode: true,
    providers: {},
    canRealSynthesize: false,
    synthesizeDisabledReason: '',
    isBusy: false,
    lastQuestion: '',
    lastRunMode: null, // 'demo' | 'real' | null
    answers: { gemini: '', openai: '', perplexity: '' },
    perplexityCitations: [],
    finalText: '',
  };

  // DOM helpers
  const $ = (id) => document.getElementById(id);

  const els = {
    modeBadge: $('mode-badge'),
    apiCallsTotal: $('api-calls-total'),
    apiCallsBreakdown: $('api-calls-breakdown'),
    demoBanner: $('demo-mode-banner'),
    questionInput: $('question-input'),
    btnRunAll: $('btn-run-all'),
    btnRunDemo: $('btn-run-demo'),
    btnSynthesize: $('btn-synthesize'),
    btnSynthesizeLabel: $('btn-synthesize-label'),
    synthesizeReason: $('synthesize-reason'),
    formError: $('form-error'),
    runModeIndicator: $('run-mode-indicator'),
    synthSection: $('synthesize-section'),
    statusCritique: $('status-critique'),
    bodyCritique: $('body-critique'),
    statusFinal: $('status-final'),
    bodyFinal: $('body-final'),
    btnCopyFinal: $('btn-copy-final'),
    citationsBox: $('citations-perplexity'),
    citationsList: $('citations-list'),
  };

  /** Thoát ký tự HTML để chống XSS tuyệt đối trước khi định dạng nhẹ */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Định dạng inline đơn giản (đậm, nghiêng, code) trên chuỗi đã escape HTML */
  function formatInline(escapedLine) {
    return escapedLine
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>');
  }

  /** Chuyển văn bản trả lời sang HTML an toàn (đoạn văn, gạch đầu dòng, danh sách số) */
  function renderSafeMarkdown(rawText) {
    const lines = String(rawText || '').replace(/\r\n/g, '\n').split('\n');
    const htmlParts = [];
    let listType = null; // 'ul' | 'ol' | null

    const closeList = () => {
      if (listType) {
        htmlParts.push(`</${listType}>`);
        listType = null;
      }
    };

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        closeList();
        continue;
      }

      const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/);
      const olMatch = trimmed.match(/^\d+[.)]\s+(.*)$/);

      if (ulMatch) {
        if (listType !== 'ul') {
          closeList();
          htmlParts.push('<ul>');
          listType = 'ul';
        }
        htmlParts.push(`<li>${formatInline(escapeHtml(ulMatch[1]))}</li>`);
      } else if (olMatch) {
        if (listType !== 'ol') {
          closeList();
          htmlParts.push('<ol>');
          listType = 'ol';
        }
        htmlParts.push(`<li>${formatInline(escapeHtml(olMatch[1]))}</li>`);
      } else {
        closeList();
        const headingMatch = trimmed.match(/^#{1,3}\s+(.*)$/);
        if (headingMatch) {
          htmlParts.push(
            `<p><strong>${formatInline(escapeHtml(headingMatch[1]))}</strong></p>`
          );
        } else {
          htmlParts.push(`<p>${formatInline(escapeHtml(trimmed))}</p>`);
        }
      }
    }

    closeList();
    return htmlParts.join('') || '<p class="text-stone-400 italic">Không có nội dung.</p>';
  }

  function showFormError(msg) {
    if (!msg) {
      els.formError.textContent = '';
      els.formError.classList.add('hidden');
      return;
    }
    els.formError.textContent = msg;
    els.formError.classList.remove('hidden');
  }

  function updateApiCalls(apiCalls) {
    if (!apiCalls) return;
    els.apiCallsTotal.textContent = String(apiCalls.total ?? 0);
    els.apiCallsBreakdown.textContent = `(G: ${apiCalls.gemini ?? 0} · GPT: ${apiCalls.openai ?? 0} · P: ${apiCalls.perplexity ?? 0})`;
  }

  function setStatusBadge(el, status, customText) {
    const base =
      'shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium';
    if (status === 'running') {
      el.className = `${base} bg-amber-100 text-amber-900`;
      el.innerHTML = `<span class="spinner-ring" aria-hidden="true"></span><span>${escapeHtml(customText || 'Đang chạy...')}</span>`;
    } else if (status === 'done') {
      el.className = `${base} bg-emerald-100 text-emerald-900`;
      el.textContent = customText || 'Xong';
    } else if (status === 'error') {
      el.className = `${base} bg-red-100 text-red-800`;
      el.textContent = customText || 'Lỗi';
    } else if (status === 'missing_key') {
      el.className = `${base} bg-stone-200 text-stone-700`;
      el.textContent = customText || 'Chưa có key';
    } else {
      el.className = `${base} bg-stone-100 text-stone-600`;
      el.textContent = customText || 'Chờ câu hỏi';
    }
  }

  function renderCitations(citations) {
    els.citationsList.innerHTML = '';
    if (!Array.isArray(citations) || citations.length === 0) {
      els.citationsBox.classList.add('hidden');
      return;
    }

    const validItems = citations.filter(
      (item) =>
        item &&
        typeof item.url === 'string' &&
        (item.url.startsWith('http://') || item.url.startsWith('https://'))
    );

    if (validItems.length === 0) {
      els.citationsBox.classList.add('hidden');
      return;
    }

    validItems.forEach((item, index) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = item.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.className =
        'inline-flex items-start gap-1.5 text-teal-800 hover:text-teal-950 hover:underline break-all';
      a.textContent = `[${index + 1}] ${item.title || item.url}`;
      li.appendChild(a);
      els.citationsList.appendChild(li);
    });

    els.citationsBox.classList.remove('hidden');
  }

  function hasAnyAnswer() {
    return PROVIDERS.some((p) => Boolean((state.answers[p] || '').trim()));
  }

  function updateButtons() {
    els.btnRunAll.disabled = state.isBusy;
    els.btnRunDemo.disabled = state.isBusy;

    const answersReady = hasAnyAnswer();

    if (state.isBusy) {
      els.btnSynthesize.disabled = true;
      return;
    }

    if (state.lastRunMode === 'demo' && answersReady) {
      els.btnSynthesize.disabled = false;
      els.btnSynthesizeLabel.textContent = 'Phản biện & chốt (Demo)';
      if (!state.canRealSynthesize && state.synthesizeDisabledReason) {
        els.synthesizeReason.textContent = `Đang bật bản Demo (0 lượt API). Lưu ý khi chạy API thật: ${state.synthesizeDisabledReason}`;
        els.synthesizeReason.className = 'text-xs text-amber-800';
      } else {
        els.synthesizeReason.textContent = 'Đang ở chế độ Demo — bấm để xem luồng Gemini phản biện và GPT chốt mẫu (không tốn phí).';
        els.synthesizeReason.className = 'text-xs text-muted';
      }
      return;
    }

    els.btnSynthesizeLabel.textContent = 'Phản biện & chốt';

    if (!state.canRealSynthesize) {
      els.btnSynthesize.disabled = true;
      els.synthesizeReason.textContent =
        state.synthesizeDisabledReason ||
        'Cần có cả GEMINI_API_KEY và OPENAI_API_KEY trong file .env để chạy Phản biện & chốt.';
      els.synthesizeReason.className = 'text-xs text-amber-800 font-medium';
      return;
    }

    if (!answersReady) {
      els.btnSynthesize.disabled = true;
      els.synthesizeReason.textContent =
        'Hãy bấm "Chạy cả ba" trước để có ít nhất 1 câu trả lời rồi mới bấm "Phản biện & chốt".';
      els.synthesizeReason.className = 'text-xs text-muted';
      return;
    }

    els.btnSynthesize.disabled = false;
    els.synthesizeReason.textContent =
      'Sẵn sàng: Gemini sẽ phản biện các câu trả lời đã có, sau đó GPT viết bản chốt tiếng Việt (tốn 2 lượt gọi API).';
    els.synthesizeReason.className = 'text-xs text-emerald-800';
  }

  function renderProviderStatusChips() {
    const dotColors = {
      gemini: 'bg-blue-600',
      openai: 'bg-emerald-600',
      perplexity: 'bg-teal-600',
    };

    for (const provider of PROVIDERS) {
      const info = state.providers[provider];
      if (!info) continue;

      const modelEl = $(`model-${provider}`);
      if (modelEl) {
        modelEl.textContent = info.model || '';
      }

      const chip = $(`chip-${provider}`);
      if (!chip) continue;

      if (info.configured) {
        chip.className =
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 font-medium';
        chip.innerHTML = `<span class="w-2 h-2 rounded-full ${dotColors[provider]}"></span><span>${escapeHtml(info.name)}: Sẵn sàng</span>`;
      } else {
        chip.className =
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-100 border border-line text-stone-500';
        chip.innerHTML = `<span class="w-2 h-2 rounded-full bg-stone-400"></span><span>${escapeHtml(info.name)}: Chưa có key</span>`;
      }
    }

    if (state.defaultDemoMode) {
      els.modeBadge.textContent = 'Chế độ Demo (Miễn phí)';
      els.modeBadge.className =
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900';
      els.demoBanner.classList.remove('hidden');
    } else {
      els.modeBadge.textContent = 'Kết nối API chính thức';
      els.modeBadge.className =
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-900';
      els.demoBanner.classList.add('hidden');
    }
  }

  /** Đọc phản hồi NDJSON stream từng dòng ngay khi backend gửi ra */
  async function readNdjsonStream(response, onEvent) {
    if (!response.body) {
      throw new Error('Trình duyệt không hỗ trợ đọc stream.');
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          onEvent(JSON.parse(trimmed));
        } catch (_err) {
          // Bỏ qua dòng không hợp lệ nếu có
        }
      }
    }

    const tail = buffer.trim();
    if (tail) {
      try {
        onEvent(JSON.parse(tail));
      } catch (_err) {
        // ignore
      }
    }
  }

  function resetColumnsForNewRun() {
    state.answers = { gemini: '', openai: '', perplexity: '' };
    state.perplexityCitations = [];
    state.finalText = '';

    for (const provider of PROVIDERS) {
      setStatusBadge($(`status-${provider}`), 'idle', 'Chuẩn bị...');
      $(`body-${provider}`).innerHTML =
        '<p class="text-stone-400 italic">Đang chuẩn bị gửi câu hỏi...</p>';
      const footer = $(`footer-${provider}`);
      footer.textContent = '';
      footer.classList.add('hidden');
    }

    els.citationsBox.classList.add('hidden');
    els.citationsList.innerHTML = '';
    els.synthSection.classList.add('hidden');
    els.btnCopyFinal.classList.add('hidden');
  }

  async function runAsk(forceDemo) {
    const question = els.questionInput.value.trim();
    if (!question) {
      showFormError('Vui lòng nhập một câu hỏi trước khi bấm chạy.');
      els.questionInput.focus();
      return;
    }

    showFormError('');
    state.isBusy = true;
    state.lastQuestion = question;
    resetColumnsForNewRun();
    updateButtons();

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, demo: Boolean(forceDemo) }),
      });

      if (!response.ok) {
        let errMsg = 'Không thể gửi câu hỏi. Hãy thử lại.';
        try {
          const errData = await response.json();
          if (errData && errData.error) errMsg = errData.error;
        } catch (_e) {
          // ignore
        }
        showFormError(errMsg);
        return;
      }

      await readNdjsonStream(response, (ev) => {
        if (ev.api_calls) updateApiCalls(ev.api_calls);

        if (ev.type === 'meta') {
          state.lastRunMode = ev.mode;
          els.runModeIndicator.textContent =
            ev.mode === 'demo'
              ? 'Đang hiển thị dữ liệu Chế độ demo (không gọi API thật)'
              : 'Đang gọi trực tiếp API chính thức';
        } else if (ev.type === 'provider_status') {
          setStatusBadge($(`status-${ev.provider}`), 'running', 'Đang chạy...');
          $(`body-${ev.provider}`).innerHTML =
            '<p class="text-stone-500 italic">Đang chờ phản hồi từ AI...</p>';
        } else if (ev.type === 'provider_result') {
          const p = ev.provider;
          const bodyEl = $(`body-${p}`);
          const statusEl = $(`status-${p}`);
          const footerEl = $(`footer-${p}`);

          if (ev.status === 'done') {
            state.answers[p] = ev.answer || '';
            setStatusBadge(statusEl, 'done', 'Xong');
            bodyEl.innerHTML = `<div class="animate-fade-in">${renderSafeMarkdown(ev.answer)}</div>`;

            const timeLabel =
              typeof ev.elapsed_seconds === 'number' && ev.elapsed_seconds > 0
                ? `Hoàn thành trong ${ev.elapsed_seconds} giây`
                : 'Hoàn thành';
            footerEl.textContent = ev.is_demo ? `${timeLabel} · Dữ liệu mẫu Demo` : timeLabel;
            footerEl.classList.remove('hidden');

            if (p === 'perplexity') {
              state.perplexityCitations = Array.isArray(ev.citations) ? ev.citations : [];
              renderCitations(state.perplexityCitations);
            }
          } else if (ev.status === 'missing_key') {
            setStatusBadge(statusEl, 'missing_key', 'Chưa có key');
            bodyEl.innerHTML = `<p class="text-stone-500 bg-stone-50 border border-line rounded-xl p-3 text-xs">${escapeHtml(ev.message || 'Chưa cấu hình API key.')}</p>`;
          } else {
            setStatusBadge(statusEl, 'error', 'Lỗi');
            bodyEl.innerHTML = `<div class="rounded-xl border border-red-200 bg-red-50/80 p-3 text-xs text-red-800 leading-relaxed">${escapeHtml(ev.message || 'Đã có lỗi xảy ra.')}</div>`;
          }
        }
      });
    } catch (_err) {
      showFormError('Không kết nối được tới máy chủ TrioAI cục bộ. Hãy kiểm tra cửa sổ dòng lệnh đang chạy app.');
    } finally {
      state.isBusy = false;
      updateButtons();
    }
  }

  async function runSynthesize() {
    if (!hasAnyAnswer() || !state.lastQuestion) {
      showFormError('Chưa có câu trả lời nào để phản biện.');
      return;
    }

    const useDemo = state.lastRunMode === 'demo';
    if (!useDemo && !state.canRealSynthesize) {
      showFormError(state.synthesizeDisabledReason || 'Thiếu Gemini hoặc GPT key.');
      return;
    }

    showFormError('');
    state.isBusy = true;
    state.finalText = '';
    els.btnCopyFinal.classList.add('hidden');
    els.synthSection.classList.remove('hidden');
    setStatusBadge(els.statusCritique, 'running', 'Đang chạy...');
    els.bodyCritique.innerHTML =
      '<p class="text-stone-500 italic">Gemini đang đọc và phản biện các câu trả lời...</p>';
    setStatusBadge(els.statusFinal, 'idle', 'Chờ bước 1');
    els.bodyFinal.innerHTML =
      '<p class="text-stone-400 italic">GPT sẽ viết bản chốt ngay sau khi Gemini phản biện xong.</p>';
    updateButtons();

    els.synthSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
      const response = await fetch('/api/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: state.lastQuestion,
          answers: state.answers,
          citations: state.perplexityCitations,
          demo: useDemo,
        }),
      });

      if (!response.ok) {
        let errMsg = 'Không thể chạy Phản biện & chốt.';
        try {
          const errData = await response.json();
          if (errData && errData.error) errMsg = errData.error;
        } catch (_e) {
          // ignore
        }
        setStatusBadge(els.statusCritique, 'error', 'Lỗi');
        els.bodyCritique.innerHTML = `<div class="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">${escapeHtml(errMsg)}</div>`;
        return;
      }

      await readNdjsonStream(response, (ev) => {
        if (ev.api_calls) updateApiCalls(ev.api_calls);

        if (ev.type === 'step') {
          if (ev.step === 'critique') {
            setStatusBadge(els.statusCritique, 'running', 'Đang chạy...');
          } else if (ev.step === 'final') {
            setStatusBadge(els.statusFinal, 'running', 'Đang chạy...');
            els.bodyFinal.innerHTML =
              '<p class="text-stone-500 italic">GPT đang tổng hợp bản chốt tiếng Việt ngắn gọn...</p>';
          }
        } else if (ev.type === 'critique_result') {
          if (ev.status === 'done') {
            setStatusBadge(els.statusCritique, 'done', 'Xong');
            els.bodyCritique.innerHTML = `<div class="animate-fade-in">${renderSafeMarkdown(ev.text)}</div>`;
          } else {
            setStatusBadge(els.statusCritique, 'error', 'Lỗi');
            els.bodyCritique.innerHTML = `<div class="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">${escapeHtml(ev.message || 'Gemini phản biện gặp lỗi.')}</div>`;
            setStatusBadge(els.statusFinal, 'idle', 'Đã dừng');
            els.bodyFinal.innerHTML =
              '<p class="text-stone-400 italic">Không chạy bước chốt vì bước phản biện chưa thành công.</p>';
          }
        } else if (ev.type === 'final_result') {
          if (ev.status === 'done') {
            state.finalText = ev.text || '';
            setStatusBadge(els.statusFinal, 'done', 'Xong');
            els.bodyFinal.innerHTML = `<div class="animate-fade-in">${renderSafeMarkdown(ev.text)}</div>`;
            els.btnCopyFinal.classList.remove('hidden');
          } else {
            setStatusBadge(els.statusFinal, 'error', 'Lỗi');
            els.bodyFinal.innerHTML = `<div class="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">${escapeHtml(ev.message || 'GPT tổng hợp gặp lỗi.')}</div>`;
          }
        }
      });
    } catch (_err) {
      setStatusBadge(els.statusCritique, 'error', 'Lỗi');
      els.bodyCritique.innerHTML =
        '<div class="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">Mất kết nối tới máy chủ cục bộ khi đang phản biện. Hãy thử lại.</div>';
    } finally {
      state.isBusy = false;
      updateButtons();
    }
  }

  async function loadInitialStatus() {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      state.defaultDemoMode = Boolean(data.default_demo_mode);
      state.providers = data.providers || {};
      state.canRealSynthesize = Boolean(data.can_real_synthesize);
      state.synthesizeDisabledReason = data.synthesize_disabled_reason || '';
      updateApiCalls(data.api_calls);
      renderProviderStatusChips();
      updateButtons();
    } catch (_err) {
      showFormError('Không tải được trạng thái máy chủ TrioAI.');
    }
  }

  // Event listeners
  els.btnRunAll.addEventListener('click', () => runAsk(false));
  els.btnRunDemo.addEventListener('click', () => runAsk(true));
  els.btnSynthesize.addEventListener('click', () => runSynthesize());

  document.querySelectorAll('.sample-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const sample = btn.getAttribute('data-sample') || '';
      els.questionInput.value = sample;
      showFormError('');
      els.questionInput.focus();
    });
  });

  els.questionInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !state.isBusy) {
      e.preventDefault();
      runAsk(false);
    }
  });

  els.btnCopyFinal.addEventListener('click', async () => {
    if (!state.finalText) return;
    try {
      await navigator.clipboard.writeText(state.finalText);
      const oldLabel = els.btnCopyFinal.textContent;
      els.btnCopyFinal.textContent = 'Đã chép!';
      setTimeout(() => {
        els.btnCopyFinal.textContent = oldLabel;
      }, 1500);
    } catch (_err) {
      // ignore
    }
  });

  // Khởi tạo: chỉ kiểm tra trạng thái cấu hình, TUYỆT ĐỐI không tự động gọi API AI
  loadInitialStatus();
})();
