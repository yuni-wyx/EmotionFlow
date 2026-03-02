// script.js
const chatWindow = document.getElementById('chatWindow');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

function showAuthModal() {
    document.getElementById("authModal").style.display = "flex";
}

function toggleDropdown() {
    const dropdown = document.getElementById("dropdownContent");
    if (dropdown.style.display === "block") {
        dropdown.style.display = "none";
    } else {
        dropdown.style.display = "block";
    }
}

window.onclick = function(event) {
    if (!event.target.matches('.hamburger') && !event.target.closest('.hamburger')) {
        const dropdown = document.getElementById("dropdownContent");
        if (dropdown.style.display === "block") {
            dropdown.style.display = "none";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const guestBtn = document.getElementById("guestBtn");
    if (guestBtn) {
        guestBtn.addEventListener("click", () => {
            fetch('/anonymous-login', {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            })
            .then(res => res.json())
            .then(data => {
                console.log("Logged in as anonymous:", data.user_id);
                document.getElementById("authModal").style.display = "none";
                document.getElementById("mainContent").style.display = "block";
                localStorage.setItem("user_id", data.user_id);
            })
            .catch(err => {
                console.error("Login failed:", err);
            });
        });
    } else {
        console.warn("guestBtn not found!");
    }
});

// show login after animation
setTimeout(() => {
    document.getElementById('intro').style.display = 'none';
    showAuthModal();
}, 3000);

// type animation
async function typeText(message, fromAI = true, delay = 500) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', fromAI ? 'ai' : 'user');
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const lines = message.split('\n');
    for (const line of lines) {
        const span = document.createElement('div');
        span.innerText = line;
        msgDiv.appendChild(span);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        await new Promise(resolve => setTimeout(resolve, delay)); // show delay
    }
}

// message bubble
function addMessage(text, fromAI=false) {
  const msg = document.createElement('div');
  msg.classList.add('message', fromAI ? 'ai' : 'user');
  msg.innerText = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function updateFlowingBackground(colors) {
    const gradientValue = `linear-gradient(-45deg, ${colors.join(", ")})`;
    document.body.style.setProperty('background-image', gradientValue);
    document.body.style.setProperty('background-size', '400% 400%');
    document.body.style.setProperty('animation', 'gradientFlow 10s ease infinite');
}

function addTextFeedbackButtons(responseText, parentElement, emotion = 'neutral', userInput) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-buttons';
    feedbackDiv.setAttribute('data-response', responseText);
    feedbackDiv.setAttribute('data-emotion', emotion);
    feedbackDiv.setAttribute('data-userinput', userInput);

    feedbackDiv.innerHTML = `
        <div class="feedback-prompt">Do you like this response?</div>
        <div class="feedback-buttons-group">
            <button class="feedback-btn like-btn" onclick="sendTextFeedback(this, 'like')">👍</button>
            <button class="feedback-btn dislike-btn" onclick="sendTextFeedback(this, 'dislike')">👎</button>
        </div>
    `;

    parentElement.appendChild(feedbackDiv);
    
    const likeBtn = feedbackDiv.querySelector(".like-btn");
    const dislikeBtn = feedbackDiv.querySelector(".dislike-btn");

    if (likeBtn && dislikeBtn) {
        likeBtn.addEventListener("click", function () {
            sendTextFeedback(this, 'like');
        });
        dislikeBtn.addEventListener("click", function () {
            sendTextFeedback(this, 'dislike');
        });

    } else {
        console.error("❌ Cannot find feedback button！");
    }
}

function sendTextFeedback(button, feedbackType) {
    const feedbackDiv = button.closest(".feedback-buttons");
    const responseText = feedbackDiv?.getAttribute("data-response") || "Unknown";
    const emotion = feedbackDiv?.getAttribute("data-emotion") || "neutral";
    const originalUserInput = feedbackDiv?.getAttribute("data-userinput") || '';
    const user_id = localStorage.getItem('user_id') || 'anonymous';

    const liked = feedbackType === "like";
    const feedbackData = {
        user_id: user_id,
        text_feedback_text: originalUserInput,
        text_feedback_response: responseText,
        text_feedback_emotion: emotion,
        text_feedback_liked: liked,
    };

    fetch("/text_feedback", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(feedbackData)
    }).then(res => {
    if (res.ok && feedbackDiv) {
        feedbackDiv.innerHTML = `<span>Thanks for your feedback! 🙏</span>`;
    } else {
        console.warn("⚠️ Failed to store Feedback response or cannot find parent element");
    }
    }).catch(err => {
        console.error("❌ Failed to send feedback", err);
    });
}

