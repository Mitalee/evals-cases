# Evals Demo: Progressive Prompt Improvement

An interactive Streamlit app demonstrating how iterative evaluation drives better AI responses through systematic prompt improvement.

## 🎯 What This Demo Shows

Instead of guessing why AI responses fail, this app demonstrates:
1. **Run evaluations** with test questions
2. **Identify failures** through automated checks
3. **Improve system prompt** with targeted instructions
4. **Re-evaluate** to confirm improvement
5. **Repeat** until all evals pass

## 🏃 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

### 3. Get API Key

You'll need an Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

## 📖 The Story

### Meet Sarah
- 32-year-old professional
- Needs professional clothing for upcoming work presentations
- Needs it in 2 weeks
- Usually between sizes (struggles with fit)
- Anxious about online shopping
- Hates returns - wants to get it right the first time
- Budget: $150

### Her 3 Questions

1. **Purchase Decision**: "I need professional clothing for work presentations. Should I order clothing ID 1094?"
2. **Quality Assessment**: "Does clothing ID 829 have quality issues?"
3. **Sizing Guidance**: "I'm between sizes (usually 8-10). Which size should I order for clothing ID 1094?"

### The Progressive Improvement Flow

**Question 1 → Fails**
- AI gives generic advice
- Doesn't include buy link
- Doesn't personalize to Sarah
- Add instruction: "Include buy links and mention Sarah by name with her specific concerns"
- Re-run → Passes! ✅

**Question 2 → Fails**
- Missing personalization to Sarah's professional needs
- Add instruction: "Connect recommendations to Sarah's work presentation context"
- Re-run → Passes! ✅

...and so on for all 3 questions!

## 🎮 How to Use

1. **Start with Question 1**
   - Review Sarah's question
   - Enter your API key in the sidebar
   - Click a question button to populate the chat
   - Click "Send"

2. **Check Results**
   - See AI's response
   - Automatic evaluation shows pass/fail
   - Both assertions must pass: Commercial Behavior (buy link) + Personalization (mention Sarah + her concerns)

3. **Improve When Failed**
   - Review the failure reason and tip
   - Update your system prompt
   - Click the question again and "Send"
   - See the improvement!

4. **Progress Through All 3 Questions**
   - Each failure teaches a lesson
   - System prompt gets better incrementally
   - Final prompt is production-ready!

## 📊 What Gets Evaluated

For each response, we check 2 assertions:
1. **Commercial Behavior**: Includes buy link in format `https://santra.com/clothing/{id}`
2. **Personalization**: Mentions Sarah BY NAME + references her specific concerns (sizing struggles, return aversion, anxiety, presentation needs, or budget)

## 🏗️ Project Structure

```
evals-demo/
├── app.py              # Main Streamlit app
├── claude_api.py       # API integration & evaluation logic
├── requirements.txt    # Dependencies
├── data/
│   └── evals_demo.db   # SQLite database with reviews
└── README.md          # This file
```

## 🎓 Key Lessons

1. **Evals aren't just pass/fail** - they teach you what to improve
2. **System prompts are critical** - small changes → big impact
3. **Iterate systematically** - fix one failure mode at a time
4. **Use real scenarios** - Sarah's questions expose real gaps
5. **Measure improvement** - quantify before/after

## 🚀 Live Demo

Hosted at: [evals-cases-ms.streamlit.app](https://evals-cases-ms.streamlit.app/)

## 🤝 Contributing

Want to add more assertions, new eval cases, or fix bugs?  
PMs are welcome to vibe code and raise PRs at: [github.com/Mitalee/evals-cases](https://github.com/Mitalee/evals-cases)

## 📝 License

MIT License

---

Built with ☕ + 🤖 by mmulpuru
