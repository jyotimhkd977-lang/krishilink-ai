/* ==========================================================================
   KrishiLink AI — Conversational Voice & Chat Assistant
   Section 19: Multilingual Agricultural Decision Support
   ========================================================================== */

class KrishiAiAssistant {
  constructor() {
    this.isOpen = false;
    this.isListening = false;
    this.messages = [];
  }

  init() {
    this.bindEvents();
    this.addBotMessage(window.KrishiI18n.t('ai_chat_greeting'));
  }

  open() {
    const modal = document.getElementById('ai-assistant-modal');
    if (modal) modal.classList.add('active');
    this.isOpen = true;
    window.KrishiAudio.playClick();
  }

  close() {
    const modal = document.getElementById('ai-assistant-modal');
    if (modal) modal.classList.remove('active');
    this.isOpen = false;
    this.stopListening();
    window.KrishiAudio.playClick();
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }

  bindEvents() {
    // Floating buttons & trigger CTAs
    document.querySelectorAll('.btn-trigger-ai').forEach(btn => {
      btn.addEventListener('click', () => this.toggle());
    });

    const closeBtn = document.getElementById('ai-assistant-close');
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());

    // Prompt Chips
    document.querySelectorAll('.ai-chip-btn').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const question = e.target.textContent;
        this.askQuestion(question);
      });
    });

    // Chat form input
    const form = document.getElementById('ai-chat-form');
    const input = document.getElementById('ai-chat-input');
    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text) {
          this.askQuestion(text);
          input.value = '';
        }
      });
    }

    // Voice button
    const micBtn = document.getElementById('ai-voice-mic-btn');
    if (micBtn) {
      micBtn.addEventListener('click', () => this.toggleVoice());
    }
  }

  toggleVoice() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    this.isListening = true;
    const waves = document.getElementById('voice-waves-container');
    const input = document.getElementById('ai-chat-input');
    const micBtn = document.getElementById('ai-voice-mic-btn');

    if (waves) waves.style.display = 'flex';
    if (input) input.style.display = 'none';
    if (micBtn) micBtn.style.background = '#DC2626';

    window.KrishiAudio.playScan();

    // Check if Web Speech Recognition is available
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        const langCode = window.KrishiI18n.currentLang === 'hi' ? 'hi-IN' : (window.KrishiI18n.currentLang === 'or' ? 'or-IN' : 'en-IN');
        recognition.lang = langCode;
        recognition.start();

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          this.stopListening();
          this.askQuestion(transcript);
        };

        recognition.onerror = () => {
          this.simulateVoiceFallback();
        };
      } catch (err) {
        this.simulateVoiceFallback();
      }
    } else {
      this.simulateVoiceFallback();
    }
  }

  simulateVoiceFallback() {
    setTimeout(() => {
      this.stopListening();
      const randomPrompt = window.KrishiI18n.currentLang === 'hi'
        ? "मुझे अपना टमाटर कब बेचना चाहिए?"
        : (window.KrishiI18n.currentLang === 'or' ? "ମୁଁ ମୋ ଟମାଟୋ କେବେ ବିକ୍ରି କରିବା ଉଚିତ?" : "When should I sell my tomato?");
      this.askQuestion(randomPrompt);
    }, 2200);
  }

  stopListening() {
    this.isListening = false;
    const waves = document.getElementById('voice-waves-container');
    const input = document.getElementById('ai-chat-input');
    const micBtn = document.getElementById('ai-voice-mic-btn');

    if (waves) waves.style.display = 'none';
    if (input) input.style.display = 'block';
    if (micBtn) micBtn.style.background = '';
  }

  askQuestion(text) {
    this.addUserMessage(text);
    window.KrishiAudio.playClick();

    // Generate intelligent AI response based on agricultural query and selected language
    setTimeout(() => {
      const reply = this.generateAiResponse(text);
      this.addBotMessage(reply);
      this.speakText(reply);
      window.KrishiAudio.playSuccess();
    }, 800);
  }

  generateAiResponse(query) {
    const q = query.toLowerCase();
    const lang = window.KrishiI18n.currentLang;

    if (q.includes('price') || q.includes('भाव') || q.includes('ଦର')) {
      if (lang === 'hi') {
        return "आज खोर्धा और भुवनेश्वर मंडी में टमाटर का भाव ₹30.50/किग्रा है (8.2% की वृद्धि)। आलू ₹24/किग्रा और प्याज ₹27/किग्रा चल रहा है।";
      } else if (lang === 'or') {
        return "ଆଜି ଖୋର୍ଦ୍ଧା ବଜାରରେ ଟମାଟୋ ଦର ₹୩୦.୫୦/କେଜି (୮.୨% ବୃଦ୍ଧି)। ଆଳୁ ₹୨୪/କେଜି ଏବଂ ପିଆଜ ₹୨୭/କେଜି ଚାଲିଛି।";
      } else {
        return "Today's tomato mandi price in Khordha & Bhubaneswar is ₹30.50/kg (+8.2% increase). Potato is ₹24/kg and Onion is ₹27/kg.";
      }
    }

    if (q.includes('when') || q.includes('wait') || q.includes('कब') || q.includes('इंतज़ार') || q.includes('କେବେ')) {
      if (lang === 'hi') {
        return "कृषि एआई का पूर्वानुमान है कि स्थानीय मांग 18% बढ़ रही है। यदि आपके पास 500 किग्रा टमाटर है, तो 2-3 दिन बाद ₹32-₹34/किग्रा के भाव पर बेचना सबसे लाभदायक रहेगा।";
      } else if (lang === 'or') {
        return "ଏଆଇ ଆକଳନ ଅନୁସାରେ ସ୍ଥାନୀୟ ଚାହିଦା ୧୮% ବୃଦ୍ଧି ପାଉଛି। ୨–୩ ଦିନ ଅପେକ୍ଷା କରି ₹୩୨–₹୩୪/କେଜି ଦରରେ ବିକ୍ରି କରିବା ଦ୍ୱାରା ଆପଣଙ୍କୁ ସର୍ବାଧିକ ଲାଭ ମିଳିବ।";
      } else {
        return "Krishi AI forecasts regional demand rising by 18%. For your 500 kg tomato lot, holding for 2–3 days will unlock peak pricing of ₹32–₹34/kg.";
      }
    }

    if (q.includes('buyer') || q.includes('खरीदार') || q.includes('କ୍ରେତା')) {
      if (lang === 'hi') {
        return "आपकी फसल के लिए ABC Foods (94% एआई मिलान) सबसे अच्छा विकल्प है। वे 500 किग्रा के लिए ₹32/किग्रा की पेशकश कर रहे हैं और खेत से स्वयं पिकअप करते हैं।";
      } else if (lang === 'or') {
        return "ଆପଣଙ୍କ ପାଇଁ ABC Foods (୯୪% ଏଆଇ ମେଳକ) ସର୍ବୋତ୍ତମ କ୍ରେତା। ସେମାନେ ₹୩୨/କେଜି ଅଫର କରୁଛନ୍ତି ଏବଂ ଫାର୍ମରୁ ତୁରନ୍ତ ପିକଅପ୍ କରନ୍ତି।";
      } else {
        return "ABC Foods India Ltd. has the highest AI Match (94%). They are offering ₹32/kg for 500 kg with verified prompt payment and door-step farm pickup.";
      }
    }

    if (q.includes('earn') || q.includes('कमाई') || q.includes('ରୋଜଗାର')) {
      if (lang === 'hi') {
        return "आपके 500 किग्रा टमाटर से लगभग ₹16,000 की कुल बिक्री होगी। परिवहन और 1.5% फ़ीस काटकर आपके बैंक खाते में शुद्ध ₹15,180 आएंगे।";
      } else if (lang === 'or') {
        return "ଆପଣଙ୍କ ୫୦୦ କେଜି ଟମାଟୋରୁ ପାଖାପାଖି ₹୧୬,୦୦୦ ମୋଟ ବିକ୍ରି ହେବ। ଖର୍ଚ୍ଚ କଟି ଆପଣଙ୍କ ଖାତାକୁ ₹୧୫,୧୮୦ ଜମା ହେବ।";
      } else {
        return "Selling your 500 kg tomato lot at ₹32/kg yields ₹16,000 gross. After logistics and minimal platform fee, net settlement in your bank is ₹15,180.";
      }
    }

    // Default friendly assistant response
    if (lang === 'hi') {
      return "मैं आपकी फसल की कीमतें, सर्वोत्तम खरीदार और मौसम आधारित तुड़ाई सलाह में पूरी सहायता कर सकता हूँ। ऊपर दिए गए प्रश्नों में से चुनें!";
    } else if (lang === 'or') {
      return "ମୁଁ ଆପଣଙ୍କ ଫସଲର ବଜାର ଦର, ଉତ୍ତମ କ୍ରେତା ଏବଂ ପାଣିପାଗ ସମ୍ବନ୍ଧୀୟ ପରାମର୍ଶ ଦେଇପାରିବି। ଉପରୋକ୍ତ ପ୍ରଶ୍ନ ମଧ୍ୟରୁ ବାଛନ୍ତୁ!";
    } else {
      return "I can help you evaluate current mandi prices, match with top verified buyers, or plan your harvest around rain forecasts. Select any suggestion chip or type below!";
    }
  }

  addUserMessage(text) {
    const chatBody = document.getElementById('ai-chat-body');
    if (!chatBody) return;

    const div = document.createElement('div');
    div.className = 'ai-bubble user';
    div.textContent = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  addBotMessage(text) {
    const chatBody = document.getElementById('ai-chat-body');
    if (!chatBody) return;

    const div = document.createElement('div');
    div.className = 'ai-bubble bot';
    div.innerHTML = `<strong>🤖 Krishi AI:</strong><br>${text}`;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  speakText(text) {
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text.replace(/<[^>]*>?/gm, ''));
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        const lang = window.KrishiI18n.currentLang;
        utterance.lang = (lang === 'hi') ? 'hi-IN' : (lang === 'or' ? 'or-IN' : 'en-IN');
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.warn('Speech synthesis error:', e);
      }
    }
  }
}

window.KrishiAiAssistant = new KrishiAiAssistant();