function addMusicFeedbackButtons(responseText, parentElement, emotion = 'neutral', recommendation = null, userInput) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-buttons';
    feedbackDiv.setAttribute('data-response', responseText);
    feedbackDiv.setAttribute('data-emotion', emotion);
    feedbackDiv.setAttribute('data-recommendation', recommendation || '');
    feedbackDiv.setAttribute('data-userinput', userInput);

    feedbackDiv.innerHTML = `
        <div class="feedback-prompt">Do you like this recommendation?</div>
        <div class="feedback-buttons-group">
            <button class="feedback-btn like-btn" onclick="sendMusicFeedback(this, 'like')">👍</button>
            <button class="feedback-btn dislike-btn" onclick="sendMusicFeedback(this, 'dislike')">👎</button>
        </div>
    `;

    parentElement.appendChild(feedbackDiv);
    
    const likeBtn = feedbackDiv.querySelector(".like-btn");
    const dislikeBtn = feedbackDiv.querySelector(".dislike-btn");

    if (likeBtn && dislikeBtn) {
        likeBtn.addEventListener("click", function () {
            sendMusicFeedback(this, 'like');
        });
        dislikeBtn.addEventListener("click", function () {
            sendMusicFeedback(this, 'dislike');
        });
    } else {
        console.error("❌ Cannot find feedback button！");
    }
}

function sendMusicFeedback(button, feedbackType) {
    const feedbackDiv = button.closest(".feedback-buttons");
    const responseText = feedbackDiv?.getAttribute("data-response") || "Unknown";
    const emotion = feedbackDiv?.getAttribute("data-emotion") || "neutral";
    const recommendation = feedbackDiv?.getAttribute("data-recommendation") || null;
    const originalUserInput = feedbackDiv?.getAttribute("data-userinput") || '';
    const user_id = localStorage.getItem('user_id') || 'anonymous';

    const liked = feedbackType === "like";
    const feedbackData = {
        user_id: user_id,
        music_recommendations: recommendation,
        music_emotion: emotion,
        music_liked: liked,
        music_text: originalUserInput
        };
    fetch("/music_feedback", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(feedbackData)
    }).then(res => {
    if (res.ok && feedbackDiv) {
        feedbackDiv.innerHTML = `<span>Thanks for your feedback! 🙏</span>`;
    } else {
        console.warn("⚠️ Failed to store Feedback response or cannot find parent element");
    }
    }).catch(err => {
        console.error("❌ Failed to send feedback", err);
    });
}   

function addFeedbackButtons(type, responseText, parentElement, emotion, extra, userInput) {
    if (type === 'text') {
        addTextFeedbackButtons(responseText, parentElement, emotion, userInput);
    } else if (type === 'music') {
        addMusicFeedbackButtons(responseText, parentElement, emotion, extra, userInput);
    }
}

function makeYoutubeLink(song, artist) {
  const q = encodeURIComponent(`${song} ${artist}`.trim());
  return `https://www.youtube.com/results?search_query=${q}`;
}

