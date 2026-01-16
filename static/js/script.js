const uiStrings = {
    enterUrl: 'URL을 입력해주세요',
    analyzing: '분석 중...',
    ready: '다운로드 준비 완료',
    downloading: '다운로드 중...',
    complete: '다운로드 완료! 폴더를 확인하세요.',
    error: '오류 발생: ',
    processing: '파일 변환 중...'
};

function analyzeUrl() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return showStatus(uiStrings.enterUrl, 'error');

    const btn = document.getElementById('analyzeBtn');
    setLoading(btn, true);

    fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    })
        .then(res => {
            if (!res.ok) return res.json().then(e => { throw new Error(e.error) });
            return res.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);

            // Populate info
            document.getElementById('thumbImg').src = data.thumbnail;
            document.getElementById('videoTitle').textContent = data.title;
            document.getElementById('videoMeta').textContent = `${data.duration} • ${data.uploader}`;

            // Populate options
            const select = document.getElementById('qualitySelect');
            select.innerHTML = '';
            data.formats.forEach((fmt, index) => {
                const opt = document.createElement('option');
                opt.value = fmt.format_id;
                opt.textContent = `${fmt.resolution} (${fmt.ext.toUpperCase()}) - ${fmt.filesize ? (fmt.filesize / 1024 / 1024).toFixed(1) + 'MB' : 'Unknown size'}`;
                if (index === 0) opt.selected = true; // Best quality default
                opt.className = 'quality-option';
                select.appendChild(opt);
            });

            // Show info part
            document.getElementById('videoInfo').classList.add('active');

            // Switch buttons
            btn.style.display = 'none';
            document.getElementById('downloadOptions').style.display = 'flex';

            showStatus(uiStrings.ready, 'success');
        })
        .catch(err => {
            showStatus(uiStrings.error + err.message, 'error');
        })
        .finally(() => {
            setLoading(btn, false);
        });
}

async function download(type) {
    const url = document.getElementById('urlInput').value.trim();
    const formatId = document.getElementById('qualitySelect').value;

    const btns = document.querySelectorAll('#downloadOptions .btn');
    const activeBtn = type === 'video' ? btns[0] : btns[1];

    // Disable UI
    btns.forEach(b => {
        b.disabled = true;
        if (b !== activeBtn) b.style.opacity = '0.5';
    });
    setLoading(activeBtn, true);

    // Show Progress UI
    const progressWrapper = document.getElementById('progressWrapper');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressSpeed = document.getElementById('progressSpeed');

    progressWrapper.classList.add('active');
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
    progressSpeed.textContent = '연결 중...';

    showStatus(uiStrings.downloading, 'info');

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                type: type,
                format_id: type === 'video' ? formatId : null
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);

                    if (data.status === 'downloading') {
                        progressFill.style.width = data.percent + '%';
                        progressPercent.textContent = data.percent + '%';
                        progressSpeed.textContent = data.speed;
                    } else if (data.status === 'processing') {
                        progressFill.style.width = '100%';
                        progressPercent.textContent = '100%';
                        progressSpeed.textContent = uiStrings.processing;
                    } else if (data.status === 'complete') {
                        showStatus(uiStrings.complete, 'success');
                        progressFill.style.width = '100%';
                        progressPercent.textContent = '100%';
                        progressSpeed.textContent = '완료';
                    } else if (data.status === 'error') {
                        throw new Error(data.message);
                    }
                } catch (e) {
                    // Ignore JSON parse errors for partial chunks if any
                    // console.error(e); // Uncomment for debugging
                }
            }
        }
    } catch (err) {
        showStatus(uiStrings.error + err.message, 'error');
    } finally {
        setLoading(activeBtn, false);
        btns.forEach(b => {
            b.disabled = false;
            b.style.opacity = '1';
        });
        // Leave progress bar active for a moment then hide? No, keep it visible as record
    }
}

function openFolder() {
    fetch('/api/open_folder', { method: 'POST' });
}

function setLoading(btn, isLoading) {
    if (isLoading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function showStatus(msg, type) {
    const el = document.getElementById('statusMsg');
    el.textContent = msg;
    el.className = 'status-msg active';
    if (type === 'error') el.style.color = '#ef4444';
    else if (type === 'success') el.style.color = '#00f3ff';
    else el.style.color = '#94a3b8';
}

// Enter key support
document.getElementById('urlInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        analyzeUrl();
    }
});
