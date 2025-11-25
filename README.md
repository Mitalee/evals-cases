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
- Has a wedding in 2 weeks
- Needs a dress that fits well
- Usually between sizes (struggles with fit)
- Budget: $150

### Her 5 Questions

1. **Urgency Test**: "I have a wedding in 2 weeks... should I risk ordering it?"
2. **Demographic Analysis**: "What do other customers around my age think?"
3. **Personalization**: "I'm between M and L, which size should I order?"
4. **Risk Management**: "What's my backup plan if it doesn't work?"
5. **Value Assessment**: "Is this worth $120, or should I look elsewhere?"

### The Progressive Improvement Flow

**Question 1 → Fails**
- AI gives generic advice
- Doesn't consider timeline
- Add instruction: "Consider time constraints and shipping times"
- Re-run → Passes! ✅

**Question 2 → Fails**
- AI doesn't filter by age
- Doesn't analyze demographics
- Add instruction: "Analyze demographic data when asked about segments"
- Re-run → Passes! ✅

...and so on for all 5 questions!

## 🎮 How to Use

1. **Start with Question 1**
   - Review Sarah's question
   - See the review context
   - Enter your API key
   - Click "Run Evaluation"

2. **Check Results**
   - See AI's response
   - Automatic evaluation shows pass/fail
   - Missing elements highlighted

3. **Improve When Failed**
   - Suggested prompt improvement shown
   - Click "Add to System Prompt"
   - Re-run evaluation
   - See the improvement!

4. **Progress Through All 5 Questions**
   - Each failure teaches a lesson
   - System prompt gets better incrementally
   - Final prompt is production-ready!

## 📊 What Gets Evaluated

For each response, we check if it includes:
- **Timeline consideration** (for urgency questions)
- **Demographic insights** (for segment questions)
- **Specific recommendations** (for personalization)
- **Risk mitigation** (for planning questions)
- **Value assessment** (for budget questions)

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

## 🚀 Deployment

This app can be deployed on Streamlit Cloud:

1. Push to GitHub
2. Connect to [streamlit.app](https://streamlit.io/cloud)
3. Deploy in one click!

Similar to: [GenZ Talk AI](https://genztalkai-mitalee.streamlit.app/)

## 🤝 Contributing

Have ideas for better eval questions? Suggestions for prompt improvements?
Open an issue or PR!

## 📝 License

MIT License

---

Built with ❤️ by Mitalee | Powered by Claude & Streamlit