function addPreferenceButtons(parentElement, payload) {
  const wrap = document.createElement('div');
  wrap.className = 'pref-wrapper';

  wrap.innerHTML = `
    <div class="pref-container">
      <div class="pref-title">Which response feels more supportive?</div>
      <div class="pref-cards">
        <div class="pref-card" data-choice="A" role="button" tabindex="0">
          <div class="pref-label">A</div>
          <div class="pref-action">Select A</div>
        </div>
        <div class="pref-card" data-choice="B" role="button" tabindex="0">
          <div class="pref-label">B</div>
          <div class="pref-action">Select B</div>
        </div>
      </div>
      <div class="pref-hint">Your choice helps improve responses (RLHF).</div>
    </div>
  `;

  parentElement.appendChild(wrap);

  const cards = wrap.querySelectorAll('.pref-card');

  let submitted = false;

  const send = async (chosen) => {
    if (submitted) return;
        submitted = true;

    // disable all cards
    cards.forEach(c => c.classList.add('disabled'));

    const user_id = localStorage.getItem('user_id') || 'anonymous';

    const body = {
      user_id,
      text: payload.text,
      emotion: payload.emotion,
      request_id: payload.request_id,
      prompt_version_A: payload.candidates.A.prompt_version,
      prompt_version_B: payload.candidates.B.prompt_version,
      response_A: payload.candidates.A.response,
      response_B: payload.candidates.B.response,
      chosen
    };

    try {
      const res = await fetch('/pref_feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        wrap.innerHTML = `<div class="pref-thank">Preference saved ✔ Thanks!</div>`;
      } else {
        wrap.innerHTML = `<div class="pref-error">⚠️ Could not save preference.</div>`;
      }
    } catch (e) {
      console.error(e);
      wrap.innerHTML = `<div class="pref-error">⚠️ Could not save preference.</div>`;
    }
  };

  const pick = (choice, el) => {
    cards.forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    send(choice);
  };

  cards.forEach(card => {
    card.addEventListener('click', () => pick(card.dataset.choice, card));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        pick(card.dataset.choice, card);
      }
    });
  });
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = userInput.value.trim();
  if (!text) return;

  const user_id = localStorage.getItem('user_id') || 'anonymous';

  // ✅ 一開始就鎖住，最後一定解鎖
  sendBtn.disabled = true;
  userInput.disabled = true;

  try {
    // 1) 先顯示使用者訊息（UI 不要等後端）
    addMessage(text, false);
    userInput.value = '';

    // 2) /submit 改成「不阻塞」：就算失敗也不影響聊天
    fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id, user_input: text })
    }).catch(err => console.warn('submit failed:', err));

    // 3) 主要 pipeline：只打一個 /api/flow_ab
    const flowRes = await fetch('/api/flow_ab', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    const flowData = await flowRes.json();

    if (!flowRes.ok || flowData.ok === false) {
      console.error('flow_ab error:', flowData);
      await typeText('🤖 Sorry — I had trouble generating responses. Please try again.', true, 600);
      return; // ✅ return 也沒差，finally 會解鎖
    }

    const emotion = flowData.emotion || 'neutral';

    // 背景色
    const rawColors = flowData.color || "#ddd, #eee, #ccc";
    const colors = rawColors.split(',').map(c => c.trim());
    updateFlowingBackground(colors);

    // A/B 回覆
    const candA = flowData.candidates?.A?.response || "Response A unavailable.";
    const candB = flowData.candidates?.B?.response || "Response B unavailable.";

    await typeText(`(A) ${candA}`, true, 400);
    await typeText(`(B) ${candB}`, true, 400);

    // preference buttons
    const prefBubble = document.createElement('div');
    prefBubble.classList.add('message', 'ai');
    chatWindow.appendChild(prefBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    addPreferenceButtons(prefBubble, {
    text,
    emotion,
    request_id: flowData.request_id,
    candidates: {
        A: { prompt_version: flowData.candidates.A.prompt_version, response: candA },
        B: { prompt_version: flowData.candidates.B.prompt_version, response: candB }
    }
    });

    // music（可選）
    const music = flowData.music || {};
    const song = music.song || '';
    const artist = music.artist || '';
    const reason = music.reason || '';

    if (song || artist || reason) {
      const youtube = makeYoutubeLink(song, artist);
      const recommendationHTML =
        `${song} - ${artist}<br>` +
        `${reason}<br>` +
        `🔗 <a href='${youtube}' target='_blank'>Watch on YouTube</a>`;

      const musicBubble = document.createElement('div');
      musicBubble.classList.add('message', 'ai');
      musicBubble.innerHTML = `Emotion: ${emotion}<br>Music Recommendation🎵<br>${recommendationHTML}`;
      chatWindow.appendChild(musicBubble);
      chatWindow.scrollTop = chatWindow.scrollHeight;

      addFeedbackButtons('music', `Emotion: ${emotion}\nMusic Recommendation\n${recommendationHTML}`, musicBubble, emotion, recommendationHTML, text);
    }

  } catch (err) {
    console.error(err);
    await typeText('🤖 Error: Something went wrong.', true, 600);
  } finally {
    // ✅ 無論成功/失敗/return，都一定會跑到這裡
    sendBtn.disabled = false;
    userInput.disabled = false;
    userInput.focus();
  }
});
